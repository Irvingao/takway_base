###################### roly-play ###########################
from roleplay_main import *
import time

###################### VOSK ############################
from voice_vosk import record_audio, audio_to_text
from vosk import Model, KaldiRecognizer, SetLogLevel
wav_file_path = "recording.wav"
# vosk_model = Model(model_path="vosk-model-small-cn-0.22")
vosk_model = Model(model_path="vosk-model-cn-0.22")


###################### Spark ###########################
import SparkApi
#以下密钥信息从控制台获取
appid = "fb646f00"    #填写控制台中获取的 APPID 信息
api_secret = "Njc2M2E3Y2FjMDRjMDhjNjViNTYwOTE1"   #填写控制台中获取的 APISecret 信息
api_key ="f71ea3399c4d73fe3f6df093f7811a0d"    #填写控制台中获取的 APIKey 信息

#用于配置大模型版本，默认“general/generalv2”
# domain = "general"   # v1.5版本
# domain = "generalv2"    # v2.0版本
domain = "generalv3"    # v3.0版本
#云端环境的服务地址
# Spark_url = "ws://spark-api.xf-yun.com/v1.1/chat"  # v1.5环境的地址
# Spark_url = "ws://spark-api.xf-yun.com/v2.1/chat"  # v2.0环境的地址
Spark_url = "ws://spark-api.xf-yun.com/v3.1/chat"  # v3.0环境的地址

max_token_limit = 8000

text =[]

text.clear

###################### VITS ###########################
import os
import utils
import commons

from models import SynthesizerTrn
from text import text_to_sequence
from vits import vits

import torch
from torch import no_grad, LongTensor
import soundfile as sf

hps_ms, device, speakers, net_g_ms, limitation = tts_model_init()

###################### audio ###########################
# audio init
import pyaudio
import wave
import base64

# 音频参数设置
CHUNK = 1024
FORMAT = pyaudio.paInt16
CHANNELS = 1
IN_RATE = 44100
OUT_RATE = 22050

###################### roly-play ###########################
import json
def get_character(character_json_path="character.json"):
    with open(character_json_path, 'r',encoding="UTF-8") as f:
        character_data = json.load(f)
    return character_data

def get_user(user_json_path="user.json"):
    with open(user_json_path, 'r',encoding="UTF-8") as f:
        user_data = json.load(f)
    return user_data

def generate_sys_prompt(text, character_data, user_data):
    chat_history = ""
    token_count = 0

    name = character_data.get('char_name', '')
    background = character_data.get('description', '')
    personality = character_data.get('personality', '')
    circumstances = character_data.get('world_scenario', '')
    common_greeting = character_data.get('first_mes', '')
    # past_dialogue = character_data.get('mes_example', '')
    # past_dialogue_formatted = past_dialogue

    user_name = user_data.get('char_name', '')
    user_background = user_data.get('description', '')
    user_personality = user_data.get('personality', '')
    user_circumstances = user_data.get('world_scenario', '')
    user_common_greeting = user_data.get('first_mes', '')

    content = f"""我们在角色扮演情景中。你需要总是保持角色扮演。\n{"你的名字：" + name}\n{"你的人物背景: " + background}\n{"你的人物性格特点: " + personality}\n{"你当前的情况和环境是: " + circumstances}\n{"你常用的问候语是: " + common_greeting}\n记住，你总是保持角色扮演。你就是上面描述的角色。\n你现在在和我对话，我的基本信息如下：\n{"我的名字：" + user_name}\n{"我的人物背景: " + user_background}\n{"我的人物性格特点: " + user_personality}"""
    # for username, message in past_messages:
        # message_text = f"{username}: {message}\n"
        # message_tokens = len(chatbot.tokenizer.encode(message_text))
        # if token_count + message_tokens > max_token_limit:
            # break
        # chat_history = message_text + chat_history
        # token_count += message_tokens
    
    jsoncon = {}
    jsoncon["role"] = "system"
    jsoncon["content"] = content
    text.append(jsoncon)
    # print(f"System: {sys_prompt}")
    return text
# 每日反思优化
# 口语化，简单输出；
# 

