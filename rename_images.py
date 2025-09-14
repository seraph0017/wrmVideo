#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
图片重命名脚本
将原本的3个特写图片格式重命名为单独的narration图片格式
从 chapter_xxx_image_YY_Z.jpeg 重命名为 chapter_xxx_image_ZZ.jpeg
支持按章节执行并更新数据库记录
"""

import os
import sys
import glob
import argparse
from pathlib import Path
import django
from django.conf import settings

# 添加Django项目路径
project_root = os.path.dirname(os.path.abspath(__file__))
web_dir = os.path.join(project_root, 'web')
if web_dir not in sys.path:
    sys.path.insert(0, web_dir)

# 配置Django设置
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'web.settings')
django.setup()

def rename_images_in_chapter(chapter_path, update_database=True):
    """
    重命名章节中的图片文件并更新数据库记录
    
    Args:
        chapter_path: 章节目录路径
        update_database: 是否更新数据库记录
    
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
    
    # 更新数据库记录
    if update_database and new_index > 1:
        try:
            update_narration_image_paths(chapter_path, new_index - 1)
        except Exception as e:
            print(f"⚠️  数据库更新失败: {e}")
            # 不影响重命名操作的成功状态
    
    return True

def update_narration_image_paths(chapter_path, total_images):
    """
    更新数据库中的Narration记录，设置图片路径
    
    Args:
        chapter_path: 章节目录路径
        total_images: 重命名后的图片总数
    """
    try:
        from video.models import Chapter, Narration
        from video.utils import get_chapter_number_from_filesystem
    except ImportError as e:
        print(f"❌ 无法导入Django模型: {e}")
        print("请确保在正确的环境中运行此脚本")
        return
    
    chapter_name = os.path.basename(chapter_path)
    print(f"\n正在更新数据库记录: {chapter_name}")
    
    # 解析章节编号
    try:
        chapter_number = chapter_name.replace('chapter_', '')
        chapter_num = int(chapter_number)
    except ValueError:
        print(f"❌ 无法解析章节编号: {chapter_name}")
        return
    
    # 获取数据目录编号（从路径中提取）
    data_path = os.path.dirname(chapter_path)
    data_dir_name = os.path.basename(data_path)
    try:
        novel_id = int(data_dir_name)
    except ValueError:
        print(f"❌ 无法解析小说ID: {data_dir_name}")
        return
    
    try:
        # 查找对应的章节
        chapters = Chapter.objects.filter(novel_id=novel_id)
        chapter = None
        
        # 尝试通过章节编号匹配
        for ch in chapters:
            # 从文件系统获取章节编号进行匹配
            fs_chapter_number = get_chapter_number_from_filesystem(novel_id, ch)
            if fs_chapter_number == chapter_number:
                chapter = ch
                break
        
        if not chapter:
            print(f"❌ 未找到对应的章节记录: novel_id={novel_id}, chapter_number={chapter_number}")
            return
        
        print(f"找到章节: {chapter.title} (ID: {chapter.id})")
        
        # 获取该章节的所有Narration记录
        narrations = Narration.objects.filter(chapter=chapter).order_by('scene_number')
        
        if not narrations.exists():
            print(f"❌ 章节 {chapter.title} 没有解说记录")
            return
        
        updated_count = 0
        
        # 为每个narration设置对应的图片路径
        for i, narration in enumerate(narrations, 1):
            if i <= total_images:
                # 构建图片相对路径
                image_filename = f"{chapter_name}_image_{i:02d}.jpeg"
                image_relative_path = f"data/{novel_id:03d}/{chapter_name}/{image_filename}"
                
                # 检查图片文件是否存在
                full_image_path = os.path.join(chapter_path, image_filename)
                if os.path.exists(full_image_path):
                    # 更新generated_images字段
                    narration.generated_images = [image_relative_path]
                    narration.save()
                    updated_count += 1
                    print(f"✓ 更新解说 {narration.scene_number}: {image_relative_path}")
                else:
                    print(f"⚠️  图片文件不存在: {full_image_path}")
            else:
                # 清空超出范围的narration的图片路径
                if narration.generated_images:
                    narration.generated_images = []
                    narration.save()
                    print(f"✓ 清空解说 {narration.scene_number} 的图片路径")
        
        print(f"\n数据库更新完成: 更新了 {updated_count} 条记录")
        
    except Exception as e:
        print(f"❌ 数据库操作失败: {e}")
        import traceback
        traceback.print_exc()
        raise

def main():
    parser = argparse.ArgumentParser(description='重命名图片文件')
    parser.add_argument('data_path', help='数据目录路径（如 data/006 或 data/006/chapter_002）')
    parser.add_argument('--no-db-update', action='store_true', help='不更新数据库记录')
    
    args = parser.parse_args()
    update_database = not args.no_db_update
    
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
        success = rename_images_in_chapter(data_path, update_database)
        
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
            
            success = rename_images_in_chapter(chapter_path, update_database)
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