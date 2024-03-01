import os
import json
import time
import datetime
import requests

from .common_utils import encode_bytes2str, decode_str2bytes

'''
{
    "RESPONSE_INFO": {
        "status": "success/error",   # string
        "message": "xxxxx",  # string
    },
    "DATA": {
        "Audio": {
            "data": "xxxxx",    # base64 encoded data
            "metadata": {
                "rate": ;   # int
                "channels": ;   # int
                "format": ;  # int
            }
        },
        "Text": {
            "data": "xxxxx",    # base64 encoded data
            "metadata": {
                "is_end": True/False,  # bool
            }
        },
        "Image": {
            "data": "xxxxx",    # base64 encoded data
            "metadata": {
                "width": ;  # int
                "height": ; # int
                "format": ; # string
            }
        }
    }
}
'''

class Client:
    def __init__(self, server_url):
        self.server_url = server_url

    def gen_request_data(self, **kwargs):
        # print("kwargs:", kwargs)
        audio_data = kwargs.get("audio_data", None)
        text_data = kwargs.get("text_data", dict())
        return json.dumps(
            {
            "is_end": audio_data.get("is_end"),  # bool
            "is_bgn": audio_data.get("is_bgn"),  # bool
            "DATA": {
                "Audio": {
                    "data": encode_bytes2str(audio_data['frames']),    # base64 encoded data
                    "metadata": {
                        "frames_size": audio_data.get("frames_size"),  # string
                        "chunk_size": audio_data.get("chunk_size"),  # int
                        "is_end": audio_data.get("is_end"),  # bool
                        }
                    },
                "Text": {
                    "data": text_data.get("text"),    # base64 encoded data
                    "metadata": {
                        "chat_status": text_data.get("chat_status"),  # string
                        "chat_history": text_data.get("chat_history"),  # list of dict
                        }
                    },
                },
            "META_INFO": {
                # "model_version": kwargs.get("model_version", ""),    # string
                # "model_url": kwargs.get("model_url", ""),    # string
                "character": {
                    "name": kwargs.get("character", "Klee"),  # string
                    "speaker_id": kwargs.get("speaker_id", 113),  # int
                    "wakeup_words": kwargs.get("wakeup_words", "可莉来啦"),  # list of string
                    }
                }
            }
        ) + '\n'
    
    def send_data_to_server(self, **kwargs):
        return requests.post(self.server_url, 
            data=self.gen_request_data(**kwargs), stream=True)


from takway.roleplay_utils import *

class CharacterClient(Client, SparkRolyPlayingFunction):
    def __init__(self, 
                 server_url, 
                 character_data_dir="characters"):
        Client.__init__(self, server_url)
        SparkRolyPlayingFunction.__init__(self, character_data_dir)
        
        self.character_data_dir = character_data_dir
        self.character = None
        
    def gen_request_data(self, **kwargs):
        audio_data = kwargs.get("audio_data")
        chat_data = kwargs.get("chat_data", dict())
        character_data = kwargs.get("character_data")
        print(f"chat_data: {chat_data}")
        
        is_bgn = audio_data.get("is_bgn")
        is_end = audio_data.get("is_end")
        return json.dumps(
            {
            "is_bgn": is_bgn,  # bool
            "is_end": is_end,  # bool
            "audio_input": {
                "data": encode_bytes2str(audio_data['frames']),    # base64 encoded data
                "metadata": {
                    "frames_size": audio_data.get("frames_size"),  # string
                    "chunk_size": audio_data.get("chunk_size"),  # int
                    "is_end": is_end,  # bool
                    }
                },
            "chat_input": {
                "chat_history": chat_data.get("chat_history") if is_bgn else [],  # list of dict
                "chat_status": chat_data.get("chat_status"),  # string
                "with_question_text": chat_data.get("with_question_text", False),  # bool
                },
            "character_info": {
                "character_name": character_data.character_name,  # string
                "speaker_id": character_data.character_id,  # int
                "wakeup_words": character_data.wakeup_words,  # list of string
                }
            }
        ) + '\n'