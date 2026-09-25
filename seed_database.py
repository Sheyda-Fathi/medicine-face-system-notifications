"""Create deterministic Iranian demo data for installation and presentation."""

import argparse
from datetime import date, datetime, time, timedelta
from pathlib import Path

from config.settings import PATIENT_IMAGES_DIR
from database.appointment_queries import AppointmentQueries
from database.auth_queries import AuthQueries
from database.connection import DatabaseConnection, init_database
from database.medication_queries import MedicationQueries
from database.notes_queries import NotesQueries
from database.notification_queries import NotificationQueries
from face.encoding import FaceEncoding
from services.notification_messages import (
    appointment_notification,
    note_notification,
    prescription_notification,
)

SEED_PHOTOS_DIR = Path(PATIENT_IMAGES_DIR) / "seed"

DOCTORS = [
    ("Reza Sharifi", "Cardiology"),
    ("Sara Ahmadi", "Internal Medicine"),
    ("Ali Mohammadi", "Neurology"),
    ("Maryam Hosseini", "Endocrinology"),
    ("Amir Rezaei", "Orthopedics"),
    ("Neda Karimi", "Pediatrics"),
    ("Hossein Moradi", "Pulmonology"),
    ("Zahra Ebrahimi", "Psychiatry"),
    ("Mehdi Rahimi", "Gastroenterology"),
    ("Leila Jafari", "Dermatology"),
    ("Saeed Ghasemi", "Nephrology"),
    ("Shirin Kazemi", "General Medicine"),
]

LEGACY_DOCTOR_USERNAMES = [
    "dr.emily.johnson",
    "dr.michael.brown",
    "dr.olivia.wilson",
    "dr.ethan.davis",
    "dr.sophia.martinez",
    "dr.james.anderson",
    "dr.ava.thompson",
    "dr.william.garcia",
    "dr.isabella.robinson",
    "dr.benjamin.clark",
    "dr.mia.lewis",
    "dr.alexander.walker",
]

MEDICINES = [
    ("Metformin", "Oral medicine commonly used for type 2 diabetes."),
    ("Losartan", "Blood pressure medicine from the ARB group."),
    ("Aspirin", "Antiplatelet and pain-relief medicine."),
    ("Atorvastatin", "Medicine used to reduce LDL cholesterol."),
    ("Levothyroxine", "Thyroid hormone replacement medicine."),
    ("Omeprazole", "Proton pump inhibitor used for reflux symptoms."),
    ("Salbutamol", "Short-acting bronchodilator used for asthma symptoms."),
    ("Cetirizine", "Antihistamine used for allergy symptoms."),
    ("Vitamin D", "Vitamin D supplement."),
    ("Ferrous Sulfate", "Iron supplement used for iron deficiency."),
    ("Paracetamol", "Pain reliever and fever reducer."),
    ("Amoxicillin", "Penicillin antibiotic used for bacterial infections."),
]

PATIENT_NAMES = [
    ("Farhad", "Ahmadi"),
    ("Zahra", "Mohammadi"),
    ("Reza", "Hosseini"),
    ("Maryam", "Karimi"),
    ("Ali", "Rezaei"),
    ("Fatemeh", "Moradi"),
    ("Mohammad", "Ebrahimi"),
    ("Narges", "Rahimi"),
    ("Hassan", "Jafari"),
    ("Leila", "Ghasemi"),
    ("Amir", "Kazemi"),
    ("Shirin", "Akbari"),
    ("Mehdi", "Mahmoudi"),
    ("Sara", "Sadeghi"),
    ("Hossein", "Najafi"),
    ("Mina", "Hashemi"),
    ("Saeed", "Norouzi"),
    ("Parisa", "Abbasi"),
    ("Hamid", "Tavakoli"),
    ("Nasrin", "Soltani"),
    ("Arash", "Fathi"),
    ("Mahsa", "Khalili"),
    ("Kian", "Rostami"),
    ("Elaheh", "Zarei"),
]

CITIES = [
    "Tehran",
    "Shiraz",
    "Isfahan",
    "Tabriz",
    "Mashhad",
    "Rasht",
    "Kerman",
    "Yazd",
]

NOTES = [
    "Blood pressure is stable. Continue the current medicine and reduce salt intake.",
    "Blood glucose has improved. Continue the diet plan and daily walking.",
    "No serious side effect was reported. Review again at the next appointment.",
    "Use the medicine at the scheduled times and report any unusual symptom.",
]

