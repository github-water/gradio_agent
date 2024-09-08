import gradio as gr
from pygments.lexer import default

from client.text_split_client import process_text
from client.tts_client import batchTxt2Wav
from utils.media_util import writeWav

with gr.Blocks() as novel_block:
    # 文本裁剪
    with gr.Row() as txt_split_row:
        with gr.Column():
            input_txt = gr.Textbox(label='输入文本')
            split_size = gr.Number(label='裁剪大小', value=1314)
            split_btn = gr.Button("split")
        with gr.Column():
            output_txt = gr.Textbox(label='输出文本')
            output_size = gr.Textbox(label='输出大小')

    # 连接输入和输出
    split_btn.click(process_text, inputs=[input_txt, split_size], outputs=[output_txt, output_size])

    # tts转换
    with gr.Row() as tts_row:
        with gr.Column():
            session_id = gr.Textbox(label='音频id')
            voice_type = gr.Number(label='音色', value=101031)
            tts_btn = gr.Button("生成语音")
        with gr.Column():
            wav_file_name = gr.Textbox(label='音频路径')
    tts_btn.click(batchTxt2Wav,inputs=[output_txt, session_id, voice_type], outputs=[wav_file_name])
novel_block.launch(server_port=8000)

