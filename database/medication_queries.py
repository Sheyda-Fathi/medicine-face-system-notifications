"""Medication catalog, prescription, interaction, and intake queries."""

from datetime import date
import logging

from database.connection import DatabaseConnection

logger = logging.getLogger(__name__)


class MedicationQueries:

    def __init__(self):
        self.db = DatabaseConnection()

    def add_medication(self, name, description):
        try:
            if not self.db.connect():
                return None
            result = self.db.execute_query(
                """
                INSERT INTO medication (name, description)
                VALUES (%s, %s)
                ON CONFLICT (name) DO UPDATE SET description = EXCLUDED.description
                RETURNING id
                """,
                (name, description or None),
            )
            row = result.fetchone() if result else None
            if not row:
                self.db.connection.rollback()
                return None
            self.db.connection.commit()
            return row[0]
        except Exception as exc:
            logger.error("Medication insert failed: %s", exc)
            if self.db.connection and not self.db.connection.closed:
                self.db.connection.rollback()
            return None
        finally:
            self.db.disconnect()

    def get_medication_id_by_name(self, name):
        try:
            if not self.db.connect():
                return None
            result = self.db.execute_query(
                "SELECT id FROM medication WHERE name = %s", (name,)
            )
            row = result.fetchone() if result else None
            return row[0] if row else None
        finally:
            self.db.disconnect()

    def get_all_medications(self, search_term=""):
        try:
            if not self.db.connect():
                return []
            if search_term:
                result = self.db.execute_query(
                    """
                    SELECT id, name, description FROM medication
                    WHERE name ILIKE %s ORDER BY name
                    """,
                    (f"%{search_term}%",),
                )
            else:
                result = self.db.execute_query(
                    "SELECT id, name, description FROM medication ORDER BY name"
                )
            return result.fetchall() if result else []
        finally:
            self.db.disconnect()

    def get_medication_usage_count(self, medication_id):
        try:
            if not self.db.connect():
                return 0
            result = self.db.execute_query(
                "SELECT COUNT(*) FROM patient_medication WHERE medication_id = %s",
                (medication_id,),
            )
            row = result.fetchone() if result else None
            return row[0] if row else 0
        finally:
            self.db.disconnect()

    def delete_medication(self, medication_id):
        try:
            if not self.db.connect():
                return False, self.db.last_error or "Database connection error."
            usage = self.db.execute_query(
                "SELECT COUNT(*) FROM patient_medication WHERE medication_id = %s",
                (medication_id,),
            )
            count = usage.fetchone()[0] if usage else 0
            if count:
                return False, f"This medicine is used in {count} patient prescription(s)."

            self.db.execute_query(
                """
                DELETE FROM medication_interaction
                WHERE medication1_id = %s OR medication2_id = %s
                """,
                (medication_id, medication_id),
            )
            result = self.db.execute_query(
                "DELETE FROM medication WHERE id = %s RETURNING id",
                (medication_id,),
            )
            if not result or not result.fetchone():
                self.db.connection.rollback()
                return False, "Medicine was not found."
            self.db.connection.commit()
            return True, None
        except Exception as exc:
            logger.error("Medication deletion failed: %s", exc)
            if self.db.connection and not self.db.connection.closed:
                self.db.connection.rollback()
            return False, str(exc)
        finally:
            self.db.disconnect()

    def assign_medication_to_patient(
        self,
        patient_id,
        medication_id,
        dosage,
        schedule,
        start_date=None,
        end_date=None,
        times_per_day=1,
        time_slots=None,
        notes="",
        prescribed_by=None,
    ):
        try:
            if not self.db.connect():
                return False
            result = self.db.execute_query(
                """
                INSERT INTO patient_medication (
                    patient_id, medication_id, dosage, schedule, start_date,
                    end_date, times_per_day, time_slots, notes, status,
                    prescribed_by
                )
                VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, 'active', %s)
                ON CONFLICT (patient_id, medication_id) DO UPDATE SET
                    dosage = EXCLUDED.dosage,
                    schedule = EXCLUDED.schedule,
                    start_date = EXCLUDED.start_date,
                    end_date = EXCLUDED.end_date,
                    times_per_day = EXCLUDED.times_per_day,
                    time_slots = EXCLUDED.time_slots,
                    notes = EXCLUDED.notes,
                    status = 'active',
                    prescribed_by = EXCLUDED.prescribed_by,
                    created_at = CURRENT_TIMESTAMP
                RETURNING id
                """,
                (
                    patient_id,
                    medication_id,
                    dosage,
                    schedule,
                    start_date,
                    end_date,
                    times_per_day,
                    time_slots,
                    notes or None,
                    prescribed_by,
                ),
            )
            row = result.fetchone() if result else None
            if not row:
                self.db.connection.rollback()
                return False
            self.db.connection.commit()
            return row[0]
        except Exception as exc:
            logger.error("Prescription save failed: %s", exc)
            if self.db.connection and not self.db.connection.closed:
                self.db.connection.rollback()
            return False
        finally:
            self.db.disconnect()

    def get_patient_medications(self, patient_id):
        try:
            if not self.db.connect():
                return []
            result = self.db.execute_query(
                """
                SELECT m.id, m.name, m.description, pm.dosage, pm.schedule
                FROM patient_medication pm
                JOIN medication m ON pm.medication_id = m.id
                WHERE pm.patient_id = %s
                  AND (pm.status = 'active' OR pm.status IS NULL)
                ORDER BY m.name
                """,
                (patient_id,),
            )
            return result.fetchall() if result else []
        finally:
            self.db.disconnect()

    def get_patient_medications_with_details(self, patient_id):
        try:
            if not self.db.connect():
                return []
            result = self.db.execute_query(
                """
                SELECT m.id, m.name, m.description, pm.dosage,
                       pm.schedule, pm.created_at
                FROM patient_medication pm
                JOIN medication m ON pm.medication_id = m.id
                WHERE pm.patient_id = %s
                ORDER BY pm.created_at DESC
                """,
                (patient_id,),
            )
            return result.fetchall() if result else []
        finally:
            self.db.disconnect()

    def get_patient_medications_advanced(self, patient_id):
        try:
            if not self.db.connect():
                return []
            result = self.db.execute_query(
                """
                SELECT pm.id, m.id, m.name, m.description, pm.dosage,
                       pm.schedule, pm.start_date, pm.end_date,
                       pm.times_per_day, pm.time_slots, pm.notes,
                       pm.status, pm.created_at, pm.prescribed_by,
                       u.full_name
                FROM patient_medication pm
                JOIN medication m ON pm.medication_id = m.id
                LEFT JOIN users u ON pm.prescribed_by = u.id
                WHERE pm.patient_id = %s
                  AND (pm.status = 'active' OR pm.status IS NULL)
                ORDER BY pm.created_at DESC
                """,
                (patient_id,),
            )
            return result.fetchall() if result else []
        finally:
            self.db.disconnect()

    def update_medication_status(self, patient_medication_id, status):
        try:
            if not self.db.connect():
                return False
            result = self.db.execute_query(
                "UPDATE patient_medication SET status = %s WHERE id = %s RETURNING id",
                (status, patient_medication_id),
            )
            row = result.fetchone() if result else None
            if not row:
                self.db.connection.rollback()
                return False
            self.db.connection.commit()
            return True
        finally:
            self.db.disconnect()

    def remove_patient_medication(self, patient_id, medication_id):
        try:
            if not self.db.connect():
                return False
            result = self.db.execute_query(
                """
                DELETE FROM patient_medication
                WHERE patient_id = %s AND medication_id = %s RETURNING id
                """,
                (patient_id, medication_id),
            )
            row = result.fetchone() if result else None
            if not row:
                self.db.connection.rollback()
                return False
            self.db.connection.commit()
            return True
        finally:
            self.db.disconnect()

    def record_intake(
        self,
        patient_medication_id,
        intake_date,
        intake_time,
        taken=True,
        notes="",
        taken_at=None,
    ):
        try:
            if not self.db.connect():
                return False
            self.db.execute_query(
                """
                INSERT INTO medication_intake (
                    patient_medication_id, intake_date, intake_time,
                    taken, taken_at, notes
                )
                VALUES (
                    %s, %s, %s, %s,
                    CASE WHEN %s THEN COALESCE(%s, CURRENT_TIMESTAMP) ELSE NULL END,
                    %s
                )
                ON CONFLICT (patient_medication_id, intake_date, intake_time)
                DO UPDATE SET
                    taken = EXCLUDED.taken,
                    taken_at = EXCLUDED.taken_at,
                    notes = EXCLUDED.notes
                """,
                (
                    patient_medication_id,
                    intake_date,
                    intake_time,
                    taken,
                    taken,
                    taken_at,
                    notes or None,
                ),
            )
            self.db.connection.commit()
            return True
        except Exception as exc:
            logger.error("Intake save failed: %s", exc)
            if self.db.connection and not self.db.connection.closed:
                self.db.connection.rollback()
            return False
        finally:
            self.db.disconnect()

    def get_intake_status(self, patient_medication_id, target_date=None):
        target_date = target_date or date.today()
        try:
            if not self.db.connect():
                return []
            result = self.db.execute_query(
                """
                SELECT intake_time, taken, taken_at, notes
                FROM medication_intake
                WHERE patient_medication_id = %s AND intake_date = %s
                ORDER BY intake_time
                """,
                (patient_medication_id, target_date),
            )
            return result.fetchall() if result else []
        finally:
            self.db.disconnect()

    def get_patient_intake_history(self, patient_id, days=30):
        try:
            if not self.db.connect():
                return []
            result = self.db.execute_query(
                """
                SELECT mi.intake_date, mi.intake_time, m.name, pm.dosage,
                       mi.taken, mi.taken_at
                FROM medication_intake mi
                JOIN patient_medication pm ON mi.patient_medication_id = pm.id
                JOIN medication m ON pm.medication_id = m.id
                WHERE pm.patient_id = %s
                  AND mi.intake_date >= CURRENT_DATE - (%s * INTERVAL '1 day')
                ORDER BY mi.intake_date DESC, mi.intake_time DESC
                """,
                (patient_id, int(days)),
            )
            return result.fetchall() if result else []
        finally:
            self.db.disconnect()

    def get_recent_intake_for_doctor(self, doctor_id, limit=15):
        try:
            if not self.db.connect():
                return []
            result = self.db.execute_query(
                """
                SELECT p.first_name, p.last_name, m.name, pm.dosage,
                       mi.intake_date, mi.intake_time, mi.taken, mi.taken_at
                FROM medication_intake mi
                JOIN patient_medication pm ON mi.patient_medication_id = pm.id
                JOIN medication m ON pm.medication_id = m.id
                JOIN patient p ON pm.patient_id = p.id
                WHERE p.registered_by = %s
                ORDER BY COALESCE(
                    mi.taken_at,
                    mi.intake_date + mi.intake_time
                ) DESC
                LIMIT %s
                """,
                (doctor_id, int(limit)),
            )
            return result.fetchall() if result else []
        finally:
            self.db.disconnect()

    def check_medication_interactions(self, patient_id, new_medication_id):
        try:
            if not self.db.connect():
                return []
            result = self.db.execute_query(
                """
                SELECT m1.name, m2.name, mi.severity, mi.description
                FROM medication_interaction mi
                JOIN medication m1 ON mi.medication1_id = m1.id
                JOIN medication m2 ON mi.medication2_id = m2.id
                WHERE (
                    mi.medication1_id = %s AND mi.medication2_id IN (
                        SELECT medication_id FROM patient_medication
                        WHERE patient_id = %s
                          AND (status = 'active' OR status IS NULL)
                    )
                ) OR (
                    mi.medication2_id = %s AND mi.medication1_id IN (
                        SELECT medication_id FROM patient_medication
                        WHERE patient_id = %s
                          AND (status = 'active' OR status IS NULL)
                    )
                )
                """,
                (new_medication_id, patient_id, new_medication_id, patient_id),
            )
            rows = result.fetchall() if result else []
            return [
                {
                    "med1": row[0],
                    "med2": row[1],
                    "severity": row[2],
                    "description": row[3],
                }
                for row in rows
            ]
        except Exception as exc:
            logger.error("Interaction check failed: %s", exc)
            return []
        finally:
            self.db.disconnect()

    def get_adherence_stats(self, days=7, doctor_id=None):
        try:
            if not self.db.connect():
                return []
            query = """
                SELECT mi.intake_date,
                       SUM(CASE WHEN mi.taken THEN 1 ELSE 0 END) AS taken,
                       SUM(CASE WHEN NOT mi.taken THEN 1 ELSE 0 END) AS missed
                FROM medication_intake mi
                JOIN patient_medication pm ON mi.patient_medication_id = pm.id
                JOIN patient p ON pm.patient_id = p.id
                WHERE mi.intake_date >= CURRENT_DATE - (%s * INTERVAL '1 day')
            """
            params = [int(days)]
            if doctor_id is not None:
                query += " AND p.registered_by = %s"
                params.append(doctor_id)
            query += " GROUP BY mi.intake_date ORDER BY mi.intake_date"
            result = self.db.execute_query(query, tuple(params))
            return result.fetchall() if result else []
        finally:
            self.db.disconnect()

    def get_today_pending_intakes(self, patient_id):
        today = date.today()
        try:
            if not self.db.connect():
                return []
            result = self.db.execute_query(
                """
                SELECT pm.id, m.name, pm.dosage, pm.time_slots, pm.times_per_day
                FROM patient_medication pm
                JOIN medication m ON pm.medication_id = m.id
                WHERE pm.patient_id = %s
                  AND (pm.status = 'active' OR pm.status IS NULL)
                  AND (pm.start_date IS NULL OR pm.start_date <= %s)
                  AND (pm.end_date IS NULL OR pm.end_date >= %s)
                """,
                (patient_id, today, today),
            )
            return result.fetchall() if result else []
        finally:
            self.db.disconnect()
