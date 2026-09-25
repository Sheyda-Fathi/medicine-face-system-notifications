# Detailed Installation Guide

This guide contains the platform-specific setup and troubleshooting details that are intentionally not repeated in full in the project README. The README is the primary quick-start document; this file is for installation problems and environment preparation.

## 1. Supported Environment

Recommended configuration:

- Windows 10 or Windows 11
- Python 3.11, 64-bit
- PostgreSQL 14 or newer
- A webcam for camera-based patient login
- At least 4 GB of available memory during dlib installation

## 2. PostgreSQL Setup

Open pgAdmin or `psql` and create the database:

​```sql
CREATE DATABASE final_db;
​```

Copy `.env.example` to `.env` and fill in your real database credentials:

​```bash
copy .env.example .env
​```

Then edit `.env` and set `SMMS_DB_PASSWORD` and the other values to match your local PostgreSQL setup. The application reads these values automatically; `config/settings.py` no longer contains any hardcoded credentials.پ
## 3. Python Virtual Environment

Windows Command Prompt:

```bat
cd C:\path\to\medicine_face_system
python -m venv venv
venv\Scripts\activate
```

Windows PowerShell:

```powershell
cd C:\path\to\medicine_face_system
python -m venv venv
.\venv\Scripts\Activate.ps1
```

If PowerShell blocks activation, run the following command in the same window and activate again:

```powershell
Set-ExecutionPolicy -Scope Process -ExecutionPolicy Bypass
```

## 4. Dependency Installation

```bash
python -m pip install --upgrade pip setuptools wheel
python -m pip install -r requirements.txt
```

### dlib or face_recognition installation failure

Confirm that the active Python version is 3.11 and 64-bit:

```bash
python --version
python -c "import platform; print(platform.architecture())"
```

On Windows, installing Microsoft C++ Build Tools may be necessary when a compatible dlib wheel is unavailable.

## 5. Database Initialization, Administrator, and Demo Data

Only one setup script is needed:

```bash
python seed_database.py --reset-demo
```

This command:

1. Creates or updates all tables
2. Creates or repairs the `admin` account
3. Creates or repairs demonstration doctor accounts
4. Ensures demonstration medicines exist
5. Rebuilds 24  demo patients with prescriptions, intake history, notifications, notes, and appointments

Default administrator:

```text
admin / Admin@123
```

Default doctor:

```text
dr.reza.sharifi / Doctor@123
```

## 6. Automated Test Run

Before the presentation, run:

```bash
python -m unittest discover -s tests -p "test_*.py" -v
python tests/database_smoke_test.py
```config/settings.py

All tests should report `OK`. The camera and PostgreSQL workflow is then checked with `documents/PRESENTATION_TEST_PLAN.md`.

## 7. Running the Application

```bash
streamlit run app.py
```

Browser address:

```text
http://localhost:8501
```

## 8. Face-Login Test

For the most reliable test, register a new patient through a doctor or administrator account using a real photograph. Log out, open `Patient Face Login`, choose `Upload Photo`, and upload the same image.

The demonstration patients created without photographs cannot use face login because they do not have stored biometric encodings.

## 9. Common Problems

### Invalid distributions such as `~treamlit` or `~lotly`

These warnings normally come from damaged package folders in the global Python installation. Confirm that the virtual environment is active and reinstall the affected package inside it:

```bash
python -m pip uninstall streamlit plotly -y
python -m pip install streamlit==1.28.0
```

Plotly is not required by this project.

### Database connection error

Check:

- PostgreSQL service is running
- Database name is `final_db`
- Username and password in your `.env` file are correct
- Port `5432` is not being used by a different PostgreSQL instance

### Patient face is not recognized

Check:

- The patient was registered with a face photograph
- The image contains exactly one person
- Lighting and camera angle are similar to the registration image
- The face is not covered
- The image is not blurred

### Doctor sees no patients

Doctors see only patients assigned to their account. An administrator can open `Manage Patients > Patient Profiles > Edit Record` and assign the patient to the correct doctor.
