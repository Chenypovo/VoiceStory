# providers/cosyvoice.py
import os
import struct
import uuid
import shutil
import config
from providers.tts_base import TTSProvider

OUTPUTS_DIR = config.OUTPUTS_DIR


def _generate_silence_wav(duration_seconds: float = 2.0, sample_rate: int = 16000) -> bytes:
    """Generate a minimal valid WAV file with silence."""
    num_samples = int(sample_rate * duration_seconds)
    data = b'\x00\x00' * num_samples  # 16-bit silence
    # WAV header
    header = struct.pack(
        '<4sI4s4sIHHIIHH4sI',
        b'RIFF',
        36 + len(data),
        b'WAVE',
        b'fmt ',
        16,          # chunk size
        1,           # PCM
        1,           # mono
        sample_rate,
        sample_rate * 2,  # byte rate
        2,           # block align
        16,          # bits per sample
        b'data',
        len(data),
    )
    return header + data


class CosyVoiceProvider(TTSProvider):
    def __init__(self, api_key: str = None):
        self._api_key = api_key or config.DASHSCOPE_API_KEY
        self._voices: dict = {}

    def clone_voice(self, audio_path: str, name: str) -> str:
        voice_id = f"{name}-{uuid.uuid4().hex[:8]}"
        dest = os.path.join(config.PROFILES_DIR, f"{voice_id}.wav")
        shutil.copy2(audio_path, dest)
        self._voices[voice_id] = dest
        return voice_id

    def synthesize(self, text: str, voice_id: str) -> str:
        ref_audio_path = self._voices.get(voice_id)
        if not ref_audio_path:
            raise ValueError(f"Voice '{voice_id}' not registered")

        if config.MOCK_MODE:
            return self._mock_synthesize(text)

        import dashscope
        from dashscope import SpeechSynthesizer
        dashscope.api_key = self._api_key

        kwargs = {
            "model": config.TTS_MODEL,
            "voice": config.TTS_VOICE_DEFAULT,
            "text": text,
            "format": "wav",
        }
        if ref_audio_path and os.path.exists(ref_audio_path):
            kwargs["ref_audio_path"] = ref_audio_path
            kwargs["ref_text"] = "这是一段参考音频。"

        response = SpeechSynthesizer.call(**kwargs)
        if response.status_code != 200:
            raise RuntimeError(
                f"CosyVoice API error: {response.code} - {response.message}"
            )

        output_filename = f"{uuid.uuid4().hex}.wav"
        output_path = os.path.join(OUTPUTS_DIR, output_filename)
        audio_data = response.get_audio()
        with open(output_path, "wb") as f:
            f.write(audio_data)
        return output_path

    def _mock_synthesize(self, text: str) -> str:
        """Generate a silence WAV for mock/demo mode."""
        output_filename = f"mock_{uuid.uuid4().hex}.wav"
        output_path = os.path.join(OUTPUTS_DIR, output_filename)
        wav_data = _generate_silence_wav()
        with open(output_path, "wb") as f:
            f.write(wav_data)
        return output_path

    def register_existing(self, voice_id: str, audio_path: str):
        if os.path.exists(audio_path):
            self._voices[voice_id] = audio_path
