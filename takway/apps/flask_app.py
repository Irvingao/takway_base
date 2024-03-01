from flask import Flask, request, Response
import json
from ..common_utils import *
from ..vosk_utils import VOSKAutoSpeechRecognizer
from ..vits_utils import TextToSpeech
from ..sparkapi_utils import SparkChatClient
import asyncio

app = Flask(__name__)

class APPProcessor:
    def __init__(self, 
                 vosk_model_path='vosk-model-small-cn-0.22',
                 vits_model_path='vits-small-patch16-22k-v2',
                 sample_rate=16000,
                 stream_timeout=10,
                 device='cuda',
                 debug=False,
                 spark_cfg=None,
                 **kwargs):
        super().__init__(**kwargs)
        
        self.stream_timeout = stream_timeout

        '''
        self.vosk_asr = VOSKAutoSpeechRecognizer(
            model_path=vosk_model_path,
            RATE=sample_rate,
            efficent_mode=True,
            debug=debug,
        )
        '''
        
        self.spark_api = SparkChatClient(
            appid=spark_cfg['appid'],
            api_key=spark_cfg['api_key'],
            api_secret=spark_cfg['api_secret'],
            stream=spark_cfg['stream'],
            spark_version=spark_cfg['spark_version'],
            debug=debug,
        )
        '''
        self.vits = TextToSpeech(
            model_path=vits_model_path,
            device=device,
            debug=debug,
        )
        '''

        '''
    async def recognize_speech(self, stream):
        while True:
            data = stream.read(4096)
            if not data:
                break
            if self.recognizer.AcceptWaveform(data):
                result = json.loads(self.recognizer.Result())
                await self.handle_recognized_text(result['text'])

    async def handle_recognized_text(self, text):
        # 将识别的文字发送给大模型对话生成模块，并接收回复
        generated_text = self.generate_dialogue(text)
        # 将生成的对话传输给TTS模块处理，并以流式形式返回
        return self.stream_tts_response(generated_text)
        '''
    
    async def handle_request(self, request):
        # 处理请求，返回响应
        print(f"Received request: {request}")
        await self.stream_tts_response(request['text'])

    def generate_dialogue(self, text):
        # 这里应该有与大模型对话生成模块的交互
        # 暂时用假数据表示
        return f"Processed dialogue for: {text}"

    async def stream_tts_response(self, text):
        # 这里应该有与TTS模块的交互
        # 暂时模拟一个流式响应
        print(f"Streaming TTS response: {text}")
        def generate_stream():
            for word in text.split():
                # 假设每个单词由TTS处理后返回
                print(f"Processing word: {word}")
                yield word + " "
        return Response(generate_stream(), status=200)


if __name__ == '__main__':
    @app.route('/character-chat', methods=['POST'])
    def handle_speech():
        return asyncio.run(processor.handle_request(request.get_json()))

    app.run(host='0.0.0.0', port=5000, debug=True)
