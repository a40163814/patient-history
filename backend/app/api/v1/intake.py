from typing import List, Optional
from datetime import datetime, timezone
from fastapi import APIRouter, Depends, HTTPException, status, Query
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from backend.app.models.base import get_db
from backend.app.models.patient import Patient, ConsentRecord
from backend.app.models.intake_session import IntakeSession
from backend.app.models.clinical_data import ClinicalField
from backend.app.models.uploaded_report import UploadedReport, AuditLog
from backend.app.schemas.intake import (
    ConsentRequest, ConsentResponse,
    VitalsRequest, VitalsResponse,
    QuestionResponse, RecordAnswerRequest
)
from backend.app.services.vitals import compute_bmi
from backend.app.services.question_engine import question_engine
from backend.app.services.red_flag_scanner import red_flag_scanner
from backend.app.services.reconciler import post_session_reconciler
from backend.app.services.extractor_service import clinical_extractor
from backend.app.core.security import verify_patient_session

router = APIRouter(prefix="/intake", tags=["Intake Flow"])

@router.post("/consent", response_model=ConsentResponse)
async def submit_consent(req: ConsentRequest, db: AsyncSession = Depends(get_db)):
    """
    Plain-Language Consent Acceptance:
    Complies with DPDP Act 2023. Captures guardian details if acting for a minor/dependent.
    Blocks intake progress until consent is granted.
    """
    if not req.consent_given:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Intake cannot proceed without informed patient consent."
        )

    stmt = select(Patient).where(Patient.patient_token == req.patient_token)
    res = await db.execute(stmt)
    patient = res.scalars().first()
    if not patient:
        raise HTTPException(status_code=404, detail="Patient token not found")

    patient.preferred_language = req.preferred_language

    # Upsert consent record
    c_stmt = select(ConsentRecord).where(ConsentRecord.patient_id == patient.id)
    c_res = await db.execute(c_stmt)
    consent = c_res.scalars().first()

    if not consent:
        consent = ConsentRecord(
            patient_id=patient.id,
            consent_given=True,
            is_guardian_mode=req.is_guardian_mode,
            guardian_name=req.guardian_name,
            guardian_relation=req.guardian_relation
        )
        db.add(consent)
    else:
        consent.consent_given = True
        consent.is_guardian_mode = req.is_guardian_mode
        consent.guardian_name = req.guardian_name
        consent.guardian_relation = req.guardian_relation
        consent.timestamp = datetime.now(timezone.utc)

    # Update active session
    sess_stmt = (
        select(IntakeSession)
        .where(
            IntakeSession.patient_id == patient.id,
            IntakeSession.status == "initiated"
        )
        .order_by(IntakeSession.started_at.desc())
    )
    s_res = await db.execute(sess_stmt)
    session = s_res.scalars().first()
    if session:
        session.status = "consent_accepted"

    await db.commit()
    return ConsentResponse(
        patient_id=patient.id,
        consent_given=True,
        status="consent_accepted",
        message="Consent successfully recorded under DPDP Act 2023 standards."
    )

@router.post("/language")
async def update_patient_language(
    patient_token: str = Query(...),
    language: str = Query("en"),
    db: AsyncSession = Depends(get_db)
):
    """Allows patient to switch language (en, hi, mr) dynamically at any time."""
    stmt = select(Patient).where(Patient.patient_token == patient_token)
    res = await db.execute(stmt)
    patient = res.scalars().first()
    if not patient:
        raise HTTPException(status_code=404, detail="Patient not found")
    patient.preferred_language = language
    await db.commit()
    return {"status": "success", "language": language}

@router.post("/vitals", response_model=VitalsResponse)
async def submit_vitals(req: VitalsRequest, db: AsyncSession = Depends(get_db)):
    """
    Vitals input: Height & Weight.
    Computes BMI strictly in code. All values labeled 'self-reported'.
    """
    stmt = select(Patient).where(Patient.patient_token == req.patient_token)
    res = await db.execute(stmt)
    patient = res.scalars().first()
    if not patient:
        raise HTTPException(status_code=404, detail="Patient not found")

    bmi_val, bmi_cat = compute_bmi(req.height_cm, req.weight_kg)

    if req.session_id:
        sess_stmt = select(IntakeSession).where(
            IntakeSession.id == req.session_id,
            IntakeSession.patient_id == patient.id
        )
        s_res = await db.execute(sess_stmt)
        session = s_res.scalars().first()
    else:
        sess_stmt = (
            select(IntakeSession)
            .where(IntakeSession.patient_id == patient.id)
            .order_by(IntakeSession.started_at.desc())
        )
        s_res = await db.execute(sess_stmt)
        session = s_res.scalars().first()

    if not session:
        session = IntakeSession(patient_id=patient.id)
        db.add(session)

    session.height_cm = req.height_cm
    session.weight_kg = req.weight_kg
    session.bmi = bmi_val
    session.bmi_category = bmi_cat
    session.vitals_label = "self-reported"
    session.ayush_system = req.ayush_system or "allopathy"
    session.status = "vitals_entered"

    await db.commit()
    return VitalsResponse(
        height_cm=req.height_cm,
        weight_kg=req.weight_kg,
        bmi=bmi_val,
        bmi_category=bmi_cat,
        vitals_label="self-reported"
    )

