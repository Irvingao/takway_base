import requests
import json

def do_request():
    url = "https://api.baichuan-ai.com/v1/chat/completions"
    api_key = "sk-a10dfa7b93832e0ccaafcc5d7aaaf9ea"
    data = {
        "model": "Baichuan-NPC-Turbo",
        "character_profile": {
            "character_name":"大罗",
            "character_info":"角色基本信息：大罗被广泛认为是有史以来最伟大的足球运动员之一。因为其强悍恐怖的攻击力被冠以“外星人”称号。大罗曾三度当选世界足球先生、两度获得金球奖，为巴西夺得两次世界杯冠军及一次亚军。效力过皇家马德里，巴塞罗那，AC米兰，国际米兰等豪门俱乐部，进球无数。",
            "user_name":"小乐",
            "user_info":"某体育频道解说员，在中国举办的大罗球迷见面会上做为主持人"
        },
        "messages": [
            {
               "role": "user",
               "content": "你参加过几次世界杯？"
            }
        ],
        "temperature": 0.8,
        "top_k":10,
        "max_tokens": 512,
        "stream": True
    }

    json_data = json.dumps(data)

    headers = {
        "Content-Type": "application/json",
        "Authorization": "Bearer " + api_key
    }

    response = requests.post(url, data=json_data, headers=headers, timeout=60)

    if response.status_code == 200:
        print("请求成功！")
        print("响应body:", response.text)
        print("请求成功，X-BC-Request-Id:", response.headers.get("X-BC-Request-Id"))
    else:
        print("请求失败，状态码:", response.status_code)
        print("请求失败，body:", response.text)
        print("请求失败，X-BC-Request-Id:", response.headers.get("X-BC-Request-Id"))

if __name__ == "__main__":
    do_request()

              