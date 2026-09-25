"""Administrator interface for doctor accounts."""

import streamlit as st

from database.auth_queries import AuthQueries


def show_manage_doctors(user):
    if user.get("role") != "admin":
        st.error("Administrator access is required.")
        return

    st.title("Manage Doctors")
    st.caption("Doctor accounts are created only by the system administrator.")
    st.divider()

    auth_db = AuthQueries()
    add_tab, list_tab = st.tabs(["Add Doctor", "Doctor Accounts"])

    with add_tab:
        with st.form("admin_add_doctor"):
            full_name = st.text_input("Full name *")
            specialty = st.text_input("Specialty", placeholder="Example: Cardiology")
            email = st.text_input("Email")
            username = st.text_input("Username *")
            password = st.text_input("Initial password *", type="password")
            submitted = st.form_submit_button("Create doctor account", type="primary")
        if submitted:
            if not full_name.strip() or not username.strip() or not password:
                st.error("Full name, username, and password are required.")
            elif len(password) < 8:
                st.error("The password must contain at least 8 characters.")
            else:
                doctor_id, error = auth_db.register_doctor(
                    username.strip(), password, full_name.strip(),
                    email.strip(), specialty.strip(),
                )
                if doctor_id:
                    st.success(f"Doctor account created. Doctor ID: {doctor_id}.")
                    st.rerun()
                else:
                    st.error(error or "Doctor account could not be created.")

    with list_tab:
        doctors = auth_db.get_doctors_detailed()
        if not doctors:
            st.info("No doctor accounts are registered.")
            return
        for doctor_id, full_name, username, email, specialty, created_at, patient_count in doctors:
            with st.expander(f"{full_name} - {specialty or 'General Medicine'}"):
                st.write(f"Username: {username}")
                st.write(f"Email: {email or 'Not provided'}")
                st.write(f"Assigned patients: {patient_count}")
                st.write(f"Created: {created_at}")
                confirm = st.checkbox(
                    "Confirm doctor deletion",
                    key=f"confirm_doctor_{doctor_id}",
                )
                if st.button("Delete doctor", key=f"delete_doctor_{doctor_id}"):
                    if not confirm:
                        st.warning("Confirm deletion before continuing.")
                    else:
                        deleted, error = auth_db.delete_doctor(doctor_id)
                        if deleted:
                            st.success(
                                "Doctor deleted. Existing patient and clinical records were preserved; "
                                "affected patients are now unassigned."
                            )
                            st.rerun()
                        else:
                            st.error(error or "Doctor could not be deleted.")
