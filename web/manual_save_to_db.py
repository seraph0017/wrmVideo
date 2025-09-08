#!/usr/bin/env python
# -*- coding: utf-8 -*-

import os
import sys
import django
import glob

# 添加项目路径
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

# 设置Django环境
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'web.settings')
django.setup()

from video.utils import parse_narration_file
from video.models import Novel, Chapter, Character, Narration

def save_narration_to_db(novel_id):
    """
    手动将解说文案保存到数据库
    """
    try:
        # 获取小说对象
        novel = Novel.objects.get(id=novel_id)
        print(f"处理小说: {novel.name}")
        
        # 构建数据目录路径
        project_root = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
        data_dir = os.path.join(project_root, f"data/{novel_id:03d}")
        
        print(f"数据目录: {data_dir}")
        
        # 查找生成的解说文案文件
        narration_files = glob.glob(os.path.join(data_dir, 'chapter_*/narration.txt'))
        print(f"找到解说文案文件: {len(narration_files)} 个")
        
        for narration_file in narration_files:
            print(f"\n处理文件: {narration_file}")
            
            # 读取解说文案内容
            with open(narration_file, 'r', encoding='utf-8') as f:
                narration_content = f.read()
            
            # 解析解说文案
            parsed_data = parse_narration_file(narration_content)
            
            # 获取章节信息
            chapter_info = parsed_data['chapter_info']
            chapter_title = chapter_info.get('title')
            
            # 如果没有标题，尝试从章节号生成
            if not chapter_title and chapter_info.get('chapter_number'):
                chapter_title = f"第{chapter_info['chapter_number']}章"
            
            # 如果还是没有标题，从文件路径推断
            if not chapter_title:
                import re
                match = re.search(r'chapter_(\d+)', narration_file)
                if match:
                    chapter_title = f"第{match.group(1)}章"
                else:
                    chapter_title = "未命名章节"
            
            print(f"章节标题: {chapter_title}")
            print(f"角色数量: {len(parsed_data['characters'])}")
            print(f"分镜数量: {len(parsed_data['narrations'])}")
            
            if chapter_title:
                # 创建或更新章节记录
                chapter, created = Chapter.objects.get_or_create(
                    novel=novel,
                    title=chapter_title,
                    defaults={
                        'format': parsed_data['chapter_info'].get('format', ''),
                        'word_count': 0
                    }
                )
                
                if created:
                    print(f"创建新章节: {chapter_title}")
                else:
                    print(f"更新现有章节: {chapter_title}")
                    # 如果章节已存在，更新格式信息
                    if parsed_data['chapter_info'].get('format'):
                        chapter.format = parsed_data['chapter_info']['format']
                        chapter.save()
                
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
                        
                        if char_created:
                            print(f"  创建新角色: {char_info['name']}")
                        else:
                            print(f"  关联现有角色: {char_info['name']}")
                        
                        # 关联角色到章节
                        character.chapter = chapter
                character.save()
                
                # 清除该章节的旧解说记录
                old_narrations = Narration.objects.filter(chapter=chapter)
                if old_narrations.exists():
                    print(f"  删除 {old_narrations.count()} 个旧解说记录")
                    old_narrations.delete()
                
                # 保存分镜解说信息
                for narration_info in parsed_data['narrations']:
                    Narration.objects.create(
                        scene_number=narration_info['scene_number'],
                        featured_character=narration_info['featured_character'],
                        chapter=chapter,
                        narration=narration_info['narration'],
                        image_prompt=narration_info['image_prompt']
                    )
                
                print(f"  保存 {len(parsed_data['narrations'])} 个分镜解说")
                print(f"章节 '{chapter_title}' 的解说数据已保存到数据库")
        
        print(f"\n小说 {novel_id} 所有解说数据已保存到数据库")
        
        # 更新小说的任务状态
        novel.task_status = 'script_completed'
        novel.task_message = '解说文案生成并保存成功'
        novel.save()
        
        return True
        
    except Novel.DoesNotExist:
        print(f"小说ID {novel_id} 不存在")
        return False
    except Exception as e:
        print(f"保存时出错: {str(e)}")
        import traceback
        traceback.print_exc()
        return False

if __name__ == '__main__':
    novel_id = 13
    success = save_narration_to_db(novel_id)
    if success:
        print("\n数据保存成功！")
    else:
        print("\n数据保存失败！")