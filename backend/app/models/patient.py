import uuid
from datetime import datetime, timezone
from sqlalchemy import Column, String, Integer, Float, Boolean, DateTime, ForeignKey, Text
from sqlalchemy.orm import relationship
from backend.app.models.base import Base

def utc_now():
    return datetime.now(timezone.utc)

class Patient(Base):
    __tablename__ = "patients"

    id = Column(String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    patient_token = Column(String(64), unique=True, index=True, nullable=False, default=lambda: f"AYUSH-{uuid.uuid4().hex[:10].upper()}")
    phone_number = Column(String(20), index=True, nullable=False)
    full_name = Column(String(100), nullable=True)
    age = Column(Integer, nullable=True)
    gender = Column(String(20), nullable=True) # Male, Female, Other
    preferred_language = Column(String(10), default="en", nullable=False) # en, hi, mr
    created_at = Column(DateTime(timezone=True), default=utc_now)

    sessions = relationship("IntakeSession", back_populates="patient", cascade="all, delete-orphan")
    consent = relationship("ConsentRecord", back_populates="patient", uselist=False, cascade="all, delete-orphan")

class ConsentRecord(Base):
    __tablename__ = "consent_records"

    id = Column(String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    patient_id = Column(String(36), ForeignKey("patients.id"), unique=True, nullable=False)
    
    consent_given = Column(Boolean, default=False, nullable=False)
    is_guardian_mode = Column(Boolean, default=False, nullable=False)
    guardian_name = Column(String(100), nullable=True)
    guardian_relation = Column(String(50), nullable=True) # Parent, Child, Spouse, Caregiver
    
    # DPDP Act 2023 Disclosures Acknowledged
    audio_not_stored_acknowledged = Column(Boolean, default=True, nullable=False)
    ai_external_processing_acknowledged = Column(Boolean, default=True, nullable=False)
    purpose_limitation_acknowledged = Column(Boolean, default=True, nullable=False)
    
    timestamp = Column(DateTime(timezone=True), default=utc_now)

    patient = relationship("Patient", back_populates="consent")
