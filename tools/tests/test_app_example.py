from flask import Flask, Response, request
import time
import json
import requests

app = Flask(__name__)

def process_stream_data(stream_data):
    # 假设这是要发送的数据
    print("开始生成新的数据流")
    is_end = False
    print(stream_data)
    for idx, line in enumerate(stream_data):
        if idx == len(stream_data)-1:
            is_end = True
        print(line)
        yield json.dumps(line)+"\n"
        time.sleep(0.5)
        # 模拟数据处理时间

def get_stream_request(chunk_size=1):
    req_data_list = []
    temp_data = ''
    while True:
        chunk = request.stream.read(chunk_size)
        temp_data += chunk.decode('utf-8')
        if temp_data.endswith('\n'):
            temp_json = json.loads(temp_data)
            req_data_list.append(temp_json)
            print(temp_data)
            temp_data = ''
            if temp_json['is_end']:
                return req_data_list

@app.route('/stream', methods=['POST'])
def stream_text():
    
    data = get_stream_request()

    print("----------------------------")
    
    return Response(process_stream_data(data))

if __name__ == "__main__":
    app.run(host='0.0.0.0', port=5000, debug=True)
