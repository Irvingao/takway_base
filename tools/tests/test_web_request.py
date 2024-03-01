# 服务器的URL
server_url = 'http://127.0.0.1:5000/process_all'

import requests
import simpleaudio as sa
import io

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

def send_data_and_play_audio(text, audio_file_path, image_file_path):
    # 准备请求数据
    data = {'text': text}
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
        # 从响应中读取音频数据
        audio_data = io.BytesIO(response.content)

        # 使用simpleaudio播放音频流
        wave_obj = sa.WaveObject.from_wave_file(audio_data)
        play_obj = wave_obj.play()
        play_obj.wait_done()  # 等待音频播放完毕
    else:
        print("Error: Server responded with status code", response.status_code)


if __name__ == '__main__':  
    # 示例：同时发送文本、语音和图像数据
    # response = send_data("Hello, World!", "path_to_audio_file.wav", "path_to_image_file.jpg")
    # response = send_data("Hello, World!", "recording.wav", None)
    # print("Response:", response)

    # 示例调用
    send_data_and_play_audio("Hello, World!", "recording.wav", None)
