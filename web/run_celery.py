#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
Celery运行脚本
用于启动和管理Celery worker和beat调度器

使用方法:
    python run_celery.py worker          # 启动worker
    python run_celery.py beat            # 启动beat调度器
    python run_celery.py both            # 同时启动worker和beat
    python run_celery.py status          # 查看Celery状态
    python run_celery.py purge           # 清空任务队列
    python run_celery.py monitor         # 启动监控
"""

import os
import sys
import subprocess
import signal
import time
from pathlib import Path
import argparse
import threading

# 设置Django环境
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'web.settings')

# 添加当前目录到Python路径
sys.path.insert(0, str(Path(__file__).parent))

try:
    import django
    django.setup()
except Exception as e:
    print(f"Django设置失败: {e}")
    sys.exit(1)

from django.conf import settings
from celery import Celery

# 全局变量存储进程
worker_process = None
beat_process = None

def signal_handler(signum, frame):
    """
    信号处理器，用于优雅关闭进程
    """
    print("\n接收到停止信号，正在关闭Celery进程...")
    
    global worker_process, beat_process
    
    if worker_process:
        print("正在停止Celery worker...")
        worker_process.terminate()
        worker_process.wait()
        print("Celery worker已停止")
    
    if beat_process:
        print("正在停止Celery beat...")
        beat_process.terminate()
        beat_process.wait()
        print("Celery beat已停止")
    
    sys.exit(0)

def run_worker(loglevel='info', concurrency=None):
    """
    启动Celery worker
    
    Args:
        loglevel (str): 日志级别
        concurrency (int): 并发数
    """
    global worker_process
    
    cmd = [
        sys.executable, '-m', 'celery', 
        '-A', 'web', 'worker',
        '--loglevel', loglevel
    ]
    
    if concurrency:
        cmd.extend(['--concurrency', str(concurrency)])
    
    print(f"启动Celery worker: {' '.join(cmd)}")
    print(f"日志级别: {loglevel}")
    if concurrency:
        print(f"并发数: {concurrency}")
    print("-" * 50)
    
    try:
        worker_process = subprocess.Popen(cmd)
        worker_process.wait()
    except KeyboardInterrupt:
        print("\n接收到中断信号，正在停止worker...")
        if worker_process:
            worker_process.terminate()
            worker_process.wait()
    except Exception as e:
        print(f"启动worker失败: {e}")
        return False
    
    return True

def run_beat(loglevel='info'):
    """
    启动Celery beat调度器
    
    Args:
        loglevel (str): 日志级别
    """
    global beat_process
    
    cmd = [
        sys.executable, '-m', 'celery',
        '-A', 'web', 'beat',
        '--loglevel', loglevel,
        '--scheduler', 'django_celery_beat.schedulers:DatabaseScheduler'
    ]
    
    print(f"启动Celery beat: {' '.join(cmd)}")
    print(f"日志级别: {loglevel}")
    print(f"调度器: django_celery_beat.schedulers:DatabaseScheduler")
    print("-" * 50)
    
    try:
        beat_process = subprocess.Popen(cmd)
        beat_process.wait()
    except KeyboardInterrupt:
        print("\n接收到中断信号，正在停止beat...")
        if beat_process:
            beat_process.terminate()
            beat_process.wait()
    except Exception as e:
        print(f"启动beat失败: {e}")
        return False
    
    return True

def run_both(loglevel='info', concurrency=None):
    """
    同时启动worker和beat
    
    Args:
        loglevel (str): 日志级别
        concurrency (int): worker并发数
    """
    print("同时启动Celery worker和beat调度器")
    print("=" * 50)
    
    # 在单独的线程中启动beat
    beat_thread = threading.Thread(
        target=run_beat,
        args=(loglevel,),
        daemon=True
    )
    beat_thread.start()
    
    # 等待一下确保beat启动
    time.sleep(2)
    
    # 在主线程中启动worker
    run_worker(loglevel, concurrency)

def show_status():
    """
    显示Celery状态
    """
    print("Celery状态检查")
    print("=" * 50)
    
    try:
        # 检查worker状态
        cmd = [sys.executable, '-m', 'celery', '-A', 'web', 'inspect', 'active']
        result = subprocess.run(cmd, capture_output=True, text=True, timeout=10)
        
        if result.returncode == 0:
            print("✅ Celery连接正常")
            print("\n活跃任务:")
            print(result.stdout)
        else:
            print("❌ Celery连接失败")
            print(result.stderr)
    
    except subprocess.TimeoutExpired:
        print("❌ 连接超时，可能没有运行的worker")
    except Exception as e:
        print(f"❌ 状态检查失败: {e}")
    
    try:
        # 检查注册的任务
        cmd = [sys.executable, '-m', 'celery', '-A', 'web', 'inspect', 'registered']
        result = subprocess.run(cmd, capture_output=True, text=True, timeout=10)
        
        if result.returncode == 0:
            print("\n注册的任务:")
            print(result.stdout)
    except Exception as e:
        print(f"获取注册任务失败: {e}")

def purge_queue():
    """
    清空任务队列
    """
    print("清空Celery任务队列")
    print("=" * 50)
    
    try:
        cmd = [sys.executable, '-m', 'celery', '-A', 'web', 'purge', '-f']
        result = subprocess.run(cmd, capture_output=True, text=True)
        
        if result.returncode == 0:
            print("✅ 任务队列已清空")
            print(result.stdout)
        else:
            print("❌ 清空队列失败")
            print(result.stderr)
    except Exception as e:
        print(f"清空队列失败: {e}")

def run_monitor():
    """
    启动Celery监控
    """
    print("启动Celery监控")
    print("=" * 50)
    
    try:
        cmd = [sys.executable, '-m', 'celery', '-A', 'web', 'events']
        subprocess.run(cmd)
    except KeyboardInterrupt:
        print("\n监控已停止")
    except Exception as e:
        print(f"启动监控失败: {e}")

def main():
    """
    主函数
    """
    parser = argparse.ArgumentParser(
        description='Celery运行脚本',
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
示例:
  python run_celery.py worker                    # 启动worker
  python run_celery.py worker --concurrency 4   # 启动worker，设置并发数为4
  python run_celery.py beat                     # 启动beat调度器
  python run_celery.py both                     # 同时启动worker和beat
  python run_celery.py status                   # 查看状态
  python run_celery.py purge                    # 清空队列
  python run_celery.py monitor                  # 启动监控
        """
    )
    
    parser.add_argument(
        'command',
        choices=['worker', 'beat', 'both', 'status', 'purge', 'monitor'],
        help='要执行的命令'
    )
    
    parser.add_argument(
        '--loglevel',
        default='info',
        choices=['debug', 'info', 'warning', 'error', 'critical'],
        help='日志级别 (默认: info)'
    )
    
    parser.add_argument(
        '--concurrency',
        type=int,
        help='Worker并发数 (默认: CPU核心数)'
    )
    
    args = parser.parse_args()
    
    # 注册信号处理器
    signal.signal(signal.SIGINT, signal_handler)
    signal.signal(signal.SIGTERM, signal_handler)
    
    print(f"Celery管理脚本 - {args.command.upper()}")
    print(f"Django设置模块: {os.environ.get('DJANGO_SETTINGS_MODULE')}")
    print(f"Redis URL: {getattr(settings, 'CELERY_BROKER_URL', 'N/A')}")
    print("=" * 50)
    
    if args.command == 'worker':
        run_worker(args.loglevel, args.concurrency)
    elif args.command == 'beat':
        run_beat(args.loglevel)
    elif args.command == 'both':
        run_both(args.loglevel, args.concurrency)
    elif args.command == 'status':
        show_status()
    elif args.command == 'purge':
        purge_queue()
    elif args.command == 'monitor':
        run_monitor()

if __name__ == '__main__':
    main()