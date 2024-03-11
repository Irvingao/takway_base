# from takway.app_utils import app, TakwayApp
from takway.app_utils import *
# from takway.apps.flask_app import *
from flask import request, Response

@app.route('/character-chat', methods=['POST'])
def handle_all():
    
    takway_app.stream_request_receiver_process()
    # audio_data, text_data, image_data = takway_app.preprocess_request(request.get_json())
    # time.sleep(1000)
    return Response(takway_app.generate_stream_queue_data())
        

if __name__ == "__main__":
    
    asr_cfg={
        'model_path': 'vosk-model-small-cn-0.22',
        'RATE': 16000,
    }
    
    tts_cfg={
        'model_path': 'vits-small-patch16-22k-v2',
        'device': 'cuda',
    }
    
    spark_cfg = dict(
        appid="fb646f00",    #填写控制台中获取的 APPID 信息
        api_key="f71ea3399c4d73fe3f6df093f7811a0d",    #填写控制台中获取的 APIKey 信息
        api_secret="Njc2M2E3Y2FjMDRjMDhjNjViNTYwOTE1",   #填写控制台中获取的 APISecret 信息
        stream=True,
        spark_version="3.5",
        character_data_dir="characters",
    )
    
    takway_app = TakwayApp(app, asr_cfg=asr_cfg, tts_cfg=tts_cfg, llm_cfg=spark_cfg, debug=False)
    
    takway_app.start_app(app)