
from takway.vits_utils import TextToSpeech
from takway.audio_utils import AudioPlayer

def test_vits_saver(text='你好呀,我不知道该怎么告诉你这件事，但是我真的很需要你。', speaker_id=103, noise_scale=0.1, noise_scale_w=0.668, length_scale=1.2):
    
    tts = TextToSpeech(device='cuda')  # 初始化，设定使用的设备
    sr, audio = tts.synthesize(text, 0, speaker_id, noise_scale, noise_scale_w, length_scale)  # 生成语音
    tts.save_audio(audio, sr)  # 保存语音文件
    

def test_vits_player(text='你好呀,我不知道该怎么告诉你这件事，但是我真的很需要你。', speaker_id=103, noise_scale=0.1, noise_scale_w=0.668, length_scale=1.2):
    RATE = 22050  # 采样率
    tts = TextToSpeech(device='cuda', RATE=RATE)  # 初始化，设定使用的设备
    player = AudioPlayer(RATE=RATE)
    
    sr, audio = tts.synthesize(text, 0, speaker_id, noise_scale, noise_scale_w, length_scale)  # 生成语音
    # sr, audio = tts.synthesize(text, 0, speaker_id, 0.1, 0.668, 1.2)  # 生成语音
    # tts.save_audio(audio, sr)  # 保存语音文件
    
    player.play(audio)
    print('播放完成')