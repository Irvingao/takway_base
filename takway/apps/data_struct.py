import multiprocessing
import queue
from typing import Iterator
import time
import json
import requests

class QueueIterator:
    def __init__(self, 
                 queue, 
                 timeout: int = 10):
        self.queue = queue
        self.timeout = timeout

    def __iter__(self) -> Iterator:
        return self

    def __next__(self):
        try:
            data = self.queue.get(block=True, timeout=self.timeout)
            if data is None:  # 使用None作为结束信号
                print("QueueIterator: End of data")
                raise StopIteration
            else:
                print("QueueIterator: Get data")
                return data
        except queue.Empty:
            print("QueueIterator: Queue is empty")
            raise StopIteration




def producer(queue: multiprocessing.Queue):
    for i in range(5):  # 假设生产5个数据项
        data = {'data': i, 'is_end': False}
        queue.put(data)
        time.sleep(1)
    queue.put(None)  # 发送结束信号

def get_stream_data_from_queue(queue: multiprocessing.Queue):
    for data in QueueIterator(queue):
        print(data)
        yield json.dumps({'line': data, 'is_end': False})
        # 模拟数据处理时间

if __name__ == "__main__":
    queue = multiprocessing.Queue()
    # 创建并启动生产者进程
    p = multiprocessing.Process(target=producer, args=(queue,))
    p.start()

    # 使用迭代器来消费Queue中的数据
    for data in QueueIterator(queue):
        print(data)

    # 等待生产者进程结束
    p.join()


'''
# request body
{
    "AUTH_INFO": {
        "user": "", # string
        "authid": "",   # string
        "api_keys": "",  # string
        "timestamp": "",  # string
    },
    "DATA": {
        "Audio": {
            "data": "xxxxx",    # base64 encoded data
            "metadata": {
                "rate": ;   # int
                "channels": ;   # int
                "format": ;  # int
            }
        },
        "Text": {
            "data": "xxxxx",    # base64 encoded data
            "metadata": {
                # TODO
            }
        },
        "Image": {
            "data": "xxxxx",    # base64 encoded data
            "metadata": {
                "width": ;  # int
                "height": ; # int
                "format": ; # string
            }
        }
    }
    "META_INFO": {
        "model_type": "",     # string
        "model_version": "",    # string
        "model_url": "",    # string
        "vits": {
            "speaker_id": ;  # int
    }
}

# response body
{
    RESPONSE_INFO: {
        "status": "success/error",   # string
        "message": "xxxxx",  # string
    }
    "DATA": {
        "Audio": {
            "data": "xxxxx",    # base64 encoded data
            "metadata": {
                "rate": ;   # int
                "channels": ;   # int
                "format": ;  # int
            }
        },
        "Text": {
            "data": "xxxxx",    # base64 encoded data
            "metadata": {
                "is_end": True/False,  # bool
            }
        }
        "Image": {
            "data": "xxxxx",    # base64 encoded data
            "metadata": {
                "width": ;  # int
                "height": ; # int
                "format": ; # string
            }
        }
}
'''