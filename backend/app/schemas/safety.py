from typing import Optional, List, Dict, Any
from pydantic import BaseModel, Field

class RedFlagScanResult(BaseModel):
    is_red_flag: bool
    trigger_source: str = "none" # rule_scanner | llm_classifier | both | none
    category: Optional[str] = None
    matched_term: Optional[str] = None
    confidence: float = 0.0
    reason: Optional[str] = None
    patient_message: str
    crisis_helpline: str = "14416"
    ambulance_service: str = "108"
    staff_priority: str = "NORMAL" # CRITICAL | NORMAL
