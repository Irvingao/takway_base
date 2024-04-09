import logging
from fastapi import FastAPI, Request, File, UploadFile, Form, Depends, HTTPException
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
from sqlalchemy.orm import Session
from models.models import Base, CharacterModel, SessionLocal, engine
import redis
import uuid

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
    db_character = CharacterModel(**character.model_dump())
    db.add(db_character)
    db.commit()
    db.refresh(db_character)
    return Character.model_validate(db_character, from_attributes=True)

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
async def create_session(request: SessionRequest):
    uid = request.uid
    char_id = request.char_id
    session_id = str(uuid.uuid4())

    # 创建或更新会话
    session_data = {
        "uid": uid,
        "messages": "[]",
        "user_info": "{}",
        "char_id": str(char_id),
        "token": "0"
    }

    r.hmset(session_id, session_data)

    return {
        "session_id": session_id,
        "uid": uid,
        "messages": [],
        "user_info": {},
        "char_id": char_id,
        "token": 0
    }

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

# 初始化全局变量，用于存储会话状态
sessions = {}

# LLM Chat API 配置
API_KEY = "eyJhbGciOiJSUzI1NiIsInR5cCI6IkpXVCJ9.eyJHcm91cE5hbWUiOiJUYWt3YXkuQUkiLCJVc2VyTmFtZSI6IlRha3dheS5BSSIsIkFjY291bnQiOiIiLCJTdWJqZWN0SUQiOiIxNzY4NTM2ODA1NjIxMTIxMjA4IiwiUGhvbmUiOiIxMzA4MTg1ODcwNCIsIkdyb3VwSUQiOiIxNzY4NTM2ODA1NTc0OTgzODY0IiwiUGFnZU5hbWUiOiIiLCJNYWlsIjoiIiwiQ3JlYXRlVGltZSI6IjIwMjQtMDMtMjMgMjI6Mjc6NDUiLCJpc3MiOiJtaW5pbWF4In0.ZpSw5t_90KTt0EceDqkmDE88DyB1GufB4_fwvaMLs7f7ojesh0Q4nT0jdcfX5Y9_wve4nVifoRFhHW9h-biEn_yWxilzZbGGbwY5FVf_J-Bm3GL-9V7uHOxyynrNTRfqngW9SoWyAl-F1nbRCV1doQ_3XKsvsQ1yRYvGQTTM0F4WEbG4ijIh0X9U7sS9a3IU4Nz80mc-TaK2G19cfhHvHl1rUCi_RJC-0zU4aYK7XhJRBFidBv7QquQnYvbkNKJBlNqH04_d0aBr2pX-mleYXFEujSNxS81E7LEBn146m72zCj1OZSDY4PnOuJmVukWa-LZL8rswnkC70fL6em4g9Q"
url = "https://api.minimax.chat/v1/text/chatcompletion_v2"

# 流式请求？？？
# @app.route('/character-chat', methods=['POST'])
# def handle_all():
#     takway_app.stream_request_receiver_process()
#     return Response(takway_app.generate_stream_queue_data())

@app.post("/chat")
async def chat(text: str = Form(None), meta_info: str = Form(...), audio: UploadFile = File(None)):
    meta_info_dict = json.loads(meta_info)
    uid = meta_info_dict.get("uid")

    # 获取会话信息
    if not r.exists(uid):
        raise HTTPException(status_code=404, detail="Session not found")
    session_data = r.hgetall(uid)
    messages = json.loads(session_data["messages"])
    char_id = session_data["char_id"]
    token_count = int(session_data["token"])

    # 更新会话
    r.hmset(uid, {
        "messages": json.dumps(messages),
        "token": token_count
    })

    # 处理音频输入
    if audio:
        audio_data = await audio.read()
        audio_path = f"temp_audio_{time.time()}.wav"
        with open(audio_path, "wb") as f:
            f.write(audio_data)
        text = audio_to_text(audio_path)
        os.remove(audio_path)  # 删除临时音频文件

    # 处理文本输入
    if text:
        # 添加用户消息到会话历史
        sessions[uid]["messages"].append({"role": "user", "content": text})
        token_count += len(text)  # 更新 token 计数
        # 调用 chat_completions 函数处理文本聊天
        chat_completions(sessions[uid]["messages"], uid)

    char_info = get_db().query(Character).filter(Character.char_id == char_id).first()
    if not char_info:
        raise HTTPException(status_code=404, detail="Character not found")

    # 生成语音响应
    if meta_info_dict.get("voice_synthesize",True):
        response_audio_path = process_tts(sessions[uid]["messages"][-1]["content"])
    else:
        response_audio_path = ""

    # 返回响应
    response = ChatResponse(text=sessions[uid]["messages"][-1]["content"], meta_info=meta_info_dict, audio_path=response_audio_path)
    return response

def audio_to_text(audio_path):
    """
    Convert audio to text using FunAutoSpeechRecognizer.
    """
    if audio_path == None or "":
        return None
    
    logging.info(f"audio_path:{audio_path}")
    
    audio_data = reshape_sample_rate(audio_path)
    transcription_dict = asr.streaming_recognize(audio_data, auto_det_end=True)
    
    transcription = ''.join(transcription_dict['text'])
    logging.info(f"transcription:{transcription}")
        
    return transcription

def process_tts(text):
    """
    Convert text to speech using TextToSpeech.
    """
    time_stamp = time.strftime("%Y%m%d-%H%M%S")
    directory = './audio_cache/'
    if not os.path.exists(directory):
        os.makedirs(directory)
    path = directory + 'audio_' + time_stamp + '.wav'
    text = remove_brackets_and_contents(text)
    sr, audio = tts.synthesize(text)
    tts.save_audio(audio, sr, file_name=path)
    return path

def chat_completions(messages, uid):
    """
    Call the chat API to get completions.
    """
    headers = { 
        "Content-Type": "application/json",
        "Authorization": f"Bearer {API_KEY}"
    }
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
    content = response.json()['choices'][0]['message']['content']
    # 更新会话历史
    sessions[uid]["messages"].append({"role": "assistant", "content": content})
######################################## llm api end ########################################

if __name__ == "__main__":
    logger.info("Starting server...")
    uvicorn.run(app, host="0.0.0.0", port=8001)
