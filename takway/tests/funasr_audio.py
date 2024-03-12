from takway.audio_utils import BaseRecorder, HDRecorder
from takway.stt.funasr_utils import FunAutoSpeechRecognizer


def test_asr_file(file_path='my_recording.wav'):
    rec = BaseRecorder()
    
    data = rec.load_audio_file(file_path)
        
    asr = FunAutoSpeechRecognizer()
    
    # asr.recognize(data)
    '''
    total_chunk_num = int((len(data)-1)/rec.CHUNK+1)
    print(f"total_chunk_num: {total_chunk_num}")
    for i in range(total_chunk_num):
        is_end = i == total_chunk_num - 1
        speech_chunk = data[i*rec.CHUNK:(i+1)*rec.CHUNK]
        text_dict = asr.streaming_recognize(speech_chunk, is_end)
    '''
    text_dict = asr.streaming_recognize(data, is_end=True)
        
def test_asr_microphone():
    recorder = HDRecorder(voice_trigger=False, CHUNK=3840)
    
    asr = FunAutoSpeechRecognizer(device='cpu')
    
    while True:
        data = recorder.record_hardware()
        text_dict = asr.streaming_recognize(data, auto_det_end=True)
        
        
if __name__ == '__main__':
    # test_asr_file()
    test_asr_microphone()