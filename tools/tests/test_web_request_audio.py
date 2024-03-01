# 服务器的URL
server_url = 'http://127.0.0.1:5000/process_all'

import requests
import pyaudio
import io
import base64

def send_data(text, audio_file_path, image_file_path):
    """同时发送文本、语音和图像数据到服务器"""

    # 准备文本数据
    data = {'text': text}

    # 准备文件数据
    files = {}
    if audio_file_path:
        files['audio'] = open(audio_file_path, 'rb')
    if image_file_path:
        files['image'] = open(image_file_path, 'rb')

    # 发送请求
    response = requests.post(server_url, data=data, files=files)

    # 关闭文件
    for file in files.values():
        file.close()

    return response.json()

def send_data_and_play_audio(text, audio_file_path, image_file_path, character="Klee"):
    # 准备请求数据
    data = {'text': text, 'character': character}
    files = {}
    if audio_file_path:
        files['audio'] = open(audio_file_path, 'rb')
    if image_file_path:
        files['image'] = open(image_file_path, 'rb')

    # 发送数据到服务器
    response = requests.post(server_url, data=data, files=files)
    print("Response:", response)

    # 关闭文件
    for file in files.values():
        file.close()

    # 检查响应状态并播放音频
    if response.status_code == 200:
        # print(response.json())
        # 使用PyAudio播放音频流
        audio_base64 = response.json()['audio_base64']

        # 将base64编码的音频解码为原始字节流
        audio_bytes = base64.b64decode(audio_base64)
        # 使用PyAudio播放解码后的音频
        play_audio(audio_bytes)
        print("Audio played successfully")
    else:
        print("Error: Server responded with status code", response.status_code)

def play_audio(audio_data):
    # PyAudio配置
    p = pyaudio.PyAudio()
    stream = p.open(format=pyaudio.paInt16, channels=1, rate=22050, output=True)

    # 播放音频
    stream.write(audio_data)
    stream.stop_stream()
    stream.close()
    p.terminate()



if __name__ == '__main__':  
    # 示例：同时发送文本、语音和图像数据
    # response = send_data("Hello, World!", "path_to_audio_file.wav", "path_to_image_file.jpg")
    # response = send_data("Hello, World!", "recording.wav", None)
    # print("Response:", response)

    # 示例调用
    send_data_and_play_audio("Hello, World!", "output_file.wav", None)
