#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
修复视频合成问题的测试脚本
问题：
1. video_2没有合成进去
2. 合成的图片都很大
3. 合成的图片视频都没有上下左右的动态效果
"""

import os
import sys
import subprocess
import tempfile
import shutil

# 添加项目根目录到路径
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from gen_video import get_video_info, get_timestamps_duration

def analyze_chapter_videos(chapter_path):
    """分析章节视频文件"""
    chapter_name = os.path.basename(chapter_path)
    
    print(f"\n=== 分析 {chapter_name} 视频文件 ===")
    
    # 检查video_1和video_2
    video_1_path = os.path.join(chapter_path, f"{chapter_name}_video_1.mp4")
    video_2_path = os.path.join(chapter_path, f"{chapter_name}_video_2.mp4")
    
    if os.path.exists(video_1_path):
        width, height, fps, duration = get_video_info(video_1_path)
        print(f"video_1: {width}x{height}, {fps}fps, {duration:.2f}s")
    else:
        print("video_1: 不存在")
        
    if os.path.exists(video_2_path):
        width, height, fps, duration = get_video_info(video_2_path)
        print(f"video_2: {width}x{height}, {fps}fps, {duration:.2f}s")
    else:
        print("video_2: 不存在")
    
    # 检查timestamps文件
    timestamps_file = os.path.join(chapter_path, f"{chapter_name}_narration_01_timestamps.json")
    if os.path.exists(timestamps_file):
        duration = get_timestamps_duration(timestamps_file)
        print(f"narration_01时长: {duration:.2f}s")
    else:
        print("narration_01_timestamps.json: 不存在")
    
    # 检查最终视频
    final_video_path = os.path.join(chapter_path, f"{chapter_name}_final_video.mp4")
    if os.path.exists(final_video_path):
        width, height, fps, duration = get_video_info(final_video_path)
        print(f"final_video: {width}x{height}, {fps}fps, {duration:.2f}s")
        
        # 分析视频内容
        print("\n分析视频内容...")
        analyze_video_content(final_video_path)
    else:
        print("final_video: 不存在")

def analyze_video_content(video_path):
    """分析视频内容，检查是否包含多个片段"""
    try:
        # 使用ffprobe获取详细信息
        cmd = [
            'ffprobe', '-v', 'quiet', '-print_format', 'json',
            '-show_frames', '-select_streams', 'v:0',
            '-read_intervals', '%+#10',  # 只读取前10帧
            video_path
        ]
        result = subprocess.run(cmd, capture_output=True, text=False, check=True)
        print("视频帧分析完成")
        
        # 检查关键帧
        cmd = [
            'ffprobe', '-v', 'quiet', '-select_streams', 'v:0',
            '-show_entries', 'frame=key_frame,pkt_pts_time',
            '-of', 'csv=p=0', video_path
        ]
        result = subprocess.run(cmd, capture_output=True, text=False, check=True)
        
        key_frames = []
        for line in result.stdout.strip().split('\n')[:20]:  # 只看前20帧
            if line:
                parts = line.split(',')
                if len(parts) >= 2 and parts[0] == '1':  # 关键帧
                    key_frames.append(float(parts[1]))
        
        print(f"前20帧中的关键帧时间点: {key_frames}")
        
        # 检查是否有明显的场景切换（关键帧密集的地方）
        if len(key_frames) > 1:
            intervals = [key_frames[i+1] - key_frames[i] for i in range(len(key_frames)-1)]
            print(f"关键帧间隔: {intervals}")
            
            # 如果有很短的间隔，可能表示场景切换
            short_intervals = [i for i in intervals if i < 2.0]
            if short_intervals:
                print(f"检测到可能的场景切换点: {len(short_intervals)}个")
            else:
                print("未检测到明显的场景切换")
        
    except Exception as e:
        print(f"视频内容分析失败: {e}")

def create_improved_image_video(image_path, output_path, duration=5, width=720, height=1280, fps=30):
    """创建改进的图片视频，添加更好的动态效果和正确的缩放"""
    print(f"创建改进的图片视频: {image_path} -> {output_path}, 时长: {duration}s")
    
    try:
        # 改进的Ken Burns效果，包含多种动态效果
        effects = [
            # 缓慢放大 + 左右平移
            f"zoompan=z='min(zoom+0.001,1.3)':x='iw/2-(iw/zoom/2)+sin(t*0.1)*20':y='ih/2-(ih/zoom/2)':d=1:s={width}x{height}:fps={fps}",
            # 缓慢缩小 + 上下平移
            f"zoompan=z='max(zoom-0.001,1.0)':x='iw/2-(iw/zoom/2)':y='ih/2-(ih/zoom/2)+cos(t*0.1)*15':d=1:s={width}x{height}:fps={fps}",
            # 对角线移动
            f"zoompan=z='1.1+sin(t*0.05)*0.1':x='iw/2-(iw/zoom/2)+sin(t*0.08)*25':y='ih/2-(ih/zoom/2)+cos(t*0.08)*25':d=1:s={width}x{height}:fps={fps}",
            # 圆形运动
            f"zoompan=z='1.15':x='iw/2-(iw/zoom/2)+sin(t*0.2)*30':y='ih/2-(ih/zoom/2)+cos(t*0.2)*30':d=1:s={width}x{height}:fps={fps}"
        ]
        
        # 随机选择一种效果
        import random
        selected_effect = random.choice(effects)
        
        cmd = [
            'ffmpeg', '-y',
            '-loop', '1', '-i', image_path,
            '-t', str(duration),
            '-vf', f'scale={width}:{height}:force_original_aspect_ratio=increase,crop={width}:{height},{selected_effect}',
            '-c:v', 'libx264', '-pix_fmt', 'yuv420p', '-preset', 'medium',
            '-r', str(fps),
            output_path
        ]
        
        subprocess.run(cmd, check=True, capture_output=True)
        print(f"改进的图片视频生成成功: {output_path}")
        return True
        
    except Exception as e:
        print(f"改进的图片视频生成失败: {e}")
        return False

def test_video_concatenation():
    """测试视频拼接，确保video_1和video_2都被包含"""
    chapter_path = "/Users/xunan/Projects/wrmVideo/data/001/chapter_002"
    chapter_name = "chapter_002"
    
    video_1_path = os.path.join(chapter_path, f"{chapter_name}_video_1.mp4")
    video_2_path = os.path.join(chapter_path, f"{chapter_name}_video_2.mp4")
    
    if not os.path.exists(video_1_path) or not os.path.exists(video_2_path):
        print("video_1或video_2不存在，无法测试")
        return False
    
    # 创建测试输出目录
    test_dir = "/Users/xunan/Projects/wrmVideo/test/video_test_output"
    os.makedirs(test_dir, exist_ok=True)
    
    # 测试拼接video_1和video_2
    test_output = os.path.join(test_dir, "test_concatenated.mp4")
    
    try:
        # 创建文件列表
        filelist_path = os.path.join(test_dir, "filelist.txt")
        with open(filelist_path, 'w') as f:
            f.write(f"file '{os.path.abspath(video_1_path)}'\n")
            f.write(f"file '{os.path.abspath(video_2_path)}'\n")
        
        # 拼接视频
        cmd = [
            'ffmpeg', '-y', '-f', 'concat', '-safe', '0', '-i', filelist_path,
            '-c', 'copy', test_output
        ]
        
        subprocess.run(cmd, check=True, capture_output=True)
        
        # 检查输出视频
        width, height, fps, duration = get_video_info(test_output)
        print(f"测试拼接成功: {width}x{height}, {fps}fps, {duration:.2f}s")
        
        return True
        
    except Exception as e:
        print(f"测试拼接失败: {e}")
        return False

def main():
    """主函数"""
    chapter_path = "/Users/xunan/Projects/wrmVideo/data/001/chapter_002"
    
    print("=== 视频问题诊断工具 ===")
    
    # 1. 分析现有视频文件
    analyze_chapter_videos(chapter_path)
    
    # 2. 测试视频拼接
    print("\n=== 测试视频拼接 ===")
    test_video_concatenation()
    
    # 3. 测试改进的图片视频生成
    print("\n=== 测试改进的图片视频生成 ===")
    test_image_path = os.path.join(chapter_path, "chapter_002_image_01_3.jpeg")
    if os.path.exists(test_image_path):
        test_dir = "/Users/xunan/Projects/wrmVideo/test/video_test_output"
        os.makedirs(test_dir, exist_ok=True)
        test_output = os.path.join(test_dir, "test_improved_image_video.mp4")
        
        if create_improved_image_video(test_image_path, test_output, duration=10):
            width, height, fps, duration = get_video_info(test_output)
            print(f"改进的图片视频: {width}x{height}, {fps}fps, {duration:.2f}s")
    else:
        print(f"测试图片不存在: {test_image_path}")

if __name__ == "__main__":
    main()