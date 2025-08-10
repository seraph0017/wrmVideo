#!/usr/bin/env python3
"""
concat_finish_video.py

拼接每个chapter下面的chapter_xxx_narration_xx_video.mp4按顺序从1到10拼接成一个文件，
配上随机选择的BGM，并在最后拼接finish.mp4文件。

使用方法:
    python concat_finish_video.py data/001
"""

import os
import sys
import subprocess
import random
import glob
from pathlib import Path
import ffmpeg

def check_nvidia_gpu():
    """检测系统是否有NVIDIA GPU可用"""
    try:
        # 尝试运行nvidia-smi命令
        result = subprocess.run(['nvidia-smi'], capture_output=True, text=True, timeout=10)
        if result.returncode == 0:
            print("✓ 检测到NVIDIA GPU，将使用硬件加速")
            return True
        else:
            print("⚠️  未检测到NVIDIA GPU或驱动，使用CPU编码")
            return False
    except (subprocess.TimeoutExpired, FileNotFoundError, Exception) as e:
        print(f"⚠️  GPU检测失败，使用CPU编码: {e}")
        return False

def get_ffmpeg_gpu_params():
    """获取FFmpeg GPU优化参数 - 优化速度版本"""
    if check_nvidia_gpu():
        return {
            'hwaccel': 'cuda',
            'hwaccel_output_format': 'cuda',
            'video_codec': 'h264_nvenc',
            'preset': 'p2',  # 更快的预设 (p1=fastest, p2=faster, p7=slowest)
            'tune': 'll',    # Low latency - 更快的编码
            'extra_params': [
                '-rc-lookahead', '8',  # 减少前瞻帧数以提高速度
                '-bf', '2',            # 减少B帧数量
                '-refs', '1'           # 减少参考帧数量
            ]
        }
    else:
        return {
            'video_codec': 'libx264',
            'preset': 'fast',  # 更快的CPU预设
            'extra_params': [
                '-refs', '2',      # 限制参考帧数量
                '-me_method', 'hex', # 使用更快的运动估计
                '-subq', '6'       # 降低子像素运动估计质量以提高速度
            ]
        }

# 视频输出标准配置（从 gen_video.py 复制）
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

def get_audio_duration(audio_path):
    """获取音频文件时长（从 gen_video.py 复制）"""
    try:
        probe = ffmpeg.probe(audio_path)
        duration = float(probe['format']['duration'])
        return duration
    except Exception as e:
        print(f"获取音频时长失败: {e}")
        return 0

def get_available_bgm_files():
    """获取可用的BGM文件列表"""
    bgm_dir = "/Users/xunan/Projects/wrmVideo/src/bgm"
    bgm_files = [
        "wn1.mp3", "wn3.mp3", "wn4.mp3", "wn5.mp3", "wn6.mp3", 
        "wn7.mp3", "wn8.mp3", "wn9.mp3", "wn10.mp3", "wn11.mp3", 
        "wn12.mp3", "wn13.mp3", "wn14.mp3"
    ]
    
    available_files = []
    for bgm_file in bgm_files:
        bgm_path = os.path.join(bgm_dir, bgm_file)
        if os.path.exists(bgm_path):
            available_files.append(bgm_path)
        else:
            print(f"警告: BGM文件不存在: {bgm_path}")
    
    return available_files

def collect_chapter_narration_videos(chapter_path, chapter_name):
    """收集单个chapter目录下的narration视频文件"""
    video_files = []
    
    print(f"处理章节: {chapter_name}")
    
    # 收集该章节的narration视频文件 (1-10)
    for i in range(1, 11):
        video_filename = f"{chapter_name}_narration_{i:02d}_video.mp4"
        video_path = os.path.join(chapter_path, video_filename)
        
        if os.path.exists(video_path):
            video_files.append(video_path)
            print(f"  找到视频: {video_filename}")
        else:
            print(f"  警告: 视频文件不存在: {video_filename}")
    
    print(f"章节 {chapter_name} 共收集到 {len(video_files)} 个narration视频文件")
    return video_files

