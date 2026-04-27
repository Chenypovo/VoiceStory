# providers/cosyvoice.py
import os
import uuid
import shutil
import dashscope
from dashscope import SpeechSynthesizer
from providers.tts_base import TTSProvider
import config

OUTPUTS_DIR = config.OUTPUTS_DIR


class CosyVoiceProvider(TTSProvider):
    def __init__(self, api_key: str = None):
        dashscope.api_key = api_key or config.DASHSCOPE_API_KEY
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

    def register_existing(self, voice_id: str, audio_path: str):
        if os.path.exists(audio_path):
            self._voices[voice_id] = audio_path
