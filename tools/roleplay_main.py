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
domain = "generalv3"    # v2.0版本
#云端环境的服务地址
# Spark_url = "ws://spark-api.xf-yun.com/v1.1/chat"  # v1.5环境的地址
# Spark_url = "ws://spark-api.xf-yun.com/v2.1/chat"  # v2.0环境的地址
Spark_url = "ws://spark-api.xf-yun.com/v3.1/chat"  # v3.0环境的地址

text =[]

def getText(text, role,content):
    jsoncon = {}
    jsoncon["role"] = role
    jsoncon["content"] = f"{content}"
    text.append(jsoncon)
    return text

def getlength(text):
    length = 0
    for content in text:
        temp = content["content"]
        leng = len(temp)
        length += leng
    return length

def checklen(text):
    while (getlength(text) > 8000):
        del text[0]
    return text

def text_process(word_list):
    irregular_str = ' '.join(word_list)
    # 去掉字符串中的方括号和单引号
    clean_str = irregular_str.replace("[", "").replace("]", "").replace("'", "").replace(" ", "")
    return clean_str

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


def tts_model_init(model_dir="./model", device='cuda'):
    limitation = os.getenv("SYSTEM") == "spaces"  # limit text and audio length in huggingface spaces

    device = torch.device(device)

    hps_ms = utils.get_hparams_from_file(os.path.join(model_dir, r'config.json'))
    net_g_ms = SynthesizerTrn(
        len(hps_ms.symbols),
        hps_ms.data.filter_length // 2 + 1,
        hps_ms.train.segment_size // hps_ms.data.hop_length,
        n_speakers=hps_ms.data.n_speakers,
        **hps_ms.model)
    _ = net_g_ms.eval().to(device)
    speakers = hps_ms.speakers

    model, optimizer, learning_rate, epochs = utils.load_checkpoint(os.path.join(model_dir, r'G_953000.pth'), net_g_ms, None)

    return hps_ms, device, speakers, net_g_ms, limitation
hps_ms, device, speakers, net_g_ms, limitation = tts_model_init()

import wave
import pyaudio
answer_file = 'answer.wav'
def audio_play():
    CHUNK = 1024
    wf = wave.open(answer_file, 'rb')#(sys.argv[1], 'rb'
    p = pyaudio.PyAudio()

    stream = p.open(format=p.get_format_from_width(wf.getsampwidth()),
                    channels=wf.getnchannels(),
                    rate=wf.getframerate(),
                    output=True)

    data = wf.readframes(CHUNK)

    while len(data) > 0:
        stream.write(data)
        data = wf.readframes(CHUNK)

    stream.stop_stream()
    stream.close()

    p.terminate()

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
    global chatbot
    max_token_limit = 8000
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
### 输入是一段语音转换后的文字，可能存在可能存在不准确或不清晰的部分，你需要根据语境对该问题进行合理理解:
{content}
### 输出需要始终使用在聊天历史中未曾出现的新颖独特的信息进行回应，根据你的角色使用简短口语化的回答回应以下消息:
{name}:"""
    text.append(jsoncon)
    return text


def main(args):

    text.clear
    
    # character_data = get_character(r"characters\genshin\{}.json".format(args.character_name))
    character_data = get_character(f"characters\genshin\{args.character_name}.json")
    
    character_id = torch.tensor([int(character_data['char_id'])])
    
    user_data = get_user(r"characters\user.json")
    
    generate_sys_prompt(character_data, user_data)
    
    name = character_data.get('char_name', '')

    while True:
        # 调用函数进行录音
        record_audio(wav_file_path)
        
        # 调用函数进行音频转写
        text_res = audio_to_text(wav_file_path, vosk_model)

        Input = text_process(text_res)
        print(f"Voice Input: {Input}")
        # Input = "可莉，我们去钓鱼吧"
        # question = checklen(getText("user",Input))
        question = checklen(getCharacterText("user",Input,name))
        # print("question:", question)
        SparkApi.answer =""
        # print("答:",end = "")
        SparkApi.main(appid,api_key,api_secret,Spark_url,domain,question)
        getText("assistant",SparkApi.answer)
        # print(text)
        answer = SparkApi.answer
        print(f"answer: {answer}")
        print(f"text: {text}")
        
        # import pdb; pdb.set_trace()
        if answer != '':
            sr, audio = vits(answer, 0, character_id, 0.1, 0.668, 1.2, hps_ms, device, speakers, net_g_ms, limitation)
            print(f"Audio sr: {sr}")
            sf.write(answer_file, audio, samplerate=sr)
            
            audio_play()


if __name__ == "__main__":
    import argparse
    parser = argparse.ArgumentParser(description="Process character name.")
    parser.add_argument("character_name", type=str, help="Name of the Genshin Impact character")
    
    args = parser.parse_args()
    main(args)