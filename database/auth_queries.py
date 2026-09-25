"""Authentication and administrator operations for staff accounts."""

import hashlib
import logging

from config.settings import AUTH_SALT
from database.connection import DatabaseConnection

logger = logging.getLogger(__name__)


class AuthQueries:
    def __init__(self):
        self.db = DatabaseConnection()

    @staticmethod
    def _hash_password(password: str) -> str:
        salted = f"{AUTH_SALT}{password}".encode("utf-8")
        return hashlib.sha256(salted).hexdigest()

    def register_staff(self, username, password, full_name, email, specialty, role):
        if role not in ("doctor", "admin"):
            return None, "Role must be doctor or admin."
        try:
            if not self.db.connect():
                return None, self.db.last_error or "Database connection error."
            result = self.db.execute_query(
                """
                INSERT INTO users (username, password_hash, role, full_name, email, specialty)
                VALUES (%s, %s, %s, %s, %s, %s)
                RETURNING id
                """,
                (
                    username, self._hash_password(password), role, full_name,
                    email or None, specialty or None,
                ),
            )
            row = result.fetchone() if result else None
            if not row:
                self.db.connection.rollback()
                return None, self.db.last_error or "Account creation failed."
            self.db.connection.commit()
            return row[0], None
        except Exception as exc:
            if self.db.connection and not self.db.connection.closed:
                self.db.connection.rollback()
            if "unique" in str(exc).lower():
                return None, "This username is already registered."
            return None, str(exc)
        finally:
            self.db.disconnect()

    def ensure_staff_account(self, username, password, full_name, email, specialty, role):
        if role not in ("doctor", "admin"):
            return None, "Role must be doctor or admin."
        try:
            if not self.db.connect():
                return None, self.db.last_error or "Database connection error."
            result = self.db.execute_query(
                """
                INSERT INTO users (username, password_hash, role, full_name, email, specialty)
                VALUES (%s, %s, %s, %s, %s, %s)
                ON CONFLICT (username) DO UPDATE SET
                    password_hash = EXCLUDED.password_hash,
                    role = EXCLUDED.role,
                    full_name = EXCLUDED.full_name,
                    email = EXCLUDED.email,
                    specialty = EXCLUDED.specialty
                RETURNING id
                """,
                (
                    username, self._hash_password(password), role, full_name,
                    email or None, specialty or None,
                ),
            )
            row = result.fetchone() if result else None
            if not row:
                self.db.connection.rollback()
                return None, self.db.last_error or "Account creation failed."
            self.db.connection.commit()
            return row[0], None
        except Exception as exc:
            if self.db.connection and not self.db.connection.closed:
                self.db.connection.rollback()
            return None, str(exc)
        finally:
            self.db.disconnect()

    def register_doctor(self, username, password, full_name, email, specialty):
        return self.register_staff(
            username, password, full_name, email, specialty, role="doctor"
        )

    def login(self, username, password):
        try:
            if not self.db.connect():
                return None, self.db.last_error or "Database connection error."
            result = self.db.execute_query(
                """
                SELECT id, username, role, full_name, email, specialty
                FROM users
                WHERE username = %s AND password_hash = %s
                """,
                (username, self._hash_password(password)),
            )
            row = result.fetchone() if result else None
            if not row:
                return None, "Incorrect username or password."
            return {
                "id": row[0], "username": row[1], "role": row[2],
                "full_name": row[3], "email": row[4], "specialty": row[5],
                "patient_id": None,
            }, None
        except Exception as exc:
            return None, str(exc)
        finally:
            self.db.disconnect()

    def get_all_doctors(self):
        try:
            if not self.db.connect():
                return []
            result = self.db.execute_query(
                """
                SELECT id, full_name, specialty
                FROM users WHERE role = 'doctor'
                ORDER BY full_name
                """
            )
            return result.fetchall() if result else []
        finally:
            self.db.disconnect()

    def get_doctors_detailed(self):
        try:
            if not self.db.connect():
                return []
            result = self.db.execute_query(
                """
                SELECT u.id, u.full_name, u.username, u.email, u.specialty,
                       u.created_at, COUNT(p.id)
                FROM users u
                LEFT JOIN patient p ON p.registered_by = u.id
                WHERE u.role = 'doctor'
                GROUP BY u.id
                ORDER BY u.full_name
                """
            )
            return result.fetchall() if result else []
        finally:
            self.db.disconnect()

    def delete_doctor(self, doctor_id):
        try:
            if not self.db.connect():
                return False, self.db.last_error or "Database connection error."
            role_result = self.db.execute_query(
                "SELECT role FROM users WHERE id = %s", (doctor_id,)
            )
            row = role_result.fetchone() if role_result else None
            if not row or row[0] != "doctor":
                return False, "Doctor account was not found."

            self.db.execute_query(
                "UPDATE patient SET registered_by = NULL WHERE registered_by = %s",
                (doctor_id,),
            )
            self.db.execute_query(
                "UPDATE doctor_notes SET doctor_id = NULL WHERE doctor_id = %s",
                (doctor_id,),
            )
            self.db.execute_query(
                "UPDATE appointments SET doctor_id = NULL WHERE doctor_id = %s",
                (doctor_id,),
            )
            self.db.execute_query(
                "UPDATE patient_medication SET prescribed_by = NULL WHERE prescribed_by = %s",
                (doctor_id,),
            )
            result = self.db.execute_query(
                "DELETE FROM users WHERE id = %s AND role = 'doctor' RETURNING id",
                (doctor_id,),
            )
            deleted = result.fetchone() if result else None
            if not deleted:
                self.db.connection.rollback()
                return False, "Doctor account could not be deleted."
            self.db.connection.commit()
            return True, None
        except Exception as exc:
            logger.error("Doctor deletion failed: %s", exc)
            if self.db.connection and not self.db.connection.closed:
                self.db.connection.rollback()
            return False, str(exc)
        finally:
            self.db.disconnect()
