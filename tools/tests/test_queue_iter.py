import multiprocessing
from typing import Iterator
import time
import json
import requests

class QueueIterator:
    def __init__(self, queue: multiprocessing.Queue):
        self.queue = queue

    def __iter__(self) -> Iterator:
        return self

    def __next__(self):
        data = self.queue.get()
        if data is None:  # 使用None作为结束信号
            raise StopIteration
        return data

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
