# Complete Presentation Test Plan

This plan demonstrates every important feature in a logical order. Use a local PostgreSQL database and a camera or a clear face photograph.

## 1. Prepare the Demonstration

From the project directory:

```bash
python seed_database.py --reset-demo
python -m unittest discover -s tests -p "test_*.py" -v
python tests/database_smoke_test.py
streamlit run app.py
```

Expected seed accounts:

| Role | Username | Password |
| --- | --- | --- |
| Administrator | `admin` | `Admin@123` |
| Doctor | `dr.reza.sharifi` | `Doctor@123` |

The dataset creates 12 doctors and 24 patients. Dr. Reza Sharifi receives two demo patients, active prescriptions, seven days of intake history, a doctor note, notifications, one completed visit, and one appointment for today.

## 2. Administrator Scenario

Sign in with the administrator account.

### Dashboard

Show the total patient, doctor, medicine, and appointment cards. Open the charts to confirm that appointment and adherence data are not empty.

### Manage Doctors

1. Confirm that `Dr. Reza Sharifi` exists.
2. Add a temporary doctor:
   - Full name: `Dr. Pouya Azadi`
   - Username: `dr.pouya.azadi`
   - Password: `Doctor@123`
   - Specialty: `General Medicine`
3. Confirm the account appears in the table.
4. Delete only the temporary account to demonstrate safe doctor removal.

Expected result: the permanent  demo doctors remain available and clinical records are not deleted with a doctor account.

### Manage Medications

1. Search for `Metformin` and show its description.
2. Add a temporary catalog item named `Presentation Medicine`.
3. Delete the unused temporary item.
4. Attempt to delete a medicine already used by a patient.

Expected result: an unused medicine is deleted; a medicine used in a prescription is protected.

### Manage Patients

1. Search for `Farhad Ahmadi`.
2. Show the assigned doctor, demographics, prescriptions, reminders, appointments, and notes.
3. Demonstrate that the administrator can reassign a patient, but leave Farhad assigned to Dr. Reza Sharifi after the demonstration.

## 3. Doctor Scenario

Log out and sign in as `dr.reza.sharifi`.

### Dashboard

Show:

- Two assigned demo patients
- Active prescription count
- Today's appointment
- Seven-day adherence chart
- `Latest Patient Intake Activity`

Point out that the latest activity table has both the scheduled time and the actual confirmation time reported by the patient.

### Register a Real Test Patient

Register a person who is available during the presentation:

| Field | Suggested value |
| --- | --- |
| First name | `Nima` |
| Last name | `Azadi` |
| National code | a new 10-digit value |
| Phone | `09121234567` |
| Age | `68` |
| Gender | `Male` |
| Address | `Tehran` |
| Face photo | current camera/photo of the presenter or volunteer |

Expected result: exactly one clear face is accepted and the patient is assigned automatically to Dr. Reza Sharifi.

### Add Medication

Select the newly registered patient and prescribe:

| Field | Suggested value |
| --- | --- |
| Medication | `Metformin` |
| Dosage | `500 mg` |
| Instructions | `Take after breakfast with water.` |
| Times per day | `2` |
| Dose times | one time near the current clock and one later time |

Expected result: the prescription is saved, reminder times become active, and a `New prescription` notification is created for the patient.

### Patient Profiles

Open the real test patient.

1. `Overview`: show identity, face photo, assigned doctor, and next appointment.
2. `Prescriptions`: show Metformin, dosage, instructions, and reminder times.
3. `Reminders & Adherence`: show scheduled dose status and the actual patient confirmation column.
4. `Appointments & Notes`: schedule a future appointment and add a short doctor note.
5. `Edit Record`: show that the doctor can update the assigned patient's data and replace the reference face image.

Expected result: appointment and note actions create patient notifications.

## 4. Patient Face-Login Scenario

Log out and choose `Patient Face Login`.

1. Use the same person or upload the same clear photograph used at registration.
2. Confirm that no username or password is requested.
3. Show the patient's simplified menu.

### Home

Show active medicines, remaining doses, today's list, next appointment, and latest notifications.

### My Medications

Show medication name, dosage, instructions, treatment dates, reminder times, and prescribing doctor.

### Notifications

Show the three newly created items:

- New prescription
- New appointment
- New doctor note

Mark one notification as read, then use `Mark all as read`.

### Reminders and Actual Intake Time

For the dose near the current time, select `I took this medicine now`.

Expected result:

- The scheduled reminder time stays unchanged.
- The system stores the current date and time as the actual confirmation.
- The status changes to `Taken`.
- The actual confirmation is visible in recent intake history.

### Appointments & Notes

Show the appointment and doctor recommendation created earlier.

### My Profile

Show the stored face photo, contact information, emergency contact, and assigned doctor.

## 5. Return to the Doctor

Log out from the patient account and sign in again as Dr. Reza Sharifi.

1. Open the Dashboard.
2. Show the new entry in `Latest Patient Intake Activity`.
3. Open `Patient Profiles > Reminders & Adherence` for the test patient.
4. Compare the scheduled time with the patient's actual confirmation time.

This closes the complete doctor-to-patient-to-doctor workflow.

## 6. Negative and Validation Tests

Use these only if time remains:

| Test | Expected result |
| --- | --- |
| Register a duplicate national code | Registration is rejected |
| Upload an image without a face | Face validation error |
| Upload an image with multiple faces | Registration is rejected |
| Use an unknown face at login | Patient is not identified |
| Leave dosage empty | Prescription is not saved |
| Set end date before start date | Validation error |
| Doctor searches another doctor's patient | Patient is not listed |
| Patient tries to access staff pages | No staff navigation is available |
| Delete a medicine currently prescribed | Deletion is blocked |

## 7. Presentation Completion Checklist

- Administrator management shown
- Doctor and patient data shown
- Doctor dashboard populated
- Real patient registered with a face
- Prescription saved
- Patient notification received
- Appointment and note notification received
- Face login completed
- Medicine marked as taken
- Actual intake time visible to patient
- Actual intake time visible to doctor
- Role access restrictions demonstrated
