"""Role menu tests."""

import unittest

from config.navigation import ROLE_MENUS, get_role_menu, patient_section_from_label


class NavigationTests(unittest.TestCase):
    def test_doctor_menu_contains_only_clinical_tools(self):
        self.assertEqual(
            ROLE_MENUS["doctor"],
            ["Dashboard", "Add Medication", "Register Patient", "Patient Profiles"],
        )

    def test_admin_menu_contains_management_tools(self):
        self.assertEqual(
            ROLE_MENUS["admin"],
            ["Dashboard", "Manage Patients", "Manage Doctors", "Manage Medications"],
        )

    def test_patient_menu_includes_notifications(self):
        self.assertIn("Notifications", ROLE_MENUS["patient"])
        self.assertEqual(
            patient_section_from_label("Notifications (4)"),
            "notifications",
        )

    def test_unread_count_does_not_change_base_menu(self):
        menu = get_role_menu("patient", unread_notifications=3)
        self.assertIn("Notifications (3)", menu)
        self.assertIn("Notifications", ROLE_MENUS["patient"])


if __name__ == "__main__":
    unittest.main()
