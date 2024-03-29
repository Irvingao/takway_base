from takway.app_utils import *
from flask import Response

@app.route('/character-chat', methods=['POST'])
def handle_all():
    
    takway_app.stream_request_receiver_process()
    return Response(takway_app.generate_stream_queue_data())
        

if __name__ == "__main__":
    multiprocessing.set_start_method('spawn')
    import torch; device = 'cuda' if torch.cuda.is_available() else 'cpu'
    
    asr_cfg={
        'model_path': 'paraformer-zh-streaming',
        'device': device,
    }
    
    tts_cfg={
        'model_path': 'vits-small-patch16-22k-v2',
        'device': device,
    }
    
    spark_cfg = dict(
        model="spark",
        appid="fb646f00",    #填写控制台中获取的 APPID 信息
        api_key="f71ea3399c4d73fe3f6df093f7811a0d",    #填写控制台中获取的 APIKey 信息
        api_secret="Njc2M2E3Y2FjMDRjMDhjNjViNTYwOTE1",   #填写控制台中获取的 APISecret 信息
        stream=True,
        spark_version="3.5",
        character_data_dir="characters",
    )
    
    llm_cfg = dict(
        # base_url="http://10.10.42.227:8000/v1",
        base_url="http://10.10.230.12:22853/v1",
        model="internlm2-chat-1_8b",
        web_llm=False,
    )
    
    web_llm_cfg = dict(
        # model_path="min-max-scaler.pkl",
        web_llm=True,
    )
    
    
    takway_app = TakwayApp(app, asr_cfg=asr_cfg, tts_cfg=tts_cfg, llm_cfg=web_llm_cfg, debug=False)
    
    takway_app.start_app(app)