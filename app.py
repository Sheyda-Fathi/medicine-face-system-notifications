import streamlit as st

from config.navigation import get_role_menu, patient_section_from_label
from config.settings import LAYOUT, PAGE_ICON, PAGE_TITLE
from config.theme import inject_theme
from database.notification_queries import NotificationQueries


page_config = {
    "page_title": PAGE_TITLE,
    "layout": LAYOUT,
    "initial_sidebar_state": "expanded",
}
if PAGE_ICON:
    page_config["page_icon"] = PAGE_ICON

st.set_page_config(**page_config)
inject_theme()

if "user" not in st.session_state:
    st.session_state.user = None

if not st.session_state.user:
    from page.auth import show_auth

    show_auth()
    st.stop()

user = st.session_state.user
role = user["role"]
unread_count = 0
if role == "patient":
    unread_count = NotificationQueries().count_unread(user.get("patient_id"))

with st.sidebar:
    st.markdown("### Smart Medication System")
    st.caption("Face-based access for patient medication care")
    st.divider()

    page = st.radio(
        "Menu",
        get_role_menu(role, unread_notifications=unread_count),
        index=0,
        label_visibility="collapsed",
    )

    st.divider()
    st.markdown(f"**{user['full_name']}**")
    if role == "doctor":
        specialty = user.get("specialty")
        st.caption(f"Doctor - {specialty}" if specialty else "Doctor")
    elif role == "admin":
        st.caption("System Administrator")
    else:
        st.caption("Patient")

    if st.button("Log out", use_container_width=True):
        st.session_state.user = None
        st.session_state.pop("selected_patient_id", None)
        st.rerun()

    st.divider()
    st.caption("Educational project - 2026")

if role == "doctor":
    if page == "Dashboard":
        from page.doctor_home import show_doctor_home

        show_doctor_home(user)
    elif page == "Register Patient":
        from page.register_patient import show_register_patient

        show_register_patient(user)
    elif page == "Add Medication":
        from page.add_medication import show_add_medication

        show_add_medication(user)
    else:
        from page.patient_profile import show_patient_profile

        show_patient_profile(user)
elif role == "admin":
    if page == "Dashboard":
        from page.admin_home import show_admin_home

        show_admin_home(user)
    elif page == "Manage Patients":
        from page.admin_patients import show_admin_patients

        show_admin_patients(user)
    elif page == "Manage Doctors":
        from page.manage_doctors import show_manage_doctors

        show_manage_doctors(user)
    else:
        from page.manage_medications import show_manage_medications

        show_manage_medications(user)
else:
    from page.patient_portal import show_patient_portal

    show_patient_portal(user, patient_section_from_label(page))
