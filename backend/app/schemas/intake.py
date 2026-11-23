from typing import Optional, List, Dict, Any
from pydantic import BaseModel, Field

class LoginRequest(BaseModel):
    phone_number: str = Field(..., description="Patient mobile number for OTP login")
    language: str = Field("en", description="Preferred language: en, hi, mr")
    otp: Optional[str] = Field("123456", description="Demo OTP code")

class LoginResponse(BaseModel):
    patient_id: str
    patient_token: str
    phone_number: str
    preferred_language: str
    session_id: str
    status: str

class ConsentRequest(BaseModel):
    patient_token: str
    consent_given: bool = True
    is_guardian_mode: bool = False
    guardian_name: Optional[str] = None
    guardian_relation: Optional[str] = None
    preferred_language: str = "en"

class ConsentResponse(BaseModel):
    patient_id: str
    consent_given: bool
    status: str
    message: str

class VitalsRequest(BaseModel):
    patient_token: str
    session_id: Optional[str] = None
    height_cm: float = Field(..., gt=30, lt=260, description="Height in centimeters")
    weight_kg: float = Field(..., gt=1, lt=350, description="Weight in kilograms")
    ayush_system: Optional[str] = "allopathy"

class VitalsResponse(BaseModel):
    height_cm: float
    weight_kg: float
    bmi: float
    bmi_category: str
    vitals_label: str = "self-reported"
    disclaimer: str = "Draft prepared from patient answers. Not a diagnosis."

class QuestionResponse(BaseModel):
    section_id: str
    section_title: str
    question_id: str
    field_key: str
    prompt: str
    language: str
    question_type: str = "text"
    allowed_follow_ups: List[Dict[str, Any]] = []
    question_index: int
    total_section_questions: int
    is_last_in_section: bool = False
    is_interview_complete: bool = False
    speech_failures: int = 0
    show_tap_fallback: bool = False

class RecordAnswerRequest(BaseModel):
    patient_token: str
    session_id: str
    field_key: str
    section_id: str
    value: str
    source: str = "patient_said" # patient_said | from_report | self_reported | unclear | skipped
    confidence: float = 1.0
    transcript_quote: Optional[str] = None
