#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
测试异步图片生成功能
"""

import os
import sys
import time

# 添加项目根目录到Python路径
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from gen_image import generate_image_with_character_async
import subprocess

def test_async_image_generation():
    """
    测试异步图片生成
    """
    print("开始测试异步图片生成...")
    
    # 测试参数
    test_prompt = "一个古代武侠少年，身穿白色长袍，站在山峰之上，背景是云海和远山"
    test_output_path = "test/async_test_image.jpeg"
    
    # 确保测试目录存在
    os.makedirs(os.path.dirname(test_output_path), exist_ok=True)
    
    # 提交异步任务
    print(f"提交任务: {test_prompt}")
    success = generate_image_with_character_async(
        prompt=test_prompt,
        output_path=test_output_path,
        character_images=None,
        style="manga"
    )
    
    if success:
        print("✓ 任务提交成功")
        print("\n等待5秒后检查任务状态...")
        time.sleep(5)
        
        # 检查任务状态
        print("\n检查所有任务状态:")
        subprocess.run(["python", "check_async_tasks.py", "--check-once"])
        
    else:
        print("✗ 任务提交失败")
        return False
    
    return True

if __name__ == '__main__':
    test_async_image_generation()