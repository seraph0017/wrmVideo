#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
测试字幕边框修复功能
验证字幕不会超出视频边框
"""

import os
from generate import wrap_text, create_video_with_subtitle, generate_image, generate_audio

def test_subtitle_boundary_fix():
    """
    测试字幕边框修复效果
    """
    print("=== 测试字幕边框修复功能 ===")
    
    # 创建测试目录
    test_dir = "test_subtitle_boundary_fix"
    os.makedirs(test_dir, exist_ok=True)
    
    # 测试不同长度的字幕文本
    test_cases = [
        {
            "name": "短字幕",
            "text": "这是短字幕",
            "expected_length": 5
        },
        {
            "name": "中等长度字幕",
            "text": "这是一个中等长度的字幕文本",
            "expected_length": 12
        },
        {
            "name": "长字幕（需要截取）",
            "text": "观众老爷们大家好！今天咱们要聊的这位主角可不简单，他不仅算姻缘、算运气，还能算财运。算财运。他有都算，都能算！",
            "expected_length": 25
        },
        {
            "name": "超长字幕（需要截取）",
            "text": "这是一个非常非常非常非常非常非常非常非常非常非常非常非常非常非常非常非常非常非常非常非常长的字幕文本，应该被截取并添加省略号",
            "expected_length": 25
        }
    ]
    
    print("\n=== 测试字幕文本处理 ===")
    for i, case in enumerate(test_cases, 1):
        processed_text = wrap_text(case["text"])
        print(f"测试 {i} - {case['name']}:")
        print(f"  原始文本: {case['text']}")
        print(f"  处理后文本: {processed_text}")
        print(f"  文本长度: {len(processed_text)} (预期最大: {case['expected_length']})")
        
        # 验证长度不超过25个字符
        if len(processed_text) <= 25:
            print(f"  ✅ 长度检查通过")
        else:
            print(f"  ❌ 长度检查失败")
        print()
    
    # 生成测试视频
    print("\n=== 生成测试视频 ===")
    
    # 生成测试图片
    image_path = f"{test_dir}/test_image.jpg"
    print("正在生成测试图片...")
    if generate_image("一个神秘的算命先生坐在古老的桌子前", image_path):
        print(f"✅ 图片生成成功: {image_path}")
    else:
        print("❌ 图片生成失败")
        return False
    
    # 生成测试音频
    audio_path = f"{test_dir}/test_audio.mp3"
    print("正在生成测试音频...")
    if generate_audio("这是一段测试音频", audio_path):
        print(f"✅ 音频生成成功: {audio_path}")
    else:
        print("❌ 音频生成失败")
        return False
    
    # 为每个测试用例生成视频
    for i, case in enumerate(test_cases, 1):
        output_path = f"{test_dir}/test_video_{i}_{case['name'].replace(' ', '_')}.mp4"
        print(f"\n正在生成视频 {i}: {case['name']}")
        
        if create_video_with_subtitle(image_path, audio_path, case["text"], output_path):
            print(f"✅ 视频生成成功: {output_path}")
            print(f"   字幕内容: {wrap_text(case['text'])}")
        else:
            print(f"❌ 视频生成失败: {output_path}")
    
    print("\n=== 测试完成 ===")
    print(f"测试文件保存在: {test_dir}/")
    print("请检查生成的视频文件，确认字幕不会超出边框。")
    
    return True

if __name__ == "__main__":
    test_subtitle_boundary_fix()