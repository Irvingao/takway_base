from takway.audio_utils import BaseRecorder
from takway.audio_utils import AudioPlayer
from takway.audio_utils import reshape_sample_rate

RATE = 16000
channels = 1
device_idx = None

if __name__ == '__main__':
    # 读取录音文件并播放
    # audio_player = AudioPlayer(RATE=44100)
    # frames = audio_player.load_audio_file("my_recording.wav") # wav或pcm格式音频都支持
    # audio_player.play(frames)
    
    
    # 录音并保存
    recorder = BaseRecorder(RATE=RATE, channels=channels, input_device_index=device_idx)
    recorder.record("my_recording.wav", # save as my_recording.wav
             duration=5) # record for 5 seconds
    
    
    audio_player = AudioPlayer(RATE=RATE, channels=channels, output_device_index=device_idx)
    frames = audio_player.load_audio_file("my_recording.wav") # wav或pcm格式音频都支持
    audio_player.play(frames)
    

        
    '''
    from takway.audio_utils import HDRecorder

    recorder = HDRecorder(filename="hd_recording.wav")
    # recorder = HDRecorder(filename="hd_recording.pcm")

    recorder.record_hardware(return_type='io')
    '''