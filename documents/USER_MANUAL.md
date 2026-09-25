# User Manual

## 1. Login

The system has two login methods.

### Staff Login

Administrators and doctors enter a username and password.

### Patient Face Login

A registered patient selects `Camera` or `Upload Photo`. The system opens the patient portal only when exactly one detected face matches a stored patient encoding.

Patients do not need a username or password. Public doctor registration and patient self-registration are disabled.

## 2. Administrator Panel

### Dashboard

Shows patient, doctor, medicine, appointment, and adherence information for the whole system.

### Manage Patients

- Register a patient with a face photograph
- Search patient records
- View all patient information
- Assign or change the doctor
- Replace the face photograph
- Delete a patient and related records

### Manage Doctors

- Create a doctor account
- Review username, specialty, email, and patient count
- Delete a doctor account

Deleting a doctor preserves patients and clinical history. Affected patients become unassigned until the administrator selects another doctor.

### Manage Medications

- Add or update a medicine in the shared catalog
- Search the catalog
- Delete a medicine only when no prescription uses it

## 3. Doctor Panel

### Dashboard

Shows only the signed-in doctor's information:

- Assigned patients
- Active prescriptions
- Today's appointments
- Seven-day adherence chart
- Latest patient intake activity

The latest activity table compares the scheduled dose time with the actual time reported by the patient.

### Register Patient

The doctor enters demographic information and uploads one clear face photograph. The patient is assigned automatically to the signed-in doctor.

The image is rejected when no face, multiple faces, or an unusable face image is detected.

### Add Medication

1. Select an assigned patient.
2. Select a medicine from the administrator-managed catalog.
3. Enter dosage and instructions.
4. Select start and optional end date.
5. Set daily reminder times.
6. Review any known interaction warning.
7. Save the prescription.

After saving, the patient receives a `New prescription` notification immediately.

### Patient Profiles

#### Overview

Shows identity, contact information, assigned doctor, face photograph, and next appointment.

#### Prescriptions

Shows active medicines, dosage, treatment dates, reminder times, and instructions.

#### Reminders & Adherence

Shows:

- Scheduled dose time
- Taken, Missed, or Pending status
- Actual patient confirmation timestamp
- Thirty-day intake history

#### Appointments & Notes

The doctor can schedule a visit and add a clinical note. Each action creates a patient notification.

#### Edit Record

The doctor can update an assigned patient's details and replace the face photograph. Patient deletion remains an administrator action.

## 4. Patient Panel

The patient interface uses large headings and simple actions for elderly users.

### Home

Shows active medicines, remaining doses, today's schedule, next appointment, and latest notifications.

### My Medications

Shows medicine name, dosage, reminder times, treatment dates, instructions, and prescribing doctor.

### Reminders

For each dose, the patient selects `I took this medicine now` after taking the medicine.

The system keeps:

- The reminder time selected by the doctor
- The actual date and time of patient confirmation

A late confirmation is still saved as taken at the real confirmation time.

### Notifications

Shows:

- New prescriptions
- New appointments
- New doctor notes

The patient can mark one notification or all notifications as read. The unread count appears beside the sidebar menu label.

### Appointments & Notes

Shows scheduled and completed appointments plus doctor recommendations.

### My Profile

Shows the registered photograph, identity, contact information, emergency contact, and assigned doctor.

## 5. Demonstration Dataset

Run:

```bash
python seed_database.py --reset-demo
```

Main accounts:

```text
Administrator: admin / Admin@123
Doctor: dr.reza.sharifi / Doctor@123
```

The seed creates 12  doctors and 24  patients. Every doctor receives populated patient, prescription, intake, note, notification, and appointment data.

## 6. Complete Presentation

Use `documents/PRESENTATION_TEST_PLAN.md` to demonstrate all roles and the full workflow from doctor prescription to patient notification, patient medicine confirmation, and doctor review of the actual intake time.
