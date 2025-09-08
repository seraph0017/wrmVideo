#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
手动测试解说文案解析功能
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

from video.utils import parse_narration_file
from video.models import Novel, Chapter, Character, Narration

def test_manual_parse():
    """
    手动测试解析功能
    """
    print("=" * 50)
    print("手动测试解说文案解析")
    print("=" * 50)
    
    # 读取解说文案文件
    narration_file = "/Users/xunan/Projects/wrmVideo/data/001/chapter_001/narration.txt"
    
    if not os.path.exists(narration_file):
        print(f"文件不存在: {narration_file}")
        return
    
    print(f"读取文件: {narration_file}")
    
    try:
        with open(narration_file, 'r', encoding='utf-8') as f:
            content = f.read()
        
        print(f"文件内容长度: {len(content)} 字符")
        print(f"文件前100字符: {content[:100]}...")
        
        # 解析文件
        print("\n开始解析...")
        parsed_data = parse_narration_file(content)
        
        print("\n解析结果:")
        print(f"章节信息: {parsed_data['chapter_info']}")
        print(f"角色数量: {len(parsed_data['characters'])}")
        print(f"解说数量: {len(parsed_data['narrations'])}")
        
        print("\n角色列表:")
        for i, char in enumerate(parsed_data['characters']):
            print(f"  角色{i+1}: {char}")
        
        print("\n解说列表 (前3个):")
        for i, narr in enumerate(parsed_data['narrations'][:3]):
            print(f"  解说{i+1}: 场景{narr['scene_number']} - {narr['featured_character']}")
            print(f"    内容: {narr['narration'][:50]}...")
        
        # 尝试保存到数据库
        print("\n尝试保存到数据库...")
        
        # 获取小说对象
        novel = Novel.objects.get(id=13)
        print(f"小说: {novel.name}")
        
        # 创建或获取章节
        chapter_number = 1
        chapter_title = parsed_data['chapter_info'].get('title', f'第{chapter_number}章')
        
        # 尝试通过标题查找现有章节
        try:
            chapter = Chapter.objects.get(novel=novel, title=chapter_title)
            created = False
        except Chapter.DoesNotExist:
            # 创建新章节
            chapter = Chapter.objects.create(
                novel=novel,
                title=chapter_title,
                format=parsed_data['chapter_info'].get('format', '未知'),
                word_count=0
            )
            created = True
        
        print(f"章节: {chapter.title} ({'新建' if created else '已存在'})")
        
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
                
                # 关联角色到章节
                character.chapter = chapter
                character.save()
                print(f"  角色: {character.name} ({'新建' if char_created else '已存在'})")
        
        # 清除该章节的旧解说记录
        old_count = Narration.objects.filter(chapter=chapter).count()
        Narration.objects.filter(chapter=chapter).delete()
        print(f"清除旧解说记录: {old_count}条")
        
        # 保存分镜解说信息
        for narration_info in parsed_data['narrations']:
            Narration.objects.create(
                scene_number=narration_info['scene_number'],
                featured_character=narration_info['featured_character'],
                chapter=chapter,
                narration=narration_info['narration'],
                image_prompt=narration_info['image_prompt']
            )
        
        print(f"保存解说记录: {len(parsed_data['narrations'])}条")
        
        print("\n数据库保存成功！")
        
    except Exception as e:
        print(f"错误: {str(e)}")
        import traceback
        traceback.print_exc()

if __name__ == '__main__':
    test_manual_parse()