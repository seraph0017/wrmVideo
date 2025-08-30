#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
旁白视频合成脚本
根据ASS字幕文件和图片生成带有动态效果的旁白视频

新的逻辑：
- narration_01-03: 合并ASS文件，前10秒用first_video，后面时间用image_01-03平均分配
- narration_04-30: 正常合成，1个MP3对应1个ASS对应1个图片
- 30个图片重命名为chapter_xxx_image_01到chapter_xxx_image_30
- 保持转场和其他特效逻辑不变
"""

import os
import sys
import re
import json
import ffmpeg
import argparse
import glob
import random
import subprocess
from pathlib import Path

def check_macos_videotoolbox():
    """检测macOS系统是否支持VideoToolbox硬件编码器"""
    try:
        import platform
        if platform.system() != 'Darwin':
            return False, None
        
        # 测试h264_videotoolbox编码器
        test_cmd_h264 = [
            'ffmpeg', '-f', 'lavfi', '-i', 'testsrc=duration=1:size=320x240:rate=1',
            '-c:v', 'h264_videotoolbox', '-f', 'null', '-'
        ]
        result_h264 = subprocess.run(test_cmd_h264, capture_output=True, text=False, timeout=15)
        h264_available = result_h264.returncode == 0
        
        # 测试hevc_videotoolbox编码器
        test_cmd_hevc = [
            'ffmpeg', '-f', 'lavfi', '-i', 'testsrc=duration=1:size=320x240:rate=1',
            '-c:v', 'hevc_videotoolbox', '-f', 'null', '-'
        ]
        result_hevc = subprocess.run(test_cmd_hevc, capture_output=True, text=False, timeout=15)
        hevc_available = result_hevc.returncode == 0
        
        if h264_available or hevc_available:
            print("✓ 检测到macOS VideoToolbox硬件编码器")
            if h264_available:
                print("  - h264_videotoolbox 可用")
            if hevc_available:
                print("  - hevc_videotoolbox 可用")
            return True, {'h264': h264_available, 'hevc': hevc_available}
        else:
            print("⚠️  VideoToolbox编码器不可用，使用CPU编码")
            return False, None
            
    except (subprocess.TimeoutExpired, FileNotFoundError, Exception) as e:
        print(f"⚠️  VideoToolbox检测失败，使用CPU编码: {e}")
        return False, None

def check_nvidia_gpu():
    """检测系统是否有NVIDIA GPU和nvenc编码器可用 - 支持Docker环境"""
    try:
        # 方法1: 检测nvidia-smi (传统方式)
        try:
            result = subprocess.run(['nvidia-smi'], capture_output=True, text=False, timeout=10)
            nvidia_smi_available = (result.returncode == 0)
        except (FileNotFoundError, subprocess.TimeoutExpired):
            nvidia_smi_available = False
        
        # 方法2: 检查Docker中的NVIDIA运行时 (检查/proc/driver/nvidia/version)
        nvidia_proc_available = os.path.exists('/proc/driver/nvidia/version')
        
        # 方法3: 检查Docker环境变量
        nvidia_visible_devices = os.environ.get('NVIDIA_VISIBLE_DEVICES')
        cuda_visible_devices = os.environ.get('CUDA_VISIBLE_DEVICES')
        docker_nvidia_available = (
            nvidia_visible_devices and nvidia_visible_devices != 'void' or
            cuda_visible_devices and cuda_visible_devices != ''
        )
        
        # 如果任何一种方式检测到GPU，则继续测试nvenc
        if not (nvidia_smi_available or nvidia_proc_available or docker_nvidia_available):
            print("⚠️  未检测到NVIDIA GPU或驱动，使用CPU编码")
            return False
        
        print("✓ 检测到NVIDIA GPU环境")
        if docker_nvidia_available:
            print("  - Docker NVIDIA运行时环境")
        if nvidia_proc_available:
            print("  - NVIDIA驱动已加载")
        if nvidia_smi_available:
            print("  - nvidia-smi可用")
        
        # 检测nvenc编码器是否可用
        # 使用一个简单的测试命令来验证h264_nvenc是否工作
        test_cmd = [
            'ffmpeg', '-f', 'lavfi', '-i', 'testsrc=duration=1:size=320x240:rate=1',
            '-c:v', 'h264_nvenc', '-f', 'null', '-'
        ]
        result = subprocess.run(test_cmd, capture_output=True, text=False, timeout=15)
        
        if result.returncode == 0:
            print("✓ NVENC编码器测试成功，将使用硬件加速")
            return True
        else:
            # 安全地解码stderr，忽略无法解码的字符
            try:
                stderr_text = result.stderr.decode('utf-8', errors='ignore')
            except:
                stderr_text = str(result.stderr)
            print(f"⚠️  nvenc编码器不可用，使用CPU编码: {stderr_text}")
            return False
            
    except (subprocess.TimeoutExpired, FileNotFoundError, Exception) as e:
        print(f"⚠️  GPU检测失败，使用CPU编码: {e}")
        return False

def get_ffmpeg_gpu_params():
    """获取FFmpeg GPU优化参数 - 支持L4 GPU优化配置和macOS VideoToolbox"""
    # 首先检测macOS VideoToolbox
    videotoolbox_available, videotoolbox_info = check_macos_videotoolbox()
    if videotoolbox_available:
        # 优先使用h264_videotoolbox，如果不可用则使用hevc_videotoolbox
        if videotoolbox_info['h264']:
            return {
                'video_codec': 'h264_videotoolbox',
                'extra_params': [
                    '-allow_sw', '1',      # 允许软件回退
                    '-realtime', '1'       # 实时编码
                ]
            }
        elif videotoolbox_info['hevc']:
            return {
                'video_codec': 'hevc_videotoolbox',
                'extra_params': [
                    '-allow_sw', '1',      # 允许软件回退
                    '-realtime', '1'       # 实时编码
                ]
            }
    
    # 检测NVIDIA GPU并获取型号信息
    gpu_available = False
    is_l4_gpu = False
    
    try:
        result = subprocess.run(['nvidia-smi'], capture_output=True, text=True, timeout=10)
        if result.returncode == 0:
            gpu_available = True
            # 检查是否为L4 GPU
            if 'L4' in result.stdout:
                is_l4_gpu = True
    except:
        pass
    
    # 如果没有nvidia-smi，尝试其他检测方法
    if not gpu_available:
        gpu_available = check_nvidia_gpu()
    
    if gpu_available:
        if is_l4_gpu:
            # L4 GPU优化配置 - 优化文件大小
            return {
                'hwaccel': 'cuda',
                'video_codec': 'h264_nvenc',
                'preset': 'p4',  # L4 GPU最佳平衡预设
                'profile': 'high',
                'extra_params': [
                    '-rc', 'vbr',          # 可变比特率
                    '-cq', '32',           # 恒定质量（降低以减小文件大小）
                    '-maxrate', '2200k',   # 最大比特率限制
                    '-bufsize', '4400k',   # 缓冲区大小
                    '-bf', '3',            # B帧数量
                    '-refs', '2',          # 减少参考帧数量
                    '-spatial_aq', '1',    # 空间自适应量化
                    '-temporal_aq', '1',   # 时间自适应量化
                    '-rc-lookahead', '15', # 减少前瞻帧数
                    '-surfaces', '16',     # 减少编码表面数量
                    '-gpu', '0'            # 指定GPU
                ]
            }
        else:
            # 通用NVIDIA GPU配置 - 优化文件大小
            return {
                'hwaccel': 'cuda',
                'video_codec': 'h264_nvenc',
                'preset': 'p4',  # 平衡预设（更好压缩）
                'extra_params': [
                    '-rc', 'vbr',          # 可变比特率
                    '-cq', '32',           # 恒定质量
                    '-maxrate', '2200k',   # 最大比特率限制
                    '-bufsize', '4400k',   # 缓冲区大小
                    '-rc-lookahead', '10', # 前瞻帧数
                    '-bf', '2',            # B帧数量
                    '-refs', '1'           # 参考帧数量
                ]
            }
    else:
        # CPU编码配置 - 优化文件大小
        return {
            'video_codec': 'libx264',
            'preset': 'medium',  # 平衡预设（更好压缩）
            'extra_params': [
                '-crf', '32',        # 恒定质量因子
                '-maxrate', '2200k', # 最大比特率限制
                '-bufsize', '4400k', # 缓冲区大小
                '-refs', '2',        # 参考帧数量
                '-me_method', 'hex', # 运动估计方法
                '-subq', '7',        # 子像素运动估计质量
                '-trellis', '1'      # 启用trellis量化
            ]
        }

# 视频输出标准配置（从 gen_video.py 复制）
VIDEO_STANDARDS = {
    'width': 720,
    'height': 1280,
    'fps': 30,
    'max_size_mb': 50,
    'video_bitrate': '2200k',  # 视频码率2200kbps
    'audio_bitrate': '128k',   # 音频码率128kbps
    'video_codec': 'libx264',
    'audio_codec': 'aac',
    'format': 'mp4',
    'min_duration_warning': 195  # 3分15秒，仅提醒不强制
}

def parse_ass_time(time_str):
    """解析ASS时间格式 (H:MM:SS.CC) 为秒数（从 gen_video.py 复制）"""
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

def format_ass_time(seconds):
    """将秒数转换为ASS时间格式（从 gen_video.py 复制）"""
    hours = int(seconds // 3600)
    minutes = int((seconds % 3600) // 60)
    secs = int(seconds % 60)
    centiseconds = int((seconds % 1) * 100)
    
    return f"{hours}:{minutes:02d}:{secs:02d}.{centiseconds:02d}"

def get_ass_duration(ass_path):
    """获取ASS字幕文件的总时长（从 gen_video.py 复制）"""
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
                    end_time_str = parts[2]
                    end_time = parse_ass_time(end_time_str)
                    max_end_time = max(max_end_time, end_time)
        
        return max_end_time
    except Exception as e:
        print(f"读取ASS文件失败: {e}")
        return 0

def get_audio_duration(audio_path):
    """获取音频文件时长（从 gen_video.py 复制）"""
    try:
        probe = ffmpeg.probe(audio_path)
        duration = float(probe['format']['duration'])
        return duration
    except Exception as e:
        print(f"获取音频时长失败: {e}")
        return 0

def get_video_info(video_path):
    """获取视频的分辨率、帧率和时长（从 gen_video.py 复制）"""
    try:
        probe = ffmpeg.probe(video_path)
        video_stream = next((stream for stream in probe['streams'] if stream['codec_type'] == 'video'), None)
        if video_stream is None:
            raise ValueError("找不到视频流")
        
        width = int(video_stream['width'])
        height = int(video_stream['height'])
        
        # 解析帧率（可能是分数形式，如 "30000/1000"）
        r_frame_rate = video_stream['r_frame_rate']
        fps_num, fps_den = map(int, r_frame_rate.split('/'))
        fps = fps_num / fps_den
        
        # 获取时长
        duration = float(probe['format']['duration'])
        
        return width, height, fps, duration
    except Exception as e:
        print(f"获取视频信息失败: {e}")
        return None, None, None, None

def get_file_size_mb(file_path):
    """获取文件大小（MB）（从 gen_video.py 复制）"""
    try:
        size_bytes = os.path.getsize(file_path)
        size_mb = size_bytes / (1024 * 1024)
        return size_mb
    except Exception as e:
        print(f"获取文件大小失败: {e}")
        return 0

def check_video_standards(video_path):
    """检查视频是否符合输出标准（从 gen_video.py 复制）"""
    try:
        # 检查文件大小
        file_size_mb = get_file_size_mb(video_path)
        print(f"视频文件大小: {file_size_mb:.2f}MB")
        
        # 获取视频信息
        width, height, fps, duration = get_video_info(video_path)
        if width is None:
            return False
            
        print(f"视频参数: {width}x{height}px, {fps}fps, {duration:.2f}s")
        
        # 检查时长（仅提醒）
        if duration < VIDEO_STANDARDS['min_duration_warning']:
            print(f"⚠️  提醒: 视频时长 {duration:.2f}s 小于建议的 {VIDEO_STANDARDS['min_duration_warning']}s (3分钟)")
        
        # 严格检查文件大小
        if file_size_mb > VIDEO_STANDARDS['max_size_mb']:
            print(f"❌ 错误: 视频文件大小 {file_size_mb:.2f}MB 超过限制 {VIDEO_STANDARDS['max_size_mb']}MB")
            return False
        
        # 检查分辨率
        if width != VIDEO_STANDARDS['width'] or height != VIDEO_STANDARDS['height']:
            print(f"⚠️  警告: 视频分辨率 {width}x{height} 不符合标准 {VIDEO_STANDARDS['width']}x{VIDEO_STANDARDS['height']}")
        
        # 检查帧率
        if abs(fps - VIDEO_STANDARDS['fps']) > 1:
            print(f"⚠️  警告: 视频帧率 {fps} 不符合标准 {VIDEO_STANDARDS['fps']}")
        
        print(f"✓ 视频文件大小符合标准: {file_size_mb:.2f}MB <= {VIDEO_STANDARDS['max_size_mb']}MB")
        return True
        
    except Exception as e:
        print(f"检查视频标准失败: {e}")
        return False

def find_sound_effect(text, work_dir):
    """
    根据字幕文本匹配音效文件
    
    Args:
        text: 字幕文本
        work_dir: 工作目录
    
    Returns:
        str: 音效文件路径，未找到返回None
    """
    # 音效关键词映射
    sound_keywords = {
        # 动作类
        '脚步': ['action/footsteps_normal.wav'],
        '走': ['action/footsteps_normal.wav'],
        '跑': ['action/footsteps_normal.wav'],
        '门': ['action/door_open.wav', 'action/door_close.wav'],
        '开门': ['action/door_open.wav'],
        '关门': ['action/door_close.wav'],
        '衣服': ['action/cloth_rustle.wav'],
        '纸': ['action/paper_rustle.mp3'],
        # 移除水声音效：'水': ['action/water_splash.wav'],
        '玻璃': ['action/glass_break.mp3'],
        
        # 战斗类
        '打': ['combat/punch_impact.wav'],
        '击': ['combat/punch_impact.wav'],
        '剑': ['combat/sword_clash.wav'],
        '箭': ['combat/arrow_whoosh.wav'],
        '爆炸': ['combat/explosion_large.wav', 'combat/explosion_small.wav'],
        
        # 情感类
        '心跳': ['emotion/heartbeat_normal.mp3'],
        '紧张': ['emotion/tension_build.mp3'],
        # 移除人声音效：'笑': ['emotion/laugh_gentle.wav'],
        
        # 环境类
        '鸟': ['environment/birds_chirping.wav'],
        # 移除风声音效：'风': ['environment/wind_gentle.wav', 'environment/wind_strong.wav'],
        '雨': ['environment/rain_light.wav', 'environment/rain_heavy.wav'],
        '雷': ['environment/thunder.wav'],
        '火': ['environment/fire_crackling.wav'],
        '森林': ['environment/forest_ambient.wav'],
        '城市': ['environment/city_ambient.wav'],
        '市场': ['environment/marketplace_ambient.wav'],
        # 移除人声音效：'人群': ['environment/crowd_murmur.WAV'],
        '夜': ['environment/night_crickets.wav'],
        # 移除风声音效：'山': ['environment/mountain_wind.wav'],
        # 移除水声音效：'流水': ['environment/water_flowing.wav'],
        
        # 杂项
        '铃': ['misc/bell.wav', 'misc/bell_ring.wav'],
        '钟': ['misc/bell.wav', 'misc/bell_ring.wav'],
        '马': ['misc/horse.wav'],
        '车': ['misc/carriage_wheels.wav'],
        '钱': ['misc/coin_drop.wav']
    }
    
    # 优先搜索路径
    primary_sound_dir = os.path.join(work_dir, 'src', 'sound_effects')
    secondary_sound_dir = os.path.join(work_dir, 'sound')
    
    # 遍历关键词匹配
    for keyword, sound_files in sound_keywords.items():
        if keyword in text:
            # 在每个音效文件中查找
            for sound_file in sound_files:
                # 优先在 src/sound_effects 中查找
                primary_path = os.path.join(primary_sound_dir, sound_file)
                if os.path.exists(primary_path):
                    print(f"匹配音效: '{keyword}' -> {primary_path}")
                    return primary_path
                
                # 在 sound 目录中递归查找
                sound_filename = os.path.basename(sound_file)
                for root, dirs, files in os.walk(secondary_sound_dir):
                    for file in files:
                        if file.lower() == sound_filename.lower():
                            secondary_path = os.path.join(root, file)
                            print(f"匹配音效: '{keyword}' -> {secondary_path}")
                            return secondary_path
    
    return None

def get_sound_effects_for_narration(dialogues, narration_num, work_dir):
    """
    为narration获取音效列表
    
    Args:
        dialogues: 对话列表
        narration_num: narration编号
        work_dir: 工作目录
    
    Returns:
        list: 音效信息列表，每个元素包含 {'path': 音效路径, 'start_time': 开始时间, 'duration': 持续时间, 'volume': 音量}
    """
    sound_effects = []
    
    # narration1特殊处理
    if narration_num == "01":
        # 第3秒固定使用铃声
        bell_path = os.path.join(work_dir, 'src', 'sound_effects', 'misc', 'bell_ring.wav')
        if os.path.exists(bell_path):
            sound_effects.append({
                'path': bell_path,
                'start_time': 3,
                'duration': 2,
                'volume': 0.5
            })
        
        # 5-10秒强制确保有音效
        has_effect_5_10 = False
        for dialogue in dialogues:
            if 5 <= dialogue['start_time'] <= 10:
                effect_path = find_sound_effect(dialogue['text'], work_dir)
                if effect_path:
                    has_effect_5_10 = True
                    sound_effects.append({
                        'path': effect_path,
                        'start_time': dialogue['start_time'],
                        'duration': min(3, dialogue['end_time'] - dialogue['start_time']),
                        'volume': 0.5
                    })
                    break
        
        # 强制确保6-10秒有音效，如果没有匹配到则使用脚步声
        if not has_effect_5_10:
            footsteps_path = os.path.join(work_dir, 'src', 'sound_effects', 'action', 'footsteps_normal.wav')
            if os.path.exists(footsteps_path):
                sound_effects.append({
                    'path': footsteps_path,
                    'start_time': 6,
                    'duration': 4,
                    'volume': 0.5
                })
            else:
                # 如果脚步声文件不存在，使用铃声作为备选
                bell_path = os.path.join(work_dir, 'src', 'sound_effects', 'misc', 'bell_ring.wav')
                if os.path.exists(bell_path):
                    sound_effects.append({
                        'path': bell_path,
                        'start_time': 6,
                        'duration': 4,
                        'volume': 0.3
                    })
    
    # 为所有对话匹配音效
    for dialogue in dialogues:
        # narration1的前10秒已经特殊处理，跳过
        if narration_num == "01" and dialogue['start_time'] < 10:
            continue
            
        effect_path = find_sound_effect(dialogue['text'], work_dir)
        if effect_path:
            # 计算音效持续时间（不超过对话时长，最长3秒）
            max_duration = min(3, dialogue['end_time'] - dialogue['start_time'])
            sound_effects.append({
                'path': effect_path,
                'start_time': dialogue['start_time'],
                'duration': max_duration,
                'volume': 0.5
            })
    
    print(f"为 narration_{narration_num} 找到 {len(sound_effects)} 个音效")
    for effect in sound_effects:
        print(f"  - {os.path.basename(effect['path'])} at {effect['start_time']}s for {effect['duration']}s")
    
    return sound_effects

def merge_ass_files(chapter_path, narration_nums, output_path):
    """
    合并多个ASS文件为一个
    
    Args:
        chapter_path: 章节目录路径
        narration_nums: narration编号列表（如 ["01", "02", "03"]）
        output_path: 输出ASS文件路径
    
    Returns:
        bool: 是否成功
    """
    chapter_name = os.path.basename(chapter_path)
    
    try:
        # 读取所有ASS文件的内容
        all_dialogues = []
        current_time_offset = 0.0
        
        for narration_num in narration_nums:
            ass_file = os.path.join(chapter_path, f"{chapter_name}_narration_{narration_num}.ass")
            if not os.path.exists(ass_file):
                print(f"ASS文件不存在: {ass_file}")
                return False
            
            # 解析当前ASS文件
            dialogues = parse_ass_dialogues(ass_file)
            if not dialogues:
                print(f"无法解析ASS文件: {ass_file}")
                return False
            
            # 调整时间戳
            for dialogue in dialogues:
                dialogue['start_time'] += current_time_offset
                dialogue['end_time'] += current_time_offset
                all_dialogues.append(dialogue)
            
            # 更新时间偏移量
            if dialogues:
                current_time_offset = max(d['end_time'] for d in all_dialogues)
        
        # 生成合并后的ASS文件
        with open(output_path, 'w', encoding='utf-8') as f:
            # 写入ASS文件头部
            f.write("[Script Info]\n")
            f.write("Title: Merged Narration\n")
            f.write("ScriptType: v4.00+\n")
            f.write("\n")
            f.write("[V4+ Styles]\n")
            f.write("Format: Name, Fontname, Fontsize, PrimaryColour, SecondaryColour, OutlineColour, BackColour, Bold, Italic, Underline, StrikeOut, ScaleX, ScaleY, Spacing, Angle, BorderStyle, Outline, Shadow, Alignment, MarginL, MarginR, MarginV, Encoding\n")
            f.write("Style: Default,Arial,20,&H00FFFFFF,&H000000FF,&H00000000,&H80000000,0,0,0,0,100,100,0,0,1,2,0,2,10,10,10,1\n")
            f.write("\n")
            f.write("[Events]\n")
            f.write("Format: Layer, Start, End, Style, Name, MarginL, MarginR, MarginV, Effect, Text\n")
            
            # 写入所有对话
            for dialogue in all_dialogues:
                start_time_str = format_ass_time(dialogue['start_time'])
                end_time_str = format_ass_time(dialogue['end_time'])
                f.write(f"Dialogue: 0,{start_time_str},{end_time_str},Default,,0,0,0,,{dialogue['text']}\n")
        
        print(f"成功合并 {len(narration_nums)} 个ASS文件到: {output_path}")
        print(f"总时长: {current_time_offset:.2f}秒, 总对话数: {len(all_dialogues)}")
        return True
        
    except Exception as e:
        print(f"合并ASS文件失败: {e}")
        return False

def merge_mp3_files(chapter_path, narration_nums, output_path):
    """
    合并多个MP3文件为一个
    
    Args:
        chapter_path: 章节目录路径
        narration_nums: narration编号列表（如 ["01", "02", "03"]）
        output_path: 输出MP3文件路径
    
    Returns:
        bool: 是否成功
    """
    chapter_name = os.path.basename(chapter_path)
    
    try:
        # 创建临时文件列表
        temp_list_file = os.path.join(chapter_path, 'temp_mp3_concat.txt')
        
        with open(temp_list_file, 'w') as f:
            for narration_num in narration_nums:
                mp3_file = os.path.join(chapter_path, f"{chapter_name}_narration_{narration_num}.mp3")
                if not os.path.exists(mp3_file):
                    print(f"MP3文件不存在: {mp3_file}")
                    return False
                f.write(f"file '{os.path.abspath(mp3_file)}'\n")
        
        # 使用ffmpeg合并MP3文件
        cmd = [
            'ffmpeg', '-y', '-f', 'concat', '-safe', '0',
            '-i', temp_list_file,
            '-c', 'copy',
            output_path
        ]
        
        result = subprocess.run(cmd, capture_output=True, text=False)
        
        # 清理临时文件
        if os.path.exists(temp_list_file):
            os.remove(temp_list_file)
        
        if result.returncode == 0:
            print(f"成功合并 {len(narration_nums)} 个MP3文件到: {output_path}")
            return True
        else:
            print(f"合并MP3文件失败: {result.stderr}")
            return False
            
    except Exception as e:
        print(f"合并MP3文件失败: {e}")
        return False

def get_images_for_narration(chapter_path, narration_num):
    """
    获取指定narration对应的图片文件
    
    新的逻辑：每个narration对应一个图片文件：
    - chapter_XXX_image_YY.jpeg (对应narration_YY)
    
    Args:
        chapter_path: 章节目录路径
        narration_num: narration编号（如 "01", "02"等）
    
    Returns:
        str: 图片文件路径，如果不存在返回None
    """
    chapter_name = os.path.basename(chapter_path)
    image_file = os.path.join(chapter_path, f"{chapter_name}_image_{narration_num}.jpeg")
    
    if os.path.exists(image_file):
        print(f"找到图片文件用于 narration_{narration_num}: {os.path.basename(image_file)}")
        return image_file
    else:
        print(f"⚠️  未找到图片文件用于 narration_{narration_num}: {os.path.basename(image_file)}")
        return None

def parse_ass_dialogues(ass_file_path):
    """
    解析ASS文件中的对话时间戳
    
    Args:
        ass_file_path: ASS文件路径
    
    Returns:
        list: 包含开始时间、结束时间和文本的字典列表
    """
    dialogues = []
    
    try:
        with open(ass_file_path, 'r', encoding='utf-8') as f:
            lines = f.readlines()
        
        for line in lines:
            line = line.strip()
            if line.startswith('Dialogue:'):
                # 格式: Dialogue: Layer,Start,End,Style,Name,MarginL,MarginR,MarginV,Effect,Text
                parts = line.split(',')
                if len(parts) >= 10:
                    start_time_str = parts[1].strip()
                    end_time_str = parts[2].strip()
                    text = ','.join(parts[9:]).strip()  # 文本可能包含逗号
                    
                    start_time = parse_ass_time(start_time_str)
                    end_time = parse_ass_time(end_time_str)
                    
                    dialogues.append({
                        'start_time': start_time,
                        'end_time': end_time,
                        'text': text
                    })
        
        print(f"解析ASS文件: {ass_file_path}, 找到 {len(dialogues)} 个对话")
        return dialogues
        
    except Exception as e:
        print(f"解析ASS文件失败: {e}")
        return []

def create_image_video_with_effects(image_path, output_path, duration, width=720, height=1280, fps=30):
    """
    创建带有动态效果的图片视频
    
    Args:
        image_path: 图片文件路径
        output_path: 输出视频路径
        duration: 视频时长（秒）
        width: 视频宽度
        height: 视频高度
        fps: 帧率
    
    Returns:
        bool: 是否成功
    """
    print(f"创建图片视频: {image_path} -> {output_path}, 时长: {duration}s")
    
    try:
        # 定义多种Ken Burns动态效果（更丝滑的移动）
        total_frames = int(duration * fps)
        effects = [
            # 缓慢放大 + 丝滑左右移动
            f"zoompan=z='min(1.0+on*0.0008,1.3)':x='iw/2-(iw/zoom/2)+sin(on*0.02)*40':y='ih/2-(ih/zoom/2)':d={total_frames}:s={width}x{height}:fps={fps}",
            # 缓慢缩小 + 丝滑上下移动
            f"zoompan=z='max(1.3-on*0.0008,1.0)':x='iw/2-(iw/zoom/2)':y='ih/2-(ih/zoom/2)+cos(on*0.025)*35':d={total_frames}:s={width}x{height}:fps={fps}",
            # 固定缩放1.15 + 丝滑对角线移动
            f"zoompan=z='1.15':x='iw/2-(iw/zoom/2)+sin(on*0.018)*45':y='ih/2-(ih/zoom/2)+cos(on*0.018)*45':d={total_frames}:s={width}x{height}:fps={fps}",
            # 固定缩放1.2 + 丝滑左移
            f"zoompan=z='1.2':x='iw/2-(iw/zoom/2)+sin(on*0.015)*50':y='ih/2-(ih/zoom/2)':d={total_frames}:s={width}x{height}:fps={fps}",
            # 固定缩放1.1 + 丝滑右移
            f"zoompan=z='1.1':x='iw/2-(iw/zoom/2)-sin(on*0.02)*40':y='ih/2-(ih/zoom/2)':d={total_frames}:s={width}x{height}:fps={fps}",
            # 固定缩放1.25 + 丝滑上移
            f"zoompan=z='1.25':x='iw/2-(iw/zoom/2)':y='ih/2-(ih/zoom/2)+cos(on*0.022)*38':d={total_frames}:s={width}x{height}:fps={fps}",
            # 固定缩放1.18 + 丝滑下移
            f"zoompan=z='1.18':x='iw/2-(iw/zoom/2)':y='ih/2-(ih/zoom/2)-cos(on*0.019)*42':d={total_frames}:s={width}x{height}:fps={fps}",
            # 固定缩放1.3 + 丝滑圆形移动
            f"zoompan=z='1.3':x='iw/2-(iw/zoom/2)+sin(on*0.016)*48':y='ih/2-(ih/zoom/2)+cos(on*0.016)*48':d={total_frames}:s={width}x{height}:fps={fps}",
            # 缓慢放大 + 丝滑螺旋移动
            f"zoompan=z='min(1.0+on*0.0006,1.4)':x='iw/2-(iw/zoom/2)+sin(on*0.014)*on*0.3':y='ih/2-(ih/zoom/2)+cos(on*0.014)*on*0.3':d={total_frames}:s={width}x{height}:fps={fps}",
            # 固定缩放1.22 + 丝滑波浪移动
            f"zoompan=z='1.22':x='iw/2-(iw/zoom/2)+sin(on*0.017)*sin(on*0.003)*45':y='ih/2-(ih/zoom/2)+cos(on*0.021)*30':d={total_frames}:s={width}x{height}:fps={fps}"
        ]
        
        # 随机选择一种效果
        selected_effect = random.choice(effects)
        
        # 获取GPU优化参数
        gpu_params = get_ffmpeg_gpu_params()
        
        # 使用subprocess调用ffmpeg
        cmd = ['ffmpeg', '-y']
        
        # 添加硬件加速参数（如果有GPU）
        if 'hwaccel' in gpu_params:
            cmd.extend(['-hwaccel', gpu_params['hwaccel']])
        if 'hwaccel_output_format' in gpu_params:
            cmd.extend(['-hwaccel_output_format', gpu_params['hwaccel_output_format']])
        
        cmd.extend([
            '-loop', '1', '-i', image_path,
            '-t', str(duration),
            '-vf', f'scale={width}:{height}:force_original_aspect_ratio=increase,crop={width}:{height},{selected_effect}',
            '-c:v', gpu_params['video_codec'], 
            '-pix_fmt', 'yuv420p'
        ])
        
        # 只有非VideoToolbox编码器才添加preset参数
        if 'preset' in gpu_params and not gpu_params['video_codec'].endswith('_videotoolbox'):
            cmd.extend(['-preset', gpu_params['preset']])
            
        cmd.extend(['-r', str(fps)])
        
        # 添加调优参数（如果有）
        if 'tune' in gpu_params:
            cmd.extend(['-tune', gpu_params['tune']])
        
        # 添加额外参数
        if gpu_params['extra_params']:
            cmd.extend(gpu_params['extra_params'])
        
        cmd.append(output_path)
        
        result = subprocess.run(cmd, capture_output=True, text=False)
        if result.returncode != 0:
            print(f"FFmpeg错误: {result.stderr}")
            return False
            
        print(f"图片视频生成成功: {output_path}")
        return True
        
    except Exception as e:
        print(f"创建图片视频失败: {e}")
        return False

# 删除create_merged_narration_video函数，不再需要合并处理

def create_narration_video(chapter_path, narration_num, work_dir):
    """
    创建单个narration的视频
    
    新的逻辑：
    - narration_01: 使用video_1.mp4 + narration_01.ass + narration_01.mp3
    - narration_02: 使用video_2.mp4 + narration_02.ass + narration_02.mp3
    - narration_03及其他: 使用图片 + ASS + MP3合成
    - 时长都使用对应MP3的时长
    
    Args:
        chapter_path: 章节目录路径
        narration_num: narration编号（如 "01", "02"等）
        work_dir: 工作目录
    
    Returns:
        str: 输出视频路径，失败时返回None
    """
    chapter_name = os.path.basename(chapter_path)
    
    # 文件路径
    ass_file = os.path.join(chapter_path, f"{chapter_name}_narration_{narration_num}.ass")
    mp3_file = os.path.join(chapter_path, f"{chapter_name}_narration_{narration_num}.mp3")
    output_video = os.path.join(chapter_path, f"{chapter_name}_narration_{narration_num}_video.mp4")
    
    # 检查必要文件是否存在
    if not os.path.exists(ass_file):
        print(f"ASS文件不存在: {ass_file}")
        return None
    
    if not os.path.exists(mp3_file):
        print(f"MP3文件不存在: {mp3_file}")
        return None
    
    # 获取音频时长（使用MP3时长作为视频时长）
    audio_duration = get_audio_duration(mp3_file)
    if audio_duration <= 0:
        print(f"无法获取音频时长: {mp3_file}")
        return None
    
    video_duration = audio_duration  # 使用MP3时长
    
    print(f"\n开始处理 narration_{narration_num}")
    print(f"使用MP3时长作为视频时长: {video_duration:.2f}s")
    
    # 解析ASS文件获取对话时间戳
    dialogues = parse_ass_dialogues(ass_file)
    if not dialogues:
        print(f"无法解析ASS文件: {ass_file}")
        return None
    
    # 根据narration编号选择视频源
    base_video = None
    
    if narration_num == "01":
        # 使用video_1.mp4
        video_1_file = os.path.join(chapter_path, f"{chapter_name}_video_1.mp4")
        if os.path.exists(video_1_file):
            base_video = video_1_file
            print(f"使用video_1.mp4作为视频源")
        else:
            print(f"video_1.mp4文件不存在: {video_1_file}")
            return None
    elif narration_num == "02":
        # 使用video_2.mp4
        video_2_file = os.path.join(chapter_path, f"{chapter_name}_video_2.mp4")
        if os.path.exists(video_2_file):
            base_video = video_2_file
            print(f"使用video_2.mp4作为视频源")
        else:
            print(f"video_2.mp4文件不存在: {video_2_file}")
            return None
    else:
        # narration_03及其他使用图片合成
        image_file = get_images_for_narration(chapter_path, narration_num)
        if not image_file:
            print(f"没有找到图片文件用于 narration_{narration_num}")
            return None
        
        # 创建临时目录
        temp_dir = os.path.join(chapter_path, 'temp_narration_videos')
        os.makedirs(temp_dir, exist_ok=True)
        
        # 创建图片视频
        temp_video = os.path.join(temp_dir, f"base_video_{narration_num}.mp4")
        if create_image_video_with_effects(
            image_file, 
            temp_video, 
            video_duration,
            VIDEO_STANDARDS['width'],
            VIDEO_STANDARDS['height'],
            VIDEO_STANDARDS['fps']
        ):
            base_video = temp_video
            print(f"使用图片{os.path.basename(image_file)}创建视频")
        else:
            print(f"创建图片视频失败")
            return None
    
    if not base_video:
        print(f"无法获取基础视频用于 narration_{narration_num}")
        return None
    
    # 如果使用现有视频文件，需要调整时长
    if narration_num in ["01", "02"]:
        # 检查视频时长是否需要调整
        _, _, _, original_duration = get_video_info(base_video)
        if original_duration and abs(original_duration - video_duration) > 0.5:
            # 需要调整时长
            temp_dir = os.path.join(chapter_path, 'temp_narration_videos')
            os.makedirs(temp_dir, exist_ok=True)
            
            adjusted_video = os.path.join(temp_dir, f"adjusted_video_{narration_num}.mp4")
            try:
                gpu_params = get_ffmpeg_gpu_params()
                
                cmd = ['ffmpeg', '-y']
                
                # 添加硬件加速参数
                if 'hwaccel' in gpu_params:
                    cmd.extend(['-hwaccel', gpu_params['hwaccel']])
                if 'hwaccel_output_format' in gpu_params:
                    cmd.extend(['-hwaccel_output_format', gpu_params['hwaccel_output_format']])
                
                cmd.extend([
                    '-i', base_video,
                    '-t', str(video_duration),  # 设置时长
                    '-c:v', gpu_params['video_codec'],
                    '-c:a', VIDEO_STANDARDS['audio_codec']
                ])
                
                # 只有非VideoToolbox编码器才添加preset参数
                if 'preset' in gpu_params and not gpu_params['video_codec'].endswith('_videotoolbox'):
                    cmd.extend(['-preset', gpu_params['preset']])
                
                if 'tune' in gpu_params:
                    cmd.extend(['-tune', gpu_params['tune']])
                
                # 添加额外参数
                if gpu_params['extra_params']:
                    cmd.extend(gpu_params['extra_params'])
                
                cmd.append(adjusted_video)
                
                result = subprocess.run(cmd, capture_output=True, text=False)
                if result.returncode == 0:
                    base_video = adjusted_video
                    print(f"调整视频时长为: {video_duration:.2f}s")
                else:
                    print(f"调整视频时长失败，使用原视频")
                    
            except Exception as e:
                print(f"调整视频时长失败: {e}，使用原视频")
    
    # 获取音效列表
    sound_effects = get_sound_effects_for_narration(dialogues, narration_num, work_dir)
    
    # 添加转场、水印、字幕和音频
    final_video = add_effects_and_audio(base_video, output_video, ass_file, mp3_file, work_dir, [video_duration], sound_effects)
    
    return final_video if final_video else None

def add_effects_and_audio(base_video, output_video, ass_file, mp3_file, work_dir, segment_durations=None, sound_effects=None):
    """
    为基础视频添加转场、水印、字幕和音频
    
    Args:
        base_video: 基础视频路径
        output_video: 输出视频路径
        ass_file: 字幕文件路径
        mp3_file: 音频文件路径
        work_dir: 工作目录
        segment_durations: 视频片段时长列表，用于计算转场时间点
        sound_effects: 音效列表，每个元素包含音效信息
    
    Returns:
        str: 输出视频路径，失败时返回None
    """
    # 获取ASS字幕文件的时长作为最大输出时长
    max_duration = get_ass_duration(ass_file)
    if max_duration <= 0:
        print(f"无法获取ASS字幕时长，使用默认处理: {ass_file}")
        max_duration = None
    try:
        # 文件路径
        fuceng_path = os.path.join(work_dir, 'src', 'banner', 'fuceng1.mov')
        watermark_path = os.path.join(work_dir, 'src', 'banner', 'rmxs.png')
        
        # 检查文件是否存在
        if not os.path.exists(fuceng_path):
            print(f"转场文件不存在: {fuceng_path}")
            fuceng_path = None
        
        if not os.path.exists(watermark_path):
            print(f"水印文件不存在: {watermark_path}")
            watermark_path = None
        
        # 获取GPU优化参数
        gpu_params = get_ffmpeg_gpu_params()
        
        # 使用subprocess构建ffmpeg命令，避免ffmpeg-python的复杂性
        cmd = ['ffmpeg', '-y']
        
        # 添加硬件加速参数（如果有GPU）
        if 'hwaccel' in gpu_params:
            cmd.extend(['-hwaccel', gpu_params['hwaccel']])
        if 'hwaccel_output_format' in gpu_params:
            cmd.extend(['-hwaccel_output_format', gpu_params['hwaccel_output_format']])
        
        # 输入文件
        cmd.extend(['-i', base_video])  # 输入0: 基础视频
        
        input_count = 1
        fuceng_input_idx = None
        watermark_input_idx = None
        
        if fuceng_path:
            cmd.extend(['-stream_loop', '-1', '-i', fuceng_path])  # 输入1: 转场视频
            fuceng_input_idx = input_count
            input_count += 1
        
        if watermark_path:
            cmd.extend(['-stream_loop', '-1', '-i', watermark_path])  # 输入2: 水印
            watermark_input_idx = input_count
            input_count += 1
        
        cmd.extend(['-i', mp3_file])  # 输入: 主音频
        audio_input_idx = input_count
        input_count += 1
        
        # 添加音效输入
        sound_effect_inputs = []
        if sound_effects:
            for i, effect in enumerate(sound_effects):
                cmd.extend(['-i', effect['path']])
                sound_effect_inputs.append({
                    'index': input_count,
                    'start_time': effect['start_time'],
                    'duration': effect['duration'],
                    'volume': effect['volume']
                })
                input_count += 1
        
        # 构建滤镜链
        filter_complex = []
        
        # 基础视频流
        current_video = '[0:v]'
        
        # 添加转场效果（fuceng1.mov）
        if fuceng_path and fuceng_input_idx is not None and segment_durations:
            # 处理fuceng视频：缩放、去黑色背景
            filter_complex.append(
                f'[{fuceng_input_idx}:v]scale={VIDEO_STANDARDS["width"]}:{VIDEO_STANDARDS["height"]}:force_original_aspect_ratio=increase,'
                f'crop={VIDEO_STANDARDS["width"]}:{VIDEO_STANDARDS["height"]},'
                f'colorkey=0x000000:0.3:0.0,format=yuva420p[fuceng]'
            )
            
            # 计算转场显示时间点：第一张图片开始时 + 每个片段切换时
            transition_times = []
            
            # 第一张图片开始时显示转场效果（前1秒）
            transition_times.append('between(t,0,1.0)')
            
            # 计算图片切换时间点（每个片段切换时显示0.5秒转场效果）
            current_time = 0
            for i, duration in enumerate(segment_durations[:-1]):  # 除了最后一个片段
                current_time += duration
                # 在切换点前0.2秒到后0.3秒显示转场效果
                start_time = max(0, current_time - 0.2)
                end_time = current_time + 0.3
                transition_times.append(f'between(t,{start_time},{end_time})')
            
            # 构建enable表达式
            if transition_times:
                enable_expr = '+'.join(transition_times)
                # 叠加转场效果（第一张图片开始时 + 图片切换时显示）
                filter_complex.append(
                    f'{current_video}[fuceng]overlay=0:0:enable=\'{enable_expr}\'[v1]'
                )
                current_video = '[v1]'
        
        # 添加水印（rmxs.png）
        if watermark_path and watermark_input_idx is not None:
            # 缩放水印到视频完整尺寸，覆盖四个角
            filter_complex.append(
                f'[{watermark_input_idx}:v]scale=720:1280[watermark_scaled]'
            )
            filter_complex.append(
                f'{current_video}[watermark_scaled]overlay=0:0[v2]'
            )
            current_video = '[v2]'
        
        # 添加字幕（位置在距离视频下方三分之一高处）
        # 对于FFmpeg的subtitles滤镜，直接使用路径，转义特殊字符
        # 转义反斜杠、冒号、等号和逗号
        escaped_ass_file = ass_file.replace('\\', '\\\\').replace(':', '\\:').replace('=', '\\=').replace(',', '\\,')
        # 计算字幕位置：视频高度的2/3处（距离下方1/3）
        subtitle_y_position = int(VIDEO_STANDARDS['height'] * 2 / 3)
        filter_complex.append(
            f"{current_video}subtitles={escaped_ass_file}:force_style='MarginV={VIDEO_STANDARDS['height'] - subtitle_y_position}'[vout]"
        )
        
        # 处理音频混合
        if sound_effect_inputs:
            # 构建音频混合滤镜
            audio_inputs = [f'[{audio_input_idx}:a]']  # 主音频
            
            # 为每个音效添加延迟和音量调整
            for i, effect_input in enumerate(sound_effect_inputs):
                effect_filter = f'[{effect_input["index"]}:a]adelay={int(effect_input["start_time"] * 1000)}|{int(effect_input["start_time"] * 1000)},volume={effect_input["volume"]}[se{i}]'
                filter_complex.append(effect_filter)
                audio_inputs.append(f'[se{i}]')
            
            # 混合所有音频
            if len(audio_inputs) > 1:
                mix_filter = f'{"".join(audio_inputs)}amix=inputs={len(audio_inputs)}:duration=longest:dropout_transition=2[aout]'
                filter_complex.append(mix_filter)
                audio_map = '[aout]'
            else:
                audio_map = f'[{audio_input_idx}:a]'
        else:
            audio_map = f'{audio_input_idx}:a'
        
        # 添加滤镜复合参数
        if filter_complex:
            cmd.extend(['-filter_complex', ';'.join(filter_complex)])
            cmd.extend(['-map', '[vout]'])  # 映射处理后的视频
            if sound_effect_inputs and len(sound_effect_inputs) > 0:
                cmd.extend(['-map', '[aout]'])  # 映射混合后的音频
            else:
                cmd.extend(['-map', f'{audio_input_idx}:a'])  # 映射原音频
        else:
            cmd.extend(['-map', '0:v'])  # 直接映射原视频
            cmd.extend(['-map', f'{audio_input_idx}:a'])  # 映射音频
        
        # 输出参数
        cmd.extend([
            '-c:v', gpu_params['video_codec'],
            '-c:a', VIDEO_STANDARDS['audio_codec'],
            '-b:v', VIDEO_STANDARDS.get('video_bitrate', '1500k'),
            '-b:a', VIDEO_STANDARDS['audio_bitrate'],
            '-r', str(VIDEO_STANDARDS['fps'])
        ])
        
        # 只有非VideoToolbox编码器才添加preset参数
        if 'preset' in gpu_params and not gpu_params['video_codec'].endswith('_videotoolbox'):
            cmd.extend(['-preset', gpu_params['preset']])
        
        # 添加调优参数（如果有）
        if 'tune' in gpu_params:
            cmd.extend(['-tune', gpu_params['tune']])
        
        # 添加额外参数
        if gpu_params['extra_params']:
            cmd.extend(gpu_params['extra_params'])
        
        # 添加时长限制，确保不超过ASS字幕文件时长
        if max_duration:
            cmd.extend(['-t', str(max_duration)])
        
        cmd.extend(['-shortest', output_video])  # 以最短的输入为准，并添加输出文件
        
        # 执行命令
        print(f"执行FFmpeg命令: {' '.join(cmd)}")
        result = subprocess.run(cmd, capture_output=True, text=False)
        
        if result.returncode != 0:
            # 安全地解码stderr，忽略无法解码的字符
            try:
                stderr_text = result.stderr.decode('utf-8', errors='ignore')
            except:
                stderr_text = str(result.stderr)
            print(f"FFmpeg错误: {stderr_text}")
            return None
        
        print(f"最终视频生成成功: {output_video}")
        return output_video
        
    except Exception as e:
        print(f"添加效果和音频失败: {e}")
        return None

def process_chapter(chapter_path, work_dir):
    """
    处理单个章节的所有narration
    
    新逻辑：
    - narration_01: 使用video_1.mp4 + narration_01.ass + narration_01.mp3
    - narration_02: 使用video_2.mp4 + narration_02.ass + narration_02.mp3
    - narration_03及其他: 使用图片 + ASS + MP3合成
    - 时长都使用对应MP3的时长
    
    Args:
        chapter_path: 章节目录路径
        work_dir: 工作目录
    
    Returns:
        list: 成功生成的视频文件路径列表
    """
    chapter_name = os.path.basename(chapter_path)
    print(f"\n开始处理章节: {chapter_name}")
    
    # 查找所有narration文件
    narration_pattern = os.path.join(chapter_path, f"{chapter_name}_narration_*.ass")
    narration_files = glob.glob(narration_pattern)
    
    # 提取narration编号并排序
    narration_nums = []
    for file in narration_files:
        match = re.search(r'narration_(\d+)\.ass$', file)
        if match:
            narration_nums.append(match.group(1))
    
    narration_nums.sort()
    print(f"找到 {len(narration_nums)} 个narration: {narration_nums}")
    
    generated_videos = []
    
    # 处理所有narration
    for narration_num in narration_nums:
        video_path = create_narration_video(chapter_path, narration_num, work_dir)
        if video_path:
            generated_videos.append(video_path)
            
            # 检查视频标准
            if check_video_standards(video_path):
                print(f"✓ narration_{narration_num} 视频符合标准")
            else:
                print(f"⚠️  narration_{narration_num} 视频不完全符合标准")
        else:
            print(f"❌ narration_{narration_num} 视频生成失败")
    
    return generated_videos

def main():
    parser = argparse.ArgumentParser(description='生成旁白视频')
    parser.add_argument('work_dir', help='工作目录路径（如 data/001）')
    parser.add_argument('--chapter', help='指定章节名称（如 chapter_002），不指定则处理所有章节')
    
    args = parser.parse_args()
    
    work_dir = os.path.abspath(args.work_dir)
    if not os.path.exists(work_dir):
        print(f"工作目录不存在: {work_dir}")
        return 1
    
    # 获取项目根目录
    project_root = os.path.dirname(os.path.abspath(__file__))
    
    if args.chapter:
        # 处理指定章节
        chapter_path = os.path.join(work_dir, args.chapter)
        if not os.path.exists(chapter_path):
            print(f"章节目录不存在: {chapter_path}")
            return 1
        
        generated_videos = process_chapter(chapter_path, project_root)
        print(f"\n章节 {args.chapter} 处理完成，生成 {len(generated_videos)} 个视频")
    else:
        # 处理所有章节
        chapter_dirs = [d for d in os.listdir(work_dir) 
                       if os.path.isdir(os.path.join(work_dir, d)) and d.startswith('chapter_')]
        chapter_dirs.sort()
        
        total_generated = 0
        for chapter_dir in chapter_dirs:
            chapter_path = os.path.join(work_dir, chapter_dir)
            generated_videos = process_chapter(chapter_path, project_root)
            total_generated += len(generated_videos)
        
        print(f"\n所有章节处理完成，总共生成 {total_generated} 个视频")
    
    return 0

if __name__ == '__main__':
    sys.exit(main())