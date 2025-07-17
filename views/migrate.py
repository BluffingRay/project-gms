import streamlit as st
import pandas as pd
from services.enrollment_service import (
    get_all_semesters,
    get_all_enrollments,
    get_curriculum_subjects,
    add_enrollment,
    update_student_status,
)

def show():

    st.set_page_config(page_title="Batch Enrollment Migration", layout="wide")
    st.title("Batch Enroll Students from One Semester to Another")

    # Fetch semesters and create dict for selection
    semesters = get_all_semesters()
    semester_options = {f"{sem['schoolyear']} {sem['term']}": sem["semesterid"] for sem in semesters}

    source_sem_key = st.selectbox("Select SOURCE Semester (where students are enrolled)", list(semester_options.keys()))
    target_sem_key = st.selectbox("Select TARGET Semester (to enroll students into)", list(semester_options.keys()))

    if source_sem_key == target_sem_key:
        st.warning("Source and Target semester cannot be the same.")
        st.stop()

    source_sem_id = semester_options[source_sem_key]
    target_sem_id = semester_options[target_sem_key]

    all_enrollments = get_all_enrollments()
    df_enrollments = pd.DataFrame(all_enrollments)

    if df_enrollments.empty:
        st.info("No enrollments found.")
        st.stop()

    # Filter enrollments for source semester and regular students only
    source_enrolled_df = df_enrollments[
        (df_enrollments["semesterid"] == source_sem_id) &
        (df_enrollments["enrollmentstatus"].str.contains("Regular"))
    ]

    if source_enrolled_df.empty:
        st.info(f"No regular enrollments found in {source_sem_key}.")
        st.stop()

    # Get unique students with their program and year level
    students_in_source = source_enrolled_df[["studentid", "studentname", "program", "yearlevel"]].drop_duplicates()

    # Add Program filter
    programs = ["All"] + sorted(students_in_source["program"].dropna().unique().tolist())
    selected_program = st.selectbox("Filter by Program", programs)

    if selected_program != "All":
        students_in_source = students_in_source[students_in_source["program"] == selected_program]

    # Add Year Level filter
    year_levels = ["All"] + sorted(students_in_source["yearlevel"].dropna().unique().tolist())
    selected_year = st.selectbox("Filter by Year Level", year_levels)

    if selected_year != "All":
        students_in_source = students_in_source[students_in_source["yearlevel"] == selected_year]

    if students_in_source.empty:
        st.info("No students match the selected filters.")
        st.stop()
        
    # Display students as a multiselect for migration
    student_names = sorted(students_in_source["studentname"].tolist())  # ✅ Sort alphabetically
    students_to_migrate = st.multiselect(
        "Select students to migrate to target semester",
        options=student_names,
        default=student_names  # preselect all by default
    )

    if not students_to_migrate:
        st.warning("Please select at least one student to migrate.")
        st.stop()

    st.markdown(f"**Selected {len(students_to_migrate)} students to migrate from {source_sem_key} to {target_sem_key}.**")

    if st.button("🚀 Migrate Selected Students to Target Semester"):
        success_count = 0
        skipped_students = []
        failed_students = []

        all_enrollments_latest = get_all_enrollments()
        df_enrollments_latest = pd.DataFrame(all_enrollments_latest)

        for student_name in students_to_migrate:
            student = students_in_source[students_in_source["studentname"] == student_name].iloc[0]
            student_id = student["studentid"]
            program = student["program"]
            yearlevel = student["yearlevel"]

            # Check if already enrolled in target semester
            already_enrolled = df_enrollments_latest[
                (df_enrollments_latest["studentid"] == student_id) &
                (df_enrollments_latest["semesterid"] == target_sem_id)
            ]
            if not already_enrolled.empty:
                skipped_students.append(student_name)
                continue

            # Get subjects for target semester (using term part of semester key)
            term = target_sem_key.split(" ", 1)[1]
            subjects = get_curriculum_subjects(program, yearlevel, term)
            if not subjects:
                failed_students.append((student_name, "No subjects found for program/year/term in target semester"))
                continue

            # Enroll in all subjects
            try:
                for subject in subjects:
                    add_enrollment(
                        student_id=student_id,
                        curriculum_id=subject["id"],
                        semester_id=target_sem_id,
                        enrollment_status="Enrolled - Regular",
                        remarks="Regular"
                    )
                update_student_status(
                    student_id=student_id,
                    program=program,
                    yearlevel=yearlevel,
                    remarks="Enrolled",
                    status="Regular"
                )
                success_count += 1
            except Exception as e:
                failed_students.append((student_name, f"Enrollment error: {str(e)}"))

        if success_count > 0:
            st.success(f"✅ Successfully migrated {success_count} students to {target_sem_key}.")
        if skipped_students:
            st.warning(f"⚠️ Skipped (already enrolled): {', '.join(skipped_students)}")
        if failed_students:
            st.error("❌ Enrollment failed for:")
            for name, error in failed_students:
                st.write(f"- {name}: {error}")
