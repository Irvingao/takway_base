from takway.audio_utils import PicovoiceRecorder

ACCESS_KEY = 'hqNqw85hkJRXVjEevwpkreB8n8so3w9JPQ27qnCR5qTH8a3+XnkZTA=='

def google_wakeup():
    recorder = PicovoiceRecorder(access_key=ACCESS_KEY, sensitivities=0.9, keywords=['hey google', 'ok google'])
    recorder.record_picovoice(exception_on_overflow=False)
    
def siri_wakeup():
    recorder = PicovoiceRecorder(access_key=ACCESS_KEY, sensitivities=0.9, keywords=['hey siri'])
    recorder.record_picovoice(exception_on_overflow=False)
    
def custom_wakeup(keyword):
    if isinstance(keyword, str):
        keyword = [keyword]
    if not isinstance(keyword, list):
        raise ValueError("keyword should be [list] type")
    recorder = PicovoiceRecorder(access_key=ACCESS_KEY, sensitivities=0.9, keywords=keyword)
    recorder.record_picovoice(exception_on_overflow=False)

def klee_wakeup():
    recorder = PicovoiceRecorder(
        access_key=ACCESS_KEY, 
        sensitivities=0.9, 
        keywords=['可莉可莉'], 
        keyword_paths=[r"picovoice_models/可莉可莉_zh_raspberry-pi_v3_0_0.ppn"],
        model_path=r"picovoice_models/porcupine_params_zh.pv",
    )
    recorder.record_picovoice(exception_on_overflow=False)