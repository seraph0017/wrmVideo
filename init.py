#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
初始化脚本 - 清理章节目录

功能：
- 删除指定目录下所有子目录中除了 .txt 文件外的所有文件
- 保留目录结构和脚本文件
- 用于重新生成视频前的清理工作

使用方法：
    python init.py <目录路径>
    
示例：
    python init.py data/001
"""

import os
import sys
import shutil
from pathlib import Path

def clean_directory(directory_path):
    """
    清理目录下除txt文件外的所有文件
    
    Args:
        directory_path: 要清理的目录路径
    
    Returns:
        tuple: (删除的文件数量, 删除的目录数量)
    """
    deleted_files = 0
    deleted_dirs = 0
    
    if not os.path.exists(directory_path):
        print(f"错误: 目录 {directory_path} 不存在")
        return 0, 0
    
    print(f"开始清理目录: {directory_path}")
    
    # 遍历目录
    for root, dirs, files in os.walk(directory_path, topdown=False):
        # 删除文件（保留.txt文件）
        for file in files:
            file_path = os.path.join(root, file)
            file_ext = os.path.splitext(file)[1].lower()
            
            # 保留.txt文件，删除其他所有文件
            if file_ext != '.txt':
                try:
                    os.remove(file_path)
                    deleted_files += 1
                    print(f"删除文件: {file_path}")
                except Exception as e:
                    print(f"删除文件失败 {file_path}: {e}")
        
        # 删除空目录（但保留章节目录本身）
        for dir_name in dirs:
            dir_path = os.path.join(root, dir_name)
            try:
                # 只删除空目录
                if os.path.exists(dir_path) and not os.listdir(dir_path):
                    os.rmdir(dir_path)
                    deleted_dirs += 1
                    print(f"删除空目录: {dir_path}")
            except Exception as e:
                print(f"删除目录失败 {dir_path}: {e}")
    
    return deleted_files, deleted_dirs

def clean_chapter_directories(base_dir):
    """
    清理章节目录
    
    Args:
        base_dir: 基础目录路径
    
    Returns:
        bool: 是否成功完成清理
    """
    try:
        base_path = Path(base_dir)
        
        if not base_path.exists():
            print(f"错误: 目录 {base_dir} 不存在")
            return False
        
        if not base_path.is_dir():
            print(f"错误: {base_dir} 不是一个目录")
            return False
        
        print(f"\n=== 开始清理 {base_dir} ===")
        
        total_files = 0
        total_dirs = 0
        chapter_count = 0
        
        # 查找所有章节目录
        chapter_dirs = []
        for item in base_path.iterdir():
            if item.is_dir() and item.name.startswith('chapter'):
                chapter_dirs.append(item)
        
        if not chapter_dirs:
            print(f"警告: 在 {base_dir} 中没有找到章节目录")
            return True
        
        # 按章节编号排序
        chapter_dirs.sort(key=lambda x: int(x.name.replace('chapter', '')) if x.name.replace('chapter', '').isdigit() else 999)
        
        print(f"找到 {len(chapter_dirs)} 个章节目录")
        
        # 清理每个章节目录
        for chapter_dir in chapter_dirs:
            print(f"\n--- 清理章节: {chapter_dir.name} ---")
            
            files_deleted, dirs_deleted = clean_directory(str(chapter_dir))
            total_files += files_deleted
            total_dirs += dirs_deleted
            chapter_count += 1
            
            print(f"章节 {chapter_dir.name} 清理完成: 删除 {files_deleted} 个文件, {dirs_deleted} 个目录")
        
        # 清理基础目录下的非txt文件
        print(f"\n--- 清理基础目录: {base_dir} ---")
        base_files_deleted = 0
        for item in base_path.iterdir():
            if item.is_file() and item.suffix.lower() != '.txt':
                try:
                    item.unlink()
                    base_files_deleted += 1
                    total_files += 1
                    print(f"删除文件: {item}")
                except Exception as e:
                    print(f"删除文件失败 {item}: {e}")
        
        print(f"\n=== 清理完成 ===")
        print(f"处理了 {chapter_count} 个章节目录")
        print(f"总共删除 {total_files} 个文件, {total_dirs} 个目录")
        print(f"保留了所有 .txt 脚本文件")
        
        return True
        
    except Exception as e:
        print(f"清理过程中发生错误: {e}")
        return False

def main():
    """
    主函数
    """
    if len(sys.argv) < 2:
        print("使用方法: python init.py <目录路径>")
        print("示例: python init.py data/001")
        print("")
        print("功能: 删除指定目录下所有章节中除 .txt 文件外的所有文件")
        print("注意: 此操作不可逆，请确保已备份重要文件")
        sys.exit(1)
    
    target_dir = sys.argv[1]
    
    # 确认操作
    print(f"即将清理目录: {target_dir}")
    print("此操作将删除除 .txt 文件外的所有文件，包括:")
    print("- 所有 .mp3 音频文件")
    print("- 所有 .jpg/.png 图片文件")
    print("- 所有 .mp4 视频文件")
    print("- 其他所有非 .txt 文件")
    print("")
    
    confirm = input("确认继续吗？(y/N): ").strip().lower()
    if confirm not in ['y', 'yes', '是', '确认']:
        print("操作已取消")
        sys.exit(0)
    
    # 执行清理
    success = clean_chapter_directories(target_dir)
    
    if success:
        print("\n✅ 清理操作成功完成")
        sys.exit(0)
    else:
        print("\n❌ 清理操作失败")
        sys.exit(1)

if __name__ == "__main__":
    main()