"""Patient notification text tests."""

import unittest

from services.notification_messages import (
    appointment_notification,
    note_notification,
    prescription_notification,
)


class NotificationMessageTests(unittest.TestCase):
    def test_prescription_message_has_required_details(self):
        title, message = prescription_notification(
            "Metformin", "500 mg", "08:00, 20:00", "Dr. Reza Sharifi"
        )
        self.assertEqual(title, "New prescription")
        self.assertIn("Metformin", message)
        self.assertIn("500 mg", message)
        self.assertIn("08:00, 20:00", message)
        self.assertIn("Dr. Reza Sharifi", message)

    def test_appointment_message_has_date_and_time(self):
        title, message = appointment_notification(
            "2026-08-15", "10:30", "Dr. Reza Sharifi"
        )
        self.assertEqual(title, "New appointment")
        self.assertIn("2026-08-15", message)
        self.assertIn("10:30", message)

    def test_note_notification_does_not_copy_clinical_text(self):
        title, message = note_notification("Dr. Reza Sharifi")
        self.assertEqual(title, "New doctor note")
        self.assertIn("medical record", message)


if __name__ == "__main__":
    unittest.main()
