import pytest
from fastapi import HTTPException
from sqlalchemy.ext.asyncio import create_async_engine, AsyncSession, async_sessionmaker
from backend.app.models.base import Base
from backend.app.models.patient import Patient, ConsentRecord
from backend.app.models.intake_session import IntakeSession
from backend.app.core.security import verify_patient_session

@pytest.mark.asyncio
async def test_patient_session_isolation():
    # In-memory test sqlite DB
    engine = create_async_engine("sqlite+aiosqlite:///:memory:", echo=False)
    async_session = async_sessionmaker(engine, expire_on_commit=False, class_=AsyncSession)

    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)

    async with async_session() as session:
        # Create Patient A and Session A
        pat_a = Patient(phone_number="9876543210", full_name="Patient A", patient_token="TOKEN-PAT-A")
        session.add(pat_a)
        await session.flush()

        sess_a = IntakeSession(patient_id=pat_a.id)
        session.add(sess_a)

        # Create Patient B and Session B
        pat_b = Patient(phone_number="9123456789", full_name="Patient B", patient_token="TOKEN-PAT-B")
        session.add(pat_b)
        await session.flush()

        sess_b = IntakeSession(patient_id=pat_b.id)
        session.add(sess_b)
        await session.commit()

        # Legitimate access for Patient A
        ret_pat_a, ret_sess_a = await verify_patient_session(
            patient_token="TOKEN-PAT-A",
            session_id=sess_a.id,
            db=session
        )
        assert ret_pat_a.id == pat_a.id
        assert ret_sess_a.id == sess_a.id

        # Illegitimate cross-patient access: Patient A token trying to access Session B
        with pytest.raises(HTTPException) as excinfo:
            await verify_patient_session(
                patient_token="TOKEN-PAT-A",
                session_id=sess_b.id,
                db=session
            )
        assert excinfo.value.status_code == 403
        assert "Data isolation enforced" in excinfo.value.detail