@router.get("/question", response_model=Optional[QuestionResponse])
async def get_next_question(
    patient_token: str = Query(...),
    session_id: str = Query(...),
    consecutive_failures: int = Query(0),
    db: AsyncSession = Depends(get_db)
):
    """
    Fetches the next question determined by the backend QuestionEngine state machine.
    """
    patient, session = await verify_patient_session(patient_token, session_id, db)

    # If session was halted due to red flag, do not serve more questions
    if session.status == "emergency_halt":
        raise HTTPException(status_code=400, detail="Session halted due to emergency red-flag.")

    # Get answered fields in this session
    f_stmt = select(ClinicalField.field_key, ClinicalField.value).where(ClinicalField.session_id == session.id)
    f_res = await db.execute(f_stmt)
    rows = f_res.all()
    answered_map = {r[0]: r[1] for r in rows}
    answered_keys = list(answered_map.keys())

    # Count symptom questions
    sym_stmt = select(ClinicalField).where(
        ClinicalField.session_id == session.id,
        ClinicalField.section == "symptoms"
    )
    sym_res = await db.execute(sym_stmt)
    symptom_count = len(sym_res.all())

    next_q = question_engine.get_next_question(
        current_section=session.current_section,
        answered_fields=answered_keys,
        symptom_questions_asked=symptom_count,
        consecutive_speech_failures=consecutive_failures,
        preferred_language=patient.preferred_language,
        answered_data=answered_map
    )

    if next_q:
        session.current_section = next_q.section_id
        session.status = "interview_active"
        session.questions_asked_count += 1
        await db.commit()

    return next_q

@router.post("/answer")
async def record_answer(req: RecordAnswerRequest, db: AsyncSession = Depends(get_db)):
    """
    Records an answer to a clinical field.
    Runs the red-flag scanner on the answer first. If triggered, halts immediately.
    """
    patient, session = await verify_patient_session(req.patient_token, req.session_id, db)

    # 1. Dual-Layer Red-Flag Check FIRST
    red_flag_res = red_flag_scanner.scan_text(req.value, patient.preferred_language)
    if red_flag_res.is_red_flag:
        session.status = "emergency_halt"
        session.has_red_flag = True
        session.red_flag_category = red_flag_res.category
        session.red_flag_details = red_flag_res.reason
        session.red_flag_triggered_at = datetime.now(timezone.utc)
        
        audit = AuditLog(
            session_id=session.id,
            actor_role="system",
            action="session_halted",
            details=f"Red-flag alert: {red_flag_res.category} ('{req.value}')"
        )
        db.add(audit)
        await db.commit()

        return {
            "status": "emergency_halt",
            "red_flag": red_flag_res.model_dump()
        }

    # 2. Extract structured clinical value from natural language
    extraction = await clinical_extractor.extract_field_detail(
        field_key=req.field_key,
        section_id=req.section_id,
        raw_text=req.value,
        language=patient.preferred_language
    )
    final_value = extraction.get("value", req.value)
    confidence = extraction.get("confidence", req.confidence)

    # 3. Record or update clinical field with full provenance
    cf_stmt = select(ClinicalField).where(
        ClinicalField.session_id == session.id,
        ClinicalField.field_key == req.field_key
    )
    cf_res = await db.execute(cf_stmt)
    clinical_field = cf_res.scalars().first()

    if not clinical_field:
        clinical_field = ClinicalField(
            session_id=session.id,
            section=req.section_id,
            field_key=req.field_key,
            value=final_value,
            source=req.source,
            confidence=confidence,
            transcript_quote=req.transcript_quote or req.value
        )
        db.add(clinical_field)
    else:
        clinical_field.value = final_value
        clinical_field.source = req.source
        clinical_field.confidence = confidence
        clinical_field.transcript_quote = req.transcript_quote or req.value

    await db.commit()
    return {
        "status": "success",
        "field_key": req.field_key,
        "extracted_value": final_value,
        "confidence": confidence
    }

