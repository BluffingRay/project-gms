import streamlit as st

def require_login():
    users = {"faculty": "secret123"}

    if "logged_in" not in st.session_state:
        st.session_state.logged_in = False

    # 🔒 Hide sidebar and main menu before login
    if not st.session_state.logged_in:
        hide_sidebar = """
            <style>
                [data-testid="stSidebar"], header, footer, [data-testid="stToolbar"] {
                    display: none !important;
                }
            </style>
        """
        st.markdown(hide_sidebar, unsafe_allow_html=True)

        st.title("Faculty Login")
        username = st.text_input("Username")
        password = st.text_input("Password", type="password")
        if st.button("Login"):
            if username in users and users[username] == password:
                st.session_state.logged_in = True
                st.rerun()
            else:
                st.error("Invalid credentials")
        st.stop()
