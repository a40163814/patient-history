from typing import List, Optional
from datetime import datetime, timezone
from pathlib import Path
from fastapi import APIRouter, Depends, HTTPException, status
from fastapi.responses import FileResponse
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, desc
from backend.app.models.base import get_db
from backend.app.models.patient import Patient, ConsentRecord
from backend.app.models.intake_session import IntakeSession
from backend.app.models.clinical_data import ClinicalField
from backend.app.models.uploaded_report import UploadedReport, AuditLog
from backend.app.schemas.case_sheet import (
    CaseSheetResponse, ClinicalFieldSchema,
    DoctorEditFieldRequest, DoctorApproveRequest
)
from backend.app.schemas.reports import ReportExtractionResult, ExtractedLabValue, CandidateMedicine, MismatchFlag
from backend.app.services.pdf_generator import clinical_pdf_generator

router = APIRouter(prefix="/doctor", tags=["Doctor OPD Dashboard"])

@router.get("/queue")
async def get_doctor_priority_queue(db: AsyncSession = Depends(get_db)):
    """
    Doctor Priority Queue:
    Sorted by triage urgency (Red-Flags top priority, followed by Lab Mismatches, then arrival time).
    """
    stmt = (
        select(IntakeSession, Patient)
        .join(Patient, IntakeSession.patient_id == Patient.id)
        .where(IntakeSession.status.in_(["completed", "emergency_halt", "doctor_approved", "interview_active"]))
        .order_by(
            desc(IntakeSession.has_red_flag),
            desc(IntakeSession.started_at)
        )
    )
    result = await db.execute(stmt)
    rows = result.all()

    queue = []
    for sess, pat in rows:
        # Count mismatch flags in this session
        rep_stmt = select(UploadedReport).where(UploadedReport.session_id == sess.id)
        rep_res = await db.execute(rep_stmt)
        reports = rep_res.scalars().all()
        mismatch_count = sum(len(r.mismatch_flags or []) for r in reports)

        queue.append({
            "session_id": sess.id,
            "patient_token": pat.patient_token,
            "phone_number": pat.phone_number,
            "language": pat.preferred_language,
            "ayush_system": sess.ayush_system,
            "status": sess.status,
            "has_red_flag": sess.has_red_flag,
            "red_flag_category": sess.red_flag_category,
            "mismatch_count": mismatch_count,
            "is_approved": sess.is_doctor_approved,
            "started_at": sess.started_at,
            "completed_at": sess.completed_at
        })

    return {"queue": queue, "total_count": len(queue)}

