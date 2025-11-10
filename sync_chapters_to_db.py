#!/usr/bin/env python
"""
同步章节到数据库脚本

功能：
1. 扫描data目录下的所有章节目录
2. 解析narration.txt文件获取章节信息
3. 自动创建或更新数据库中的Novel和Chapter记录
4. 支持批量同步和单个小说同步

使用方法：
    # 同步所有小说
    python sync_chapters_to_db.py
    
    # 同步指定小说
    python sync_chapters_to_db.py --novel-id 20
    
    # 同步指定数据目录
    python sync_chapters_to_db.py --data-dir data/020
"""

import os
import sys
import re
import glob
import argparse
from pathlib import Path

# 添加Django项目路径
project_root = Path(__file__).parent
web_root = project_root / 'web'
sys.path.insert(0, str(web_root))

# 设置Django环境
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'web.settings')
import django
django.setup()

from video.models import Novel, Chapter


def extract_novel_id_from_path(data_dir):
    """
    从路径中提取小说ID
    例如: data/020 -> 20
    """
    match = re.search(r'/(\d{3})/?$', str(data_dir))
    if match:
        return int(match.group(1))
    return None


def parse_narration_file(narration_path):
    """
    解析narration.txt文件，提取章节信息
    
    返回:
        dict: 包含title, word_count, format等信息
    """
    try:
        with open(narration_path, 'r', encoding='utf-8') as f:
            content = f.read()
        
        # 提取章节标题（从文件名或内容中）
        chapter_dir = os.path.dirname(narration_path)
        chapter_name = os.path.basename(chapter_dir)
        
        # 提取解说内容并计算字数
        narration_contents = re.findall(r'<解说内容>(.*?)</解说内容>', content, re.DOTALL)
        total_words = sum(len(n.strip()) for n in narration_contents)
        
        # 提取章节风格（如果有）
        format_match = re.search(r'<章节风格>(.*?)</章节风格>', content)
        chapter_format = format_match.group(1).strip() if format_match else '未知'
        
        return {
            'title': chapter_name,
            'word_count': total_words,
            'format': chapter_format
        }
    except Exception as e:
        print(f"解析narration文件失败 {narration_path}: {e}")
        return None


def check_video_exists(chapter_dir):
    """
    检查章节目录下是否存在完整视频文件
    
    返回:
        str: 视频文件路径（相对于项目根目录），如果不存在返回None
    """
    # 查找complete.mp4文件
    video_patterns = [
        os.path.join(chapter_dir, '*_complete.mp4'),
        os.path.join(chapter_dir, 'complete.mp4'),
        os.path.join(chapter_dir, '*.mp4')
    ]
    
    for pattern in video_patterns:
        videos = glob.glob(pattern)
        if videos:
            # 返回相对路径
            rel_path = os.path.relpath(videos[0], project_root)
            return rel_path
    
    return None


def count_chapter_files(chapter_dir):
    """
    统计章节目录下的文件数量
    
    返回:
        dict: 包含script_count, audio_count, subtitle_count, image_count
    """
    stats = {
        'script_count': 0,
        'audio_count': 0,
        'subtitle_count': 0,
        'image_count': 0
    }
    
    # 统计脚本文件（narration.txt）
    if os.path.exists(os.path.join(chapter_dir, 'narration.txt')):
        stats['script_count'] = 1
    
    # 统计旁白音频文件（*.mp3）
    audio_files = glob.glob(os.path.join(chapter_dir, '*.mp3'))
    stats['audio_count'] = len(audio_files)
    
    # 统计字幕文件（*.ass）
    subtitle_files = glob.glob(os.path.join(chapter_dir, '*.ass'))
    stats['subtitle_count'] = len(subtitle_files)
    
    # 统计图片文件（*.jpeg, *.jpg, *.png）
    image_patterns = [
        os.path.join(chapter_dir, '*.jpeg'),
        os.path.join(chapter_dir, '*.jpg'),
        os.path.join(chapter_dir, '*.png')
    ]
    image_files = []
    for pattern in image_patterns:
        image_files.extend(glob.glob(pattern))
    stats['image_count'] = len(image_files)
    
    return stats