@router.post("/skip-or-advance")
async def advance_section(
    patient_token: str = Query(...),
    session_id: str = Query(...),
    db: AsyncSession = Depends(get_db)
):
    """Allows patient to skip a section or move forward freely."""
    patient, session = await verify_patient_session(patient_token, session_id, db)
    next_sec = question_engine.advance_section(session.current_section)
    if next_sec:
        session.current_section = next_sec
    else:
        session.status = "completed"
    await db.commit()
    return {"current_section": session.current_section, "status": session.status}

@router.get("/review")
async def get_patient_review(
    patient_token: str = Query(...),
    session_id: str = Query(...),
    db: AsyncSession = Depends(get_db)
):
    """
    Patient review screen:
    Shows what was understood per section with large Yes/No icons and edit options.
    """
    patient, session = await verify_patient_session(patient_token, session_id, db)

    f_stmt = select(ClinicalField).where(ClinicalField.session_id == session.id)
    f_res = await db.execute(f_stmt)
    fields = f_res.scalars().all()

    sections_data = {}
    for f in fields:
        sections_data.setdefault(f.section, []).append({
            "id": f.id,
            "field_key": f.field_key,
            "value": f.value,
            "source": f.source,
            "confidence": f.confidence,
            "quote": f.transcript_quote
        })

    # Fetch attached reports
    r_stmt = select(UploadedReport).where(UploadedReport.session_id == session.id)
    r_res = await db.execute(r_stmt)
    reports = r_res.scalars().all()
    reports_data = [
        {
            "id": r.id,
            "file_name": r.file_name,
            "file_type": r.file_type
        }
        for r in reports
    ]

    return {
        "session_id": session.id,
        "patient_token": patient.patient_token,
        "language": patient.preferred_language,
        "sections": sections_data,
        "vitals": {
            "height_cm": session.height_cm,
            "weight_kg": session.weight_kg,
            "bmi": session.bmi,
            "bmi_category": session.bmi_category,
            "ayush_system": session.ayush_system
        },
        "reports": reports_data,
        "disclaimer": "Draft prepared from patient answers. Not a diagnosis."
    }

@router.post("/submit")
async def submit_intake(
    patient_token: str = Query(...),
    session_id: str = Query(...),
    db: AsyncSession = Depends(get_db)
):
    """
    Submits completed intake to doctor OPD queue.
    Triggers post-session reconciliation pass.
    """
    patient, session = await verify_patient_session(patient_token, session_id, db)
    session.status = "completed"
    session.completed_at = datetime.now(timezone.utc)
    if session.started_at:
        started = session.started_at.replace(tzinfo=timezone.utc) if session.started_at.tzinfo is None else session.started_at
        delta = session.completed_at - started
        session.total_duration_seconds = max(0, int(delta.total_seconds()))

    # Fetch all captured fields for reconciliation
    f_stmt = select(ClinicalField).where(ClinicalField.session_id == session.id)
    f_res = await db.execute(f_stmt)
    fields = f_res.scalars().all()

    fields_dict = [
        {"section": f.section, "field_key": f.field_key, "value": f.value, "source": f.source}
        for f in fields
    ]

    # Build full transcript from recorded clinical fields quote/values
    transcript_lines = []
    for f in fields:
        q_label = f.field_label or f.field_key.replace("_", " ").title()
        val = f.value or ""
        quote = f.transcript_quote or val
        transcript_lines.append(f"Section: {f.section} | Field: {q_label} | Patient Answer: {val} (Transcript quote: '{quote}')")
    full_transcript_str = "\n".join(transcript_lines)

    # Run non-live reconciliation pass
    reconciliation = await post_session_reconciler.reconcile_session(
        full_transcript=full_transcript_str,
        live_captured_fields=fields_dict,
        patient_language=patient.preferred_language
    )

    session.ai_summary = reconciliation.get("ai_summary")

    audit = AuditLog(
        session_id=session.id,
        actor_role="patient",
        action="intake_submitted",
        details="Intake completed and placed into doctor OPD priority queue"
    )
    db.add(audit)
    await db.commit()

    return {
        "status": "completed",
        "message": "Intake successfully submitted to doctor queue.",
        "session_id": session.id
    }
