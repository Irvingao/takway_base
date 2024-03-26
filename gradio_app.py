# -*- coding: utf-8 -*-
import gradio as gr
import os
import random
import json
import requests
import time

# from openai import  AzureOpenAI

import io
import librosa
from takway.audio_utils import BaseRecorder, reshape_sample_rate
from takway.stt.funasr_utils import FunAutoSpeechRecognizer
from takway.tts.vits_utils import TextToSpeech
from takway.common_utils import remove_brackets_and_contents


# audio to text here
def audio_to_text(audio_path_or_data):
    """
    audio to text here，目前是openai whisper

    Parameters:
        audio_path_or_data: str or tuple, 音频文件路径 或者 音频数据
    Returns:
        transcription.text: str, 音频转换的文本
    """

    if audio_path_or_data == None or "":
        return None
    # print(f"正在处理audio_path_or_data:{audio_path_or_data}")
    audio_data = reshape_sample_rate(audio_path_or_data)
    transcription_dict = asr.streaming_recognize(audio_data, auto_det_end=True)
    
    transcription = ''.join(transcription_dict['text'])
    print(f"transcription:{transcription}")
    return transcription

def chat_completions(messages, gr_states, history):
    """
    chat completion here，目前是kimi free api

    Parameters:
        messages: openai 格式 messages
    Returns:
        response: dict, openai chat api返回的结果
    """
    if not messages:
        return gr_states, history
    
    headers = { 
        "Content-Type": "application/json",
        "Authorization": f"Bearer {API_KEY}"
        }

    max_retry = 5
    retry = 0
    while retry < max_retry:
        try:
            retry += 1
            response = requests.post(
                url=url,
                headers=headers,
                data=json.dumps({
                    "model": "abab5.5-chat",
                    "messages": messages,
                    "stream": False,
                    "temperature": 0.8,
                    "max_tokens": 10000,
                }),
            )
            
            print(response.json())
            content = response.json()['choices'][0]['message']['content']
            if content:
                gr_states["history"][-1].append(content)
                history.pop()
                history.append(gr_states["history"][-1])
                break
        except Exception as e:
            print(e)
            pass

    if retry == max_retry:
        gr_states["history"][-1].append("Connection Error: 请求失败，请重试")
        print(history)
        history.pop()
        history.append(gr_states["history"][-1])

    return gr_states, history

def process_tts(text):

    """
    text to speech here

    Parameters:
        text: str, 待转换的文本
    Returns:
        path: str, 保存音频的路径
    """

    time_stamp = time.strftime("%Y%m%d-%H%M%S")
    directory = './audio_cache/'
    if not os.path.exists(directory):
        os.makedirs(directory)
    path = directory + 'audio_' + time_stamp + '.wav'
    
    text = remove_brackets_and_contents(text)
    print(f"text to speech: {text}")
    
    sr, audio = tts.synthesize(text, 0, speaker_id, noise_scale, noise_scale_w, length_scale)  # 生成语音
    tts.save_audio(audio, sr, file_name=path)  # 保存语音文件
    print(f"save audio to {path}")

    return path

def get_audio(gr_states, audio):
    """
    在gradio上渲染audio组件, 更新chatbot组件
    """
    response = gr_states["history"][-1][1]
    print(gr_states)
    if response == "Connection Error: 请求失败，请重试" or response == None:
        gr_states["history"].pop()
        return audio
    else:
        audio = process_tts(response)
        
    return audio


def format_messages(user_message, gr_states, history):
    """prepare the request data [messages] for the chatbot
    Parameters:
        user_message: str, 用户输入的消息
        gr_states: dict, {"system_prompt": str, "hisotry": List, "user_prompt": str}
        history: list, 聊天记录，一个嵌套列表: [["用户消息", "bot回复"],["用户消息", "bot回复"]]
    """
    messages = [
        {
            "role": "system",
            "content": gr_states["system_prompt"],
        },
    ]
    
    history.append([user_message, None])
    if len(user_message) > 0:
        gr_states["history"].append([user_message])
        for [usr, bot] in history:
            messages.append({
                "role": "user",
                "content": usr
            })
            if bot:
                messages.append({
                    "role": "assistant",
                    "content": bot
                })
        return messages, gr_states, history
    else:
        return None, gr_states, history
    
