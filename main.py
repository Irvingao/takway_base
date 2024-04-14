import logging
from fastapi import FastAPI, Request, File, UploadFile, Form, Depends, HTTPException ,WebSocket
from fastapi.responses import JSONResponse, FileResponse
from pydantic import BaseModel
import uvicorn
import json
import time
import os
import requests
from takway.audio_utils import BaseRecorder, reshape_sample_rate
from takway.stt.funasr_utils import FunAutoSpeechRecognizer
from takway.tts.vits_utils import TextToSpeech
from takway.common_utils import remove_brackets_and_contents
from takway.satt import generate_xf_satt_url
from sqlalchemy.orm import Session
from takway.roleplay_utils import BaseCharacterInfo
from takway.sqls.models import Base, CharacterModel, SessionLocal, engine
import redis
import uuid
import _thread as thread
from config import config
import websocket
from flask import request
import queue
import base64
import io

######################################## log init start ########################################
logger = logging.getLogger('takway_log')
logger.setLevel(logging.DEBUG)

file_handler = logging.FileHandler('takway_log.log')
file_handler.setLevel(logging.DEBUG)
file_handler.setFormatter(logging.Formatter('%(asctime)s - %(name)s - %(levelname)s - %(message)s'))

stream_handler = logging.StreamHandler()
stream_handler.setLevel(logging.DEBUG)
stream_handler.setFormatter(logging.Formatter('%(asctime)s - %(name)s - %(levelname)s - %(message)s'))

logger.addHandler(file_handler)
logger.addHandler(stream_handler)
######################################## log init end ########################################

app = FastAPI()

######################################## request models start ########################################
class Character(BaseModel):
    char_id: int
    voice_id: int
    char_name: str
    wakeup_words: str
    world_scenario: str
    description: str
    emojis: list
    dialogues: str

class SessionRequest(BaseModel):
    uid: str
    char_id: int

class SessionResponse(BaseModel):
    session_id: str
    uid: str
    messages: list
    user_info: dict
    char_id: int
    token: int

class ChatRequest(BaseModel):
    text: str = None
    meta_info: dict

class ChatResponse(BaseModel):
    text: str = None
    meta_info: dict
    audio_path: str = None

class ChatHttpRequest(BaseModel):
    format :str
    rate:int
    session_id: str
    speech:str
######################################## request models end ########################################


######################################## character crud start ########################################
def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close() 

@app.post("/characters/", response_model=Character)
def create_character(character: Character, db: Session = Depends(get_db)):
    try:
        db_character = CharacterModel(**character.model_dump())
        db.add(db_character)
        db.commit()
        db.refresh(db_character)
        return Character.model_validate(db_character, from_attributes=True)
    except Exception as e:
        raise HTTPException(status_code=409,detail=str(e))

@app.get("/characters/{char_id}", response_model=Character)
def read_character(char_id: int, db: Session = Depends(get_db)):
    logger.info(f"read_character char_id:{char_id}")
    character = db.query(CharacterModel).filter(CharacterModel.char_id == char_id).first()
    logger.info(f"character:{character}")
    if character is None:
        raise HTTPException(status_code=404, detail="Character not found")
    return Character.model_validate(character, from_attributes=True)

@app.put("/characters/{char_id}", response_model=Character)
def update_character(char_id: int, character: Character, db: Session = Depends(get_db)):
    db_character = db.query(CharacterModel).filter(CharacterModel.char_id == char_id).first()
    if db_character is None:
        raise HTTPException(status_code=404, detail="Character not found")
    for key, value in character.dict().items():
        setattr(db_character, key, value)
    db.commit()
    return Character.model_validate(db_character, from_attributes=True)

@app.delete("/characters/{char_id}", response_model=Character)
def delete_character(char_id: int, db: Session = Depends(get_db)):
    character = db.query(CharacterModel).filter(CharacterModel.char_id == char_id).first()
    if character is None:
        raise HTTPException(status_code=404, detail="Character not found")
    db.delete(character)
    db.commit()
    return Character.model_validate(character, from_attributes=True)
