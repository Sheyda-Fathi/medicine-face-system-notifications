from database.connection import DatabaseConnection


def scalar(db, query, params=()):
    result = db.execute_query(query, params)
    row = result.fetchone() if result else None
    return row[0] if row else None


def require(condition, message):
    if not condition:
        raise AssertionError(message)
    print(f"PASS: {message}")


def main():
    db = DatabaseConnection()
    require(db.connect(), "Database connection succeeds")
    try:
        require(
            scalar(db, "SELECT COUNT(*) FROM users WHERE username = 'admin'") == 1,
            "Administrator account exists",
        )
        require(
            scalar(
                db,
                "SELECT COUNT(*) FROM users WHERE username = 'dr.reza.sharifi'",
            ) == 1,
            "Dr. Reza Sharifi account exists",
        )
        require(
            scalar(
                db,
                """
                SELECT COUNT(*) FROM patient
                WHERE national_code BETWEEN '7000000001' AND '7000000024'
                """,
            ) == 24,
            "All 24  demo patients exist",
        )
        require(
            scalar(
                db,
                """
                SELECT COUNT(*)
                FROM patient p
                JOIN users u ON p.registered_by = u.id
                WHERE u.username = 'dr.reza.sharifi'
                  AND p.national_code BETWEEN '7000000001' AND '7000000024'
                """,
            ) == 2,
            "Dr. Reza Sharifi has two demo patients",
        )
        require(
            scalar(
                db,
                """
                SELECT COUNT(*) FROM patient_medication pm
                JOIN patient p ON pm.patient_id = p.id
                WHERE p.national_code BETWEEN '7000000001' AND '7000000024'
                """,
            ) >= 48,
            "Demo patients have active prescriptions",
        )
        require(
            scalar(
                db,
                """
                SELECT COUNT(*) FROM notifications n
                JOIN patient p ON n.patient_id = p.id
                WHERE p.national_code BETWEEN '7000000001' AND '7000000024'
                """,
            ) >= 96,
            "Prescription, appointment, and note notifications exist",
        )
        require(
            scalar(
                db,
                """
                SELECT COUNT(*) FROM medication_intake mi
                JOIN patient_medication pm ON mi.patient_medication_id = pm.id
                JOIN patient p ON pm.patient_id = p.id
                WHERE p.national_code BETWEEN '7000000001' AND '7000000024'
                  AND mi.taken = TRUE
                  AND mi.taken_at IS NOT NULL
                """,
            ) > 0,
            "Taken doses contain actual confirmation timestamps",
        )
        require(
            scalar(
                db,
                """
                SELECT COUNT(*) FROM appointments a
                JOIN users u ON a.doctor_id = u.id
                WHERE u.username = 'dr.reza.sharifi'
                  AND a.visit_date = CURRENT_DATE
                """,
            ) >= 1,
            "Dr. Reza Sharifi has an appointment today",
        )
    finally:
        db.disconnect()

    print("\nDatabase smoke test completed successfully.")


if __name__ == "__main__":
    main()
