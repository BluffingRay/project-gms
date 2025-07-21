import streamlit as st
import pandas as pd
from database_client import supabase
from services.enrollment_service import get_all_semesters
from services.curriculum_service import get_all_curriculum_subjects
import uuid

def show():

    st.set_page_config(page_title="Manage Semester Subjects", layout="wide")
    st.title("📚 Manage Semester Subject Offerings")

    # -------------------------------
    # Load Data
    # -------------------------------
    semesters = get_all_semesters()
    semester_options = {f"{sem['schoolyear']} {sem['term']}": sem["semesterid"] for sem in semesters}
    curriculum_subjects = get_all_curriculum_subjects()
    curriculum_df = pd.DataFrame(curriculum_subjects)

    # Ensure curriculum_df has a 'curriculum_semester' column like "1st Year 1st Sem"
    # Example: curriculum_df["curriculum_semester"] = "1st Year 1st Sem"

    # -------------------------------
    # Select Semester
    # -------------------------------
    selected_semester = st.selectbox("Select Semester", list(semester_options.keys()))
    selected_semester_id = semester_options[selected_semester]

    # -------------------------------
    # Choose Curriculum Semester First
    # -------------------------------
    curriculum_semesters = sorted(curriculum_df["term"].dropna().unique())
    selected_curriculum_sem = st.selectbox("Filter Subjects By Curriculum Semester", curriculum_semesters)

    # -------------------------------
    # Filter Available Subjects
    # -------------------------------
    filtered_subjects_df = curriculum_df[curriculum_df["term"] == selected_curriculum_sem]

    if filtered_subjects_df.empty:
        st.info("No subjects found for this curriculum semester.")
        st.stop()

    subject_options = {
        f"{row['name']} ({row['code']})": row["id"]
        for _, row in filtered_subjects_df.iterrows()
    }

    selected_subject_names = st.multiselect(
        "Select Subjects to Offer for the Semester",
        list(subject_options.keys())
    )

    selected_subject_ids = [subject_options[name] for name in selected_subject_names]

    # -------------------------------
    # Existing Subjects (Optional Display)
    # -------------------------------
    response = supabase.table("semester_subjects").select("""
        id,
        curriculum_subject_id,
        curriculum_subjects(name, code)
    """).eq("semester_id", selected_semester_id).execute()

    existing_subjects_df = pd.DataFrame([
        {
            "Subject": item["curriculum_subjects"]["name"],
            "Code": item["curriculum_subjects"]["code"]
        }
        for item in response.data
    ])

    st.subheader(f"Subjects Already Assigned for {selected_semester}")
    if not existing_subjects_df.empty:
        st.dataframe(existing_subjects_df, use_container_width=True)

    # -------------------------------
    # Save Subjects
    # -------------------------------
    if st.button("✅ Save Subjects for Semester"):
        if not selected_subject_ids:
            st.warning("Please select at least one subject.")
            st.stop()

        # Clear previous
        supabase.table("semester_subjects").delete().eq("semester_id", selected_semester_id).execute()

        for subject_id in selected_subject_ids:
            supabase.table("semester_subjects").insert({
                "id": str(uuid.uuid4()),
                "semester_id": selected_semester_id,
                "curriculum_subject_id": subject_id
            }).execute()

        st.success(f"✅ Saved {len(selected_subject_ids)} subjects for {selected_semester}!")
        st.rerun()