# basic
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

class WebRequestMPManager:
    def __init__(self, 
                 server_args, 
                 audio_args, 
                 recorder_args, 
                 asr_args, 
                 video_args, 
                 emo_args, 
                 log_args):
        # server_args
        self.server_args = server_args
        # audio_args
        self.record_CHUNK_SIZE = audio_args['record_CHUNK_SIZE']
        self.voice_trigger = audio_args['voice_trigger']
        self.keywords = audio_args['keywords']
        # recorder_args
        self.recorder_args = recorder_args
        # asr_args
        self.asr_args = asr_args
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
        self.audio_queue = manager.Queue()
        self.audio_play_queue = manager.Queue()
        self.emo_display_queue = manager.Queue()
        
        processes = [
            multiprocessing.Process(target=self.audio_process, args=(self.logger,self.voice_trigger,self.trigger_queue,self.client_queue)),
            # multiprocessing.Process(target=self.camera_process, args=(self.trigger_queue,self.client_queue)),
            # multiprocessing.Process(target=self.local_client_process, args=(self.logger,self.client_queue,self.audio_play_queue,self.emo_display_queue)),
            # multiprocessing.Process(target=self.audio_play_process, args=(self.logger,self.audio_play_queue,)),
            # multiprocessing.Process(target=self.emo_display_process, args=(self.logger,self.emo_display_queue,)),
        ]
        for process in processes:
            process.start()
        for process in processes:
            process.join()

    def audio_process(self, logger, voice_trigger, trigger_queue, client_queue):
        """audio_process
        
        Args:    
            voice_trigger: bool, whether to use voice trigger
            trigger_queue: multiprocessing.Queue, trigger queue
            client_queue: multiprocessing.Queue, client queue
        """
        # from takway.audio_utils import Recorder
        from takway.audio_utils import VADRecorder
        recorder = VADRecorder(
            **self.recorder_args,
            )
        
        # two threads for hardware and voice trigger
        # shared data struct:
        self.shared_waiting = False
        self.shared_hd_trigger = False
        self.shared_kw_trigger = False
        self.shared_lock = threading.Lock()
        
        self.shared_data_lock = threading.Lock()
        self.shared_audio_data = None
        # vad
        self.shared_vad_data = None
        self.shared_vad_lock = threading.Lock()
        # stt
        # event 
        self.record_event = threading.Event()
        self.vad_event = threading.Event()
        self.stt_event = threading.Event()
        
        self._debug_count = 0

        '''
        shared_waiting: 控制所有线程的待机状态，True表示待机，False表示工作
        shared_hd_trigger: 控制硬件触发器的状态，True表示触发，False表示未触发
        shared_kw_trigger: 控制语音触发器的状态，True表示触发，False表示未触发
        
        share_audio_data: 共享音频数据，用于存储从麦克风采集的音频数据
        '''
        # create threads
        threads = [threading.Thread(target=self.hardware_trigger_thread, args=(recorder,))]
        if self.voice_trigger:
            vioce_threads = [
                threading.Thread(target=self.voice_record_thread, args=(recorder,)),
                # threading.Thread(target=self.vad_thread, args=(recorder,)),
                threading.Thread(target=self.stt_thread, args=(recorder,)),
                             ]
            threads.extend(vioce_threads)
        for thread in threads:
            thread.start()
        # self.logger.info("Audio Process started.")
        
        while True:
            '''
            # Warning: 一定要加延时！！！否则会有bug！！！
            time.sleep(0.001) 
            if (self.shared_hd_trigger or self.shared_kw_trigger):
                # print(f"self.shared_hd_trigger: {self.shared_hd_trigger}, self.shared_kw_trigger: {self.shared_kw_trigger}")
                audio_data = self.shared_audio_data
                trigger_queue.put(('trgrigger_status', True))
                client_queue.put(('audio', audio_data))
                self.shared_lock.acquire()   # 加锁
                self.shared_hd_trigger = False
                self.shared_kw_trigger = False
                self.shared_audio_data = None
                self.shared_waiting = False
                self.shared_lock.release()   # 释放锁
            '''
            self.record_event.wait() # 等待record线程被唤醒
            trigger_queue.put(('trgrigger_status', True))
            client_queue.put(('audio', self.shared_audio_data))
            # print(f"send audio data to client"); exit()
            
    def hardware_trigger_thread(self, recorder):
        """hardware_trigger_thread
        
        Args: 
            recorder: takway.audio_utils.Recorder, recorder object
        """
        self.logger.info("Hardware trigger thread started.")
        
        trgrigger_status = False
        while True:
            time.sleep(0.2)
            if self.shared_waiting:
                continue
            trgrigger_status = recorder.get_hardware_trigger_status()
            if trgrigger_status:
                self.shared_lock.acquire()   
                self.shared_waiting = True  # shared_waiting 控制所有线程的待机状态，True表示待机，False表示工作
                self.shared_hd_trigger = True   # share_hd_trigger 控制硬件触发器的状态，True表示触发，False表示未触发
                self.shared_lock.release()   
                # record microphone data
                audio_data = recorder.record_hardware()
                self.shared_data_lock.acquire() 
                self.shared_audio_data = audio_data # shared_audio_data 共享音频数据，用于存储从麦克风采集的音频数据
                self.shared_data_lock.release() 
                self.record_event.set() # 唤醒record线程
            else:
                self.shared_lock.acquire()  
                self.shared_waiting = False # 释放
                self.shared_lock.release()  
                
    def voice_record_thread(self, recorder, keywords=['你好']):
        """voice_record_thread
        
        Args: 
            recorder: takway.audio_utils.Recorder, recorder object
        """
        self.logger.info("voice record thread started.")
        
        while True:
            if self.shared_waiting:
                time.sleep(0.01)
                continue
            
            frames = []
            # status buffer
            is_currently_speaking = False
            buffer_size = recorder.vad_buffer_size
            # buffer_size = 6
            active_buffer = deque([False for i in range(buffer_size-1)]+[True], maxlen=buffer_size)
            audio_buffer = deque(maxlen=buffer_size)
            silence_buffer = deque([True for i in range(buffer_size)]+[False], maxlen=buffer_size)
            
            while True:
                data = recorder.record_chunk_voice(
                    CHUNK=recorder.vad_chunk_size, 
                    return_type=None, 
                    exception_on_overflow=False)
                if data is None:
                    continue
                t1 = time.time()
                # print(f"VAD is_speech: {recorder.is_speech(data)}")
                # print(f"VAD cost: {(time.time() - t1)/1000} ms")
                if recorder.is_speech(data):
                    # 标志位buffer
                    active_buffer.append(True); active_buffer.popleft()
                    silence_buffer.append(False); silence_buffer.popleft()
                    # 暂时增加到buffer中
                    audio_buffer.append(data)
                    # 如果满足检测要求
                    if all(active_buffer):
                        if not is_currently_speaking:
                            print("Speech start detected")
                            is_currently_speaking = True
                            frames.extend(audio_buffer)   # 把说话的buffer也加上
                    if is_currently_speaking:
                        frames.append(data)
                else:
                    # 标志位buffer
                    # active_buffer.append(False); active_buffer.popleft()
                    silence_buffer.append(True); silence_buffer.popleft()
                    if all(silence_buffer):
                        # 检测到人声并持续录音
                        if is_currently_speaking:
                        # 结束标志位
                            print("Speech end detected")
                            # print("frames length: ", len(frames))
                            self.shared_vad_lock.acquire() 
                            self.shared_vad_data = frames
                            self.shared_vad_lock.release() 
                            self.stt_event.set()    # 唤醒stt线程
                            print("Wake stt thread")
                            break
                        else:
                            frames = []
            '''
            # print(f"audio_data: {len(audio_data)}")
            self.shared_lock.acquire() 
            self.shared_audio_data = audio_data
            self.shared_lock.release() 
            self.vad_event.set() # 唤醒vad线程
            '''
    '''
    def vad_thread(self, recorder):
        self.logger.info("VAD thread started.")
        while True:
            frames = []
            # status buffer
            is_currently_speaking = False
            buffer_size = recorder.vad_buffer_size
            active_buffer = deque([False for i in range(buffer_size)], maxlen=buffer_size)
            audio_buffer = deque(maxlen=buffer_size)
            silence_buffer = deque([True for i in range(buffer_size)], maxlen=buffer_size)
            
            while True:
                self.vad_event.wait() # 等待vad线程被唤醒
                data = self.shared_audio_data
                if data is None:
                    continue
                t1 = time.time()
                print(f"VAD is_speech: {recorder.is_speech(data)}")
                print(f"VAD cost: {(time.time() - t1)/1000} ms")
                if recorder.is_speech(data):
                    # 标志位buffer
                    active_buffer.append(True); active_buffer.popleft()
                    silence_buffer.append(False); silence_buffer.popleft()
                    # 暂时增加到buffer中
                    audio_buffer.append(data)
                    # 如果满足检测要求
                    if all(active_buffer):
                        if not is_currently_speaking:
                            print("Speech start detected")
                            is_currently_speaking = True
                            frames.extend(audio_buffer)   # 把说话的buffer也加上
                    if is_currently_speaking:
                        frames.append(data)
                else:
                    # 标志位buffer
                    active_buffer.append(False); active_buffer.popleft()
                    silence_buffer.append(True); silence_buffer.popleft()
                    # 检测到人声并持续录音
                    if is_currently_speaking:
                        # 结束标志位
                        if all(silence_buffer):
                            print("Speech end detected")
                            # print("frames length: ", len(frames))
                            self.shared_vad_lock.acquire() 
                            self.shared_vad_data = frames
                            self.shared_vad_lock.release() 
                            self.stt_event.set()    # 唤醒stt线程
                            break
    '''

    def stt_thread(self, recorder):
        """stt_thread
        
        Args: 
            recorder: takway.audio_utils.Recorder, recorder object
        """
        self.logger.info("STT thread started.")
        from takway.vosk_utils import AutoSpeechRecognizer
        asr = AutoSpeechRecognizer(**self.asr_args)
        asr.add_keyword(self.keywords)
        
        kw_trgrigger_status = False
        while True:
            self.stt_event.wait() # 等待stt线程被唤醒
            print("STT thread start")
            data = self.shared_vad_data 
            if data is None:
                continue
            print("Start to Recongnize key words")
            kw_trgrigger_status = asr.recognize_keywords(data, partial_size=512)
            print("Finish to Recongnize key words")
            if kw_trgrigger_status:
                self.shared_lock.acquire()  
                self.shared_kw_trigger = True   # share_kw_trigger 语音关键词触发器的状态，True表示触发，False表示未触发
                self.shared_lock.release() 
                self.record_event.set() # 唤醒record线程
                kw_trgrigger_status = False
                # print(f"Got keyword trigger"); exit()
                
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


    def local_client_process(self, logger, client_queue,audio_play_queue,emo_display_queue):
        from takway.client_utils import Client
        client = Client(**self.server_args)
        # print("Local client process started.")
        self.logger.info("Local client process started.")
        image = None; audio = None
        chat_status = 'init'
        while True:
            if client_queue.empty():
                time.sleep(0.2)
            else:
                item = client_queue.get()
                # print(f"Get item: {item[0]}")
                if item[0] == 'image':
                    # TODO: analyise image and send text to server
                    image = None
                if item[0] == 'audio':
                    audio = item[1]
                    print("get audio data.")
                    emo_display_queue.put(('emo_data', 'happy'))
                    '''
                    # 发送数据到服务器
                    response = client.send_data_to_server(
                        text=None, audio_data=audio, image_data=None, chat_status=chat_status)
                    print("get response from server.")
                    chat_status = 'chating'
                    print(f"response: {response}")

                    audio_play_queue.put(('audio', response))
                    '''
                    image = None; audio = None

    def audio_play_process(self, logger, audio_play_queue):
        from takway.audio_utils import AudioPlayer
        audio_player = AudioPlayer()
        self.logger.info("Audio play process started.")
        while True:
            if audio_play_queue.empty():
                time.sleep(0.2)
            else:
                item = audio_play_queue.get()
                if item[0] == 'server_data':
                    # 播放音频
                    print("Playing audio...")
                    server_data = item[1]
                    audio_player.play(server_data['audio_base64'], audio_type='base64')

    def emo_display_process(self, logger, emo_display_queue):
        from takway.emo_utils import EmoVideoPlayer
        emo_player = EmoVideoPlayer(**self.emo_args)
        self.logger.info("Emo display process started.")
        # logger.info("Emo display process started.")
        # print("Emo display process started.")
        while True:
            if emo_display_queue.empty():
                time.sleep(0.2)
                seed = random.randrange(0, 1000)
                print(f"seed: {seed}")
                if seed < 100:
                    # emo_player.display_emo_opencv(emo_name='静态', stage='seldom_wink')
                    emo_player.display_emo_maixsense(emo_name='静态', stage='seldom_wink')
                    
            else:  
                item = emo_display_queue.get()
                print(f"Emo display process Get item: {item[0]}")
                if item[0] == 'emo_data':
                    server_data = item[1]
                    print("Displaying emo...")
                    
                    # emo_player.display_emo_opencv(emo_name='静态', stage='seldom_wink')
                    # emo_player.display_emo_opencv(emo_name='静态', stage='quick_wink')
                    emo_player.display_emo_maixsense(emo_name='静态', stage='seldom_wink')
                    emo_player.display_emo_maixsense(emo_name='静态', stage='quick_wink')
                    
            

    '''
    def display_process(q):
        print("Display process started.")
        while True:
            item = q.get()
            if item[0] == 'server_data':
                server_data = item[1]
                # 显示图像和文本
                # print("Displaying image and text:", item[1]['image'], item[1]['text'])
                print("Displaying image and text:")
                # 这里可以加上实际的显示图像和文本的代码
            if item[0] == 'image':
                # 显示图像和文本
                cv2.imshow('image', item[1])
                cv2.waitKey(1)
    '''

