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
import urllib.request
from config.config import IMAGE_TWO_CONFIG, ARK_CONFIG
from volcengine.visual.VisualService import VisualService
from volcenginesdkarkruntime import Ark

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

def query_image_task_status(task_id, max_retries=2, retry_delay=1):
    """
    查询图片任务状态（带重试机制）
    
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
                print(f"查询图片任务状态失败 {task_id}: {error_msg}")
            else:
                print(f"重试查询图片任务状态 (第{attempt}次) {task_id}: {error_msg}")
            
            # 如果是访问被拒绝错误且还有重试机会，则重试
            if attempt < max_retries and ("Access Denied" in error_msg or "Internal Error" in error_msg):
                print(f"等待 {retry_delay} 秒后重试查询...")
                time.sleep(retry_delay)
                retry_delay *= 2  # 指数退避
                continue
            else:
                return None
    
    return None

def query_video_task_status(task_id, max_retries=2, retry_delay=1):
    """
    查询视频任务状态（带重试机制）
    
    Args:
        task_id: 任务ID
        max_retries: 最大重试次数
        retry_delay: 重试间隔（秒）
    
    Returns:
        dict: 任务状态信息，失败返回None
    """
    for attempt in range(max_retries + 1):
        try:
            client = Ark(api_key=ARK_CONFIG["api_key"])
            
            # 查询任务状态
            resp = client.content_generation.tasks.get(task_id=task_id)
            return resp
            
        except Exception as e:
            error_msg = str(e)
            if attempt == 0:
                print(f"查询视频任务状态失败 {task_id}: {error_msg}")
            else:
                print(f"重试查询视频任务状态 (第{attempt}次) {task_id}: {error_msg}")
            
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

def download_video(video_url, output_path):
    """
    下载视频文件
    
    Args:
        video_url: 视频URL
        output_path: 输出文件路径
    
    Returns:
        bool: 是否成功下载
    """
    try:
        # 确保输出目录存在
        os.makedirs(os.path.dirname(output_path), exist_ok=True)
        
        print(f"开始下载视频: {video_url}")
        urllib.request.urlretrieve(video_url, output_path)
        print(f"视频已保存: {output_path}")
        return True
        
    except Exception as e:
        print(f"下载视频失败 {output_path}: {e}")
        return False

def move_task_to_done(task_file, done_tasks_dir='done_tasks'):
    """
    将任务文件移动到done_tasks目录
    
    Args:
        task_file: 任务文件路径
        done_tasks_dir: 完成任务目录
    
    Returns:
        bool: 是否成功移动
    """
    try:
        # 确保done_tasks目录存在
        os.makedirs(done_tasks_dir, exist_ok=True)
        
        # 获取文件名
        filename = os.path.basename(task_file)
        done_task_path = os.path.join(done_tasks_dir, filename)
        
        # 移动文件
        os.rename(task_file, done_task_path)
        print(f"✓ 任务文件已移动到done_tasks: {filename}")
        return True
        
    except Exception as e:
        print(f"移动任务文件失败: {e}")
        return False

def process_completed_image_task(task_info, task_file, resp_data):
    """
    处理已完成的图片任务
    
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
                
                print(f"✓ 图片任务完成: {task_info['filename']}")
                
                # 将任务文件移动到done_tasks目录
                if move_task_to_done(task_file):
                    return True
                else:
                    print(f"警告: 图片下载成功但任务文件移动失败: {task_info['filename']}")
                    return True  # 图片已下载，认为任务成功
            else:
                print(f"✗ 图片下载失败: {task_info['filename']}")
                return False
        else:
            print(f"✗ 响应中没有图片数据: {task_info['filename']}")
            return False
            
    except Exception as e:
        print(f"处理完成图片任务失败: {e}")
        return False

