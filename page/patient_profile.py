"""Role-aware patient profiles and clinical record management."""

import io
from datetime import date, datetime
from pathlib import Path

import pandas as pd
import streamlit as st # type: ignore
from PIL import Image, ImageOps

from config.settings import PATIENT_IMAGES_DIR
from database.appointment_queries import AppointmentQueries
from database.auth_queries import AuthQueries
from database.medication_queries import MedicationQueries
from database.notes_queries import NotesQueries
from database.notification_queries import NotificationQueries
from database.patient_queries import PatientQueries
from face.encoding import FaceEncoding
from services.medication_schedule import dose_status, format_recorded_at, parse_time_slots
from services.notification_messages import appointment_notification, note_notification

_MAX_PHOTO_SIDE = 900


def _prepare_image_from_bytes(raw_bytes, max_side=_MAX_PHOTO_SIDE):
    image = Image.open(io.BytesIO(raw_bytes))
    image = ImageOps.exif_transpose(image)
    image = image.convert("RGB")
    image.thumbnail((max_side, max_side))
    return image


def _doctor_scope(user):
    return user.get("id") if user.get("role") == "doctor" else None


def _select_patient(patient_db, user):
    doctor_id = _doctor_scope(user)
    search_term = st.text_input("Search by name or national code")
    patients = (
        patient_db.search_patients(search_term.strip(), doctor_id=doctor_id)
        if search_term.strip()
        else patient_db.get_all_patients(doctor_id=doctor_id)
    )
    if not patients:
        st.warning("No matching patient is available for this account.")
        return None

    options = {
        f"{row[1]} {row[2]} - {row[3]}": row[0] for row in patients
    }
    default_id = st.session_state.get("selected_patient_id")
    default_index = 0
    if default_id in options.values():
        default_index = list(options.values()).index(default_id)
    selected = st.selectbox("Patient", list(options), index=default_index)
    return options[selected]


def _render_overview(patient):
    photo_col, detail_col, appointment_col = st.columns([1, 2, 1])
    with photo_col:
        image_path = patient.get("image_path")
        if image_path and Path(image_path).exists():
            st.image(image_path, width=220)
        elif image_path:
            st.warning(
                "The photograph record exists, but the image file could not "
                "be found. Use Edit Record to upload it again."
            )
        else:
            st.info("No patient photograph is stored.")

    with detail_col:
        st.subheader(f"{patient['first_name']} {patient['last_name']}")
        details = {
            "National code": patient["national_code"],
            "Phone": patient.get("phone") or "Not provided",
            "Age": patient.get("age") or "Not provided",
            "Gender": patient.get("gender") or "Not provided",
            "Blood group": patient.get("blood_group") or "Not provided",
            "Height": f"{patient['height_cm']} cm" if patient.get("height_cm") else "Not provided",
            "Weight": f"{patient['weight_kg']} kg" if patient.get("weight_kg") else "Not provided",
            "Emergency contact": patient.get("emergency_contact") or "Not provided",
            "Assigned doctor": patient.get("doctor_name") or "Unassigned",
        }
        for label, value in details.items():
            st.write(f"**{label}:** {value}")
        if patient.get("address"):
            st.write(f"**Address:** {patient['address']}")

    with appointment_col:
        st.subheader("Next Appointment")
        upcoming = AppointmentQueries().get_upcoming_for_patient(patient["id"])
        if upcoming:
            visit_date, visit_time, reason, doctor_name = upcoming
            st.write(f"**Date:** {visit_date}")
            st.write(f"**Time:** {visit_time or 'Not set'}")
            st.write(f"**Doctor:** {doctor_name or 'Unassigned'}")
            st.caption(reason or "Follow-up visit")
        else:
            st.info("No upcoming appointment is scheduled.")