def sync_novel_chapters(novel_id, data_dir):
    """
    同步指定小说的所有章节到数据库
    
    参数:
        novel_id: 小说ID
        data_dir: 数据目录路径（如 data/020）
    
    返回:
        tuple: (创建数量, 更新数量, 跳过数量)
    """
    # 获取或创建Novel对象
    novel, created = Novel.objects.get_or_create(
        id=novel_id,
        defaults={
            'name': f'小说{novel_id:03d}',
            'word_count': 0,
            'type': '未分类'
        }
    )
    
    if created:
        print(f"✓ 创建小说记录: ID={novel_id}, 名称={novel.name}")
    else:
        print(f"✓ 找到小说记录: ID={novel_id}, 名称={novel.name}")
    
    # 查找所有章节目录
    chapter_dirs = sorted(glob.glob(os.path.join(data_dir, 'chapter_*')))
    
    created_count = 0
    updated_count = 0
    skipped_count = 0
    
    for chapter_dir in chapter_dirs:
        # 提取章节编号
        chapter_name = os.path.basename(chapter_dir)
        match = re.search(r'chapter_(\d+)', chapter_name)
        if not match:
            print(f"✗ 跳过无效章节目录: {chapter_dir}")
            skipped_count += 1
            continue
        
        chapter_num = int(match.group(1))
        
        # 查找narration.txt文件
        narration_path = os.path.join(chapter_dir, 'narration.txt')
        if not os.path.exists(narration_path):
            print(f"✗ 跳过（无narration.txt）: {chapter_name}")
            skipped_count += 1
            continue
        
        # 解析章节信息
        chapter_info = parse_narration_file(narration_path)
        if not chapter_info:
            print(f"✗ 跳过（解析失败）: {chapter_name}")
            skipped_count += 1
            continue
        
        # 检查视频文件
        video_path = check_video_exists(chapter_dir)
        
        # 统计章节文件数量
        file_stats = count_chapter_files(chapter_dir)
        
        # 创建或更新Chapter记录
        chapter, created = Chapter.objects.update_or_create(
            novel=novel,
            title=chapter_info['title'],
            defaults={
                'word_count': chapter_info['word_count'],
                'format': chapter_info['format'],
                'video_path': video_path,
                'script_count': file_stats['script_count'],
                'audio_count': file_stats['audio_count'],
                'subtitle_count': file_stats['subtitle_count'],
                'image_count': file_stats['image_count']
            }
        )
        
        if created:
            print(f"  ✓ 创建章节: {chapter_info['title']} "
                  f"(字数: {chapter_info['word_count']}, "
                  f"脚本: {file_stats['script_count']}, "
                  f"旁白: {file_stats['audio_count']}, "
                  f"字幕: {file_stats['subtitle_count']}, "
                  f"图片: {file_stats['image_count']}, "
                  f"视频: {'有' if video_path else '无'})")
            created_count += 1
        else:
            print(f"  ✓ 更新章节: {chapter_info['title']} "
                  f"(字数: {chapter_info['word_count']}, "
                  f"脚本: {file_stats['script_count']}, "
                  f"旁白: {file_stats['audio_count']}, "
                  f"字幕: {file_stats['subtitle_count']}, "
                  f"图片: {file_stats['image_count']}, "
                  f"视频: {'有' if video_path else '无'})")
            updated_count += 1
    
    # 更新小说的总字数
    total_words = sum(c.word_count for c in novel.chapters.all())
    novel.word_count = total_words
    novel.save()
    print(f"✓ 更新小说总字数: {total_words}")
    
    return created_count, updated_count, skipped_count


def sync_all_novels(data_root='data'):
    """
    同步data目录下所有小说的章节到数据库
    
    参数:
        data_root: data根目录路径
    
    返回:
        dict: 统计信息
    """
    print(f"开始扫描目录: {data_root}")
    print("=" * 60)
    
    # 查找所有小说目录（如 data/001, data/020 等）
    novel_dirs = sorted(glob.glob(os.path.join(data_root, '[0-9][0-9][0-9]')))
    
    if not novel_dirs:
        print(f"✗ 未找到任何小说目录")
        return None
    
    print(f"找到 {len(novel_dirs)} 个小说目录\n")
    
    total_stats = {
        'novels': 0,
        'created': 0,
        'updated': 0,
        'skipped': 0
    }
    
    for novel_dir in novel_dirs:
        novel_id = extract_novel_id_from_path(novel_dir)
        if not novel_id:
            print(f"✗ 跳过无效目录: {novel_dir}")
            continue
        
        print(f"\n处理小说 ID={novel_id:03d} ({novel_dir})")
        print("-" * 60)
        
        created, updated, skipped = sync_novel_chapters(novel_id, novel_dir)
        
        total_stats['novels'] += 1
        total_stats['created'] += created
        total_stats['updated'] += updated
        total_stats['skipped'] += skipped
    
    print("\n" + "=" * 60)
    print("同步完成！统计信息：")
    print(f"  处理小说数: {total_stats['novels']}")
    print(f"  创建章节数: {total_stats['created']}")
    print(f"  更新章节数: {total_stats['updated']}")
    print(f"  跳过章节数: {total_stats['skipped']}")
    print("=" * 60)
    
    return total_stats


def main():
    parser = argparse.ArgumentParser(description='同步章节到数据库')
    parser.add_argument('--novel-id', type=int, help='指定要同步的小说ID')
    parser.add_argument('--data-dir', type=str, help='指定要同步的数据目录（如 data/020）')
    parser.add_argument('--data-root', type=str, default='data', help='data根目录路径（默认: data）')
    
    args = parser.parse_args()
    
    try:
        if args.data_dir:
            # 同步指定目录
            novel_id = extract_novel_id_from_path(args.data_dir)
            if not novel_id:
                print(f"✗ 无法从路径中提取小说ID: {args.data_dir}")
                return 1
            
            print(f"同步指定目录: {args.data_dir}")
            print("=" * 60)
            created, updated, skipped = sync_novel_chapters(novel_id, args.data_dir)
            print("\n" + "=" * 60)
            print("同步完成！统计信息：")
            print(f"  创建章节数: {created}")
            print(f"  更新章节数: {updated}")
            print(f"  跳过章节数: {skipped}")
            print("=" * 60)
            
        elif args.novel_id:
            # 同步指定小说
            data_dir = os.path.join(args.data_root, f'{args.novel_id:03d}')
            if not os.path.exists(data_dir):
                print(f"✗ 数据目录不存在: {data_dir}")
                return 1
            
            print(f"同步指定小说: ID={args.novel_id}")
            print("=" * 60)
            created, updated, skipped = sync_novel_chapters(args.novel_id, data_dir)
            print("\n" + "=" * 60)
            print("同步完成！统计信息：")
            print(f"  创建章节数: {created}")
            print(f"  更新章节数: {updated}")
            print(f"  跳过章节数: {skipped}")
            print("=" * 60)
            
        else:
            # 同步所有小说
            sync_all_novels(args.data_root)
        
        return 0
        
    except Exception as e:
        print(f"\n✗ 同步失败: {e}")
        import traceback
        traceback.print_exc()
        return 1


if __name__ == '__main__':
    sys.exit(main())

