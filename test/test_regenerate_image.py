#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
测试图片重新生成功能

该脚本用于测试llm_image.py中修改后的regenerate_failed_image函数，
验证是否能正确基于gen_image_async.py的方法重新生成失败的图片。
"""

import os
import sys
import shutil
from pathlib import Path

# 添加项目根目录到Python路径
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))

from llm_image import regenerate_failed_image
from gen_image_async import get_random_character_image

def test_regenerate_specific_image():
    """
    测试重新生成指定的失败图片
    """
    # 指定要重新生成的图片路径
    target_image = "/Users/xunan/Projects/wrmVideo/data/004/chapter_001/chapter_001_character_03_楚秀.jpeg"
    
    print("=" * 80)
    print("测试图片重新生成功能")
    print("=" * 80)
    print(f"目标图片: {target_image}")
    
    # 检查图片是否存在
    if not os.path.exists(target_image):
        print(f"错误: 目标图片不存在: {target_image}")
        return False
    
    # 备份原图片
    backup_path = target_image + ".backup"
    try:
        shutil.copy2(target_image, backup_path)
        print(f"✓ 已备份原图片到: {backup_path}")
    except Exception as e:
        print(f"警告: 备份原图片失败: {e}")
    
    # 测试重新生成功能
    print("\n开始测试重新生成功能...")
    print("-" * 50)
    
    try:
        # 调用重新生成函数
        success = regenerate_failed_image(target_image)
        
        if success:
            print("\n✓ 重新生成任务提交成功!")
            print("请使用以下命令检查任务状态:")
            print("python check_async_tasks.py")
            print("\n或者监控任务进度:")
            print("python check_async_tasks.py --monitor")
            return True
        else:
            print("\n✗ 重新生成任务提交失败")
            return False
            
    except Exception as e:
        print(f"\n✗ 测试过程中发生错误: {e}")
        return False

def test_random_character_image():
    """
    测试随机角色图片获取功能
    """
    print("\n=== 测试随机角色图片获取 ===")
    
    try:
        character_image = get_random_character_image()
        if character_image:
            print(f"✓ 成功获取随机角色图片: {character_image}")
            
            # 检查文件是否存在
            if os.path.exists(character_image):
                print(f"✓ 角色图片文件存在")
                return True
            else:
                print(f"✗ 角色图片文件不存在: {character_image}")
                return False
        else:
            print("✗ 无法获取随机角色图片")
            return False
            
    except Exception as e:
        print(f"✗ 获取随机角色图片时发生错误: {e}")
        return False

def main():
    """
    主测试函数
    """
    print("开始测试图片重新生成功能...\n")
    
    # 测试1: 随机角色图片获取
    test1_result = test_random_character_image()
    
    # 测试2: 重新生成指定图片
    test2_result = test_regenerate_specific_image()
    
    # 输出测试结果
    print("\n" + "=" * 80)
    print("测试结果汇总")
    print("=" * 80)
    print(f"随机角色图片获取: {'✓ 通过' if test1_result else '✗ 失败'}")
    print(f"图片重新生成功能: {'✓ 通过' if test2_result else '✗ 失败'}")
    
    if test1_result and test2_result:
        print("\n🎉 所有测试通过!")
        print("\n后续步骤:")
        print("1. 等待异步任务完成")
        print("2. 使用 check_async_tasks.py 检查生成结果")
        print("3. 使用 llm_image.py 重新检查生成的图片")
    else:
        print("\n❌ 部分测试失败，请检查配置和依赖")
    
    return test1_result and test2_result

if __name__ == "__main__":
    main()