import io
import os
import time
import pyaudio
import wave
import json
import warnings
import threading
import numpy as np
from collections import deque
try:
    import keyboard
except:
    warnings.warn("keyboard module not found, please install it if use `keyboard` hd_trigger.")
try:
    import gpiod as gpio
except:
    warnings.warn("gpiod module not found, please install it if use `button` hd_trigger.")
from .common_utils import encode_bytes2str, decode_str2bytes
   
                        
def play_audio(audio_data, type='base64'):
    '''
    读取base64编码的音频流并播放
    '''
    # PyAudio配置
    p = pyaudio.PyAudio()
    stream = p.open(format=pyaudio.paInt16, channels=1, rate=22050, output=True)

    # 播放音频
    stream.write(audio_data)
    stream.stop_stream()
    stream.close()
    p.terminate()

# ####################################################### #
# base audio class
# ####################################################### #

class BaseAudio:
    def __init__(self, 
                 input=False, 
                 output=False, 
                 CHUNK=2048, 
                 FORMAT=pyaudio.paInt16, 
                 CHANNELS=1, 
                 RATE=16000,
                 filename=None):
        self.CHUNK = CHUNK
        self.FORMAT = FORMAT
        self.CHANNELS = CHANNELS
        self.RATE = RATE
        self.filename = filename
        assert input!= output, "input and output cannot be the same, \
            but got input={} and output={}.".format(input, output)
        self.p = pyaudio.PyAudio()
        self.stream = self.p.open(format=FORMAT,
                                  channels=CHANNELS,
                                  rate=RATE,
                                  input=input,
                                  output=output,
                                  frames_per_buffer=CHUNK)
    
    def load_audio_file(self, wav_file):
        with wave.open(wav_file, 'rb') as wf:
            params = wf.getparams()
            frames = wf.readframes(params.nframes)
        return frames
    
    def check_audio_type(self, audio_data, return_type=None):
        assert return_type in ['bytes', 'io', None], \
            "return_type should be 'bytes', 'io' or None."
        if isinstance(audio_data, str):
            if len(audio_data) > 50:
                audio_data = decode_str2bytes(audio_data)
            else:
                assert os.path.isfile(audio_data), \
                    "audio_data should be a file path or a bytes object."
                wf = wave.open(audio_data, 'rb')
                audio_data = wf.readframes(wf.getnframes())
        elif isinstance(audio_data, np.ndarray):
            if audio_data.dtype == np.dtype('float32'):
                audio_data = np.int16(audio_data * np.iinfo(np.int16).max)
            audio_data = audio_data.tobytes()
        elif isinstance(audio_data, bytes):
            pass
        else:
            raise TypeError(f"audio_data must be bytes, numpy.ndarray or str, \
                but got {type(audio_data)}")
        
        if return_type == None:
            return audio_data
        return self.write_wave(None, [audio_data], return_type)
    
    def write_wave(self, filename, frames, return_type='io'):
        """Write audio data to a file."""
        if isinstance(frames, bytes):
            frames = [frames]
        if not isinstance(frames, list): 
            raise TypeError("frames should be \
            a list of bytes or a bytes object, \
            but got {}.".format(type(frames)))
        
        if return_type == 'io':
            if filename is None:
                filename = io.BytesIO()
            return self.write_wave_io(filename, frames) 
        elif return_type == 'bytes':
            return self.write_wave_bytes(frames)

    
    def write_wave_io(self, filename, frames):
        """Write audio data to a file-like object."""
        wf = wave.open(filename, 'wb')
        wf.setnchannels(self.CHANNELS)
        wf.setsampwidth(self.p.get_sample_size(self.FORMAT))
        wf.setframerate(self.RATE)
        wf.writeframes(b''.join(frames))
        wf.close()
        if isinstance(filename, io.BytesIO):
            filename.seek(0)   # reset file pointer to beginning
        return filename
    
    def write_wave_bytes(self, frames):
        """Write audio data to a bytes object."""
        return b''.join(frames)


# ####################################################### #
# play audio data from Speaker
# ####################################################### #

class AudioPlayer(BaseAudio):
    def __init__(self, 
                 RATE=22050, 
                 **kwargs):
        super().__init__(output=True, RATE=RATE, **kwargs)

    def play(self, audio_data):
        print("Playing audio data...")
        audio_data = self.check_audio_type(audio_data, return_type=None)
        
        for i in range(0, len(audio_data), self.CHUNK):
            self.stream.write(audio_data[i:i+self.CHUNK])
        print("Audio data played.")    

    def close(self):
        self.stream.stop_stream()
        self.stream.close()
        self.p.terminate()

