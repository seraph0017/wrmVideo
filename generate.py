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

# 添加src目录到路径
src_dir = os.path.join(os.path.dirname(__file__), 'src')
sys.path.insert(0, src_dir)

from config.config import TTS_CONFIG, ARK_CONFIG, IMAGE_CONFIG, IMAGE_TWO_CONFIG
from src.script.gen_script import ScriptGenerator
from src.voice.gen_voice import VoiceGenerator
from src.image.gen_image import generate_image_with_volcengine

def clean_text_for_tts(text):
    """
    清理文本用于TTS生成，移除括号内的内容
    
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
    
    # 清理多余的空格和换行
    text = re.sub(r'\s+', ' ', text).strip()
    
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
                "speed_ratio": 1.2,
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

# 艺术风格模板
ART_STYLES = {
    'manga': (
        "漫画风格，动漫插画，精美细腻的画风，鲜艳的色彩，清晰的线条，"
        "日式动漫风格，高质量插画，细节丰富，光影效果好，"
    ),
    'realistic': (
        "写实风格，真实感强，细节丰富，高清画质，专业摄影，"
        "自然光线，真实色彩，"
    ),
    'watercolor': (
        "水彩画风格，柔和的色彩，艺术感强，手绘质感，"
        "淡雅的色调，水彩晕染效果，"
    ),
    'oil_painting': (
        "油画风格，厚重的笔触，丰富的色彩层次，古典艺术感，"
        "油画质感，艺术大师风格，"
    )
}

def generate_image(prompt, output_path, style=None):
    """
    生成图片文件
    
    Args:
        prompt: 图片描述
        output_path: 输出文件路径
        style: 艺术风格，如果为None则使用配置文件中的默认风格
    
    Returns:
        bool: 是否成功生成
    """
    try:
        # 初始化Ark客户端
        client = Ark(
            base_url=ARK_CONFIG['base_url'],
            api_key=ARK_CONFIG['api_key'],
        )
        
        # 获取风格设置
        if style is None:
            style = IMAGE_CONFIG.get('default_style', 'manga')
        
        style_prompt = ART_STYLES.get(style, ART_STYLES['manga'])
        
        print(f"正在生成{style}风格图片: {os.path.basename(output_path)}")
        
        # 构建完整的prompt
        full_prompt = style_prompt + "\n\n以下面描述为内容，生成一张故事图片：\n" + prompt
        
        # 统一使用文生图模式
        imagesResponse = client.images.generate(
            model=IMAGE_CONFIG.get('model', 'doubao-seedream-3-0-t2i-250415'),
            prompt=full_prompt,
            watermark=IMAGE_CONFIG.get('watermark', False),
            size=IMAGE_CONFIG.get('size', '720x1280'),
            response_format="b64_json"
        )
        
        # 处理base64格式的图片数据并保存
        if hasattr(imagesResponse.data[0], 'b64_json') and imagesResponse.data[0].b64_json:
            # 确保输出目录存在
            os.makedirs(os.path.dirname(output_path), exist_ok=True)
            
            # 解码base64数据并保存
            image_data = base64.b64decode(imagesResponse.data[0].b64_json)
            with open(output_path, 'wb') as f:
                f.write(image_data)
            
            print(f"图片已保存: {output_path}")
            return True
        else:
            print("未获取到base64格式的图片数据")
            return False
            
    except Exception as e:
        print(f"生成图片时发生错误: {e}")
        return False

def generate_images_batch(prompts_and_paths, style=None):
    """
    批量生成图片文件（优化的批量处理，减少API调用次数）
    
    Args:
        prompts_and_paths: 包含(prompt, output_path)元组的列表
        style: 艺术风格，如果为None则使用配置文件中的默认风格
    
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
            style = IMAGE_CONFIG.get('default_style', 'manga')
        
        successful_paths = []
        
        # 初始化Ark客户端（只初始化一次）
        client = Ark(
            base_url=ARK_CONFIG['base_url'],
            api_key=ARK_CONFIG['api_key'],
        )
        
        style_prompt = ART_STYLES.get(style, ART_STYLES['manga'])
        
        # 逐个生成图片，但使用统一的客户端和风格设置
        for i, (prompt, output_path) in enumerate(prompts_and_paths, 1):
            try:
                print(f"正在生成第{i}/{len(prompts_and_paths)}张图片: {os.path.basename(output_path)}")
                
                # 构建完整的prompt
                full_prompt = style_prompt + "\n\n以下面描述为内容，生成一张故事图片：\n" + prompt
                
                # 生成图片
                imagesResponse = client.images.generate(
                    model=IMAGE_CONFIG.get('model', 'doubao-seedream-3-0-t2i-250415'),
                    prompt=full_prompt,
                    watermark=IMAGE_CONFIG.get('watermark', False),
                    size=IMAGE_CONFIG.get('size', '720x1280'),
                    response_format="b64_json"
                )
                
                # 处理图片数据并保存
                if hasattr(imagesResponse.data[0], 'b64_json') and imagesResponse.data[0].b64_json:
                    # 确保输出目录存在
                    os.makedirs(os.path.dirname(output_path), exist_ok=True)
                    
                    # 解码base64数据并保存
                    image_data = base64.b64decode(imagesResponse.data[0].b64_json)
                    with open(output_path, 'wb') as f:
                        f.write(image_data)
                    
                    print(f"✓ 第{i}张图片已保存: {output_path}")
                    successful_paths.append(output_path)
                else:
                    print(f"✗ 第{i}张图片生成失败: 未获取到base64格式的图片数据")
                    
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

