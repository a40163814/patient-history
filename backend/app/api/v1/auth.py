from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from backend.app.models.base import get_db
from backend.app.models.patient import Patient, ConsentRecord
from backend.app.models.intake_session import IntakeSession
from backend.app.models.uploaded_report import AuditLog
from backend.app.schemas.intake import LoginRequest, LoginResponse

router = APIRouter(prefix="/auth", tags=["Authentication"])

@router.post("/login", response_model=LoginResponse)
async def login_with_otp(req: LoginRequest, db: AsyncSession = Depends(get_db)):
    """
    Mock OTP Login & QR Code Entry:
    Binds session to a single patient token so data can never cross between patients.
    Resumes incomplete sessions seamlessly.
    """
    # Find or create patient
    stmt = select(Patient).where(Patient.phone_number == req.phone_number).order_by(Patient.created_at.desc())
    result = await db.execute(stmt)
    patient = result.scalars().first()

    if not patient:
        patient = Patient(
            phone_number=req.phone_number,
            preferred_language=req.language
        )
        db.add(patient)
        await db.flush()
    else:
        # Update preferred language to current user selection
        patient.preferred_language = req.language

    # Find active incomplete session or create new
    sess_stmt = (
        select(IntakeSession)
        .where(
            IntakeSession.patient_id == patient.id,
            IntakeSession.status.in_(["initiated", "consent_accepted", "vitals_entered", "interview_active"])
        )
        .order_by(IntakeSession.started_at.desc())
    )
    sess_res = await db.execute(sess_stmt)
    session = sess_res.scalars().first()

    if not session:
        session = IntakeSession(
            patient_id=patient.id,
            status="initiated",
            current_section="red_flags"
        )
        db.add(session)
        await db.flush()

        # Log session initiation
        audit = AuditLog(
            session_id=session.id,
            actor_role="patient",
            actor_id=patient.patient_token,
            action="session_started",
            details="New intake session initiated via mobile OTP"
        )
        db.add(audit)

    await db.commit()
    await db.refresh(patient)
    await db.refresh(session)

    return LoginResponse(
        patient_id=patient.id,
        patient_token=patient.patient_token,
        phone_number=patient.phone_number,
        preferred_language=patient.preferred_language,
        session_id=session.id,
        status=session.status
    )
