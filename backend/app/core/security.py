from fastapi import HTTPException, Security, status
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from backend.app.models.patient import Patient
from backend.app.models.intake_session import IntakeSession

security = HTTPBearer(auto_error=False)

async def verify_patient_session(
    patient_token: str,
    session_id: str,
    db: AsyncSession
) -> tuple[Patient, IntakeSession]:
    """
    Guarantees strict patient-session isolation:
    Data can never cross between patients or unauthorized tokens.
    """
    stmt = (
        select(Patient, IntakeSession)
        .join(IntakeSession, Patient.id == IntakeSession.patient_id)
        .where(
            Patient.patient_token == patient_token,
            IntakeSession.id == session_id
        )
    )
    result = await db.execute(stmt)
    row = result.first()
    
    if not row:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Access denied: Invalid patient token or session mismatch. Data isolation enforced."
        )
        
    patient, intake_session = row
    return patient, intake_session
