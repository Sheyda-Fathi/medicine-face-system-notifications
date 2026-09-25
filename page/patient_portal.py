"""Simple face-authenticated portal for elderly patients."""

from datetime import date, datetime
from pathlib import Path

import pandas as pd
import streamlit as st

from config.theme import render_header, stat_card
from database.appointment_queries import AppointmentQueries
from database.medication_queries import MedicationQueries
from database.notes_queries import NotesQueries
from database.notification_queries import NotificationQueries
from database.patient_queries import PatientQueries
from services.medication_schedule import dose_status, format_recorded_at, parse_time_slots


def _get_patient(user):
    patient_id = user.get("patient_id")
    if not patient_id:
        st.error("This login session is not linked to a patient record.")
        st.stop()
    patient = PatientQueries().get_patient_by_id(patient_id)
    if not patient:
        st.error("The patient record no longer exists.")
        st.stop()
    return patient


def _today_schedule(medications):
    items = []
    for medication in medications:
        for slot in parse_time_slots(medication[9]):
            items.append((slot, medication[0], medication[2], medication[4], medication[10]))
    return sorted(items)


def _dose_records(medication_db, prescription_id):
    return {
        str(row[0])[:5]: (bool(row[1]), row[2])
        for row in medication_db.get_intake_status(prescription_id, date.today())
    }


def _render_overview(patient, medications, medication_db):
    render_header(
        f"Welcome, {patient['first_name']}",
        "Your medicines, notifications, and next appointment",
    )

    schedule = _today_schedule(medications)
    upcoming = AppointmentQueries().get_upcoming_for_patient(patient["id"])
    notifications = NotificationQueries().get_for_patient(patient["id"], limit=3)

    remaining = 0
    for slot, prescription_id, _name, _dosage, _instruction in schedule:
        taken, _taken_at = _dose_records(medication_db, prescription_id).get(
            slot, (None, None)
        )
        if taken is not True:
            remaining += 1

    card_1, card_2, card_3 = st.columns(3)
    stat_card(card_1, "stat-purple", "MEDICINES", "Active Medicines", len(medications), "prescribed")
    stat_card(card_2, "stat-pink", "TODAY", "Remaining Doses", remaining, "not confirmed")
    stat_card(card_3, "stat-blue", "VISIT", "Next Appointment", upcoming[0] if upcoming else "None", "scheduled date")

    left, right = st.columns([2, 1])
    with left:
        st.markdown('<div class="smms-card">', unsafe_allow_html=True)
        st.subheader("Today's Medicines")
        if schedule:
            for slot, prescription_id, name, dosage, instruction in schedule:
                taken, taken_at = _dose_records(medication_db, prescription_id).get(
                    slot, (None, None)
                )
                status = dose_status(slot, taken=taken)
                st.markdown(f"### {slot} - {name}")
                st.write(f"Dosage: **{dosage}**")
                if instruction:
                    st.write(f"Instruction: {instruction}")
                st.write(f"Status: **{status}**")
                if taken_at:
                    st.caption(f"Confirmed at {format_recorded_at(taken_at)}")
                st.divider()
        else:
            st.info("No medicine reminders are configured for today.")
        st.markdown("</div>", unsafe_allow_html=True)

    with right:
        st.markdown('<div class="smms-card">', unsafe_allow_html=True)
        st.subheader("Next Appointment")
        if upcoming:
            visit_date, visit_time, reason, doctor_name = upcoming
            st.markdown(f"## {visit_date}")
            st.write(f"Time: **{visit_time or 'Not set'}**")
            st.write(f"Doctor: **{doctor_name or 'Not assigned'}**")
            st.write(reason or "Follow-up visit")
        else:
            st.info("No upcoming appointment is scheduled.")
        st.markdown("</div>", unsafe_allow_html=True)

        st.markdown('<div class="smms-card">', unsafe_allow_html=True)
        st.subheader("Latest Notifications")
        if notifications:
            for _id, _kind, title, message, _related, is_read, created_at in notifications:
                marker = "Read" if is_read else "New"
                st.write(f"**{title}** - {marker}")
                st.caption(f"{message}\n\n{created_at}")
        else:
            st.info("No notification is available.")
        st.markdown("</div>", unsafe_allow_html=True)


def _render_medications(medications):
    render_header("My Medications", "Your current prescriptions")
    if not medications:
        st.info("No medicine is currently prescribed.")
        return
    for medication in medications:
        st.markdown('<div class="smms-card">', unsafe_allow_html=True)
        st.markdown(f"## {medication[2]}")
        st.markdown(f"### Dosage: {medication[4]}")
        st.write(f"Reminder times: {medication[9] or 'Not configured'}")
        st.write(f"Start date: {medication[6] or 'Immediate'}")
        st.write(f"End date: {medication[7] or 'Ongoing'}")
        if medication[10]:
            st.info(f"Doctor instruction: {medication[10]}")
        if len(medication) > 14 and medication[14]:
            st.caption(f"Prescribed by {medication[14]}")
        st.markdown("</div>", unsafe_allow_html=True)


