#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
视频生成脚本
基于test_ffmpeg.py的合成模式，遍历章节文件夹生成完整视频
"""

import os
import sys
import re
import json
import ffmpeg
import argparse
import glob
from pathlib import Path
import concurrent.futures
import random

# 导入音效处理模块
sys.path.append(os.path.join(os.path.dirname(os.path.abspath(__file__)), 'src'))
from sound_effects_processor import SoundEffectsProcessor

# 视频输出标准配置
VIDEO_STANDARDS = {
    'width': 720,
    'height': 1280,
    'fps': 30,
    'max_size_mb': 50,
    'audio_bitrate': '128k',
    'video_codec': 'libx264',
    'audio_codec': 'aac',
    'format': 'mp4',
    'min_duration_warning': 180  # 3分钟，仅提醒不强制
}

def get_file_size_mb(file_path):
    """获取文件大小（MB）"""
    try:
        size_bytes = os.path.getsize(file_path)
        size_mb = size_bytes / (1024 * 1024)
        return size_mb
    except Exception as e:
        print(f"获取文件大小失败: {e}")
        return 0

def check_video_standards(video_path):
    """检查视频是否符合输出标准"""
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

def optimize_video_for_size(input_path, output_path, target_size_mb=50):
    """优化视频以满足文件大小要求"""
    try:
        # 获取原始视频信息
        width, height, fps, duration = get_video_info(input_path)
        if width is None:
            return False
            
        # 计算目标比特率（考虑音频比特率）
        audio_bitrate_kbps = 128  # 128kbps
        target_size_bits = target_size_mb * 8 * 1024 * 1024  # 转换为bits
        audio_bits = audio_bitrate_kbps * 1000 * duration  # 音频总bits
        video_bits = target_size_bits - audio_bits  # 视频可用bits
        target_video_bitrate_kbps = int(video_bits / (duration * 1000))  # 目标视频比特率
        
        # 确保比特率不会太低
        min_video_bitrate = 500  # 最低500kbps
        target_video_bitrate_kbps = max(target_video_bitrate_kbps, min_video_bitrate)
        
        print(f"优化视频: 目标大小 {target_size_mb}MB, 计算得出视频比特率 {target_video_bitrate_kbps}kbps")
        
        # 重新编码视频
        (
            ffmpeg
            .input(input_path)
            .output(
                output_path,
                vcodec=VIDEO_STANDARDS['video_codec'],
                acodec=VIDEO_STANDARDS['audio_codec'],
                video_bitrate=f"{target_video_bitrate_kbps}k",
                audio_bitrate=VIDEO_STANDARDS['audio_bitrate'],
                r=VIDEO_STANDARDS['fps'],
                s=f"{VIDEO_STANDARDS['width']}x{VIDEO_STANDARDS['height']}",
                preset='medium',  # 使用medium预设平衡质量和文件大小
                crf=23  # 添加CRF参数进一步控制质量
            )
            .overwrite_output()
            .run()
        )
        
        # 检查优化后的文件大小
        optimized_size_mb = get_file_size_mb(output_path)
        print(f"优化后文件大小: {optimized_size_mb:.2f}MB")
        
        if optimized_size_mb <= target_size_mb:
            print(f"✓ 视频优化成功: {optimized_size_mb:.2f}MB <= {target_size_mb}MB")
            return True
        else:
            print(f"⚠️  视频优化后仍超过目标大小: {optimized_size_mb:.2f}MB > {target_size_mb}MB")
            return False
            
    except Exception as e:
        print(f"视频优化失败: {e}")
        return False

def get_video_info(video_path):
    """获取视频的分辨率、帧率和时长"""
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

def format_ass_time(seconds):
    """将秒数转换为ASS时间格式"""
    hours = int(seconds // 3600)
    minutes = int((seconds % 3600) // 60)
    secs = int(seconds % 60)
    centiseconds = int((seconds % 1) * 100)
    
    return f"{hours}:{minutes:02d}:{secs:02d}.{centiseconds:02d}"

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
                    end_time_str = parts[2]
                    end_time = parse_ass_time(end_time_str)
                    max_end_time = max(max_end_time, end_time)
        
        return max_end_time
    except Exception as e:
        print(f"读取ASS文件失败: {e}")
        return 0

def get_audio_duration(audio_path):
    """获取音频文件时长"""
    try:
        probe = ffmpeg.probe(audio_path)
        duration = float(probe['format']['duration'])
        return duration
    except Exception as e:
        print(f"获取音频时长失败: {e}")
        return 0

def get_timestamps_duration(timestamps_path):
    """从timestamps.json文件获取duration"""
    try:
        with open(timestamps_path, 'r', encoding='utf-8') as f:
            data = json.load(f)
            return float(data.get('duration', 0))
    except Exception as e:
        print(f"读取timestamps文件失败: {e}")
        return 0

def image_to_video(image_path, output_path, duration=5, width=None, height=None, fps=None, fade_duration=0.5, audio_path=None):
    """将图片转换为视频片段，使用ffmpeg实现
    
    Args:
        image_path: 图片文件路径
        output_path: 输出视频路径
        duration: 视频时长（秒），如果提供了audio_path则会被覆盖
        width: 视频宽度，None时使用标准配置
        height: 视频高度，None时使用标准配置
        fps: 帧率，None时使用标准配置
        fade_duration: 保留参数以兼容性
        audio_path: 音频文件路径，如果提供则使用音频时长作为视频时长
    """
    # 使用标准配置作为默认值
    if width is None:
        width = VIDEO_STANDARDS['width']
    if height is None:
        height = VIDEO_STANDARDS['height']
    if fps is None:
        fps = VIDEO_STANDARDS['fps']
    
    # 直接使用ffmpeg实现
    print("使用ffmpeg方式进行视频合成")
    return image_to_video_ffmpeg(image_path, output_path, duration, width, height, fps, fade_duration, audio_path)
    


def image_to_video_ffmpeg(image_path, output_path, duration=5, width=720, height=1280, fps=30, fade_duration=0.5, audio_path=None):
    """ffmpeg版本的图片转视频函数（备用）"""
    # 如果提供了音频文件，使用音频时长
    if audio_path and os.path.exists(audio_path):
        audio_duration = get_audio_duration(audio_path)
        if audio_duration > 0:
            duration = audio_duration
            print(f"使用音频时长: {duration:.2f}s (音频文件: {audio_path})")
        else:
            print(f"警告: 无法获取音频时长，使用默认时长: {duration}s")
    
    print(f"开始转换图片到视频 (ffmpeg): {image_path} -> {output_path}, 时长: {duration}s")
    try:
        # 计算四角滑动动画参数
        total_frames = int(duration * fps)
        corner_offset = min(width, height) * 0.15  # 移动距离
        
        # 创建四角滑动动画的表达式
        # 简化的四角循环移动：使用正弦和余弦函数的组合
        # 时间进度：t/{duration} 从0到1，乘以2π实现完整循环
        
        # 简化动画效果，使用固定的缩放和居中裁剪
        # 创建基础视频（图片转视频，带缩放效果）
        base_video = (
            ffmpeg
            .input(image_path, loop=1, t=duration)
            .filter('scale', int(width*1.1), int(height*1.1))  # 适度放大1.1倍
            .filter('crop', width, height, f'(iw-{width})/2', f'(ih-{height})/2')  # 居中裁剪
        )
        
        # 定义overlay文件路径 - 随机选择一个fuceng文件
        banner_dir = os.path.join(os.path.dirname(os.path.abspath(__file__)), "src", "banner")
        fuceng_files = ["fuceng1.mov"]  # 只包含实际存在的文件
        selected_fuceng = random.choice(fuceng_files)
        fuceng_path = os.path.join(banner_dir, selected_fuceng)
        print(f"随机选择的中间层文件: {selected_fuceng}")
        watermark_path = os.path.join(os.path.dirname(os.path.abspath(__file__)), "src", "banner", "rmxs.png")
        
        # 检查fuceng.mp4是否存在
        if os.path.exists(fuceng_path):
            # 添加fuceng.mp4作为中间层
            fuceng_input = ffmpeg.input(fuceng_path, an=None)  # 播放一次，不包含音频
            
            # 处理fuceng.mp4：缩放到视频尺寸并极致过滤所有暗色
            fuceng_processed = (
                fuceng_input
                .filter('scale', width, height)  # 缩放到视频尺寸
                .filter('colorkey', color='0x000000', similarity=0.99, blend=0.0)  # 极致过滤纯黑
                .filter('colorkey', color='0x010101', similarity=0.95, blend=0.0)  # 过滤接近黑色
                .filter('colorkey', color='0x020202', similarity=0.9, blend=0.0)   # 过滤深灰色
                .filter('colorkey', color='0x030303', similarity=0.85, blend=0.0)  # 过滤更深灰色
                .filter('colorkey', color='0x040404', similarity=0.8, blend=0.0)   # 过滤暗灰色
                .filter('colorkey', color='0x050505', similarity=0.75, blend=0.0)  # 过滤深色调
                .filter('colorkey', color='0x0a0a0a', similarity=0.7, blend=0.0)   # 过滤极深色
            )
            
            # 第一步：将处理后的fuceng.mp4作为中间层overlay到基础视频上
            video_with_fuceng = ffmpeg.filter([base_video, fuceng_processed], 'overlay', 
                                             x=0, y=0)  # 全屏覆盖
        else:
            print(f"警告: fuceng.mp4文件不存在: {fuceng_path}")
            video_with_fuceng = base_video
        
        # 检查rmxs.png是否存在并添加为最上层
        if os.path.exists(watermark_path):
            watermark_input = ffmpeg.input(watermark_path, loop=1, t=duration)  # 循环播放角标，持续整个视频时长
            
            # 第二步：将rmxs.png作为最上层overlay
            final_video = ffmpeg.filter([video_with_fuceng, watermark_input], 'overlay', 
                                       x='W-w',  # 右上角贴边：视频宽度-角标宽度
                                       y=0)      # 上边距0像素，完全贴边
        else:
            print(f"警告: rmxs.png文件不存在: {watermark_path}")
            final_video = video_with_fuceng
        
        # 输出最终视频，使用标准配置
        (
            final_video
            .output(
                output_path, 
                r=VIDEO_STANDARDS['fps'], 
                vcodec=VIDEO_STANDARDS['video_codec'], 
                acodec=VIDEO_STANDARDS['audio_codec'],
                pix_fmt='yuv420p', 
                preset='medium',  # 使用medium预设平衡质量和文件大小
                video_bitrate='1500k',  # 适中的视频比特率
                audio_bitrate=VIDEO_STANDARDS['audio_bitrate'],
                s=f"{VIDEO_STANDARDS['width']}x{VIDEO_STANDARDS['height']}"
            )
            .overwrite_output()
            .run(quiet=False)  # 改为非安静模式以显示ffmpeg进度
        )
        print(f"图片转视频成功（带Ken Burns效果、平移和多层overlay）：{output_path} (时长: {duration}s)")
        return True
    except Exception as e:
        print(f"图片转视频失败: {e}")
        return False

def concat_videos(video_list, output_path):
    """拼接多个视频片段（无过渡）"""
    try:
        if len(video_list) == 0:
            return False
        if len(video_list) == 1:
            import shutil
            shutil.copy2(video_list[0], output_path)
            print(f"视频复制成功：{output_path}")
            return True
        
        # 创建临时文件列表，为每个视频添加静音音频
        temp_dir = os.path.dirname(output_path)
        temp_videos = []
        
        for i, video_path in enumerate(video_list):
            temp_video_path = os.path.join(temp_dir, f"temp_with_audio_{i}.mp4")
            
            # 为视频添加静音音频轨道
            video_info = get_video_info(video_path)
            duration = video_info[3] if video_info[3] else 5
            
            # 为视频添加静音音频
            video_input = ffmpeg.input(video_path)
            audio_input = ffmpeg.input('anullsrc=channel_layout=stereo:sample_rate=48000', f='lavfi', t=duration)
            
            (
                ffmpeg
                .output(
                    video_input['v'], audio_input['a'],
                    temp_video_path,
                    vcodec='copy',
                    acodec='aac'
                )
                .overwrite_output()
                .run()
            )
            temp_videos.append(temp_video_path)
        
        # 使用文件列表方式拼接，避免ffmpeg.concat的输入流数量限制问题
        import tempfile
        import subprocess
        
        # 创建临时文件列表，确保使用绝对路径
        with tempfile.NamedTemporaryFile(mode='w', suffix='.txt', delete=False) as f:
            for video in temp_videos:
                # 确保使用绝对路径
                abs_video_path = os.path.abspath(video)
                f.write(f"file '{abs_video_path}'\n")
            filelist_path = f.name
        
        try:
            # 使用ffmpeg命令行工具拼接，强制重新生成时间戳从0开始
            subprocess.run([
                'ffmpeg', '-fflags', '+genpts', '-f', 'concat', '-safe', '0', '-i', filelist_path,
                '-c:v', 'libx264', '-c:a', 'aac', '-preset', 'fast',
                '-avoid_negative_ts', 'make_zero', '-start_at_zero', output_path, '-y'
            ], check=True)
            print(f"视频拼接成功：{output_path}")
        finally:
            # 清理临时文件
            os.unlink(filelist_path)
        
        # 清理临时文件
        for temp_video in temp_videos:
            try:
                os.remove(temp_video)
            except:
                pass
        
        return True
    except Exception as e:
        print(f"视频拼接失败: {e}")
        return False

def clean_ass_punctuation(ass_file_path):
    """清理ASS文件中的所有标点符号（包括引号）"""
    try:
        with open(ass_file_path, 'r', encoding='utf-8') as f:
            lines = f.readlines()
        
        cleaned_lines = []
        for line in lines:
            if line.strip().startswith('Dialogue:'):
                # 解析Dialogue行
                parts = line.split(',', 9)  # 最多分割9次，保留最后的文本部分
                if len(parts) >= 10:
                    # 获取文本部分（最后一个元素）
                    text_part = parts[9]
                    
                    # 定义要移除的标点符号（包括中英文标点）
                    punctuation_chars = '，。！？；：""“”''（）【】《》、,."!?;:()[]<>/\\|`~@#$%^&*-_=+{}'
                    
                    # 清理文本，但保留ASS格式标签
                    cleaned_text = ''
                    i = 0
                    while i < len(text_part):
                        if text_part[i] == '{':
                            # 找到ASS标签的结束位置
                            end_pos = text_part.find('}', i)
                            if end_pos != -1:
                                # 保留整个标签
                                cleaned_text += text_part[i:end_pos+1]
                                i = end_pos + 1
                            else:
                                # 如果没有找到结束标签，保留当前字符
                                if text_part[i] not in punctuation_chars:
                                    cleaned_text += text_part[i]
                                i += 1
                        elif text_part[i] not in punctuation_chars:
                            # 保留非标点符号字符
                            cleaned_text += text_part[i]
                            i += 1
                        else:
                            # 跳过标点符号
                            i += 1
                    
                    # 重新组装Dialogue行
                    parts[9] = cleaned_text
                    cleaned_line = ','.join(parts)
                    cleaned_lines.append(cleaned_line)
                else:
                    cleaned_lines.append(line)
            else:
                # 非Dialogue行保持不变
                cleaned_lines.append(line)
        
        # 写回文件
        with open(ass_file_path, 'w', encoding='utf-8') as f:
            f.writelines(cleaned_lines)
        
        print(f"已清理ASS文件中的标点符号: {ass_file_path}")
        return True
    except Exception as e:
        print(f"清理ASS文件标点符号失败: {e}")
        return False

def add_subtitle(video_path, subtitle_path, output_path):
    """为视频添加硬字幕"""
    try:
        (
            ffmpeg
            .input(video_path)
            .filter('subtitles', subtitle_path)
            .output(output_path)
            .overwrite_output()
            .run()
        )
        print(f"添加字幕成功：{output_path}")
        return True
    except Exception as e:
        print(f"添加字幕失败: {e}")
        return False

def add_watermark(video_path, watermark_path, output_path):
    """为视频添加多层overlay：随机选择的fuceng文件作为中间层，rmxs.png作为最上层"""
    try:
        # 检查角标文件是否存在
        if not os.path.exists(watermark_path):
            print(f"警告: 角标文件不存在: {watermark_path}")
            # 如果角标文件不存在，直接复制原视频
            import shutil
            shutil.copy2(video_path, output_path)
            return True
        
        # 获取视频信息
        video_info = get_video_info(video_path)
        if video_info[0] is None:
            print(f"无法获取视频信息: {video_path}")
            return False
        
        video_width, video_height = video_info[0], video_info[1]
        
        # 定义overlay文件路径 - 随机选择一个fuceng文件
        banner_dir = os.path.join(os.path.dirname(os.path.abspath(__file__)), "src", "banner")
        fuceng_files = ["fuceng1.mov"]  # 只包含实际存在的文件
        selected_fuceng = random.choice(fuceng_files)
        fuceng_path = os.path.join(banner_dir, selected_fuceng)
        print(f"随机选择的中间层文件: {selected_fuceng}")
        
        # 检查选中的fuceng文件是否存在
        if not os.path.exists(fuceng_path):
            print(f"警告: 选中的fuceng文件不存在: {fuceng_path}")
            # 如果选中的fuceng文件不存在，只添加rmxs.png
            video_input = ffmpeg.input(video_path)
            watermark_input = ffmpeg.input(watermark_path, loop=1)
            
            (
                ffmpeg
                .filter([video_input, watermark_input], 'overlay', 
                       x='W-w',  # 右上角贴边：视频宽度-角标宽度
                       y=0,      # 上边距0像素，完全贴边
                       shortest=1)  # 确保角标持续到视频结束
                .output(
                    output_path, 
                    vcodec=VIDEO_STANDARDS['video_codec'], 
                    acodec='copy', 
                    video_bitrate='1500k',
                    r=VIDEO_STANDARDS['fps']
                )
                .overwrite_output()
                .run()
            )
        else:
            # 添加多层overlay
            video_input = ffmpeg.input(video_path)
            # 获取视频时长用于播放fuceng文件
            video_duration = video_info[3] if video_info[3] else 10  # 默认10秒
            fuceng_input = ffmpeg.input(fuceng_path, an=None)  # 播放一次，不包含音频
            watermark_input = ffmpeg.input(watermark_path, loop=1, t=video_duration)  # 循环播放角标，持续整个视频时长
            
            # 处理fuceng.mp4：缩放到视频尺寸并极致过滤所有暗色
            fuceng_processed = (
                fuceng_input
                .filter('scale', video_width, video_height)  # 缩放到视频尺寸
                .filter('colorkey', color='0x000000', similarity=0.99, blend=0.0)  # 极致过滤纯黑
                .filter('colorkey', color='0x010101', similarity=0.95, blend=0.0)  # 过滤接近黑色
                .filter('colorkey', color='0x020202', similarity=0.9, blend=0.0)   # 过滤深灰色
                .filter('colorkey', color='0x030303', similarity=0.85, blend=0.0)  # 过滤更深灰色
                .filter('colorkey', color='0x040404', similarity=0.8, blend=0.0)   # 过滤暗灰色
                .filter('colorkey', color='0x050505', similarity=0.75, blend=0.0)  # 过滤深色调
                .filter('colorkey', color='0x0a0a0a', similarity=0.7, blend=0.0)   # 过滤极深色
            )
            
            # 第一步：将处理后的fuceng.mp4作为中间层overlay到原视频上
            video_with_fuceng = ffmpeg.filter([video_input, fuceng_processed], 'overlay', 
                                             x=0, y=0)  # 全屏覆盖
            
            # 第二步：将rmxs.png作为最上层overlay
            (
                ffmpeg
                .filter([video_with_fuceng, watermark_input], 'overlay', 
                       x='W-w',  # 右上角贴边：视频宽度-角标宽度
                       y=0)      # 上边距0像素，完全贴边
                .output(
                    output_path, 
                    vcodec=VIDEO_STANDARDS['video_codec'], 
                    acodec='copy', 
                    video_bitrate='1500k',
                    r=VIDEO_STANDARDS['fps']
                )
                .overwrite_output()
                .run()
            )
        
        print(f"添加多层overlay成功：{output_path}")
        return True
    except Exception as e:
        print(f"添加多层overlay失败: {e}")
        return False

def add_audio(video_path, audio_path, output_path, replace=True):
    """为视频添加音频（替换或混合）"""
    try:
        # 获取视频和音频的时长
        video_info = get_video_info(video_path)
        audio_duration = get_audio_duration(audio_path)
        video_duration = video_info[3] if video_info[3] else 0
        
        print(f"视频时长: {video_duration:.2f}s, 音频时长: {audio_duration:.2f}s")
        
        video = ffmpeg.input(video_path)
        audio = ffmpeg.input(audio_path)
        
        if replace:
            # 替换原音频，以音频时长为准
            if abs(video_duration - audio_duration) > 0.1:  # 时长差异超过0.1秒
                if video_duration > audio_duration:
                    # 视频比音频长，截取视频来匹配音频时长
                    print(f"视频比音频长 {video_duration - audio_duration:.2f}s，将截取视频")
                    video = video.filter('trim', duration=audio_duration)
                elif audio_duration > video_duration:
                    # 音频比视频长，截取音频
                    print(f"音频比视频长 {audio_duration - video_duration:.2f}s，将截取音频")
                    audio = audio.filter('atrim', duration=video_duration)
            
            (
                ffmpeg
                .output(
                    video, audio, output_path, 
                    vcodec=VIDEO_STANDARDS['video_codec'], 
                    acodec=VIDEO_STANDARDS['audio_codec'], 
                    video_bitrate='1500k', 
                    audio_bitrate=VIDEO_STANDARDS['audio_bitrate'],
                    r=VIDEO_STANDARDS['fps']
                )
                .overwrite_output()
                .run()
            )
        else:
            # 混合原音频和新音频
            (
                ffmpeg
                .filter([video.audio, audio.audio], 'amix', inputs=2, duration='shortest')
                .output(video.video, 'a', output_path)
                .overwrite_output()
                .run()
            )
        print(f"添加音频成功：{output_path}")
        return True
    except Exception as e:
        print(f"添加音频失败: {e}")
        return False

def concat_audio_files(audio_files, output_path):
    """拼接多个音频文件"""
    try:
        if len(audio_files) == 1:
            import shutil
            shutil.copy2(audio_files[0], output_path)
            print(f"音频复制成功：{output_path}")
            return True
        
        # 创建输入流
        inputs = [ffmpeg.input(audio_file) for audio_file in audio_files]
        
        # 拼接音频
        (
            ffmpeg
            .concat(*inputs, v=0, a=1)
            .output(output_path)
            .overwrite_output()
            .run()
        )
        print(f"音频拼接成功：{output_path}")
        return True
    except Exception as e:
        print(f"音频拼接失败: {e}")
        return False

def get_sound_effects_dir():
    """获取音效目录，优先使用 src/sound_effects，找不到时使用 sound"""
    base_dir = os.path.dirname(os.path.abspath(__file__))
    
    # 优先使用 src/sound_effects 目录
    primary_dir = os.path.join(base_dir, "src", "sound_effects")
    if os.path.exists(primary_dir):
        print(f"使用优先音效目录: {primary_dir}")
        return primary_dir
    
    # 备用目录 sound
    fallback_dir = os.path.join(base_dir, "sound")
    if os.path.exists(fallback_dir):
        print(f"使用备用音效目录: {fallback_dir}")
        return fallback_dir
    
    print("警告: 未找到任何音效目录")
    return None

def mix_audio_with_bgm_and_effects(narration_audio_path, video_duration, output_path, merged_ass_file=None):
    """将台词音频与随机选择的BGM和音效混合
    
    Args:
        narration_audio_path: 台词音频文件路径
        video_duration: 视频总时长
        output_path: 输出音频路径
        merged_ass_file: 合并后的ASS字幕文件路径（用于音效匹配）
    """
    try:
        # 获取BGM目录
        bgm_dir = os.path.join(os.path.dirname(os.path.abspath(__file__)), "src", "bgm")
        sound_effects_dir = get_sound_effects_dir()
        
        # 查找所有wn*.mp3文件
        bgm_files = glob.glob(os.path.join(bgm_dir, "wn*.mp3"))
        if not bgm_files:
            print("警告: 未找到BGM文件，仅使用台词音频")
            import shutil
            shutil.copy2(narration_audio_path, output_path)
            return True
        
        # 随机选择一个BGM文件
        selected_bgm = random.choice(bgm_files)
        print(f"随机选择BGM: {os.path.basename(selected_bgm)}")
        
        # 获取台词音频时长
        narration_duration = get_audio_duration(narration_audio_path)
        bgm_duration = get_audio_duration(selected_bgm)
        
        print(f"台词音频时长: {narration_duration:.2f}s, BGM时长: {bgm_duration:.2f}s, 视频时长: {video_duration:.2f}s")
        
        # 以台词音频时长为准，添加3秒渐变时间
        fade_duration = 3.0
        target_duration = narration_duration + fade_duration
        print(f"目标音频时长: {target_duration:.2f}s (台词 {narration_duration:.2f}s + 渐变 {fade_duration:.2f}s)")
        
        # 准备音频输入列表
        audio_inputs = []
        
        # 1. 处理台词音频
        narration_input = ffmpeg.input(narration_audio_path)
        silence = ffmpeg.input('anullsrc=channel_layout=stereo:sample_rate=48000', f='lavfi', t=fade_duration)
        narration_extended = ffmpeg.concat(narration_input, silence, v=0, a=1)
        narration_volume = narration_extended.filter('volume', volume=1.0)
        audio_inputs.append(narration_volume)
        
        # 2. 处理BGM
        bgm_input = ffmpeg.input(selected_bgm)
        if bgm_duration < target_duration:
            loop_count = int(target_duration / bgm_duration) + 1
            print(f"BGM需要循环 {loop_count} 次以匹配目标时长")
            bgm_looped = bgm_input.filter('aloop', loop=loop_count-1, size=int(bgm_duration * 48000 * 2))
        else:
            bgm_looped = bgm_input
        
        bgm_trimmed = bgm_looped.filter('atrim', duration=target_duration)
        bgm_volume = bgm_trimmed.filter('volume', volume=0.1)
        
        # BGM在台词结束后渐变消失
        fade_start = narration_duration
        print(f"BGM将在 {fade_start:.2f}s 开始渐变，持续 {fade_duration:.2f}s")
        bgm_volume = bgm_volume.filter('afade', type='out', start_time=fade_start, duration=fade_duration)
        audio_inputs.append(bgm_volume)
        
        # 3. 处理音效（如果提供了ASS文件）
        if merged_ass_file and os.path.exists(merged_ass_file) and sound_effects_dir and os.path.exists(sound_effects_dir):
            print("开始处理音效...")
            sound_processor = SoundEffectsProcessor(sound_effects_dir)
            
            # 解析字幕并匹配音效
            dialogues = sound_processor.parse_ass_file(merged_ass_file)
            if dialogues:
                sound_events = sound_processor.match_sound_effects(dialogues)
                
                if sound_events:
                    print(f"找到 {len(sound_events)} 个音效事件")
                    
                    # 为每个音效事件创建音频输入
                    for event in sound_events:
                        try:
                            sound_input = ffmpeg.input(event['sound_file'])
                            sound_volume = sound_input.filter('volume', volume=event['volume'])
                            
                            # 添加延迟到指定时间
                            if event['start_time'] > 0:
                                sound_delayed = sound_volume.filter('adelay', delays=f"{int(event['start_time'] * 1000)}")
                            else:
                                sound_delayed = sound_volume
                            
                            audio_inputs.append(sound_delayed)
                            print(f"添加音效: {os.path.basename(event['sound_file'])} 在 {event['start_time']:.2f}s")
                        except Exception as e:
                            print(f"处理音效失败: {event['sound_file']}, 错误: {e}")
                else:
                    print("未匹配到任何音效")
            else:
                print("未解析到有效对话")
        else:
            print("跳过音效处理（未提供ASS文件或音效目录不存在）")
        
        # 注释：移除固定音效，现在使用智能匹配系统
        
        # 混合所有音频
        if len(audio_inputs) > 1:
            mixed_audio = ffmpeg.filter(audio_inputs, 'amix', inputs=len(audio_inputs), duration='longest')
        else:
            mixed_audio = audio_inputs[0]
        
        # 输出混合后的音频
        (
            ffmpeg
            .output(mixed_audio, output_path, acodec='mp3', audio_bitrate='128k')
            .overwrite_output()
            .run()
        )
        
        print(f"音频混合成功（包含 {len(audio_inputs)} 个音轨）：{output_path}")
        return True
        
    except Exception as e:
        print(f"音频混合失败: {e}")
        return False

def mix_audio_with_bgm(narration_audio_path, video_duration, output_path):
    """将台词音频与随机选择的BGM混合（兼容性函数）
    
    Args:
        narration_audio_path: 台词音频文件路径
        video_duration: 视频总时长
        output_path: 输出音频路径
    """
    return mix_audio_with_bgm_and_effects(narration_audio_path, video_duration, output_path)

def merge_ass_files(ass_files, output_path, video_segments_info):
    """合并多个ASS文件，调整时间戳"""
    try:
        merged_content = []
        
        # 计算每个音频文件的实际时长，用于累积时间偏移
        audio_durations = []
        for ass_file in ass_files:
            # 获取对应的音频文件时长
            audio_file = ass_file.replace('.ass', '.mp3')
            if os.path.exists(audio_file):
                duration = get_audio_duration(audio_file)
                audio_durations.append(duration)
                print(f"音频文件 {audio_file} 时长: {duration:.2f}s")
            else:
                # 如果音频文件不存在，使用ASS文件时长作为备选
                duration = get_ass_duration(ass_file)
                audio_durations.append(duration)
                print(f"ASS文件 {ass_file} 时长: {duration:.2f}s (音频文件不存在)")
        
        # 计算累积时间偏移（基于音频文件的实际时长）
        time_offsets = [0]  # 第一个文件从0开始
        for i in range(len(audio_durations)):
            if i > 0:  # 从第二个文件开始累加
                time_offsets.append(time_offsets[-1] + audio_durations[i-1])
        
        for i, ass_file in enumerate(ass_files):
            with open(ass_file, 'r', encoding='utf-8') as f:
                lines = f.readlines()
            
            # 获取当前文件的时间偏移
            current_time_offset = time_offsets[i] if i < len(time_offsets) else 0
            print(f"处理ASS文件 {i+1}: {ass_file}, 时间偏移: {current_time_offset}s")
            
            # 如果是第一个文件，包含完整的头部信息
            if i == 0:
                for line in lines:
                    line = line.rstrip('\n\r')  # 移除行尾换行符
                    if line.startswith('Dialogue:'):
                        # 调整对话时间戳
                        parts = line.split(',')
                        if len(parts) >= 10:
                            start_time = parts[1].strip()
                            end_time = parts[2].strip()
                            
                            # 转换时间并添加偏移
                            start_seconds = parse_ass_time(start_time) + current_time_offset
                            end_seconds = parse_ass_time(end_time) + current_time_offset
                            
                            # 转换回ASS时间格式
                            parts[1] = f" {format_ass_time(start_seconds)}"
                            parts[2] = f" {format_ass_time(end_seconds)}"
                            
                            # 清理字幕文本中的标点符号
                            if len(parts) >= 10:
                                subtitle_text = parts[9]
                                # 移除所有标点符号，但保留ASS标签
                                import re
                                # 先提取ASS标签
                                ass_tags = []
                                tag_pattern = r'\{[^}]*\}'
                                def replace_tag(match):
                                    ass_tags.append(match.group(0))
                                    return f'__ASS_TAG_{len(ass_tags)-1}__'
                                text_with_placeholders = re.sub(tag_pattern, replace_tag, subtitle_text)
                                # 移除标点符号
                                cleaned_text = re.sub(r'[，。；：、！？""''（）【】《》〈〉「」『』〔〕［］｛｝｜～·…—–,.;:!?"''()\[\]{}|~`@#$%^&*+=<>/\\-]', '', text_with_placeholders)
                                # 恢复ASS标签
                                for i, tag in enumerate(ass_tags):
                                    cleaned_text = cleaned_text.replace(f'__ASS_TAG_{i}__', tag)
                                parts[9] = cleaned_text
                            
                            merged_content.append(','.join(parts) + '\n')
                    elif line.strip():  # 只添加非空行
                        merged_content.append(line + '\n')
            else:
                # 对于后续文件，只处理对话行
                for line in lines:
                    line = line.rstrip('\n\r')  # 移除行尾换行符
                    if line.startswith('Dialogue:'):
                        parts = line.split(',')
                        if len(parts) >= 10:
                            start_time = parts[1].strip()
                            end_time = parts[2].strip()
                            
                            # 转换时间并添加偏移
                            start_seconds = parse_ass_time(start_time) + current_time_offset
                            end_seconds = parse_ass_time(end_time) + current_time_offset
                            
                            # 转换回ASS时间格式
                            parts[1] = f" {format_ass_time(start_seconds)}"
                            parts[2] = f" {format_ass_time(end_seconds)}"
                            
                            # 清理字幕文本中的标点符号
                            if len(parts) >= 10:
                                subtitle_text = parts[9]
                                # 移除所有标点符号，但保留ASS标签
                                import re
                                # 先提取ASS标签
                                ass_tags = []
                                tag_pattern = r'\{[^}]*\}'
                                def replace_tag(match):
                                    ass_tags.append(match.group(0))
                                    return f'__ASS_TAG_{len(ass_tags)-1}__'
                                text_with_placeholders = re.sub(tag_pattern, replace_tag, subtitle_text)
                                # 移除标点符号
                                cleaned_text = re.sub(r'[，。；：、！？""''（）【】《》〈〉「」『』〔〕［］｛｝｜～·…—–,.;:!?"\'\'(\)\[\]{}|~`@#$%^&*+=<>/\\-]', '', text_with_placeholders)
                                # 恢复ASS标签
                                for i, tag in enumerate(ass_tags):
                                    cleaned_text = cleaned_text.replace(f'__ASS_TAG_{i}__', tag)
                                parts[9] = cleaned_text
                            
                            merged_content.append(','.join(parts) + '\n')
        
        # 写入合并后的文件，确保没有多余的空行
        with open(output_path, 'w', encoding='utf-8') as f:
            f.writelines(merged_content)
        
        print(f"ASS文件合并成功：{output_path}")
        return True
    except Exception as e:
        print(f"ASS文件合并失败: {e}")
        return False

def process_chapter(chapter_path):
    """处理单个章节文件夹"""
    chapter_name = os.path.basename(chapter_path)
    print(f"\n处理章节: {chapter_name}")
    print(f"章节路径: {chapter_path}")
    
    # 查找first_video文件
    first_video_path = os.path.join(chapter_path, f"{chapter_name}_first_video.mp4")
    if not os.path.exists(first_video_path):
        print(f"警告: 未找到first_video文件: {first_video_path}")
        print(f"将仅使用图片生成视频")
        first_video_path = None
        # 设置默认视频参数
        width, height, fps, first_video_duration = 1920, 1080, 30, 0
    else:
        # 获取first_video信息
        width, height, fps, first_video_duration = get_video_info(first_video_path)
        if width is None:
            print(f"无法获取first_video信息: {first_video_path}")
            return False
        print(f"First video时长: {first_video_duration:.2f}s, 分辨率: {width}x{height}, 帧率: {fps}")
    
    # 查找所有narration ASS文件
    ass_files = sorted(glob.glob(os.path.join(chapter_path, f"{chapter_name}_narration_*.ass")))
    if not ass_files:
        print(f"未找到ASS字幕文件")
        return False
    
    print(f"找到 {len(ass_files)} 个ASS文件")
    
    # 计算每个narration的时长和对应的图片视频时长
    image_videos = []
    video_segments_info = []  # 记录每个视频段的时长
    temp_dir = os.path.join(chapter_path, "temp_videos")
    os.makedirs(temp_dir, exist_ok=True)
    
    # 如果有first_video，记录其时长
    if first_video_path:
        video_segments_info.append(first_video_duration)
    
    for i, ass_file in enumerate(ass_files):
        # 提取narration编号
        narration_match = re.search(r'narration_(\d+)', ass_file)
        if not narration_match:
            continue
        narration_num = narration_match.group(1)
        narration_num_int = int(narration_num)
        
        # 获取ASS文件时长
        ass_duration = get_ass_duration(ass_file)
        print(f"Narration {narration_num} ASS时长: {ass_duration:.2f}s")
        
        # 查找对应的图片文件
        image_num = str(narration_num_int).zfill(2)  # narration_01对应image_01
        if narration_num_int == 1:
            # narration_01特殊处理：只使用3和4的jpeg
            image_paths = [
                os.path.join(chapter_path, f"{chapter_name}_image_{image_num}_3.jpeg"),
                os.path.join(chapter_path, f"{chapter_name}_image_{image_num}_4.jpeg")
            ]
        else:
            # 其他narration：使用1、2、3、4四张jpeg
            image_paths = [
                os.path.join(chapter_path, f"{chapter_name}_image_{image_num}_1.jpeg"),
                os.path.join(chapter_path, f"{chapter_name}_image_{image_num}_2.jpeg"),
                os.path.join(chapter_path, f"{chapter_name}_image_{image_num}_3.jpeg"),
                os.path.join(chapter_path, f"{chapter_name}_image_{image_num}_4.jpeg")
            ]
        
        # 查找对应的音频文件和timestamps文件
        audio_file = ass_file.replace('.ass', '.mp3')
        timestamps_file = ass_file.replace('.ass', '_timestamps.json')
        
        # 检查图片文件是否都存在，如果不存在则跳过
        missing_images = [img for img in image_paths if not os.path.exists(img)]
        if missing_images:
            print(f"跳过 Narration {narration_num}: 缺少图片文件 {missing_images}")
            continue
        
        # 检查音频文件是否存在
        if not os.path.exists(audio_file):
            print(f"跳过 Narration {narration_num}: 未找到音频文件 {audio_file}")
            continue
        
        # narration_01特殊处理：使用timestamps时长减去10秒，只生成image_01_2.jpeg的视频
        if narration_num_int == 1:
            narration_01_duration = get_timestamps_duration(timestamps_file)
            calculated_duration = max(0, narration_01_duration - 10)  # 减去10秒，确保不为负数
            print(f"Narration {narration_num}: 特殊计算时长 {narration_01_duration:.2f}s - 10s = {calculated_duration:.2f}s")
            
            # 只使用image_01_4.jpeg生成视频
            image_01_4_path = os.path.join(chapter_path, f"{chapter_name}_image_01_4.jpeg")
            if not os.path.exists(image_01_4_path):
                print(f"跳过 Narration {narration_num}: 缺少图片文件 {image_01_4_path}")
                continue
            
            narration_video_path = os.path.join(temp_dir, f"narration_{narration_num}.mp4")
            if image_to_video(image_01_4_path, narration_video_path, duration=calculated_duration,
                            width=width, height=height, fps=fps):
                image_videos.append(narration_video_path)
                video_segments_info.append(calculated_duration)
                print(f"Narration {narration_num} 视频生成成功，时长: {calculated_duration:.2f}s")
            else:
                print(f"生成Narration {narration_num}视频失败")
            continue
        
        # 计算图片视频时长
        if narration_num_int == 2:
            # image_02.mp4使用特殊逻辑：narration_01时长 - first_video时长 + narration_02时长
            narration_01_timestamps = os.path.join(chapter_path, f"{chapter_name}_narration_01_timestamps.json")
            narration_01_duration = 0
            if os.path.exists(narration_01_timestamps):
                narration_01_duration = get_timestamps_duration(narration_01_timestamps)
            
            narration_02_duration = get_timestamps_duration(timestamps_file)
            
            calculated_duration = narration_01_duration - first_video_duration + narration_02_duration
            print(f"Image_02特殊计算: {narration_01_duration:.2f}s - {first_video_duration:.2f}s + {narration_02_duration:.2f}s = {calculated_duration:.2f}s")
        else:
            # 其他image视频使用对应的timestamps时长
            calculated_duration = get_timestamps_duration(timestamps_file)
            print(f"Narration {narration_num}: 使用timestamps时长 {calculated_duration:.2f}s")
        
        # 为每个narration生成图片视频，每个时长为总时长除以图片数量
        segment_duration = calculated_duration / len(image_paths)
        narration_videos = []
        
        for j, image_path in enumerate(image_paths, 1):
            image_video_path = os.path.join(temp_dir, f"image_{narration_num}_{j}.mp4")
            if image_to_video(image_path, image_video_path, duration=segment_duration,
                            width=width, height=height, fps=fps):
                narration_videos.append(image_video_path)
                print(f"Narration {narration_num} 图片{j}视频生成成功，时长: {segment_duration:.2f}s")
            else:
                print(f"生成图片视频失败: {image_path}")
                break
        
        # 只有当所有图片视频都生成成功时，才拼接它们
        if len(narration_videos) == len(image_paths):
            # 拼接所有图片视频为一个narration视频
            narration_video_path = os.path.join(temp_dir, f"narration_{narration_num}.mp4")
            if concat_videos(narration_videos, narration_video_path):
                image_videos.append(narration_video_path)
                video_segments_info.append(calculated_duration)
                print(f"Narration {narration_num} 完整视频生成成功，时长: {calculated_duration:.2f}s")
                
                # 清理临时的单个图片视频文件
                for temp_video in narration_videos:
                    try:
                        os.remove(temp_video)
                    except:
                        pass
            else:
                print(f"拼接narration {narration_num}的图片视频失败")
        else:
            print(f"Narration {narration_num} 图片视频生成不完整，跳过")
    
    if not image_videos:
        print("没有成功生成任何图片视频")
        return False
    
    # 拼接所有视频（first_video + 所有图片视频）
    if first_video_path:
        all_videos = [first_video_path] + image_videos
    else:
        all_videos = image_videos
    
    concatenated_video = os.path.join(temp_dir, "concatenated.mp4")
    
    if len(all_videos) == 1:
        # 如果只有一个视频，直接复制
        import shutil
        shutil.copy2(all_videos[0], concatenated_video)
        print(f"视频复制成功：{concatenated_video}")
    else:
        if not concat_videos(all_videos, concatenated_video):
            return False
    
    # 合并所有ASS字幕文件
    merged_ass_file = os.path.join(temp_dir, "merged_subtitles.ass")
    if not merge_ass_files(ass_files, merged_ass_file, video_segments_info):
        print("字幕合并失败，使用第一个ASS文件")
        merged_ass_file = ass_files[0]
    
    # 清理ASS文件中的标点符号
    if not clean_ass_punctuation(merged_ass_file):
        print("警告：清理ASS文件标点符号失败，继续处理")
    
    # 添加合并后的字幕
    video_with_sub = os.path.join(temp_dir, "video_with_sub.mp4")
    if not add_subtitle(concatenated_video, merged_ass_file, video_with_sub):
        return False
    
    # 跳过添加角标步骤，因为每个视频片段已经包含了fuceng.mp4和rmxs.png效果
    video_with_watermark = video_with_sub
    
    # 查找并拼接所有可用的音频文件
    audio_files = []
    for ass_file in ass_files:
        audio_file = ass_file.replace('.ass', '.mp3')
        if os.path.exists(audio_file):
            audio_files.append(audio_file)
            print(f"找到音频文件: {audio_file}")
    
    final_output = os.path.join(chapter_path, f"{chapter_name}_final_video.mp4")
    
    if audio_files:
        # 先拼接所有台词音频文件
        merged_narration_audio = os.path.join(temp_dir, "merged_narration.mp3")
        if concat_audio_files(audio_files, merged_narration_audio):
            # 获取视频总时长
            video_info = get_video_info(video_with_watermark)
            total_video_duration = video_info[3] if video_info[3] else sum(video_segments_info)
            
            # 将台词音频与BGM和音效混合
            mixed_audio_file = os.path.join(temp_dir, "mixed_audio.mp3")
            if mix_audio_with_bgm_and_effects(merged_narration_audio, total_video_duration, mixed_audio_file, merged_ass_file):
                # 添加混合后的音频
                if add_audio(video_with_watermark, mixed_audio_file, final_output, replace=True):
                    print(f"✓ 章节视频生成成功: {final_output}")
                else:
                    print(f"添加音频失败，但保存无音频版本: {final_output}")
                    import shutil
                    shutil.copy2(video_with_watermark, final_output)
            else:
                print(f"音频混合失败，使用原始台词音频")
                if add_audio(video_with_watermark, merged_narration_audio, final_output, replace=True):
                    print(f"✓ 章节视频生成成功(仅台词音频): {final_output}")
                else:
                    print(f"添加音频失败，保存无音频版本: {final_output}")
                    import shutil
                    shutil.copy2(video_with_watermark, final_output)
        else:
            print(f"音频拼接失败，保存无音频版本: {final_output}")
            import shutil
            shutil.copy2(video_with_watermark, final_output)
    else:
        print(f"未找到任何音频文件，保存无音频版本: {final_output}")
        import shutil
        shutil.copy2(video_with_watermark, final_output)
    
    # 检查视频是否符合输出标准
    print("\n=== 检查视频输出标准 ===")
    if os.path.exists(final_output):
        if not check_video_standards(final_output):
            # 如果文件大小超标，尝试优化
            file_size_mb = get_file_size_mb(final_output)
            if file_size_mb > VIDEO_STANDARDS['max_size_mb']:
                print(f"\n文件大小超标，开始优化...")
                optimized_output = final_output.replace('.mp4', '_optimized.mp4')
                
                if optimize_video_for_size(final_output, optimized_output, VIDEO_STANDARDS['max_size_mb']):
                    # 优化成功，替换原文件
                    import shutil
                    shutil.move(optimized_output, final_output)
                    print(f"✓ 视频优化完成，已替换原文件: {final_output}")
                    
                    # 再次检查优化后的文件
                    check_video_standards(final_output)
                else:
                    print(f"❌ 视频优化失败，保留原文件: {final_output}")
                    # 清理失败的优化文件
                    if os.path.exists(optimized_output):
                        os.remove(optimized_output)
        else:
            print(f"✓ 视频符合所有输出标准")
    else:
        print(f"❌ 最终视频文件不存在: {final_output}")
    
    # 清理临时文件
    try:
        # import shutil
        # shutil.rmtree(temp_dir)
        print(f"\n清理临时文件: {temp_dir}")
    except Exception as e:
        print(f"清理临时文件失败: {e}")
    
    return True

def main():
    parser = argparse.ArgumentParser(description='视频生成脚本')
    parser.add_argument('input_path', help='输入路径（可以是单个章节目录或包含多个章节的数据目录）')
    args = parser.parse_args()
    
    input_path = args.input_path
    if not os.path.exists(input_path):
        print(f"路径不存在: {input_path}")
        return
    
    # 检测输入路径类型
    chapter_dirs = []
    
    # 检查是否是单个章节目录
    if os.path.basename(input_path).startswith('chapter_') and os.path.isfile(os.path.join(input_path, 'narration.txt')):
        # 单个章节目录
        chapter_dirs = [input_path]
        print(f"检测到单个章节目录: {os.path.basename(input_path)}")
    else:
        # 数据目录，查找所有chapter文件夹
        chapter_dirs = sorted([d for d in glob.glob(os.path.join(input_path, "chapter_*")) 
                              if os.path.isdir(d)])
        
        if chapter_dirs:
            print(f"检测到数据目录，找到 {len(chapter_dirs)} 个章节文件夹")
    
    if not chapter_dirs:
        print(f"在 {input_path} 中没有找到有效的章节目录")
        return
    
    success_count = 0
    for chapter_dir in chapter_dirs:
        try:
            if process_chapter(chapter_dir):
                success_count += 1
            else:
                print(f"处理章节失败: {os.path.basename(chapter_dir)}")
        except Exception as e:
            print(f"处理章节时发生错误: {os.path.basename(chapter_dir)}, 错误: {e}")
    
    print(f"\n处理完成! 成功: {success_count}/{len(chapter_dirs)}")
    
    # 最终检查所有生成的视频文件
    if success_count > 0:
        print("\n=== 最终视频标准检查汇总 ===")
        print(f"视频输出标准: {VIDEO_STANDARDS['width']}x{VIDEO_STANDARDS['height']}px, {VIDEO_STANDARDS['fps']}fps, H.264编码, 音频{VIDEO_STANDARDS['audio_bitrate']}, 最大{VIDEO_STANDARDS['max_size_mb']}MB")
        
        total_videos = 0
        compliant_videos = 0
        oversized_videos = []
        
        for chapter_dir in chapter_dirs:
            chapter_name = os.path.basename(chapter_dir)
            final_video = os.path.join(chapter_dir, f"{chapter_name}_final_video.mp4")
            
            if os.path.exists(final_video):
                total_videos += 1
                file_size_mb = get_file_size_mb(final_video)
                width, height, fps, duration = get_video_info(final_video)
                
                print(f"\n{chapter_name}: {file_size_mb:.2f}MB, {width}x{height}px, {fps}fps, {duration:.2f}s")
                
                if file_size_mb <= VIDEO_STANDARDS['max_size_mb']:
                    compliant_videos += 1
                    print(f"  ✓ 符合大小标准")
                else:
                    oversized_videos.append((chapter_name, file_size_mb))
                    print(f"  ❌ 超过大小限制 ({file_size_mb:.2f}MB > {VIDEO_STANDARDS['max_size_mb']}MB)")
                
                if duration < VIDEO_STANDARDS['min_duration_warning']:
                    print(f"  ⚠️  时长提醒: {duration:.2f}s < {VIDEO_STANDARDS['min_duration_warning']}s")
        
        print(f"\n=== 汇总结果 ===")
        print(f"总视频数: {total_videos}")
        print(f"符合大小标准: {compliant_videos}/{total_videos} ({compliant_videos/total_videos*100:.1f}%)")
        
        if oversized_videos:
            print(f"\n❌ 超大小限制的视频:")
            for name, size in oversized_videos:
                print(f"  - {name}: {size:.2f}MB")
            print(f"\n建议: 对超大小限制的视频运行优化功能")
        else:
            print(f"\n✓ 所有视频都符合大小标准!")
        
        print(f"\n注意: 时长小于3分钟的视频仅为提醒，不影响标准符合性。")

if __name__ == "__main__":
    main()