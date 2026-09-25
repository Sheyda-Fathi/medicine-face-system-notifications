# Final Project Report

## Patient Medication Management System Using Face Recognition

**Student:** Sheyda Fathi  
**Supervisor:** Hosein Shahsavar Haghighi  
**Year:** 2026

## Abstract

This project implements a medication management system intended especially for elderly patients who may have difficulty using conventional usernames and passwords. A registered patient signs in through facial recognition and receives a clear view of prescribed medicines, daily reminder times, doctor instructions, medication intake status, clinical notes, and appointments. Doctors manage clinical information for their assigned patients, while administrators manage patient records, doctor accounts, and the medication catalog.

## Objectives

- Provide password-free patient access through face recognition
- Reduce patient identification errors
- Present medicine instructions and reminder times clearly
- Notify patients when a prescription, appointment, or doctor note is added
- Record the actual medicine confirmation time for doctor review
- Separate administrator, doctor, and patient responsibilities
- Store patient, prescription, appointment, and intake information in PostgreSQL
- Support a local academic demonstration through Streamlit

## Technologies

- Python
- Streamlit
- PostgreSQL
- OpenCV
- face_recognition and dlib
- NumPy
- Pillow
- pandas

## Role Design

The administrator maintains accounts and master data. The doctor registers and treats assigned patients. The patient signs in by face and reads personal treatment information. Public doctor registration was removed, and the former Smart Dashboard was merged into the patient profile because both represented the same patient-level information.

## Main Workflows

### Patient Enrollment

A doctor or administrator enters patient information and uploads one clear face photograph. The system validates that exactly one face is present, creates a 128-dimensional encoding, stores the image path and encoding, and assigns the patient to a doctor.

### Patient Login

The patient provides a camera image or uploaded photograph. The system creates a new encoding and selects the nearest stored encoding inside the configured tolerance. A successful match creates a patient session without requiring a password.

### Prescription, Notifications, and Reminders

A doctor selects an assigned patient and a catalog medicine, enters dosage, instructions, treatment dates, and daily reminder times. Saving the prescription creates a patient notification immediately. The patient can mark a medicine as taken, while the system preserves both the scheduled reminder time and the exact confirmation timestamp. These values are visible to the patient and the assigned doctor.

### Appointments and Notes

The doctor schedules appointments and writes clinical notes from the patient profile. Each new appointment or note creates a patient notification. The patient can read the next appointment, appointment history, and doctor recommendations.

## Architecture

The application follows a layered architecture consisting of Streamlit pages, workflow logic, query services, PostgreSQL storage, local patient photographs, and face-recognition services.

## Testing

The project includes automated tests for role menus, notification messages, reminder status rules, demo data, database schema features, and the doctor intake-time display. A complete manual presentation plan covers administrator management, doctor workflows, face login, patient notifications, medicine confirmation, and the return flow showing the actual confirmation time in the doctor panel. Runtime camera tests require a real registered face on the target computer.

## Limitations

This version is an academic demonstration and is not suitable for real clinical deployment without biometric encryption, stronger password hashing, audit logging, backup policies, formal security review, and medical validation.

## Conclusion

The project demonstrates a practical method for combining face recognition with medication management. Its final role structure is aligned with real operational responsibilities: the administrator manages the system, the doctor manages treatment, and the patient receives a simple password-free interface focused on medicines and reminders.
