#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
测试llm_image.py中将异步任务保存到各个chapter的async_tasks目录的功能
"""

import os
import sys
import time
from pathlib import Path

# 添加项目根目录到Python路径
project_root = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, project_root)

from llm_image import regenerate_failed_image, generate_image_with_character_to_chapter_async
from gen_image_async import get_random_character_image

def test_chapter_async_tasks():
    """
    测试异步任务保存到chapter目录的功能
    """
    print("=== 测试异步任务保存到chapter目录功能 ===")
    
    # 测试图片路径（模拟一个chapter下的图片）
    test_image_path = "/Users/xunan/Projects/wrmVideo/data/004/chapter_001/chapter_001_character_03_楚秀.jpeg"
    
    print(f"测试图片路径: {test_image_path}")
    
    # 检查图片是否存在
    if not os.path.exists(test_image_path):
        print(f"警告: 测试图片不存在，将创建模拟路径")
        # 创建模拟的目录结构
        os.makedirs(os.path.dirname(test_image_path), exist_ok=True)
        # 创建一个空的测试文件
        with open(test_image_path, 'w') as f:
            f.write("test image")
    
    # 测试重新生成功能
    print("\n--- 测试重新生成失败图片功能 ---")
    success = regenerate_failed_image(test_image_path)
    
    if success:
        print("✓ 重新生成任务提交成功")
        
        # 检查chapter的async_tasks目录是否创建
        chapter_dir = "/Users/xunan/Projects/wrmVideo/data/004/chapter_001"
        async_tasks_dir = os.path.join(chapter_dir, "async_tasks")
        
        print(f"\n检查async_tasks目录: {async_tasks_dir}")
        if os.path.exists(async_tasks_dir):
            print("✓ async_tasks目录已创建")
            
            # 列出目录中的任务文件
            task_files = [f for f in os.listdir(async_tasks_dir) if f.endswith('.txt')]
            print(f"找到 {len(task_files)} 个任务文件:")
            for task_file in task_files[-3:]:  # 只显示最新的3个
                print(f"  - {task_file}")
                
                # 查看最新任务文件的内容
                if task_file == task_files[-1]:
                    task_file_path = os.path.join(async_tasks_dir, task_file)
                    try:
                        with open(task_file_path, 'r', encoding='utf-8') as f:
                            import json
                            task_info = json.load(f)
                            print(f"\n最新任务信息:")
                            print(f"  Task ID: {task_info.get('task_id', 'N/A')}")
                            print(f"  输出路径: {task_info.get('output_path', 'N/A')}")
                            print(f"  文件名: {task_info.get('filename', 'N/A')}")
                            print(f"  状态: {task_info.get('status', 'N/A')}")
                            print(f"  提交时间: {time.ctime(task_info.get('submit_time', 0))}")
                    except Exception as e:
                        print(f"读取任务文件失败: {e}")
        else:
            print("✗ async_tasks目录未创建")
    else:
        print("✗ 重新生成任务提交失败")

def test_direct_async_generation():
    """
    直接测试异步生成函数
    """
    print("\n=== 直接测试异步生成函数 ===")
    
    # 获取随机角色图片
    character_image = get_random_character_image()
    if not character_image:
        print("✗ 无法获取角色图片")
        return
    
    print(f"使用角色图片: {character_image}")
    
    # 测试路径
    test_output_path = "/Users/xunan/Projects/wrmVideo/data/005/chapter_002/test_async_image.jpeg"
    
    # 确保目录存在
    os.makedirs(os.path.dirname(test_output_path), exist_ok=True)
    
    # 测试提示词
    test_prompt = "一个美丽的古代女性，穿着华丽的宫廷服装，圆领设计，优雅端庄"
    
    print(f"测试输出路径: {test_output_path}")
    print(f"测试提示词: {test_prompt}")
    
    # 调用异步生成函数
    success = generate_image_with_character_to_chapter_async(
        prompt=test_prompt,
        output_path=test_output_path,
        character_images=[character_image],
        style='manga'
    )
    
    if success:
        print("✓ 异步任务提交成功")
        
        # 检查对应的async_tasks目录
        chapter_dir = "/Users/xunan/Projects/wrmVideo/data/005/chapter_002"
        async_tasks_dir = os.path.join(chapter_dir, "async_tasks")
        
        print(f"检查async_tasks目录: {async_tasks_dir}")
        if os.path.exists(async_tasks_dir):
            print("✓ async_tasks目录已创建")
            
            # 列出任务文件
            task_files = [f for f in os.listdir(async_tasks_dir) if f.endswith('.txt')]
            print(f"找到 {len(task_files)} 个任务文件")
            if task_files:
                print(f"最新任务文件: {task_files[-1]}")
        else:
            print("✗ async_tasks目录未创建")
    else:
        print("✗ 异步任务提交失败")

def main():
    """
    主测试函数
    """
    print("开始测试异步任务保存到chapter目录功能...\n")
    
    try:
        # 测试1: 重新生成失败图片
        test_chapter_async_tasks()
        
        # 测试2: 直接测试异步生成
        test_direct_async_generation()
        
        print("\n=== 测试完成 ===")
        print("请检查对应chapter目录下是否创建了async_tasks子目录")
        print("可以使用以下命令查看任务文件:")
        print("find data -name 'async_tasks' -type d")
        print("find data -path '*/async_tasks/*.txt' -type f")
        
    except Exception as e:
        print(f"测试过程中发生错误: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    main()