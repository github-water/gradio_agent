import json
from tencentcloud.common import credential
from tencentcloud.common.profile.client_profile import ClientProfile
from tencentcloud.common.profile.http_profile import HttpProfile
from tencentcloud.common.exception.tencent_cloud_sdk_exception import TencentCloudSDKException
from tencentcloud.tts.v20190823 import tts_client, models
from utils.media_util import writeWav
from config.client_auth_config import TTS_TX_CONFIG


def txt2Wav(txt, SessionId, VoiceType):
    if len(txt) > 100:
        return None
    try:
        cred = credential.Credential(TTS_TX_CONFIG.SECRECT_ID, TTS_TX_CONFIG.SECRECT_KEY)
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
            "SessionId": SessionId,
            "VoiceType":VoiceType
        }
        req.from_json_string(json.dumps(params))
        # 返回的resp是一个TextToVoiceResponsmodel = models.TextToVoiceResponse()e的实例，与请求对象对应
        resp = client.TextToVoice(req)
        # 写入wav文件
        return writeWav(resp.Audio, resp.SessionId)
    except TencentCloudSDKException as err:
        print(err)


def batchTxt2Wav(text, SessionId, VoiceType):
    # 计算文本长度
    text_length = len(text)

    file_name_list=[]
    # 循环处理每个文本段
    for i in range(0, text_length, 100):
        # 截取文本段，最多100个字符
        chunk = text[i:i + 100]
        file_name = txt2Wav(chunk, SessionId+"_"+i, VoiceType)
        file_name_list.append(file_name)
    return "，".join(file_name_list)

if __name__ == "__main__":
    txt2Wav("你好呀","tts-002", 101031)

