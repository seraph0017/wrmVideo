#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
视频生成脚本 - 重写版本
按顺序执行：concat_narration_video.py -> concat_finish_video.py
"""

import os
import sys
import argparse
import subprocess
from pathlib import Path
import glob

def standardize_segments(data_path, target_width=720, target_height=1280, fps=30):
    """将每个章节目录下 temp_narration_videos 内的 segment_*.mp4 标准化为 720x1280。
    - 使用 scale=force_original_aspect_ratio=increase + 居中 crop，避免拉伸
    - 设置 setsar=1，确保像素宽高比正确
    - 保持或可选混入原音频（若有）
    """
    print(f"\n=== 标准化 segment 视频到 {target_width}x{target_height} ===")
    changed = 0
    chapter_dirs = sorted([d for d in glob.glob(os.path.join(data_path, "chapter_*"))
                           if os.path.isdir(d)])

    for chapter_dir in chapter_dirs:
        temp_dir = os.path.join(chapter_dir, "temp_narration_videos")
        if not os.path.isdir(temp_dir):
            continue

        segment_files = sorted(glob.glob(os.path.join(temp_dir, "segment_*.mp4")))
        if not segment_files:
            continue

        print(f"{os.path.basename(chapter_dir)}: 找到 {len(segment_files)} 段")
        for seg in segment_files:
            try:
                probe = subprocess.run(
                    [
                        "ffprobe", "-v", "error",
                        "-select_streams", "v:0",
                        "-show_entries", "stream=width,height",
                        "-of", "csv=p=0:s=x",
                        seg,
                    ],
                    capture_output=True,
                    text=True,
                )
                if probe.returncode != 0:
                    print(f"  ❌ ffprobe 失败: {os.path.basename(seg)}")
                    continue

                res = probe.stdout.strip()
                w, h = (0, 0)
                if "x" in res:
                    try:
                        w, h = map(int, res.split("x"))
                    except Exception:
                        pass

                if w == target_width and h == target_height:
                    print(f"  ✓ 已是 {target_width}x{target_height}: {os.path.basename(seg)}")
                    continue

                tmp_out = seg + ".std.mp4"
                vf = (
                    f"scale={target_width}:{target_height}:force_original_aspect_ratio=increase,"
                    f"crop={target_width}:{target_height}:(in_w-{target_width})/2:(in_h-{target_height})/2,"
                    "setsar=1"
                )
                cmd = [
                    "ffmpeg", "-y", "-i", seg,
                    "-map", "0:v:0", "-map", "0:a?",
                    "-vf", vf,
                    "-r", str(fps),
                    "-c:v", "libx264", "-crf", "20", "-preset", "medium",
                    "-pix_fmt", "yuv420p",
                    "-c:a", "aac", "-b:a", "160k",
                    "-movflags", "+faststart",
                    tmp_out,
                ]

                proc = subprocess.run(cmd, capture_output=True, text=True)
                if proc.returncode == 0 and os.path.exists(tmp_out):
                    os.replace(tmp_out, seg)
                    print(f"  ✓ 已标准化: {os.path.basename(seg)} -> {target_width}x{target_height}")
                    changed += 1
                else:
                    print(f"  ❌ 标准化失败: {os.path.basename(seg)}")
            except Exception as e:
                print(f"  ❌ 处理失败 {os.path.basename(seg)}: {e}")

    if changed == 0:
        print("没有需要标准化的段或全部已标准化")
    else:
        print(f"共标准化 {changed} 段")

def run_script(script_name, data_path):
    """
    运行指定的脚本
    
    Args:
        script_name: 脚本名称
        data_path: 数据路径
    
    Returns:
        bool: 执行是否成功
    """
    try:
        script_path = os.path.join(os.path.dirname(os.path.abspath(__file__)), script_name)
        if not os.path.exists(script_path):
            print(f"❌ 脚本不存在: {script_path}")
            return False
        
        print(f"\n=== 执行 {script_name} ===")
        print(f"命令: python {script_name} {data_path}")
        
        # 执行脚本
        result = subprocess.run(
            [sys.executable, script_path, data_path],
            capture_output=True,
            text=False,
            cwd=os.path.dirname(os.path.abspath(__file__))
        )
        
        # 输出执行结果
        if result.stdout:
            try:
                stdout_text = result.stdout.decode('utf-8', errors='ignore')
            except:
                stdout_text = str(result.stdout)
            print(stdout_text)
        
        if result.stderr:
            try:
                stderr_text = result.stderr.decode('utf-8', errors='ignore')
            except:
                stderr_text = str(result.stderr)
            print(f"错误输出: {stderr_text}")
        
        if result.returncode == 0:
            print(f"✓ {script_name} 执行成功")
            return True
        else:
            print(f"❌ {script_name} 执行失败，返回码: {result.returncode}")
            return False
            
    except Exception as e:
        print(f"❌ 执行 {script_name} 时发生异常: {e}")
        return False

def process_data_directory(data_path):
    """
    处理数据目录，按顺序执行三个脚本
    
    Args:
        data_path: 数据目录路径
    
    Returns:
        bool: 处理是否成功
    """
    print(f"开始处理数据目录: {data_path}")
    
    # 检查数据目录是否存在
    if not os.path.exists(data_path):
        print(f"❌ 数据目录不存在: {data_path}")
        return False
    
    # 检查是否包含章节目录
    chapter_dirs = sorted([d for d in glob.glob(os.path.join(data_path, "chapter_*")) 
                          if os.path.isdir(d)])
    
    if not chapter_dirs:
        print(f"❌ 在 {data_path} 中没有找到章节目录")
        return False
    
    print(f"找到 {len(chapter_dirs)} 个章节目录")

    # 预标准化：若章节下已有 segment_*.mp4（例如前置流程生成），先统一到 720x1280
    try:
        standardize_segments(data_path)
    except Exception as e:
        print(f"❌ 预标准化阶段发生异常: {e}")

    # 按顺序执行两个脚本
    scripts = [
        "concat_narration_video.py", 
        "concat_finish_video.py"
    ]
    
    success_count = 0
    
    for script in scripts:
        if run_script(script, data_path):
            success_count += 1
            # 在生成旁白主视频后，统一所有 segment 段到 720x1280，避免后续拼接拉伸/偏移
            if script == "concat_narration_video.py":
                try:
                    standardize_segments(data_path)
                except Exception as e:
                    print(f"❌ 标准化阶段发生异常: {e}")
        else:
            print(f"❌ {script} 执行失败，停止后续处理")
            break
    
    if success_count == len(scripts):
        print(f"\n✓ 所有脚本执行成功！数据目录 {data_path} 处理完成")
        
        # 显示最终生成的视频文件
        print("\n=== 生成的视频文件 ===")
        for chapter_dir in chapter_dirs:
            chapter_name = os.path.basename(chapter_dir)
            
            # 检查各阶段生成的文件
            first_video = os.path.join(chapter_dir, f"{chapter_name}_first_video.mp4")
            main_video = os.path.join(chapter_dir, f"{chapter_name}_main_video.mp4")
            complete_video = os.path.join(chapter_dir, f"{chapter_name}_complete_video.mp4")
            
            print(f"\n{chapter_name}:")
            if os.path.exists(first_video):
                print(f"  ✓ first_video: {first_video}")
            else:
                print(f"  ❌ first_video: 未生成")
                
            if os.path.exists(main_video):
                print(f"  ✓ main_video: {main_video}")
            else:
                print(f"  ❌ main_video: 未生成")
                
            if os.path.exists(complete_video):
                print(f"  ✓ complete_video: {complete_video}")
            else:
                print(f"  ❌ complete_video: 未生成")
        
        return True
    else:
        print(f"\n❌ 处理失败，成功执行 {success_count}/{len(scripts)} 个脚本")
        return False

def main():
    """
    主函数
    """
    parser = argparse.ArgumentParser(
        description='视频生成脚本 - 按顺序执行 concat_narration_video.py、concat_finish_video.py',
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
使用示例:
  python gen_video.py data/001
  
执行流程:
  1. concat_narration_video.py - 生成 main_video (添加旁白、BGM、音效等)
  2. concat_finish_video.py - 生成 complete_video (添加片尾视频)
        """
    )
    
    parser.add_argument(
        'data_path', 
        help='数据目录路径，包含多个 chapter_xxx 子目录'
    )
    
    parser.add_argument(
        '--verbose', '-v',
        action='store_true',
        help='显示详细输出'
    )
    
    args = parser.parse_args()
    
    # 设置详细输出
    if args.verbose:
        print("启用详细输出模式")
    
    # 验证输入路径
    data_path = os.path.abspath(args.data_path)
    
    print(f"视频生成脚本启动")
    print(f"数据路径: {data_path}")
    print(f"执行顺序: concat_narration_video.py -> concat_finish_video.py")
    
    # 处理数据目录
    if process_data_directory(data_path):
        print(f"\n🎉 视频生成完成！")
        sys.exit(0)
    else:
        print(f"\n❌ 视频生成失败！")
        sys.exit(1)

if __name__ == "__main__":
    main()