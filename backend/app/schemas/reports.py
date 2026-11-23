from typing import Optional, List, Dict, Any
from pydantic import BaseModel, Field

class ExtractedLabValue(BaseModel):
    test_name: str
    raw_value: str
    numeric_value: Optional[float] = None
    unit: Optional[str] = None
    reference_range_printed: Optional[str] = None
    confidence: float = 1.0

class CandidateMedicine(BaseModel):
    name: str
    strength: Optional[str] = None
    confidence: float = 0.9

class MismatchFlag(BaseModel):
    biomarker: str
    patient_value: str
    report_value: str
    message: str
    rule_source: str = "config/lab_thresholds.json"

class ReportExtractionResult(BaseModel):
    report_id: str
    file_name: str
    file_type: str
    thumbnail_url: Optional[str] = None
    lab_values: List[ExtractedLabValue] = []
    candidate_medicines: List[CandidateMedicine] = []
    mismatch_flags: List[MismatchFlag] = []
    disclaimer: str = "Values extracted from document. The AI does not interpret results or diagnose."
