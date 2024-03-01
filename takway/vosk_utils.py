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
from .common_utils import decode_str2bytes

class VOSKAutoSpeechRecognizer:
    def __init__(self, model_path="vosk-model-small-cn-0.22", RATE=16000, cfg_path=None, efficent_mode=True, debug=False):
        self.vosk_model = Model(model_path=model_path)
        self.RATE = RATE
        self.efficent_mode = efficent_mode
        self.debug = debug
        
        self.keywords = []
        
        self.asr_cfg = self.parse_json(cfg_path)
        self.apply_asr_config(self.asr_cfg)

    def parse_json(self, cfg_path):
        if cfg_path is not None:
            print(f"cfg_path: {cfg_path}")
            with open(cfg_path, 'r', encoding='utf-8') as f:
                cfg = json.load(f)
            print(f"cfg: {cfg}")

            self.keywords = cfg.get('hot_words', [])
    
    
    def apply_asr_config(self, config):
        """apply config to asr"""
        
        print('Start to init ASR config.')

        self.asr = KaldiRecognizer(self.vosk_model, self.RATE)
        if self.efficent_mode:
            self.asr.SetMaxAlternatives(0)
            self.asr.SetWords(False)
            self.asr.SetPartialWords(False)
        else:
            self.asr.SetMaxAlternatives(5)
            self.asr.SetWords(True)
            self.asr.SetPartialWords(True)
        if self.debug:
            SetLogLevel(5)
        else:
            SetLogLevel(0)
        '''
        # print(f"keywords: {self.keywords}")
        # print(f"str(self.keywords): {str(self.keywords)}")
        # self.asr.SetGrammar(kw_str)
        # self.asr.SetGrammar('["天王盖地虎", "亲爱的"]')
        '''
        
        print("init ASR config successfully.")
        

    def check_audio_type(self, audio_data):
        """check audio data type and convert it to bytes if necessary."""
        if isinstance(audio_data, bytes):
            pass
        elif isinstance(audio_data, list):
            audio_data = b''.join(audio_data)
        elif isinstance(audio_data, str):
            audio_data = decode_str2bytes(audio_data)
        elif isinstance(audio_data, io.BytesIO):
            wf = wave.open(audio_data, 'rb')
            audio_data = wf.readframes(wf.getnframes())
        else:
            raise TypeError(f"audio_data must be bytes, str or io.BytesIO, but got {type(audio_data)}")
        return audio_data
    
    def result_postprecess(self, result, data_id='text'):
        """postprecess recognized result."""
        text = result[data_id]
        if isinstance(text, list):
            text = ''.join(text)
        return text.replace(' ', '')
    
    def add_keyword(self, keyword):
        """add keyword to list"""
        if isinstance(keyword, str):
            self.keywords.append(keyword)
        elif isinstance(keyword, list):
            self.keywords.extend(keyword)
        else:
            raise TypeError("keyword must be str or list")
    
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