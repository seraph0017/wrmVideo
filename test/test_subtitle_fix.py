#!/usr/bin/env python3
# -*- coding: utf-8 -*-

import sys
import os

# 添加项目根目录到Python路径
project_root = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.append(project_root)

# 切换到项目根目录
os.chdir(project_root)

from generate import create_video_with_subtitle, generate_image, generate_audio

def test_subtitle_boundary():
    """
    测试字幕边界修复效果
    """
    print("=== 测试字幕边界修复 ===")
    
    # 创建测试目录
    test_dir = "test_subtitle_boundary"
    os.makedirs(test_dir, exist_ok=True)
    
    # 测试用的长文本（容易超出边界）
    long_text = "观众老爷们大家好！今天咱们要聊的这位主角可不简单，他不仅算姻缘、算运气，还能算财运。算财运。他有都算，都能算！"
    
    # 生成测试图片
    image_path = f"{test_dir}/test_image.jpg"
    print(f"正在生成测试图片...")
    if generate_image("一个神秘的算命先生坐在古老的桌子前", image_path):
        print(f"✅ 图片生成成功: {image_path}")
    else:
        print("❌ 图片生成失败")
        return False
    
    # 生成测试音频
    audio_path = f"{test_dir}/test_audio.mp3"
    print(f"正在生成测试音频...")
    if generate_audio(long_text, audio_path):
        print(f"✅ 音频生成成功: {audio_path}")
    else:
        print("❌ 音频生成失败")
        return False
    
    # 生成带字幕的视频
    video_path = f"{test_dir}/test_video_with_subtitle.mp4"
    print(f"正在生成带字幕的视频...")
    if create_video_with_subtitle(image_path, audio_path, long_text, video_path):
        print(f"✅ 视频生成成功: {video_path}")
        print(f"\n🎬 请检查视频文件，确认字幕是否正确显示在边界内")
        print(f"视频路径: {os.path.abspath(video_path)}")
        return True
    else:
        print("❌ 视频生成失败")
        return False

if __name__ == "__main__":
    success = test_subtitle_boundary()
    if success:
        print("\n✅ 字幕边界修复测试完成")
    else:
        print("\n❌ 字幕边界修复测试失败")