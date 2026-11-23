import time
import json
import logging
from fastapi import APIRouter, WebSocket, WebSocketDisconnect, Depends
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from backend.app.models.base import AsyncSessionLocal
from backend.app.models.patient import Patient
from backend.app.models.intake_session import IntakeSession
from backend.app.models.clinical_data import ClinicalField
from backend.app.models.uploaded_report import AuditLog
from backend.app.voice.live_adapter import LiveAdapter
from backend.app.voice.web_speech_adapter import WebSpeechAdapter
from backend.app.services.red_flag_scanner import red_flag_scanner
from backend.app.core.config import settings

logger = logging.getLogger("voice_api")

router = APIRouter(tags=["Realtime Voice WebSocket"])

@router.websocket("/ws/voice/{session_id}")
async def voice_websocket_endpoint(websocket: WebSocket, session_id: str):
    await websocket.accept()
    logger.info(f"WebSocket client connected for session {session_id}")

    patient_token: str = ""
    language: str = "en"
    adapter = None

    try:
        # First message must be initialization with patient token
        init_data = await websocket.receive_text()
        init_payload = json.loads(init_data)
        patient_token = init_payload.get("patient_token", "")
        language = init_payload.get("language", "en")

        # Verify session in DB
        async with AsyncSessionLocal() as db:
            stmt = (
                select(Patient, IntakeSession)
                .join(IntakeSession, Patient.id == IntakeSession.patient_id)
                .where(
                    Patient.patient_token == patient_token,
                    IntakeSession.id == session_id
                )
            )
            res = await db.execute(stmt)
            row = res.first()
            if not row:
                await websocket.send_json({"type": "error", "message": "Invalid session or patient token"})
                await websocket.close(code=1008)
                return

        # Callbacks for the adapter
        async def on_audio_out(audio_bytes: bytes):
            await websocket.send_bytes(audio_bytes)

        async def on_transcript(speaker: str, text: str):
            await websocket.send_json({
                "type": "transcript",
                "speaker": speaker,
                "text": text
            })

        async def on_red_flag(rf):
            logger.warning(f"Pushing RED FLAG ALERT via WebSocket for session {session_id}")
            await websocket.send_json({
                "type": "red_flag_alert",
                "alert": rf.model_dump()
            })

        async def on_latency(elapsed: float):
            await websocket.send_json({
                "type": "latency",
                "turn_latency_ms": round(elapsed * 1000, 1)
            })

        # Initialize Adapter (LiveAdapter if Gemini key available, else WebSpeechAdapter)
        if settings.is_gemini_configured:
            adapter = LiveAdapter()
        else:
            adapter = WebSpeechAdapter()
            await websocket.send_json({
                "type": "notice",
                "message": "Gemini Live API requires a valid GEMINI_API_KEY in .env. Falling back to local Web Speech / Quick-Tap mode."
            })

        await adapter.connect(
            session_id=session_id,
            language=language,
            on_audio_out=on_audio_out,
            on_transcript=on_transcript,
            on_red_flag=on_red_flag,
            on_turn_latency=on_latency
        )

        await websocket.send_json({
            "type": "ready",
            "adapter": adapter.__class__.__name__,
            "language": language
        })

        # Main message loop
        while True:
            message = await websocket.receive()
            if "bytes" in message and message["bytes"]:
                # 16-bit 16kHz PCM audio chunk from AudioWorklet
                await adapter.send_audio_chunk(message["bytes"])
            elif "text" in message and message["text"]:
                payload = json.loads(message["text"])
                msg_type = payload.get("type")

                if msg_type == "text_input":
                    text = payload.get("text", "")
                    await adapter.send_text_input(text)

                elif msg_type == "ask_question":
                    prompt = payload.get("prompt", "")
                    lang = payload.get("language", language)
                    success = False
                    if hasattr(adapter, "ask_question"):
                        success = await adapter.ask_question(prompt, lang)
                    if not success:
                        await websocket.send_json({
                            "type": "live_fallback",
                            "prompt": prompt,
                            "language": lang
                        })

                elif msg_type == "barge_in":
                    # Instant user interrupt: stop active playback
                    await adapter.interrupt()
                    await websocket.send_json({"type": "interrupted"})

                elif msg_type == "ping":
                    await websocket.send_json({"type": "pong"})

    except WebSocketDisconnect:
        logger.info(f"WebSocket client disconnected for session {session_id}")
    except Exception as e:
        logger.error(f"WebSocket error in session {session_id}: {e}")
    finally:
        if adapter:
            await adapter.close()
