from backend.app.services.mismatch_detector import mismatch_detector
from backend.app.schemas.reports import ExtractedLabValue

def test_diabetes_mismatch_detected_when_denied():
    # Patient denies any conditions
    patient_conditions = "No prior conditions, I am completely healthy"
    extracted = [
        ExtractedLabValue(
            test_name="Fasting Blood Glucose",
            raw_value="152 mg/dL",
            numeric_value=152.0,
            unit="mg/dL"
        )
    ]
    flags = mismatch_detector.detect_mismatches(patient_conditions, extracted)
    assert len(flags) == 1
    assert flags[0].biomarker == "Fasting Blood Sugar"
    assert "Check: patient answer differs from report" in flags[0].message
    assert "152.0 mg/dL" in flags[0].message

def test_hba1c_mismatch_detected():
    patient_conditions = "None"
    extracted = [
        ExtractedLabValue(
            test_name="Glycated Hemoglobin (HbA1c)",
            raw_value="7.6 %",
            numeric_value=7.6,
            unit="%"
        )
    ]
    flags = mismatch_detector.detect_mismatches(patient_conditions, extracted)
    assert len(flags) == 1
    assert flags[0].biomarker == "HbA1c"
    assert "7.6 %" in flags[0].message

def test_no_mismatch_when_patient_disclosed_condition():
    patient_conditions = "Yes, I was diagnosed with diabetes and sugar problem 3 years ago"
    extracted = [
        ExtractedLabValue(
            test_name="Fasting Blood Sugar",
            raw_value="148 mg/dL",
            numeric_value=148.0,
            unit="mg/dL"
        ),
        ExtractedLabValue(
            test_name="HbA1c",
            raw_value="7.2 %",
            numeric_value=7.2,
            unit="%"
        )
    ]
    flags = mismatch_detector.detect_mismatches(patient_conditions, extracted)
    # Since patient already disclosed diabetes, no contradictory mismatch is flagged
    assert len(flags) == 0

def test_hypertension_mismatch():
    patient_conditions = "I only have mild knee pain, nothing else"
    extracted = [
        ExtractedLabValue(
            test_name="Systolic Blood Pressure",
            raw_value="155 mmHg",
            numeric_value=155.0,
            unit="mmHg"
        )
    ]
    flags = mismatch_detector.detect_mismatches(patient_conditions, extracted)
    assert len(flags) == 1
    assert flags[0].biomarker == "Systolic BP"
    assert "155.0 mmHg" in flags[0].message
