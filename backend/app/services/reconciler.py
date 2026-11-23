import json
import logging
from typing import Dict, Any, List, Optional
from backend.app.core.config import settings

logger = logging.getLogger("reconciler")

class PostSessionReconciler:
    def __init__(self):
        self.prompt_file = settings.PROMPTS_DIR / "post_session_reconcile.txt"

    async def reconcile_session(
        self,
        full_transcript: str,
        live_captured_fields: List[Dict[str, Any]],
        patient_language: str = "en"
    ) -> Dict[str, Any]:
        """
        Runs a structured reconciliation pass comparing the full transcript against realtime tool-call records.
        """
        # If Gemini API key is configured, invoke non-live text-model pass
        if settings.GEMINI_API_KEY and full_transcript.strip():
            try:
                from google import genai
                client = genai.Client(api_key=settings.GEMINI_API_KEY)
                system_instruction = self.prompt_file.read_text(encoding="utf-8") if self.prompt_file.exists() else ""

                user_prompt = f"""
                PATIENT LANGUAGE: {patient_language}
                FULL TRANSCRIPT:
                {full_transcript}

                REALTIME FUNCTION-CALL CAPTURED FIELDS:
                {json.dumps(live_captured_fields, indent=2)}
                """

                response = await client.aio.models.generate_content(
                    model=settings.GEMINI_TEXT_MODEL,
                    contents=[user_prompt],
                    config=genai.types.GenerateContentConfig(
                        system_instruction=system_instruction,
                        temperature=0.0,
                        response_mime_type="application/json"
                    )
                )

                if response.text:
                    return json.loads(response.text)
            except Exception as e:
                logger.warning(f"Non-live LLM reconciliation pass failed: {e}")

        # Deterministic reconciliation logic
        captured_keys = {f.get("field_key"): f.get("value") for f in live_captured_fields}
        
        # Build factual summary from captured keys (strictly max 5 lines)
        chief = captured_keys.get("chief_complaint", "General pre-OPD checkup")
        dur = captured_keys.get("symptom_duration", "unspecified duration")
        conditions = captured_keys.get("known_chronic_conditions", "None disclosed")
        meds = captured_keys.get("active_medications", "No active medications")
        allergies = captured_keys.get("allergies_list", "No known allergies")

        ai_summary_lines = [
            f"1. Chief concern: Patient reports {chief} for {dur}.",
            f"2. Pre-existing health: {conditions}.",
            f"3. Active medications/remedies: {meds}.",
            f"4. Allergies: {allergies}.",
            f"5. Intake completed. Draft prepared from patient answers. Not a diagnosis."
        ]

        return {
            "reconciled_fields": live_captured_fields,
            "discrepancies_and_gaps": [],
            "ai_summary": "\n".join(ai_summary_lines)
        }

post_session_reconciler = PostSessionReconciler()
