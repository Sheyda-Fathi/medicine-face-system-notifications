"""Administrator dashboard for system ownership and master data."""

import pandas as pd
import streamlit as st

from config.theme import render_header, stat_card
from database.appointment_queries import AppointmentQueries
from database.auth_queries import AuthQueries
from database.medication_queries import MedicationQueries
from database.patient_queries import PatientQueries


def show_admin_home(user):
    render_header(
        f"Welcome, {user['full_name']}",
        "System administration and master-data overview",
    )

    patients = PatientQueries().get_all_patients()
    doctors = AuthQueries().get_doctors_detailed()
    medication_db = MedicationQueries()
    medicines = medication_db.get_all_medications()
    appointment_db = AppointmentQueries()

    card_1, card_2, card_3, card_4 = st.columns(4)
    stat_card(card_1, "stat-purple", "PATIENTS", "Patients", len(patients), "registered")
    stat_card(card_2, "stat-pink", "DOCTORS", "Doctors", len(doctors), "staff accounts")
    stat_card(card_3, "stat-blue", "MEDICINES", "Catalog", len(medicines), "medicine entries")
    stat_card(card_4, "stat-pink2", "TODAY", "Appointments", appointment_db.count_today(), "scheduled")

    st.info(
        "The administrator maintains users and master data. Clinical decisions, "
        "prescriptions, doctor notes, and appointment care remain the doctor's responsibility."
    )

    left, right = st.columns([2, 1])
    with left:
        st.markdown('<div class="smms-card">', unsafe_allow_html=True)
        st.subheader("Appointments - Last 7 Days")
        rows = appointment_db.get_appointments_per_day(7)
        if rows:
            chart = pd.DataFrame(rows, columns=["Date", "Appointments"]).set_index("Date")
            st.line_chart(chart)
        else:
            st.info("No appointment records are available.")
        st.markdown("</div>", unsafe_allow_html=True)

        st.markdown('<div class="smms-card">', unsafe_allow_html=True)
        st.subheader("System Medication Adherence - Last 7 Days")
        adherence = medication_db.get_adherence_stats(7)
        if adherence:
            chart = pd.DataFrame(adherence, columns=["Date", "Taken", "Missed"]).set_index("Date")
            st.bar_chart(chart)
        else:
            st.info("No medication intake has been recorded yet.")
        st.markdown("</div>", unsafe_allow_html=True)

    with right:
        st.markdown('<div class="smms-card">', unsafe_allow_html=True)
        st.subheader("Administrator Responsibilities")
        st.markdown(
            "- Add or remove patients\n"
            "- Add or remove doctor accounts\n"
            "- Add or remove catalog medicines\n"
            "- Review system totals and activity"
        )
        st.markdown("</div>", unsafe_allow_html=True)

        st.markdown('<div class="smms-card">', unsafe_allow_html=True)
        st.subheader("Doctors")
        for row in doctors[:8]:
            st.write(f"**{row[1]}**")
            st.caption(f"{row[4] or 'General Medicine'} - {row[6]} patient(s)")
        if not doctors:
            st.info("No doctor account exists.")
        st.markdown("</div>", unsafe_allow_html=True)