def _render_prescriptions(patient_id, user):
    medication_db = MedicationQueries()
    medications = medication_db.get_patient_medications_advanced(patient_id)
    if not medications:
        st.info("No active medication is prescribed.")
        return

    rows = []
    for item in medications:
        rows.append(
            {
                "Medicine": item[2],
                "Dosage": item[4],
                "Schedule": item[5],
                "Start": item[6],
                "End": item[7],
                "Status": item[11] or "active",
            }
        )
    st.dataframe(pd.DataFrame(rows), use_container_width=True, hide_index=True)

    for item in medications:
        prescription_id, medication_id, name = item[0], item[1], item[2]
        with st.expander(f"{name} - {item[4]}"):
            st.write(f"Description: {item[3] or 'Not provided'}")
            st.write(f"Reminder times: {item[9] or 'Not configured'}")
            st.write(f"Doctor instruction: {item[10] or 'None'}")
            if user.get("role") == "doctor":
                if st.button(
                    "Remove prescription",
                    key=f"remove_prescription_{prescription_id}",
                ):
                    if medication_db.remove_patient_medication(patient_id, medication_id):
                        st.success("Prescription removed.")
                        st.rerun()
                    else:
                        st.error("Prescription could not be removed.")


def _render_adherence(patient_id):
    medication_db = MedicationQueries()
    medications = medication_db.get_patient_medications_advanced(patient_id)
    st.subheader("Today's Reminder Status")

    today_rows = []
    for medication in medications:
        records = {
            str(row[0])[:5]: (bool(row[1]), row[2])
            for row in medication_db.get_intake_status(medication[0], date.today())
        }
        for slot in parse_time_slots(medication[9]):
            taken, taken_at = records.get(slot, (None, None))
            today_rows.append(
                {
                    "Scheduled": slot,
                    "Medicine": medication[2],
                    "Dosage": medication[4],
                    "Status": dose_status(slot, taken=taken),
                    "Patient confirmed at": format_recorded_at(taken_at),
                }
            )
    if today_rows:
        st.dataframe(
            pd.DataFrame(today_rows).sort_values("Scheduled"),
            use_container_width=True,
            hide_index=True,
        )
    else:
        st.info("No reminder times are configured for today.")

    st.subheader("Recent Intake History")
    history = medication_db.get_patient_intake_history(patient_id, days=30)
    if history:
        history_rows = [
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
        st.dataframe(
            pd.DataFrame(history_rows), use_container_width=True, hide_index=True
        )
    else:
        st.info("No medication intake history has been recorded.")


def _render_appointments_and_notes(patient_id, user):
    appointment_db = AppointmentQueries()
    notes_db = NotesQueries()

    appointment_col, note_col = st.columns(2)
    with appointment_col:
        st.subheader("Appointments")
        if user.get("role") == "doctor":
            with st.form(f"new_appointment_{patient_id}"):
                visit_date = st.date_input(
                    "Appointment date", value=date.today(),
                    min_value=date.today(),
                )
                visit_time = st.time_input("Appointment time")
                reason = st.text_input("Reason", placeholder="Example: Follow-up visit")
                save_appointment = st.form_submit_button(
                    "Schedule appointment", type="primary"
                )
            if save_appointment:
                appointment_id = appointment_db.add_appointment(
                    patient_id, user["id"], visit_date, visit_time,
                    status="scheduled", reason=reason.strip(),
                )
                if appointment_id:
                    title, message = appointment_notification(
                        visit_date, visit_time, user["full_name"]
                    )
                    notification_id = NotificationQueries().create(
                        patient_id,
                        "appointment",
                        title,
                        message,
                        related_id=appointment_id,
                    )
                    if notification_id:
                        st.success("Appointment scheduled and patient notified.")
                    else:
                        st.warning(
                            "The appointment was saved, but its notification failed."
                        )
                else:
                    st.error("Appointment could not be scheduled.")

        appointments = appointment_db.get_for_patient(patient_id)
        if appointments:
            for appointment_id, visit_date, visit_time, status, reason, doctor_name, appointment_doctor_id in appointments:
                with st.expander(f"{visit_date} - {status.capitalize()}"):
                    st.write(f"Time: {visit_time or 'Not set'}")
                    st.write(f"Doctor: {doctor_name or 'Former or unassigned doctor'}")
                    st.write(f"Reason: {reason or 'Not provided'}")
                    if (
                        user.get("role") == "doctor"
                        and status == "scheduled"
                        and appointment_doctor_id == user.get("id")
                    ):
                        complete_col, cancel_col = st.columns(2)
                        with complete_col:
                            if st.button(
                                "Mark completed",
                                key=f"complete_appointment_{appointment_id}",
                            ):
                                appointment_db.update_status(
                                    appointment_id, "completed", doctor_id=user["id"]
                                )
                                st.rerun()
                        with cancel_col:
                            if st.button(
                                "Cancel",
                                key=f"cancel_appointment_{appointment_id}",
                            ):
                                appointment_db.update_status(
                                    appointment_id, "cancelled", doctor_id=user["id"]
                                )
                                st.rerun()
        else:
            st.info("No appointments are recorded.")

    with note_col:
        st.subheader("Doctor Notes")
        if user.get("role") == "doctor":
            with st.form(f"new_note_{patient_id}"):
                note_text = st.text_area("New clinical note")
                save_note = st.form_submit_button("Save note", type="primary")
            if save_note:
                if not note_text.strip():
                    st.warning("Enter a note before saving.")
                else:
                    note_id = notes_db.add_note(
                        patient_id, user["id"], note_text.strip()
                    )
                    if note_id:
                        title, message = note_notification(user["full_name"])
                        notification_id = NotificationQueries().create(
                            patient_id,
                            "doctor_note",
                            title,
                            message,
                            related_id=note_id,
                        )
                        if notification_id:
                            st.success("Note saved and patient notified.")
                        else:
                            st.warning("The note was saved, but its notification failed.")
                    else:
                        st.error("Note could not be saved.")

        notes = notes_db.get_notes_for_patient(patient_id)
        if notes:
            for note_id, note_text, created_at, doctor_name, doctor_id in notes:
                with st.expander(f"{created_at} - {doctor_name or 'Former doctor'}"):
                    st.write(note_text)
                    if user.get("role") == "doctor" and doctor_id == user.get("id"):
                        if st.button("Delete note", key=f"delete_note_{note_id}"):
                            notes_db.delete_note(note_id, doctor_id=user["id"])
                            st.rerun()
        else:
            st.info("No doctor notes are available.")


def _render_edit(patient_db, patient, user):
    doctor_options = {"Unassigned": None}
    if user.get("role") == "admin":
        doctor_options.update(
            {
                f"{name} ({specialty or 'General Medicine'})": doctor_id
                for doctor_id, name, specialty in AuthQueries().get_all_doctors()
            }
        )

    with st.form(f"edit_patient_{patient['id']}"):
        first_name = st.text_input("First name", value=patient["first_name"])
        last_name = st.text_input("Last name", value=patient["last_name"])
        phone = st.text_input("Phone", value=patient.get("phone") or "")
        age = st.number_input(
            "Age", min_value=0, max_value=120,
            value=int(patient.get("age") or 0),
        )
        gender_values = ["Female", "Male", "Other"]
        current_gender = patient.get("gender")
        gender_index = gender_values.index(current_gender) if current_gender in gender_values else 0
        gender = st.selectbox("Gender", gender_values, index=gender_index)
        address = st.text_input("Address", value=patient.get("address") or "")
        emergency_contact = st.text_input(
            "Emergency contact", value=patient.get("emergency_contact") or ""
        )

        assigned_doctor = patient.get("registered_by")
        if user.get("role") == "admin":
            labels = list(doctor_options)
            selected_index = 0
            for index, value in enumerate(doctor_options.values()):
                if value == assigned_doctor:
                    selected_index = index
                    break
            doctor_label = st.selectbox("Assigned doctor", labels, index=selected_index)
            assigned_doctor = doctor_options[doctor_label]

        save_details = st.form_submit_button("Save patient details", type="primary")

    if save_details:
        if not first_name.strip() or not last_name.strip():
            st.error("First and last name are required.")
        elif patient_db.update_patient(
            patient["id"],
            first_name=first_name.strip(),
            last_name=last_name.strip(),
            phone=phone.strip(),
            age=int(age),
            gender=gender,
            address=address.strip(),
            emergency_contact=emergency_contact.strip(),
            registered_by=assigned_doctor,
        ):
            st.success("Patient details updated.")
            st.rerun()
        else:
            st.error("Patient details could not be updated.")

    st.subheader("Replace Face Photograph")

    upload_version_key = f"photo_upload_version_{patient['id']}"
    if upload_version_key not in st.session_state:
        st.session_state[upload_version_key] = 0

    new_photo = st.file_uploader(
        "New face photograph", type=["jpg", "jpeg", "png"],
        key=f"new_photo_{patient['id']}_{st.session_state[upload_version_key]}",
    )
    if new_photo:
        try:
            preview_image = _prepare_image_from_bytes(new_photo.getvalue())
            st.image(preview_image, width=180)
        except Exception:
            st.error("The selected image could not be opened.")
            preview_image = None

        if preview_image is not None and st.button(
            "Save new face photograph", type="primary",
            key=f"save_photo_{patient['id']}",
        ):
            with st.spinner("Validating the new face photograph..."):
                encoding_buffer = io.BytesIO()
                preview_image.save(encoding_buffer, format="JPEG")
                encoding_buffer.seek(0)
                encoding, error = FaceEncoding.get_face_encoding_with_validation(
                    encoding_buffer
                )
            if error:
                st.error(error)
            else:
                filename = f"{patient['national_code']}_{datetime.now():%Y%m%d_%H%M%S}.jpg"
                new_path = Path(PATIENT_IMAGES_DIR) / filename
                preview_image.save(new_path, format="JPEG")
                if patient_db.update_patient_photo(
                    patient["id"], str(new_path),
                    FaceEncoding.encoding_to_string(encoding),
                ):
                    old_path = patient.get("image_path")
                    if old_path and Path(old_path) != new_path:
                        Path(old_path).unlink(missing_ok=True)
                    st.success("Face photograph updated.")
                    st.session_state[upload_version_key] += 1
                    st.rerun()
                else:
                    new_path.unlink(missing_ok=True)
                    st.error("Face photograph could not be updated.")

    if user.get("role") == "admin":
        st.divider()
        st.subheader("Delete Patient")
        confirm = st.checkbox(
            "I understand that this permanently removes the patient and related records.",
            key=f"confirm_delete_patient_{patient['id']}",
        )
        if st.button("Delete patient", key=f"delete_patient_{patient['id']}"):
            if not confirm:
                st.warning("Confirm permanent deletion before continuing.")
            elif patient_db.delete_patient(patient["id"]):
                image_path = patient.get("image_path")
                if image_path:
                    Path(image_path).unlink(missing_ok=True)
                st.session_state.selected_patient_id = None
                st.success("Patient deleted.")
                st.rerun()
            else:
                st.error("Patient could not be deleted.")


def show_patient_profile(user=None, embedded=False):
    user = user or st.session_state.get("user") or {}
    if user.get("role") not in ("doctor", "admin"):
        st.error("Staff access is required.")
        return

    if not embedded:
        st.title("Patient Profiles")
        st.caption(
            "Patient information, prescriptions, reminders, appointments, and notes."
        )
        st.divider()

    patient_db = PatientQueries()
    patient_id = _select_patient(patient_db, user)
    if not patient_id:
        return

    st.session_state.selected_patient_id = patient_id
    patient = patient_db.get_patient_by_id(
        patient_id, doctor_id=_doctor_scope(user)
    )
    if not patient:
        st.error("The selected patient is not available for this account.")
        return

    overview_tab, prescription_tab, adherence_tab, clinical_tab, edit_tab = st.tabs(
        [
            "Overview",
            "Prescriptions",
            "Reminders & Adherence",
            "Appointments & Notes",
            "Edit Record",
        ]
    )
    with overview_tab:
        _render_overview(patient)
    with prescription_tab:
        _render_prescriptions(patient_id, user)
    with adherence_tab:
        _render_adherence(patient_id)
    with clinical_tab:
        _render_appointments_and_notes(patient_id, user)
    with edit_tab:
        _render_edit(patient_db, patient, user)