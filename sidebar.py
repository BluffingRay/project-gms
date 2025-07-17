import streamlit as st


def sidebar_navigation():
    with st.sidebar:
        st.markdown("# Grading Management System")

        # ---------------- Regular ----------------
        st.markdown("### 📋 Regular Enrollment")

        if st.button("Overview", key="regular_overview"):
            st.session_state.page = "overview"
            st.rerun()
        if st.button("Edit Info", key="regular_edit"):
            st.session_state.page = "edit"
            st.rerun()
        if st.button("Migrate Data", key="regular_migrate"):
            st.session_state.page = "migrate"
            st.rerun()
        if st.button("Wide View", key="regular_wideview"):
            st.session_state.page = "wideview"
            st.rerun()

        # ---------------- Irregular ----------------
        st.markdown("---")
        st.markdown("### 📋 Irregular Enrollment")

        if st.button("Irregular Overview", key="irregular_overview"):
            st.session_state.page = "irregular_overview"
            st.rerun()
        if st.button("Irregular Edit Info", key="irregular_edit"):
            st.session_state.page = "irregular_edit"
            st.rerun()

        # ---------------- Graduate ----------------
        st.markdown("---")
        st.markdown("### 🎓 Graduate Records")

        if st.button("Graduate Edit Info", key="graduate_edit"):
            st.session_state.page = "graduate_edit"
            st.rerun()

        # ---------------- Tools ----------------
        st.markdown("---")
        st.markdown("### 🛠️ Tools")

        if st.button("Enrollment", key="regular_enrollment"):
            st.session_state.page = "enrollment"
            st.rerun()
        if st.button("Batch Graduate", key="regular_batch"):
            st.session_state.page = "batch_graduate"
            st.rerun()
        if st.button("Student List", key="tools_student"):
            st.session_state.page = "student"
            st.rerun()
        if st.button("Curriculum", key="tools_curriculum"):
            st.session_state.page = "curriculum"
            st.rerun()
        if st.button("Semester", key="tools_semester"):
            st.session_state.page = "semester"
            st.rerun()
