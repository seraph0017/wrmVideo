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

def image_to_video(image_path, output_path, duration=5, width=780, height=1280, fps=30, fade_duration=0.5, audio_path=None):
    """将图片转换为视频片段，添加Ken Burns效果和平移效果
    
    Args:
        image_path: 图片文件路径
        output_path: 输出视频路径
        duration: 视频时长（秒），如果提供了audio_path则会被覆盖
        width: 视频宽度
        height: 视频高度
        fps: 帧率
        fade_duration: 保留参数以兼容性（现在用于平移距离控制）
        audio_path: 音频文件路径，如果提供则使用音频时长作为视频时长
    """
    # 如果提供了音频文件，使用音频时长
    if audio_path and os.path.exists(audio_path):
        audio_duration = get_audio_duration(audio_path)
        if audio_duration > 0:
            duration = audio_duration
            print(f"使用音频时长: {duration:.2f}s (音频文件: {audio_path})")
        else:
            print(f"警告: 无法获取音频时长，使用默认时长: {duration}s")
    
    print(f"开始转换图片到视频: {image_path} -> {output_path}, 时长: {duration}s")
    try:
        # 计算平移参数 - 增强动态效果
        total_frames = int(duration * fps)
        pan_distance = 300  # 增加平移距离（像素）
        
        (
            ffmpeg
            .input(image_path, loop=1, t=duration)
            .filter('scale', width*3, -1)  # 放大3倍以便有更大的平移空间
            .filter('zoompan', 
                   z='min(zoom+0.003,2.0)',  # 增强缩放效果，更明显的缩放变化
                   x=f'iw/2-(iw/zoom/2)+({pan_distance}*on/{total_frames})',  # 水平平移：从左到右，增加距离
                   y=f'ih/2-(ih/zoom/2)+({pan_distance/3}*on/{total_frames})',  # 垂直平移：从上到下，适度调整
                   d=1, fps=fps, s=f"{width}x{height}")
            .output(output_path, r=fps, vcodec='libx264', pix_fmt='yuv420p', preset='ultrafast')
            .overwrite_output()
            .run(quiet=False)  # 改为非安静模式以显示ffmpeg进度
        )
        print(f"图片转视频成功（带Ken Burns效果和平移）：{output_path} (时长: {duration}s)")
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
            # 使用ffmpeg命令行工具拼接
            subprocess.run([
                'ffmpeg', '-f', 'concat', '-safe', '0', '-i', filelist_path,
                '-c', 'copy', output_path, '-y'
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
    """为视频添加右上角角标"""
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
        
        video_input = ffmpeg.input(video_path)
        watermark_input = ffmpeg.input(watermark_path, loop=1)  # 循环播放角标
        
        (
            ffmpeg
            .filter([video_input, watermark_input], 'overlay', 
                   x='W-w',  # 右上角贴边：视频宽度-角标宽度
                   y=0,      # 上边距0像素，完全贴边
                   shortest=1)  # 确保角标持续到视频结束
            .output(output_path, vcodec='libx264', acodec='copy')
            .overwrite_output()
            .run()
        )
        print(f"添加角标成功：{output_path}")
        return True
    except Exception as e:
        print(f"添加角标失败: {e}")
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
                .output(video, audio, output_path, vcodec='libx264', acodec='aac')
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

def merge_ass_files(ass_files, output_path, video_segments_info):
    """合并多个ASS文件，调整时间戳"""
    try:
        merged_content = []
        
        # 计算每个ASS文件的实际时长，用于累积时间偏移
        ass_durations = []
        for ass_file in ass_files:
            duration = get_ass_duration(ass_file)
            ass_durations.append(duration)
            print(f"ASS文件 {ass_file} 时长: {duration:.2f}s")
        
        # 计算累积时间偏移（基于ASS文件的实际时长）
        time_offsets = [0]  # 第一个文件从0开始
        for i in range(len(ass_durations)):
            if i > 0:  # 从第二个文件开始累加
                time_offsets.append(time_offsets[-1] + ass_durations[i-1])
        
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
        image_path = os.path.join(chapter_path, f"{chapter_name}_image_{image_num}.jpeg")
        
        # 查找对应的音频文件和timestamps文件
        audio_file = ass_file.replace('.ass', '.mp3')
        timestamps_file = ass_file.replace('.ass', '_timestamps.json')
        
        # 检查图片文件是否存在，如果不存在则跳过
        if not os.path.exists(image_path):
            print(f"跳过 Narration {narration_num}: 未找到图片文件 {image_path}")
            continue
        
        # 检查音频文件是否存在
        if not os.path.exists(audio_file):
            print(f"跳过 Narration {narration_num}: 未找到音频文件 {audio_file}")
            continue
        
        # 跳过narration_01，直接从narration_02开始生成
        if narration_num_int == 1:
            print(f"跳过 Narration {narration_num}: 不生成image_01.mp4")
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
        
        # 生成图片视频，使用计算出的时长
        image_video_path = os.path.join(temp_dir, f"image_{narration_num}.mp4")
        if image_to_video(image_path, image_video_path, duration=calculated_duration,
                        width=width, height=height, fps=fps):
            image_videos.append(image_video_path)
            video_segments_info.append(calculated_duration)
            print(f"Narration {narration_num} 图片视频生成成功，时长: {calculated_duration:.2f}s")
        else:
            print(f"生成图片视频失败: {image_path}")
    
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
    
    # 添加合并后的字幕
    video_with_sub = os.path.join(temp_dir, "video_with_sub.mp4")
    if not add_subtitle(concatenated_video, merged_ass_file, video_with_sub):
        return False
    
    # 添加角标
    watermark_path = os.path.join(os.path.dirname(os.path.abspath(__file__)), "src", "banner", "rmxs.png")
    video_with_watermark = os.path.join(temp_dir, "video_with_watermark.mp4")
    if not add_watermark(video_with_sub, watermark_path, video_with_watermark):
        return False
    
    # 查找并拼接所有可用的音频文件
    audio_files = []
    for ass_file in ass_files:
        audio_file = ass_file.replace('.ass', '.mp3')
        if os.path.exists(audio_file):
            audio_files.append(audio_file)
            print(f"找到音频文件: {audio_file}")
    
    final_output = os.path.join(chapter_path, f"{chapter_name}_final_video.mp4")
    
    if audio_files:
        # 拼接所有音频文件
        merged_audio_file = os.path.join(temp_dir, "merged_audio.mp3")
        if concat_audio_files(audio_files, merged_audio_file):
            # 添加合并后的音频
            if add_audio(video_with_watermark, merged_audio_file, final_output, replace=True):
                print(f"✓ 章节视频生成成功: {final_output}")
            else:
                print(f"添加音频失败，但保存无音频版本: {final_output}")
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
    
    # 清理临时文件
    try:
        # import shutil
        # shutil.rmtree(temp_dir)
        print(f"清理临时文件: {temp_dir}")
    except Exception as e:
        print(f"清理临时文件失败: {e}")
    
    return True

def main():
    parser = argparse.ArgumentParser(description='视频生成脚本')
    parser.add_argument('data_dir', help='数据目录路径 (例如: data/002)')
    args = parser.parse_args()
    
    data_dir = args.data_dir
    if not os.path.exists(data_dir):
        print(f"数据目录不存在: {data_dir}")
        return
    
    # 查找所有chapter文件夹
    chapter_dirs = sorted([d for d in glob.glob(os.path.join(data_dir, "chapter_*")) 
                          if os.path.isdir(d)])
    
    if not chapter_dirs:
        print(f"在 {data_dir} 中未找到chapter文件夹")
        return
    
    print(f"找到 {len(chapter_dirs)} 个章节文件夹")
    
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

if __name__ == "__main__":
    main()