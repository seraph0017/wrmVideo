#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
测试角色图片生成脚本
用于验证批量生成功能的改进
"""

import os
from batch_generate_character_images import (
    parse_directory_info, 
    generate_character_variations,
    count_total_directories
)

def test_directory_parsing():
    """
    测试目录解析功能
    """
    print("=== 测试目录解析功能 ===")
    
    test_paths = [
        "Male/15-22_Youth/Ancient/Chivalrous",
        "Female/23-30_YoungAdult/Fantasy/Mage", 
        "Male/31-45_MiddleAged/SciFi/Villain",
        "Female/14-22_Youth/Modern/Mysterious"
    ]
    
    for path in test_paths:
        result = parse_directory_info(path)
        print(f"路径: {path}")
        print(f"解析结果: {result}")
        print()

def test_character_variations():
    """
    测试角色变化生成
    """
    print("=== 测试角色变化生成 ===")
    
    variations = generate_character_variations()
    print(f"生成了 {len(variations)} 种变化:")
    
    for i, var in enumerate(variations[:3], 1):  # 只显示前3种
        print(f"变化 {i}: {var}")
    print("...")

def test_directory_counting():
    """
    测试目录统计功能
    """
    print("=== 测试目录统计功能 ===")
    
    base_dir = "Character_Images"
    if os.path.exists(base_dir):
        total_dirs = count_total_directories(base_dir)
        print(f"发现 {total_dirs} 个角色类型目录")
        print(f"预计生成 {total_dirs * 12} 张图片")
    else:
        print(f"目录不存在: {base_dir}")

def list_character_types():
    """
    列出所有可用的角色类型
    """
    print("=== 可用角色类型 ===")
    
    base_dir = "Character_Images"
    if not os.path.exists(base_dir):
        print(f"目录不存在: {base_dir}")
        return
    
    character_types = set()
    
    for gender in ["Male", "Female"]:
        gender_path = os.path.join(base_dir, gender)
        if os.path.exists(gender_path):
            for root, dirs, files in os.walk(gender_path):
                if root != gender_path and not dirs:  # 最深层目录
                    parts = root.split(os.sep)
                    if len(parts) >= 4:
                        temperament = parts[-1]
                        character_types.add(temperament)
    
    print("可用气质类型:")
    for char_type in sorted(character_types):
        print(f"  - {char_type}")
    
    print(f"\n总共 {len(character_types)} 种气质类型")

def main():
    """
    主测试函数
    """
    print("角色图片生成功能测试\n")
    
    test_directory_parsing()
    test_character_variations()
    test_directory_counting()
    list_character_types()
    
    print("\n=== 测试完成 ===")

if __name__ == '__main__':
    main()