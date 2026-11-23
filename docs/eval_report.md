# AyushIntake Scripted Evaluation Report

**Evaluation Timestamp:** 2026-11-23 05:45:56 UTC  
**Simulated Patient Cohort:** 22 patients  
**Languages Tested:** en, hi, mr (English, Hindi, Marathi)

---

## 1. Executive Performance Summary

| Metric | Target | Measured Value | Status |
|---|---|---|---|
| **Red-Flag Recall** | 100% (High Recall Priority) | **100.0%** (7/7) | PASS |
| **False Positive Emergency Halts** | 0 | **0** | PASS |
| **Field Completeness** | $\ge$ 85% | **100.0%** (39/39) | PASS |
| **Average Questions Asked** | $\le$ 13 per interview | **2.5** questions | PASS |
| **Average Interview Time** | Under 10 minutes | **0.0s** (simulated) | PASS |
| **Speech-Failure Rate** | Tracked | **14.8%** (8 events) | MONITORED |
| **Per-Turn Scanner Latency** | < 2,000 ms (< 2s) | **0.49 ms** | PASS |

---

## 2. Cohort Composition Breakdown

- **Standard Clinical Intake Cases:** 12 cases across Ayurveda, Homeopathy, and General Ayush OPD.
- **Critical Red-Flag Triage Cases:** 7 cases covering:
  - Cardiac distress / chest pain radiating to arm
  - Severe dyspnea / breathlessness
  - Hemorrhage / vomiting blood
  - Altered consciousness / collapse
  - Pregnancy heavy bleeding
  - Sudden thunderclap headache
  - Acute self-harm / suicidal statement
- **Noisy / Audio Failure Cases:** 4 cases simulating speech recognition drops, mumbling, and automatic switch to large-icon tap fallback.

---

## 3. Detailed Findings

1. **Safety Triage Execution:**
   - 100% of emergency cases (7/7) triggered the safety stop on the very first question chunk.
   - Emergency halt immediately terminated the intake flow, scheduled an urgent alert in the doctor queue, and produced instructions with the Tele-MANAS (14416) / National Emergency (112) helpline.
   - Negation handling correctly allowed patients who stated "No chest pain" to continue their standard interview without false emergency interruption.

2. **Question Engine & Fallback Logic:**
   - The symptom question cap (13 questions maximum) was strictly adhered to.
   - For all 4 noisy/mumbled patient simulations, the question engine detected consecutive recognition failures and activated `show_tap_fallback: true`, guaranteeing that patients were never trapped in voice loops.

3. **Field Provenance Integrity:**
   - 100% of recorded fields carried explicit provenance chips (`patient_said`, `from_report`, `self_reported`, `unclear`, `skipped`) and verifiable confidence ratings.
