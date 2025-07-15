import streamlit as st
from datetime import date
from services.semester_service import get_all_semesters, add_semester, delete_semester
import pandas as pd


st.title("Semester Management")

tab1, tab2 = st.tabs(["📋 View Semesters", "➕ Add Semester"])

# -------------------------
# View Semesters Tab
# -------------------------
with tab1:
    st.header("All Semesters")

    semesters = get_all_semesters()

    if semesters:
        df = pd.DataFrame(semesters)
        df["startdate"] = pd.to_datetime(df["startdate"]).dt.strftime("%Y-%m-%d")
        df["enddate"] = pd.to_datetime(df["enddate"]).dt.strftime("%Y-%m-%d")
        df = df.sort_values(by="startdate", ascending=False)

        st.dataframe(df[["schoolyear", "term", "startdate", "enddate"]], use_container_width=True)

        semester_options = [
            f"{row['schoolyear']} {row['term']} ({row['startdate']} - {row['enddate']})"
            for _, row in df.iterrows()
        ]
        semester_ids = df["semesterid"].tolist()
        semester_map = dict(zip(semester_options, semester_ids))

        selected_semester = st.selectbox("Select Semester to Delete", semester_options)

        if "semester_to_delete" not in st.session_state:
            st.session_state.semester_to_delete = None

        if st.button("🚨 Delete Selected Semester"):
            st.session_state.semester_to_delete = selected_semester

        if st.session_state.semester_to_delete:
            st.warning(
                f"Are you sure you want to delete:\n\n**{st.session_state.semester_to_delete}**?\n\n"
                "This may affect connected records (students, grades, etc)."
            )
            col1, col2 = st.columns([1, 2.5])
            with col1:
                if st.button("✅ Yes, Confirm Delete"):
                    delete_semester(semester_map[st.session_state.semester_to_delete])
                    st.success(f"Deleted semester: {st.session_state.semester_to_delete}")
                    st.session_state.semester_to_delete = None
                    st.rerun()
            with col2:
                if st.button("❌ Cancel"):
                    st.session_state.semester_to_delete = None
                    st.rerun()
    else:
        st.info("No semesters found.")


# -------------------------
# Add New Semester Tab
# -------------------------
with tab2:
    st.header("Add New Semester")

    with st.form("add_semester"):
        semester_data = {
            "schoolyear": st.text_input("School Year (e.g., 2024-2025)"),
            "term": st.selectbox("Term", ["1st Semester", "2nd Semester", "Midyear"]),
            "startdate": st.date_input("Start Date", min_value=date(2000, 1, 1)).isoformat(),
            "enddate": st.date_input("End Date", min_value=date(2000, 1, 1)).isoformat(),
        }
        submit = st.form_submit_button("Save Semester")

    if submit:
        add_semester(semester_data)
        st.success(f"Semester {semester_data['schoolyear']} {semester_data['term']} added successfully!")
        st.rerun()
