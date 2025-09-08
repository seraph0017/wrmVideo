#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
简化的Celery监控脚本
"""

import subprocess
import time
import json
from datetime import datetime

def run_celery_command(cmd):
    """执行celery命令并返回结果"""
    try:
        result = subprocess.run(
            ['celery', '-A', 'web'] + cmd.split(),
            capture_output=True,
            text=True,
            cwd='/Users/xunan/Projects/wrmVideo/web'
        )
        return result.stdout if result.returncode == 0 else None
    except Exception as e:
        print(f"执行命令失败: {e}")
        return None

def show_active_tasks():
    """显示活跃任务"""
    print("\n🔍 检查活跃任务...")
    output = run_celery_command('inspect active')
    if output:
        print(output)
    else:
        print("❌ 无法获取活跃任务信息")

def show_worker_stats():
    """显示worker统计"""
    print("\n📊 Worker统计信息...")
    output = run_celery_command('inspect stats')
    if output:
        # 只显示关键信息
        lines = output.split('\n')
        for line in lines[:20]:  # 只显示前20行
            if line.strip():
                print(line)
    else:
        print("❌ 无法获取统计信息")

def show_registered_tasks():
    """显示已注册任务"""
    print("\n📋 已注册任务...")
    output = run_celery_command('inspect registered')
    if output:
        print(output)
    else:
        print("❌ 无法获取已注册任务")

def monitor_once():
    """执行一次监控"""
    print("=" * 60)
    print(f"⏰ 监控时间: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    
    show_active_tasks()
    show_registered_tasks()
    show_worker_stats()

if __name__ == "__main__":
    print("🚀 Celery简化监控工具")
    print("按 Ctrl+C 退出")
    
    try:
        while True:
            monitor_once()
            print("\n⏳ 等待30秒...")
            time.sleep(30)
    except KeyboardInterrupt:
        print("\n👋 监控已停止")