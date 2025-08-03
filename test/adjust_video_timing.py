#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
视频时长调整脚本
调整视频时长以匹配字幕时间轴
"""

import ffmpeg
import os
import sys
import re

def parse_ass_time(time_str):
    """解析ASS时间格式 (H:MM:SS.CC) 为秒数"""
    try:
        # 格式: H:MM:SS.CC
        parts = time_str.split(':')
        hours = int(parts[0])
        minutes = int(parts[1])
        seconds_parts = parts[2].split('.')
        seconds = int(seconds_parts[0])
        centiseconds = int(seconds_parts[1])
        
        total_seconds = hours * 3600 + minutes * 60 + seconds + centiseconds / 100.0
        return total_seconds
    except Exception as e:
        print(f"解析时间格式失败: {time_str}, 错误: {e}")
        return 0

def get_ass_duration(ass_path):
    """获取ASS字幕文件的总时长"""
    try:
        with open(ass_path, 'r', encoding='utf-8') as f:
            lines = f.readlines()
        
        max_end_time = 0
        for line in lines:
            line = line.strip()
            if line.startswith('Dialogue:'):
                # 格式: Dialogue: Layer,Start,End,Style,Name,MarginL,MarginR,MarginV,Effect,Text
                parts = line.split(',')
                if len(parts) >= 3:
                    end_time_str = parts[2].strip()
                    end_time = parse_ass_time(end_time_str)
                    max_end_time = max(max_end_time, end_time)
        
        return max_end_time
    except Exception as e:
        print(f"读取ASS文件失败: {e}")
        return 0

def get_video_duration(video_path):
    """获取视频时长"""
    try:
        probe = ffmpeg.probe(video_path)
        duration = float(probe['format']['duration'])
        return duration
    except Exception as e:
        print(f"获取视频时长失败: {e}")
        return 0

def adjust_video_speed(input_video, output_video, target_duration):
    """通过调整播放速度来匹配目标时长"""
    try:
        # 获取原视频时长
        original_duration = get_video_duration(input_video)
        if original_duration <= 0:
            print("无法获取原视频时长")
            return False
        
        # 计算速度调整比例
        speed_ratio = original_duration / target_duration
        print(f"原视频时长: {original_duration:.2f}s")
        print(f"目标时长: {target_duration:.2f}s")
        print(f"速度调整比例: {speed_ratio:.4f}")
        
        # 检查速度调整比例是否在合理范围内
        if speed_ratio > 2.0 or speed_ratio < 0.5:
            print(f"警告: 速度调整比例 {speed_ratio:.4f} 可能导致音视频质量问题")
        
        # 使用ffmpeg调整视频和音频速度
        input_stream = ffmpeg.input(input_video)
        
        # 分别处理视频和音频流
        video_stream = input_stream.video.filter('setpts', f'{1/speed_ratio}*PTS')
        audio_stream = input_stream.audio.filter('atempo', speed_ratio)
        
        # 合并视频和音频流
        (
            ffmpeg
            .output(video_stream, audio_stream, output_video, vcodec='libx264', acodec='aac')
            .overwrite_output()
            .run()
        )
        
        # 验证调整后的时长
        new_duration = get_video_duration(output_video)
        print(f"调整后视频时长: {new_duration:.2f}s")
        print(f"时长差异: {abs(new_duration - target_duration):.2f}s")
        
        return True
        
    except Exception as e:
        print(f"调整视频速度失败: {e}")
        return False

def trim_video_to_duration(input_video, output_video, target_duration):
    """裁剪视频到指定时长"""
    try:
        # 获取原视频时长
        original_duration = get_video_duration(input_video)
        if original_duration <= 0:
            print("无法获取原视频时长")
            return False
        
        print(f"原视频时长: {original_duration:.2f}s")
        print(f"目标时长: {target_duration:.2f}s")
        
        if target_duration >= original_duration:
            print("目标时长大于或等于原视频时长，无需裁剪")
            # 直接复制文件
            import shutil
            shutil.copy2(input_video, output_video)
            return True
        
        # 裁剪视频到目标时长
        (
            ffmpeg
            .input(input_video)
            .output(output_video, t=target_duration, vcodec='libx264', acodec='aac')
            .overwrite_output()
            .run()
        )
        
        # 验证裁剪后的时长
        new_duration = get_video_duration(output_video)
        print(f"裁剪后视频时长: {new_duration:.2f}s")
        print(f"时长差异: {abs(new_duration - target_duration):.2f}s")
        
        return True
        
    except Exception as e:
        print(f"裁剪视频失败: {e}")
        return False

def adjust_video_to_subtitle_timing(video_path, subtitle_path, output_path, method='speed'):
    """调整视频时长以匹配字幕时间轴
    
    Args:
        video_path: 输入视频路径
        subtitle_path: 字幕文件路径
        output_path: 输出视频路径
        method: 调整方法 ('speed' 或 'trim')
    """
    print(f"开始调整视频时长以匹配字幕...")
    print(f"输入视频: {video_path}")
    print(f"字幕文件: {subtitle_path}")
    print(f"输出视频: {output_path}")
    print(f"调整方法: {method}")
    
    # 检查文件是否存在
    if not os.path.exists(video_path):
        print(f"视频文件不存在: {video_path}")
        return False
    
    if not os.path.exists(subtitle_path):
        print(f"字幕文件不存在: {subtitle_path}")
        return False
    
    # 获取字幕时长
    subtitle_duration = get_ass_duration(subtitle_path)
    if subtitle_duration <= 0:
        print("无法获取字幕时长")
        return False
    
    print(f"字幕总时长: {subtitle_duration:.2f}s")
    
    # 根据方法调整视频
    if method == 'speed':
        return adjust_video_speed(video_path, output_path, subtitle_duration)
    elif method == 'trim':
        return trim_video_to_duration(video_path, output_path, subtitle_duration)
    else:
        print(f"不支持的调整方法: {method}")
        return False

def main():
    if len(sys.argv) < 4:
        print("用法: python adjust_video_timing.py <视频文件> <字幕文件> <输出文件> [方法]")
        print("方法: speed (调整速度) 或 trim (裁剪视频)，默认为 speed")
        sys.exit(1)
    
    video_path = sys.argv[1]
    subtitle_path = sys.argv[2]
    output_path = sys.argv[3]
    method = sys.argv[4] if len(sys.argv) > 4 else 'speed'
    
    success = adjust_video_to_subtitle_timing(video_path, subtitle_path, output_path, method)
    
    if success:
        print(f"\n✓ 视频时长调整成功!")
        print(f"输出文件: {output_path}")
    else:
        print(f"\n❌ 视频时长调整失败!")
        sys.exit(1)

if __name__ == "__main__":
    main()