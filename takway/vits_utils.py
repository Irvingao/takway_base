import os
import numpy as np
import torch
from torch import LongTensor
import soundfile as sf
# vits
from .vits import utils, commons
from .vits.models import SynthesizerTrn
from .vits.text import text_to_sequence

def tts_model_init(device='cuda'):
    # hps_ms = utils.get_hparams_from_file(os.path.join(model_path, 'config.json'))
    hps_ms = utils.get_hparams_from_file('vits_model/config.json')
    net_g_ms = SynthesizerTrn(
        len(hps_ms.symbols),
        hps_ms.data.filter_length // 2 + 1,
        hps_ms.train.segment_size // hps_ms.data.hop_length,
        n_speakers=hps_ms.data.n_speakers,
        **hps_ms.model)
    net_g_ms = net_g_ms.eval().to(device)
    speakers = hps_ms.speakers
    # utils.load_checkpoint(os.path.join(model_path, 'G_953000.pth'), net_g_ms, None)
    utils.load_checkpoint('vits_model/G_953000.pth', net_g_ms, None)
    return hps_ms, net_g_ms, speakers

class TextToSpeech:
    def __init__(self, 
                 model_path="./vits_model", 
                 device='cuda',
                 RATE=22050,
                 debug=False,
                 ):
        self.debug = debug
        self.RATE = RATE
        self.device = torch.device(device)
        self.limitation = os.getenv("SYSTEM") == "spaces"  # 在huggingface spaces中限制文本和音频长度
        self.hps_ms, self.net_g_ms, self.speakers = self._tts_model_init(model_path)
        
    def _tts_model_init(self, model_path):
        # hps_ms = utils.get_hparams_from_file(os.path.join(model_path, 'config.json'))
        hps_ms = utils.get_hparams_from_file('vits_model/config.json')
        net_g_ms = SynthesizerTrn(
            len(hps_ms.symbols),
            hps_ms.data.filter_length // 2 + 1,
            hps_ms.train.segment_size // hps_ms.data.hop_length,
            n_speakers=hps_ms.data.n_speakers,
            **hps_ms.model)
        net_g_ms = net_g_ms.eval().to(self.device)
        speakers = hps_ms.speakers
        # utils.load_checkpoint(os.path.join(model_path, 'G_953000.pth'), net_g_ms, None)
        utils.load_checkpoint('vits_model/G_953000.pth', net_g_ms, None)
        if self.debug:
            print("Model loaded.")
        return hps_ms, net_g_ms, speakers

    def _get_text(self, text):
        text_norm, clean_text = text_to_sequence(text, self.hps_ms.symbols, self.hps_ms.data.text_cleaners)
        if self.hps_ms.data.add_blank:
            text_norm = commons.intersperse(text_norm, 0)
        text_norm = LongTensor(text_norm)
        return text_norm, clean_text

    def _preprocess_text(self, text, language):
        if language == 0:
            return f"[ZH]{text}[ZH]"
        elif language == 1:
            return f"[JA]{text}[JA]"
        return text

    def _generate_audio(self, text, speaker_id, noise_scale, noise_scale_w, length_scale):
        import time
        start_time = time.time()
        stn_tst, clean_text = self._get_text(text)
        with torch.no_grad():
            x_tst = stn_tst.unsqueeze(0).to(self.device)
            x_tst_lengths = LongTensor([stn_tst.size(0)]).to(self.device)
            speaker_id = LongTensor([speaker_id]).to(self.device)
            audio = self.net_g_ms.infer(x_tst, x_tst_lengths, sid=speaker_id, noise_scale=noise_scale, noise_scale_w=noise_scale_w,
                                        length_scale=length_scale)[0][0, 0].data.cpu().float().numpy()
        if self.debug:
            print(f"Synthesis time: {time.time() - start_time} s")
        return audio
    
    def synthesize(self, text, language, speaker_id, noise_scale, noise_scale_w, length_scale, save_audio=False, return_bytes=False):
        if not len(text):
            return "输入文本不能为空！", None
        text = text.replace('\n', ' ').replace('\r', '').replace(" ", "")
        if len(text) > 100 and self.limitation:
            return f"输入文字过长！{len(text)}>100", None
        text = self._preprocess_text(text, language)
        audio = self._generate_audio(text, speaker_id, noise_scale, noise_scale_w, length_scale)
        if self.debug or save_audio:
            self.save_audio(audio, self.RATE, 'output_file.wav')
        if return_bytes:
            audio = self.convert_numpy_to_bytes(audio)
        return self.RATE, audio

    def convert_numpy_to_bytes(self, audio_data):
        if isinstance(audio_data, np.ndarray):
            if audio_data.dtype == np.dtype('float32'):
                audio_data = np.int16(audio_data * np.iinfo(np.int16).max)
            audio_data = audio_data.tobytes()
            return audio_data
        else:
            raise TypeError("audio_data must be a numpy array")

    def save_audio(self, audio, sample_rate, file_name='output_file.wav'):
        sf.write(file_name, audio, samplerate=sample_rate)
        print(f"VITS Audio saved to {file_name}")
        
    

if __name__ == '__main__':
    tts = TextToSpeech(device='cuda')  # 初始化，设定使用的设备
    sr, audio = tts.synthesize('你好呀,我不知道该怎么告诉你这件事，但是我真的很需要你。', 0, 103, 0.1, 0.668, 1.2)  # 生成语音
    tts.save_audio(audio, sr)  # 保存语音文件
    

    
    

