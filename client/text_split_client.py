import re

import gradio as gr

# 定义处理文本的函数
def process_text(input_text, max_length):
    # 去除空格和换行
    cleaned_text = input_text.replace(" ", "").replace("\n", "")
    # 按照输入的大小截取文本
    truncated_text = cleaned_text[:max_length]
    truncate_index = find_last_punctuation_index(truncated_text)
     #如果找到了句号或逗号，则更新截取后的文本
    if truncate_index > -1:
        truncated_text = truncated_text[:truncate_index]

    return truncated_text, len(truncated_text)


def find_last_punctuation_index(text):
    # 正则表达式匹配所有标点符号
    pattern = r'[.,;:!?"\'-。，]'

    # 使用re.finditer()查找所有匹配的标点符号
    matches = list(re.finditer(pattern, text))

    # 如果没有找到任何标点符号，返回-1
    if not matches:
        return -1

    # 返回最后一个匹配的索引
    return matches[-1].end()


# 创建agent-文本截取
text_split_interface = gr.Interface(
    fn=process_text,
    inputs=[gr.Textbox(lines=2, placeholder="Enter text here...", label="input_text"), gr.Number(label="Max Length")],
    outputs=[gr.Textbox(label='output_text'), gr.Number(label='output_size')]
)

