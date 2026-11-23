import os
import uuid
import shutil
import logging
from pathlib import Path
from typing import List, Optional
from fastapi import APIRouter, Depends, HTTPException, UploadFile, File, Form, status
from fastapi.responses import FileResponse
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from backend.app.models.base import get_db
from backend.app.models.uploaded_report import UploadedReport, AuditLog
from backend.app.models.clinical_data import ClinicalField
from backend.app.schemas.reports import ReportExtractionResult, ExtractedLabValue, CandidateMedicine, MismatchFlag
from backend.app.services.report_ocr_service import report_ocr_service
from backend.app.services.mismatch_detector import mismatch_detector
from backend.app.core.security import verify_patient_session
from backend.app.core.config import settings

logger = logging.getLogger("reports_api")

router = APIRouter(prefix="/reports", tags=["Reports & OCR"])

async def _process_uploaded_file(
    file: UploadFile,
    session,
    db: AsyncSession
) -> ReportExtractionResult:
    """Helper to save, OCR extract, check mismatches, and store a single report."""
    orig_name = file.filename or "uploaded_report.pdf"
    ext = Path(orig_name).suffix.lower() or (".pdf" if "pdf" in str(file.content_type).lower() else ".jpg")
    safe_filename = f"rep_{uuid.uuid4().hex[:12]}{ext}"
    dest_path = settings.UPLOAD_DIR / safe_filename

    with open(dest_path, "wb") as buffer:
        shutil.copyfileobj(file.file, buffer)

    content_type = file.content_type or ("application/pdf" if ext == ".pdf" else "image/jpeg")

    # Generate thumbnail for image files
    thumbnail_path = None
    if content_type.startswith("image/"):
        try:
            thumbnail_path = report_ocr_service.create_thumbnail(dest_path)
        except Exception as e:
            logger.warning(f"Thumbnail creation skipped: {e}")

    # OCR extraction with fail-safe fallback
    try:
        lab_vals, meds = await report_ocr_service.extract_from_report(dest_path, content_type, orig_name)
    except Exception as e:
        logger.warning(f"OCR extraction encountered error, continuing gracefully: {e}")
        lab_vals, meds = [], []

    # Fetch patient's disclosed conditions to test for mismatches
    cf_stmt = select(ClinicalField).where(
        ClinicalField.session_id == session.id,
        ClinicalField.field_key == "known_chronic_conditions"
    )
    cf_res = await db.execute(cf_stmt)
    cond_field = cf_res.scalars().first()
    reported_conditions = cond_field.value if cond_field else ""

    # Detect discrepancies
    mismatches = []
    try:
        mismatches = mismatch_detector.detect_mismatches(reported_conditions, lab_vals)
    except Exception as e:
        logger.warning(f"Mismatch detection error: {e}")

    # Store in database
    db_report = UploadedReport(
        session_id=session.id,
        file_name=orig_name,
        file_path=str(dest_path),
        thumbnail_path=thumbnail_path,
        file_type=content_type,
        extracted_data={
            "lab_values": [lv.model_dump() for lv in lab_vals],
            "candidate_medicines": [m.model_dump() for m in meds]
        },
        mismatch_flags=[m.model_dump() for m in mismatches]
    )
    db.add(db_report)
    await db.commit()
    await db.refresh(db_report)

    return ReportExtractionResult(
        report_id=db_report.id,
        file_name=db_report.file_name,
        file_type=db_report.file_type,
        thumbnail_url=f"/api/v1/reports/file/{Path(thumbnail_path).name}" if thumbnail_path else None,
        lab_values=lab_vals,
        candidate_medicines=meds,
        mismatch_flags=mismatches
    )

@router.post("/upload", response_model=ReportExtractionResult)
async def upload_diagnostic_report(
    patient_token: str = Form(...),
    session_id: str = Form(...),
    file: UploadFile = File(...),
    db: AsyncSession = Depends(get_db)
):
    """
    Diagnostic Report Upload & Vision OCR:
    Transcribes lab values strictly without interpretation.
    Compares against patient self-reports to generate 'Check: patient answer differs' alerts.
    """
    patient, session = await verify_patient_session(patient_token, session_id, db)
    return await _process_uploaded_file(file, session, db)

@router.post("/upload-batch", response_model=List[ReportExtractionResult])
async def upload_multiple_diagnostic_reports(
    patient_token: str = Form(...),
    session_id: str = Form(...),
    files: List[UploadFile] = File(...),
    db: AsyncSession = Depends(get_db)
):
    """Batch upload of multiple lab reports or prescription photos."""
    patient, session = await verify_patient_session(patient_token, session_id, db)
    results = []
    for f in files:
        res = await _process_uploaded_file(f, session, db)
        results.append(res)
    return results

@router.post("/confirm-medicine")
async def confirm_candidate_medicine(
    patient_token: str = Form(...),
    session_id: str = Form(...),
    medicine_name: str = Form(...),
    is_confirmed: bool = Form(...),
    corrected_name: Optional[str] = Form(None),
    db: AsyncSession = Depends(get_db)
):
    """Medicine photo step: confirm or correct candidate medicine."""
    patient, session = await verify_patient_session(patient_token, session_id, db)
    final_name = corrected_name if (not is_confirmed and corrected_name) else medicine_name
    
    # Save into clinical medicines
    cf = ClinicalField(
        session_id=session.id,
        section="current_medicines",
        field_key=f"photo_rx_{uuid.uuid4().hex[:6]}",
        value=f"Confirmed Medicine: {final_name}",
        source="from_report",
        confidence=0.95
    )
    db.add(cf)
    await db.commit()
    return {"status": "success", "confirmed_medicine": final_name}

@router.get("/file/{filename}")
async def get_uploaded_report_file(filename: str):
    """Serves uploaded reports and generated thumbnails securely."""
    safe_name = Path(filename).name
    file_path = settings.UPLOAD_DIR / safe_name
    if not file_path.exists():
        raise HTTPException(status_code=404, detail="Report file not found")
    
    media_type = "image/png" if safe_name.endswith(".png") else "application/pdf" if safe_name.endswith(".pdf") else "image/jpeg"
    return FileResponse(path=file_path, media_type=media_type)
