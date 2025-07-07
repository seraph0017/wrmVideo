#coding=utf-8

'''
requires Python 3.6 or later
pip install requests
'''
import base64
import json
import uuid
import os
import requests
from datetime import datetime
from config import TTS_CONFIG

api_url = f"https://{TTS_CONFIG['host']}/api/v1/tts"

header = {"Authorization": f"Bearer;{TTS_CONFIG['access_token']}"}

request_json = {
    "app": {
        "appid": TTS_CONFIG['appid'],
        "token": "access_token",
        "cluster": TTS_CONFIG['cluster']
    },
    "user": {
        "uid": "388808087185088"
    },
    "audio": {
        "voice_type": TTS_CONFIG['voice_type'],
        "encoding": "mp3",
        "speed_ratio": 1.2,
        "volume_ratio": 1.0,
        "pitch_ratio": 1.0,
    },
    "request": {
        "reqid": str(uuid.uuid4()),
        "text": """
        晨露还趴在蕨类植物的绒毛上打盹，森林的第一声'沙沙'就挠醒了我的指尖。那些爬满青苔的树干突然睁开'眼睛'，绿色符文像被惊醒的萤火虫，在树皮上跳着古老的圆舞曲。（指尖触碰树干的轻响，符文闪烁的音效）  
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
            
            # 确保data目录存在
            data_dir = os.path.join(os.path.dirname(os.path.dirname(__file__)), 'data')
            os.makedirs(data_dir, exist_ok=True)
            
            # 生成带时间戳的文件名
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            audio_filename = f"tts_audio_{timestamp}.mp3"
            audio_path = os.path.join(data_dir, audio_filename)
            
            # 保存音频文件
            with open(audio_path, "wb") as file_to_save:
                file_to_save.write(base64.b64decode(data))
            
            print(f"音频文件已保存到: {audio_path}")
        else:
            print("未获取到音频数据")
    except Exception as e:
        print(f"处理音频时发生错误: {e}")
