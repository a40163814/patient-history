# AyushIntake — Pre-OPD AI Voice Assistant & Clinical Triage

> **Ministry of Ayush (India) Setting**  
> An intelligent, accessible pre-OPD voice intake web application that takes a patient's medical history before a clinical consultation, extracts structured health data with provenance, and produces a doctor-approved case sheet and ReportLab PDF.

---

## ⚠️ Mandatory Clinical Notice

> **Draft prepared from patient answers. Not a diagnosis.**  
> AyushIntake strictly **collects and organizes** information. The AI never diagnoses, prescribes medications or dosages, or interprets laboratory values. All data must be reviewed and approved by a licensed Ayush Medical Officer before consultation.

---

## Architecture Highlights

- **Multilingual Support:** English, Hindi (हिंदी), and Marathi (मराठी).
- **Responsive Platform:** Mobile-first for patients (installable PWA with service worker caching), tablet kiosk mode for staff-assisted hospital entry, and desktop clinical layout for doctors.
- **Dual-Layer Red-Flag Triage:** 
  1. Synchronous regex and keyword scanner across English, Hindi, and Marathi (`/config/red_flags.json`).
  2. Asynchronous LLM danger classifier (`/prompts/safety_classifier.txt`).
  3. Immediate emergency halt screen with active hotlines: Tele-MANAS (`14416`) and National Emergency (`112` / `108`).
- **Clinician-Reviewable Configurations:** Triage rules and lab mismatch thresholds are stored exclusively in `/config/` JSON files, never buried in application code.
- **Strict Data Provenance:** Every stored field tracks its source (`patient_said`, `from_report`, `self_reported`, `unclear`, `skipped`), confidence rating, and linked transcript quote.
- **Discrepancy / Lab Mismatch Scanner:** Flags conflicting patient answers against OCR-extracted diagnostic reports (e.g. denying diabetes when HbA1c is 7.9%) as *"Check: patient answer differs from report"*.
- **ReportLab PDF Engine:** Fixed immutable template with ministry branding, vitals, mismatch warnings, provenance chips, doctor inline edits, and official approval stamp.

---

## Quick Start (One Command per Service)

### Prerequisites
- **Python:** 3.12+ (Tested on Python 3.14 / 3.13)
- **Node.js:** 24 LTS / 26 LTS

### 1. Environment Setup
Clone the repository and copy the example environment file:
```bash
cp .env.example .env
```

### 2. Backend Service (FastAPI)
From the project root:
```bash
# Setup virtual environment (first time only)
python -m venv .venv

# Activate virtual environment
# Windows:
.venv\Scripts\activate
# Linux/macOS:
source .venv/bin/activate

# Install dependencies
pip install -r backend/requirements.txt

# Run Backend
python backend/run.py
```
*The FastAPI backend will start on `http://localhost:8000` (API docs at `/docs`).*

### 3. Frontend Service (React + Vite PWA)
In a new terminal:
```bash
cd frontend
npm install
npm run dev
```
*The frontend client will open on `http://localhost:5173`.*

---

## Running the Automated Test & Evaluation Suite

Run the full pytest suite (including red-flag rules, BMI, mismatch detection, patient session isolation, adversarial guards, and 22-patient scripted evaluation):
```bash
pytest
```
*All 31 unit tests and the scripted evaluation benchmark will execute.*

---

## 1-Click Demo Testing Scenarios

The Doctor OPD dashboard includes a **"1-Click Reset & Seed"** button that instantly seeds 3 realistic synthetic patients:

1. **Ramesh Sharma (`AYUSH-DEMO-001`, Hindi):**  
   Normal OPD intake for morning knee stiffness (Ayurvedic Sandhivata). Demonstrates full voice Q&A, vitals computation (BMI 23.7), and clean case sheet generation.
2. **Sunita Deshmukh (`AYUSH-DEMO-002`, Marathi):**  
   Lab mismatch test. Patient denies chronic illness, but an uploaded blood test indicates HbA1c 7.9% and Fasting Blood Glucose 158 mg/dL. The system flags: *"Check: patient answer differs from report"*.
3. **Vijay Patil (`AYUSH-DEMO-003`, English):**  
   Emergency Red-Flag test. Patient discloses severe crushing chest pain radiating to left arm. System immediately halts intake, cuts audio, displays calm triage directions with Tele-MANAS `14416`, and creates a top-priority red alert in the doctor queue.

---

## Documentation Index

- [Architecture & State Machine](docs/architecture.md)
- [Safety, Triage & Privacy Protocol](docs/safety_and_privacy.md)
- [Known Limitations & Fallbacks](docs/known_limitations.md)
- [DPDP Act 2023 & Clinical Legal Review Checklist](docs/legal_review_todo.md)
- [Scripted Evaluation Report (22 Simulated Patients)](docs/eval_report.md)
- [3-Minute Live Demo Pitch Script](docs/demo_script.md)
