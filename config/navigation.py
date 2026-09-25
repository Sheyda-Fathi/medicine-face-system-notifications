"""Role menus kept outside Streamlit so access rules can be tested."""

ROLE_MENUS = {
    "doctor": [
        "Dashboard",
        "Add Medication",
        "Register Patient",
        "Patient Profiles",
    ],
    "admin": [
        "Dashboard",
        "Manage Patients",
        "Manage Doctors",
        "Manage Medications",
    ],
    "patient": [
        "Home",
        "My Medications",
        "Reminders",
        "Notifications",
        "Appointments & Notes",
        "My Profile",
    ],
}


def get_role_menu(role, unread_notifications=0):
    menu = list(ROLE_MENUS.get(role, ["Home"]))
    if role == "patient" and unread_notifications:
        index = menu.index("Notifications")
        menu[index] = f"Notifications ({unread_notifications})"
    return menu


def patient_section_from_label(label):
    if label.startswith("Notifications"):
        return "notifications"
    return {
        "Home": "overview",
        "My Medications": "medications",
        "Reminders": "reminders",
        "Appointments & Notes": "appointments_notes",
        "My Profile": "profile",
    }.get(label, "overview")
