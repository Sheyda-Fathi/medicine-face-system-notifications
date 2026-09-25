# Patient Medication Management System with Face Recognition

A local Streamlit and PostgreSQL application for managing patients, prescriptions, medication reminders, appointments, and doctor notes. Elderly patients sign in with their face instead of a username and password.

## Main Workflow

```text
Administrator prepares doctors and the medicine catalog
                    |
                    v
Doctor registers a patient and reference face photo
                    |
                    v
Doctor writes a prescription and reminder times
                    |
                    v
Patient receives a notification and signs in by face
                    |
                    v
Patient confirms each dose after taking it
                    |
                    v
Doctor sees scheduled time and actual confirmation time
```

## User Roles

### Administrator

- View system totals and charts
- Add, review, reassign, and delete patients
- Add and delete doctor accounts
- Add and delete unused catalog medicines

The administrator does not prescribe medicine or write clinical notes.

### Doctor

- View assigned patients and today's appointments
- Register a patient with a face photograph
- Prescribe medicines and daily reminder times
- Review prescriptions, adherence, and actual dose-confirmation times
- Add doctor notes and schedule appointments

A doctor can access only patients assigned to that doctor.

### Patient

- Sign in by camera or uploaded face photograph
- Read current prescriptions and doctor instructions
- Receive notifications for prescriptions, appointments, and doctor notes
- Confirm a medicine dose with `I took this medicine now`
- Review scheduled time and actual confirmation time
- View appointments, notes, and profile information

## Project Structure

```text
medicine_face_system/
|-- app.py
|-- seed_database.py
|-- requirements.txt
|-- config/
|   |-- navigation.py
|   |-- settings.py
|   `-- theme.py
|-- database/
|   |-- connection.py
|   |-- auth_queries.py
|   |-- patient_queries.py
|   |-- medication_queries.py
|   |-- notification_queries.py
|   |-- appointment_queries.py
|   `-- notes_queries.py
|-- face/
|-- page/
|-- services/
|-- tests/
|-- documents/
`-- media/patients/
```

## Requirements

- Python 3.11 recommended
- PostgreSQL
- Windows, Linux, or macOS
- Camera for live patient login, or a clear face photograph for testing

## Installation on Windows

Open CMD in the project folder:

```bat
python -m venv venv
venv\Scripts\activate
python -m pip install --upgrade pip
pip install -r requirements.txt
```

For PowerShell activation:

```powershell
.\venv\Scripts\Activate.ps1
```

Copy `.env.example` to `.env`, fill in your local PostgreSQL credentials, then prepare the database:

```bat
python seed_database.py --reset-demo
```

The reset flag removes only the previous generated English demo records and rebuilds the presentation dataset. It does not remove ordinary patients registered outside the known demo code ranges.

Start the application:

```bat
streamlit run app.py
```

Open `http://localhost:8501` if the browser does not open automatically.

## Demonstration Accounts

| Role | Username | Password |
| --- | --- | --- |
| Administrator | `admin` | `Admin@123` |
| Doctor | `dr.reza.sharifi` | `Doctor@123` |

All seeded doctors use `Doctor@123`. Change demonstration passwords before using the project outside a classroom environment.

##  Demonstration Data

The seed creates:

- 12  doctors, including Dr. Reza Sharifi
- 24  patients
- Two patients for every doctor
- Active prescriptions and reminder times
- Seven days of taken and missed dose records
- Actual confirmation timestamps
- Doctor notes
- Completed and upcoming appointments
- Patient notifications

Seeded patients do not support face login unless consented images are placed in `media/patients/seed` before running the seed. For the presentation, register one real test patient with a new photograph.

## Automated Tests

Run:

```bat
python -m unittest discover -s tests -p "test_*.py" -v
```

The test suite checks:

- Role menus and access design
- Notification menu behavior
- Reminder parsing and Taken/Missed/Pending rules
- Notification message contents
- seed names and counts
- Notification and intake-time schema
- Doctor display of actual patient confirmation time

After seeding PostgreSQL, run the read-only database verification:

```bat
python tests/database_smoke_test.py
```

## Complete Presentation Test

Follow:

```text
documents/PRESENTATION_TEST_PLAN.md
```

It provides a start-to-finish demonstration for the administrator, Dr. Reza Sharifi, a newly registered face-login patient, notifications, medication intake, and the return flow to the doctor panel.

## Important Behavior

### Prescription Notification

When a doctor saves a prescription, the patient immediately receives a `New prescription` notification containing the medicine, dosage, reminder times, and doctor name.

### Intake Time

The system stores two separate values:

- Scheduled time: the reminder configured by the doctor
- Actual confirmation time: the exact time the patient selects `I took this medicine now`

Both values are visible in the patient history and the doctor's adherence views.

### Dose Status

- `Taken`: the patient confirmed the dose
- `Missed`: an explicit missed record exists or the scheduled time has passed without confirmation
- `Pending`: the scheduled time has not arrived

## Environment Configuration

This project reads database credentials from a `.env` file (not committed to git).

​```bash
copy .env.example .env
​```

Edit `.env` and set your real PostgreSQL host, port, database name, username, and password.

## Documentation

- `documents/INSTALLATION_GUIDE.md`: detailed installation and troubleshooting
- `documents/USER_MANUAL.md`: every role and menu
- `documents/SYSTEM_DESIGN.md`: architecture, authorization, notifications, and intake workflow
- `documents/PRESENTATION_TEST_PLAN.md`: complete presentation script and validation cases
- `documents/FINAL_REPORT.md`: English report
- `documents/FINAL_REPORT.docx`: Persian academic report

## Academic Scope

This project is an academic demonstration. A production healthcare system would additionally require strong password hashing, encrypted biometric storage, audit logging, backup and recovery, privacy consent, accessibility testing, and formal clinical validation.

## License

Educational and academic use only.
