#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
Celery实时日志监控脚本
用于实时查看Celery任务的详细执行日志
"""

import os
import sys
import time
import subprocess
from datetime import datetime

def watch_celery_logs():
    """
    实时监控Celery日志
    """
    print("=" * 60)
    print("Celery实时日志监控")
    print(f"开始时间: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    print("按 Ctrl+C 退出监控")
    print("=" * 60)
    
    # 日志文件路径
    log_file = "logs/celery.log"
    
    # 如果日志文件不存在，创建它
    if not os.path.exists(log_file):
        os.makedirs(os.path.dirname(log_file), exist_ok=True)
        with open(log_file, 'w') as f:
            f.write(f"Celery日志开始 - {datetime.now()}\n")
    
    try:
        # 使用tail -f命令实时监控日志文件
        process = subprocess.Popen(
            ['tail', '-f', log_file],
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            universal_newlines=True,
            bufsize=1
        )
        
        print(f"正在监控日志文件: {log_file}")
        print("-" * 60)
        
        # 实时输出日志内容
        for line in iter(process.stdout.readline, ''):
            if line:
                # 添加时间戳和格式化输出
                timestamp = datetime.now().strftime('%H:%M:%S')
                print(f"[{timestamp}] {line.rstrip()}")
                
    except KeyboardInterrupt:
        print("\n" + "=" * 60)
        print("日志监控已停止")
        print(f"结束时间: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
        print("=" * 60)
        process.terminate()
        
    except Exception as e:
        print(f"监控日志时发生错误: {e}")
        
def show_recent_logs(lines=50):
    """
    显示最近的日志内容
    
    Args:
        lines (int): 显示的行数
    """
    log_file = "logs/celery.log"
    
    if not os.path.exists(log_file):
        print(f"日志文件不存在: {log_file}")
        return
        
    try:
        result = subprocess.run(
            ['tail', '-n', str(lines), log_file],
            capture_output=True,
            text=True
        )
        
        if result.stdout:
            print(f"最近 {lines} 行日志:")
            print("-" * 60)
            print(result.stdout)
        else:
            print("日志文件为空")
            
    except Exception as e:
        print(f"读取日志时发生错误: {e}")

def main():
    """
    主函数
    """
    if len(sys.argv) > 1:
        if sys.argv[1] == '--recent':
            lines = int(sys.argv[2]) if len(sys.argv) > 2 else 50
            show_recent_logs(lines)
        elif sys.argv[1] == '--help':
            print("Celery日志监控工具")
            print("")
            print("用法:")
            print("  python watch_celery_logs.py           # 实时监控日志")
            print("  python watch_celery_logs.py --recent  # 显示最近50行日志")
            print("  python watch_celery_logs.py --recent 100  # 显示最近100行日志")
            print("  python watch_celery_logs.py --help    # 显示帮助信息")
        else:
            print("未知参数，使用 --help 查看帮助")
    else:
        watch_celery_logs()

if __name__ == '__main__':
    main()