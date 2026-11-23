import os
from pathlib import Path
from backend.app.services.pdf_generator import clinical_pdf_generator

def test_generate_pdf_case_sheet():
    session_id = "test-session-12345"
    patient_data = {
        "patient_token": "AYUSH-TEST-999",
        "phone_number": "9876543210",
        "preferred_language": "en",
        "ayush_system": "ayurveda",
        "guardian_info": "Self"
    }
    vitals = {
        "height_cm": 170.0,
        "weight_kg": 68.0,
        "bmi": 23.5,
        "bmi_category": "Overweight",
        "vitals_label": "self-reported"
    }
    clinical_fields = [
        {
            "section": "pre_existing_conditions",
            "field_key": "known_chronic_conditions",
            "value": "Mild acidity and occasional hypertension",
            "source": "patient_said",
            "confidence": 0.95,
            "transcript_quote": "I have some gas and mild BP"
        },
        {
            "section": "current_medicines",
            "field_key": "active_medications",
            "value": "Triphala Churna 1 tsp night, Amlodipine 5mg",
            "source": "patient_said",
            "confidence": 0.98,
            "transcript_quote": "Taking triphala and amlodipine"
        },
        {
            "section": "symptoms",
            "field_key": "chief_complaint",
            "value": "Joint stiffness in both knees in mornings",
            "source": "patient_said",
            "confidence": 0.99,
            "transcript_quote": "Knees feel stiff when I wake up"
        }
    ]
    mismatch_flags = [
        {
            "biomarker": "Fasting Blood Sugar",
            "message": "Check: patient answer differs from report (Blood Sugar: reported 'No diabetes', report indicates '152 mg/dL')"
        }
    ]
    reports = [
        {
            "file_name": "blood_test_jan.pdf",
            "file_type": "application/pdf",
            "lab_values": [{"test_name": "Fasting Blood Sugar", "raw_value": "152 mg/dL", "reference_range_printed": "70-100"}]
        }
    ]
    doctor_review = {
        "doctor_id": "DOC-AYUSH-KUMAR",
        "doctor_notes": "Advised Janu Basti and diet regulation. Continue routine follow-up.",
        "ai_summary": "1. Chief concern: Joint stiffness.\n2. Medications: Triphala & Amlodipine.\n3. Draft prepared from patient answers. Not a diagnosis."
    }

    pdf_path = clinical_pdf_generator.generate_case_sheet(
        session_id=session_id,
        patient_data=patient_data,
        vitals=vitals,
        clinical_fields=clinical_fields,
        mismatch_flags=mismatch_flags,
        reports=reports,
        doctor_review=doctor_review,
        has_red_flag=False
    )

    assert os.path.exists(pdf_path)
    assert os.path.getsize(pdf_path) > 1000 # Valid non-empty PDF binary

def test_generate_pdf_when_session_dropped():
    # Even if session dropped midway with 0 clinical fields, valid PDF must be generated
    pdf_path = clinical_pdf_generator.generate_case_sheet(
        session_id="dropped-session-000",
        patient_data={"patient_token": "AYUSH-DROPPED-1", "phone_number": "9111111111"},
        vitals={},
        clinical_fields=[],
        mismatch_flags=[],
        reports=[],
        doctor_review={"doctor_id": "DOC-EMERGENCY"}
    )
    assert os.path.exists(pdf_path)
    assert os.path.getsize(pdf_path) > 500
