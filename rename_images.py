#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
图片重命名脚本
将原本的3个特写图片格式重命名为单独的narration图片格式
从 chapter_xxx_image_YY_Z.jpeg 重命名为 chapter_xxx_image_ZZ.jpeg
"""

import os
import sys
import glob
import argparse
from pathlib import Path

def rename_images_in_chapter(chapter_path):
    """
    重命名章节中的图片文件
    
    Args:
        chapter_path: 章节目录路径
    
    Returns:
        bool: 是否成功
    """
    chapter_name = os.path.basename(chapter_path)
    print(f"\n开始处理章节: {chapter_name}")
    
    # 查找所有图片文件
    image_pattern = f"{chapter_name}_image_*_*.jpeg"
    image_files = glob.glob(os.path.join(chapter_path, image_pattern))
    
    if not image_files:
        print(f"没有找到需要重命名的图片文件")
        return False
    
    print(f"找到 {len(image_files)} 个图片文件")
    
    # 按文件名排序
    image_files.sort()
    
    # 重命名计数器
    new_index = 1
    
    # 遍历所有图片文件进行重命名
    for old_path in image_files:
        old_filename = os.path.basename(old_path)
        
        # 生成新的文件名
        new_filename = f"{chapter_name}_image_{new_index:02d}.jpeg"
        new_path = os.path.join(chapter_path, new_filename)
        
        # 检查新文件是否已存在
        if os.path.exists(new_path):
            print(f"⚠️  目标文件已存在，跳过: {new_filename}")
            continue
        
        try:
            # 重命名文件
            os.rename(old_path, new_path)
            print(f"✓ {old_filename} -> {new_filename}")
            new_index += 1
        except Exception as e:
            print(f"❌ 重命名失败: {old_filename} -> {new_filename}, 错误: {e}")
            return False
    
    print(f"\n重命名完成，总共处理了 {new_index - 1} 个图片文件")
    return True

def main():
    parser = argparse.ArgumentParser(description='重命名图片文件')
    parser.add_argument('data_path', help='数据目录路径（如 data/006 或 data/006/chapter_002）')
    
    args = parser.parse_args()
    
    data_path = os.path.abspath(args.data_path)
    if not os.path.exists(data_path):
        print(f"目录不存在: {data_path}")
        return 1
    
    if not os.path.isdir(data_path):
        print(f"路径不是目录: {data_path}")
        return 1
    
    # 检查是否是章节目录（包含chapter_前缀）
    if os.path.basename(data_path).startswith('chapter_'):
        # 单个章节目录
        print(f"处理单个章节目录: {os.path.basename(data_path)}")
        success = rename_images_in_chapter(data_path)
        
        if success:
            print(f"\n✓ 图片重命名完成")
            return 0
        else:
            print(f"\n❌ 图片重命名失败")
            return 1
    else:
        # 数据目录，遍历所有章节
        chapter_dirs = [d for d in os.listdir(data_path) 
                       if os.path.isdir(os.path.join(data_path, d)) and d.startswith('chapter_')]
        
        if not chapter_dirs:
            print(f"在目录 {data_path} 中没有找到章节目录")
            return 1
        
        chapter_dirs.sort()
        print(f"找到 {len(chapter_dirs)} 个章节目录: {chapter_dirs}")
        
        total_success = 0
        total_chapters = len(chapter_dirs)
        
        for chapter_dir in chapter_dirs:
            chapter_path = os.path.join(data_path, chapter_dir)
            print(f"\n{'='*50}")
            print(f"处理章节: {chapter_dir}")
            print(f"{'='*50}")
            
            success = rename_images_in_chapter(chapter_path)
            if success:
                total_success += 1
                print(f"✓ {chapter_dir} 处理成功")
            else:
                print(f"❌ {chapter_dir} 处理失败")
        
        print(f"\n{'='*50}")
        print(f"处理完成: {total_success}/{total_chapters} 个章节成功")
        print(f"{'='*50}")
        
        if total_success == total_chapters:
            print(f"\n✓ 所有章节图片重命名完成")
            return 0
        else:
            print(f"\n⚠️  部分章节处理失败")
            return 1

if __name__ == '__main__':
    sys.exit(main())