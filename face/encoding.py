"""Face detection, encoding, serialization, and comparison helpers."""

import ast
from pathlib import Path

import cv2
import face_recognition
import numpy as np
from PIL import Image

from config.settings import FACE_ENCODING_NUM_JITTERS, FACE_RECOGNITION_TOLERANCE


class FaceEncoding:
    @staticmethod
    def _load_rgb_image(image_source) -> np.ndarray:
        if isinstance(image_source, (str, Path)):
            with Image.open(image_source) as image:
                return np.array(image.convert("RGB"))
        with Image.open(image_source) as image:
            return np.array(image.convert("RGB"))

    @staticmethod
    def get_face_encoding_from_image(image_path):
        encoding, _error = FaceEncoding.get_face_encoding_with_validation(image_path)
        return encoding

    @staticmethod
    def get_face_encoding_with_validation(image_source):
        try:
            image = FaceEncoding._load_rgb_image(image_source)
        except Exception:
            return None, "The image could not be opened. Use a valid JPG or PNG file."

        height, width = image.shape[:2]
        if min(height, width) < 80:
            return None, "The image resolution is too low for reliable recognition."

        try:
            locations = face_recognition.face_locations(image, model="hog")
        except Exception as exc:
            return None, f"Face detection failed: {exc}"

        if not locations:
            return None, "No face was detected. Use a clear, front-facing photograph."
        if len(locations) > 1:
            return None, "More than one face was detected. Use a photo of one person."

        try:
            encodings = face_recognition.face_encodings(
                image,
                known_face_locations=locations,
                num_jitters=FACE_ENCODING_NUM_JITTERS,
            )
        except Exception as exc:
            return None, f"Facial features could not be extracted: {exc}"

        if not encodings:
            return None, "The face was detected, but an encoding could not be generated."
        return encodings[0], None

    @staticmethod
    def get_face_encoding_from_uploaded_file(uploaded_file):
        encoding, _error = FaceEncoding.get_face_encoding_with_validation(uploaded_file)
        return encoding

    @staticmethod
    def get_face_encoding_from_frame(frame):
        try:
            rgb_frame = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
            locations = face_recognition.face_locations(rgb_frame, model="hog")
            if not locations:
                return None, "no_face"
            if len(locations) > 1:
                return None, "multiple_faces"

            encodings = face_recognition.face_encodings(
                rgb_frame,
                known_face_locations=locations,
                num_jitters=FACE_ENCODING_NUM_JITTERS,
            )
            return (encodings[0], None) if encodings else (None, "no_encoding")
        except Exception:
            return None, "processing_error"

    @staticmethod
    def get_face_locations(frame):
        try:
            rgb_frame = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
            return face_recognition.face_locations(rgb_frame, model="hog")
        except Exception:
            return []

    @staticmethod
    def encoding_to_string(encoding):
        return None if encoding is None else repr(encoding.tolist())

    @staticmethod
    def string_to_encoding(encoding_string):
        if not encoding_string:
            return None
        try:
            values = ast.literal_eval(encoding_string)
            encoding = np.asarray(values, dtype=np.float64)
        except (ValueError, SyntaxError, TypeError):
            return None
        return encoding if encoding.shape == (128,) else None

    @staticmethod
    def compare_faces(
        known_encoding,
        unknown_encoding,
        tolerance=FACE_RECOGNITION_TOLERANCE,
    ) -> bool:
        if known_encoding is None or unknown_encoding is None:
            return False
        return bool(
            face_recognition.compare_faces(
                [known_encoding],
                unknown_encoding,
                tolerance=tolerance,
            )[0]
        )
