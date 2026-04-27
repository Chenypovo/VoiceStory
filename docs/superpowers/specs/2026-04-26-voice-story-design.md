# Voice Story - 声音克隆晚安故事

## 概述

一个 Web 应用，用户上传一段声音样本，系统克隆该音色，然后用这个声音朗读预设或 AI 生成的故事。

## 目标用户

兴趣驱动的技术实验项目，核心价值在于端到端串联 ASR / LLM / Voice Clone TTS 三个 AI 能力。

## 系统架构

```
┌─────────────┐
│  Web UI     │  Gradio
│  (浏览器)    │
└──────┬──────┘
       │
       ▼
┌─────────────┐
│  app.py     │  Gradio 主入口，内置后端
└──┬───┬───┬──┘
   │   │   │
   ▼   ▼   ▼
 ┌───┐┌──┐┌──────┐
 │LLM││TTS││ASR   │
 │生成││克隆││(可选) │
 │故事││声音││语音输入│
 └───┘└──┘└──────┘
```

## 技术选型

| 组件 | 第一版 | 后续可替换 |
|------|--------|-----------|
| 声音克隆 TTS | 通义 CosyVoice API（零样本克隆） | Fish Speech / ChatTTS 本地部署 |
| 故事生成 | 通义千问 API | 不变 |
| ASR（可选） | 通义 ASR API | Whisper 本地 |
| Web 框架 | Gradio（内置音频上传/播放组件） | 可迁 Streamlit |
| 存储 | 本地文件系统 | 按需升级 |

### 为什么选 CosyVoice 先行

- 已有 BAILIAN_API_KEY，零配置
- 零样本克隆，上传 3-30s 音频即可
- 纯 API，不需要本地 GPU
- 后续通过 TTSProvider 抽象层可无缝切换到本地模型

## 核心数据流

```
用户上传音频 (3-30s)
       │
       ▼
  声音注册（CosyVoice 提取 voice_id → 存储到 profiles/）
       │
用户选择故事来源 ──┐
       │          │
  预设故事库(JSON)  LLM 实时生成(用户描述→故事)
       │          │
       └────┬─────┘
            │ 故事文本
            ▼
     TTS 合成（voice_id + 文本 → 克隆语音）
            │
            ▼
     Web 播放器（在线播放 + 可下载）
```

## 文件结构

```
voice-story/
├── app.py                 # Gradio 主入口
├── requirements.txt
├── config.py              # API keys, 模型配置
├── providers/
│   ├── tts_base.py        # TTSProvider 抽象接口
│   ├── cosyvoice.py       # CosyVoice API 实现
│   └── local_tts.py       # 后续 Fish Speech 实现
├── story/
│   ├── generator.py       # LLM 故事生成
│   └── presets/           # 预设故事 JSON
│       └── *.json
├── voice/
│   ├── manager.py         # 声音注册/管理
│   └── profiles/          # 用户上传的音频
├── outputs/               # 生成的音频文件
└── docs/
    └── superpowers/
        └── specs/
            └── 2026-04-26-voice-story-design.md
```

## 接口设计

### TTSProvider 抽象层

```python
class TTSProvider(ABC):
    def clone_voice(self, audio_path: str, name: str) -> str:
        """注册声音，返回 voice_id"""

    def synthesize(self, text: str, voice_id: str) -> str:
        """合成语音，返回输出音频路径"""
```

### StoryGenerator

```python
class StoryGenerator:
    def from_prompt(self, prompt: str) -> str:
        """LLM 生成故事"""

    def load_preset(self, name: str) -> str:
        """加载预设故事"""
```

### VoiceManager

```python
class VoiceManager:
    def register(self, audio_path: str, name: str) -> str:
        """注册声音配置"""

    def list_voices(self) -> list[dict]:
        """列出已注册声音"""

    def get_voice(self, voice_id: str) -> dict:
        """获取声音配置"""
```

## 数据模型

### voice_profile

```json
{
  "id": "uuid",
  "name": "Taylor Swift",
  "created_at": "2026-04-26T01:00:00",
  "audio_path": "profiles/{id}.wav",
  "voice_id": "cosyvoice_ref_id"
}
```

### preset story

```json
{
  "id": "little_red_riding_hood",
  "title": "小红帽",
  "text": "从前有一个小女孩...",
  "tags": ["经典", "童话"]
}
```

## Gradio 界面

三步式流程：

1. **声音注册**：拖拽上传 3-30s 音频 + 输入名称 → 注册
2. **选择故事**：下拉选预设 或 文本框输入描述让 AI 生成
3. **生成播放**：点击生成 → 在线播放 + 下载按钮

## 实施路线

### Phase 1：最小可用 demo

- CosyVoice API 对接（声音克隆 + TTS）
- 通义千问生成故事
- Gradio 三步界面
- 3-5 个预设故事

### Phase 2：体验优化

- 声音库管理（保存/切换）
- 故事生成 prompt 优化（角色、风格可控）
- 播放进度条 + 历史记录

### Phase 3：本地化

- Fish Speech / ChatTTS 本地 TTS 替换
- Whisper 本地 ASR（可选语音输入）
- 部署优化

## 约束

- 仅限合法声音克隆用途（自己声音、授权声音）
- 音频上传限制 30s，格式 wav/mp3
- 第一版不支持实时流式播放，先生成完整音频再播放