def get_total_video_duration(video_files):
    """计算所有视频的总时长"""
    total_duration = 0
    for video_file in video_files:
        width, height, fps, duration = get_video_info(video_file)
        if duration:
            total_duration += duration
        else:
            print(f"警告: 无法获取视频时长: {video_file}")
    
    return total_duration

def create_bgm_audio(bgm_file, target_duration, output_path):
    """创建与视频时长匹配的BGM音频，支持循环和淡出"""
    try:
        # 获取BGM原始时长
        bgm_duration = get_audio_duration(bgm_file)
        if bgm_duration <= 0:
            print(f"错误: 无法获取BGM时长: {bgm_file}")
            return False
        
        print(f"BGM原始时长: {bgm_duration:.2f}s, 目标时长: {target_duration:.2f}s")
        
        # 获取GPU优化参数
        gpu_params = get_ffmpeg_gpu_params()
        
        # 构建FFmpeg命令
        cmd = ["ffmpeg", "-y"]
        
        # 添加硬件加速参数（如果可用）
        if 'hwaccel' in gpu_params:
            cmd.extend(["-hwaccel", gpu_params['hwaccel']])
        if 'hwaccel_output_format' in gpu_params:
            cmd.extend(["-hwaccel_output_format", gpu_params['hwaccel_output_format']])
        
        if bgm_duration >= target_duration:
            # BGM比视频长，直接裁剪并在最后3秒淡出
            cmd.extend([
                "-i", bgm_file,
                "-t", str(target_duration),
                "-af", f"afade=t=out:st={max(0, target_duration-3)}:d=3",
                "-c:a", "aac",
                "-b:a", "128k",
                output_path
            ])
        else:
            # BGM比视频短，需要循环播放并在最后3秒淡出
            # 计算需要循环的次数，确保生成足够长的音频
            loop_count = int(target_duration / bgm_duration) + 1
            cmd.extend([
                "-stream_loop", str(loop_count),
                "-i", bgm_file,
                "-t", f"{target_duration:.3f}",  # 精确到毫秒
                "-af", f"afade=t=out:st={max(0, target_duration-3):.3f}:d=3",
                "-c:a", "aac",
                "-b:a", "128k",
                output_path
            ])
        
        print(f"执行BGM处理命令: {' '.join(cmd)}")
        result = subprocess.run(cmd, capture_output=True, text=True)
        
        if result.returncode != 0:
            print(f"BGM处理失败: {result.stderr}")
            return False
        
        print(f"BGM音频创建成功: {output_path}")
        return True
        
    except Exception as e:
        print(f"创建BGM音频时发生错误: {e}")
        return False

def concat_videos_with_bgm(video_files, bgm_audio_path, output_path):
    """拼接视频并添加BGM，混合原有音频和BGM"""
    try:
        # 创建临时文件列表
        temp_dir = os.path.dirname(output_path)
        concat_list_path = os.path.join(temp_dir, "concat_list.txt")
        
        # 写入视频文件列表
        with open(concat_list_path, 'w', encoding='utf-8') as f:
            for video_file in video_files:
                f.write(f"file '{os.path.abspath(video_file)}'\n")
        
        # 获取GPU优化参数
        gpu_params = get_ffmpeg_gpu_params()
        
        # 使用FFmpeg拼接视频并混合音频（原有音频+BGM）
        cmd = ["ffmpeg", "-y"]
        
        # 添加硬件加速参数（如果可用）
        if 'hwaccel' in gpu_params:
            cmd.extend(["-hwaccel", gpu_params['hwaccel']])
        if 'hwaccel_output_format' in gpu_params:
            cmd.extend(["-hwaccel_output_format", gpu_params['hwaccel_output_format']])
        
        cmd.extend([
            "-f", "concat",
            "-safe", "0",
            "-i", concat_list_path,
            "-i", bgm_audio_path,
            "-c:v", gpu_params.get('video_codec', 'libx264'),  # 使用GPU编码器或CPU编码器
            "-filter_complex", "[0:a]volume=1.0[original];[1:a]volume=0.3[bgm];[original][bgm]amix=inputs=2:duration=first:dropout_transition=3[mixed]",
            "-map", "0:v:0",  # 使用第一个输入的视频流
            "-map", "[mixed]",  # 使用混合后的音频流
            "-c:a", "aac",
            "-b:a", "128k"
        ])
        
        # 添加GPU特定的编码参数
        if 'preset' in gpu_params:
            cmd.extend(["-preset", gpu_params['preset']])
        if 'tune' in gpu_params:
            cmd.extend(["-tune", gpu_params['tune']])
        
        # 添加额外的优化参数
        cmd.extend(gpu_params.get('extra_params', []))
        
        cmd.append(output_path)
        
        print(f"执行视频拼接命令: {' '.join(cmd)}")
        result = subprocess.run(cmd, capture_output=True, text=True)
        
        if result.returncode != 0:
            print(f"视频拼接失败: {result.stderr}")
            return False
        
        # 清理临时文件
        if os.path.exists(concat_list_path):
            os.remove(concat_list_path)
        
        print(f"视频拼接成功: {output_path}")
        return True
        
    except Exception as e:
        print(f"拼接视频时发生错误: {e}")
        return False

