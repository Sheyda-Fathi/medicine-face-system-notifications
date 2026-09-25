"""Doctor dashboard for assigned patients and recent clinical activity."""

import pandas as pd
import streamlit as st

from config.theme import render_header, stat_card
from database.appointment_queries import AppointmentQueries
from database.medication_queries import MedicationQueries
from database.patient_queries import PatientQueries
from services.medication_schedule import format_recorded_at


def show_doctor_home(user):
    render_header(
        f"Welcome, {user['full_name']}",
        "Your patients, prescriptions, appointments, and intake activity",
    )

    patient_db = PatientQueries()
    medication_db = MedicationQueries()
    appointment_db = AppointmentQueries()

    patients = patient_db.get_all_patients(doctor_id=user["id"])
    today_appointments = appointment_db.get_today_for_doctor(user["id"])
    active_prescriptions = sum(
        len(medication_db.get_patient_medications_advanced(row[0])) for row in patients
    )

    card_1, card_2, card_3 = st.columns(3)
    stat_card(card_1, "stat-purple", "PATIENTS", "My Patients", len(patients), "assigned")
    stat_card(card_2, "stat-pink", "ACTIVE", "Prescriptions", active_prescriptions, "active")
    stat_card(card_3, "stat-blue", "TODAY", "Appointments", len(today_appointments), "scheduled")

    st.write("")
    left, right = st.columns([2, 1])
    with left:
        st.markdown('<div class="smms-card">', unsafe_allow_html=True)
        st.subheader("Today's Appointments")
        if today_appointments:
            for appointment_id, first, last, visit_time, status, reason, patient_id in today_appointments:
                name_col, time_col, status_col = st.columns([2, 1, 2])
                with name_col:
                    st.write(f"**{first} {last}**")
                with time_col:
                    st.write(str(visit_time or "Time not set"))
                with status_col:
                    st.write(f"{status.capitalize()} - {reason or 'General visit'}")
                if st.button("Open profile", key=f"open_today_{appointment_id}"):
                    st.session_state.selected_patient_id = patient_id
                    st.info("Open Patient Profiles from the sidebar.")
        else:
            st.info("No appointments are scheduled for today.")
        st.markdown("</div>", unsafe_allow_html=True)

        st.markdown('<div class="smms-card">', unsafe_allow_html=True)
        st.subheader("Medication Adherence - Last 7 Days")
        adherence = medication_db.get_adherence_stats(7, doctor_id=user["id"])
        if adherence:
            chart = pd.DataFrame(adherence, columns=["Date", "Taken", "Missed"]).set_index("Date")
            st.bar_chart(chart)
        else:
            st.info("No intake records are available for your patients yet.")
        st.markdown("</div>", unsafe_allow_html=True)

        st.markdown('<div class="smms-card">', unsafe_allow_html=True)
        st.subheader("Latest Patient Intake Activity")
        activity = medication_db.get_recent_intake_for_doctor(user["id"], limit=15)
        if activity:
            rows = [
                {
                    "Patient": f"{row[0]} {row[1]}",
                    "Medicine": row[2],
                    "Dosage": row[3],
                    "Scheduled date": row[4],
                    "Scheduled time": row[5],
                    "Status": "Taken" if row[6] else "Missed",
                    "Actual confirmation": format_recorded_at(row[7]),
                }
                for row in activity
            ]
            st.dataframe(pd.DataFrame(rows), use_container_width=True, hide_index=True)
        else:
            st.info("No patient has recorded a medicine dose yet.")
        st.markdown("</div>", unsafe_allow_html=True)

    with right:
        st.markdown('<div class="smms-card">', unsafe_allow_html=True)
        st.subheader("Recent Patients")
        if patients:
            for patient in patients[:8]:
                st.write(f"**{patient[1]} {patient[2]}**")
                st.caption(f"National code: {patient[3]}")
        else:
            st.info("No patients are assigned to this account.")
        st.markdown("</div>", unsafe_allow_html=True)

        st.markdown('<div class="smms-card">', unsafe_allow_html=True)
        st.subheader("Doctor Tools")
        st.markdown(
            "- Register a patient and face photo\n"
            "- Prescribe medicines and reminder times\n"
            "- Review actual intake confirmation times\n"
            "- Add notes and schedule appointments"
        )
        st.markdown("</div>", unsafe_allow_html=True)
