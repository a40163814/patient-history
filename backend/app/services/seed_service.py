import os
import uuid
from datetime import datetime, timezone, timedelta
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import delete
from backend.app.models.patient import Patient, ConsentRecord
from backend.app.models.intake_session import IntakeSession
from backend.app.models.clinical_data import ClinicalField
from backend.app.models.uploaded_report import UploadedReport, AuditLog
from backend.app.services.vitals import compute_bmi
from backend.app.services.mismatch_detector import mismatch_detector
from backend.app.schemas.reports import ExtractedLabValue

async def reset_and_seed_database(db: AsyncSession):
    """
    1-Click Reset and Seeding of 3 Realistic Synthetic Patients and Sample Reports.
    Complies with strict privacy standards (zero real patient data).
    """
    # 1. Clear existing records
    await db.execute(delete(AuditLog))
    await db.execute(delete(ClinicalField))
    await db.execute(delete(UploadedReport))
    await db.execute(delete(ConsentRecord))
    await db.execute(delete(IntakeSession))
    await db.execute(delete(Patient))
    await db.commit()

    now = datetime.now(timezone.utc)

    # --------------------------------------------------------------------------
    # PATIENT 1: Normal Flow (Ayurveda OPD - Joint Stiffness)
    # --------------------------------------------------------------------------
    p1 = Patient(
        phone_number="9876543210",
        full_name="Ramesh Sharma",
        patient_token="AYUSH-DEMO-001",
        age=52,
        gender="Male",
        preferred_language="hi"
    )
    db.add(p1)
    await db.flush()

    c1 = ConsentRecord(
        patient_id=p1.id,
        consent_given=True,
        is_guardian_mode=False
    )
    db.add(c1)

    bmi1, cat1 = compute_bmi(172, 70) # 23.7 Overweight
    s1 = IntakeSession(
        id=str(uuid.uuid4()),
        patient_id=p1.id,
        status="completed",
        current_section="lifestyle",
        ayush_system="allopathy",
        height_cm=172.0,
        weight_kg=70.0,
        bmi=bmi1,
        bmi_category=cat1,
        started_at=now - timedelta(minutes=25),
        completed_at=now - timedelta(minutes=15),
        total_duration_seconds=600,
        questions_asked_count=8,
        ai_summary="1. Chief concern: Joint pain and morning stiffness in knees for 3 weeks.\n"
                   "2. Pre-existing: Acidity and occasional gas.\n"
                   "3. Medicines: Triphala churna at bedtime.\n"
                   "4. Allergies: None disclosed.\n"
                   "5. Draft prepared from patient answers. Not a diagnosis."
    )
    db.add(s1)
    await db.flush()

    fields_p1 = [
        ("pre_existing_conditions", "known_chronic_conditions", "Acidity and occasional bloating after oily food", "patient_said", 0.96, "खाने के बाद कभी-कभी गैस और एसिडिटी बनती है"),
        ("allergies", "allergies_list", "No known food or drug allergies", "patient_said", 0.99, "कोई एलर्जी नहीं है"),
        ("current_medicines", "active_medications", "Triphala Churna 1 teaspoon with warm water at night", "patient_said", 0.97, "रात को त्रिफला चूर्ण लेता हूँ गर्म पानी से"),
        ("family_history", "family_health_history", "Father had joint arthritis", "patient_said", 0.92, "पिताजी को जोड़ों का दर्द था"),
        ("symptoms", "chief_complaint", "Knee stiffness and aching when standing up in the morning", "patient_said", 0.98, "सुबह उठने पर घुटनों में अकड़न और दर्द होता है"),
        ("symptoms", "symptom_duration", "3 weeks", "patient_said", 0.95, "तीन हफ्ते से"),
        ("symptoms", "symptom_severity", "Moderate, makes climbing stairs uncomfortable", "patient_said", 0.94, "मध्यम है, सीढ़ियां चढ़ने में तकलीफ होती है"),
        ("lifestyle", "agni_digestion_quality", "Sluggish digestion (Mandagni)", "patient_said", 0.91, "भूख सामान्य है लेकिन पचने में भारीपन रहता है")
    ]
    for sec, key, val, src, conf, quote in fields_p1:
        cf = ClinicalField(
            session_id=s1.id,
            section=sec,
            field_key=key,
            value=val,
            source=src,
            confidence=conf,
            transcript_quote=quote
        )
        db.add(cf)

    # --------------------------------------------------------------------------
    # PATIENT 2: Lab Mismatch Case (Denies diabetes, but HbA1c is 7.9%)
    # --------------------------------------------------------------------------
    p2 = Patient(
        phone_number="9823456789",
        full_name="Sunita Deshmukh",
        patient_token="AYUSH-DEMO-002",
        age=46,
        gender="Female",
        preferred_language="mr"
    )
    db.add(p2)
    await db.flush()

    c2 = ConsentRecord(
        patient_id=p2.id,
        consent_given=True,
        is_guardian_mode=False
    )
    db.add(c2)

    bmi2, cat2 = compute_bmi(158, 64) # 25.6 Obese
    s2 = IntakeSession(
        id=str(uuid.uuid4()),
        patient_id=p2.id,
        status="completed",
        current_section="lifestyle",
        ayush_system="allopathy",
        height_cm=158.0,
        weight_kg=64.0,
        bmi=bmi2,
        bmi_category=cat2,
        started_at=now - timedelta(minutes=40),
        completed_at=now - timedelta(minutes=30),
        total_duration_seconds=580,
        questions_asked_count=7,
        ai_summary="1. Chief concern: Fatigue and increased thirst for 1 month.\n"
                   "2. Pre-existing: States no chronic diseases.\n"
                   "3. Report conflict: Uploaded lab indicates HbA1c 7.9% and FBS 158 mg/dL.\n"
                   "4. Vitals: BMI 25.6 (Obese).\n"
                   "5. Draft prepared from patient answers. Not a diagnosis."
    )
    db.add(s2)
    await db.flush()

    fields_p2 = [
        ("pre_existing_conditions", "known_chronic_conditions", "None, no known chronic illness", "patient_said", 0.98, "मला कोणताही जुना आजार नाही"),
        ("allergies", "allergies_list", "No allergies", "patient_said", 0.99, "काही अ‍ॅलर्जी नाही"),
        ("current_medicines", "active_medications", "No regular medicines", "patient_said", 0.98, "काही औषधे घेत नाही"),
        ("symptoms", "chief_complaint", "Feeling tired and thirsty all day, waking up at night to urinate", "patient_said", 0.97, "खूप थकवा येतो आणि वारंवार तहान लागते"),
        ("symptoms", "symptom_duration", "1 month", "patient_said", 0.95, "एक महिन्यापासून")
    ]
    for sec, key, val, src, conf, quote in fields_p2:
        cf = ClinicalField(
            session_id=s2.id,
            section=sec,
            field_key=key,
            value=val,
            source=src,
            confidence=conf,
            transcript_quote=quote
        )
        db.add(cf)

    # Attach uploaded report with high sugar values to trigger mismatch
    rep_vals = [
        ExtractedLabValue(test_name="Fasting Blood Glucose", raw_value="158 mg/dL", numeric_value=158.0, unit="mg/dL", reference_range_printed="70 - 100 mg/dL", confidence=0.98),
        ExtractedLabValue(test_name="HbA1c", raw_value="7.9 %", numeric_value=7.9, unit="%", reference_range_printed="< 5.7 %", confidence=0.97)
    ]
    mismatches2 = mismatch_detector.detect_mismatches("None, no known chronic illness", rep_vals)

    rep2 = UploadedReport(
        session_id=s2.id,
        file_name="lab_blood_report_sunita.pdf",
        file_path="/mock_uploads/lab_blood_report_sunita.pdf",
        file_type="application/pdf",
        extracted_data={"lab_values": [lv.model_dump() for lv in rep_vals], "candidate_medicines": []},
        mismatch_flags=[m.model_dump() for m in mismatches2]
    )
    db.add(rep2)

    # --------------------------------------------------------------------------
    # PATIENT 3: Emergency Red-Flag Halt (Cardiac Distress)
    # --------------------------------------------------------------------------
    p3 = Patient(
        phone_number="9123456780",
        full_name="Vijay Patil",
        patient_token="AYUSH-DEMO-003",
        age=58,
        gender="Male",
        preferred_language="en"
    )
    db.add(p3)
    await db.flush()

    c3 = ConsentRecord(
        patient_id=p3.id,
        consent_given=True,
        is_guardian_mode=True,
        guardian_name="Anil Patil",
        guardian_relation="Son"
    )
    db.add(c3)

    bmi3, cat3 = compute_bmi(168, 74) # 26.2 Obese
    s3 = IntakeSession(
        id=str(uuid.uuid4()),
        patient_id=p3.id,
        status="emergency_halt",
        current_section="symptoms",
        ayush_system="allopathy",
        height_cm=168.0,
        weight_kg=74.0,
        bmi=bmi3,
        bmi_category=cat3,
        has_red_flag=True,
        red_flag_category="cardiac_chest_pain",
        red_flag_details="Matched danger term 'chest pain' in cardiac_chest_pain category. Patient stated: 'Severe crushing chest pain radiating to my left arm'.",
        red_flag_triggered_at=now - timedelta(minutes=5),
        started_at=now - timedelta(minutes=8),
        completed_at=now - timedelta(minutes=5),
        total_duration_seconds=180,
        questions_asked_count=1
    )
    db.add(s3)
    await db.flush()

    cf3 = ClinicalField(
        session_id=s3.id,
        section="red_flags",
        field_key="chief_emergency_check",
        value="Emergency Red-Flag Triggered: Severe crushing chest pain radiating to left arm",
        source="patient_said",
        confidence=1.0,
        transcript_quote="I have severe crushing chest pain going to my arm"
    )
    db.add(cf3)

    audit3 = AuditLog(
        session_id=s3.id,
        actor_role="system",
        action="session_halted",
        details="CRITICAL EMERGENCY HALT: Cardiac red flag. Staff notified on site."
    )
    db.add(audit3)

    await db.commit()
    return {"status": "success", "seeded_patients": 3}
