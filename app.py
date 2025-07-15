import streamlit as st
from utils.auth import require_login

st.set_page_config(page_title="Grading System", layout="wide")
require_login()

st.title("Grading Dashboard")
st.write("Use sidebar to navigate pages.")
