# tests/test_voice_manager.py
import pytest
import os
import json
from voice.manager import VoiceManager

@pytest.fixture
def manager(tmp_path, monkeypatch):
    import voice.manager as vm
    profiles_dir = str(tmp_path / "profiles")
    os.makedirs(profiles_dir, exist_ok=True)
    monkeypatch.setattr(vm, "PROFILES_DIR", profiles_dir)
    monkeypatch.setattr(vm, "META_FILE", str(tmp_path / "voices.json"))
    return VoiceManager()

def test_register_creates_profile(manager, tmp_path):
    ref_audio = tmp_path / "ref.wav"
    ref_audio.write_bytes(b"fake")
    voice_id = manager.register(str(ref_audio), "Test Speaker")
    profile = manager.get_voice(voice_id)
    assert profile["name"] == "Test Speaker"
    assert os.path.exists(profile["audio_path"])

def test_list_voices(manager, tmp_path):
    ref1 = tmp_path / "a.wav"; ref1.write_bytes(b"a")
    ref2 = tmp_path / "b.wav"; ref2.write_bytes(b"b")
    manager.register(str(ref1), "Voice A")
    manager.register(str(ref2), "Voice B")
    voices = manager.list_voices()
    assert len(voices) == 2

def test_get_voice_raises_on_unknown(manager):
    with pytest.raises(KeyError):
        manager.get_voice("nonexistent")
