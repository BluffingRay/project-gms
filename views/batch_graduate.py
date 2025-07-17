import streamlit as st
import pandas as pd
from services.enrollment_service import (
    get_all_semesters,
    get_all_enrollments,
    update_student_status,
)
from database_client import supabase

def show():

    st.set_page_config(page_title="Batch Graduation", layout="wide")
    st.title("Batch Graduation of 4th Year, 2nd Semester Students")

    # -------------------------
    # Fetch semesters and enrollments
    # -------------------------
    semesters = get_all_semesters()
    semester_options = {f"{sem['schoolyear']} {sem['term']}": sem["semesterid"] for sem in semesters}

    selected_sem_key = st.selectbox("Select Semester (Graduating Batch)", list(semester_options.keys()))
    selected_sem_id = semester_options[selected_sem_key]

    all_enrollments = pd.DataFrame(get_all_enrollments())

    if all_enrollments.empty:
        st.warning("No enrollment records found.")
        st.stop()

    # -------------------------
    # Filter 4th Year 2nd Sem Regulars
    # -------------------------
    graduating_df = all_enrollments[
        (all_enrollments["semesterid"] == selected_sem_id) &
        (all_enrollments["yearlevel"] == "4th Year") &
        (all_enrollments["semester_term"] == "2nd Semester") &
        (all_enrollments["enrollmentstatus"].str.contains("Regular", na=False))
    ][["studentid", "studentname", "program"]].drop_duplicates()

    if graduating_df.empty:
        st.info("No 4th Year 2nd Semester students found in this semester.")
        st.stop()

    # -------------------------
    # Program Filter
    # -------------------------
    programs = ["All"] + sorted(graduating_df["program"].dropna().unique().tolist())
    selected_program = st.selectbox("Filter by Program", programs)

    if selected_program != "All":
        graduating_df = graduating_df[graduating_df["program"] == selected_program]

    if graduating_df.empty:
        st.info("No students match the selected program.")
        st.stop()

    # -------------------------
    # Student Selection
    # -------------------------
    student_names = sorted(graduating_df["studentname"].tolist())  # ✅ Sort alphabetically
    students_to_graduate = st.multiselect(
        "Select students to mark as Graduated",
        options=student_names,
        default=student_names
    )

    if not students_to_graduate:
        st.warning("Please select at least one student to mark as Graduated.")
        st.stop()

    st.markdown(f"**Selected {len(students_to_graduate)} students to mark as Graduated in {selected_sem_key}.**")

    # -------------------------
    # Graduation Process
    # -------------------------
    if st.button("🎓 Mark Selected Students as Graduated"):
        success_count = 0
        failed_students = []

        for student_name in students_to_graduate:
            student = graduating_df[graduating_df["studentname"] == student_name].iloc[0]
            student_id = student["studentid"]

            try:
                update_student_status(
                    student_id=student_id,
                    program=student["program"],
                    yearlevel="Graduated",
                    remarks="Graduated",
                    status="Graduated"
                )
                # Optionally, you can update 'enrollments' remarks too, via Supabase:
                supabase.table("enrollments").update({"remarks": "Graduated"}).eq("studentid", student_id).eq("semesterid", selected_sem_id).execute()
                success_count += 1
            except Exception as e:
                failed_students.append((student_name, f"Update error: {str(e)}"))

        if success_count > 0:
            st.success(f"✅ Successfully marked {success_count} students as Graduated.")
        if failed_students:
            st.error("❌ Failed to update for:")
            for name, error in failed_students:
                st.write(f"- {name}: {error}")
