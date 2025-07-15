import streamlit as st
import pandas as pd
from services.enrollment_service import (
    get_all_students,
    get_all_enrollments,
    update_student_status,
)
from services.student_service import update_student_info
from services.grades_service import upsert_grade
from database_client import supabase


st.set_page_config(page_title="Edit Student Info", layout="wide")

# -------------------------
# Search Input (Top Right)
# -------------------------
students = get_all_students()
student_df = pd.DataFrame(students)
student_names = [f"{s['firstname']} {s['lastname']}" for s in students]

col1, col2 = st.columns([6, 1])
with col2:
    selected_student_name = st.selectbox(" ", student_names, label_visibility="collapsed")

if not selected_student_name:
    st.stop()

selected_student = student_df[
    (student_df["firstname"] + " " + student_df["lastname"]) == selected_student_name
].iloc[0]

student_id = selected_student["studentid"]

# -------------------------
# Notice Board (Top)
# -------------------------
remarks_content = selected_student.get("remarks") or "- No remarks available -"
st.info(f"**Notice Board**\n\n{remarks_content.strip()}")

# -------------------------
# Centered Student Name
# -------------------------
st.markdown(
    f"<h2 style='text-align:center;'>{selected_student_name}</h2><br>",
    unsafe_allow_html=True,
)

# -------------------------
# Fetch Enrollments
# -------------------------
enrollments = pd.DataFrame(get_all_enrollments())
student_enrollments = enrollments[enrollments["studentid"] == student_id]

# -------------------------
# Semester Selection for Editing Grades
# -------------------------
available_semesters = (
    student_enrollments[["schoolyear", "semester_term"]]
    .drop_duplicates()
    .apply(lambda row: f"{row['schoolyear']} {row['semester_term']}", axis=1)
    .tolist()
)

if not available_semesters:
    st.warning("No enrollments found for this student.")
    st.stop()

selected_semester = st.selectbox("Select Semester to Edit Grades", available_semesters)
school_year, semester_term = selected_semester.split(" ", 1)

# -------------------------
# Functions
# -------------------------
def compute_gwa(df, term, schoolyear):
    grades = df[
        (df["semester_term"] == term) &
        (df["schoolyear"] == schoolyear)
    ]["grade"].fillna("").astype(str)

    numeric_grades = pd.to_numeric(grades, errors="coerce").dropna()
    valid_grades = numeric_grades[(numeric_grades >= 1.0) & (numeric_grades <= 5.0)]

    return round(valid_grades.mean(), 2) if not valid_grades.empty else "--"


def compute_overall_gwa(df):
    grades = df["grade"].fillna("").astype(str)
    numeric_grades = pd.to_numeric(grades, errors="coerce").dropna()
    valid_grades = numeric_grades[(numeric_grades >= 1.0) & (numeric_grades <= 5.0)]
    return round(valid_grades.mean(), 2) if not valid_grades.empty else "--"


# -------------------------
# KPIs Section (removed selected semester KPI)
# -------------------------
gwa_selected = compute_gwa(student_enrollments, semester_term, school_year)
gwa_overall = compute_overall_gwa(student_enrollments)

st.markdown("""
<style>
.kpi-value {
    font-weight: bold;
    font-size: 1.2em;
}
</style>
""", unsafe_allow_html=True)

kpi1, kpi2, kpi3, kpi4 = st.columns(4)
with kpi1:
    st.markdown("Year & Program")
    st.markdown(f"<div class='kpi-value'>{selected_student['yearlevel']} / {selected_student['program']}</div>", unsafe_allow_html=True)

with kpi2:
    st.markdown("Latest Enrollment")
    latest_enrollment = student_enrollments.sort_values("schoolyear", ascending=False).head(1)
    latest_year = latest_enrollment["schoolyear"].values[0] if not latest_enrollment.empty else "-"
    latest_term = latest_enrollment["semester_term"].values[0] if not latest_enrollment.empty else "-"
    st.markdown(f"<div class='kpi-value'>{latest_year} {latest_term}</div>", unsafe_allow_html=True)

with kpi3:
    st.markdown("Selected Sem GWA")
    st.markdown(f"<div class='kpi-value'>{gwa_selected}</div>", unsafe_allow_html=True)

with kpi4:
    st.markdown("Overall GWA")
    st.markdown(f"<div class='kpi-value'>{gwa_overall}</div>", unsafe_allow_html=True)

st.markdown("<br>", unsafe_allow_html=True)


# -------------------------
# Tabs: Grades / Edit Info / Edit Notice Board
# -------------------------
tab1, tab2, tab3 = st.tabs(["📚 Grades", "📝 Edit Info", "📌 Edit Notice Board"])

with tab1:
    st.header("Current Enrollments & Grades")
    st.markdown("<br>", unsafe_allow_html=True)

    current_subjects = student_enrollments[
        (student_enrollments["schoolyear"] == school_year) &
        (student_enrollments["semester_term"] == semester_term)
    ][["subjectname", "grade", "enrollmentid"]].reset_index(drop=True)

    edited_grades = {}

    for index, row in current_subjects.iterrows():
        subject = row["subjectname"]
        grade = row["grade"] if pd.notna(row["grade"]) else ""
        new_grade = st.text_input(f"{subject} Grade", value=str(grade))
        edited_grades[row["enrollmentid"]] = new_grade


with tab2:
    st.header("Edit Student Information")
    st.markdown("<br>", unsafe_allow_html=True)

    updated_info = {}
    for col in selected_student.index:
        if col in ["studentid", "remarks"]:  # Skip primary key and remarks
            continue
        value = selected_student[col] if pd.notna(selected_student[col]) else ""

        if col.lower() == "dateofbirth":
            # Ensure it's parsed as date if it's a string
            try:
                value = pd.to_datetime(value).date() if value else None
            except:
                value = None

            updated_info[col] = st.date_input(
                "Date of Birth",
                value=value if value else pd.to_datetime("2000-01-01"),
                format="YYYY-MM-DD"
            ).strftime("%Y-%m-%d")
        else:
            updated_info[col] = st.text_input(f"{col.capitalize()}", value=str(value))


with tab3:
    st.header("Edit Notice Board Remarks")
    st.markdown("<br>", unsafe_allow_html=True)
    new_remarks = st.text_area("Remarks / Notices", value=selected_student.get("remarks", ""), height=150)

# -------------------------
# Save & Delete Buttons
# -------------------------
st.markdown("<br><hr><br>", unsafe_allow_html=True)
col1, col2 = st.columns(2)

with col1:
    if st.button("💾 Save Changes"):
        # Update Student Info (dynamic columns)
        update_student_info(
            student_id=student_id,
            data=updated_info | {"remarks": new_remarks}
        )
        # Update Grades
        for enrollment_id, grade in edited_grades.items():
            upsert_grade(enrollment_id=enrollment_id, grade=grade)
        st.success("✅ Changes Saved!")

with col2:
    if st.button("🗑️ Delete Student"):
        supabase.table("students").delete().eq("studentid", student_id).execute()
        st.success(f"Deleted student: {selected_student_name}")
        st.rerun()
