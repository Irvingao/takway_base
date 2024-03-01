from takway.vosk_utils import AutoSpeechRecognizer
from takway.audio_utils import Recorder

'''
import time
import webrtcvad
from collections import deque

class VADRecorder(Recorder):
    def __init__(self, vad_sensitivity=1, frame_duration=30, silence_threshold=20,**kwargs):
        super().__init__(**kwargs)
        self.vad = webrtcvad.Vad(vad_sensitivity)
        self.vad_chunk_size = int(self.RATE * frame_duration / 1000)
        
        self.silence_buffer = deque(maxlen=silence_threshold)  # 用于存储连续的静默帧
        self.is_currently_speaking = False
        self.frames = []

    def is_speech(self, data):
        return self.vad.is_speech(data, self.RATE)

    def run(self, return_type='io', CHUNK=None, queue=None):
        all_frames = []
        print("Enhanced VAD started. Press Ctrl+C to stop.")
        try:
            while True:
                data = self.stream.read(self.vad_chunk_size)
                all_frames.append(data)
                print(f"VAD processing..., is_speech: {self.is_speech(data)}")
                if self.is_speech(data):
                    if not self.is_currently_speaking:
                        print("Speech start detected")
                        self.is_currently_speaking = True
                        # self.frames.extend(self.silence_buffer)  # 把静默帧也加进去，为了保留前导静默
                    self.frames.append(data)
                    self.silence_buffer.clear()
                else:
                    if self.is_currently_speaking:
                        
                        # self.silence_buffer.append(data)
                        if len(self.silence_buffer) == self.silence_buffer.maxlen:
                            print("Speech end detected")
                            # self.save_frames(filename=f"output_{time.now()}.wav")
                            self.is_currently_speaking = False
                            self.frames = []
                            self.silence_buffer.clear()
                    else:
                        self.silence_buffer.append(data)
                
        except KeyboardInterrupt:
            print("Stopping...")
            if len(all_frames) > 0:
                self.save_frames(all_frames, filename=f"output_{time.time()}_all.wav")
                self.save_frames(self.frames, filename=f"output_{time.time()}.wav")
                
            return self.write_wave(None, self.frames, return_type='bytes')

    def save_frames(self, frames, filename="output.wav"):
        import wave
        wf = wave.open(filename, 'wb')
        wf.setnchannels(self.CHANNELS)
        wf.setsampwidth(self.p.get_sample_size(self.FORMAT))
        wf.setframerate(self.RATE)
        wf.writeframes(b''.join(frames))
        wf.close()
        print(f"Saved {filename}, {len(frames)}")


class VADRecorderV2(Recorder):
    def __init__(self, vad_sensitivity=1, frame_duration=30, silence_threshold=10,**kwargs):
        super().__init__(**kwargs)
        self.vad = webrtcvad.Vad(vad_sensitivity)
        self.vad_chunk_size = int(self.RATE * frame_duration / 1000)
        
        self.silence_buffer = deque([True for i in range(silence_threshold)], maxlen=silence_threshold)  # 用于存储连续的静默帧
        self.is_currently_speaking = False
        self.frames = []

    def is_speech(self, data):
        return self.vad.is_speech(data, self.RATE)

    def run(self, return_type='io', CHUNK=None, queue=None):
        all_frames = []
        print("Enhanced VAD started. Press Ctrl+C to stop.")
        try:
            while True:
                data = self.stream.read(self.vad_chunk_size)
                all_frames.append(data)
                print(f"VAD processing..., is_speech: {self.is_speech(data)}")
                if self.is_speech(data):
                    if not self.is_currently_speaking:
                        print("Speech start detected")
                        self.is_currently_speaking = True
                        # self.frames.extend(self.silence_buffer)  # 把静默帧也加进去，为了保留前导静默
                    self.frames.append(data)
                    self.silence_buffer.clear()
                else:
                    if self.is_currently_speaking:
                        
                        # self.silence_buffer.append(data)
                        if len(self.silence_buffer) == self.silence_buffer.maxlen:
                            print("Speech end detected")
                            # self.save_frames(filename=f"output_{time.now()}.wav")
                            self.is_currently_speaking = False
                            self.frames = []
                            self.silence_buffer.clear()
                    else:
                        self.silence_buffer.append(data)
        except KeyboardInterrupt:
            print("Stopping...")
            if len(all_frames) > 0:
                self.write_wave(f"output_{time.time()}_all.wav", all_frames)
                self.write_wave(f"output_{time.time()}.wav", self.frames)
            return self.write_wave(None, self.frames, return_type='bytes')

    def vad_recorded_audio(self):
        """录音并进行语音活动检测人声并返回分割后的音频数据"""
        all_frames = []
        
        buffer_size = 5
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
                print(f"all frame: {len(all_frames)}")
                print(f"speech frame: {len(self.frames)}")
                self.write_wave(f"output_{time.time()}_all.wav", all_frames)
                self.write_wave(f"output_{time.time()}.wav", self.frames)
            return self.write_wave(None, self.frames, return_type='bytes')
'''

def vad_vosk_test_pc():
    import time
    # keywords = ['你好', '早上好', '晚上好']
    
    asr = AutoSpeechRecognizer(cfg_path=r'takway/configs/vosk_cfg.json')

    from takway.audio_utils import VADRecorder as Rec
    recorder = Rec()
    
    while True:
        # audio_data = recorder.run()
        # audio_data = recorder.vad_recorded_audio()
        audio_data = recorder.vad_record(return_type='bytes', save_file=True)
        
        print("Got audio data")
        t1 = time.time()
        # kw_trgrigger_status, text = asr.recognize_keywords(audio_data)
        res = asr.partial_recognize(audio_data, partial_size=2048)
        
        print(f"Partial recognize time: {time.time()-t1} s")
        break
        

def main():
    vad_vosk_test_pc()

if __name__ == '__main__':
    main()