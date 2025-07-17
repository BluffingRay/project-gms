import streamlit as st
import pandas as pd
from services.enrollment_service import (
    get_all_students,
    get_all_enrollments,
    update_student_status,
    update_enrollment_status_and_remarks
)
from services.student_service import update_student_info
from services.grades_service import upsert_grade
from services.curriculum_service import get_all_curriculum_subjects
from services.semester_service import get_all_semesters
from database_client import supabase

def show():

    st.set_page_config(page_title="Edit Student Info", layout="wide")

    # -------------------------
    # Initialize Session State
    # -------------------------
    if 'selected_student_id' not in st.session_state:
        st.session_state.selected_student_id = None
    if 'selected_semester' not in st.session_state:
        st.session_state.selected_semester = None
    if 'students_cache' not in st.session_state:
        st.session_state.students_cache = None
    if 'enrollments_cache' not in st.session_state:
        st.session_state.enrollments_cache = None
    if 'last_updated' not in st.session_state:
        st.session_state.last_updated = None

    # -------------------------
    # Cache Management Functions
    # -------------------------
    def refresh_student_data():
        """Refresh cached data"""
        st.session_state.students_cache = get_all_students()
        st.session_state.enrollments_cache = get_all_enrollments()

    def get_cached_students():
        """Get students from cache or fetch if not cached"""
        if st.session_state.students_cache is None:
            refresh_student_data()
        return st.session_state.students_cache

    def get_cached_enrollments():
        """Get enrollments from cache or fetch if not cached"""
        if st.session_state.enrollments_cache is None:
            refresh_student_data()
        return st.session_state.enrollments_cache

    # -------------------------
    # Search Input (Top Right) - With Load Button
    # -------------------------
    students = get_cached_students()
    student_df = pd.DataFrame(students)
    student_df = student_df[student_df["status"].str.lower() == "regular"]
    student_df["fullname"] = student_df["firstname"] + " " + student_df["lastname"]
    student_df = student_df.sort_values(by="fullname")

    student_names = student_df["fullname"].tolist()

    # Create a mapping of names to student IDs
    name_to_id = {f"{s['firstname']} {s['lastname']}": s['studentid'] for s in students}
    id_to_name = {v: k for k, v in name_to_id.items()}

    # Get default fullname from session_state if available
    default_fullname = id_to_name.get(st.session_state.get("selected_student_id"), None)

    col1, col2 = st.columns([6, 1])

    with col1:
        selected_student_name = st.selectbox(
            " ",
            student_names,
            index=student_names.index(default_fullname) if default_fullname in student_names else 0,
            label_visibility="collapsed"
        )

    with col2:
        if st.button("🔍 Load Student"):
            if selected_student_name:
                if st.session_state.selected_student_id != name_to_id[selected_student_name]:
                    st.session_state.selected_semester = None  # Reset only when switching student
                st.session_state.selected_student_id = name_to_id[selected_student_name]
                st.rerun()

    # -------------------------
    # Stop if no student selected yet
    # -------------------------
    if not st.session_state.selected_student_id:
        st.stop()

    # -------------------------
    # Get selected student info
    # -------------------------
    student_df = student_df.set_index("studentid")
    selected_student = student_df.loc[st.session_state.selected_student_id]
    student_id = selected_student.name
    selected_student_name = selected_student["fullname"]



    # -------------------------
    # Notice Board (Top) - WITH NEW FIELDS + Dropped/INC Auto Notice
    # -------------------------

    enrollments = pd.DataFrame(get_cached_enrollments())
    student_enrollments = enrollments[enrollments["studentid"] == student_id]

    if not student_enrollments.empty:
        latest_enrollment = student_enrollments.sort_values("schoolyear", ascending=False).head(1)
        school_year = latest_enrollment["schoolyear"].values[0]
        semester_term = latest_enrollment["semester_term"].values[0]
    else:
        school_year = None
        semester_term = None


    dl_applicable = selected_student.get("dl_applicable", False)
    laude_applicable = selected_student.get("laude_applicable", False)

    notice_content = f"""
    **Academic Eligibility**
    - DL Applicable: {'✅ Yes' if dl_applicable else '❌ No'}
    - Laude Applicable: {'✅ Yes' if laude_applicable else '❌ No'}

    **Remarks**  
    {selected_student.get("remarks") or "- No remarks available -"}
    """.strip()


    # -------------------------
    # Auto-generate notice for Dropped / INC
    # -------------------------

    if school_year and semester_term:
        subjects_this_sem = student_enrollments[
            (student_enrollments["schoolyear"] == school_year) &
            (student_enrollments["semester_term"] == semester_term)
        ]

        dropped_or_inc_all = student_enrollments[
            student_enrollments["grade"]
            .astype(str)
            .str.upper()
            .str.contains("DROP|DROPPED|INC", na=False)
        ]

        if not dropped_or_inc_all.empty:
            issues = "\n".join(
                f"- {row['subjectname']} ({row['schoolyear']} {row['semester_term']}): {row['grade']}"
                for _, row in dropped_or_inc_all.iterrows()
            )
            auto_notice = f"""
            **⚠️ Issues Across All Semesters**
            The following subjects have a status of 'Dropped' or 'INC':

            {issues}
            """.strip()

            notice_content += "\n\n" + auto_notice

        st.info(notice_content.strip())


    # -------------------------
    # Centered Student Name
    # -------------------------
    st.markdown(
        f"<h2 style='text-align:center;'>{selected_student_name}</h2><br>",
        unsafe_allow_html=True,
    )

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

    # Find the index of the previously selected semester
    default_semester_index = 0
    if st.session_state.selected_semester and st.session_state.selected_semester in available_semesters:
        default_semester_index = available_semesters.index(st.session_state.selected_semester)

    selected_semester = st.selectbox(
        "Select Semester to Edit Grades", 
        available_semesters,
        key="selected_semester"
    )

    if not selected_semester:
        st.warning("Please select a semester.")
        st.stop()

    school_year, semester_term = selected_semester.split(" ", 1)

    # Standardize semester term to match the gwa_summary keys
    semester_term_map = {
        "1st Semester": "1st Sem",
        "2nd Semester": "2nd Sem",
        "1st Sem": "1st Sem",
        "2nd Sem": "2nd Sem",
    }
    semester_term_short = semester_term_map.get(semester_term.strip(), semester_term.strip())

    selected_semester_key = f"{selected_student['yearlevel']} {semester_term_short}"

    curriculum_df = pd.DataFrame(get_all_curriculum_subjects())

    # Make sure both are the same type
    student_enrollments["curriculumid"] = student_enrollments["curriculumid"].astype(str)
    curriculum_df["id"] = curriculum_df["id"].astype(str)

    # Merge using curriculumid
    student_enrollments = pd.merge(
        student_enrollments,
        curriculum_df[["id", "units"]].rename(columns={"id": "curriculumid"}),
        on="curriculumid",
        how="left"
    )


    # -------------------------
    # GWA from Services
    # -------------------------
    from services.grades_service import get_student_gwa_summary

    gwa_summary = get_student_gwa_summary(student_id)

    # Format semester key same as in your service
    selected_semester_key = f"{selected_student['yearlevel']} {semester_term}"
    gwa_selected = gwa_summary.get(selected_semester_key) or "--"
    gwa_overall = gwa_summary.get("Overall", "--")


    # -------------------------
    # KPIs Section (removed selected semester KPI)
    # -------------------------


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

        numeric_grades = [str(x) for x in [1, 1.25, 1.5, 1.75, 2, 2.25, 2.5, 2.75, 3]]
        remarks_grades = ["INC", "Dropped", "FAILED"]
        allowed_grades = [""] + numeric_grades + remarks_grades  # "" for 'No Grade Yet'

        for index, row in current_subjects.iterrows():
            subject = row["subjectname"]
            grade = str(row["grade"]).strip() if pd.notna(row["grade"]) else ""

            # Default index handling
            default_index = allowed_grades.index(grade) if grade in allowed_grades else 0

            new_grade = st.selectbox(
                f"{subject} Grade",
                options=allowed_grades,
                index=default_index,
                key=f"{row['enrollmentid']}"
            )
            edited_grades[row["enrollmentid"]] = new_grade


    with tab2:
        st.header("Edit Student Information")
        st.markdown("<br>", unsafe_allow_html=True)

        updated_info = {}
        new_status = selected_student.get("status", "")

        for col in selected_student.index:
            if col in ["studentid", "remarks", "enrollmentstatus", "fullname"]:  # Skip primary key and remarks
                continue

            value = selected_student[col] if pd.notna(selected_student[col]) else ""

            if col.lower() == "dateofbirth":
                try:
                    value = pd.to_datetime(value).date() if value else None
                except:
                    value = None

                updated_info[col] = st.date_input(
                    "Date of Birth",
                    value=value if value else pd.to_datetime("2000-01-01"),
                    format="YYYY-MM-DD"
                ).strftime("%Y-%m-%d")

            elif col == "dl_applicable":
                dl_value = "Yes" if value else "No"
                new_dl = st.selectbox("DL Applicable", ["Yes", "No"], index=0 if dl_value == "Yes" else 1)
                updated_info[col] = (new_dl == "Yes")

            elif col == "laude_applicable":
                laude_value = "Yes" if value else "No"
                new_laude = st.selectbox("Laude Applicable", ["Yes", "No"], index=0 if laude_value == "Yes" else 1)
                updated_info[col] = (new_laude == "Yes")

            elif col == "status":
                new_status = st.selectbox(
                    "Status",
                    options=["Regular", "Irregular"],
                    index=0 if str(value) == "Regular" else 1
                )
                updated_info[col] = new_status

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
    col1, col2 = st.columns([3, 1])

    # -------------------------
    # Update Enrollments on Save
    # -------------------------
    with col1:
        if st.button("💾 Save Changes"):
            try:
                # Exclude 'fullname' from being saved
                data_to_save = {k: v for k, v in updated_info.items() if k != "fullname"}

                # Update Student Info (dynamic columns)
                update_student_info(
                    student_id=student_id,
                    data=data_to_save | {"remarks": new_remarks}
                )
                
                # 🔧 Find semester ID
                semesters = pd.DataFrame(get_all_semesters())
                semester_row = semesters[
                    (semesters["schoolyear"] == school_year) &
                    (semesters["term"] == semester_term)
                ]
                if not semester_row.empty:
                    semester_id = semester_row.iloc[0]["semesterid"]

                    # Update enrollment status and remarks if user edited the 'status' field
                    new_status = updated_info.get("status")
                    if new_status:
                        enrollment_status = f"Enrolled - {new_status}"
                        remarks = new_status
                        
                        from services.enrollment_service import update_enrollment_status_and_remarks
                        update_enrollment_status_and_remarks(
                            student_id=student_id,
                            semester_id=semester_id,
                            enrollment_status=enrollment_status,
                            remarks=remarks
                        )

                # Update Grades
                for enrollment_id, grade in edited_grades.items():
                    upsert_grade(enrollment_id=enrollment_id, grade=grade)

                # Clear cache to force refresh and maintain selections
                st.session_state.students_cache = None
                st.session_state.enrollments_cache = None
                st.session_state.last_updated = pd.Timestamp.now()

                st.success("✅ Changes Saved Successfully!")

                # Auto-refresh to show updated data while maintaining selections
                st.rerun()

            except Exception as e:
                st.error(f"❌ Error saving changes: {str(e)}")


    with col2:
        if st.button("🗑️ Delete Student"):
            try:
                supabase.table("students").delete().eq("studentid", student_id).execute()
                
                # Clear caches and session state
                st.session_state.students_cache = None
                st.session_state.enrollments_cache = None
                st.session_state.selected_student_id = None
                st.session_state.selected_semester = None
                
                st.success(f"✅ Deleted student: {selected_student_name}")
                st.rerun()  # Only rerun for delete since student no longer exists
                
            except Exception as e:
                st.error(f"❌ Error deleting student: {str(e)}")

    # -------------------------
    # Show last updated time if available
    # -------------------------
    if st.session_state.last_updated:
        st.caption(f"Last updated: {st.session_state.last_updated.strftime('%Y-%m-%d %H:%M:%S')}")