import uuid
from datetime import datetime, timezone
from sqlalchemy import Column, String, DateTime, ForeignKey, Text, JSON
from sqlalchemy.orm import relationship
from backend.app.models.base import Base

def utc_now():
    return datetime.now(timezone.utc)

class UploadedReport(Base):
    __tablename__ = "uploaded_reports"

    id = Column(String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    session_id = Column(String(36), ForeignKey("intake_sessions.id"), nullable=False, index=True)

    file_name = Column(String(255), nullable=False)
    file_path = Column(String(500), nullable=False)
    thumbnail_path = Column(String(500), nullable=True)
    file_type = Column(String(50), nullable=False) # image/png, image/jpeg, application/pdf
    
    # OCR / Vision extracted structured data (untrusted, strictly non-diagnostic)
    extracted_data = Column(JSON, nullable=True)
    # Mismatch flags identified against patient's spoken answers
    mismatch_flags = Column(JSON, nullable=True)

    created_at = Column(DateTime(timezone=True), default=utc_now)

    session = relationship("IntakeSession", back_populates="reports")

class AuditLog(Base):
    __tablename__ = "audit_logs"

    id = Column(String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    session_id = Column(String(36), ForeignKey("intake_sessions.id"), nullable=False, index=True)

    actor_role = Column(String(20), nullable=False) # patient, doctor, staff, system
    actor_id = Column(String(64), nullable=True)
    action = Column(String(50), nullable=False) # session_started, answer_recorded, field_edited, session_halted, doctor_approved, pdf_exported
    
    field_changed = Column(String(80), nullable=True)
    old_value = Column(Text, nullable=True)
    new_value = Column(Text, nullable=True)
    details = Column(Text, nullable=True)

    timestamp = Column(DateTime(timezone=True), default=utc_now)

    session = relationship("IntakeSession", back_populates="audit_logs")