######################################## character crud end ########################################

######################################## session crud start ########################################
r = redis.Redis(host='127.0.0.1', port=6379, db=0, decode_responses=True, password='takway')

def get_redis():
    return r

@app.post("/session", response_model=SessionResponse)
async def create_session(request: SessionRequest,db: Session = Depends(get_db)):
    try:
        uid = request.uid
        char_id = request.char_id
        session_id = str(uuid.uuid4())

        db_character =  db.query(CharacterModel).filter(CharacterModel.char_id == char_id).first()
        system_prompt = f"""我们正在角色扮演对话游戏中，你需要始终保持角色扮演并待在角色设定的情景中，你扮演的角色信息如下：\n{"角色名称: " + db_character.char_name}。\n{"角色背景: " + db_character.description}\n{"角色所处环境: " + db_character.world_scenario}\n{"角色的常用问候语: " + db_character.wakeup_words}。\n\n你需要用简单、通俗易懂的口语化方式进行对话，在没有经过允许的情况下，你需要保持上述角色，不得擅自跳出角色设定。\n"""

        messages = [{"role":"system","content":f"{system_prompt}"}]

        # 创建或更新会话
        session_data = {
            "uid": uid,
            "messages": json.dumps(messages,ensure_ascii=False),
            "user_info": "{}",
            "char_id": str(char_id),
            "token": "0"
        }

        r.hmset(session_id, session_data)
        

        return {
            "session_id": session_id,
            "uid": uid,
            "messages": messages,
            "user_info": {},
            "char_id": char_id,
            "token": 0
        }
    except Exception as e:
        raise HTTPException(status_code=409,detail=str(e))

@app.get("/session/{session_id}", response_model=SessionResponse)
async def get_session(session_id: str):
    if not r.exists(session_id):
        raise HTTPException(status_code=404, detail="Session not found")

    session_data = r.hgetall(session_id)

    return {
        "session_id": session_id,
        "uid": session_data["uid"],
        "messages": json.loads(session_data["messages"]),
        "user_info": json.loads(session_data["user_info"]),
        "char_id": int(session_data["char_id"]),
        "token": int(session_data["token"])
    }

######################################## session crud end ########################################

######################################## llm api start ########################################
# 初始化语音识别和语音合成
rec = BaseRecorder()
asr = FunAutoSpeechRecognizer()
tts = TextToSpeech(device='cuda')


# LLM Chat API 配置
API_KEY = "eyJhbGciOiJSUzI1NiIsInR5cCI6IkpXVCJ9.eyJHcm91cE5hbWUiOiJUYWt3YXkuQUkiLCJVc2VyTmFtZSI6IlRha3dheS5BSSIsIkFjY291bnQiOiIiLCJTdWJqZWN0SUQiOiIxNzY4NTM2ODA1NjIxMTIxMjA4IiwiUGhvbmUiOiIxMzA4MTg1ODcwNCIsIkdyb3VwSUQiOiIxNzY4NTM2ODA1NTc0OTgzODY0IiwiUGFnZU5hbWUiOiIiLCJNYWlsIjoiIiwiQ3JlYXRlVGltZSI6IjIwMjQtMDMtMjMgMjI6Mjc6NDUiLCJpc3MiOiJtaW5pbWF4In0.ZpSw5t_90KTt0EceDqkmDE88DyB1GufB4_fwvaMLs7f7ojesh0Q4nT0jdcfX5Y9_wve4nVifoRFhHW9h-biEn_yWxilzZbGGbwY5FVf_J-Bm3GL-9V7uHOxyynrNTRfqngW9SoWyAl-F1nbRCV1doQ_3XKsvsQ1yRYvGQTTM0F4WEbG4ijIh0X9U7sS9a3IU4Nz80mc-TaK2G19cfhHvHl1rUCi_RJC-0zU4aYK7XhJRBFidBv7QquQnYvbkNKJBlNqH04_d0aBr2pX-mleYXFEujSNxS81E7LEBn146m72zCj1OZSDY4PnOuJmVukWa-LZL8rswnkC70fL6em4g9Q"
url = "https://api.minimax.chat/v1/text/chatcompletion_v2"

