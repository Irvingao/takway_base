#!/usr/bin/env python3
# -*- coding: utf-8 -*-
# ####################################################### #
# VOSKAutoSpeechRecognizer
# ####################################################### #
import json
import wave
import io
import os
from vosk import Model, KaldiRecognizer, SetLogLevel
from .base_stt import STTBase
from ..common_utils import decode_str2bytes

class VOSKAutoSpeechRecognizer(STTBase):
    def __init__(self, model_path="vosk-model-small-cn-0.22", RATE=16000, cfg_path=None, efficent_mode=True, debug=False):
        super().__init__(self, model_path=model_path, RATE=RATE, cfg_path=cfg_path, debug=debug)
        self.asr_model = AutoModel(model="paraformer-zh-streaming")
        
        self.apply_asr_config(self.asr_cfg)
    
    def recognize_keywords(self, audio_data, partial_size=None, queue=None):
        """recognize keywords in audio data"""
        audio_data = self.check_audio_type(audio_data)
        if partial_size is None:
            rec_result = self.recognize(audio_data, queue)
            rec_text = self.result_postprecess(rec_result)
        else:
            rec_result = self.partial_recognize(audio_data, partial_size, queue)
            rec_text = self.result_postprecess(rec_result, 'partial')
        print(f"rec_text: {rec_text}")
        if rec_text != '':
            print(f"rec_text: {rec_text}")
        if any(keyword in rec_text for keyword in self.keywords):
            print("Keyword detected.")
            return True, rec_text
        else:
            return False, None

    def recognize(self, audio_data, queue=None):
        """recognize audio data to text"""
        audio_data = self.check_audio_type(audio_data)
        self.asr.AcceptWaveform(audio_data)
        result = json.loads(self.asr.FinalResult())
        # TODO: put result to queue
        return result

    def partial_recognize(self, audio_data, partial_size=1024, queue=None):
        """recognize partial result"""
        audio_data = self.check_audio_type(audio_data)
        text_dict = dict(
            text=[],
            partial=[],
            final=[],
            is_end=False)
        # 逐个分割音频数据进行识别
        for i in range(0, len(audio_data), partial_size):
            # print(f"partial data: {i} - {i+partial_size}")
            data = audio_data[i:i+partial_size]
            if len(data) == 0:
                break
            if self.asr.AcceptWaveform(data):
                result = json.loads(self.asr.Result())
                if result['text'] != '':
                    text_dict['text'].append(result['text'])
                    if queue is not None:
                        queue.put(('stt_info', text_dict))
                    # print(f"text result: {result}")
            else:
                result = json.loads(self.asr.PartialResult())
                if result['partial'] != '':
                    # text_dict['partial'].append(result['partial'])
                    text_dict['partial'] = [result['partial']]
                    if queue is not None:
                        queue.put(('stt_info', text_dict))
                    # print(f"partial result: {result}")
        
        # final recognize
        final_result = json.loads(self.asr.FinalResult())
        if final_result['text'] != '':
            text_dict['final'].append(final_result['text'])
            text_dict['text'].append(final_result['text'])
            
        text_dict['is_end'] = True
        
        print(f"final dict: {text_dict}")
        if queue is not None:
            queue.put(('stt_info', text_dict))
        return text_dict
        

if __name__ == "__main__":
    '''
    wav_file_path = "recording.wav"

    # You can set log level to -1 to disable debug messages
    SetLogLevel(0)

    model = Model(model_path="vosk-model-small-cn-0.22")

    # 调用函数进行录音
    # record_audio(wav_file_path)
    data = record_audio()

    # 调用函数进行音频转写
    result = audio_to_text(data, model)

    print("-------------")
    print(result)
    '''
    from takway.audio_utils import Recorder
    rec = Recorder()
    
    return_type = 'bytes'
    data = rec.record(return_type)
    print(type(data))
        
    asr = AutoSpeechRecognizer()
    # asr.recognize(data)
    asr.add_keyword("你好")
    asr.recognize_keywords(data)