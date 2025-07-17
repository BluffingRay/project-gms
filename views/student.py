import streamlit as st
from datetime import date
from services.student_service import get_all_students, add_student
from services.program_service import get_all_programs
from utils.student_fake_data import generate_fake_students

def show():

    st.title("Students Management")

    tab1, tab2 = st.tabs(["📋 View All Students", "➕ Add Student"])


    # -------------------------
    # View All Students Tab
    # -------------------------
    with tab1:
        st.header("All Students")
        students = get_all_students()

        if students:
            st.dataframe(students, use_container_width=True)
        else:
            st.info("No students found.")


    # -------------------------
    # Add New Student Tab
    # -------------------------
    with tab2:

        st.header("⚙️ Developer Tools")

        if st.button("Add 10 Fake Students"):
            generate_fake_students(10)
            st.success("10 fake students added successfully!")


        st.header("Add New Student")

         # Fetch programs for dropdown
        programs_data = get_all_programs()
        program_options = [p["program_name"] for p in programs_data] if programs_data else []

        with st.form("add_student"):
            student_data = {
                "studentid": st.text_input("Student ID"),
                "firstname": st.text_input("First Name"),
                "lastname": st.text_input("Last Name"),
                "middlename": st.text_input("Middle Name"),
                "gender": st.selectbox("Gender", ["Male", "Female", "Other"]),
                "dateofbirth": st.date_input("Date of Birth", min_value=date(1900, 1, 1)).isoformat(),
                "emailaddress": st.text_input("Email Address"),
                "yearlevel": st.selectbox("Year Level", ["1st Year", "2nd Year", "3rd Year", "4th Year", "Onward"]),
                "program": st.selectbox("Program", program_options) if program_options else st.text_input("Program (no programs found)"),
                "section": st.text_input("Section"),
                "enrollmentstatus": st.selectbox("Enrollment Status", ["Enrolled", "Not Enrolled", "Graduated", "Dropped"])
            }
            submit = st.form_submit_button("Save Student")

        if submit:
            add_student(student_data)
            st.success(f"Student {student_data['firstname']} {student_data['lastname']} added successfully!")
