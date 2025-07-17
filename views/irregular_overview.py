import streamlit as st
import pandas as pd
from database_client import supabase

def show():
        

    st.set_page_config(page_title="Irregular Students Overview", layout="wide")
    st.title("📋 Irregular Students Overview")

    # -------------------------
    # Fetch Irregular Students
    # -------------------------
    students_response = supabase.table("students").select("*").eq("status", "Irregular").execute()
    students_df = pd.DataFrame(students_response.data if students_response.data else [])

    if students_df.empty:
        st.warning("No irregular students found.")
        st.stop()

    # -------------------------
    # Fetch Enrollments for School Year / Semester Filtering
    # -------------------------
    enrollments_response = supabase.table("enrollments_view").select("*").execute()
    enrollments_df = pd.DataFrame(enrollments_response.data if enrollments_response.data else [])

    schoolyear_semesters = sorted(
        enrollments_df[["schoolyear", "semester_term"]]
        .dropna()
        .drop_duplicates()
        .apply(lambda row: f"{row['schoolyear']} {row['semester_term']}", axis=1)
        .tolist(),
        reverse=True
    )

    # -------------------------
    # Filters Above Table
    # -------------------------
    col1, col2 = st.columns(2)

    with col1:
        programs = ["All"] + sorted(students_df["program"].dropna().unique().tolist())
        selected_program = st.selectbox("Program", programs)

    with col2:
        year_levels = ["All"] + sorted(students_df["yearlevel"].dropna().unique().tolist())
        selected_yearlevel = st.selectbox("Year Level", year_levels)


    # -------------------------
    # Apply Filters to Students
    # -------------------------
    filtered_students = students_df.copy()

    if selected_program != "All":
        filtered_students = filtered_students[filtered_students["program"] == selected_program]

    if selected_yearlevel != "All":
        filtered_students = filtered_students[filtered_students["yearlevel"] == selected_yearlevel]


    # -------------------------
    # Count Failures per Student (Filtered by School Year / Semester)
    # -------------------------
    failed_counts = []

    for _, student in filtered_students.iterrows():
        student_id = student["studentid"]
        student_enrollments = enrollments_df[enrollments_df["studentid"] == student_id]

        if not student_enrollments.empty:
            failed = student_enrollments[
                student_enrollments["grade"]
                .astype(str)
                .str.upper()
                .str.contains("5.0|FAILED|DROP|DROPPED|INC", na=False)
            ]
            failed_count = failed.shape[0]
        else:
            failed_count = 0

        failed_counts.append(failed_count)

    filtered_students["Failures"] = failed_counts

    # -------------------------
    # Display Final Table
    # -------------------------
    st.write("Number of Failed / Dropped / INC subjects per irregular student (based on filters):")

    display_df = (
        filtered_students[["studentid", "firstname", "lastname", "program", "yearlevel", "Failures"]]
        .rename(columns={
            "studentid": "ID",
            "firstname": "First Name",
            "lastname": "Last Name",
            "program": "Program",
            "yearlevel": "Year Level"
        })
        .sort_values(by="Failures", ascending=False)
        .reset_index(drop=True)
    )

    st.dataframe(display_df, use_container_width=True)
