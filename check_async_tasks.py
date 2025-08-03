#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
异步任务状态查询脚本
轮询查询async_tasks目录中的所有任务状态，下载完成的图片
"""

import os
import json
import time
import base64
import argparse
from config.config import IMAGE_TWO_CONFIG
from volcengine.visual.VisualService import VisualService

def load_task_info(task_file):
    """
    从txt文件加载任务信息
    
    Args:
        task_file: 任务文件路径
    
    Returns:
        dict: 任务信息，失败返回None
    """
    try:
        with open(task_file, 'r', encoding='utf-8') as f:
            return json.load(f)
    except Exception as e:
        print(f"加载任务文件失败 {task_file}: {e}")
        return None

def save_task_info(task_info, task_file):
    """
    保存任务信息到txt文件
    
    Args:
        task_info: 任务信息
        task_file: 任务文件路径
    """
    try:
        with open(task_file, 'w', encoding='utf-8') as f:
            json.dump(task_info, f, ensure_ascii=False, indent=2)
    except Exception as e:
        print(f"保存任务文件失败 {task_file}: {e}")

def query_task_status(task_id, max_retries=2, retry_delay=1):
    """
    查询任务状态（带重试机制）
    
    Args:
        task_id: 任务ID
        max_retries: 最大重试次数
        retry_delay: 重试间隔（秒）
    
    Returns:
        dict: 任务状态信息，失败返回None
    """
    for attempt in range(max_retries + 1):
        try:
            visual_service = VisualService()
            
            # 设置访问密钥
            visual_service.set_ak(IMAGE_TWO_CONFIG['access_key'])
            visual_service.set_sk(IMAGE_TWO_CONFIG['secret_key'])
            
            # 查询任务状态
            form = {
                "req_key": IMAGE_TWO_CONFIG['req_key'],
                "task_id": task_id
            }
            
            resp = visual_service.cv_sync2async_get_result(form)
            return resp
            
        except Exception as e:
            error_msg = str(e)
            if attempt == 0:
                print(f"查询任务状态失败 {task_id}: {error_msg}")
            else:
                print(f"重试查询任务状态 (第{attempt}次) {task_id}: {error_msg}")
            
            # 如果是访问被拒绝错误且还有重试机会，则重试
            if attempt < max_retries and ("Access Denied" in error_msg or "Internal Error" in error_msg):
                print(f"等待 {retry_delay} 秒后重试查询...")
                time.sleep(retry_delay)
                retry_delay *= 2  # 指数退避
                continue
            else:
                return None
    
    return None

def download_image(image_data_base64, output_path):
    """
    下载并保存图片
    
    Args:
        image_data_base64: base64编码的图片数据
        output_path: 输出文件路径
    
    Returns:
        bool: 是否成功保存
    """
    try:
        # 确保输出目录存在
        os.makedirs(os.path.dirname(output_path), exist_ok=True)
        
        # 解码并保存图片
        image_data = base64.b64decode(image_data_base64)
        with open(output_path, 'wb') as f:
            f.write(image_data)
        
        print(f"图片已保存: {output_path}")
        return True
        
    except Exception as e:
        print(f"保存图片失败 {output_path}: {e}")
        return False

def process_completed_task(task_info, task_file, resp_data):
    """
    处理已完成的任务
    
    Args:
        task_info: 任务信息
        task_file: 任务文件路径
        resp_data: 响应数据
    
    Returns:
        bool: 是否成功处理
    """
    try:
        if 'binary_data_base64' in resp_data and resp_data['binary_data_base64']:
            # 下载图片
            image_data = resp_data['binary_data_base64'][0]
            output_path = task_info['output_path']
            
            if download_image(image_data, output_path):
                # 更新任务状态
                task_info['status'] = 'completed'
                task_info['completed_time'] = time.time()
                save_task_info(task_info, task_file)
                
                print(f"✓ 任务完成: {task_info['filename']}")
                return True
            else:
                print(f"✗ 图片下载失败: {task_info['filename']}")
                return False
        else:
            print(f"✗ 响应中没有图片数据: {task_info['filename']}")
            return False
            
    except Exception as e:
        print(f"处理完成任务失败: {e}")
        return False

def process_failed_task(task_info, task_file, error_msg):
    """
    处理失败的任务
    
    Args:
        task_info: 任务信息
        task_file: 任务文件路径
        error_msg: 错误信息
    """
    task_info['status'] = 'failed'
    task_info['error_msg'] = error_msg
    task_info['failed_time'] = time.time()
    save_task_info(task_info, task_file)
    
    print(f"✗ 任务失败: {task_info['filename']} - {error_msg}")

def get_all_task_files(tasks_dir):
    """
    获取所有任务文件
    
    Args:
        tasks_dir: 任务目录
    
    Returns:
        list: 任务文件路径列表
    """
    if not os.path.exists(tasks_dir):
        return []
    
    task_files = []
    for filename in os.listdir(tasks_dir):
        if filename.endswith('.txt'):
            task_files.append(os.path.join(tasks_dir, filename))
    
    return task_files

def check_all_tasks(tasks_dir):
    """
    检查所有任务的状态
    
    Args:
        tasks_dir: 任务目录
    
    Returns:
        dict: 统计信息
    """
    task_files = get_all_task_files(tasks_dir)
    
    if not task_files:
        print(f"在目录 {tasks_dir} 中没有找到任务文件")
        return {'total': 0, 'pending': 0, 'completed': 0, 'failed': 0}
    
    stats = {
        'total': len(task_files),
        'pending': 0,
        'completed': 0,
        'failed': 0,
        'processing': 0
    }
    
    print(f"\n=== 检查 {len(task_files)} 个任务的状态 ===")
    
    for i, task_file in enumerate(task_files, 1):
        task_info = load_task_info(task_file)
        if not task_info:
            continue
        
        task_id = task_info.get('task_id')
        current_status = task_info.get('status', 'unknown')
        
        print(f"\n[{i}/{len(task_files)}] 检查任务: {task_info.get('filename', 'unknown')}")
        print(f"  Task ID: {task_id}")
        print(f"  当前状态: {current_status}")
        
        # 如果任务已经完成或失败，跳过查询
        if current_status in ['completed', 'failed']:
            stats[current_status] += 1
            print(f"  状态: {current_status} (跳过查询)")
            continue
        
        # 查询任务状态
        resp = query_task_status(task_id)
        if not resp:
            print(f"  查询失败")
            continue
        
        # 解析响应
        if 'data' in resp:
            data = resp['data']
            status = data.get('status', 'unknown')
            
            print(f"  API状态: {status}")
            
            if status == 'done':
                # 任务完成，下载图片
                if process_completed_task(task_info, task_file, data):
                    stats['completed'] += 1
                else:
                    stats['failed'] += 1
                    
            elif status == 'failed':
                # 任务失败
                error_msg = data.get('reason', '未知错误')
                process_failed_task(task_info, task_file, error_msg)
                stats['failed'] += 1
                
            elif status in ['pending', 'running']:
                # 任务进行中
                task_info['status'] = 'processing'
                save_task_info(task_info, task_file)
                stats['processing'] += 1
                print(f"  状态: 处理中...")
                
            else:
                # 其他状态
                print(f"  未知状态: {status}")
                stats['pending'] += 1
        else:
            print(f"  响应格式错误: {resp}")
            stats['pending'] += 1
        
        # 避免请求过于频繁
        time.sleep(0.5)
    
    return stats

def monitor_tasks(tasks_dir, check_interval=30):
    """
    持续监控任务状态直到所有任务完成
    
    Args:
        tasks_dir: 任务目录
        check_interval: 检查间隔（秒）
    """
    print(f"=== 开始监控异步任务 ===")
    print(f"任务目录: {tasks_dir}")
    print(f"检查间隔: {check_interval} 秒")
    
    round_count = 0
    
    while True:
        round_count += 1
        print(f"\n{'='*50}")
        print(f"第 {round_count} 轮检查 - {time.strftime('%Y-%m-%d %H:%M:%S')}")
        print(f"{'='*50}")
        
        stats = check_all_tasks(tasks_dir)
        
        print(f"\n=== 统计信息 ===")
        print(f"总任务数: {stats['total']}")
        print(f"已完成: {stats['completed']}")
        print(f"处理中: {stats['processing']}")
        print(f"等待中: {stats['pending']}")
        print(f"失败: {stats['failed']}")
        
        # 检查是否所有任务都已完成
        if stats['total'] > 0 and (stats['completed'] + stats['failed']) >= stats['total']:
            print(f"\n🎉 所有任务已完成！")
            print(f"成功: {stats['completed']} 个")
            print(f"失败: {stats['failed']} 个")
            print(f"成功率: {(stats['completed'] / stats['total'] * 100):.1f}%")
            break
        
        if stats['total'] == 0:
            print(f"\n没有找到任务文件，退出监控")
            break
        
        # 等待下一轮检查
        print(f"\n等待 {check_interval} 秒后进行下一轮检查...")
        time.sleep(check_interval)

def main():
    """
    主函数
    """
    parser = argparse.ArgumentParser(description='异步任务状态查询工具')
    parser.add_argument('--check-once', action='store_true', help='检查一次所有任务状态后退出')
    parser.add_argument('--monitor', action='store_true', help='持续监控任务状态')
    parser.add_argument('--interval', type=int, default=30, help='监控间隔（秒，默认30）')
    parser.add_argument('--tasks-dir', default='async_tasks', help='任务目录路径')
    
    args = parser.parse_args()
    tasks_dir = args.tasks_dir
    
    if not os.path.exists(tasks_dir):
        print(f"任务目录不存在: {tasks_dir}")
        print(f"请先运行图片生成脚本提交任务")
        return
    
    print(f"异步任务状态查询工具")
    print(f"任务目录: {tasks_dir}")
    
    if args.check_once:
        # 单次检查
        stats = check_all_tasks(tasks_dir)
        print(f"\n=== 检查完成 ===")
        print(f"总任务数: {stats['total']}")
        print(f"已完成: {stats['completed']}")
        print(f"处理中: {stats['processing']}")
        print(f"等待中: {stats['pending']}")
        print(f"失败: {stats['failed']}")
        
    elif args.monitor:
        # 持续监控
        monitor_tasks(tasks_dir, args.interval)
        
    else:
        # 交互式模式
        print(f"\n请选择运行模式:")
        print(f"1. 检查一次所有任务状态")
        print(f"2. 持续监控直到所有任务完成")
        
        choice = input(f"\n请输入选择 (1/2): ").strip()
        
        if choice == '1':
            # 单次检查
            stats = check_all_tasks(tasks_dir)
            print(f"\n=== 检查完成 ===")
            print(f"总任务数: {stats['total']}")
            print(f"已完成: {stats['completed']}")
            print(f"处理中: {stats['processing']}")
            print(f"等待中: {stats['pending']}")
            print(f"失败: {stats['failed']}")
            
        elif choice == '2':
            # 持续监控
            check_interval = input(f"\n请输入检查间隔（秒，默认30）: ").strip()
            try:
                check_interval = int(check_interval) if check_interval else 30
            except ValueError:
                check_interval = 30
            
            monitor_tasks(tasks_dir, check_interval)
            
        else:
            print(f"无效选择，退出")

if __name__ == '__main__':
    main()