import streamlit as st
import pandas as pd
from services.enrollment_service import get_all_regular_enrollments
from services.grades_service import get_student_gwa_summary

def show():


    st.set_page_config(page_title="Student GWA Overview", layout="wide")
    st.title("Student GWA Overview")

    # -------------------------
    # Fetch Data
    # -------------------------
    df = pd.DataFrame(get_all_regular_enrollments())

    if df.empty:
        st.warning("No data available.")
        st.stop()

    # -------------------------
    # Filters
    # -------------------------
    school_years = sorted(df["schoolyear"].dropna().unique(), reverse=True)
    programs = sorted(df["program"].dropna().unique())
    year_levels = ["1st Year", "2nd Year", "3rd Year", "4th Year"]

    col1, col2, col3 = st.columns(3)
    school_year_filter = col1.selectbox("School Year Batch", school_years, index=0)
    program_filter = col2.selectbox("Program", programs, index=0)
    year_filter = col3.selectbox("Year Level", ["All"] + year_levels)

    filtered_df = df[
        (df["schoolyear"] == school_year_filter) &
        (df["program"] == program_filter)
    ]

    if year_filter != "All":
        filtered_df = filtered_df[filtered_df["yearlevel"] == year_filter]

    # -------------------------
    # Build Table via GWA Summary Service
    # -------------------------
    gwa_table = []

    student_names = filtered_df[["studentid", "studentname"]].drop_duplicates().values.tolist()

    for student_id, student_name in student_names:
        gwa_summary = get_student_gwa_summary(student_id)

        gwa_row = {"Name": student_name}
        for year in year_levels:
            for sem in ["1st Semester", "2nd Semester"]:
                gwa_row[f"{year} {sem}"] = gwa_summary.get(f"{year} {sem}", "--")
            gwa_row[f"{year} Overall"] = gwa_summary.get(f"{year} Overall", "--")

        gwa_row["Overall"] = gwa_summary.get("Overall", "--")
        gwa_table.append(gwa_row)

    gwa_df = pd.DataFrame(gwa_table)

    if gwa_df.empty:
        st.warning("No records found for the selected filters.")
        st.stop()

    gwa_df = gwa_df.sort_values(by="Name").reset_index(drop=True)

    # -------------------------
    # Styling Highlights
    # -------------------------
    def highlight_overall(s):
        return ['background-color: #fffbcc' if 'Overall' in c else '' for c in s.index]

    styled_df = gwa_df.style.apply(highlight_overall, axis=1)

    # -------------------------
    # Display
    # -------------------------
    st.dataframe(styled_df, use_container_width=True)
