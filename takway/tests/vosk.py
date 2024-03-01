

def vosk_test_pc():
    from ..vosk_utils import AutoSpeechRecognizer
    from ..audio_utils import Recorder

    keywords = ['你好', '早上好', '晚上好']
    
    asr = AutoSpeechRecognizer()
    asr.add_keyword(keywords)
    
    recorder = Recorder()

    while True:
        audio_data = recorder.record_chunk_voice(CHUNK=16000)
        kw_trgrigger_status, text = asr.recognize_keywords(audio_data)

def vosk_test_edge():
    from ..vosk_utils import AutoSpeechRecognizer
    from ..audio_utils import Recorder

    keywords = ['你好', '早上好', '晚上好']
    
    asr = AutoSpeechRecognizer()
    print("init ASR successfully.")
    asr.add_keyword(keywords)
    
    recorder = Recorder(hd_trigger='button', RATE=8000)
    print("init Recorder successfully.")

    while True:
        audio_data = recorder.record_chunk_voice(CHUNK=2000)
        kw_trgrigger_status, text = asr.recognize_keywords(audio_data)
