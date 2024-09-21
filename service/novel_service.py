import glob
import json
import os
import re
import time

from client.llm import kimi_client
from client.text_split_client import split_text_array,split_text_by_mark
from client.tts.tts_client import batchTxt2Wav
from config import novel_material_path
from config.media_format_suffix import MediaFormatSuffix
from config.prompt_config import *


def get_value(cur_prompt, prompt_result, i):
    if cur_prompt is not None:
        return cur_prompt
    size = len(prompt_result)
    if size - 1 >= i:
        return prompt_result[i]['prompt']
    else:
        return None


class Novel:
    def __init__(self, id):
        self.id = id   # 在创建对象时生成唯一ID
        self.raw_text = None  # 原始文本
        self.raw_text_array = []  # 原始文本数组
        self.role = None  # 叙述者角色
        self.optimize_text = None  # 优化文本
        self.srt_path = None  # srt_path
        self.audio_path = None  # 音频文件路径
        self.pic_path = None    # 图片文件路径
        self.sentence_info = None    # asr信息
        self.split_story_info = None    # 分镜信息
        self.pic_prompt_info = None  # 分镜图片信息
        self.pic_task_Ids = []

    def __str__(self):
        return f'id:{self.id}\nraw_text:{self.raw_text}\nrole:{self.role}\noptimize_text:{self.optimize_text}\nraw_text_array:{self.raw_text_array}'


    def get_id(self):
        return self.id

    def generate_tts_tmp_file_path(self, order, model):
        return novel_material_path.tts_dir(self.id) + 'tmp' + '_' + self.id + '_' + str(order) + model

    def generate_tts_mix_file_path(self, model):
        return novel_material_path.tts_dir(self.id) + 'mix' + '_' + self.id + model

    def rm_tmp_tts_file(self):
        to_rm_files = self.find_tmp_tts_files()
        for file_name in to_rm_files:
            try:
                os.remove(file_name)
                print(f"文件 {file_name} 已被删除。")
            except OSError as e:
                print(f"删除文件 {file_name} 时出错: {e}")
        return None

    def find_tmp_tts_files(self):
        file_pattern = novel_material_path.tts_dir(self.id) + 'tmp' + '_' + self.id + '_' + '*'
        files = glob.glob(file_pattern)
        return files

    def save_srt_file(self, sentence_info):
        srt_file_path = novel_material_path.srt_dir(self.id) + self.id + '.json'
        # 将 JSON 数组写入文件，指定编码
        with open(srt_file_path, 'w', encoding='utf-8') as f:
            json.dump(sentence_info, f, ensure_ascii=False, indent=4)
            print(f"文件 {srt_file_path} 已保存。")
        # 更新novel的属性
        self.srt_path = srt_file_path
        self.sentence_info = sentence_info
        return srt_file_path

    def save_pic_prompt_info(self):
        save_path = novel_material_path.prompt_dir(self.id) + 'pic_prompt_info' + '.json'
        # 确保保存路径存在，如果不存在则创建
        # 将 JSON 数组写入文件，指定编码
        with open(save_path, 'w', encoding='utf-8') as f:
            json.dump(self.pic_prompt_info, f, ensure_ascii=False, indent=4)

        print(f"数据已写入 {save_path} 文件。")

    def optimize_text_by_split_story(self):
        optimize_text = ''
        role = '少年'

        role_system_prompt = role_analyze_system_prompt()
        text_optimize_system_prompt = novel_optimize_system_prompt()
        # 获取角色画像
        user_prompt = self.raw_text
        result = kimi_client.call_kimi_client_json(system_content=role_system_prompt, user_content=user_prompt)
        if result is not None:
            role = result['role']
        # 获取优化后正文
        if self.raw_text_array:
            for raw_text in self.raw_text_array:
                user_prompt_item = raw_text
                result = kimi_client.call_kimi_client_json(system_content=text_optimize_system_prompt,
                                                           user_content=user_prompt_item)
                if result is not None:
                    rt_text = result['text']
                    print(f'optimize_text: {rt_text}')
                    optimize_text += rt_text
        else:
            result = kimi_client.call_kimi_client_json(system_content=text_optimize_system_prompt,
                                                       user_content=user_prompt)
            if result is not None:
                optimize_text += result['text']

        # 二次校准字数
        optimize_text, length = split_text_by_mark(optimize_text, len(self.raw_text))
        return optimize_text, role

    def split_story_srt(self):
        self.split_story_info = convert_split_story(self.sentence_info)
        self.save_split_story_time()
        # 序号-文本
        split_story_srt = ''
        for i in range(len(self.split_story_info)):
            split_story_srt += str(i) + '-' + self.split_story_info[i]['text'] + '\n'
        return split_story_srt

    def save_split_story_time(self):
        '''
        保存分镜故事时间信息

        Returns:
            None
        '''
        save_path = novel_material_path.pic_dir(self.id) + str(self.id) + '.json'
        # 确保保存路径存在，如果不存在则创建
        # 将 JSON 数组写入文件，指定编码
        with open(save_path, 'w', encoding='utf-8') as f:
            json.dump(self.split_story_info, f, ensure_ascii=False, indent=4)

        print(f"数据已写入 {save_path} 文件。")

    def format_pic_prompt(self, bacthPrompt):
        pic_prompt_map = {}
        # 去除最后的换行符
        bacthPrompt = bacthPrompt.rstrip('\n')
        # 合并连续的换行符为一个换行符
        bacthPrompt = re.sub(r'\n+', '\n', bacthPrompt)

        pattern = r"(\d+)-(.*?)(?=\n\d+-|\Z)"

        # 使用 findall 方法查找所有匹配的描述
        matches = re.findall(pattern, bacthPrompt)
        for match in matches:
            # 将匹配的序号和描述存储在字典中
            pic_prompt_map[match[0]] = match[1]
        return pic_prompt_map

    def build_prompt_info(self, pic_prompt_map):
        # 更新场景
        if len(pic_prompt_map) == 0:
            return self.pic_prompt_info
        size = len(self.split_story_info)
        pic_prompt_info = {}
        # 如果是新增
        if self.pic_prompt_info:
            pic_prompt_info = self.pic_prompt_info
        else:
            pic_prompt_info['size'] = 0
            # 构建prompt_info
            pic_prompt_info['result'] = []
            pic_prompt_info['except_index'] = []
        for i in range(size):
            story_board = self.split_story_info[i]['text']
            # 判断prompt是否为空, 新增或者更新场景
            prompt = get_value(pic_prompt_map.get(str(i)), pic_prompt_info['result'], i)
            if prompt is None:
                pic_prompt_info['except_index'].append(i)
            else:
                pic_prompt_info['size'] += 1
            pic_prompt_item = {'index': i, 'prompt': prompt, 'story_board': story_board}
            pic_prompt_info['result'].append(pic_prompt_item)
        return pic_prompt_info

    def reload_story_board(self, story_board_llm_out):
        '''
        加载story_board

        Args:
         story_board_llm_out (str): story_board的LLM输出

        Returns:
         dict: 包含序号-描述的字典
        '''
        # 格式化,返回序号-描述
        pic_prompt_map = self.format_pic_prompt(story_board_llm_out)
        # 识别有效的story_board
        self.pic_prompt_info = self.build_prompt_info(pic_prompt_map)
        self.save_pic_prompt_info()
        print(f"reload_story_board novel:{self}")
        return self.pic_prompt_info


