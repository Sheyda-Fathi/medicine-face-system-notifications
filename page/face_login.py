"""Patient login page based on a captured or uploaded face image."""

import streamlit as st

from database.patient_queries import PatientQueries
from face.encoding import FaceEncoding


def show_face_login():
    st.markdown("#### Patient Login")
    st.caption("Capture a clear image or upload a front-facing photograph.")

    mode = st.radio(
        "Method",
        ["Camera", "Upload Photo"],
        horizontal=True,
        key="face_login_mode",
    )
    if mode == "Camera":
        image_file = st.camera_input(
            "Look directly at the camera",
            key="face_login_camera",
        )
    else:
        image_file = st.file_uploader(
            "Upload a face photo",
            type=["jpg", "jpeg", "png"],
            key="face_login_upload",
        )

    if not image_file:
        return

    with st.spinner("Recognizing face..."):
        encoding, error = FaceEncoding.get_face_encoding_with_validation(image_file)
        if error:
            st.error(error)
            return

        match = PatientQueries().get_patient_by_face_encoding(encoding)
        patient = (
            PatientQueries().get_patient_by_id(match["id"])
            if match
            else None
        )

    if not patient:
        st.error(
            "The face was not recognized. Ask a doctor to register the patient first."
        )
        return

    confidence = max(0.0, (1.0 - match["distance"]) * 100.0)
    st.success(
        f"Welcome, {patient['first_name']} {patient['last_name']}. "
        f"Match confidence: {confidence:.1f}%."
    )
    st.session_state.user = {
        "id": None,
        "role": "patient",
        "full_name": f"{patient['first_name']} {patient['last_name']}",
        "patient_id": patient["id"],
    }
    st.rerun()