if __name__ == '__main__':
    
    try:
        import gpiod as gpio
        model_path="vosk-model-small-cn-0.22"
        emo_dir="ResizedEmoji"
    except:
        model_path=r"G:\WorkSpace\CodeWorkspace\GPT_projects\vits_project\vits-uma-genshin-honkai\vosk-model-small-cn-0.22"
        emo_dir=r"G:\WorkSpace\CodeWorkspace\GPT_projects\vits_project\vits-uma-genshin-honkai\ResizedEmoji"
        
    import argparse
    parser = argparse.ArgumentParser()
    # server params
    parser.add_argument('--server_url', type=str, default='http://127.0.0.1:5000/process_all', help='Server url')
    # audio paramters
    parser.add_argument('--voice_trigger', type=bool, default=True, help='Voice trigger')
    parser.add_argument('--record_CHUNK_SIZE', type=int, default=8000, help='Record chunk size')
    parser.add_argument('--keywords', type=list, default=['你好'], help='Voice trigger keywords')
    # recorder paramters
    parser.add_argument('--hd_trigger', type=str, default='keyboard', help='Hardware trigger')
    parser.add_argument('--keyboard_key', type=str, default='space', help='Keyboard key')
    parser.add_argument('--CHUNK', type=int, default=2048, help='Record chunk size')
    parser.add_argument('--RATE', type=int, default=8000, help='Audio rate')
    parser.add_argument('--FORMAT', type=int, default=16, help='Audio format')
    parser.add_argument('--CHANNELS', type=int, default=1, help='Audio channels')
    parser.add_argument('--filename', type=str, default=None, help='Audio file name')
    # ASR paramters
    # model_path="vosk-model-small-cn-0.22"
    # model_path=r"G:\WorkSpace\CodeWorkspace\GPT_projects\vits_project\vits-uma-genshin-honkai\vosk-model-small-cn-0.22"
    parser.add_argument('--model_path', type=str, default=model_path, help='Vosk model path')
    # video paramters
    parser.add_argument('--device', type=str, default='pc', help='Video device')
    parser.add_argument('--width', type=int, default=1280, help='Video width')
    parser.add_argument('--height', type=int, default=720, help='Video height')
    # emo paramters
    # emo_dir="ResizedEmoji"
    # emo_dir=r"G:\WorkSpace\CodeWorkspace\GPT_projects\vits_project\vits-uma-genshin-honkai\ResizedEmoji"
    parser.add_argument('--emo_dir', type=str, default=emo_dir, help='Emo dir')
    # log paramters
    parser.add_argument('--log_file', type=str, default='my.log', help='Log file')
    parser.add_argument('--log_level', type=str, default='INFO', help='Log level')
    
    parser.add_argument('--debug', type=bool, default=True, help='Debug mode')
    args = parser.parse_args()
    
    
    # sort out args and params
    server_args = {
       'server_url': args.server_url,
    }
    
    audio_args = {
        'voice_trigger': args.voice_trigger,
        'keywords': args.keywords,
        'record_CHUNK_SIZE': args.record_CHUNK_SIZE,
    }
    
    recorder_args = {
        'hd_trigger': args.hd_trigger,
        'keyboard_key': args.keyboard_key,
        'model_path': args.model_path,
        'CHUNK': args.CHUNK,
        'FORMAT': pyaudio.paInt16 if args.FORMAT == 16 else pyaudio.paInt32,
        'CHANNELS': args.CHANNELS,
        'RATE': args.RATE,
        'filename': args.filename,
    }
    
    asr_args = {
        'model_path': args.model_path,
        'RATE': args.RATE,
        'debug': args.debug,
    }
    
    video_args = {
        'device': args.device,
        'width': args.width,
        'height': args.height,
    }
    
    emo_args = {
        'emo_dir': args.emo_dir,
    }
    
    log_args = {
        'log_file': args.log_file,
        'log_level': args.log_level,
    }
    
    
    web_request_mp_manager = WebRequestMPManager(
        server_args=server_args, 
        audio_args=audio_args, 
        recorder_args=recorder_args, 
        asr_args=asr_args, 
        video_args=video_args, 
        emo_args=emo_args, 
        log_args=log_args)
    web_request_mp_manager.process_init()