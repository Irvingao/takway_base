#使用远程或本地TTS
# LOCAL_ASR = 0
# REMOTE_ASR = 1

# #使用远程或本地VITS
# LOCAL_TTS = 0
# REMOTE_TTS = 1



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
        "user":"root",
        "password":"takway"
    },
    "llm":{
        "API_KEY" : "eyJhbGciOiJSUzI1NiIsInR5cCI6IkpXVCJ9.eyJHcm91cE5hbWUiOiIyMzQ1dm9yIiwiVXNlck5hbWUiOiIyMzQ1dm9yIiwiQWNjb3VudCI6IiIsIlN1YmplY3RJRCI6IjE3NTk0ODIxODAxMDAxNzAyMDgiLCJQaG9uZSI6IjE1MDcyNjQxNTYxIiwiR3JvdXBJRCI6IjE3NTk0ODIxODAwOTU5NzU5MDQiLCJQYWdlTmFtZSI6IiIsIk1haWwiOiIiLCJDcmVhdGVUaW1lIjoiMjAyNC0wNC0xMyAxOTowNDoxNyIsImlzcyI6Im1pbmltYXgifQ.RO_WJMz5T0XlL3F6xB9p015hL3PibCbsr5KqO3aMjBL5hKrf1uIjOICTDZWZoucyJV1suxvFPAd_2Ds2Rv01eCu6GFdai1hUByfp51mOOD0PtaZ5-JKRpRPpLSNpqrNoQteANZz0gdr2_GEGTgTzpbfGbXfRYKrQyeQSvq0zHwqumGPd9gJCre2RavPUmzKRrq9EAaQXtSNhBvVkf5lDlxr8fTAHgbj6MLAJZIvvf4uOZErNrbPylo1Vcy649KxEkc0HCWOZErOieeUQFRkKibnE5Q30CgywqxY2qMjrxGRZ_dtizan_0EZ62nXp-J6jarhcY9le1SqiMu1Cv61TuA",
        "url" : "https://api.minimax.chat/v1/text/chatcompletion_v2"
    },
    "tta":{
        "API_KEY": "eyJhbGciOiJSUzI1NiIsInR5cCI6IkpXVCJ9.eyJHcm91cE5hbWUiOiIyMzQ1dm9yIiwiVXNlck5hbWUiOiIyMzQ1dm9yIiwiQWNjb3VudCI6IiIsIlN1YmplY3RJRCI6IjE3NTk0ODIxODAxMDAxNzAyMDgiLCJQaG9uZSI6IjE1MDcyNjQxNTYxIiwiR3JvdXBJRCI6IjE3NTk0ODIxODAwOTU5NzU5MDQiLCJQYWdlTmFtZSI6IiIsIk1haWwiOiIiLCJDcmVhdGVUaW1lIjoiMjAyNC0wNC0xMyAxOTowNDoxNyIsImlzcyI6Im1pbmltYXgifQ.RO_WJMz5T0XlL3F6xB9p015hL3PibCbsr5KqO3aMjBL5hKrf1uIjOICTDZWZoucyJV1suxvFPAd_2Ds2Rv01eCu6GFdai1hUByfp51mOOD0PtaZ5-JKRpRPpLSNpqrNoQteANZz0gdr2_GEGTgTzpbfGbXfRYKrQyeQSvq0zHwqumGPd9gJCre2RavPUmzKRrq9EAaQXtSNhBvVkf5lDlxr8fTAHgbj6MLAJZIvvf4uOZErNrbPylo1Vcy649KxEkc0HCWOZErOieeUQFRkKibnE5Q30CgywqxY2qMjrxGRZ_dtizan_0EZ62nXp-J6jarhcY9le1SqiMu1Cv61TuA",
        "url" : "https://api.minimax.chat/v1/t2a_pro",
        "group_id":"1759482180095975904"
    },
    
    "main":{
        "port":8000,
        "asr": 0,
        "tts":0,
    }
}