# ####################################################### #
# record audio data from microphone
# ####################################################### #
class BaseRecorder(BaseAudio):
    def __init__(self, 
                 input=True, 
                 RATE=16000, 
                 **kwargs):
        super().__init__(input=input, RATE=RATE, **kwargs)

    def record(self, 
               filename,
               duration=5, 
               return_type='io'):
        print("Recording started.")
        frames = []
        for i in range(0, int(self.RATE / self.CHUNK * duration)):
            data = self.stream.read(self.CHUNK)
            frames.append(data)
        print("Recording stopped.")
        return self.write_wave(filename, frames, return_type)

    def record_chunk_voice(self, 
                           return_type='bytes', 
                           CHUNK=None, 
                           exception_on_overflow=True, 
                           queue=None):
        data = self.stream.read(self.CHUNK if CHUNK is None else CHUNK, 
                                exception_on_overflow=exception_on_overflow)
        if return_type is not None:
            return self.write_wave(None, [data], return_type)
        return data



class HDRecorder(BaseRecorder):
    def __init__(self, 
                 hd_trigger='keyboard', 
                 keyboard_key='space',
                 voice_trigger=True,
                 hd_chunk_size=2048,
                 hd_detect_threshold=50,
                 **kwargs):
        super().__init__(**kwargs)
        assert hd_trigger in ['keyboard', 'button', 'all']
        
        self.hd_trigger = hd_trigger
        self.voice_trigger = voice_trigger
        self.hd_chunk_size = hd_chunk_size
        
        self.hd_detect_threshold = hd_detect_threshold
        self.hd_lock = threading.Lock()
        self.shared_hd_status = False
        if hd_trigger == 'keyboard':
            self.keyboard_key = keyboard_key
            hd_detect_thread = threading.Thread(target=self.get_keyboard_status)
        if hd_trigger == 'button':
            self.button = self.button_init()
            hd_detect_thread = threading.Thread(target=self.get_button_status)
        hd_detect_thread.start()
        print(f"Using {hd_trigger} as hardware trigger.")
        
    def button_init(self):
        PH_BASE = (8-1)*32 #PH

        gpiochip1 = gpio.chip("gpiochip1")
        button = gpiochip1.get_line((PH_BASE+5))
        config = gpio.line_request()
        config.request_type = gpio.line_request.DIRECTION_INPUT
        config.flags = gpio.line_request.FLAG_BIAS_PULL_UP
        button.request(config)
        return button

    def get_tmp_button_status(self):
        return True if self.button.get_value() == 1 else False
        
    def get_button_status(self):
        self.shared_hd_status = False
        button_value_list = deque(maxlen=self.hd_detect_threshold)
        while True:
            if len(button_value_list) > button_value_list.maxlen:
                button_value_list.popleft()
            button_value_list.append(self.get_tmp_button_status())
            # 记录50个值，如果连续50个值都是True，则认为按钮被按下
            if button_value_list.count(True) == button_value_list.maxlen:
                with self.hd_lock:
                    self.shared_hd_status = True
            # 记录50个值，如果连续50个值都是False，则认为按钮被松开
            if button_value_list.count(False) == button_value_list.maxlen:
                with self.hd_lock:
                    self.shared_hd_status = False
    
    def get_keyboard_status(self):
        while True:
            keyboard_status = keyboard.is_pressed(self.keyboard_key)
            with self.hd_lock:
                self.shared_hd_status = keyboard_status
            time.sleep(0.001)
    
    @property
    def is_hardware_pressed(self):
        return self.shared_hd_status
    
    def wait_for_hardware_pressed(self):
        print("Waiting for hardware trigger.")
        while True:
            if self.is_hardware_pressed:
                break
        return True
    
    def record_hardware(self, return_type='bytes', queue=None):
        """record audio when hardware trigger"""
        print("Recording started for hardware trigger.")
        frames = []
        recording = True
        while recording:
            self.wait_for_hardware_pressed()
            while recording:
                if self.hd_trigger == 'keyboard':
                    if keyboard.is_pressed(self.keyboard_key):
                        data = self.stream.read(self.CHUNK)
                        frames.append(data)
                    else:
                        recording = False
                        print("Recording stopped.")
                elif self.hd_trigger == 'button':
                    if self.button.get_value() == 0:
                        if self.get_button_status():
                            data = self.stream.read(self.CHUNK)
                            frames.append(data)
                        else:
                            recording = False
                else:
                    recording = False
                    raise ValueError("hd_trigger should be 'keyboard' or 'button'.")
        return self.write_wave(self.filename, frames, return_type)
    
    '''
    def record(self, return_type='bytes', queue=None):
        if self.hd_trigger == 'all':
            value_list = []  # 用于记录value的状态
            if keyboard.is_pressed(self.keyboard_key):
                audio_data = self.record_keyboard(return_type, queue)
            elif self.button.get_value() == 0:
                if self.get_button_status():
                    audio_data = self.record_button(return_type, queue)
            else:
                audio_data = self.record_voice(return_type, queue)
        elif self.hd_trigger == 'keyboard':
            print("Press SPACE to start recording.")
            keyboard.wait("space")
            audio_data = self.record_keyboard(return_type, queue)
        elif self.hd_trigger == 'button':
            print("Touch to start recording...")
            if self.button.get_value() == 0:
                if self.get_button_status():
                    audio_data = self.record_button(return_type, queue)
        else:
            audio_data = self.record_voice(return_type, queue)
            
        return audio_data
    
    def record_keyboard(self, return_type='bytes', queue=None):
        """record audio when keyboard pressing"""
        print("Recording started.")
        frames = []
        recording = True
        while recording:
            if keyboard.is_pressed(self.keyboard_key):
                data = self.stream.read(self.CHUNK)
                frames.append(data)
            else:
                recording = False
                print("Recording stopped.")
        return self.write_wave(self.filename, frames, return_type)
        
    def record_button(self, return_type='bytes', queue=None):
        """record audio when button pressing"""
        print("Recording started.")
        frames = []
        recording = True
        while recording:
            value = self.button.get_value()
            if value == 0:
                data = self.stream.read(CHUNK)
                frames.append(data)
            else:
                recording = False
                print("Recording stopped.")
        return self.write_wave(self.filename, frames, return_type)
    '''
        
