import re
import json
import logging
from typing import Dict, Any, Optional
from backend.app.core.config import settings

logger = logging.getLogger("extractor_service")

# Common multilingual filler patterns to strip for clean clinical extraction
FILLER_PATTERNS = [
    r"^(i have|i feel|i am having|i think|actually|doctor|sir|madam)\s+",
    r"^(mujhe|muze|mere ko|humko|mala|majhe|mi)\s+",
    r"\s+(hota hai|hote ahe|ho raha hai|lag raha hai|ahe|aahe)$",
    r"\s+(please check|kripya dekhiye|doctor saheb)$"
]

# Standard condition mapping
CONDITION_MAP = {
    "sugar": "Type 2 Diabetes Mellitus",
    "diabetes": "Type 2 Diabetes Mellitus",
    "madhumeh": "Type 2 Diabetes Mellitus",
    "मधुमेह": "Type 2 Diabetes Mellitus",
    "डायबिटीज": "Type 2 Diabetes Mellitus",
    "bp": "Hypertension (High BP)",
    "blood pressure": "Hypertension (High BP)",
    "high pressure": "Hypertension (High BP)",
    "रक्तचाप": "Hypertension (High BP)",
    "बीपी": "Hypertension (High BP)",
    "asthma": "Bronchial Asthma",
    "dama": "Bronchial Asthma",
    "दमा": "Bronchial Asthma",
    "thyroid": "Hypothyroidism / Thyroid Disorder",
    "थायराइड": "Hypothyroidism / Thyroid Disorder",
    "acidity": "Hyperacidity (Amlapitta)",
    "gas": "Gastritis / Flatulence",
    "bloating": "Abdominal Bloating",
    "arthritis": "Osteoarthritis / Joint Disorder",
    "sandhivata": "Sandhivata (Joint Disorder)",
    "संधिवात": "Sandhivata (Joint Disorder)",
    "gout": "Gout (Vatarakta)",
    "migraine": "Migraine (Ardhavabhedaka)"
}

class ClinicalDetailExtractor:
    """
    Extracts structured clinical values from patient voice/text answers.
    Combines LLM extraction (when Gemini API is provided) with robust local clinical NLP.
    Never diagnoses or recommends treatments.
    """

    async def extract_field_detail(
        self,
        field_key: str,
        section_id: str,
        raw_text: str,
        language: str = "en"
    ) -> Dict[str, Any]:
        cleaned = raw_text.strip()
        if not cleaned:
            return {"value": "None reported", "confidence": 1.0}

        # Check for simple negative / affirmative responses
        lower = cleaned.lower()
        if any(neg in lower for neg in ["no", "none", "nahi", "nako", "kahi nahi", "नहीं", "नाही", "काही नाही"]):
            if field_key == "chief_emergency_check":
                return {"value": "No emergency symptoms reported (Screening cleared)", "confidence": 0.99}
            if field_key in ["allergies_list", "known_chronic_conditions", "active_medications"]:
                return {"value": "None reported / Denies", "confidence": 0.98}

        # If Gemini API key is configured, use LLM extraction
        if settings.GEMINI_API_KEY:
            try:
                from google import genai
                client = genai.Client(api_key=settings.GEMINI_API_KEY)
                system_prompt = (
                    "You are a clinical intake entity extractor. Extract the clinical facts from the patient's statement "
                    "strictly as concise medical phrases without diagnosing, interpreting, or prescribing. "
                    "Return a JSON object with keys: 'structured_value' (concise string) and 'confidence' (float between 0.8 and 1.0)."
                )
                user_msg = f"Field: {field_key} ({section_id})\nLanguage: {language}\nPatient statement: {raw_text}"
                
                response = await client.aio.models.generate_content(
                    model=settings.GEMINI_TEXT_MODEL,
                    contents=[user_msg],
                    config=genai.types.GenerateContentConfig(
                        system_instruction=system_prompt,
                        temperature=0.0,
                        response_mime_type="application/json"
                    )
                )
                if response.text:
                    res_json = json.loads(response.text)
                    if isinstance(res_json, list) and len(res_json) > 0:
                        res_json = res_json[0]
                    if isinstance(res_json, dict):
                        val = res_json.get("structured_value")
                        conf = float(res_json.get("confidence", 0.95))
                        if val:
                            return {"value": val, "confidence": conf}
            except Exception as e:
                logger.warning(f"LLM entity extraction fallback: {e}")

        # Local high-precision heuristic extractor
        structured = cleaned
        for pat in FILLER_PATTERNS:
            structured = re.sub(pat, "", structured, flags=re.IGNORECASE).strip()

        # Map known chronic conditions if present
        if section_id == "pre_existing_conditions" or field_key == "known_chronic_conditions":
            matched = []
            for kw, standard_label in CONDITION_MAP.items():
                if kw in lower:
                    if standard_label not in matched:
                        matched.append(standard_label)
            if matched:
                structured = ", ".join(matched)
            elif any(neg in lower for neg in ["no", "none", "nahi", "nako", "kahi", "नहीं", "नाही"]):
                structured = "No known chronic conditions"

        # Duration standardization
        if field_key == "symptom_duration":
            num_match = re.search(r"(\d+)\s*(day|din|divas|week|hafta|mahina|month|year|saal|varsha)", lower)
            if num_match:
                structured = f"{num_match.group(1)} {num_match.group(2)}(s)"

        # Emergency check standardization
        if field_key == "chief_emergency_check":
            if any(pos in lower for pos in ["yes", "ha", "haan", "ho", "ahe", "होय", "हाँ"]):
                structured = "Urgent attention indicated by patient response"
            else:
                structured = "No emergency symptoms reported (Screening cleared)"

        return {
            "value": structured or cleaned,
            "confidence": 0.95
        }

clinical_extractor = ClinicalDetailExtractor()
