"""Database operations for patient appointments."""

from datetime import date
import logging

from database.connection import DatabaseConnection

logger = logging.getLogger(__name__)


class AppointmentQueries:
    def __init__(self):
        self.db = DatabaseConnection()

    def add_appointment(
        self, patient_id, doctor_id, visit_date, visit_time=None,
        status="scheduled", reason="",
    ):
        try:
            if not self.db.connect():
                return None
            result = self.db.execute_query(
                """
                INSERT INTO appointments (
                    patient_id, doctor_id, visit_date, visit_time, status, reason
                ) VALUES (%s, %s, %s, %s, %s, %s)
                RETURNING id
                """,
                (patient_id, doctor_id, visit_date, visit_time, status, reason or None),
            )
            row = result.fetchone() if result else None
            if not row:
                self.db.connection.rollback()
                return None
            self.db.connection.commit()
            return row[0]
        except Exception as exc:
            logger.error("Appointment insert failed: %s", exc)
            if self.db.connection and not self.db.connection.closed:
                self.db.connection.rollback()
            return None
        finally:
            self.db.disconnect()

    def get_for_patient(self, patient_id):
        try:
            if not self.db.connect():
                return []
            result = self.db.execute_query(
                """
                SELECT a.id, a.visit_date, a.visit_time, a.status,
                       a.reason, u.full_name, a.doctor_id
                FROM appointments a
                LEFT JOIN users u ON a.doctor_id = u.id
                WHERE a.patient_id = %s
                ORDER BY a.visit_date DESC, a.visit_time DESC
                """,
                (patient_id,),
            )
            return result.fetchall() if result else []
        finally:
            self.db.disconnect()

    def get_upcoming_for_patient(self, patient_id):
        try:
            if not self.db.connect():
                return None
            result = self.db.execute_query(
                """
                SELECT a.visit_date, a.visit_time, a.reason, u.full_name
                FROM appointments a
                LEFT JOIN users u ON a.doctor_id = u.id
                WHERE a.patient_id = %s
                  AND a.visit_date >= %s
                  AND a.status = 'scheduled'
                ORDER BY a.visit_date, a.visit_time
                LIMIT 1
                """,
                (patient_id, date.today()),
            )
            return result.fetchone() if result else None
        finally:
            self.db.disconnect()

    def get_today_for_doctor(self, doctor_id):
        try:
            if not self.db.connect():
                return []
            result = self.db.execute_query(
                """
                SELECT a.id, p.first_name, p.last_name, a.visit_time,
                       a.status, a.reason, p.id
                FROM appointments a
                JOIN patient p ON a.patient_id = p.id
                WHERE a.doctor_id = %s AND a.visit_date = %s
                ORDER BY a.visit_time
                """,
                (doctor_id, date.today()),
            )
            return result.fetchall() if result else []
        finally:
            self.db.disconnect()

    def update_status(self, appointment_id, status, doctor_id=None):
        if status not in ("scheduled", "completed", "cancelled"):
            return False
        try:
            if not self.db.connect():
                return False
            query = "UPDATE appointments SET status = %s WHERE id = %s"
            params = [status, appointment_id]
            if doctor_id is not None:
                query += " AND doctor_id = %s"
                params.append(doctor_id)
            query += " RETURNING id"
            result = self.db.execute_query(query, tuple(params))
            row = result.fetchone() if result else None
            if not row:
                self.db.connection.rollback()
                return False
            self.db.connection.commit()
            return True
        finally:
            self.db.disconnect()

    def count_today(self):
        try:
            if not self.db.connect():
                return 0
            result = self.db.execute_query(
                "SELECT COUNT(*) FROM appointments WHERE visit_date = %s",
                (date.today(),),
            )
            row = result.fetchone() if result else None
            return row[0] if row else 0
        finally:
            self.db.disconnect()

    def get_appointments_per_day(self, days=7):
        try:
            if not self.db.connect():
                return []
            result = self.db.execute_query(
                """
                SELECT visit_date, COUNT(*) FROM appointments
                WHERE visit_date >= CURRENT_DATE - (%s * INTERVAL '1 day')
                GROUP BY visit_date ORDER BY visit_date
                """,
                (int(days),),
            )
            return result.fetchall() if result else []
        finally:
            self.db.disconnect()
