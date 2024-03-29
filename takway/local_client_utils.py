# basic
import io
import time
import json
import random
from collections import deque
# log
import logging
import warnings
# multiprocessing
import queue
import threading
import multiprocessing
# web request
import requests
import pyaudio
# hot words detection
import pvporcupine

from takway.apps.data_struct import QueueIterator
from takway.common_utils import *

class LocalClinet:
    def __init__(self, 
                 server_args, 
                 recorder_args, 
                 video_args, 
                 emo_args, 
                 log_args):
        # server_args
        self.server_args = server_args
        # recorder_args
        self.recorder_args = recorder_args
        # video_args
        self.video_args = video_args
        # emo_args
        self.emo_args = emo_args
        # log_args
        self.log_args = log_args
        
        # TODO: 设计多进程log queue
        self.logger_init()
        
        
    def logger_init(self):
        # log_args
        log_level = self.log_args['log_level']
        log_file = self.log_args['log_file']
        
        if log_level == 'debug':
            log_level = logging.DEBUG
        elif log_level == 'info':
            log_level = logging.INFO
        
        # logger
        self.logger = logging.getLogger('mylogger')
        self.logger.setLevel(log_level)
        # handler 创建一个handler，用于写入日志文件
        handler = logging.FileHandler(log_file)
        handler.setLevel(log_level)
        # stream handler 创建一个handler，用于输出到控制台
        console = logging.StreamHandler()
        console.setLevel(logging.INFO)
        
        # 定义handler的输出格式（formatter）
        formatter = logging.Formatter('%(asctime)s - %(name)s - %(levelname)s - %(message)s')
        handler.setFormatter(formatter)
        console.setFormatter(formatter)
        
        # 添加handler        
        self.logger.addHandler(handler)
        self.logger.addHandler(console)
        self.logger.info("Logger started.")
        
    def process_init(self):
        # multiprocessing
        manager = multiprocessing.Manager()
        self.trigger_queue = manager.Queue()
        self.client_queue = manager.Queue()
        self.audio_play_queue = manager.Queue()
        self.emo_display_queue = manager.Queue()
        
        self.share_time_dict = manager.dict()
        
        self.speaking_emo_event = manager.Event()
        
        processes = [
            multiprocessing.Process(target=self.audio_process, 
                                    args=(self.trigger_queue,self.client_queue)),
            # multiprocessing.Process(target=self.camera_process, args=(self.trigger_queue,self.client_queue)),
            multiprocessing.Process(target=self.local_client_process, 
                                    args=(self.client_queue,self.audio_play_queue,self.emo_display_queue, self.share_time_dict)),
            multiprocessing.Process(target=self.audio_play_process, 
                                    args=(self.audio_play_queue,self.share_time_dict)),
        ]
        if self.emo_args.pop('enable'):
            processes.append(
                multiprocessing.Process(target=self.emo_display_process, args=(self.emo_display_queue,)),
            )
        
        for process in processes:
            process.start()
        for process in processes:
            process.join()

    def audio_process(self, 
                      trigger_queue, 
                      client_queue):
        """audio_process
        
        Args:    
            trigger_queue: multiprocessing.Queue, trigger queue
            client_queue: multiprocessing.Queue, client queue
        """
        
        self.frame_chunk_size = self.recorder_args.pop('frame_chunk_size')
        self.min_stream_record_time = self.recorder_args.pop('min_stream_record_time')
        voice_trigger = self.recorder_args.pop('voice_trigger')
        self.RATE = self.recorder_args['RATE']
        
        from takway.audio_utils import PicovoiceRecorder
        recorder = PicovoiceRecorder(**self.recorder_args)
        
        # shared data struct:
        self.shared_waiting = False
        self.shared_lock = threading.Lock()
        self.shared_data_lock = threading.Lock()
        
        # create threads
        threads = [threading.Thread(target=self.hardware_trigger_thread, args=(recorder,))]
        if voice_trigger:
            vioce_threads = [
                threading.Thread(target=self.voice_trigger_thread, args=(recorder,)),
            ]
            threads.extend(vioce_threads)
        for thread in threads:
            thread.start()
        self.logger.info("Audio Process started.")
        
        while True:
            for thread in threads:
                thread.join()
            print(f"audio process exit") ; exit()
            
            
    def hardware_trigger_thread(self, recorder):
        """hardware_trigger_thread
        
        Args: 
            recorder: takway.audio_utils.Recorder, recorder object
        """
        self.logger.info("Hardware trigger thread started.")
        
        trgrigger_status = False
        while True:
            if self.shared_waiting:
                continue
            
            # init status buffer
            is_bgn = True
            _frames = 0
            _total_frames = 0
            frames = []
            full_frames = []
            
            print("Waiting for button press...")
            recorder.wait_for_hardware_pressed()
            print("Button pressed.")
            # stop voice trigger thread
            with self.shared_data_lock:
                self.shared_waiting = True  # shared_waiting 控制所有线程的待机状态，True表示待机，False表示工作
            
            print("Start recording...")
            bg_t = time.time()
            record_chunk_size = recorder.hd_chunk_size
            while True:
                
                data = recorder.record_chunk_voice(
                    CHUNK=record_chunk_size, 
                    return_type=None, 
                    exception_on_overflow=False)
                
                frames.append(data)
                full_frames.append(data)
                _total_frames += 1
                
                if not recorder.is_hardware_pressed:
                    break
                
                stream_reset_status = self.stream_record(
                    bytes_frames=recorder.write_wave_bytes(full_frames), 
                    frames_size=len(full_frames),
                    record_chunk_size=record_chunk_size,
                    is_bgn=is_bgn,
                    is_end=False)
                if stream_reset_status:
                    full_frames.clear()
                    is_bgn = False
            
            self.stream_record(
                bytes_frames=recorder.write_wave_bytes(full_frames), 
                frames_size=len(full_frames),
                record_chunk_size=record_chunk_size,
                is_bgn=is_bgn,
                is_end=True)
            
            print(f"Tatal frames: {_total_frames*record_chunk_size}, {_total_frames*record_chunk_size/recorder.RATE} sec.")
            # recorder.write_wave_io(f"record_{int(bg_t)}.wav", frames); print(f"write record_{int(bg_t)}.wav")

            with self.shared_data_lock:
                self.shared_waiting = False # 恢复voice trigger线程工作
                
    def voice_trigger_thread(self, recorder):
        """voice_trigger_thread
        
        Args: 
            recorder: takway.audio_utils.Recorder, recorder object
        """
        self.logger.info("voice record thread started.")
        
        print("Waiting for wake up...")
        while True:
            if self.shared_waiting:
                continue
            data = recorder.record_chunk_voice(
                CHUNK=recorder.porcupine.frame_length, 
                return_type=None, 
                exception_on_overflow=False, 
                queue=None)
            
            record_chunk_size = recorder.vad_chunk_size
            
            if not recorder.is_wakeup(data):
                continue
            # wake up
            is_bgn = True
            _frames = 0
            _total_frames = 0
            frames = []
            full_frames = []
            # status buffer
            buffer_size = recorder.vad_buffer_size
            active_buffer = deque(maxlen=buffer_size)
            bg_t = time.time()
            print("Start recording...")
            while True:
                data = recorder.record_chunk_voice(
                    CHUNK=record_chunk_size, 
                    return_type=None, 
                    exception_on_overflow=False)
                if data is None:
                    continue
                
                is_speech = recorder.is_speech(data)
                if is_speech:
                    _frames += 1
                    frames.append(data)
                    print("add vad frame")
                _total_frames += 1
                full_frames.append(data)
                
                # send chunk data to client
                stream_reset_status = self.stream_record(
                    bytes_frames=recorder.write_wave_bytes(full_frames), 
                    frames_size=len(full_frames),
                    record_chunk_size=record_chunk_size,
                    is_bgn=is_bgn,
                    is_end=False)
                if stream_reset_status:
                    full_frames.clear()
                    is_bgn = False
                
                if is_speech:
                    if active_buffer.__len__() == buffer_size:
                        active_buffer.popleft()
                    active_buffer.append(True)
                else:
                    if active_buffer.__len__() == buffer_size:
                        active_buffer.popleft()
                    active_buffer.append(False)
                    if active_buffer.count(False) != active_buffer.maxlen:
                        continue
                    if time.time() - bg_t > recorder.min_act_time:
                        # end recording
                        self.stream_record(
                            bytes_frames=recorder.write_wave_bytes(full_frames), 
                            frames_size=len(full_frames),
                            record_chunk_size=record_chunk_size,
                            is_bgn=is_bgn,
                            is_end=True)
                        print(f"Tatal frames: {_total_frames*record_chunk_size}, valid frame: {_frames*record_chunk_size}, valid rate: {_frames/_total_frames*100:.2f}%, {_frames*record_chunk_size/recorder.RATE} sec.")
                        print("End recording.")
                        break
                
    
    
    def stream_record(self, 
                      bytes_frames: bytes, 
                      frames_size: int,
                      record_chunk_size: int,
                      is_bgn: bool,
                      is_end: bool):
        '''
        Args:
            bytes_frames: bytes, audio data
            frames_size: int, audio data size
            record_chunk_size: int, audio data chunk size
            is_bgn: bool, is begin of stream
            is_end: bool, is end of stream
        
        Returns:
            bool, if stream reset status
        '''
        if len(bytes_frames) == 0:
            return False
        if frames_size*record_chunk_size >= self.min_stream_record_time*self.RATE or is_end:
            if is_bgn and is_end:
                return False
            stream_data = dict(
                frames=bytes_frames, 
                frames_size=frames_size,
                chunk_size=record_chunk_size,
                is_bgn=is_bgn,
                is_end=is_end)
            self.client_queue.put(('audio', stream_data))
            if is_end:
                print("put None to client queue.")
                self.client_queue.put(None)
            return True
        else:
            return False
    
    def camera_process(self, logger, trigger_queue, client_queue):
        from takway.cam_utils import Camera
        cam = Camera(self.video_args)
        while True:
            if trigger_queue.empty():
                time.sleep(0.5)
            else:
                item = trigger_queue.get()
                if item[0] == 'trgrigger_status' and item[1]:
                    _, frame = cap.read()
                    client_queue.put(('image', frame))


    def local_client_process(self, 
                             client_queue,
                             audio_play_queue,
                             emo_display_queue, 
                             share_time_dict):
        '''
        Args:
            client_queue: multiprocessing.Queue, client queue
            audio_play_queue: multiprocessing.Queue, audio play queue
            emo_display_queue: multiprocessing.Queue, emo display queue
            share_time_dict: multiprocessing.Manager.dict, shared time dict
        '''
        from takway.client_utils import CharacterClient
        character = self.server_args.pop('character')
        client = CharacterClient(**self.server_args)
        
        # print(f"-------------------{character}-------------------")
        # print(f"client.chat_status: {client.chat_status}")
        if client.chat_status == 'init':
            client.set_character(character)
            client.chat_status = 'chating'
        # print(f"client.chat_history: {client.chat_history}")
                
        self.logger.info("Local client process started.")
        
        while True:
            response = None
            if self.client_queue.empty():
                continue
            try:
                response = requests.post(client.server_url, stream=True, 
                    data=self.generate_stream_queue_data(client, client_queue))
                print("get response from server.")
                self.get_stream_response(client, response, audio_play_queue, emo_display_queue)
            except requests.exceptions.ConnectionError or ConnectionError as e:
                print(f"Wait for Server connection...")
            except requests.exceptions.Timeout or Timeout as e:
                print(f"Timeout: {e}")
            except requests.exceptions.ChunkedEncodingError:
                print("ChunkedEncodingError")
                
    def generate_stream_queue_data(self, client, client_queue, **kwargs):
        _i = 0
        for queue_data in QueueIterator(client_queue):
            if queue_data[0] == 'audio':
                _i += 1
                if _i == 1:
                    self.share_time_dict['client_time'] = [time.time()]
                else:
                    self.share_time_dict['client_time'].append(time.time())
                audio_data = queue_data[1]
                print("send audio data to server...")
                # print(f"local chat history: {client.chat_history}")
                yield client.gen_request_data(
                        audio_data=audio_data, 
                        chat_data=dict(
                            chat_history=client.chat_history,
                            chat_status=client.chat_status),
                        character_data=client.character_info)
                
    def get_stream_response(self, 
                            client, 
                            response, 
                            audio_play_queue=None,
                            emo_display_queue=None, 
                            chunk_size=1024):
        '''
        Args:
            client: takway.client_utils.CharacterClient, client object
            response: requests.Response, response object
            audio_play_queue: multiprocessing.Queue, audio play queue
            emo_display_queue: multiprocessing.Queue, emo display queue
            chunk_size: int, chunk size
        '''
        assert isinstance(response, requests.Response), \
            f"response is not requests.Response, but {type(response)}"
        
        temp_data = ''  # init temp_data
        
        if response.status_code == 200:
            print("get response from server successfully.")
        else:
            print(f"response error, status code: {response.status_code}")
        
        chat_llm_response = ''
        
        _i = 0
        # for chunk in response.iter_lines():
            # if chunk:
        for chunk in response.iter_content(chunk_size=chunk_size):
            temp_data += chunk.decode('utf-8')
            if temp_data.endswith('\n'):
                _i += 1
                try:
                    temp_json = json.loads(temp_data.rstrip('\n'))
                    # phase 1: get audio data
                    audio_play_queue.put(('server_data', temp_json['audio_output']['tts_stream_data']))
                    # phase 2: get chat data
                    chat_llm_response += temp_json['chat_output']['llm_stream_data']
                    
                    if temp_json['is_end']:
                        client.update_chat_history(question=temp_json['chat_output']['question'],
                            response=chat_llm_response, asw_prompt_id=1)
                    # print(f"chat_history: {client.chat_history}")
                    if _i == 1:
                        emo_display_queue.put(('emo_data', '高兴'))
                except json.JSONDecodeError:
                    print(f"json decode error: {temp_data}")
                temp_data = ''
                # print("get response.")
        print("End get response.")
            
    def audio_play_process(self, 
                           audio_play_queue, 
                           share_time_dict):
        '''
        Args:
            audio_play_queue: multiprocessing.Queue, audio play queue
            share_time_dict: multiprocessing.Manager.dict, shared time dict
        '''
        from takway.audio_utils import AudioPlayer
        audio_player = AudioPlayer()
        self.logger.info("Audio play process started.")
        while True:
            self.speaking_emo_event.clear()
            item = audio_play_queue.get()
            self.speaking_emo_event.set()   # stop emo random display
            if item[0] == 'server_data':
                # 播放音频
                print("Playing audio...")
                tts_audio = item[1]
                print(f"wait time: {(time.time() - self.share_time_dict['client_time'][0])*1000:.2f} ms")
                try:
                    audio_player.play(tts_audio)
                except TypeError as e:
                    # print(f"audio play error: {e}")
                    # print(f"tts_audio: {tts_audio}")
                    # print(f"type tts_audio: {type(tts_audio)}")
                    # tts_audio: <class 'NoneType'>
                    continue


    def emo_display_process(self, emo_display_queue):
        '''
        Args:
            emo_display_queue: multiprocessing.Queue, emo display queue
        '''
        from takway.emo_utils import EmoVideoPlayer
        emo_player = EmoVideoPlayer(**self.emo_args)
        self.logger.info("Emo display process started.")
        while True:
            if emo_display_queue.empty():
                time.sleep(0.1)
                if self.speaking_emo_event.is_set():
                    continue
                emo_player.random_wink()
            else:
                item = emo_display_queue.get()
                print(f"Emo display process Get item: {item[0]}")
                if item[0] == 'emo_data':
                    server_data = item[1]
                    print("Displaying emo...")
                    emo_player.display_emo(emo_name='兴奋', stage='start')
                    emo_player.display_emo(emo_name='兴奋', stage='loop')
                    emo_player.display_emo(emo_name='兴奋', stage='end')
                    print("Display done.")
                    time.sleep(15)