def split_text_array_without_segment(text, split_size=600):
    segments = []
    segments_tmp = split_text_array(text, split_size)
    for segment in segments_tmp:
        # 替换所有标点符号为空
        segment = re.sub(r'[^\w\s\d]', '', segment)
        segments.append(segment)
    return segments

def convert_split_story(sentence_info, split_limit=5000):
    split_story_infos = []
    current_segment = {'start': 0, 'end': split_limit, 'text': ''}
    num = 1
    for segment in sentence_info:
        # 当前分镜为空则文本直接添加,结束时间取最大
        if segment['text'] == '':
            current_segment['text'] += segment['text']
            current_segment['end'] = max(current_segment['end'], segment['end'])
        # 如果代合并文本结束时间小于分镜时间直接合入
        elif segment['end'] <= current_segment['end']:
            current_segment['text'] += segment['text']
        else:
            # 分镜结束,更正结束时间添加到数组
            end = segment['start']
            current_segment['end'] = end
            split_story_infos.append(current_segment)
            # 创建新的分镜
            current_segment = {'start': end, 'end': end + split_limit, 'text': segment['text']}
            num += 1

    # 添加最后一个分镜
    # 获取sentence_info最后一个元素的结束时间
    if len(split_story_infos) < num:
        current_segment['end'] = sentence_info[-1]['end']
        split_story_infos.append(current_segment)

    return split_story_infos


def gen_novel_by_text_array(novel_id, novel_raw_text):
    novel_in = Novel(novel_id)
    # 生成正文数组，去除符号
    novel_in.raw_text = novel_raw_text
    novel_in.raw_text_array = split_text_array_without_segment(text=novel_raw_text)
    # 生成优化文本
    novel_in.optimize_text, novel_in.role = novel_in.optimize_text_by_split_story()
    return novel_in


def gen_novel_audio(novel_text, voice_type, voice_speed, novel):
    file_path = novel.generate_tts_mix_file_path(MediaFormatSuffix.AUDIO_WAV.value)
    batchTxt2Wav(novel_text, novel.id, voice_type, voice_speed, file_path)
    return file_path