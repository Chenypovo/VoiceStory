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
        stories = []
        for path in glob.glob(os.path.join(self.presets_dir, "*.json")):
            with open(path, "r", encoding="utf-8") as f:
                data = json.load(f)
                stories.append({"id": data["id"], "title": data["title"], "tags": data.get("tags", [])})
        return stories

    def load_preset(self, story_id: str) -> str:
        path = os.path.join(self.presets_dir, f"{story_id}.json")
        if not os.path.exists(path):
            raise FileNotFoundError(f"Preset story '{story_id}' not found")
        with open(path, "r", encoding="utf-8") as f:
            return json.load(f)["text"]

    def from_prompt(self, prompt: str) -> str:
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
