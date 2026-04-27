# Voice Story Phase 1 Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Build a working demo where users upload audio, clone a voice, and hear AI-generated or preset stories in that voice.

**Architecture:** Gradio web app calling DashScope CosyVoice API for voice cloning + TTS, and DashScope Qwen API for story generation. All behind a provider abstraction layer for future local model swap.

**Tech Stack:** Python 3.10+, Gradio, DashScope SDK (`dashscope`), OpenAI-compatible API via `openai` SDK.

**Pre-implementation note:** CosyVoice zero-shot cloning API parameters should be verified against latest [DashScope docs](https://help.aliyun.com/zh/model-studio/) before Task 3. Run a quick curl test with your `BAILIAN_API_KEY` to confirm the exact request format.

---

## File Structure

```
voice-story/
├── app.py                  # Gradio main entry
├── requirements.txt        # Dependencies
├── config.py               # API keys, model names, paths
├── providers/
│   ├── __init__.py
│   ├── tts_base.py         # TTSProvider ABC
│   └── cosyvoice.py        # CosyVoice implementation
├── story/
│   ├── __init__.py
│   ├── generator.py        # LLM story generation + preset loading
│   └── presets/            # Preset stories JSON
│       ├── little_red_riding_hood.json
│       ├── three_little_pigs.json
│       └── ugly_duckling.json
├── voice/
│   ├── __init__.py
│   └── manager.py          # Voice profile CRUD
├── tests/
│   ├── __init__.py
│   ├── test_cosyvoice.py
│   ├── test_generator.py
│   └── test_voice_manager.py
├── outputs/                # Generated audio (gitignored)
└── voice/profiles/         # Uploaded audio (gitignored)
```

---

### Task 1: Project Scaffold

**Files:**
- Create: `voice-story/requirements.txt`
- Create: `voice-story/config.py`
- Create: `voice-story/providers/__init__.py`
- Create: `voice-story/story/__init__.py`
- Create: `voice-story/voice/__init__.py`
- Create: `voice-story/tests/__init__.py`
- Create: `voice-story/.gitignore`

- [ ] **Step 1: Create project directory and virtual environment**

```bash
cd ~/voice-story
python3 -m venv venv
source venv/bin/activate
```

- [ ] **Step 2: Write requirements.txt**

```txt
gradio>=5.0
dashscope>=1.20
openai>=1.0
pytest>=8.0
```

- [ ] **Step 3: Install dependencies**

```bash
pip install -r requirements.txt
```

- [ ] **Step 4: Write config.py**

```python
import os

BASE_DIR = os.path.dirname(os.path.abspath(__file__))
PROFILES_DIR = os.path.join(BASE_DIR, "voice", "profiles")
OUTPUTS_DIR = os.path.join(BASE_DIR, "outputs")
PRESETS_DIR = os.path.join(BASE_DIR, "story", "presets")

DASHSCOPE_API_KEY = os.environ.get("BAILIAN_API_KEY", "")
LLM_MODEL = "qwen-plus"
TTS_MODEL = "cosyvoice-v1"
TTS_VOICE_DEFAULT = "longxiaochun"

os.makedirs(PROFILES_DIR, exist_ok=True)
os.makedirs(OUTPUTS_DIR, exist_ok=True)
```

- [ ] **Step 5: Create __init__.py files and directories**

Create empty `__init__.py` in `providers/`, `story/`, `voice/`, `tests/`.
Create empty `outputs/` and `voice/profiles/` directories.

- [ ] **Step 6: Write .gitignore**

```
venv/
__pycache__/
*.pyc
outputs/
voice/profiles/
*.wav
*.mp3
.env
```

- [ ] **Step 7: Initialize git repo and commit**

```bash
cd ~/voice-story
git init
git add .
git commit -m "chore: project scaffold with config and dependencies"
```

---

### Task 2: TTSProvider Abstract Base

**Files:**
- Create: `voice-story/providers/tts_base.py`
- Create: `voice-story/tests/test_tts_base.py`

- [ ] **Step 1: Write the test**

```python
# tests/test_tts_base.py
import pytest
from providers.tts_base import TTSProvider

def test_tts_provider_is_abstract():
    """TTSProvider cannot be instantiated directly."""
    with pytest.raises(TypeError):
        TTSProvider()

def test_tts_provider_subclass_must_implement_methods():
    """Subclass must implement clone_voice and synthesize."""
    class IncompleteProvider(TTSProvider):
        pass

    with pytest.raises(TypeError):
        IncompleteProvider()

def test_tts_provider_subclass_with_all_methods():
    """Subclass with all methods can be instantiated."""
    class CompleteProvider(TTSProvider):
        def clone_voice(self, audio_path, name):
            return "voice-123"
        def synthesize(self, text, voice_id):
            return "/tmp/output.wav"

    provider = CompleteProvider()
    assert provider.clone_voice("a.wav", "test") == "voice-123"
    assert provider.synthesize("hello", "voice-123") == "/tmp/output.wav"
```

- [ ] **Step 2: Run test to verify it fails**

```bash
cd ~/voice-story && python -m pytest tests/test_tts_base.py -v
```

Expected: FAIL (module not found)

- [ ] **Step 3: Write tts_base.py**

```python
# providers/tts_base.py
from abc import ABC, abstractmethod

class TTSProvider(ABC):
    @abstractmethod
    def clone_voice(self, audio_path: str, name: str) -> str:
        """Register a voice from reference audio. Returns voice_id."""

    @abstractmethod
    def synthesize(self, text: str, voice_id: str) -> str:
        """Synthesize speech from text using a cloned voice. Returns output audio path."""
```

- [ ] **Step 4: Run test to verify it passes**

```bash
cd ~/voice-story && python -m pytest tests/test_tts_base.py -v
```

Expected: 3 passed

- [ ] **Step 5: Commit**

```bash
git add providers/tts_base.py tests/test_tts_base.py
git commit -m "feat: add TTSProvider abstract base class"
```

---

### Task 3: CosyVoice Provider

**Files:**
- Create: `voice-story/providers/cosyvoice.py`
- Create: `voice-story/tests/test_cosyvoice.py`

**NOTE:** Before implementing, verify the exact CosyVoice zero-shot cloning API by running:

```bash
# Quick API probe - adjust parameters based on latest DashScope docs
# https://help.aliyun.com/zh/model-studio/developer-reference/cosyvoice-api
curl -X POST https://dashscope.aliyuncs.com/api/v1/services/aigc/text2audio/generation \
  -H "Authorization: Bearer $BAILIAN_API_KEY" \
  -H "Content-Type: application/json" \
  -d '{
    "model": "cosyvoice-v1",
    "input": {"text": "测试语音合成"},
    "parameters": {"voice": "longxiaochun", "format": "wav"}
  }'
```

The implementation below uses the `dashscope` SDK. Adjust parameter names if the SDK API has changed.

- [ ] **Step 1: Write the test**

```python
# tests/test_cosyvoice.py
import pytest
from unittest.mock import patch, MagicMock
from providers.cosyvoice import CosyVoiceProvider

@pytest.fixture
def provider():
    return CosyVoiceProvider(api_key="test-key")

def test_clone_voice_returns_voice_id(provider, tmp_path):
    """clone_voice stores reference audio and returns a voice_id."""
    ref_audio = tmp_path / "ref.wav"
    ref_audio.write_bytes(b"fake audio bytes")

    voice_id = provider.clone_voice(str(ref_audio), "test-speaker")

    assert voice_id  # non-empty string
    assert "test-speaker" in voice_id or len(voice_id) > 0

def test_synthesize_calls_api_and_returns_path(provider, tmp_path, monkeypatch):
    """synthesize calls DashScope API and saves audio to file."""
    monkeypatch.setattr("providers.cosyvoice.OUTPUTS_DIR", str(tmp_path))

    mock_response = MagicMock()
    mock_response.status_code = 200
    mock_response.get_audio.return_value = b"fake audio data"

    with patch("providers.cosyvoice.SpeechSynthesizer") as MockSS:
        MockSS.call.return_value = mock_response
        output_path = provider.synthesize("你好世界", "voice-123")

    assert output_path.endswith(".wav")
    import os
    assert os.path.exists(output_path)

def test_synthesize_raises_on_api_error(provider):
    """synthesize raises RuntimeError when API fails."""
    mock_response = MagicMock()
    mock_response.status_code = 400
    mock_response.code = "InvalidParameter"
    mock_response.message = "bad request"

    with patch("providers.cosyvoice.SpeechSynthesizer") as MockSS:
        MockSS.call.return_value = mock_response

    with pytest.raises(RuntimeError):
        provider.synthesize("test", "voice-123")
```

- [ ] **Step 2: Run test to verify it fails**

```bash
cd ~/voice-story && python -m pytest tests/test_cosyvoice.py -v
```

Expected: FAIL (module not found)

- [ ] **Step 3: Write cosyvoice.py**

```python
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
        self._voices: dict[str, str] = {}  # voice_id -> ref_audio_path

    def clone_voice(self, audio_path: str, name: str) -> str:
        """Store reference audio for zero-shot cloning. Returns voice_id."""
        voice_id = f"{name}-{uuid.uuid4().hex[:8]}"
        dest = os.path.join(config.PROFILES_DIR, f"{voice_id}.wav")
        shutil.copy2(audio_path, dest)
        self._voices[voice_id] = dest
        return voice_id

    def synthesize(self, text: str, voice_id: str) -> str:
        """Synthesize speech using cloned voice via CosyVoice API."""
        ref_audio_path = self._voices.get(voice_id)
        if not ref_audio_path:
            raise ValueError(f"Voice '{voice_id}' not registered")

        kwargs = {
            "model": config.TTS_MODEL,
            "voice": config.TTS_VOICE_DEFAULT,
            "text": text,
            "format": "wav",
        }

        # Zero-shot cloning: pass reference audio
        # NOTE: verify parameter names against latest DashScope docs
        # Possible names: ref_audio_path, prompt_audio_url, ref_audio
        if ref_audio_path and os.path.exists(ref_audio_path):
            kwargs["ref_audio_path"] = ref_audio_path
            kwargs["ref_text"] = "这是一段参考音频。"  # minimal ref text

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
        """Re-register a previously saved voice."""
        if os.path.exists(audio_path):
            self._voices[voice_id] = audio_path
```

- [ ] **Step 4: Run test to verify it passes**

```bash
cd ~/voice-story && python -m pytest tests/test_cosyvoice.py -v
```

Expected: 3 passed

- [ ] **Step 5: Commit**

```bash
git add providers/cosyvoice.py tests/test_cosyvoice.py
git commit -m "feat: add CosyVoice TTS provider with zero-shot cloning"
```

---

### Task 4: VoiceManager

**Files:**
- Create: `voice-story/voice/manager.py`
- Create: `voice-story/tests/test_voice_manager.py`

- [ ] **Step 1: Write the test**

```python
# tests/test_voice_manager.py
import pytest
import json
from voice.manager import VoiceManager

@pytest.fixture
def manager(tmp_path, monkeypatch):
    monkeypatch.setattr("voice.manager.PROFILES_DIR", str(tmp_path / "profiles"))
    monkeypatch.setattr("voice.manager.META_FILE", str(tmp_path / "voices.json"))
    import voice.manager as vm
    vm.PROFILES_DIR = str(tmp_path / "profiles")
    vm.META_FILE = str(tmp_path / "voices.json")
    os.makedirs(vm.PROFILES_DIR, exist_ok=True)
    return VoiceManager()

import os

def test_register_creates_profile(manager, tmp_path):
    ref_audio = tmp_path / "ref.wav"
    ref_audio.write_bytes(b"fake")

    voice_id = manager.register(str(ref_audio), "Test Speaker")

    profile = manager.get_voice(voice_id)
    assert profile["name"] == "Test Speaker"
    assert os.path.exists(profile["audio_path"])

def test_list_voices(manager, tmp_path):
    ref1 = tmp_path / "a.wav"
    ref2 = tmp_path / "b.wav"
    ref1.write_bytes(b"a")
    ref2.write_bytes(b"b")

    manager.register(str(ref1), "Voice A")
    manager.register(str(ref2), "Voice B")

    voices = manager.list_voices()
    assert len(voices) == 2

def test_get_voice_raises_on_unknown(manager):
    with pytest.raises(KeyError):
        manager.get_voice("nonexistent")
```

- [ ] **Step 2: Run test to verify it fails**

```bash
cd ~/voice-story && python -m pytest tests/test_voice_manager.py -v
```

Expected: FAIL

- [ ] **Step 3: Write manager.py**

```python
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
        """Register a new voice profile. Returns voice_id."""
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
```

- [ ] **Step 4: Run test to verify it passes**

```bash
cd ~/voice-story && python -m pytest tests/test_voice_manager.py -v
```

Expected: 3 passed

- [ ] **Step 5: Commit**

```bash
git add voice/manager.py tests/test_voice_manager.py
git commit -m "feat: add VoiceManager for voice profile CRUD"
```

---

### Task 5: Preset Stories

**Files:**
- Create: `voice-story/story/presets/little_red_riding_hood.json`
- Create: `voice-story/story/presets/three_little_pigs.json`
- Create: `voice-story/story/presets/ugly_duckling.json`

- [ ] **Step 1: Write little_red_riding_hood.json**

```json
{
  "id": "little_red_riding_hood",
  "title": "小红帽",
  "tags": ["经典", "童话"],
  "text": "从前，有一个可爱的小女孩，她总是戴着奶奶送的红色帽子，所以大家都叫她小红帽。一天，妈妈让小红帽去森林里给生病的奶奶送蛋糕和果汁。妈妈叮嘱她：不要离开大路，也不要和陌生人说话。小红帽答应了，提着篮子出发了。森林里阳光透过树叶洒下金色的光斑，小鸟在枝头唱歌。走着走着，小红帽遇到了一只大灰狼。大灰狼假装和善地问：小姑娘，你要去哪里呀？小红帽忘了妈妈的叮嘱，告诉了狼奶奶家的地址。狼抄近路先跑到了奶奶家，把奶奶关进了衣柜，然后穿上奶奶的衣服，戴上奶奶的帽子，躺在床上装病。小红帽到了奶奶家，觉得奶奶今天看起来有些奇怪。奶奶，你的眼睛怎么这么大？为了看清你呀。奶奶，你的耳朵怎么这么大？为了听清你呀。奶奶，你的嘴巴怎么这么大？为了吃掉你呀！狼扑向小红帽。就在这时，一位路过的猎人听到了呼救声，冲进来赶走了大灰狼。小红帽和奶奶都得救了。从此小红帽记住了：不要和陌生人说话，一定要听妈妈的话。晚安，做个好梦。"
}
```

- [ ] **Step 2: Write three_little_pigs.json**

```json
{
  "id": "three_little_pigs",
  "title": "三只小猪",
  "tags": ["经典", "童话"],
  "text": "从前有三只小猪，他们长大了，要离开妈妈自己盖房子住。猪大哥很懒，他用稻草搭了一间草屋，很快就盖好了，然后躺在里面睡大觉。猪二哥也不太勤快，他用木头搭了一间木屋，也很快盖好了，然后去玩耍了。猪小弟最勤劳，他搬来一块块砖头，和上水泥，认认真真地砌了一间结实的砖房。一天，大灰狼来了。他来到草屋前，深吸一口气，呼的一声，草屋被吹飞了。猪大哥拼命跑到猪二哥的木屋里。大灰狼来到木屋前，用力一撞，木屋也倒了。两只小猪拼命跑到猪小弟的砖房里。大灰狼对着砖房呼呼地吹，可砖房纹丝不动。他用力撞，撞得自己头晕眼花，砖房还是好好的。大灰狼爬上屋顶想从烟囱溜进去，猪小弟早就在壁炉里烧了一大锅热水。大灰狼从烟囱掉进热水里，烫得嗷嗷叫，狼狈地逃走了。从此三只小猪一起住在砖房里，再也不怕大灰狼了。这个故事告诉我们，勤劳和认真是最重要的。晚安，宝贝。"
}
```

- [ ] **Step 3: Write ugly_duckling.json**

```json
{
  "id": "ugly_duckling",
  "title": "丑小鸭",
  "tags": ["经典", "童话"],
  "text": "在一个温暖的夏天，鸭妈妈正在孵蛋。一只又一只毛茸茸的小鸭子破壳而出。可是最后一只蛋特别大，孵出来的小鸭子灰灰的、大大的，和其他小鸭子完全不一样。其他小鸭子都嘲笑他：你真丑！你不属于我们！丑小鸭很难过，他离开了鸭群，独自流浪。秋天来了，他看到一群美丽的天鹅飞过天空，心想：要是能像它们一样优雅就好了。冬天很冷，丑小鸭躲在芦苇丛里挨冻。终于，春天来了。丑小鸭来到湖边，低下头想喝水，却看到水里倒映着一只美丽的白天鹅。他不敢相信那是自己。这时其他天鹅游过来围着他，亲热地用嘴梳理他的羽毛。原来丑小鸭根本不是鸭子，他一直都是一只天鹅。他展开洁白的翅膀，飞向蓝天，再也没有人嘲笑他了。这个故事告诉我们，每个人都有自己独特的美。晚安，愿你像天鹅一样自信闪耀。"
}
```

- [ ] **Step 4: Commit**

```bash
git add story/presets/
git commit -m "feat: add 3 preset bedtime stories"
```

---

### Task 6: StoryGenerator

**Files:**
- Create: `voice-story/story/generator.py`
- Create: `voice-story/tests/test_generator.py`

- [ ] **Step 1: Write the test**

```python
# tests/test_generator.py
import pytest
import json
import os
from story.generator import StoryGenerator

@pytest.fixture
def generator(tmp_path, monkeypatch):
    monkeypatch.setattr("story.generator.PRESETS_DIR", str(tmp_path / "presets"))
    g = StoryGenerator()
    g.presets_dir = str(tmp_path / "presets")
    return g

def test_list_presets(generator, tmp_path):
    presets = tmp_path / "presets"
    presets.mkdir()
    (presets / "test.json").write_text(
        json.dumps({"id": "test", "title": "Test Story", "text": "Once upon a time...", "tags": []}),
        encoding="utf-8"
    )

    result = generator.list_presets()
    assert len(result) == 1
    assert result[0]["title"] == "Test Story"

def test_load_preset(generator, tmp_path):
    presets = tmp_path / "presets"
    presets.mkdir()
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

from unittest.mock import patch, MagicMock
```

- [ ] **Step 2: Run test to verify it fails**

```bash
cd ~/voice-story && python -m pytest tests/test_generator.py -v
```

Expected: FAIL

- [ ] **Step 3: Write generator.py**

```python
# story/generator.py
import json
import os
import glob

from openai import OpenAI

import config

PRESETS_DIR = config.PRESETS_DIR

STORY_SYSTEM_PROMPT = """你是一个儿童故事作家。根据用户的描述，写一个适合睡前听的温馨故事。

要求：
- 语言温柔、简单，适合 3-8 岁儿童
- 故事长度 300-500 字
- 结尾要有"晚安，做个好梦"或类似的温暖结束语
- 不要出现恐怖或暴力的内容"""


class StoryGenerator:
    def __init__(self):
        self.presets_dir = PRESETS_DIR
        self._client = None

    @property
    def client(self):
        if self._client is None:
            self._client = OpenAI(
                api_key=config.DASHSCOPE_API_KEY,
                base_url="https://dashscope.aliyuncs.com/compatible-mode/v1",
            )
        return self._client

    def list_presets(self) -> list[dict]:
        """List available preset stories."""
        stories = []
        for path in glob.glob(os.path.join(self.presets_dir, "*.json")):
            with open(path, "r", encoding="utf-8") as f:
                data = json.load(f)
                stories.append({
                    "id": data["id"],
                    "title": data["title"],
                    "tags": data.get("tags", []),
                })
        return stories

    def load_preset(self, story_id: str) -> str:
        """Load a preset story text by ID."""
        path = os.path.join(self.presets_dir, f"{story_id}.json")
        if not os.path.exists(path):
            raise FileNotFoundError(f"Preset story '{story_id}' not found")
        with open(path, "r", encoding="utf-8") as f:
            return json.load(f)["text"]

    def from_prompt(self, prompt: str) -> str:
        """Generate a new story from user prompt using LLM."""
        response = self.client.chat.completions.create(
            model=config.LLM_MODEL,
            messages=[
                {"role": "system", "content": STORY_SYSTEM_PROMPT},
                {"role": "user", "content": f"请写一个关于{prompt}的睡前故事"},
            ],
            max_tokens=1000,
            temperature=0.8,
        )
        return response.choices[0].message.content
```

- [ ] **Step 4: Run test to verify it passes**

```bash
cd ~/voice-story && python -m pytest tests/test_generator.py -v
```

Expected: 4 passed

- [ ] **Step 5: Commit**

```bash
git add story/generator.py tests/test_generator.py
git commit -m "feat: add StoryGenerator with preset loading and LLM generation"
```

---

### Task 7: Gradio UI

**Files:**
- Create: `voice-story/app.py`

- [ ] **Step 1: Write app.py**

```python
# app.py
import gradio as gr
from providers.cosyvoice import CosyVoiceProvider
from story.generator import StoryGenerator
from voice.manager import VoiceManager
import config

tts = CosyVoiceProvider()
story_gen = StoryGenerator()
voice_mgr = VoiceManager()

# State: map voice_id -> display name
voice_options = {}

def refresh_voices():
    voices = voice_mgr.list_voices()
    return {v["name"]: v["id"] for v in voices}

def register_voice(audio_file, name):
    if not audio_file or not name.strip():
        return "请上传音频并输入名称", gr.update(choices=[])
    voice_id = voice_mgr.register(audio_file, name.strip())
    tts.register_existing(voice_id, voice_mgr.get_voice(voice_id)["audio_path"])
    opts = refresh_voices()
    return f"声音 '{name}' 注册成功！(ID: {voice_id[:8]}...)", gr.update(choices=list(opts.keys()))

def generate_story_audio(voice_name, story_mode, preset_choice, custom_prompt):
    opts = refresh_voices()
    if voice_name not in opts:
        return None, "请先注册并选择一个声音"

    voice_id = opts[voice_name]

    # Get story text
    if story_mode == "预设故事":
        if not preset_choice:
            return None, "请选择一个预设故事"
        preset_id = preset_choice.split(" - ")[0] if " - " in preset_choice else preset_choice
        # Find preset by title
        presets = story_gen.list_presets()
        for p in presets:
            if p["title"] == preset_choice or p["id"] == preset_id:
                text = story_gen.load_preset(p["id"])
                break
        else:
            return None, "找不到该预设故事"
    else:
        if not custom_prompt.strip():
            return None, "请输入故事描述"
        text = story_gen.from_prompt(custom_prompt.strip())

    # Synthesize
    output_path = tts.synthesize(text, voice_id)
    return output_path, f"生成完成！故事长度: {len(text)} 字"

def get_preset_options():
    presets = story_gen.list_presets()
    return [f"{p['title']}" for p in presets]

with gr.Blocks(title="Voice Story - 声音克隆晚安故事") as demo:
    gr.Markdown("# Voice Story - 声音克隆晚安故事")
    gr.Markdown("上传声音样本，用克隆的声音朗读故事")

    with gr.Row():
        with gr.Column(scale=1):
            gr.Markdown("### Step 1: 注册声音")
            audio_input = gr.Audio(
                sources=["upload"],
                type="filepath",
                label="上传参考音频 (3-30秒)",
            )
            voice_name = gr.Textbox(label="声音名称", placeholder="例: 妈妈、Taylor Swift")
            register_btn = gr.Button("注册声音", variant="secondary")
            register_status = gr.Textbox(label="状态", interactive=False)

        with gr.Column(scale=1):
            gr.Markdown("### Step 2: 选择故事")
            story_mode = gr.Radio(
                choices=["预设故事", "AI 创作"],
                value="预设故事",
                label="故事来源",
            )
            preset_dropdown = gr.Dropdown(
                choices=get_preset_options(),
                label="选择预设故事",
                visible=True,
            )
            custom_prompt = gr.Textbox(
                label="故事描述",
                placeholder="例: 一只小兔子在森林里迷路了...",
                visible=False,
                lines=3,
            )
            voice_dropdown = gr.Dropdown(
                choices=list(refresh_voices().keys()),
                label="选择声音",
            )

    gr.Markdown("### Step 3: 生成")
    generate_btn = gr.Button("生成故事音频", variant="primary", size="lg")
    gen_status = gr.Textbox(label="状态", interactive=False)
    audio_output = gr.Audio(label="播放", type="filepath")

    # Event handlers
    story_mode.change(
        fn=lambda mode: (
            gr.update(visible=(mode == "预设故事")),
            gr.update(visible=(mode == "AI 创作")),
        ),
        inputs=[story_mode],
        outputs=[preset_dropdown, custom_prompt],
    )

    register_btn.click(
        fn=register_voice,
        inputs=[audio_input, voice_name],
        outputs=[register_status, voice_dropdown],
    )

    generate_btn.click(
        fn=generate_story_audio,
        inputs=[voice_dropdown, story_mode, preset_dropdown, custom_prompt],
        outputs=[audio_output, gen_status],
    )

if __name__ == "__main__":
    demo.launch(server_name="0.0.0.0", server_port=7860)
```

- [ ] **Step 2: Verify app loads without errors**

```bash
cd ~/voice-story && python -c "import app; print('App loaded OK')"
```

Expected: "App loaded OK"

- [ ] **Step 3: Commit**

```bash
git add app.py
git commit -m "feat: add Gradio UI with 3-step voice-story workflow"
```

---

### Task 8: API Smoke Test

**Files:**
- No new files

This task verifies the CosyVoice and Qwen APIs work with your actual key. Only run if `BAILIAN_API_KEY` is set.

- [ ] **Step 1: Test Qwen story generation**

```bash
cd ~/voice-story && python -c "
from story.generator import StoryGenerator
import config
print('API Key:', config.DASHSCOPE_API_KEY[:8] + '...')
sg = StoryGenerator()
story = sg.from_prompt('一只小猫找妈妈')
print('Generated story:')
print(story[:200])
"
```

Expected: A short story about a kitten finding its mother.

- [ ] **Step 2: Test CosyVoice TTS with preset voice (no cloning)**

```bash
cd ~/voice-story && python -c "
import dashscope
import config
from dashscope import SpeechSynthesizer

dashscope.api_key = config.DASHSCOPE_API_KEY
response = SpeechSynthesizer.call(
    model='cosyvoice-v1',
    voice='longxiaochun',
    text='测试语音合成，你好世界。',
    format='wav',
)
print('Status:', response.status_code)
if response.status_code == 200:
    audio = response.get_audio()
    with open('outputs/test_smoke.wav', 'wb') as f:
        f.write(audio)
    print('Saved: outputs/test_smoke.wav')
else:
    print('Error:', response.code, response.message)
"
```

Expected: `Status: 200` and a playable wav file.

- [ ] **Step 3: If Step 2 succeeds, test zero-shot cloning**

```bash
# Record a 5-second audio sample first, save as test_ref.wav
# Then run:
cd ~/voice-story && python -c "
from providers.cosyvoice import CosyVoiceProvider
import config

provider = CosyVoiceProvider(config.DASHSCOPE_API_KEY)
voice_id = provider.clone_voice('test_ref.wav', 'my-voice')
print('Voice ID:', voice_id)

output = provider.synthesize('这是一个声音克隆测试。', voice_id)
print('Output:', output)
"
```

Expected: A wav file using your cloned voice.

- [ ] **Step 4: Commit any API-related fixes**

If parameter names needed adjustment, commit the fixes:

```bash
git add -A
git commit -m "fix: adjust CosyVoice API parameters based on smoke test"
```

---

### Task 9: Launch Demo

- [ ] **Step 1: Start the app**

```bash
cd ~/voice-story
source venv/bin/activate
export BAILIAN_API_KEY="your-key-here"
python app.py
```

- [ ] **Step 2: Open browser**

Navigate to `http://localhost:7860`

- [ ] **Step 3: Test the full flow**

1. Upload a 5-10 second audio sample
2. Enter a name and click "注册声音"
3. Select "预设故事" → pick a story
4. Select the registered voice
5. Click "生成故事音频"
6. Verify the audio plays back with the cloned voice

- [ ] **Step 4: Final commit**

```bash
git add -A
git commit -m "chore: phase 1 complete - voice story demo working"
```
