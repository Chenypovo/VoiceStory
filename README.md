# Voice Story - 声音克隆晚安故事

上传一段声音样本，用 AI 克隆的声音朗读睡前故事。

## 功能

- **声音克隆** — 上传 3-30 秒音频，即可复刻声音
- **AI 故事创作** — 输入一句话描述，AI 生成 300-500 字温馨睡前故事
- **预设故事** — 内置 3 篇精选故事，开箱即用
- **Mock 模式** — 未配置 API Key 时自动进入，可预览完整 UI 流程

## 技术栈

- **前端**: Gradio
- **TTS / 声音克隆**: 阿里云百炼 Qwen3-TTS-Flash
- **故事生成**: 阿里云百炼 Qwen-Plus (通义千问)
- **语言**: Python 3.9+

## 架构

```
voice-story/
├── app.py                  # Gradio UI 入口
├── config.py               # 全局配置（API key、模型、路径）
├── providers/
│   ├── tts_base.py         # TTS 抽象基类
│   └── cosyvoice.py        # Qwen3-TTS 实现（REST API + 声音克隆）
├── story/
│   ├── generator.py        # AI 故事生成器（Qwen-Plus）
│   └── presets/             # 预设故事 JSON
├── voice/
│   └── manager.py          # 声音注册与管理
├── outputs/                 # 生成的音频（自动创建）
├── tests/                   # 单元测试
├── Dockerfile
├── docker-compose.yml
└── requirements.txt
```

**工作流程:**

1. 用户上传参考音频 → 上传至 DashScope OSS → 返回声音 ID
2. 用户选择故事来源（预设 / AI 创作）→ 获取故事文本
3. 调用 TTS API，传入故事文本 + 参考音频 URL → 返回克隆声音的音频

## 快速开始

### 方式一：Docker（推荐）

需要先安装 [Docker Desktop](https://www.docker.com/products/docker-desktop/)。

```bash
git clone https://github.com/Chenypovo/VoiceStory.git
cd VoiceStory
cp .env.example .env
# 编辑 .env，填入你的百炼 API Key
docker compose up
```

打开 http://localhost:7860

### 方式二：本地运行

```bash
git clone https://github.com/Chenypovo/VoiceStory.git
cd VoiceStory
python -m venv venv
source venv/bin/activate   # Windows: venv\Scripts\activate
pip install -r requirements.txt

# 设置 API Key
export BAILIAN_API_KEY=sk-your-key-here   # Windows: set BAILIAN_API_KEY=sk-xxx

python app.py
```

打开 http://127.0.0.1:7860

## 获取 API Key

1. 注册 [阿里云百炼平台](https://bailian.console.aliyun.com/)
2. 进入控制台，创建 API Key
3. 确保 Qwen-Plus 和 Qwen3-TTS-Flash 模型已开通

## 使用说明

1. **注册声音** — 上传一段 3-30 秒的音频文件（WAV/MP3），输入名称，点击注册
2. **选择故事** — 选"预设故事"直接使用内置故事，或选"AI 创作"输入描述让 AI 生成
3. **生成音频** — 选择已注册的声音，点击"生成故事音频"，等待生成完成即可播放

## 运行测试

```bash
pytest tests/ -v
```

## License

MIT