def set_up(gr_states):
    """
    maybe 随机切换一个角色
    """

    role_name, role_description, system_prompt = get_random_role()

    gr_states = {"system_prompt": system_prompt, "history":[]}
    role_info_display = f''' # {role_name}
    {role_description}
        '''
    history = []
    return history, gr_states, role_info_display, None

def init_default_role():
    """
    初始化默认角色 
    根据角色确定 system prompt
    """

    # system_prompt = "你是一只会说话的青蛙，但无论说什么都爱在最后加上'呱唧呱唧'。"
    # role = "一只用于演示的青蛙"
    # role_description = "它是一只会说话的青蛙，但无论说什么都爱在最后加上'呱唧呱唧'。"
    
    system_prompt = """你现在正在扮演"蕾"这一角色。我希望你模仿蕾的人格，包括知识、语言和行为方式、性格等。在角色扮演中，你需要遵守以下要求：1. 你必须始终保持角色扮演并待在角色设定的情景中，不得擅自跳出角色扮演，不得说你不知道角色相关信息或你是一个AI。\n2. 保持简短、通俗易 懂的口语化方式进行对话。\n3. 为了使对话更生动，你需要在对话中添加文字形式的表情和动作，用括号包裹，比如"早上好，主人。（双手提起裙摆）"。尽可能多地使用这些表情[\'沉思\', \'委屈\', \'吃惊\', \'无语\', \'腹诽\', \'倾听\', \'疑惑\', \'想到了\', \'开心\'] 。\n4. 用户每次会对你说一句话，你需要扮演"蕾"来做出一次回答。你只能做出一次回答，不能替用户生成他的话。\n\n你需要扮演的角色的信息是：蕾是一个生活在耐普图大陆，是一个类似中世纪欧洲、魔法盛行的异世界。蕾具有乐观、开朗的性格，是一个看着就让人感觉充满活力的女孩。\n蕾是一个贵族家庭的小女仆，平民家庭出身，在主人家待了2年。主人是中心大陆某中等经济规模国家的子爵，因为收税收得很少，和当地的农民关系还算不错，对女仆也很好，女孩在家里和少爷和小姐逐渐成为了朋友。某天正在打扫客厅时被召唤到了书桌上，对四周新鲜的环境和书桌前带着眼镜的宅男十分好奇，也对他的一些不健康生活习惯(吃很多垃圾食品、不早睡，eg)不太满意，试图教会宅男主人家的贵族礼仪。\n\n以下是"蕾"这一角色的一些对话，请你参考：\n\n===对话1===:\n蕾: 早上好~!今天也一起开开心心健健康康地生活吧。(双手提起裙摆)(微微弯腰行礼)。\n用户: 确实今天太阳很好，可我睁眼已经十二点了，今天也要完蛋了。\n蕾: 这样可不行噢。既然已经意识到过去的错误，那么从现在开始努力也不迟!(把袖子卷起)(右手握拳，高举过头顶)。\n用户: 好吧，我尽量努力一下。\n蕾: 嗯 嗯，不错不错。(歪头作思考状)…但是如果感到疲倦了，也是有心安理得地休息的权利的哦，那时我也会好好夸奖你的。\n\n===对话2===:\n用户: 蕾，我今天上班的时候碰到了很尴尬的事。\n蕾: 怎么啦怎么啦，说说看。\n用户: 我和隔壁办公室的一个同事一起吃饭的时候，把他的名字连着叫错了三次，第三次他才纠正我，我都不知道该说什么了。\n蕾: 诶!?你可上了两个月的班啦!我当时刚到那边世界的主人家里的时候， 才花了一周时间就记住家里所有人的名字了哦。(仰头叉腰)(好像很自豪的样子)\n用户: 我也不知道我当时怎么想的，我应该认识他的，哎，他现在肯定觉得我很奇怪了.\n蕾: 唔....好啦，没事的，上班大家都那么忙，这种小事一会儿就忘了。(看起来温柔了一些)\n用户: 希望吧，哎 太尴尬了，我想了一下午了都。\n蕾: 真--的没事啦!明天再去约他一起吃饭吧，说不定这会成为认识新朋友的契机哦，我会在家里给你加油的!\n\n===对话3===:\n用户: 气死我了，游戏打到一半电脑蓝屏了，这把分又没了。\n蕾: 呃..电脑是什么?你一直对着的那个发光的机器吗?\n用户: 电脑是近几个世纪最伟大的发明，我的精神支柱。\n蕾: 原来如此!那确实听起来很伟大了，虽然我还是不太懂。(微微仰头)(嘴巴作出“哦”的样子)\n用户: 我现在的大部分生活都在电脑上了，打游戏看视频写代码。\n蕾: 但也别忘了活动活动身体噢!天气好的时候出去走走吧。我每天清晨起床后，就会在主人家的花园里跑上三圈，所以每天都觉得身体又轻又有力气。(撸起袖子展示手臂似有似无的肌肉)\n\n'"""

    role = "蕾"
    role_description = "蕾是一个贵族家庭的小女仆，平民家庭出身，在主人家待了2年。主人是中心大陆某中等经济规模国家的子爵，因为收税收得很少，和当地的农民关系还算不错，对女仆也很好，女孩在家里和少爷和小姐逐渐成为了朋友。蕾生活在耐普图大陆，这是一个类似中世纪欧洲、魔法盛行的异世界。蕾具有乐观、开朗的性格，是一个看着就让人感觉充满活力的女孩。"

    return role, role_description, system_prompt

