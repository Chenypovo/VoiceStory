# tests/test_cosyvoice.py
import pytest
import os
from unittest.mock import patch, MagicMock
from providers.cosyvoice import CosyVoiceProvider
import config


@pytest.fixture
def provider(monkeypatch):
    monkeypatch.setattr(config, "MOCK_MODE", False)
    return CosyVoiceProvider(api_key="test-key")


def test_clone_voice_returns_voice_id(provider, tmp_path):
    ref_audio = tmp_path / "ref.wav"
    ref_audio.write_bytes(b"fake audio bytes")
    voice_id = provider.clone_voice(str(ref_audio), "test-speaker")
    assert voice_id
    assert "test-speaker" in voice_id or len(voice_id) > 0


def test_synthesize_calls_api_and_returns_path(provider, tmp_path, monkeypatch):
    monkeypatch.setattr("providers.cosyvoice.OUTPUTS_DIR", str(tmp_path))
    provider._voices["voice-123"] = "/fake/path.wav"
    mock_response = MagicMock()
    mock_response.status_code = 200
    mock_response.get_audio.return_value = b"fake audio data"
    with patch("dashscope.SpeechSynthesizer") as MockSS:
        MockSS.call.return_value = mock_response
        output_path = provider.synthesize("你好世界", "voice-123")
    assert output_path.endswith(".wav")
    assert os.path.exists(output_path)


def test_synthesize_raises_on_api_error(provider, monkeypatch):
    monkeypatch.setattr(config, "MOCK_MODE", False)
    provider._voices["voice-123"] = "/fake/path.wav"
    mock_response = MagicMock()
    mock_response.status_code = 400
    mock_response.code = "InvalidParameter"
    mock_response.message = "bad request"
    with patch("dashscope.SpeechSynthesizer") as MockSS:
        MockSS.call.return_value = mock_response
        with pytest.raises(RuntimeError):
            provider.synthesize("test", "voice-123")