def wrap_text(text, max_chars_per_line=25):
    """
    处理字幕文本，确保只显示一行字幕且不超出边框
    
    Args:
        text: 原始文本
        max_chars_per_line: 每行最大字符数（默认25，确保不超出边框）
    
    Returns:
        str: 处理后的单行文本
    """
    # 去掉首尾的标点符号
    punctuation = '。！？，；：、""''（）()[]{}【】《》<>'
    text = text.strip(punctuation + ' \t\n')
    
    # 如果文本过长，截取前面部分并添加省略号
    if len(text) > max_chars_per_line:
        text = text[:max_chars_per_line-3] + "..."
    
    # 确保返回单行文本，移除所有换行符
    text = text.replace('\n', ' ').replace('\r', ' ')
    
    return text

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
        
        # 如果有字幕文本，添加字幕
        if clean_subtitle.strip():
            # 视频尺寸 720x1280，字幕区域设置
            video_width = 720
            video_height = 1280
            
            # 字幕处理，确保单行显示，最多25个字符（避免超出边框）
            wrapped_subtitle = wrap_text(clean_subtitle, max_chars_per_line=25)
            
            # 字幕位置：距离底部三分之一处，并确保有足够边距
            subtitle_y = int(video_height * 2 / 3)  # 约853像素位置（距离底部三分之一）
            
            # 添加字幕滤镜（黑色粗体字，透明背景，每行居中，确保不超出边框）
            video_with_subtitle = image_input.video.filter(
                'drawtext',
                text=wrapped_subtitle,
                fontfile='/System/Library/Fonts/PingFang.ttc',  # macOS中文字体
                fontsize=28,  # 减小字号避免超出边框
                fontcolor='black',
                x='max(20, min(w-text_w-20, (w-text_w)/2))',  # 水平居中，但确保左右至少20像素边距
                y=subtitle_y,      # 距离底部三分之一处
                # 添加白色描边增强可读性
                borderw=2,
                bordercolor='white',
                # 移除背景框，使字幕透明
                # box=0 表示不显示背景框
                box=0
            )
        else:
            video_with_subtitle = image_input.video
        
        # 合成视频
        output = ffmpeg.output(
            video_with_subtitle, audio_input,
            output_path,
            vcodec='libx264',
            acodec='aac',
            audio_bitrate='192k',  # 设置音频比特率
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
        image_path = os.path.join(chapter_dir, f"{image_name}.jpg")
        prompts_and_paths.append((prompt, image_path))
        print(f"准备生成图片 {i}: {prompt[:30]}...")
    
    # 批量生成所有图片
    successful_image_paths = generate_images_batch(prompts_and_paths)
    
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
        image_path = os.path.join(chapter_dir, f"{image_name}.jpg")
        
        # 检查图片是否成功生成
        if image_path not in successful_image_paths:
            print(f"段落组 {i} 对应的图片生成失败，跳过")
            continue
        
        print(f"使用图片: {image_name}.jpg")
        
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
        
        # 使用ffmpeg拼接视频
        cmd = [
            'ffmpeg', '-y',
            '-f', 'concat',
            '-safe', '0',
            '-i', temp_list_file,
            '-c', 'copy',
            output_path
        ]
        
        result = subprocess.run(cmd, capture_output=True, text=True)
        
        # 清理临时文件
        if os.path.exists(temp_list_file):
            os.remove(temp_list_file)
        
        if result.returncode == 0:
            print(f"章节视频拼接成功: {output_path}")
            return True
        else:
            print(f"章节视频拼接失败: {result.stderr}")
            return False
            
    except Exception as e:
        print(f"拼接章节视频时发生错误: {e}")
        # 清理临时文件
        if 'temp_list_file' in locals() and os.path.exists(temp_list_file):
            os.remove(temp_list_file)
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
        
        # 读取小说内容
        with open(novel_file, 'r', encoding='utf-8') as f:
            novel_content = f.read()
        
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

def generate_images_from_scripts(data_dir):
    """
    根据脚本生成图片
    
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
            
            # 查找图片prompt文件
            prompt_file = os.path.join(chapter_dir, "image_prompt.txt")
            if not os.path.exists(prompt_file):
                print(f"警告: 图片prompt文件不存在 {prompt_file}")
                continue
            
            # 读取prompt
            with open(prompt_file, 'r', encoding='utf-8') as f:
                prompt = f.read().strip()
            
            if not prompt:
                print(f"警告: 图片prompt为空")
                continue
            
            # 生成图片
            image_path = os.path.join(chapter_dir, f"{chapter_name}_image.jpg")
            
            # 使用新的图片生成函数
            if generate_image_with_volcengine(prompt, image_path):
                success_count += 1
            else:
                print(f"✗ 章节 {chapter_name} 图片生成失败")
        
        print(f"\n图片生成完成，成功生成 {success_count}/{len(chapter_dirs)} 张图片")
        return success_count > 0
        
    except Exception as e:
        print(f"生成图片时发生错误: {e}")
        return False

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
            
            # 读取解说内容
            with open(narration_file, 'r', encoding='utf-8') as f:
                narration = f.read().strip()
            
            if not narration:
                print(f"警告: 解说内容为空")
                continue
            
            # 清理文本
            clean_narration = clean_text_for_tts(narration)
            
            # 智能断句
            text_parts = smart_split_text(clean_narration, max_length=50)
            
            print(f"解说内容分为 {len(text_parts)} 个部分")
            
            # 为每个部分生成语音
            for i, text_part in enumerate(text_parts, 1):
                audio_path = os.path.join(chapter_dir, f"{chapter_name}_audio_{i:02d}.mp3")
                
                if generate_audio(text_part, audio_path):
                    print(f"✓ 第 {i} 部分语音生成成功")
                    success_count += 1
                else:
                    print(f"✗ 第 {i} 部分语音生成失败")
        
        print(f"\n语音生成完成，成功生成 {success_count} 个语音文件")
        return success_count > 0
        
    except Exception as e:
        print(f"生成语音时发生错误: {e}")
        return False

def concat_videos_from_assets(data_dir):
    """
    拼接图片、语音和字幕生成视频
    
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
            image_path = os.path.join(chapter_dir, f"{chapter_name}_image.jpg")
            if not os.path.exists(image_path):
                print(f"警告: 图片文件不存在 {image_path}")
                continue
            
            # 查找解说文件
            narration_file = os.path.join(chapter_dir, "narration.txt")
            if not os.path.exists(narration_file):
                print(f"警告: 解说文件不存在 {narration_file}")
                continue
            
            # 读取解说内容
            with open(narration_file, 'r', encoding='utf-8') as f:
                narration = f.read().strip()
            
            # 清理文本
            clean_narration = clean_text_for_tts(narration)
            text_parts = smart_split_text(clean_narration, max_length=50)
            
            chapter_videos = []
            
            # 为每个音频部分创建视频
            for i, text_part in enumerate(text_parts, 1):
                audio_path = os.path.join(chapter_dir, f"{chapter_name}_audio_{i:02d}.mp3")
                
                if not os.path.exists(audio_path):
                    print(f"警告: 音频文件不存在 {audio_path}")
                    continue
                
                # 检查文本长度，如果太长则分割
                if len(text_part) > 25:  # 超过25个字符需要分割
                    # 分割成两部分
                    mid_point = len(text_part) // 2
                    # 寻找合适的分割点（标点符号）
                    split_chars = ['。', '！', '？', '，', '；', '：']
                    best_split = mid_point
                    for j in range(max(0, mid_point-10), min(len(text_part), mid_point+10)):
                        if text_part[j] in split_chars:
                            best_split = j + 1
                            break
                    
                    part1 = text_part[:best_split].strip()
                    part2 = text_part[best_split:].strip()
                    
                    if part1 and part2:
                        # 创建两个视频
                        video1_path = os.path.join(chapter_dir, f"{chapter_name}_video_{i:02d}_part1.mp4")
                        video2_path = os.path.join(chapter_dir, f"{chapter_name}_video_{i:02d}_part2.mp4")
                        
                        if create_video_with_subtitle(image_path, audio_path, part1, video1_path):
                            chapter_videos.append(video1_path)
                            print(f"✓ 视频片段 {i}-1 创建成功")
                        
                        # 为第二部分创建静音音频（如果需要）
                        # 这里简化处理，使用同一个音频文件
                        if create_video_with_subtitle(image_path, audio_path, part2, video2_path):
                            chapter_videos.append(video2_path)
                            print(f"✓ 视频片段 {i}-2 创建成功")
                    else:
                        # 如果分割失败，使用原文本
                        video_path = os.path.join(chapter_dir, f"{chapter_name}_video_{i:02d}.mp4")
                        if create_video_with_subtitle(image_path, audio_path, text_part, video_path):
                            chapter_videos.append(video_path)
                            print(f"✓ 视频片段 {i} 创建成功")
                else:
                    # 文本长度合适，直接创建视频
                    video_path = os.path.join(chapter_dir, f"{chapter_name}_video_{i:02d}.mp4")
                    if create_video_with_subtitle(image_path, audio_path, text_part, video_path):
                        chapter_videos.append(video_path)
                        print(f"✓ 视频片段 {i} 创建成功")
            
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
    
    args = parser.parse_args()
    
    print(f"执行命令: {args.command}")
    print(f"目标路径: {args.path}")
    
    if args.command == 'script':
        # 生成脚本
        if not args.output:
            # 从路径推断输出目录
            base_name = os.path.splitext(os.path.basename(args.path))[0]
            args.output = os.path.join('data', base_name)
        
        success = generate_script_from_novel(args.path, args.output)
        if success:
            print(f"\n✓ 脚本生成完成，输出目录: {args.output}")
        else:
            print(f"\n✗ 脚本生成失败")
            sys.exit(1)
    
    elif args.command == 'image':
        # 生成图片
        success = generate_images_from_scripts(args.path)
        if success:
            print(f"\n✓ 图片生成完成")
        else:
            print(f"\n✗ 图片生成失败")
            sys.exit(1)
    
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