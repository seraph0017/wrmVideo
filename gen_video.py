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
    """获取音频文件的时长"""
    try:
        probe = ffmpeg.probe(audio_path)
        duration = float(probe['format']['duration'])
        return duration
    except Exception as e:
        print(f"获取音频时长失败: {e}")
        return 0

def image_to_video(image_path, output_path, duration=5, width=780, height=1280, fps=30):
    """将图片转换为视频片段"""
    try:
        (
            ffmpeg
            .input(image_path, loop=1, t=duration)
            .filter('scale', width, height)
            .output(output_path, r=fps, vcodec='libx264', pix_fmt='yuv420p')
            .overwrite_output()
            .run(quiet=True)
        )
        print(f"图片转视频成功：{output_path} (时长: {duration}s)")
        return True
    except Exception as e:
        print(f"图片转视频失败: {e}")
        return False

def concat_videos(video_list, output_path):
    """拼接多个视频片段，处理不同格式和流情况"""
    try:
        # 检查每个输入文件是否有音频流
        has_audio = []
        for video in video_list:
            probe = ffmpeg.probe(video)
            audio_streams = [s for s in probe['streams'] if s['codec_type'] == 'audio']
            has_audio.append(len(audio_streams) > 0)
        
        # 创建输入流
        inputs = [ffmpeg.input(v) for v in video_list]
        
        # 根据是否所有输入都有音频，调整concat参数
        if all(has_audio):
            # 所有输入都有音频，拼接视频和音频
            stream = ffmpeg.concat(*inputs, v=1, a=1).output(output_path)
        elif not any(has_audio):
            # 所有输入都没有音频，只拼接视频
            stream = ffmpeg.concat(*inputs, v=1, a=0).output(output_path)
        else:
            # 部分输入有音频，需要特殊处理（这里选择忽略音频）
            print("警告：部分输入有音频，部分没有。拼接结果将不含音频。")
            video_streams = [i.video for i in inputs]
            stream = ffmpeg.concat(*video_streams, v=1, a=0).output(output_path)
        
        # 执行拼接
        stream.overwrite_output().run(quiet=True)
        print(f"视频拼接成功：{output_path}")
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
            .run(quiet=True)
        )
        print(f"添加字幕成功：{output_path}")
        return True
    except Exception as e:
        print(f"添加字幕失败: {e}")
        return False

def add_audio(video_path, audio_path, output_path, replace=True):
    """为视频添加音频（替换或混合）"""
    try:
        video = ffmpeg.input(video_path)
        audio = ffmpeg.input(audio_path)
        
        if replace:
            # 替换原音频
            (
                ffmpeg
                .output(video.video, audio.audio, output_path, c='copy')
                .overwrite_output()
                .run(quiet=True)
            )
        else:
            # 混合原音频和新音频
            (
                ffmpeg
                .filter([video.audio, audio.audio], 'amix', inputs=2, duration='shortest')
                .output(video.video, 'a', output_path)
                .overwrite_output()
                .run(quiet=True)
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
            .run(quiet=True)
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

def format_ass_time(seconds):
    """将秒数转换为ASS时间格式"""
    hours = int(seconds // 3600)
    minutes = int((seconds % 3600) // 60)
    secs = seconds % 60
    return f"{hours}:{minutes:02d}:{secs:05.2f}"

def process_chapter(chapter_path):
    """处理单个章节文件夹"""
    chapter_name = os.path.basename(chapter_path)
    print(f"\n处理章节: {chapter_name}")
    
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
        image_num = str(narration_num_int + 1).zfill(2)  # narration_01对应image_02
        image_path = os.path.join(chapter_path, f"{chapter_name}_image_{image_num}.jpeg")
        
        # 查找对应的音频文件
        audio_file = ass_file.replace('.ass', '.mp3')
        
        # 根据narration编号决定使用哪种逻辑
        if narration_num_int <= 2:
            # narration1和narration2: 使用image_to_video逻辑
            if i == 0:
                # 第一个narration: ASS结束时间 - first_video时长 + 第二个narration的ASS结束时间
                second_ass_duration = 0
                if len(ass_files) > 1:
                    second_ass_duration = get_ass_duration(ass_files[1])
                    print(f"第二个narration ASS时长: {second_ass_duration:.2f}s")
                
                image_duration = max(0, (ass_duration - first_video_duration) + second_ass_duration)
            else:
                # 第二个narration: 使用ASS的完整时长
                image_duration = ass_duration
            
            print(f"Narration {narration_num} 图片视频时长 (image_to_video): {image_duration:.2f}s")
            
            if image_duration > 0 and os.path.exists(image_path):
                # 生成图片视频
                image_video_path = os.path.join(temp_dir, f"image_{narration_num}.mp4")
                if image_to_video(image_path, image_video_path, duration=image_duration, 
                                width=width, height=height, fps=fps):
                    image_videos.append(image_video_path)
                    video_segments_info.append(image_duration)
                else:
                    print(f"生成图片视频失败: {image_path}")
            else:
                if not os.path.exists(image_path):
                    print(f"未找到图片文件: {image_path}")
        else:
            # narration3及以后: 使用mp3时长生成视频
            if os.path.exists(audio_file):
                audio_duration = get_audio_duration(audio_file)
                print(f"Narration {narration_num} 音频时长: {audio_duration:.2f}s")
                
                if audio_duration > 0 and os.path.exists(image_path):
                    # 使用音频时长生成图片视频
                    image_video_path = os.path.join(temp_dir, f"image_{narration_num}.mp4")
                    if image_to_video(image_path, image_video_path, duration=audio_duration, 
                                    width=width, height=height, fps=fps):
                        image_videos.append(image_video_path)
                        video_segments_info.append(audio_duration)
                        print(f"Narration {narration_num} 图片视频时长 (按音频): {audio_duration:.2f}s")
                    else:
                        print(f"生成图片视频失败: {image_path}")
                else:
                    if not os.path.exists(image_path):
                        print(f"未找到图片文件: {image_path}")
                    if audio_duration <= 0:
                        print(f"音频时长无效: {audio_file}")
            else:
                print(f"未找到音频文件: {audio_file}")
    
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
            if add_audio(video_with_sub, merged_audio_file, final_output, replace=True):
                print(f"✓ 章节视频生成成功: {final_output}")
            else:
                print(f"添加音频失败，但保存无音频版本: {final_output}")
                import shutil
                shutil.copy2(video_with_sub, final_output)
        else:
            print(f"音频拼接失败，保存无音频版本: {final_output}")
            import shutil
            shutil.copy2(video_with_sub, final_output)
    else:
        print(f"未找到任何音频文件，保存无音频版本: {final_output}")
        import shutil
        shutil.copy2(video_with_sub, final_output)
    
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