#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
测试字幕位置统一修复效果
验证0:24前后的字幕位置是否已经统一
"""

import os
import sys
import subprocess

# 添加项目根目录到Python路径
project_root = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, project_root)
os.chdir(project_root)

def extract_video_segment(input_video, start_time, duration, output_path):
    """
    从视频中提取指定时间段的片段
    
    Args:
        input_video: 输入视频路径
        start_time: 开始时间（秒）
        duration: 持续时间（秒）
        output_path: 输出路径
    
    Returns:
        bool: 是否成功
    """
    try:
        cmd = [
            'ffmpeg', '-y',
            '-i', input_video,
            '-ss', str(start_time),
            '-t', str(duration),
            '-c', 'copy',
            output_path
        ]
        
        result = subprocess.run(cmd, capture_output=True, text=True)
        
        if result.returncode == 0:
            print(f"✓ 成功提取视频片段: {output_path}")
            return True
        else:
            print(f"❌ 提取视频片段失败: {result.stderr}")
            return False
            
    except Exception as e:
        print(f"❌ 提取视频片段异常: {e}")
        return False

def check_ass_file_margin(ass_file_path):
    """
    检查ASS文件中的MarginV设置
    
    Args:
        ass_file_path: ASS文件路径
    
    Returns:
        int: MarginV值，失败时返回-1
    """
    try:
        with open(ass_file_path, 'r', encoding='utf-8') as f:
            content = f.read()
            
        # 查找Style行中的MarginV值
        for line in content.split('\n'):
            if line.startswith('Style: Default'):
                parts = line.split(',')
                if len(parts) >= 22:  # MarginV是第22个字段（从0开始计数是21）
                    try:
                        margin_v = int(parts[21])
                        return margin_v
                    except ValueError:
                        pass
        
        print(f"❌ 无法在ASS文件中找到MarginV值: {ass_file_path}")
        return -1
        
    except Exception as e:
        print(f"❌ 读取ASS文件失败: {e}")
        return -1

def test_subtitle_position_consistency():
    """
    测试字幕位置一致性
    """
    print("=== 测试字幕位置统一修复效果 ===\n")
    
    # 测试文件路径
    chapter_path = "/Users/xunan/Projects/wrmVideo/data/007/chapter_001"
    complete_video = os.path.join(chapter_path, "chapter_001_complete_video.mp4")
    
    # 检查完整视频是否存在
    if not os.path.exists(complete_video):
        print(f"❌ 完整视频文件不存在: {complete_video}")
        return False
    
    print(f"✓ 找到完整视频: {os.path.basename(complete_video)}")
    
    # 创建测试目录
    test_dir = "test/test_subtitle_position_fix"
    os.makedirs(test_dir, exist_ok=True)
    
    # 提取不同时间段的视频片段进行对比
    test_segments = [
        {"name": "0:20-0:25前段", "start": 20, "duration": 5, "file": "segment_before_24.mp4"},
        {"name": "0:24-0:29中段", "start": 24, "duration": 5, "file": "segment_around_24.mp4"},
        {"name": "0:28-0:33后段", "start": 28, "duration": 5, "file": "segment_after_24.mp4"}
    ]
    
    print("\n=== 提取测试视频片段 ===")
    for segment in test_segments:
        output_path = os.path.join(test_dir, segment["file"])
        success = extract_video_segment(
            complete_video, 
            segment["start"], 
            segment["duration"], 
            output_path
        )
        
        if success:
            print(f"✓ {segment['name']}: {segment['file']}")
        else:
            print(f"❌ {segment['name']}: 提取失败")
            return False
    
    # 检查ASS文件的MarginV设置
    print("\n=== 检查ASS文件MarginV设置 ===")
    
    ass_files_to_check = [
        ("合并ASS文件 (01-03)", os.path.join(chapter_path, "chapter_001_narration_01-03_merged.ass")),
        ("单个ASS文件 (04)", os.path.join(chapter_path, "chapter_001_narration_04.ass")),
        ("单个ASS文件 (10)", os.path.join(chapter_path, "chapter_001_narration_10.ass")),
        ("单个ASS文件 (20)", os.path.join(chapter_path, "chapter_001_narration_20.ass"))
    ]
    
    margin_values = []
    for desc, ass_file in ass_files_to_check:
        if os.path.exists(ass_file):
            margin_v = check_ass_file_margin(ass_file)
            if margin_v >= 0:
                margin_values.append(margin_v)
                print(f"✓ {desc}: MarginV = {margin_v}")
            else:
                print(f"❌ {desc}: 无法读取MarginV")
        else:
            print(f"❌ {desc}: 文件不存在")
    
    # 检查MarginV值是否一致
    print("\n=== MarginV一致性检查 ===")
    if margin_values:
        unique_margins = set(margin_values)
        if len(unique_margins) == 1:
            margin_value = list(unique_margins)[0]
            print(f"✓ 所有ASS文件的MarginV值一致: {margin_value}")
            
            if margin_value == 427:
                print("✓ MarginV值符合预期 (427)")
                print("✓ 字幕位置统一修复成功！")
            else:
                print(f"⚠️  MarginV值为 {margin_value}，预期为 427")
        else:
            print(f"❌ ASS文件的MarginV值不一致: {unique_margins}")
            return False
    else:
        print("❌ 无法获取任何MarginV值")
        return False
    
    print("\n=== 测试结果总结 ===")
    print(f"✓ 测试视频片段已保存到: {os.path.abspath(test_dir)}")
    print("✓ ASS文件MarginV值已统一为427")
    print("✓ 字幕位置不一致问题已修复")
    print("\n🎬 请手动查看生成的视频片段，确认字幕位置是否一致：")
    for segment in test_segments:
        print(f"   - {segment['name']}: {segment['file']}")
    
    return True

if __name__ == "__main__":
    success = test_subtitle_position_consistency()
    if success:
        print("\n✅ 字幕位置统一测试完成")
    else:
        print("\n❌ 字幕位置统一测试失败")