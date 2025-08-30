#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
角色图片生成脚本（异步版本）
根据narration.txt中的角色信息异步生成角色图片
"""

import os
import re
import argparse
import sys
import base64
import json
import time
from config.prompt_config import ART_STYLES
from config.config import STORY_STYLE, IMAGE_TWO_CONFIG
from volcengine.visual.VisualService import VisualService

def parse_character_info(narration_file_path):
    """
    从narration.txt文件中解析角色信息和绘画风格
    
    Args:
        narration_file_path: narration.txt文件路径
    
    Returns:
        tuple: (角色信息列表, 绘画风格)
    """
    characters = []
    
    try:
        if not os.path.exists(narration_file_path):
            print(f"错误: narration.txt文件不存在: {narration_file_path}")
            return characters, None
        
        with open(narration_file_path, 'r', encoding='utf-8') as f:
            content = f.read()
        
        # 解析绘画风格
        style_match = re.search(r'<绘画风格>([^<]+)</绘画风格>', content)
        drawing_style = style_match.group(1) if style_match else None
        
        # 优先解析出镜人物列表中的角色定义
        cast_pattern = r'<出镜人物>(.*?)</出镜人物>'
        cast_match = re.search(cast_pattern, content, re.DOTALL)
        
        if cast_match:
            # 从出镜人物列表中解析角色
            cast_content = cast_match.group(1)
            character_pattern = r'<角色>(.*?)</角色>'
            character_matches = re.findall(character_pattern, cast_content, re.DOTALL)
            
            print(f"从出镜人物列表中找到 {len(character_matches)} 个角色")
            
            for i, char_content in enumerate(character_matches, 1):
                character_info = {}
                
                # 提取姓名
                name_match = re.search(r'<姓名>([^<]+)</姓名>', char_content)
                if name_match:
                    character_info['name'] = name_match.group(1).strip()
                else:
                    character_info['name'] = f'角色{i}'
                
                # 提取性别
                gender_match = re.search(r'<性别>([^<]+)</性别>', char_content)
                character_info['gender'] = gender_match.group(1).strip() if gender_match else '未知'
                
                # 提取年龄段
                age_match = re.search(r'<年龄段>([^<]+)</年龄段>', char_content)
                age_group = age_match.group(1).strip() if age_match else '未知'
                
                # 提取时代背景和角色形象
                era_match = re.search(r'<时代背景>([^<]+)</时代背景>', char_content)
                era_background = era_match.group(1).strip() if era_match else '未知'
                
                image_match = re.search(r'<角色形象>([^<]+)</角色形象>', char_content)
                character_image = image_match.group(1).strip() if image_match else '未知'
                
                # 构建角色描述
                details = []
                
                # 外貌特征
                appearance_section = re.search(r'<外貌特征>(.*?)</外貌特征>', char_content, re.DOTALL)
                if appearance_section:
                    appearance_content = appearance_section.group(1)
                    
                    # 发型
                    hair_style_match = re.search(r'<发型>([^<]+)</发型>', appearance_content)
                    if hair_style_match:
                        details.append(hair_style_match.group(1).strip())
                    
                    # 发色
                    hair_color_match = re.search(r'<发色>([^<]+)</发色>', appearance_content)
                    if hair_color_match:
                        details.append(hair_color_match.group(1).strip())
                    
                    # 面部特征
                    face_match = re.search(r'<面部特征>([^<]+)</面部特征>', appearance_content)
                    if face_match:
                        details.append(face_match.group(1).strip())
                    
                    # 身材特征
                    body_match = re.search(r'<身材特征>([^<]+)</身材特征>', appearance_content)
                    if body_match:
                        details.append(body_match.group(1).strip())
                    
                    # 特殊标记
                    special_match = re.search(r'<特殊标记>([^<]+)</特殊标记>', appearance_content)
                    if special_match and special_match.group(1).strip() != '无':
                        details.append(special_match.group(1).strip())
                
                # 服装风格
                clothing_section = re.search(r'<服装风格>(.*?)</服装风格>', char_content, re.DOTALL)
                if clothing_section:
                    clothing_content = clothing_section.group(1)
                    
                    # 上衣
                    top_match = re.search(r'<上衣>([^<]+)</上衣>', clothing_content)
                    if top_match:
                        details.append(top_match.group(1).strip())
                    
                    # 下装
                    bottom_match = re.search(r'<下装>([^<]+)</下装>', clothing_content)
                    if bottom_match:
                        details.append(bottom_match.group(1).strip())
                    
                    # 鞋履
                    shoes_match = re.search(r'<鞋履>([^<]+)</鞋履>', clothing_content)
                    if shoes_match and shoes_match.group(1).strip() != '无':
                        details.append(shoes_match.group(1).strip())
                    
                    # 配饰
                    accessory_match = re.search(r'<配饰>([^<]+)</配饰>', clothing_content)
                    if accessory_match and accessory_match.group(1).strip() != '无':
                        details.append(accessory_match.group(1).strip())
                
                character_info['description'] = '，'.join(details)
                character_info['age_group'] = age_group
                character_info['era_background'] = era_background
                character_info['character_image'] = character_image
                character_info['era'] = 'single'  # 标记为单一时代（从出镜人物列表解析）
                characters.append(character_info)
                
                print(f"解析到角色: {character_info['name']} ({era_background}, {character_image}) -> {character_info['description']}")
        
        # 如果出镜人物列表中没有找到角色，尝试解析旧格式
        if not characters:
            print("出镜人物列表中未找到角色，尝试解析旧格式...")
            # 首先尝试解析新格式的角色定义（<角色1>、<角色2>等）
            character_pattern = r'<角色(\d+)>(.*?)</角色\d+>'
            character_matches = re.findall(character_pattern, content, re.DOTALL)
            
            if character_matches:
                 # 新格式：<角色1>、<角色2>等
                 for char_num, char_content in character_matches:
                     character_info = {}
                     
                     # 提取姓名
                     name_match = re.search(r'<姓名>([^<]+)</姓名>', char_content)
                     if name_match:
                         character_info['name'] = name_match.group(1).strip()
                     else:
                         character_info['name'] = f'角色{char_num}'
                     
                     # 提取性别
                     gender_match = re.search(r'<性别>([^<]+)</性别>', char_content)
                     character_info['gender'] = gender_match.group(1).strip() if gender_match else '未知'
                     
                     # 提取年龄段
                     age_match = re.search(r'<年龄段>([^<]+)</年龄段>', char_content)
                     age_group = age_match.group(1).strip() if age_match else '未知'
                     
                     # 构建角色描述
                     details = []
                     
                     # 外貌特征
                     appearance_section = re.search(r'<外貌特征>(.*?)</外貌特征>', char_content, re.DOTALL)
                     if appearance_section:
                         appearance_content = appearance_section.group(1)
                         
                         # 发型
                         hair_style_match = re.search(r'<发型>([^<]+)</发型>', appearance_content)
                         if hair_style_match:
                             details.append(hair_style_match.group(1).strip())
                         
                         # 发色
                         hair_color_match = re.search(r'<发色>([^<]+)</发色>', appearance_content)
                         if hair_color_match:
                             details.append(hair_color_match.group(1).strip())
                         
                         # 面部特征
                         face_match = re.search(r'<面部特征>([^<]+)</面部特征>', appearance_content)
                         if face_match:
                             details.append(face_match.group(1).strip())
                         
                         # 身材特征
                         body_match = re.search(r'<身材特征>([^<]+)</身材特征>', appearance_content)
                         if body_match:
                             details.append(body_match.group(1).strip())
                         
                         # 特殊标记
                         special_match = re.search(r'<特殊标记>([^<]+)</特殊标记>', appearance_content)
                         if special_match and special_match.group(1).strip() != '无':
                             details.append(special_match.group(1).strip())
                     
                     # 检查是否有现代形象和古代形象（新格式）
                     modern_section = re.search(r'<现代形象>(.*?)</现代形象>', char_content, re.DOTALL)
                     ancient_section = re.search(r'<古代形象>(.*?)</古代形象>', char_content, re.DOTALL)
                     
                     if modern_section and ancient_section:
                         # 新格式：双时代格式
                         # 现代形象
                         modern_details = list(details)  # 复制基础外貌特征
                         modern_content = modern_section.group(1)
                         
                         # 现代上衣
                         modern_top_match = re.search(r'<上衣>([^<]+)</上衣>', modern_content)
                         if modern_top_match:
                             modern_details.append(modern_top_match.group(1).strip())
                         
                         # 现代下装
                         modern_bottom_match = re.search(r'<下装>([^<]+)</下装>', modern_content)
                         if modern_bottom_match:
                             modern_details.append(modern_bottom_match.group(1).strip())
                         
                         # 现代配饰
                         modern_accessory_match = re.search(r'<配饰>([^<]+)</配饰>', modern_content)
                         if modern_accessory_match and modern_accessory_match.group(1).strip() != '无':
                             modern_details.append(modern_accessory_match.group(1).strip())
                         
                         # 古代形象
                         ancient_details = list(details)  # 复制基础外貌特征
                         ancient_content = ancient_section.group(1)
                         
                         # 古代上衣
                         ancient_top_match = re.search(r'<上衣>([^<]+)</上衣>', ancient_content)
                         if ancient_top_match:
                             ancient_details.append(ancient_top_match.group(1).strip())
                         
                         # 古代下装
                         ancient_bottom_match = re.search(r'<下装>([^<]+)</下装>', ancient_content)
                         if ancient_bottom_match:
                             ancient_details.append(ancient_bottom_match.group(1).strip())
                         
                         # 古代配饰
                         ancient_accessory_match = re.search(r'<配饰>([^<]+)</配饰>', ancient_content)
                         if ancient_accessory_match and ancient_accessory_match.group(1).strip() != '无':
                             ancient_details.append(ancient_accessory_match.group(1).strip())
                         
                         # 创建两个角色信息：现代和古代
                         modern_character = {
                             'name': character_info['name'],
                             'gender': character_info['gender'],
                             'description': '，'.join(modern_details),
                             'age_group': age_group,
                             'era': 'modern'
                         }
                         
                         ancient_character = {
                             'name': character_info['name'],
                             'gender': character_info['gender'],
                             'description': '，'.join(ancient_details),
                             'age_group': age_group,
                             'era': 'ancient'
                         }
                         
                         characters.append(modern_character)
                         characters.append(ancient_character)
                         
                     else:
                         # 兼容旧格式或单一时代格式
                         clothing_section = re.search(r'<服装风格>(.*?)</服装风格>', char_content, re.DOTALL)
                         if clothing_section:
                             clothing_content = clothing_section.group(1)
                             
                             # 上衣
                             top_match = re.search(r'<上衣>([^<]+)</上衣>', clothing_content)
                             if top_match:
                                 details.append(top_match.group(1).strip())
                             
                             # 下装
                             bottom_match = re.search(r'<下装>([^<]+)</下装>', clothing_content)
                             if bottom_match:
                                 details.append(bottom_match.group(1).strip())
                             
                             # 配饰
                             accessory_match = re.search(r'<配饰>([^<]+)</配饰>', clothing_content)
                             if accessory_match and accessory_match.group(1).strip() != '无':
                                 details.append(accessory_match.group(1).strip())
                         
                         character_info['description'] = '，'.join(details)
                         character_info['age_group'] = age_group
                         character_info['era'] = 'single'  # 单一时代
                         characters.append(character_info)
                     
                     if modern_section and ancient_section:
                         print(f"解析到角色: {character_info['name']} (现代) -> {modern_character['description']}")
                         print(f"解析到角色: {character_info['name']} (古代) -> {ancient_character['description']}")
                     else:
                         print(f"解析到角色: {character_info['name']} -> {character_info['description']}")
        
        else:
            # 兼容旧格式：<主角1>、<配角1>等
            # 解析主角定义
            protagonist_pattern = r'<主角(\d+)>(.*?)</主角\d+>'
            protagonist_matches = re.findall(protagonist_pattern, content, re.DOTALL)
            
            for char_num, char_content in protagonist_matches:
                character_info = {}
                
                # 提取姓名
                name_match = re.search(r'<姓名>([^<]+)</姓名>', char_content)
                if name_match:
                    character_info['name'] = name_match.group(1).strip()
                else:
                    character_info['name'] = f'主角{char_num}'
                
                # 提取性别
                gender_match = re.search(r'<性别>([^<]+)</性别>', char_content)
                character_info['gender'] = gender_match.group(1).strip() if gender_match else '未知'
                
                # 提取年龄段
                age_match = re.search(r'<年龄段>([^<]+)</年龄段>', char_content)
                age_group = age_match.group(1).strip() if age_match else '未知'
                
                # 构建角色描述
                details = []
                
                # 外貌特征
                appearance_section = re.search(r'<外貌特征>(.*?)</外貌特征>', char_content, re.DOTALL)
                if appearance_section:
                    appearance_content = appearance_section.group(1)
                    
                    # 发型
                    hair_style_match = re.search(r'<发型>([^<]+)</发型>', appearance_content)
                    if hair_style_match:
                        details.append(hair_style_match.group(1).strip())
                    
                    # 发色
                    hair_color_match = re.search(r'<发色>([^<]+)</发色>', appearance_content)
                    if hair_color_match:
                        details.append(hair_color_match.group(1).strip())
                    
                    # 面部特征
                    face_match = re.search(r'<面部特征>([^<]+)</面部特征>', appearance_content)
                    if face_match:
                        details.append(face_match.group(1).strip())
                    
                    # 身材特征
                    body_match = re.search(r'<身材特征>([^<]+)</身材特征>', appearance_content)
                    if body_match:
                        details.append(body_match.group(1).strip())
                
                # 服装风格
                clothing_section = re.search(r'<服装风格>(.*?)</服装风格>', char_content, re.DOTALL)
                if clothing_section:
                    clothing_content = clothing_section.group(1)
                    
                    # 上衣
                    top_match = re.search(r'<上衣>([^<]+)</上衣>', clothing_content)
                    if top_match:
                        details.append(top_match.group(1).strip())
                    
                    # 下装
                    bottom_match = re.search(r'<下装>([^<]+)</下装>', clothing_content)
                    if bottom_match:
                        details.append(bottom_match.group(1).strip())
                    
                    # 配饰
                    accessory_match = re.search(r'<配饰>([^<]+)</配饰>', clothing_content)
                    if accessory_match:
                        details.append(accessory_match.group(1).strip())
                
                character_info['description'] = '，'.join(details)
                character_info['age_group'] = age_group
                character_info['era'] = 'single'  # 兼容旧格式，标记为单一时代
                characters.append(character_info)
                
                print(f"解析到主角: {character_info['name']} -> {character_info['description']}")
            
            # 解析配角定义
            supporting_pattern = r'<配角(\d+)>(.*?)</配角\d+>'
            supporting_matches = re.findall(supporting_pattern, content, re.DOTALL)
            
            for char_num, char_content in supporting_matches:
                character_info = {}
                
                # 提取姓名
                name_match = re.search(r'<姓名>([^<]+)</姓名>', char_content)
                if name_match:
                    character_info['name'] = name_match.group(1).strip()
                else:
                    character_info['name'] = f'配角{char_num}'
                
                # 提取性别
                gender_match = re.search(r'<性别>([^<]+)</性别>', char_content)
                character_info['gender'] = gender_match.group(1).strip() if gender_match else '未知'
                
                # 提取年龄段
                age_match = re.search(r'<年龄段>([^<]+)</年龄段>', char_content)
                age_group = age_match.group(1).strip() if age_match else '未知'
                
                # 构建角色描述（简化版）
                details = []
                
                # 外貌特征
                appearance_section = re.search(r'<外貌特征>(.*?)</外貌特征>', char_content, re.DOTALL)
                if appearance_section:
                    appearance_content = appearance_section.group(1)
                    
                    # 发型
                    hair_style_match = re.search(r'<发型>([^<]+)</发型>', appearance_content)
                    if hair_style_match:
                        details.append(hair_style_match.group(1).strip())
                    
                    # 发色
                    hair_color_match = re.search(r'<发色>([^<]+)</发色>', appearance_content)
                    if hair_color_match:
                        details.append(hair_color_match.group(1).strip())
                    
                    # 面部特征
                    face_match = re.search(r'<面部特征>([^<]+)</面部特征>', appearance_content)
                    if face_match:
                        details.append(face_match.group(1).strip())
                
                # 服装风格
                clothing_section = re.search(r'<服装风格>(.*?)</服装风格>', char_content, re.DOTALL)
                if clothing_section:
                    clothing_content = clothing_section.group(1)
                    
                    # 上衣
                    top_match = re.search(r'<上衣>([^<]+)</上衣>', clothing_content)
                    if top_match:
                        details.append(top_match.group(1).strip())
                
                character_info['description'] = '，'.join(details)
                character_info['age_group'] = age_group
                character_info['era'] = 'single'  # 兼容旧格式，标记为单一时代
                characters.append(character_info)
                
                print(f"解析到配角: {character_info['name']} -> {character_info['description']}")
        
        return characters, drawing_style
        
    except Exception as e:
        print(f"解析角色信息时发生错误: {e}")
        return characters, None

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

def generate_character_image_async(prompt, output_path, character_name, style=None, chapter_path=None, max_retries=3):
    """
    异步生成角色图片
    
    Args:
        prompt: 图片描述
        output_path: 输出文件路径
        character_name: 角色名称
        style: 艺术风格，如果为None则使用配置文件中的默认风格
        chapter_path: 章节路径，用于保存任务信息
        max_retries: 最大重试次数
    
    Returns:
        bool: 是否成功提交任务
    """
    # 检查图片是否已存在
    if os.path.exists(output_path):
        print(f"✓ 图片已存在，跳过生成: {os.path.basename(output_path)}")
        return True
    
    for attempt in range(max_retries + 1):
        try:
            if attempt > 0:
                print(f"🔄 第 {attempt} 次重试生成角色图片: {character_name}")
                time.sleep(2 * attempt)  # 递增延迟
            
            visual_service = VisualService()
            
            # 设置访问密钥
            visual_service.set_ak(IMAGE_TWO_CONFIG['access_key'])
            visual_service.set_sk(IMAGE_TWO_CONFIG['secret_key'])
            
            # 获取风格设置
            if style is None:
                style = IMAGE_TWO_CONFIG.get('default_style', 'manga')
            
            style_config = ART_STYLES.get(style, ART_STYLES['manga'])
            style_prompt = style_config.get('description', style_config)
            
            print(f"正在异步生成{style}风格角色图片: {character_name}")
            
            # 构建完整的prompt
            full_prompt = "以下内容为描述生成图片\n\
                 人物着装：圆领袍\n领口：高领，圆领，立领，不要V领，不要衽领，不要交领，不要y型领，不要漏脖子以下的皮肤\n\
                    2d漫画，细线条，厚涂，简洁，柔和的灯光，平面插画，动漫美感，数字技术技艺 \n\n" + style_prompt + "\n\n" + prompt + "\n\n"
            
            if attempt == 0:  # 只在第一次尝试时打印完整prompt
                print("这里是完整的prompt===>>>{}".format(full_prompt))
            
            # 构建请求参数
            form = {
                "req_key": "high_aes_general_v21_L",
                "prompt": full_prompt,
                "seed": 10 + attempt,  # 每次重试使用不同的seed
                "scale": 3.5,
                "return_url": IMAGE_TWO_CONFIG['return_url'],  # 返回base64格式
                "negative_prompt": IMAGE_TWO_CONFIG['negative_prompt'],
                "logo_info": {
                    "add_logo": False,
                    "position": 0,
                    "language": 0,
                    "opacity": 0.3,
                    "logo_text_content": "这里是明水印内容"
                }
            }
            
            # 调用异步API提交任务
            if attempt == 0:
                print("提交异步任务...")
            
            resp = visual_service.cv_sync2async_submit_task(form)
            
            if attempt == 0:
                print(f"异步任务响应: {resp}")
            
            # 检查响应
            if 'data' in resp and 'task_id' in resp['data']:
                task_id = resp['data']['task_id']
                print(f"✓ 角色图片任务提交成功，Task ID: {task_id}")
                
                # 保存任务信息到章节的async_tasks目录
                safe_character_name = character_name.replace('&', '')
                task_info = {
                    'task_id': task_id,
                    'output_path': output_path,
                    'filename': os.path.basename(output_path),
                    'character_name': safe_character_name,
                    'prompt': prompt,
                    'full_prompt': full_prompt,
                    'style': style,
                    'submit_time': time.time(),
                    'status': 'submitted',
                    'attempt': attempt + 1
                }
                
                # 保存到章节目录下的async_tasks文件夹
                if chapter_path:
                    async_tasks_dir = os.path.join(chapter_path, 'async_tasks')
                else:
                    async_tasks_dir = 'async_tasks'
                
                save_task_info(task_id, task_info, async_tasks_dir)
                return True
            else:
                error_msg = resp.get('message', '未知错误')
                print(f"✗ 角色图片任务提交失败 (尝试 {attempt + 1}/{max_retries + 1}): {error_msg}")
                
                if attempt == max_retries:
                    print(f"✗ 达到最大重试次数，角色图片任务最终失败")
                    return False
                
                # 继续下一次重试
                continue
                
        except Exception as e:
            print(f"✗ 生成角色图片时发生错误 (尝试 {attempt + 1}/{max_retries + 1}): {e}")
            
            if attempt == max_retries:
                print(f"✗ 达到最大重试次数，角色图片任务最终失败")
                return False
            
            # 继续下一次重试
            continue
    
    return False

def generate_character_images_async(input_path):
    """
    为指定路径异步生成角色图片
    支持单个章节目录或包含多个章节的数据目录
    
    Args:
        input_path: 输入路径（可以是单个章节目录或数据目录）
    
    Returns:
        bool: 是否成功提交任务
    """
    try:
        print(f"=== 开始异步生成角色图片 ===")
        print(f"输入路径: {input_path}")
        
        if not os.path.exists(input_path):
            print(f"错误: 路径不存在 {input_path}")
            return False
        
        # 检测输入路径类型
        chapter_dirs = []
        
        # 检查是否是单个章节目录
        if os.path.basename(input_path).startswith('chapter_') and os.path.isfile(os.path.join(input_path, 'narration.txt')):
            # 单个章节目录
            chapter_dirs = [input_path]
            print(f"检测到单个章节目录: {os.path.basename(input_path)}")
        else:
            # 数据目录，查找所有章节目录
            for item in os.listdir(input_path):
                item_path = os.path.join(input_path, item)
                if os.path.isdir(item_path) and item.startswith('chapter_'):
                    chapter_dirs.append(item_path)
            
            if chapter_dirs:
                chapter_dirs.sort()
                print(f"检测到数据目录，找到 {len(chapter_dirs)} 个章节目录")
        
        if not chapter_dirs:
            print(f"错误: 在 {input_path} 中没有找到有效的章节目录")
            return False
        
        submitted_count = 0
        skipped_count = 0
        failed_count = 0
        
        # 处理每个章节
        for chapter_dir in chapter_dirs:
            chapter_name = os.path.basename(chapter_dir)
            print(f"\n--- 处理章节: {chapter_name} ---")
            
            # 查找narration文件
            narration_file = os.path.join(chapter_dir, "narration.txt")
            if not os.path.exists(narration_file):
                print(f"警告: narration文件不存在 {narration_file}")
                continue
            
            # 解析角色信息和绘画风格
            characters, drawing_style = parse_character_info(narration_file)
            
            if not characters:
                print(f"警告: 未找到角色信息")
                continue
            
            print(f"找到 {len(characters)} 个角色")
            if drawing_style:
                print(f"绘画风格: {drawing_style}")
            
            # 获取绘画风格的model_prompt
            style_prompt = ""
            if drawing_style and drawing_style in STORY_STYLE:
                style_config = STORY_STYLE[drawing_style]
                if isinstance(style_config.get('model_prompt'), list):
                    style_prompt = style_config['model_prompt'][0]  # 取第一个
                else:
                    style_prompt = style_config.get('model_prompt', '')
                print(f"使用风格提示: {style_prompt}")
            
            # 为每个角色异步生成图片
            for i, character in enumerate(characters, 1):
                character_name = character['name']
                character_desc = character['description']
                character_gender = character.get('gender', '未知')
                character_era = character.get('era', 'single')
                
                # 根据性别决定视角
                if character_gender == '女':
                    view_angle = "背部视角，看不到领口和正面"
                else:
                    view_angle = "正面视角，清晰面部特征"
                
                # 构建角色图片的prompt，加入风格提示
                if style_prompt:
                    character_prompt = f"单人肖像，{character_desc}，高质量角色设定图，{view_angle}，{style_prompt}"
                else:
                    character_prompt = f"单人肖像，{character_desc}，高质量角色设定图，{view_angle}，动漫风格"
                
                # 根据时代信息生成不同的显示名称和文件名
                if character_era == 'modern':
                    display_name = f"{character_name}(现代)"
                    era_suffix = "_modern"
                elif character_era == 'ancient':
                    display_name = f"{character_name}(古代)"
                    era_suffix = "_ancient"
                else:
                    display_name = character_name
                    era_suffix = ""
                
                print(f"  生成第 {i}/{len(characters)} 个角色图片: {display_name}")
                print(f"  角色描述: {character_desc}")
                print(f"  完整提示词: {character_prompt}")
                
                # 生成图片（去掉文件名中的&符号，并加入时代标识）
                safe_character_name = character_name.replace('&', '')
                image_path = os.path.join(chapter_dir, f"{chapter_name}_character_{i:02d}_{safe_character_name}{era_suffix}.jpeg")
                
                # 检查图片是否已存在
                if os.path.exists(image_path):
                    print(f"  ✓ 角色图片已存在，跳过: {display_name}")
                    skipped_count += 1
                    continue
                
                # 异步生成图片
                if generate_character_image_async(character_prompt, image_path, display_name, chapter_path=chapter_dir):
                    print(f"  ✓ 角色图片任务提交成功: {display_name}")
                    submitted_count += 1
                else:
                    print(f"  ✗ 角色图片任务提交失败: {display_name}")
                    failed_count += 1
                
                # 添加短暂延迟，避免API请求过于频繁
                if i < len(characters):
                    time.sleep(1)
            
            print(f"章节 {chapter_name} 处理完成")
        
        # 输出统计信息
        print(f"\n{'='*50}")
        print(f"角色图片异步生成任务提交完成")
        print(f"任务提交成功: {submitted_count}")
        print(f"图片已存在: {skipped_count}")
        print(f"任务提交失败: {failed_count}")
        print(f"{'='*50}")
        
        return submitted_count > 0 or skipped_count > 0
        
    except Exception as e:
        print(f"生成角色图片时发生错误: {e}")
        return False

def main():
    parser = argparse.ArgumentParser(description='角色图片生成脚本（异步版本）')
    parser.add_argument('path', help='输入路径（可以是单个章节目录或包含多个章节的数据目录）')
    
    args = parser.parse_args()
    
    print(f"开始异步生成角色图片...")
    print(f"输入路径: {args.path}")
    
    # 调用异步生成函数
    success = generate_character_images_async(args.path)
    if success:
        print(f"\n✓ 角色图片异步任务提交完成")
        print("请使用相应的任务监控工具查看生成进度和结果。")
    else:
        print(f"\n✗ 角色图片异步任务提交失败")
        sys.exit(1)
    
    print("\n=== 异步任务提交完成 ===")

if __name__ == '__main__':
    main()