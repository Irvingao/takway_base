#!/usr/bin/env python3
# -*- coding: utf-8 -*-
# ####################################################### #
# FunAutoSpeechRecognizer: https://github.com/alibaba-damo-academy/FunASR
# ####################################################### #
import time
import numpy as np
from funasr import AutoModel

from takway.stt.base_stt import STTBase

class FunAutoSpeechRecognizer(STTBase):
    def __init__(self, 
                 model_path="paraformer-zh-streaming", 
                 device="cuda", 
                 RATE=16000, 
                 cfg_path=None, 
                 debug=False, 
                 chunk_ms=480, 
                 encoder_chunk_look_back=4, 
                 decoder_chunk_look_back=1, 
                 **kwargs):
        super().__init__(RATE=RATE, cfg_path=cfg_path, debug=debug)
        
        self.asr_model = AutoModel(model=model_path, device=device, **kwargs)
        
        self.encoder_chunk_look_back = encoder_chunk_look_back #number of chunks to lookback for encoder self-attention
        self.decoder_chunk_look_back = decoder_chunk_look_back #number of encoder chunks to lookback for decoder cross-attention
        
        #[0, 8, 4] 480ms, [0, 10, 5] 600ms
        if chunk_ms == 480:
            self.chunk_size = [0, 8, 4] 
        elif chunk_ms == 600:
            self.chunk_size = [0, 10, 5]
        else:
            raise ValueError("`chunk_ms` should be 480 or 600, and type is int.")
        self.chunk_partial_size = self.chunk_size[1] * 960 
        self.audio_cache = None
        self.asr_cache = {}
        
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
        
        if isinstance(audio_data, bytes):
            audio_data = np.frombuffer(audio_data, dtype=np.int16)
        else:
            raise TypeError(f"audio_data must be bytes, str or io.BytesIO, but got {type(audio_data)}")
        return audio_data
    
    def recognize(self, audio_data):
        """recognize audio data to text"""
        audio_data = self.check_audio_type(audio_data)
        result = self.asr_model.generate(input=audio_data, 
                     batch_size_s=300, 
                     hotword=self.keywords)
        print(result)
        return result

    def streaming_recognize(self, 
                            audio_data, 
                            is_end=False, 
                            auto_det_end=False):
        """recognize partial result
        
        Args:
            audio_data: bytes or numpy array, partial audio data
            is_end: bool, whether the audio data is the end of a sentence
            auto_det_end: bool, whether to automatically detect the end of a audio data
        """
        text_dict = dict(text=[], is_end=is_end)
        
        audio_data = self.check_audio_type(audio_data)
        if self.audio_cache is None:
            self.audio_cache = audio_data
        else:
            print(f"audio_data: {audio_data.shape}, audio_cache: {self.audio_cache.shape}")
            if self.audio_cache.shape[0] > 0:
                self.audio_cache = np.concatenate([self.audio_cache, audio_data], axis=0)
        
        if not is_end and self.audio_cache.shape[0] < self.chunk_partial_size:
            return text_dict
        
        total_chunk_num = int((len(self.audio_cache)-1)/self.chunk_partial_size)
        
        if is_end:
            # if the audio data is the end of a sentence, \
            # we need to add one more chunk to the end to \
            # ensure the end of the sentence is recognized correctly.
            auto_det_end = True
        
        if auto_det_end:
            total_chunk_num += 1

        print(f"chunk_size: {self.chunk_size}, chunk_stride: {self.chunk_partial_size}, total_chunk_num: {total_chunk_num}, len: {len(self.audio_cache)}")
        for i in range(total_chunk_num):
            if auto_det_end:
                is_end = i == total_chunk_num - 1
            print(f"cut part: {i*self.chunk_partial_size}:{(i+1)*self.chunk_partial_size}, is_end: {is_end}")
            
            t_stamp = time.time()
            
            speech_chunk = self.audio_cache[i*self.chunk_partial_size:(i+1)*self.chunk_partial_size].copy() # 创建一个可写副本
            assert speech_chunk.flags.writeable == True, "speech_chunk should be a writable array"
            
            res = self.asr_model.generate(input=speech_chunk, cache=self.asr_cache, is_final=is_end, chunk_size=self.chunk_size, encoder_chunk_look_back=self.encoder_chunk_look_back, decoder_chunk_look_back=self.decoder_chunk_look_back)
            
            # print(f"asr_cache: {self.asr_cache.flags.writeable}")
            # self.asr_cache['encoder']['feats'].flags.writeable
            # self.asr_cache['encoder']
            
            print(f"streaming res: {res}")
            text_dict['text'].append(self.text_postprecess(res[0], data_id='text'))
            
            print(f"each chunk time: {time.time()-t_stamp}")
            
        if is_end:
            self.audio_cache = None
            self.asr_cache = {}
        else:
            self.audio_cache = self.audio_cache[total_chunk_num*self.chunk_partial_size:] # cut the processed part from audio_cache
        
        # print(f"text_dict: {text_dict}")
        return text_dict


if __name__ == '__main__':
    from takway.audio_utils import BaseAudio
    rec = BaseAudio(input=True)
    
    # return_type = 'bytes'
    file_path = 'my_recording.wav'
    data = rec.load_audio_file(file_path)
        
    asr = FunAutoSpeechRecognizer()
    
    # asr.recognize(data)
    total_chunk_num = int((len(data)-1)/rec.CHUNK+1)
    print(f"total_chunk_num: {total_chunk_num}")
    for i in range(total_chunk_num):
        is_end = i == total_chunk_num - 1
        speech_chunk = data[i*rec.CHUNK:(i+1)*rec.CHUNK]
        text_dict = asr.streaming_recognize(speech_chunk, is_end)
    '''
    asr.streaming_recognize(data, auto_det_end=True)
    '''
    