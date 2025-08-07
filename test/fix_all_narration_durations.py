#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
批量修复所有narration视频的时长问题
确保所有视频时长与对应的ASS字幕文件匹配
"""

import os
import sys
import glob
import subprocess

# 添加项目根目录到路径
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from gen_video import get_ass_duration, get_video_info

def fix_video_duration(video_path, ass_path, tolerance=0.5):
    """
    修复单个视频的时长
    
    Args:
        video_path: 视频文件路径
        ass_path: ASS字幕文件路径
        tolerance: 时长差异容忍度（秒）
    
    Returns:
        bool: 是否成功修复
    """
    # 获取ASS字幕时长
    ass_duration = get_ass_duration(ass_path)
    if ass_duration <= 0:
        print(f"  ❌ 无法获取ASS字幕时长: {ass_path}")
        return False
    
    # 获取当前视频时长
    video_info = get_video_info(video_path)
    if not video_info[0]:
        print(f"  ❌ 无法获取视频信息: {video_path}")
        return False
    
    current_duration = video_info[3]
    duration_diff = abs(current_duration - ass_duration)
    
    print(f"  📹 当前视频时长: {current_duration:.2f}s")
    print(f"  📝 ASS字幕时长: {ass_duration:.2f}s")
    print(f"  📊 时长差异: {duration_diff:.2f}s")
    
    if duration_diff <= tolerance:
        print(f"  ✅ 视频时长正确，无需修复")
        return True
    
    # 创建备份
    backup_path = video_path + ".backup"
    if not os.path.exists(backup_path):
        import shutil
        shutil.copy2(video_path, backup_path)
        print(f"  💾 已创建备份: {os.path.basename(backup_path)}")
    
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
        
        print(f"  🔧 正在修复视频时长...")
        result = subprocess.run(cmd, capture_output=True, text=True)
        
        if result.returncode == 0:
            # 替换原文件
            os.replace(temp_path, video_path)
            
            # 验证修复结果
            new_info = get_video_info(video_path)
            if new_info[0]:
                new_duration = new_info[3]
                print(f"  ✅ 修复成功！新时长: {new_duration:.2f}s")
                return True
            else:
                print(f"  ❌ 修复后无法获取视频信息")
                return False
        else:
            print(f"  ❌ 视频裁剪失败: {result.stderr}")
            if os.path.exists(temp_path):
                os.remove(temp_path)
            return False
            
    except Exception as e:
        print(f"  ❌ 修复视频时长时出错: {e}")
        if os.path.exists(temp_path):
            os.remove(temp_path)
        return False

def find_narration_videos(chapter_dir):
    """
    查找章节目录下的所有narration视频文件
    
    Args:
        chapter_dir: 章节目录路径
    
    Returns:
        list: (video_path, ass_path) 元组列表
    """
    video_files = []
    
    # 查找所有narration视频文件
    pattern = os.path.join(chapter_dir, "*_narration_*_video.mp4")
    for video_path in glob.glob(pattern):
        # 构造对应的ASS文件路径
        video_name = os.path.basename(video_path)
        ass_name = video_name.replace("_video.mp4", ".ass")
        ass_path = os.path.join(chapter_dir, ass_name)
        
        if os.path.exists(ass_path):
            video_files.append((video_path, ass_path))
        else:
            print(f"⚠️  找不到对应的ASS文件: {ass_path}")
    
    return video_files

def main():
    """
    主函数：批量修复所有narration视频的时长
    """
    # 可以指定特定章节目录，或者扫描所有章节
    import argparse
    
    parser = argparse.ArgumentParser(description='批量修复narration视频时长')
    parser.add_argument('chapter_dir', nargs='?', 
                       default='/Users/xunan/Projects/wrmVideo/data/001/chapter_002',
                       help='章节目录路径')
    parser.add_argument('--tolerance', type=float, default=0.5,
                       help='时长差异容忍度（秒），默认0.5秒')
    
    args = parser.parse_args()
    
    chapter_dir = args.chapter_dir
    tolerance = args.tolerance
    
    if not os.path.exists(chapter_dir):
        print(f"❌ 章节目录不存在: {chapter_dir}")
        return
    
    print(f"🔍 扫描章节目录: {chapter_dir}")
    print(f"📏 时长差异容忍度: {tolerance}秒")
    print("=" * 60)
    
    # 查找所有narration视频文件
    video_files = find_narration_videos(chapter_dir)
    
    if not video_files:
        print("❌ 没有找到任何narration视频文件")
        return
    
    print(f"📹 找到 {len(video_files)} 个narration视频文件")
    print("=" * 60)
    
    # 逐个修复视频
    success_count = 0
    for i, (video_path, ass_path) in enumerate(video_files, 1):
        video_name = os.path.basename(video_path)
        print(f"\n[{i}/{len(video_files)}] 处理: {video_name}")
        
        if fix_video_duration(video_path, ass_path, tolerance):
            success_count += 1
    
    print("\n" + "=" * 60)
    print(f"🎉 修复完成！成功修复 {success_count}/{len(video_files)} 个视频")
    
    if success_count < len(video_files):
        print(f"⚠️  有 {len(video_files) - success_count} 个视频修复失败，请检查日志")

if __name__ == "__main__":
    main()