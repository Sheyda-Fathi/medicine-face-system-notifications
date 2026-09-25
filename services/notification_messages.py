"""Consistent patient-facing notification text."""


def prescription_notification(medicine, dosage, time_slots, doctor_name):
    times = time_slots or "No reminder time"
    title = "New prescription"
    message = (
        f"{doctor_name} prescribed {medicine} ({dosage}). "
        f"Reminder time(s): {times}."
    )
    return title, message


def appointment_notification(visit_date, visit_time, doctor_name):
    time_text = str(visit_time)[:5] if visit_time else "Time not set"
    return (
        "New appointment",
        f"{doctor_name} scheduled an appointment for {visit_date} at {time_text}.",
    )


def note_notification(doctor_name):
    return (
        "New doctor note",
        f"{doctor_name} added a new note to your medical record.",
    )
