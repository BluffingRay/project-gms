from database_client import supabase
import streamlit as st
import pandas as pd


def get_student_grades(student_id):
    """Fetch all enrollments + grades + subjects + units for the student."""
    enrollments = supabase.table("enrollments_view").select(
        "enrollmentid, studentid, studentname, program, yearlevel, semester_term, schoolyear, subjectname, curriculumid, grade"
    ).eq("studentid", student_id).execute().data

    if not enrollments:
        return pd.DataFrame()

    enrollments_df = pd.DataFrame(enrollments)

    # Fetch units for curriculum subjects
    curriculum = supabase.table("curriculum_subjects").select("id, units").execute().data
    curriculum_df = pd.DataFrame(curriculum)
    curriculum_df.rename(columns={"id": "curriculumid"}, inplace=True)

    # Merge units into enrollments
    merged = enrollments_df.merge(curriculum_df, on="curriculumid", how="left")
    merged["units"] = pd.to_numeric(merged["units"], errors="coerce")
    merged["grade"] = pd.to_numeric(merged["grade"], errors="coerce")

    return merged


def calculate_gwa(df, yearlevel=None, semester_term=None):
    if yearlevel:
        df = df[df["yearlevel"] == yearlevel]
    if semester_term:
        df = df[df["semester_term"] == semester_term]

    # If ANY grades are Dropped or INC here, fail fast
    if df["grade"].astype(str).str.upper().str.contains("DROP|DROPPED|INC").any():
        return "--"

    # Numeric grades only
    df.loc[:, "grade"] = pd.to_numeric(df["grade"], errors="coerce")
    df.loc[:, "units"] = pd.to_numeric(df["units"], errors="coerce")


    valid_df = df[
        (df["grade"].between(1.0, 5.0)) &
        (df["units"] > 0)
    ]

    if valid_df.empty or valid_df["units"].sum() == 0:
        return "--"

    valid_df["gp"] = valid_df["grade"] * valid_df["units"]
    total_gp = valid_df["gp"].sum()
    total_units = valid_df["units"].sum()

    return round(total_gp / total_units, 2)


def get_student_gwa_summary(student_id):
    """Return a dict of per-year, per-semester, and overall GWA for the student."""
    df = get_student_grades(student_id)
    if df.empty:
        return {}

    def has_invalid_grades(df):
        return (
            df["grade"].isna().any()
            or df["grade"].astype(str).str.upper().str.contains("INC|DROP|DROPPED").any()
        )

    summary = {}

    for year in ["1st Year", "2nd Year", "3rd Year", "4th Year"]:
        for sem in ["1st Semester", "2nd Semester"]:
            filtered = df[(df["yearlevel"] == year) & (df["semester_term"] == sem)]
            if has_invalid_grades(filtered):
                gwa = "--"
            else:
                gwa = calculate_gwa(filtered)
            summary[f"{year} {sem}"] = gwa

        # For overall per year
        filtered_year = df[df["yearlevel"] == year]
        if has_invalid_grades(filtered_year):
            gwa_year = "--"
        else:
            gwa_year = calculate_gwa(filtered_year)
        summary[f"{year} Overall"] = gwa_year

    # For overall
    if has_invalid_grades(df):
        summary["Overall"] = "--"
    else:
        summary["Overall"] = calculate_gwa(df)

    return summary


def upsert_grade(enrollment_id, grade):
    existing = supabase.table("grades").select("gradeid").eq("enrollmentid", enrollment_id).execute()
    if existing.data and len(existing.data) > 0:
        grade_id = existing.data[0]["gradeid"]
        return supabase.table("grades").update({"grade": grade}).eq("gradeid", grade_id).execute()
    else:
        return supabase.table("grades").insert({"enrollmentid": enrollment_id, "grade": grade}).execute()
    


