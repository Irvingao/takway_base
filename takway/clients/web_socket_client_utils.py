# basic
import io
import os
import sys
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
                 board, 
                 server_args, 
                 recorder_args, 
                 player_args, 
                 log_args, 
                 excute_args=None, 
                 ):
        self.board = board
        # server_args
        self.server_args = server_args
        # recorder_args
        self.recorder_args = recorder_args
        # player_args
        self.player_args = player_args
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
        print("Logger started.")
        
    def process_init(self):
        # multiprocessing
        manager = multiprocessing.Manager()
        self.trigger_queue = manager.Queue()
        self.client_queue = manager.Queue()
        self.audio_play_queue = manager.Queue()
        self.excute_queue = manager.Queue()
        
        # 多进程标志为
        self.mircophone_active_set = manager.Event()
        self.speaker_active_set = manager.Event()
                
        processes = [
            multiprocessing.Process(target=self.audio_process),
            multiprocessing.Process(target=self.web_socket_client_process),
            multiprocessing.Process(target=self.audio_play_process),
        ]
        if self.excute_args.get('enable', False):
            processes.append(
                multiprocessing.Process(target=self.excute_process),
            )
        
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
        
        # create threads
        threads = [threading.Thread(target=self.hardware_trigger_thread, args=(recorder,))]
        if voice_trigger:
            vioce_threads = [
                threading.Thread(target=self.voice_trigger_thread, args=(recorder,)),
            ]
            threads.extend(vioce_threads)
        for thread in threads:
            thread.start()
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
            
            self.mircophone_active_set.clear()
            print("Waiting for button press...")
            recorder.wait_for_hardware_pressed()
            print("Button pressed.")
            self.mircophone_active_set.set()
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
                    # print("Button released.")
                    print(f"button rlse time: {datetime.now()}")
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
            
            # print(f"Tatal frames: {_total_frames*record_chunk_size}, {_total_frames*record_chunk_size/recorder.RATE} sec.")
            # print(f"rcrd time: {datetime.now()}")
            
            with self.shared_data_lock:
                self.shared_waiting = False # 恢复voice trigger线程工作
                
    def voice_trigger_thread(self, recorder):
        """voice_trigger_thread
        
        Args: 
            recorder: takway.audio_utils.Recorder, recorder object
        """
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
            
            self.mircophone_active_set.clear()
            if not recorder.is_wakeup(data):
                continue
            
            if self.board == 'orangepi':
                recorder.hardware.set_led2_on()
            self.mircophone_active_set.set()
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
                    # print("add vad frame")
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
                        # print(f"Tatal frames: {_total_frames*record_chunk_size}, valid frame: {_frames*record_chunk_size}, valid RATE: {_frames/_total_frames*100:.2f}%, {_frames*record_chunk_size/recorder.RATE} sec.")
                        # print("End recording.")
                        break
            if self.board == 'orangepi':
                recorder.hardware.set_led2_off()
    
    
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
                # print("put None to client queue.")
                self.client_queue.put(None)
            return True
        else:
            return False
    
    def web_socket_client_process(self):
        
        client = BaseWebSocketClient(self.server_args['server_url'], self.server_args['session_id'])
        print("Web socket client process started.")
        # print("Web socket client process started.")
        
        while True:
            if self.client_queue.empty():
                continue
            
            # print(f"init skt time: {datetime.now()}")
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
                    # print(f"send skt time: {datetime.now()}")
            # print(f"fnsh skt time: {datetime.now()}")
                    
            # 接收数据
            while True:
                response, data_type = client.receive_per_data()
                if data_type == dict:
                    print(response)  # 打印接收到的消息
                    try:
                        response = json.loads(response['msg'])
                        if 'content' in response.keys():
                            self.excute_queue.put((response['instruct'], response['content']))
                    except json.JSONDecodeError as e:
                        print(f"json decode error: {e}")
                        continue
                    # print(f"recv json time: {datetime.now()}")
                elif data_type == bytes:
                    # print(f"recv bytes time: {datetime.now()}")
                    self.audio_play_queue.put(('audio_bytes', response))
                elif data_type == None:
                    break  # 如果没有接收到消息，则退出循环
            # print("接收完毕:", datetime.now())
            
    def audio_play_process(self):
        '''
        Args:
            audio_play_queue: multiprocessing.Queue, audio play queue
            share_time_dict: multiprocessing.Manager.dict, shared time dict
        '''
        audio_player = AudioPlayer(**self.player_args)
        print("Audio play process started.")
        while True:
            item = self.audio_play_queue.get()
            if item[0] == 'audio_bytes':
                # 播放音频
                print("Playing audio...")
                tts_audio = item[1]
                print(f"play audio time: {datetime.now()}")
                try:
                    # 播放
                    self.speaker_active_set.set()
                    tts_audio = audio_player.check_audio_type(tts_audio, return_type=None)
                    for i in range(0, len(tts_audio), audio_player.CHUNK):
                        audio_player.stream.write(tts_audio[i:i+audio_player.CHUNK])
                        print("Playing {} data...{}/{}".format(item[0], i, len(tts_audio)))
                        if self.mircophone_active_set.is_set():
                            print("mirophone is active.")
                            self.mircophone_active_set.wait()
                            break
                    audio_player.stream.write(tts_audio[i+audio_player.CHUNK:])
                    print(f"audio data played.")
                except TypeError as e:
                    print(f"audio play error: {e}")
                    continue
            else:
                if item[0] == 'story':
                    audio_data = audio_player.load_audio_file(f"/home/orangepi/story_22050/{item[1]}.wav")
                elif item[0] == 'music':
                    audio_data = audio_player.load_audio_file("/home/orangepi/music_22050/1.wav")
                # 播放
                self.speaker_active_set.set()
                audio_data = audio_player.check_audio_type(audio_data, return_type=None)
                time.sleep(0.5)
                for i in range(0, len(audio_data), audio_player.CHUNK):
                    audio_player.stream.write(audio_data[i:i+audio_player.CHUNK])
                    print("Playing {} data...{}/{}".format(item[0], i, len(audio_data)))
                    if self.mircophone_active_set.is_set():
                        audio_player.close()
                        print("Reinit audio player.")
                        print("mirophone is active.")
                        self.mircophone_active_set.wait()
                        time.sleep(0.5)
                        audio_player = AudioPlayer(**self.player_args)
                        break
                    
                # audio_player.stream.write(audio_data[i+audio_player.CHUNK:])
                # print(f"{item[0]} data played.")
                
                '''
                audio_player.close()
                if item[0] == 'story':
                    try:
                        os.system(f"aplay -D hw:3,0 /home/orangepi/story/{item[1]}.wav")
                    except Exception as e:
                        print(f"story play error: {e}")
                elif item[0] == 'music':
                    try:
                        os.system(f"aplay -D hw:3,0 /home/orangepi/music/1.wav")
                    except Exception as e:
                        print(f"music play error: {e}")
                    # 使用subprocess.Popen执行命令，而不是os.system
                    process = subprocess.Popen(['aplay', '-D', 'hw:3,0', f'/home/orangepi/story/{item[1]}.wav'], stdout=subprocess.PIPE, stderr=subprocess.PIPE)
                    # 此时process.pid将包含命令的PID
                    print(f"The PID of the executed command is: {process.pid}")
                    while True:
                        # ... 执行一些操作 ...
                        if subprocess.run(["gpio", "read", str(8)], capture_output=True, text=True).stdout.strip() == '0':
                            # 如果需要终止进程，可以使用terminate()方法
                            process.terminate()
                            print("Process terminated.")
                            break
                        time.sleep(0.1)
                audio_player.init_audio_player(False, True, )
                '''
        

    def excute_process(self):
        '''
        Args:
            excute_queue: multiprocessing.Queue, excute display queue
        '''
        print("Excute process started.")
        
        while True:
            if self.excute_queue.empty():
                continue
            
            if self.speaker_active_set.is_set():
                instruct, content = self.excute_queue.get()
                
                print(f"Got speaker info: {instruct, content}")
                
                print(f"Playing {instruct} {content}...")
                print(f"play {instruct} time: {datetime.now()}")
                self.audio_play_queue.put((instruct, content))

                self.speaker_active_set.clear()
                