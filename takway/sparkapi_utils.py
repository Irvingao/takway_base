import _thread as thread
import queue
import threading
import base64
import time
import datetime
import hashlib
import hmac
import json
from urllib.parse import urlparse
import ssl
from datetime import datetime
from time import mktime
from urllib.parse import urlencode
from wsgiref.handlers import format_date_time
import websocket  # 使用websocket_client

from .roleplay_utils import BaseRolyPlayingFunction, SparkRolyPlayingFunction

class SparkChatClient(BaseRolyPlayingFunction):
    def __init__(self, 
                 appid=None, 
                 api_secret=None, 
                 api_key=None, 
                 spark_version="3.5",
                 temperature=0.8,
                 top_k=4,
                 debug=True,
                 stream=True,
                 stream_timeout=10,
                 stream_thread_enable=False,
                 spark_url=None,
                 spark_refresh_time=300,
                 max_tokens=8192):
        '''
        Args:
            appid: 应用ID
            api_secret: 应用密钥
            api_key: 应用API_KEY
            spark_version: 接口版本，可选值：1.1, 2.1, 3.1, 3.5
            temperature: 结果随机性，取值越高随机性越强即相同的问题得到的不同答案的可能性越高，取值范围 (0，1] ，默认值0.5
            top_k: 从k个候选中随机选择⼀个（⾮等概率），取值为[1，6],默认为4
            debug: 是否开启调试模式
            stream: 是否开启流式响应
            stream_timeout: 流式响应超时时间
            stream_thread_enable: 是否开启流式响应线程
            spark_url: 接口地址，如果不指定，则根据appid, api_secret, api_key, spark_version自动生成
            spark_refresh_time: 接口刷新时间，单位秒
            max_tokens: 最大文本长度，超过此长度则自动截断
        '''
        self.appid = appid
        self.api_secret = api_secret
        self.api_key = api_key
        self.spark_version = spark_version
        self.temperature = temperature
        self.top_k = top_k
        self.debug = debug
        self.max_tokens = max_tokens
        self.spark_refresh_time = spark_refresh_time
        
        self.spark_url = spark_url
        
        
        self.text = []
        self.stream = stream
        if stream:
            self.stream_answer = []
            self.stream_answer_queue = queue.Queue()
            self.stream_timeout = stream_timeout
            
            if stream_thread_enable:
                self.EXIT_FLAG = False
                self.answer_thread = threading.Thread(target=self.get_stream_response)
                self.answer_thread.start()
            

    def init_url(self):
        api_key = self.api_key
        api_secret = self.api_secret
        spark_version = self.spark_version
        
        if spark_version == "3.5":
            self.domain = "generalv3.5"
            spark_url = "wss://spark-api.xf-yun.com/v3.5/chat"
        elif spark_version == "3.1":
            self.domain = "generalv3"
            spark_url = "wss://spark-api.xf-yun.com/v3.1/chat"
        elif spark_version == "2.1":
            self.domain = "generalv2"
            spark_url = "wss://spark-api.xf-yun.com/v2.1/chat"
        elif spark_version == "1.1":
            self.domain = "general"
            spark_url = "wss://spark-api.xf-yun.com/v1.1/chat"
        else:
            raise ValueError(f"spark_version must be 1.1, 2.1, 3.1 or 3.5, but got {spark_version}")
        
        # 生成RFC1123格式的时间戳
        now = datetime.now()
        date = format_date_time(mktime(now.timetuple()))
        
        host = urlparse(spark_url).netloc
        path = urlparse(spark_url).path

        # 拼接字符串
        signature_origin = "host: " + host + "\n"
        signature_origin += "date: " + date + "\n"
        signature_origin += "GET " + path + " HTTP/1.1"

        # 进行hmac-sha256进行加密
        signature_sha = hmac.new(api_secret.encode('utf-8'), signature_origin.encode('utf-8'),
                                 digestmod=hashlib.sha256).digest()

        signature_sha_base64 = base64.b64encode(signature_sha).decode(encoding='utf-8')

        authorization_origin = f'api_key="{api_key}", algorithm="hmac-sha256", headers="host date request-line", signature="{signature_sha_base64}"'

        authorization = base64.b64encode(authorization_origin.encode('utf-8')).decode(encoding='utf-8')

        # 将请求的鉴权参数组合为字典
        v = {
            "authorization": authorization,
            "date": date,
            "host": host
        }
        # 拼接鉴权参数，生成url
        url = spark_url + '?' + urlencode(v)
        # 此处打印出建立连接时候的url,参考本demo的时候可取消上方打印的注释，比对相同参数时生成的url与自己代码生成的url是否一致
        print("建立连接的url:", url)
        return url

    def init_websocket(self):
        self.text.clear()
        # if self.spark_url is None:
        #     self.spark_url = self.init_url()
        self.spark_url = self.init_url()
        
        websocket.enableTrace(False)
        self.ws = websocket.WebSocketApp(
            self.spark_url, 
            on_message=self.on_stream_message, 
            on_error=self.on_error, 
            on_close=self.on_close, 
            on_open=self.on_open)
        self.ws.appid = self.appid

    def run_terminal_chat(self):
        self.init_websocket()
        while True:
            try:
                self.answer = ""
                
                Input = input("\n我: ")
                question = self.checklen(self.getText(self.text, Input, "user"))
                if self.debug:
                    print(f"question: {question}")
                    self.bg_time = time.time()
                self.chat(self.text)
                self.getText(self.text, self.answer, "assistant")
                if self.debug:
                    print(f"full cost: {(time.time() - self.bg_time)*1000:.0f} ms")
                    print(f"星火: {self.answer}")
                    print(f"full text: {self.text}")
            except KeyboardInterrupt:
                self.EXIT_FLAG = True
                print("exit terminal chat")
                break

    def chat(self, question):
        try:
            self.answer = ""
            self.ws.question = question
            self.ws.run_forever(
                sslopt={"cert_reqs": 
                    ssl.CERT_NONE})
        except websocket._exceptions.WebSocketException as e:
            print(f"websocket error: {e}")
            self.ws.close()
        
    def get_stream_response(self):
        while not self.EXIT_FLAG:
            data = self.stream_answer_queue.get(self.stream_timeout)
            if self.debug:
                print(f"stream data: {data}")
                # print(f"stream costs: {(time.time() - self.stream_bg_time)*1000:.4f} ms") # time
        print("exit stream thread")
        exit()

    def on_error(self, ws, error):
        # 收到websocket错误的处理
        if self.debug:
            print("### error:", error)
        self.ws.close()
        print("websocket restart")
        self.init_websocket()

    def on_close(self, ws,one,two):
        # 收到websocket关闭的处理
        if self.debug:
            print("### closed ###")
            print(f"ws close: {one}, {two}")
        self.ws.close()

    def on_open(self, ws):
        # 收到websocket连接建立的处理
        thread.start_new_thread(self._run, (self.ws,))

    def _run(self, ws, *args):
        data = json.dumps(self.gen_request_data(self.ws.question))
        ws.send(data)

    def on_message(self, ws, message):
        # 收到websocket消息的处理
        data = json.loads(message)
        print("data: ", data)
        code = data['header']['code']
        if code != 0:
            print(f'请求错误: {code}, {data}')
            self.ws.close()
        else:
            choices = data["payload"]["choices"]
            status = choices["status"]
            content = choices["text"][0]["content"]
            if self.debug:
                print("content: ", content,end ="")
                print(" status: ", status)
                print("choices: ", choices)
            # global answer
            self.answer += content
            if self.stream:
                if self.debug:
                    self.st_init_time = time.time(); print(f"stream init time: {(self.st_init_time - self.bg_time)*1000:.4f} ms")
            # end
            if status == 2:
                self.ws.close()

    def on_stream_message(self, ws, message):
        data = json.loads(message)
        code = data['header']['code']
        if code != 0:
            print(f'请求错误: {code}, {data}')
            self.stream_answer_queue.put(
                dict(
            is_bgn=False,
            is_end=True,
            text='这样说人家会羞羞的。',
        ))
            self.ws.close()
        else:
            self.answer += data["payload"]["choices"]["text"][0]["content"]
            if self.stream:
                self.stream_answer_queue.put(self.postprocess_asw_data(data))
                if self.debug:
                    self.stream_bg_time = time.time()
            if data["payload"]["choices"]["status"] == 2:
                self.ws.close()

    def postprocess_asw_data(self, data):
        '''
        {'header': {'code': 0, 'message': 'Success', 'sid': 'cht000c9309@dx18dc57b7304b8f3550', 'status': 0}, 'payload': {'choices': {'status': 0, 'seq': 0, 'text': [{'content': 'Hello', 'role': 'assistant', 'index': 0}]}}}
        '''
        asw_data = dict(
            is_bgn=True if data['payload']['choices']['status'] == 0 else False,
            is_end=True if data['payload']['choices']['status'] == 2 else False,
            text=data['payload']['choices']['text'][0]['content'],
        )
        if self.debug:
            asw_data['usage'] = data['payload'].get('usage', '')
        return asw_data

    def gen_request_data(self, question):
        """
        通过appid和用户的提问来生成请参数
        """
        data = {
            "header": {
                "app_id": self.appid,
                "uid": "1234"
            },
            "parameter": {
                "chat": {
                    "domain": self.domain,
                    "temperature": self.temperature,
                    "max_tokens": self.max_tokens,
                    "top_k": self.top_k,
                }
            },
            "payload": {
                "message": {
                    "text": question
                }
            }
        }
        return data


