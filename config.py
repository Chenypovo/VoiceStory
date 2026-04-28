import os

BASE_DIR = os.path.dirname(os.path.abspath(__file__))
PROFILES_DIR = os.path.join(BASE_DIR, "voice", "profiles")
OUTPUTS_DIR = os.path.join(BASE_DIR, "outputs")
PRESETS_DIR = os.path.join(BASE_DIR, "story", "presets")

DASHSCOPE_API_KEY = os.environ.get("BAILIAN_API_KEY", "")
MOCK_MODE = not bool(DASHSCOPE_API_KEY)

# LLM (OpenAI-compatible endpoint)
LLM_MODEL = "qwen-plus"
LLM_BASE_URL = "https://dashscope-intl.aliyuncs.com/compatible-mode/v1"

# TTS (native DashScope MultiModalConversation API)
TTS_MODEL = "qwen3-tts-flash"
TTS_VOICE_DEFAULT = "Cherry"
TTS_API_URL = "https://dashscope-intl.aliyuncs.com/api/v1/services/aigc/multimodal-generation/generation"

os.makedirs(PROFILES_DIR, exist_ok=True)
os.makedirs(OUTPUTS_DIR, exist_ok=True)
