import asyncio
import time
import websockets
import json
import base64

# 假设您的PCM文件路径是 'your_pcm_file.pcm'
pcm_file_path = 'iat_pcm_16k.pcm'

def read_pcm_file_in_chunks(chunk_size):
    with open(pcm_file_path, 'rb') as pcm_file:
        while True:
            data = pcm_file.read(chunk_size)
            if not data:
                break
            yield data

data = {
    "text": "你好啊，可以给我介绍一下你自己吗？",
    "audio": "",
    "meta_info": {
        "session_id":"88f1beae-fd7f-4490-91e3-a4b46112ad05",
        "stream": True,
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
    async with websockets.connect('ws://114.214.236.207:7878/chat') as websocket:
        chunks = read_pcm_file_in_chunks(2048)  # 读取PCM文件并生成数据块
        for chunk in chunks:
            await send_audio_chunk(websocket, chunk)
            await asyncio.sleep(0.01)  # 等待0.04秒
        # 设置data字典中的"is_end"键为True，表示音频流结束
        data["meta_info"]["is_end"] = True
        # 发送最后一个数据块和流结束信号
        await send_audio_chunk(websocket, b'')  # 发送空数据块表示结束
        # 等待并打印接收到的数据

        if data["meta_info"]["voice_synthesize"]:
            while True:
                bytes = await websocket.recv()
                #这里收到音频二进制流处理
                print(bytes)
                if bytes == "CLOSE_CONNECTION":
                    break  # 如果没有接收到消息，则退出循环
                time.sleep(0.04)
        else:
            while True:
                message = await websocket.recv()  #
                if message == "CLOSE_CONNECTION":
                    break  # 如果没有接收到消息，则退出循环
                print(message)  # 打印接收到的消息

        await asyncio.sleep(0.04)  # 等待0.04秒后断开连接
        await websocket.close()

# 启动事件循环
try:
    asyncio.run(send_json())
except websockets.exceptions.ConnectionClosedOK:
    print("成功")
