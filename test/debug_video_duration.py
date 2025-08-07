#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
视频时长问题调试脚本
用于分析concat_finish_video.py中视频时长异常的根本原因
"""

import os
import subprocess
import sys

def get_video_duration(video_path):
    """获取视频时长"""
    try:
        result = subprocess.run([
            'ffprobe', '-v', 'quiet', '-show_entries', 'format=duration',
            '-of', 'csv=p=0', video_path
        ], capture_output=True, text=True)
        if result.returncode == 0:
            return float(result.stdout.strip())
        return None
    except Exception as e:
        print(f"获取视频时长失败: {e}")
        return None

def test_simple_concat(chapter_dir):
    """测试简单的视频拼接，不添加BGM"""
    print(f"\n=== 测试章节 {os.path.basename(chapter_dir)} 的简单拼接 ===")
    
    # 收集narration视频
    chapter_name = os.path.basename(chapter_dir)
    video_files = []
    for f in os.listdir(chapter_dir):
        if f.startswith(f'{chapter_name}_narration_') and f.endswith('_video.mp4'):
            video_files.append(os.path.join(chapter_dir, f))
    
    video_files.sort()
    print(f"找到 {len(video_files)} 个narration视频")
    
    # 计算总时长
    total_duration = 0
    for video_file in video_files:
        duration = get_video_duration(video_file)
        if duration:
            total_duration += duration
            print(f"  {os.path.basename(video_file)}: {duration:.2f}s")
    
    print(f"Narration视频总时长: {total_duration:.2f}s")
    
    # 创建拼接列表
    concat_list_path = os.path.join(chapter_dir, "debug_concat_list.txt")
    with open(concat_list_path, 'w', encoding='utf-8') as f:
        for video_file in video_files:
            f.write(f"file '{os.path.abspath(video_file)}'\n")
    
    # 执行简单拼接（只拼接视频，不添加BGM）
    simple_output = os.path.join(chapter_dir, f"{chapter_name}_debug_simple.mp4")
    cmd = [
        "ffmpeg", "-y",
        "-f", "concat",
        "-safe", "0",
        "-i", concat_list_path,
        "-c", "copy",
        simple_output
    ]
    
    print(f"执行简单拼接: {' '.join(cmd)}")
    result = subprocess.run(cmd, capture_output=True, text=True)
    
    if result.returncode == 0:
        simple_duration = get_video_duration(simple_output)
        print(f"简单拼接结果时长: {simple_duration:.2f}s")
        print(f"时长差异: {simple_duration - total_duration:.2f}s")
        return simple_output, simple_duration
    else:
        print(f"简单拼接失败: {result.stderr}")
        return None, None

def test_finish_concat(simple_video_path, chapter_dir):
    """测试添加finish.mp4的拼接"""
    print(f"\n=== 测试添加finish.mp4 ===")
    
    chapter_name = os.path.basename(chapter_dir)
    finish_video_path = "/Users/xunan/Projects/wrmVideo/src/banner/finish.mp4"
    
    # 获取finish.mp4时长
    finish_duration = get_video_duration(finish_video_path)
    simple_duration = get_video_duration(simple_video_path)
    
    print(f"简单拼接视频时长: {simple_duration:.2f}s")
    print(f"finish.mp4时长: {finish_duration:.2f}s")
    print(f"预期总时长: {simple_duration + finish_duration:.2f}s")
    
    # 创建最终拼接列表
    final_concat_list = os.path.join(chapter_dir, "debug_final_concat_list.txt")
    with open(final_concat_list, 'w', encoding='utf-8') as f:
        f.write(f"file '{os.path.abspath(simple_video_path)}'\n")
        f.write(f"file '{os.path.abspath(finish_video_path)}'\n")
    
    # 测试流复制拼接
    final_output_copy = os.path.join(chapter_dir, f"{chapter_name}_debug_final_copy.mp4")
    cmd_copy = [
        "ffmpeg", "-y",
        "-f", "concat",
        "-safe", "0",
        "-i", final_concat_list,
        "-c", "copy",
        "-avoid_negative_ts", "make_zero",
        final_output_copy
    ]
    
    print(f"执行流复制拼接: {' '.join(cmd_copy)}")
    result_copy = subprocess.run(cmd_copy, capture_output=True, text=True)
    
    if result_copy.returncode == 0:
        final_duration_copy = get_video_duration(final_output_copy)
        print(f"流复制拼接结果时长: {final_duration_copy:.2f}s")
        print(f"与预期差异: {final_duration_copy - (simple_duration + finish_duration):.2f}s")
    else:
        print(f"流复制拼接失败: {result_copy.stderr}")
    
    # 测试重新编码拼接
    final_output_encode = os.path.join(chapter_dir, f"{chapter_name}_debug_final_encode.mp4")
    cmd_encode = [
        "ffmpeg", "-y",
        "-f", "concat",
        "-safe", "0",
        "-i", final_concat_list,
        "-c:v", "libx264",
        "-c:a", "aac",
        "-b:a", "128k",
        final_output_encode
    ]
    
    print(f"执行重新编码拼接: {' '.join(cmd_encode)}")
    result_encode = subprocess.run(cmd_encode, capture_output=True, text=True)
    
    if result_encode.returncode == 0:
        final_duration_encode = get_video_duration(final_output_encode)
        print(f"重新编码拼接结果时长: {final_duration_encode:.2f}s")
        print(f"与预期差异: {final_duration_encode - (simple_duration + finish_duration):.2f}s")
    else:
        print(f"重新编码拼接失败: {result_encode.stderr}")

def main():
    if len(sys.argv) != 2:
        print("使用方法: python debug_video_duration.py data/001/chapter_001")
        sys.exit(1)
    
    chapter_dir = sys.argv[1]
    if not os.path.exists(chapter_dir):
        print(f"错误: 章节目录不存在: {chapter_dir}")
        sys.exit(1)
    
    print(f"开始调试章节: {chapter_dir}")
    
    # 测试简单拼接
    simple_video, simple_duration = test_simple_concat(chapter_dir)
    
    if simple_video and simple_duration:
        # 测试添加finish.mp4
        test_finish_concat(simple_video, chapter_dir)
    
    print("\n调试完成")

if __name__ == "__main__":
    main()