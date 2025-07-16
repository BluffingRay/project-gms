import streamlit as st
import pandas as pd
from services.student_service import update_student_info
from services.grades_service import upsert_grade
from services.semester_service import get_all_semesters
from services.irregular_service import (
    get_irregular_students,
    get_irregular_subjects
)
from database_client import supabase

st.set_page_config(page_title="Irregular Students", layout="wide")

# -------------------------
# Session State
# -------------------------
if 'selected_student_id' not in st.session_state:
    st.session_state.selected_student_id = None
if 'selected_semester' not in st.session_state:
    st.session_state.selected_semester = None

# -------------------------
# Load Irregular Students
# -------------------------
students = get_irregular_students()
student_df = pd.DataFrame(students)
student_df["fullname"] = student_df["studentname"]
student_df = student_df.sort_values(by="fullname")
name_to_id = {row['fullname']: row['studentid'] for _, row in student_df.iterrows()}

col1, col2 = st.columns([6, 1])
with col1:
    selected_name = st.selectbox("Select Irregular Student", list(name_to_id.keys()))
with col2:
    if st.button("🔍 Load"):
        st.session_state.selected_student_id = name_to_id[selected_name]
        st.rerun()

if not st.session_state.selected_student_id:
    st.stop()

# -------------------------
# Load Selected Student
# -------------------------
selected_id = st.session_state.selected_student_id
selected_student = student_df[student_df['studentid'] == selected_id].iloc[0]
st.markdown(f"<h2 style='text-align:center;'>{selected_student['fullname']}</h2>", unsafe_allow_html=True)

# -------------------------
# Notice Board
# -------------------------
dl_applicable = selected_student.get("dl_applicable", False)
laude_applicable = selected_student.get("laude_applicable", False)

notice_content = f"""
**Academic Eligibility**
- DL Applicable: {'✅ Yes' if dl_applicable else '❌ No'}
- Laude Applicable: {'✅ Yes' if laude_applicable else '❌ No'}

**Remarks**  
{selected_student.get("remarks") or "- No remarks available -"}
"""

st.info(notice_content.strip())

# -------------------------
# Semester Selection
# -------------------------
semesters = pd.DataFrame(get_all_semesters())
semesters["label"] = semesters["schoolyear"] + " " + semesters["term"]

sem_options = semesters["label"].tolist()
selected_sem = st.selectbox("Select Semester", sem_options)
school_year, semester_term = selected_sem.split(" ", 1)

st.session_state.selected_semester = selected_sem
semester_id = semesters[(semesters["schoolyear"] == school_year) & (semesters["term"] == semester_term)].iloc[0]["semesterid"]

# -------------------------
# Get Irregular Subjects
# -------------------------
subjects_df = pd.DataFrame(get_irregular_subjects(selected_id, school_year, semester_term))

st.header("Subject Grades")
edited_grades = {}
for index, row in subjects_df.iterrows():
    grade = row["grade"] if pd.notna(row["grade"]) else ""
    new_grade = st.text_input(f"{row['subjectname']} Grade", value=str(grade), key=f"grade_{row['curriculumid']}")
    edited_grades[row["curriculumid"]] = new_grade

# -------------------------
# Save Grades
# -------------------------
if st.button("💾 Save Grades"):
    for subject_id, grade in edited_grades.items():
        upsert_grade(enrollment_id=subject_id, grade=grade)
    st.success("Grades saved successfully!")
    st.rerun()

# -------------------------
# Edit Student Info Section
# -------------------------
st.markdown("<br><hr><br>", unsafe_allow_html=True)
col1, col2 = st.columns([2, 2])

with col1:
    st.subheader("Edit Student Information")
    updated_info = {}
    for field in ["program", "yearlevel", "status"]:
        value = selected_student.get(field, "")
        updated_info[field] = st.text_input(f"{field.capitalize()}", value=value)

    # Additional fields
    dl_value = "Yes" if selected_student.get("dl_applicable", False) else "No"
    new_dl = st.selectbox("DL Applicable", ["Yes", "No"], index=0 if dl_value == "Yes" else 1)
    updated_info["dl_applicable"] = (new_dl == "Yes")

    laude_value = "Yes" if selected_student.get("laude_applicable", False) else "No"
    new_laude = st.selectbox("Laude Applicable", ["Yes", "No"], index=0 if laude_value == "Yes" else 1)
    updated_info["laude_applicable"] = (new_laude == "Yes")

with col2:
    st.subheader("Edit Notice Board Remarks")
    new_remarks = st.text_area("Remarks / Notices", value=selected_student.get("remarks", ""), height=150)

# -------------------------
# Save Info
# -------------------------
if st.button("Update Info"):
    update_student_info(student_id=selected_id, data=updated_info | {"remarks": new_remarks})
    st.success("Student information updated!")
    st.rerun()
