import pytest
import json
import os
from unittest.mock import patch, MagicMock
from story.generator import StoryGenerator

@pytest.fixture
def generator(tmp_path, monkeypatch):
    presets_dir = str(tmp_path / "presets")
    os.makedirs(presets_dir, exist_ok=True)
    monkeypatch.setattr("story.generator.PRESETS_DIR", presets_dir)
    g = StoryGenerator()
    g.presets_dir = presets_dir
    return g

def test_list_presets(generator, tmp_path):
    presets = tmp_path / "presets"
    (presets / "test.json").write_text(
        json.dumps({"id": "test", "title": "Test Story", "text": "Once upon a time...", "tags": []}),
        encoding="utf-8"
    )
    result = generator.list_presets()
    assert len(result) == 1
    assert result[0]["title"] == "Test Story"

def test_load_preset(generator, tmp_path):
    presets = tmp_path / "presets"
    (presets / "test.json").write_text(
        json.dumps({"id": "test", "title": "Test", "text": "Hello world", "tags": []}),
        encoding="utf-8"
    )
    text = generator.load_preset("test")
    assert text == "Hello world"

def test_load_preset_raises_on_missing(generator):
    with pytest.raises(FileNotFoundError):
        generator.load_preset("nonexistent")

def test_from_prompt_returns_story_text(generator):
    mock_client = MagicMock()
    mock_client.chat.completions.create.return_value = MagicMock(
        choices=[MagicMock(message=MagicMock(content="生成的故事文本"))]
    )
    with patch("story.generator.OpenAI", return_value=mock_client):
        result = generator.from_prompt("一只勇敢的小猫")
        assert result == "生成的故事文本"