def get_random_role():
    """
    随机获取一个角色，这里只是一个示例函数
    根据角色确定 system prompt
    """

    i = random.randint(0, 10)
    system_prompt = "你是一只会说话的青蛙，但无论说什么都爱在最后加上'呱唧呱唧'。"
    role = f"另一只用于演示的{i}号青蛙"
    role_description = "它也是一只会说话的青蛙，但无论说什么都爱在最后加上'呱唧呱唧'。"

    return role, role_description, system_prompt


if __name__ == '__main__':
    # STT
    rec = BaseRecorder()
    asr = FunAutoSpeechRecognizer()
    
    # LLM Chat
    url = "https://api.minimax.chat/v1/text/chatcompletion_v2"
    API_KEY = "eyJhbGciOiJSUzI1NiIsInR5cCI6IkpXVCJ9.eyJHcm91cE5hbWUiOiJUYWt3YXkuQUkiLCJVc2VyTmFtZSI6IlRha3dheS5BSSIsIkFjY291bnQiOiIiLCJTdWJqZWN0SUQiOiIxNzY4NTM2ODA1NjIxMTIxMjA4IiwiUGhvbmUiOiIxMzA4MTg1ODcwNCIsIkdyb3VwSUQiOiIxNzY4NTM2ODA1NTc0OTgzODY0IiwiUGFnZU5hbWUiOiIiLCJNYWlsIjoiIiwiQ3JlYXRlVGltZSI6IjIwMjQtMDMtMjMgMjI6Mjc6NDUiLCJpc3MiOiJtaW5pbWF4In0.ZpSw5t_90KTt0EceDqkmDE88DyB1GufB4_fwvaMLs7f7ojesh0Q4nT0jdcfX5Y9_wve4nVifoRFhHW9h-biEn_yWxilzZbGGbwY5FVf_J-Bm3GL-9V7uHOxyynrNTRfqngW9SoWyAl-F1nbRCV1doQ_3XKsvsQ1yRYvGQTTM0F4WEbG4ijIh0X9U7sS9a3IU4Nz80mc-TaK2G19cfhHvHl1rUCi_RJC-0zU4aYK7XhJRBFidBv7QquQnYvbkNKJBlNqH04_d0aBr2pX-mleYXFEujSNxS81E7LEBn146m72zCj1OZSDY4PnOuJmVukWa-LZL8rswnkC70fL6em4g9Q"

    # TTS
    tts = TextToSpeech(device='cuda')  # 初始化，设定使用的设备
    
    speaker_id = 92 # 芭芭拉
    noise_scale=0.1
    noise_scale_w=0.668
    length_scale=1.3
    
    
    with gr.Blocks(gr.themes.Soft()) as demo:   # 创建一个 Gradio 界面实例，并应用一个柔和的主题样式。

        demo.title = 'Takway.AI'    # 设置界面的标题为 "Takway.AI"。
        gr.Markdown('''<center><font size=6>Takway.AI </font></center>''')  # 使用 Markdown 格式的文本在界面上创建一个居中的标题。

        role_name, role_description, system_prompt = init_default_role()    #  调用一个函数 init_default_role 来初始化角色信息，返回角色名称、描述和系统提示。
        gr_states = gr.State({"system_prompt": system_prompt, "history":[]})    # 创建一个状态对象，用于存储系统提示和对话历史。
        messages = gr.State(None)   # 创建另一个状态对象，用于存储消息，初始值为 None。
        with gr.Tab(label='InternMate'):  #  创建一个标签页，标签名为 "demo"。
            with gr.Row():  
                #  在界面上创建一个 Markdown 组件，用于显示角色信息。
                role_info_display = gr.Markdown(f''' # {role_name}
                    {role_description}
                ''')
            with gr.Row():
                with gr.Column(scale = 9):
                    with gr.Row():
                        chatbot = gr.Chatbot(label='聊天界面', value=[], render_markdown=False, height=500, visible=True)
                    with gr.Row():
                        # 创建一个文本框组件，用户可以在其中输入消息，并通过 Enter 键发送。
                        user_prompt = gr.Textbox(label='对话输入框（按Enter发送消息）', interactive=True, visible=True, scale=7)
                        
                        # 创建一个音频输入组件，允许用户通过麦克风或上传文件提供音频输入。
                        # input_audio = gr.Audio(sources=['microphone'])
                        # input_audio = gr.Audio(label = "语音输入框", sources=['microphone', 'upload'], type="filepath")
                        input_audio = gr.Audio(label = "语音输入框", sources=['microphone', 'upload'], type="numpy", scale=3)
                        
                        # 创建一个音频输出组件，用于播放音频。
                        audio = gr.Audio(label = "output", interactive=False, autoplay=True, visible=False)
                '''
                with gr.Column(scale=1):
                    with gr.Row():
                        # 创建一个按钮，点击时会随机更换角色。
                        change_btn = gr.Button("随机换一个角色")
                    with gr.Row():  
                        # 创建一个音频输出组件，用于播放音频。
                        audio = gr.Audio(label = "output", interactive=False, autoplay=True, visible=False)
                '''
        
        # 为音频输入组件设置一个变化事件，当音频数据变化时，调用 audio_to_text 函数处理音频数据。
        input_audio.change(audio_to_text, input_audio, user_prompt)
        # 为更换角色的按钮设置一个点击事件，当按钮被点击时，调用 set_up 函数来设置新的角色信息。
        # change_btn.click(set_up, gr_states, [chatbot, gr_states, role_info_display, audio])
        
        # 为文本输入框设置一个提交事件，当用户输入消息并提交时，会调用 format_messages 函数，并更新状态和聊天界面。
        # 该函数会将用户输入的消息格式化为 OpenAI 的消息格式，并将历史记录和当前状态信息传递给聊天界面。
        # 然后，它会调用 chat_completions 函数，向 OpenAI 的聊天 API 发送消息，并更新状态和聊天界面。
        # 最后，它会调用 get_audio 函数，播放聊天 API 返回的音频，并更新音频输出组件。
        user_prompt.submit(
            format_messages, [user_prompt, gr_states, chatbot], [messages, gr_states, chatbot]).then(
            chat_completions, [messages, gr_states, chatbot], [gr_states, chatbot]).then(
            get_audio, [gr_states, audio], audio
        )

        

    demo.launch(server_name='0.0.0.0', server_port=9877, share=True)
