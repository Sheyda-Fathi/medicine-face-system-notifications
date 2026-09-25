"""Administrator interface for the medication catalog."""

import streamlit as st

from database.medication_queries import MedicationQueries


def show_manage_medications(user):
    if user.get("role") != "admin":
        st.error("Administrator access is required.")
        return

    st.title("Manage Medication Catalog")
    st.caption(
        "Doctors prescribe medicines from this catalog. A medicine in an existing "
        "prescription cannot be deleted."
    )
    st.divider()

    medication_db = MedicationQueries()
    add_tab, catalog_tab = st.tabs(["Add Medicine", "Catalog"])

    with add_tab:
        with st.form("add_catalog_medicine"):
            name = st.text_input("Medicine name *")
            description = st.text_area("Description")
            submitted = st.form_submit_button("Save medicine", type="primary")
        if submitted:
            if not name.strip():
                st.error("Medicine name is required.")
            else:
                medication_id = medication_db.add_medication(
                    name.strip(), description.strip()
                )
                if medication_id:
                    st.success(f"Medicine saved. Catalog ID: {medication_id}.")
                    st.rerun()
                else:
                    st.error("The medicine could not be saved.")

    with catalog_tab:
        search = st.text_input("Search medicine")
        medicines = medication_db.get_all_medications(search.strip())
        st.caption(f"{len(medicines)} medicine(s) shown")
        for medication_id, name, description in medicines:
            with st.expander(name):
                st.write(description or "No description")
                usage = medication_db.get_medication_usage_count(medication_id)
                st.write(f"Patient prescriptions: {usage}")
                if usage:
                    st.caption("Remove the patient prescriptions before deleting this catalog item.")
                elif st.button("Delete medicine", key=f"delete_medicine_{medication_id}"):
                    deleted, error = medication_db.delete_medication(medication_id)
                    if deleted:
                        st.success("Medicine deleted from the catalog.")
                        st.rerun()
                    else:
                        st.error(error or "Medicine could not be deleted.")
