#!/usr/bin/env python
"""
同步Narration到数据库脚本

功能：
1. 从narration.txt文件中解析所有解说段落
2. 自动创建或更新数据库中的Narration记录
3. 关联对应的音频、字幕、图片文件路径

使用方法：
    # 同步指定章节的narrations
    python sync_narrations_to_db.py --chapter-id 268
    
    # 同步指定小说的所有章节
    python sync_narrations_to_db.py --novel-id 19
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

from video.models import Novel, Chapter, Narration


def parse_narration_file(narration_path):
    """
    解析narration.txt文件，提取所有解说段落
    
    返回:
        list: 包含所有narration信息的列表
    """
    try:
        with open(narration_path, 'r', encoding='utf-8') as f:
            content = f.read()
        
        narrations = []
        
        # 提取所有分镜
        scenes = re.findall(r'<分镜(\d+)>(.*?)</分镜\1>', content, re.DOTALL)
        
        for scene_num, scene_content in scenes:
            # 提取该分镜下的所有图片特写
            closeups = re.findall(
                r'<图片特写(\d+)>(.*?)</图片特写\1>',
                scene_content,
                re.DOTALL
            )
            
            for closeup_num, closeup_content in closeups:
                # 提取特写人物
                character_match = re.search(r'<特写人物>(.*?)</特写人物>', closeup_content, re.DOTALL)
                if character_match:
                    character_block = character_match.group(1)
                    # 提取角色姓名（支持嵌套标签）
                    name_match = re.search(r'<角色姓名>(.*?)</角色姓名>', character_block)
                    if not name_match:
                        name_match = re.search(r'<姓名>.*?<角色姓名>(.*?)</角色姓名>.*?</姓名>', character_block)
                    featured_character = name_match.group(1).strip() if name_match else '未知'
                else:
                    featured_character = '未知'
                
                # 提取解说内容
                narration_match = re.search(r'<解说内容>(.*?)</解说内容>', closeup_content, re.DOTALL)
                narration_text = narration_match.group(1).strip() if narration_match else ''
                
                # 提取图片prompt
                prompt_match = re.search(r'<图片prompt>(.*?)</图片prompt>', closeup_content, re.DOTALL)
                image_prompt = prompt_match.group(1).strip() if prompt_match else ''
                
                # 构建scene_number（如：1_1, 1_2, 1_3）
                scene_number = f"{scene_num}_{closeup_num}"
                
                narrations.append({
                    'scene_number': scene_number,
                    'featured_character': featured_character,
                    'narration': narration_text,
                    'image_prompt': image_prompt
                })
        
        return narrations
        
    except Exception as e:
        print(f"解析narration文件失败 {narration_path}: {e}")
        return []


def find_narration_files(chapter_dir, scene_number):
    """
    查找指定scene_number对应的音频、字幕、图片文件
    
    返回:
        dict: 包含mp3_path, subtitle_content, image_paths
    """
    files = {
        'mp3_path': None,
        'subtitle_content': None,
        'image_paths': []
    }
    
    # 解析scene_number（如 "1_1" -> scene=1, closeup=1）
    parts = scene_number.split('_')
    if len(parts) != 2:
        return files
    
    scene_num, closeup_num = parts
    
    # 查找音频文件（如 narration_01.mp3）
    # 计算narration编号：(scene-1)*3 + closeup
    narration_idx = (int(scene_num) - 1) * 3 + int(closeup_num)
    mp3_pattern = os.path.join(chapter_dir, f'narration_{narration_idx:02d}.mp3')
    mp3_files = glob.glob(mp3_pattern)
    if mp3_files:
        files['mp3_path'] = os.path.relpath(mp3_files[0], project_root)
    
    # 查找字幕文件（如 narration_01.ass）
    ass_pattern = os.path.join(chapter_dir, f'narration_{narration_idx:02d}.ass')
    ass_files = glob.glob(ass_pattern)
    if ass_files:
        try:
            with open(ass_files[0], 'r', encoding='utf-8') as f:
                files['subtitle_content'] = f.read()
        except:
            pass
    
    # 查找图片文件（如 chapter_001_image_01_1.jpeg）
    chapter_name = os.path.basename(chapter_dir)
    chapter_match = re.search(r'chapter_(\d+)', chapter_name)
    if chapter_match:
        chapter_num = chapter_match.group(1)
        image_pattern = os.path.join(
            chapter_dir,
            f'chapter_{chapter_num}_image_{int(scene_num):02d}_{closeup_num}.*'
        )
        image_files = glob.glob(image_pattern)
        if image_files:
            files['image_paths'] = [os.path.relpath(f, project_root) for f in image_files]
    
    return files


def sync_chapter_narrations(chapter_id):
    """
    同步指定章节的所有narrations到数据库
    
    返回:
        tuple: (创建数量, 更新数量, 跳过数量)
    """
    try:
        chapter = Chapter.objects.get(pk=chapter_id)
    except Chapter.DoesNotExist:
        print(f"✗ 章节ID {chapter_id} 不存在")
        return 0, 0, 0
    
    print(f"处理章节: {chapter.title} (ID={chapter_id})")
    
    # 构建章节目录路径
    novel_id = chapter.novel.id
    data_dir = os.path.join(project_root, 'data', f'{novel_id:03d}')
    
    # 查找章节目录
    chapter_dirs = glob.glob(os.path.join(data_dir, 'chapter_*'))
    chapter_dir = None
    for cdir in chapter_dirs:
        if os.path.basename(cdir) == chapter.title:
            chapter_dir = cdir
            break
    
    if not chapter_dir:
        print(f"✗ 未找到章节目录: {chapter.title}")
        return 0, 0, 0
    
    # 查找narration.txt文件
    narration_path = os.path.join(chapter_dir, 'narration.txt')
    if not os.path.exists(narration_path):
        print(f"✗ 未找到narration.txt文件")
        return 0, 0, 0
    
    # 解析narration文件
    narrations = parse_narration_file(narration_path)
    if not narrations:
        print(f"✗ 解析narration文件失败或无内容")
        return 0, 0, 0
    
    print(f"  找到 {len(narrations)} 个解说段落")
    
    created_count = 0
    updated_count = 0
    skipped_count = 0
    
    for narr_info in narrations:
        # 查找对应的文件
        files = find_narration_files(chapter_dir, narr_info['scene_number'])
        
        # 创建或更新Narration记录
        narration, created = Narration.objects.update_or_create(
            chapter=chapter,
            scene_number=narr_info['scene_number'],
            defaults={
                'featured_character': narr_info['featured_character'],
                'narration': narr_info['narration'],
                'image_prompt': narr_info['image_prompt'],
                'narration_mp3_path': files['mp3_path'],
                'subtitle_content': files['subtitle_content'],
                'generated_images': files['image_paths']
            }
        )
        
        if created:
            print(f"  ✓ 创建解说: {narr_info['scene_number']} - {narr_info['featured_character'][:10]}... "
                  f"(音频: {'有' if files['mp3_path'] else '无'}, "
                  f"字幕: {'有' if files['subtitle_content'] else '无'}, "
                  f"图片: {len(files['image_paths'])})")
            created_count += 1
        else:
            print(f"  ✓ 更新解说: {narr_info['scene_number']} - {narr_info['featured_character'][:10]}... "
                  f"(音频: {'有' if files['mp3_path'] else '无'}, "
                  f"字幕: {'有' if files['subtitle_content'] else '无'}, "
                  f"图片: {len(files['image_paths'])})")
            updated_count += 1
    
    return created_count, updated_count, skipped_count


def sync_novel_narrations(novel_id):
    """
    同步指定小说的所有章节的narrations
    
    返回:
        dict: 统计信息
    """
    try:
        novel = Novel.objects.get(pk=novel_id)
    except Novel.DoesNotExist:
        print(f"✗ 小说ID {novel_id} 不存在")
        return None
    
    print(f"同步小说: {novel.name} (ID={novel_id})")
    print("=" * 60)
    
    chapters = novel.chapters.all()
    if not chapters:
        print(f"✗ 该小说没有章节")
        return None
    
    total_stats = {
        'chapters': 0,
        'created': 0,
        'updated': 0,
        'skipped': 0
    }
    
    for chapter in chapters:
        print()
        created, updated, skipped = sync_chapter_narrations(chapter.id)
        
        total_stats['chapters'] += 1
        total_stats['created'] += created
        total_stats['updated'] += updated
        total_stats['skipped'] += skipped
    
    print("\n" + "=" * 60)
    print("同步完成！统计信息：")
    print(f"  处理章节数: {total_stats['chapters']}")
    print(f"  创建解说数: {total_stats['created']}")
    print(f"  更新解说数: {total_stats['updated']}")
    print(f"  跳过解说数: {total_stats['skipped']}")
    print("=" * 60)
    
    return total_stats


def main():
    parser = argparse.ArgumentParser(description='同步Narration到数据库')
    parser.add_argument('--chapter-id', type=int, help='指定要同步的章节ID')
    parser.add_argument('--novel-id', type=int, help='指定要同步的小说ID（同步该小说的所有章节）')
    
    args = parser.parse_args()
    
    try:
        if args.chapter_id:
            # 同步指定章节
            print(f"同步指定章节: ID={args.chapter_id}")
            print("=" * 60)
            created, updated, skipped = sync_chapter_narrations(args.chapter_id)
            print("\n" + "=" * 60)
            print("同步完成！统计信息：")
            print(f"  创建解说数: {created}")
            print(f"  更新解说数: {updated}")
            print(f"  跳过解说数: {skipped}")
            print("=" * 60)
            
        elif args.novel_id:
            # 同步指定小说的所有章节
            sync_novel_narrations(args.novel_id)
            
        else:
            print("请指定 --chapter-id 或 --novel-id 参数")
            return 1
        
        return 0
        
    except Exception as e:
        print(f"\n✗ 同步失败: {e}")
        import traceback
        traceback.print_exc()
        return 1


if __name__ == '__main__':
    sys.exit(main())

