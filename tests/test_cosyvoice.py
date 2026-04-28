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
    with patch("providers.cosyvoice._upload_to_oss", return_value="oss://fake/url.wav"):
        with patch.object(provider, '_voices', {}):
            voice_id = provider.clone_voice(str(ref_audio), "test-speaker")
    assert voice_id
    assert "test-speaker" in voice_id


def test_synthesize_calls_api_and_returns_path(provider, tmp_path, monkeypatch):
    monkeypatch.setattr("providers.cosyvoice.OUTPUTS_DIR", str(tmp_path))
    provider._voices["voice-123"] = {"local_path": "/fake/path.wav", "oss_url": None}

    mock_audio_resp = MagicMock()
    mock_audio_resp.content = b"fake wav data"

    mock_api_resp = MagicMock()
    mock_api_resp.status_code = 200
    mock_api_resp.json.return_value = {
        "output": {"audio": {"url": "https://example.com/audio.wav"}},
    }

    with patch("providers.cosyvoice.requests") as mock_requests:
        mock_requests.post.return_value = mock_api_resp
        mock_requests.get.return_value = mock_audio_resp
        output_path = provider.synthesize("你好世界", "voice-123")

    assert output_path.endswith(".wav")
    assert os.path.exists(output_path)


def test_synthesize_with_voice_cloning(provider, tmp_path, monkeypatch):
    monkeypatch.setattr("providers.cosyvoice.OUTPUTS_DIR", str(tmp_path))
    provider._voices["voice-123"] = {
        "local_path": "/fake/path.wav",
        "oss_url": "oss://bucket/ref.wav",
    }

    mock_audio_resp = MagicMock()
    mock_audio_resp.content = b"fake wav data"

    mock_api_resp = MagicMock()
    mock_api_resp.status_code = 200
    mock_api_resp.json.return_value = {
        "output": {"audio": {"url": "https://example.com/audio.wav"}},
    }

    with patch("providers.cosyvoice.requests") as mock_requests:
        mock_requests.post.return_value = mock_api_resp
        mock_requests.get.return_value = mock_audio_resp
        output_path = provider.synthesize("你好世界", "voice-123")

    # Verify ref_audio_url was included in the API call
    call_args = mock_requests.post.call_args
    payload = call_args[1]["json"] if "json" in call_args[1] else call_args[0][0]
    assert payload["input"]["ref_audio_url"] == "oss://bucket/ref.wav"
    assert output_path.endswith(".wav")


def test_synthesize_raises_on_api_error(provider, monkeypatch):
    provider._voices["voice-123"] = {"local_path": "/fake/path.wav", "oss_url": None}

    mock_api_resp = MagicMock()
    mock_api_resp.status_code = 400
    mock_api_resp.json.return_value = {
        "code": "InvalidParameter",
        "message": "bad request",
    }

    with patch("providers.cosyvoice.requests") as mock_requests:
        mock_requests.post.return_value = mock_api_resp
        with pytest.raises(RuntimeError):
            provider.synthesize("test", "voice-123")
