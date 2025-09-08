#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
检查任务状态
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

from celery.result import AsyncResult
from web.celery import app

def check_task_status(task_id):
    """
    检查任务状态
    """
    try:
        result = AsyncResult(task_id, app=app)
        print(f"任务ID: {task_id}")
        print(f"任务状态: {result.status}")
        print(f"任务就绪: {result.ready()}")
        print(f"任务成功: {result.successful() if result.ready() else 'N/A'}")
        
        if result.ready():
            if result.successful():
                print(f"任务结果: {result.result}")
            else:
                print(f"任务失败信息: {result.traceback}")
        
        return True
        
    except Exception as e:
        print(f"检查失败: {e}")
        import traceback
        traceback.print_exc()
        return False

if __name__ == '__main__':
    if len(sys.argv) > 1:
        task_id = sys.argv[1]
        success = check_task_status(task_id)
    else:
        print("用法: python check_task_status.py <task_id>")
        success = False
    
    sys.exit(0 if success else 1)