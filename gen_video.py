#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
独立的视频生成脚本
从图片、音频和字幕生成视频，支持根据timestamps精确分段
"""

import os
import sys
import re
import json
import ffmpeg
import argparse

# 添加src目录到路径
src_dir = os.path.join(os.path.dirname(__file__), 'src')
sys.path.insert(0, src_dir)

def clean_text_for_tts(text):
    """
    清理文本用于TTS生成，移除括号内的内容和&符号
    
    Args:
        text: 原始文本
    
    Returns:
        str: 清理后的文本
    """
    # 移除各种括号及其内容
    text = re.sub(r'\([^)]*\)', '', text)  # 移除圆括号内容
    text = re.sub(r'\[[^\]]*\]', '', text)  # 移除方括号内容
    text = re.sub(r'\{[^}]*\}', '', text)  # 移除花括号内容
    text = re.sub(r'（[^）]*）', '', text)  # 移除中文圆括号内容
    text = re.sub(r'【[^】]*】', '', text)  # 移除中文方括号内容
    
    # 移除&符号
    text = text.replace('&', '')
    
    # 清理多余的空格
    text = re.sub(r'\s+', ' ', text).strip()
    
    return text

def wrap_text(text, max_chars_per_line=20):
    """
    处理字幕文本，确保只显示一行字幕且不超出边框
    
    Args:
        text: 原始文本
        max_chars_per_line: 每行最大字符数（默认20，确保不超出边框）
    
    Returns:
        str: 处理后的单行文本
    """
    # 去掉首尾的标点符号
    punctuation = '。！？，；：、""''（）()[]{}【】《》<>'
    text = text.strip(punctuation + ' \t\n')
    
    # 移除引号内的内容，避免字幕过长
    text = re.sub(r'"[^"]*"', '', text)  # 移除双引号内容
    text = re.sub(r'"[^"]*"', '', text)  # 移除中文双引号内容
    text = re.sub(r"'[^']*'", '', text)  # 移除中文单引号内容
    
    # 清理多余的空格
    text = re.sub(r'\s+', ' ', text).strip()
    
    # 如果文本过长，截取前面部分并添加省略号
    if len(text) > max_chars_per_line:
        text = text[:max_chars_per_line-3] + "..."
    
    # 确保返回单行文本，移除所有换行符
    text = text.replace('\n', ' ').replace('\r', ' ')
    
    return text

def split_text_by_timestamps(text, timestamps, max_chars_per_segment=40):
    """
    根据时间戳分割文本，优化分割策略以避免在词语中间分割
    
    Args:
        text: 完整文本
        timestamps: character_timestamps列表
        max_chars_per_segment: 每段最大字符数
    
    Returns:
        list: 包含(文本片段, 开始时间, 结束时间)的元组列表
    """
    segments = []
    current_text = ""
    start_time = 0
    
    # 定义自然停顿的标点符号（优先级从高到低）
    major_punctuation = ['。', '！', '？']  # 句子结束符，优先分割
    minor_punctuation = ['，', '；', '：', '、']  # 次要停顿符
    
    # 定义词边界字符（中文常见的词尾字符）
    word_boundary_chars = ['的', '了', '着', '过', '地', '得', '在', '与', '和', '或', '但', '而', '然', '后', '前', '中', '上', '下', '内', '外']
    
    for i, char_info in enumerate(timestamps):
        char = char_info['character']
        char_start = char_info['start_time']
        char_end = char_info['end_time']
        
        # 如果是第一个字符，记录开始时间
        if not current_text:
            start_time = char_start
        
        current_text += char
        
        # 检查是否需要分段
        should_split = False
        split_priority = 0  # 分割优先级，数字越大优先级越高
        
        # 如果是最后一个字符，必须分段
        if i == len(timestamps) - 1:
            should_split = True
            split_priority = 100
        
        # 检查各种分割条件
        elif len(current_text) >= max_chars_per_segment:
            # 达到最大字符数，需要寻找合适的分割点
            if char in major_punctuation:
                # 遇到主要标点符号，立即分割
                should_split = True
                split_priority = 90
            elif char in minor_punctuation:
                # 遇到次要标点符号，优先分割
                should_split = True
                split_priority = 80
            elif char in word_boundary_chars:
                # 遇到词边界字符，可以分割
                should_split = True
                split_priority = 70
            elif len(current_text) >= max_chars_per_segment + 5:
                # 超出太多字符，强制分割
                should_split = True
                split_priority = 60
        
        # 在合适长度下遇到自然停顿点
        elif len(current_text) >= 8:  # 最小长度要求
            if char in major_punctuation:
                # 遇到主要标点符号，分割
                should_split = True
                split_priority = 85
            elif char in minor_punctuation and len(current_text) >= 12:
                # 遇到次要标点符号且长度适中，分割
                should_split = True
                split_priority = 75
        
        # 寻找更好的分割点（向前回溯）
        if should_split and len(current_text) > 15 and split_priority < 80:
            # 尝试在最近的标点符号处分割
            best_split_pos = -1
            best_priority = 0
            
            # 向前回溯最多5个字符寻找更好的分割点
            for j in range(min(5, len(current_text) - 8)):
                check_pos = len(current_text) - 1 - j
                if check_pos < 8:  # 确保最小长度
                    break
                    
                check_char = current_text[check_pos]
                check_priority = 0
                
                if check_char in major_punctuation:
                    check_priority = 85
                elif check_char in minor_punctuation:
                    check_priority = 75
                elif check_char in word_boundary_chars:
                    check_priority = 65
                
                if check_priority > best_priority:
                    best_split_pos = check_pos + 1  # 在标点符号后分割
                    best_priority = check_priority
            
            # 如果找到更好的分割点，调整分割位置
            if best_split_pos > 0 and best_priority > split_priority:
                # 回退到更好的分割点
                split_text = current_text[:best_split_pos]
                remaining_text = current_text[best_split_pos:]
                
                # 计算分割点的时间戳
                split_timestamp_index = i - len(remaining_text)
                if split_timestamp_index >= 0:
                    split_end_time = timestamps[split_timestamp_index]['end_time']
                    
                    # 添加分割的片段
                    if split_text.strip():
                        segments.append((split_text.strip(), start_time, split_end_time))
                    
                    # 重置当前文本为剩余部分
                    current_text = remaining_text
                    start_time = timestamps[split_timestamp_index + 1]['start_time'] if split_timestamp_index + 1 < len(timestamps) else char_start
                    should_split = False
        
        if should_split and current_text.strip():
            segments.append((current_text.strip(), start_time, char_end))
            current_text = ""
    
    return segments

def create_video_segment_with_timing(image_path, audio_path, text_segment, start_time, end_time, output_path, is_first_segment=False):
    """
    创建带有精确时间控制的视频片段
    
    Args:
        image_path: 图片文件路径
        audio_path: 音频文件路径
        text_segment: 字幕文本片段
        start_time: 开始时间（秒）
        end_time: 结束时间（秒）
        output_path: 输出视频路径
        is_first_segment: 是否为第一个片段
    
    Returns:
        bool: 是否成功生成
    """
    try:
        # 确保输出目录存在
        output_dir = os.path.dirname(output_path)
        if output_dir:
            os.makedirs(output_dir, exist_ok=True)
        
        print(f"正在创建视频片段: {os.path.basename(output_path)}")
        print(f"时间范围: {start_time:.2f}s - {end_time:.2f}s")
        print(f"字幕内容: {text_segment}")
        
        # 计算片段时长
        duration = end_time - start_time
        
        # 创建输入流，使用超高精度时间参数
        # 将时间精度提高到微秒级别（6位小数）
        precise_start_time = f"{start_time:.6f}"
        precise_duration = f"{duration:.6f}"
        
        print(f"精确时间参数 - 开始时间: {precise_start_time}s, 持续时间: {precise_duration}s")
        
        # 图片输入：循环播放，持续时间为片段时长
        image_input = ffmpeg.input(image_path, loop=1, t=precise_duration)
        
        # 字幕提前显示时间（秒）- 让字幕稍微早于声音出现
        subtitle_advance_time = 0.15  # 字幕提前0.15秒显示
        
        # 音频输入：先切割指定时间段的音频，然后重新从0开始
        # 这样可以避免片段开头的静音问题
        audio_segment = ffmpeg.input(audio_path, 
                                   ss=precise_start_time, 
                                   t=precise_duration,
                                   accurate_seek=None,
                                   avoid_negative_ts='make_zero')
        
        # 将切割后的音频重新设置为从0开始，避免时间偏移导致的静音
        # 只在第一个片段添加音频延迟以实现字幕提前显示，避免拼接时的间隙
        if is_first_segment:
            audio_input = audio_segment.filter('asetpts', 'PTS-STARTPTS').filter('adelay', f'{int(subtitle_advance_time * 1000)}|{int(subtitle_advance_time * 1000)}')
        else:
            audio_input = audio_segment.filter('asetpts', 'PTS-STARTPTS')
        
        # 不使用图片特效，直接使用原始视频流
        video_with_effects = image_input.video
        
        # 清理字幕文本
        clean_subtitle = clean_text_for_tts(text_segment)
        
        if clean_subtitle.strip():
            # 视频尺寸设置
            video_width = 720
            video_height = 1280
            
            # 处理字幕文本，确保不超出边框
            wrapped_subtitle = wrap_text(clean_subtitle, max_chars_per_line=30)
            
            # 字幕位置：使用FFmpeg表达式确保显示在底部
            subtitle_y = 'h-text_h-h/3'  # 距离底部1/3视频高度像素
            
            print(f"调试信息 - 视频尺寸: {video_width}x{video_height}")
            print(f"调试信息 - 字幕文本: '{wrapped_subtitle}'")
            print(f"调试信息 - 字幕Y位置表达式: {subtitle_y}")
            
            # 计算字幕显示时间范围，只在第一个片段让字幕提前显示
            if is_first_segment:
                subtitle_start_time = 0  # 字幕从视频开始就显示
                subtitle_end_time = duration + subtitle_advance_time  # 字幕显示到音频结束后
            else:
                subtitle_start_time = 0  # 字幕从视频开始就显示
                subtitle_end_time = duration  # 字幕显示到音频结束
            
            # 添加字幕滤镜（黑体字，透明背景，每行居中，确保不超出边框）
            # 通过enable参数控制字幕显示时间，实现提前显示效果
            video_with_subtitle = video_with_effects.filter(
                'drawtext',
                text=wrapped_subtitle,
                fontfile='/System/Library/Fonts/Helvetica-Bold.ttc',  # 使用黑体字体
                fontsize=72,  # 增大字号到72以便更清晰可见
                fontcolor='black',
                x='max(20, min(w-text_w-20, (w-text_w)/2))',  # 水平居中，确保边距
                y=subtitle_y,
                borderw=3,  # 增加描边宽度
                bordercolor='white',
                box=0,  # 透明背景
                enable=f'gte(t,{subtitle_start_time})*lte(t,{subtitle_end_time})'  # 控制字幕显示时间
            )
        else:
            video_with_subtitle = video_with_effects
        
        # 合成视频，添加超精确时间控制参数
        # 只在第一个片段调整视频时长以适应字幕提前显示
        if is_first_segment:
            adjusted_duration = duration + subtitle_advance_time
        else:
            adjusted_duration = duration
        
        output = ffmpeg.output(
            video_with_subtitle, audio_input,
            output_path,
            vcodec='libx264',
            acodec='aac',
            audio_bitrate='192k',
            ar=44100,
            pix_fmt='yuv420p',
            t=adjusted_duration,  # 设置输出时长
            # 添加超精确时间控制参数
            avoid_negative_ts='make_zero',  # 避免负时间戳
            fflags='+genpts+igndts',  # 生成精确时间戳并忽略DTS
            copyts=None,  # 复制时间戳
            start_at_zero=None,  # 从零开始时间戳
            **{
                'c:a': 'aac', 
                'b:a': '192k',
                'ac': '2',  # 双声道
                'frame_duration': '0.02'  # 设置帧持续时间为20ms
            }
        )
        
        # 运行ffmpeg命令
        try:
            ffmpeg.run(output, overwrite_output=True, quiet=False)
        except ffmpeg.Error as e:
            print(f"FFmpeg详细错误信息: {e.stderr.decode() if e.stderr else str(e)}")
            raise e
        
        # 检查输出文件是否存在
        if os.path.exists(output_path):
            print(f"✓ 视频片段创建成功: {output_path}")
            return True
        else:
            print(f"✗ 视频片段创建失败: {output_path}")
            return False
            
    except Exception as e:
        print(f"创建视频片段时发生错误: {e}")
        return False

def create_combined_video_with_duration(first_video_path, second_image_path, target_duration, output_path):
    """
    拼接视频和图片，设置指定时长
    
    Args:
        first_video_path: 第一个视频文件路径
        second_image_path: 第二个图片文件路径
        target_duration: 目标总时长（秒）
        output_path: 输出文件路径
    
    Returns:
        bool: 是否成功拼接
    """
    try:
        import subprocess
        
        # 创建输出目录
        os.makedirs(os.path.dirname(output_path), exist_ok=True)
        
        # 获取第一个视频的时长
        probe_cmd = ['ffprobe', '-v', 'quiet', '-show_entries', 'format=duration', '-of', 'csv=p=0', first_video_path]
        result = subprocess.run(probe_cmd, capture_output=True, text=True)
        
        if result.returncode != 0:
            print(f"✗ 无法获取视频时长: {result.stderr}")
            return False
        
        first_video_duration = float(result.stdout.strip())
        second_image_duration = target_duration - first_video_duration
        
        if second_image_duration <= 0:
            print(f"✗ 目标时长({target_duration}s)小于第一个视频时长({first_video_duration}s)")
            return False
        
        print(f"拼接视频: 第一段{first_video_duration}s + 第二段{second_image_duration}s = 总时长{target_duration}s")
        
        # 先创建图片视频
        temp_image_video = output_path.replace('.mp4', '_temp_img.mp4')
        
        # 从图片创建视频
        img_cmd = [
            'ffmpeg', '-y',
            '-loop', '1', '-i', second_image_path,
            '-f', 'lavfi', '-i', 'anullsrc=channel_layout=stereo:sample_rate=44100',
            '-c:v', 'libx264',
            '-c:a', 'aac',
            '-t', str(second_image_duration),
            '-pix_fmt', 'yuv420p',
            '-vf', 'scale=1920:1080,fps=30',
            temp_image_video
        ]
        
        result = subprocess.run(img_cmd, capture_output=True, text=True)
        if result.returncode != 0:
            print(f"✗ 创建图片视频失败: {result.stderr}")
            return False
        
        # 创建文件列表用于concat
        concat_list_path = output_path.replace('.mp4', '_concat.txt')
        with open(concat_list_path, 'w', encoding='utf-8') as f:
            f.write(f"file '{first_video_path}'\n")
            f.write(f"file '{temp_image_video}'\n")
        
        # 拼接视频
        cmd = [
            'ffmpeg', '-y',
            '-f', 'concat',
            '-safe', '0',
            '-i', concat_list_path,
            '-c', 'copy',
            output_path
        ]
        
        result = subprocess.run(cmd, capture_output=True, text=True)
        
        # 清理临时文件
        if os.path.exists(temp_image_video):
            os.remove(temp_image_video)
        if os.path.exists(concat_list_path):
            os.remove(concat_list_path)
        
        if result.returncode == 0:
            print(f"✓ 视频拼接成功: {output_path}")
            return True
        else:
            print(f"✗ 视频拼接失败: {result.stderr}")
            return False
            
    except Exception as e:
        print(f"拼接视频时出错: {e}")
        return False

def create_complete_video_with_timestamps(video_path, audio_path, character_timestamps, text, start_time, duration, output_path):
    """为视频添加字幕和配音"""
    try:
        # 创建输出目录
        os.makedirs(os.path.dirname(output_path), exist_ok=True)
        
        # 创建字幕文件
        subtitle_path = output_path.replace('.mp4', '.srt')
        
        with open(subtitle_path, 'w', encoding='utf-8') as f:
            subtitle_index = 1
            current_text = ""
            
            for i, char_data in enumerate(character_timestamps):
                char = char_data['character']
                char_start = char_data['start']
                
                if char.strip() and char not in '，。！？；：':
                    current_text += char
                
                # 每10个字符或遇到标点符号时创建一个字幕条目
                if (len(current_text) >= 10 and char in '，。！？；：') or i == len(character_timestamps) - 1:
                    if current_text.strip():
                        # 计算字幕的结束时间
                        if i < len(character_timestamps) - 1:
                            end_time = character_timestamps[i + 1]['start']
                        else:
                            end_time = duration
                        
                        # 格式化时间
                        start_srt = format_time_for_srt(char_start)
                        end_srt = format_time_for_srt(end_time)
                        
                        f.write(f"{subtitle_index}\n")
                        f.write(f"{start_srt} --> {end_srt}\n")
                        f.write(f"{current_text.strip()}\n\n")
                        
                        subtitle_index += 1
                        current_text = ""
        
        # 使用ffmpeg合成最终视频
        cmd = [
            'ffmpeg', '-y',
            '-i', video_path,
            '-i', audio_path,
            '-vf', f"subtitles={subtitle_path}:force_style='FontName=SimHei,FontSize=24,PrimaryColour=&Hffffff,OutlineColour=&H000000,Outline=2,Alignment=2'",
            '-c:v', 'libx264',
            '-c:a', 'aac',
            '-preset', 'medium',
            '-crf', '23',
            '-t', str(duration),
            output_path
        ]
        
        result = subprocess.run(cmd, capture_output=True, text=True)
        
        # 清理字幕文件
        if os.path.exists(subtitle_path):
            os.remove(subtitle_path)
        
        if result.returncode == 0:
            print(f"✓ 完整视频生成成功: {output_path}")
            return True
        else:
            print(f"✗ 完整视频生成失败: {result.stderr}")
            return False
            
    except Exception as e:
        print(f"生成完整视频时出错: {e}")
        return False

def format_time_for_srt(seconds):
    """将秒数转换为SRT字幕格式的时间"""
    hours = int(seconds // 3600)
    minutes = int((seconds % 3600) // 60)
    secs = int(seconds % 60)
    millisecs = int((seconds % 1) * 1000)
    return f"{hours:02d}:{minutes:02d}:{secs:02d},{millisecs:03d}"

def concat_chapter_videos(video_files, output_path):
    """
    拼接章节内的所有视频段落
    
    Args:
        video_files: 视频文件路径列表
        output_path: 输出文件路径
    
    Returns:
        bool: 是否成功拼接
    """
    try:
        if not video_files:
            print("没有视频文件需要拼接")
            return False
        
        if len(video_files) == 1:
            # 只有一个视频文件，直接复制
            import shutil
            shutil.copy2(video_files[0], output_path)
            print(f"单个视频文件已复制到: {output_path}")
            return True
        
        print(f"正在拼接 {len(video_files)} 个视频段落...")
        
        # 确保输出目录存在
        os.makedirs(os.path.dirname(output_path), exist_ok=True)
        
        # 创建临时文件列表
        temp_list_file = "temp_video_list.txt"
        with open(temp_list_file, 'w', encoding='utf-8') as f:
            for video_file in video_files:
                # 使用相对路径或绝对路径
                f.write(f"file '{os.path.abspath(video_file)}'\n")
        
        # 使用ffmpeg-python拼接视频，重新编码音频以确保平滑拼接
        input_stream = ffmpeg.input(temp_list_file, f='concat', safe=0)
        output_stream = ffmpeg.output(
            input_stream,
            output_path,
            vcodec='copy',  # 视频流直接复制
            acodec='aac',   # 音频重新编码为AAC
            audio_bitrate='192k',  # 音频比特率
            ar=44100,  # 音频采样率
            ac=2,      # 双声道
            af='aresample=async=1'  # 音频重采样，确保同步
        )
        
        try:
            ffmpeg.run(output_stream, overwrite_output=True, quiet=True)
            result_returncode = 0
        except ffmpeg.Error as e:
            print(f"FFmpeg错误: {e.stderr.decode() if e.stderr else str(e)}")
            result_returncode = 1
        
        # 清理临时文件
        if os.path.exists(temp_list_file):
            os.remove(temp_list_file)
        
        if result_returncode == 0:
            print(f"章节视频拼接成功: {output_path}")
            return True
        else:
            print(f"章节视频拼接失败")
            return False
            
    except Exception as e:
        print(f"拼接章节视频时发生错误: {e}")
        # 清理临时文件
        if 'temp_list_file' in locals() and os.path.exists(temp_list_file):
            os.remove(temp_list_file)
        return False

# 删除重复的函数定义

def process_first_narration_stage1(video_path, audio_path, timestamp_path, output_path):
    """
    处理第一个narration的第一阶段：播放完整的first_video.mp4，匹配前10秒的字幕和音频
    直接生成完整视频，不分割成片段
    
    Args:
        video_path: first_video.mp4的路径
        audio_path: 音频文件路径
        timestamp_path: 时间戳文件路径
        output_path: 输出视频路径
    
    Returns:
        bool: 是否成功
    """
    try:
        print(f"第一阶段：播放完整视频 {video_path}，匹配前10秒的字幕和音频（完整生成）")
        
        # 读取时间戳文件
        with open(timestamp_path, 'r', encoding='utf-8') as f:
            timestamp_data = json.load(f)
        
        text = timestamp_data.get('text', '')
        character_timestamps = timestamp_data.get('character_timestamps', [])
        
        if not character_timestamps:
            print(f"警告: 时间戳文件中没有character_timestamps数据")
            return False
        
        # 筛选前10秒的字幕数据
        stage1_timestamps = []
        stage1_text = ""
        
        for ts in character_timestamps:
            if ts['start_time'] < 10.0:  # 只取前10秒的字幕
                stage1_timestamps.append(ts)
                stage1_text += ts['character']
            else:
                break
        
        if not stage1_timestamps:
            print(f"警告: 前10秒没有字幕数据")
            return False
        
        print(f"第一阶段字幕文本: {stage1_text}")
        print(f"第一阶段字幕时长: {stage1_timestamps[-1]['end_time']:.2f}秒")
        
        # 直接生成完整视频，使用完整的时间戳数据
        return create_complete_video_with_timestamps(
            video_path, audio_path, stage1_timestamps, stage1_text, 
            0, stage1_timestamps[-1]['end_time'], output_path
        )
            
    except Exception as e:
        print(f"处理第一阶段视频时发生错误: {e}")
        return False

def create_video_segment_with_timing_for_video(video_path, audio_path, text_segment, start_time, end_time, output_path, is_first_segment=False):
    """
    创建带有精确时间控制的视频片段，使用视频文件作为背景
    
    Args:
        video_path: 背景视频文件路径
        audio_path: 音频文件路径
        text_segment: 字幕文本片段
        start_time: 开始时间（秒）
        end_time: 结束时间（秒）
        output_path: 输出视频路径
        is_first_segment: 是否为第一个片段
    
    Returns:
        bool: 是否成功生成
    """
    try:
        # 确保输出目录存在
        output_dir = os.path.dirname(output_path)
        if output_dir:
            os.makedirs(output_dir, exist_ok=True)
        
        print(f"正在创建视频片段: {os.path.basename(output_path)}")
        print(f"时间范围: {start_time:.2f}s - {end_time:.2f}s")
        print(f"字幕内容: {text_segment}")
        
        # 计算片段时长
        duration = end_time - start_time
        
        # 创建输入流，使用超高精度时间参数
        precise_start_time = f"{start_time:.6f}"
        precise_duration = f"{duration:.6f}"
        
        print(f"精确时间参数 - 开始时间: {precise_start_time}s, 持续时间: {precise_duration}s")
        
        # 视频输入：使用视频文件，如果需要循环播放则使用filter
        # 先获取视频时长，然后决定是否需要循环
        probe = ffmpeg.probe(video_path)
        video_duration = float(probe['streams'][0]['duration'])
        
        if duration > video_duration:
            # 如果需要的时长超过视频长度，使用循环滤镜
            video_input = ffmpeg.input(video_path).filter('loop', loop=-1, size=32767, start=0).filter('trim', duration=precise_duration)
        else:
            # 如果视频足够长，直接截取
            video_input = ffmpeg.input(video_path, t=precise_duration)
        
        # 字幕提前显示时间（秒）
        subtitle_advance_time = 0.15
        
        # 音频输入：先切割指定时间段的音频
        audio_segment = ffmpeg.input(audio_path, 
                                   ss=precise_start_time, 
                                   t=precise_duration,
                                   accurate_seek=None,
                                   avoid_negative_ts='make_zero')
        
        # 将切割后的音频重新设置为从0开始
        if is_first_segment:
            audio_input = audio_segment.filter('asetpts', 'PTS-STARTPTS').filter('adelay', f'{int(subtitle_advance_time * 1000)}|{int(subtitle_advance_time * 1000)}')
        else:
            audio_input = audio_segment.filter('asetpts', 'PTS-STARTPTS')
        
        # 使用原始视频流
        video_with_effects = video_input.video
        
        # 清理字幕文本
        clean_subtitle = clean_text_for_tts(text_segment)
        
        if clean_subtitle.strip():
            # 处理字幕文本，确保不超出边框
            wrapped_subtitle = wrap_text(clean_subtitle, max_chars_per_line=30)
            
            # 字幕位置：使用FFmpeg表达式确保显示在底部
            subtitle_y = 'h-text_h-h/3'  # 距离底部1/3视频高度像素
            
            print(f"调试信息 - 字幕文本: '{wrapped_subtitle}'")
            print(f"调试信息 - 字幕Y位置表达式: {subtitle_y}")
            
            # 计算字幕显示时间范围
            if is_first_segment:
                subtitle_start_time = 0
                subtitle_end_time = duration + subtitle_advance_time
            else:
                subtitle_start_time = 0
                subtitle_end_time = duration
            
            # 添加字幕滤镜
            video_with_subtitle = video_with_effects.filter(
                'drawtext',
                text=wrapped_subtitle,
                fontfile='/System/Library/Fonts/Helvetica-Bold.ttc',
                fontsize=72,
                fontcolor='black',
                x='max(20, min(w-text_w-20, (w-text_w)/2))',
                y=subtitle_y,
                borderw=3,
                bordercolor='white',
                box=0,
                enable=f'gte(t,{subtitle_start_time})*lte(t,{subtitle_end_time})'
            )
        else:
            video_with_subtitle = video_with_effects
        
        # 合成视频
        if is_first_segment:
            adjusted_duration = duration + subtitle_advance_time
        else:
            adjusted_duration = duration
        
        output = ffmpeg.output(
            video_with_subtitle, audio_input,
            output_path,
            vcodec='libx264',
            acodec='aac',
            audio_bitrate='192k',
            ar=44100,
            pix_fmt='yuv420p',
            t=adjusted_duration,
            avoid_negative_ts='make_zero',
            fflags='+genpts+igndts',
            copyts=None,
            start_at_zero=None,
            **{
                'c:a': 'aac', 
                'b:a': '192k',
                'ac': '2',
                'frame_duration': '0.02'
            }
        )
        
        # 运行ffmpeg命令
        try:
            ffmpeg.run(output, overwrite_output=True, quiet=False)
        except ffmpeg.Error as e:
            print(f"FFmpeg详细错误信息: {e.stderr.decode() if e.stderr else str(e)}")
            return False
        
        # 检查输出文件是否存在
        if os.path.exists(output_path):
            print(f"✓ 视频片段创建成功: {output_path}")
            return True
        else:
            print(f"✗ 视频片段创建失败: {output_path}")
            return False
            
    except Exception as e:
        print(f"创建视频片段时发生错误: {e}")
        return False

def process_first_narration_stage2(image_path, audio_path, timestamp_path, output_path):
    """
    处理第一个narration的第二阶段：使用image_02.jpeg匹配10秒后的字幕和音频
    直接生成完整视频，不分割成片段
    
    Args:
        image_path: image_02.jpeg的路径
        audio_path: 音频文件路径
        timestamp_path: 时间戳文件路径
        output_path: 输出视频路径
    
    Returns:
        bool: 是否成功
    """
    try:
        print(f"第二阶段：使用图片 {image_path}，匹配10秒后的字幕和音频（完整生成）")
        
        # 读取时间戳文件
        with open(timestamp_path, 'r', encoding='utf-8') as f:
            timestamp_data = json.load(f)
        
        text = timestamp_data.get('text', '')
        character_timestamps = timestamp_data.get('character_timestamps', [])
        
        if not character_timestamps:
            print(f"警告: 时间戳文件中没有character_timestamps数据")
            return False
        
        # 筛选10秒后的字幕数据
        stage2_timestamps = []
        stage2_text = ""
        
        for ts in character_timestamps:
            if ts['start_time'] >= 10.0:  # 只取10秒后的字幕
                # 调整时间戳，让第二阶段从0开始
                adjusted_ts = {
                    'character': ts['character'],
                    'start_time': ts['start_time'] - 10.0,
                    'end_time': ts['end_time'] - 10.0
                }
                stage2_timestamps.append(adjusted_ts)
                stage2_text += ts['character']
        
        if not stage2_timestamps:
            print(f"警告: 10秒后没有字幕数据")
            return False
        
        print(f"第二阶段字幕文本: {stage2_text}")
        print(f"第二阶段字幕时长: {stage2_timestamps[-1]['end_time']:.2f}秒")
        
        # 直接生成完整视频，使用完整的时间戳数据
        # 第二阶段需要从音频的10秒开始
        return create_complete_video_with_timestamps(
            image_path, audio_path, stage2_timestamps, stage2_text, 
            10.0, character_timestamps[-1]['end_time'], output_path
        )
            
    except Exception as e:
        print(f"处理第二阶段视频时发生错误: {e}")
        return False



def concat_videos_from_assets(data_dir):
    """
    拼接图片、语音和字幕生成视频，支持根据timestamps精确分段
    
    Args:
        data_dir: 数据目录路径
    
    Returns:
        bool: 是否成功
    """
    try:
        print(f"=== 开始拼接视频 ===")
        print(f"数据目录: {data_dir}")
        
        if not os.path.exists(data_dir):
            print(f"错误: 数据目录不存在 {data_dir}")
            return False
        
        # 查找所有章节目录
        chapter_dirs = []
        for item in os.listdir(data_dir):
            item_path = os.path.join(data_dir, item)
            if os.path.isdir(item_path) and item.startswith('chapter_'):
                chapter_dirs.append(item_path)
        
        if not chapter_dirs:
            print(f"错误: 在 {data_dir} 中没有找到章节目录")
            return False
        
        chapter_dirs.sort()
        print(f"找到 {len(chapter_dirs)} 个章节目录")
        
        all_videos = []
        
        # 处理每个章节
        for chapter_dir in chapter_dirs:
            chapter_name = os.path.basename(chapter_dir)
            print(f"\n--- 处理章节: {chapter_name} ---")
            
            # 查找图片文件
            image_files = [f for f in os.listdir(chapter_dir) if f.endswith('.jpeg') and 'image' in f]
            if not image_files:
                print(f"警告: 在 {chapter_dir} 中没有找到图片文件")
                continue
            
            # 查找音频和时间戳文件
            audio_files = [f for f in os.listdir(chapter_dir) if f.endswith('.mp3') and 'narration' in f]
            timestamp_files = [f for f in os.listdir(chapter_dir) if f.endswith('_timestamps.json')]
            
            if not audio_files:
                print(f"警告: 在 {chapter_dir} 中没有找到音频文件")
                continue
            
            chapter_videos = []
            
            # 处理每个音频文件
            for audio_file in sorted(audio_files):
                # 找到对应的图片和时间戳文件
                base_name = audio_file.replace('.mp3', '')
                image_file = None
                timestamp_file = None
                
                # 特殊处理每个章节的第一个narration
                if 'narration_01.mp3' in audio_file:
                    print(f"\n=== 特殊处理第一个narration ===\n")
                    
                    # 查找必要的文件
                    first_video_file = f'{chapter_name}_first_video.mp4'
                    first_video_path = os.path.join(chapter_dir, first_video_file)
                    second_image_file = f'{chapter_name}_image_02.jpeg'
                    second_image_path = os.path.join(chapter_dir, second_image_file)
                    
                    # 查找对应的时间戳文件
                    for ts in timestamp_files:
                        if base_name in ts:
                            timestamp_file = ts
                            break
                    
                    # 读取chapter_002的时长参数
                    chapter_002_timestamp_path = '/Users/nathan/Projects/wrmVideo/data/002/chapter_002/chapter_002_narration_01_timestamps.json'
                    target_duration = 21.744  # 默认时长
                    
                    try:
                        if os.path.exists(chapter_002_timestamp_path):
                            with open(chapter_002_timestamp_path, 'r', encoding='utf-8') as f:
                                chapter_002_data = json.load(f)
                                target_duration = chapter_002_data.get('duration', 21.744)
                                print(f"使用chapter_002的时长参数: {target_duration}秒")
                    except Exception as e:
                        print(f"读取chapter_002时长参数失败，使用默认值: {e}")
                    
                    if os.path.exists(first_video_path) and os.path.exists(second_image_path) and timestamp_file:
                        timestamp_path = os.path.join(chapter_dir, timestamp_file)
                        audio_path = os.path.join(chapter_dir, audio_file)
                        
                        # 创建拼接后的视频（first_video + image_02）
                        combined_video_output = os.path.join(chapter_dir, f"{base_name}_combined_base.mp4")
                        combined_success = create_combined_video_with_duration(first_video_path, second_image_path, target_duration, combined_video_output)
                        
                        if combined_success:
                            # 为拼接后的视频添加字幕和配音
                            final_narration_output = os.path.join(chapter_dir, f"{base_name}_complete.mp4")
                            
                            # 读取时间戳数据
                            try:
                                with open(timestamp_path, 'r', encoding='utf-8') as f:
                                    timestamp_data = json.load(f)
                                
                                text = timestamp_data.get('text', '')
                                character_timestamps = timestamp_data.get('character_timestamps', [])
                                
                                if character_timestamps:
                                    # 使用完整的时间戳数据创建视频
                                    if create_complete_video_with_timestamps(combined_video_output, audio_path, character_timestamps, text, 0, target_duration, final_narration_output):
                                        chapter_videos.append(final_narration_output)
                                        print(f"✓ 第一个narration完整视频生成成功")
                                        # 清理临时文件
                                        if os.path.exists(combined_video_output):
                                            os.remove(combined_video_output)
                                    else:
                                        print(f"✗ 第一个narration字幕配音添加失败")
                                else:
                                    print(f"✗ 时间戳数据为空")
                                    
                            except Exception as e:
                                print(f"处理时间戳文件失败: {e}")
                        else:
                            print(f"✗ 视频拼接失败")
                    else:
                        print(f"✗ 缺少必要文件: first_video={os.path.exists(first_video_path)}, image_02={os.path.exists(second_image_path)}, timestamp={timestamp_file is not None}")
                    
                    print(f"\n=== 第一个narration处理完成 ===\n")
                    continue  # 跳过常规处理
                
                # 常规处理逻辑
                # 查找对应的图片文件
                for img in image_files:
                    if base_name.replace('_narration', '_image') in img:
                        image_file = img
                        break
                
                # 查找对应的时间戳文件
                for ts in timestamp_files:
                    if base_name in ts:
                        timestamp_file = ts
                        break
                
                if not image_file:
                    print(f"警告: 找不到 {audio_file} 对应的图片文件")
                    continue
                
                if not timestamp_file:
                    print(f"警告: 找不到 {audio_file} 对应的时间戳文件")
                    continue
                
                # 构建完整路径
                audio_path = os.path.join(chapter_dir, audio_file)
                image_path = os.path.join(chapter_dir, image_file)
                timestamp_path = os.path.join(chapter_dir, timestamp_file)
                
                print(f"处理音频: {audio_file}")
                print(f"对应图片: {image_file}")
                print(f"时间戳文件: {timestamp_file}")
                
                # 读取时间戳文件
                try:
                    with open(timestamp_path, 'r', encoding='utf-8') as f:
                        timestamp_data = json.load(f)
                    
                    text = timestamp_data.get('text', '')
                    character_timestamps = timestamp_data.get('character_timestamps', [])
                    
                    if not character_timestamps:
                        print(f"警告: {timestamp_file} 中没有character_timestamps数据")
                        continue
                    
                    # 根据时间戳分割文本，使用更大的字符数以减少分割频率
                    text_segments = split_text_by_timestamps(text, character_timestamps, max_chars_per_segment=40)
                    
                    print(f"文本分割为 {len(text_segments)} 个片段")
                    
                    # 为每个文本片段创建视频
                    segment_videos = []
                    for i, (segment_text, start_time, end_time) in enumerate(text_segments):
                        segment_output = os.path.join(chapter_dir, f"{base_name}_segment_{i+1:02d}.mp4")
                        
                        # 只在第一个片段添加字幕提前显示效果
                        is_first_segment = (i == 0)
                        if create_video_segment_with_timing(image_path, audio_path, segment_text, start_time, end_time, segment_output, is_first_segment):
                            segment_videos.append(segment_output)
                    
                    # 拼接当前音频的所有片段
                    if segment_videos:
                        audio_complete_path = os.path.join(chapter_dir, f"{base_name}_complete.mp4")
                        if concat_chapter_videos(segment_videos, audio_complete_path):
                            chapter_videos.append(audio_complete_path)
                            print(f"✓ 音频 {audio_file} 的视频片段拼接成功")
                        else:
                            print(f"✗ 音频 {audio_file} 的视频片段拼接失败")
                    
                except Exception as e:
                    print(f"处理时间戳文件 {timestamp_file} 时发生错误: {e}")
                    continue
            
            # 拼接章节内的所有视频
            if chapter_videos:
                chapter_final_path = os.path.join(chapter_dir, f"{chapter_name}_complete.mp4")
                if concat_chapter_videos(chapter_videos, chapter_final_path):
                    all_videos.append(chapter_final_path)
                    print(f"✓ 章节 {chapter_name} 视频拼接成功")
                else:
                    print(f"✗ 章节 {chapter_name} 视频拼接失败")
        
        # 拼接所有章节视频
        if all_videos:
            final_video_path = os.path.join(data_dir, "final_complete_video.mp4")
            if concat_chapter_videos(all_videos, final_video_path):
                print(f"\n✓ 最终视频拼接成功: {final_video_path}")
                return True
            else:
                print(f"\n✗ 最终视频拼接失败")
                return False
        else:
            print("\n没有生成任何章节视频")
            return False
        
    except Exception as e:
        print(f"拼接视频时发生错误: {e}")
        return False

def main():
    """
    主函数
    """
    parser = argparse.ArgumentParser(description='独立的视频生成脚本')
    parser.add_argument('data_dir', help='数据目录路径')
    
    args = parser.parse_args()
    
    print(f"开始处理数据目录: {args.data_dir}")
    
    # 拼接视频
    success = concat_videos_from_assets(args.data_dir)
    if success:
        print(f"\n✓ 视频拼接完成")
    else:
        print(f"\n✗ 视频拼接失败")
        sys.exit(1)
    
    print("\n=== 处理完成 ===")

if __name__ == '__main__':
    main()