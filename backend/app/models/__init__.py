from backend.app.models.base import Base, async_engine, sync_engine, get_db
from backend.app.models.patient import Patient, ConsentRecord
from backend.app.models.intake_session import IntakeSession
from backend.app.models.clinical_data import ClinicalField
from backend.app.models.uploaded_report import UploadedReport, AuditLog

def init_db():
    Base.metadata.create_all(bind=sync_engine)

async def init_db_async():
    async with async_engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)

__all__ = [
    "Base",
    "async_engine",
    "sync_engine",
    "get_db",
    "init_db",
    "init_db_async",
    "Patient",
    "ConsentRecord",
    "IntakeSession",
    "ClinicalField",
    "UploadedReport",
    "AuditLog"
]
