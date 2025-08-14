#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
生成缺失图片详细报告脚本

生成Character_Images目录下缺失图片的详细报告，
包括CSV格式和文本格式的报告文件。

作者: AI Assistant
日期: 2024
"""

import os
import csv
import sys
from datetime import datetime
from pathlib import Path

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
        if file.startswith('.') or not file.lower().endswith(('.jpg', '.jpeg', '.png')):
            continue
            
        parts = file.split('_')
        if parts:
            last_part = parts[-1]
            name_without_ext = os.path.splitext(last_part)[0]
            
            if name_without_ext.isdigit():
                numbers.add(int(name_without_ext))
            else:
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
            'is_complete': len(missing_numbers) == 0 and len(file_numbers) >= expected_count,
            'image_files': image_files
        }
    except Exception as e:
        return {
            'path': directory_path,
            'error': str(e),
            'is_complete': False
        }

def generate_csv_report(incomplete_dirs, output_file):
    """
    生成CSV格式的报告
    
    Args:
        incomplete_dirs (list): 不完整目录列表
        output_file (str): 输出文件路径
    """
    with open(output_file, 'w', newline='', encoding='utf-8') as csvfile:
        fieldnames = ['目录路径', '现有文件数', '缺失编号', '现有编号', '缺失文件数']
        writer = csv.DictWriter(csvfile, fieldnames=fieldnames)
        
        writer.writeheader()
        
        for result in incomplete_dirs:
            rel_path = os.path.relpath(result['path'], "/Users/xunan/Projects/wrmVideo/Character_Images")
            missing_str = ', '.join([f"{num:02d}" for num in result['missing_numbers']])
            existing_str = ', '.join([f"{num:02d}" for num in result['file_numbers']])
            
            writer.writerow({
                '目录路径': rel_path,
                '现有文件数': f"{result['total_files']}/8",
                '缺失编号': missing_str,
                '现有编号': existing_str,
                '缺失文件数': len(result['missing_numbers'])
            })

def generate_text_report(incomplete_dirs, complete_dirs, error_dirs, output_file):
    """
    生成文本格式的详细报告
    
    Args:
        incomplete_dirs (list): 不完整目录列表
        complete_dirs (list): 完整目录列表
        error_dirs (list): 错误目录列表
        output_file (str): 输出文件路径
    """
    with open(output_file, 'w', encoding='utf-8') as f:
        f.write("Character_Images 目录文件完整性检查报告\n")
        f.write("=" * 60 + "\n")
        f.write(f"生成时间: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\n")
        f.write(f"检查目录: /Users/xunan/Projects/wrmVideo/Character_Images\n\n")
        
        # 统计信息
        f.write("📊 检查结果统计:\n")
        f.write(f"  ✅ 完整目录: {len(complete_dirs)}\n")
        f.write(f"  ❌ 不完整目录: {len(incomplete_dirs)}\n")
        f.write(f"  ⚠️  错误目录: {len(error_dirs)}\n")
        f.write(f"  📁 总目录数: {len(complete_dirs) + len(incomplete_dirs) + len(error_dirs)}\n\n")
        
        # 不完整目录详情
        if incomplete_dirs:
            f.write("❌ 不完整的目录详情:\n")
            f.write("=" * 60 + "\n")
            
            for i, result in enumerate(incomplete_dirs, 1):
                rel_path = os.path.relpath(result['path'], "/Users/xunan/Projects/wrmVideo/Character_Images")
                f.write(f"{i:2d}. {rel_path}\n")
                f.write(f"    文件数量: {result['total_files']}/8\n")
                f.write(f"    现有编号: {result['file_numbers']}\n")
                
                if result['missing_numbers']:
                    missing_str = ', '.join([f"{num:02d}" for num in result['missing_numbers']])
                    f.write(f"    缺少编号: {missing_str}\n")
                
                f.write("\n")
        
        # 错误目录
        if error_dirs:
            f.write("⚠️  检查时出错的目录:\n")
            f.write("=" * 60 + "\n")
            
            for result in error_dirs:
                rel_path = os.path.relpath(result['path'], "/Users/xunan/Projects/wrmVideo/Character_Images")
                f.write(f"📂 {rel_path}\n")
                f.write(f"   错误: {result['error']}\n\n")
        
        # 按缺失数量分组统计
        if incomplete_dirs:
            f.write("📈 按缺失数量分组统计:\n")
            f.write("=" * 60 + "\n")
            
            missing_count_groups = {}
            for result in incomplete_dirs:
                missing_count = len(result['missing_numbers'])
                if missing_count not in missing_count_groups:
                    missing_count_groups[missing_count] = []
                missing_count_groups[missing_count].append(result)
            
            for missing_count in sorted(missing_count_groups.keys()):
                dirs = missing_count_groups[missing_count]
                f.write(f"缺失 {missing_count} 个文件的目录 ({len(dirs)} 个):\n")
                for result in dirs:
                    rel_path = os.path.relpath(result['path'], "/Users/xunan/Projects/wrmVideo/Character_Images")
                    f.write(f"  - {rel_path}\n")
                f.write("\n")

def main():
    """
    主函数
    """
    character_images_path = "/Users/xunan/Projects/wrmVideo/Character_Images"
    
    if not os.path.exists(character_images_path):
        print(f"❌ 错误: 目录不存在 {character_images_path}")
        sys.exit(1)
    
    print(f"🔍 检查角色图片目录: {character_images_path}")
    print("正在扫描目录...")
    
    # 获取所有叶子目录
    leaf_directories = get_leaf_directories(character_images_path)
    
    if not leaf_directories:
        print("❌ 未找到任何最下级子目录")
        sys.exit(1)
    
    print(f"📁 找到 {len(leaf_directories)} 个最下级子目录")
    print("正在检查文件完整性...")
    
    # 检查每个目录
    incomplete_dirs = []
    complete_dirs = []
    error_dirs = []
    
    for i, directory in enumerate(sorted(leaf_directories), 1):
        if i % 100 == 0:
            print(f"已检查 {i}/{len(leaf_directories)} 个目录...")
        
        result = check_directory_completeness(directory)
        
        if 'error' in result:
            error_dirs.append(result)
            continue
        
        if result['is_complete']:
            complete_dirs.append(result)
        else:
            incomplete_dirs.append(result)
    
    print("\n📊 检查完成!")
    print(f"  ✅ 完整目录: {len(complete_dirs)}")
    print(f"  ❌ 不完整目录: {len(incomplete_dirs)}")
    print(f"  ⚠️  错误目录: {len(error_dirs)}")
    
    # 生成报告文件
    if incomplete_dirs or error_dirs:
        timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
        
        # CSV报告
        csv_file = f"test/missing_images_report_{timestamp}.csv"
        generate_csv_report(incomplete_dirs, csv_file)
        print(f"\n📄 CSV报告已生成: {csv_file}")
        
        # 文本报告
        txt_file = f"test/missing_images_report_{timestamp}.txt"
        generate_text_report(incomplete_dirs, complete_dirs, error_dirs, txt_file)
        print(f"📄 详细报告已生成: {txt_file}")
        
        print(f"\n🎯 总结: 发现 {len(incomplete_dirs)} 个目录需要补充文件")
        
        # 显示前5个不完整目录
        if incomplete_dirs:
            print("\n前5个需要补充的目录:")
            for i, result in enumerate(incomplete_dirs[:5], 1):
                rel_path = os.path.relpath(result['path'], character_images_path)
                missing_str = ', '.join([f"{num:02d}" for num in result['missing_numbers']])
                print(f"  {i}. {rel_path} (缺少: {missing_str})")
            
            if len(incomplete_dirs) > 5:
                print(f"  ... 还有 {len(incomplete_dirs) - 5} 个目录 (详见报告文件)")
    else:
        print("\n🎉 所有目录都已完整!")

if __name__ == "__main__":
    main()