from typing import Optional, List, Dict, Any
from datetime import datetime
from pydantic import BaseModel, Field
from backend.app.schemas.reports import ReportExtractionResult

class ClinicalFieldSchema(BaseModel):
    id: str
    section: str
    field_key: str
    field_label: Optional[str] = None
    value: str
    source: str # patient_said | from_report | self_reported | unclear | skipped
    confidence: float
    transcript_quote: Optional[str] = None
    original_value: Optional[str] = None
    is_edited_by_doctor: bool = False

class CaseSheetResponse(BaseModel):
    session_id: str
    patient_id: str
    patient_token: str
    phone_number: str
    preferred_language: str
    ayush_system: str
    
    # Status
    status: str
    started_at: datetime
    completed_at: Optional[datetime] = None
    total_duration_seconds: int
    
    # Consent & Guardian
    is_guardian_mode: bool
    guardian_name: Optional[str] = None
    guardian_relation: Optional[str] = None
    
    # Vitals
    height_cm: Optional[float] = None
    weight_kg: Optional[float] = None
    bmi: Optional[float] = None
    bmi_category: Optional[str] = None
    vitals_label: str = "self-reported"
    
    # Safety Triage
    has_red_flag: bool
    red_flag_category: Optional[str] = None
    red_flag_details: Optional[str] = None
    
    # Clinical Fields by Section
    sections: Dict[str, List[ClinicalFieldSchema]] = {}
    
    # Reports
    reports: List[ReportExtractionResult] = []
    
    # Doctor review
    ai_summary: Optional[str] = None
    doctor_notes: Optional[str] = None
    is_doctor_approved: bool = False
    approved_at: Optional[datetime] = None
    pdf_file_path: Optional[str] = None
    
    disclaimer: str = "Draft prepared from patient answers. Not a diagnosis."

class DoctorEditFieldRequest(BaseModel):
    field_id: str
    doctor_id: str = "DOC-AYUSH-101"
    new_value: str
    reason: Optional[str] = "Clinician clarification during examination"

class DoctorApproveRequest(BaseModel):
    doctor_id: str = "DOC-AYUSH-101"
    doctor_notes: Optional[str] = None
    ai_summary: Optional[str] = None # Doctor can edit or clear the 5-line summary
