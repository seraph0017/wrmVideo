#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
基于 ComfyUI 的“第一个叙述视频”生成脚本（v2）
- 参考 test/comfyui/test_comfyui.py 的请求逻辑与参数
- CLI 参数参考 main.md 的调用方式：python gen_first_video_async_v2.py data/001 [备注]
- 为每个章节目录找到 chapter_xxx_image_01.*，上传并生成视频
- 将下载的 ComfyUI 输出视频重命名为旧版命名：chapter_xxx_video_1.mp4
"""

import os
import sys
import argparse
import json
import time

# 将 test/comfyui 加入 import 路径，复用现有 ComfyUI 客户端逻辑
REPO_ROOT = os.path.dirname(os.path.abspath(__file__))
TEST_COMFYUI_DIR = os.path.join(REPO_ROOT, 'test', 'comfyui')
sys.path.insert(0, TEST_COMFYUI_DIR)

try:
    import test_comfyui as comfy
except Exception as e:
    print(f"导入 test_comfyui 失败: {e}")
    sys.exit(1)

SUPPORTED_EXTS = ['.jpg', '.jpeg', '.png', '.bmp', '.webp']

# 本地常量，避免依赖 test_comfyui 中的常量
COMFYUI_API_URL = "http://115.190.188.138:8188/api/prompt"
DEFAULT_LENGTH = 161
DEFAULT_FPS = 16


def find_chapters(data_dir):
    """列出 data_dir 下的章节目录（以 'chapter_' 开头的子目录）。"""
    if not os.path.isdir(data_dir):
        return []
    chapters = []
    for name in os.listdir(data_dir):
        path = os.path.join(data_dir, name)
        if os.path.isdir(path) and name.startswith('chapter_'):
            chapters.append((name, path))
    return sorted(chapters)


def find_first_image(chapter_dir):
    """在章节目录中查找 chapter_xxx_image_01.* 图片。"""
    chapter_name = os.path.basename(chapter_dir)
    for ext in SUPPORTED_EXTS:
        candidate = os.path.join(chapter_dir, f"{chapter_name}_image_01{ext}")
        if os.path.exists(candidate):
            return candidate
    # 回退：从目录中找任何 image_01.* 文件
    for file in os.listdir(chapter_dir):
        lower = file.lower()
        if 'image_01' in lower and any(lower.endswith(e) for e in SUPPORTED_EXTS):
            return os.path.join(chapter_dir, file)
    return None

# 新增：查找第二张图
def find_second_image(chapter_dir):
    """在章节目录中查找 chapter_xxx_image_02.* 图片。"""
    chapter_name = os.path.basename(chapter_dir)
    for ext in SUPPORTED_EXTS:
        candidate = os.path.join(chapter_dir, f"{chapter_name}_image_02{ext}")
        if os.path.exists(candidate):
            return candidate
    # 回退：从目录中找任何 image_02.* 文件
    for file in os.listdir(chapter_dir):
        lower = file.lower()
        if 'image_02' in lower and any(lower.endswith(e) for e in SUPPORTED_EXTS):
            return os.path.join(chapter_dir, file)
    return None


def process_single_chapter(chapter_dir, api_url, timeout, max_retries, poll_interval, max_wait):
    """处理单个章节：上传图片、生成两个视频（video_1 与 video_2）、下载并重命名。"""
    chapter_name = os.path.basename(chapter_dir)
    target_video1 = os.path.join(chapter_dir, f"{chapter_name}_video_1.mp4")
    target_video2 = os.path.join(chapter_dir, f"{chapter_name}_video_2.mp4")

    # 整章快速跳过：如 video_1 与 video_2 都已存在
    if os.path.exists(target_video1) and os.path.exists(target_video2):
        print(f"✓ 两个视频均已存在，整章跳过: {chapter_dir}")
        return True

    image_path1 = find_first_image(chapter_dir)
    image_path2 = find_second_image(chapter_dir)

    # 创建配置与客户端（复用 comfy 模块）
    config = comfy.ComfyUIConfig(api_url=api_url, timeout=timeout, max_retries=max_retries)
    client = comfy.ComfyUIClient(config)

    success_any = False

    # 处理第一张图 -> video_1
    if os.path.exists(target_video1):
        print(f"✓ 视频已存在，跳过: {target_video1}")
    else:
        if not image_path1:
            print(f"✗ 未找到首图: {chapter_dir}")
        else:
            print(f"开始上传图片: {os.path.basename(image_path1)}")
            up_ok, up_res, up_err = client.upload_image(image_path1, img_type='input', subfolder='')
            if not up_ok:
                print(f"✗ 图片上传失败: {up_err}")
            else:
                print(json.dumps(up_res, ensure_ascii=False, indent=2))
                image_name1 = up_res.get('name') or os.path.basename(image_path1)
                print(f"开始生成视频（ComfyUI）: {image_name1}")
                success, result, error = client.generate_video_from_image(
                    image_filename=image_name1,
                    positive_prompt="让他动起来",
                    width=720,
                    height=1280,
                    length=DEFAULT_LENGTH,
                    fps=DEFAULT_FPS
                )
                if not success:
                    print(f"✗ 工作流提交失败: {error}")
                else:
                    print("✓ 工作流提交成功")
                    prompt_id = (result or {}).get('prompt_id')
                    if not prompt_id:
                        print("✗ 返回中未找到 prompt_id")
                    else:
                        print(f"prompt_id: {prompt_id}")
                        fname, subfolder, type_ = client.wait_for_output_filename(prompt_id, poll_interval, max_wait)
                        if not fname:
                            print("✗ 轮询超时或未获得输出文件")
                        else:
                            local_path = client.download_view_file(fname, subfolder or 'video', type_ or 'output', chapter_dir)
                            if not local_path:
                                print("✗ 下载失败")
                            else:
                                try:
                                    if os.path.abspath(local_path) != os.path.abspath(target_video1):
                                        if os.path.exists(target_video1):
                                            os.remove(target_video1)
                                        os.replace(local_path, target_video1)
                                    print(f"🎬 已生成并重命名: {target_video1}")
                                    success_any = True
                                except Exception as e:
                                    print(f"✗ 重命名失败: {e}")

    # 处理第二张图 -> video_2
    if os.path.exists(target_video2):
        print(f"✓ 视频已存在，跳过: {target_video2}")
    else:
        if not image_path2:
            print(f"⚠️ 未找到第二张图: {chapter_dir}")
        else:
            print(f"开始上传图片: {os.path.basename(image_path2)}")
            up_ok, up_res, up_err = client.upload_image(image_path2, img_type='input', subfolder='')
            if not up_ok:
                print(f"✗ 图片上传失败: {up_err}")
            else:
                print(json.dumps(up_res, ensure_ascii=False, indent=2))
                image_name2 = up_res.get('name') or os.path.basename(image_path2)
                print(f"开始生成视频（ComfyUI）: {image_name2}")
                success, result, error = client.generate_video_from_image(
                    image_filename=image_name2,
                    positive_prompt="让他动起来",
                    width=720,
                    height=1280,
                    length=DEFAULT_LENGTH,
                    fps=DEFAULT_FPS
                )
                if not success:
                    print(f"✗ 工作流提交失败: {error}")
                else:
                    print("✓ 工作流提交成功")
                    prompt_id = (result or {}).get('prompt_id')
                    if not prompt_id:
                        print("✗ 返回中未找到 prompt_id")
                    else:
                        print(f"prompt_id: {prompt_id}")
                        fname, subfolder, type_ = client.wait_for_output_filename(prompt_id, poll_interval, max_wait)
                        if not fname:
                            print("✗ 轮询超时或未获得输出文件")
                        else:
                            local_path = client.download_view_file(fname, subfolder or 'video', type_ or 'output', chapter_dir)
                            if not local_path:
                                print("✗ 下载失败")
                            else:
                                try:
                                    if os.path.abspath(local_path) != os.path.abspath(target_video2):
                                        if os.path.exists(target_video2):
                                            os.remove(target_video2)
                                        os.replace(local_path, target_video2)
                                    print(f"🎬 已生成并重命名: {target_video2}")
                                    success_any = True
                                except Exception as e:
                                    print(f"✗ 重命名失败: {e}")

    return success_any


def main():
    parser = argparse.ArgumentParser(description='基于 ComfyUI 生成“第一个叙述视频”（v2）')
    parser.add_argument('data_dir', help='数据目录，例如: data/001')
    parser.add_argument('note', nargs='?', default='', help='可选备注（例如：用来异步生成第一个narration的视频）')
    parser.add_argument('--chapter', help='指定处理单个章节，如: chapter_001')

    # 参考 test_comfyui.py 的参数
    parser.add_argument('--api_url', default=COMFYUI_API_URL, help='ComfyUI API地址')
    parser.add_argument('--timeout', type=int, default=30, help='请求超时(秒)')
    parser.add_argument('--max_retries', type=int, default=3, help='最大重试次数')
    parser.add_argument('--poll_interval', type=float, default=1.0, help='轮询间隔(秒)')
    parser.add_argument('--max_wait', type=int, default=900, help='轮询最长等待(秒)')

    args = parser.parse_args()

    data_dir = args.data_dir
    if not os.path.isdir(data_dir):
        print(f"错误：数据目录不存在: {data_dir}")
        sys.exit(1)

    if args.note:
        print(f"备注: {args.note}")

    if args.chapter:
        chapter_dir = os.path.join(data_dir, args.chapter)
        if not os.path.isdir(chapter_dir):
            print(f"错误：章节目录不存在: {chapter_dir}")
            sys.exit(1)
        ok = process_single_chapter(chapter_dir, args.api_url, args.timeout, args.max_retries, args.poll_interval, args.max_wait)
        sys.exit(0 if ok else 1)

    # 处理所有章节
    chapters = find_chapters(data_dir)
    if not chapters:
        print(f"警告：未在 {data_dir} 下找到章节目录")
        sys.exit(0)

    success_count = 0
    for chapter_name, chapter_dir in chapters:
        print(f"\n=== 处理章节: {chapter_name} ===")
        ok = process_single_chapter(chapter_dir, args.api_url, args.timeout, args.max_retries, args.poll_interval, args.max_wait)
        if ok:
            success_count += 1
    print(f"\n完成：{success_count}/{len(chapters)} 章节生成任务成功")
    sys.exit(0 if success_count > 0 else 1)


if __name__ == '__main__':
    main()