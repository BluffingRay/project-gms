import streamlit as st
import pandas as pd
from services.enrollment_service import get_all_regular_enrollments
from services.student_service import get_all_students
from services.grades_service import get_student_grades, calculate_gwa

def show():

    st.set_page_config(page_title="Overview", layout="wide")
    st.title("Enrollment and Grades Overview")

    # -------------------------
    # Fetch Data
    # -------------------------
    data = get_all_regular_enrollments()
    df = pd.DataFrame(data)

    if df.empty:
        st.warning("No data available.")
        st.stop()

    # 🔍 Search Bar on Top
    st.subheader("🔎 Search Student to Edit")

    # Prepare options
    students_for_search = get_all_students()
    students_df = pd.DataFrame(students_for_search)

    students_df["studentname"] = students_df["firstname"] + ' ' + students_df["lastname"]
    students_df = students_df[students_df["status"].str.lower() == "regular"]

    student_options = {
        f"{row['studentname']} ({row['studentid']})": row["studentid"] for _, row in students_df.iterrows()
    }

    selected_student_display = st.selectbox(
        "Search Student",
        options=[""] + list(student_options.keys()),
        key="search_student_selectbox"
    )

    if selected_student_display:
        selected_student_id = student_options[selected_student_display]
        st.session_state.selected_student_id = selected_student_id
        st.session_state.page = "edit"
        st.rerun()

    # -------------------------
    # Filters
    # -------------------------
    latest_school_year = sorted(df["schoolyear"].dropna().unique())[-1]
    latest_year_level = sorted(df["yearlevel"].dropna().unique())[0]
    latest_term = sorted(df["semester_term"].dropna().unique())[0]
    latest_program = sorted(df["program"].dropna().unique())[0]

    col1, col2, col3, col4 = st.columns(4)
    school_year_filter = col1.selectbox("School Year", sorted(df["schoolyear"].unique()), index=sorted(df["schoolyear"].unique()).index(latest_school_year))
    year_level_filter = col2.selectbox("Year Level", sorted(df["yearlevel"].unique()), index=0)
    semester_filter = col3.selectbox("Semester Term", sorted(df["semester_term"].unique()), index=0)
    program_filter = col4.selectbox("Program", sorted(df["program"].unique()), index=0)

    filtered_df = df[
        (df["schoolyear"] == school_year_filter) &
        (df["yearlevel"] == year_level_filter) &
        (df["semester_term"] == semester_filter) &
        (df["program"] == program_filter)
    ]

    if filtered_df.empty:
        st.info("No data to display after applying filters.")
        st.stop()

    # -------------------------
    # KPIs
    # -------------------------
    total_enrollment = filtered_df["studentname"].nunique()

    def has_problematic_grade(grades):
        return any(
            (pd.isna(g) or str(g).strip().upper() == "INC" or str(g).strip() == "" or str(g).strip().upper() == "Dropped")
            for g in grades
        )

    students_with_problems = (
        filtered_df.groupby("studentname")["grade"]
        .apply(has_problematic_grade)
    )

    problematic_students = students_with_problems.sum()
    students_with_grades = total_enrollment - problematic_students

    col1, col2, col3 = st.columns(3)
    col1.metric("📊 Total Enrollment", total_enrollment)
    col2.metric("✅ Students with Complete Grades", students_with_grades)
    col3.metric("⚠️ Students with Issues", problematic_students)

    # -------------------------
    # Build Custom Table (Only Current Filter's Subjects)
    # -------------------------
    unique_subjects = sorted(filtered_df["subjectname"].dropna().unique())
    students = filtered_df[["studentid", "studentname", "studentremarks"]].drop_duplicates().reset_index(drop=True)

    for subject in unique_subjects:
        subject_df = filtered_df[filtered_df["subjectname"] == subject][["studentname", "grade"]]
        subject_df = subject_df.drop_duplicates(subset=["studentname"], keep="last").set_index("studentname")["grade"]
        students[subject] = students["studentname"].map(subject_df)

    # -------------------------
    # Compute GWA via grades_service properly
    # -------------------------
    def get_student_gwa(student_id):
        df_grades = get_student_grades(student_id)
        gwa = calculate_gwa(df_grades, yearlevel=year_level_filter, semester_term=semester_filter)
        if gwa == "--":
            return None
        return gwa

    students["GWA"] = students["studentid"].apply(get_student_gwa)
    students.rename(columns={"studentremarks": "Remarks"}, inplace=True)
    students["Remarks"] = students["Remarks"].fillna("-")

    # -------------------------
    # Final Columns
    # -------------------------
    columns_order = ["studentname"] + unique_subjects + ["GWA", "Remarks"]
    students.drop(columns=["studentid"], inplace=True)
    missing_cols = [col for col in columns_order if col not in students.columns]
    if missing_cols:
        st.error(f"Missing columns: {missing_cols}")
        st.stop()

    display_df = students[columns_order]
    display_df.rename(columns={"studentname": "Name"}, inplace=True)

    # Clean GWA column to avoid pyarrow errors
    display_df["GWA"] = pd.to_numeric(display_df["GWA"], errors="coerce")

    # -------------------------
    # Checkbox Filters
    # -------------------------
    st.subheader("Additional Filters")
    col1, col2, col3 = st.columns(3)
    show_inc = col1.checkbox("Show INC")
    show_dropped = col2.checkbox("Show Dropped or Failed")
    show_missing = col3.checkbox("Show Missing Grades")

    if show_inc or show_dropped or show_missing:
        def row_matches(row):
            values = list(row[unique_subjects])
            if show_inc and any("INC" in str(v).upper() for v in values if pd.notna(v)):
                return True
            if show_dropped and any(str(v).strip().upper() in ["5.0", "DROPPED", "DROP"] for v in values if pd.notna(v)):
                return True
            if show_missing and any(pd.isna(v) or str(v).strip() == "" for v in values):
                return True
            return False

        display_df = display_df[display_df.apply(row_matches, axis=1)]

    # -------------------------
    # Final Display
    # -------------------------
    st.dataframe(display_df, use_container_width=True)
