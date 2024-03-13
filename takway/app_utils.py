import os
from flask import Flask, request, Response

from .common_utils import *
from .stt.funasr_utils import FunAutoSpeechRecognizer
from .tts.vits_utils import TextToSpeech
from .llm.sparkapi_utils import SparkChatClient, SparkRolyPlayingClient

from .apps.data_struct import *

import websocket  # 使用websocket_client

import time
import json
import base64
import queue
import threading
import multiprocessing

app = Flask(__name__)

class TakwayApp:
    def __init__(self, 
                 app,
                 stream_timeout=10,
                 device='cuda',
                 debug=False,
                 asr_cfg=None,
                 tts_cfg=None,
                 llm_cfg=None,
                 **kwargs):
        super().__init__(**kwargs)
        
        self.debug = debug
        self.stream_timeout = stream_timeout

        self.asr_cfg = self._init_asr_cfg(asr_cfg)

        self.llm_cfg = self._init_llm_cfg(llm_cfg)
        
        self.tts_cfg = self._init_tts_cfg(tts_cfg)
        
        self.process_init()
    
    def _init_asr_cfg(self, asr_cfg):
        assert 'model_path' in asr_cfg, "asr_cfg must contain model_path"
        asr_cfg['debug'] = self.debug
        return asr_cfg
    
    def _init_llm_cfg(self, llm_cfg):
        assert 'api_key' in llm_cfg, "llm_cfg must contain api_key"
        assert 'api_secret' in llm_cfg, "llm_cfg must contain api_secret"
        llm_cfg['stream_timeout'] = self.stream_timeout
        llm_cfg['debug'] = self.debug
        return llm_cfg
    
    def _init_tts_cfg(self, tts_cfg):
        assert'model_path' in tts_cfg, "tts_cfg must contain model_path"
        assert 'device' in tts_cfg, "tts_cfg must contain device"
        tts_cfg['debug'] = self.debug
        return tts_cfg
    
    def start_app(self, app, port=5000, **kwargs):
        app.run(host='0.0.0.0', port=5000, debug=self.debug, **kwargs)
    
    def process_init(self):
        '''
        init three processes for auto speech recognition, llm chat, and text to speech.
        '''
        # multiprocessing
        manager = multiprocessing.Manager()
        self.stt_queue = manager.Queue()
        self.chat_queue = manager.Queue()
        self.tts_queue = manager.Queue()
        self.api_queue = manager.Queue()
        processes = [multiprocessing.Process(target=self.stream_stt_process),
                    multiprocessing.Process(target=self.stream_chat_process),
                    multiprocessing.Process(target=self.stream_tts_process)]
        for process in processes:
            process.start()

    
    def stream_stt_process(self):
        '''
        流式语音识别进程
        
        流式接收来自前端的语音数据，进行流式语音识别，并将识别的文字结果放入队列中，供后续处理。
        '''
        asr = FunAutoSpeechRecognizer(**self.asr_cfg)
        
        print("stream_stt_process start")
        stt_texts = []
        while True:
            print("wait for stream audio data request")
            data = self.stt_queue.get()
            print("Recieved stream audio data!")
            
            audio_data = decode_str2bytes(data['audio_input'].pop('data'))
            audio_text = self.process_stt(asr, audio_data, is_end=data['is_end'])
            stt_texts.append(audio_text)

            if data.pop('is_bgn'):
                print(f"put wakeup_data to queue.")
                self.tts_queue.put(
                    dict(
                        stream_text=data['character_info'].pop('wakeup_words'),
                        character_info=data['character_info'],
                        is_end=False)
                    )
                
                self.chat_queue.put(
                    dict(
                        character_info=data['character_info'],
                        chat_input=data.pop('chat_input'),
                        init_character=True)
                    )
                print(f"recieved wakeup_data: {data}")
            
            if data.pop('is_end'):
                stt_data = dict(
                    stt_text=''.join(stt_texts),
                    init_character=False,
                    **data)

                if stt_data['stt_text'] == '':
                    print("stt_text is empty")
                else:                 
                    print("put stt_data to queue")
                    self.chat_queue.put(stt_data)
                stt_texts.clear()

    def process_stt(self, asr, audio_data, is_end):
        # 语音识别
        asr_result = asr.streaming_recognize(audio_data, is_end)
        
        # 去掉字符串中的方括号和单引号
        asr_text = asr_result['text']
        asr_text = ' '.join(asr_text)
        asr_str = asr_text.replace("[", "").replace("]", "").replace("'", "").replace(" ", "")
            
        return asr_str
        
    def stream_chat_process(self):
        '''
        大模型对话进程
        
        接收来自语音识别文本结果，送入大模型对话，并将对话结果放入队列中，供后续处理。
        '''
        
        print("stream_chat_process start")
        spark_api = SparkRolyPlayingClient(**self.llm_cfg)

        spark_api.init_websocket()
        
        self.stream_data_queue = queue.Queue()
        
        get_response_thread = threading.Thread(target=self.get_stream_response_thread, args=(spark_api,)).start()
        
        while True:
            try:
                stt_data = self.chat_queue.get(timeout=spark_api.spark_refresh_time)
            except queue.Empty:
                spark_api.init_websocket()
                print(f"wait for {spark_api.spark_refresh_time} seconds and refresh spark websocket")
                continue
            # ##########################################
            print(f"recieved stt_data: {stt_data}")
            # TODO: 处理init_character的信息
            if stt_data.pop('init_character'):
                if stt_data['chat_input']['chat_status'] == 'init':
                    spark_api.clear_character()
                spark_api.set_character(stt_data['character_info']['character_name'], prompt_id=4, gen_sys_pmt=False)
                spark_api.chat_history = stt_data['chat_input']['chat_history']
                # spark_api.chat_history = spark_api.gen_sys_prompt(prompt_id=4) + spark_api.chat_history
                continue
            # ##########################################
            
            # TODO
            if stt_data['stt_text'] != '':
                self.stream_data_queue.put(stt_data)    # put data to queue
                
                print(f"stt_data: {stt_data}")
                
                question = stt_data['stt_text']
                chat_status = stt_data['chat_input'].pop('chat_status')
                
                chat_text = spark_api.gen_user_prompt(spark_api.chat_history, content=question, prompt_id=1)
                print(f"chat_text: {chat_text}")
                
                spark_api.chat(chat_text)   # chat
                
                spark_api.clear_character()

                        
    def get_stream_response_thread(self, spark_api):
        temp_text = ''
        while True:
            stt_data = self.stream_data_queue.get()
            if stt_data is None:
                continue
            while True:
                stream_chat_data = spark_api.stream_answer_queue.get()
                # print(f"stream_chat_data: {stream_chat_data}")
                # TODO
                temp_text += stream_chat_data['text']
                sentence_patch, is_full_sentence = split_chinese_text(temp_text, return_patch=True)
                if is_full_sentence:
                    chat_text = sentence_patch[0]
                    temp_text = temp_text.replace(chat_text, '')
                    
                    chat_data = dict(
                        stream_text=chat_text,
                        is_bgn=stream_chat_data['is_bgn'],
                        is_end=stream_chat_data['is_end'],
                        **stt_data,
                    )
                    self.tts_queue.put(chat_data)
                if stream_chat_data['is_end']:
                    break

    def stream_tts_process(self):
        vits = TextToSpeech(
            **self.tts_cfg
        )
        print("stream_tts_process start")
        while True:
            chat_data = self.tts_queue.get(); bg_t = time.time()
            
            out_data = self.process_tts(vits, chat_data)
            print(f"process tts data time: {(time.time() - bg_t)*1000:.2f} ms")
            
            self.api_queue.put(out_data)
            if out_data['is_end']:
                self.api_queue.put(None)
                print("stream_tts_process end")
            
    def process_tts(self, vits, chat_data):
        # 调用VITS进行语音合成
        sr, audio = vits.synthesize(
            chat_data['stream_text'], 
            language=0, 
            speaker_id=chat_data['character_info']['speaker_id'], 
            noise_scale=0.1, 
            noise_scale_w=0.668, 
            length_scale=1.2,
            return_bytes=True,
        )
        chat_data['tts_data'] = dict(
            tts_audio=encode_bytes2str(audio),
            rate=sr)
        return chat_data
    
    
    def stream_request_receiver_process(self, chunk_size=1):
        temp_data = ''
        print("wait for stream request")
        while True:
            try:
                chunk = request.stream.read(chunk_size)
            except ConnectionResetError as e:
                print(f"ConnectionResetError: {e}")
                break
            temp_data += chunk.decode('utf-8')
            if temp_data.endswith('\n'):
                temp_json_data, temp_data = temp_data.split('\n', 1)
                temp_json = json.loads(temp_json_data)
                # temp_json = json.loads(temp_data.rstrip('\n'))
                self.stt_queue.put(temp_json)
                # temp_data = ''
                if temp_json['is_end']:
                    break
    
    def generate_stream_queue_data(self):
        for queue_data in QueueIterator(self.api_queue):
            # print(f"len(queue_data['tts_data']['tts_audio']): {len(queue_data['tts_data']['tts_audio'])}")
            # print(f"queue_data: {queue_data['tts_data'].pop('tts_audio')}")
            yield self.gen_response_data(queue_data)
            # yield json.dumps(queue_data) + '\n'
    
    def gen_response_data(self, queue_data):
        return json.dumps({
            'status': queue_data.get('status', 0),  # 0: success, 1: error, 2: warning, 3: info, 4: debug
            'message': queue_data.get('message', ''),
            'is_end': queue_data['is_end'],
            'chat_output': {
                'llm_stream_data': queue_data.get('stream_text', ''),
                'question': queue_data['stt_text'] if queue_data['is_end'] else '',
            },
            'audio_output': {
                'tts_stream_data': queue_data['tts_data'].get('tts_audio', ''),
            },
        }) + '\n'
        
        
        
if __name__ == "__main__":
    
    takway_app = TakwayApp(
        app=app,
        stream_timeout=10,
        device='cuda',
        debug=False,
        asr_cfg={
            'model_path': 'vosk-model-small-cn-0.22',
            'RATE': 16000,
        },
        tts_cfg={
            'model_path': 'vits-small-patch16-22k-v2',
            'device': 'cuda',
        },
        llm_cfg={
            'appid': 'xxxxx',
            'api_key': 'xxxxx',
            'api_secret': 'xxxxx',
            'stream': 'xxxxx',
            'spark_version': 'xxxxx',
        }
    )
    
    takway_app.start_app(host='0.0.0.0', port=5000, debug=False)