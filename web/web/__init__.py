# -*- coding: utf-8 -*-
"""
Django项目初始化文件
确保Celery应用在Django启动时被加载
"""

# 导入Celery应用
from .celery import app as celery_app

__all__ = ('celery_app',)