# ####################################################### #
# record audio data from microphone with VAD
# ####################################################### #
try:
    import webrtcvad
    webrtcvad_available = True
except:
    warnings.warn("webrtcvad module not found, please install it if use `vad` hd_trigger.")
    webrtcvad_available = False

class VADRecorder(HDRecorder):
    def __init__(self, vad_sensitivity=1, frame_duration=30, vad_buffer_size=7, min_act_time=1,**kwargs):
        super().__init__(**kwargs)
        if webrtcvad_available:
            self.vad = webrtcvad.Vad(vad_sensitivity)
        self.vad_buffer_size = vad_buffer_size
        self.vad_chunk_size = int(self.RATE * frame_duration / 1000)
            
        self.min_act_time = min_act_time    # 最小活动时间，单位秒
            
        self.is_currently_speaking = False
        self.frames = []

    def is_speech(self, data):
        return self.vad.is_speech(data, self.RATE)
    
    def vad_filter(self, data):
        pass
        

    def vad_record(self, return_type='io', CHUNK=None, queue=None, save_file=False):
        """录音并进行语音活动检测人声并返回分割后的音频数据"""
        all_frames = []
        
        buffer_size = self.vad_buffer_size
        active_buffer = deque([False for i in range(buffer_size)], maxlen=buffer_size)
        audio_buffer = deque(maxlen=buffer_size)
        silence_buffer = deque([True for i in range(buffer_size)], maxlen=buffer_size)
        
        print("vad_recorded_audio VAD started. Press Ctrl+C to stop.")
        try:
            while True:
                data = self.stream.read(self.vad_chunk_size)
                all_frames.append(data)
                print(f"VAD processing..., is_speech: {self.is_speech(data)}")
                if self.is_speech(data):
                    # 标志位buffer
                    active_buffer.append(True); active_buffer.popleft()
                    silence_buffer.append(False); silence_buffer.popleft()
                    # 暂时增加到buffer中
                    audio_buffer.append(data)
                    # 如果满足检测要求
                    if all(active_buffer):
                        if not self.is_currently_speaking:
                            print("Speech start detected")
                            self.is_currently_speaking = True
                            self.frames.extend(audio_buffer)   # 把说话的buffer也加上
                    if self.is_currently_speaking:
                        self.frames.append(data)
                else:
                    # 标志位buffer
                    active_buffer.append(False); active_buffer.popleft()
                    silence_buffer.append(True); silence_buffer.popleft()
                    # 检测到人声并持续录音
                    if self.is_currently_speaking:
                        # 结束标志位
                        if all(silence_buffer):
                            print("Speech end detected")
                            break
        except KeyboardInterrupt:
            print("KeyboardInterrupt")
            
        finally:
            print("Stopping...")
            if len(all_frames) > 0:
                print(f"ALL frame: {len(all_frames)}")
                print(f"ASR frame: {len(self.frames)}")
                if save_file:
                    self.write_wave(f"output_{time.time()}_all.wav", all_frames)
                    self.write_wave(f"output_{time.time()}.wav", self.frames)
            return self.write_wave(None, self.frames, return_type='bytes')
        

