import time
import json
import logging
import asyncio
from typing import Optional, Callable, Awaitable
from backend.app.voice.adapter_interface import VoiceAdapter
from backend.app.core.config import settings
from backend.app.services.red_flag_scanner import red_flag_scanner
from backend.app.schemas.safety import RedFlagScanResult

logger = logging.getLogger("live_adapter")

class LiveAdapter(VoiceAdapter):
    """
    Real-time speech-to-speech adapter connecting the browser to Gemini Live API.
    Maintains a continuous multi-turn live session using gemini-2.5-flash-native-audio-latest.
    """

    def __init__(self, record_answer_callback: Optional[Callable] = None):
        self.session_id: Optional[str] = None
        self.language: str = "en"
        self.on_audio_out: Optional[Callable[[bytes], Awaitable[None]]] = None
        self.on_transcript: Optional[Callable[[str, str], Awaitable[None]]] = None
        self.on_red_flag: Optional[Callable[[RedFlagScanResult], Awaitable[None]]] = None
        self.on_turn_latency: Optional[Callable[[float], Awaitable[None]]] = None
        
        self.record_answer_callback = record_answer_callback
        self.is_connected: bool = False
        self.turn_start_time: float = 0.0
        self.client = None
        self.live_session = None
        self._live_task = None

    async def connect(
        self,
        session_id: str,
        language: str,
        on_audio_out: Callable[[bytes], Awaitable[None]],
        on_transcript: Callable[[str, str], Awaitable[None]],
        on_red_flag: Callable[[RedFlagScanResult], Awaitable[None]],
        on_turn_latency: Callable[[float], Awaitable[None]]
    ) -> None:
        self.session_id = session_id
        self.language = language
        self.on_audio_out = on_audio_out
        self.on_transcript = on_transcript
        self.on_red_flag = on_red_flag
        self.on_turn_latency = on_turn_latency

        if not settings.is_gemini_configured:
            logger.info("No valid GEMINI_API_KEY set; LiveAdapter ready in simulated bridge mode.")
            self.is_connected = True
            return

        try:
            from google import genai
            self.client = genai.Client(api_key=settings.GEMINI_API_KEY, http_options={"api_version": "v1alpha"})
            self.is_connected = True
            self._live_task = asyncio.create_task(self._run_live_loop())
            logger.info(f"LiveAdapter connected for session {session_id} using {settings.GEMINI_LIVE_MODEL}")
        except Exception as e:
            logger.error(f"LiveAdapter connection failed: {e}")
            self.is_connected = False
            raise e

    async def _run_live_loop(self):
        """Continuous background loop keeping the Gemini Live session alive for the entire interview."""
        try:
            from google.genai import types
            prompt_file = settings.PROMPTS_DIR / "live_voice_persona.txt"
            system_instruction = prompt_file.read_text(encoding="utf-8") if prompt_file.exists() else (
                "You are an empathetic, calm Pre-OPD Intake AI Assistant for Ayush clinics. "
                "Ask one question at a time. Never diagnose or prescribe medicines. "
                "Speak in warm, short sentences."
            )
            config = types.LiveConnectConfig(
                response_modalities=["AUDIO"],
                input_audio_transcription={},
                output_audio_transcription={},
                thinking_config=types.ThinkingConfig(thinking_budget=0),
                speech_config=types.SpeechConfig(
                    voice_config=types.VoiceConfig(
                        prebuilt_voice_config=types.PrebuiltVoiceConfig(voice_name="Kore")
                    )
                ),
                system_instruction=system_instruction
            )
            logger.info(f"Connecting to Gemini Live WebSocket model={settings.GEMINI_LIVE_MODEL}...")
            async with self.client.aio.live.connect(model=settings.GEMINI_LIVE_MODEL, config=config) as session:
                self.live_session = session
                logger.info(f"Gemini Live session successfully established for {self.session_id}")

                # Persistent receive loop across turns using _receive()
                while self.is_connected:
                    try:
                        response = await session._receive()
                    except Exception as e:
                        logger.info(f"Gemini Live receive ended: {e}")
                        break

                    if not response:
                        break

                    server_content = response.server_content
                    if server_content is not None:
                        # 1. Spoken audio chunks (24kHz PCM)
                        if server_content.model_turn is not None:
                            for part in server_content.model_turn.parts:
                                if part.inline_data and part.inline_data.data:
                                    if self.on_audio_out:
                                        await self.on_audio_out(part.inline_data.data)

                        # 2. Assistant speech transcript
                        if server_content.output_transcription and server_content.output_transcription.text:
                            spoken_text = server_content.output_transcription.text
                            if self.on_transcript:
                                await self.on_transcript("assistant", spoken_text)

                        # 3. Patient input transcription (from live mic)
                        patient_spoken = None
                        if server_content.input_transcription and server_content.input_transcription.text:
                            patient_spoken = server_content.input_transcription.text
                        elif server_content.interim_input_transcription and server_content.interim_input_transcription.text:
                            patient_spoken = server_content.interim_input_transcription.text

                        if patient_spoken:
                            rf = red_flag_scanner.scan_text(patient_spoken, self.language)
                            if rf.is_red_flag and self.on_red_flag:
                                await self.on_red_flag(rf)
                            if self.on_transcript:
                                await self.on_transcript("patient", patient_spoken)

                        # 4. Turn complete
                        if server_content.turn_complete:
                            if self.turn_start_time > 0 and self.on_turn_latency:
                                elapsed = time.time() - self.turn_start_time
                                await self.on_turn_latency(elapsed)
                                self.turn_start_time = 0.0

        except asyncio.CancelledError:
            logger.info("Gemini Live loop cancelled.")
        except Exception as e:
            logger.error(f"Gemini Live session loop exception: {e}")
        finally:
            self.live_session = None

    async def ask_question(self, prompt: str, language: Optional[str] = None) -> bool:
        """Prompts Gemini Live to speak the official question in the target language."""
        if not self.is_connected or not self.live_session:
            return False
        self.turn_start_time = time.time()
        lang = language or self.language
        lang_instruction = "in English"
        if lang == "hi":
            lang_instruction = "in warm natural spoken Hindi"
        elif lang == "mr":
            lang_instruction = "in warm natural spoken Marathi"

        instruction = (
            f"Please speak directly to the patient {lang_instruction} "
            f"asking this clinical intake question in one warm, conversational sentence: \"{prompt}\""
        )
        try:
            from google.genai import types
            await self.live_session.send_client_content(
                turns=types.Content(
                    role="user",
                    parts=[types.Part(text=instruction)]
                ),
                turn_complete=True
            )
            return True
        except Exception as e:
            logger.warning(f"Error asking question via Gemini Live: {e}")
            return False

    async def send_audio_chunk(self, pcm_16k_bytes: bytes) -> None:
        if not self.is_connected or not self.live_session:
            return
        try:
            from google.genai import types
            # Upstream 16kHz PCM audio chunk to Gemini Live
            await self.live_session.send_realtime_input(
                media=types.Blob(data=pcm_16k_bytes, mime_type="audio/pcm;rate=16000")
            )
        except Exception as e:
            logger.warning(f"Error streaming upstream PCM: {e}")

    async def send_text_input(self, text: str) -> None:
        if not text:
            return
        self.turn_start_time = time.time()
        
        # 1. ALWAYS run Red-Flag Scanner on every transcript chunk
        red_flag_res = red_flag_scanner.scan_text(text, self.language)
        if red_flag_res.is_red_flag:
            logger.warning(f"LiveAdapter caught RED FLAG: {red_flag_res.category}")
            if self.on_red_flag:
                await self.on_red_flag(red_flag_res)
            await self.interrupt()
            return

        if self.on_transcript:
            await self.on_transcript("patient", text)

        if self.live_session:
            try:
                from google.genai import types
                await self.live_session.send_client_content(
                    turns=types.Content(
                        role="user",
                        parts=[types.Part(text=f"The patient answered: \"{text}\". Please acknowledge briefly and warmheartedly in one short phrase (under 5 words).")]
                    ),
                    turn_complete=True
                )
            except Exception as e:
                logger.warning(f"Error forwarding patient text to Gemini Live: {e}")

    async def interrupt(self) -> None:
        """Barge-in: clear outgoing queue and stop speech."""
        logger.info(f"Barge-in interrupt triggered for session {self.session_id}")

    async def close(self) -> None:
        self.is_connected = False
        if self._live_task and not self._live_task.done():
            self._live_task.cancel()
        if self.live_session and hasattr(self.live_session, '_ws'):
            try:
                await self.live_session._ws.close()
            except Exception:
                pass
        self.live_session = None
        logger.info(f"LiveAdapter closed for session {self.session_id}")