DIAGNOSES = [
    "Hypertension follow-up",
    "Type 2 diabetes follow-up",
    "Thyroid review",
    "Respiratory review",
    "Medication response review",
    "Routine clinical follow-up",
]

BLOOD_GROUPS = ["A+", "A-", "B+", "B-", "AB+", "AB-", "O+", "O-"]


def _username(full_name):
    return "dr." + full_name.lower().replace(" ", ".")


def parse_args():
    """Read the optional reset flag used before a clean presentation."""
    parser = argparse.ArgumentParser(description="Seed Iranian presentation data.")
    parser.add_argument(
        "--reset-demo",
        action="store_true",
        help="Remove old generated demo records before rebuilding the Iranian dataset.",
    )
    return parser.parse_args()


def reset_demo_data():
    """Remove only known generated records, never ordinary registered patients."""
    db = DatabaseConnection()
    if not db.connect():
        raise RuntimeError(db.last_error or "Database connection failed.")
    try:
        db.execute_query(
            """
            DELETE FROM patient
            WHERE national_code BETWEEN '8000000000' AND '8000000039'
               OR national_code BETWEEN '7000000001' AND '7000000024'
            """
        )

        # Legacy English doctors belonged only to the previous demo dataset.
        placeholders = ", ".join(["%s"] * len(LEGACY_DOCTOR_USERNAMES))
        legacy_ids = db.execute_query(
            f"SELECT id FROM users WHERE username IN ({placeholders})",
            tuple(LEGACY_DOCTOR_USERNAMES),
        )
        doctor_ids = [row[0] for row in (legacy_ids.fetchall() if legacy_ids else [])]
        for doctor_id in doctor_ids:
            db.execute_query(
                "UPDATE patient SET registered_by = NULL WHERE registered_by = %s",
                (doctor_id,),
            )
            db.execute_query(
                "UPDATE doctor_notes SET doctor_id = NULL WHERE doctor_id = %s",
                (doctor_id,),
            )
            db.execute_query(
                "UPDATE appointments SET doctor_id = NULL WHERE doctor_id = %s",
                (doctor_id,),
            )
            db.execute_query(
                "UPDATE patient_medication SET prescribed_by = NULL WHERE prescribed_by = %s",
                (doctor_id,),
            )
        db.execute_query(
            f"DELETE FROM users WHERE username IN ({placeholders})",
            tuple(LEGACY_DOCTOR_USERNAMES),
        )
        db.connection.commit()
        print("  Previous generated demo records removed.")
    except Exception:
        db.connection.rollback()
        raise
    finally:
        db.disconnect()


def ensure_staff_accounts():
    """Create the administrator and Iranian doctor accounts."""
    auth = AuthQueries()
    admin_id, error = auth.ensure_staff_account(
        username="admin",
        password="Admin@123",
        full_name="System Administrator",
        email="admin@medication.local",
        specialty="Administration",
        role="admin",
    )
    if not admin_id:
        raise RuntimeError(f"Administrator account failed: {error}")

    doctors = {}
    for full_name, specialty in DOCTORS:
        username = _username(full_name)
        doctor_id, error = auth.ensure_staff_account(
            username=username,
            password="Doctor@123",
            full_name=f"Dr. {full_name}",
            email=f"{username}@medication.local",
            specialty=specialty,
            role="doctor",
        )
        if not doctor_id:
            raise RuntimeError(f"Doctor account failed: {username}: {error}")
        doctors[full_name] = doctor_id
        print(f"  Doctor ready: Dr. {full_name} ({username})")
    return doctors


def ensure_medicines():
    """Create the small catalog used throughout the presentation."""
    medication_db = MedicationQueries()
    medicine_ids = {}
    for name, description in MEDICINES:
        medicine_id = medication_db.add_medication(name, description)
        if not medicine_id:
            raise RuntimeError(f"Medicine could not be prepared: {name}")
        medicine_ids[name] = medicine_id
    return medicine_ids


def ensure_interactions(medicine_ids):
    """Add one visible interaction example for the doctor workflow."""
    db = DatabaseConnection()
    if not db.connect():
        return
    try:
        first = medicine_ids["Aspirin"]
        second = medicine_ids["Paracetamol"]
        exists = db.execute_query(
            """
            SELECT 1 FROM medication_interaction
            WHERE (medication1_id = %s AND medication2_id = %s)
               OR (medication1_id = %s AND medication2_id = %s)
            """,
            (first, second, second, first),
        )
        if not exists or not exists.fetchone():
            db.execute_query(
                """
                INSERT INTO medication_interaction (
                    medication1_id, medication2_id, severity, description
                ) VALUES (%s, %s, %s, %s)
                """,
                (
                    first,
                    second,
                    "mild",
                    "Review total daily pain-relief use and monitor the patient.",
                ),
            )
        db.connection.commit()
    finally:
        db.disconnect()


