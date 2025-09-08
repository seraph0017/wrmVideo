#!/usr/bin/env python
import os
import sys
import django

# 设置Django环境
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'web.settings')
django.setup()

from video.models import Novel, Chapter, Character

# 查找小说ID为13的小说
novel = Novel.objects.filter(id=13).first()
print(f"Novel 13: {novel}")

if novel:
    # 查找所有章节
    chapters = Chapter.objects.filter(novel=novel)
    print(f"All chapters in novel 13: {chapters.count()}")
    for ch in chapters:
        print(f"  - {ch.title} (ID: {ch.id})")
        characters = ch.characters.all()
        print(f"    Characters: {characters.count()}")
        for char in characters:
            print(f"      - {char.name} (ID: {char.id})")
    
    # 特别查找包含'002'的章节
    chapter_002 = chapters.filter(title__icontains='002').first()
    if not chapter_002:
        chapter_002 = chapters.filter(title__icontains='2').first()
    
    if chapter_002:
        print(f"\nFound chapter 002: {chapter_002.title} (ID: {chapter_002.id})")
        characters = chapter_002.characters.all()
        print(f"Characters in chapter 002: {characters.count()}")
        for char in characters:
            print(f"  - {char.name} (ID: {char.id})")
else:
    print("Novel with ID 13 not found")
    # 查找所有小说
    novels = Novel.objects.all()
    print(f"All novels:")
    for n in novels:
        print(f"  - {n.name} (ID: {n.id})")