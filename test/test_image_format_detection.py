#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
图片格式检测测试脚本
测试gen_first_video_async.py中的upload_image_to_server函数
能否正确识别图片的实际格式而不依赖文件扩展名
"""

import os
import sys
import tempfile
import shutil
from PIL import Image

# 添加项目根目录到路径
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from gen_first_video_async import upload_image_to_server

def create_test_images():
    """
    创建测试图片文件
    返回: (temp_dir, test_files)
    """
    temp_dir = tempfile.mkdtemp()
    test_files = []
    
    # 创建一个简单的测试图片
    img = Image.new('RGB', (100, 100), color='red')
    
    # 创建PNG格式但扩展名为.jpeg的文件
    png_as_jpeg = os.path.join(temp_dir, 'test_png.jpeg')
    img.save(png_as_jpeg, 'PNG')
    test_files.append(('PNG', png_as_jpeg, 'image/png'))
    
    # 创建JPEG格式但扩展名为.png的文件
    jpeg_as_png = os.path.join(temp_dir, 'test_jpeg.png')
    img.save(jpeg_as_png, 'JPEG')
    test_files.append(('JPEG', jpeg_as_png, 'image/jpeg'))
    
    # 创建正常的PNG文件
    normal_png = os.path.join(temp_dir, 'test_normal.png')
    img.save(normal_png, 'PNG')
    test_files.append(('PNG', normal_png, 'image/png'))
    
    # 创建正常的JPEG文件
    normal_jpeg = os.path.join(temp_dir, 'test_normal.jpeg')
    img.save(normal_jpeg, 'JPEG')
    test_files.append(('JPEG', normal_jpeg, 'image/jpeg'))
    
    return temp_dir, test_files

def test_image_format_detection():
    """
    测试图片格式检测功能
    """
    print("开始测试图片格式检测功能...")
    
    temp_dir, test_files = create_test_images()
    
    try:
        all_passed = True
        
        for actual_format, file_path, expected_mime in test_files:
            print(f"\n测试文件: {os.path.basename(file_path)}")
            print(f"实际格式: {actual_format}")
            print(f"期望MIME类型: {expected_mime}")
            
            try:
                result = upload_image_to_server(file_path)
                detected_mime = result.split(',')[0].split(':')[1].split(';')[0]  # 移除;base64后缀
                
                print(f"检测到的MIME类型: {detected_mime}")
                
                if detected_mime == expected_mime:
                    print("✅ 测试通过")
                else:
                    print("❌ 测试失败")
                    all_passed = False
                    
            except Exception as e:
                print(f"❌ 测试出错: {e}")
                all_passed = False
        
        print("\n" + "="*50)
        if all_passed:
            print("🎉 所有测试通过！图片格式检测功能正常工作。")
        else:
            print("⚠️  部分测试失败，请检查代码。")
            
    finally:
        # 清理临时文件
        shutil.rmtree(temp_dir)
        print(f"\n清理临时目录: {temp_dir}")

def test_real_file():
    """
    测试实际的问题文件
    """
    problem_file = '/Users/xunan/Projects/wrmVideo/data/004/chapter_001/chapter_001_image_01_1.jpeg'
    
    if os.path.exists(problem_file):
        print(f"\n测试实际问题文件: {problem_file}")
        try:
            result = upload_image_to_server(problem_file)
            detected_mime = result.split(',')[0].split(':')[1].split(';')[0]  # 移除;base64后缀
            print(f"检测到的MIME类型: {detected_mime}")
            
            if detected_mime == 'image/png':
                print("✅ 正确识别为PNG格式（尽管扩展名是.jpeg）")
            else:
                print(f"⚠️  检测结果: {detected_mime}")
                
        except Exception as e:
            print(f"❌ 测试出错: {e}")
    else:
        print(f"\n⚠️  测试文件不存在: {problem_file}")

if __name__ == "__main__":
    test_image_format_detection()
    test_real_file()