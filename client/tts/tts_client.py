import json
import os

from tencentcloud.common import credential
from tencentcloud.common.profile.client_profile import ClientProfile
from tencentcloud.common.profile.http_profile import HttpProfile
from tencentcloud.common.exception.tencent_cloud_sdk_exception import TencentCloudSDKException
from tencentcloud.tts.v20190823 import tts_client, models

from config.media_format_suffix import MediaFormatSuffix
from utils.media_util import base2Wav, merge_audio_files,rm_tmp_files
from config.client_auth_config import TTS_TX_CONFIG
from client.text_split_client import split_text_array


def txt2Wav(txt,
            session_id,
            voice_type,
            speed,
            file_path):
    if len(txt) > 150:
        print("txt2Wav: txt长度超过150，分段处理")
        return None
    try:
        cred = credential.Credential(TTS_TX_CONFIG.SECRECT_ID, TTS_TX_CONFIG.SECRECT_TTS_KEY)
        # 实例化一个http选项，可选的，没有特殊需求可以跳过
        httpProfile = HttpProfile()
        httpProfile.endpoint = "tts.tencentcloudapi.com"

        # 实例化一个client选项，可选的，没有特殊需求可以跳过
        clientProfile = ClientProfile()
        clientProfile.httpProfile = httpProfile
        # 实例化要请求产品的client对象,clientProfile是可选的
        client = tts_client.TtsClient(cred, "ap-nanjing", clientProfile)

        # 实例化一个请求对象,每个接口都会对应一个request对象
        req = models.TextToVoiceRequest()
        params = {
            "Text": txt,
            "SessionId": session_id,
            "VoiceType": voice_type,
            "speed": speed
        }
        req.from_json_string(json.dumps(params))
        # 返回的resp是一个TextToVoiceResponsmodel = models.TextToVoiceResponse()e的实例，与请求对象对应
        resp = client.TextToVoice(req)
        # 写入wav文件
        return base2Wav(resp.Audio, file_path)
    except TencentCloudSDKException as err:
        print(f'TencentCloudSDKException: {err}')
        return None


def batchTxt2Wav(text, SessionId, VoiceType, speed, file_path):
    # 计算文本长度
    split_size_in = 140
    output_txt_array_in = split_text_array(text, split_size_in)
    size = len(output_txt_array_in)
    suffix = '.' + os.path.splitext(file_path)[1]
    tmp_file_paths = []
    # 循环生成音频文件
    for i in range(size):
        tmp_file_path = os.path.splitext(file_path)[0] + '_' + 'tmp' + '_' + str(i) + suffix
        path = txt2Wav(output_txt_array_in[i], SessionId + "_" + str(i), VoiceType, speed, tmp_file_path)
        if path:
            tmp_file_paths.append(path)
    # 合并临时音频文件
    merge_audio_files(tmp_file_paths, file_path)
    # 删除临时文件
    rm_tmp_files(tmp_file_paths)
    return file_path

if __name__ == "__main__":
    batchTxt2Wav("我是个独居女孩，雨天夜晚11点，突然来了个陌生电话，你是triplex牌照的车主吗？你的车窗没关，雨下大了，我连声道谢，准备下楼，却被工作绊住了。10分钟后，电话又响了，接通的瞬间。电话那头是另一个男的在说话，等会儿你这么跟他接着换回了原来的人。喂，你怎么还不下来呢？车都叫坏了。我突然觉得事情好像有点不对劲，怕怕温馨提醒你，正文开始电话又响了，还是那个号码？我接通打算解释一下，可接通的一瞬间，电话那头是另外一个男人的声音，等会儿你这么跟他那头的声音戛然而止，怎么会有男人半晌换成了之前那个女生。喂，你怎么还不下来呢？车都浇坏了。通话里的背景音仍然是哗啦的雨声。这次他的声音似乎带着些不耐烦。他还在我的车旁客厅的表真咔哒响距离第一通电话已经过了十多分钟了，而且听声音车旁似乎不止他一个人，我突然莫名觉得有点不对劲，有什么违和的东西扯住了我一根神经，沉下心翻出物业的号码，打算叫物业帮我去看看什么情况，一边应付电话里的人哦，我刚找到钥匙正要下去呢。试探性的问，对面外面雨不小吧，你一个女孩子这么晚在外不安全吧。编辑好，给物业的短信点击了发送此时电话那头的雨声短暂的响了一下，就像是被人捂住了话筒。, 在说话时，电话那头的女生有点怪异啊，我在这楼下等人恰好看见你的车窗没关这么长时间, ","tts-002", 101031, "D:/python/github/gradio_agent/tmp_data/test.wav")

