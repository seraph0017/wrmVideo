#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
异步视频生成脚本
遍历每个章节目录，使用每个章节的第一张和第二张图片异步生成视频
任务提交后将task_id保存到async_tasks目录，由check_async_tasks.py负责下载
"""

import os
import sys
import time
import json
import base64
from volcenginesdkarkruntime import Ark

# 添加config目录到路径
config_dir = os.path.join(os.path.dirname(__file__), 'config')
sys.path.insert(0, config_dir)

# 导入配置
from config import ARK_CONFIG, IMAGE_TO_VIDEO_CONFIG

def upload_image_to_server(image_path):
    """
    将图片转换为base64编码的data URL
    
    Args:
        image_path: 图片路径
    
    Returns:
        str: base64编码的data URL，失败返回None
    """
    try:
        print(f"处理图片: {image_path}")
        
        # 读取图片文件并转换为base64
        with open(image_path, 'rb') as image_file:
            image_data = image_file.read()
            base64_encoded = base64.b64encode(image_data).decode('utf-8')
        
        # 根据文件扩展名确定MIME类型
        file_ext = os.path.splitext(image_path)[1].lower()
        if file_ext in ['.jpg', '.jpeg']:
            mime_type = 'image/jpeg'
        elif file_ext == '.png':
            mime_type = 'image/png'
        elif file_ext == '.gif':
            mime_type = 'image/gif'
        elif file_ext == '.bmp':
            mime_type = 'image/bmp'
        else:
            mime_type = 'image/jpeg'  # 默认使用jpeg
        
        # 返回data URL格式
        data_url = f"data:{mime_type};base64,{base64_encoded}"
        print(f"图片转换成功: {os.path.basename(image_path)}")
        return data_url
        
    except Exception as e:
        print(f"处理图片时发生错误: {e}")
        return None

def save_task_info(task_id, task_info, tasks_dir):
    """
    保存任务信息到txt文件
    
    Args:
        task_id: 任务ID
        task_info: 任务信息
        tasks_dir: 任务文件保存目录
    """
    task_file = os.path.join(tasks_dir, f"{task_id}.txt")
    
    # 确保目录存在
    os.makedirs(tasks_dir, exist_ok=True)
    
    # 保存任务信息
    with open(task_file, 'w', encoding='utf-8') as f:
        json.dump(task_info, f, ensure_ascii=False, indent=2)
    
    print(f"任务信息已保存: {task_file}")

def create_video_from_single_image_async(image_path, duration, output_path, max_retries=3):
    """
    使用单张图片异步生成视频，带重试机制
    
    Args:
        image_path: 图片路径
        duration: 视频时长
        output_path: 输出视频路径
        max_retries: 最大重试次数
    
    Returns:
        bool: 是否成功提交任务
    """
    # 检查视频是否已存在
    if os.path.exists(output_path):
        print(f"✓ 视频已存在，跳过生成: {os.path.basename(output_path)}")
        return True
    
    for attempt in range(max_retries + 1):
        try:
            if attempt > 0:
                print(f"🔄 第 {attempt} 次重试生成视频: {os.path.basename(output_path)}")
                time.sleep(2 * attempt)  # 递增延迟
            
            print(f"开始生成视频: {image_path}")
            
            # 将图片转换为base64编码的data URL
            image_url = upload_image_to_server(image_path)
            
            if not image_url:
                print("图片处理失败")
                if attempt == max_retries:
                    return False
                continue
            
            # 创建视频生成任务
            client = Ark(api_key=ARK_CONFIG["api_key"])
            
            resp = client.content_generation.tasks.create(
                model="doubao-seedance-1-0-lite-i2v-250428",
                content=[
                    {
                        "type": "text",
                        "text": f"画面有轻微的动态效果，保持画面稳定 --ratio adaptive --dur {duration}"
                    },
                    {
                        "type": "image_url",
                        "image_url": {
                            "url": image_url
                        }
                    }
                ]
            )
            
            task_id = resp.id
            print(f"✓ 视频生成任务提交成功，Task ID: {task_id}")
            
            # 保存任务信息到async_tasks目录
            task_info = {
                'task_id': task_id,
                'task_type': 'video',  # 标识为视频任务
                'output_path': output_path,
                'filename': os.path.basename(output_path),
                'image_path': image_path,
                'duration': duration,
                'submit_time': time.time(),
                'status': 'submitted',
                'attempt': attempt + 1
            }
            
            # 使用统一的保存函数
            async_tasks_dir = 'async_tasks'
            save_task_info(task_id, task_info, async_tasks_dir)
            return True
            
        except Exception as e:
            print(f"✗ 生成视频时发生错误 (尝试 {attempt + 1}/{max_retries + 1}): {e}")
            
            if attempt == max_retries:
                print(f"✗ 达到最大重试次数，任务最终失败")
                return False
            
            # 继续下一次重试
            continue
    
    return False

def get_chapter_images(chapter_path):
    """
    获取章节目录中的前两张图片
    优先查找特定命名格式：chapter_XXX_image_01_1.jpeg 和 chapter_XXX_image_01_2.jpeg
    如果找不到，则回退到原来的逻辑
    
    Args:
        chapter_path: 章节目录路径
    
    Returns:
        tuple: (第一张图片路径, 第二张图片路径) 或 (None, None)
    """
    try:
        chapter_name = os.path.basename(chapter_path)
        
        # 优先查找特定命名格式的图片
        first_image_name = f"{chapter_name}_image_01_1.jpeg"
        second_image_name = f"{chapter_name}_image_01_2.jpeg"
        
        first_image_path = os.path.join(chapter_path, first_image_name)
        second_image_path = os.path.join(chapter_path, second_image_name)
        
        if os.path.exists(first_image_path) and os.path.exists(second_image_path):
            print(f"找到特定命名格式的图片: {first_image_name}, {second_image_name}")
            return first_image_path, second_image_path
        
        # 如果找不到特定命名格式，回退到原来的逻辑
        print(f"未找到特定命名格式的图片，使用通用查找方式")
        
        # 获取目录中的所有图片文件
        image_extensions = ['.jpg', '.jpeg', '.png', '.bmp', '.gif']
        image_files = []
        
        for file in os.listdir(chapter_path):
            if any(file.lower().endswith(ext) for ext in image_extensions):
                image_files.append(os.path.join(chapter_path, file))
        
        # 按文件名排序
        image_files.sort()
        
        if len(image_files) >= 2:
            return image_files[0], image_files[1]
        elif len(image_files) == 1:
            print(f"警告: 章节 {chapter_path} 只有一张图片，无法生成视频")
            return None, None
        else:
            print(f"警告: 章节 {chapter_path} 没有找到图片文件")
            return None, None
            
    except Exception as e:
        print(f"获取章节图片时发生错误: {e}")
        return None, None

def generate_videos_for_chapter(chapter_dir):
    """
    为单个章节生成视频
    
    Args:
        chapter_dir: 章节目录路径
    
    Returns:
        bool: 是否成功提交所有任务
    """
    try:
        chapter_name = os.path.basename(chapter_dir)
        print(f"\n=== 处理章节: {chapter_name} ===")
        
        # 获取章节的前两张图片
        first_image, second_image = get_chapter_images(chapter_dir)
        
        if not first_image or not second_image:
            print(f"✗ 章节 {chapter_name} 跳过，图片不足")
            return False
        
        # 生成两个视频的输出路径
        first_video_path = os.path.join(chapter_dir, f"{chapter_name}_video_1.mp4")
        second_video_path = os.path.join(chapter_dir, f"{chapter_name}_video_2.mp4")
        
        # 默认每个视频5秒时长
        duration = 5
        
        success_count = 0
        
        # 生成第一个视频
        print(f"\n提交第一个视频生成任务...")
        if create_video_from_single_image_async(first_image, duration, first_video_path):
            success_count += 1
        
        # 生成第二个视频
        print(f"\n提交第二个视频生成任务...")
        if create_video_from_single_image_async(second_image, duration, second_video_path):
            success_count += 1
        
        if success_count == 2:
            print(f"✓ 章节 {chapter_name} 所有视频任务提交成功")
            return True
        elif success_count == 1:
            print(f"⚠ 章节 {chapter_name} 部分视频任务提交成功")
            return True
        else:
            print(f"✗ 章节 {chapter_name} 所有视频任务提交失败")
            return False
        
    except Exception as e:
        print(f"处理章节 {chapter_dir} 时发生错误: {e}")
        return False

def process_chapters(data_dir):
    """
    处理所有章节目录，为每个章节生成视频
    
    Args:
        data_dir: 数据目录路径
    """
    try:
        if not os.path.exists(data_dir):
            print(f"错误: 数据目录不存在: {data_dir}")
            return
        
        # 获取所有章节目录
        chapter_dirs = []
        for item in os.listdir(data_dir):
            item_path = os.path.join(data_dir, item)
            if os.path.isdir(item_path) and item.startswith('chapter'):
                chapter_dirs.append(item_path)
        
        # 按章节名称排序
        chapter_dirs.sort()
        
        if not chapter_dirs:
            print(f"警告: 在 {data_dir} 中没有找到章节目录")
            return
        
        print(f"找到 {len(chapter_dirs)} 个章节目录")
        
        success_count = 0
        total_tasks = 0
        
        # 处理每个章节
        for chapter_dir in chapter_dirs:
            if generate_videos_for_chapter(chapter_dir):
                success_count += 1
            total_tasks += 2  # 每个章节生成2个视频
        
        print(f"\n=== 处理完成 ===")
        print(f"成功处理章节: {success_count}/{len(chapter_dirs)}")
        print(f"预计生成视频任务: {total_tasks} 个")
        print(f"\n请运行以下命令监控任务状态:")
        print(f"python check_async_tasks.py --monitor")
        
    except Exception as e:
        print(f"处理章节时发生错误: {e}")

def main():
    """
    主函数
    """
    import argparse
    
    parser = argparse.ArgumentParser(description='异步视频生成工具')
    parser.add_argument('data_dir', help='数据目录路径，例如: data/001')
    parser.add_argument('--tasks-dir', default='async_tasks', help='异步任务目录路径')
    
    args = parser.parse_args()
    
    data_dir = args.data_dir
    async_tasks_dir = args.tasks_dir
    
    print(f"开始异步处理数据目录: {data_dir}")
    print("注意: 请确保已正确配置 ARK_CONFIG 中的 api_key")
    
    if not os.path.exists(data_dir):
        print(f"错误: 数据目录不存在: {data_dir}")
        sys.exit(1)
    
    # 确保async_tasks目录存在
    os.makedirs(async_tasks_dir, exist_ok=True)
    
    # 处理所有章节
    process_chapters(data_dir)
    
    print("\n=== 异步视频生成任务提交完成 ===")
    print("请使用 check_async_tasks.py 监控任务状态并下载完成的视频")
    print("例如: python check_async_tasks.py --monitor")

if __name__ == "__main__":
    main()