def process_completed_video_task(task_info, task_file, resp):
    """
    处理已完成的视频任务
    
    Args:
        task_info: 任务信息
        task_file: 任务文件路径
        resp: 响应对象
    
    Returns:
        bool: 是否成功处理
    """
    try:
        if hasattr(resp, 'content') and hasattr(resp.content, 'video_url'):
            # 下载视频
            video_url = resp.content.video_url
            output_path = task_info['output_path']
            
            if download_video(video_url, output_path):
                # 更新任务状态
                task_info['status'] = 'completed'
                task_info['completed_time'] = time.time()
                save_task_info(task_info, task_file)
                
                print(f"✓ 视频任务完成: {task_info['filename']}")
                
                # 将任务文件移动到done_tasks目录
                if move_task_to_done(task_file):
                    return True
                else:
                    print(f"警告: 视频下载成功但任务文件移动失败: {task_info['filename']}")
                    return True  # 视频已下载，认为任务成功
            else:
                print(f"✗ 视频下载失败: {task_info['filename']}")
                return False
        else:
            print(f"✗ 响应中没有视频数据: {task_info['filename']}")
            return False
            
    except Exception as e:
        print(f"处理完成视频任务失败: {e}")
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
        return {'total': 0, 'pending': 0, 'completed': 0, 'failed': 0, 'processing': 0}
    
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
        
        # 根据任务类型查询状态
        task_type = task_info.get('task_type', 'image')  # 默认为图片任务
        
        if task_type == 'video':
            # 视频任务
            resp = query_video_task_status(task_id)
            if not resp:
                print(f"  查询失败")
                continue
            
            # 解析视频任务响应
            status = resp.status
            print(f"  API状态: {status}")
            
            if status == 'succeeded':
                # 任务完成，下载视频
                if process_completed_video_task(task_info, task_file, resp):
                    stats['completed'] += 1
                else:
                    stats['failed'] += 1
                    
            elif status == 'failed':
                # 任务失败
                error_msg = getattr(resp, 'error', '未知错误')
                process_failed_task(task_info, task_file, str(error_msg))
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
            # 图片任务
            resp = query_image_task_status(task_id)
            if not resp:
                print(f"  查询失败")
                continue
            
            # 解析图片任务响应
            if 'data' in resp:
                data = resp['data']
                status = data.get('status', 'unknown')
                
                print(f"  API状态: {status}")
                
                if status == 'done':
                    # 任务完成，下载图片
                    if process_completed_image_task(task_info, task_file, data):
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

