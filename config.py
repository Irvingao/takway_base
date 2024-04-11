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
    "main":{
        "port":7878
    }
}