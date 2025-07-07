#coding=utf-8

'''
requires Python 3.6 or later
pip install requests
'''
import base64
import json
import uuid
import requests

# 填写平台申请的appid, access_token以及cluster
appid = "2535746880"
access_token= "dexjYgOYpYRiNAc-QJaDRplD9G5SGZPe"
cluster = "volcano_tts"

voice_type = "BV701_streaming"
host = "openspeech.bytedance.com"
api_url = f"https://{host}/api/v1/tts"

header = {"Authorization": f"Bearer;{access_token}"}

request_json = {
    "app": {
        "appid": appid,
        "token": "access_token",
        "cluster": cluster
    },
    "user": {
        "uid": "388808087185088"
    },
    "audio": {
        "voice_type": voice_type,
        "encoding": "mp3",
        "speed_ratio": 1.0,
        "volume_ratio": 1.0,
        "pitch_ratio": 1.0,
    },
    "request": {
        "reqid": str(uuid.uuid4()),
        "text": """
        晨露还趴在蕨类植物的绒毛上打盹，森林的第一声‘沙沙’就挠醒了我的指尖。那些爬满青苔的树干突然睁开‘眼睛’，绿色符文像被惊醒的萤火虫，在树皮上跳着古老的圆舞曲。（指尖触碰树干的轻响，符文闪烁的音效）  
传说中会吞噬旅人的低语森林，此刻正用潮湿的呼吸，轻轻舔舐着闯入者的衣角。我忽然明白，真正的危险从不是未知，而是你以为自己早已看透了未知。
        """,
        "text_type": "plain",
        "operation": "query",
        "with_frontend": 1,
        "frontend_type": "unitTson"

    }
}

if __name__ == '__main__':
    try:
        resp = requests.post(api_url, json.dumps(request_json), headers=header)
        print(f"resp body: \n{resp.json()}")
        if "data" in resp.json():
            data = resp.json()["data"]
            file_to_save = open("test2_submit.mp3", "wb")
            file_to_save.write(base64.b64decode(data))
    except Exception as e:
        e.with_traceback()
