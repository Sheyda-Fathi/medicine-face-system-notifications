"""Medication reminder logic tests."""

from datetime import date, datetime
import unittest

from services.medication_schedule import dose_status, format_recorded_at, parse_time_slots


class MedicationScheduleTests(unittest.TestCase):
    def test_time_slots_are_valid_unique_and_sorted(self):
        self.assertEqual(
            parse_time_slots("20:00, 08:00, bad, 08:00, 13:30"),
            ["08:00", "13:30", "20:00"],
        )

    def test_taken_record_overrides_clock(self):
        now = datetime(2026, 7, 26, 7, 0)
        self.assertEqual(dose_status("20:00", taken=True, now=now), "Taken")

    def test_explicit_missed_record_is_missed(self):
        now = datetime(2026, 7, 26, 7, 0)
        self.assertEqual(dose_status("20:00", taken=False, now=now), "Missed")

    def test_unrecorded_past_dose_is_missed(self):
        now = datetime(2026, 7, 26, 12, 0)
        self.assertEqual(
            dose_status("08:00", now=now, target_date=date(2026, 7, 26)),
            "Missed",
        )

    def test_unrecorded_future_dose_is_pending(self):
        now = datetime(2026, 7, 26, 12, 0)
        self.assertEqual(
            dose_status("20:00", now=now, target_date=date(2026, 7, 26)),
            "Pending",
        )

    def test_actual_confirmation_format(self):
        value = datetime(2026, 7, 26, 8, 12, 5)
        self.assertEqual(format_recorded_at(value), "2026-07-26 08:12:05")


if __name__ == "__main__":
    unittest.main()
