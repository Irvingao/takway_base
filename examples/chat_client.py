import asyncio
from takway.audio_utils import AudioPlayer
import websockets
import json
import base64
from datetime import datetime
import io
# 假设您的PCM文件路径是 'your_pcm_file.pcm'
from pydub import AudioSegment
from pydub.playback import play
pcm_file_path = 'example_recording.wav'

def read_pcm_file_in_chunks(chunk_size):
    with open(pcm_file_path, 'rb') as pcm_file:
        while True:
            data = pcm_file.read(chunk_size)
            if not data:
                break
            yield data

data = {
    "text": "",
    "audio": "",
    "meta_info": {
        "session_id":"7d0546dd-36b6-4bc2-8008-fc77c78aaa14",
        "stream": False,
        "voice_synthesize": True,
        "is_end": False,
        "encoding": "raw"
    }
}

async def send_audio_chunk(websocket, chunk):
    # 将PCM数据进行Base64编码
    encoded_data = base64.b64encode(chunk).decode('utf-8')
    # 更新data字典中的"audio"键的值为Base64编码后的音频数据
    data["audio"] = encoded_data
    # 将JSON数据对象转换为JSON字符串
    message = json.dumps(data)
    # 发送JSON字符串到WebSocket接口
    await websocket.send(message)

async def send_json():
    async with websockets.connect('ws://121.41.224.27:8000/chat') as websocket:
        chunks = read_pcm_file_in_chunks(2048)  # 读取PCM文件并生成数据块
        for chunk in chunks:
            await send_audio_chunk(websocket, chunk)
            await asyncio.sleep(0.01)  # 等待0.04秒
        # 设置data字典中的"is_end"键为True，表示音频流结束
        data["meta_info"]["is_end"] = True
        # 发送最后一个数据块和流结束信号
        await send_audio_chunk(websocket, b'')  # 发送空数据块表示结束
        # 等待并打印接收到的数据

        print("等待接收:",datetime.now())
        audio_bytes = b''
        while True:
            data_ws = await websocket.recv()
            try:
                message_json = json.loads(data_ws)
                print(message_json)  # 打印接收到的消息
                if message_json["type"] == "close":
                    break  # 如果没有接收到消息，则退出循环
            except Exception as e:
                audio_bytes += data_ws
                print(e)
        print("接收完毕:", datetime.now())


        await asyncio.sleep(0.04)  # 等待0.04秒后断开连接
        await websocket.close()

# 启动事件循环
try:
    asyncio.run(send_json())
except websockets.exceptions.ConnectionClosedOK:
    print("成功")
