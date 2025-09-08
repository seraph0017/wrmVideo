#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
检查数据库中的数据状态
"""

import os
import sys
import django

# 添加项目根目录到Python路径
project_root = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, project_root)
sys.path.insert(0, os.path.join(project_root, 'web'))

# 设置Django环境
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'web.settings')
django.setup()

from video.models import Novel, Chapter, Character, Narration

def check_database_status():
    """
    检查数据库中的数据状态
    """
    print("=" * 50)
    print("数据库状态检查")
    print("=" * 50)
    
    # 统计数据
    novel_count = Novel.objects.count()
    chapter_count = Chapter.objects.count()
    character_count = Character.objects.count()
    narration_count = Narration.objects.count()
    
    print(f"小说数量: {novel_count}")
    print(f"章节数量: {chapter_count}")
    print(f"角色数量: {character_count}")
    print(f"解说数量: {narration_count}")
    
    print("\n=== 小说列表 ===")
    for novel in Novel.objects.all():
        print(f"小说{novel.id}: {novel.name} (类型: {novel.type}, 字数: {novel.word_count})")
        print(f"  任务状态: {novel.task_status}")
        if novel.task_message:
            print(f"  任务消息: {novel.task_message}")
    
    print("\n=== 章节列表 ===")
    for chapter in Chapter.objects.all():
        print(f"章节{chapter.id}: {chapter.title} (小说: {chapter.novel.name})")
        print(f"  格式: {chapter.format}, 字数: {chapter.word_count}")
        print(f"  解说数量: {chapter.narrations.count()}")
        print(f"  角色数量: {chapter.characters.count()}")
    
    print("\n=== 角色列表 ===")
    for character in Character.objects.all():
        print(f"角色{character.id}: {character.name} ({character.gender}, {character.age_group})")
        print(f"  所属章节: {character.chapter.title if character.chapter else '未分配'}")
    
    print("\n=== 解说列表 (前10个) ===")
    for narration in Narration.objects.all()[:10]:
        print(f"解说{narration.id}: {narration.scene_number} - {narration.featured_character}")
        print(f"  章节: {narration.chapter.title}")
        print(f"  解说内容: {narration.narration[:50]}...")
        print()
    
    # 检查特定小说的数据
    print("\n=== 小说13的详细信息 ===")
    try:
        novel_13 = Novel.objects.get(id=13)
        print(f"小说: {novel_13.name}")
        print(f"任务状态: {novel_13.task_status}")
        print(f"任务消息: {novel_13.task_message}")
        
        chapters = Chapter.objects.filter(novel=novel_13)
        print(f"章节数量: {chapters.count()}")
        
        for chapter in chapters:
            print(f"  章节: {chapter.title}")
            print(f"    解说数量: {chapter.narrations.count()}")
            print(f"    角色数量: {chapter.characters.count()}")
            
    except Novel.DoesNotExist:
        print("小说13不存在")

if __name__ == '__main__':
    check_database_status()