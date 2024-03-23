# -*- coding: utf-8 -*-
import requests
import json
import binascii

group_id = "1768536805574983864"
api_key = "eyJhbGciOiJSUzI1NiIsInR5cCI6IkpXVCJ9.eyJHcm91cE5hbWUiOiJUYWt3YXkuQUkiLCJVc2VyTmFtZSI6IlRha3dheS5BSSIsIkFjY291bnQiOiIiLCJTdWJqZWN0SUQiOiIxNzY4NTM2ODA1NjIxMTIxMjA4IiwiUGhvbmUiOiIxMzA4MTg1ODcwNCIsIkdyb3VwSUQiOiIxNzY4NTM2ODA1NTc0OTgzODY0IiwiUGFnZU5hbWUiOiIiLCJNYWlsIjoiIiwiQ3JlYXRlVGltZSI6IjIwMjQtMDMtMjMgMjI6Mjc6NDUiLCJpc3MiOiJtaW5pbWF4In0.ZpSw5t_90KTt0EceDqkmDE88DyB1GufB4_fwvaMLs7f7ojesh0Q4nT0jdcfX5Y9_wve4nVifoRFhHW9h-biEn_yWxilzZbGGbwY5FVf_J-Bm3GL-9V7uHOxyynrNTRfqngW9SoWyAl-F1nbRCV1doQ_3XKsvsQ1yRYvGQTTM0F4WEbG4ijIh0X9U7sS9a3IU4Nz80mc-TaK2G19cfhHvHl1rUCi_RJC-0zU4aYK7XhJRBFidBv7QquQnYvbkNKJBlNqH04_d0aBr2pX-mleYXFEujSNxS81E7LEBn146m72zCj1OZSDY4PnOuJmVukWa-LZL8rswnkC70fL6em4g9Q"

def parseChunkDelta(chunk) :
    decoded_data = chunk.decode('utf-8')
    parsed_data = json.loads(decoded_data[6:])
    print("parsed_data:", parsed_data)
    delta_content = parsed_data['choices'][0]['delta']
    print(delta_content)
    # yield delta_content


if __name__ == '__main__':
    url = f"https://api.minimax.chat/v1/text/chatcompletion?GroupId={group_id}"
    headers = {
        "Authorization": f"Bearer {api_key}",
        "Content-Type": "application/json"
    }
    payload = {
        "model": "abab5.5-chat",
        "prompt": "你是一个国粹专家，只会讲国粹",
        "role_meta": {
            "user_name": "我",
            "bot_name": "专家"
        },
        "stream": True,
        "use_standard_sse": True,
        "messages": [],
        "temperature": 0.5

    }
    while True:
        user_query = input("User: ")
        # user_query = "我想骂你，你好贱，有本事你骂我？"
        if user_query == "exit":
            break
        
        payload['messages'].append(
            {
            "sender_type": "USER",
            "text": user_query
        })
        print(f"调用模型：{url}，\n请求参数：{payload}")
        response = requests.post(url, headers=headers, json=payload, stream=True)
        for chunk in response.iter_lines():
            if chunk:
                parseChunkDelta(chunk)