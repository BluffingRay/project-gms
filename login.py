import streamlit as st
from database_client import verify_login

st.title("🔐 Login")

user_id = st.text_input("ID")
password = st.text_input("Password", type="password")

if st.button("Login"):
    user = verify_login(user_id, password)
    if user:
        st.session_state["user"] = user
        st.success(f"Welcome {user['fullname']}!")
        st.switch_page("app.py")
    else:
        st.error("Invalid ID or password.")