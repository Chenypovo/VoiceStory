# providers/tts_base.py
from abc import ABC, abstractmethod


class TTSProvider(ABC):
    @abstractmethod
    def clone_voice(self, audio_path: str, name: str) -> str:
        """Register a voice from reference audio. Returns voice_id."""

    @abstractmethod
    def synthesize(self, text: str, voice_id: str) -> str:
        """Synthesize speech from text using a cloned voice. Returns output audio path."""
