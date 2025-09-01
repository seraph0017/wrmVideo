#!/usr/bin/env python3
"""
concat_finish_video.py

拼接每个chapter下面的narration视频文件，配上随机选择的BGM，并在最后拼接finish.mp4文件。

新逻辑：
- 收集合并的narration_01-03视频（chapter_xxx_narration_01-03_video.mp4）
- 收集正常的narration_04-30视频（chapter_xxx_narration_04_video.mp4 到 chapter_xxx_narration_30_video.mp4）
- 如果合并视频不存在，回退到收集单独的narration_01-03视频

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
    bgm_dir = os.path.join(os.path.dirname(os.path.abspath(__file__)), "src", "bgm")
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
    """收集单个chapter目录下的narration视频文件
    
    新逻辑：
    - 收集合并的narration_01-03视频
    - 收集正常的narration_04-30视频
    """
    video_files = []
    
    print(f"处理章节: {chapter_name}")
    
    # 1. 收集合并的narration_01-03视频
    merged_video_filename = f"{chapter_name}_narration_01-03_video.mp4"
    merged_video_path = os.path.join(chapter_path, merged_video_filename)
    
    if os.path.exists(merged_video_path):
        video_files.append(merged_video_path)
        print(f"  找到合并视频: {merged_video_filename}")
    else:
        print(f"  警告: 合并视频文件不存在: {merged_video_filename}")
        # 如果合并视频不存在，尝试收集单独的narration_01-03视频作为备选
        for i in range(1, 4):
            video_filename = f"{chapter_name}_narration_{i:02d}_video.mp4"
            video_path = os.path.join(chapter_path, video_filename)
            if os.path.exists(video_path):
                video_files.append(video_path)
                print(f"  找到备选视频: {video_filename}")
            else:
                print(f"  警告: 备选视频文件不存在: {video_filename}")
    
    # 2. 收集正常的narration_04-30视频
    for i in range(4, 31):
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
        result = subprocess.run(cmd, capture_output=True, text=False)
        
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
            "-filter_complex", "[0:a]dynaudnorm=f=75:g=25:p=0.95:m=10.0:r=0.9:n=1:c=1,volume=1.0[original];[1:a]volume=0.1[bgm];[original][bgm]amix=inputs=2:duration=first:dropout_transition=3[mixed]",
            "-map", "0:v:0",  # 使用第一个输入的视频流
            "-map", "[mixed]",  # 使用混合后的音频流
            "-c:a", "aac",
            "-b:a", "128k"
        ])
        
        # 添加GPU特定的编码参数
        # 只有非VideoToolbox编码器才添加preset参数
        if 'preset' in gpu_params and not gpu_params['video_codec'].endswith('_videotoolbox'):
            cmd.extend(["-preset", gpu_params['preset']])
        if 'tune' in gpu_params:
            cmd.extend(["-tune", gpu_params['tune']])
        
        # 添加额外的优化参数
        cmd.extend(gpu_params.get('extra_params', []))
        
        cmd.append(output_path)
        
        print(f"执行视频拼接命令: {' '.join(cmd)}")
        result = subprocess.run(cmd, capture_output=True, text=False)
        
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

def super_compress_video(input_path, output_path):
    """超级压缩视频，用于进一步减小文件大小"""
    try:
        # 获取GPU参数
        gpu_params = get_ffmpeg_gpu_params()
        
        # 构建超级压缩命令
        cmd = [
            "ffmpeg", "-y",
            "-i", input_path,
            "-c:v", gpu_params['video_codec'],
            "-c:a", "aac",
            "-b:a", "64k",  # 极低音频比特率
            "-movflags", "+faststart"
        ]
        
        # 根据GPU类型添加超级压缩参数
        if gpu_params['video_codec'] == 'h264_nvenc':
            # NVIDIA GPU - 超级压缩
            cmd.extend([
                "-preset", "p7",  # 最慢但压缩率最高
                "-rc", "vbr",
                "-cq", "40",  # 很高的CQ值
                "-maxrate", "1400k",  # 很低的最大比特率
                "-bufsize", "1400k",
                "-refs", "1",  # 最少参考帧
                "-rc-lookahead", "10"
            ])
        elif gpu_params['video_codec'] == 'h264_videotoolbox':
            # macOS VideoToolbox - 超级压缩
            cmd.extend([
                "-b:v", "1200k",  # 很低的视频码率
                "-maxrate", "1400k",
                "-bufsize", "1400k",
                "-q:v", "75"  # 很高的质量值（很低质量）
            ])
        else:
            # CPU编码 - 超级压缩
            cmd.extend([
                "-preset", "veryslow",  # 最慢预设
                "-crf", "40",  # 很高的CRF值
                "-maxrate", "1200k",  # 很低的最大比特率
                "-bufsize", "1200k",
                "-refs", "1",  # 最少参考帧
                "-trellis", "2",
                "-me_method", "umh",
                "-subq", "9",  # 最高的子像素运动估计质量
                "-aq-mode", "2"  # 自适应量化
            ])
        
        cmd.append(output_path)
        
        print(f"执行超级压缩命令: {' '.join(cmd)}")
        result = subprocess.run(cmd, capture_output=True, text=False)
        
        if result.returncode != 0:
            print(f"超级压缩失败: {result.stderr}")
            return False
        
        print(f"超级压缩成功: {output_path}")
        return True
        
    except Exception as e:
        print(f"超级压缩时发生错误: {e}")
        return False

def compress_final_video(input_path, output_path):
    """对最终视频进行压缩以确保文件大小小于50MB"""
    try:
        # 获取GPU参数
        gpu_params = get_ffmpeg_gpu_params()
        
        # 构建压缩命令，使用更激进的压缩参数
        cmd = [
            "ffmpeg", "-y",
            "-i", input_path,
            "-c:v", gpu_params['video_codec'],
            "-c:a", "aac",
            "-b:a", "80k",  # 进一步降低音频比特率
            "-movflags", "+faststart"
        ]
        
        # 根据GPU类型添加更激进的压缩参数
        if gpu_params['video_codec'] == 'h264_nvenc':
            # NVIDIA GPU - 更激进的压缩
            cmd.extend([
                "-preset", "p6",  # 更慢但压缩率更高
                "-rc", "vbr",
                "-cq", "35",  # 更高的CQ值，更小文件
                "-maxrate", "1800k",  # 降低最大比特率
                "-bufsize", "1800k",
                "-refs", "2",  # 减少参考帧
                "-rc-lookahead", "15"
            ])
        elif gpu_params['video_codec'] == 'h264_videotoolbox':
            # macOS VideoToolbox - 更激进的压缩
            cmd.extend([
                "-b:v", "1600k",  # 降低视频码率
                "-maxrate", "1800k",
                "-bufsize", "1800k",
                "-q:v", "70"  # 更高的质量值（更低质量）
            ])
        else:
            # CPU编码 - 更激进的CRF值
            cmd.extend([
                "-preset", "slow",  # 更慢但压缩率更高
                "-crf", "35",  # 更高的CRF值
                "-maxrate", "1600k",  # 降低最大比特率
                "-bufsize", "1600k",
                "-refs", "2",  # 减少参考帧
                "-trellis", "2",  # 更高的trellis量化
                "-me_method", "umh",  # 更好的运动估计
                "-subq", "8"  # 更高的子像素运动估计质量
            ])
        
        cmd.append(output_path)
        
        print(f"执行最终压缩命令: {' '.join(cmd)}")
        result = subprocess.run(cmd, capture_output=True, text=False)
        
        if result.returncode != 0:
            print(f"最终压缩失败: {result.stderr}")
            return False
        
        print(f"最终压缩成功: {output_path}")
        return True
        
    except Exception as e:
        print(f"最终压缩时发生错误: {e}")
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
        result = subprocess.run(cmd, capture_output=True, text=False)
        
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
        
        # 9. 检查最终视频并进行压缩
        if os.path.exists(final_output_path):
            width, height, fps, duration = get_video_info(final_output_path)
            file_size_mb = os.path.getsize(final_output_path) / (1024 * 1024)
            print(f"\n=== 章节 {chapter_name} 初始视频信息 ===")
            print(f"文件路径: {final_output_path}")
            print(f"视频参数: {width}x{height}px, {fps}fps")
            print(f"视频时长: {duration:.2f}s ({duration/60:.2f}分钟)")
            print(f"文件大小: {file_size_mb:.2f}MB")
            
            # 如果文件大小超过50MB，进行最终压缩
            if file_size_mb > 50:
                print(f"\n=== 文件大小超过50MB，进行最终压缩 ===")
                compressed_path = os.path.join(chapter_path, f"{chapter_name}_compressed.mp4")
                if compress_final_video(final_output_path, compressed_path):
                    # 替换原文件
                    os.remove(final_output_path)
                    os.rename(compressed_path, final_output_path)
                    
                    # 重新检查压缩后的文件信息
                    width, height, fps, duration = get_video_info(final_output_path)
                    file_size_mb = os.path.getsize(final_output_path) / (1024 * 1024)
                    print(f"\n=== 章节 {chapter_name} 压缩后视频信息 ===")
                    print(f"文件路径: {final_output_path}")
                    print(f"视频参数: {width}x{height}px, {fps}fps")
                    print(f"视频时长: {duration:.2f}s ({duration/60:.2f}分钟)")
                    print(f"文件大小: {file_size_mb:.2f}MB")
                    
                    # 如果压缩后仍然超过50MB，进行超级压缩
                    if file_size_mb > 50:
                        print(f"\n=== 文件大小仍超过50MB，进行超级压缩 ===")
                        super_compressed_path = os.path.join(chapter_path, f"{chapter_name}_super_compressed.mp4")
                        if super_compress_video(final_output_path, super_compressed_path):
                            # 替换原文件
                            os.remove(final_output_path)
                            os.rename(super_compressed_path, final_output_path)
                            
                            # 重新检查超级压缩后的文件信息
                            width, height, fps, duration = get_video_info(final_output_path)
                            file_size_mb = os.path.getsize(final_output_path) / (1024 * 1024)
                            print(f"\n=== 章节 {chapter_name} 超级压缩后视频信息 ===")
                            print(f"文件路径: {final_output_path}")
                            print(f"视频参数: {width}x{height}px, {fps}fps")
                            print(f"视频时长: {duration:.2f}s ({duration/60:.2f}分钟)")
                            print(f"文件大小: {file_size_mb:.2f}MB")
                        else:
                            print(f"警告: 超级压缩失败，保留压缩后的文件")
                else:
                    print(f"警告: 最终压缩失败，保留原文件")
            
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