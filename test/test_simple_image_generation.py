#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
简单的图片生成测试
"""

import os
import sys

# 添加项目根目录到Python路径
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from generate import generate_image

def test_simple_image_generation():
    """
    测试单张图片生成
    """
    print("=== 简单图片生成测试 ===")
    
    # 创建测试目录
    test_dir = "test_simple_image"
    os.makedirs(test_dir, exist_ok=True)
    
    # 测试图片生成
    prompt = "一个简单的测试图片：蓝天白云下的绿色草地"
    output_path = os.path.join(test_dir, "test_simple.jpg")
    
    print(f"测试prompt: {prompt}")
    print(f"输出路径: {output_path}")
    
    try:
        result = generate_image(prompt, output_path)
        
        if result and os.path.exists(output_path):
            file_size = os.path.getsize(output_path)
            print(f"✓ 图片生成成功: {output_path} ({file_size} bytes)")
            return True
        else:
            print(f"✗ 图片生成失败")
            return False
            
    except Exception as e:
        print(f"✗ 图片生成过程中发生错误: {e}")
        return False

if __name__ == "__main__":
    success = test_simple_image_generation()
    
    if success:
        print("\n✓ 简单图片生成测试通过")
    else:
        print("\n✗ 简单图片生成测试失败")
        print("请检查：")
        print("1. 网络连接是否正常")
        print("2. API密钥是否正确")
        print("3. 配置文件是否正确")