def getCharacterText(text, role,content,name):
    jsoncon = {}
    jsoncon["role"] = role
    jsoncon["content"] = f"""
### 输入是一段语音转换后的文字，可能存在可能存在不准确或不清晰的部分，你需要根据文字的发音对该问题进行合理地断句和理解:
{content}
### 输出需要始终使用在聊天历史中未曾出现的新颖独特的信息进行回应，根据你的角色使用简短口语化的回答回应以下消息:
{name}:"""
    text.append(jsoncon)
    return text

def clearPromptText(text, content):
    text[-1]["content"] = content
    return text

###################### Flask ###########################
from flask import Flask, request, jsonify, send_file
import os

app = Flask(__name__)

UPLOAD_FOLDER = 'temp'
app.config['UPLOAD_FOLDER'] = UPLOAD_FOLDER

@app.route('/process_all', methods=['POST'])
def handle_all():
    t1 = time.time()
    global text, character
    audio_base64 = None
    
    # 获取文本数据
    text_data = request.form.get('text')
    print("text_data:", text_data, type(text_data))
    print("------------------------------------------")
    
    character = request.form.get('character')
    if character == 'default':
        character = 'Klee'
    
    chat_status = request.form.get('chat_status')
    print("chat_status:", chat_status)
    
    # 保存并处理语音文件
    audio_file = request.files.get('audio')
    # 保存并处理图像文件
    image_file = request.files.get('image')
    t2 = time.time()# ; print("data prepare time:", t2-t1, "s")
    
    # #######################
    character_data = get_character(f"characters\genshin\{character}.json")
    
    character_id = torch.tensor([int(character_data['char_id'])])
    
    user_data = get_user(r"characters\user.json")
    
    if chat_status == 'init':
        # text = []
        text.clear()
        text = generate_sys_prompt(text, character_data, user_data)
    elif chat_status == 'chating':
        # text = json.dumps(text_data, ensure_ascii=False, indent=2)
        text_data = json.loads(text_data)
        print("text_data:", text_data, type(text_data))
        pass
    
    name = character_data.get('char_name', '')
    
    t3 = time.time()# ; print("prompt generate time:", t3-t2, "s")
    
    if text_data or audio_file or image_file:
        if audio_file:
            # 调用函数进行音频转写
            text_res = audio_to_text(audio_file, vosk_model)
            Input = text_process(text_res)
        elif text_data:
            Input = text_data
        t4 = time.time()# ; print("audio process time:", t4-t3, "s")
        print(f"Voice Input: {Input}")
        text = getCharacterText(text, "user", Input, name)
        
        SparkApi.answer = ""
        SparkApi.main(appid,api_key,api_secret,Spark_url,domain,text)
        t5 = time.time()# ; print("spark api time:", t5-t4, "s")
        
        text = clearPromptText(text, Input)
        
        answer = SparkApi.answer
        text = getText(text, "assistant", answer)
        # print(f"answer: {answer}")
        print(f"text: {text}")
        
        if answer != '':
            audio_path = "answer.wav"
            sample_rate, audio = vits(answer, 0, character_id, 0.1, 0.668, 1.2, hps_ms, device, speakers, net_g_ms, limitation)
            t6 = time.time()# ; print("vits time:", t6-t5, "s")
            sf.write(audio_path, audio, samplerate=sample_rate)
            with open(audio_path, 'rb') as audio_file:
                audio_base64 = base64.b64encode(audio_file.read()).decode('utf-8')
            t7 = time.time()# ; print("audio encode time:", t7-t6, "s")

    
    if image_file:
        # image_path = os.path.join(app.config['UPLOAD_FOLDER'], image_file.filename)
        # image_file.save(image_path)
        # 这里可以加入图像处理逻辑
        pass

    from takway.my_utils import format_table
    header = ["Event", "Time (s)"]
    # 行数据
    rows = [
        ("Data Prepare", t2 - t1),
        ("Prompt Generate", t3 - t2),
        ("Audio Process", t4 - t3),
        ("Spark Api", t5 - t4),
        ("Vits", t6 - t5),
        ("Audio Encode", t7 - t6),
        ("Total Time", t7 - t1)
    ]
    # 格式化并打印表格
    format_table(header, rows)
    
    # 返回处理后的数据
    return jsonify({'text': text, 'audio_base64': audio_base64, 'audio': {'sample_rate': sample_rate, 'CHUNK': CHUNK, 'FORMAT': 16, 'CHANNELS': CHANNELS}})

if __name__ == "__main__":
    app.run(host='0.0.0.0', port=5000, debug=False)