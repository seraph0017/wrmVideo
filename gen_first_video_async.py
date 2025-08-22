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
import random
import imghdr
from volcenginesdkarkruntime import Ark

# 添加config目录到路径
config_dir = os.path.join(os.path.dirname(__file__), 'config')
sys.path.insert(0, config_dir)

# 导入配置
from config import ARK_CONFIG, IMAGE_TO_VIDEO_CONFIG

def find_sound_effect(text, work_dir):
    """
    根据字幕文本匹配音效文件
    
    Args:
        text: 字幕文本
        work_dir: 工作目录
    
    Returns:
        str: 音效文件路径，未找到返回None
    """
    # 音效关键词映射
    sound_keywords = {
        # 动作类
        '脚步': ['action/footsteps_normal.wav'],
        '走': ['action/footsteps_normal.wav'],
        '跑': ['action/footsteps_normal.wav'],
        '门': ['action/door_open.wav', 'action/door_close.wav'],
        '开门': ['action/door_open.wav'],
        '关门': ['action/door_close.wav'],
        '衣服': ['action/cloth_rustle.wav'],
        '纸': ['action/paper_rustle.mp3'],
        '水': ['action/water_splash.wav'],
        '玻璃': ['action/glass_break.mp3'],
        
        # 战斗类
        '打': ['combat/punch_impact.wav'],
        '击': ['combat/punch_impact.wav'],
        '剑': ['combat/sword_clash.wav'],
        '箭': ['combat/arrow_whoosh.wav'],
        '爆炸': ['combat/explosion_large.wav', 'combat/explosion_small.wav'],
        
        # 情感类
        '心跳': ['emotion/heartbeat_normal.mp3'],
        '紧张': ['emotion/tension_build.mp3'],
        # 移除人声音效：'笑': ['emotion/laugh_gentle.wav'],
        
        # 环境类
        '鸟': ['environment/birds_chirping.wav'],
        '风': ['environment/wind_gentle.wav', 'environment/wind_strong.wav'],
        '雨': ['environment/rain_light.wav', 'environment/rain_heavy.wav'],
        '雷': ['environment/thunder.wav'],
        '火': ['environment/fire_crackling.wav'],
        '森林': ['environment/forest_ambient.wav'],
        '城市': ['environment/city_ambient.wav'],
        '市场': ['environment/marketplace_ambient.wav'],
        # 移除人声音效：'人群': ['environment/crowd_murmur.WAV'],
        '夜': ['environment/night_crickets.wav'],
        '山': ['environment/mountain_wind.wav'],
        '流水': ['environment/water_flowing.wav'],
        
        # 杂项
        '铃': ['misc/bell.wav', 'misc/bell_ring.wav'],
        '钟': ['misc/bell.wav', 'misc/bell_ring.wav'],
        '马': ['misc/horse.wav'],
        '车': ['misc/carriage_wheels.wav'],
        '钱': ['misc/coin_drop.wav']
    }
    
    # 优先搜索路径
    primary_sound_dir = os.path.join(work_dir, 'src', 'sound_effects')
    secondary_sound_dir = os.path.join(work_dir, 'sound')
    
    # 遍历关键词匹配
    for keyword, sound_files in sound_keywords.items():
        if keyword in text:
            # 在每个音效文件中查找
            for sound_file in sound_files:
                # 优先在 src/sound_effects 中查找
                primary_path = os.path.join(primary_sound_dir, sound_file)
                if os.path.exists(primary_path):
                    print(f"匹配音效: '{keyword}' -> {primary_path}")
                    return primary_path
                
                # 在 sound 目录中递归查找
                sound_filename = os.path.basename(sound_file)
                for root, dirs, files in os.walk(secondary_sound_dir):
                    for file in files:
                        if file.lower() == sound_filename.lower():
                            secondary_path = os.path.join(root, file)
                            print(f"匹配音效: '{keyword}' -> {secondary_path}")
                            return secondary_path
    
    return None

