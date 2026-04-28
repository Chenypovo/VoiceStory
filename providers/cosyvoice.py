# providers/cosyvoice.py
import os
import struct
import uuid
import shutil
import requests
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


def _upload_to_oss(file_path: str, api_key: str) -> str:
    """Upload a local audio file to DashScope OSS and return the oss:// URL."""
    import dashscope
    from dashscope.utils.oss_utils import OssUtils
    dashscope.api_key = api_key
    dashscope.base_http_api_url = 'https://dashscope-intl.aliyuncs.com/api/v1'
    file_url, _ = OssUtils.upload(
        model=config.TTS_MODEL,
        file_path=file_path,
        api_key=api_key,
    )
    return file_url


class CosyVoiceProvider(TTSProvider):
    def __init__(self, api_key: str = None):
        self._api_key = api_key or config.DASHSCOPE_API_KEY
        self._voices: dict = {}  # voice_id -> {"local_path": str, "oss_url": str|None}

    def clone_voice(self, audio_path: str, name: str) -> str:
        voice_id = f"{name}-{uuid.uuid4().hex[:8]}"
        dest = os.path.join(config.PROFILES_DIR, f"{voice_id}.wav")
        shutil.copy2(audio_path, dest)

        oss_url = None
        if not config.MOCK_MODE:
            try:
                oss_url = _upload_to_oss(dest, self._api_key)
            except Exception:
                pass  # Fall back to default voice if upload fails

        self._voices[voice_id] = {"local_path": dest, "oss_url": oss_url}
        return voice_id

    def synthesize(self, text: str, voice_id: str) -> str:
        if voice_id not in self._voices:
            raise ValueError(f"Voice '{voice_id}' not registered")

        if config.MOCK_MODE:
            return self._mock_synthesize(text)

        voice_info = self._voices[voice_id]

        input_data = {
            "text": text,
            "voice": config.TTS_VOICE_DEFAULT,
            "language_type": "Chinese",
        }
        # Use voice cloning if OSS URL is available
        if voice_info.get("oss_url"):
            input_data["ref_audio_url"] = voice_info["oss_url"]

        payload = {"model": config.TTS_MODEL, "input": input_data}
        headers = {
            "Authorization": f"Bearer {self._api_key}",
            "Content-Type": "application/json",
        }
        resp = requests.post(config.TTS_API_URL, json=payload, headers=headers, timeout=60)
        resp_json = resp.json()

        if resp.status_code != 200 or "error" in resp_json:
            code = resp_json.get("code", resp.status_code)
            message = resp_json.get("message", resp_json.get("error", {}).get("message", "unknown"))
            raise RuntimeError(f"TTS API error: {code} - {message}")

        audio_url = resp_json["output"]["audio"]["url"]
        audio_resp = requests.get(audio_url, timeout=60)

        output_filename = f"{uuid.uuid4().hex}.wav"
        output_path = os.path.join(OUTPUTS_DIR, output_filename)
        with open(output_path, "wb") as f:
            f.write(audio_resp.content)
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
            self._voices[voice_id] = {"local_path": audio_path, "oss_url": None}
