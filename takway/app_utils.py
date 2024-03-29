# -*- coding: utf-8 -*-
import os
from flask import Flask, request, Response

from .common_utils import *
from .stt.funasr_utils import FunAutoSpeechRecognizer
from .tts.vits_utils import TextToSpeech
from .llm.sparkapi_utils import SparkChatClient, SparkRolyPlayingClient
from .llm.openllm_api import OpenLLMAPI

import bida # web llm
from bida import ChatLLM

from .apps.data_struct import *

import websocket  # 使用websocket_client

import time
import json
import base64
import queue
import threading
import multiprocessing

app = Flask(__name__)

class TakwayApp:
    def __init__(self, 
                 app,
                 stream_timeout=10,
                 device='cuda',
                 debug=False,
                 asr_cfg=None,
                 tts_cfg=None,
                 llm_cfg=None,
                 **kwargs):
        super().__init__(**kwargs)
        
        self.debug = debug
        self.stream_timeout = stream_timeout

        self.asr_cfg = self._init_asr_cfg(asr_cfg)

        self.llm_cfg = self._init_llm_cfg(llm_cfg)
        
        self.tts_cfg = self._init_tts_cfg(tts_cfg)
        
        self.process_init()
    
    def _init_asr_cfg(self, asr_cfg):
        assert 'model_path' in asr_cfg, "asr_cfg must contain model_path"
        asr_cfg['debug'] = self.debug
        return asr_cfg
    
    def _init_llm_cfg(self, llm_cfg):
        # assert 'api_key' in llm_cfg, "llm_cfg must contain api_key"
        # assert 'api_secret' in llm_cfg, "llm_cfg must contain api_secret"
        llm_cfg['stream_timeout'] = self.stream_timeout
        llm_cfg['debug'] = self.debug
        return llm_cfg
    
    def _init_tts_cfg(self, tts_cfg):
        assert'model_path' in tts_cfg, "tts_cfg must contain model_path"
        assert 'device' in tts_cfg, "tts_cfg must contain device"
        tts_cfg['debug'] = self.debug
        return tts_cfg
    
    def start_app(self, app, port=5000, **kwargs):
        app.run(host='0.0.0.0', port=5000, debug=self.debug, **kwargs)
    
    def process_init(self):
        '''
        init three processes for auto speech recognition, llm chat, and text to speech.
        '''
        # multiprocessing
        manager = multiprocessing.Manager()
        self.stt_queue = manager.Queue()
        self.chat_queue = manager.Queue()
        self.tts_queue = manager.Queue()
        self.api_queue = manager.Queue()
        processes = [
                    multiprocessing.Process(target=self.stream_stt_process),
                    # multiprocessing.Process(target=self.stream_chat_process),
                    multiprocessing.Process(target=self.stream_llm_process),
                    multiprocessing.Process(target=self.stream_tts_process)
                    ]
        for process in processes:
            process.start()

    
    def stream_stt_process(self):
        '''
        流式语音识别进程
        
        流式接收来自前端的语音数据，进行流式语音识别，并将识别的文字结果放入队列中，供后续处理。
        '''
        asr = FunAutoSpeechRecognizer(**self.asr_cfg)
        
        print("stream_stt_process start")
        stt_texts = []
        while True:
            print("wait for stream audio data request")
            data = self.stt_queue.get()
            print("Recieved stream audio data!")
            
            audio_data = decode_str2bytes(data['audio_input'].pop('data'))
            audio_text = self.process_stt(asr, audio_data, is_end=data['is_end'])
            stt_texts.append(audio_text)

            if data.pop('is_bgn'):
                print(f"put wakeup_data to queue.")
                self.tts_queue.put(
                    dict(
                        stream_text=data['character_info'].pop('wakeup_words'),
                        character_info=data['character_info'],
                        is_end=False)
                    )
                
                self.chat_queue.put(
                    dict(
                        character_info=data['character_info'],
                        chat_input=data.pop('chat_input'),
                        init_character=True)
                    )
                print(f"recieved wakeup_data: {data}")
            
            if data.pop('is_end'):
                stt_data = dict(
                    stt_text=''.join(stt_texts),
                    init_character=False,
                    **data)

                if stt_data['stt_text'] == '':
                    print("stt_text is empty")
                else:                 
                    print("put stt_data to queue")
                    self.chat_queue.put(stt_data)
                stt_texts.clear()

    def process_stt(self, asr, audio_data, is_end):
        # 语音识别
        asr_result = asr.streaming_recognize(audio_data, is_end)
        
        # 去掉字符串中的方括号和单引号
        asr_text = asr_result['text']
        asr_text = ' '.join(asr_text)
        asr_str = asr_text.replace("[", "").replace("]", "").replace("'", "").replace(" ", "")
            
        return asr_str
    
    def stream_llm_process(self):
        print("stream_chat_process start")
        
        # stream_timeout = self.llm_cfg.pop('stream_timeout')
        web_llm = self.llm_cfg.get('web_llm', False)
        if web_llm:
            def stream_process_data(data, stream_callback_args):
                print(f"stream_process_data: {data}")
                # is_bgn = True if idx == 0 else False
                # is_end = True if steaming_content is None else False    
                self, stt_data = stream_callback_args 
                is_bgn = False
                is_end = True if data == '' else False
                self.tts_queue.put(
                    dict(
                    stream_text=data,
                    is_bgn=is_bgn,
                    is_end=is_end,
                    **stt_data,
                    )
                )
                
            sys_prompt = """你现在正在扮演"蕾"这一角色。我希望你模仿蕾的人格，包括知识、语言和行为方式、性格等。在角色扮演中，你需要遵守以下要求：1. 你必须始终保持角色扮演并待在角色设定的情景中，不得擅自跳出角色扮演，不得说你不知道角色相关信息或你是一个AI。\n2. 保持简短、通俗易 懂的口语化方式进行对话。\n3. 为了使对话更生动，你需要在对话中添加文字形式的表情和动作，用括号包裹，比如"早上好，主人。（双手提起裙摆）"。尽可能多地使用这些表情[\'沉思\', \'委屈\', \'吃惊\', \'无语\', \'腹诽\', \'倾听\', \'疑惑\', \'想到了\', \'开心\'] 。\n4. 用户每次会对你说一句话，你需要扮演"蕾"来做出一次回答。你只能做出一次回答，不能替用户生成他的话。\n\n你需要扮演的角色的信息是：蕾是一个生活在耐普图大陆，是一个类似中世纪欧洲、魔法盛行的异世界。蕾具有乐观、开朗的性格，是一个看着就让人感觉充满活力的女孩。\n蕾是一个贵族家庭的小女仆，平民家庭出身，在主人家待了2年。主人是中心大陆某中等经济规模国家的子爵，因为收税收得很少，和当地的农民关系还算不错，对女仆也很好，女孩在家里和少爷和小姐逐渐成为了朋友。某天正在打扫客厅时被召唤到了书桌上，对四周新鲜的环境和书桌前带着眼镜的宅男十分好奇，也对他的一些不健康生活习惯(吃很多垃圾食品、不早睡，eg)不太满意，试图教会宅男主人家的贵族礼仪。\n\n以下是"蕾"这一角色的一些对话，请你参考：\n\n===对话1===:\n蕾: 早上好~!今天也一起开开心心健健康康地生活吧。(双手提起裙摆)(微微弯腰行礼)。\n用户: 确实今天太阳很好，可我睁眼已经十二点了，今天也要完蛋了。\n蕾: 这样可不行噢。既然已经意识到过去的错误，那么从现在开始努力也不迟!(把袖子卷起)(右手握拳，高举过头顶)。\n用户: 好吧，我尽量努力一下。\n蕾: 嗯 嗯，不错不错。(歪头作思考状)…但是如果感到疲倦了，也是有心安理得地休息的权利的哦，那时我也会好好夸奖你的。\n\n===对话2===:\n用户: 蕾，我今天上班的时候碰到了很尴尬的事。\n蕾: 怎么啦怎么啦，说说看。\n用户: 我和隔壁办公室的一个同事一起吃饭的时候，把他的名字连着叫错了三次，第三次他才纠正我，我都不知道该说什么了。\n蕾: 诶!?你可上了两个月的班啦!我当时刚到那边世界的主人家里的时候， 才花了一周时间就记住家里所有人的名字了哦。(仰头叉腰)(好像很自豪的样子)\n用户: 我也不知道我当时怎么想的，我应该认识他的，哎，他现在肯定觉得我很奇怪了.\n蕾: 唔....好啦，没事的，上班大家都那么忙，这种小事一会儿就忘了。(看起来温柔了一些)\n用户: 希望吧，哎 太尴尬了，我想了一下午了都。\n蕾: 真--的没事啦!明天再去约他一起吃饭吧，说不定这会成为认识新朋友的契机哦，我会在家里给你加油的!\n\n===对话3===:\n用户: 气死我了，游戏打到一半电脑蓝屏了，这把分又没了。\n蕾: 呃..电脑是什么?你一直对着的那个发光的机器吗?\n用户: 电脑是近几个世纪最伟大的发明，我的精神支柱。\n蕾: 原来如此!那确实听起来很伟大了，虽然我还是不太懂。(微微仰头)(嘴巴作出“哦”的样子)\n用户: 我现在的大部分生活都在电脑上了，打游戏看视频写代码。\n蕾: 但也别忘了活动活动身体噢!天气好的时候出去走走吧。我每天清晨起床后，就会在主人家的花园里跑上三圈，所以每天都觉得身体又轻又有力气。(撸起袖子展示手臂似有似无的肌肉)\n\n'"""
            llm_api = ChatLLM(model_type="minimax",
                        prompt_template=sys_prompt,
                        stream_callback=stream_process_data,
                        )
            while True:
                stt_data = self.chat_queue.get()
                print(f"recieved stt_data: {stt_data}")
                if stt_data.pop('init_character'):
                    continue
                user_prompt = stt_data['stt_text']
                response = llm_api.chat(prompt=user_prompt, 
                                        stream_callback_args=(self, stt_data),
                                        return_full_content=True)
                '''
                if stt_data.pop('init_character'):
                    # TODO: 用结构化的数据结构来表示输入，当前写死输入system prompt
                    print(f"stt_data: {stt_data}")
                    history_enable = False
                    if stt_data['chat_input'].get('chat_history', None):
                        # print(f"sys_prompt: {sys_prompt}")
                        history_enable = True
                    else:
                        sys_prompt = None
                        raise ValueError("system prompt should not be None")
                    llm_api = ChatLLM(model_type="minimax", 
                        prompt_template="""你现在正在扮演"蕾"这一角色。我希望你模仿蕾的人格，包括知识、语言和行为方式、性格等。在角色扮演中，你需要遵守以下要求：1. 你必须始终保持角色扮演并待在角色设定的情景中，不得擅自跳出角色扮演，不得说你不知道角色相关信息或你是一个AI。\n2. 保持简短、通俗易 懂的口语化方式进行对话。\n3. 为了使对话更生动，你需要在对话中添加文字形式的表情和动作，用括号包裹，比如"早上好，主人。（双手提起裙摆）"。尽可能多地使用这些表情[\'沉思\', \'委屈\', \'吃惊\', \'无语\', \'腹诽\', \'倾听\', \'疑惑\', \'想到了\', \'开心\'] 。\n4. 用户每次会对你说一句话，你需要扮演"蕾"来做出一次回答。你只能做出一次回答，不能替用户生成他的话。\n\n你需要扮演的角色的信息是：蕾是一个生活在耐普图大陆，是一个类似中世纪欧洲、魔法盛行的异世界。蕾具有乐观、开朗的性格，是一个看着就让人感觉充满活力的女孩。\n蕾是一个贵族家庭的小女仆，平民家庭出身，在主人家待了2年。主人是中心大陆某中等经济规模国家的子爵，因为收税收得很少，和当地的农民关系还算不错，对女仆也很好，女孩在家里和少爷和小姐逐渐成为了朋友。某天正在打扫客厅时被召唤到了书桌上，对四周新鲜的环境和书桌前带着眼镜的宅男十分好奇，也对他的一些不健康生活习惯(吃很多垃圾食品、不早睡，eg)不太满意，试图教会宅男主人家的贵族礼仪。\n\n以下是"蕾"这一角色的一些对话，请你参考：\n\n===对话1===:\n蕾: 早上好~!今天也一起开开心心健健康康地生活吧。(双手提起裙摆)(微微弯腰行礼)。\n用户: 确实今天太阳很好，可我睁眼已经十二点了，今天也要完蛋了。\n蕾: 这样可不行噢。既然已经意识到过去的错误，那么从现在开始努力也不迟!(把袖子卷起)(右手握拳，高举过头顶)。\n用户: 好吧，我尽量努力一下。\n蕾: 嗯 嗯，不错不错。(歪头作思考状)…但是如果感到疲倦了，也是有心安理得地休息的权利的哦，那时我也会好好夸奖你的。\n\n===对话2===:\n用户: 蕾，我今天上班的时候碰到了很尴尬的事。\n蕾: 怎么啦怎么啦，说说看。\n用户: 我和隔壁办公室的一个同事一起吃饭的时候，把他的名字连着叫错了三次，第三次他才纠正我，我都不知道该说什么了。\n蕾: 诶!?你可上了两个月的班啦!我当时刚到那边世界的主人家里的时候， 才花了一周时间就记住家里所有人的名字了哦。(仰头叉腰)(好像很自豪的样子)\n用户: 我也不知道我当时怎么想的，我应该认识他的，哎，他现在肯定觉得我很奇怪了.\n蕾: 唔....好啦，没事的，上班大家都那么忙，这种小事一会儿就忘了。(看起来温柔了一些)\n用户: 希望吧，哎 太尴尬了，我想了一下午了都。\n蕾: 真--的没事啦!明天再去约他一起吃饭吧，说不定这会成为认识新朋友的契机哦，我会在家里给你加油的!\n\n===对话3===:\n用户: 气死我了，游戏打到一半电脑蓝屏了，这把分又没了。\n蕾: 呃..电脑是什么?你一直对着的那个发光的机器吗?\n用户: 电脑是近几个世纪最伟大的发明，我的精神支柱。\n蕾: 原来如此!那确实听起来很伟大了，虽然我还是不太懂。(微微仰头)(嘴巴作出“哦”的样子)\n用户: 我现在的大部分生活都在电脑上了，打游戏看视频写代码。\n蕾: 但也别忘了活动活动身体噢!天气好的时候出去走走吧。我每天清晨起床后，就会在主人家的花园里跑上三圈，所以每天都觉得身体又轻又有力气。(撸起袖子展示手臂似有似无的肌肉)\n\n'""",
                        stream_callback=stream_process_data,
                        )
                    if history_enable:
                        for chat_message in stt_data['chat_input']['chat_history'][1:]:
                            llm_api.conversation.append_message(chat_message['role'], chat_message['content'])
                    print(f"llm_api.conversation: {llm_api.conversation}")
                else:
                    user_prompt = stt_data['stt_text']
                    response = llm_api.chat(prompt=user_prompt, 
                                            stream_callback_args=(self, stt_data),
                                            return_full_content=True) 
                    '''
                
        if not web_llm:
            llm_api = OpenLLMAPI(**self.llm_cfg)
        
            while True:
                stt_data = self.chat_queue.get()
                '''
                try:
                    stt_data = self.chat_queue.get(timeout=stream_timeout)
                except queue.Empty:
                    continue
                '''
                print(f"recieved stt_data: {stt_data}")
                
                if stt_data.pop('init_character'):
                    chat_history = stt_data['chat_input'].get('chat_history')
                    print(f"chat_history: {chat_history}")
                    continue
                else:
                    prompt = stt_data['stt_text']
                    # chat_status = stt_data['chat_input'].pop('chat_status')
                    
                    chat_history = llm_api.create_chat_prompt(prompt, chat_history)
                    response = llm_api.get_completion(chat_history, temperature=0.7)
                    
                    temp_text = ''
                    for idx, chunk in enumerate(response):
                        steaming_content = chunk.choices[0].delta.content
                        is_bgn = True if idx == 0 else False
                        is_end = True if steaming_content is None else False
                        if steaming_content:
                            temp_text += steaming_content
                            sentence_patch, is_full_sentence = split_chinese_text(temp_text, return_patch=True)
                            if is_full_sentence:
                                chat_text = sentence_patch[0]
                                temp_text = temp_text.replace(chat_text, '')
                                self.tts_queue.put(
                                    dict(
                                    stream_text=chat_text,
                                    is_bgn=is_bgn,
                                    is_end=is_end,
                                    **stt_data,
                                    )
                                )
                    
                
    
    def stream_chat_process(self):
        '''
        大模型对话进程
        
        接收来自语音识别文本结果，送入大模型对话，并将对话结果放入队列中，供后续处理。
        '''
        
        print("stream_chat_process start")
        
        spark_api = SparkRolyPlayingClient(**self.llm_cfg)
        spark_api.init_websocket()
        
        self.stream_data_queue = queue.Queue()
        
        get_response_thread = threading.Thread(target=self.get_stream_response_thread, args=(spark_api,)).start()
        
        while True:
            try:
                stt_data = self.chat_queue.get(timeout=spark_api.spark_refresh_time)
            except queue.Empty:
                spark_api.init_websocket()
                print(f"wait for {spark_api.spark_refresh_time} seconds and refresh spark websocket")
                continue
            # ##########################################
            print(f"recieved stt_data: {stt_data}")
            # TODO: 处理init_character的信息
            if stt_data.pop('init_character'):
                if stt_data['chat_input']['chat_status'] == 'init':
                    spark_api.clear_character()
                spark_api.set_character(stt_data['character_info']['character_name'], prompt_id=4, gen_sys_pmt=False)
                spark_api.chat_history = stt_data['chat_input']['chat_history']
                # spark_api.chat_history = spark_api.gen_sys_prompt(prompt_id=4) + spark_api.chat_history
                continue
            # ##########################################
            
            # TODO
            if stt_data['stt_text'] != '':
                self.stream_data_queue.put(stt_data)    # put data to queue
                
                print(f"stt_data: {stt_data}")
                
                question = stt_data['stt_text']
                chat_status = stt_data['chat_input'].pop('chat_status')
                
                chat_text = spark_api.gen_user_prompt(spark_api.chat_history, content=question, prompt_id=1)
                print(f"chat_text: {chat_text}")
                
                spark_api.chat(chat_text)   # chat
                
                spark_api.clear_character()
                        
    def get_stream_response_thread(self, spark_api):
        temp_text = ''
        while True:
            stt_data = self.stream_data_queue.get()
            if stt_data is None:
                continue
            while True:
                stream_chat_data = spark_api.stream_answer_queue.get()
                # print(f"stream_chat_data: {stream_chat_data}")
                # TODO
                temp_text += stream_chat_data['text']
                sentence_patch, is_full_sentence = split_chinese_text(temp_text, return_patch=True)
                if is_full_sentence:
                    chat_text = sentence_patch[0]
                    temp_text = temp_text.replace(chat_text, '')
                    
                    chat_data = dict(
                        stream_text=chat_text,
                        is_bgn=stream_chat_data['is_bgn'],
                        is_end=stream_chat_data['is_end'],
                        **stt_data,
                    )
                    self.tts_queue.put(chat_data)
                if stream_chat_data['is_end']:
                    break

    def stream_tts_process(self):
        vits = TextToSpeech(
            **self.tts_cfg
        )
        print("stream_tts_process start")
        while True:
            chat_data = self.tts_queue.get(); bg_t = time.time()
            
            out_data = self.process_tts(vits, chat_data)
            print(f"process tts data time: {(time.time() - bg_t)*1000:.2f} ms")
            
            self.api_queue.put(out_data)
            if out_data['is_end']:
                self.api_queue.put(None)
                print("stream_tts_process end")
            
    def process_tts(self, vits, chat_data):
        # 调用VITS进行语音合成
        sr, audio = vits.synthesize(
            chat_data['stream_text'], 
            language=0, 
            speaker_id=chat_data['character_info']['speaker_id'], 
            noise_scale=0.1, 
            noise_scale_w=0.668, 
            length_scale=1.2,
            return_bytes=True,
        )
        chat_data['tts_data'] = dict(
            tts_audio=encode_bytes2str(audio),
            rate=sr)
        return chat_data
    
    
    def stream_request_receiver_process(self, chunk_size=1):
        temp_data = ''
        print("wait for stream request")
        while True:
            try:
                chunk = request.stream.read(chunk_size)
            except ConnectionResetError as e:
                print(f"ConnectionResetError: {e}")
                break
            temp_data += chunk.decode('utf-8')
            if temp_data.endswith('\n'):
                temp_json_data, temp_data = temp_data.split('\n', 1)
                temp_json = json.loads(temp_json_data)
                # temp_json = json.loads(temp_data.rstrip('\n'))
                self.stt_queue.put(temp_json)
                # temp_data = ''
                if temp_json['is_end']:
                    break
    
    def generate_stream_queue_data(self):
        for queue_data in QueueIterator(self.api_queue):
            # print(f"len(queue_data['tts_data']['tts_audio']): {len(queue_data['tts_data']['tts_audio'])}")
            # print(f"queue_data: {queue_data['tts_data'].pop('tts_audio')}")
            yield self.gen_response_data(queue_data)
            # yield json.dumps(queue_data) + '\n'
    
    def gen_response_data(self, queue_data):
        return json.dumps({
            'status': queue_data.get('status', 0),  # 0: success, 1: error, 2: warning, 3: info, 4: debug
            'message': queue_data.get('message', ''),
            'is_end': queue_data['is_end'],
            'chat_output': {
                'llm_stream_data': queue_data.get('stream_text', ''),
                'question': queue_data['stt_text'] if queue_data['is_end'] else '',
            },
            'audio_output': {
                'tts_stream_data': queue_data['tts_data'].get('tts_audio', ''),
            },
        }) + '\n'
        
        
        
if __name__ == "__main__":
    
    takway_app = TakwayApp(
        app=app,
        stream_timeout=10,
        device='cuda',
        debug=False,
        asr_cfg={
            'model_path': 'vosk-model-small-cn-0.22',
            'RATE': 16000,
        },
        tts_cfg={
            'model_path': 'vits-small-patch16-22k-v2',
            'device': 'cuda',
        },
        llm_cfg={
            'appid': 'xxxxx',
            'api_key': 'xxxxx',
            'api_secret': 'xxxxx',
            'stream': 'xxxxx',
            'spark_version': 'xxxxx',
        }
    )
    
    takway_app.start_app(host='0.0.0.0', port=5000, debug=False)