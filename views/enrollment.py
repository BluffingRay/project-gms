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
from services.program_service import get_all_programs

def show():
        
    st.set_page_config(page_title="Enrollment Management", layout="wide")
    st.title("Enrollment Management")

    tab1, tab2, tab3 = st.tabs(["➕ Enroll Student", "📋 View Enrollments", "🗑️ Delete Enrollments"])

    # Fetch programs for dropdown
    programs_data = get_all_programs()
    program_options = [p["program_name"] for p in programs_data] if programs_data else []

    # -------------------------
    # Enroll Student
    # -------------------------
    with tab1:
        st.header("Enroll Student")

        students = get_all_students()
        semesters = get_all_semesters()

        # Exclude Dropped and Graduated students
        filtered_students = [s for s in students if s.get('enrollmentstatus') not in ['Dropped', 'Graduated']]

        student_options = {f"{s['firstname']} {s['lastname']}": s["studentid"] for s in filtered_students}
        semester_options = {f"{sem['schoolyear']} {sem['term']}": sem["semesterid"] for sem in semesters}

        student_name = st.selectbox("Select Student", list(student_options.keys()))
        enrollment_type = st.radio("Enrollment Type", ["Regular", "Irregular"])

        selected_student = next((s for s in filtered_students if f"{s['firstname']} {s['lastname']}" == student_name), None)
        if selected_student:
            current_program = selected_student.get('program', 'Not Set')
            current_year = selected_student.get('yearlevel', 'Not Set')
            st.info(f"Current Program: **{current_program}** | Current Year Level: **{current_year}**")

        if enrollment_type == "Regular":
            st.subheader("Regular Enrollment")
            st.write("📋 Automatically enrolls student to all subjects for their program/year/term")

            program = st.selectbox("Program", program_options) if program_options else st.text_input("Program (no programs found)")
            year_level = st.selectbox("Year Level", ["1st Year", "2nd Year", "3rd Year", "4th Year", "Onward"])

            semester_key = st.selectbox("Semester for Record", list(semester_options.keys()))
            semester_id = semester_options.get(semester_key)
            school_year, term = semester_key.split(" ", 1)

            if st.button("🚀 Enroll to All Subjects (Regular)"):
                all_enrollments = get_all_enrollments()
                df_enrollments = pd.DataFrame(all_enrollments)

                student_id = student_options[student_name]
                already_enrolled = df_enrollments[
                    (df_enrollments["studentid"] == student_id) &
                    (df_enrollments["schoolyear"] == school_year) &
                    (df_enrollments["semester_term"] == term)
                ]

                if not already_enrolled.empty:
                    st.warning(f"{student_name} is already enrolled for {school_year} {term}.")
                else:
                    subjects = get_curriculum_subjects(program, year_level, term)

                    if subjects:
                        for subject in subjects:
                            add_enrollment(
                                student_id=student_id,
                                curriculum_id=subject["id"],
                                semester_id=semester_id,
                                enrollment_status= "Enrolled - Regular",
                                remarks="Regular"
                            )
                        update_student_status(
                            student_id=student_id,
                            program=program,
                            yearlevel=year_level,
                            remarks="Enrolled ",
                            status="Regular"
                        )
                        st.success(f"✅ {student_name} enrolled in all {program} {year_level} {term} subjects as **Regular** student.")
                        st.rerun()
                    else:
                        st.warning("No subjects found for this Program / Year / Term.")

        elif enrollment_type == "Irregular":  # Irregular Enrollment
            st.subheader("Irregular Enrollment")
            st.write("📝 Select available subjects for the student (regardless of semester)")

            # Lock Semester for Record
            if "record_semester_key" not in st.session_state:
                with st.form("semester_record_form"):
                    semester_key = st.selectbox(
                        "Semester for Record (for recording purposes)", 
                        list(semester_options.keys())
                    )
                    confirm = st.form_submit_button("Confirm Semester Selection")
                    if confirm:
                        st.session_state["record_semester_key"] = semester_key
                        st.session_state["selected_subjects"] = set()
                        school_year, term = semester_key.split(" ", 1)
                        st.session_state["record_school_year"] = school_year
                        st.session_state["record_term"] = term
                        st.rerun()

            if "record_semester_key" in st.session_state:
                semester_key = st.session_state["record_semester_key"]
                school_year = st.session_state["record_school_year"]
                term = st.session_state["record_term"]
                semester_id = semester_options.get(semester_key)

                st.success(f"Locked Semester: {semester_key}")
                if st.button("🔄 Reset Semester Selection"):
                    del st.session_state["record_semester_key"]
                    del st.session_state["record_school_year"]
                    del st.session_state["record_term"]
                    del st.session_state["selected_subjects"]
                    st.rerun()

                # Program selection
                program = st.selectbox(
                    "Filter Subjects by Program",
                    program_options,
                    help="Select a program to view all its available subjects"
                )

                # Load all subjects once (if not cached yet)
                if f"all_subjects_{program}" not in st.session_state:
                    all_subjects = []
                    year_levels = ["1st Year", "2nd Year", "3rd Year", "4th Year"]
                    terms = ["1st Semester", "2nd Semester", "Summer"]

                    for year_level in year_levels:
                        for sub_term in terms:
                            subjects = get_curriculum_subjects(program, year_level, sub_term)
                            if subjects:
                                for subject in subjects:
                                    subject["year_level"] = year_level
                                    subject["term"] = sub_term
                                    all_subjects.append(subject)
                    st.session_state[f"all_subjects_{program}"] = all_subjects

                all_subjects = st.session_state[f"all_subjects_{program}"]

                # Search and Select
                st.subheader(f"Available Subjects for {program}")
                search_term = st.text_input("🔍 Search Subjects", "")

                cols = st.columns(2)
                col_index = 0

                for subject in all_subjects:
                    if search_term:
                        if search_term.lower() not in subject["name"].lower() and \
                        search_term.lower() not in subject["code"].lower():
                            continue
                    with cols[col_index]:
                        key = f"select_{subject['id']}"
                        checked = st.checkbox(
                            f"{subject['code']} - {subject['name']}",
                            key=key,
                            value=subject['id'] in st.session_state["selected_subjects"],
                            help=f"Year: {subject['year_level']} | Term: {subject['term']} | Units: {subject.get('units', 'N/A')}"
                        )
                        if checked:
                            st.session_state["selected_subjects"].add(subject['id'])
                        else:
                            st.session_state["selected_subjects"].discard(subject['id'])

                        st.caption(f"Year: {subject['year_level']} | Term: {subject['term']} | Units: {subject.get('units', 'N/A')}")
                    col_index = (col_index + 1) % 2

                # Selected Subjects Summary
                if st.session_state["selected_subjects"]:
                    st.divider()
                    st.subheader("Selected Subjects")
                    selected_subjects = [s for s in all_subjects if s["id"] in st.session_state["selected_subjects"]]

                    year_groups = {}
                    for sub in selected_subjects:
                        group_key = f"{sub['year_level']} ({sub['term']})"
                        if group_key not in year_groups:
                            year_groups[group_key] = []
                        year_groups[group_key].append(sub)

                    for group, subjects in year_groups.items():
                        st.markdown(f"**{group}**")
                        for sub in subjects:
                            st.write(f"- {sub['code']}: {sub['name']}")

                # Record Information
                st.divider()
                st.subheader("Student Record Information")
                col1, col2 = st.columns(2)
                with col1:
                    record_program = st.selectbox(
                        "Program to Record",
                        program_options,
                        index=program_options.index(program) if program in program_options else 0,
                        help="This will be recorded as the student's official program"
                    )
                with col2:
                    record_year = st.selectbox(
                        "Year Level to Record",
                        ["1st Year", "2nd Year", "3rd Year", "4th Year", "Onward"],
                        help="This will be recorded as the student's official year level"
                    )

                # Enrollment
                if st.button("🚀 Enroll to Selected Subjects (Irregular)"):
                    if not st.session_state["selected_subjects"]:
                        st.warning("Please select at least one subject to enroll.")
                        st.stop()

                    student_id = student_options[student_name]
                    all_enrollments = get_all_enrollments()
                    df_enrollments = pd.DataFrame(all_enrollments)

                    already_enrolled = df_enrollments[
                        (df_enrollments["studentid"] == student_id) &
                        (df_enrollments["schoolyear"] == school_year) &
                        (df_enrollments["semester_term"] == term)
                    ]

                    if not already_enrolled.empty:
                        st.warning(f"{student_name} already has enrollments recorded for {school_year} {term}.")
                    else:
                        success_count = 0
                        for subject in selected_subjects:
                            try:
                                add_enrollment(
                                    student_id=student_id,
                                    curriculum_id=subject["id"],
                                    semester_id=semester_id,
                                    enrollment_status="Enrolled - Irregular",
                                    remarks="Irregular"
                                )
                                success_count += 1
                            except Exception as e:
                                st.error(f"Failed to enroll in {subject['code']}: {str(e)}")

                        if success_count > 0:
                            update_student_status(
                                student_id=student_id,
                                program=record_program,
                                yearlevel=record_year,
                                remarks="Enrolled - Irregular",
                                status="Irregular"
                            )
                            st.success(f"✅ {student_name} enrolled in {success_count} subjects as **Irregular** student.")
                            del st.session_state["selected_subjects"]
                            del st.session_state["record_semester_key"]
                            del st.session_state["record_school_year"]
                            del st.session_state["record_term"]
                            st.rerun()



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
                "semester_term": "Semester Term",
                "subjectcode": "Subject Code",
                "subjectname": "Subject Name",
                "schoolyear": "School Year",
                "enrollmentdate": "Enrollment Date",
                "enrollmentstatus": "Status"
            }, inplace=True)

            df["Type"] = df["Status"].apply(lambda x: "🔄 Irregular" if x == "Enrolled - Irregular" else "📋 Regular")

            col1, col2, col3, col4, col5 = st.columns(5)
            programs = ["All"] + sorted(df["Program"].unique().tolist())
            years = ["All"] + sorted(df["Year Level"].unique().tolist())
            school_years = ["All"] + sorted(df["School Year"].unique().tolist())
            terms = ["All"] + sorted(df["Semester Term"].unique().tolist())
            statuses = ["All"] + sorted(df["Status"].unique().tolist())

            selected_program = col1.selectbox("Program", programs)
            selected_year = col2.selectbox("Year Level", years)
            selected_school_year = col3.selectbox("School Year", school_years)
            selected_term = col4.selectbox("Semester Term", terms)
            selected_status = col5.selectbox("Status", statuses)

            if selected_program != "All":
                df = df[df["Program"] == selected_program]
            if selected_year != "All":
                df = df[df["Year Level"] == selected_year]
            if selected_school_year != "All":
                df = df[df["School Year"] == selected_school_year]
            if selected_term != "All":
                df = df[df["Semester Term"] == selected_term]
            if selected_status != "All":
                df = df[df["Status"] == selected_status]

            st.dataframe(
                df[
                    [
                        "Student Name",
                        "Type",
                        "Program",
                        "Year Level",
                        "Semester Term",
                        "Subject Code",
                        "Subject Name",
                        "School Year",
                        "Enrollment Date"
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
                "semester_term": "Semester Term",
                "subjectcode": "Subject Code",
                "subjectname": "Subject Name",
                "schoolyear": "School Year",
                "enrollmentdate": "Enrollment Date",
                "enrollmentstatus": "Status",
                "enrollmentid": "Enrollment ID"
            }, inplace=True)

            filtered_students = [s for s in students if s.get('enrollmentstatus') not in ['Dropped', 'Graduated']]
            student_options_dict = {f"{s['firstname']} {s['lastname']}": s["studentid"] for s in filtered_students}
            student_options_list = sorted(student_options_dict.keys())
            selected_student = st.selectbox("Select Student", student_options_list)

            semesters = df[df["Student Name"] == selected_student][["School Year", "Semester Term"]]
            semester_keys = semesters.apply(lambda row: f"{row['School Year']} {row['Semester Term']}", axis=1).unique().tolist()

            if semester_keys:
                selected_semester_key = st.selectbox("Select Semester", semester_keys)
                semester_id = semester_options.get(selected_semester_key)

                semester_filtered_df = df[
                    (df["Student Name"] == selected_student)
                    & (df["School Year"] + " " + df["Semester Term"] == selected_semester_key)
                ]

                enrollment_type = semester_filtered_df["Status"].iloc[0] if not semester_filtered_df.empty else "Unknown"
                st.info(f"Enrollment Type: **{enrollment_type}**")

                st.subheader("Enrollments for Deletion (Preview)")
                st.dataframe(
                    semester_filtered_df[
                        ["Subject Code", "Subject Name", "Enrollment Date", "Status"]
                    ],
                    use_container_width=True,
                )

                delete_options = ["Delete All Enrollments for this Semester", "Delete a Single Subject"]
                delete_choice = st.radio("Delete Options", delete_options)

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
                st.info(f"No enrollments found for {selected_student}")
        else:
            st.info("No enrollments found to delete.")
