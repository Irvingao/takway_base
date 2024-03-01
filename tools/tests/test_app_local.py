import requests

def send_data(text):
    """同时发送文本、语音和图像数据到服务器"""

    # 准备文本数据
    data = {'text': text}

    # 发送请求
    response = requests.post(server_url, data=data, stream=True)
    
    return response.json()

if __name__ == '__main__':  
    # 服务器的URL
    server_url = 'http://127.0.0.1:5000/character-chat'

    # 示例：同时发送文本、语音和图像数据
    response = send_data("Hello, World!")
    # response = send_data("Hello, World!", "recording.wav", None)
    print("Response:", response)
