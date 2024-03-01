import requests
import time
import json

def generate_stream_data():
    # 假设这是要发送的文本列表
    is_end = False
    lines = ["Hello", "world", "this", "is", "a", "stream", "of", "text"]
    for line in lines:
        print(line)
        if lines.index(line) == len(lines) - 1:
            is_end = True
        yield json.dumps({'line': line, 'is_end': is_end}) + '\n'
        time.sleep(0.5)
        # 模拟数据处理时间

def get_stream_response(response):
    # 流式接收response
    rec_data_list = []
    temp_data = ''
    for chunk in response.iter_content(chunk_size=1):
        temp_data += chunk.decode('utf-8')
        if temp_data.endswith('\n'):
            temp_json = json.loads(temp_data)
            rec_data_list.append(temp_json)
            print(temp_data)
            temp_data = ''
            if temp_json['is_end']:
                break
    print(rec_data_list)
    print("----------------------------")
    print(temp_data)
    return rec_data_list

def stream_upload(url):
    
    # 流式接收response
    response = requests.post(url, data=generate_stream_data(), stream=True)
    
    final_response = get_stream_response(response)
    
    return final_response

url = 'http://127.0.0.1:5000/stream'
response = stream_upload(url)