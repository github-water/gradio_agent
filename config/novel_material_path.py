import os
from config.sys_config import sysConfig

def tts_dir(id):
    path = sysConfig.data_parent_path + str(id) + '/' + 'tts/'
    ensure_dir_exists(path)
    return path


def srt_dir(id):
    path = sysConfig.data_parent_path + str(id) + '/' + 'srt/'
    ensure_dir_exists(path)
    return path

def pic_dir(id):
    path = sysConfig.data_parent_path + str(id) + '/' + 'pic/'
    ensure_dir_exists(path)
    return path

def prompt_dir(id):
    path = sysConfig.data_parent_path + str(id) + '/' + 'prompt/'
    ensure_dir_exists(path)
    return path

def tmp_dir():
    return sysConfig.data_parent_path

def ensure_dir_exists(path):
    if not os.path.exists(path):
        os.makedirs(path)
        print(f"目录 {path} 被创建.")