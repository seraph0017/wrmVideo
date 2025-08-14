#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
初始化脚本 - 清理章节目录中的生成文件

功能：
- 清除指定目录下每个chapter文件夹中除了narration.txt和original_content.txt之外的所有文件
- 保留源文件，删除所有生成的中间文件和输出文件

使用方法：
    python init.py data/001
"""

import os
import sys
import argparse
import shutil
from pathlib import Path


def clean_chapter_directory(chapter_path):
    """
    清理单个章节目录，保留narration.txt和original_content.txt
    
    Args:
        chapter_path (str): 章节目录路径
    
    Returns:
        tuple: (删除的文件数量, 删除的目录数量)
    """
    if not os.path.exists(chapter_path):
        print(f"警告: 章节目录不存在: {chapter_path}")
        return 0, 0
    
    # 需要保留的文件
    keep_files = {'narration.txt', 'original_content.txt'}
    
    deleted_files = 0
    deleted_dirs = 0
    
    try:
        # 遍历章节目录中的所有文件和文件夹
        for item in os.listdir(chapter_path):
            item_path = os.path.join(chapter_path, item)
            
            if os.path.isfile(item_path):
                # 如果是文件且不在保留列表中，则删除
                if item not in keep_files:
                    try:
                        os.remove(item_path)
                        print(f"  删除文件: {item}")
                        deleted_files += 1
                    except Exception as e:
                        print(f"  删除文件失败 {item}: {e}")
                else:
                    print(f"  保留文件: {item}")
            
            elif os.path.isdir(item_path):
                # 如果是目录，则递归删除整个目录
                try:
                    shutil.rmtree(item_path)
                    print(f"  删除目录: {item}/")
                    deleted_dirs += 1
                except Exception as e:
                    print(f"  删除目录失败 {item}/: {e}")
    
    except Exception as e:
        print(f"处理章节目录失败 {chapter_path}: {e}")
        return 0, 0
    
    return deleted_files, deleted_dirs


def clean_data_directory(data_path):
    """
    清理数据目录下的所有章节目录
    
    Args:
        data_path (str): 数据目录路径（如 data/001）
    
    Returns:
        bool: 清理是否成功
    """
    if not os.path.exists(data_path):
        print(f"错误: 数据目录不存在: {data_path}")
        return False
    
    if not os.path.isdir(data_path):
        print(f"错误: 指定路径不是目录: {data_path}")
        return False
    
    print(f"开始清理数据目录: {data_path}")
    print("=" * 50)
    
    total_deleted_files = 0
    total_deleted_dirs = 0
    chapter_count = 0
    
    # 查找所有chapter目录
    chapter_dirs = []
    for item in os.listdir(data_path):
        item_path = os.path.join(data_path, item)
        if os.path.isdir(item_path) and item.startswith('chapter_'):
            chapter_dirs.append((item, item_path))
    
    # 按章节编号排序
    chapter_dirs.sort(key=lambda x: x[0])
    
    if not chapter_dirs:
        print(f"未找到任何chapter目录在: {data_path}")
        return True
    
    # 清理每个章节目录
    for chapter_name, chapter_path in chapter_dirs:
        print(f"\n处理章节: {chapter_name}")
        deleted_files, deleted_dirs = clean_chapter_directory(chapter_path)
        total_deleted_files += deleted_files
        total_deleted_dirs += deleted_dirs
        chapter_count += 1
        
        if deleted_files > 0 or deleted_dirs > 0:
            print(f"  本章节删除: {deleted_files} 个文件, {deleted_dirs} 个目录")
        else:
            print(f"  本章节无需清理")
    
    print("\n" + "=" * 50)
    print(f"清理完成!")
    print(f"处理章节数: {chapter_count}")
    print(f"总计删除: {total_deleted_files} 个文件, {total_deleted_dirs} 个目录")
    
    return True


def main():
    """
    主函数 - 解析命令行参数并执行清理操作
    """
    parser = argparse.ArgumentParser(
        description='清理章节目录中的生成文件，保留narration.txt和original_content.txt',
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
示例用法:
  python init.py data/001          # 清理data/001目录下的所有章节
  python init.py data/002          # 清理data/002目录下的所有章节
        """
    )
    
    parser.add_argument(
        'data_path',
        help='数据目录路径（如: data/001）'
    )
    
    parser.add_argument(
        '--dry-run',
        action='store_true',
        help='仅显示将要删除的文件，不实际执行删除操作'
    )
    
    parser.add_argument(
        '--confirm',
        action='store_true',
        help='跳过确认提示，直接执行清理'
    )
    
    args = parser.parse_args()
    
    # 转换为绝对路径
    data_path = os.path.abspath(args.data_path)
    
    print(f"初始化脚本 - 清理章节目录")
    print(f"目标目录: {data_path}")
    
    # 检查目录是否存在
    if not os.path.exists(data_path):
        print(f"错误: 目录不存在: {data_path}")
        sys.exit(1)
    
    # 预览将要清理的内容
    chapter_dirs = []
    for item in os.listdir(data_path):
        item_path = os.path.join(data_path, item)
        if os.path.isdir(item_path) and item.startswith('chapter_'):
            chapter_dirs.append(item)
    
    if not chapter_dirs:
        print(f"未找到任何chapter目录在: {data_path}")
        sys.exit(0)
    
    chapter_dirs.sort()
    print(f"\n找到 {len(chapter_dirs)} 个章节目录:")
    for chapter in chapter_dirs:
        print(f"  - {chapter}")
    
    print(f"\n将保留以下文件:")
    print(f"  - narration.txt")
    print(f"  - original_content.txt")
    print(f"\n将删除所有其他文件和目录")
    
    # 确认操作
    if not args.confirm and not args.dry_run:
        response = input("\n确认执行清理操作? (y/N): ")
        if response.lower() not in ['y', 'yes', '是']:
            print("操作已取消")
            sys.exit(0)
    
    if args.dry_run:
        print("\n[DRY RUN] 仅预览，不实际删除文件")
        # TODO: 实现dry-run模式的预览功能
        print("dry-run模式暂未实现，请使用正常模式")
        return
    
    # 执行清理
    success = clean_data_directory(data_path)
    
    if success:
        print("\n清理操作完成!")
        sys.exit(0)
    else:
        print("\n清理操作失败!")
        sys.exit(1)


if __name__ == '__main__':
    main()