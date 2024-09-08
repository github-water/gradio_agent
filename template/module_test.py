import gradio as gr

def process_input(text):
    return text.upper(), text.lower()

# 上下文管理器
with gr.Blocks() as demo:
    # 行管理器
    with gr.Row():
        #列管理器
        with gr.Column():
            # 第一个文本输入框
            input1 = gr.Textbox(label="Enter text")
            # 第一个文本输出框
            output1 = gr.Textbox(label="Uppercase")
        with gr.Column():
            # 第二个文本输入框
            input2 = gr.Textbox(label="Enter more text")
            # 第二个文本输出框
            output2 = gr.Textbox(label="Lowercase")
    # 将输入和输出连接到 process_input 函数
    output1.change(fn=process_input, inputs=input1, outputs=output1)
    output2.change(fn=process_input, inputs=input2, outputs=output2)

# 启动界面
demo.launch()