#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
修复 narration_02 视频时长问题
将视频裁剪到与ASS字幕文件匹配的时长
"""

import os
import sys
import subprocess

# 添加项目根目录到路径
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from gen_video import get_ass_duration, get_video_info

def fix_video_duration(video_path, ass_path):
    """
    修复视频时长，使其与ASS字幕文件时长匹配
    
    Args:
        video_path: 视频文件路径
        ass_path: ASS字幕文件路径
    """
    # 获取ASS字幕时长
    ass_duration = get_ass_duration(ass_path)
    if ass_duration <= 0:
        print(f"无法获取ASS字幕时长: {ass_path}")
        return False
    
    # 获取当前视频时长
    video_info = get_video_info(video_path)
    if not video_info[0]:
        print(f"无法获取视频信息: {video_path}")
        return False
    
    current_duration = video_info[3]
    print(f"当前视频时长: {current_duration:.2f}s")
    print(f"ASS字幕时长: {ass_duration:.2f}s")
    
    if abs(current_duration - ass_duration) < 0.1:
        print("视频时长已经正确，无需修复")
        return True
    
    # 创建备份
    backup_path = video_path + ".backup"
    if not os.path.exists(backup_path):
        import shutil
        shutil.copy2(video_path, backup_path)
        print(f"已创建备份: {backup_path}")
    
    # 裁剪视频到正确时长
    temp_path = video_path + ".temp.mp4"
    
    try:
        cmd = [
            'ffmpeg', '-y',
            '-i', video_path,
            '-t', str(ass_duration),
            '-c', 'copy',  # 使用copy避免重新编码
            temp_path
        ]
        
        print(f"执行命令: {' '.join(cmd)}")
        result = subprocess.run(cmd, capture_output=True, text=True)
        
        if result.returncode == 0:
            # 替换原文件
            os.replace(temp_path, video_path)
            print(f"视频时长修复成功: {video_path}")
            
            # 验证修复结果
            new_info = get_video_info(video_path)
            if new_info[0]:
                print(f"修复后视频时长: {new_info[3]:.2f}s")
            return True
        else:
            print(f"视频裁剪失败: {result.stderr}")
            if os.path.exists(temp_path):
                os.remove(temp_path)
            return False
            
    except Exception as e:
        print(f"修复视频时长时出错: {e}")
        if os.path.exists(temp_path):
            os.remove(temp_path)
        return False

def main():
    # 文件路径
    video_path = "/Users/xunan/Projects/wrmVideo/data/001/chapter_002/chapter_002_narration_02_video.mp4"
    ass_path = "/Users/xunan/Projects/wrmVideo/data/001/chapter_002/chapter_002_narration_02.ass"
    
    # 检查文件是否存在
    if not os.path.exists(video_path):
        print(f"视频文件不存在: {video_path}")
        return
    
    if not os.path.exists(ass_path):
        print(f"ASS文件不存在: {ass_path}")
        return
    
    print("开始修复 narration_02 视频时长...")
    success = fix_video_duration(video_path, ass_path)
    
    if success:
        print("\n修复完成！")
    else:
        print("\n修复失败！")

if __name__ == "__main__":
    main()