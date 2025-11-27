#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
异步视频生成脚本
遍历每个章节目录，使用每个章节的第一张和第二张图片异步生成视频
任务提交后将task_id保存到async_tasks目录，由check_async_tasks.py负责下载

使用方法:
python video_scripts/20251124v1/gen_narration_video.py data/031
python video_scripts/20251124v1/gen_narration_video.py data/031 --chapter chapter_001
"""

import os
import sys
import time
import json
import base64
import random
import imghdr
import ffmpeg

# 添加项目根目录到Python路径
# 当前文件路径: video_scripts/20251124v1/gen_narration_video.py
# 项目根目录: video_scripts/20251124v1/gen_narration_video.py -> ../../
current_dir = os.path.dirname(os.path.abspath(__file__))
project_root = os.path.dirname(os.path.dirname(current_dir))
if project_root not in sys.path:
    sys.path.insert(0, project_root)

from volcenginesdkarkruntime import Ark

# 导入配置
from config.config import ARK_CONFIG, IMAGE_TO_VIDEO_CONFIG

def get_audio_duration(audio_path):
    """
    获取音频文件时长
    
    Args:
        audio_path: 音频文件路径
    
    Returns:
        int: 音频时长（秒，向上取整），失败返回0
    """
    try:
        probe = ffmpeg.probe(audio_path)
        duration = float(probe['format']['duration'])
        import math
        return math.ceil(duration)
    except Exception as e:
        print(f"获取音频时长失败: {e}")
        return 0

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
        # 第一个章节从第3秒开始使用默认音效
        default_sound_path = os.path.join(work_dir, 'src', 'sound_effects', 'environment', 'wind_gentle.wav')
        if os.path.exists(default_sound_path):
            sound_effects.append({
                'path': default_sound_path,
                'start_time': 3,
                'duration': 5,
                'volume': 0.5
            })
            print(f"添加默认音效: {default_sound_path}")
    
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

def extract_video_prompts(narration_path):
    """
    从narration文件中提取视频prompt
    
    Args:
        narration_path: narration文件路径
    
    Returns:
        list: 视频prompt列表
    """
    try:
        if not os.path.exists(narration_path):
            return []
            
        with open(narration_path, 'r', encoding='utf-8') as f:
            content = f.read()
            
        import re
        prompts = re.findall(r'<视频prompt>(.*?)</视频prompt>', content, re.DOTALL)
        return [p.strip() for p in prompts]
    except Exception as e:
        print(f"提取视频prompt失败: {e}")
        return []

def create_video_from_single_image_async(image_path, duration, output_path, max_retries=3, video_prompt=None):
    """
    使用单张图片异步生成视频，带重试机制
    
    Args:
        image_path: 图片路径
        duration: 视频时长
        output_path: 输出视频路径
        max_retries: 最大重试次数
        video_prompt: 视频生成提示词，如果为None则使用默认提示词
    
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
            
            # 限制 duration 最大为 12 秒
            limited_duration = min(duration, 12)
            if duration > 12:
                print(f"  原始时长 {duration}s 超过限制，调整为 {limited_duration}s")
            else:
                print(f"  视频时长: {limited_duration}s")
            
            # 将图片转换为base64编码的data URL
            image_url = upload_image_to_server(image_path)
            
            if not image_url:
                print("图片处理失败")
                if attempt == max_retries:
                    return False
                continue
            
            # 创建视频生成任务
            client = Ark(api_key=ARK_CONFIG["api_key"])
            
            # 构建提示词
            prompt_text = f"{video_prompt} --ratio 9:16 --dur {limited_duration}" if video_prompt else f"画面有明显的动态效果，动作大一些 --ratio 9:16 --dur {limited_duration}"
            print(f"  使用提示词: {prompt_text}")
            
            resp = client.content_generation.tasks.create(
                model="doubao-seedance-1-0-lite-i2v-250428",
                content=[
                    {
                        "type": "text",
                        "text": prompt_text
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
            async_tasks_dir = os.path.join(project_root, 'async_tasks')
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

def parse_narration_closeups(narration_file_path):
    """
    解析narration文件中的特写人物信息，提取角色姓名和时代背景
    
    Args:
        narration_file_path: narration.txt文件路径
    
    Returns:
        list: 特写人物信息列表，每个元素包含 {'character_name': 角色姓名, 'era': 时代背景}
    """
    closeups = []
    
    try:
        if not os.path.exists(narration_file_path):
            print(f"警告: narration.txt文件不存在: {narration_file_path}")
            return closeups
        
        with open(narration_file_path, 'r', encoding='utf-8') as f:
            content = f.read()
        
        # 使用正则表达式提取所有特写人物信息
        import re
        
        # 匹配特写人物块
        closeup_pattern = r'<特写人物>(.*?)</特写人物>'
        closeup_matches = re.findall(closeup_pattern, content, re.DOTALL)
        
        for closeup_content in closeup_matches:
            character_info = {}
            
            # 提取角色姓名
            name_match = re.search(r'<角色姓名>([^<]+)</角色姓名>', closeup_content)
            if name_match:
                character_info['character_name'] = name_match.group(1).strip()
            
            # 提取时代背景
            era_match = re.search(r'<时代背景>([^<]+)</时代背景>', closeup_content)
            if era_match:
                era_text = era_match.group(1).strip()
                if '现代' in era_text:
                    character_info['era'] = 'modern'
                elif '古代' in era_text:
                    character_info['era'] = 'ancient'
                else:
                    character_info['era'] = 'single'
            else:
                # 如果没有时代背景标签，默认为单一时代
                character_info['era'] = 'single'
            
            if 'character_name' in character_info:
                closeups.append(character_info)
        
        print(f"解析到 {len(closeups)} 个特写人物信息")
        for i, closeup in enumerate(closeups[:5]):  # 只显示前5个
            era_text = {'modern': '现代', 'ancient': '古代', 'single': '单一时代'}[closeup['era']]
            print(f"  特写 {i+1}: {closeup['character_name']} ({era_text})")
        
        return closeups
        
    except Exception as e:
        print(f"解析narration文件时发生错误: {e}")
        return closeups

def find_character_image_by_era(chapter_path, character_name, era):
    """
    根据角色姓名和时代背景查找对应的角色图片
    
    Args:
        chapter_path: 章节目录路径
        character_name: 角色姓名
        era: 时代背景 ('modern', 'ancient', 'single')
    
    Returns:
        str: 角色图片路径，未找到返回None
    """
    try:
        chapter_name = os.path.basename(chapter_path)
        
        # 根据时代背景构建文件名后缀
        if era == 'modern':
            era_suffix = '_modern'
        elif era == 'ancient':
            era_suffix = '_ancient'
        else:
            era_suffix = ''
        
        # 查找角色图片文件
        image_extensions = ['.jpg', '.jpeg', '.png', '.bmp', '.gif']
        
        # 首先在 images 子目录中查找
        images_dir = os.path.join(chapter_path, 'images')
        if os.path.exists(images_dir):
            for file in os.listdir(images_dir):
                if any(file.lower().endswith(ext) for ext in image_extensions):
                    # 检查文件名是否包含角色姓名和时代后缀
                    if character_name in file and era_suffix in file:
                        image_path = os.path.join(images_dir, file)
                        print(f"找到角色图片: {character_name} ({era}) -> {file}")
                        return image_path
            
            # 如果没找到带时代后缀的，尝试查找不带后缀的（适用于单一时代）
            if era == 'single':
                for file in os.listdir(images_dir):
                    if any(file.lower().endswith(ext) for ext in image_extensions):
                        if character_name in file and '_modern' not in file and '_ancient' not in file:
                            image_path = os.path.join(images_dir, file)
                            print(f"找到角色图片: {character_name} (单一时代) -> {file}")
                            return image_path
        
        # 如果 images 目录不存在或没找到，回退到章节根目录查找（兼容旧格式）
        for file in os.listdir(chapter_path):
            if any(file.lower().endswith(ext) for ext in image_extensions):
                # 检查文件名是否包含角色姓名和时代后缀
                if character_name in file and era_suffix in file:
                    image_path = os.path.join(chapter_path, file)
                    print(f"找到角色图片: {character_name} ({era}) -> {file}")
                    return image_path
        
        # 如果没找到带时代后缀的，尝试查找不带后缀的（适用于单一时代）
        if era == 'single':
            for file in os.listdir(chapter_path):
                if any(file.lower().endswith(ext) for ext in image_extensions):
                    if character_name in file and '_modern' not in file and '_ancient' not in file:
                        image_path = os.path.join(chapter_path, file)
                        print(f"找到角色图片: {character_name} (单一时代) -> {file}")
                        return image_path
        
        print(f"未找到角色图片: {character_name} ({era})")
        return None
        
    except Exception as e:
        print(f"查找角色图片时发生错误: {e}")
        return None

def get_chapter_images(chapter_path):
    """
    获取章节目录中的所有chapter_xxx_image_XX格式的图片
    
    Args:
        chapter_path: 章节目录路径
    
    Returns:
        list: 图片路径列表，按编号排序
    """
    try:
        import re
        
        # 获取章节名称
        chapter_name = os.path.basename(chapter_path)
        
        # 支持的图片扩展名
        image_extensions = ['.jpg', '.jpeg', '.png', '.bmp', '.gif']
        
        # 存储找到的图片
        images = []
        
        # 遍历章节目录中的所有文件
        for file in os.listdir(chapter_path):
            # 检查文件扩展名
            if any(file.lower().endswith(ext) for ext in image_extensions):
                # 检查文件名格式是否匹配 chapter_xxx_image_XX
                pattern = rf'{re.escape(chapter_name)}_image_(\d+)'
                match = re.search(pattern, file)
                if match:
                    image_number = int(match.group(1))
                    image_path = os.path.join(chapter_path, file)
                    images.append((image_number, image_path))
        
        # 按图片编号排序
        images.sort(key=lambda x: x[0])
        
        # 提取路径列表
        image_paths = [img[1] for img in images]
        
        if image_paths:
            print(f"找到 {len(image_paths)} 张图片:")
            for img_path in image_paths:
                print(f"  - {os.path.basename(img_path)}")
        else:
            print(f"警告: 章节 {chapter_path} 没有找到 {chapter_name}_image_XX 格式的文件")
        
        return image_paths
            
    except Exception as e:
        print(f"获取章节图片时发生错误: {e}")
        return []

def generate_videos_for_chapter(chapter_dir):
    """
    为单个章节生成视频，处理所有图片并匹配音效
    
    Args:
        chapter_dir: 章节目录路径
    
    Returns:
        bool: 是否成功提交所有任务
    """
    try:
        chapter_name = os.path.basename(chapter_dir)
        print(f"\n=== 处理章节: {chapter_name} ===")
        
        # 获取工作目录（项目根目录）
        work_dir = project_root
        
        # 获取章节的所有图片
        image_paths = get_chapter_images(chapter_dir)
        
        if not image_paths:
            print(f"✗ 章节 {chapter_name} 跳过，没有找到图片")
            return False
        
        print(f"共找到 {len(image_paths)} 张图片，将生成 {len(image_paths)} 个视频")
        
        # 获取音效列表
        print(f"\n=== 匹配音效 ===")
        sound_effects = get_sound_effects_for_first_video(chapter_dir, work_dir)
        
        # 提取视频prompts
        print(f"\n=== 提取视频Prompts ===")
        video_prompts = []
        # 尝试查找 narration 文件
        possible_narration_files = ['narration_01.txt', 'narration.txt', f'{chapter_name}_narration.txt']
        for fname in possible_narration_files:
            fpath = os.path.join(chapter_dir, fname)
            if os.path.exists(fpath):
                print(f"从 {fname} 提取Prompts")
                video_prompts = extract_video_prompts(fpath)
                if video_prompts:
                    print(f"成功提取 {len(video_prompts)} 个视频Prompt")
                    break
        
        if not video_prompts:
             print("未找到视频Prompt，将使用默认提示词")
        
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
        failed_count = 0
        
        # 遍历所有图片，为每张图片生成视频
        for idx, image_path in enumerate(image_paths, 1):
            print(f"\n--- 处理第 {idx}/{len(image_paths)} 张图片 ---")
            
            # 从图片文件名中提取编号
            import re
            image_filename = os.path.basename(image_path)
            match = re.search(r'_image_(\d+)', image_filename)
            if match:
                image_number = match.group(1)
            else:
                image_number = f"{idx:02d}"
            
            # 生成视频输出路径
            video_path = os.path.join(chapter_dir, f"{chapter_name}_video_{image_number}.mp4")
            
            # 获取对应的narration音频文件的时长
            narration_path = os.path.join(chapter_dir, f"{chapter_name}_narration_{image_number}.mp3")
            
            # 如果存在对应的narration音频，使用其时长；否则使用默认时长5秒
            if os.path.exists(narration_path):
                duration = get_audio_duration(narration_path)
                print(f"视频时长: {duration}s (来自 {os.path.basename(narration_path)})")
            else:
                duration = 5
                print(f"警告: 未找到 {os.path.basename(narration_path)}，使用默认时长 {duration}s")
            
            # 获取对应的视频Prompt
            video_prompt = None
            try:
                # 尝试根据图片编号匹配Prompt (假设Prompt顺序与图片顺序一致)
                prompt_idx = int(image_number) - 1
                if 0 <= prompt_idx < len(video_prompts):
                    video_prompt = video_prompts[prompt_idx]
                    print(f"匹配到视频Prompt: {video_prompt[:20]}...")
            except ValueError:
                pass
            
            # 提交视频生成任务
            print(f"提交视频生成任务: {os.path.basename(image_path)} -> {os.path.basename(video_path)}")
            if create_video_from_single_image_async(image_path, duration, video_path, video_prompt=video_prompt):
                success_count += 1
                print(f"✓ 第 {idx} 个视频任务提交成功")
            else:
                failed_count += 1
                print(f"✗ 第 {idx} 个视频任务提交失败")
        
        # 输出统计结果
        print(f"\n=== 章节 {chapter_name} 处理完成 ===")
        print(f"成功提交: {success_count}/{len(image_paths)}")
        print(f"失败: {failed_count}/{len(image_paths)}")
        
        if success_count > 0:
            return True
        else:
            print(f"✗ 章节 {chapter_name} 所有视频任务提交失败")
            return False
        
    except Exception as e:
        print(f"处理章节 {chapter_dir} 时发生错误: {e}")
        return False

def process_single_chapter(data_dir, chapter_name):
    """
    处理单个章节目录，为指定章节生成视频
    
    Args:
        data_dir: 数据目录路径
        chapter_name: 章节名称，例如 'chapter_001'
    
    Returns:
        bool: 处理是否成功
    """
    try:
        if not os.path.exists(data_dir):
            print(f"错误: 数据目录不存在: {data_dir}")
            return False
        
        # 构建章节目录路径
        chapter_dir = os.path.join(data_dir, chapter_name)
        
        if not os.path.exists(chapter_dir):
            print(f"错误: 章节目录不存在: {chapter_dir}")
            return False
        
        if not os.path.isdir(chapter_dir):
            print(f"错误: {chapter_dir} 不是一个目录")
            return False
        
        print(f"开始处理章节: {chapter_name}")
        
        # 处理指定章节
        success = generate_videos_for_chapter(chapter_dir)
        
        if success:
            print(f"\n=== 章节 {chapter_name} 处理完成 ===")
            print(f"\n请运行以下命令监控任务状态:")
            print(f"python check_async_tasks.py --monitor")
        else:
            print(f"\n=== 章节 {chapter_name} 处理失败 ===")
        
        return success
        
    except Exception as e:
        print(f"处理章节 {chapter_name} 时发生错误: {e}")
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
        
        print(f"\n=== 处理完成 ===")
        print(f"成功处理章节: {success_count}/{len(chapter_dirs)}")
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
    parser.add_argument('data_dir', help='数据目录路径，例如: data/031')
    parser.add_argument('--tasks-dir', default='async_tasks', help='异步任务目录路径')
    parser.add_argument('--chapter', help='指定处理单个章节，例如: chapter_001')
    
    args = parser.parse_args()
    
    data_dir = args.data_dir
    async_tasks_dir = args.tasks_dir
    chapter_name = args.chapter
    
    print(f"开始异步处理数据目录: {data_dir}")
    if chapter_name:
        print(f"指定处理章节: {chapter_name}")
    print("注意: 请确保已正确配置 ARK_CONFIG 中的 api_key")
    
    if not os.path.exists(data_dir):
        print(f"错误: 数据目录不存在: {data_dir}")
        sys.exit(1)
    
    # 确保async_tasks目录存在
    async_tasks_dir_full = os.path.join(project_root, async_tasks_dir)
    os.makedirs(async_tasks_dir_full, exist_ok=True)
    
    # 根据参数决定处理方式
    if chapter_name:
        # 处理单个章节
        success = process_single_chapter(data_dir, chapter_name)
        if success:
            print("\n=== 异步视频生成任务提交完成 ===")
            print("请使用 check_async_tasks.py 监控任务状态并下载完成的视频")
            print("例如: python check_async_tasks.py --monitor")
        else:
            print("\n=== 任务提交失败 ===")
            sys.exit(1)
    else:
        # 处理所有章节
        process_chapters(data_dir)
        print("\n=== 异步视频生成任务提交完成 ===")
        print("请使用 check_async_tasks.py 监控任务状态并下载完成的视频")
        print("例如: python check_async_tasks.py --monitor")

if __name__ == "__main__":
    main()

