#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
视频字幕同步验证脚本
验证视频时长与字幕时间轴是否匹配
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
        dialogue_count = 0
        for line in lines:
            line = line.strip()
            if line.startswith('Dialogue:'):
                dialogue_count += 1
                # 格式: Dialogue: Layer,Start,End,Style,Name,MarginL,MarginR,MarginV,Effect,Text
                parts = line.split(',')
                if len(parts) >= 3:
                    end_time_str = parts[2].strip()
                    end_time = parse_ass_time(end_time_str)
                    max_end_time = max(max_end_time, end_time)
        
        return max_end_time, dialogue_count
    except Exception as e:
        print(f"读取ASS文件失败: {e}")
        return 0, 0

def get_video_duration(video_path):
    """获取视频时长"""
    try:
        probe = ffmpeg.probe(video_path)
        duration = float(probe['format']['duration'])
        return duration
    except Exception as e:
        print(f"获取视频时长失败: {e}")
        return 0

def get_video_info(video_path):
    """获取视频详细信息"""
    try:
        probe = ffmpeg.probe(video_path)
        video_stream = next((stream for stream in probe['streams'] if stream['codec_type'] == 'video'), None)
        audio_stream = next((stream for stream in probe['streams'] if stream['codec_type'] == 'audio'), None)
        
        if video_stream is None:
            raise ValueError("找不到视频流")
        
        width = int(video_stream['width'])
        height = int(video_stream['height'])
        
        # 解析帧率
        r_frame_rate = video_stream['r_frame_rate']
        fps_num, fps_den = map(int, r_frame_rate.split('/'))
        fps = fps_num / fps_den
        
        # 获取时长
        duration = float(probe['format']['duration'])
        
        # 获取文件大小
        file_size = os.path.getsize(video_path) / (1024 * 1024)  # MB
        
        # 音频信息
        audio_info = None
        if audio_stream:
            audio_info = {
                'codec': audio_stream.get('codec_name', 'unknown'),
                'sample_rate': audio_stream.get('sample_rate', 'unknown'),
                'channels': audio_stream.get('channels', 'unknown')
            }
        
        return {
            'width': width,
            'height': height,
            'fps': fps,
            'duration': duration,
            'file_size_mb': file_size,
            'video_codec': video_stream.get('codec_name', 'unknown'),
            'audio_info': audio_info
        }
    except Exception as e:
        print(f"获取视频信息失败: {e}")
        return None

def verify_sync(video_path, subtitle_path):
    """验证视频和字幕的同步情况"""
    print(f"=== 视频字幕同步验证 ===")
    print(f"视频文件: {video_path}")
    print(f"字幕文件: {subtitle_path}")
    print()
    
    # 检查文件是否存在
    if not os.path.exists(video_path):
        print(f"❌ 视频文件不存在: {video_path}")
        return False
    
    if not os.path.exists(subtitle_path):
        print(f"❌ 字幕文件不存在: {subtitle_path}")
        return False
    
    # 获取视频信息
    video_info = get_video_info(video_path)
    if video_info is None:
        print("❌ 无法获取视频信息")
        return False
    
    # 获取字幕信息
    subtitle_duration, dialogue_count = get_ass_duration(subtitle_path)
    if subtitle_duration <= 0:
        print("❌ 无法获取字幕时长")
        return False
    
    # 显示详细信息
    print(f"📹 视频信息:")
    print(f"   时长: {video_info['duration']:.3f}s ({video_info['duration']//60:.0f}分{video_info['duration']%60:.1f}秒)")
    print(f"   分辨率: {video_info['width']}x{video_info['height']}px")
    print(f"   帧率: {video_info['fps']:.2f}fps")
    print(f"   文件大小: {video_info['file_size_mb']:.2f}MB")
    print(f"   视频编码: {video_info['video_codec']}")
    if video_info['audio_info']:
        audio = video_info['audio_info']
        print(f"   音频编码: {audio['codec']}, {audio['sample_rate']}Hz, {audio['channels']}声道")
    else:
        print(f"   音频: 无音频流")
    print()
    
    print(f"📝 字幕信息:")
    print(f"   时长: {subtitle_duration:.3f}s ({subtitle_duration//60:.0f}分{subtitle_duration%60:.1f}秒)")
    print(f"   对话行数: {dialogue_count}")
    print()
    
    # 计算时间差异
    time_diff = abs(video_info['duration'] - subtitle_duration)
    time_diff_percent = (time_diff / max(video_info['duration'], subtitle_duration)) * 100
    
    print(f"⏱️  同步分析:")
    print(f"   时间差异: {time_diff:.3f}s ({time_diff_percent:.2f}%)")
    
    # 判断同步状态
    if time_diff <= 0.1:
        sync_status = "✅ 完美同步"
        sync_quality = "excellent"
    elif time_diff <= 0.5:
        sync_status = "✅ 良好同步"
        sync_quality = "good"
    elif time_diff <= 2.0:
        sync_status = "⚠️  可接受同步"
        sync_quality = "acceptable"
    elif time_diff <= 5.0:
        sync_status = "⚠️  同步偏差较大"
        sync_quality = "poor"
    else:
        sync_status = "❌ 严重不同步"
        sync_quality = "bad"
    
    print(f"   同步状态: {sync_status}")
    print()
    
    # 提供建议
    if sync_quality in ['excellent', 'good']:
        print(f"🎉 视频和字幕时间轴匹配良好，可以正常使用！")
    elif sync_quality == 'acceptable':
        print(f"💡 建议: 时间差异在可接受范围内，但可以考虑进一步优化。")
    elif sync_quality == 'poor':
        print(f"⚠️  警告: 时间差异较大，建议重新调整视频时长。")
        print(f"   可以使用 adjust_video_timing.py 脚本进行调整。")
    else:
        print(f"❌ 错误: 时间差异过大，必须重新调整视频时长。")
        print(f"   请使用 adjust_video_timing.py 脚本进行调整。")
    
    return sync_quality in ['excellent', 'good', 'acceptable']

def main():
    if len(sys.argv) < 3:
        print("用法: python verify_video_subtitle_sync.py <视频文件> <字幕文件>")
        sys.exit(1)
    
    video_path = sys.argv[1]
    subtitle_path = sys.argv[2]
    
    success = verify_sync(video_path, subtitle_path)
    
    if success:
        print(f"\n✅ 验证通过: 视频和字幕同步良好")
        sys.exit(0)
    else:
        print(f"\n❌ 验证失败: 视频和字幕同步存在问题")
        sys.exit(1)

if __name__ == "__main__":
    main()