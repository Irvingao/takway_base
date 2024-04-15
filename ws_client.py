from takway.clients.web_socket_client_utils import WebSocketClinet
import pvporcupine
import pyaudio

if __name__ == '__main__':
    
    server_url = 'ws://121.41.224.27:8000/chat'
    
    try:
        import gpiod as gpio
        emo_dir="ResizedEmoji"
        
        
        keywords = ['hey google', 'ok google']
        keyword_paths = None
        model_path = None
        
        keywords = ['可莉可莉']
        keyword_paths = [r"picovoice_models/可莉可莉_zh_raspberry-pi_v3_0_0.ppn"]
        model_path = r"picovoice_models/porcupine_params_zh.pv"
        
        hd_trigger = 'button'
        player = 'maixsense'
        # server_url = 'http://192.168.1.106:5000/character-chat'
        emo_enable = False
        
    except:
        # model_path=r"G:\WorkSpace\CodeWorkspace\GPT_projects\vits_project\vits-uma-genshin-honkai\vosk-model-small-cn-0.22"
        emo_dir=r"G:\WorkSpace\CodeWorkspace\GPT_projects\vits_project\vits-uma-genshin-honkai\ResizedEmoji"
        
        keywords = ['hey google', 'ok google']
        keyword_paths = None
        model_path = None
        
        hd_trigger = 'keyboard'
        player = 'opencv'
        
        # server_url = 'http://127.0.0.1:5000/character-chat'
        # server_url = 'http://10.10.42.227:5000/character-chat'
        
        emo_enable = False
        
    character = 'Klee_test_v2_en'
    character = '蕾'
    # character = 'Taijian'
    
    import argparse
    parser = argparse.ArgumentParser()
    # server params
    parser.add_argument('--server_url', type=str, default=server_url, help='Server url')
    parser.add_argument('--character_data_dir', type=str, default='characters', help='Character data dir')
    parser.add_argument('--character', type=str, default=character, help='Character name')
    # audio paramters
    parser.add_argument('--voice_trigger', type=bool, default=True, help='Voice trigger')
    # recorder paramters
    ACCESS_KEY = 'hqNqw85hkJRXVjEevwpkreB8n8so3w9JPQ27qnCR5qTH8a3+XnkZTA=='
    parser.add_argument('--access_key',default=ACCESS_KEY,
        help='AccessKey obtained from Picovoice Console (https://console.picovoice.ai/)')
    
    parser.add_argument('--keywords',nargs='+',choices=sorted(pvporcupine.KEYWORDS),type=list,
        # default=['可莉可莉'],
        # default=['hey google', 'ok google'],
        # default=None,
        default=keywords,
        help='List of default keywords for detection. Available keywords: %s' % ', '.join(
        '%s' % w for w in sorted(pvporcupine.KEYWORDS)),metavar='')
    parser.add_argument('--keyword_paths',nargs='+',
        # default=[r"picovoice_models/可莉可莉_zh_raspberry-pi_v3_0_0.ppn"],
        # default=None,
        default=keyword_paths,
        help="Absolute paths to keyword model files. If not set it will be populated from `--keywords` argument")
    parser.add_argument('--library_path',default=None,
        help='Absolute path to dynamic library. Default: using the library provided by `pvporcupine`')
    parser.add_argument('--model_path',
        default=model_path,
        # default=None,
        # default=r"picovoice_models/porcupine_params_zh.pv",
        help='Absolute path to the file containing model parameters. '
             'Default: using the library provided by `pvporcupine`')
    parser.add_argument('--sensitivities',type=float,
        default=0.5,
        help="Sensitivities for detecting keywords. Each value should be a number within [0, 1]. A higher "
             "sensitivity results in fewer misses at the cost of increasing the false alarm rate. If not set 0.5 "
             "will be used.")
    parser.add_argument('--hd_trigger', type=str, 
                        # default='keyboard', 
                        default=hd_trigger, 
                        help='Hardware trigger')
    parser.add_argument('--keyboard_key', type=str, default='space', help='Keyboard key')
    parser.add_argument('--CHUNK', type=int, default=3840, help='Record chunk size')    # 原来的
    parser.add_argument('--RATE', type=int, default=16000, help='Audio rate')
    parser.add_argument('--FORMAT', type=int, default=16, help='Audio format')
    parser.add_argument('--CHANNELS', type=int, default=1, help='Audio channels')
    parser.add_argument('--filename', type=str, default=None, help='Audio file name')
    # local record paramters
    parser.add_argument('--min_stream_record_time', type=int, default=0.8, help='Min stream record time, sec')
    # video paramters
    parser.add_argument('--player', type=str, 
                        default=player, 
                        help='Video player')
    parser.add_argument('--width', type=int, default=1280, help='Video width')
    parser.add_argument('--height', type=int, default=720, help='Video height')
    # emo paramters
    # emo_dir="ResizedEmoji"
    # emo_dir=r"G:\WorkSpace\CodeWorkspace\GPT_projects\vits_project\vits-uma-genshin-honkai\ResizedEmoji"
    parser.add_argument('--emo_enable', type=bool, default=emo_enable, help='Emo enable')
    parser.add_argument('--emo_dir', type=str, default=emo_dir, help='Emo dir')
    # log paramters
    parser.add_argument('--log_file', type=str, default='my.log', help='Log file')
    parser.add_argument('--log_level', type=str, default='INFO', help='Log level')
    
    parser.add_argument('--debug', type=bool, default=False, help='Debug mode')
    args = parser.parse_args()
    
    
    # sort out args and params
    server_args = {
       'server_url': args.server_url,
       'character_data_dir': args.character_data_dir,
       'character': args.character,
    }
    
    recorder_args = {
        'access_key': args.access_key,
        'keywords': args.keywords,
        'keyword_paths': args.keyword_paths,
        'library_path': args.library_path,
        'model_path': args.model_path,
        'sensitivities': args.sensitivities,
        'hd_trigger': args.hd_trigger,
        'keyboard_key': args.keyboard_key,
        'voice_trigger': args.voice_trigger,
        'CHUNK': args.CHUNK,
        'FORMAT': pyaudio.paInt16 if args.FORMAT == 16 else pyaudio.paInt32,
        'CHANNELS': args.CHANNELS,
        'RATE': args.RATE,
        'filename': args.filename,
        'min_stream_record_time': args.min_stream_record_time,
    }
    
    video_args = {
        'device': args.player,
        'width': args.width,
        'height': args.height,
    }
    
    emo_args = {
        'enable': args.emo_enable,
        'player': args.player,
        'emo_dir': args.emo_dir,
    }
    
    log_args = {
        'log_file': args.log_file,
        'log_level': args.log_level,
    }
    
    
    localclient = WebSocketClinet(
        server_args=server_args, 
        recorder_args=recorder_args, 
        log_args=log_args)
    localclient.process_init()