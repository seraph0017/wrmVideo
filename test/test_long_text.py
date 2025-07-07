#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
测试长文本分割功能的脚本
"""

import os
import sys
sys.path.append('src')

from generate import create_video_with_subtitle, clean_text_for_tts

def test_long_text_processing():
    """
    测试长文本处理功能
    """
    print("=== 测试长文本分割功能 ===")
    
    # 创建测试用的长文本
    long_text = "这是一段非常长的测试文本，用来验证当文本超过25个字符时，系统是否会正确地将其分割为多个部分进行处理，而不是简单地换行显示。"
    
    print(f"原始文本长度: {len(long_text)} 字符")
    print(f"原始文本: {long_text}")
    print()
    
    # 清理文本
    clean_text = clean_text_for_tts(long_text)
    print(f"清理后文本: {clean_text}")
    print(f"清理后长度: {len(clean_text)} 字符")
    print()
    
    # 模拟分割逻辑
    max_chars = 25
    if len(clean_text) > max_chars:
        text_parts = []
        current_part = ""
        
        for char in clean_text:
            if len(current_part) >= max_chars:
                text_parts.append(current_part)
                current_part = char
            else:
                current_part += char
        
        if current_part:
            text_parts.append(current_part)
        
        print(f"文本将被分为 {len(text_parts)} 个部分:")
        for i, part in enumerate(text_parts, 1):
            print(f"  部分 {i}: {part} (长度: {len(part)})")
    else:
        print("文本长度适中，无需分割")
    
    print("\n=== 测试完成 ===")

def test_subtitle_without_background():
    """
    测试无背景字幕功能
    """
    print("\n=== 测试无背景字幕功能 ===")
    
    # 检查是否有测试用的图片和音频文件
    test_dir = "test/test_chapters/chapter02"
    if os.path.exists(test_dir):
        # 查找现有的图片和音频文件
        files = os.listdir(test_dir)
        image_files = [f for f in files if f.endswith('.jpg')]
        audio_files = [f for f in files if f.endswith('.mp3')]
        
        if image_files and audio_files:
            image_path = os.path.join(test_dir, image_files[0])
            audio_path = os.path.join(test_dir, audio_files[0])
            output_path = "test_no_background_subtitle.mp4"
            
            print(f"使用图片: {image_path}")
            print(f"使用音频: {audio_path}")
            print(f"输出视频: {output_path}")
            
            # 测试无背景字幕视频生成
            subtitle_text = "这是测试字幕，应该没有黑色背景框"
            success = create_video_with_subtitle(image_path, audio_path, subtitle_text, output_path)
            
            if success:
                print("✅ 无背景字幕视频生成成功！")
                print(f"请查看生成的视频文件: {output_path}")
                print("字幕应该是白色文字，没有黑色背景框")
            else:
                print("❌ 无背景字幕视频生成失败")
        else:
            print("❌ 未找到测试用的图片或音频文件")
    else:
        print("❌ 测试目录不存在")

if __name__ == "__main__":
    test_long_text_processing()
    test_subtitle_without_background()