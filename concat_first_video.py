#!/usr/bin/env python3
"""concat_first_video.py

批量处理指定作品目录（如 data/001），把每个 chapter 目录下的
    chapter_xxx_video_1.mp4
    chapter_xxx_video_2.mp4
按照 gen_video.py 中的 VIDEO_STANDARDS（720x1280 30fps H.264）要求拼接成
    chapter_xxx_first_video.mp4
并在 video_2 前叠加转场特效 src/banner/fuceng1.mov。

用法：
    python concat_first_video.py data/001
"""

from __future__ import annotations

import argparse
import json
import shutil
import subprocess
from pathlib import Path
from typing import List

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

# ------------------------- 全局常量 ------------------------- #

PROJECT_ROOT = Path(__file__).resolve().parent
BANNER_DIR = PROJECT_ROOT / "src" / "banner"
FUCENG_PATH = BANNER_DIR / "fuceng1.mov"

# 若 gen_video.py 修改了标准，只需同步此处即可
VIDEO_STANDARDS = {
    "width": 720,
    "height": 1280,
    "fps": 30,
    "video_codec": "libx264",
    "audio_codec": "aac",
}

TEMP_DIR_NAME = "temp_concat_first_video"

# ------------------------- 工具函数 ------------------------- #

def run_cmd(cmd: List[str]) -> None:
    """运行 shell 命令并在失败时抛异常。"""
    try:
        subprocess.run(cmd, check=True)
    except subprocess.CalledProcessError as e:
        raise RuntimeError(f"命令执行失败: {' '.join(cmd)}\n{e}")


def generate_overlay_video(video2: Path, temp_dir: Path) -> Path:
    """在 video2 上叠加 fuceng1.mov 转场特效，返回处理后的视频路径。"""
    output_path = temp_dir / f"{video2.stem}_overlay.mp4"
    width, height, fps = (
        VIDEO_STANDARDS["width"],
        VIDEO_STANDARDS["height"],
        VIDEO_STANDARDS["fps"],
    )

    if not FUCENG_PATH.exists():
        print("⚠️ 未找到 fuceng1.mov，直接返回原 video2")
        return video2

    # 获取GPU优化参数
    gpu_params = get_ffmpeg_gpu_params()

    # 先统一分辨率，并在前 5 秒（或 fuceng 时长更短者）叠加转场
    # 由于无法提前获取 fuceng 时长，直接在前 5 秒启用 enable between(t,0,5)
    filter_complex = (
        f"[0:v]scale={width}:{height}:force_original_aspect_ratio=increase,"  # 调整分辨率
        f"crop={width}:{height},setsar=1[v0];"
        f"[1:v]scale={width}:{height},format=rgba,colorkey=0x000000:0.3:0.0,setsar=1[fg];"
        f"[v0][fg]overlay=(W-w)/2:(H-h)/2:enable='between(t,0,5)'[v]"
    )

    cmd = ["ffmpeg", "-y"]
    
    # 添加硬件加速参数（如果可用）
    if 'hwaccel' in gpu_params:
        cmd.extend(["-hwaccel", gpu_params['hwaccel']])
    if 'hwaccel_output_format' in gpu_params:
        cmd.extend(["-hwaccel_output_format", gpu_params['hwaccel_output_format']])
    
    cmd.extend([
        "-i", str(video2),
        "-i", str(FUCENG_PATH),
        "-filter_complex", filter_complex,
        "-map", "[v]",
        "-map", "0:a?",  # 若存在音轨则保留
        "-c:v", gpu_params.get('video_codec', VIDEO_STANDARDS["video_codec"]),
        "-c:a", VIDEO_STANDARDS["audio_codec"],
        "-r", str(fps)
    ])
    
    # 添加GPU特定的编码参数
    if 'preset' in gpu_params:
        cmd.extend(["-preset", gpu_params['preset']])
    if 'tune' in gpu_params:
        cmd.extend(["-tune", gpu_params['tune']])
    
    # 添加额外的优化参数
    cmd.extend(gpu_params.get('extra_params', []))
    
    cmd.extend(["-pix_fmt", "yuv420p", str(output_path)])

    print("执行转场叠加...", " ".join(cmd))
    run_cmd(cmd)
    return output_path


def concat_videos(video1: Path, video2: Path, output: Path) -> None:
    """利用 concat demuxer 无损拼接两个 mp4（需封装相同编码）。"""
    concat_list = output.parent / (output.stem + "_list.txt")
    concat_list.write_text(f"file '{video1.resolve()}'\nfile '{video2.resolve()}'\n", encoding="utf-8")

    cmd = [
        "ffmpeg",
        "-y",
        "-f",
        "concat",
        "-safe",
        "0",
        "-i",
        str(concat_list),
        "-c",
        "copy",
        str(output),
    ]
    print("执行视频拼接...", " ".join(cmd))
    run_cmd(cmd)
    concat_list.unlink(missing_ok=True)

# ------------------------- 主逻辑 ------------------------- #