# 流式请求？？？
# @app.route('/character-chat', methods=['POST'])
# def handle_all():
#     takway_app.stream_request_receiver_process()
#     return Response(takway_app.generate_stream_queue_data())

CHAT_TEXT = 0
CHAT_AUDIO = 1
CHAT_UNCERTAIN = -1

FIRST_FRAME = 1
CONTINUE_FRAME =2
LAST_FRAME =3

RESPONSE_TEXT = 0
RESPONSE_AUDIO = 1

@app.post("/chat_http")
async def chat_http(chat_http_request:ChatHttpRequest):
    speech = chat_http_request.speech
    session_id =  chat_http_request.session_id
    url = generate_xf_satt_url()
    current_message = ""

    # 收到websocket连接建立的处理
    def on_open(ws):
        def run(*args):
            frameSize = 8000  # 每一帧的音频大小
            intervel = 0.04  # 发送音频间隔(单位:s)
            status = FIRST_FRAME  # 音频的状态信息，标识音频是第一帧，还是中间帧、最后一帧
            with io.StringIO(speech) as fp:
                while True:
                    buf = fp.read(frameSize)
                    # 文件结束
                    if not buf:
                        status = LAST_FRAME
                    # 第一帧处理
                    # 发送第一帧音频，带business 参数
                    # appid 必须带上，只需第一帧发送
                    if status == FIRST_FRAME:
                        d = {"common": {"app_id": config['xfapi']['APPID']},
                            "business": {"domain": config['satt']['domain'], "language": config['satt']['language'],"accent": config['satt']['accent'], "vad_eos": config['satt']['vad_eos']},
                            "data": {"status": 0, "format": "audio/L16;rate=16000",
                                    "audio": buf,
                                    "encoding": "raw"}}
                        d = json.dumps(d)
                        ws.send(d)
                        status = CONTINUE_FRAME
                    # 中间帧处理
                    elif status == CONTINUE_FRAME:
                        d = {"data": {"status": 1, "format": "audio/L16;rate=16000",
                                    "audio": buf,
                                    "encoding": "raw"}}
                        ws.send(json.dumps(d))
                    # 最后一帧处理
                    elif status == LAST_FRAME:
                        d = {"data": {"status": 2, "format": "audio/L16;rate=16000",
                                    "audio": buf,
                                    "encoding": "raw"}}
                        ws.send(json.dumps(d))
                        time.sleep(0.05)
                        break
                    # 模拟音频采样间隔
                    time.sleep(intervel)
            ws.close()
        thread.start_new_thread(run, ())

    def on_message(ws, message):
        try:
            nonlocal current_message
            code = json.loads(message)["code"]
            sid = json.loads(message)["sid"]
            if code != 0:
                errMsg = json.loads(message)["message"]
                raise HTTPException(status_code=409,detail="sid:%s call error:%s code is:%s" % (sid, errMsg, code))
            else:
                data = json.loads(message)["data"]["result"]["ws"]
                result = ""
                for i in data:
                    for w in i["cw"]:
                        result += w["w"]
                current_message+=result
        except Exception as e:
            raise HTTPException(status_code=409,detail=f"receive msg,but parse exception:{str(e)}")
    
    def on_close(ws,a,b):
        print("### closed ###")

    def on_error(ws,error):
        print("### error:", error)
    try:
        websocket.enableTrace(False)
        xfws = websocket.WebSocketApp(url,on_message=on_message,on_close=on_close,on_error=on_error)
        xfws.on_open=on_open
        xfws.run_forever()
    except Exception as e:
        raise HTTPException(status_code=409,detail=f"error occur when calling xf api: {str(e)}" )

    print(f"user message: {current_message}")
    if not r.exists(session_id):
        raise HTTPException(status_code=404,detail="session not found")
    
    try:
        session_data = r.hgetall(session_id)
        messages = json.loads(session_data['messages'])
        messages.append({"role":"user","content":f"{current_message}"})
    except:
        raise HTTPException(status_code=409,detail=f"error occur when getting session data: {str(e)}" )

    try:
        payload = json.dumps({
            "model":"abab5.5-chat",
            "stream":True,
            "messages": messages,
            "tool_choice":"auto",
            "max_tokens":10000,
            "temperature":0.9,
            "top_p":1
        })
        headers={
            'Authorization':f"Bearer {config['llm']['API_KEY']}",
            'Content-Type':'application/json'
        }
        response = requests.request("POST",config["llm"]["url"],headers=headers,data=payload)

        llm_response = ""
        if response.status_code == 200:
            for line in response.iter_lines():
                if line:
                    decoded_line = line.decode('utf-8')
                    llm_message_str = decoded_line.split('data: ')[1]
                    llm_message = json.loads(llm_message_str)
                    if llm_message["object"]=="chat.completion.chunk":
                        llm_response += llm_message["choices"][0]['delta']["content"]
                else:
                    break
        print(f"llm_response: {llm_response}")
        messages.append({"role":"assistant","content":f"{llm_response}"})
        session_data["messages"] = json.dumps(messages,ensure_ascii=False)
        r.hmset(session_id,session_data)
    except Exception as e:
        raise HTTPException(status_code=409,detail=f"error occur when calling llm: {str(e)}" )

    try:
        group_id = config["tta"]["group_id"]
        api_key = config["tta"]["API_KEY"]
        tta_url = f'{config["tta"]["url"]}?GroupId={group_id}'
        headers = {
            "Authorization": f"Bearer {api_key}",
            "Content-Type": "application/json",
        }
        data = {
            "voice_id": "female-tianmei-jingpin",
            # 如同时传入voice_id和timber_weights时，则会自动忽略voice_id，以timber_weights传递的参数为准
            "text": f"{llm_response}",
            # 如需要控制停顿时长，则增加输入<#X#>，X取值0.01-99.99，单位为秒，如：你<#5#>好（你与好中间停顿5秒）需要注意的是文本间隔时间需设置在两个可以语音发音的文本之间，且不能设置多个连续的时间间隔。
            "model": "speech-01",
            "speed": 1.0,
            "vol": 1.0,
            "pitch": 0,
            "audio_sample_rate": 24000,
            "bitrate": 128000,
            "char_to_pitch": ["你/(ni1)"]
        }
        response = requests.post(tta_url, headers=headers, json=data)
        if response.status_code == 200:
            data = response.json()
            audio_file = data.get('audio_file', None)
        return {"code":200,"audio_path":f"{audio_file}"}
    except Exception as e:
        raise HTTPException(status_code=409,detail=f"error occur when doing text to audio: {str(e)}" )



