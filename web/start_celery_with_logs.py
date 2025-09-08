#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
Celery启动脚本 - 带详细日志输出
用于启动Celery worker并配置详细的日志记录
"""

import os
import sys
import subprocess
from datetime import datetime

def start_celery_worker():
    """
    启动Celery worker，配置详细日志输出
    """
    print("=" * 60)
    print("启动Celery Worker - 详细日志模式")
    print(f"启动时间: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    print("=" * 60)
    
    # 确保logs目录存在
    logs_dir = "logs"
    if not os.path.exists(logs_dir):
        os.makedirs(logs_dir)
        print(f"创建日志目录: {logs_dir}")
    
    # 日志文件路径
    log_file = os.path.join(logs_dir, "celery.log")
    
    print(f"日志文件: {log_file}")
    print(f"日志级别: INFO")
    print("-" * 60)
    
    try:
        # 构建Celery命令
        cmd = [
            'celery', '-A', 'web', 'worker',
            '--loglevel=info',
            f'--logfile={log_file}',
            '--concurrency=4',
            '--pool=prefork'
        ]
        
        print(f"执行命令: {' '.join(cmd)}")
        print("\n提示:")
        print("1. 使用 'python watch_celery_logs.py' 实时监控日志")
        print("2. 使用 'python watch_celery_logs.py --recent' 查看最近日志")
        print("3. 按 Ctrl+C 停止 Celery worker")
        print("-" * 60)
        
        # 启动Celery worker
        process = subprocess.run(cmd, cwd=os.getcwd())
        
    except KeyboardInterrupt:
        print("\n" + "=" * 60)
        print("Celery Worker 已停止")
        print(f"停止时间: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
        print("=" * 60)
        
    except Exception as e:
        print(f"启动Celery Worker时发生错误: {e}")
        sys.exit(1)

def show_help():
    """
    显示帮助信息
    """
    print("Celery Worker 启动工具")
    print("")
    print("功能:")
    print("- 启动Celery worker并配置详细的INFO级别日志")
    print("- 自动创建logs目录和日志文件")
    print("- 提供日志监控工具的使用提示")
    print("")
    print("用法:")
    print("  python start_celery_with_logs.py        # 启动Celery worker")
    print("  python start_celery_with_logs.py --help # 显示帮助信息")
    print("")
    print("配套工具:")
    print("  python watch_celery_logs.py             # 实时监控日志")
    print("  python watch_celery_logs.py --recent    # 查看最近日志")
    print("")
    print("日志文件位置: logs/celery.log")

def main():
    """
    主函数
    """
    if len(sys.argv) > 1 and sys.argv[1] == '--help':
        show_help()
    else:
        start_celery_worker()

if __name__ == '__main__':
    main()