@router.get("/case/{session_id}", response_model=CaseSheetResponse)
async def get_patient_case_sheet(session_id: str, db: AsyncSession = Depends(get_db)):
    """
    Detailed Doctor Case Sheet Review:
    Delivers structured clinical fields with provenance chips, transcript quotes,
    reports side-by-side, and audit trails.
    """
    sess_stmt = (
        select(IntakeSession, Patient)
        .join(Patient, IntakeSession.patient_id == Patient.id)
        .where(IntakeSession.id == session_id)
    )
    res = await db.execute(sess_stmt)
    row = res.first()
    if not row:
        raise HTTPException(status_code=404, detail="Case sheet session not found")
    session, patient = row

    # Fetch consent
    c_stmt = select(ConsentRecord).where(ConsentRecord.patient_id == patient.id)
    c_res = await db.execute(c_stmt)
    consent = c_res.scalars().first()

    # Fetch fields
    f_stmt = select(ClinicalField).where(ClinicalField.session_id == session.id)
    f_res = await db.execute(f_stmt)
    fields = f_res.scalars().all()

    sections_dict = {}
    for f in fields:
        sections_dict.setdefault(f.section, []).append(ClinicalFieldSchema(
            id=f.id,
            section=f.section,
            field_key=f.field_key,
            field_label=f.field_label or f.field_key.replace("_", " ").title(),
            value=f.value,
            source=f.source,
            confidence=f.confidence,
            transcript_quote=f.transcript_quote,
            original_value=f.original_value,
            is_edited_by_doctor=(f.is_edited_by_doctor == "true")
        ))

    # Fetch reports
    r_stmt = select(UploadedReport).where(UploadedReport.session_id == session.id)
    r_res = await db.execute(r_stmt)
    db_reports = r_res.scalars().all()

    report_schemas = []
    for r in db_reports:
        extracted = r.extracted_data or {}
        lvs = [ExtractedLabValue(**item) for item in extracted.get("lab_values", [])]
        meds = [CandidateMedicine(**item) for item in extracted.get("candidate_medicines", [])]
        mismatches = [MismatchFlag(**item) for item in (r.mismatch_flags or [])]
        report_schemas.append(ReportExtractionResult(
            report_id=r.id,
            file_name=r.file_name,
            file_type=r.file_type,
            lab_values=lvs,
            candidate_medicines=meds,
            mismatch_flags=mismatches
        ))

    return CaseSheetResponse(
        session_id=session.id,
        patient_id=patient.id,
        patient_token=patient.patient_token,
        phone_number=patient.phone_number,
        preferred_language=patient.preferred_language,
        ayush_system=session.ayush_system,
        status=session.status,
        started_at=session.started_at,
        completed_at=session.completed_at,
        total_duration_seconds=session.total_duration_seconds,
        is_guardian_mode=consent.is_guardian_mode if consent else False,
        guardian_name=consent.guardian_name if consent else None,
        guardian_relation=consent.guardian_relation if consent else None,
        height_cm=session.height_cm,
        weight_kg=session.weight_kg,
        bmi=session.bmi,
        bmi_category=session.bmi_category,
        vitals_label=session.vitals_label,
        has_red_flag=session.has_red_flag,
        red_flag_category=session.red_flag_category,
        red_flag_details=session.red_flag_details,
        sections=sections_dict,
        reports=report_schemas,
        ai_summary=session.ai_summary,
        doctor_notes=session.doctor_notes,
        is_doctor_approved=session.is_doctor_approved,
        approved_at=session.approved_at,
        pdf_file_path=session.pdf_file_path
    )

@router.put("/case/{session_id}/field")
async def edit_clinical_field_inline(
    session_id: str,
    req: DoctorEditFieldRequest,
    db: AsyncSession = Depends(get_db)
):
    """
    Inline Clinical Edit with Immediate Audit Logging:
    Preserves original patient statement while documenting doctor's clinical modification.
    """
    f_stmt = select(ClinicalField).where(
        ClinicalField.id == req.field_id,
        ClinicalField.session_id == session_id
    )
    res = await db.execute(f_stmt)
    field = res.scalar_one_or_none()
    if not field:
        raise HTTPException(status_code=404, detail="Clinical field not found")

    old_val = field.value
    field.original_value = old_val if not field.original_value else field.original_value
    field.value = req.new_value
    field.is_edited_by_doctor = "true"

    # Audit log entry
    audit = AuditLog(
        session_id=session_id,
        actor_role="doctor",
        actor_id=req.doctor_id,
        action="field_edited",
        field_changed=field.field_key,
        old_value=old_val,
        new_value=req.new_value,
        details=f"Doctor edit reason: {req.reason}"
    )
    db.add(audit)
    await db.commit()

    return {"status": "success", "field_id": field.id, "new_value": field.value}

