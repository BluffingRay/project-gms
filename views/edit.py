import streamlit as st
import pandas as pd
from services.enrollment_service import (
    get_all_students,
    get_all_enrollments,
    update_enrollment_status_and_remarks,
)
from services.student_service import update_student_info
from services.grades_service import upsert_grade, get_student_gwa_summary
from services.curriculum_service import get_all_curriculum_subjects
from services.semester_service import get_all_semesters
from database_client import supabase

st.set_page_config(page_title="Edit Student Info", layout="wide")
st.title("Edit Student Information")

def show():

    # --- Cache Student List Once ---
    students = pd.DataFrame(get_all_students())
    students["fullname"] = students["firstname"] + " " + students["lastname"]
    students["display_name"] = students["yearlevel"].astype(str) + " - " + students["firstname"] + " " + students["lastname"]
    students = students.sort_values("display_name")

    student_names = students["display_name"].tolist()
    name_to_id = {row["display_name"]: row["studentid"] for _, row in students.iterrows()}

    # --- Last Edited Student in Session State ---
    default_name = None
    if st.session_state.get("last_selected_student_id"):
        default_name = students.loc[students["studentid"] == st.session_state["last_selected_student_id"], "display_name"].values[0]

    selected_name = st.selectbox("Select Student", student_names, index=student_names.index(default_name) if default_name in student_names else 0)

    student_id = name_to_id[selected_name]
    st.session_state["last_selected_student_id"] = student_id

    selected_student = students.loc[students["studentid"] == student_id].squeeze()

    # --- Enrollment Data ---
    enrollments = pd.DataFrame(get_all_enrollments())
    if enrollments.empty:
        enrollments = pd.DataFrame(columns=["studentid", "schoolyear", "semester_term", "curriculumid", "enrollmentid", "subjectname", "grade"])

    student_enrollments = enrollments[enrollments["studentid"] == student_id]

    school_year = None
    semester_term = None

    if not student_enrollments.empty:
        latest_enrollment = student_enrollments.sort_values("schoolyear", ascending=False).iloc[0]
        school_year = latest_enrollment["schoolyear"]
        semester_term = latest_enrollment["semester_term"]

    tabs = st.tabs(["Overview", "Grades", "Edit Info"])

    with tabs[0]:
        st.header("Overview")
        if student_enrollments.empty:
            st.warning("⚠️ This student has no enrollment records.")
        else:
            curriculum_df = pd.DataFrame(get_all_curriculum_subjects())
            student_enrollments = student_enrollments.merge(
                curriculum_df.rename(columns={"id": "curriculumid"})[["curriculumid", "units"]],
                on="curriculumid",
                how="left"
            )

            gwa_summary = get_student_gwa_summary(student_id)
            semester_key = f"{selected_student['yearlevel']} {semester_term}"
            gwa_selected = gwa_summary.get(semester_key, "--")
            gwa_overall = gwa_summary.get("Overall", "--")

            notice = f"""
            **Remarks**: {selected_student.get('remarks') or '- No remarks -'}  
            **DL Applicable**: {'✅ Yes' if selected_student.get('dl_applicable') else '❌ No'}  
            **Laude Applicable**: {'✅ Yes' if selected_student.get('laude_applicable') else '❌ No'}
            """
            st.info(notice)

            col1, col2, col3 = st.columns(3)
            col1.metric("Year / Program", f"{selected_student['yearlevel']} / {selected_student['program']}")
            col2.metric("Latest Enrollment", f"{school_year} {semester_term}")
            col3.metric("Overall GWA", gwa_overall)


    with tabs[1]:
        st.header("Edit Grades by Semester")

        if student_enrollments.empty:
            st.warning("⚠️ Cannot view grades. This student has no enrollment records.")
        else:
            # --- Build mapping: display -> semesterid (only semesters where student is enrolled)
            semester_options = {
                f"{row['schoolyear']} {row['semester_term']}": row["semesterid"]
                for _, row in student_enrollments.drop_duplicates(subset=["semesterid"]).iterrows()
            }

            selected_semester_display = st.selectbox("Select Semester", list(semester_options.keys()))
            selected_semester_id = semester_options[selected_semester_display]

            # --- Filter enrollments by semesterid directly
            current_sem = student_enrollments[
                student_enrollments["semesterid"] == selected_semester_id
            ]

            if current_sem.empty:
                st.info(f"No subjects found for {selected_semester_display}")
            else:
                st.caption(f"Editing Grades for: **{selected_semester_display}**")

                edited_grades = {}
                for _, row in current_sem.iterrows():
                    subject = row["subjectname"]
                    grade = str(row["grade"]) if pd.notna(row["grade"]) else ""
                    allowed_grades = ["", "1", "1.25", "1.5", "1.75", "2", "2.25", "2.5", "2.75", "3", "INC", "Dropped", "FAILED"]

                    new_grade = st.selectbox(
                        f"{subject} Grade",
                        allowed_grades,
                        index=allowed_grades.index(grade) if grade in allowed_grades else 0,
                        key=row["enrollmentid"]
                    )
                    edited_grades[row["enrollmentid"]] = new_grade

                # --- Save Grades Button (OUTSIDE LOOP)
                if st.button("💾 Save Grades for this Semester"):
                    update_enrollment_status_and_remarks(
                        student_id=student_id,
                        semester_id=selected_semester_id,
                        enrollment_status="Enrolled - Regular",  # Or fetch dynamically if needed
                        remarks="Regular"
                    )

                    for enrollment_id, grade in edited_grades.items():
                        upsert_grade(enrollment_id, grade)

                    st.success(f"✅ Grades updated for {selected_semester_display}!")
                    st.rerun()


    with tabs[2]:
        st.header("Edit Student Information")
        st.markdown("<br>", unsafe_allow_html=True)

        updated_info = {}
        new_status = selected_student.get("status", "")

        for col in selected_student.index:
            if col in ["studentid", "remarks", "enrollmentstatus", "fullname", "display_name"]:
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

        updated_info["status"] = new_status  # Ensure latest selected status is stored.

        if st.button("💾 Save Changes"):
            update_student_info(
                student_id=student_id,
                data=updated_info
            )

            if not student_enrollments.empty and school_year is not None:
                semesters = pd.DataFrame(get_all_semesters())
                semester_row = semesters[(semesters["schoolyear"] == school_year) & (semesters["term"] == semester_term)]
                if not semester_row.empty:
                    semester_id = semester_row.iloc[0]["semesterid"]
                    update_enrollment_status_and_remarks(
                        student_id=student_id,
                        semester_id=semester_id,
                        enrollment_status=f"Enrolled - {updated_info['status']}",
                        remarks=updated_info["status"]
                    )

            st.success("✅ Changes saved successfully!")
            st.rerun()

        if st.button("🗑️ Delete Student"):
            supabase.table("students").delete().eq("studentid", student_id).execute()
            st.session_state["last_selected_student_id"] = None
            st.success("✅ Student deleted.")
            st.rerun()
