#!/usr/bin/env python
# -*- coding: utf-8 -*-

import os
import sys
import django

# 添加项目路径
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

# 设置Django环境
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'web.settings')
django.setup()

from video.models import Novel, Chapter, Narration, Character

def check_novel_status(novel_id):
    """
    检查小说的数据库状态
    """
    try:
        novel = Novel.objects.get(id=novel_id)
        print(f"小说ID: {novel.id}")
        print(f"小说名称: {novel.name}")
        print(f"任务状态: {novel.task_status}")
        print(f"任务消息: {novel.task_message}")
        print(f"当前任务ID: {novel.current_task_id}")
        print("-" * 50)
        
        chapters = Chapter.objects.filter(novel=novel)
        print(f"章节数量: {chapters.count()}")
        
        for chapter in chapters:
            narrations = Narration.objects.filter(chapter=chapter)
            print(f"章节: {chapter.title}")
            print(f"  - 格式: {chapter.format}")
            print(f"  - 解说数量: {narrations.count()}")
            
            if narrations.exists():
                for narration in narrations[:3]:  # 只显示前3个
                    print(f"    * 分镜 {narration.scene_number}: {narration.featured_character}")
                if narrations.count() > 3:
                    print(f"    ... 还有 {narrations.count() - 3} 个分镜")
        
        print("-" * 50)
        characters = Character.objects.filter(chapters__novel=novel).distinct()
        print(f"角色数量: {characters.count()}")
        for character in characters:
            print(f"  - {character.name} ({character.gender}, {character.age_group})")
            
    except Novel.DoesNotExist:
        print(f"小说ID {novel_id} 不存在")
    except Exception as e:
        print(f"检查时出错: {str(e)}")

if __name__ == '__main__':
    novel_id = 13
    check_novel_status(novel_id)