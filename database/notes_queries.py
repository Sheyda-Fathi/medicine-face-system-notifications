"""Database operations for clinical notes."""

import logging

from database.connection import DatabaseConnection

logger = logging.getLogger(__name__)


class NotesQueries:
    def __init__(self):
        self.db = DatabaseConnection()

    def add_note(self, patient_id, doctor_id, note):
        try:
            if not self.db.connect():
                return None
            result = self.db.execute_query(
                """
                INSERT INTO doctor_notes (patient_id, doctor_id, note)
                VALUES (%s, %s, %s) RETURNING id
                """,
                (patient_id, doctor_id, note),
            )
            row = result.fetchone() if result else None
            if not row:
                self.db.connection.rollback()
                return None
            self.db.connection.commit()
            return row[0]
        except Exception as exc:
            logger.error("Doctor note insert failed: %s", exc)
            if self.db.connection and not self.db.connection.closed:
                self.db.connection.rollback()
            return None
        finally:
            self.db.disconnect()

    def get_notes_for_patient(self, patient_id):
        try:
            if not self.db.connect():
                return []
            result = self.db.execute_query(
                """
                SELECT dn.id, dn.note, dn.created_at, u.full_name, dn.doctor_id
                FROM doctor_notes dn
                LEFT JOIN users u ON dn.doctor_id = u.id
                WHERE dn.patient_id = %s
                ORDER BY dn.created_at DESC
                """,
                (patient_id,),
            )
            return result.fetchall() if result else []
        finally:
            self.db.disconnect()

    def delete_note(self, note_id, doctor_id=None):
        try:
            if not self.db.connect():
                return False
            query = "DELETE FROM doctor_notes WHERE id = %s"
            params = [note_id]
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
