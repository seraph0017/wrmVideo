#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
测试简单的Celery任务执行
"""

import os
import sys
import django
from pathlib import Path
import time

# 设置项目路径
project_root = Path(__file__).parent.parent
web_root = project_root / 'web'
sys.path.insert(0, str(project_root))
sys.path.insert(0, str(web_root))

# 设置Django环境
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'web.settings')
os.chdir(str(web_root))  # 切换到web目录
django.setup()

from web.celery import debug_task
from celery.result import AsyncResult

def test_simple_task():
    """
    测试简单任务执行
    """
    try:
        print("=== 提交debug_task ===")
        result = debug_task.delay()
        print(f"任务ID: {result.id}")
        print(f"任务状态: {result.status}")
        
        # 等待任务完成
        print("\n等待任务完成...")
        for i in range(10):
            time.sleep(1)
            print(f"第{i+1}秒 - 状态: {result.status}")
            if result.ready():
                break
        
        if result.ready():
            print(f"\n任务完成!")
            print(f"最终状态: {result.status}")
            if result.successful():
                print(f"任务结果: {result.result}")
            else:
                print(f"任务失败: {result.traceback}")
        else:
            print("\n任务仍在执行中或超时")
        
        return True
        
    except Exception as e:
        print(f"测试失败: {e}")
        import traceback
        traceback.print_exc()
        return False

if __name__ == '__main__':
    success = test_simple_task()
    sys.exit(0 if success else 1)