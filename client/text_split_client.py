import re

import gradio as gr

def split_text_array(text, split_size=600):
    segments = []
    start = 0
    while start < len(text):
        tmp_text = text[start:start+split_size]
        end = start + split_size
        # 寻找最接近的结束标点符号
        relative_index = find_last_punctuation_index(tmp_text)
        if relative_index > -1:
            last_punctuation_index = relative_index + start
            end = min(last_punctuation_index, end)
        segments.append(text[start:end].strip())
        print("start: {}, end: {}".format(start, end))
        start = end
    return segments

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


def split_text_by_mark(input_text, max_length):
    # 去除空格和换行
    cleaned_text = (input_text
                    .replace(" ", "")
                    .replace("\n", "")
                    )
    # 按照输入的大小截取文本
    cleaned_text = cleaned_text[:max_length]
    truncate_index = find_last_punctuation_index(cleaned_text)
     #如果找到了句号或逗号，则更新截取后的文本
    if truncate_index > -1:
        cleaned_text = cleaned_text[:truncate_index]

    return cleaned_text, len(cleaned_text)


# 创建agent-文本截取
text_split_interface = gr.Interface(
    fn=process_text,
    inputs=[gr.Textbox(lines=2, placeholder="Enter text here...", label="input_text"), gr.Number(label="Max Length")],
    outputs=[gr.Textbox(label='output_text'), gr.Number(label='output_size')]
)

