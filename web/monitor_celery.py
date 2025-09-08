#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Celery监控脚本
用于实时监控Celery worker状态和任务执行情况
"""

import os
import sys
import time
import django
from datetime import datetime

# 设置Django环境
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'web.settings')
django.setup()

from celery import Celery
from video.models import Novel

# 初始化Celery应用
app = Celery('web')
app.config_from_object('django.conf:settings', namespace='CELERY')
app.autodiscover_tasks()

def print_separator():
    """打印分隔线"""
    print("=" * 80)

def get_worker_status():
    """获取worker状态"""
    try:
        inspect = app.control.inspect()
        
        # 获取活跃的workers
        active_workers = inspect.active()
        if not active_workers:
            print("❌ 没有活跃的worker")
            return False
            
        print(f"✅ 活跃的workers: {len(active_workers)}")
        
        # 显示每个worker的状态
        for worker_name, tasks in active_workers.items():
            print(f"\n📊 Worker: {worker_name}")
            if tasks:
                print(f"   正在执行的任务数: {len(tasks)}")
                for task in tasks:
                    print(f"   - 任务ID: {task['id'][:8]}...")
                    print(f"     任务名称: {task['name']}")
                    print(f"     参数: {task['args']}")
                    start_time = datetime.fromtimestamp(task['time_start'])
                    print(f"     开始时间: {start_time.strftime('%H:%M:%S')}")
            else:
                print("   当前空闲")
                
        return True
        
    except Exception as e:
        print(f"❌ 获取worker状态失败: {e}")
        return False

def get_registered_tasks():
    """获取已注册的任务"""
    try:
        inspect = app.control.inspect()
        registered = inspect.registered()
        
        if registered:
            for worker_name, tasks in registered.items():
                print(f"\n📋 Worker {worker_name} 已注册的任务:")
                for task in sorted(tasks):
                    print(f"   - {task}")
        else:
            print("❌ 无法获取已注册的任务")
            
    except Exception as e:
        print(f"❌ 获取已注册任务失败: {e}")

def get_worker_stats():
    """获取worker统计信息"""
    try:
        inspect = app.control.inspect()
        stats = inspect.stats()
        
        if stats:
            for worker_name, worker_stats in stats.items():
                print(f"\n📈 Worker {worker_name} 统计信息:")
                print(f"   总任务数: {worker_stats.get('total', 'N/A')}")
                print(f"   进程池大小: {worker_stats.get('pool', {}).get('max-concurrency', 'N/A')}")
                print(f"   运行时间: {worker_stats.get('clock', 'N/A')}")
        else:
            print("❌ 无法获取worker统计信息")
            
    except Exception as e:
        print(f"❌ 获取worker统计信息失败: {e}")

def monitor_loop():
    """监控循环"""
    print("🚀 开始监控Celery...")
    print("按 Ctrl+C 退出监控")
    
    try:
        while True:
            print_separator()
            print(f"⏰ 监控时间: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
            
            # 检查worker状态
            print("\n🔍 检查Worker状态...")
            get_worker_status()
            
            # 获取已注册任务
            print("\n🔍 检查已注册任务...")
            get_registered_tasks()
            
            # 获取统计信息
            print("\n🔍 检查统计信息...")
            get_worker_stats()
            
            print("\n⏳ 等待30秒后继续监控...")
            time.sleep(30)
            
    except KeyboardInterrupt:
        print("\n\n👋 监控已停止")
    except Exception as e:
        print(f"\n❌ 监控过程中发生错误: {e}")

def show_help():
    """显示帮助信息"""
    print("""
🔧 Celery监控工具

使用方法:
  python monitor_celery.py [选项]

选项:
  status    - 显示当前worker状态
  tasks     - 显示已注册的任务
  stats     - 显示worker统计信息
  monitor   - 持续监控模式（默认）
  help      - 显示此帮助信息

示例:
  python monitor_celery.py status
  python monitor_celery.py monitor
    """)

if __name__ == "__main__":
    if len(sys.argv) > 1:
        command = sys.argv[1].lower()
        
        if command == "status":
            print("🔍 检查Worker状态...")
            get_worker_status()
        elif command == "tasks":
            print("🔍 检查已注册任务...")
            get_registered_tasks()
        elif command == "stats":
            print("🔍 检查统计信息...")
            get_worker_stats()
        elif command == "help":
            show_help()
        elif command == "monitor":
            monitor_loop()
        else:
            print(f"❌ 未知命令: {command}")
            show_help()
    else:
        monitor_loop()