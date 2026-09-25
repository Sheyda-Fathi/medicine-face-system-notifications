"""Administrator patient registration and record management."""

import streamlit as st

from page.patient_profile import show_patient_profile
from page.register_patient import show_register_patient


def show_admin_patients(user):
    st.title("Manage Patients")
    st.caption("Register, assign, update, or remove patient records.")
    register_tab, profiles_tab = st.tabs(["Register Patient", "Patient Profiles"])
    with register_tab:
        show_register_patient(user)
    with profiles_tab:
        show_patient_profile(user, embedded=True)