def load_seed_photos():
    """Load optional consented images in filename order."""
    if not SEED_PHOTOS_DIR.is_dir():
        return []
    return sorted(
        path
        for path in SEED_PHOTOS_DIR.iterdir()
        if path.suffix.lower() in {".jpg", ".jpeg", ".png"}
    )


def upsert_patient(index, doctor_id, photo_path=None):
    """Create or refresh one deterministic Iranian patient."""
    first_name, last_name = PATIENT_NAMES[index]
    national_code = f"70000000{index + 1:02d}"
    face_encoding = None
    image_path = None

    if photo_path:
        encoding, error = FaceEncoding.get_face_encoding_with_validation(photo_path)
        if encoding is not None:
            face_encoding = FaceEncoding.encoding_to_string(encoding)
            image_path = str(photo_path)
        else:
            print(f"  Photo ignored: {photo_path.name}: {error}")

    db = DatabaseConnection()
    if not db.connect():
        return None
    try:
        result = db.execute_query(
            """
            INSERT INTO patient (
                first_name, last_name, national_code, phone,
                face_encoding, image_path, registered_by, age, gender,
                height_cm, weight_kg, blood_group, address,
                emergency_contact
            )
            VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s)
            ON CONFLICT (national_code) DO UPDATE SET
                first_name = EXCLUDED.first_name,
                last_name = EXCLUDED.last_name,
                phone = EXCLUDED.phone,
                registered_by = EXCLUDED.registered_by,
                age = EXCLUDED.age,
                gender = EXCLUDED.gender,
                height_cm = EXCLUDED.height_cm,
                weight_kg = EXCLUDED.weight_kg,
                blood_group = EXCLUDED.blood_group,
                address = EXCLUDED.address,
                emergency_contact = EXCLUDED.emergency_contact,
                face_encoding = COALESCE(EXCLUDED.face_encoding, patient.face_encoding),
                image_path = COALESCE(EXCLUDED.image_path, patient.image_path)
            RETURNING id
            """,
            (
                first_name,
                last_name,
                national_code,
                f"0912{index + 1:07d}",
                face_encoding,
                image_path,
                doctor_id,
                58 + (index % 28),
                "Female" if index % 2 else "Male",
                156 + (index % 24),
                58 + (index % 31),
                BLOOD_GROUPS[index % len(BLOOD_GROUPS)],
                f"{CITIES[index % len(CITIES)]}, District {index % 6 + 1}",
                f"{PATIENT_NAMES[(index + 5) % len(PATIENT_NAMES)][0]} - 0913{index + 1:07d}",
            ),
        )
        row = result.fetchone() if result else None
        if not row:
            db.connection.rollback()
            return None
        patient_id = row[0]

        # Related demo rows are rebuilt so repeated seeding stays predictable.
        db.execute_query("DELETE FROM notifications WHERE patient_id = %s", (patient_id,))
        db.execute_query("DELETE FROM doctor_notes WHERE patient_id = %s", (patient_id,))
        db.execute_query("DELETE FROM appointments WHERE patient_id = %s", (patient_id,))
        db.execute_query("DELETE FROM patient_medication WHERE patient_id = %s", (patient_id,))
        db.connection.commit()
        return patient_id
    except Exception:
        db.connection.rollback()
        raise
    finally:
        db.disconnect()