def _render_reminders(patient, medications, medication_db):
    render_header("Reminders", "Confirm a medicine after you take it")
    schedule = _today_schedule(medications)
    if not schedule:
        st.info("No medicine reminder is configured for today.")

    for slot, prescription_id, name, dosage, instruction in schedule:
        taken, taken_at = _dose_records(medication_db, prescription_id).get(
            slot, (None, None)
        )
        status = dose_status(slot, taken=taken)
        st.markdown('<div class="smms-card">', unsafe_allow_html=True)
        st.markdown(f"## {slot} - {name}")
        st.markdown(f"### {dosage}")
        if instruction:
            st.write(instruction)
        st.write(f"Status: **{status}**")

        if taken:
            st.success(f"Confirmed at {format_recorded_at(taken_at)}")
        elif st.button(
            "I took this medicine now",
            key=f"patient_take_{prescription_id}_{slot}",
            type="primary",
            use_container_width=True,
        ):
            saved = medication_db.record_intake(
                prescription_id,
                date.today(),
                datetime.strptime(slot, "%H:%M").time(),
                taken=True,
                notes="Confirmed by patient portal",
            )
            if saved:
                st.rerun()
            st.error("The dose confirmation could not be saved.")
        st.markdown("</div>", unsafe_allow_html=True)

    st.subheader("Recent Intake History")
    history = medication_db.get_patient_intake_history(patient["id"], days=14)
    if history:
        rows = [
            {
                "Date": row[0],
                "Scheduled": row[1],
                "Medicine": row[2],
                "Dosage": row[3],
                "Status": "Taken" if row[4] else "Missed",
                "Actual confirmation": format_recorded_at(row[5]),
            }
            for row in history
        ]
        st.dataframe(pd.DataFrame(rows), use_container_width=True, hide_index=True)
    else:
        st.info("No intake history has been recorded yet.")


def _render_notifications(patient):
    render_header("Notifications", "New prescriptions, appointments, and doctor notes")
    notification_db = NotificationQueries()
    notifications = notification_db.get_for_patient(patient["id"], limit=100)
    if not notifications:
        st.info("No notification is available.")
        return

    unread = any(not row[5] for row in notifications)
    if unread and st.button("Mark all as read"):
        notification_db.mark_all_read(patient["id"])
        st.rerun()

    for notification_id, notification_type, title, message, _related, is_read, created_at in notifications:
        st.markdown('<div class="smms-card">', unsafe_allow_html=True)
        st.markdown(f"### {title}")
        st.caption(f"{notification_type.replace('_', ' ').title()} - {created_at}")
        st.write(message)
        if is_read:
            st.caption("Read")
        elif st.button("Mark as read", key=f"read_notification_{notification_id}"):
            notification_db.mark_read(notification_id, patient["id"])
            st.rerun()
        st.markdown("</div>", unsafe_allow_html=True)


def _render_appointments_notes(patient):
    render_header("Appointments & Notes", "Visits and recommendations from your doctor")
    appointment_tab, note_tab = st.tabs(["Appointments", "Doctor Notes"])
    with appointment_tab:
        appointments = AppointmentQueries().get_for_patient(patient["id"])
        if appointments:
            for _id, visit_date, visit_time, status, reason, doctor_name, _doctor_id in appointments:
                st.markdown('<div class="smms-card">', unsafe_allow_html=True)
                st.markdown(f"## {visit_date}")
                st.write(f"Time: **{visit_time or 'Not set'}**")
                st.write(f"Doctor: **{doctor_name or 'Not assigned'}**")
                st.write(f"Status: **{status.capitalize()}**")
                st.write(reason or "No reason was recorded.")
                st.markdown("</div>", unsafe_allow_html=True)
        else:
            st.info("No appointment is recorded.")

    with note_tab:
        notes = NotesQueries().get_notes_for_patient(patient["id"])
        if notes:
            for _note_id, note_text, created_at, doctor_name, _doctor_id in notes:
                st.markdown('<div class="smms-card">', unsafe_allow_html=True)
                st.markdown(f"### {doctor_name or 'Doctor'}")
                st.write(note_text)
                st.caption(str(created_at))
                st.markdown("</div>", unsafe_allow_html=True)
        else:
            st.info("No doctor note is available.")


def _render_profile(patient):
    render_header("My Profile", "Your registered information")
    photo_col, detail_col = st.columns([1, 2])
    with photo_col:
        path = patient.get("image_path")
        if path and Path(path).exists():
            st.image(path, width=260)
        else:
            st.info("No photograph is stored.")
    with detail_col:
        fields = {
            "Name": f"{patient['first_name']} {patient['last_name']}",
            "National code": patient["national_code"],
            "Phone": patient.get("phone") or "Not provided",
            "Age": patient.get("age") or "Not provided",
            "Gender": patient.get("gender") or "Not provided",
            "Blood group": patient.get("blood_group") or "Not provided",
            "Assigned doctor": patient.get("doctor_name") or "Unassigned",
            "Emergency contact": patient.get("emergency_contact") or "Not provided",
        }
        for label, value in fields.items():
            st.markdown(f"### {label}: {value}")
    st.info("Ask your doctor or the administrator to correct registered information.")


def show_patient_portal(user, section="overview"):
    patient = _get_patient(user)
    medication_db = MedicationQueries()
    medications = medication_db.get_patient_medications_advanced(patient["id"])
    renderers = {
        "overview": lambda: _render_overview(patient, medications, medication_db),
        "medications": lambda: _render_medications(medications),
        "reminders": lambda: _render_reminders(patient, medications, medication_db),
        "notifications": lambda: _render_notifications(patient),
        "appointments_notes": lambda: _render_appointments_notes(patient),
        "profile": lambda: _render_profile(patient),
    }
    renderers.get(section, renderers["overview"])()