def process_chapter_async_tasks(chapter_dir):
    """
    处理单个章节目录下的异步任务
    
    Args:
        chapter_dir: 章节目录路径
    
    Returns:
        dict: 处理统计信息
    """
    async_tasks_dir = os.path.join(chapter_dir, 'async_tasks')
    
    if not os.path.exists(async_tasks_dir):
        return {'total': 0, 'success': 0, 'failed': 0, 'images_moved': 0}
    
    # 创建目标目录
    done_dir = os.path.join(chapter_dir, 'done')
    failed_dir = os.path.join(chapter_dir, 'failed')
    images_dir = os.path.join(chapter_dir, 'images')
    
    os.makedirs(done_dir, exist_ok=True)
    os.makedirs(failed_dir, exist_ok=True)
    os.makedirs(images_dir, exist_ok=True)
    
    stats = {'total': 0, 'success': 0, 'failed': 0, 'images_moved': 0}
    
    try:
        for filename in os.listdir(async_tasks_dir):
            file_path = os.path.join(async_tasks_dir, filename)
            
            # 跳过目录
            if os.path.isdir(file_path):
                continue
            
            # 处理图片文件
            if filename.lower().endswith(('.jpg', '.jpeg', '.png', '.gif', '.bmp', '.webp')):
                try:
                    target_path = os.path.join(images_dir, filename)
                    os.rename(file_path, target_path)
                    stats['images_moved'] += 1
                    print(f"✓ 图片文件已移动: {filename} -> images/")
                except Exception as e:
                    print(f"✗ 移动图片文件失败 {filename}: {e}")
                continue
            
            # 处理txt文件
            if filename.endswith('.txt'):
                stats['total'] += 1
                
                try:
                    # 加载任务信息
                    task_info = load_task_info(file_path)
                    if not task_info:
                        # 无法加载任务信息，移动到失败目录
                        target_path = os.path.join(failed_dir, filename)
                        os.rename(file_path, target_path)
                        stats['failed'] += 1
                        print(f"✗ 任务文件格式错误，已移动到failed: {filename}")
                        continue
                    
                    # 检查任务状态
                    task_status = task_info.get('status', 'unknown')
                    
                    if task_status == 'completed':
                        # 任务已完成，移动到done目录
                        target_path = os.path.join(done_dir, filename)
                        os.rename(file_path, target_path)
                        stats['success'] += 1
                        print(f"✓ 已完成任务已移动到done: {filename}")
                    elif task_status == 'failed':
                        # 任务失败，移动到failed目录
                        target_path = os.path.join(failed_dir, filename)
                        os.rename(file_path, target_path)
                        stats['failed'] += 1
                        print(f"✗ 失败任务已移动到failed: {filename}")
                    else:
                        # 任务还在处理中，查询最新状态
                        task_id = task_info.get('task_id')
                        task_type = task_info.get('task_type', 'image')
                        
                        if task_type == 'video':
                            resp = query_video_task_status(task_id)
                            if resp and resp.status == 'succeeded':
                                # 处理完成的视频任务
                                if process_completed_video_task(task_info, file_path, resp):
                                    target_path = os.path.join(done_dir, filename)
                                    if os.path.exists(file_path):
                                        os.rename(file_path, target_path)
                                    stats['success'] += 1
                                else:
                                    target_path = os.path.join(failed_dir, filename)
                                    os.rename(file_path, target_path)
                                    stats['failed'] += 1
                            elif resp and resp.status == 'failed':
                                # 任务失败
                                error_msg = getattr(resp, 'error', '未知错误')
                                process_failed_task(task_info, file_path, str(error_msg))
                                target_path = os.path.join(failed_dir, filename)
                                os.rename(file_path, target_path)
                                stats['failed'] += 1
                            else:
                                # 任务还在处理中，保持原位置
                                print(f"⏳ 视频任务处理中: {filename}")
                        else:
                            # 图片任务
                            resp = query_image_task_status(task_id)
                            if resp and 'data' in resp:
                                data = resp['data']
                                status = data.get('status', 'unknown')
                                
                                if status == 'done':
                                    # 处理完成的图片任务
                                    if process_completed_image_task(task_info, file_path, data):
                                        target_path = os.path.join(done_dir, filename)
                                        if os.path.exists(file_path):
                                            os.rename(file_path, target_path)
                                        stats['success'] += 1
                                    else:
                                        target_path = os.path.join(failed_dir, filename)
                                        os.rename(file_path, target_path)
                                        stats['failed'] += 1
                                elif status == 'failed':
                                    # 任务失败
                                    error_msg = data.get('reason', '未知错误')
                                    process_failed_task(task_info, file_path, error_msg)
                                    target_path = os.path.join(failed_dir, filename)
                                    os.rename(file_path, target_path)
                                    stats['failed'] += 1
                                else:
                                    # 任务还在处理中，保持原位置
                                    print(f"⏳ 图片任务处理中: {filename}")
                            else:
                                # 查询失败，保持原位置
                                print(f"⚠️ 查询任务状态失败: {filename}")
                    
                except Exception as e:
                    print(f"✗ 处理任务文件失败 {filename}: {e}")
                    try:
                        target_path = os.path.join(failed_dir, filename)
                        os.rename(file_path, target_path)
                        stats['failed'] += 1
                    except Exception as move_e:
                        print(f"✗ 移动失败文件也失败 {filename}: {move_e}")
    
    except Exception as e:
        print(f"✗ 处理章节目录失败 {chapter_dir}: {e}")
    
    return stats

