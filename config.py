import os

BASE_DIR = os.path.dirname(os.path.abspath(__file__))
PROFILES_DIR = os.path.join(BASE_DIR, "voice", "profiles")
OUTPUTS_DIR = os.path.join(BASE_DIR, "outputs")
PRESETS_DIR = os.path.join(BASE_DIR, "story", "presets")

DASHSCOPE_API_KEY = os.environ.get("BAILIAN_API_KEY", "")
MOCK_MODE = not bool(DASHSCOPE_API_KEY)
LLM_MODEL = "qwen-plus"
TTS_MODEL = "cosyvoice-v1"
TTS_VOICE_DEFAULT = "longxiaochun"

os.makedirs(PROFILES_DIR, exist_ok=True)
os.makedirs(OUTPUTS_DIR, exist_ok=True)
