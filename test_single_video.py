#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
测试使用指定图片生成单个视频的脚本
"""

import os
import subprocess
import sys

def test_single_video_generation():
    """
    测试使用指定的两张图片生成视频
    """
    # 指定的图片路径（请根据实际情况修改这些路径）
    first_image = "data/003/chapter_001/chapter_001_image_01.jpeg"
    second_image = "data/003/chapter_001/chapter_001_image_02.jpeg"
    output_video = "test_output_video.mp4"
    
    print("测试单个视频生成功能")
    print(f"第一张图片: {first_image}")
    print(f"第二张图片: {second_image}")
    print(f"输出视频: {output_video}")
    print()
    
    # 检查图片文件是否存在
    if not os.path.exists(first_image):
        print(f"❌ 第一张图片不存在: {first_image}")
        print("\n💡 解决方案:")
        print("1. 先运行图片生成脚本: python gen_image.py data/003")
        print("2. 或者修改此脚本中的图片路径指向实际存在的图片文件")
        print("3. 或者将您的图片文件复制到指定路径")
        return False
    
    if not os.path.exists(second_image):
        print(f"❌ 第二张图片不存在: {second_image}")
        print("\n💡 解决方案:")
        print("1. 先运行图片生成脚本: python gen_image.py data/003")
        print("2. 或者修改此脚本中的图片路径指向实际存在的图片文件")
        print("3. 或者将您的图片文件复制到指定路径")
        return False
    
    # 调用gen_first_video.py脚本
    try:
        cmd = [sys.executable, "gen_first_video.py", first_image, second_image, output_video]
        print(f"执行命令: {' '.join(cmd)}")
        
        result = subprocess.run(cmd, capture_output=True, text=True)
        
        print("\n--- 脚本输出 ---")
        print(result.stdout)
        
        if result.stderr:
            print("\n--- 错误输出 ---")
            print(result.stderr)
        
        if result.returncode == 0:
            print(f"\n✓ 视频生成成功！输出文件: {output_video}")
            if os.path.exists(output_video):
                file_size = os.path.getsize(output_video)
                print(f"视频文件大小: {file_size} 字节")
            return True
        else:
            print(f"\n✗ 视频生成失败，返回码: {result.returncode}")
            return False
            
    except Exception as e:
        print(f"执行脚本时发生错误: {e}")
        return False

def main():
    """
    主函数
    """
    print("开始测试单个视频生成功能...")
    print("注意: 请确保已正确配置 config/config.py 中的 API 密钥")
    print()
    
    success = test_single_video_generation()
    
    if success:
        print("\n🎉 测试完成！视频生成成功")
    else:
        print("\n❌ 测试失败")
        sys.exit(1)

if __name__ == "__main__":
    main()