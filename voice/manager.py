# voice/manager.py
import json
import os
import uuid
import shutil
from datetime import datetime
import config

PROFILES_DIR = config.PROFILES_DIR
META_FILE = os.path.join(PROFILES_DIR, "voices.json")


def _load_meta() -> dict:
    if os.path.exists(META_FILE):
        with open(META_FILE, "r", encoding="utf-8") as f:
            return json.load(f)
    return {}


def _save_meta(data: dict):
    os.makedirs(PROFILES_DIR, exist_ok=True)
    with open(META_FILE, "w", encoding="utf-8") as f:
        json.dump(data, f, ensure_ascii=False, indent=2)


class VoiceManager:
    def register(self, audio_path: str, name: str) -> str:
        voice_id = uuid.uuid4().hex[:12]
        dest = os.path.join(PROFILES_DIR, f"{voice_id}.wav")
        shutil.copy2(audio_path, dest)
        meta = _load_meta()
        meta[voice_id] = {
            "id": voice_id,
            "name": name,
            "created_at": datetime.now().isoformat(),
            "audio_path": dest,
        }
        _save_meta(meta)
        return voice_id

    def list_voices(self) -> list[dict]:
        return list(_load_meta().values())

    def get_voice(self, voice_id: str) -> dict:
        meta = _load_meta()
        if voice_id not in meta:
            raise KeyError(f"Voice '{voice_id}' not found")
        return meta[voice_id]
