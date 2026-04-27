# tests/test_tts_base.py
import pytest
from providers.tts_base import TTSProvider


def test_tts_provider_is_abstract():
    with pytest.raises(TypeError):
        TTSProvider()


def test_tts_provider_subclass_must_implement_methods():
    class IncompleteProvider(TTSProvider):
        pass

    with pytest.raises(TypeError):
        IncompleteProvider()


def test_tts_provider_subclass_with_all_methods():
    class CompleteProvider(TTSProvider):
        def clone_voice(self, audio_path, name):
            return "voice-123"

        def synthesize(self, text, voice_id):
            return "/tmp/output.wav"

    provider = CompleteProvider()
    assert provider.clone_voice("a.wav", "test") == "voice-123"
    assert provider.synthesize("hello", "voice-123") == "/tmp/output.wav"
