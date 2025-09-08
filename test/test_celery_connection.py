#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
测试Celery连接和任务提交
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

from video.tasks import test_task
from web.celery import debug_task
import redis

def test_celery_connection():
    """
    测试Celery连接和任务提交
    """
    try:
        print("=== 测试Redis连接 ===")
        r = redis.Redis(host='localhost', port=6379, db=0)
        print(f"Redis连接状态: {r.ping()}")
        print(f"队列长度: {r.llen('celery')}")
        
        print("\n=== 测试Celery任务提交 ===")
        
        # 测试debug_task
        print("提交debug_task...")
        result1 = debug_task.delay()
        print(f"debug_task任务ID: {result1.id}")
        
        # 测试test_task
        print("提交test_task...")
        result2 = test_task.delay("测试消息")
        print(f"test_task任务ID: {result2.id}")
        
        # 检查队列状态
        print(f"\n提交后队列长度: {r.llen('celery')}")
        queue_content = r.lrange('celery', 0, -1)
        print(f"队列内容数量: {len(queue_content)}")
        
        if queue_content:
            print("队列中的任务:")
            for i, task in enumerate(queue_content):
                print(f"  {i+1}. {task[:100]}...")
        
        return True
        
    except Exception as e:
        print(f"测试失败: {e}")
        import traceback
        traceback.print_exc()
        return False

if __name__ == '__main__':
    success = test_celery_connection()
    sys.exit(0 if success else 1)