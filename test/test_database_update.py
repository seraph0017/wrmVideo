#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
测试生成和校验功能的数据库更新
"""

import os
import sys
import django
from pathlib import Path

# 添加项目根目录到Python路径
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))
sys.path.insert(0, str(project_root / 'web'))

# 设置Django环境
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'settings')
django.setup()

from video.models import Novel, Chapter, Character, Narration
from video.utils import parse_narration_file

def test_parse_and_save():
    """
    测试解析和保存功能
    """
    print("=== 测试解析和保存功能 ===")
    
    # 查找测试数据
    test_data_dir = project_root / 'data' / '013'
    if not test_data_dir.exists():
        print(f"测试数据目录不存在: {test_data_dir}")
        return False
    
    # 查找narration.txt文件
    narration_files = list(test_data_dir.glob('chapter_*/narration.txt'))
    if not narration_files:
        print("未找到narration.txt文件")
        return False
    
    print(f"找到 {len(narration_files)} 个解说文案文件")
    
    # 获取或创建测试小说
    novel, created = Novel.objects.get_or_create(
        id=13,
        defaults={
            'title': '测试小说',
            'author': '测试作者',
            'content': '测试内容',
            'task_status': 'pending'
        }
    )
    
    if created:
        print("创建了新的测试小说")
    else:
        print("使用现有的测试小说")
    
    # 清理旧数据
    old_chapters = Chapter.objects.filter(novel=novel)
    old_narrations_count = sum(chapter.narration_set.count() for chapter in old_chapters)
    old_chapters.delete()
    print(f"清理了 {old_chapters.count()} 个旧章节和 {old_narrations_count} 条旧解说")
    
    # 解析并保存每个文件
    total_narrations = 0
    for narration_file in narration_files:
        print(f"\n处理文件: {narration_file}")
        
        # 读取文件内容
        with open(narration_file, 'r', encoding='utf-8') as f:
            content = f.read()
        
        # 解析内容
        try:
            parsed_data = parse_narration_file(content)
            print(f"  解析成功: {len(parsed_data['narrations'])} 个分镜")
        except Exception as e:
            print(f"  解析失败: {e}")
            continue
        
        # 获取章节信息
        chapter_info = parsed_data['chapter_info']
        chapter_title = chapter_info.get('title')
        
        if not chapter_title:
            import re
            match = re.search(r'chapter_(\d+)', str(narration_file))
            if match:
                chapter_title = f"第{match.group(1)}章"
            else:
                chapter_title = "未命名章节"
        
        # 创建章节
        chapter, created = Chapter.objects.get_or_create(
            novel=novel,
            title=chapter_title,
            defaults={
                'format': parsed_data['chapter_info'].get('format', ''),
                'word_count': 0
            }
        )
        
        print(f"  章节: {chapter_title} ({'新建' if created else '更新'})")
        
        # 保存角色信息
        for char_info in parsed_data['characters']:
            if char_info.get('name'):
                character, char_created = Character.objects.get_or_create(
                    name=char_info['name'],
                    defaults={
                        'gender': char_info.get('gender', '其他'),
                        'age_group': char_info.get('age_group', '青年')
                    }
                )
                character.chapter = chapter
                character.save()
        
        print(f"  角色: {len(parsed_data['characters'])} 个")
        
        # 保存分镜解说信息
        for narration_info in parsed_data['narrations']:
            Narration.objects.create(
                scene_number=narration_info['scene_number'],
                featured_character=narration_info['featured_character'],
                chapter=chapter,
                narration=narration_info['narration'],
                image_prompt=narration_info['image_prompt']
            )
        
        total_narrations += len(parsed_data['narrations'])
        print(f"  保存了 {len(parsed_data['narrations'])} 条解说")
    
    print(f"\n=== 保存完成 ===")
    print(f"总计保存: {total_narrations} 条解说")
    
    # 验证数据库中的数据
    chapters = Chapter.objects.filter(novel=novel)
    narrations = Narration.objects.filter(chapter__novel=novel)
    characters = Character.objects.filter(chapters__novel=novel).distinct()
    
    print(f"\n=== 数据库验证 ===")
    print(f"章节数: {chapters.count()}")
    print(f"解说数: {narrations.count()}")
    print(f"角色数: {characters.count()}")
    
    # 显示每个章节的解说数量
    for chapter in chapters:
        chapter_narrations = chapter.narration_set.count()
        print(f"  {chapter.title}: {chapter_narrations} 条解说")
    
    return narrations.count() > 0

def test_database_consistency():
    """
    测试数据库一致性
    """
    print("\n=== 测试数据库一致性 ===")
    
    # 检查是否有孤立的解说记录
    orphan_narrations = Narration.objects.filter(chapter__isnull=True)
    print(f"孤立解说记录: {orphan_narrations.count()}")
    
    # 检查是否有空的章节
    empty_chapters = Chapter.objects.filter(narration__isnull=True)
    print(f"空章节: {empty_chapters.count()}")
    
    # 检查角色关联
    characters_with_chapters = Character.objects.filter(chapters__isnull=False).distinct()
    total_characters = Character.objects.count()
    print(f"有章节关联的角色: {characters_with_chapters.count()}/{total_characters}")
    
    return orphan_narrations.count() == 0

if __name__ == '__main__':
    print("=" * 50)
    print("数据库更新功能测试")
    print("=" * 50)
    
    # 测试解析和保存
    parse_success = test_parse_and_save()
    
    # 测试数据库一致性
    consistency_success = test_database_consistency()
    
    print("\n=== 测试总结 ===")
    print(f"解析保存测试: {'通过' if parse_success else '失败'}")
    print(f"数据库一致性测试: {'通过' if consistency_success else '失败'}")
    
    if parse_success and consistency_success:
        print("\n🎉 数据库更新功能正常！")
    else:
        print("\n❌ 数据库更新功能存在问题。")