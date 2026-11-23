import json
import logging
from typing import List, Dict, Any, Optional
from pathlib import Path
from backend.app.core.config import settings
from backend.app.schemas.reports import MismatchFlag, ExtractedLabValue

logger = logging.getLogger("mismatch_detector")

class MismatchDetector:
    def __init__(self, config_path: Optional[Path] = None):
        self.config_path = config_path or (settings.CONFIG_DIR / "lab_thresholds.json")
        self.config = self._load_config()
        self.biomarkers = self.config.get("biomarkers", {})
        self.template = self.config.get(
            "_metadata", {}
        ).get(
            "mismatch_message_template",
            "Check: patient answer differs from report ({field}: reported '{patient_value}', report indicates '{report_value}')"
        )

    def _load_config(self) -> Dict[str, Any]:
        try:
            with open(self.config_path, "r", encoding="utf-8") as f:
                return json.load(f)
        except Exception as e:
            logger.error(f"Failed to load lab_thresholds.json: {e}")
            return {"biomarkers": {}}

    def detect_mismatches(
        self,
        patient_conditions_reported: str,
        extracted_values: List[ExtractedLabValue]
    ) -> List[MismatchFlag]:
        """
        Rule-based detection comparing patient disclosures against extracted lab values.
        Strictly flags discrepancy without formulating diagnosis.
        """
        flags: List[MismatchFlag] = []
        conditions_lower = (patient_conditions_reported or "").lower()

        # Check if patient stated "none", "no", "nahi", "kahi nahi" or omitted conditions
        denies_or_omits = any(w in conditions_lower for w in ["no", "none", "nothing", "nahi", "nahin", "kahi nahi", "nil"]) or len(conditions_lower.strip()) == 0

        for val in extracted_values:
            test_name_lower = val.test_name.lower()
            num_val = val.numeric_value

            if num_val is None:
                continue

            # 1. Glucose / Blood Sugar check
            if "glucose" in test_name_lower or "sugar" in test_name_lower or "fbs" in test_name_lower:
                thresh_info = self.biomarkers.get("fasting_blood_glucose", {})
                thresh = thresh_info.get("diabetes_threshold", 126)
                if num_val >= thresh and ("diabetes" not in conditions_lower and "sugar" not in conditions_lower):
                    flags.append(MismatchFlag(
                        biomarker="Fasting Blood Sugar",
                        patient_value=patient_conditions_reported or "Denies chronic conditions",
                        report_value=f"{num_val} {val.unit or 'mg/dL'}",
                        message=self.template.format(
                            field="Blood Sugar",
                            patient_value=patient_conditions_reported or "No diabetes stated",
                            report_value=f"{num_val} {val.unit or 'mg/dL'}"
                        )
                    ))

            # 2. HbA1c check
            elif "hba1c" in test_name_lower or "glycated" in test_name_lower:
                thresh_info = self.biomarkers.get("hba1c", {})
                thresh = thresh_info.get("diabetes_threshold", 6.5)
                if num_val >= thresh and ("diabetes" not in conditions_lower and "sugar" not in conditions_lower):
                    flags.append(MismatchFlag(
                        biomarker="HbA1c",
                        patient_value=patient_conditions_reported or "Denies chronic conditions",
                        report_value=f"{num_val} {val.unit or '%'}",
                        message=self.template.format(
                            field="HbA1c",
                            patient_value=patient_conditions_reported or "No diabetes stated",
                            report_value=f"{num_val} {val.unit or '%'}"
                        )
                    ))

            # 3. Blood Pressure check
            elif "systolic" in test_name_lower or "bp" in test_name_lower or "blood pressure" in test_name_lower:
                thresh_info = self.biomarkers.get("systolic_bp", {})
                thresh = thresh_info.get("hypertension_stage2", 140)
                if num_val >= thresh and ("hypertension" not in conditions_lower and "bp" not in conditions_lower and "blood pressure" not in conditions_lower):
                    flags.append(MismatchFlag(
                        biomarker="Systolic BP",
                        patient_value=patient_conditions_reported or "Denies chronic conditions",
                        report_value=f"{num_val} {val.unit or 'mmHg'}",
                        message=self.template.format(
                            field="Blood Pressure",
                            patient_value=patient_conditions_reported or "No BP condition stated",
                            report_value=f"{num_val} {val.unit or 'mmHg'}"
                        )
                    ))

            # 4. Serum Creatinine check
            elif "creatinine" in test_name_lower:
                thresh_info = self.biomarkers.get("serum_creatinine", {})
                thresh = thresh_info.get("elevation_threshold", 1.4)
                if num_val >= thresh and ("kidney" not in conditions_lower and "renal" not in conditions_lower):
                    flags.append(MismatchFlag(
                        biomarker="Serum Creatinine",
                        patient_value=patient_conditions_reported or "Denies chronic conditions",
                        report_value=f"{num_val} {val.unit or 'mg/dL'}",
                        message=self.template.format(
                            field="Serum Creatinine",
                            patient_value=patient_conditions_reported or "No kidney condition stated",
                            report_value=f"{num_val} {val.unit or 'mg/dL'}"
                        )
                    ))

        return flags

mismatch_detector = MismatchDetector()
