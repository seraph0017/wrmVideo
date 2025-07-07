#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
测试视频音频功能的脚本
"""

import subprocess
import os

def check_video_audio(video_path):
    """
    检查视频文件是否包含音频流
    
    Args:
        video_path: 视频文件路径
    
    Returns:
        bool: 是否包含音频
    """
    try:
        # 使用ffprobe检查音频流
        result = subprocess.run([
            'ffprobe', '-v', 'quiet', '-show_streams', 
            '-select_streams', 'a', video_path
        ], capture_output=True, text=True)
        
        return result.returncode == 0 and len(result.stdout.strip()) > 0
    except Exception as e:
        print(f"检查音频时出错: {e}")
        return False

def get_video_info(video_path):
    """
    获取视频文件的详细信息
    
    Args:
        video_path: 视频文件路径
    
    Returns:
        dict: 视频信息
    """
    try:
        # 获取视频时长
        duration_result = subprocess.run([
            'ffprobe', '-v', 'quiet', '-show_entries', 'format=duration',
            '-of', 'csv=p=0', video_path
        ], capture_output=True, text=True)
        
        # 获取音频信息
        audio_result = subprocess.run([
            'ffprobe', '-v', 'quiet', '-show_entries', 
            'stream=codec_name,sample_rate,channels',
            '-select_streams', 'a:0', '-of', 'csv=p=0', video_path
        ], capture_output=True, text=True)
        
        info = {
            'duration': float(duration_result.stdout.strip()) if duration_result.stdout.strip() else 0,
            'has_audio': len(audio_result.stdout.strip()) > 0
        }
        
        if info['has_audio']:
            audio_parts = audio_result.stdout.strip().split(',')
            if len(audio_parts) >= 3:
                info['audio_codec'] = audio_parts[0]
                info['sample_rate'] = audio_parts[1]
                info['channels'] = audio_parts[2]
        
        return info
        
    except Exception as e:
        print(f"获取视频信息时出错: {e}")
        return {'duration': 0, 'has_audio': False}

def main():
    """
    主测试函数
    """
    print("=== 视频音频测试 ===")
    
    test_videos = [
        "test/test_chapters/final_complete_video.mp4",
        "test/test_chapters/chapter02/chapter02_complete.mp4",
        "test/test_chapters/chapter03/chapter03_complete.mp4"
    ]
    
    for video_path in test_videos:
        if os.path.exists(video_path):
            print(f"\n检查视频: {video_path}")
            
            # 检查音频
            has_audio = check_video_audio(video_path)
            print(f"包含音频: {'✅ 是' if has_audio else '❌ 否'}")
            
            # 获取详细信息
            info = get_video_info(video_path)
            print(f"视频时长: {info['duration']:.2f} 秒")
            
            if info['has_audio']:
                print(f"音频编码: {info.get('audio_codec', 'N/A')}")
                print(f"采样率: {info.get('sample_rate', 'N/A')} Hz")
                print(f"声道数: {info.get('channels', 'N/A')}")
        else:
            print(f"\n❌ 视频文件不存在: {video_path}")
    
    print("\n=== 测试完成 ===")

if __name__ == "__main__":
    main()