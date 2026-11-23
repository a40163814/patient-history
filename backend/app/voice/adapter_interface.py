from abc import ABC, abstractmethod
from typing import Optional, Dict, Any, Callable, Awaitable
from backend.app.schemas.safety import RedFlagScanResult

class VoiceAdapter(ABC):
    """
    Abstract interface for all pre-OPD voice intake implementations.
    Guarantees pluggability between Gemini Live API, Bhashini cascaded pipeline,
    and Browser WebSpeech/Text fallback.
    """

    @abstractmethod
    async def connect(
        self,
        session_id: str,
        language: str,
        on_audio_out: Callable[[bytes], Awaitable[None]],
        on_transcript: Callable[[str, str], Awaitable[None]], # (speaker, text)
        on_red_flag: Callable[[RedFlagScanResult], Awaitable[None]],
        on_turn_latency: Callable[[float], Awaitable[None]]
    ) -> None:
        pass

    @abstractmethod
    async def send_audio_chunk(self, pcm_16k_bytes: bytes) -> None:
        """Processes 16-bit 16kHz PCM upstream audio from browser AudioWorklet."""
        pass

    @abstractmethod
    async def send_text_input(self, text: str) -> None:
        """Processes text turn or transcript input."""
        pass

    @abstractmethod
    async def interrupt(self) -> None:
        """Barge-in: clears active playback queue and informs the underlying voice session."""
        pass

    async def ask_question(self, prompt: str, language: Optional[str] = None) -> None:
        """Optional speech synthesis / live turn for asking a clinical question."""
        pass

    @abstractmethod
    async def close(self) -> None:
        """Cleanly releases sockets and session resources."""
        pass
