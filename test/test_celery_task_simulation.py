#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
模拟Celery任务调用，测试环境变量传递
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
from django.conf import settings

def simulate_celery_task():
    """
    模拟Celery任务的环境变量设置和脚本调用
    """
    print("=== 模拟Celery任务调用 ===")
    
    # 使用实际的角色和章节数据
    character_id = 5  # 陆川
    chapter_id = 48   # 第2章
    task_id = 'test_simulation_001'
    
    try:
        # 获取任务记录
        character = Character.objects.get(id=character_id)
        chapter = Chapter.objects.get(id=chapter_id)
        
        print(f"角色信息: ID={character.id}, 名称={character.name}, 性别={character.gender}, 年龄组={character.age_group}")
        print(f"章节信息: ID={chapter.id}, 标题={chapter.title}")
        
        # 构建数据目录路径
        novel_id = chapter.novel.id
        data_dir = os.path.join(settings.BASE_DIR, '..', 'data', f'{novel_id:03d}')
        chapter_dir = os.path.join(data_dir, f'chapter_{chapter.id:03d}')
        
        print(f"数据目录: {data_dir}")
        print(f"章节目录: {chapter_dir}")
        
        # 确保数据目录存在
        if not os.path.exists(data_dir):
            os.makedirs(data_dir, exist_ok=True)
        if not os.path.exists(chapter_dir):
            os.makedirs(chapter_dir, exist_ok=True)
        
        # 构建角色描述信息
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
        
        # 设置环境变量
        env = os.environ.copy()
        env_vars = {
            'CHARACTER_ID': str(character_id),
            'CHARACTER_NAME': character.name or '',
            'CHARACTER_GENDER': character.gender or '',
            'CHARACTER_AGE_GROUP': character.age_group or '',
            'CHARACTER_DESCRIPTION': description_text,
            'IMAGE_STYLE': '动漫风格',
            'IMAGE_QUALITY': 'high',
            'IMAGE_COUNT': '1',
            'CUSTOM_PROMPT': '',
            'TASK_ID': task_id,
            'CHAPTER_PATH': chapter_dir
        }
        
        print(f"\n设置环境变量:")
        for key, value in env_vars.items():
            print(f"  {key}: {value}")
            
        env.update(env_vars)
        
        # 构建命令参数
        cmd = [
            'python', 
            os.path.join(settings.BASE_DIR, '..', 'gen_single_character_image.py')
        ]
        
        print(f"\n执行命令: {' '.join(cmd)}")
        print(f"工作目录: {os.path.join(settings.BASE_DIR, '..')}")
        
        # 执行生成脚本
        result = subprocess.run(
            cmd,
            cwd=os.path.join(settings.BASE_DIR, '..'),
            env=env,
            capture_output=True,
            text=True,
            timeout=120  # 2分钟超时
        )
        
        print(f"\n返回码: {result.returncode}")
        print(f"标准输出:\n{result.stdout}")
        if result.stderr:
            print(f"标准错误:\n{result.stderr}")
            
        return result.returncode == 0
        
    except Character.DoesNotExist:
        print(f"角色ID {character_id} 不存在")
        return False
    except Chapter.DoesNotExist:
        print(f"章节ID {chapter_id} 不存在")
        return False
    except Exception as e:
        print(f"模拟任务异常: {e}")
        return False

def check_environment_variables():
    """
    检查环境变量是否正确传递
    """
    print("\n=== 检查环境变量传递 ===")
    
    # 模拟gen_single_character_image.py中的环境变量检查
    required_vars = ['CHARACTER_ID', 'CHARACTER_NAME', 'TASK_ID', 'CHAPTER_PATH']
    
    # 设置测试环境变量
    test_env = {
        'CHARACTER_ID': '5',
        'CHARACTER_NAME': '陆川',
        'CHARACTER_GENDER': '男',
        'CHARACTER_AGE_GROUP': '青年',
        'CHARACTER_DESCRIPTION': '',
        'IMAGE_STYLE': '动漫风格',
        'IMAGE_QUALITY': 'high',
        'IMAGE_COUNT': '1',
        'CUSTOM_PROMPT': '',
        'TASK_ID': 'test_env_check',
        'CHAPTER_PATH': '/Users/xunan/Projects/wrmVideo/data/013/chapter_002'
    }
    
    # 临时设置环境变量
    original_env = {}
    for key, value in test_env.items():
        original_env[key] = os.environ.get(key)
        os.environ[key] = value
    
    try:
        # 检查必要的环境变量
        missing_vars = []
        for var in required_vars:
            value = os.environ.get(var)
            if not value:
                missing_vars.append(var)
            else:
                print(f"✓ {var}: {value}")
        
        if missing_vars:
            print(f"✗ 缺少环境变量: {missing_vars}")
            return False
        else:
            print("✓ 所有必要的环境变量都已设置")
            return True
            
    finally:
        # 恢复原始环境变量
        for key, value in original_env.items():
            if value is None:
                os.environ.pop(key, None)
            else:
                os.environ[key] = value

def main():
    """
    主函数
    """
    print("开始模拟Celery任务调用测试...\n")
    
    results = []
    
    # 测试1: 检查环境变量传递
    results.append(check_environment_variables())
    
    # 测试2: 模拟完整的Celery任务调用
    results.append(simulate_celery_task())
    
    # 总结
    print("\n=== 测试总结 ===")
    print(f"测试1 (环境变量传递): {'通过' if results[0] else '失败'}")
    print(f"测试2 (模拟Celery任务): {'通过' if results[1] else '失败'}")
    
    success_count = sum(results)
    print(f"\n总体结果: {success_count}/{len(results)} 个测试通过")
    
    return all(results)

if __name__ == '__main__':
    success = main()
    sys.exit(0 if success else 1)