class SparkRolyPlayingClient(SparkChatClient, SparkRolyPlayingFunction):
    def __init__(self, 
                 *args,
                 character_data_dir, 
                 **kwargs):
        SparkChatClient.__init__(self, *args, **kwargs)
        SparkRolyPlayingFunction.__init__(self, character_data_dir)
        
    def run_roleplay_chat(self, character='Klee'):
        self.init_websocket()
        self.chat_status = "init"
        
        while True:
            self.answer = ""
            if self.chat_status == "init":
                self.set_character(character)
                self.gen_sys_prompt(self.text, prompt_id=4)
                self.chat_status = "chating"
                
            Input = input(f"我: ")
            
            question = self.gen_user_prompt(self.text, Input, prompt_id=1)
            if self.debug:
                print(f"question: {question}")
                self.bg_time = time.time()
            self.chat(self.text)
            self.get_ai_response(self.text, self.answer)
            if self.debug:
                print(f"full cost: {(time.time() - self.bg_time)*1000:.0f} ms")
                print(f"{self.character_info.character_name}: {self.answer}")
                print(f"self.text(对话内容): {self.text}")

    def on_stream_message(self, ws, message):
        data = json.loads(message)
        code = data['header']['code']
        if code != 0:
            print(f'请求错误: {code}, {data}')
            self.stream_answer_queue.put(
                dict(
            is_bgn=False,
            is_end=True,
            text='这样说人家会羞羞的。',
        ))
            self.ws.close()
        else:
            self.answer += data["payload"]["choices"]["text"][0]["content"]
            if self.stream:
                self.stream_answer_queue.put(self.postprocess_asw_data(data))
                if self.debug:
                    self.stream_bg_time = time.time()
            if data["payload"]["choices"]["status"] == 2:
                self.ws.close()





if __name__ == '__main__':
    #以下密钥信息从控制台获取
    appid = "fb646f00"    #填写控制台中获取的 APPID 信息
    api_secret = "Njc2M2E3Y2FjMDRjMDhjNjViNTYwOTE1"   #填写控制台中获取的 APISecret 信息
    api_key ="f71ea3399c4d73fe3f6df093f7811a0d"    #填写控制台中获取的 APIKey 信息

    spark_client = SparkChatClient(appid, api_secret, api_key, stream_thread_enable=True, debug=True)
    spark_client.run_terminal_chat()

