import uuid
from datetime import datetime, timezone
from sqlalchemy import Column, String, Integer, Float, Boolean, DateTime, ForeignKey, Text
from sqlalchemy.orm import relationship
from backend.app.models.base import Base

def utc_now():
    return datetime.now(timezone.utc)

class IntakeSession(Base):
    __tablename__ = "intake_sessions"

    id = Column(String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    patient_id = Column(String(36), ForeignKey("patients.id"), nullable=False, index=True)
    
    # State Machine: 'initiated', 'consent_accepted', 'vitals_entered', 'interview_active', 'emergency_halt', 'completed', 'doctor_approved'
    status = Column(String(30), default="initiated", nullable=False, index=True)
    current_section = Column(String(50), default="symptoms", nullable=False)
    
    # Session Timers & Resumption
    started_at = Column(DateTime(timezone=True), default=utc_now)
    completed_at = Column(DateTime(timezone=True), nullable=True)
    total_duration_seconds = Column(Integer, default=0)
    questions_asked_count = Column(Integer, default=0)
    speech_failures_count = Column(Integer, default=0)
    
    # Vitals (Self-Reported)
    height_cm = Column(Float, nullable=True)
    weight_kg = Column(Float, nullable=True)
    bmi = Column(Float, nullable=True) # Computed strictly in code
    bmi_category = Column(String(30), nullable=True) # Underweight, Normal, Overweight, Obese
    vitals_label = Column(String(50), default="self-reported", nullable=False)
    
    # OPD Discipline (Allopathy by default)
    ayush_system = Column(String(30), default="allopathy", nullable=False)
    
    # Red Flag Triage Fields
    has_red_flag = Column(Boolean, default=False, nullable=False, index=True)
    red_flag_category = Column(String(50), nullable=True)
    red_flag_details = Column(Text, nullable=True)
    red_flag_triggered_at = Column(DateTime(timezone=True), nullable=True)
    
    # Doctor Review & Approval
    doctor_id = Column(String(50), nullable=True)
    doctor_notes = Column(Text, nullable=True)
    ai_summary = Column(Text, nullable=True) # Max 5 lines, labeled 'AI-generated summary'
    is_doctor_approved = Column(Boolean, default=False, nullable=False)
    approved_at = Column(DateTime(timezone=True), nullable=True)
    pdf_file_path = Column(String(255), nullable=True)

    # Relationships
    patient = relationship("Patient", back_populates="sessions")
    fields = relationship("ClinicalField", back_populates="session", cascade="all, delete-orphan")
    reports = relationship("UploadedReport", back_populates="session", cascade="all, delete-orphan")
    audit_logs = relationship("AuditLog", back_populates="session", cascade="all, delete-orphan")
