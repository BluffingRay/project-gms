import streamlit as st
import pandas as pd
from services.curriculum_service import (
    get_all_curriculum_subjects,
    add_curriculum_subject,
    delete_curriculum_subject,
    update_curriculum_subject
)
from utils.student_fake_data import insert_fake_curriculum_data


st.set_page_config(page_title="Curriculum Management", layout="wide")
st.title("Curriculum Subjects Management")

programs = ["JD", "BSED-English", "BSED-Math", "BSCS"]
year_levels = ["1st Year", "2nd Year", "3rd Year", "4th Year"]
terms = ["1st Semester", "2nd Semester", "Midyear"]

# -------------------------
# Developer Fake Data Button
# -------------------------
with st.expander("💾 Developer: Insert Fake Data for Testing"):
    if st.button("➕ Insert Fake Curriculum Subjects"):
        insert_fake_curriculum_data()
        st.success("Fake curriculum subjects inserted.")
        st.rerun()

# -------------------------
# Session State for Delete Confirmation
# -------------------------
if "confirm_delete_curriculum" not in st.session_state:
    st.session_state.confirm_delete_curriculum = False
    st.session_state.subject_to_delete = None

# -------------------------
# Tabs: View / Add
# -------------------------
tab1, tab2, tab3 = st.tabs(["📋 View Curriculum Subjects", "➕ Add Curriculum Subject", "✏️ Edit Curriculum Subject"])

# -------------------------
# View Curriculum Subjects with Filters
# -------------------------
with tab1:
    st.header("All Curriculum Subjects")

    curriculum_subjects = get_all_curriculum_subjects()
    if curriculum_subjects:
        df = pd.DataFrame(curriculum_subjects)
        df = df.sort_values(by=["program", "yearlevel", "term", "code"])

        col1, col2, col3 = st.columns(3)
        with col1:
            selected_program = st.selectbox("Filter by Program", ["All"] + sorted(df["program"].unique().tolist()))
        with col2:
            selected_yearlevel = st.selectbox("Filter by Year Level", ["All"] + sorted(df["yearlevel"].unique().tolist()))
        with col3:
            selected_term = st.selectbox("Filter by Term", ["All"] + sorted(df["term"].unique().tolist()))

        if selected_program != "All":
            df = df[df["program"] == selected_program]
        if selected_yearlevel != "All":
            df = df[df["yearlevel"] == selected_yearlevel]
        if selected_term != "All":
            df = df[df["term"] == selected_term]

        st.dataframe(df[["program", "yearlevel", "term", "code", "name", "units"]], use_container_width=True)

        subject_options = {
            f"{row['program']} {row['yearlevel']} {row['term']} {row['code']} {row['name']}": row["id"]
            for _, row in df.iterrows()
        }

        selected_subject = st.selectbox("Select Curriculum Subject to Delete", list(subject_options.keys()))

        if st.button("🚨 Delete Selected Curriculum Subject"):
            st.session_state.confirm_delete_curriculum = True
            st.session_state.subject_to_delete = selected_subject

        # Confirmation Dialog
        if st.session_state.confirm_delete_curriculum:
            st.warning(
                f"Are you sure you want to delete:\n\n**{st.session_state.subject_to_delete}**?\n\n"
                "This affects your program's curriculum.",
                icon="⚠️"
            )
            col1, col2 = st.columns([1, 0.6])
            with col1:
                if st.button("✅ Yes, Confirm Delete"):
                    delete_curriculum_subject(subject_options[st.session_state.subject_to_delete])
                    st.success(f"Deleted: {st.session_state.subject_to_delete}")
                    st.session_state.confirm_delete_curriculum = False
                    st.rerun()
            with col2:
                if st.button("❌ Cancel"):
                    st.session_state.confirm_delete_curriculum = False
                    st.rerun()

    else:
        st.info("No curriculum subjects found.")


# -------------------------
# Add Curriculum Subject
# -------------------------
with tab2:
    st.header("Add New Curriculum Subject")

    with st.form("add_curriculum_subject"):
        subject_data = {
            "program": st.selectbox("Program", programs),
            "yearlevel": st.selectbox("Year Level", year_levels),
            "term": st.selectbox("Term", terms),
            "code": st.text_input("Subject Code (e.g., ENG101)"),
            "name": st.text_input("Subject Name (e.g., English 101)"),
            "units": st.number_input("Units", min_value=0, step=1),
        }
        submit = st.form_submit_button("Save Subject")

    if submit:
        add_curriculum_subject(subject_data)
        st.success(f"Curriculum Subject {subject_data['code']} - {subject_data['name']} added successfully!")
        st.rerun()

with tab3:
    st.header("Edit Curriculum Subject")

    curriculum_subjects = get_all_curriculum_subjects()
    if curriculum_subjects:
        df = pd.DataFrame(curriculum_subjects)
        df = df.sort_values(by=["program", "yearlevel", "term", "code"])

        subject_options = {
            f"{row['program']} {row['yearlevel']} {row['term']} {row['code']} {row['name']}": row
            for _, row in df.iterrows()
        }

        selected_subject_key = st.selectbox("Select Curriculum Subject to Edit", list(subject_options.keys()))
        selected_subject = subject_options[selected_subject_key]

        with st.form("edit_curriculum_subject"):
            program = st.selectbox("Program", programs, index=programs.index(selected_subject["program"]))
            yearlevel = st.selectbox("Year Level", year_levels, index=year_levels.index(selected_subject["yearlevel"]))
            term = st.selectbox("Term", terms, index=terms.index(selected_subject["term"]))
            code = st.text_input("Subject Code", value=selected_subject["code"])
            name = st.text_input("Subject Name", value=selected_subject["name"])
            units = st.number_input("Units", min_value=0, step=1, value=selected_subject["units"])

            submit_edit = st.form_submit_button("Update Subject")

        if submit_edit:
            updated_data = {
                "id": selected_subject["id"],  # important to identify the record
                "program": program,
                "yearlevel": yearlevel,
                "term": term,
                "code": code,
                "name": name,
                "units": units,
            }
            # Call your update function here (you need to implement it)
            update_curriculum_subject(updated_data)

            st.success(f"Curriculum Subject {code} - {name} updated successfully!")
            st.rerun()

    else:
        st.info("No curriculum subjects found.")