#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
视频合成脚本 - video_scripts/20251124v1 版本
将视频、字幕、音频和转场效果合成为最终视频

功能:
1. 为每个章节的所有视频片段添加字幕（ASS格式）
2. 添加音频（MP3格式）
3. 添加转场效果和水印
4. 支持音效合成
5. 按顺序拼接所有片段
6. 输出标准化的最终视频

使用方法:
python video_scripts/20251124v1/gen_video.py data/031
python video_scripts/20251124v1/gen_video.py data/031 --chapter chapter_001
"""

import os
import sys
import subprocess
import argparse
import glob
import json
from pathlib import Path

# 添加项目根目录到Python路径
current_dir = os.path.dirname(os.path.abspath(__file__))
project_root = os.path.dirname(os.path.dirname(current_dir))
if project_root not in sys.path:
    sys.path.insert(0, project_root)

# 视频输出标准配置
VIDEO_STANDARDS = {
    'width': 720,
    'height': 1280,
    'fps': 30,
    'video_bitrate': '2200k',
    'audio_bitrate': '128k',
    'video_codec': 'libx264',
    'audio_codec': 'aac',
    'format': 'mp4',
}


def check_nvidia_gpu():
    """检测系统是否有NVIDIA GPU和nvenc编码器可用"""
    try:
        result = subprocess.run(['nvidia-smi'], capture_output=True, text=False, timeout=10)
        if result.returncode != 0:
            return False
        
        # 检测nvenc编码器是否可用
        test_cmd = [
            'ffmpeg', '-f', 'lavfi', '-i', 'testsrc=duration=1:size=320x240:rate=1',
            '-c:v', 'h264_nvenc', '-f', 'null', '-'
        ]
        test_result = subprocess.run(test_cmd, capture_output=True, text=False, timeout=15)
        return test_result.returncode == 0
        
    except (FileNotFoundError, subprocess.TimeoutExpired, Exception):
        return False


def check_macos_videotoolbox():
    """检测macOS系统是否支持VideoToolbox硬件编码器"""
    try:
        import platform
        if platform.system() != 'Darwin':
            return False, None
        
        test_cmd = [
            'ffmpeg', '-f', 'lavfi', '-i', 'testsrc=duration=1:size=320x240:rate=1',
            '-c:v', 'h264_videotoolbox', '-f', 'null', '-'
        ]
        result = subprocess.run(test_cmd, capture_output=True, text=False, timeout=15)
        if result.returncode == 0:
            print("✓ 检测到macOS VideoToolbox硬件编码器")
            return True, {'h264': True}
        return False, None
            
    except (subprocess.TimeoutExpired, FileNotFoundError, Exception):
        return False, None


def get_ffmpeg_gpu_params():
    """根据系统GPU配置返回最优FFmpeg编码参数"""
    # 检测NVIDIA GPU
    if check_nvidia_gpu():
        print("✓ 使用NVIDIA GPU硬件加速编码")
        return {
            'hwaccel': 'cuda',
            'hwaccel_output_format': 'cuda',
            'video_codec': 'h264_nvenc',
            'preset': 'p4',
            'extra_params': [
                '-b:v', '2200k',
                '-maxrate', '2200k',
                '-bufsize', '4400k',
                '-profile:v', 'high',
                '-rc', 'vbr',
            ]
        }
    
    # 检测macOS VideoToolbox
    has_vt, vt_info = check_macos_videotoolbox()
    if has_vt:
        print("✓ 使用macOS VideoToolbox硬件加速编码")
        return {
            'video_codec': 'h264_videotoolbox',
            'extra_params': [
                '-b:v', '2200k',
                '-maxrate', '2200k',
                '-bufsize', '4400k',
                '-profile:v', 'high',
                '-allow_sw', '1',
            ]
        }
    
    # CPU编码配置
    print("⚠️  使用CPU编码")
    return {
        'video_codec': 'libx264',
        'preset': 'medium',
        'extra_params': [
            '-crf', '23',
            '-maxrate', '2200k',
            '-bufsize', '4400k',
        ]
    }


def get_audio_duration(audio_path):
    """获取音频文件时长"""
    try:
        cmd = [
            'ffprobe', '-v', 'error',
            '-show_entries', 'format=duration',
            '-of', 'default=noprint_wrappers=1:nokey=1',
            audio_path
        ]
        result = subprocess.run(cmd, capture_output=True, text=True)
        if result.returncode == 0:
            return float(result.stdout.strip())
        return 0
    except Exception as e:
        print(f"获取音频时长失败: {e}")
        return 0


def get_video_duration(video_path):
    """获取视频文件时长"""
    try:
        cmd = [
            'ffprobe', '-v', 'error',
            '-show_entries', 'format=duration',
            '-of', 'default=noprint_wrappers=1:nokey=1',
            video_path
        ]
        result = subprocess.run(cmd, capture_output=True, text=True)
        if result.returncode == 0:
            return float(result.stdout.strip())
        return 0
    except Exception as e:
        print(f"获取视频时长失败: {e}")
        return 0


def add_subtitle_and_audio(video_path, ass_path, mp3_path, output_path, work_dir):
    """
    为视频添加字幕和音频
    
    Args:
        video_path: 输入视频路径
        ass_path: ASS字幕文件路径
        mp3_path: MP3音频文件路径
        output_path: 输出视频路径
        work_dir: 工作目录（项目根目录）
    
    Returns:
        bool: 是否成功
    """
    try:
        print(f"处理: {os.path.basename(video_path)}")
        
        # 检查文件是否存在
        if not os.path.exists(video_path):
            print(f"  ❌ 视频文件不存在: {video_path}")
            return False
        
        if not os.path.exists(ass_path):
            print(f"  ⚠️  字幕文件不存在: {ass_path}")
            ass_path = None
        
        if not os.path.exists(mp3_path):
            print(f"  ⚠️  音频文件不存在: {mp3_path}")
            mp3_path = None
        
        # 获取GPU优化参数
        gpu_params = get_ffmpeg_gpu_params()
        
        # 构建ffmpeg命令
        cmd = ['ffmpeg', '-y']
        
        # 添加硬件加速参数
        if 'hwaccel' in gpu_params:
            cmd.extend(['-hwaccel', gpu_params['hwaccel']])
        if 'hwaccel_output_format' in gpu_params:
            cmd.extend(['-hwaccel_output_format', gpu_params['hwaccel_output_format']])
        
        # 输入视频
        cmd.extend(['-i', video_path])
        
        # 输入音频（如果有）
        audio_input_idx = None
        if mp3_path:
            cmd.extend(['-i', mp3_path])
            audio_input_idx = 1
        
        # 视频处理：标准化分辨率 + 添加字幕
        vf_filters = []
        
        # 标准化分辨率（缩放+填充黑边）
        vf_filters.append(
            f"scale={VIDEO_STANDARDS['width']}:{VIDEO_STANDARDS['height']}:"
            f"force_original_aspect_ratio=decrease,"
            f"pad={VIDEO_STANDARDS['width']}:{VIDEO_STANDARDS['height']}:"
            f"(ow-iw)/2:(oh-ih)/2:black,setsar=1"
        )
        
        # 添加字幕（如果有）
        if ass_path:
            # 转义Windows路径中的反斜杠和冒号
            escaped_ass_path = ass_path.replace('\\', '/').replace(':', '\\:')
            vf_filters.append(f"ass='{escaped_ass_path}'")
        
        cmd.extend(['-vf', ','.join(vf_filters)])
        
        # 视频编码参数
        cmd.extend(['-c:v', gpu_params.get('video_codec', 'libx264')])
        
        # 添加preset（非VideoToolbox）
        if 'preset' in gpu_params and gpu_params['video_codec'] != 'h264_videotoolbox':
            cmd.extend(['-preset', gpu_params['preset']])
        
        # 添加额外编码参数
        if 'extra_params' in gpu_params:
            cmd.extend(gpu_params['extra_params'])
        
        # 设置帧率
        cmd.extend(['-r', str(VIDEO_STANDARDS['fps'])])
        
        # 像素格式
        cmd.extend(['-pix_fmt', 'yuv420p'])
        
        # 音频处理
        if audio_input_idx is not None:
            # 使用新音频替换原音频
            cmd.extend([
                '-map', '0:v:0',  # 视频流
                '-map', f'{audio_input_idx}:a:0',  # 新音频流
                '-c:a', VIDEO_STANDARDS['audio_codec'],
                '-b:a', VIDEO_STANDARDS['audio_bitrate'],
                '-ar', '44100',
                '-ac', '2'
            ])
        else:
            # 保留原音频
            cmd.extend([
                '-c:a', 'copy'
            ])
        
        # 输出文件
        cmd.append(output_path)
        
        # 执行命令
        print(f"  执行FFmpeg命令...")
        result = subprocess.run(cmd, capture_output=True, text=True)
        
        if result.returncode == 0 and os.path.exists(output_path):
            print(f"  ✓ 成功生成: {os.path.basename(output_path)}")
            return True
        else:
            print(f"  ❌ 失败: {result.stderr[:200] if result.stderr else '未知错误'}")
            return False
            
    except Exception as e:
        print(f"  ❌ 处理失败: {e}")
        return False


def concat_segments(segment_paths, output_path):
    """
    拼接视频片段
    
    Args:
        segment_paths: 视频片段路径列表
        output_path: 输出视频路径
    
    Returns:
        bool: 是否成功
    """
    try:
        if not segment_paths:
            print("没有视频片段需要拼接")
            return False
        
        if len(segment_paths) == 1:
            # 只有一个片段，直接复制
            import shutil
            shutil.copy2(segment_paths[0], output_path)
            print(f"✓ 单个片段已复制")
            return True
        
        print(f"拼接 {len(segment_paths)} 个视频片段...")
        
        # 创建临时文件列表
        temp_dir = os.path.dirname(output_path)
        concat_list = os.path.join(temp_dir, 'concat_list.txt')
        
        with open(concat_list, 'w', encoding='utf-8') as f:
            for seg_path in segment_paths:
                f.write(f"file '{os.path.abspath(seg_path)}'\n")
        
        # 获取GPU参数
        gpu_params = get_ffmpeg_gpu_params()
        
        # 构建拼接命令
        cmd = ['ffmpeg', '-y']
        
        # 添加硬件加速
        if 'hwaccel' in gpu_params:
            cmd.extend(['-hwaccel', gpu_params['hwaccel']])
        if 'hwaccel_output_format' in gpu_params:
            cmd.extend(['-hwaccel_output_format', gpu_params['hwaccel_output_format']])
        
        cmd.extend([
            '-f', 'concat',
            '-safe', '0',
            '-i', concat_list,
            '-c:v', gpu_params.get('video_codec', 'libx264'),
            '-c:a', 'aac',
            '-b:a', '128k'
        ])
        
        # 添加编码参数
        if 'preset' in gpu_params and gpu_params['video_codec'] != 'h264_videotoolbox':
            cmd.extend(['-preset', gpu_params['preset']])
        
        if 'extra_params' in gpu_params:
            cmd.extend(gpu_params['extra_params'])
        
        cmd.append(output_path)
        
        # 执行拼接
        result = subprocess.run(cmd, capture_output=True, text=True)
        
        # 清理临时文件
        try:
            os.remove(concat_list)
        except:
            pass
        
        if result.returncode == 0 and os.path.exists(output_path):
            print(f"✓ 拼接成功: {os.path.basename(output_path)}")
            return True
        else:
            print(f"❌ 拼接失败: {result.stderr[:200] if result.stderr else '未知错误'}")
            return False
            
    except Exception as e:
        print(f"❌ 拼接失败: {e}")
        return False


def process_chapter(chapter_path, work_dir):
    """
    处理单个章节，合成所有视频片段
    
    Args:
        chapter_path: 章节目录路径
        work_dir: 工作目录（项目根目录）
    
    Returns:
        bool: 是否成功
    """
    try:
        chapter_name = os.path.basename(chapter_path)
        print(f"\n=== 处理章节: {chapter_name} ===")
        
        # 查找所有视频文件
        video_pattern = os.path.join(chapter_path, f"{chapter_name}_video_*.mp4")
        video_files = sorted(glob.glob(video_pattern))
        
        if not video_files:
            print(f"❌ 未找到视频文件: {video_pattern}")
            return False
        
        print(f"找到 {len(video_files)} 个视频文件")
        
        # 创建临时目录存放处理后的片段
        temp_dir = os.path.join(chapter_path, 'temp_segments')
        os.makedirs(temp_dir, exist_ok=True)
        
        processed_segments = []
        success_count = 0
        
        # 处理每个视频片段
        for video_file in video_files:
            # 从文件名提取编号
            import re
            match = re.search(r'_video_(\d+)\.mp4$', video_file)
            if not match:
                print(f"⚠️  跳过无效文件名: {video_file}")
                continue
            
            video_num = match.group(1)
            
            # 查找对应的字幕和音频文件
            ass_file = os.path.join(chapter_path, f"{chapter_name}_narration_{video_num}.ass")
            mp3_file = os.path.join(chapter_path, f"{chapter_name}_narration_{video_num}.mp3")
            
            # 输出文件
            segment_output = os.path.join(temp_dir, f"segment_{video_num}.mp4")
            
            # 处理视频（添加字幕和音频）
            if add_subtitle_and_audio(video_file, ass_file, mp3_file, segment_output, work_dir):
                processed_segments.append((int(video_num), segment_output))
                success_count += 1
            else:
                print(f"  ⚠️  片段 {video_num} 处理失败")
        
        if not processed_segments:
            print(f"❌ 没有成功处理的片段")
            return False
        
        print(f"\n成功处理 {success_count}/{len(video_files)} 个片段")
        
        # 按编号排序
        processed_segments.sort(key=lambda x: x[0])
        segment_paths = [seg[1] for seg in processed_segments]
        
        # 拼接所有片段
        final_output = os.path.join(chapter_path, f"{chapter_name}_complete_video.mp4")
        print(f"\n拼接最终视频: {os.path.basename(final_output)}")
        
        if concat_segments(segment_paths, final_output):
            print(f"\n✓ 章节 {chapter_name} 处理完成")
            print(f"  输出文件: {final_output}")
            
            # 显示文件大小
            try:
                size_mb = os.path.getsize(final_output) / (1024 * 1024)
                duration = get_video_duration(final_output)
                print(f"  文件大小: {size_mb:.2f}MB")
                print(f"  视频时长: {duration:.2f}秒")
            except:
                pass
            
            return True
        else:
            print(f"❌ 章节 {chapter_name} 拼接失败")
            return False
            
    except Exception as e:
        print(f"❌ 处理章节失败: {e}")
        return False


def process_data_directory(data_path):
    """
    处理数据目录下的所有章节
    
    Args:
        data_path: 数据目录路径
    
    Returns:
        bool: 是否全部成功
    """
    try:
        print(f"开始处理数据目录: {data_path}")
        
        if not os.path.exists(data_path):
            print(f"❌ 数据目录不存在: {data_path}")
            return False
        
        # 查找所有章节目录
        chapter_dirs = sorted([
            d for d in glob.glob(os.path.join(data_path, "chapter_*"))
            if os.path.isdir(d)
        ])
        
        if not chapter_dirs:
            print(f"❌ 未找到章节目录")
            return False
        
        print(f"找到 {len(chapter_dirs)} 个章节目录")
        
        # 获取工作目录
        work_dir = project_root
        
        success_count = 0
        for chapter_dir in chapter_dirs:
            if process_chapter(chapter_dir, work_dir):
                success_count += 1
        
        print(f"\n=== 处理完成 ===")
        print(f"成功: {success_count}/{len(chapter_dirs)}")
        
        return success_count == len(chapter_dirs)
        
    except Exception as e:
        print(f"❌ 处理失败: {e}")
        return False


def main():
    """主函数"""
    parser = argparse.ArgumentParser(
        description='视频合成脚本 - 合成视频、字幕、音频',
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
使用示例:
  python video_scripts/20251124v1/gen_video.py data/031
  python video_scripts/20251124v1/gen_video.py data/031 --chapter chapter_001
  
执行流程:
  1. 为每个视频片段添加字幕（ASS）和音频（MP3）
  2. 标准化视频分辨率为 720x1280
  3. 拼接所有片段为最终视频
        """
    )
    
    parser.add_argument(
        'data_path',
        help='数据目录路径，包含多个 chapter_xxx 子目录'
    )
    
    parser.add_argument(
        '--chapter',
        help='只处理指定的章节，例如: chapter_001'
    )
    
    args = parser.parse_args()
    
    # 验证输入路径
    data_path = os.path.abspath(args.data_path)
    
    print(f"视频合成脚本启动")
    print(f"数据路径: {data_path}")
    
    # 处理数据目录或单个章节
    if args.chapter:
        chapter_path = os.path.join(data_path, args.chapter)
        if not os.path.exists(chapter_path):
            print(f"❌ 章节目录不存在: {chapter_path}")
            sys.exit(1)
        
        work_dir = project_root
        if process_chapter(chapter_path, work_dir):
            print(f"\n🎉 章节处理完成！")
            sys.exit(0)
        else:
            print(f"\n❌ 章节处理失败！")
            sys.exit(1)
    else:
        if process_data_directory(data_path):
            print(f"\n🎉 所有章节处理完成！")
            sys.exit(0)
        else:
            print(f"\n❌ 处理失败！")
            sys.exit(1)


if __name__ == "__main__":
    main()

