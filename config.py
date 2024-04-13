config={
    "xfapi":{ #讯飞API接口参数
        "APPID": "fb646f00",
        "APISecret":"Njc2M2E3Y2FjMDRjMDhjNjViNTYwOTE1",
        "APIKey":"f71ea3399c4d73fe3f6df093f7811a0d"
    },
    "satt":{
        "domain": "iat", #讯飞流式语音听写接口参数，详细定义见https://www.xfyun.cn/doc/asr/voicedictation/API.html
        "language": "zh_cn", 
        "accent": "mandarin",
        "vad_eos": 10000
    },
    "redis":{
        "host":'127.0.0.1',
        "port":6379,
        "db":0,
        "password":'takway'
    },
    "mysql":{
        "user":"admin02",
        "password":"LabA100102"
    },
    "llm":{
        "API_KEY" : "eyJhbGciOiJSUzI1NiIsInR5cCI6IkpXVCJ9.eyJHcm91cE5hbWUiOiJUYWt3YXkuQUkiLCJVc2VyTmFtZSI6IlRha3dheS5BSSIsIkFjY291bnQiOiIiLCJTdWJqZWN0SUQiOiIxNzY4NTM2ODA1NjIxMTIxMjA4IiwiUGhvbmUiOiIxMzA4MTg1ODcwNCIsIkdyb3VwSUQiOiIxNzY4NTM2ODA1NTc0OTgzODY0IiwiUGFnZU5hbWUiOiIiLCJNYWlsIjoiIiwiQ3JlYXRlVGltZSI6IjIwMjQtMDMtMjMgMjI6Mjc6NDUiLCJpc3MiOiJtaW5pbWF4In0.ZpSw5t_90KTt0EceDqkmDE88DyB1GufB4_fwvaMLs7f7ojesh0Q4nT0jdcfX5Y9_wve4nVifoRFhHW9h-biEn_yWxilzZbGGbwY5FVf_J-Bm3GL-9V7uHOxyynrNTRfqngW9SoWyAl-F1nbRCV1doQ_3XKsvsQ1yRYvGQTTM0F4WEbG4ijIh0X9U7sS9a3IU4Nz80mc-TaK2G19cfhHvHl1rUCi_RJC-0zU4aYK7XhJRBFidBv7QquQnYvbkNKJBlNqH04_d0aBr2pX-mleYXFEujSNxS81E7LEBn146m72zCj1OZSDY4PnOuJmVukWa-LZL8rswnkC70fL6em4g9Q",
        "url" : "https://api.minimax.chat/v1/text/chatcompletion_v2"
    },
    "main":{
        "port":7878
    }
}