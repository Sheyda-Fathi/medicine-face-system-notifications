"""Database operations for patient records and doctor ownership."""

import logging

import face_recognition

from config.settings import FACE_RECOGNITION_TOLERANCE
from database.connection import DatabaseConnection
from face.encoding import FaceEncoding

logger = logging.getLogger(__name__)


class PatientQueries:

    def __init__(self):
        self.db = DatabaseConnection()

    def add_patient(
        self,
        first_name,
        last_name,
        national_code,
        phone,
        face_encoding,
        image_path,
        registered_by=None,
        age=None,
        gender=None,
        height_cm=None,
        weight_kg=None,
        blood_group=None,
        address=None,
        emergency_contact=None,
    ):
        try:
            if not self.db.connect():
                return None
            result = self.db.execute_query(
                """
                INSERT INTO patient (
                    first_name, last_name, national_code, phone,
                    face_encoding, image_path, registered_by, age, gender,
                    height_cm, weight_kg, blood_group, address,
                    emergency_contact
                )
                VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s)
                RETURNING id
                """,
                (
                    first_name, last_name, national_code, phone or None,
                    face_encoding, image_path, registered_by, age, gender,
                    height_cm, weight_kg, blood_group, address,
                    emergency_contact,
                ),
            )
            row = result.fetchone() if result else None
            if not row:
                self.db.connection.rollback()
                return None
            self.db.connection.commit()
            return row[0]
        except Exception as exc:
            logger.error("Patient insert failed: %s", exc)
            if self.db.connection and not self.db.connection.closed:
                self.db.connection.rollback()
            return None
        finally:
            self.db.disconnect()

    def get_all_patients(self, doctor_id=None):
        try:
            if not self.db.connect():
                return []
            if doctor_id is None:
                query = """
                    SELECT id, first_name, last_name, national_code, phone
                    FROM patient
                    ORDER BY first_name, last_name
                """
                params = None
            else:
                query = """
                    SELECT id, first_name, last_name, national_code, phone
                    FROM patient
                    WHERE registered_by = %s
                    ORDER BY first_name, last_name
                """
                params = (doctor_id,)
            result = self.db.execute_query(query, params)
            return result.fetchall() if result else []
        finally:
            self.db.disconnect()

    def count_patients(self, doctor_id=None):
        try:
            if not self.db.connect():
                return 0
            if doctor_id is None:
                result = self.db.execute_query("SELECT COUNT(*) FROM patient")
            else:
                result = self.db.execute_query(
                    "SELECT COUNT(*) FROM patient WHERE registered_by = %s",
                    (doctor_id,),
                )
            row = result.fetchone() if result else None
            return row[0] if row else 0
        finally:
            self.db.disconnect()

    def get_patient_by_id(self, patient_id, doctor_id=None):
        try:
            if not self.db.connect():
                return None
            query = """
                SELECT p.id, p.first_name, p.last_name, p.national_code,
                       p.phone, p.face_encoding, p.image_path, p.age,
                       p.gender, p.height_cm, p.weight_kg, p.blood_group,
                       p.address, p.emergency_contact, p.created_at,
                       p.registered_by, u.full_name, u.specialty
                FROM patient p
                LEFT JOIN users u ON p.registered_by = u.id
                WHERE p.id = %s
            """
            params = [patient_id]
            if doctor_id is not None:
                query += " AND p.registered_by = %s"
                params.append(doctor_id)
            result = self.db.execute_query(query, tuple(params))
            row = result.fetchone() if result else None
            if not row:
                return None
            keys = [
                "id", "first_name", "last_name", "national_code", "phone",
                "face_encoding", "image_path", "age", "gender", "height_cm",
                "weight_kg", "blood_group", "address", "emergency_contact",
                "created_at", "registered_by", "doctor_name", "doctor_specialty",
            ]
            return dict(zip(keys, row))
        finally:
            self.db.disconnect()

    def get_patient_by_national_code(self, national_code):
        try:
            if not self.db.connect():
                return None
            result = self.db.execute_query(
                """
                SELECT id, first_name, last_name, national_code, phone
                FROM patient WHERE national_code = %s
                """,
                (national_code,),
            )
            row = result.fetchone() if result else None
            if not row:
                return None
            return {
                "id": row[0], "first_name": row[1], "last_name": row[2],
                "national_code": row[3], "phone": row[4],
            }
        finally:
            self.db.disconnect()

    def get_patient_by_face_encoding(self, face_encoding):
        try:
            if not self.db.connect():
                return None
            result = self.db.execute_query(
                """
                SELECT id, first_name, last_name, face_encoding
                FROM patient WHERE face_encoding IS NOT NULL
                """
            )
            rows = result.fetchall() if result else []
        finally:
            self.db.disconnect()

        best_row = None
        best_distance = float("inf")
        for row in rows:
            stored = FaceEncoding.string_to_encoding(row[3])
            if stored is None:
                continue
            distance = float(face_recognition.face_distance([stored], face_encoding)[0])
            if distance < best_distance:
                best_row = row
                best_distance = distance
        if best_row is None or best_distance > FACE_RECOGNITION_TOLERANCE:
            return None
        return {
            "id": best_row[0], "first_name": best_row[1],
            "last_name": best_row[2], "distance": best_distance,
        }

    def patient_exists(self, national_code):
        try:
            if not self.db.connect():
                return False
            result = self.db.execute_query(
                "SELECT 1 FROM patient WHERE national_code = %s",
                (national_code,),
            )
            return bool(result and result.fetchone())
        finally:
            self.db.disconnect()

    def doctor_has_access(self, patient_id, doctor_id):
        try:
            if not self.db.connect():
                return False
            result = self.db.execute_query(
                "SELECT 1 FROM patient WHERE id = %s AND registered_by = %s",
                (patient_id, doctor_id),
            )
            return bool(result and result.fetchone())
        finally:
            self.db.disconnect()

    def delete_patient(self, patient_id):
        try:
            if not self.db.connect():
                return False
            result = self.db.execute_query(
                "DELETE FROM patient WHERE id = %s RETURNING id",
                (patient_id,),
            )
            row = result.fetchone() if result else None
            if not row:
                self.db.connection.rollback()
                return False
            self.db.connection.commit()
            return True
        except Exception as exc:
            logger.error("Patient deletion failed: %s", exc)
            if self.db.connection and not self.db.connection.closed:
                self.db.connection.rollback()
            return False
        finally:
            self.db.disconnect()

    def update_patient(self, patient_id, **fields):
        allowed = {
            "first_name", "last_name", "phone", "age", "gender",
            "height_cm", "weight_kg", "blood_group", "address",
            "emergency_contact", "registered_by",
        }
        updates = []
        params = []
        for name, value in fields.items():
            if name not in allowed:
                continue
            if value is None and name != "registered_by":
                continue
            updates.append(f"{name} = %s")
            params.append(value if value != "" else None)
        if not updates:
            return True
        try:
            if not self.db.connect():
                return False
            params.append(patient_id)
            result = self.db.execute_query(
                f"UPDATE patient SET {', '.join(updates)} WHERE id = %s RETURNING id",
                tuple(params),
            )
            row = result.fetchone() if result else None
            if not row:
                self.db.connection.rollback()
                return False
            self.db.connection.commit()
            return True
        except Exception as exc:
            logger.error("Patient update failed: %s", exc)
            if self.db.connection and not self.db.connection.closed:
                self.db.connection.rollback()
            return False
        finally:
            self.db.disconnect()

    def update_patient_photo(self, patient_id, image_path, face_encoding):
        try:
            if not self.db.connect():
                return False
            result = self.db.execute_query(
                """
                UPDATE patient SET image_path = %s, face_encoding = %s
                WHERE id = %s RETURNING id
                """,
                (image_path, face_encoding, patient_id),
            )
            row = result.fetchone() if result else None
            if not row:
                self.db.connection.rollback()
                return False
            self.db.connection.commit()
            return True
        except Exception as exc:
            logger.error("Patient photo update failed: %s", exc)
            if self.db.connection and not self.db.connection.closed:
                self.db.connection.rollback()
            return False
        finally:
            self.db.disconnect()

    def search_patients(self, search_term, doctor_id=None):
        try:
            if not self.db.connect():
                return []
            pattern = f"%{search_term}%"
            query = """
                SELECT id, first_name, last_name, national_code, phone
                FROM patient
                WHERE (first_name ILIKE %s OR last_name ILIKE %s OR national_code ILIKE %s)
            """
            params = [pattern, pattern, pattern]
            if doctor_id is not None:
                query += " AND registered_by = %s"
                params.append(doctor_id)
            query += " ORDER BY first_name, last_name"
            result = self.db.execute_query(query, tuple(params))
            return result.fetchall() if result else []
        finally:
            self.db.disconnect()
