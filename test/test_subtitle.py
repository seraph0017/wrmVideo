#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
测试字幕功能的简单脚本
"""

import os
import sys
sys.path.append('src')

from generate import create_video_with_subtitle, wrap_text

def test_subtitle_functionality():
    """
    测试字幕功能
    """
    print("=== 测试字幕功能 ===")
    
    # 测试文本换行功能
    test_text = "这是一段很长的测试文本，用来验证字幕换行功能是否正常工作，确保文字不会超出视频边框。"
    wrapped = wrap_text(test_text, max_chars_per_line=25)
    print(f"原始文本: {test_text}")
    print(f"换行后文本:\n{wrapped}")
    print()
    
    # 检查是否有测试用的图片和音频文件
    test_dir = "test/test_chapters/chapter02"
    if os.path.exists(test_dir):
        image_files = [f for f in os.listdir(test_dir) if f.endswith('.jpg')]
        audio_files = [f for f in os.listdir(test_dir) if f.endswith('.mp3')]
        
        if image_files and audio_files:
            image_path = os.path.join(test_dir, image_files[0])
            audio_path = os.path.join(test_dir, audio_files[0])
            output_path = "test_subtitle_video.mp4"
            
            print(f"使用图片: {image_path}")
            print(f"使用音频: {audio_path}")
            print(f"输出视频: {output_path}")
            
            # 测试字幕视频生成
            subtitle_text = "这是一个测试字幕，用来验证字幕是否正确显示在视频的下方三分之一处。"
            success = create_video_with_subtitle(image_path, audio_path, subtitle_text, output_path)
            
            if success:
                print("✅ 字幕视频生成成功！")
                print(f"请查看生成的视频文件: {output_path}")
            else:
                print("❌ 字幕视频生成失败")
        else:
            print("❌ 未找到测试用的图片或音频文件")
    else:
        print("❌ 测试目录不存在")

if __name__ == "__main__":
    test_subtitle_functionality()