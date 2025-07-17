import streamlit as st
from sidebar import sidebar_navigation

# -------------------
# Initialize session state
# -------------------
if "page" not in st.session_state:
    st.session_state.page = "overview"  # ✅ Set to overview

# -------------------
# Sidebar
# -------------------
sidebar_navigation()

# -------------------
# Routing for all views
# -------------------
if st.session_state.page == "overview":
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

# -------------------
# Render selected page
# -------------------
page.show()