def process_all_data_directories(data_dir='data'):
    """
    处理所有数据目录下的异步任务
    
    Args:
        data_dir: 数据根目录路径
    
    Returns:
        dict: 总体统计信息
    """
    if not os.path.exists(data_dir):
        print(f"数据目录不存在: {data_dir}")
        return {'total_chapters': 0, 'total_tasks': 0, 'total_success': 0, 'total_failed': 0, 'total_images': 0}
    
    total_stats = {
        'total_chapters': 0,
        'total_tasks': 0,
        'total_success': 0,
        'total_failed': 0,
        'total_images': 0
    }
    
    print(f"=== 开始处理数据目录: {data_dir} ===")
    
    # 遍历所有00x子文件夹
    for item in os.listdir(data_dir):
        item_path = os.path.join(data_dir, item)
        
        # 跳过非目录项
        if not os.path.isdir(item_path):
            continue
        
        # 检查是否是00x格式的目录
        if not (item.startswith('00') and len(item) == 3 and item[2:].isdigit()):
            continue
        
        print(f"\n--- 处理数据集: {item} ---")
        
        # 遍历chapter_xxx子文件夹
        try:
            for chapter_item in os.listdir(item_path):
                chapter_path = os.path.join(item_path, chapter_item)
                
                # 跳过非目录项
                if not os.path.isdir(chapter_path):
                    continue
                
                # 检查是否是chapter_xxx格式的目录
                if not chapter_item.startswith('chapter_'):
                    continue
                
                print(f"\n处理章节: {item}/{chapter_item}")
                total_stats['total_chapters'] += 1
                
                # 处理该章节的异步任务
                chapter_stats = process_chapter_async_tasks(chapter_path)
                
                # 累计统计
                total_stats['total_tasks'] += chapter_stats['total']
                total_stats['total_success'] += chapter_stats['success']
                total_stats['total_failed'] += chapter_stats['failed']
                total_stats['total_images'] += chapter_stats['images_moved']
                
                print(f"  章节统计: 任务{chapter_stats['total']}个, 成功{chapter_stats['success']}个, 失败{chapter_stats['failed']}个, 图片{chapter_stats['images_moved']}个")
                
        except Exception as e:
            print(f"✗ 处理数据集失败 {item}: {e}")
    
    return total_stats

def monitor_all_data_directories(data_dir='data', check_interval=30):
    """
    持续监控所有数据目录下的异步任务
    
    Args:
        data_dir: 数据根目录路径
        check_interval: 检查间隔（秒）
    """
    if not os.path.exists(data_dir):
        print(f"数据目录不存在: {data_dir}")
        return
    
    print(f"=== 开始持续监控数据目录: {data_dir} ===")
    
    try:
        while True:
            print(f"\n{time.strftime('%Y-%m-%d %H:%M:%S')} - 开始检查所有数据目录...")
            
            total_stats = process_all_data_directories(data_dir)
            
            print(f"\n=== 本轮检查完成 ===")
            print(f"处理章节数: {total_stats['total_chapters']}")
            print(f"总任务数: {total_stats['total_tasks']}")
            print(f"成功处理: {total_stats['total_success']}")
            print(f"失败处理: {total_stats['total_failed']}")
            print(f"图片移动: {total_stats['total_images']}")
            if total_stats['total_tasks'] > 0:
                success_rate = (total_stats['total_success'] / total_stats['total_tasks'] * 100)
                print(f"成功率: {success_rate:.1f}%")
            
            print(f"\n等待 {check_interval} 秒后进行下一轮检查...")
            time.sleep(check_interval)
            
    except KeyboardInterrupt:
        print(f"\n\n监控已停止")
    except Exception as e:
        print(f"\n监控过程中发生错误: {e}")
        print(f"等待 {check_interval} 秒后重试...")
        time.sleep(check_interval)
        # 递归重新开始监控
        monitor_all_data_directories(data_dir, check_interval)

