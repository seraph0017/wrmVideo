#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
重新生成角色图片并更新数据库image_path字段

使用方法:
    python regenerate_character_images.py --character-id 24
    python regenerate_character_images.py --chapter 013 chapter_002
    python regenerate_character_images.py --all
"""

import os
import sys
import django
import argparse
import subprocess
from pathlib import Path

# 添加Django项目路径
sys.path.append('/Users/xunan/Projects/wrmVideo/web')
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'web.settings')
django.setup()

from django.db import models
from video.models import Character, Chapter, Novel, CharacterImageTask

def regenerate_character_image(character_id, novel_id=None, chapter_id=None):
    """
    重新生成指定角色的图片并更新数据库image_path字段
    
    Args:
        character_id: 角色ID
        novel_id: 小说ID（可选）
        chapter_id: 章节ID（可选）
    
    Returns:
        bool: 是否成功
    """
    try:
        # 获取角色信息
        character = Character.objects.get(id=character_id)
        print(f"正在为角色 '{character.name}' (ID: {character_id}) 重新生成图片...")
        
        # 如果没有指定章节，获取角色的第一个章节
        if not novel_id or not chapter_id:
            first_chapter = character.chapter
            if not first_chapter:
                print(f"错误: 角色 '{character.name}' 没有关联的章节")
                return False
            
            novel_id = str(first_chapter.novel.id).zfill(3)
            chapter_id = f"chapter_{str(first_chapter.id).zfill(3)}"
            print(f"使用章节: {novel_id}/{chapter_id}")
        
        # 构建章节路径
        chapter_path = f"data/{novel_id}/{chapter_id}"
        
        # 检查章节路径是否存在
        if not os.path.exists(chapter_path):
            print(f"错误: 章节路径不存在: {chapter_path}")
            return False
        
        # 设置环境变量
        env = os.environ.copy()
        env['CHARACTER_ID'] = str(character_id)
        env['CHARACTER_NAME'] = character.name
        env['CHARACTER_GENDER'] = character.gender or ''
        env['CHARACTER_AGE_GROUP'] = character.age_group or ''
        env['CHARACTER_DESCRIPTION'] = f"{character.hair_style or ''} {character.hair_color or ''} {character.face_features or ''} {character.body_features or ''} {character.special_notes or ''}".strip()
        env['CHAPTER_PATH'] = chapter_path
        env['TASK_ID'] = f"regenerate_{character_id}_{int(time.time())}"
        env['CMD_MODE'] = '1'  # 命令行模式
        
        print(f"开始生成角色图片...")
        print(f"角色信息: {character.name} ({character.gender}, {character.age_group})")
        
        # 调用角色图片生成脚本
        result = subprocess.run(
            ['python', 'gen_single_character_image.py'],
            cwd='/Users/xunan/Projects/wrmVideo',
            env=env,
            capture_output=True,
            text=True,
            timeout=300  # 5分钟超时
        )
        
        if result.returncode == 0:
            print("✓ 角色图片生成成功")
            print(f"输出: {result.stdout}")
            
            # 解析生成结果，查找JSON输出
            try:
                import json
                import re
                
                # 查找JSON结果（支持多种格式）
                json_match = re.search(r'\{[^{}]*"status"[^{}]*\}', result.stdout)
                if json_match:
                    result_json = json.loads(json_match.group())
                    
                    # 检查是否生成成功
                    if result_json.get('status') == 'success' and 'generated_images' in result_json:
                        generated_images = result_json['generated_images']
                        
                        if generated_images and len(generated_images) > 0:
                            # 使用第一张生成的图片路径
                            image_path = generated_images[0]
                            
                            # 转换为相对路径（去掉data/前缀）
                            if image_path.startswith('data/'):
                                relative_path = image_path[5:]  # 去掉'data/'前缀
                            else:
                                relative_path = image_path
                            
                            # 更新角色的image_path字段
                            character.image_path = relative_path
                            character.save()
                            
                            print(f"✓ 已更新角色image_path: {relative_path}")
                            return True
                        else:
                            print(f"✗ 生成结果中没有找到图片路径")
                    else:
                        print(f"✗ 图片生成失败或状态不正确")
                else:
                    print(f"✗ 无法解析生成结果中的JSON")
                    
            except Exception as e:
                print(f"✗ 解析生成结果时出错: {e}")
                
        else:
            print(f"✗ 角色图片生成失败")
            print(f"错误输出: {result.stderr}")
            
        return False
        
    except Character.DoesNotExist:
        print(f"错误: 角色ID {character_id} 不存在")
        return False
    except subprocess.TimeoutExpired:
        print(f"错误: 角色图片生成超时")
        return False
    except Exception as e:
        print(f"错误: {e}")
        return False

def regenerate_chapter_characters(novel_id, chapter_id):
    """
    重新生成指定章节所有角色的图片
    
    Args:
        novel_id: 小说ID
        chapter_id: 章节ID
    
    Returns:
        bool: 是否成功
    """
    try:
        # 查找章节
        novel_id_int = int(novel_id)
        chapter_id_int = int(chapter_id.replace('chapter_', ''))
        
        chapter = Chapter.objects.get(novel_id=novel_id_int, id=chapter_id_int)
        characters = chapter.characters.all()
        
        if not characters:
            print(f"章节 {novel_id}/{chapter_id} 没有关联的角色")
            return True
        
        print(f"开始为章节 {novel_id}/{chapter_id} 的 {len(characters)} 个角色重新生成图片...")
        
        success_count = 0
        for character in characters:
            print(f"\n--- 处理角色 {character.name} (ID: {character.id}) ---")
            if regenerate_character_image(character.id, novel_id, chapter_id):
                success_count += 1
            else:
                print(f"角色 {character.name} 图片生成失败")
        
        print(f"\n=== 章节处理完成 ===")
        print(f"成功: {success_count}/{len(characters)} 个角色")
        
        return success_count == len(characters)
        
    except Chapter.DoesNotExist:
        print(f"错误: 章节 {novel_id}/{chapter_id} 不存在")
        return False
    except Exception as e:
        print(f"错误: {e}")
        return False

def regenerate_all_characters():
    """
    重新生成所有角色的图片
    
    Returns:
        bool: 是否成功
    """
    try:
        # 获取所有有image_path为空或NULL的角色
        characters = Character.objects.filter(
            models.Q(image_path__isnull=True) | models.Q(image_path='')
        )
        
        if not characters:
            print("没有找到需要重新生成图片的角色")
            return True
        
        print(f"找到 {len(characters)} 个需要重新生成图片的角色")
        
        success_count = 0
        for character in characters:
            print(f"\n--- 处理角色 {character.name} (ID: {character.id}) ---")
            if regenerate_character_image(character.id):
                success_count += 1
            else:
                print(f"角色 {character.name} 图片生成失败")
        
        print(f"\n=== 全部处理完成 ===")
        print(f"成功: {success_count}/{len(characters)} 个角色")
        
        return success_count == len(characters)
        
    except Exception as e:
        print(f"错误: {e}")
        return False

def main():
    parser = argparse.ArgumentParser(description='重新生成角色图片并更新数据库image_path字段')
    
    group = parser.add_mutually_exclusive_group(required=True)
    group.add_argument('--character-id', type=int, help='指定角色ID')
    group.add_argument('--chapter', nargs=2, metavar=('NOVEL_ID', 'CHAPTER_ID'), help='指定章节（小说ID 章节ID）')
    group.add_argument('--all', action='store_true', help='重新生成所有角色图片')
    
    args = parser.parse_args()
    
    if args.character_id:
        success = regenerate_character_image(args.character_id)
    elif args.chapter:
        novel_id, chapter_id = args.chapter
        success = regenerate_chapter_characters(novel_id, chapter_id)
    elif args.all:
        success = regenerate_all_characters()
    
    if success:
        print("\n✓ 任务完成")
        sys.exit(0)
    else:
        print("\n✗ 任务失败")
        sys.exit(1)

if __name__ == '__main__':
    import time
    main()