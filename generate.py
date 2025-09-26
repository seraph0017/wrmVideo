#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
统一的视频生成系统
支持脚本生成、图片生成、语音生成和视频拼接
"""

import os
import sys
import re
import argparse
from datetime import datetime
import json
import base64
import uuid
import requests
import subprocess
import ffmpeg
from volcenginesdkarkruntime import Ark
import xml.etree.ElementTree as ET

# 添加src目录到路径
src_dir = os.path.join(os.path.dirname(__file__), 'src')
sys.path.insert(0, src_dir)

from config.config import TTS_CONFIG, ARK_CONFIG, IMAGE_TWO_CONFIG
from src.script.gen_script import ScriptGenerator
from src.voice.gen_voice import VoiceGenerator
from src.image.gen_image import generate_image_with_volcengine
import time
import urllib.request


def read_novel_file_with_encoding(file_path):
    """
    读取小说文件，支持多种编码格式
    
    Args:
        file_path: 文件路径
    
    Returns:
        str: 文件内容
    """
    # 尝试多种编码格式
    encodings = ['utf-8', 'gbk', 'gb2312', 'gb18030', 'big5', 'latin1']
    
    for encoding in encodings:
        try:
            with open(file_path, 'r', encoding=encoding) as f:
                content = f.read()
                print(f"成功使用 {encoding} 编码读取文件")
                return content
        except UnicodeDecodeError:
            continue
        except Exception as e:
            print(f"使用 {encoding} 编码读取文件时出错：{e}")
            continue
    
    print(f"无法读取文件 {file_path}，尝试了所有编码格式都失败")
    return ""


def clean_text_for_tts(text):
    """
    清理文本用于TTS生成，移除括号内的内容和&符号
    
    Args:
        text: 原始文本
    
    Returns:
        str: 清理后的文本
    """
    # 移除各种括号及其内容
    text = re.sub(r'\([^)]*\)', '', text)  # 移除圆括号内容
    text = re.sub(r'\[[^\]]*\]', '', text)  # 移除方括号内容
    text = re.sub(r'\{[^}]*\}', '', text)  # 移除花括号内容
    text = re.sub(r'（[^）]*）', '', text)  # 移除中文圆括号内容
    text = re.sub(r'【[^】]*】', '', text)  # 移除中文方括号内容
    
    # 移除&符号
    text = text.replace('&', '')
    
    # 清理多余的空格和换行
    text = re.sub(r'\s+', ' ', text).strip()

def create_video_from_images(first_image_path, second_image_path, duration, output_path):
    """
    使用两张图片生成视频
    
    Args:
        first_image_path: 第一张图片路径
        second_image_path: 第二张图片路径
        duration: 视频时长
        output_path: 输出视频路径
    
    Returns:
        bool: 是否成功生成视频
    """
    try:
        print(f"开始生成视频: {first_image_path} -> {second_image_path}")
        
        # 上传图片到临时服务器或使用本地路径
        # 这里需要实现图片上传逻辑，暂时使用占位符URL
        first_image_url = upload_image_to_server(first_image_path)
        second_image_url = upload_image_to_server(second_image_path)
        
        if not first_image_url or not second_image_url:
            print("图片上传失败")
            return False
        
        # 创建视频生成任务
        client = Ark(api_key=ARK_CONFIG["api_key"])
        
        resp = client.content_generation.tasks.create(
            model="doubao-seedance-1-0-lite-i2v-250428",
            content=[
                {
                    "type": "text",
                    "text": f"慢慢过渡转场 --dur {duration}"
                },
                {
                    "type": "image_url",
                    "image_url": {
                        "url": first_image_url
                    },
                    "role": "first_frame"
                },
                {
                    "type": "image_url",
                    "image_url": {
                        "url": second_image_url
                    },
                    "role": "last_frame"
                }
            ]
        )
        
        task_id = resp.id
        print(f"视频生成任务创建成功，任务ID: {task_id}")
        
        # 等待任务完成
        max_wait_time = 300  # 最大等待5分钟
        wait_interval = 10   # 每10秒检查一次
        waited_time = 0
        
        while waited_time < max_wait_time:
            time.sleep(wait_interval)
            waited_time += wait_interval
            
            # 查询任务状态
            status_resp = client.content_generation.tasks.get(task_id=task_id)
            
            if status_resp.status == "succeeded":
                video_url = status_resp.content.video_url
                print(f"视频生成成功，下载URL: {video_url}")
                
                # 下载视频
                if download_video(video_url, output_path):
                    print(f"视频下载成功: {output_path}")
                    return True
                else:
                    print("视频下载失败")
                    return False
            elif status_resp.status == "failed":
                print(f"视频生成失败: {status_resp}")
                return False
            else:
                print(f"视频生成中... 状态: {status_resp.status}")
        
        print("视频生成超时")
        return False
        
    except Exception as e:
        print(f"生成视频时发生错误: {e}")
        return False

def upload_image_to_server(image_path):
    """
    上传图片到服务器（占位符实现）
    
    Args:
        image_path: 图片路径
    
    Returns:
        str: 图片URL，失败返回None
    """
    # 这里需要实现实际的图片上传逻辑
    # 暂时返回占位符URL
    print(f"上传图片: {image_path}")
    # 实际实现中需要将图片上传到可访问的服务器
    return "https://example.com/placeholder.jpg"

def download_video(video_url, output_path):
    """
    下载视频文件
    
    Args:
        video_url: 视频URL
        output_path: 输出路径
    
    Returns:
        bool: 是否下载成功
    """
    try:
        print(f"开始下载视频: {video_url}")
        urllib.request.urlretrieve(video_url, output_path)
        print(f"视频下载完成: {output_path}")
        return True
    except Exception as e:
        print(f"下载视频时发生错误: {e}")
        return False

def get_audio_duration(audio_path):
    """
    获取音频文件时长
    
    Args:
        audio_path: 音频文件路径
    
    Returns:
        float: 音频时长（秒），失败返回0
    """
    try:
        probe = ffmpeg.probe(audio_path)
        duration = float(probe['streams'][0]['duration'])
        return duration
    except Exception as e:
        print(f"获取音频时长失败: {e}")
        return 0
    
    return text

def generate_audio(text, output_path):
    """
    生成音频文件
    
    Args:
        text: 要转换的文本
        output_path: 输出文件路径
    
    Returns:
        bool: 是否成功生成
    """
    try:
        # 清理文本
        clean_text = clean_text_for_tts(text)
        
        if not clean_text.strip():
            print("警告: 清理后的文本为空，跳过音频生成")
            return False
        
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
                "speed_ratio": 1.0,
                "volume_ratio": 1.0,
                "pitch_ratio": 1.0,
                "sample_rate": 44100,  # 提升采样率到44.1kHz
                "bitrate": 192000,     # 提升比特率到192kbps
            },
            "request": {
                "reqid": str(uuid.uuid4()),
                "text": clean_text,
                "text_type": "plain",
                "operation": "query",
                "with_frontend": 1,
                "frontend_type": "unitTson"
            }
        }
        
        print(f"正在生成音频: {os.path.basename(output_path)}")
        resp = requests.post(api_url, json.dumps(request_json), headers=header)
        
        if "data" in resp.json():
            data = resp.json()["data"]
            
            # 确保输出目录存在
            os.makedirs(os.path.dirname(output_path), exist_ok=True)
            
            # 保存音频文件
            with open(output_path, "wb") as file_to_save:
                file_to_save.write(base64.b64decode(data))
            
            print(f"音频文件已保存: {output_path}")
            return True
        else:
            print(f"音频生成失败: {resp.json()}")
            return False
            
    except Exception as e:
        print(f"生成音频时发生错误: {e}")
        return False

    """
    生成图片文件
    
    Args:
        prompt: 图片描述
        output_path: 输出文件路径
        style: 艺术风格，如果为None则使用配置文件中的默认风格
        chapter_path: 章节路径，用于获取人物描述信息
    
    Returns:
        bool: 是否成功生成
    """
    try:
        from volcengine.visual.VisualService import VisualService
        
        visual_service = VisualService()
        
        # 设置访问密钥
        visual_service.set_ak(IMAGE_TWO_CONFIG['access_key'])
        visual_service.set_sk(IMAGE_TWO_CONFIG['secret_key'])
        
        # 获取风格设置
        if style is None:
            style = IMAGE_TWO_CONFIG.get('default_style', 'manga')
        
        style_prompt = ART_STYLES.get(style, ART_STYLES['manga'])
        
        print(f"正在生成{style}风格图片: {os.path.basename(output_path)}")
        
        # 如果提供了章节路径，则增强人物描述
        enhanced_prompt = prompt
        if chapter_path:
            enhanced_prompt = enhance_prompt_with_character_details(prompt, chapter_path)
        
        # 构建完整的prompt
        full_prompt = "无任何形式的文字, 字母, 数字, 符号, 水印, 签名  （包括标识、符号、背景纹理里的隐藏字）\n\n" + style_prompt + "\n\n以下面描述为内容，生成一张故事图片\n" + enhanced_prompt + "\n\n"
        
        print("这里是完整的prompt===>>>{}".format(full_prompt))
        # 请求参数 - 使用配置文件中的值
        form = {
            "req_key": IMAGE_TWO_CONFIG['req_key'],
            "prompt": full_prompt,
            "llm_seed": -1,
            "seed": -1,
            "scale": IMAGE_TWO_CONFIG['scale'],
            "ddim_steps": IMAGE_TWO_CONFIG['ddim_steps'],
            "width": IMAGE_TWO_CONFIG['default_width'],
            "height": IMAGE_TWO_CONFIG['default_height'],
            "use_pre_llm": IMAGE_TWO_CONFIG['use_pre_llm'],
            "use_sr": IMAGE_TWO_CONFIG['use_sr'],
            "return_url": IMAGE_TWO_CONFIG['return_url'],  # 返回base64格式
            "logo_info": {
                "add_logo": False,
                "position": 0,
                "language": 0,
                "opacity": 0.3,
                "logo_text_content": "这里是明水印内容"
            }
        }
        
        resp = visual_service.cv_process(form)
        
        # 检查响应
        if 'data' in resp and 'binary_data_base64' in resp['data']:
            # 获取base64图片数据
            base64_data = resp['data']['binary_data_base64'][0]  # 取第一张图片
            
            # 确保输出目录存在
            os.makedirs(os.path.dirname(output_path), exist_ok=True)
            
            # 解码并保存图片
            image_data = base64.b64decode(base64_data)
            with open(output_path, 'wb') as f:
                f.write(image_data)
            
            print(f"图片已保存: {output_path}")
            return True
        else:
            print(f"图片生成失败: {resp}")
            return False
            
    except Exception as e:
        print(f"生成图片时发生错误: {e}")
        return False

    """
    批量生成图片文件（优化的批量处理，减少API调用次数）
    
    Args:
        prompts_and_paths: 包含(prompt, output_path)元组的列表
        style: 艺术风格，如果为None则使用配置文件中的默认风格
        chapter_path: 章节路径，用于获取人物描述信息
    
    Returns:
        list: 成功生成的图片路径列表
    """
    try:
        if not prompts_and_paths:
            print("没有图片需要生成")
            return []
        
        print(f"正在批量生成{len(prompts_and_paths)}张图片...")
        print("注意：由于API限制，将逐个生成图片，但会优化处理流程")
        
        # 获取风格设置
        if style is None:
            style = IMAGE_TWO_CONFIG.get('default_style', 'manga')
        
        successful_paths = []
        
        # 初始化火山引擎客户端（只初始化一次）
        from volcengine.visual.VisualService import VisualService
        client = VisualService()
        client.set_ak(IMAGE_TWO_CONFIG['access_key'])
        client.set_sk(IMAGE_TWO_CONFIG['secret_key'])
        
        style_prompt = ART_STYLES.get(style, ART_STYLES['manga'])
        
        # 逐个生成图片，但使用统一的客户端和风格设置
        for i, (prompt, output_path) in enumerate(prompts_and_paths, 1):
            try:
                print(f"正在生成第{i}/{len(prompts_and_paths)}张图片: {os.path.basename(output_path)}")
                
                # 如果提供了章节路径，则增强人物描述
                enhanced_prompt = prompt
                if chapter_path:
                    enhanced_prompt = enhance_prompt_with_character_details(prompt, chapter_path)
                
                # 构建完整的prompt
                full_prompt = style_prompt + "\n\n以下面描述为内容，生成一张故事图片：\n" + enhanced_prompt
                
                # 请求参数
                form = {
                    "req_key": IMAGE_TWO_CONFIG['req_key'],
                    "prompt": full_prompt,
                    "llm_seed": -1,
                    "seed": -1,
                    "scale": IMAGE_TWO_CONFIG['scale'],
                    "ddim_steps": IMAGE_TWO_CONFIG['ddim_steps'],
                    "width": IMAGE_TWO_CONFIG['default_width'],
                    "height": IMAGE_TWO_CONFIG['default_height'],
                    "use_pre_llm": IMAGE_TWO_CONFIG['use_pre_llm'],
                    "use_sr": IMAGE_TWO_CONFIG['use_sr'],
                    "return_url": IMAGE_TWO_CONFIG['return_url'],
                    "logo_info": {
                        "add_logo": False,
                        "position": 0,
                        "language": 0,
                        "opacity": 0.3,
                        "logo_text_content": "这里是明水印内容"
                    }
                }
                
                resp = client.cv_process(form)
                
                # 处理图片数据并保存
                if 'data' in resp and 'binary_data_base64' in resp['data']:
                    # 获取base64图片数据
                    base64_data = resp['data']['binary_data_base64'][0]
                    
                    # 确保输出目录存在
                    os.makedirs(os.path.dirname(output_path), exist_ok=True)
                    
                    # 解码并保存图片
                    image_data = base64.b64decode(base64_data)
                    with open(output_path, 'wb') as f:
                        f.write(image_data)
                    
                    print(f"✓ 第{i}张图片已保存: {output_path}")
                    successful_paths.append(output_path)
                else:
                    print(f"✗ 第{i}张图片生成失败: {resp}")
                    
            except Exception as e:
                print(f"✗ 第{i}张图片生成失败: {e}")
                continue
        
        print(f"\n批量生成完成，成功生成{len(successful_paths)}/{len(prompts_and_paths)}张图片")
        
        if len(successful_paths) == len(prompts_and_paths):
            print("✓ 所有图片生成成功")
        elif len(successful_paths) > 0:
            print(f"⚠ 部分图片生成成功 ({len(successful_paths)}/{len(prompts_and_paths)})")
        else:
            print("✗ 所有图片生成失败")
        
        return successful_paths
        
    except Exception as e:
        print(f"批量生成图片时发生错误: {e}")
        return []

def wrap_text(text, max_chars_per_line=20):
    """
    处理字幕文本，确保只显示一行字幕且不超出边框
    
    Args:
        text: 原始文本
        max_chars_per_line: 每行最大字符数（默认20，确保不超出边框）
    
    Returns:
        str: 处理后的单行文本
    """
    # 去掉首尾的标点符号
    punctuation = '。！？，；：、""''（）()[]{}【】《》<>'
    text = text.strip(punctuation + ' \t\n')
    
    # 移除引号内的内容，避免字幕过长
    text = re.sub(r'"[^"]*"', '', text)  # 移除双引号内容
    text = re.sub(r'"[^"]*"', '', text)  # 移除中文双引号内容
    text = re.sub(r"'[^']*'", '', text)  # 移除中文单引号内容
    
    # 清理多余的空格
    text = re.sub(r'\s+', ' ', text).strip()
    
    # 如果文本过长，截取前面部分并添加省略号
    if len(text) > max_chars_per_line:
        text = text[:max_chars_per_line-3] + "..."
    
    # 确保返回单行文本，移除所有换行符
    text = text.replace('\n', ' ').replace('\r', ' ')
    
    return text

def add_image_effects(video_stream, duration=None):
    """
    为图片添加动态特效（简化版本）
    
    Args:
        video_stream: ffmpeg视频流
        duration: 视频时长（秒），如果为None则使用默认特效
    
    Returns:
        ffmpeg视频流: 添加特效后的视频流
    """
    try:
        # 视频尺寸
        video_width = 720
        video_height = 1280
        
        # 暂时禁用复杂特效，只使用基本缩放以确保稳定性
        # print("应用图片特效: 基本缩放")  # 已禁用特效
        
        # 简单的缩放到目标尺寸
        video_with_effects = video_stream.filter(
            'scale', 
            f'{video_width}:{video_height}'
        )
        
        return video_with_effects
        
    except Exception as e:
        print(f"添加图片特效时出错: {e}，使用原始视频流")
        # 如果特效失败，返回原始视频流
        return video_stream.filter('scale', f'720:1280')

def create_video_with_subtitle(image_path, audio_path, subtitle_text, output_path):
    """
    将图片、音频和字幕合成为视频
    
    Args:
        image_path: 图片文件路径
        audio_path: 音频文件路径
        subtitle_text: 字幕文本
        output_path: 输出视频路径
    
    Returns:
        bool: 是否成功生成
    """
    try:
        # 确保输出目录存在
        output_dir = os.path.dirname(output_path)
        if output_dir:  # 只有当目录路径不为空时才创建
            os.makedirs(output_dir, exist_ok=True)
        
        print(f"正在合成视频: {os.path.basename(output_path)}")
        
        # 清理字幕文本（移除括号内容）
        clean_subtitle = clean_text_for_tts(subtitle_text)
        
        # 创建输入流
        image_input = ffmpeg.input(image_path, loop=1)
        audio_input = ffmpeg.input(audio_path)
        
        # 不使用图片特效，直接使用原始视频流
        video_with_effects = image_input.video
        
        # 如果有字幕文本，添加字幕
        if clean_subtitle.strip():
            # 视频尺寸 720x1280，字幕区域设置
            video_width = 720
            video_height = 1280
            
            # 字幕处理，确保单行显示，最多20个字符（避免超出边框）
            wrapped_subtitle = wrap_text(clean_subtitle, max_chars_per_line=20)
            
            # 字幕位置：使用FFmpeg表达式确保显示在底部
            subtitle_y = "h-text_h-h/3"  # 距离底部1/3视频高度像素
            
            print(f"调试信息 - 视频尺寸: {video_width}x{video_height}")
            print(f"调试信息 - 字幕文本: '{wrapped_subtitle}'")
            print(f"调试信息 - 字幕Y位置表达式: {subtitle_y}")
            
            # 添加字幕滤镜（黑体字，透明背景，每行居中，确保不超出边框）
            video_with_subtitle = video_with_effects.filter(
                'drawtext',
                text=wrapped_subtitle,
                fontfile='/System/Library/Fonts/Helvetica-Bold.ttc',  # 使用黑体字体
                fontsize=48,  # 减小字号到48，确保不超出边界
                fontcolor='yellow',
                x='max(30, min(w-text_w-30, (w-text_w)/2))',  # 水平居中，但确保左右至少30像素边距
                y=subtitle_y,      # 使用表达式确保在底部
                # 添加白色描边增强可读性和清晰度
                borderw=2,  # 减小描边宽度
                bordercolor='white',
                # 移除背景框，使字幕透明
                # box=0 表示不显示背景框
                box=0
            )
        else:
            video_with_subtitle = video_with_effects
        
        # 合成视频
        output = ffmpeg.output(
            video_with_subtitle, audio_input,
            output_path,
            vcodec='libx264',
            acodec='aac',
            video_bitrate='2000k', # 设置视频码率
            audio_bitrate='128k',  # 设置音频比特率
            ar=44100,              # 设置音频采样率
            pix_fmt='yuv420p',
            shortest=None
        )
        
        # 运行ffmpeg命令
        ffmpeg.run(output, overwrite_output=True, quiet=True)
        
        # 检查输出文件是否存在
        if os.path.exists(output_path):
            print(f"视频合成成功: {output_path}")
            return True
        else:
            print("视频合成失败: 输出文件未生成")
            return False
            
    except Exception as e:
        print(f"视频合成过程中发生错误: {e}")
        return False

def create_video(image_path, audio_path, output_path):
    """
    将图片和音频合成为视频（兼容旧接口）
    
    Args:
        image_path: 图片文件路径
        audio_path: 音频文件路径
        output_path: 输出视频路径
    
    Returns:
        bool: 是否成功生成
    """
    return create_video_with_subtitle(image_path, audio_path, "", output_path)

def smart_split_text(text, max_length=50):
    """
    按语气词智能断句
    
    Args:
        text: 要分割的文本
        max_length: 每段最大长度
    
    Returns:
        list: 分割后的文本段落列表
    """
    # 语气词和标点符号
    pause_markers = ['。', '！', '？', '，', '；', '：', '、', '呢', '吧', '啊', '呀', '哦', '嗯', '哈']
    
    if len(text) <= max_length:
        return [text]
    
    segments = []
    current_segment = ""
    
    i = 0
    while i < len(text):
        char = text[i]
        current_segment += char
        
        # 检查是否到达语气词或标点
        is_pause_point = False
        if char in pause_markers:
            is_pause_point = True
        elif i < len(text) - 1:
            # 检查双字符语气词
            two_char = text[i:i+2]
            if two_char in ['呢。', '吧。', '啊。', '呀。', '哦。']:
                current_segment += text[i+1]
                i += 1
                is_pause_point = True
        
        # 如果达到合适的断句点且长度适中，或者超过最大长度
        if (is_pause_point and len(current_segment) >= 15) or len(current_segment) >= max_length:
            # 检查分割后的文本是否有效（不只是标点符号）
            cleaned_segment = current_segment.strip()
            if is_valid_text_segment(cleaned_segment):
                segments.append(cleaned_segment)
            current_segment = ""
        
        i += 1
    
    # 添加剩余文本
    if current_segment.strip():
        cleaned_segment = current_segment.strip()
        if is_valid_text_segment(cleaned_segment):
            segments.append(cleaned_segment)
    
    return segments

def is_valid_text_segment(text):
    """
    检查文本片段是否有效（不只是标点符号或空白）
    
    Args:
        text: 要检查的文本
    
    Returns:
        bool: 是否为有效文本
    """
    if not text or not text.strip():
        return False
    
    # 移除所有标点符号和空白字符
    punctuation = '。！？，；：、""（）()[]{}【】《》<>…'
    text_without_punctuation = ''.join(char for char in text if char not in punctuation and not char.isspace())
    
    # 如果移除标点后还有内容，则认为是有效文本
    return len(text_without_punctuation) > 0

def parse_chapter_script(script_path):
    """
    解析章节脚本文件，支持多个解说内容共用一张图片
    
    Args:
        script_path: 脚本文件路径
    
    Returns:
        list: 包含(解说内容列表, 图片prompt)的元组列表
    """
    try:
        with open(script_path, 'r', encoding='utf-8') as f:
            content = f.read()
        
        # 解析XML内容
        segments = []
        
        # 使用正则表达式提取解说内容和图片prompt
        narration_pattern = r'<解说内容>(.*?)</解说内容>'
        prompt_pattern = r'<图片prompt>(.*?)</图片prompt>'
        
        narrations = re.findall(narration_pattern, content, re.DOTALL)
        prompts = re.findall(prompt_pattern, content, re.DOTALL)
        
        # 重新组织：多个解说内容可以共用一张图片
        current_narrations = []
        
        for i in range(len(narrations)):
            narration = narrations[i].strip()
            if narration:
                current_narrations.append(narration)
            
            # 如果有对应的图片prompt，或者是最后一个解说
            if i < len(prompts) or i == len(narrations) - 1:
                if current_narrations:
                    # 获取对应的图片prompt
                    prompt_index = min(i, len(prompts) - 1) if prompts else 0
                    prompt = prompts[prompt_index].strip() if prompts else "默认场景"
                    
                    segments.append((current_narrations.copy(), prompt))
                    current_narrations = []
        
        return segments
        
    except Exception as e:
        print(f"解析脚本文件失败 {script_path}: {e}")
        return []

def process_chapter(chapter_dir):
    """
    处理单个章节
    
    Args:
        chapter_dir: 章节目录路径
    
    Returns:
        list: 生成的视频文件路径列表
    """
    chapter_name = os.path.basename(chapter_dir)
    script_file = os.path.join(chapter_dir, f"{chapter_name}_script.txt")
    
    if not os.path.exists(script_file):
        print(f"警告: 脚本文件不存在 {script_file}")
        return []
    
    print(f"\n=== 处理章节: {chapter_name} ===")
    
    # 解析脚本文件
    segments = parse_chapter_script(script_file)
    
    if not segments:
        print(f"警告: 章节 {chapter_name} 没有有效的内容段落")
        return []
    
    # 第一步：批量生成所有图片
    print(f"\n--- 第一步：批量生成{len(segments)}张图片 ---")
    prompts_and_paths = []
    for i, (narrations, prompt) in enumerate(segments, 1):
        image_name = f"{chapter_name}_segment_{i:02d}"
        image_path = os.path.join(chapter_dir, f"{image_name}.jpeg")
        prompts_and_paths.append((prompt, image_path))
        print(f"准备生成图片 {i}: {prompt[:30]}...")
    
    # 批量生成所有图片
    successful_image_paths = generate_images_batch(prompts_and_paths, chapter_path=chapter_dir)
    
    if len(successful_image_paths) != len(segments):
        print(f"警告: 只成功生成了{len(successful_image_paths)}/{len(segments)}张图片")
    
    # 第二步：为每个段落生成音频和视频
    print(f"\n--- 第二步：生成音频和视频 ---")
    video_files = []
    
    # 处理每个段落组（多个解说内容共用一张图片）
    for i, (narrations, prompt) in enumerate(segments, 1):
        print(f"\n--- 处理段落组 {i}/{len(segments)} ---")
        
        # 获取对应的图片路径
        image_name = f"{chapter_name}_segment_{i:02d}"
        image_path = os.path.join(chapter_dir, f"{image_name}.jpeg")
        
        # 检查图片是否成功生成
        if image_path not in successful_image_paths:
            print(f"段落组 {i} 对应的图片生成失败，跳过")
            continue
        
        print(f"使用图片: {image_name}.jpeg")
        
        # 处理该组内的每个解说内容
        for j, narration in enumerate(narrations, 1):
            print(f"\n  处理解说 {j}/{len(narrations)}: {narration[:20]}...")
            
            # 清理解说文本
            clean_narration = clean_text_for_tts(narration)
            
            # 使用智能断句
            text_parts = smart_split_text(clean_narration, max_length=50)
            
            if len(text_parts) > 1:
                print(f"  智能断句为 {len(text_parts)} 个部分")
            
            # 为每个断句部分生成音频和视频
            for part_idx, text_part in enumerate(text_parts, 1):
                if len(text_parts) > 1:
                    segment_name = f"{chapter_name}_segment_{i:02d}_narration_{j:02d}_part_{part_idx:02d}"
                else:
                    segment_name = f"{chapter_name}_segment_{i:02d}_narration_{j:02d}"
                
                # 定义文件路径
                audio_path = os.path.join(chapter_dir, f"{segment_name}.mp3")
                video_path = os.path.join(chapter_dir, f"{segment_name}.mp4")
                
                if len(text_parts) > 1:
                    print(f"    处理部分 {part_idx}/{len(text_parts)}: {text_part[:15]}...")
                
                # 生成音频
                if generate_audio(text_part, audio_path):
                    # 使用共用图片合成视频（带字幕）
                    if create_video_with_subtitle(image_path, audio_path, text_part, video_path):
                        video_files.append(video_path)
                        if len(text_parts) > 1:
                            print(f"    部分 {part_idx} 处理完成")
                        else:
                            print(f"  解说 {j} 处理完成")
                    else:
                        print(f"    部分 {part_idx} 视频合成失败" if len(text_parts) > 1 else f"  解说 {j} 视频合成失败")
                else:
                    print(f"    部分 {part_idx} 音频生成失败" if len(text_parts) > 1 else f"  解说 {j} 音频生成失败")
    
    return video_files

def concat_chapter_videos(video_files, output_path):
    """
    拼接章节内的所有视频段落
    
    Args:
        video_files: 视频文件路径列表
        output_path: 输出文件路径
    
    Returns:
        bool: 是否成功拼接
    """
    try:
        if not video_files:
            print("没有视频文件需要拼接")
            return False
        
        if len(video_files) == 1:
            # 只有一个视频文件，直接复制
            import shutil
            shutil.copy2(video_files[0], output_path)
            print(f"单个视频文件已复制到: {output_path}")
            return True
        
        print(f"正在拼接 {len(video_files)} 个视频段落...")
        
        # 确保输出目录存在
        os.makedirs(os.path.dirname(output_path), exist_ok=True)
        
        # 创建临时文件列表
        temp_list_file = "temp_video_list.txt"
        with open(temp_list_file, 'w', encoding='utf-8') as f:
            for video_file in video_files:
                # 使用相对路径或绝对路径
                f.write(f"file '{os.path.abspath(video_file)}'\n")
        
        # 使用ffmpeg-python拼接视频，重新编码音频以确保平滑拼接
        input_stream = ffmpeg.input(temp_list_file, f='concat', safe=0)
        output_stream = ffmpeg.output(
            input_stream,
            output_path,
            vcodec='copy',  # 视频流直接复制
            acodec='aac',   # 音频重新编码为AAC
            audio_bitrate='128k',  # 音频比特率
            ar=44100,  # 音频采样率
            ac=2,      # 双声道
            af='aresample=async=1'  # 音频重采样，确保同步
        )
        
        try:
            ffmpeg.run(output_stream, overwrite_output=True, quiet=True)
            result_returncode = 0
        except ffmpeg.Error as e:
            print(f"FFmpeg错误: {e.stderr.decode() if e.stderr else str(e)}")
            result_returncode = 1
        
        # 清理临时文件
        if os.path.exists(temp_list_file):
            os.remove(temp_list_file)
        
        if result_returncode == 0:
            print(f"章节视频拼接成功: {output_path}")
            return True
        else:
            print(f"章节视频拼接失败")
            return False
            
    except Exception as e:
        print(f"拼接章节视频时发生错误: {e}")
        # 清理临时文件
        if 'temp_list_file' in locals() and os.path.exists(temp_list_file):
            os.remove(temp_list_file)
        return False

def split_novel_into_chapters(novel_content, target_chapters=50):
    """
    将小说内容智能分割成指定数量的章节
    
    Args:
        novel_content: 小说内容
        target_chapters: 目标章节数量（默认50）
    
    Returns:
        List[str]: 分割后的章节内容列表
    """
    # 计算每章大致长度
    total_length = len(novel_content)
    avg_chapter_length = total_length // target_chapters
    
    chapters = []
    current_pos = 0
    
    for i in range(target_chapters):
        if i == target_chapters - 1:  # 最后一章包含剩余所有内容
            chapter_content = novel_content[current_pos:]
        else:
            # 寻找合适的分割点（句号、感叹号、问号后）
            end_pos = current_pos + avg_chapter_length
            
            # 在目标位置前后寻找合适的分割点
            search_range = min(200, avg_chapter_length // 4)  # 搜索范围
            best_split = end_pos
            
            # 向后搜索分割点
            for j in range(end_pos, min(end_pos + search_range, total_length)):
                if novel_content[j] in ['。', '！', '？']:
                    best_split = j + 1
                    break
            
            # 如果向后没找到，向前搜索
            if best_split == end_pos:
                for j in range(end_pos, max(current_pos, end_pos - search_range), -1):
                    if novel_content[j] in ['。', '！', '？']:
                        best_split = j + 1
                        break
            
            chapter_content = novel_content[current_pos:best_split]
            current_pos = best_split
        
        if chapter_content.strip():  # 只添加非空章节
            chapters.append(chapter_content.strip())
    
    return chapters

def generate_chapter_narration(chapter_content, chapter_num, total_chapters):
    """
    为单个章节生成850字解说文案
    
    Args:
        chapter_content: 章节内容
        chapter_num: 章节编号
        total_chapters: 总章节数
    
    Returns:
        str: 生成的解说文案
    """
    try:
        # 导入必要的模块
        from jinja2 import Environment, FileSystemLoader
        import os
        
        # 创建脚本生成器实例
        generator = ScriptGenerator(api_key=ARK_CONFIG['api_key'])
        
        # 设置模板环境
        template_dir = os.path.join(os.path.dirname(__file__), 'src', 'script')
        env = Environment(loader=FileSystemLoader(template_dir))
        template = env.get_template('chapter_narration_prompt.j2')
        
        # 示例人物数据（实际使用时可以从章节内容中提取或预定义）
        characters = [
            {
                'name': '主角',
                'height_build': '身材高大（约180cm），体型匀称',
                'hair_color': '乌黑色',
                'hair_style': '短发寸头',
                'hair_texture': '直发',
                'eye_color': '深棕色',
                'eye_shape': '丹凤眼',
                'eye_expression': '眼神犀利专注',
                'face_shape': '方形脸',
                'chin_shape': '方形下巴',
                'skin_tone': '健康肤色',
                'clothing_color': '深蓝色',
                'clothing_style': '长款羊毛风衣',
                'clothing_material': '羊毛',
                'glasses': '黑框眼镜',
                'jewelry': '银色金属表带手表',
                'other_accessories': '无',
                'expression_posture': '给人可靠专业的感觉'
            }
        ]
        
        # 渲染模板
        custom_prompt = template.render(
            chapter_num=chapter_num,
            total_chapters=total_chapters,
            chapter_content=chapter_content,
            characters=characters
        )
        
        print(f"正在为第{chapter_num}章生成解说文案...")
        
        # 调用API生成解说
        completion = generator.client.chat.completions.create(
            model=generator.model,
            messages=[
                {"role": "user", "content": custom_prompt}
            ],
            stream=False
        )
        
        narration = completion.choices[0].message.content.strip()
        print(f"第{chapter_num}章解说文案生成完成，长度：{len(narration)}字")
        
        return narration
        
    except Exception as e:
        print(f"生成第{chapter_num}章解说文案时出错：{e}")
        return ""

def generate_script_from_novel_new(novel_file, output_dir, target_chapters=50):
    """
    新的小说脚本生成函数，支持章节分割和850字解说生成
    
    Args:
        novel_file: 小说文件路径
        output_dir: 输出目录
        target_chapters: 目标章节数量（默认50）
    
    Returns:
        bool: 是否成功
    """
    try:
        print(f"=== 开始新的脚本生成流程 ===")
        print(f"输入文件: {novel_file}")
        print(f"输出目录: {output_dir}")
        print(f"目标章节数: {target_chapters}")
        
        # 检查输入文件
        if not os.path.exists(novel_file):
            print(f"错误: 小说文件不存在 {novel_file}")
            return False
        
        # 读取小说内容，支持多种编码格式
        novel_content = read_novel_file_with_encoding(novel_file)
        
        if not novel_content.strip():
            print("错误: 小说文件内容为空")
            return False
        
        print(f"小说总长度: {len(novel_content)}字")
        
        # 分割小说为章节
        print("\n=== 开始分割章节 ===")
        chapters = split_novel_into_chapters(novel_content, target_chapters)
        print(f"成功分割为 {len(chapters)} 个章节")
        
        # 创建输出目录
        os.makedirs(output_dir, exist_ok=True)
        
        # 为每个章节生成解说文案
        print("\n=== 开始生成章节解说文案 ===")
        success_count = 0
        
        for i, chapter_content in enumerate(chapters, 1):
            print(f"\n--- 处理第 {i}/{len(chapters)} 章 ---")
            print(f"章节内容长度: {len(chapter_content)}字")
            
            # 创建章节目录
            chapter_dir = os.path.join(output_dir, f"chapter_{i:03d}")
            os.makedirs(chapter_dir, exist_ok=True)
            
            # 保存原始章节内容
            chapter_file = os.path.join(chapter_dir, "original_content.txt")
            with open(chapter_file, 'w', encoding='utf-8') as f:
                f.write(chapter_content)
            
            # 生成850字解说文案
            narration = generate_chapter_narration(chapter_content, i, len(chapters))
            
            if narration:
                # 保存解说文案
                narration_file = os.path.join(chapter_dir, "narration.txt")
                with open(narration_file, 'w', encoding='utf-8') as f:
                    f.write(narration)
                
                print(f"✓ 第{i}章解说文案已保存")
                success_count += 1
            else:
                print(f"✗ 第{i}章解说文案生成失败")
        
        print(f"\n=== 脚本生成完成 ===")
        print(f"成功生成 {success_count}/{len(chapters)} 个章节的解说文案")
        print(f"输出目录: {output_dir}")
        
        return success_count > 0
        
    except Exception as e:
        print(f"生成脚本时发生错误: {e}")
        return False

def generate_script_from_novel(novel_file, output_dir):
    """
    从小说文件生成脚本
    
    Args:
        novel_file: 小说文件路径
        output_dir: 输出目录
    
    Returns:
        bool: 是否成功
    """
    try:
        print(f"=== 开始生成脚本 ===")
        print(f"输入文件: {novel_file}")
        print(f"输出目录: {output_dir}")
        
        # 检查输入文件
        if not os.path.exists(novel_file):
            print(f"错误: 小说文件不存在 {novel_file}")
            return False
        
        # 读取小说内容，支持多种编码格式
        novel_content = read_novel_file_with_encoding(novel_file)
        
        if not novel_content.strip():
            print("错误: 小说文件内容为空")
            return False
        
        # 创建脚本生成器
        generator = ScriptGenerator(api_key=ARK_CONFIG['api_key'])
        
        # 生成脚本
        success = generator.generate_script(novel_content, output_dir)
        
        if success:
            print(f"✓ 脚本生成成功，保存到: {output_dir}")
            return True
        else:
            print("✗ 脚本生成失败")
            return False
            
    except Exception as e:
        print(f"生成脚本时发生错误: {e}")
        return False

    """
    根据脚本生成图片（支持风格配置）
    
    Args:
        data_dir: 数据目录路径
    
    Returns:
        bool: 是否成功
    """
    try:
        print(f"=== 开始生成图片 ===")
        print(f"数据目录: {data_dir}")
        
        if not os.path.exists(data_dir):
            print(f"错误: 数据目录不存在 {data_dir}")
            return False
        
        # 查找所有章节目录
        chapter_dirs = []
        for item in os.listdir(data_dir):
            item_path = os.path.join(data_dir, item)
            if os.path.isdir(item_path) and item.startswith('chapter_'):
                chapter_dirs.append(item_path)
        
        if not chapter_dirs:
            print(f"错误: 在 {data_dir} 中没有找到章节目录")
            return False
        
        chapter_dirs.sort()
        print(f"找到 {len(chapter_dirs)} 个章节目录")
        
        success_count = 0
        
        # 处理每个章节
        for chapter_dir in chapter_dirs:
            chapter_name = os.path.basename(chapter_dir)
            print(f"\n--- 处理章节: {chapter_name} ---")
            
            # 查找narration文件
            narration_file = os.path.join(chapter_dir, "narration.txt")
            if not os.path.exists(narration_file):
                print(f"警告: narration文件不存在 {narration_file}")
                continue
            
            # 读取narration内容
            with open(narration_file, 'r', encoding='utf-8') as f:
                narration_content = f.read().strip()
            
            if not narration_content:
                print(f"警告: narration内容为空")
                continue
            
            # 提取风格信息
            story_style = "玄幻修真"  # 默认风格
            style_pattern = r'<风格>\s*([^<]+)\s*</风格>'
            style_match = re.search(style_pattern, narration_content)
            if style_match:
                story_style = style_match.group(1).strip()
                print(f"检测到故事风格: {story_style}")
            
            # 获取风格配置
            style_config = STORY_STYLE.get(story_style, STORY_STYLE["玄幻修真"])
            model_prompt = style_config.get("model_prompt", "")
            core_style = style_config.get("core_style", "")
            
            # 如果model_prompt是列表，取第一个
            if isinstance(model_prompt, list):
                model_prompt = model_prompt[0]
            
            print(f"使用风格配置: {core_style}")
            print(f"模型提示词: {model_prompt}")
            
            # 提取人物信息
            characters = {}
            character_pattern = r'<主要人物>\s*([\s\S]*?)(?=<|$)'
            character_match = re.search(character_pattern, narration_content)
            if character_match:
                character_text = character_match.group(1)
                # 解析每个人物的信息
                char_blocks = re.split(r'\n(?=\S)', character_text.strip())
                for block in char_blocks:
                    if block.strip():
                        lines = block.strip().split('\n')
                        if lines:
                            name = lines[0].strip().rstrip('：:')
                            details = []
                            for line in lines[1:]:
                                line = line.strip()
                                if line and not line.startswith('-'):
                                    details.append(line)
                            if details:
                                characters[name] = '，'.join(details)
            
            # 提取图片prompts
            prompt_pattern = r'<图片prompt>\s*([\s\S]*?)(?=<|$)'
            prompts = re.findall(prompt_pattern, narration_content)
            
            if not prompts:
                print(f"警告: 未找到图片prompt")
                continue
            
            print(f"找到 {len(prompts)} 个图片prompt")
            
            # 为每个prompt生成图片
            for i, prompt in enumerate(prompts, 1):
                prompt = prompt.strip()
                if not prompt:
                    continue
                
                # 增强prompt：添加风格信息
                enhanced_prompt = f"{model_prompt}，{core_style}，{prompt}"
                
                # 如果包含人名，添加人物细节
                for char_name in characters:
                    if char_name in prompt:
                        char_details = characters[char_name]
                        enhanced_prompt = enhanced_prompt.replace(char_name, f"{char_name}（{char_details}）")
                
                print(f"  生成第 {i}/{len(prompts)} 张图片: {chapter_name}_image_{i:02d}.jpeg")
                print(f"  风格增强prompt: {enhanced_prompt[:150]}...")
                
                # 生成图片
                image_path = os.path.join(chapter_dir, f"{chapter_name}_image_{i:02d}.jpeg")
                
                # 使用本地图片生成函数（使用ARK_CONFIG配置）
                if generate_image(enhanced_prompt, image_path, chapter_path=chapter_dir):
                    print(f"  ✓ 图片生成成功")
                    success_count += 1
                else:
                    print(f"  ✗ 图片生成失败")
            
            print(f"章节 {chapter_name} 处理完成，成功生成 {len([p for p in prompts if p.strip()])} 张图片")
        
        print(f"\n图片生成完成，成功生成 {success_count} 张图片")
        return success_count > 0
        
    except Exception as e:
        print(f"生成图片时发生错误: {e}")
        return False

def extract_narration_content(narration_file_path):
    """
    从narration.txt文件中提取解说内容
    
    Args:
        narration_file_path: narration.txt文件路径
    
    Returns:
        list: 解说内容列表
    """
    narration_contents = []
    
    try:
        if not os.path.exists(narration_file_path):
            print(f"警告: narration.txt文件不存在: {narration_file_path}")
            return narration_contents
        
        with open(narration_file_path, 'r', encoding='utf-8') as f:
            content = f.read()
        
        # 使用正则表达式提取所有<解说内容>标签中的内容
        narration_matches = re.findall(r'<解说内容>(.*?)</解说内容>', content, re.DOTALL)
        
        for narration in narration_matches:
            # 清理文本，移除多余的空白字符
            clean_narration = narration.strip()
            if clean_narration:
                narration_contents.append(clean_narration)
        
        print(f"从 {narration_file_path} 中提取到 {len(narration_contents)} 段解说内容")
        return narration_contents
        
    except Exception as e:
        print(f"提取解说内容时发生错误: {e}")
        return narration_contents

def generate_voices_from_scripts(data_dir):
    """
    根据脚本生成语音
    
    Args:
        data_dir: 数据目录路径
    
    Returns:
        bool: 是否成功
    """
    try:
        print(f"=== 开始生成语音 ===")
        print(f"数据目录: {data_dir}")
        
        if not os.path.exists(data_dir):
            print(f"错误: 数据目录不存在 {data_dir}")
            return False
        
        # 查找所有章节目录
        chapter_dirs = []
        for item in os.listdir(data_dir):
            item_path = os.path.join(data_dir, item)
            if os.path.isdir(item_path) and item.startswith('chapter_'):
                chapter_dirs.append(item_path)
        
        if not chapter_dirs:
            print(f"错误: 在 {data_dir} 中没有找到章节目录")
            return False
        
        chapter_dirs.sort()
        print(f"找到 {len(chapter_dirs)} 个章节目录")
        
        # 创建语音生成器
        voice_generator = VoiceGenerator()
        
        success_count = 0
        
        # 处理每个章节
        for chapter_dir in chapter_dirs:
            chapter_name = os.path.basename(chapter_dir)
            print(f"\n--- 处理章节: {chapter_name} ---")
            
            # 查找解说文件
            narration_file = os.path.join(chapter_dir, "narration.txt")
            if not os.path.exists(narration_file):
                print(f"警告: 解说文件不存在 {narration_file}")
                continue
            
            # 提取解说内容
            narration_contents = extract_narration_content(narration_file)
            
            if not narration_contents:
                print(f"警告: 未找到解说内容")
                continue
            
            print(f"找到 {len(narration_contents)} 段解说内容")
            
            # 为每段解说内容生成语音
            for i, narration_text in enumerate(narration_contents, 1):
                # 清理文本用于TTS
                clean_narration = clean_text_for_tts(narration_text)
                
                if not clean_narration.strip():
                    print(f"警告: 第 {i} 段解说内容清理后为空")
                    continue
                
                # 生成音频文件路径
                audio_path = os.path.join(chapter_dir, f"{chapter_name}_narration_{i:02d}.mp3")
                
                # 生成时间戳文件路径
                timestamp_path = os.path.join(chapter_dir, f"{chapter_name}_narration_{i:02d}_timestamps.json")
                
                print(f"正在生成第 {i} 段解说语音...")
                print(f"文本内容: {clean_narration[:50]}{'...' if len(clean_narration) > 50 else ''}")
                
                # 使用语音生成器生成语音
                if voice_generator.generate_voice(clean_narration, audio_path):
                    print(f"✓ 第 {i} 段语音生成成功: {audio_path}")
                    
                    # 生成时间戳信息（模拟，实际需要从TTS API获取）
                    timestamp_data = {
                        "text": clean_narration,
                        "audio_file": audio_path,
                        "duration": len(clean_narration) * 0.15,  # 估算时长（每字0.15秒）
                        "character_timestamps": [],
                        "generated_at": datetime.now().isoformat()
                    }
                    
                    # 为每个字符生成时间戳（模拟）
                    current_time = 0.0
                    for char_idx, char in enumerate(clean_narration):
                        char_duration = 0.15  # 每个字符0.15秒
                        timestamp_data["character_timestamps"].append({
                            "character": char,
                            "start_time": current_time,
                            "end_time": current_time + char_duration,
                            "index": char_idx
                        })
                        current_time += char_duration
                    
                    # 保存时间戳文件
                    try:
                        with open(timestamp_path, 'w', encoding='utf-8') as f:
                            json.dump(timestamp_data, f, ensure_ascii=False, indent=2)
                        print(f"✓ 时间戳文件保存成功: {timestamp_path}")
                    except Exception as e:
                        print(f"✗ 时间戳文件保存失败: {e}")
                    
                    success_count += 1
                else:
                    print(f"✗ 第 {i} 段语音生成失败")
        
        print(f"\n语音生成完成，成功生成 {success_count} 个语音文件")
        return success_count > 0
        
    except Exception as e:
        print(f"生成语音时发生错误: {e}")
        return False

def split_text_by_timestamps(text, timestamps, max_chars_per_segment=40):
    """
    根据时间戳分割文本，优化分割策略以避免在词语中间分割
    
    Args:
        text: 完整文本
        timestamps: character_timestamps列表
        max_chars_per_segment: 每段最大字符数
    
    Returns:
        list: 包含(文本片段, 开始时间, 结束时间)的元组列表
    """
    import re
    
    segments = []
    current_text = ""
    start_time = 0
    
    # 定义自然停顿的标点符号（优先级从高到低）
    major_punctuation = ['。', '！', '？']  # 句子结束符，优先分割
    minor_punctuation = ['，', '；', '：', '、']  # 次要停顿符
    
    # 定义词边界字符（中文常见的词尾字符）
    word_boundary_chars = ['的', '了', '着', '过', '地', '得', '在', '与', '和', '或', '但', '而', '然', '后', '前', '中', '上', '下', '内', '外']
    
    for i, char_info in enumerate(timestamps):
        char = char_info['character']
        char_start = char_info['start_time']
        char_end = char_info['end_time']
        
        # 如果是第一个字符，记录开始时间
        if not current_text:
            start_time = char_start
        
        current_text += char
        
        # 检查是否需要分段
        should_split = False
        split_priority = 0  # 分割优先级，数字越大优先级越高
        
        # 如果是最后一个字符，必须分段
        if i == len(timestamps) - 1:
            should_split = True
            split_priority = 100
        
        # 检查各种分割条件
        elif len(current_text) >= max_chars_per_segment:
            # 达到最大字符数，需要寻找合适的分割点
            if char in major_punctuation:
                # 遇到主要标点符号，立即分割
                should_split = True
                split_priority = 90
            elif char in minor_punctuation:
                # 遇到次要标点符号，优先分割
                should_split = True
                split_priority = 80
            elif char in word_boundary_chars:
                # 遇到词边界字符，可以分割
                should_split = True
                split_priority = 70
            elif len(current_text) >= max_chars_per_segment + 5:
                # 超出太多字符，强制分割
                should_split = True
                split_priority = 60
        
        # 在合适长度下遇到自然停顿点
        elif len(current_text) >= 8:  # 最小长度要求
            if char in major_punctuation:
                # 遇到主要标点符号，分割
                should_split = True
                split_priority = 85
            elif char in minor_punctuation and len(current_text) >= 12:
                # 遇到次要标点符号且长度适中，分割
                should_split = True
                split_priority = 75
        
        # 寻找更好的分割点（向前回溯）
        if should_split and len(current_text) > 15 and split_priority < 80:
            # 尝试在最近的标点符号处分割
            best_split_pos = -1
            best_priority = 0
            
            # 向前回溯最多5个字符寻找更好的分割点
            for j in range(min(5, len(current_text) - 8)):
                check_pos = len(current_text) - 1 - j
                if check_pos < 8:  # 确保最小长度
                    break
                    
                check_char = current_text[check_pos]
                check_priority = 0
                
                if check_char in major_punctuation:
                    check_priority = 85
                elif check_char in minor_punctuation:
                    check_priority = 75
                elif check_char in word_boundary_chars:
                    check_priority = 65
                
                if check_priority > best_priority:
                    best_split_pos = check_pos + 1  # 在标点符号后分割
                    best_priority = check_priority
            
            # 如果找到更好的分割点，调整分割位置
            if best_split_pos > 0 and best_priority > split_priority:
                # 回退到更好的分割点
                split_text = current_text[:best_split_pos]
                remaining_text = current_text[best_split_pos:]
                
                # 计算分割点的时间戳
                split_timestamp_index = i - len(remaining_text)
                if split_timestamp_index >= 0:
                    split_end_time = timestamps[split_timestamp_index]['end_time']
                    
                    # 添加分割的片段
                    if split_text.strip():
                        segments.append((split_text.strip(), start_time, split_end_time))
                    
                    # 重置当前文本为剩余部分
                    current_text = remaining_text
                    start_time = timestamps[split_timestamp_index + 1]['start_time'] if split_timestamp_index + 1 < len(timestamps) else char_start
                    should_split = False
        
        if should_split and current_text.strip():
            segments.append((current_text.strip(), start_time, char_end))
            current_text = ""
    
    return segments

def create_video_segment_with_timing(image_path, audio_path, text_segment, start_time, end_time, output_path, is_first_segment=False):
    """
    创建带有精确时间控制的视频片段
    
    Args:
        image_path: 图片文件路径
        audio_path: 音频文件路径
        text_segment: 字幕文本片段
        start_time: 开始时间（秒）
        end_time: 结束时间（秒）
        output_path: 输出视频路径
    
    Returns:
        bool: 是否成功生成
    """
    try:
        # 确保输出目录存在
        output_dir = os.path.dirname(output_path)
        if output_dir:
            os.makedirs(output_dir, exist_ok=True)
        
        print(f"正在创建视频片段: {os.path.basename(output_path)}")
        print(f"时间范围: {start_time:.2f}s - {end_time:.2f}s")
        print(f"字幕内容: {text_segment}")
        
        # 计算片段时长
        duration = end_time - start_time
        
        # 创建输入流，使用超高精度时间参数
        # 将时间精度提高到微秒级别（6位小数）
        precise_start_time = f"{start_time:.6f}"
        precise_duration = f"{duration:.6f}"
        
        print(f"精确时间参数 - 开始时间: {precise_start_time}s, 持续时间: {precise_duration}s")
        
        # 图片输入：循环播放，持续时间为片段时长
        image_input = ffmpeg.input(image_path, loop=1, t=precise_duration)
        
        # 字幕提前显示时间（秒）- 让字幕稍微早于声音出现
        subtitle_advance_time = 0.15  # 字幕提前0.15秒显示
        
        # 音频输入：先切割指定时间段的音频，然后重新从0开始
        # 这样可以避免片段开头的静音问题
        audio_segment = ffmpeg.input(audio_path, 
                                   ss=precise_start_time, 
                                   t=precise_duration,
                                   accurate_seek=None,
                                   avoid_negative_ts='make_zero')
        
        # 将切割后的音频重新设置为从0开始，避免时间偏移导致的静音
        # 只在第一个片段添加音频延迟以实现字幕提前显示，避免拼接时的间隙
        if is_first_segment:
            audio_input = audio_segment.filter('asetpts', 'PTS-STARTPTS').filter('adelay', f'{int(subtitle_advance_time * 1000)}|{int(subtitle_advance_time * 1000)}')
        else:
            audio_input = audio_segment.filter('asetpts', 'PTS-STARTPTS')
        
        # 不使用图片特效，直接使用原始视频流
        video_with_effects = image_input.video
        
        # 清理字幕文本
        clean_subtitle = clean_text_for_tts(text_segment)
        
        if clean_subtitle.strip():
            # 视频尺寸设置
            video_width = 720
            video_height = 1280
            
            # 处理字幕文本，确保不超出边框
            wrapped_subtitle = wrap_text(clean_subtitle, max_chars_per_line=30)
            
            # 字幕位置：使用FFmpeg表达式确保显示在底部
            subtitle_y = 'h-text_h-h/3'  # 距离底部1/3视频高度像素
            
            print(f"调试信息 - 视频尺寸: {video_width}x{video_height}")
            print(f"调试信息 - 字幕文本: '{wrapped_subtitle}'")
            print(f"调试信息 - 字幕Y位置表达式: {subtitle_y}")
            
            # 计算字幕显示时间范围，只在第一个片段让字幕提前显示
            if is_first_segment:
                subtitle_start_time = 0  # 字幕从视频开始就显示
                subtitle_end_time = duration + subtitle_advance_time  # 字幕显示到音频结束后
            else:
                subtitle_start_time = 0  # 字幕从视频开始就显示
                subtitle_end_time = duration  # 字幕显示到音频结束
            
            # 添加字幕滤镜（黑体字，透明背景，每行居中，确保不超出边框）
            # 通过enable参数控制字幕显示时间，实现提前显示效果
            video_with_subtitle = video_with_effects.filter(
                'drawtext',
                text=wrapped_subtitle,
                fontfile='/System/Library/Fonts/Helvetica-Bold.ttc',  # 使用黑体字体
                fontsize=72,  # 增大字号到72以便更清晰可见
                fontcolor='black',
                x='max(20, min(w-text_w-20, (w-text_w)/2))',  # 水平居中，确保边距
                y=subtitle_y,
                borderw=3,  # 增加描边宽度
                bordercolor='white',
                box=0,  # 透明背景
                enable=f'gte(t,{subtitle_start_time})*lte(t,{subtitle_end_time})'  # 控制字幕显示时间
            )
        else:
            video_with_subtitle = video_with_effects
        
        # 合成视频，添加超精确时间控制参数
        # 只在第一个片段调整视频时长以适应字幕提前显示
        if is_first_segment:
            adjusted_duration = duration + subtitle_advance_time
        else:
            adjusted_duration = duration
        
        output = ffmpeg.output(
            video_with_subtitle, audio_input,
            output_path,
            vcodec='libx264',
            acodec='aac',
            video_bitrate='2000k', # 设置视频码率
            audio_bitrate='128k',
            ar=44100,
            pix_fmt='yuv420p',
            t=adjusted_duration,  # 设置输出时长
            # 添加超精确时间控制参数
            avoid_negative_ts='make_zero',  # 避免负时间戳
            fflags='+genpts+igndts',  # 生成精确时间戳并忽略DTS
            copyts=None,  # 复制时间戳
            start_at_zero=None,  # 从零开始时间戳
            **{
                'c:a': 'aac', 
                'b:a': '128k',
                'ac': '2',  # 双声道
                'frame_duration': '0.02'  # 设置帧持续时间为20ms
            }
        )
        
        # 运行ffmpeg命令
        ffmpeg.run(output, overwrite_output=True, quiet=True)
        
        # 检查输出文件是否存在
        if os.path.exists(output_path):
            print(f"✓ 视频片段创建成功: {output_path}")
            return True
        else:
            print(f"✗ 视频片段创建失败: {output_path}")
            return False
            
    except Exception as e:
        print(f"创建视频片段时发生错误: {e}")
        return False

def concat_videos_from_assets(data_dir):
    """
    拼接图片、语音和字幕生成视频，支持根据timestamps精确分段
    
    Args:
        data_dir: 数据目录路径
    
    Returns:
        bool: 是否成功
    """
    try:
        print(f"=== 开始拼接视频 ===")
        print(f"数据目录: {data_dir}")
        
        if not os.path.exists(data_dir):
            print(f"错误: 数据目录不存在 {data_dir}")
            return False
        
        # 查找所有章节目录
        chapter_dirs = []
        for item in os.listdir(data_dir):
            item_path = os.path.join(data_dir, item)
            if os.path.isdir(item_path) and item.startswith('chapter_'):
                chapter_dirs.append(item_path)
        
        if not chapter_dirs:
            print(f"错误: 在 {data_dir} 中没有找到章节目录")
            return False
        
        chapter_dirs.sort()
        print(f"找到 {len(chapter_dirs)} 个章节目录")
        
        all_videos = []
        
        # 处理每个章节
        for chapter_dir in chapter_dirs:
            chapter_name = os.path.basename(chapter_dir)
            print(f"\n--- 处理章节: {chapter_name} ---")
            
            # 查找图片文件
            image_files = [f for f in os.listdir(chapter_dir) if f.endswith('.jpeg') and 'image' in f]
            if not image_files:
                print(f"警告: 在 {chapter_dir} 中没有找到图片文件")
                continue
            
            # 查找音频和时间戳文件
            audio_files = [f for f in os.listdir(chapter_dir) if f.endswith('.mp3') and 'narration' in f]
            timestamp_files = [f for f in os.listdir(chapter_dir) if f.endswith('_timestamps.json')]
            
            if not audio_files:
                print(f"警告: 在 {chapter_dir} 中没有找到音频文件")
                continue
            
            chapter_videos = []
            
            # 处理每个音频文件
            for audio_file in sorted(audio_files):
                # 找到对应的图片和时间戳文件
                base_name = audio_file.replace('.mp3', '')
                image_file = None
                timestamp_file = None
                
                # 查找对应的图片文件
                for img in image_files:
                    if base_name.replace('_narration', '_image') in img:
                        image_file = img
                        break
                
                # 查找对应的时间戳文件
                for ts in timestamp_files:
                    if base_name in ts:
                        timestamp_file = ts
                        break
                
                if not image_file:
                    print(f"警告: 找不到 {audio_file} 对应的图片文件")
                    continue
                
                if not timestamp_file:
                    print(f"警告: 找不到 {audio_file} 对应的时间戳文件")
                    continue
                
                # 构建完整路径
                audio_path = os.path.join(chapter_dir, audio_file)
                image_path = os.path.join(chapter_dir, image_file)
                timestamp_path = os.path.join(chapter_dir, timestamp_file)
                
                print(f"处理音频: {audio_file}")
                print(f"对应图片: {image_file}")
                print(f"时间戳文件: {timestamp_file}")
                
                # 读取时间戳文件
                try:
                    with open(timestamp_path, 'r', encoding='utf-8') as f:
                        timestamp_data = json.load(f)
                    
                    text = timestamp_data.get('text', '')
                    character_timestamps = timestamp_data.get('character_timestamps', [])
                    
                    if not character_timestamps:
                        print(f"警告: {timestamp_file} 中没有character_timestamps数据")
                        continue
                    
                    # 根据时间戳分割文本，使用更大的字符数以减少分割频率
                    text_segments = split_text_by_timestamps(text, character_timestamps, max_chars_per_segment=40)
                    
                    print(f"文本分割为 {len(text_segments)} 个片段")
                    
                    # 为每个文本片段创建视频
                    segment_videos = []
                    for i, (segment_text, start_time, end_time) in enumerate(text_segments):
                        segment_output = os.path.join(chapter_dir, f"{base_name}_segment_{i+1:02d}.mp4")
                        
                        # 只在第一个片段添加字幕提前显示效果
                        is_first_segment = (i == 0)
                        if create_video_segment_with_timing(image_path, audio_path, segment_text, start_time, end_time, segment_output, is_first_segment):
                            segment_videos.append(segment_output)
                    
                    # 拼接当前音频的所有片段
                    if segment_videos:
                        audio_complete_path = os.path.join(chapter_dir, f"{base_name}_complete.mp4")
                        if concat_chapter_videos(segment_videos, audio_complete_path):
                            chapter_videos.append(audio_complete_path)
                            print(f"✓ 音频 {audio_file} 的视频片段拼接成功")
                        else:
                            print(f"✗ 音频 {audio_file} 的视频片段拼接失败")
                    
                except Exception as e:
                    print(f"处理时间戳文件 {timestamp_file} 时发生错误: {e}")
                    continue
            
            # 拼接章节内的所有视频
            if chapter_videos:
                chapter_final_path = os.path.join(chapter_dir, f"{chapter_name}_complete.mp4")
                if concat_chapter_videos(chapter_videos, chapter_final_path):
                    all_videos.append(chapter_final_path)
                    print(f"✓ 章节 {chapter_name} 视频拼接成功")
                else:
                    print(f"✗ 章节 {chapter_name} 视频拼接失败")
        
        # 拼接所有章节视频
        if all_videos:
            final_video_path = os.path.join(data_dir, "final_complete_video.mp4")
            if concat_chapter_videos(all_videos, final_video_path):
                print(f"\n✓ 最终视频拼接成功: {final_video_path}")
                return True
            else:
                print(f"\n✗ 最终视频拼接失败")
                return False
        else:
            print("\n没有生成任何章节视频")
            return False
        
    except Exception as e:
        print(f"拼接视频时发生错误: {e}")
        return False

def clean_directory(data_dir):
    """
    清除指定目录下除原始小说文件外的所有文件
    
    Args:
        data_dir: 数据目录路径
    
    Returns:
        bool: 是否成功
    """
    try:
        print(f"=== 开始清理目录 ===")
        print(f"目标目录: {data_dir}")
        
        if not os.path.exists(data_dir):
            print(f"错误: 目录不存在 {data_dir}")
            return False
        
        # 遍历目录中的所有文件和文件夹
        for item in os.listdir(data_dir):
            item_path = os.path.join(data_dir, item)
            
            # 保留原始小说文件（.txt文件）
            if os.path.isfile(item_path) and item.endswith('.txt'):
                print(f"保留原始小说文件: {item}")
                continue
            
            # 删除其他所有文件和文件夹
            try:
                if os.path.isfile(item_path):
                    os.remove(item_path)
                    print(f"删除文件: {item}")
                elif os.path.isdir(item_path):
                    import shutil
                    shutil.rmtree(item_path)
                    print(f"删除目录: {item}")
            except Exception as e:
                print(f"删除 {item} 时发生错误: {e}")
                return False
        
        print(f"✓ 目录清理完成")
        return True
        
    except Exception as e:
        print(f"清理目录时发生错误: {e}")
        return False

def main():
    """
    主函数
    """
    parser = argparse.ArgumentParser(description='统一的视频生成系统')
    parser.add_argument('command', choices=['script', 'image', 'voice', 'concat', 'init'], 
                       help='要执行的命令')
    parser.add_argument('path', help='文件或目录路径')
    parser.add_argument('--output', '-o', help='输出目录（仅用于script命令）')
    parser.add_argument('--chapters', '-c', type=int, default=50, help='目标章节数量（默认50）')
    
    args = parser.parse_args()
    
    print(f"执行命令: {args.command}")
    print(f"目标路径: {args.path}")
    
    if args.command == 'script':
        # 使用新的脚本生成逻辑
        if not args.output:
            # 从路径推断输出目录
            base_name = os.path.splitext(os.path.basename(args.path))[0]
            args.output = os.path.join('data', base_name)
        
        # 使用新的章节分割和解说生成函数
        success = generate_script_from_novel_new(args.path, args.output, args.chapters)
        if success:
            print(f"\n✓ 脚本生成完成，输出目录: {args.output}")
        else:
            print(f"\n✗ 脚本生成失败")
            sys.exit(1)
    
    elif args.command == 'image':
        import subprocess
        subprocess.run(['python', 'gen_image.py', args.path])
    
    elif args.command == 'voice':
        # 生成语音
        success = generate_voices_from_scripts(args.path)
        if success:
            print(f"\n✓ 语音生成完成")
        else:
            print(f"\n✗ 语音生成失败")
            sys.exit(1)
    
    elif args.command == 'concat':
        # 拼接视频
        success = concat_videos_from_assets(args.path)
        if success:
            print(f"\n✓ 视频拼接完成")
        else:
            print(f"\n✗ 视频拼接失败")
            sys.exit(1)
    
    elif args.command == 'init':
        # 清理目录
        success = clean_directory(args.path)
        if success:
            print(f"\n✓ 目录清理完成")
        else:
            print(f"\n✗ 目录清理失败")
            sys.exit(1)
    
    print("\n=== 处理完成 ===")

if __name__ == '__main__':
    main()