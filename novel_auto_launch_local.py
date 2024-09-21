import copy
import json
import re

import gradio as gr
import argparse
from funasr import AutoModel
from client.text_split_client import split_text_by_mark, split_text_array
from service.novel_service import gen_novel_by_text_array, gen_novel_audio
from client.asr.fun_asr_client import asr_client
from client.llm.qwen_client import call_qwen_model
from client.llm.kimi_client import call_kimi_client
from config.sys_config import sysConfig, get_model_path
from config.prompt_config import *

if __name__ == "__main__":
    parser = argparse.ArgumentParser(description='argparse testing')
    parser.add_argument('--lang', '-l', type=str, default="zh", help="language")
    parser.add_argument('--share', '-s', action='store_true', help="if to establish gradio share link")
    parser.add_argument('--port', '-p', type=int, default=6666, help='port number')
    parser.add_argument('--listen', action='store_true', help="if to listen to all hosts")
    args = parser.parse_args()


    funasr_model = AutoModel(model=get_model_path("iic/speech_seaco_paraformer_large_asr_nat-zh-cn-16k-common-vocab8404-pytorch"),
                             model_revision="v2.0.4",
                             vad_model=get_model_path("damo/speech_fsmn_vad_zh-cn-16k-common-pytorch"),
                             punc_model=get_model_path("damo/punc_ct-transformer_zh-cn-common-vocab272727-pytorch"),
                             spk_model=get_model_path("damo/speech_campplus_sv_zh-cn_16k-common")
                            )

    def display_novel(novel_p):
        return str(novel_p)

    def init_novel_by_text(novel_id, novel_origin_text, split_size):
        # 限制分割大小在2000以内
        split_size_tmp = min(split_size, 2000)
        # 调用分割文本函数，并获取分割后的文本列表
        split_text_list, length = split_text_by_mark(novel_origin_text, split_size_tmp)
        # 初始化小说
        novel_in = gen_novel_by_text_array(novel_id, split_text_list)
        return novel_in, novel_in.optimize_text

    # 定义异步函数
    def generate_audio(voice_type_p, voice_speed_p, novel_p):
        file_path = gen_novel_audio(novel_p.optimize_text, voice_type_p, voice_speed_p, novel_p)
        return file_path, file_path

    # asr识别
    def asr_recog(audio_file_path, novel):
        # 识别asr
        client = asr_client(funasr_model)
        client.lang = 'zh'
        srt_text, sentence_info = client.recog(audio_file_path)
        # 保存asr文件\填充novel的属性
        srt_path = novel.save_srt_file(sentence_info)
        return srt_text, srt_path



    def gen_story_board_v2(system_content_p, user_content_p, model_p, apikey_p, steps_p, novel_p):
        # 首先进行分镜拆分
        split_story_srt = novel_p.split_story_srt()
        # 优化系统prompt
        system_content_p = "叙述者是一个" + novel_p.role + system_content_p
        # 其次根据分镜脚本请求大模型
        llm_ouput_list = ''
        srt_text_chunks = split_text_by_lines(split_story_srt, steps_p)
        for srt_text_chunk in srt_text_chunks:
            llm_ouput_list += llm_inference(system_content_p, user_content_p, srt_text_chunk, model_p, apikey_p)
            llm_ouput_list += '\n'
        # 读取llm_ouput_list并加载到novel
        pic_prompt_info = novel_p.reload_story_board(llm_ouput_list)
        output_list = gen_list_by_prompt(pic_prompt_info['result'])
        return output_list, pic_prompt_info['size'], pic_prompt_info['except_index']


    def split_text_by_lines(text, lines_per_chunk):
        """
        将文本按照指定的行数拆分成多个部分。

        :param text: 要拆分的文本，应该是一个字符串，其中每行由换行符分隔。
        :param lines_per_chunk: 每个拆分后的文本块包含的行数。
        :return: 包含拆分后的文本块的列表。
        """
        # 合并连续的换行符为一个换行符
        text = re.sub(r'\n+', '\n', text)
        # 将文本分割成行
        lines = text.split('\n')
        # 使用列表推导式来创建文本块，每个块是一个字符串
        chunks = ['\n'.join(lines[i:i + lines_per_chunk]) for i in range(0, len(lines), lines_per_chunk)]
        return chunks



    # llm调用
    def llm_inference(system_content, user_content, srt_text, model, apikey):
        if model.startswith('qwen'):
            return call_qwen_model(apikey, model, user_content + '\n' + srt_text, system_content)
        elif model.startswith('kimi'):
            return call_kimi_client(None, None, user_content + '\n' + srt_text, system_content)
        else:
            print("llm_interface call exception")
            return None


    def gen_list_by_prompt(prompt_list):
        output_list = ''
        for prompt in prompt_list:
            if prompt['prompt'] is not None:
                output_list += str(prompt['index']) +'-'+ prompt['prompt']+'\n'
        return output_list

    def batch_painting_v2(novel):
        style_model = pic_style_system_prompt()
        img_url_list = novel.painting_by_stroy(style_model, None)
        # 替换None
        img_url_list = [url if url is not None else '' for url in img_url_list]
        return img_url_list

    with gr.Blocks() as novel_block:
        # 生成小说
        novel = gr.State()
        # 生成对象
        with gr.Row() as novel_row:
            with gr.Column():
                novel_id = gr.Textbox(label='小说id', value='test')
                novel_origin_text = gr.Textbox(label='小说原文', lines=2, value='我们村的女子结婚前夜必须去村后的山庙裸睡一夜才能出嫁。只有把初夜交给山神，这样娘家才会平平安安。如果违背这条村规，娘家必有横祸。大学时，我谈了一个男朋友告诉他，我们村这个不成文的规矩，男友自然不信，觉得是我们村里的某个老色胚装神弄鬼，目的就是白嫖姑娘。趁着十一假期，男友决定跟我一起回老家，他要亲自把那老色胚揪出来，并将老色胚绳之以法拯救我们村的未婚女子。')
                split_size = gr.Number(label='裁剪大小<2000', value=1200)
                gen_novel_btn = gr.Button("初始化")
            with gr.Row():
                novel_optimize_text = gr.Textbox(label='小说优化', lines=3)
        gen_novel_btn.click(init_novel_by_text,
                            inputs=[novel_id, novel_origin_text, split_size],
                            outputs=[novel, novel_optimize_text])

        # 生成语音
        with gr.Row() as tts_row:
            with gr.Column():
                # 展示腾讯音色
                voice_type = gr.Dropdown(choices=[10510000,
                                                  1001,
                                                  1002,
                                                  100510000,
                                                  101001,
                                                  301000,
                                                  101031], label='音色', value=101031)
                voice_speed = gr.Number(label='音速', value=0)
                tts_btn = gr.Button("生成语音")
            with gr.Column():
                # 创建一个音频组件，初始不播放任何音频
                audio = gr.Audio(label='音频', value=None)
                audio_file_path = gr.Textbox(label='音频路径', lines=1)
        tts_btn.click(generate_audio, inputs=[voice_type, voice_speed, novel], outputs=[audio, audio_file_path])

        # asr识别
        '''
            1、需要对srt时间轴进行校准
        '''
        with gr.Row() as asr_row:
            # asr生成
            asr_btn = gr.Button("ASR识别")
            asr_output = gr.Textbox(label='ASR识别结果', lines=3)
            srt_file_path = gr.Textbox(label='srt文件路径', lines=1)
        asr_btn.click(asr_recog, inputs=[audio_file_path, novel], outputs=[asr_output, srt_file_path])


        # 生成分镜
        with gr.Row():
            with gr.Row() as story_board_row:
                with gr.Column():
                    llm_model = gr.Dropdown(['qwen-plus','kimi'], label='llm模型',value='qwen-plus')
                    llm_key = gr.Textbox(label='apikey', lines=1)
                    story_board_btn = gr.Button("生成分镜")
                    story_board_size = gr.Number(label='分镜个数')
                    except_index = gr.Json(label='异常分镜')
                with gr.Column():
                    story_board_prompt_head = gr.Textbox(label='prompt_head', lines=2,
                                                         value="""
                                                            针对所提供的分镜脚本中的每一句台词，请创作相应的动漫风格悬疑气氛图片描述;确保每张图片聚焦单一主体人物，以冷暗色调的背景来增强氛围感。请确保描述内容避开血腥、暴力元素及任何敏感词汇，维持画面的和谐美感;并与视频剧本的整体风格保持连贯。请按照如下格式输出：原文序列号-描述，确保序列号与SRT原文对应,不要输出无关信息。                      
                                                         """)
                    story_board_prompt_user = gr.Textbox(label='prompt_user', lines=1, value='以下是分镜脚本:')
                    story_board_step = gr.Number(label='步数', value=5)
                    story_board_output = gr.Textbox(label='分镜结果', lines=3)
            story_board_btn.click(gen_story_board_v2,
                                  inputs=[story_board_prompt_head, story_board_prompt_user,
                                          llm_model, llm_key, story_board_step, novel],
                                  outputs=[story_board_output, story_board_size, except_index])



        # 文生图
        with gr.Row() as prompt_2_pic_row:
            with gr.Column():
                prompt_2_pic_btn = gr.Button("文生图")
                image_list = gr.Json(label="图片列表")
                dis_play_btn = gr.Button("novel")
        prompt_2_pic_btn.click(batch_painting_v2, inputs=[novel], outputs=[image_list])

        # 创建JSON组件来展示novel的内容
        novel_display = gr.Textbox(value='novel_object')

        # 当按钮被点击时，更新novel的值
        dis_play_btn.click(display_novel, inputs=[novel], outputs=novel_display)



if __name__ == '__main__':
    novel_block.launch(server_port=sysConfig.SERVER_PORT, server_name=sysConfig.SERVER_HOST)

