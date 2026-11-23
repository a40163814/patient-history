# Legal & Clinical Review Checklist (DPDP Act 2023 & Ministry of Ayush)

Before deploying AyushIntake in a live government or private hospital OPD setting, legal counsel and a clinician advisory board must formally review and sign off on the following items:

---

## 1. Digital Personal Data Protection (DPDP) Act 2023 Compliance

- [ ] **Cross-Border Health Data Processing:**  
  *Context:* Real-time speech transcription via external cloud AI providers (e.g. Gemini Live API) may process transient audio on cloud infrastructure.  
  *Action:* Confirm whether cloud processing contracts satisfy Section 16 of the DPDP Act 2023 regarding cross-border transfer of sensitive personal data.
- [ ] **Data Principal Consent Architecture:**  
  *Context:* Section 6 of the DPDP Act mandates that consent must be free, specific, informed, unconditional, and unambiguous with clear notice.  
  *Action:* Review the multilingual consent screen text in Hindi, Marathi, and English to ensure regulatory compliance across regional hospital networks.
- [ ] **Minor & Dependent Guardian Consent (Section 9):**  
  *Context:* Ayush clinics treat pediatric patients and elderly dependents.  
  *Action:* Verify verification mechanisms for guardian consent and lawful representation.
- [ ] **Right to Erasure & Grievance Redressal (Section 12 & 13):**  
  *Context:* Patients may request deletion of pre-OPD case drafts or withdraw consent prior to consultation.  
  *Action:* Formalize retention schedules (`DATA_RETENTION_DAYS`) and appoint a Data Protection Officer (DPO) contact on the consent screen.

---

## 2. Clinical Validation & Professional Medical Council Alignment

- [ ] **Formal Validation of Question Bank (`/config/question_bank.json`):**  
  *Context:* Ayush systems (Ayurveda, Yoga & Naturopathy, Unani, Siddha, Homeopathy) feature unique diagnostic paradigms (e.g. Prakriti, Agni, Koshtha, Mizaj, Mukkuttram).  
  *Action:* A panel of registered Ayush doctors (BAMS / BHMS / BUMS / BSMS / BNYS) must review, test, and formally endorse all intake questions and adaptive follow-up sequences.
- [ ] **Red-Flag Danger Signs Validation (`/config/red_flags.json`):**  
  *Context:* Clinical triage protocols must align with national emergency guidelines (e.g. Directorate General of Health Services / NABH OPD triage guidelines).  
  *Action:* Emergency medicine specialists must confirm the exhaustiveness of the 8 danger categories.
- [ ] **Crisis Helpline Verification:**  
  *Context:* Emergency contact numbers are displayed during a red-flag stop.  
  *Action:* Re-verify active routing for:
  - Tele-MANAS (Mental Health Helpline): **`14416`**
  - Emergency Response Support System (ERSS): **`112`**
  - Emergency Medical Ambulance: **`108`**

---

## 3. Clinical Liability & Disclaimer Notice

- [ ] **Non-Diagnostic Shield:**  
  *Context:* Clinical software that assists pre-intake must not incur unauthorized practice liability.  
  *Action:* Confirm legal efficacy of the mandatory disclaimer stamped on all screens and PDFs:  
  *"Draft prepared from patient answers. Not a diagnosis. All clinical findings must be verified by the examining Ayush Medical Officer prior to prescription."*