def main():
    """
    主函数 - 默认启用--process-all --monitor模式，持续监控所有数据目录
    """
    parser = argparse.ArgumentParser(description='异步任务状态查询工具 - 默认持续监控所有数据目录')
    parser.add_argument('--check-once', action='store_true', help='检查一次所有任务状态后退出')
    parser.add_argument('--monitor', action='store_true', help='持续监控任务状态')
    parser.add_argument('--interval', type=int, default=30, help='监控间隔（秒，默认30）')
    parser.add_argument('--tasks-dir', default='async_tasks', help='任务目录路径')
    parser.add_argument('--process-all', action='store_true', help='处理所有数据目录下的异步任务')
    parser.add_argument('--data-dir', default='data', help='数据根目录路径')
    parser.add_argument('--legacy-mode', action='store_true', help='使用旧版交互模式')
    
    args = parser.parse_args()
    
    # 如果没有指定任何参数，默认启用--process-all --monitor模式
    if not any([args.check_once, args.monitor, args.process_all, args.legacy_mode]):
        args.process_all = True
        args.monitor = True
        print("默认模式：持续监控所有数据目录下的异步任务")
    
    if args.process_all:
        # 处理所有数据目录下的异步任务
        data_dir = args.data_dir
        print(f"异步任务批量处理工具")
        print(f"数据目录: {data_dir}")
        
        if args.monitor:
            # 持续监控模式
            print(f"监控间隔: {args.interval}秒")
            print(f"按 Ctrl+C 停止监控\n")
            monitor_all_data_directories(data_dir, args.interval)
        else:
            # 单次处理模式
            total_stats = process_all_data_directories(data_dir)
            
            print(f"\n=== 处理完成 ===")
            print(f"处理章节数: {total_stats['total_chapters']}")
            print(f"总任务数: {total_stats['total_tasks']}")
            print(f"成功处理: {total_stats['total_success']}")
            print(f"失败处理: {total_stats['total_failed']}")
            print(f"图片移动: {total_stats['total_images']}")
            if total_stats['total_tasks'] > 0:
                success_rate = (total_stats['total_success'] / total_stats['total_tasks'] * 100)
                print(f"成功率: {success_rate:.1f}%")
        
        return
    
    # 原有功能
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
        
    elif args.legacy_mode:
        # 交互式模式（旧版模式）
        print(f"\n请选择运行模式:")
        print(f"1. 检查一次所有任务状态")
        print(f"2. 持续监控直到所有任务完成")
        print(f"3. 处理所有数据目录下的异步任务")
        
        choice = input(f"\n请输入选择 (1/2/3): ").strip()
        
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
            
        elif choice == '3':
            # 处理所有数据目录下的异步任务
            data_dir = input(f"\n请输入数据目录路径（默认data）: ").strip()
            data_dir = data_dir if data_dir else 'data'
            
            total_stats = process_all_data_directories(data_dir)
            
            print(f"\n=== 处理完成 ===")
            print(f"处理章节数: {total_stats['total_chapters']}")
            print(f"总任务数: {total_stats['total_tasks']}")
            print(f"成功处理: {total_stats['total_success']}")
            print(f"失败处理: {total_stats['total_failed']}")
            print(f"图片移动: {total_stats['total_images']}")
            if total_stats['total_tasks'] > 0:
                success_rate = (total_stats['total_success'] / total_stats['total_tasks'] * 100)
                print(f"成功率: {success_rate:.1f}%")
            
        else:
            print(f"无效选择，退出")
    
    else:
        # 如果没有匹配任何参数，显示帮助信息
        print(f"使用 --help 查看所有可用选项")
        print(f"默认模式：持续监控所有数据目录下的异步任务")
        print(f"使用 --legacy-mode 进入交互模式")

if __name__ == '__main__':
    main()