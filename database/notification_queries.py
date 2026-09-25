"""Patient notification database operations."""

import logging

from database.connection import DatabaseConnection

logger = logging.getLogger(__name__)


class NotificationQueries:

    def __init__(self):
        self.db = DatabaseConnection()

    def create(self, patient_id, notification_type, title, message, related_id=None):
        try:
            if not self.db.connect():
                return None
            result = self.db.execute_query(
                """
                INSERT INTO notifications (
                    patient_id, notification_type, title, message, related_id
                ) VALUES (%s, %s, %s, %s, %s)
                RETURNING id
                """,
                (patient_id, notification_type, title, message, related_id),
            )
            row = result.fetchone() if result else None
            if not row:
                self.db.connection.rollback()
                return None
            self.db.connection.commit()
            return row[0]
        except Exception as exc:
            logger.error("Notification insert failed: %s", exc)
            if self.db.connection and not self.db.connection.closed:
                self.db.connection.rollback()
            return None
        finally:
            self.db.disconnect()

    def get_for_patient(self, patient_id, limit=50, unread_only=False):
        try:
            if not self.db.connect():
                return []
            query = """
                SELECT id, notification_type, title, message, related_id,
                       is_read, created_at
                FROM notifications
                WHERE patient_id = %s
            """
            params = [patient_id]
            if unread_only:
                query += " AND is_read = FALSE"
            query += " ORDER BY created_at DESC LIMIT %s"
            params.append(int(limit))
            result = self.db.execute_query(query, tuple(params))
            return result.fetchall() if result else []
        finally:
            self.db.disconnect()

    def count_unread(self, patient_id):
        if not patient_id:
            return 0
        try:
            if not self.db.connect():
                return 0
            result = self.db.execute_query(
                """
                SELECT COUNT(*) FROM notifications
                WHERE patient_id = %s AND is_read = FALSE
                """,
                (patient_id,),
            )
            row = result.fetchone() if result else None
            return row[0] if row else 0
        finally:
            self.db.disconnect()

    def mark_read(self, notification_id, patient_id):
        try:
            if not self.db.connect():
                return False
            result = self.db.execute_query(
                """
                UPDATE notifications SET is_read = TRUE
                WHERE id = %s AND patient_id = %s
                RETURNING id
                """,
                (notification_id, patient_id),
            )
            row = result.fetchone() if result else None
            if not row:
                self.db.connection.rollback()
                return False
            self.db.connection.commit()
            return True
        finally:
            self.db.disconnect()

    def mark_all_read(self, patient_id):
        try:
            if not self.db.connect():
                return False
            self.db.execute_query(
                """
                UPDATE notifications SET is_read = TRUE
                WHERE patient_id = %s AND is_read = FALSE
                """,
                (patient_id,),
            )
            self.db.connection.commit()
            return True
        finally:
            self.db.disconnect()