def get_sound_effects_for_first_video(chapter_path, work_dir):
    """
    为第一个视频获取音效列表，参考concat_narration_video.py中的逻辑
    
    Args:
        chapter_path: 章节目录路径
        work_dir: 工作目录
    
    Returns:
        list: 音效信息列表，每个元素包含 {'path': 音效路径, 'start_time': 开始时间, 'duration': 持续时间, 'volume': 音量}
    """
    sound_effects = []
    
    # 检查是否为第一个章节（chapter_001）
    chapter_name = os.path.basename(chapter_path)
    is_first_chapter = chapter_name.endswith('_001') or chapter_name == 'chapter_001'
    
    if is_first_chapter:
        # 第一个章节从第3秒开始使用铃声
        bell_path = os.path.join(work_dir, 'src', 'sound_effects', 'misc', 'bell_ring.wav')
        if os.path.exists(bell_path):
            sound_effects.append({
                'path': bell_path,
                'start_time': 3,
                'duration': 5,
                'volume': 0.5
            })
            print(f"添加铃声音效: {bell_path}")
    
    # 尝试读取narration文件来匹配音效
    narration_file = os.path.join(chapter_path, 'narration_01.txt')
    if os.path.exists(narration_file):
        try:
            with open(narration_file, 'r', encoding='utf-8') as f:
                narration_content = f.read()
            
            # 简单的文本分析，为关键词添加音效
            effect_path = find_sound_effect(narration_content, work_dir)
            if effect_path:
                # 如果是第一个章节，音效从8秒后开始，避免与铃声重叠
                start_time = 8 if is_first_chapter else 0
                sound_effects.append({
                    'path': effect_path,
                    'start_time': start_time,
                    'duration': 3,
                    'volume': 0.5
                })
                print(f"添加匹配音效: {effect_path}")
        except Exception as e:
            print(f"读取narration文件失败: {e}")
    
    # 如果没有找到任何音效，添加默认的脚步声（除了第一个章节的前8秒）
    if not sound_effects or (is_first_chapter and len(sound_effects) == 1):
        footsteps_path = os.path.join(work_dir, 'src', 'sound_effects', 'action', 'footsteps_normal.wav')
        if os.path.exists(footsteps_path):
            start_time = 8 if is_first_chapter else 0
            sound_effects.append({
                'path': footsteps_path,
                'start_time': start_time,
                'duration': 3,
                'volume': 0.5
            })
            print(f"添加默认脚步声音效: {footsteps_path}")
    
    print(f"为章节 {chapter_name} 找到 {len(sound_effects)} 个音效")
    for effect in sound_effects:
        print(f"  - {os.path.basename(effect['path'])} at {effect['start_time']}s for {effect['duration']}s")
    
    return sound_effects

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
        
        # 根据文件实际内容确定MIME类型
        image_format = imghdr.what(image_path)
        if image_format == 'jpeg':
            mime_type = 'image/jpeg'
        elif image_format == 'png':
            mime_type = 'image/png'
        elif image_format == 'gif':
            mime_type = 'image/gif'
        elif image_format == 'bmp':
            mime_type = 'image/bmp'
        elif image_format == 'webp':
            mime_type = 'image/webp'
        else:
            # 如果imghdr无法识别，尝试通过文件头手动检测
            with open(image_path, 'rb') as f:
                header = f.read(16)
                if header.startswith(b'\xff\xd8\xff'):
                    mime_type = 'image/jpeg'
                elif header.startswith(b'\x89PNG\r\n\x1a\n'):
                    mime_type = 'image/png'
                elif header.startswith(b'GIF87a') or header.startswith(b'GIF89a'):
                    mime_type = 'image/gif'
                elif header.startswith(b'BM'):
                    mime_type = 'image/bmp'
                elif header.startswith(b'RIFF') and b'WEBP' in header:
                    mime_type = 'image/webp'
                else:
                    mime_type = 'image/jpeg'  # 默认使用jpeg
        
        # 返回data URL格式
        print(mime_type)
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
                        "text": f"画面有明显的动态效果，保持画面整体稳定 --ratio 9:16 --dur {duration}"
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
    为单个章节生成视频，并匹配音效
    
    Args:
        chapter_dir: 章节目录路径
    
    Returns:
        bool: 是否成功提交所有任务
    """
    try:
        chapter_name = os.path.basename(chapter_dir)
        print(f"\n=== 处理章节: {chapter_name} ===")
        
        # 获取工作目录（项目根目录）
        work_dir = os.path.dirname(os.path.abspath(__file__))
        
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
        
        # 获取音效列表
        print(f"\n=== 匹配音效 ===")
        sound_effects = get_sound_effects_for_first_video(chapter_dir, work_dir)
        
        # 保存音效信息到文件
        if sound_effects:
            sound_effects_file = os.path.join(chapter_dir, 'sound_effects.json')
            try:
                with open(sound_effects_file, 'w', encoding='utf-8') as f:
                    json.dump(sound_effects, f, ensure_ascii=False, indent=2)
                print(f"✓ 音效信息已保存到: {sound_effects_file}")
            except Exception as e:
                print(f"⚠ 保存音效信息失败: {e}")
        else:
            print(f"⚠ 未找到匹配的音效")
        
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