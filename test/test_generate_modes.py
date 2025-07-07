#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
测试generate.py的两种使用模式
"""

import os
import subprocess
import sys

def test_single_chapter():
    """
    测试单个章节处理模式
    """
    print("=== 测试单个章节处理模式 ===")
    
    # 切换到项目根目录
    os.chdir(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
    chapter_path = "data/001/chapter01"
    
    if not os.path.exists(chapter_path):
        print(f"❌ 章节目录不存在: {chapter_path}")
        return False
    
    script_file = os.path.join(chapter_path, "chapter01_script.txt")
    if not os.path.exists(script_file):
        print(f"❌ 脚本文件不存在: {script_file}")
        return False
    
    print(f"✅ 章节目录存在: {chapter_path}")
    print(f"✅ 脚本文件存在: {script_file}")
    
    # 检查生成的视频文件
    video_file = os.path.join(chapter_path, "chapter01_complete.mp4")
    if os.path.exists(video_file):
        print(f"✅ 章节视频已存在: {video_file}")
        
        # 检查音频质量
        try:
            result = subprocess.run([
                'ffprobe', '-v', 'quiet', '-show_entries', 
                'stream=sample_rate', '-select_streams', 'a:0', 
                '-of', 'csv=p=0', video_file
            ], capture_output=True, text=True)
            
            if result.returncode == 0 and result.stdout.strip():
                sample_rate = int(result.stdout.strip())
                if sample_rate >= 44100:
                    print(f"✅ 音频质量良好: {sample_rate} Hz")
                else:
                    print(f"⚠️  音频质量较低: {sample_rate} Hz")
            else:
                print("❌ 无法检测音频质量")
        except Exception as e:
            print(f"❌ 检测音频质量时出错: {e}")
    else:
        print(f"❌ 章节视频不存在: {video_file}")
    
    return True

def test_multiple_chapters():
    """
    测试多章节处理模式
    """
    print("\n=== 测试多章节处理模式 ===")
    
    base_path = "data/001"
    
    if not os.path.exists(base_path):
        print(f"❌ 基础目录不存在: {base_path}")
        return False
    
    # 查找章节目录
    chapter_dirs = []
    for item in os.listdir(base_path):
        item_path = os.path.join(base_path, item)
        if os.path.isdir(item_path) and item.startswith('chapter') and item[7:].isdigit():
            chapter_dirs.append(item)
    
    if not chapter_dirs:
        print(f"❌ 没有找到章节目录")
        return False
    
    chapter_dirs.sort(key=lambda x: int(x[7:]))
    print(f"✅ 找到 {len(chapter_dirs)} 个章节目录: {', '.join(chapter_dirs)}")
    
    # 检查每个章节的脚本文件
    valid_chapters = 0
    for chapter_dir in chapter_dirs:
        chapter_path = os.path.join(base_path, chapter_dir)
        script_file = os.path.join(chapter_path, f"{chapter_dir}_script.txt")
        
        if os.path.exists(script_file):
            valid_chapters += 1
            print(f"  ✅ {chapter_dir}: 脚本文件存在")
        else:
            print(f"  ❌ {chapter_dir}: 脚本文件不存在")
    
    print(f"✅ 有效章节数: {valid_chapters}/{len(chapter_dirs)}")
    
    # 检查最终视频文件
    final_video = os.path.join(base_path, "final_complete_video.mp4")
    if os.path.exists(final_video):
        print(f"✅ 最终视频已存在: {final_video}")
    else:
        print(f"❌ 最终视频不存在: {final_video}")
    
    return True

def show_usage_examples():
    """
    显示使用示例
    """
    print("\n=== 使用示例 ===")
    print("\n1. 处理单个章节:")
    print("   python generate.py data/001/chapter01")
    print("   - 只处理chapter01目录")
    print("   - 生成 chapter01_complete.mp4")
    
    print("\n2. 处理多个章节:")
    print("   python generate.py data/001")
    print("   - 处理data/001下的所有章节目录")
    print("   - 生成各章节的 chapterXX_complete.mp4")
    print("   - 最终合并为 final_complete_video.mp4")
    
    print("\n3. 音频质量提升:")
    print("   python utils/fix_audio_quality.py data/001/chapter01")
    print("   - 检测并修复低质量音频文件")
    print("   - 提升采样率到44.1kHz")

def main():
    """
    主测试函数
    """
    print("视频生成系统 - 使用模式测试")
    print("=" * 50)
    
    # 测试单个章节模式
    test_single_chapter()
    
    # 测试多章节模式
    test_multiple_chapters()
    
    # 显示使用示例
    show_usage_examples()
    
    print("\n=== 测试完成 ===")
    print("\n💡 提示:")
    print("- 如果音频质量较低，请运行 utils/fix_audio_quality.py 修复")
    print("- 新生成的音频将自动使用44.1kHz采样率")
    print("- 支持单个章节和多章节两种处理模式")

if __name__ == "__main__":
    main()