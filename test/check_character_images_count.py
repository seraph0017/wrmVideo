#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
角色图片目录文件数量检查脚本

检查Character_Images目录下每个最下级子目录的文件数量，
找出少于8个文件的目录并列出缺少的文件编号。

作者: AI Assistant
日期: 2024
"""

import os
import sys
from pathlib import Path
from collections import defaultdict

def get_leaf_directories(root_path):
    """
    获取所有最下级子目录（叶子目录）
    
    Args:
        root_path (str): 根目录路径
        
    Returns:
        list: 所有叶子目录的路径列表
    """
    leaf_dirs = []
    
    for root, dirs, files in os.walk(root_path):
        # 如果当前目录没有子目录，则为叶子目录
        if not dirs:
            leaf_dirs.append(root)
    
    return leaf_dirs

def extract_file_numbers(files):
    """
    从文件名中提取编号
    
    Args:
        files (list): 文件名列表
        
    Returns:
        set: 提取到的编号集合
    """
    numbers = set()
    
    for file in files:
        # 跳过隐藏文件和非图片文件
        if file.startswith('.') or not file.lower().endswith(('.jpg', '.jpeg', '.png')):
            continue
            
        # 尝试从文件名末尾提取数字编号
        # 例如: YoungAdult_Ancient_Western_Villain_07.jpeg -> 07
        parts = file.split('_')
        if parts:
            last_part = parts[-1]
            # 移除文件扩展名
            name_without_ext = os.path.splitext(last_part)[0]
            
            # 检查是否为数字
            if name_without_ext.isdigit():
                numbers.add(int(name_without_ext))
            else:
                # 尝试提取末尾的数字
                import re
                match = re.search(r'(\d+)$', name_without_ext)
                if match:
                    numbers.add(int(match.group(1)))
    
    return numbers

def check_directory_completeness(directory_path, expected_count=8):
    """
    检查目录中文件的完整性
    
    Args:
        directory_path (str): 目录路径
        expected_count (int): 期望的文件数量
        
    Returns:
        dict: 包含检查结果的字典
    """
    try:
        files = os.listdir(directory_path)
        image_files = [f for f in files if f.lower().endswith(('.jpg', '.jpeg', '.png')) and not f.startswith('.')]
        
        file_numbers = extract_file_numbers(image_files)
        expected_numbers = set(range(1, expected_count + 1))
        missing_numbers = expected_numbers - file_numbers
        
        return {
            'path': directory_path,
            'total_files': len(image_files),
            'file_numbers': sorted(file_numbers),
            'missing_numbers': sorted(missing_numbers),
            'is_complete': len(missing_numbers) == 0 and len(file_numbers) >= expected_count
        }
    except Exception as e:
        return {
            'path': directory_path,
            'error': str(e),
            'is_complete': False
        }

def format_path_for_display(path, base_path):
    """
    格式化路径用于显示
    
    Args:
        path (str): 完整路径
        base_path (str): 基础路径
        
    Returns:
        str: 相对路径
    """
    try:
        return os.path.relpath(path, base_path)
    except:
        return path

def main():
    """
    主函数
    """
    # Character_Images目录路径
    character_images_path = "/Users/xunan/Projects/wrmVideo/Character_Images"
    
    # 检查目录是否存在
    if not os.path.exists(character_images_path):
        print(f"❌ 错误: 目录不存在 {character_images_path}")
        sys.exit(1)
    
    print(f"🔍 检查角色图片目录: {character_images_path}")
    print("=" * 80)
    
    # 获取所有叶子目录
    leaf_directories = get_leaf_directories(character_images_path)
    
    if not leaf_directories:
        print("❌ 未找到任何最下级子目录")
        sys.exit(1)
    
    print(f"📁 找到 {len(leaf_directories)} 个最下级子目录")
    print()
    
    # 检查每个目录
    incomplete_dirs = []
    complete_dirs = []
    error_dirs = []
    
    for directory in sorted(leaf_directories):
        result = check_directory_completeness(directory)
        
        if 'error' in result:
            error_dirs.append(result)
            continue
        
        if result['is_complete']:
            complete_dirs.append(result)
        else:
            incomplete_dirs.append(result)
    
    # 显示结果
    print("📊 检查结果统计:")
    print(f"  ✅ 完整目录: {len(complete_dirs)}")
    print(f"  ❌ 不完整目录: {len(incomplete_dirs)}")
    print(f"  ⚠️  错误目录: {len(error_dirs)}")
    print()
    
    # 显示不完整的目录详情
    if incomplete_dirs:
        print("❌ 不完整的目录 (少于8个文件):")
        print("=" * 80)
        
        for result in incomplete_dirs:
            rel_path = format_path_for_display(result['path'], character_images_path)
            print(f"📂 {rel_path}")
            print(f"   文件数量: {result['total_files']}/8")
            print(f"   现有编号: {result['file_numbers']}")
            
            if result['missing_numbers']:
                missing_str = ', '.join([f"{num:02d}" for num in result['missing_numbers']])
                print(f"   缺少编号: {missing_str}")
            
            print()
    
    # 显示错误目录
    if error_dirs:
        print("⚠️  检查时出错的目录:")
        print("=" * 80)
        
        for result in error_dirs:
            rel_path = format_path_for_display(result['path'], character_images_path)
            print(f"📂 {rel_path}")
            print(f"   错误: {result['error']}")
            print()
    
    # 显示完整目录（可选）
    if complete_dirs and len(complete_dirs) <= 10:  # 只在数量不多时显示
        print("✅ 完整的目录:")
        print("=" * 80)
        
        for result in complete_dirs:
            rel_path = format_path_for_display(result['path'], character_images_path)
            print(f"📂 {rel_path} ({result['total_files']} 文件)")
        print()
    
    # 总结
    print("📋 检查完成!")
    if incomplete_dirs:
        print(f"发现 {len(incomplete_dirs)} 个目录需要补充文件")
    else:
        print("所有目录都已完整!")

if __name__ == "__main__":
    main()