def add_finish_video(main_video_path, finish_video_path, final_output_path):
    """在主视频后面拼接finish.mp4"""
    try:
        # 创建临时文件列表
        temp_dir = os.path.dirname(final_output_path)
        concat_list_path = os.path.join(temp_dir, "final_concat_list.txt")
        
        # 写入视频文件列表
        with open(concat_list_path, 'w', encoding='utf-8') as f:
            f.write(f"file '{os.path.abspath(main_video_path)}'\n")
            f.write(f"file '{os.path.abspath(finish_video_path)}'\n")
        
        # 使用FFmpeg拼接，使用流复制避免重新编码导致的时长问题
        cmd = [
            "ffmpeg", "-y",
            "-f", "concat",
            "-safe", "0",
            "-i", concat_list_path,
            "-c", "copy",  # 使用流复制而不是重新编码
            "-avoid_negative_ts", "make_zero",  # 处理时间戳问题
            final_output_path
        ]
        
        print(f"执行最终拼接命令: {' '.join(cmd)}")
        result = subprocess.run(cmd, capture_output=True, text=True)
        
        if result.returncode != 0:
            print(f"最终拼接失败: {result.stderr}")
            return False
        
        # 清理临时文件
        if os.path.exists(concat_list_path):
            os.remove(concat_list_path)
        
        print(f"最终视频生成成功: {final_output_path}")
        return True
        
    except Exception as e:
        print(f"添加finish视频时发生错误: {e}")
        return False

