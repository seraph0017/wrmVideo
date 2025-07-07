#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
测试字幕改进功能：
1. 换行后居中对齐
2. 去掉首尾标点符号
3. 透明背景
"""

import sys
import os

# 添加项目根目录到Python路径
project_root = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, project_root)
os.chdir(project_root)

from generate import create_video_with_subtitle, wrap_text, generate_image, generate_audio

def test_subtitle_improvements():
    """
    测试字幕改进功能
    """
    print("=== 测试字幕改进功能 ===")
    
    # 创建测试目录
    test_dir = "test_subtitle_improvements"
    os.makedirs(test_dir, exist_ok=True)
    
    # 测试用的文本（包含首尾标点符号）
    test_texts = [
        "，观众老爷们大家好！今天咱们要聊的这位主角可不简单，他不仅算姻缘、算运气，还能算财运。算财运。他有都算，都能算！，",
        "。这是一段带有首尾标点符号的测试文本，用来验证去除标点符号功能是否正常工作。",
        "！！多行文本测试：第一行内容比较长需要换行，第二行内容也很长同样需要换行处理，第三行内容用来测试居中对齐效果！！"
    ]
    
    print("\n=== 测试文本换行和标点符号处理 ===")
    for i, text in enumerate(test_texts):
        print(f"\n测试文本 {i+1}:")
        print(f"原始文本: '{text}'")
        wrapped = wrap_text(text, max_chars_per_line=20)
        print(f"处理后文本:\n{wrapped}")
        print("-" * 50)
    
    # 生成测试图片
    print("\n正在生成测试图片...")
    image_path = os.path.join(test_dir, "test_image.jpg")
    if generate_image("一个古代街道场景，有传统建筑和石板路", image_path):
        print(f"✅ 图片生成成功: {image_path}")
    else:
        print("❌ 图片生成失败")
        return False
    
    # 生成测试音频
    print("正在生成测试音频...")
    audio_path = os.path.join(test_dir, "test_audio.mp3")
    test_audio_text = "观众老爷们大家好！今天咱们要聊的这位主角可不简单，他不仅算姻缘、算运气，还能算财运。"
    if generate_audio(test_audio_text, audio_path):
        print(f"✅ 音频生成成功: {audio_path}")
    else:
        print("❌ 音频生成失败")
        return False
    
    # 为每个测试文本生成视频
    for i, text in enumerate(test_texts):
        print(f"\n正在生成测试视频 {i+1}...")
        video_path = os.path.join(test_dir, f"test_video_{i+1}.mp4")
        
        if create_video_with_subtitle(image_path, audio_path, text, video_path):
            print(f"✅ 视频 {i+1} 生成成功: {video_path}")
        else:
            print(f"❌ 视频 {i+1} 生成失败")
    
    print("\n🎬 请检查生成的视频文件，确认以下功能：")
    print("1. 字幕换行后每行都居中对齐")
    print("2. 首尾标点符号已被去除")
    print("3. 字幕背景透明（无白色框）")
    print(f"视频目录: {os.path.abspath(test_dir)}")
    
    print("\n✅ 字幕改进功能测试完成")
    return True

if __name__ == "__main__":
    test_subtitle_improvements()