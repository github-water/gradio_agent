import dashscope
from dashscope import Generation


def call_qwen_model(key=None,
                    model="qwen_plus",
                    user_content="如何做西红柿炖牛腩？",
                    system_content=None):
    dashscope.api_key = key
    if system_content is not None and len(system_content.strip()):
        messages = [
            {'role': 'system', 'content': system_content},
            {'role': 'user', 'content': user_content}
      ]
    else:
        messages = [
            {'role': 'user', 'content': user_content}
      ]
    responses = Generation.call(model,
                                messages=messages,
                                result_format='message',  # 设置输出为'message'格式
                                stream=False, # 设置输出方式为流式输出
                                incremental_output=False  # 增量式流式输出
                                )
    print(responses)
    return responses['output']['choices'][0]['message']['content']


if __name__ == '__main__':
    api_key = 'sk-453b2ab98dc84f9ebe7ffed86fe24c05'
    model = "qwen-plus"
    system_content = "请审阅以下视频脚本，每5秒生成一个段落。每个合并后的段落应聚焦于一个清晰的主题或场景，并保持整体的连贯性和一致性。确保每个段落都包含足够的细节，以便为文生图提供明确的指导。请在输出中明确标注每个段落的开始和结束时间，格式为：[开始时间-结束时间]"
    user_content = '以下是具体的srt'
    srt_text = '这是待裁剪的srt：0 00:00:00,50 --> 00:00:04,50 我们村的女子结婚前夜必须去村后的山庙裸睡一夜才能出家。1 00:00:04,230 --> 00:00:05,610 只有把初夜交给山神，2 00:00:05,690 --> 00:00:07,230 这样娘家才会平平安安。3 00:00:07,450 --> 00:00:08,730 如果违背这条村规，4 00:00:08,870 --> 00:00:09,870 娘家必有横祸。'
    call_qwen_model(api_key, model, user_content + '\n' + srt_text, system_content)