#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
语音生成模块（兼容性保持）
使用新的配置化系统
"""

import base64
import json
import uuid
import os
import sys
import requests
from datetime import datetime

# 添加项目根目录到路径
project_root = os.path.dirname(os.path.dirname(__file__))
sys.path.insert(0, project_root)

from config.prompt_config import prompt_config, VOICE_PRESETS

# TTS配置
TTS_CONFIG = {
    "appid": "6359073393",
    "cluster": "volcano_tts",
    "voice_type": "BV700_streaming",
    "host": "openspeech.bytedance.com",
    "access_token": "your_access_token_here"
}

api_url = f"https://{TTS_CONFIG['host']}/api/v1/tts"

header = {"Authorization": f"Bearer;{TTS_CONFIG['access_token']}"}

def generate_voice(text, output_path, preset='default'):
    """
    生成语音文件
    
    Args:
        text: 要转换的文本
        output_path: 输出文件路径
        preset: 语音预设
    
    Returns:
        bool: 是否生成成功
    """
    
    try:
        # 生成唯一的请求ID
        request_id = str(uuid.uuid4())
        
        # 使用配置管理器生成请求配置
        request_json = prompt_config.get_voice_config(
            text=text,
            request_id=request_id,
            tts_config=TTS_CONFIG,
            **VOICE_PRESETS.get(preset, VOICE_PRESETS['default'])
        )
        
        # 发送请求
        resp = requests.post(api_url, json.dumps(request_json), headers=header)
        
        if "data" in resp.json():
            data = resp.json()["data"]
            
            # 确保输出目录存在
            os.makedirs(os.path.dirname(output_path), exist_ok=True)
            
            # 保存音频文件
            with open(output_path, "wb") as file_to_save:
                file_to_save.write(base64.b64decode(data))
            
            print(f"音频文件已保存到: {output_path}")
            return True
        else:
            print("未获取到音频数据")
            return False
            
    except Exception as e:
        print(f"生成语音时发生错误: {e}")
        return False

# 保持向后兼容的默认文本
default_text = """
晨露还趴在蕨类植物的绒毛上打盹，森林的第一声'沙沙'就挠醒了我的指尖。那些爬满青苔的树干突然睁开'眼睛'，绿色符文像被惊醒的萤火虫，在树皮上跳着古老的圆舞曲。（指尖触碰树干的轻响，符文闪烁的音效）  
传说中会吞噬旅人的低语森林，此刻正用潮湿的呼吸，轻轻舔舐着闯入者的衣角。我忽然明白，真正的危险从不是未知，而是你以为自己早已看透了未知。
"""

if __name__ == '__main__':
    # 确保data目录存在
    data_dir = os.path.join(os.path.dirname(os.path.dirname(__file__)), 'data')
    os.makedirs(data_dir, exist_ok=True)
    
    # 生成带时间戳的文件名
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    audio_filename = f"tts_audio_{timestamp}.mp3"
    audio_path = os.path.join(data_dir, audio_filename)
    
    # 使用新的generate_voice函数
    success = generate_voice(default_text, audio_path)
    
    if not success:
        print("语音生成失败")
