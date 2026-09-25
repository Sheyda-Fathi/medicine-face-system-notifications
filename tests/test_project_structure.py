"""Static checks for presentation-critical features."""

import ast
from pathlib import Path
import unittest

ROOT = Path(__file__).resolve().parents[1]


def literal_assignment(filename, variable):
    tree = ast.parse((ROOT / filename).read_text(encoding="utf-8"))
    for node in tree.body:
        if isinstance(node, ast.Assign):
            for target in node.targets:
                if isinstance(target, ast.Name) and target.id == variable:
                    return ast.literal_eval(node.value)
    raise AssertionError(f"{variable} was not found in {filename}")


class ProjectStructureTests(unittest.TestCase):
    def test_seed_uses_doctor_names(self):
        doctors = literal_assignment("seed_database.py", "DOCTORS")
        names = {name for name, _specialty in doctors}
        self.assertIn("Reza Sharifi", names)
        self.assertIn("Sara Ahmadi", names)
        self.assertEqual(len(doctors), 12)

    def test_seed_has_patient_names(self):
        patients = literal_assignment("seed_database.py", "PATIENT_NAMES")
        self.assertIn(("Farhad", "Ahmadi"), patients)
        self.assertIn(("Zahra", "Mohammadi"), patients)
        self.assertEqual(len(patients), 24)

    def test_schema_contains_notifications_and_actual_intake_time(self):
        schema = (ROOT / "database" / "connection.py").read_text(encoding="utf-8")
        self.assertIn("CREATE TABLE IF NOT EXISTS notifications", schema)
        self.assertIn("taken_at TIMESTAMP", schema)
        self.assertIn("prescribed_by INTEGER", schema)

    def test_doctor_page_displays_actual_confirmation(self):
        page = (ROOT / "page" / "doctor_home.py").read_text(encoding="utf-8")
        self.assertIn("Latest Patient Intake Activity", page)
        self.assertIn("Actual confirmation", page)

    def test_prescription_page_creates_patient_notification(self):
        page = (ROOT / "page" / "add_medication.py").read_text(encoding="utf-8")
        self.assertIn("prescription_notification", page)
        self.assertIn("NotificationQueries().create", page)


if __name__ == "__main__":
    unittest.main()