def process_chapter(chapter_dir: Path) -> None:
    """处理单个章节目录。"""
    video1 = next(chapter_dir.glob("*_video_1.mp4"), None)
    video2 = next(chapter_dir.glob("*_video_2.mp4"), None)

    if not video1 or not video2:
        print(f"❌ 缺少 video_1 / video_2: {chapter_dir}")
        return

    output_video = chapter_dir / (chapter_dir.name + "_first_video.mp4")
    if output_video.exists():
        print(f"✅ 已存在，跳过: {output_video}")
        return

    temp_dir = chapter_dir / TEMP_DIR_NAME
    temp_dir.mkdir(exist_ok=True)

    # 获取GPU优化参数
    gpu_params = get_ffmpeg_gpu_params()
    
    # 统一分辨率与帧率到 video1
    scaled_video1 = temp_dir / f"{video1.stem}_scaled.mp4"
    cmd_scale_v1 = ["ffmpeg", "-y"]
    
    # 添加硬件加速参数（如果可用）
    if 'hwaccel' in gpu_params:
        cmd_scale_v1.extend(["-hwaccel", gpu_params['hwaccel']])
    if 'hwaccel_output_format' in gpu_params:
        cmd_scale_v1.extend(["-hwaccel_output_format", gpu_params['hwaccel_output_format']])
    
    cmd_scale_v1.extend([
        "-i", str(video1),
        "-vf", f"scale={VIDEO_STANDARDS['width']}:{VIDEO_STANDARDS['height']}:force_original_aspect_ratio=increase,crop={VIDEO_STANDARDS['width']}:{VIDEO_STANDARDS['height']}",
        "-c:v", gpu_params.get('video_codec', VIDEO_STANDARDS["video_codec"]),
        "-c:a", VIDEO_STANDARDS["audio_codec"],
        "-r", str(VIDEO_STANDARDS["fps"])
    ])
    
    # 添加GPU特定的编码参数
    if 'preset' in gpu_params:
        cmd_scale_v1.extend(["-preset", gpu_params['preset']])
    if 'tune' in gpu_params:
        cmd_scale_v1.extend(["-tune", gpu_params['tune']])
    
    # 添加额外的优化参数
    cmd_scale_v1.extend(gpu_params.get('extra_params', []))
    
    cmd_scale_v1.extend(["-pix_fmt", "yuv420p", str(scaled_video1)])
    print("统一 video_1 分辨率...", " ".join(cmd_scale_v1))
    run_cmd(cmd_scale_v1)

    # 对 video2 处理叠加 & 分辨率
    processed_video2 = generate_overlay_video(video2, temp_dir)

    if processed_video2 != video2:
        # 处理后视频已保证分辨率，直接用
        scaled_video2 = processed_video2
    else:
        # 若未叠加则仍需缩放裁剪
        scaled_video2 = temp_dir / f"{video2.stem}_scaled.mp4"
        cmd_scale_v2 = ["ffmpeg", "-y"]
        
        # 添加硬件加速参数（如果可用）
        if 'hwaccel' in gpu_params:
            cmd_scale_v2.extend(["-hwaccel", gpu_params['hwaccel']])
        if 'hwaccel_output_format' in gpu_params:
            cmd_scale_v2.extend(["-hwaccel_output_format", gpu_params['hwaccel_output_format']])
        
        cmd_scale_v2.extend([
            "-i", str(video2),
            "-vf", f"scale={VIDEO_STANDARDS['width']}:{VIDEO_STANDARDS['height']}:force_original_aspect_ratio=increase,crop={VIDEO_STANDARDS['width']}:{VIDEO_STANDARDS['height']}",
            "-c:v", gpu_params.get('video_codec', VIDEO_STANDARDS["video_codec"]),
            "-c:a", VIDEO_STANDARDS["audio_codec"],
            "-r", str(VIDEO_STANDARDS["fps"])
        ])
        
        # 添加GPU特定的编码参数
        if 'preset' in gpu_params:
            cmd_scale_v2.extend(["-preset", gpu_params['preset']])
        if 'tune' in gpu_params:
            cmd_scale_v2.extend(["-tune", gpu_params['tune']])
        
        # 添加额外的优化参数
        cmd_scale_v2.extend(gpu_params.get('extra_params', []))
        
        cmd_scale_v2.extend(["-pix_fmt", "yuv420p", str(scaled_video2)])
        print("统一 video_2 分辨率...", " ".join(cmd_scale_v2))
        run_cmd(cmd_scale_v2)

    concat_videos(scaled_video1, scaled_video2, output_video)
    print(f"✅ 章节合并完成: {output_video}")

    # 清理临时目录
    shutil.rmtree(temp_dir, ignore_errors=True)


def main():
    parser = argparse.ArgumentParser(description="合并每章的 video_1 与 video_2，加入转场特效")
    parser.add_argument("work_dir", help="作品目录，例如 data/001")
    args = parser.parse_args()

    root = Path(args.work_dir).resolve()
    if not root.exists():
        raise FileNotFoundError(f"目录不存在: {root}")

    chapters = sorted([p for p in root.iterdir() if p.is_dir() and p.name.startswith("chapter_")])
    if not chapters:
        raise RuntimeError("未找到 chapter_* 目录")

    for ch in chapters:
        print("\n=== 处理章节 ===", ch)
        try:
            process_chapter(ch)
        except Exception as e:
            print(f"❌ 处理失败 {ch}: {e}")

if __name__ == "__main__":
    main()