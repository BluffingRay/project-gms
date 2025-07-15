import streamlit as st
import pandas as pd
from services.enrollment_service import (
    get_all_students,
    get_all_semesters,
    get_curriculum_subjects,
    add_enrollment,
    update_student_status,
    get_all_enrollments,
    delete_enrollment,
    delete_all_enrollments_for_student_semester,
)


st.set_page_config(page_title="Enrollment Management", layout="wide")
st.title("Enrollment Management")

tab1, tab2, tab3 = st.tabs(["➕ Enroll Student", "📋 View Enrollments", "🗑️ Delete Enrollments"])

# -------------------------
# Enroll Student
# -------------------------
with tab1:
    st.header("Enroll Student (Regular Only)")

    students = get_all_students()
    semesters = get_all_semesters()

    # Exclude Dropped and Graduated students
    filtered_students = [s for s in students if s.get('enrollmentstatus') not in ['Dropped', 'Graduated']]

    student_options = {f"{s['firstname']} {s['lastname']}": s["studentid"] for s in filtered_students}
    semester_options = {f"{sem['schoolyear']} {sem['term']}": sem["semesterid"] for sem in semesters}

    student_name = st.selectbox("Select Student", list(student_options.keys()))
    enrollment_type = st.radio("Enrollment Type", ["Regular", "Irregular (coming soon)"])

    if enrollment_type == "Regular":
        program = st.selectbox("Program", ["JD", "BSED-English", "BSED-Math", "BSCS"])
        year_level = st.selectbox("Year Level", ["1st Year", "2nd Year", "3rd Year", "4th Year"])

        semester_key = st.selectbox("Semester for Record", list(semester_options.keys()))
        semester_id = semester_options.get(semester_key)
        school_year, term = semester_key.split(" ", 1)
        st.write(semester_id)

        if st.button("🚀 Enroll to Subjects"):
            subjects = subjects = get_curriculum_subjects(program, year_level, term)

            if subjects:
                for subject in subjects:
                    add_enrollment(
                        student_id=student_options[student_name],
                        curriculum_id=subject["id"],
                        semester_id=semester_id
                    )
                    # Update the student to latest enrollment info
                    update_student_status(
                        student_id=student_options[student_name],
                        program=program,
                        yearlevel=year_level,
                        remarks="Enrolled"
                    )

                st.success(f"{student_name} enrolled in all {program} {year_level} {term} subjects.")
                st.rerun()
            else:
                st.warning("No subjects found for this Program / Year / Term.")


# -------------------------
# View Enrollments
# -------------------------
with tab2:
    st.header("All Enrollments")

    enrollments = get_all_enrollments()
    if enrollments:
        df = pd.DataFrame(enrollments)
        df.rename(columns={
            "studentname": "Student Name",
            "program": "Program",
            "yearlevel": "Year Level",
            "semester_term": "Semester Term",  # ✅ Corrected here
            "subjectcode": "Subject Code",
            "subjectname": "Subject Name",
            "schoolyear": "School Year",
            "enrollmentdate": "Enrollment Date",
            "enrollmentstatus": "Status"
        }, inplace=True)

        col1, col2, col3, col4 = st.columns(4)
        programs = ["All"] + sorted(df["Program"].unique().tolist())
        years = ["All"] + sorted(df["Year Level"].unique().tolist())
        school_years = ["All"] + sorted(df["School Year"].unique().tolist())
        terms = ["All"] + sorted(df["Semester Term"].unique().tolist())  # ✅ Corrected here

        selected_program = col1.selectbox("Program", programs)
        selected_year = col2.selectbox("Year Level", years)
        selected_school_year = col3.selectbox("School Year", school_years)
        selected_term = col4.selectbox("Semester Term", terms)

        if selected_program != "All":
            df = df[df["Program"] == selected_program]
        if selected_year != "All":
            df = df[df["Year Level"] == selected_year]
        if selected_school_year != "All":
            df = df[df["School Year"] == selected_school_year]
        if selected_term != "All":
            df = df[df["Semester Term"] == selected_term]  # ✅ Corrected here

        st.dataframe(
            df[
                [
                    "Student Name",
                    "Program",
                    "Year Level",
                    "Semester Term",  # ✅ Corrected here
                    "Subject Code",
                    "Subject Name",
                    "School Year",
                    "Enrollment Date",
                    "Status"
                ]
            ],
            use_container_width=True,
        )
    else:
        st.info("No enrollments found.")


