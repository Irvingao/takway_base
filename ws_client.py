from takway.clients.web_socket_client_utils import WebSocketClinet
import pvporcupine
import pyaudio
import platform


if __name__ == '__main__':
    
    # server_url = 'ws://121.41.224.27:8000/chat'
    # server_url = 'ws://39.107.254.69:33089/chat'
    server_url = 'wss://takway-ai.kingtous.cn/chat/streaming'
    # server_url = 'ws://114.214.236.207:7878/chat/streaming'
    
    session_id = 'b5923335-a0dd-4d50-b3bf-5ce2a50894ed'
    
    excute_args = {'enable': True}
    
    ACCESS_KEY = 'hqNqw85hkJRXVjEevwpkreB8n8so3w9JPQ27qnCR5qTH8a3+XnkZTA=='
    
    system = platform.system()
    if system == 'Windows':
        print("WebSocketClinet runs on Windows system.")
        board = None
    elif system == 'Linux':
        # board = 'v329'
        board = 'orangepi'
    
    mircophone_device = None
    speaker_device = None
    
    
    if board == 'v329':
        import gpiod as gpio
        
        keywords = ['hey google', 'ok google']
        keyword_paths = None
        model_path = None
        
        keywords = ['可莉可莉']
        keyword_paths = [r"picovoice_models/可莉可莉_zh_raspberry-pi_v3_0_0.ppn"]
        model_path = r"picovoice_models/porcupine_params_zh.pv"
        
        hd_trigger = 'button'
        player = 'maixsense'
    elif board == 'orangepi':
        
        keywords = ['hey google', 'ok google']
        keyword_paths = None
        model_path = None
        
        hd_trigger = 'button'
        
        mircophone_device = 2
        speaker_device = 2
        
    else:

        keywords = ['hey google', 'ok google']
        keyword_paths = None
        model_path = None
        
        hd_trigger = 'keyboard'
        player = 'opencv'
        
    
    import argparse
    parser = argparse.ArgumentParser()
    # server params
    
    
    # recorder paramters
    parser.add_argument('--voice_trigger', type=bool, default=True, help='Voice trigger')
    parser.add_argument('--access_key',default=ACCESS_KEY,
        help='AccessKey obtained from Picovoice Console (https://console.picovoice.ai/)')
    parser.add_argument('--keywords',nargs='+',choices=sorted(pvporcupine.KEYWORDS),type=list,
        default=keywords,
        help='List of default keywords for detection. Available keywords: %s' % ', '.join(
        '%s' % w for w in sorted(pvporcupine.KEYWORDS)),metavar='')
    parser.add_argument('--keyword_paths',nargs='+',
        default=keyword_paths,
        help="Absolute paths to keyword model files. If not set it will be populated from `--keywords` argument")
    parser.add_argument('--library_path',default=None,
        help='Absolute path to dynamic library. Default: using the library provided by `pvporcupine`')
    parser.add_argument('--model_path',
        default=model_path,
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
    parser.add_argument('--IN_CHUNK', type=int, default=3840, help='Record chunk size')    # 原来的
    parser.add_argument('--IN_RATE', type=int, default=16000, help='Audio rate')
    parser.add_argument('--IN_FORMAT', type=int, default=16, help='Audio format')
    parser.add_argument('--IN_CHANNELS', type=int, default=1, help='Audio channels')
    parser.add_argument('--IN_filename', type=str, default=None, help='Audio file name')
    parser.add_argument('--IN_frames_per_buffer', type=int, default=1024, help='Frames per buffer')
    # local record paramters
    parser.add_argument('--min_stream_record_time', type=int, default=0.8, help='Min stream record time, sec')
    parser.add_argument('--mircophone_device', type=int, default=mircophone_device, help='Microphone device index')
    
    
    
    # player paramters
    parser.add_argument('--speaker_device', type=int, default=speaker_device, help='Speaker device index')
    parser.add_argument('--OUT_CHUNK', type=int, default=1024, help='Player chunk size')
    parser.add_argument('--OUT_RATE', type=int, default=22050, help='Player audio rate')
    parser.add_argument('--OUT_FORMAT', type=int, default=16, help='Player audio format')
    parser.add_argument('--OUT_CHANNELS', type=int, default=1, help='Player audio channels')
    parser.add_argument('--OUT_filename', type=str, default=None, help='Player audio file name')
    parser.add_argument('--OUT_frames_per_buffer', type=int, default=11025, help='Player frames per buffer')
    
    # log paramters
    parser.add_argument('--log_file', type=str, default='ws_client.log', help='Log file')
    parser.add_argument('--log_level', type=str, default='INFO', help='Log level')
    
    parser.add_argument('--debug', type=bool, default=False, help='Debug mode')
    args = parser.parse_args()
    
    # sort out args and params
    server_args = {
       'server_url': server_url,
       'session_id': session_id,
    }
    
    recorder_args = {
        'board': board,
        'access_key': args.access_key,
        'keywords': args.keywords,
        'keyword_paths': args.keyword_paths,
        'library_path': args.library_path,
        'model_path': args.model_path,
        'sensitivities': args.sensitivities,
        'hd_trigger': args.hd_trigger,
        'keyboard_key': args.keyboard_key,
        'voice_trigger': args.voice_trigger,
        'CHUNK': args.IN_CHUNK,
        'FORMAT': pyaudio.paInt16 if args.IN_FORMAT == 16 else pyaudio.paInt32,
        'CHANNELS': args.IN_CHANNELS,
        'RATE': args.IN_RATE,
        'min_stream_record_time': args.min_stream_record_time,
        'input_device_index': args.mircophone_device,
        'frames_per_buffer': args.IN_frames_per_buffer,
    }
    
    player_args = {
        'output_device_index': args.speaker_device,
        'CHUNK': args.OUT_CHUNK,
        'FORMAT': pyaudio.paInt16 if args.OUT_FORMAT == 16 else pyaudio.paInt32,
        'CHANNELS': args.OUT_CHANNELS,
        'RATE': args.OUT_RATE,
        'filename': args.OUT_filename,
        'frames_per_buffer': args.OUT_frames_per_buffer,
    }
    
    log_args = {
        'log_file': args.log_file,
        'log_level': args.log_level,
    }
    
    
    localclient = WebSocketClinet(
        board=board, 
        server_args=server_args, 
        recorder_args=recorder_args, 
        player_args=player_args,
        excute_args=excute_args,
        log_args=log_args)
    localclient.process_init()