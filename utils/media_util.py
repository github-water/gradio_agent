import base64
import os

from moviepy.audio.AudioClip import concatenate_audioclips
from moviepy.audio.io.AudioFileClip import AudioFileClip



def base2Wav(base64_data, tts_out_file):
    # 解码 Base64 数据
    audio_data = base64.b64decode(base64_data)

    # 将二进制数据写入 WAV 文件
    with open(tts_out_file, "wb") as audio_file:
        audio_file.write(audio_data)
    return tts_out_file


def merge_audio_files(file_paths, output_file):
    audio_clip_list=[]
    # 创建音频剪辑对象
    for file_path in file_paths:
        audio = AudioFileClip(file_path)
        audio_clip_list.append(audio)

    # 合并音频剪辑
    merged_audio = concatenate_audioclips(audio_clip_list)
    # 导出合并后的音频文件
    merged_audio.write_audiofile(output_file)
    print(f'Merged audio file {output_file}')

def rm_tmp_files(file_paths):
    for file_name in file_paths:
        try:
            os.remove(file_name)
            print(f"文件 {file_name} 已被删除。")
        except OSError as e:
            print(f"删除文件 {file_name} 时出错: {e}")