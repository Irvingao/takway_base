import datetime
import hashlib
import base64
import hmac
from urllib.parse import urlencode
from wsgiref.handlers import format_date_time
from datetime import datetime
from time import mktime
from config import config


def generate_xf_satt_url():
    #设置讯飞流式听写API相关参数
    APIKey = config['xfapi']['APIKey']
    APISecret = config['xfapi']['APISecret']

    #鉴权并创建websocket_url
    url = 'wss://ws-api.xfyun.cn/v2/iat'
    now = datetime.now()
    date = format_date_time(mktime(now.timetuple()))
    signature_origin = "host: " + "ws-api.xfyun.cn" + "\n"
    signature_origin += "date: " + date + "\n"
    signature_origin += "GET " + "/v2/iat " + "HTTP/1.1"
    signature_sha = hmac.new(APISecret.encode('utf-8'), signature_origin.encode('utf-8'),
                                digestmod=hashlib.sha256).digest()
    signature_sha = base64.b64encode(signature_sha).decode(encoding='utf-8')
    authorization_origin = "api_key=\"%s\", algorithm=\"%s\", headers=\"%s\", signature=\"%s\"" % (
        APIKey, "hmac-sha256", "host date request-line", signature_sha)
    authorization = base64.b64encode(authorization_origin.encode('utf-8')).decode(encoding='utf-8')
    v = {
        "authorization": authorization,
        "date": date,
        "host": "ws-api.xfyun.cn"
    }
    url = url + '?' + urlencode(v)
    return url



