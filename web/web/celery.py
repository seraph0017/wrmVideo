# -*- coding: utf-8 -*-
"""
Celery配置文件
用于配置异步任务队列
"""

import os
from celery import Celery

# 设置Django设置模块
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'web.settings')

# 创建Celery应用实例
app = Celery('web')

# 从Django设置中加载配置
app.config_from_object('django.conf:settings', namespace='CELERY')

# 自动发现任务
app.autodiscover_tasks()

# 配置Beat调度器
app.conf.beat_scheduler = 'django_celery_beat.schedulers:DatabaseScheduler'


@app.task(bind=True)
def debug_task(self):
    """
    调试任务
    """
    print(f'Request: {self.request!r}')