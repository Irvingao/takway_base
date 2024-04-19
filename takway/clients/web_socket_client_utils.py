# basic
import io
import time
import json
import random
from collections import deque
from datetime import datetime
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
from takway.audio_utils import PicovoiceRecorder, HDRecorder
from takway.clients.client_utils import BaseWebSocketClient
from takway.audio_utils import AudioPlayer


class WebSocketClinet:
    def __init__(self, 
                 server_args, 
                 recorder_args, 
                 log_args, 
                 video_args=None, 
                 excute_args=None, 
                 ):
        # server_args
        self.server_args = server_args
        # recorder_args
        self.recorder_args = recorder_args
        # video_args
        self.video_args = video_args
        # excute_args
        self.excute_args = excute_args
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
        self.excute_display_queue = manager.Queue()
        
        self.share_time_dict = manager.dict()
        
        processes = [
            multiprocessing.Process(target=self.audio_process),
            multiprocessing.Process(target=self.web_socket_client_process),
            multiprocessing.Process(target=self.audio_play_process),
        ]
        # if self.excute_args.pop('enable'):
        #     processes.append(
        #         multiprocessing.Process(target=self.excute_display_process, args=(self.excute_display_queue,)),
        #     )
        
        for process in processes:
            time.sleep(0.5)
            process.start()
        for process in processes:
            process.join()

    def audio_process(self):
        """audio_process
        
        Args:    
            trigger_queue: multiprocessing.Queue, trigger queue
            client_queue: multiprocessing.Queue, client queue
        """
        min_stream_record_time = self.recorder_args.pop('min_stream_record_time')
        voice_trigger = self.recorder_args.pop('voice_trigger')
        if voice_trigger:
            recorder = PicovoiceRecorder(**self.recorder_args)
        else:
            voice_keys = ['access_key', 'keywords', 'keyword_paths', 'model_path','sensitivities', 'library_path']
            for key in voice_keys:
                self.recorder_args.pop(key)
            recorder = HDRecorder(**self.recorder_args)
        recorder.min_stream_record_time = min_stream_record_time
        
        # shared data struct:
        self.shared_waiting = False
        self.shared_lock = threading.Lock()
        self.shared_data_lock = threading.Lock()
        print("Audio Process starting...")
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
        print("Audio Process started.")
        
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
        print("Hardware trigger thread started.")
        
        trgrigger_status = False
        record_chunk_size = recorder.hd_chunk_size
        
        while True:
            if self.shared_waiting:
                continue
            
            # init status buffer
            is_bgn = True
            frames = []
            _total_frames = 0
            
            print("Waiting for button press...")
            recorder.wait_for_hardware_pressed()
            print("Button pressed.")
            # stop voice trigger thread
            with self.shared_data_lock:
                self.shared_waiting = True  # shared_waiting 控制所有线程的待机状态，True表示待机，False表示工作
            
            print("Start recording...")
            bg_t = time.time()
            while True:
                
                data = recorder.record_chunk_voice(
                    CHUNK=record_chunk_size, 
                    return_type=None, 
                    exception_on_overflow=False)
                
                frames.append(data)
                _total_frames += 1
                
                if not recorder.is_hardware_pressed:
                    print("Button released.")
                    print(f"rlse time: {datetime.now()}")
                    break
                
                stream_reset_status = self.stream_record_process(
                    bytes_frames=recorder.write_wave_bytes(frames), 
                    frames_size=len(frames),
                    record_chunk_size=record_chunk_size,
                    sample_rate=recorder.RATE,
                    min_stream_record_time=recorder.min_stream_record_time,
                    is_bgn=is_bgn,
                    is_end=False)
                if stream_reset_status:
                    frames.clear()
                    is_bgn = False
            
            self.stream_record_process(
                bytes_frames=recorder.write_wave_bytes(frames), 
                frames_size=len(frames),
                record_chunk_size=record_chunk_size,
                sample_rate=recorder.RATE,
                min_stream_record_time=recorder.min_stream_record_time,
                is_bgn=is_bgn,
                is_end=True)
            
            print(f"Tatal frames: {_total_frames*record_chunk_size}, {_total_frames*record_chunk_size/recorder.RATE} sec.")
            print(f"rcrd time: {datetime.now()}")
            
            with self.shared_data_lock:
                self.shared_waiting = False # 恢复voice trigger线程工作
                
    def voice_trigger_thread(self, recorder):
        """voice_trigger_thread
        
        Args: 
            recorder: takway.audio_utils.Recorder, recorder object
        """
        self.logger.info("voice record thread started.")
        print("voice record thread started.")
        
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
                stream_reset_status = self.stream_record_process(
                    bytes_frames=recorder.write_wave_bytes(full_frames), 
                    frames_size=len(full_frames),
                    record_chunk_size=record_chunk_size,
                    sample_rate=recorder.RATE,
                    min_stream_record_time=recorder.min_stream_record_time,
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
                        self.stream_record_process(
                            bytes_frames=recorder.write_wave_bytes(full_frames), 
                            frames_size=len(full_frames),
                            record_chunk_size=record_chunk_size,
                            sample_rate=recorder.RATE,
                            min_stream_record_time=recorder.min_stream_record_time,
                            is_bgn=is_bgn,
                            is_end=True)
                        print(f"Tatal frames: {_total_frames*record_chunk_size}, valid frame: {_frames*record_chunk_size}, valid RATE: {_frames/_total_frames*100:.2f}%, {_frames*record_chunk_size/recorder.RATE} sec.")
                        print("End recording.")
                        break
    
    
    def stream_record_process(self, 
                            bytes_frames: bytes, 
                            frames_size: int,
                            record_chunk_size: int,
                            sample_rate: int,
                            min_stream_record_time: int,
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
        if frames_size*record_chunk_size >= min_stream_record_time*sample_rate or is_end:
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
    
    def web_socket_client_process(self):
        
        client = BaseWebSocketClient(self.server_args['server_url'], self.server_args['session_id'])
        self.logger.info("Web socket client process started.")
        print("Web socket client process started.")
        
        while True:
            if self.client_queue.empty():
                continue
            
            print(f"init skt time: {datetime.now()}")
            # 唤醒
            client.wakeup_client()
            
            # 发送数据
            for queue_data in QueueIterator(self.client_queue):
                if queue_data[0] == 'audio':
                    audio_dict = queue_data[1]
                
                    client.send_per_data(
                        audio=audio_dict['frames'],
                        stream=True,
                        voice_synthesize=True,
                        is_end=audio_dict['is_end'],
                        encoding='base64',
                    )
                    print(f"send skt time: {datetime.now()}")
            print(f"fnsh skt time: {datetime.now()}")
                    
            # 接收数据
            while True:
                response, data_type = client.receive_per_data()
                if data_type == dict:
                    print(response)  # 打印接收到的消息
                    print(f"recv json time: {datetime.now()}")
                elif data_type == bytes:
                    print(f"recv bytes time: {datetime.now()}")
                    self.audio_play_queue.put(('audio_bytes', response))
                elif data_type == None:
                    break  # 如果没有接收到消息，则退出循环
            print("接收完毕:", datetime.now())
            
    def audio_play_process(self):
        '''
        Args:
            audio_play_queue: multiprocessing.Queue, audio play queue
            share_time_dict: multiprocessing.Manager.dict, shared time dict
        '''
        audio_player = AudioPlayer(output_device_index=self.recorder_args['output_device_index'])
        self.logger.info("Audio play process started.")
        while True:
            item = self.audio_play_queue.get()
            if item[0] == 'audio_bytes':
                # 播放音频
                print("Playing audio...")
                tts_audio = item[1]
                print(f"play time: {datetime.now()}")
                try:
                    audio_player.play(tts_audio)
                except TypeError as e:
                    print(f"audio play error: {e}")
                    continue


    def excute_display_process(self, excute_display_queue):
        '''
        Args:
            excute_display_queue: multiprocessing.Queue, excute display queue
        '''
        self.logger.info("excute display process not used.")
        