import gradio as gr
from providers.cosyvoice import CosyVoiceProvider
from story.generator import StoryGenerator
from voice.manager import VoiceManager
import config

tts = CosyVoiceProvider()
story_gen = StoryGenerator()
voice_mgr = VoiceManager()


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

    if story_mode == "预设故事":
        if not preset_choice:
            return None, "请选择一个预设故事"
        presets = story_gen.list_presets()
        for p in presets:
            if p["title"] == preset_choice or p["id"] == preset_choice:
                text = story_gen.load_preset(p["id"])
                break
        else:
            return None, "找不到该预设故事"
    else:
        if not custom_prompt.strip():
            return None, "请输入故事描述"
        text = story_gen.from_prompt(custom_prompt.strip())

    output_path = tts.synthesize(text, voice_id)
    return output_path, f"生成完成！故事长度: {len(text)} 字"


def get_preset_options():
    presets = story_gen.list_presets()
    return [p["title"] for p in presets]


with gr.Blocks(title="Voice Story - 声音克隆晚安故事") as demo:
    gr.Markdown("# Voice Story - 声音克隆晚安故事")
    gr.Markdown("上传声音样本，用克隆的声音朗读故事")

    with gr.Row():
        with gr.Column(scale=1):
            gr.Markdown("### Step 1: 注册声音")
            audio_input = gr.Audio(sources=["upload"], type="filepath", label="上传参考音频 (3-30秒)")
            voice_name = gr.Textbox(label="声音名称", placeholder="例: 妈妈、Taylor Swift")
            register_btn = gr.Button("注册声音", variant="secondary")
            register_status = gr.Textbox(label="状态", interactive=False)

        with gr.Column(scale=1):
            gr.Markdown("### Step 2: 选择故事")
            story_mode = gr.Radio(choices=["预设故事", "AI 创作"], value="预设故事", label="故事来源")
            preset_dropdown = gr.Dropdown(choices=get_preset_options(), label="选择预设故事", visible=True)
            custom_prompt = gr.Textbox(label="故事描述", placeholder="例: 一只小兔子在森林里迷路了...", visible=False, lines=3)
            voice_dropdown = gr.Dropdown(choices=list(refresh_voices().keys()), label="选择声音")

    gr.Markdown("### Step 3: 生成")
    generate_btn = gr.Button("生成故事音频", variant="primary", size="lg")
    gen_status = gr.Textbox(label="状态", interactive=False)
    audio_output = gr.Audio(label="播放", type="filepath")

    story_mode.change(
        fn=lambda mode: (gr.update(visible=(mode == "预设故事")), gr.update(visible=(mode == "AI 创作"))),
        inputs=[story_mode], outputs=[preset_dropdown, custom_prompt],
    )
    register_btn.click(fn=register_voice, inputs=[audio_input, voice_name], outputs=[register_status, voice_dropdown])
    generate_btn.click(fn=generate_story_audio, inputs=[voice_dropdown, story_mode, preset_dropdown, custom_prompt], outputs=[audio_output, gen_status])

if __name__ == "__main__":
    demo.launch(server_name="0.0.0.0", server_port=7860)
