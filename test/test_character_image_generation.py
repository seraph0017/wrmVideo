#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
测试角色图片生成功能
"""

import os
import sys
import django
import subprocess
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

def test_environment_variables():
    """
    测试环境变量设置
    """
    print("=== 测试1: 环境变量设置 ===")
    
    # 模拟环境变量
    test_env = {
        'CHARACTER_ID': '1',
        'CHARACTER_NAME': '测试角色',
        'CHARACTER_GENDER': '女',
        'CHARACTER_AGE_GROUP': '青年',
        'CHARACTER_DESCRIPTION': '美丽的女主角',
        'IMAGE_STYLE': '动漫风格',
        'IMAGE_QUALITY': 'high',
        'IMAGE_COUNT': '1',
        'CUSTOM_PROMPT': '',
        'TASK_ID': 'test_task_001',
        'CHAPTER_PATH': '/Users/xunan/Projects/wrmVideo/data/001/chapter_001'
    }
    
    # 设置环境变量
    env = os.environ.copy()
    env.update(test_env)
    
    print("设置的环境变量:")
    for key, value in test_env.items():
        print(f"  {key}: {value}")
    
    # 测试gen_single_character_image.py
    try:
        cmd = ['python', str(project_root / 'gen_single_character_image.py')]
        print(f"\n执行命令: {' '.join(cmd)}")
        
        result = subprocess.run(
            cmd,
            cwd=str(project_root),
            env=env,
            capture_output=True,
            text=True,
            timeout=60
        )
        
        print(f"\n返回码: {result.returncode}")
        print(f"标准输出:\n{result.stdout}")
        if result.stderr:
            print(f"标准错误:\n{result.stderr}")
            
        return result.returncode == 0
        
    except subprocess.TimeoutExpired:
        print("命令执行超时")
        return False
    except Exception as e:
        print(f"执行异常: {e}")
        return False

def test_database_character():
    """
    测试数据库中的角色数据
    """
    print("\n=== 测试2: 数据库角色数据 ===")
    
    try:
        # 查找第一个角色
        character = Character.objects.first()
        if not character:
            print("数据库中没有角色数据")
            return False
            
        print(f"找到角色: {character.name}")
        print(f"  ID: {character.id}")
        print(f"  性别: {character.gender}")
        print(f"  年龄组: {character.age_group}")
        print(f"  面部特征: {character.face_features}")
        print(f"  身材特征: {character.body_features}")
        print(f"  发型: {character.hair_style}")
        print(f"  发色: {character.hair_color}")
        print(f"  特殊标记: {character.special_notes}")
        
        # 查找对应的章节
        chapter = character.chapter
        if not chapter:
            print("找不到对应的章节")
            return False
            
        print(f"\n找到章节: {chapter.title}")
        print(f"  章节号: {chapter.chapter_number}")
        print(f"  小说ID: {chapter.novel.id}")
        
        return True
        
    except Exception as e:
        print(f"数据库查询异常: {e}")
        return False

def test_real_character_generation():
    """
    测试真实角色数据生成
    """
    print("\n=== 测试3: 真实角色数据生成 ===")
    
    try:
        # 获取第一个角色和章节
        character = Character.objects.first()
        if not character:
            print("数据库中没有角色数据，跳过测试")
            return True
            
        chapter = character.chapter
        if not chapter:
            print("找不到对应的章节，跳过测试")
            return True
            
        # 构建角色描述
        character_description = []
        if character.face_features:
            character_description.append(f"面部特征: {character.face_features}")
        if character.body_features:
            character_description.append(f"身材特征: {character.body_features}")
        if character.hair_style:
            character_description.append(f"发型: {character.hair_style}")
        if character.hair_color:
            character_description.append(f"发色: {character.hair_color}")
        if character.special_notes:
            character_description.append(f"特殊标记: {character.special_notes}")
            
        description_text = '; '.join(character_description) if character_description else ''
        
        # 构建数据目录路径
        novel_id = chapter.novel.id
        data_dir = project_root / 'data' / f'{novel_id:03d}'
        chapter_dir = data_dir / f'chapter_{chapter.chapter_number:03d}'
        
        # 确保目录存在
        chapter_dir.mkdir(parents=True, exist_ok=True)
        
        # 设置环境变量
        env = os.environ.copy()
        env.update({
            'CHARACTER_ID': str(character.id),
            'CHARACTER_NAME': character.name or '',
            'CHARACTER_GENDER': character.gender or '',
            'CHARACTER_AGE_GROUP': character.age_group or '',
            'CHARACTER_DESCRIPTION': description_text,
            'IMAGE_STYLE': '动漫风格',
            'IMAGE_QUALITY': 'high',
            'IMAGE_COUNT': '1',
            'CUSTOM_PROMPT': '',
            'TASK_ID': f'test_real_{character.id}',
            'CHAPTER_PATH': str(chapter_dir)
        })
        
        print(f"使用角色: {character.name} (ID: {character.id})")
        print(f"章节路径: {chapter_dir}")
        print(f"角色描述: {description_text}")
        
        # 执行生成脚本
        cmd = ['python', str(project_root / 'gen_single_character_image.py')]
        print(f"\n执行命令: {' '.join(cmd)}")
        
        result = subprocess.run(
            cmd,
            cwd=str(project_root),
            env=env,
            capture_output=True,
            text=True,
            timeout=120
        )
        
        print(f"\n返回码: {result.returncode}")
        print(f"标准输出:\n{result.stdout}")
        if result.stderr:
            print(f"标准错误:\n{result.stderr}")
            
        return result.returncode == 0
        
    except Exception as e:
        print(f"测试异常: {e}")
        return False

def main():
    """
    主测试函数
    """
    print("开始测试角色图片生成功能...\n")
    
    results = []
    
    # 测试1: 环境变量设置
    results.append(test_environment_variables())
    
    # 测试2: 数据库角色数据
    results.append(test_database_character())
    
    # 测试3: 真实角色数据生成
    results.append(test_real_character_generation())
    
    # 总结
    print("\n=== 测试总结 ===")
    print(f"测试1 (环境变量设置): {'通过' if results[0] else '失败'}")
    print(f"测试2 (数据库角色数据): {'通过' if results[1] else '失败'}")
    print(f"测试3 (真实角色数据生成): {'通过' if results[2] else '失败'}")
    
    success_count = sum(results)
    print(f"\n总体结果: {success_count}/{len(results)} 个测试通过")
    
    return all(results)

if __name__ == '__main__':
    success = main()
    sys.exit(0 if success else 1)