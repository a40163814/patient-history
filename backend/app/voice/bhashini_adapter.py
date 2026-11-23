import time
import logging
from typing import Optional, Callable, Awaitable
from backend.app.voice.adapter_interface import VoiceAdapter
from backend.app.core.config import settings
from backend.app.services.red_flag_scanner import red_flag_scanner
from backend.app.schemas.safety import RedFlagScanResult

logger = logging.getLogger("bhashini_adapter")

class BhashiniAdapter(VoiceAdapter):
    """
    Cascaded pipeline adapter:
    Bhashini STT (Speech-to-Text) -> Backend Question Orchestrator -> Bhashini TTS (Text-to-Speech)
    Provides wide Indian language coverage (Hindi, Marathi, etc.).
    """

    def __init__(self, record_answer_callback: Optional[Callable] = None):
        self.session_id: Optional[str] = None
        self.language: str = "hi"
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
        logger.info(f"BhashiniAdapter initialized for language: {language}")

    async def send_audio_chunk(self, pcm_16k_bytes: bytes) -> None:
        """Buffers PCM audio for Bhashini ASR inference batching."""
        pass

    async def send_text_input(self, text: str) -> None:
        """Called when ASR completes or text fallback is submitted."""
        start_t = time.time()
        # Scan for red flags
        red_flag_res = red_flag_scanner.scan_text(text, self.language)
        if red_flag_res.is_red_flag:
            if self.on_red_flag:
                await self.on_red_flag(red_flag_res)
            return

        if self.on_transcript:
            await self.on_transcript("patient", text)

        elapsed = time.time() - start_t
        if self.on_turn_latency:
            await self.on_turn_latency(elapsed)

    async def interrupt(self) -> None:
        logger.info("BhashiniAdapter barge-in triggered.")

    async def close(self) -> None:
        self.is_connected = False
