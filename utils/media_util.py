import base64
import os

from tmp_data import gradio_path

def base2Wav(base64_data, tts_out_file):
    # 解码 Base64 数据
    audio_data = base64.b64decode(base64_data)

    # 将二进制数据写入 WAV 文件
    with open(tts_out_file, "wb") as audio_file:
        audio_file.write(audio_data)


def writeWav(base64_data, file_name):
    dir = gradio_path.tts_out_dir()
    file_path = os.path.join(dir, file_name+".wav")
    base2Wav(base64_data, file_path)
    return file_path