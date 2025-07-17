import streamlit as st
from sidebar import sidebar_navigation
from database_client import verify_login

st.set_page_config(page_title="Login", page_icon="🔐", layout="centered", initial_sidebar_state="collapsed")



# -------------------
# Login
# -------------------
if "user" not in st.session_state:

    st.title("🔐 Login")
    user_id = st.text_input("ID")
    password = st.text_input("Password", type="password")

    if st.button("Login"):
        user = verify_login(user_id, password)
        if user:
            st.session_state["user"] = user
            st.rerun()
        else:
            st.error("Invalid ID or password.")

    st.stop()

if "page" not in st.session_state:
    st.session_state.page = "landing"

sidebar_navigation()

# -------------------
# Routing
# -------------------
if st.session_state.page == "landing":
    import views.landing as page
elif st.session_state.page == "overview":
    import views.overview as page
elif st.session_state.page == "enrollment":
    import views.enrollment as page
elif st.session_state.page == "edit":
    import views.edit as page
elif st.session_state.page == "batch_graduate":
    import views.batch_graduate as page
elif st.session_state.page == "migrate":
    import views.migrate as page
elif st.session_state.page == "wideview":
    import views.wideview as page
elif st.session_state.page == "irregular_overview":
    import views.irregular_overview as page
elif st.session_state.page == "irregular_edit":
    import views.irregular_edit as page
elif st.session_state.page == "graduate_edit":
    import views.graduate_edit as page
elif st.session_state.page == "curriculum":
    import views.curriculum as page
elif st.session_state.page == "semester":
    import views.semester as page
elif st.session_state.page == "student":
    import views.student as page
else:
    st.error("🚨 Page not found.")

page.show()

if st.button("Logout"):
    del st.session_state["user"]
    st.rerun()