@router.post("/case/{session_id}/approve")
async def approve_and_generate_pdf(
    session_id: str,
    req: DoctorApproveRequest,
    db: AsyncSession = Depends(get_db)
):
    """
    Doctor Approval & PDF Generation:
    Locks case sheet, applies doctor digital approval stamp, generates ReportLab PDF.
    """
    sess_stmt = (
        select(IntakeSession, Patient)
        .join(Patient, IntakeSession.patient_id == Patient.id)
        .where(IntakeSession.id == session_id)
    )
    res = await db.execute(sess_stmt)
    row = res.first()
    if not row:
        raise HTTPException(status_code=404, detail="Session not found")
    session, patient = row

    session.is_doctor_approved = True
    session.doctor_id = req.doctor_id
    session.doctor_notes = req.doctor_notes or "Evaluated and verified during in-person clinical OPD examination."
    if req.ai_summary is not None:
        session.ai_summary = req.ai_summary
    session.approved_at = datetime.now(timezone.utc)
    session.status = "doctor_approved"

    # Fetch fields & reports for PDF
    f_stmt = select(ClinicalField).where(ClinicalField.session_id == session.id)
    f_res = await db.execute(f_stmt)
    fields = f_res.scalars().all()
    fields_list = [
        {
            "section": f.section,
            "field_key": f.field_key,
            "value": f.value,
            "source": f.source,
            "confidence": f.confidence,
            "transcript_quote": f.transcript_quote,
            "is_edited_by_doctor": (f.is_edited_by_doctor == "true"),
            "original_value": f.original_value
        }
        for f in fields
    ]

    r_stmt = select(UploadedReport).where(UploadedReport.session_id == session.id)
    r_res = await db.execute(r_stmt)
    reports = r_res.scalars().all()
    
    mismatches = []
    reports_list = []
    for r in reports:
        mismatches.extend(r.mismatch_flags or [])
        reports_list.append({
            "file_name": r.file_name,
            "file_type": r.file_type,
            "lab_values": (r.extracted_data or {}).get("lab_values", []),
            "candidate_medicines": (r.extracted_data or {}).get("candidate_medicines", [])
        })

    pdf_path = clinical_pdf_generator.generate_case_sheet(
        session_id=session.id,
        patient_data={
            "patient_token": patient.patient_token,
            "phone_number": patient.phone_number,
            "preferred_language": patient.preferred_language,
            "ayush_system": session.ayush_system
        },
        vitals={
            "height_cm": session.height_cm,
            "weight_kg": session.weight_kg,
            "bmi": session.bmi,
            "bmi_category": session.bmi_category,
            "vitals_label": session.vitals_label
        },
        clinical_fields=fields_list,
        mismatch_flags=mismatches,
        reports=reports_list,
        doctor_review={
            "doctor_id": session.doctor_id,
            "doctor_notes": session.doctor_notes,
            "ai_summary": session.ai_summary,
            "approved_at": session.approved_at.strftime("%d-%b-%Y %H:%M UTC")
        },
        has_red_flag=session.has_red_flag,
        red_flag_details=session.red_flag_details
    )

    session.pdf_file_path = pdf_path

    audit = AuditLog(
        session_id=session.id,
        actor_role="doctor",
        actor_id=req.doctor_id,
        action="doctor_approved",
        details=f"Doctor approved case sheet and generated official PDF: {Path(pdf_path).name}"
    )
    db.add(audit)
    await db.commit()

    return {
        "status": "approved",
        "session_id": session.id,
        "pdf_download_url": f"/api/v1/doctor/case/{session.id}/pdf",
        "approved_at": session.approved_at
    }

@router.get("/case/{session_id}/pdf")
async def download_case_sheet_pdf(session_id: str, db: AsyncSession = Depends(get_db)):
    """Serves the final approved immutable clinical PDF."""
    sess_stmt = select(IntakeSession).where(IntakeSession.id == session_id)
    res = await db.execute(sess_stmt)
    session = res.scalars().first()
    if not session or not session.pdf_file_path or not Path(session.pdf_file_path).exists():
        raise HTTPException(status_code=404, detail="PDF has not yet been generated for this session")

    return FileResponse(
        path=session.pdf_file_path,
        media_type="application/pdf",
        filename=Path(session.pdf_file_path).name
    )
