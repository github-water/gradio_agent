import os

class sysConfig:
    SERVER_PORT = 8080
    SERVER_HOST = '127.0.0.1'
    # asr模型路径
    ASR_MODEL_DIR = 'C:/Users/11105152/.cache/modelscope/hub/'
    # 临时文件路径
    data_parent_path = 'D:/python/github/gradio_agent/tmp_data/'


def get_model_path(model_name):
    return os.path.join(sysConfig.ASR_MODEL_DIR, model_name)