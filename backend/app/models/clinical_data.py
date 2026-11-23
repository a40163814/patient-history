import uuid
from datetime import datetime, timezone
from sqlalchemy import Column, String, Float, DateTime, ForeignKey, Text
from sqlalchemy.orm import relationship
from backend.app.models.base import Base

def utc_now():
    return datetime.now(timezone.utc)

class ClinicalField(Base):
    __tablename__ = "clinical_fields"

    id = Column(String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    session_id = Column(String(36), ForeignKey("intake_sessions.id"), nullable=False, index=True)
    
    section = Column(String(50), nullable=False, index=True)
    field_key = Column(String(80), nullable=False, index=True)
    field_label = Column(String(120), nullable=True)
    
    # Stored content & Provenance
    value = Column(Text, nullable=False)
    # Allowed sources: 'patient_said', 'from_report', 'self_reported', 'unclear', 'skipped'
    source = Column(String(30), default="patient_said", nullable=False)
    confidence = Column(Float, default=1.0, nullable=False)
    transcript_quote = Column(Text, nullable=True)
    
    # Doctor inline modifications
    original_value = Column(Text, nullable=True)
    is_edited_by_doctor = Column(String(10), default="false", nullable=False)
    
    updated_at = Column(DateTime(timezone=True), default=utc_now, onupdate=utc_now)

    session = relationship("IntakeSession", back_populates="fields")
