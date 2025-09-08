#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
调试角色和章节关联问题
"""

import os
import sys
import django
from pathlib import Path

# 添加项目路径
project_root = Path(__file__).parent.parent
web_root = project_root / 'web'
sys.path.insert(0, str(project_root))
sys.path.insert(0, str(web_root))

# 设置Django环境
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'web.settings')
os.chdir(str(web_root))  # 切换到web目录
django.setup()

from video.models import Character, Chapter, Novel

def debug_character_chapter_relation():
    """
    调试角色和章节关联问题
    """
    print("=== 调试角色和章节关联问题 ===")
    
    # 检查角色ID为5的角色
    try:
        character = Character.objects.get(id=5)
        print(f"找到角色: {character.name} (ID: {character.id})")
        print(f"  性别: {character.gender}")
        print(f"  年龄组: {character.age_group}")
        print(f"  面部特征: {character.face_features}")
        print(f"  身材特征: {character.body_features}")
        print(f"  发型: {character.hair_style}")
        print(f"  发色: {character.hair_color}")
        print(f"  特殊标记: {character.special_notes}")
        
        # 检查关联的章节
        chapter = character.chapter
        print(f"\n关联的章节: {chapter.title if chapter else '未分配'}")
        if chapter:
            print(f"  章节: {chapter.title} (ID: {chapter.id}, 章节号: {chapter.chapter_number})")
            print(f"    小说: {chapter.novel.name} (ID: {chapter.novel.id})")
            
    except Character.DoesNotExist:
        print("角色ID为5的角色不存在")
        return False
    except Exception as e:
        print(f"查询角色异常: {e}")
        return False
    
    # 检查章节ID为48的章节
    try:
        chapter = Chapter.objects.get(id=48)
        print(f"\n找到章节: {chapter.title} (ID: {chapter.id})")
        print(f"  章节号: {chapter.chapter_number}")
        print(f"  小说: {chapter.novel.name} (ID: {chapter.novel.id})")
        
        # 检查该章节关联的角色
        characters = chapter.characters.all()
        print(f"\n该章节关联的角色数量: {characters.count()}")
        for char in characters:
            print(f"  角色: {char.name} (ID: {char.id})")
            
    except Chapter.DoesNotExist:
        print("章节ID为48的章节不存在")
        return False
    except Exception as e:
        print(f"查询章节异常: {e}")
        return False
    
    return True

def check_all_characters_chapters():
    """
    检查所有角色的章节关联情况
    """
    print("\n=== 检查所有角色的章节关联情况 ===")
    
    characters = Character.objects.all()
    print(f"总角色数量: {characters.count()}")
    
    for character in characters:
        chapter = character.chapter
        print(f"角色 {character.name} (ID: {character.id}): 所属章节 {chapter.title if chapter else '未分配'}")
        if not chapter:
            print(f"  ⚠️  角色 {character.name} 没有关联任何章节")
        else:
            print(f"    - {chapter.title} (ID: {chapter.id})")

def check_all_chapters_characters():
    """
    检查所有章节的角色关联情况
    """
    print("\n=== 检查所有章节的角色关联情况 ===")
    
    chapters = Chapter.objects.all()
    print(f"总章节数量: {chapters.count()}")
    
    for chapter in chapters:
        characters = chapter.characters.all()
        print(f"章节 {chapter.title} (ID: {chapter.id}): 关联 {characters.count()} 个角色")
        if characters.count() == 0:
            print(f"  ⚠️  章节 {chapter.title} 没有关联任何角色")
        else:
            for character in characters:
                print(f"    - {character.name} (ID: {character.id})")

def main():
    """
    主函数
    """
    print("开始调试角色和章节关联问题...\n")
    
    # 调试具体的角色和章节
    debug_character_chapter_relation()
    
    # 检查所有角色的章节关联
    check_all_characters_chapters()
    
    # 检查所有章节的角色关联
    check_all_chapters_characters()
    
    print("\n调试完成")

if __name__ == '__main__':
    main()