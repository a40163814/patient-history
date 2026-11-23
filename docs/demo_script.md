# 3-Minute Live Demo Script: AyushIntake

> **Presenter Role:** Health-tech Architect & Lead Engineer  
> **Audience:** Hackathon Judges, Clinicians, Ayush OPD Administrators  
> **Demo URL:** `http://localhost:5173` (Frontend) & `http://localhost:8000` (Backend)

---

### [00:00 – 00:30] Introduction & The Problem
> *"Good morning judges. In outpatient departments across the Ministry of Ayush in India, doctors see 60 to 100 patients daily. Over 60% of their consultation time is consumed taking basic medical histories, asking about chronic conditions, OTC herbal remedies, and typing notes.*
> 
> *Meet **AyushIntake**: an accessible, multilingual pre-OPD voice assistant that takes a patient's history in the waiting area, strictly organizes it with provenance, flags lab discrepancies, and prepares a verified case sheet and PDF for the doctor.*
> 
> *Crucially: **The AI only collects and organizes. It never diagnoses, recommends treatment or dosage, or interprets lab values.**"*

---

### [00:30 – 01:15] Act 1: The Patient Flow & Voice Engine (Normal Flow)
1. **Login & Multilingual Selection:**
   - Click **"Patient (PWA)"** view on top.
   - Show language selection: Select **हिंदी (Hindi)** or **मराठी (Marathi)**.
   - Click quick demo profile: **Ramesh (Hindi)** and tap **"Begin Intake"**.
2. **Informed Consent (DPDP Act 2023):**
   - Point out clear disclosures: What is collected, why, who sees it, and that raw audio is processed in memory and not stored.
   - Show the **Guardian / Caregiver Mode** toggle (e.g. parent answering for minor).
   - Check the box and tap **"Accept & Continue"**.
3. **Vitals & Code-Computed BMI:**
   - Enter height (172 cm) and weight (70 kg).
   - Show the live **BMI display: 23.7 kg/m² (Overweight)** labeled strictly as **"self-reported"**.
   - Tap **"Proceed to Voice Interview"**.
4. **Adaptive Voice Q&A:**
   - Tap **"Start Voice Interview"**. The voice engine speaks the question in natural Hindi.
   - Show the live captions and the **"Listening"** indicator.
   - Demonstrate **Barge-in Interrupt:** Tap *"Tap to Interrupt & Speak"*, showing immediate audio stop.
   - Show the elderly accessibility features: **Large Text mode** and **Adjustable Speech Speed**.

---

### [01:15 – 01:50] Act 2: Safety Triage (Red-Flag Emergency Halt)
1. **Triggering an Emergency:**
   - Switch to patient **Vijay Patil (English)** or speak:  
     *"I have severe crushing chest pain going to my left arm right now."*
2. **Immediate System Reaction:**
   - Point out that **audio output cuts out instantly**.
   - The screen turns calm red:  
     *"Please sit down and rest comfortably. Our clinic staff and medical team are being alerted immediately to attend to you right now."*
   - Point out the active national crisis numbers: **Tele-MANAS (`14416`)** and **Emergency Ambulance (`108` / `112`)**.
   - Explain: *"Safety is non-negotiable. Our dual-layer scanner halted the session within milliseconds and queued an emergency alert for staff."*

---

### [01:50 – 02:30] Act 3: Report OCR & Lab Mismatch Flag
1. **The Discrepancy Scenario:**
   - Switch to **Sunita Deshmukh (Marathi)**.
   - Patient stated: *"I have no chronic diseases, completely healthy."*
   - But she uploaded a lab report (`lab_blood_report_sunita.pdf`).
   - Show the OCR extraction: **HbA1c: 7.9%**, **Fasting Blood Glucose: 158 mg/dL**.
2. **The Discrepancy Alert:**
   - The system detects the conflict against `/config/lab_thresholds.json` and displays:  
     **"⚠️ Check: patient answer differs from report (Blood Sugar: reported 'None', report indicates '158 mg/dL')"**
   - Point out: *"Notice it does not say 'Patient has diabetes'. It says 'Check: patient answer differs from report' so the doctor can clarify."*

---

### [02:30 – 03:00] Act 4: Doctor Dashboard, Inline Audit & Immutable PDF
1. **Doctor Priority Queue:**
   - Click **"Doctor OPD"** tab on top.
   - Point out the priority sort: Vijay's **CRITICAL RED-FLAG** is pinned to the top, followed by Sunita's **LAB MISMATCH**, then standard patients.
2. **Case Sheet Review:**
   - Open Ramesh's case sheet.
   - Point out the **Provenance Chips** on every field:
     - `[patient_said]` with exact transcript quote *"रात को त्रिफला चूर्ण लेता हूँ"*
     - `[self_reported]` for BMI
   - Show **Inline Doctor Editing:** Click edit on pre-existing condition, change it to *"Acidity (Amlapitta)"*. The system logs a permanent audit entry showing doctor ID, timestamp, and diff.
   - Point out the **AI-Generated Summary** (strictly 5 lines, fully editable by the doctor).
3. **Approval & PDF Generation:**
   - Tap **"Approve & Stamp PDF"**.
   - Click **"Download Stamped PDF"**.
   - Show the final ReportLab PDF:
     - Government Ayush branding.
     - Prominent legal notice: *"Draft prepared from patient answers. Not a diagnosis."*
     - Structured clinical history with source tags.
     - Extracted report readings.
     - Doctor's digital approval stamp and timestamp.
4. **Closing Pitch:**
   - *"AyushIntake saves up to 8 minutes per patient, prevents missed emergencies, and empowers doctors to practice medicine rather than data entry. Thank you!"*
