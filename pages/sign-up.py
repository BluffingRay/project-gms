import streamlit as st
from database_client import create_account

st.set_page_config(page_title="Sign-Up", page_icon="📝", layout="centered", initial_sidebar_state="collapsed")
hide_streamlit_style = """
            <style>
            #MainMenu {visibility: hidden;}
            footer {visibility: hidden;}
            header {visibility: hidden;}
            .css-1d391kg {visibility: hidden;}  /* Sidebar navigation */
            </style>
            """
st.markdown(hide_streamlit_style, unsafe_allow_html=True)

st.title("Create Account")

signup_code = st.text_input("Sign-up Code", type="password")
if signup_code != st.secrets["auth"]["signup_code"]:
    st.warning("Incorrect code.")
    st.stop()

user_id = st.text_input("ID")
fullname = st.text_input("Full Name")
password = st.text_input("Password", type="password")

if st.button("Create Account"):
    success, message = create_account(user_id, password, fullname)
    if success:
        st.success(message)
        st.switch_page("app.py")
    else:
        st.error(message)
