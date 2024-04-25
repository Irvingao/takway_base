import os
import torch
import numpy as np
import soundfile as sf
#bert-vits
from takway.tts.bert_vits.infer import get_net_g, infer
from takway.tts.bert_vits import utils

latest_version = "2.4"

class TextToSpeechV2:
    def __init__(self, 
                 model_path="./bert_vits_model", 
                 device='cuda',
                 ):
        self.model_path = model_path
        self.device = torch.device(device)
        self.hps = utils.get_hparams_from_file(os.path.join(model_path, 'config.json'))
        self.net_g = self._model_init(model_path)

    def _model_init(self,mo):
        # 若config.json中未指定版本则默认为最新版本
        version = self.hps.version if hasattr(self.hps, "version") else latest_version
        net_g = get_net_g(
            model_path=os.path.join(self.model_path, 'G_3000.pth'), version=version, device=self.device, hps=self.hps
        )
        return net_g
    
    def generate_audio(
            self,
            slices,
            sdp_ratio,
            noise_scale,
            noise_scale_w,
            length_scale,
            speaker,
            language,
            reference_audio,
            emotion,
            style_text,
            style_weight,
            skip_start=False,
            skip_end=False,
        ):
        audio_list = []
        with torch.no_grad():
            for idx, piece in enumerate(slices):
                skip_start = (idx != 0) and skip_start
                skip_end = (idx != len(slices) - 1) and skip_end
                audio = infer(
                    piece,
                    reference_audio=reference_audio,
                    emotion=emotion,
                    sdp_ratio=sdp_ratio,
                    noise_scale=noise_scale,
                    noise_scale_w=noise_scale_w,
                    length_scale=length_scale,
                    sid=speaker,
                    language=language,
                    hps=self.hps,
                    net_g=self.net_g,
                    device=self.device,
                    style_text=style_text,
                    style_weight=style_weight,
                    skip_start=skip_start,
                    skip_end=skip_end,
                )
                audio_list.append(audio)
        return audio_list

    def synthesize(
            self,
            text,
            sdp_ratio,
            noise_scale,
            noise_scale_w,
            length_scale,
            speaker,
            language,
            reference_audio,
            emotion,
            style_text,
            style_weight,
        ):
        audio = self.generate_audio(
            text,
            sdp_ratio,
            noise_scale,
            noise_scale_w,
            length_scale,
            speaker,
            language,
            reference_audio,
            emotion,
            style_text,
            style_weight,
            )
        audio_concat = np.concatenate(audio)
        return self.hps.data.sampling_rate, audio_concat

    def save_audio(self, audio, sample_rate, file_name='output_file.wav'):
            sf.write(file_name, audio, samplerate=sample_rate)
            print(f"VITS Audio saved to {file_name}")

if __name__ == '__main__':
    tts = TextToSpeechV2(device="cpu")
    sr, audio = tts.synthesize('你好呀,我不知道该怎么告诉你这件事，但是我真的很需要你。',0.2,0.6,0.8,1.0,"test","ZH",None,"Happy","",0)
    tts.save_audio(audio, sr)
    