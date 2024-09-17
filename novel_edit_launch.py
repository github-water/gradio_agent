import re

import gradio as gr
import argparse
from funasr import AutoModel
from client.text_split_client import split_text_by_mark, split_text_array
from client.asr.fun_asr_client import asr_client
from client.llm.qwen_api import call_qwen_model

if __name__ == "__main__":
    parser = argparse.ArgumentParser(description='argparse testing')
    parser.add_argument('--lang', '-l', type=str, default="zh", help="language")
    parser.add_argument('--share', '-s', action='store_true', help="if to establish gradio share link")
    parser.add_argument('--port', '-p', type=int, default=6666, help='port number')
    parser.add_argument('--listen', action='store_true', help="if to listen to all hosts")
    server_name='172.22.211.56'
    args = parser.parse_args()


    funasr_model = AutoModel(model="iic/speech_seaco_paraformer_large_asr_nat-zh-cn-16k-common-vocab8404-pytorch",
                             model_revision="v2.0.4",
                             vad_model="damo/speech_fsmn_vad_zh-cn-16k-common-pytorch",
                             punc_model="damo/punc_ct-transformer_zh-cn-common-vocab272727-pytorch",
                             spk_model="damo/speech_campplus_sv_zh-cn_16k-common"
                            )


    def generate_novel_id(novel_id):
        novel = generate_novel(novel_id)
        return novel


    # 定义异步函数
    async def asyc_batchTxt2Wav(ioutput_txt_array, voice_type, voice_speed, novel):
        file_path = await batchTxt2Wav(ioutput_txt_array, voice_type, voice_speed, novel)
        return file_path, file_path


    # asr识别
    def asr_recog(audio_file_path, novel):
        # 识别asr
        client = asr_client(funasr_model)
        client.lang = 'zh'
        srt_text, sentence_info = client.recog(audio_file_path)
        # 保存asr文件\填充novel的属性
        srt_path = novel.save_srt_file(srt_text, sentence_info)
        return srt_text, srt_path


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


    def llm_inference(system_content, user_content, srt_text, model, apikey):
        if model.startswith('qwen'):
            return call_qwen_model(apikey, model, user_content + '\n' + srt_text, system_content)
        else:
            print("llm_interface call exception")
            return None


    def gen_list_by_prompt(prompt_list):
        output_list = ''
        for prompt in prompt_list:
            if prompt['prompt'] is not None:
                output_list += str(prompt['index']) + '-' + prompt['prompt'] + '\n'
        return output_list


    #
    def gen_story_board(system_content, user_content, srt_text_arr, model, apikey, steps, novel):
        llm_ouput_list = ''
        srt_text_chunks = split_text_by_lines(srt_text_arr, steps)
        for srt_text_chunk in srt_text_chunks:
            llm_ouput_list += llm_inference(system_content, user_content, srt_text_chunk, model, apikey)
            llm_ouput_list += '\n'
        # 读取llm_ouput_list并加载到novel
        pic_prompt_info = novel.reload_story_board(llm_ouput_list)
        output_list = gen_list_by_prompt(pic_prompt_info['result'])
        return output_list, pic_prompt_info['size'], pic_prompt_info['except_index']


    def retry_stroy_board(system_content, user_content, model, apikey, novel):
        llm_ouput_list = ''
        srt_text_chunk = novel.get_fail_story_board_str()
        if srt_text_chunk is not None:
            llm_ouput_list = llm_inference(system_content, user_content, srt_text_chunk, model, apikey)
        pic_prompt_info = novel.reload_story_board(llm_ouput_list)
        output_list = gen_list_by_prompt(pic_prompt_info['result'])
        return output_list, pic_prompt_info['size'], pic_prompt_info['except_index']


    def split_story_srt(novel):
        return novel.split_story_srt()


    def format_pic_prompt(bacthPrompt):
        # 去除最后的换行符
        bacthPrompt = bacthPrompt.rstrip('\n')
        # 合并连续的换行符为一个换行符
        bacthPrompt = re.sub(r'\n+', '\n', bacthPrompt)

        pattern = r"(\d+)-(.*?)(?=\n\d+-|\Z)"

        # 使用 findall 方法查找所有匹配的描述
        matches = re.findall(pattern, bacthPrompt)

        # 组装成数组
        prompt_arr = [match[1] for match in matches]
        return prompt_arr


    def batch_painting(bacthPrompt, novel):
        promt_arr_input = []
        prompt_arr = format_pic_prompt(bacthPrompt)
        style_model = '画风：诡异、悬疑、略带恐怖；环境阴暗、破旧，不要出现亮色调；风格：动漫。'
        for e in prompt_arr:
            e += style_model
            promt_arr_input.append(e)
        img_url_list = novel.invokePainting(promt_arr_input)
        # 替换None
        img_url_list = [url if url is not None else '' for url in img_url_list]
        return img_url_list


    def batch_painting_v2(novel):
        style_model = '画风：诡异、悬疑、略带恐怖；环境阴暗、破旧；风格：动漫。'
        img_url_list = novel.painting_by_stroy(style_model, None)
        # 替换None
        img_url_list = [url if url is not None else '' for url in img_url_list]
        return img_url_list


    def refresh_novel(novel_id):
        novel.id = novel_id


    with gr.Blocks() as novel_block:
        # 生成小说
        novel = gr.State()
        # 生成对象
        with gr.Row() as novel_row:
            novel_id = gr.Textbox(label='小说id', value='test')
            gen_novel_btn = gr.Button("Generate Novel")
        gen_novel_btn.click(generate_novel_id, inputs=[novel_id], outputs=[novel])

        # 文本裁剪
        with gr.Row() as txt_split_row:
            with gr.Column():
                input_txt = gr.Textbox(label='输入文本', lines=3,
                                       value='我们村的女子结婚前夜必须去村后的山庙裸睡一夜才能出嫁。只有把初夜交给山神，这样娘家才会平平安安。如果违背这条村规，娘家必有横祸。大学时，我谈了一个男朋友告诉他，我们村这个不成文的规矩，男友自然不信，觉得是我们村里的某个老色胚装神弄鬼，目的就是白嫖姑娘。趁着十一假期，男友决定跟我一起回老家，他要亲自把那老色胚揪出来，并将老色胚绳之以法拯救我们村的未婚女子。')
                split_size = gr.Number(label='裁剪大小', value=1200)
                split_btn = gr.Button("split")
            with gr.Column():
                output_txt = gr.Textbox(label='输出文本', lines=3)
                output_size = gr.Textbox(label='输出大小')
                split_array_btn = gr.Button("split_array")
        # 连接输入和输出
        split_btn.click(split_text_by_mark, inputs=[input_txt, split_size], outputs=[output_txt, output_size])

        # 文本分段
        with gr.Row() as txt_split_array:
            with gr.Column():
                tts_size = gr.Number(label='元素大小', value=600)
                output_txt_array = gr.Json(label='分段文本', height=100)
        split_array_btn.click(split_text_array, inputs=[output_txt, tts_size], outputs=[output_txt_array])

        # tts转换
        with gr.Row() as tts_row:
            with gr.Column():
                # 展示玄机音色
                voice_type = gr.Dropdown(['wanqing', 'x2_M02', 'xiaoming'], label='玄机音色', value='x2_M02')
                voice_speed = gr.Number(label='玄机音速', value=60)
                '''
                # 展示腾讯音色
                session_id = gr.Textbox(label='音频id')
                voice_type = gr.Number(label='腾讯音色', value=101031)
                tts_btn = gr.Button("生成语音")
                '''
            with gr.Column():
                # 创建一个音频组件，初始不播放任何音频
                audio = gr.Audio(label='音频', value=None)
                wav_file_name = gr.Textbox(label='音频路径', lines=3)
                tts_btn = gr.Button("生成语音")

        tts_btn.click(asyc_batchTxt2Wav, inputs=[output_txt_array, voice_type, voice_speed, novel],
                      outputs=[audio, wav_file_name])

        # asr识别
        '''
            1、需要对srt时间轴进行校准
        '''
        with gr.Row() as asr_row:
            # asr生成
            asr_btn = gr.Button("ASR识别")
            asr_output = gr.Textbox(label='ASR识别结果', lines=3)
            srt_file_path = gr.Textbox(label='srt文件路径', lines=1)
        asr_btn.click(asr_recog, inputs=[wav_file_name, novel], outputs=[asr_output, srt_file_path])

        # 分镜切分
        with gr.Row() as srt_correct_row:
            split_story_btn = gr.Button("分镜切分")
            split_story_output = gr.Textbox(label='分镜切分结果', lines=3)
        split_story_btn.click(split_story_srt, inputs=[novel], outputs=[split_story_output])

        # 分镜生成
        '''
            1、需要对srt文件进行分割，不要超过模型输入范围
            2、支持可配置，按照1分钟
        '''
        with gr.Row() as story_board_row:
            with gr.Column():
                llm_model = gr.Dropdown(['qwen-plus','kimi'], label='llm模型',
                                        value='kimi')
                llm_key = gr.Textbox(label='apikey', lines=1)
                story_board_btn = gr.Button("生成分镜")
                story_board_size = gr.Number(label='分镜个数')
                except_index = gr.Json(label='异常分镜')
                retry_button = gr.Button("重试")
            with gr.Column():
                story_board_prompt_head = gr.Textbox(label='prompt_head', lines=2,
                                                     value='针对所提供的SRT文件中的每一句台词，叙述者一个身处悬疑故事中的少年，请创作相应的动漫风格悬疑气氛图片描述，确保每张图片聚焦单一主体人物，以冷暗色调的背景来增强氛围感。请确保描述内容避开血腥、暴力元素及任何敏感词汇，维持画面的和谐美感，并与视频剧本的整体风格保持连贯。请按照如下格式输出：原文序列号-描述，确保序列号与SRT原文对应,，不要输出无关信息。')
                story_board_prompt_user = gr.Textbox(label='prompt_user', lines=1, value='以下是srt文件:')
                story_board_step = gr.Number(label='步数', value=5)
                story_board_output = gr.Textbox(label='分镜结果', lines=3)
        story_board_btn.click(gen_story_board,
                              inputs=[story_board_prompt_head, story_board_prompt_user, split_story_output, llm_model,
                                      llm_key, story_board_step, novel],
                              outputs=[story_board_output, story_board_size, except_index])
        retry_button.click(retry_stroy_board,
                           inputs=[story_board_prompt_head, story_board_prompt_user, llm_model, llm_key, novel],
                           outputs=[story_board_output, story_board_size, except_index])

        # 文生图
        with gr.Row() as prompt_2_pic_row:
            with gr.Column():
                # prompt_2_pic_prompt_head = gr.Textbox(label='prompt_head', lines=2, value='请根据以下每一段描述分别生成一张动漫风格的悬疑氛围图片：画面中只有一个主体人物，背景应与人物形成对比，增强悬疑感。避免血')
                prompt_2_pic_btn = gr.Button("文生图")
                # 创建一个画廊组件，用于显示图片列表
                # image_gallery = gr.Gallery(label="图片画廊")
                image_list = gr.Json(label="图片列表")
        prompt_2_pic_btn.click(batch_painting_v2, inputs=[novel], outputs=[image_list])