# ####################################################### #
# record audio data from microphone with PicoVoice hot words detection
# ####################################################### #

import struct
from datetime import datetime
import pvporcupine

class PicovoiceRecorder(VADRecorder):
    def __init__(self, 
                 access_key, 
                 keywords=None, 
                 keyword_paths=None, 
                 model_path=None, 
                 sensitivities=0.5, 
                 library_path=None,
                 **kwargs):
        super().__init__(**kwargs)
        
        pico_cfg = dict(
            access_key=access_key,
            keywords=keywords,
            keyword_paths=keyword_paths,
            model_path=model_path,
            sensitivities=sensitivities,
            library_path=library_path,
        )
        
        self.pico_detector_init(pico_cfg)
        
        self.keywords = self.pico_cfg['keywords']
        print(f"PicovoiceRecorder initialized with keywords: {self.keywords}")

    def pico_detector_init(self, pico_cfg):
        if pico_cfg['keyword_paths'] is None:
            if pico_cfg['keywords'] is None:
                raise ValueError(f"Either `--keywords` or `--keyword_paths` must be set. \
                    Available keywords: {list(pvporcupine.KEYWORDS)}")

            keyword_paths = [pvporcupine.KEYWORD_PATHS[x] for x in pico_cfg['keywords']]
        else:
            keyword_paths = pico_cfg['keyword_paths']

        if pico_cfg['sensitivities'] is None:
            pico_cfg['sensitivities'] = [0.5] * len(keyword_paths)
        elif isinstance(pico_cfg['sensitivities'], float):
            pico_cfg['sensitivities'] = [pico_cfg['sensitivities']] * len(keyword_paths)
            
        if len(keyword_paths) != len(pico_cfg['sensitivities']):
            raise ValueError('Number of keywords does not match the number of sensitivities.')
        
        try:
            self.porcupine = pvporcupine.create(
                access_key=pico_cfg['access_key'],
                keywords=pico_cfg['keywords'],
                keyword_paths=keyword_paths,
                model_path=pico_cfg['model_path'],
                sensitivities=pico_cfg['sensitivities'],
                library_path=pico_cfg['library_path'])
        except pvporcupine.PorcupineInvalidArgumentError as e:
            print("One or more arguments provided to Porcupine is invalid: ", pico_cfg.keys())
            print(e)
            raise e
        except pvporcupine.PorcupineActivationError as e:
            print("AccessKey activation error")
            raise e
        except pvporcupine.PorcupineActivationLimitError as e:
            print("AccessKey '%s' has reached it's temporary device limit" % pico_cfg['access_key'])
            raise e
        except pvporcupine.PorcupineActivationRefusedError as e:
            print("AccessKey '%s' refused" % pico_cfg['access_key'])
            raise e
        except pvporcupine.PorcupineActivationThrottledError as e:
            print("AccessKey '%s' has been throttled" % pico_cfg['access_key'])
            raise e
        except pvporcupine.PorcupineError as e:
            print("Failed to initialize Porcupine")
            raise e

        self.pico_cfg = pico_cfg
        
    def is_wakeup(self, data):
        pcm = struct.unpack_from("h" * self.porcupine.frame_length, data)
        result = self.porcupine.process(pcm)
        # print(f"picovoice result: {result}")
        if result >= 0:
            print('[%s] Detected %s' % (str(datetime.now()), self.keywords[result]))
            return True
        # self.write_wave(f"output_{time.time()}.wav", [data])
        # print(f"write to: output_{time.time()}.wav")
        return False
        

    def record_picovoice(self, return_type=None, exception_on_overflow=False, queue=None):
        
        print("Recording started. Press Ctrl+C to stop.")
        while True:
            data = self.record_chunk_voice(
                return_type=None, 
                CHUNK=self.porcupine.frame_length, 
                exception_on_overflow=exception_on_overflow, 
                queue=queue)
            
            wake_up = self.is_wakeup(data)
            if wake_up:
                break
        return True
