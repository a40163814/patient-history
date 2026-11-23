import json
import re
import logging
from typing import Optional, Dict, Any
from pathlib import Path
from backend.app.core.config import settings
from backend.app.schemas.safety import RedFlagScanResult

logger = logging.getLogger("red_flag_scanner")

class RedFlagScanner:
    def __init__(self, config_path: Optional[Path] = None):
        self.config_path = config_path or (settings.CONFIG_DIR / "red_flags.json")
        self.rules = self._load_rules()
        self.crisis_helpline = self.rules.get("_metadata", {}).get("crisis_helpline", "14416")
        self.ambulance_service = self.rules.get("_metadata", {}).get("ambulance_service", "108")
        self.triage_messages = self.rules.get("triage_response", {}).get("patient_message", {})

    def _load_rules(self) -> Dict[str, Any]:
        try:
            with open(self.config_path, "r", encoding="utf-8") as f:
                return json.load(f)
        except Exception as e:
            logger.error(f"Failed to load red_flags.json: {e}")
            return {"categories": []}

    def _is_negated(self, text: str, match_start: int, match_end: int) -> bool:
        """Checks if a danger keyword is preceded or followed by a negation phrase."""
        prefix = text[max(0, match_start - 30):match_start].strip()
        suffix = text[match_end:min(len(text), match_end + 30)].strip()

        # English, Hindi, and Marathi negation patterns (both Latin and Devanagari scripts)
        negation_prefixes = [
            r'\b(no|not|never|neither|denies|denied|without|free of)\b',
            r'\b(nahi|nahin|na|bilkul nahi)\b',
            r'\b(nahi|nako|kahi nahi)\b',
            r'(नहीं|नही|ना|बिलकुल नहीं|कोई.*नहीं)',
            r'(नाही|नको|काही नाही)'
        ]
        negation_suffixes = [
            r'\b(nahi hai|nahi|nahin hai|nahin|matlab nahi)\b',
            r'\b(nahi ahe|nahi|navhate)\b',
            r'\b(is absent|was ruled out)\b',
            r'(नहीं है|नही है|नहीं|नही)',
            r'(नाही आहे|नाही|नाहीत)'
        ]

        for p in negation_prefixes:
            if re.search(p, prefix, re.IGNORECASE):
                return True
        for s in negation_suffixes:
            if re.search(s, suffix, re.IGNORECASE):
                return True
        return False

    def scan_text(self, text: str, language: str = "en") -> RedFlagScanResult:
        """
        Layer 1: Deterministic keyword and regex scanner.
        Scans multilingual inputs against all configured emergency categories.
        Favors high recall while respecting explicit clinical denials (e.g., 'no chest pain').
        """
        if not text or not text.strip():
            return RedFlagScanResult(
                is_red_flag=False,
                patient_message="",
                crisis_helpline=self.crisis_helpline
            )

        clean_text = text.lower().strip()
        matched_category = None
        matched_keyword = None

        for category in self.rules.get("categories", []):
            cat_id = category.get("id")
            keywords_dict = category.get("keywords", {})
            
            # Check all supported language keyword lists
            for lang_key, keywords in keywords_dict.items():
                for kw in keywords:
                    pattern = r'\b' + re.escape(kw.lower()) + r'\b'
                    match = re.search(pattern, clean_text)
                    if match:
                        # Check negation
                        if self._is_negated(clean_text, match.start(), match.end()):
                            continue
                        matched_category = cat_id
                        matched_keyword = kw
                        break
                    elif kw.lower() in clean_text:
                        start_pos = clean_text.find(kw.lower())
                        end_pos = start_pos + len(kw)
                        if self._is_negated(clean_text, start_pos, end_pos):
                            continue
                        matched_category = cat_id
                        matched_keyword = kw
                        break
                if matched_category:
                    break
            if matched_category:
                break

        if matched_category:
            patient_msg = self.triage_messages.get(
                language, 
                self.triage_messages.get("en", "Please sit down and rest. Staff are coming to attend to you right now.")
            )
            logger.warning(f"RED FLAG TRIGGERED: category='{matched_category}', keyword='{matched_keyword}', text='{text}'")
            return RedFlagScanResult(
                is_red_flag=True,
                trigger_source="rule_scanner",
                category=matched_category,
                matched_term=matched_keyword,
                confidence=1.0,
                reason=f"Matched danger term '{matched_keyword}' in {matched_category}",
                patient_message=patient_msg,
                crisis_helpline=self.crisis_helpline,
                ambulance_service=self.ambulance_service,
                staff_priority="CRITICAL"
            )

        return RedFlagScanResult(
            is_red_flag=False,
            patient_message="",
            crisis_helpline=self.crisis_helpline,
            ambulance_service=self.ambulance_service,
            staff_priority="NORMAL"
        )

    async def scan_with_llm_classifier(self, text: str, language: str = "en") -> RedFlagScanResult:
        """
        Layer 2: Fast LLM emergency classification if Gemini is configured.
        Falls back safely to Layer 1 rule scan if LLM is unavailable.
        """
        # Always run Layer 1 first
        rule_result = self.scan_text(text, language)
        if rule_result.is_red_flag:
            return rule_result

        # If rule did not trigger and Gemini key is provided, run prompt-based classification
        if settings.GEMINI_API_KEY:
            try:
                from google import genai
                client = genai.Client(api_key=settings.GEMINI_API_KEY)
                prompt_file = settings.PROMPTS_DIR / "safety_classifier.txt"
                system_instruction = prompt_file.read_text(encoding="utf-8") if prompt_file.exists() else ""
                
                response = await client.aio.models.generate_content(
                    model=settings.GEMINI_SAFETY_MODEL,
                    contents=[f"Patient Utterance: {text}"],
                    config=genai.types.GenerateContentConfig(
                        system_instruction=system_instruction,
                        temperature=0.0,
                        response_mime_type="application/json"
                    )
                )
                if response.text:
                    parsed = json.loads(response.text)
                    if parsed.get("is_red_flag"):
                        patient_msg = self.triage_messages.get(
                            language,
                            self.triage_messages.get("en", "Please sit down and rest. Staff are coming immediately.")
                        )
                        return RedFlagScanResult(
                            is_red_flag=True,
                            trigger_source="llm_classifier",
                            category=parsed.get("category", "unspecified_emergency"),
                            confidence=float(parsed.get("confidence", 0.9)),
                            reason=parsed.get("reason", "LLM danger classifier flagged utterance"),
                            patient_message=patient_msg,
                            crisis_helpline=self.crisis_helpline,
                            ambulance_service=self.ambulance_service,
                            staff_priority="CRITICAL"
                        )
            except Exception as e:
                logger.warning(f"LLM classifier call failed or skipped: {e}")

        return rule_result

red_flag_scanner = RedFlagScanner()