@app.websocket("/chat")
async def chat(ws: WebSocket):
    await ws.accept()

    q_recv = queue.Queue()
    current_message = ""
    chat_type = CHAT_UNCERTAIN
    response_type = RESPONSE_TEXT
    session_id = ""
    
    async def usr_chat_recv():
        nonlocal current_message
        nonlocal chat_type
        nonlocal session_id
        nonlocal response_type
        try:
            while True:
                data_json = await ws.receive_json()
                q_recv.put(data_json)
                if data_json["text"]:
                    if data_json["meta_info"]["voice_synthesize"]:
                        response_type = RESPONSE_AUDIO
                    chat_type = CHAT_TEXT
                    current_message = data_json['text']
                    session_id = data_json["meta_info"]["session_id"]
                    break
                else:
                    chat_type = CHAT_AUDIO

                if data_json['meta_info']["is_end"]:
                    if data_json["meta_info"]["voice_synthesize"]:
                        response_type = RESPONSE_AUDIO
                    session_id = data_json["meta_info"]["session_id"]
                    break
        except Exception as e:
            error_message = {"type":"error","code":500,"msg":f"error occur when receiving data from front: {str(e)}"}
            print(error_message)
            ws.send_text(json.dumps(error_message))
    
    
    async def user_chat_send():
        url = generate_xf_satt_url()
        def on_open(xfws):
            def run(*args):
                interval = 0.04
                status = FIRST_FRAME
                while True:
                    data_json = q_recv.get()
                    if data_json["meta_info"]["is_end"]:
                        status = LAST_FRAME
                    if status == FIRST_FRAME:
                        d = {"common": {"app_id": config['xfapi']['APPID']},
                            "business": {"domain": config['satt']['domain'], "language": config['satt']['language'],"accent": config['satt']['accent'], "vad_eos": config['satt']['vad_eos']},
                            "data": {"status": 0, "format": "audio/L16;rate=16000",
                                    "audio": data_json["audio"],
                                    "encoding": "raw"}}
                        d = json.dumps(d)
                        xfws.send(d)
                        status = CONTINUE_FRAME
                    elif status == CONTINUE_FRAME:
                        d = {"data": {"status": 1, "format": "audio/L16;rate=16000",
                                    "audio": data_json["audio"],
                                    "encoding": "raw"}}
                        xfws.send(json.dumps(d))
                    elif status == LAST_FRAME:
                        d = {"data": {"status": 2, "format": "audio/L16;rate=16000",
                                    "audio": data_json["audio"],
                                    "encoding": "raw"}}
                        xfws.send(json.dumps(d))
                        time.sleep(0.05)
                        break
                    time.sleep(interval)
                xfws.close()
            thread.start_new_thread(run,())
        
        def  on_message(xfws,message):       
            try:
                nonlocal current_message
                code = json.loads(message)["code"]
                sid = json.loads(message)["sid"]
                if code != 0:
                    errMsg = json.loads(message)["message"]
                    print("sid:%s call error:%s code is:%s" % (sid, errMsg, code))
                else:
                    data = json.loads(message)["data"]["result"]["ws"]
                    # print(json.loads(message))
                    result = ""
                    for i in data:
                        for w in i["cw"]:
                            result += w["w"]
                    current_message += result
            except Exception as e:
                print("receive msg,but parse exception:", e)
        
        def on_close(xfws,a,b):
            print("### closed ###")

        def on_error(xfws,error):
            print("### error:", error)
        
        websocket.enableTrace(False)
        xfws = websocket.WebSocketApp(url,on_message=on_message,on_close=on_close,on_error=on_error)
        xfws.on_open=on_open
        xfws.run_forever()

    await usr_chat_recv()
    if chat_type==CHAT_AUDIO:
        await user_chat_send()



    if not r.exists(session_id):
        error_message = {"type":"error","code":500,"msg":f"error occur when getting session_data: session_id not found"}
        await ws.send_text(json.dumps(error_message))

    try:
        print(f"user input : {current_message}")
        msg_input = {"type":"debug_msg","code":200,"msg":f"receieve from user: {current_message}"}
        await ws.send_text(json.dumps(msg_input,ensure_ascii=False))

        session_data = r.hgetall(session_id)
        print(f"session_data = {session_data}")   
        messages = json.loads(session_data["messages"])
        token_count = int(session_data["token"])

        messages.append({"role":"user","content":current_message})
        token_count += len(current_message)

    except Exception as e:
        error_message = {"type":"error","code":500,"msg":f"error occur when haddling session data: {str(e)}"}
        print(error_message)
        await ws.send_text(json.dumps(error_message))


    try:
        payload = json.dumps({
            "model":"abab5.5-chat",
            "stream":True,
            "messages": messages,
            "tool_choice":"auto",
            "max_tokens":10000,
            "temperature":0.9,
            "top_p":1
        })
        headers={
            'Authorization':f"Bearer {config['llm']['API_KEY']}",
            'Content-Type':'application/json'
        }
        response = requests.request("POST",config["llm"]["url"],headers=headers,data=payload)
    except Exception as e:
        error_message = {"type":"error","code":500,"msg":f"error occur when sending data to the llm: {str(e)}"}
        print(error_message)
        await ws.send_text(json.dumps(error_message))

    def split_string_with_punctuation(text):
        punctuations = "，！？。"
        result = []
        current_sentence = ""
        for char in text:
            current_sentence += char
            if char in punctuations:
                result.append(current_sentence)
                current_sentence = ""
        # 判断最后一个字符是否为标点符号
        if current_sentence and current_sentence[-1] not in punctuations:
            # 如果最后一段不以标点符号结尾，则加入拆分数组
            result.append(current_sentence)
        return result

    llm_response = ""
    try:
        response_buf = ""
        if response.status_code == 200:
            for line in response.iter_lines():
                if line:
                    if response_type == RESPONSE_TEXT:
                        decoded_line = line.decode('utf-8')
                        llm_message_str = decoded_line.split('data: ')[1]
                        llm_message = json.loads(llm_message_str)
                        if llm_message["object"]=="chat.completion.chunk":
                            llm_response += llm_message["choices"][0]['delta']["content"]
                            text_message = {"type":"text","code":200,"msg":llm_message["choices"][0]['delta']["content"]}    
                            await ws.send_text(json.dumps(text_message,ensure_ascii=False))
                        else:
                            break
                    elif response_type == RESPONSE_AUDIO:
                        decoded_line = line.decode('utf-8')
                        llm_message_str = decoded_line.split('data: ')[1]
                        llm_message = json.loads(llm_message_str)
                        if llm_message["object"]=="chat.completion.chunk":
                            llm_response += llm_message["choices"][0]['delta']["content"]
                            response_buf += llm_message["choices"][0]['delta']["content"]
                            splitted_llm_text = split_string_with_punctuation(response_buf)
                            if splitted_llm_text[-1] and splitted_llm_text[-1] not in "，。？！":
                                response_buf = splitted_llm_text[-1]
                                del splitted_llm_text[-1]
                            else:
                                response_buf = ""
                            if len(splitted_llm_text) !=0:
                                for sentence in splitted_llm_text:
                                    sr,audio = tts.synthesize(sentence,0,103,0.1,0.668,1.2,False,False)
                                    audio_message = {"type":"audio","code":200,"msg":base64.b64encode(audio).decode('utf-8')}
                                    await ws.send_text(json.dumps(audio_message))
                        else:
                            break
    except Exception as e:
        error_message = {"type":"error","code":500,"msg":f"error occur when responding to the clint: {str(e)}"}
        print(error_message)
        await ws.send_text(json.dumps(error_message))
    try:
        messages.append({'role':'assistant',"content":llm_response})
        token_count += len(llm_response)
        session_data["messages"] = json.dumps(messages)
        session_data["token"] = str(token_count)
        
        r.hmset(session_id,session_data)
    except Exception as e:
        error_message = {"type":"error","code":500,"msg":f"error occur when updating session: {str(e)}"}
        print(error_message)
        await ws.send_text(json.dumps(error_message))
    
    close_message = {"type":"close","code":200,"msg":""}
    await ws.send_text(json.dumps(close_message))
    time.sleep(0.5)
    await ws.close()

    


if __name__ == "__main__":
    logger.info("Starting server...")
    uvicorn.run(app, host="0.0.0.0", port=config["main"]['port'])
