import streamlit as st

def show():

    
    st.title("Welcome to the Enrollment System 🎓")
    st.write("✅ You are successfully logged in.")

    st.markdown(
        """
        ---
        ## 📌 Navigation
        Please use the **sidebar** to navigate through the system.
        - Manage students
        - Manage enrollment
        - Curriculum subjects
        - Other tools
        
        ---
        """
    )
    st.info("Select a page from the sidebar to begin.")
