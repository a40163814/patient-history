# Safety, Triage & Privacy Protocol

AyushIntake is architected with healthcare safety and patient privacy as core non-negotiables.

---

## 1. Dual-Layer Red-Flag Triage Engine

The backend runs a dual-layer safety scanner on **every incoming transcript chunk** in real-time.

```
                           Patient Voice Utterance
                                      |
                                      v
          +--------------------------------------------------------+
          |         Layer 1: Deterministic Keyword Scanner         |
          |               (/config/red_flags.json)                 |
          +--------------------------------------------------------+
                                  /        \
                            [Match]        [No Match]
                              /                \
                             v                  v
          +-----------------------+   +------------------------------------+
          |  EMERGENCY HALT       |   |   Layer 2: Fast LLM Classifier     |
          |  * Cut audio stream   |   |   (/prompts/safety_classifier.txt) |
          |  * Trigger alert      |   +------------------------------------+
          |  * Show helpline      |           /               \
          +-----------------------+     [Flagged]          [Safe]
                                           /                  \
                                          v                    v
                                 [EMERGENCY HALT]      [Continue Interview]
```

### Mandatory Emergency Triggers Covered
1. **Cardiac Distress / Chest Pain:** Radiating arm pain, heavy crushing pressure, cold sweats (`cardiac_chest_pain`).
2. **Severe Dyspnea / Breathlessness:** Inability to breathe, suffocating, gasping, severe acute asthma (`respiratory_distress`).
3. **Severe Hemorrhage:** Hematemesis (vomiting blood), hemoptysis (coughing blood), uncontrollable bleeding (`severe_hemorrhage`).
4. **Altered Consciousness / Collapse:** Syncope, sudden blackout, loss of consciousness (`altered_consciousness`).
5. **Neurological / Stroke Deficit (FAST):** Facial drooping, unilateral weakness, sudden slurred speech (`stroke_neurological`).
6. **Obstetric / Pregnancy Danger Signs:** Vaginal bleeding during pregnancy, severe premature contractions, absent fetal movement (`pregnancy_danger`).
7. **Thunderclap / Agonizing Pain:** Sudden unbearable headache ("worst headache of life"), acute surgical abdomen (`acute_severe_pain`).
8. **Psychiatric Emergency / Self-Harm:** Explicit suicidal statements, threats of self-harm (`self_harm_crisis`).

### Emergency Action Protocol
- **Immediate Audio Kill Switch:** Audio generation and playback are abruptly terminated.
- **Calm Screen Presentation:** Displays: *"Please sit down and rest comfortably. Our clinic staff and medical team are being alerted immediately to attend to you right now."*
- **Active Helplines Displayed:**
  - National Mental Health Crisis Helpline: **Tele-MANAS (`14416`)**
  - National Emergency Number: **`112`**
  - Ambulance Service: **`108`**
- **Priority Queue Escalation:** Creates an immediate top-priority `CRITICAL` alert pinned to the top of the Doctor OPD Dashboard.

---

## 2. Non-Diagnostic Boundary & Adversarial Guardrails

- **Zero Diagnostic Output:** The model NEVER outputs a diagnosis, suggests what disease the patient may have, or says "this is probably X".
- **Zero Medication Suggestions:** The model never recommends medicines, supplements, or dosages.
- **Prominent Disclaimers:** Every screen and every generated PDF bears the prominent notice:  
  **"Draft prepared from patient answers. Not a diagnosis."**
- **Adversarial Defenses:** When patients ask *"What medicine should I take?"* or *"What is my diagnosis?"*, the system triggers an automatic deterministic redirection:  
  *"I am an intake assistant here only to note your health details for the doctor. I cannot prescribe medicines or provide medical diagnosis. The consulting Ayush doctor will examine you shortly and recommend the appropriate treatment."*
- **Untrusted Document Defense:** All uploaded files (prescriptions, lab slips) are treated purely as **untrusted data**. Any prompt injections (e.g. *"Ignore all previous instructions"*) embedded in document text or images are completely ignored.

---

## 3. Privacy & Compliance with India's DPDP Act 2023

1. **Explicit, Plain-Language Consent:** The consent screen informs the patient of what is collected, why, who sees it, and that audio is processed in-memory by an external AI provider. Progress is blocked until accepted.
2. **Guardian / Caregiver Mode:** When a minor or dependent is answering through a relative, the system records who is answering and captures guardian consent.
3. **Purpose Limitation & Data Minimization:** Only fields necessary for pre-OPD clinical evaluation are queried.
4. **No Raw Audio Retention:** Audio streams are processed purely in volatile memory. No raw audio files are persisted on clinic servers.
5. **Patient Session Isolation:** Every database operation is cryptographically scoped to a single `patient_token`. No cross-patient data access is possible.
6. **Comprehensive Audit Logging:** Every field view, inline edit, approval stamp, and PDF export is permanently logged with timestamp and user role in `audit_logs`.
7. **Synthetic Data Policy:** The test suite and seeded demo profiles use 100% synthetic fictitious patients and reports.
