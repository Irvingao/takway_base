import requests

group_id="group_id"
api_key="api_key"

url = "https://api.minimax.chat/v1/text/chatcompletion_pro?GroupId=" + group_id
headers = {"Content-Type": "application/json", "Authorization": "Bearer " + api_key}

payload = {
    "bot_setting": [
        {
            "bot_name": "MM智能助理",
            "content": "MM智能助理是一款由MiniMax自研的，没有调用其他产品的接口的大型语言模型。MiniMax是一家中国科技公司，一直致力于进行大模型相关的研究。",
        }
    ],
    "messages": [{"sender_type": "USER", "sender_name": "小明", "text": "帮我用英文翻译下面这句话：我是谁"}],
    "reply_constraints": {"sender_type": "BOT", "sender_name": "MM智能助理"},
    "model": "abab5.5-chat",
    "tokens_to_generate": 1034,
    "temperature": 0.01,
    "top_p": 0.95,
}

response = requests.request("POST", url, headers=headers, json=payload)

print(response.status_code)
print(response.text)