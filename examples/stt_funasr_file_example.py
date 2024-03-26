from takway.audio_utils import BaseRecorder
from takway.stt.funasr_utils import FunAutoSpeechRecognizer

def asr_file(file_path='my_recording.wav'):
    rec = BaseRecorder()
    
    data = rec.load_audio_file(file_path)
        
    asr = FunAutoSpeechRecognizer()
    
    res = asr.recognize(data)
    print(res)

    
def asr_file_stream(file_path='my_recording.wav'):
    rec = BaseRecorder()
    
    data = rec.load_audio_file(file_path)
        
    asr = FunAutoSpeechRecognizer()

    text_dict = asr.streaming_recognize(data, auto_det_end=True)
    print(text_dict)
    
    transcription = ''.join(text_dict['text'])
    print(transcription)
    # {'text': ['', '啊', '你吃', '什么', '饭晚', '', '上我想', '吃红', '烧', '肉和', '兰州牛肉'], 'is_end': True}
        
if __name__ == '__main__':
    asr_file_stream()