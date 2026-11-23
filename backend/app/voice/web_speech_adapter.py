import time
import logging
from typing import Optional, Callable, Awaitable
from backend.app.voice.adapter_interface import VoiceAdapter
from backend.app.services.red_flag_scanner import red_flag_scanner
from backend.app.services.question_engine import question_engine
from backend.app.schemas.safety import RedFlagScanResult

logger = logging.getLogger("web_speech_adapter")

class WebSpeechAdapter(VoiceAdapter):
    """
    Browser Web Speech / Text-Tap fallback adapter.
    Enables zero-data-loss fallback whenever live WebSocket drops or speech fails twice.
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
        self.is_connected = True
        logger.info(f"WebSpeechAdapter active for session {session_id} in {language}")

    async def send_audio_chunk(self, pcm_16k_bytes: bytes) -> None:
        # Browser handles recognition natively; this is a no-op placeholder
        pass

    async def send_text_input(self, text: str) -> None:
        t0 = time.time()
        red_flag_res = red_flag_scanner.scan_text(text, self.language)
        if red_flag_res.is_red_flag:
            if self.on_red_flag:
                await self.on_red_flag(red_flag_res)
            return

        if self.on_transcript:
            await self.on_transcript("patient", text)

        elapsed = time.time() - t0
        if self.on_turn_latency:
            await self.on_turn_latency(elapsed)

    async def interrupt(self) -> None:
        logger.info("WebSpeechAdapter interrupt received.")

    async def close(self) -> None:
        self.is_connected = False
