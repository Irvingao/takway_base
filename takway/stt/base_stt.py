#!/usr/bin/env python3
# -*- coding: utf-8 -*-
import json
import wave
import io
import os
import logging
from ..common_utils import decode_str2bytes

class STTBase:
    def __init__(self, RATE=16000, cfg_path=None, debug=False):
        self.RATE = RATE
        self.debug = debug
        self.asr_cfg = self.parse_json(cfg_path)
        
    def parse_json(self, cfg_path):
        cfg = None
        self.hotwords = None
        if cfg_path is not None:
            with open(cfg_path, 'r', encoding='utf-8') as f:
                cfg = json.load(f)
            self.hotwords = cfg.get('hot_words', None)
            logging.info(f"load STT config file: {cfg_path}")
            logging.info(f"Hot words: {self.hotwords}")
        else:
            logging.warning("No STT config file provided, using default config.")
        return cfg

    def add_hotword(self, hotword):
        """add hotword to list"""
        if self.hotwords is None:
            self.hotwords = ""
        if isinstance(hotword, str):
            self.hotwords = self.hotwords + " " + "hotword"
        elif isinstance(hotword, (list, tuple)):
            # 将hotwords转换为str，并用空格隔开
            self.hotwords = self.hotwords + " " + " ".join(hotword)
        else:
            raise TypeError("hotword must be str or list")

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
    
    def text_postprecess(self, result, data_id='text'):
        """postprecess recognized result."""
        text = result[data_id]
        if isinstance(text, list):
            text = ''.join(text)
        return text.replace(' ', '')

    def recognize(self, audio_data, queue=None):
        """recognize audio data to text"""
        pass
