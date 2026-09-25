"""Doctor workflow for prescribing a catalog medicine."""

from datetime import date, datetime

import streamlit as st

from database.medication_queries import MedicationQueries
from database.notification_queries import NotificationQueries
from database.patient_queries import PatientQueries
from services.notification_messages import prescription_notification


def show_add_medication(user=None):
    user = user or st.session_state.get("user") or {}
    if user.get("role") != "doctor":
        st.error("Medication prescriptions are available only to doctors.")
        return

    st.title("Add Medication")
    st.caption("Create or update a prescription for an assigned patient.")
    st.divider()

    patient_db = PatientQueries()
    medication_db = MedicationQueries()
    patients = patient_db.get_all_patients(doctor_id=user["id"])
    if not patients:
        st.warning("No patients are assigned to this doctor. Register a patient first.")
        return

    patient_options = {
        f"{row[1]} {row[2]} - {row[3]}": row[0] for row in patients
    }
    default_id = st.session_state.get("selected_patient_id")
    default_index = 0
    if default_id in patient_options.values():
        default_index = list(patient_options.values()).index(default_id)
    selected_label = st.selectbox("Patient", list(patient_options), index=default_index)
    patient_id = patient_options[selected_label]
    st.session_state.selected_patient_id = patient_id

    medications = medication_db.get_all_medications()
    if not medications:
        st.error("The medication catalog is empty. Ask the administrator to add medicines.")
        return
    medication_options = {row[1]: row[0] for row in medications}
    medication_name = st.selectbox("Medication", list(medication_options))
    medication_id = medication_options[medication_name]

    detail_col, schedule_col = st.columns(2)
    with detail_col:
        st.subheader("Prescription")
        dosage = st.text_input("Dosage *", placeholder="Example: 500 mg or 1 tablet")
        instructions = st.text_area(
            "Doctor instructions",
            placeholder="Example: Take after breakfast with water.",
        )
        start_date = st.date_input("Start date", value=date.today())
        end_date = st.date_input("End date (optional)", value=None)

    with schedule_col:
        st.subheader("Daily Reminder Times")
        times_per_day = st.selectbox("Times per day", [1, 2, 3, 4])
        defaults = ["08:00", "14:00", "20:00", "23:00"]
        time_slots = []
        for index in range(times_per_day):
            default_time = datetime.strptime(defaults[index], "%H:%M").time()
            selected_time = st.time_input(f"Dose time {index + 1}", value=default_time)
            time_slots.append(selected_time.strftime("%H:%M"))

    st.subheader("Interaction Check")
    interactions = medication_db.check_medication_interactions(patient_id, medication_id)
    if interactions:
        for item in interactions:
            st.warning(
                f"{item['med1']} and {item['med2']} - "
                f"{item['severity'].upper()}: {item['description']}"
            )
    else:
        st.success("No known interaction was found with the patient's active medicines.")

    if not st.button("Save prescription", type="primary"):
        return
    if not dosage.strip():
        st.error("Dosage is required.")
        return
    if end_date and end_date < start_date:
        st.error("End date cannot be earlier than start date.")
        return

    time_slots_text = ", ".join(time_slots)
    schedule = f"{times_per_day} time(s) per day at {time_slots_text}"
    prescription_id = medication_db.assign_medication_to_patient(
        patient_id=patient_id,
        medication_id=medication_id,
        dosage=dosage.strip(),
        schedule=schedule,
        start_date=start_date,
        end_date=end_date,
        times_per_day=times_per_day,
        time_slots=time_slots_text,
        notes=instructions.strip(),
        prescribed_by=user["id"],
    )
    if not prescription_id:
        st.error("The prescription could not be saved.")
        return

    title, message = prescription_notification(
        medication_name,
        dosage.strip(),
        time_slots_text,
        user["full_name"],
    )
    notification_id = NotificationQueries().create(
        patient_id,
        "prescription",
        title,
        message,
        related_id=prescription_id,
    )
    if notification_id:
        st.success(
            f"{medication_name} was prescribed to {selected_label}. "
            "The patient was notified and reminder times are active."
        )
    else:
        st.warning(
            "The prescription was saved, but the patient notification could not be created."
        )
