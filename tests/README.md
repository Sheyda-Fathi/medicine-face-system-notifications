# Tests

## Pure Automated Tests

These tests do not change the database:

```bash
python -m unittest discover -s tests -p "test_*.py" -v
```

They check role menus, reminder status rules, notification text, demonstration constants, schema features, and the doctor intake-time display.

## Seeded Database Smoke Test

After running `python seed_database.py --reset-demo`, run:

```bash
python tests/database_smoke_test.py
```

This read-only test confirms the administrator, Dr. Reza Sharifi, 24  patients, prescriptions, notifications, actual intake timestamps, and today's doctor appointment.

Camera and end-to-end role behavior are covered by `documents/PRESENTATION_TEST_PLAN.md` because they require a real face and the target computer's camera.
