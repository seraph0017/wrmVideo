#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
测试音频截断问题修复效果

验证concat_narration_video.py中的音频时长修复是否生效：
1. 检查合并的MP3和ASS文件时长差异
2. 验证生成的视频是否使用音频时长
3. 确认音频内容完整性
"""

import os
import sys
import subprocess

# 添加项目根目录到Python路径
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from concat_narration_video import get_audio_duration, get_ass_duration

def get_video_duration(video_path):
    """
    获取视频文件时长
    
    Args:
        video_path: 视频文件路径
    
    Returns:
        float: 视频时长（秒），失败时返回0
    """
    try:
        result = subprocess.run([
            'ffprobe', '-v', 'quiet', '-show_entries', 'format=duration',
            '-of', 'csv=p=0', video_path
        ], capture_output=True, text=True, check=True)
        return float(result.stdout.strip())
    except Exception as e:
        print(f"获取视频时长失败: {e}")
        return 0

def test_audio_duration_fix():
    """
    测试音频截断问题修复效果
    """
    print("=== 测试音频截断问题修复效果 ===")
    
    # 测试文件路径
    chapter_path = "/Users/xunan/Projects/wrmVideo/data/007/chapter_001"
    chapter_name = "chapter_001"
    
    # 合并文件路径
    merged_mp3 = os.path.join(chapter_path, f"{chapter_name}_narration_01-03_merged.mp3")
    merged_ass = os.path.join(chapter_path, f"{chapter_name}_narration_01-03_merged.ass")
    merged_video = os.path.join(chapter_path, f"{chapter_name}_narration_01-03_video.mp4")
    
    # 检查文件是否存在
    files_to_check = [
        ("合并MP3文件", merged_mp3),
        ("合并ASS文件", merged_ass),
        ("合并视频文件", merged_video)
    ]
    
    for file_desc, file_path in files_to_check:
        if not os.path.exists(file_path):
            print(f"❌ {file_desc}不存在: {file_path}")
            return False
        else:
            print(f"✓ {file_desc}存在: {os.path.basename(file_path)}")
    
    print("\n=== 时长对比分析 ===")
    
    # 获取各文件时长
    mp3_duration = get_audio_duration(merged_mp3)
    ass_duration = get_ass_duration(merged_ass)
    video_duration = get_video_duration(merged_video)
    
    print(f"MP3音频时长: {mp3_duration:.3f}秒")
    print(f"ASS字幕时长: {ass_duration:.3f}秒")
    print(f"生成视频时长: {video_duration:.3f}秒")
    
    # 计算时长差异
    mp3_ass_diff = mp3_duration - ass_duration
    video_mp3_diff = abs(video_duration - mp3_duration)
    video_ass_diff = abs(video_duration - ass_duration)
    
    print(f"\n=== 时长差异分析 ===")
    print(f"MP3与ASS时长差异: {mp3_ass_diff:.3f}秒")
    print(f"视频与MP3时长差异: {video_mp3_diff:.3f}秒")
    print(f"视频与ASS时长差异: {video_ass_diff:.3f}秒")
    
    # 验证修复效果
    print(f"\n=== 修复效果验证 ===")
    
    # 检查是否使用音频时长
    if video_mp3_diff < 0.1:  # 允许0.1秒的误差
        print("✓ 视频时长与音频时长一致，修复成功")
        success = True
    else:
        print("❌ 视频时长与音频时长不一致，修复失败")
        success = False
    
    # 检查音频是否被截断
    if mp3_ass_diff > 0.5:  # ASS比MP3短超过0.5秒
        if video_duration > ass_duration:
            print("✓ 视频时长超过ASS时长，音频未被截断")
        else:
            print("❌ 视频时长等于ASS时长，音频可能被截断")
            success = False
    else:
        print("ℹ️  MP3与ASS时长差异较小，无截断风险")
    
    # 检查具体的时长改进
    expected_old_duration = ass_duration  # 修复前应该是ASS时长
    actual_new_duration = video_duration  # 修复后的实际时长
    improvement = actual_new_duration - expected_old_duration
    
    if improvement > 0.5:
        print(f"✓ 时长改进: +{improvement:.3f}秒，音频完整性得到保障")
    else:
        print(f"ℹ️  时长改进: +{improvement:.3f}秒")
    
    return success

def test_individual_narration():
    """
    测试单个narration的音频时长修复
    """
    print("\n=== 测试单个narration音频时长修复 ===")
    
    # 测试narration_04（第一个正常的narration）
    chapter_path = "/Users/xunan/Projects/wrmVideo/data/007/chapter_001"
    chapter_name = "chapter_001"
    narration_num = "04"
    
    mp3_file = os.path.join(chapter_path, f"{chapter_name}_narration_{narration_num}.mp3")
    ass_file = os.path.join(chapter_path, f"{chapter_name}_narration_{narration_num}.ass")
    video_file = os.path.join(chapter_path, f"{chapter_name}_narration_{narration_num}_video.mp4")
    
    if not all(os.path.exists(f) for f in [mp3_file, ass_file, video_file]):
        print(f"❌ narration_{narration_num}的某些文件不存在，跳过测试")
        return True
    
    mp3_duration = get_audio_duration(mp3_file)
    ass_duration = get_ass_duration(ass_file)
    video_duration = get_video_duration(video_file)
    
    print(f"narration_{narration_num}:")
    print(f"  MP3时长: {mp3_duration:.3f}秒")
    print(f"  ASS时长: {ass_duration:.3f}秒")
    print(f"  视频时长: {video_duration:.3f}秒")
    
    # 验证是否使用音频时长
    if abs(video_duration - mp3_duration) < 0.1:
        print(f"  ✓ 使用音频时长，修复生效")
        return True
    else:
        print(f"  ❌ 未使用音频时长，修复失败")
        return False

def main():
    """
    主测试函数
    """
    print("音频截断问题修复测试")
    print("=" * 50)
    
    # 测试合并视频的修复效果
    test1_success = test_audio_duration_fix()
    
    # 测试单个narration的修复效果
    test2_success = test_individual_narration()
    
    print("\n=== 测试结果总结 ===")
    if test1_success and test2_success:
        print("✅ 所有测试通过，音频截断问题修复成功！")
        return 0
    else:
        print("❌ 部分测试失败，音频截断问题可能未完全修复")
        return 1

if __name__ == "__main__":
    sys.exit(main())