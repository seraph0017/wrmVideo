#!/usr/bin/env python3
# -*- coding: utf-8 -*-

import os
import sys
import base64
import json
import uuid
import requests
from datetime import datetime
from volcenginesdkarkruntime import Ark

# 添加src目录到Python路径
sys.path.append(os.path.join(os.path.dirname(__file__), 'src'))

from config import ARK_CONFIG, TTS_CONFIG
from concat import concat_video

def read_text_file(file_path):
    """
    读取文本文件内容
    
    Args:
        file_path: 文本文件路径
    
    Returns:
        str: 文件内容
    """
    try:
        with open(file_path, 'r', encoding='utf-8') as f:
            content = f.read().strip()
        return content
    except Exception as e:
        print(f"读取文件失败: {e}")
        return None

def generate_image(text, output_dir):
    """
    生成图片
    
    Args:
        text: 文本内容
        output_dir: 输出目录
    
    Returns:
        str: 生成的图片文件路径
    """
    try:
        # 初始化Ark客户端
        client = Ark(
            base_url=ARK_CONFIG['base_url'],
            api_key=ARK_CONFIG['api_key'],
        )
        
        prompt = f"""
以下面一段描述为描述，生成一张故事图片

{text}
"""
        
        print("正在生成图片...")
        imagesResponse = client.images.generate(
            model="doubao-seedream-3-0-t2i-250415",
            prompt=prompt,
            watermark=False,
            size="720x1280",
            response_format="b64_json"
        )
        
        # 处理base64格式的图片数据并保存
        if hasattr(imagesResponse.data[0], 'b64_json') and imagesResponse.data[0].b64_json:
            # 确保输出目录存在
            os.makedirs(output_dir, exist_ok=True)
            
            # 生成带时间戳的文件名
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            image_filename = f"generated_image_{timestamp}.jpg"
            image_path = os.path.join(output_dir, image_filename)
            
            # 解码base64数据并保存
            image_data = base64.b64decode(imagesResponse.data[0].b64_json)
            with open(image_path, 'wb') as f:
                f.write(image_data)
            
            print(f"图片生成成功: {image_path}")
            return image_path
        else:
            print("未获取到base64格式的图片数据")
            return None
            
    except Exception as e:
        print(f"图片生成失败: {e}")
        return None

def generate_voice(text, output_dir):
    """
    生成语音
    
    Args:
        text: 文本内容
        output_dir: 输出目录
    
    Returns:
        str: 生成的音频文件路径
    """
    try:
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
                "text": text,
                "text_type": "plain",
                "operation": "query",
                "with_frontend": 1,
                "frontend_type": "unitTson"
            }
        }
        
        print("正在生成语音...")
        resp = requests.post(api_url, json.dumps(request_json), headers=header)
        
        if "data" in resp.json():
            data = resp.json()["data"]
            
            # 确保输出目录存在
            os.makedirs(output_dir, exist_ok=True)
            
            # 生成带时间戳的文件名
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            audio_filename = f"tts_audio_{timestamp}.mp3"
            audio_path = os.path.join(output_dir, audio_filename)
            
            # 保存音频文件
            with open(audio_path, "wb") as file_to_save:
                file_to_save.write(base64.b64decode(data))
            
            print(f"语音生成成功: {audio_path}")
            return audio_path
        else:
            print("未获取到音频数据")
            return None
            
    except Exception as e:
        print(f"语音生成失败: {e}")
        return None

def main():
    """
    主函数
    """
    if len(sys.argv) != 2:
        print("使用方法: python generate.py data/test1/test1.txt")
        sys.exit(1)
    
    input_file = sys.argv[1]
    
    # 检查输入文件是否存在
    if not os.path.exists(input_file):
        print(f"错误: 文件 {input_file} 不存在")
        sys.exit(1)
    
    # 获取输出目录（输入文件所在的目录）
    output_dir = os.path.dirname(input_file)
    
    print(f"开始处理文件: {input_file}")
    print(f"输出目录: {output_dir}")
    
    # 读取文本内容
    text_content = read_text_file(input_file)
    if not text_content:
        print("读取文本内容失败")
        sys.exit(1)
    
    print(f"文本内容: {text_content[:100]}...")
    
    # 生成图片
    image_path = generate_image(text_content, output_dir)
    if not image_path:
        print("图片生成失败")
        sys.exit(1)
    
    # 生成语音
    audio_path = generate_voice(text_content, output_dir)
    if not audio_path:
        print("语音生成失败")
        sys.exit(1)
    
    # 合成视频
    print("正在合成视频...")
    video_path = concat_video(image_path, audio_path, output_dir)
    if not video_path:
        print("视频合成失败")
        sys.exit(1)
    
    print("\n=== 处理完成 ===")
    print(f"图片文件: {image_path}")
    print(f"音频文件: {audio_path}")
    print(f"视频文件: {video_path}")
    print(f"所有文件已保存到: {output_dir}")

if __name__ == '__main__':
    main()