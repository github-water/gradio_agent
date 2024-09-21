import json
import types
from tencentcloud.common import credential
from tencentcloud.common.profile.client_profile import ClientProfile
from tencentcloud.common.profile.http_profile import HttpProfile
from tencentcloud.common.exception.tencent_cloud_sdk_exception import TencentCloudSDKException
from tencentcloud.hunyuan.v20230901 import hunyuan_client, models
from config.client_auth_config import TTS_TX_CONFIG

cred = credential.Credential(TTS_TX_CONFIG.SECRECT_ID, TTS_TX_CONFIG.SECRECT_PAINT_KEY)


def submit_hunyuan_image(prompt):
    try:
        # 实例化一个http选项，可选的，没有特殊需求可以跳过
        httpProfile = HttpProfile()
        httpProfile.endpoint = "hunyuan.tencentcloudapi.com"

        # 实例化一个client选项，可选的，没有特殊需求可以跳过
        clientProfile = ClientProfile()
        clientProfile.httpProfile = httpProfile
        # 实例化要请求产品的client对象,clientProfile是可选的
        client = hunyuan_client.HunyuanClient(cred, "ap-guangzhou", clientProfile)

        # 实例化一个请求对象,每个接口都会对应一个request对象
        req = models.SubmitHunyuanImageJobRequest()
        params = {
            "Prompt": prompt,
            "Num": 1
        }
        req.from_json_string(json.dumps(params))

        # 返回的resp是一个SubmitHunyuanImageJobResponse的实例，与请求对象对应
        resp = client.SubmitHunyuanImageJob(req)
        job_id = resp.to_json_string()['Response']['JobId']
        # 输出json格式的字符串回包
        print(resp.to_json_string())
        return job_id
    except TencentCloudSDKException as err:
        print(err)