def process_single_chapter(data_dir, chapter_dir):
    """处理单个chapter，生成该chapter的完整视频"""
    chapter_path = os.path.join(data_dir, chapter_dir)
    chapter_name = chapter_dir  # 例如: chapter_001
    
    print(f"\n{'='*50}")
    print(f"开始处理章节: {chapter_name}")
    print(f"{'='*50}")
    
    # 1. 收集该章节的narration视频文件
    video_files = collect_chapter_narration_videos(chapter_path, chapter_name)
    if not video_files:
        print(f"警告: 章节 {chapter_name} 没有找到任何narration视频文件")
        return False
    
    # 2. 计算该章节视频总时长
    total_duration = get_total_video_duration(video_files)
    print(f"章节 {chapter_name} 视频总时长: {total_duration:.2f}s ({total_duration/60:.2f}分钟)")
    
    # 3. 随机选择BGM
    bgm_files = get_available_bgm_files()
    if not bgm_files:
        print("错误: 没有找到可用的BGM文件")
        return False
    
    selected_bgm = random.choice(bgm_files)
    print(f"为章节 {chapter_name} 随机选择的BGM: {os.path.basename(selected_bgm)}")
    
    # 4. 创建输出文件路径
    temp_bgm_path = os.path.join(chapter_path, f"{chapter_name}_temp_bgm_audio.aac")
    main_video_path = os.path.join(chapter_path, f"{chapter_name}_main_video.mp4")
    final_output_path = os.path.join(chapter_path, f"{chapter_name}_complete_video.mp4")
    
    try:
        # 5. 创建匹配时长的BGM音频
        print(f"\n=== 为章节 {chapter_name} 创建BGM音频 ===")
        if not create_bgm_audio(selected_bgm, total_duration, temp_bgm_path):
            print(f"错误: 章节 {chapter_name} BGM音频创建失败")
            return False
        
        # 6. 拼接该章节的narration视频并添加BGM
        print(f"\n=== 拼接章节 {chapter_name} 的narration视频 ===")
        if not concat_videos_with_bgm(video_files, temp_bgm_path, main_video_path):
            print(f"错误: 章节 {chapter_name} 视频拼接失败")
            return False
        
        # 7. 添加finish.mp4（使用兼容版本）
        finish_video_path = "src/banner/finish_compatible.mp4"
        if not os.path.exists(finish_video_path):
            print(f"警告: finish.mp4文件不存在: {finish_video_path}")
            print(f"跳过finish视频拼接，使用主视频作为章节 {chapter_name} 的最终输出")
            import shutil
            shutil.copy2(main_video_path, final_output_path)
        else:
            print(f"\n=== 为章节 {chapter_name} 添加finish视频 ===")
            if not add_finish_video(main_video_path, finish_video_path, final_output_path):
                print(f"错误: 章节 {chapter_name} finish视频拼接失败")
                return False
        
        # 8. 清理临时文件
        if os.path.exists(temp_bgm_path):
            os.remove(temp_bgm_path)
        if os.path.exists(main_video_path) and os.path.exists(final_output_path):
            os.remove(main_video_path)
        
        # 9. 检查最终视频
        if os.path.exists(final_output_path):
            width, height, fps, duration = get_video_info(final_output_path)
            file_size_mb = os.path.getsize(final_output_path) / (1024 * 1024)
            print(f"\n=== 章节 {chapter_name} 最终视频信息 ===")
            print(f"文件路径: {final_output_path}")
            print(f"视频参数: {width}x{height}px, {fps}fps")
            print(f"视频时长: {duration:.2f}s ({duration/60:.2f}分钟)")
            print(f"文件大小: {file_size_mb:.2f}MB")
            print(f"\n✓ 章节 {chapter_name} 视频生成完成!")
            return True
        else:
            print(f"错误: 章节 {chapter_name} 最终视频文件未生成")
            return False
            
    except Exception as e:
        print(f"处理章节 {chapter_name} 时发生错误: {e}")
        return False

def main():
    if len(sys.argv) != 2:
        print("使用方法: python concat_finish_video.py data/001")
        sys.exit(1)
    
    data_dir = sys.argv[1]
    if not os.path.exists(data_dir):
        print(f"错误: 数据目录不存在: {data_dir}")
        sys.exit(1)
    
    print(f"开始处理数据目录: {data_dir}")
    
    # 获取所有chapter目录
    chapter_dirs = sorted([d for d in os.listdir(data_dir) 
                          if d.startswith('chapter_') and os.path.isdir(os.path.join(data_dir, d))])
    
    if not chapter_dirs:
        print("错误: 没有找到任何chapter目录")
        sys.exit(1)
    
    print(f"找到 {len(chapter_dirs)} 个章节目录: {chapter_dirs}")
    
    # 处理每个chapter
    success_count = 0
    failed_chapters = []
    
    for chapter_dir in chapter_dirs:
        if process_single_chapter(data_dir, chapter_dir):
            success_count += 1
        else:
            failed_chapters.append(chapter_dir)
    
    # 输出处理结果总结
    print(f"\n{'='*60}")
    print(f"处理完成总结:")
    print(f"{'='*60}")
    print(f"总章节数: {len(chapter_dirs)}")
    print(f"成功生成: {success_count} 个章节视频")
    print(f"失败章节: {len(failed_chapters)} 个")
    
    if failed_chapters:
        print(f"失败的章节: {', '.join(failed_chapters)}")
    
    if success_count == len(chapter_dirs):
        print(f"\n🎉 所有章节视频生成成功!")
    else:
        print(f"\n⚠️  部分章节处理失败，请检查日志")

if __name__ == "__main__":
    main()