# -------------------------
# Delete Enrollments
# -------------------------
with tab3:
    st.header("Delete Enrollment(s)")

    enrollments = get_all_enrollments()
    if enrollments:
        df = pd.DataFrame(enrollments)
        df.rename(columns={
            "studentname": "Student Name",
            "program": "Program",
            "yearlevel": "Year Level",
            "semester_term": "Semester Term",  # ✅ Corrected here
            "subjectcode": "Subject Code",
            "subjectname": "Subject Name",
            "schoolyear": "School Year",
            "enrollmentdate": "Enrollment Date",
            "enrollmentstatus": "Status",
            "enrollmentid": "Enrollment ID"
        }, inplace=True)

        student_options_dict = {f"{s['firstname']} {s['lastname']}": s["studentid"] for s in filtered_students}
        student_options_list = sorted(student_options_dict.keys())
        selected_student = st.selectbox("Select Student", student_options_list)

        semesters = df[df["Student Name"] == selected_student][["School Year", "Semester Term"]]
        semester_keys = semesters.apply(lambda row: f"{row['School Year']} {row['Semester Term']}", axis=1).unique().tolist()
        selected_semester_key = st.selectbox("Select Semester", semester_keys)

        semester_id = semester_options.get(selected_semester_key)

        semester_filtered_df = df[
            (df["Student Name"] == selected_student)
            & (df["School Year"] + " " + df["Semester Term"] == selected_semester_key)
        ]


        st.subheader("Enrollments for Deletion (Preview)")
        st.dataframe(
            semester_filtered_df[
                ["Subject Code", "Subject Name", "Enrollment Date", "Status"]
            ],
            use_container_width=True,
        )

        delete_options = ["Delete All Enrollments for this Semester", "Delete a Single Subject"]
        delete_choice = st.radio("Delete Options", delete_options)

        # Session states for confirmations
        if "confirm_delete_all" not in st.session_state:
            st.session_state.confirm_delete_all = False
        if "confirm_delete_single" not in st.session_state:
            st.session_state.confirm_delete_single = False

        if delete_choice == "Delete All Enrollments for this Semester":
            if st.button("❗ Delete All for this Semester"):
                st.session_state.confirm_delete_all = True

            if st.session_state.confirm_delete_all:
                st.warning(f"Are you sure you want to delete ALL enrollments for {selected_student} in {selected_semester_key}?")
                col1, col2 = st.columns(2)
                with col1:
                    if st.button("✅ Yes, Confirm Delete"):
                        student_id = student_options_dict[selected_student]

                        semester_id = semester_options.get(selected_semester_key)

                        delete_all_enrollments_for_student_semester(
                            student_id, semester_id
                        )

                        st.success(f"All enrollments for {selected_student} in {selected_semester_key} deleted.")
                        st.session_state.confirm_delete_all = False
                        st.rerun()
                with col2:
                    if st.button("❌ Cancel"):
                        st.session_state.confirm_delete_all = False
                        st.rerun()

        else:
            enrollments_to_delete = {
                f"{row['Subject Code']} - {row['Subject Name']}": row["Enrollment ID"]
                for _, row in semester_filtered_df.iterrows()
            }
            selected_subject = st.selectbox("Select Subject to Delete", list(enrollments_to_delete.keys()))

            if st.button(f"❗ Delete {selected_subject}"):
                st.session_state.confirm_delete_single = True

            if st.session_state.confirm_delete_single:
                st.warning(f"Are you sure you want to delete {selected_subject} for {selected_student}?")
                col1, col2 = st.columns(2)
                with col1:
                    if st.button("✅ Yes, Confirm Delete"):
                        delete_enrollment(enrollments_to_delete[selected_subject])
                        st.success(f"{selected_subject} for {selected_student} deleted.")
                        st.session_state.confirm_delete_single = False
                        st.rerun()
                with col2:
                    if st.button("❌ Cancel"):
                        st.session_state.confirm_delete_single = False
                        st.rerun()
    else:
        st.info("No enrollments found to delete.")
