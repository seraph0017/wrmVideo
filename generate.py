#!/usr/bin/env python3
# -*- coding: utf-8 -*-

import os
import sys
import re
import xml.etree.ElementTree as ET
from datetime import datetime
import json
import base64
import uuid
import requests
from volcenginesdkarkruntime import Ark
import ffmpeg

# 添加src目录到Python路径
sys.path.append(os.path.join(os.path.dirname(__file__), 'src'))

from config import TTS_CONFIG, ARK_CONFIG, IMAGE_CONFIG

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
        full_prompt = style_prompt + "以下面一段描述为描述，生成一张故事图片\n\n" + prompt
        
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

def wrap_text(text, max_chars_per_line=30):
    """
    将长文本按指定字符数换行，并去掉首尾标点符号
    
    Args:
        text: 原始文本
        max_chars_per_line: 每行最大字符数
    
    Returns:
        str: 换行后的文本
    """
    # 去掉首尾的标点符号
    punctuation = '。！？，；：、""''（）()[]{}【】《》<>'
    text = text.strip(punctuation + ' \t\n')
    
    if len(text) <= max_chars_per_line:
        return text
    
    lines = []
    current_line = ""
    
    for char in text:
        if len(current_line) >= max_chars_per_line:
            lines.append(current_line.strip())
            current_line = char
        else:
            current_line += char
    
    if current_line:
        lines.append(current_line.strip())
    
    return "\n".join(lines)

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
            
            # 字幕换行处理，每行最多20个字符
            wrapped_subtitle = wrap_text(clean_subtitle, max_chars_per_line=20)
            
            # 字幕位置：距离底部三分之一处
            subtitle_y = int(video_height * 2 / 3)  # 约853像素位置（距离底部三分之一）
            
            # 添加字幕滤镜（黑色粗体字，透明背景，每行居中）
            video_with_subtitle = image_input.video.filter(
                'drawtext',
                text=wrapped_subtitle,
                fontfile='/System/Library/Fonts/PingFang.ttc',  # macOS中文字体
                fontsize=32,  # 稍微减小字号
                fontcolor='black',
                x='(w-text_w)/2',  # 水平居中
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
            segments.append(current_segment.strip())
            current_segment = ""
        
        i += 1
    
    # 添加剩余文本
    if current_segment.strip():
        segments.append(current_segment.strip())
    
    return segments

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
    
    video_files = []
    
    # 处理每个段落组（多个解说内容共用一张图片）
    for i, (narrations, prompt) in enumerate(segments, 1):
        print(f"\n--- 处理段落组 {i}/{len(segments)} ---")
        print(f"图片prompt: {prompt[:30]}...")
        
        # 生成共用的图片
        image_name = f"{chapter_name}_segment_{i:02d}"
        image_path = os.path.join(chapter_dir, f"{image_name}.jpg")
        
        print(f"生成共用图片: {image_name}.jpg")
        if not generate_image(prompt, image_path):
            print(f"段落组 {i} 图片生成失败")
            continue
        
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
        
        # 创建输入流列表
        inputs = []
        for video_file in video_files:
            input_stream = ffmpeg.input(video_file)
            inputs.extend([input_stream['v'], input_stream['a']])
        
        # 拼接视频（确保包含音频和视频流）
        output = ffmpeg.concat(*inputs, v=1, a=1).output(output_path)
        
        # 运行ffmpeg命令
        ffmpeg.run(output, overwrite_output=True, quiet=True)
        
        # 检查输出文件是否存在
        if os.path.exists(output_path):
            print(f"章节视频拼接成功: {output_path}")
            return True
        else:
            print("章节视频拼接失败: 输出文件未生成")
            return False
            
    except Exception as e:
        print(f"拼接章节视频时发生错误: {e}")
        return False

def main():
    """
    主函数
    """
    if len(sys.argv) < 2:
        print("使用方法:")
        print("  python generate.py <包含章节的目录路径>  # 处理多个章节")
        print("  python generate.py <单个章节目录路径>    # 处理单个章节")
        print("示例:")
        print("  python generate.py data/001           # 处理data/001下的所有章节")
        print("  python generate.py data/001/chapter01 # 只处理chapter01")
        sys.exit(1)
    
    target_path = sys.argv[1]
    
    if not os.path.exists(target_path):
        print(f"错误: 目录 {target_path} 不存在")
        sys.exit(1)
    
    print(f"开始处理目录: {target_path}")
    
    # 检查是单个章节目录还是包含多个章节的父目录
    target_name = os.path.basename(target_path)
    
    if target_name.startswith('chapter') and target_name[7:].isdigit():
        # 这是一个单个章节目录
        print(f"检测到单个章节目录: {target_name}")
        
        # 检查是否有脚本文件
        script_file = os.path.join(target_path, f"{target_name}_script.txt")
        if not os.path.exists(script_file):
            print(f"错误: 脚本文件不存在 {script_file}")
            sys.exit(1)
        
        # 处理单个章节
        video_files = process_chapter(target_path)
        
        if video_files:
            # 拼接章节内的视频段落
            chapter_video_path = os.path.join(target_path, f"{target_name}_complete.mp4")
            if concat_chapter_videos(video_files, chapter_video_path):
                print(f"\n=== 章节 {target_name} 处理完成 ===")
                print(f"章节视频已保存到: {chapter_video_path}")
            else:
                print(f"\n章节 {target_name} 拼接失败")
        else:
            print(f"\n章节 {target_name} 没有生成任何视频")
    
    else:
        # 这是包含多个章节的父目录
        print(f"检测到父目录，将处理其中的所有章节")
        
        # 获取所有章节目录
        chapter_dirs = []
        for item in os.listdir(target_path):
            item_path = os.path.join(target_path, item)
            if os.path.isdir(item_path) and item.startswith('chapter') and item[7:].isdigit():
                chapter_dirs.append(item_path)
        
        # 按章节编号排序
        chapter_dirs.sort(key=lambda x: int(re.search(r'chapter(\d+)', x).group(1)))
        
        if not chapter_dirs:
            print(f"错误: 在 {target_path} 中没有找到章节目录")
            sys.exit(1)
        
        print(f"找到 {len(chapter_dirs)} 个章节目录")
        
        all_chapter_videos = []
        
        # 处理每个章节
        for chapter_dir in chapter_dirs:
            chapter_name = os.path.basename(chapter_dir)
            
            # 处理章节
            video_files = process_chapter(chapter_dir)
            
            if video_files:
                # 拼接章节内的视频段落
                chapter_video_path = os.path.join(chapter_dir, f"{chapter_name}_complete.mp4")
                if concat_chapter_videos(video_files, chapter_video_path):
                    all_chapter_videos.append(chapter_video_path)
                    print(f"章节 {chapter_name} 处理完成")
                else:
                    print(f"章节 {chapter_name} 拼接失败")
            else:
                print(f"章节 {chapter_name} 没有生成任何视频")
        
        # 拼接所有章节视频
        if all_chapter_videos:
            final_video_path = os.path.join(target_path, "final_complete_video.mp4")
            if concat_chapter_videos(all_chapter_videos, final_video_path):
                print(f"\n=== 所有章节处理完成 ===")
                print(f"最终视频已保存到: {final_video_path}")
            else:
                print("\n最终视频拼接失败")
        else:
            print("\n没有生成任何章节视频")
    
    print("\n=== 处理完成 ===")

if __name__ == '__main__':
    main()