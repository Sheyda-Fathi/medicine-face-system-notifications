# System Design Document

## 1. Purpose

The system gives elderly patients face-based access to prescriptions, reminders, appointments, and doctor notes. Streamlit provides the interface, PostgreSQL stores records, and `face_recognition` creates 128-dimensional face encodings.

## 2. Roles

| Function | Administrator | Doctor | Patient |
| --- | --- | --- | --- |
| System management | Yes | No | No |
| Add/delete doctor | Yes | No | No |
| Add/delete catalog medicine | Yes | No | No |
| Register patient | Yes | Assigned automatically | No |
| Delete patient | Yes | No | No |
| Prescribe medicine | No | Assigned patients only | No |
| Schedule appointment | No | Assigned patients only | Read only |
| Add doctor note | No | Assigned patients only | Read only |
| View notifications | No | No | Yes |
| Confirm medicine intake | No | Review only | Yes |
| Patient login | No | No | Face only |

## 3. Navigation

### Administrator

```text
Dashboard
Manage Patients
Manage Doctors
Manage Medications
```

### Doctor

```text
Dashboard
Add Medication
Register Patient
Patient Profiles
```

### Patient

```text
Home
My Medications
Reminders
Notifications
Appointments & Notes
My Profile
```

## 4. Application Layers

```text
Streamlit role routing and pages
              |
              v
Small workflow services
              |
              v
Parameterized database query classes
              |
              v
PostgreSQL and local face photographs
```

Important source files:

- `config/navigation.py`: role menus independent of Streamlit
- `services/medication_schedule.py`: time parsing and dose status
- `services/notification_messages.py`: consistent patient notification text
- `database/notification_queries.py`: notification persistence and read state
- `database/medication_queries.py`: prescriptions and actual intake timestamps

## 5. Prescription and Notification Workflow

```text
Doctor saves prescription
          |
          v
patient_medication row is inserted or updated
          |
          v
prescribed_by stores the doctor identifier
          |
          v
notification row is created for the patient
          |
          v
patient sidebar unread count increases
```

Appointment and doctor-note actions use the same notification table with different notification types.

## 6. Medication Intake Workflow

```text
Doctor sets scheduled time, for example 08:00
          |
          v
Patient sees the reminder
          |
          v
Patient selects I took this medicine now
          |
          v
medication_intake stores:
- intake_date
- intake_time as scheduled time
- taken = true
- taken_at as actual confirmation timestamp
          |
          v
Patient and doctor see both times
```

The scheduled time is never replaced by the actual confirmation time. This separation allows the doctor to evaluate delayed or missed doses.

## 7. Dose Status Rules

- `Taken`: a true intake record exists
- `Missed`: a false record exists, or an unconfirmed scheduled time has passed
- `Pending`: the scheduled time is still in the future

The rules are implemented in a pure service and covered by automated tests.

## 8. Main Database Additions

### `patient_medication.prescribed_by`

Stores the doctor who created the latest prescription version. The reference becomes null if the doctor account is removed, while the prescription remains.

### `medication_intake.taken_at`

Stores the exact confirmation timestamp from the patient portal.

### `notifications`

| Column | Purpose |
| --- | --- |
| `patient_id` | Notification owner |
| `notification_type` | Prescription, appointment, or doctor note |
| `title` | Short heading |
| `message` | Patient-facing text |
| `related_id` | Related record identifier |
| `is_read` | Read state |
| `created_at` | Creation timestamp |

Notifications are deleted automatically when the patient is deleted.

## 9. Authorization

Doctor patient queries use `patient.registered_by`. This prevents normal doctor pages from listing or opening another doctor's patients. Patient sessions contain only the recognized patient identifier. Administrator pages remain system-wide.

## 10. Face Authentication

```text
Staff registers one clear reference face
          |
          v
Encoding is stored with the patient
          |
          v
Patient provides camera image or photo
          |
          v
Nearest valid encoding inside tolerance is selected
          |
          v
Patient session opens without password
```

## 11. Testing Design

Automated tests cover role menus, reminder rules, notification messages, dataset definitions, schema features, and doctor intake-time display. PostgreSQL, camera, and complete role workflows are covered by `PRESENTATION_TEST_PLAN.md` on the target computer.

## 12. Academic Scope

Production use requires encrypted biometric data, stronger credential storage, full audit logs, backups, privacy consent, accessibility validation, and formal medical review.
