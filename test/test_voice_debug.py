#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
语音生成API调试脚本
用于测试和调试语音生成API的响应
"""

import requests
import json
import sys
import os

# 添加项目根目录到Python路径
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from config.config import TTS_CONFIG

def test_voice_generation():
    """测试语音生成API"""
    
    # 测试文本 - 使用实际失败的文本
    test_text = "李承乾西市布疑阵！当牙人们簇拥着这位'败家太子'时，没人注意他悄悄将三个亲信派往不同方向。一个去联络"
    
    print(f"测试文本: {test_text}")
    print(f"文本长度: {len(test_text)}")
    
    # API配置
    url = f"https://{TTS_CONFIG['host']}/api/v1/tts"
    
    # 生成请求ID
    import uuid
    request_id = str(uuid.uuid4())
    
    # 使用正确的API格式
    payload = {
        "app": {
            "appid": TTS_CONFIG['appid'],
            "token": TTS_CONFIG['access_token'],
            "cluster": TTS_CONFIG['cluster']
        },
        "user": {
            "uid": "388808087185088"
        },
        "audio": {
            "voice_type": TTS_CONFIG.get('voice_type', 'BV115_streaming'),
            "encoding": "mp3",
            "speed_ratio": 1.0,
            "volume_ratio": 1.0,
            "pitch_ratio": 1.0
        },
        "request": {
            "reqid": request_id,
            "text": test_text,
            "text_type": "plain",
            "operation": "query",
            "with_frontend": 1,
            "frontend_type": "unitTson"
        }
    }
    
    headers = {
        'Content-Type': 'application/json',
        'Authorization': f"Bearer; {TTS_CONFIG['access_token']}"
    }
    
    print(f"\n=== API请求信息 ===")
    print(f"URL: {url}")
    print(f"Headers: {headers}")
    print(f"Payload: {json.dumps(payload, ensure_ascii=False, indent=2)}")
    
    try:
        print(f"\n=== 发送API请求 ===")
        response = requests.post(url, json=payload, headers=headers, timeout=30)
        
        print(f"响应状态码: {response.status_code}")
        print(f"响应头: {dict(response.headers)}")
        print(f"响应内容长度: {len(response.text)}")
        
        print(f"\n=== 完整API响应内容 ===")
        print(response.text)
        print(f"=== 响应内容结束 ===\n")
        
        if response.status_code == 200:
            try:
                print(f"\n=== 尝试解析主JSON ===")
                data = response.json()
                print(f"✓ 主JSON解析成功")
                print(f"响应键: {list(data.keys())}")
                
                if 'addition' in data and 'frontend' in data['addition']:
                    frontend_str = data['addition']['frontend']
                    print(f"\nfrontend字段类型: {type(frontend_str)}")
                    print(f"frontend字段长度: {len(frontend_str)}")
                    print(f"frontend内容（前500字符）: {frontend_str[:500]}")
                    
                    print(f"\n=== 尝试解析frontend JSON ===")
                    try:
                        frontend_data = json.loads(frontend_str)
                        print(f"✓ frontend JSON解析成功")
                        print(f"frontend数据键: {list(frontend_data.keys()) if isinstance(frontend_data, dict) else 'Not a dict'}")
                    except json.JSONDecodeError as e:
                        print(f"✗ frontend JSON解析失败: {e}")
                        print(f"错误位置: line {e.lineno}, column {e.colno}, char {e.pos}")
                        
                        # 显示错误位置附近的内容
                        if e.pos < len(frontend_str):
                            start = max(0, e.pos - 100)
                            end = min(len(frontend_str), e.pos + 100)
                            print(f"错误位置附近: ...{frontend_str[start:end]}...")
                            
                        # 显示第19行的内容（错误经常在第19行）
                        lines = frontend_str.split('\n')
                        if len(lines) >= 19:
                            print(f"第19行内容: {lines[18]}")
                            
                else:
                    print(f"响应中没有找到 data.frontend 字段")
                    
            except json.JSONDecodeError as e:
                print(f"✗ 主JSON解析失败: {e}")
                print(f"错误位置: line {e.lineno}, column {e.colno}, char {e.pos}")
                
        else:
            print(f"API请求失败，状态码: {response.status_code}")
            
    except Exception as e:
        print(f"请求异常: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    test_voice_generation()