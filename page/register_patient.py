"""Patient enrollment form for doctors and administrators."""

import io
from datetime import datetime
from pathlib import Path

import streamlit as st # type: ignore
from PIL import Image, ImageOps

from config.settings import PATIENT_IMAGES_DIR
from database.auth_queries import AuthQueries
from database.patient_queries import PatientQueries
from face.encoding import FaceEncoding


_MAX_PHOTO_SIDE = 900


def _prepare_image_from_bytes(raw_bytes, max_side=_MAX_PHOTO_SIDE):
    image = Image.open(io.BytesIO(raw_bytes))
    image = ImageOps.exif_transpose(image)  
    image = image.convert("RGB")
    image.thumbnail((max_side, max_side))
    return image


def _validate(first_name, last_name, national_code, uploaded_image):
    if not first_name.strip() or not last_name.strip():
        return "First name and last name are required."
    if not national_code.isdigit() or len(national_code) != 10:
        return "National code must contain exactly 10 digits."
    if uploaded_image is None:
        return "A clear face photograph is required."
    return None


def _resolve_assigned_doctor(user):
    if user.get("role") == "doctor":
        st.info(f"Assigned doctor: {user['full_name']}")
        return user["id"]

    doctors = AuthQueries().get_all_doctors()
    options = {"Unassigned": None}
    options.update(
        {
            f"{name} ({specialty or 'General Medicine'})": doctor_id
            for doctor_id, name, specialty in doctors
        }
    )
    selected = st.selectbox("Assigned doctor", list(options))
    return options[selected]


def show_register_patient(user=None):
    user = user or st.session_state.get("user") or {}
    if user.get("role") not in ("doctor", "admin"):
        st.error("Only staff members can register a patient.")
        return

    st.title("Register Patient")
    st.caption(
        "This reference photograph will be used when the patient signs in by face."
    )
    st.divider()

    assigned_doctor_id = _resolve_assigned_doctor(user)
    form_col, preview_col = st.columns([2, 1])

    with form_col:
        with st.form("register_patient_form"):
            first_name = st.text_input("First name *")
            last_name = st.text_input("Last name *")
            national_code = st.text_input("National code *", max_chars=10)
            phone = st.text_input("Phone number")

            age_col, gender_col = st.columns(2)
            with age_col:
                age = st.number_input("Age", min_value=0, max_value=120, value=65)
            with gender_col:
                gender = st.selectbox("Gender", ["Female", "Male", "Other"])

            height_col, weight_col, blood_col = st.columns(3)
            with height_col:
                height_cm = st.number_input(
                    "Height (cm)", min_value=0.0, max_value=250.0,
                    value=165.0, step=0.5,
                )
            with weight_col:
                weight_kg = st.number_input(
                    "Weight (kg)", min_value=0.0, max_value=300.0,
                    value=70.0, step=0.5,
                )
            with blood_col:
                blood_group = st.selectbox(
                    "Blood group",
                    ["", "A+", "A-", "B+", "B-", "AB+", "AB-", "O+", "O-"],
                )

            address = st.text_input("Address")
            emergency_contact = st.text_input("Emergency contact")
            uploaded_image = st.file_uploader(
                "Face photograph *",
                type=["jpg", "jpeg", "png"],
                help="Use one front-facing face in good light, without a mask or dark glasses.",
            )
            submitted = st.form_submit_button("Register patient", type="primary")

    with preview_col:
        st.subheader("Photo Preview")
        if uploaded_image:
            try:
                preview_image = _prepare_image_from_bytes(uploaded_image.getvalue())
                st.image(preview_image, width=280)
            except Exception:
                st.error("The selected image could not be opened.")
        else:
            st.info("Upload a patient photo to preview it here.")
        st.markdown(
            """
            **Face photo checklist**

            - One person only
            - Front-facing view
            - Good lighting
            - Clear, non-blurred image
            - No mask or dark glasses
            """
        )

    if not submitted:
        return

    code = national_code.strip()
    error = _validate(first_name, last_name, code, uploaded_image)
    if error:
        st.error(error)
        return

    patient_db = PatientQueries()
    if patient_db.patient_exists(code):
        st.error("A patient with this national code is already registered.")
        return
    try:
        raw_bytes = uploaded_image.getvalue()
        prepared_image = _prepare_image_from_bytes(raw_bytes)
    except Exception:
        st.error("The selected image could not be opened.")
        return

    with st.spinner("Validating the face photograph..."):
        encoding_buffer = io.BytesIO()
        prepared_image.save(encoding_buffer, format="JPEG")
        encoding_buffer.seek(0)
        encoding, face_error = FaceEncoding.get_face_encoding_with_validation(
            encoding_buffer
        )
    if face_error:
        st.error(face_error)
        return

    filename = f"{code}_{datetime.now():%Y%m%d_%H%M%S}.jpg"
    image_path = Path(PATIENT_IMAGES_DIR) / filename
    prepared_image.save(image_path, format="JPEG")

    patient_id = patient_db.add_patient(
        first_name=first_name.strip(),
        last_name=last_name.strip(),
        national_code=code,
        phone=phone.strip(),
        face_encoding=FaceEncoding.encoding_to_string(encoding),
        image_path=str(image_path),
        registered_by=assigned_doctor_id,
        age=int(age),
        gender=gender,
        height_cm=height_cm or None,
        weight_kg=weight_kg or None,
        blood_group=blood_group or None,
        address=address.strip() or None,
        emergency_contact=emergency_contact.strip() or None,
    )
    if not patient_id:
        image_path.unlink(missing_ok=True)
        st.error("The patient record could not be saved.")
        return

    st.session_state.selected_patient_id = patient_id
    st.success(
        f"Patient registered successfully. Patient ID: {patient_id}. "
        "Log out and use Patient Face Login to test the account."
    )