#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
测试中式/西式角色分类功能
"""

import os
from batch_generate_character_images import (
    parse_directory_info, 
    count_total_directories
)

def test_new_directory_parsing():
    """
    测试新的目录解析功能（包含文化分类）
    """
    print("=== 测试新目录解析功能 ===")
    
    test_paths = [
        "Male/15-22_Youth/Ancient/Chinese/Chivalrous",
        "Female/23-30_YoungAdult/Fantasy/Western/Mage", 
        "Male/31-45_MiddleAged/SciFi/Chinese/Villain",
        "Female/14-22_Youth/Modern/Western/Mysterious",
        "Male/25-40_FantasyAdult/Ancient/Chinese/Monk",
        "Female/31-45_MiddleAged/Fantasy/Western/Royal"
    ]
    
    for path in test_paths:
        result = parse_directory_info(path)
        print(f"路径: {path}")
        print(f"解析结果: {result}")
        print()

def test_directory_structure():
    """
    测试新目录结构
    """
    print("=== 测试新目录结构 ===")
    
    new_base_dir = "Character_Images_New"
    if os.path.exists(new_base_dir):
        total_dirs = count_total_directories(new_base_dir)
        print(f"新目录结构发现 {total_dirs} 个角色类型目录")
        print(f"预计生成 {total_dirs * 12} 张图片")
        
        # 统计中式和西式目录数量
        chinese_count = 0
        western_count = 0
        
        for gender in ["Male", "Female"]:
            gender_path = os.path.join(new_base_dir, gender)
            if os.path.exists(gender_path):
                for root, dirs, files in os.walk(gender_path):
                    if "Chinese" in root and not dirs:
                        chinese_count += 1
                    elif "Western" in root and not dirs:
                        western_count += 1
        
        print(f"中式角色类型: {chinese_count} 个")
        print(f"西式角色类型: {western_count} 个")
    else:
        print(f"新目录不存在: {new_base_dir}")

def list_culture_combinations():
    """
    列出所有文化-风格组合
    """
    print("=== 文化-风格组合 ===")
    
    new_base_dir = "Character_Images_New"
    if not os.path.exists(new_base_dir):
        print(f"目录不存在: {new_base_dir}")
        return
    
    combinations = set()
    
    for gender in ["Male", "Female"]:
        gender_path = os.path.join(new_base_dir, gender)
        if os.path.exists(gender_path):
            for root, dirs, files in os.walk(gender_path):
                parts = root.split(os.sep)
                if len(parts) >= 6:  # 包含文化层级
                    style = parts[-3]  # Ancient/Fantasy/Modern/SciFi
                    culture = parts[-2]  # Chinese/Western
                    if style in ["Ancient", "Fantasy", "Modern", "SciFi"] and culture in ["Chinese", "Western"]:
                        combinations.add(f"{style}-{culture}")
    
    print("可用的文化-风格组合:")
    for combo in sorted(combinations):
        print(f"  - {combo}")
    
    print(f"\n总共 {len(combinations)} 种组合")

def compare_old_new_structure():
    """
    比较新旧目录结构
    """
    print("=== 新旧目录结构对比 ===")
    
    old_base_dir = "Character_Images"
    new_base_dir = "Character_Images_New"
    
    old_count = 0
    new_count = 0
    
    if os.path.exists(old_base_dir):
        old_count = count_total_directories(old_base_dir)
        print(f"旧结构目录数: {old_count}")
    
    if os.path.exists(new_base_dir):
        new_count = count_total_directories(new_base_dir)
        print(f"新结构目录数: {new_count}")
    
    if old_count > 0 and new_count > 0:
        ratio = new_count / old_count
        print(f"扩展倍数: {ratio:.1f}x")
        print(f"新增目录数: {new_count - old_count}")

def main():
    """
    主测试函数
    """
    print("中式/西式角色分类功能测试\n")
    
    test_new_directory_parsing()
    test_directory_structure()
    list_culture_combinations()
    compare_old_new_structure()
    
    print("\n=== 测试完成 ===")

if __name__ == '__main__':
    main()