def seed_patient_content(patient_id, patient_index, doctor_id, doctor_name, medicine_ids):
    """Populate every patient page with prescriptions, intake, notes, and visits."""
    medication_db = MedicationQueries()
    appointment_db = AppointmentQueries()
    notes_db = NotesQueries()
    notification_db = NotificationQueries()

    medicine_names = list(medicine_ids)
    selected = [
        medicine_names[patient_index % len(medicine_names)],
        medicine_names[(patient_index + 4) % len(medicine_names)],
    ]

    for medicine_index, medicine_name in enumerate(selected):
        slots = ["08:00", "20:00"] if medicine_index == 0 else ["13:00"]
        dosage = "500 mg" if "Metformin" in medicine_name else "1 tablet"
        prescription_id = medication_db.assign_medication_to_patient(
            patient_id=patient_id,
            medication_id=medicine_ids[medicine_name],
            dosage=dosage,
            schedule=f"{len(slots)} time(s) per day at {', '.join(slots)}",
            start_date=date.today() - timedelta(days=14),
            end_date=date.today() + timedelta(days=45),
            times_per_day=len(slots),
            time_slots=", ".join(slots),
            notes="Take with water and follow the prescribed reminder time.",
            prescribed_by=doctor_id,
        )
        title, message = prescription_notification(
            medicine_name,
            dosage,
            ", ".join(slots),
            f"Dr. {doctor_name}",
        )
        notification_db.create(
            patient_id,
            "prescription",
            title,
            message,
            related_id=prescription_id,
        )

        # Seven days of mixed records make adherence charts useful during the demo.
        for days_ago in range(7):
            intake_date = date.today() - timedelta(days=days_ago)
            for slot_index, slot in enumerate(slots):
                scheduled_time = time(*map(int, slot.split(":")))
                scheduled_at = datetime.combine(intake_date, scheduled_time)
                if days_ago == 0 and scheduled_at > datetime.now():
                    continue
                taken = (patient_index + days_ago + slot_index) % 5 != 0
                actual_time = None
                if taken:
                    actual_time = scheduled_at + timedelta(
                        minutes=5 + ((patient_index + days_ago) % 18)
                    )
                medication_db.record_intake(
                    prescription_id,
                    intake_date,
                    scheduled_time,
                    taken=taken,
                    notes="Generated presentation record",
                    taken_at=actual_time,
                )

    note_id = notes_db.add_note(
        patient_id,
        doctor_id,
        NOTES[patient_index % len(NOTES)],
    )
    title, message = note_notification(f"Dr. {doctor_name}")
    notification_db.create(
        patient_id,
        "doctor_note",
        title,
        message,
        related_id=note_id,
    )

    appointment_db.add_appointment(
        patient_id,
        doctor_id,
        date.today() - timedelta(days=21 + patient_index % 10),
        time(10 + patient_index % 5, 0),
        status="completed",
        reason=DIAGNOSES[patient_index % len(DIAGNOSES)],
    )
    next_date = date.today() if patient_index < len(DOCTORS) else date.today() + timedelta(
        days=3 + patient_index % 18
    )
    appointment_id = appointment_db.add_appointment(
        patient_id,
        doctor_id,
        next_date,
        time(9 + patient_index % 7, 30),
        status="scheduled",
        reason="Follow-up visit and medication review",
    )
    title, message = appointment_notification(
        next_date,
        time(9 + patient_index % 7, 30),
        f"Dr. {doctor_name}",
    )
    notification_db.create(
        patient_id,
        "appointment",
        title,
        message,
        related_id=appointment_id,
    )


def seed_patients(doctors, medicine_ids):
    """Create two complete presentation patients for every doctor."""
    photos = load_seed_photos()
    if not photos:
        print("  No consented seed photos found; demo patients cannot use face login.")

    doctor_items = list(doctors.items())
    for index, (first_name, last_name) in enumerate(PATIENT_NAMES):
        doctor_name, doctor_id = doctor_items[index % len(doctor_items)]
        photo_path = photos[index] if index < len(photos) else None
        patient_id = upsert_patient(index, doctor_id, photo_path)
        if not patient_id:
            raise RuntimeError(f"Patient could not be prepared: {first_name} {last_name}")
        seed_patient_content(
            patient_id,
            index,
            doctor_id,
            doctor_name,
            medicine_ids,
        )
        print(f"  Patient ready: {first_name} {last_name} -> Dr. {doctor_name}")


def main():
    """Initialize the schema and build a repeatable presentation dataset."""
    args = parse_args()
    print("=" * 72)
    print("Smart Medication System - Iranian presentation dataset")
    print("=" * 72)

    if not init_database():
        raise SystemExit("Database initialization failed. Check config/settings.py.")
    if args.reset_demo:
        reset_demo_data()

    doctors = ensure_staff_accounts()
    medicine_ids = ensure_medicines()
    ensure_interactions(medicine_ids)
    seed_patients(doctors, medicine_ids)

    print("\nPresentation data is ready.")
    print("Admin: admin / Admin@123")
    print("Doctor: dr.reza.sharifi / Doctor@123")
    print("Run with --reset-demo to remove the previous generated English dataset.")
    print("Face login still requires a real patient registered with a consented photo.")


if __name__ == "__main__":
    main()
