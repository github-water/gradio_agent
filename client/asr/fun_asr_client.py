from funasr import AutoModel

from utils.subtitle_utils import generate_srt

class asr_client():
    def __init__(self, funasr_model):
        self.funasr_model = funasr_model
        self.GLOBAL_COUNT = 0


    def recog(self, audio_path):
        rec_result = self.funasr_model.generate(audio_path,
                                                return_spk_res=True,
                                                return_raw_text=True,
                                                is_final=True,
                                                pred_timestamp=self.lang=='en',
                                                en_post_proc=self.lang=='en',
                                                cache={})
        res_srt = generate_srt(rec_result[0]['sentence_info'])
        return res_srt, rec_result[0]['sentence_info']


if __name__ == '__main__':
    funasr_model = AutoModel(model="E:/modelscope/hub/iic/speech_seaco_paraformer_large_asr_nat-zh-cn-16k-common-vocab8404-pytorch",
                             model_revision="v2.0.4",
                             vad_model="E:/modelscope/hub/damo/speech_fsmn_vad_zh-cn-16k-common-pytorch",
                             punc_model="E:/modelscope/hub/damo/punc_ct-transformer_zh-cn-common-vocab272727-pytorch",
                             spk_model="E:/modelscope/hub/damo/speech_campplus_sv_zh-cn_16k-common"
                             )

    file_path = 'E:/github/gradio_agent/tmp_data/tts/001.wav'
    client = asr_client(funasr_model)
    client.lang = 'zh'
    srt_file, sentence_info = client.recog(file_path)
    print(srt_file)