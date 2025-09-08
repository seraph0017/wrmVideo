#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
触发角色图片生成任务的测试脚本
"""

import os
import sys
import django
from pathlib import Path

# 设置项目路径
project_root = Path(__file__).parent.parent
web_root = project_root / 'web'
sys.path.insert(0, str(project_root))
sys.path.insert(0, str(web_root))

# 设置Django环境
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'web.settings')
os.chdir(str(web_root))  # 切换到web目录
django.setup()

from video.models import Character, Chapter, CharacterImageTask
from video.tasks import generate_character_image_async

def trigger_task():
    """
    触发角色图片生成任务
    """
    try:
        # 使用已知的角色和章节ID
        character_id = 5  # 陆川
        chapter_id = 48   # 第2章
        
        print(f"触发角色图片生成任务: 角色ID={character_id}, 章节ID={chapter_id}")
        
        # 生成正确的task_id格式
        import uuid
        task_id = f'char_img_{character_id}_{chapter_id}_{uuid.uuid4().hex[:8]}'
        
        # 先创建数据库任务记录
        character = Character.objects.get(id=character_id)
        chapter = Chapter.objects.get(id=chapter_id)
        
        task_record = CharacterImageTask.objects.create(
            task_id=task_id,
            character=character,
            chapter=chapter,
            image_style='anime',
            image_quality='hd',
            image_count=1,
            status='pending',
            progress=0,
            log_message='任务已创建，等待执行...'
        )
        
        print(f"数据库任务记录已创建: ID={task_record.id}, task_id={task_id}")
        
        # 调用Celery任务
        result = generate_character_image_async.delay(
            task_id=task_id,
            character_id=character_id,
            chapter_id=chapter_id,
            image_style='anime',
            image_quality='hd',
            image_count=1
        )
        
        print(f"任务已提交，任务ID: {result.id}")
        print("请检查Celery日志以查看调试信息")
        
        return True
        
    except Exception as e:
        print(f"触发任务失败: {e}")
        return False

if __name__ == '__main__':
    success = trigger_task()
    sys.exit(0 if success else 1)