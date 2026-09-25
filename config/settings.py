"""Application settings loaded from environment variables and safe defaults."""

import os
from dotenv import load_dotenv
load_dotenv()

from pathlib import Path

BASE_DIR = Path(__file__).resolve().parent.parent
MEDIA_DIR = BASE_DIR / "media"
PATIENT_IMAGES_DIR = MEDIA_DIR / "patients"
PATIENT_IMAGES_DIR.mkdir(parents=True, exist_ok=True)

DB_CONFIG = {
    "host": os.environ.get("SMMS_DB_HOST", "localhost"),
    "port": int(os.environ.get("SMMS_DB_PORT", "5432")),
    "database": os.environ.get("SMMS_DB_NAME", "final_db"),
    "user": os.environ.get("SMMS_DB_USER", "postgres"),
    "password": os.environ.get("SMMS_DB_PASSWORD", ""),
}

AUTH_SALT = os.environ.get("SMMS_AUTH_SALT", "medicine_face_system_salt_2026")

FACE_RECOGNITION_TOLERANCE = 0.6
FACE_ENCODING_NUM_JITTERS = 1
CAMERA_INDEX = 0
CAMERA_FPS = 30

PAGE_TITLE = "Patient Medication Management System with Face Recognition"
PAGE_ICON = "P"
LAYOUT = "wide"

MESSAGES = {
    "face_not_found": "No face was detected.",
    "multiple_faces": "Only one face may be visible in the image.",
    "patient_not_found": "No registered patient matches this face.",
    "patient_found": "Patient identified successfully.",
    "save_success": "Information saved successfully.",
    "db_error": "Database connection error.",
}
