

from takway.tts.vits_utils import TextToSpeech

def save_text2audio_example(text='你好呀,我不知道该怎么告诉你这件事，但是我真的很需要你。', speaker_id=103, noise_scale=0.1, noise_scale_w=0.668, length_scale=1.2, file_name='example.wav'):
    
    tts = TextToSpeech(device='cuda')  # 初始化，设定使用的设备
    sr, audio = tts.synthesize(text, 0, speaker_id, noise_scale, noise_scale_w, length_scale)  # 生成语音
    tts.save_audio(audio, sr, file_name=file_name)  # 保存语音文件


def text2audio_example():
    length = 1.0
    
    # speaker_id = 87 # 神里绫华（龟龟）
    speaker_id = 92 # 芭芭拉
    # speaker_id = 103
    # speaker_id=111 # 成熟甜
    # speaker_id=125  # 成熟深沉
    # speaker_id=132  # 成熟冷酷
    
    example_text = "晚上好呀！今天怎么看起来这么累，刚回来就趴着不动了。"
    
    save_text2audio_example(example_text, speaker_id, length_scale=length)


if __name__ == '__main__':
    text2audio_example()