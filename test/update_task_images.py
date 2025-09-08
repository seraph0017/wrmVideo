#!/usr/bin/env python
# -*- coding: utf-8 -*-

import os
import sys
import django
import json

# 添加项目路径
sys.path.append('/Users/xunan/Projects/wrmVideo/web')
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'web.settings')
django.setup()

from video.models import CharacterImageTask

def update_task_images():
    """更新任务的生成图片信息"""
    try:
        # 获取任务
        task = CharacterImageTask.objects.get(task_id='char_img_5_48_d1d5af1d')
        
        # 读取生成结果文件
        result_file = '/Users/xunan/Projects/wrmVideo/data/013/chapter_002/Character_Images/陆川_5/generation_result_char_img_5_48_d1d5af1d.json'
        with open(result_file, 'r', encoding='utf-8') as f:
            result = json.load(f)
        
        # 更新任务的生成图片信息
        task.generated_images = result['generated_images']
        task.save()
        
        print(f'数据库已更新，生成的图片: {task.generated_images}')
        print(f'任务状态: {task.status}')
        print(f'进度: {task.progress}%')
        
    except Exception as e:
        print(f'更新失败: {e}')

if __name__ == '__main__':
    update_task_images()