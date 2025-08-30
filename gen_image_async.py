# !/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
独立的图片生成脚本
遍历章节目录，为每个分镜生成图片
"""

import os
import re
import argparse
import base64
import sys
import json
import time
import shutil
import random
from config.config import IMAGE_TWO_CONFIG, STORY_STYLE
from config.prompt_config import ART_STYLES
from volcengine.visual.VisualService import VisualService

def parse_character_gender(content, character_name):
    """
    从narration.txt内容中解析指定角色的性别
    
    Args:
        content: narration.txt文件内容
        character_name: 角色名称
    
    Returns:
        str: 角色性别（'男'/'女'/'未知'）
    """
    # 查找角色信息块
    character_pattern = rf'<角色>\s*{re.escape(character_name)}\s*</角色>(.*?)(?=<角色>|$)'
    character_match = re.search(character_pattern, content, re.DOTALL)
    
    if character_match:
        character_content = character_match.group(1)
        # 提取性别信息
        gender_match = re.search(r'<性别>([^<]+)</性别>', character_content)
        if gender_match:
            return gender_match.group(1).strip()
    
    return '未知'

def parse_character_definitions(content):
    """
    解析角色定义，建立角色姓名映射（适配新格式）
    
    Args:
        content: narration.txt文件内容
    
    Returns:
        dict: 角色姓名映射字典，格式为 {"角色姓名": {"数字编号": "01", "性别": "Male", ...}}
    """
    character_map = {}
    
    # 解析新格式的角色定义（角色1、角色2等）
    character_pattern = r'<角色(\d+)>(.*?)</角色\d+>'
    character_matches = re.findall(character_pattern, content, re.DOTALL)
    
    for char_num, char_content in character_matches:
        char_info = {}
        
        # 提取角色姓名
        name_match = re.search(r'<姓名>([^<]+)</姓名>', char_content)
        if not name_match:
            continue  # 没有姓名的角色跳过
        
        character_name = name_match.group(1).strip()
        
        # 提取各种属性
        gender_match = re.search(r'<性别>([^<]+)</性别>', char_content)
        age_match = re.search(r'<年龄段>([^<]+)</年龄段>', char_content)
        
        # 提取外貌特征
        appearance_block = re.search(r'<外貌特征>(.*?)</外貌特征>', char_content, re.DOTALL)
        if appearance_block:
            appearance_content = appearance_block.group(1)
            hair_style_match = re.search(r'<发型>([^<]+)</发型>', appearance_content)
            hair_color_match = re.search(r'<发色>([^<]+)</发色>', appearance_content)
            face_match = re.search(r'<面部特征>([^<]+)</面部特征>', appearance_content)
            body_match = re.search(r'<身材特征>([^<]+)</身材特征>', appearance_content)
            
            if hair_style_match:
                char_info['发型'] = hair_style_match.group(1).strip()
            if hair_color_match:
                char_info['发色'] = hair_color_match.group(1).strip()
            if face_match:
                char_info['面部特征'] = face_match.group(1).strip()
            if body_match:
                char_info['身材特征'] = body_match.group(1).strip()
        
        # 提取服装风格（现代形象或古代形象或单一服装风格）
        modern_style_block = re.search(r'<现代形象>(.*?)</现代形象>', char_content, re.DOTALL)
        ancient_style_block = re.search(r'<古代形象>(.*?)</古代形象>', char_content, re.DOTALL)
        single_style_block = re.search(r'<服装风格>(.*?)</服装风格>', char_content, re.DOTALL)
        
        if modern_style_block:
            char_info['现代形象'] = modern_style_block.group(1).strip()
        if ancient_style_block:
            char_info['古代形象'] = ancient_style_block.group(1).strip()
        if single_style_block:
            char_info['服装风格'] = single_style_block.group(1).strip()
        
        # 设置基本属性
        if gender_match:
            char_info['性别'] = gender_match.group(1).strip()
        if age_match:
            char_info['年龄段'] = age_match.group(1).strip()
        
        # 设置默认值
        char_info['风格'] = 'Common'
        char_info['文化'] = 'Chinese'
        char_info['气质'] = 'Common'
        char_info['数字编号'] = f"{int(char_num):02d}"
        
        # 使用角色姓名作为键
        character_map[character_name] = char_info
    
    # 兼容旧格式的主角和配角定义
    protagonist_pattern = r'<主角(\d+)>(.*?)</主角\d+>'
    protagonist_matches = re.findall(protagonist_pattern, content, re.DOTALL)
    
    for char_num, char_content in protagonist_matches:
        char_info = {}
        
        # 提取各种属性
        name_match = re.search(r'<姓名>([^<]+)</姓名>', char_content)
        if not name_match:
            continue
        
        character_name = name_match.group(1).strip()
        
        gender_match = re.search(r'<性别>([^<]+)</性别>', char_content)
        age_match = re.search(r'<年龄段>([^<]+)</年龄段>', char_content)
        style_match = re.search(r'<风格>([^<]+)</风格>', char_content)
        culture_match = re.search(r'<文化>([^<]+)</文化>', char_content)
        temperament_match = re.search(r'<气质>([^<]+)</气质>', char_content)
        number_match = re.search(r'<角色编号>([^<]+)</角色编号>', char_content)
        
        if gender_match:
            char_info['性别'] = gender_match.group(1).strip()
        if age_match:
            char_info['年龄段'] = age_match.group(1).strip()
        if style_match:
            char_info['风格'] = style_match.group(1).strip()
        if culture_match:
            char_info['文化'] = culture_match.group(1).strip()
        if temperament_match:
            char_info['气质'] = temperament_match.group(1).strip()
        if number_match:
            char_info['数字编号'] = number_match.group(1).strip()
        
        character_map[character_name] = char_info
    
    # 兼容旧格式的配角定义
    supporting_pattern = r'<配角(\d+)>(.*?)</配角\d+>'
    supporting_matches = re.findall(supporting_pattern, content, re.DOTALL)
    
    for char_num, char_content in supporting_matches:
        char_info = {}
        
        # 提取各种属性
        name_match = re.search(r'<姓名>([^<]+)</姓名>', char_content)
        if not name_match:
            continue
        
        character_name = name_match.group(1).strip()
        
        gender_match = re.search(r'<性别>([^<]+)</性别>', char_content)
        age_match = re.search(r'<年龄段>([^<]+)</年龄段>', char_content)
        style_match = re.search(r'<风格>([^<]+)</风格>', char_content)
        culture_match = re.search(r'<文化>([^<]+)</文化>', char_content)
        temperament_match = re.search(r'<气质>([^<]+)</气质>', char_content)
        number_match = re.search(r'<角色编号>([^<]+)</角色编号>', char_content)
        
        if gender_match:
            char_info['性别'] = gender_match.group(1).strip()
        if age_match:
            char_info['年龄段'] = age_match.group(1).strip()
        if style_match:
            char_info['风格'] = style_match.group(1).strip()
        if culture_match:
            char_info['文化'] = culture_match.group(1).strip()
        if temperament_match:
            char_info['气质'] = temperament_match.group(1).strip()
        if number_match:
            char_info['数字编号'] = number_match.group(1).strip()
        
        character_map[character_name] = char_info
    
    return character_map

def parse_narration_file(narration_file_path):
    """
    解析narration.txt文件，提取分镜信息、图片prompt和绘画风格
    
    Args:
        narration_file_path: narration.txt文件路径
    
    Returns:
        tuple: (分镜信息列表, 绘画风格, 角色映射字典)
    """
    scenes = []
    drawing_style = None
    character_map = {}
    
    try:
        if not os.path.exists(narration_file_path):
            print(f"警告: narration.txt文件不存在: {narration_file_path}")
            return scenes, drawing_style, character_map
        
        with open(narration_file_path, 'r', encoding='utf-8') as f:
            content = f.read()
        
        # 解析角色定义
        character_map = parse_character_definitions(content)
        print(f"解析到 {len(character_map)} 个角色定义")
        for char_key, char_info in character_map.items():
            print(f"  {char_key}: {char_info.get('姓名', '未知')} (编号: {char_info.get('数字编号', '未知')})")
        
        # 解析绘画风格
        style_match = re.search(r'<绘画风格>([^<]+)</绘画风格>', content)
        drawing_style = style_match.group(1) if style_match else None
        
        # 提取分镜信息 - 修复正则表达式以匹配所有分镜格式
        scene_pattern = r'<分镜[^>]*>(.*?)</分镜[^>]*>'
        scene_matches = re.findall(scene_pattern, content, re.DOTALL)
        
        for idx, scene_content in enumerate(scene_matches):
            print(f"处理分镜 {idx+1}")
            scene_info = {}
            
            # 提取所有特写（新格式：每个特写包含独立的解说内容）
            scene_info['closeups'] = []
            # 动态检测特写数量，最多支持10个特写
            for i in range(1, 11):  # 图片特写1到图片特写10
                closeup_pattern = f'<图片特写{i}>(.*?)</图片特写{i}>'
                closeup_match = re.search(closeup_pattern, scene_content, re.DOTALL)
                if closeup_match:
                    closeup_content = closeup_match.group(1)
                    closeup_info = {}
                    
                    # 提取该特写的解说内容（新格式）
                    narration_match = re.search(r'<解说内容>([^<]+)</解说内容>', closeup_content, re.DOTALL)
                    if narration_match:
                        closeup_info['narration'] = narration_match.group(1).strip()
                        print(f"      特写{i}解说内容: {closeup_info['narration'][:30]}...")
                    
                    # 提取特写人物信息
                    character_name = None
                    
                    # 从<特写人物>块中提取角色姓名（支持容错处理）
                    character_block_match = re.search(r'<特写人物>(.*?)</特写人物>', closeup_content, re.DOTALL)
                    character_block = None
                    
                    if character_block_match:
                        character_block = character_block_match.group(1)
                        print(f"      找到完整的<特写人物>标签")
                    else:
                        # 容错处理：检查是否有缺失开始标签的情况
                        # 查找</特写人物>结束标签，然后向前查找角色信息
                        end_tag_match = re.search(r'(.*?)</特写人物>', closeup_content, re.DOTALL)
                        if end_tag_match:
                            potential_block = end_tag_match.group(1).strip()
                            # 检查是否包含角色相关标签
                            if re.search(r'<角色姓名>.*?</角色姓名>', potential_block) or re.search(r'<时代背景>.*?</时代背景>', potential_block):
                                character_block = potential_block
                                print(f"      容错处理：找到缺失开始标签的<特写人物>内容")
                    
                    if character_block:
                        # 优先从<角色姓名>标签中提取角色名称
                        character_name_match = re.search(r'<角色姓名>([^<]+)</角色姓名>', character_block)
                        if character_name_match:
                            character_name = character_name_match.group(1).strip()
                            closeup_info['character'] = character_name
                            print(f"      从<角色姓名>提取到角色: {character_name}")
                        
                        # 提取时代背景信息
                        era_background_match = re.search(r'<时代背景>([^<]+)</时代背景>', character_block)
                        if era_background_match:
                            era_background = era_background_match.group(1).strip()
                            closeup_info['era_background'] = era_background
                            print(f"      提取到时代背景: {era_background}")
                        
                        # 提取角色形象信息
                        character_image_match = re.search(r'<角色形象>([^<]+)</角色形象>', character_block)
                        if character_image_match:
                            character_image = character_image_match.group(1).strip()
                            closeup_info['character_image'] = character_image
                            print(f"      提取到角色形象: {character_image}")
                    
                    # 兼容旧格式的角色提取
                    if not character_name:
                        character_match = re.search(r'<特写人物>([^<]+)</特写人物>', closeup_content)
                        if character_match:
                            character_name = character_match.group(1).strip()
                            closeup_info['character'] = character_name
                            print(f"      从<特写人物>提取到角色: {character_name}")
                    
                    if character_name:
                        # 根据角色名称查找角色定义
                        if character_name in character_map:
                            char_info = character_map[character_name]
                            closeup_info['gender'] = char_info.get('性别', '')
                            closeup_info['age_group'] = char_info.get('年龄段', '')
                            closeup_info['character_style'] = char_info.get('风格', '')
                            closeup_info['culture'] = char_info.get('文化', 'Chinese')
                            closeup_info['temperament'] = char_info.get('气质', 'Common')
                            closeup_info['character_number'] = char_info.get('数字编号', '')
                    
                    # 提取图片prompt
                    prompt_match = re.search(r'<图片prompt>([^<]+)</图片prompt>', closeup_content, re.DOTALL)
                    if prompt_match:
                        closeup_info['prompt'] = prompt_match.group(1).strip()
                    
                    if 'prompt' in closeup_info:
                        scene_info['closeups'].append(closeup_info)
            
            if scene_info['closeups']:  # 只有当有特写时才添加分镜
                scenes.append(scene_info)
        
        print(f"解析到 {len(scenes)} 个分镜")
        if drawing_style:
            print(f"绘画风格: {drawing_style}")
        
        return scenes, drawing_style, character_map
        
    except Exception as e:
        print(f"解析narration文件时发生错误: {e}")
        return scenes, drawing_style, character_map

def find_character_image(chapter_path, character_name, era_background=None):
    """
    查找角色图片文件，支持时代背景区分
    
    Args:
        chapter_path: 章节目录路径
        character_name: 角色名称
        era_background: 时代背景（现代/古代），可选
    
    Returns:
        str: 角色图片文件路径，如果未找到返回None
    """
    try:
        chapter_name = os.path.basename(chapter_path)
        # 移除角色名称中的&符号
        safe_character_name = character_name.replace('&', '')
        
        # 根据时代背景确定文件名后缀
        era_suffix = ""
        if era_background == "现代":
            era_suffix = "_modern"
        elif era_background == "古代":
            era_suffix = "_ancient"
        
        # 优先查找带时代后缀的图片
        if era_suffix:
            for filename in os.listdir(chapter_path):
                if (filename.endswith(f"_{safe_character_name}{era_suffix}.jpeg") and "character" in filename):
                    image_path = os.path.join(chapter_path, filename)
                    print(f"找到时代背景角色图片: {image_path}")
                    return image_path
        
        # 如果没有找到时代背景图片，查找通用角色图片
        for filename in os.listdir(chapter_path):
            if (filename.endswith(f"_{safe_character_name}.jpeg") and "character" in filename and 
                not filename.endswith(f"_{safe_character_name}_modern.jpeg") and 
                not filename.endswith(f"_{safe_character_name}_ancient.jpeg")):
                image_path = os.path.join(chapter_path, filename)
                print(f"找到通用角色图片: {image_path}")
                return image_path
        
        print(f"未找到角色 {character_name} 的图片文件 (时代背景: {era_background})")
        return None
        
    except Exception as e:
        print(f"查找角色图片时发生错误: {e}")
        return None

def find_similar_character_image_by_prompt(prompt, gender=None, character_style=None):
    """
    根据prompt内容查找相似的角色图片
    
    Args:
        prompt: 图片描述文本
        gender: 性别偏好 (Male/Female)，可选
        character_style: 风格偏好 (Ancient/Fantasy/Modern/SciFi)，可选
    
    Returns:
        str: 角色图片文件路径，如果未找到返回None
    """
    script_dir = os.path.dirname(os.path.abspath(__file__))
    character_images_dir = os.path.join(script_dir, 'Character_Images')
    
    if not os.path.exists(character_images_dir):
        print(f"    警告: Character_Images目录不存在: {character_images_dir}")
        return None
    
    # 从prompt中提取关键词
    prompt_lower = prompt.lower()
    
    # 定义关键词映射
    gender_keywords = {
        'male': ['男', '男性', '男人', '少年', '青年', '中年', '老人', '武士', '将军', '皇帝', '王子', '书生'],
        'female': ['女', '女性', '女人', '少女', '女子', '美女', '公主', '皇后', '仙女', '侍女']
    }
    
    age_keywords = {
        '15-22_Youth': ['少年', '少女', '青春', '年轻', '稚嫩'],
        '23-30_YoungAdult': ['青年', '年轻人', '成年'],
        '25-40_FantasyAdult': ['成人', '壮年'],
        '31-45_MiddleAged': ['中年', '成熟']
    }
    
    style_keywords = {
        'Ancient': ['古代', '古装', '传统', '古典', '汉服', '唐装', '宫廷'],
        'Fantasy': ['仙侠', '修仙', '玄幻', '仙人', '神仙', '法师', '魔法'],
        'Modern': ['现代', '当代', '都市', '时尚'],
        'SciFi': ['科幻', '未来', '机甲', '太空']
    }
    
    temperament_keywords = {
        'Royal': ['皇帝', '皇后', '王子', '公主', '贵族', '宫廷'],
        'Chivalrous': ['武士', '侠客', '英雄', '勇士'],
        'Scholar': ['书生', '学者', '文人'],
        'Assassin': ['刺客', '杀手', '暗杀'],
        'Monk': ['僧人', '和尚', '道士'],
        'Beggar': ['乞丐', '流浪'],
        'Common': ['平民', '普通', '百姓']
    }
    
    # 分析prompt，确定最佳匹配
    detected_gender = gender
    detected_style = character_style
    detected_age = None
    detected_temperament = 'Common'
    
    # 检测性别
    if not detected_gender:
        for g, keywords in gender_keywords.items():
            if any(keyword in prompt_lower for keyword in keywords):
                detected_gender = g.capitalize()
                break
    
    # 检测风格
    if not detected_style:
        for s, keywords in style_keywords.items():
            if any(keyword in prompt_lower for keyword in keywords):
                detected_style = s
                break
    
    # 检测年龄段
    for age, keywords in age_keywords.items():
        if any(keyword in prompt_lower for keyword in keywords):
            detected_age = age
            break
    
    # 检测气质
    for temp, keywords in temperament_keywords.items():
        if any(keyword in prompt_lower for keyword in keywords):
            detected_temperament = temp
            break
    
    # 设置默认值
    if not detected_gender:
        detected_gender = 'Male'
    if not detected_style:
        detected_style = 'Ancient'
    if not detected_age:
        detected_age = '23-30_YoungAdult'
    
    print(f"    根据prompt分析: {detected_gender}/{detected_age}/{detected_style}/Chinese/{detected_temperament}")
    
    # 尝试查找匹配的图片
    search_combinations = [
        (detected_gender, detected_age, detected_style, 'Chinese', detected_temperament),
        (detected_gender, detected_age, detected_style, 'Chinese', 'Common'),
        (detected_gender, '23-30_YoungAdult', detected_style, 'Chinese', 'Common'),
        (detected_gender, detected_age, 'Ancient', 'Chinese', 'Common'),
        ('Male', '23-30_YoungAdult', 'Ancient', 'Chinese', 'Common'),
        ('Female', '23-30_YoungAdult', 'Ancient', 'Chinese', 'Common')
    ]
    
    for gender_try, age_try, style_try, culture_try, temp_try in search_combinations:
        character_dir = os.path.join(character_images_dir, gender_try, age_try, style_try, culture_try, temp_try)
        if os.path.exists(character_dir):
            for file in os.listdir(character_dir):
                if file.lower().endswith(('.jpg', '.jpeg', '.png', '.webp')):
                    print(f"    找到相似角色图片: {gender_try}/{age_try}/{style_try}/{culture_try}/{temp_try}/{file}")
                    return os.path.join(character_dir, file)
    
    # 如果所有搜索组合都失败，随机选择一张角色图片作为备选
    print(f"    所有搜索组合都失败，尝试随机选择角色图片...")
    random_image = get_random_character_image()
    if random_image:
        return random_image
    
    print(f"    未找到任何角色图片")
    return None

def find_character_image_by_attributes(gender, age_group, character_style, culture='Chinese', temperament='Common', prompt=None):
    """
    根据角色属性查找Character_Images目录中的角色图片，如果找不到则尝试根据prompt查找相似图片
    
    Args:
        gender: 性别 (Male/Female)
        age_group: 年龄段 (15-22_Youth/23-30_YoungAdult/25-40_FantasyAdult/31-45_MiddleAged)
        character_style: 风格 (Ancient/Fantasy/Modern/SciFi)
        culture: 文化类型 (Chinese/Western)，默认Chinese
        temperament: 气质类型 (Common/Royal/Chivalrous等)，默认Common
        prompt: 图片描述文本，用于相似度匹配，可选
    
    Returns:
        str: 角色图片文件路径，如果未找到返回None
    """
    # 构建Character_Images目录路径
    script_dir = os.path.dirname(os.path.abspath(__file__))
    character_images_dir = os.path.join(script_dir, 'Character_Images')
    
    # 构建具体的角色目录路径（5层结构）
    character_dir = os.path.join(character_images_dir, gender, age_group, character_style, culture, temperament)
    
    if os.path.exists(character_dir):
        # 查找目录中的图片文件
        for file in os.listdir(character_dir):
            if file.lower().endswith(('.jpg', '.jpeg', '.png', '.webp')):
                print(f"    找到角色图片: {gender}/{age_group}/{character_style}/{culture}/{temperament}/{file}")
                return os.path.join(character_dir, file)
        
        # 如果没有图片文件，检查是否有prompt.txt
        prompt_file = os.path.join(character_dir, 'prompt.txt')
        if os.path.exists(prompt_file):
            print(f"    找到角色描述文件但无图片: {gender}/{age_group}/{character_style}/{culture}/{temperament}/prompt.txt")
    else:
        print(f"    警告: 未找到角色目录 {gender}/{age_group}/{character_style}/{culture}/{temperament}")
    
    # 如果精确匹配失败且提供了prompt，尝试根据prompt查找相似图片
    if prompt:
        print(f"    尝试根据prompt查找相似角色图片...")
        return find_similar_character_image_by_prompt(prompt, gender, character_style)
    
    return None

def get_random_character_image():
    """
    从Character_Images目录中随机选择一张角色图片
    
    Returns:
        str: 随机角色图片文件路径，如果未找到返回None
    """
    script_dir = os.path.dirname(os.path.abspath(__file__))
    character_images_dir = os.path.join(script_dir, 'Character_Images')
    
    if not os.path.exists(character_images_dir):
        print(f"警告: Character_Images目录不存在: {character_images_dir}")
        return None
    
    # 收集所有图片文件
    all_images = []
    for root, dirs, files in os.walk(character_images_dir):
        for file in files:
            if file.lower().endswith(('.jpg', '.jpeg', '.png', '.webp')):
                all_images.append(os.path.join(root, file))
    
    if all_images:
        selected_image = random.choice(all_images)
        print(f"    随机选择角色图片: {os.path.relpath(selected_image, character_images_dir)}")
        return selected_image
    else:
        print("    警告: Character_Images目录中未找到任何图片文件")
        return None

def ensure_30_images_per_chapter(chapter_dir):
    """
    确保每个章节有固定的30张图片，不足的从Character_Images目录复制补足
    
    Args:
        chapter_dir: 章节目录路径
    
    Returns:
        bool: 是否成功确保30张图片
    """
    try:
        chapter_name = os.path.basename(chapter_dir)
        print(f"\n=== 检查章节 {chapter_name} 的图片数量 ===")
        
        # 统计现有图片数量
        existing_images = []
        for file in os.listdir(chapter_dir):
            if file.startswith(f"{chapter_name}_image_") and file.endswith('.jpeg'):
                existing_images.append(file)
        
        existing_count = len(existing_images)
        print(f"现有图片数量: {existing_count}")
        
        if existing_count >= 30:
            print(f"✓ 图片数量已满足要求 (>= 30张)")
            return True
        
        # 需要补足的图片数量
        needed_count = 30 - existing_count
        print(f"需要补足 {needed_count} 张图片")
        
        # 从Character_Images目录复制图片来补足
        success_count = 0
        for i in range(needed_count):
            # 计算新图片的编号
            new_image_index = existing_count + i + 1
            
            # 生成新图片文件名 (格式: chapter_xxx_image_xx_x.jpeg)
            # 假设每个分镜最多10个特写，按顺序分配
            scene_num = ((new_image_index - 1) // 10) + 1
            closeup_num = ((new_image_index - 1) % 10) + 1
            new_filename = f"{chapter_name}_image_{scene_num:02d}_{closeup_num}.jpeg"
            new_filepath = os.path.join(chapter_dir, new_filename)
            
            # 如果文件已存在，跳过
            if os.path.exists(new_filepath):
                print(f"    跳过已存在的文件: {new_filename}")
                success_count += 1
                continue
            
            # 随机选择一张角色图片
            source_image = get_random_character_image()
            if source_image:
                try:
                    # 复制图片并重命名
                    shutil.copy2(source_image, new_filepath)
                    print(f"    ✓ 复制图片: {os.path.basename(source_image)} -> {new_filename}")
                    success_count += 1
                except Exception as e:
                    print(f"    ✗ 复制图片失败: {e}")
            else:
                print(f"    ✗ 无法找到源图片进行复制")
        
        print(f"补足完成: 成功 {success_count}/{needed_count} 张")
        
        # 再次统计最终图片数量
        final_images = []
        for file in os.listdir(chapter_dir):
            if file.startswith(f"{chapter_name}_image_") and file.endswith('.jpeg'):
                final_images.append(file)
        
        final_count = len(final_images)
        print(f"最终图片数量: {final_count}")
        
        return final_count >= 30
        
    except Exception as e:
        print(f"确保30张图片时发生错误: {e}")
        return False

def encode_image_to_base64(image_path):
    """
    将图片文件编码为base64格式，包含实际图片类型信息
    
    Args:
        image_path: 图片文件路径
    
    Returns:
        str: base64编码的图片数据，格式为 data:image/<format>;base64,<data>
             如果编码失败返回None
    """
    try:
        with open(image_path, 'rb') as image_file:
            # 读取图片二进制数据
            image_data = image_file.read()
            # 编码为base64
            base64_data = base64.b64encode(image_data).decode('utf-8')
            
            # 获取图片格式 - 根据实际文件内容而不是扩展名
            import imghdr
            from pathlib import Path
            detected_format = imghdr.what(image_path)
            if detected_format:
                # 使用检测到的实际格式
                image_format = detected_format
            else:
                # 如果检测失败，回退到扩展名判断
                file_extension = Path(image_path).suffix.lower()
                if file_extension == '.jpg':
                    image_format = 'jpeg'
                else:
                    image_format = file_extension[1:]  # 去掉点号
            
            # 构造完整的data URL
            return f"data:image/{image_format};base64,{base64_data}"
            
    except Exception as e:
        print(f"编码图片为base64时发生错误: {e}")
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

def generate_image_with_character_async(prompt, output_path, character_images=None, style=None, max_retries=3):
    """
    使用角色图片异步生成图片，带重试机制
    
    Args:
        prompt: 图片描述
        output_path: 输出文件路径
        character_images: 角色图片路径列表
        style: 艺术风格，如果为None则使用配置文件中的默认风格
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
                print(f"🔄 第 {attempt} 次重试生成图片: {os.path.basename(output_path)}")
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
            
            print(f"正在生成{style}风格图片: {os.path.basename(output_path)}")
            
            # 构建完整的prompt
            full_prompt = "去掉衽领，交领，V领，换成高领圆领袍\n\
                人物姿势和背景变化要大\n\
                    以下内容为描述生成图片\n\
                        2d漫画，细线条，厚涂，简洁，柔和的灯光，平面插画，动漫美感，数字技术技艺\n\
                            " + style_prompt + "\n" + prompt
            
            if attempt == 0:  # 只在第一次尝试时打印完整prompt
                print("这里是完整的prompt===>>>{}".format(full_prompt))
            
            # 构建请求参数 - 使用配置文件中的值
            # form = {
            #     # "req_key": "high_aes_ip_v20",
            #     "req_key": "high_aes_ip_v20",
            #     "prompt": full_prompt,
            #     "llm_seed": 10 + attempt,  # 每次重试使用不同的seed
            #     "seed": 10 + attempt,
            #     "scale": 0.4,
            #     "ddim_steps": IMAGE_TWO_CONFIG['ddim_steps'],
            #     "width": IMAGE_TWO_CONFIG['default_width'],
            #     "height": IMAGE_TWO_CONFIG['default_height'],
            #     "ref_ip_weight": 0.5,
            #     "ref_id_weight": 0.5,
            #     "use_sr": IMAGE_TWO_CONFIG['use_sr'],
            #     "return_url": IMAGE_TWO_CONFIG['return_url'],
            #     "use_pre_llm": True,
            #     "negative_prompt": IMAGE_TWO_CONFIG.get('negative_prompt', []),
            #     "logo_info": {
            #         "add_logo": False,
            #         "position": 0,
            #         "language": 0,
            #         "opacity": 0.3,
            #         "logo_text_content": "这里是明水印内容"
            #     }
            # }
            form = {
                "req_key": "high_aes_ip_v20",
                "prompt": full_prompt,
                "llm_seed": -1,
                "seed": 10 + attempt,  # 每次重试使用不同的seed
                "scale": 3.5,
                "ddim_steps": IMAGE_TWO_CONFIG['ddim_steps'],
                "width": IMAGE_TWO_CONFIG['default_width'],
                "height": IMAGE_TWO_CONFIG['default_height'],
                "use_pre_llm": IMAGE_TWO_CONFIG['use_pre_llm'],
                "use_sr": IMAGE_TWO_CONFIG['use_sr'],
                "return_url": IMAGE_TWO_CONFIG['return_url'],  # 返回base64格式
                "negative_prompt": IMAGE_TWO_CONFIG['negative_prompt'],
                # "controlnet_args": [
                #     {
                #         "type": "depth",
                #         "binary_data_index": 0,
                #         "strength": 0.6
                #     }
                # ],
                "ref_ip_weight": 0,
                "ref_id_weight": 0.6,
                "logo_info": {
                    "add_logo": False,
                    "position": 0,
                    "language": 0,
                    "opacity": 0.3,
                    "logo_text_content": "这里是明水印内容"
                }
            }
            
            # 如果有角色图片，添加到请求中
            print(f"角色图片参数: {character_images}")
            if character_images:
                print(f"开始处理 {len(character_images)} 个角色图片")
                binary_data_base64_list = []
                for img_path in character_images:
                    print(f"处理角色图片: {img_path}")
                    if img_path and os.path.exists(img_path):
                        base64_data = encode_image_to_base64(img_path)
                        if base64_data:
                            # 从data URL中提取纯base64数据（去掉"data:image/xxx;base64,"前缀）
                            if base64_data.startswith('data:'):
                                pure_base64 = base64_data.split(',')[1]
                            else:
                                pure_base64 = base64_data
                            binary_data_base64_list.append(pure_base64)
                            print(f"成功编码角色图片: {img_path}")
                        else:
                            print(f"编码角色图片失败: {img_path}")
                    else:
                        print(f"角色图片不存在: {img_path}")
                
                if binary_data_base64_list:
                    form["binary_data_base64"] = binary_data_base64_list
                    print(f"已添加 {len(binary_data_base64_list)} 个角色图片到请求中")
                else:
                    print("没有有效的角色图片数据，尝试随机选择角色图片")
                    random_image = get_random_character_image()
                    if random_image:
                        base64_data = encode_image_to_base64(random_image)
                        if base64_data:
                            form["binary_data_base64"] = [base64_data]
                            print(f"已添加随机角色图片到请求中: {random_image}")
                        else:
                            print(f"编码随机角色图片失败: {random_image}")
                    else:
                        print("未能获取随机角色图片")
            else:
                print("没有角色图片参数，尝试随机选择角色图片")
                random_image = get_random_character_image()
                if random_image:
                    base64_data = encode_image_to_base64(random_image)
                    if base64_data:
                        form["binary_data_base64"] = [base64_data]
                        print(f"已添加随机角色图片到请求中: {random_image}")
                    else:
                        print(f"随机角色图片编码失败: {random_image}")
                else:
                    print("未能获取随机角色图片")
            
            # 调用异步API提交任务
            if attempt == 0:  # 只在第一次尝试时打印详细信息
                print("这里是响应前===============")
            print(form.keys())
            resp = visual_service.cv_sync2async_submit_task(form)
            if attempt == 0:
                print("这里是响应参数===============")
                print(resp)
                print("这里是响应参数===============")
            
            # 检查响应
            if 'data' in resp and 'task_id' in resp['data']:
                task_id = resp['data']['task_id']
                print(f"✓ 任务提交成功，Task ID: {task_id}")
                
                # 保存任务信息到async_tasks目录
                task_info = {
                    'task_id': task_id,
                    'output_path': output_path,
                    'filename': os.path.basename(output_path),
                    'prompt': prompt,
                    'full_prompt': full_prompt,
                    'character_images': character_images or [],
                    'style': style,
                    'submit_time': time.time(),
                    'status': 'submitted',
                    'attempt': attempt + 1
                }
                
                # 使用统一的保存函数
                async_tasks_dir = 'async_tasks'
                save_task_info(task_id, task_info, async_tasks_dir)
                return True
            else:
                error_msg = resp.get('message', '未知错误')
                print(f"✗ 任务提交失败 (尝试 {attempt + 1}/{max_retries + 1}): {error_msg}")
                
                if attempt == max_retries:
                    print(f"✗ 达到最大重试次数，任务最终失败")
                    return False
                
                # 继续下一次重试
                continue
                
        except Exception as e:
            print(f"✗ 生成图片时发生错误 (尝试 {attempt + 1}/{max_retries + 1}): {e}")
            
            if attempt == max_retries:
                print(f"✗ 达到最大重试次数，任务最终失败")
                return False
            
            # 继续下一次重试
            continue
    
    return False

def generate_image_with_character(prompt, output_path, character_images=None, style=None):
    """
    兼容性函数：调用异步版本
    
    Args:
        prompt: 图片描述
        output_path: 输出文件路径
        character_images: 角色图片路径列表
        style: 艺术风格，如果为None则使用配置文件中的默认风格
    
    Returns:
        bool: 是否成功提交任务
    """
    return generate_image_with_character_async(prompt, output_path, character_images, style)

def generate_images_for_chapter(chapter_dir):
    """
    为单个章节生成图片 - 按照10个分镜每个分镜3张图片的规则生成30张图片
    先尝试API生成，失败后从Character_Images目录复制
    
    Args:
        chapter_dir: 章节目录路径
    
    Returns:
        bool: 是否成功生成图片
    """
    try:
        chapter_name = os.path.basename(chapter_dir)
        print(f"=== 开始为章节 {chapter_name} 生成图片 ===")
        print(f"章节目录: {chapter_dir}")
        print(f"生成规则: 10个分镜，每个分镜3张图片，共30张")
        
        if not os.path.exists(chapter_dir):
            print(f"错误: 章节目录不存在 {chapter_dir}")
            return False
        
        # 查找narration文件
        narration_file = os.path.join(chapter_dir, "narration.txt")
        if not os.path.exists(narration_file):
            print(f"错误: narration文件不存在 {narration_file}")
            return False
        
        # 解析narration文件
        scenes, drawing_style, character_map = parse_narration_file(narration_file)
        
        if not scenes:
            print(f"错误: 未找到分镜信息")
            return False
        
        print(f"从narration文件解析到 {len(scenes)} 个分镜")
        
        # 获取绘画风格的model_prompt
        style_prompt = ""
        if drawing_style and drawing_style in STORY_STYLE:
            style_config = STORY_STYLE[drawing_style]
            if isinstance(style_config.get('model_prompt'), list):
                style_prompt = style_config['model_prompt'][0]  # 取第一个
            else:
                style_prompt = style_config.get('model_prompt', '')
            print(f"使用风格提示: {style_prompt}")
        
        success_count = 0
        
        # 按照10个分镜每个分镜3张图片的规则生成30张图片
        for scene_num in range(1, 11):  # 10个分镜
            print(f"\n  处理第 {scene_num}/10 个分镜")
            
            # 每个分镜生成3张图片
            for image_num in range(1, 4):  # 每个分镜3张图片
                image_filename = f"{chapter_name}_image_{scene_num:02d}_{image_num}.jpeg"
                image_path = os.path.join(chapter_dir, image_filename)
                
                print(f"    生成图片 {image_num}/3: {image_filename}")
                
                # 如果图片已存在，跳过
                if os.path.exists(image_path):
                    print(f"    ✓ 图片已存在，跳过: {image_filename}")
                    success_count += 1
                    continue
                
                # 尝试从解析的分镜中获取对应的prompt
                prompt = ""
                character_images = []
                
                if scene_num <= len(scenes):
                    # 使用对应分镜的信息
                    scene = scenes[scene_num - 1]
                    closeups = scene['closeups']
                    
                    if closeups:
                        # 循环使用分镜中的特写信息
                        closeup_index = (image_num - 1) % len(closeups)
                        closeup = closeups[closeup_index]
                        
                        prompt = closeup['prompt']
                        character = closeup.get('character', '')
                        gender = closeup.get('gender', '')
                        age_group = closeup.get('age_group', '')
                        character_style = closeup.get('character_style', '')
                        culture = closeup.get('culture', 'Chinese')
                        temperament = closeup.get('temperament', 'Common')
                        era_background = closeup.get('era_background', '')
                        
                        print(f"    使用分镜信息: {character} ({gender}/{age_group}/{character_style}) 时代背景: {era_background}")
                        
                        # 查找角色图片 - 优先根据角色姓名匹配章节中的角色图片
                        char_img_path = None
                        if character:
                            # 首先尝试根据角色姓名在当前章节目录中查找角色图片，传递时代背景信息
                            char_img_path = find_character_image(chapter_dir, character, era_background)
                            if char_img_path:
                                character_images.append(char_img_path)
                                print(f"    根据角色姓名找到角色图片: {char_img_path}")
                            else:
                                print(f"    未找到角色 {character} 的图片，尝试根据属性查找...")
                        
                        # 如果根据角色姓名未找到，则根据角色属性查找
                        if not char_img_path and gender and age_group and character_style:
                            char_img_path = find_character_image_by_attributes(gender, age_group, character_style, culture, temperament, prompt)
                            if char_img_path:
                                character_images.append(char_img_path)
                                print(f"    根据属性找到角色图片: {char_img_path}")
                        
                        # 根据角色性别调整视角
                        view_angle_prompt = ""
                        if gender:
                            if gender.lower() in ['female', '女']:
                                view_angle_prompt = "，背部视角，看不到领口和正面"
                            else:
                                view_angle_prompt = "，正面视角，清晰面部特征"
                        
                        # 构建完整的prompt
                        if style_prompt:
                            full_prompt = f"{prompt}{view_angle_prompt}，{style_prompt}"
                        else:
                            full_prompt = f"{prompt}{view_angle_prompt}"
                else:
                    # 如果分镜数量不足，使用通用prompt
                    full_prompt = f"古代中国场景，{style_prompt}" if style_prompt else "古代中国场景"
                    print(f"    使用通用prompt（分镜不足）")
                
                # 先尝试API生成
                api_success = False
                if full_prompt:
                    print(f"    尝试API生成...")
                    api_success = generate_image_with_character_async(full_prompt, image_path, character_images, drawing_style)
                    
                    if api_success:
                        print(f"    ✓ API生成任务提交成功")
                        success_count += 1
                    else:
                        print(f"    ✗ API生成失败")
                
                # 如果API生成失败，从Character_Images复制图片
                if not api_success:
                    print(f"    尝试从Character_Images复制图片...")
                    source_image = get_random_character_image()
                    if source_image:
                        try:
                            shutil.copy2(source_image, image_path)
                            print(f"    ✓ 复制成功: {os.path.basename(source_image)} -> {image_filename}")
                            success_count += 1
                        except Exception as e:
                            print(f"    ✗ 复制失败: {e}")
                    else:
                        print(f"    ✗ 无法找到源图片进行复制")
        
        print(f"\n章节 {chapter_name} 处理完成，成功生成/复制 {success_count}/30 张图片")
        
        return success_count >= 30
        
    except Exception as e:
        print(f"生成章节图片时发生错误: {e}")
        return False

def generate_images_from_scripts(data_dir):
    """
    遍历数据目录，为每个章节生成图片 - 按照10个分镜每个分镜3张图片的规则
    
    Args:
        data_dir: 数据目录路径
    
    Returns:
        bool: 是否成功生成图片
    """
    try:
        print(f"=== 开始批量生成图片 ===")
        print(f"数据目录: {data_dir}")
        print(f"生成规则: 每个章节10个分镜，每个分镜3张图片，共30张")
        
        if not os.path.exists(data_dir):
            print(f"错误: 数据目录不存在 {data_dir}")
            return False
        
        # 查找所有章节目录
        chapter_dirs = []
        for item in os.listdir(data_dir):
            item_path = os.path.join(data_dir, item)
            if os.path.isdir(item_path) and item.startswith('chapter_'):
                chapter_dirs.append(item_path)
        
        if not chapter_dirs:
            print(f"错误: 在 {data_dir} 中没有找到章节目录")
            return False
        
        chapter_dirs.sort()
        print(f"找到 {len(chapter_dirs)} 个章节目录")
        
        success_chapters = 0
        
        # 处理每个章节
        for chapter_dir in chapter_dirs:
            chapter_name = os.path.basename(chapter_dir)
            print(f"\n--- 处理章节: {chapter_name} ---")
            
            # 调用单章节生成函数
            if generate_images_for_chapter(chapter_dir):
                print(f"✓ 章节 {chapter_name} 处理成功")
                success_chapters += 1
            else:
                print(f"✗ 章节 {chapter_name} 处理失败")
        
        print(f"\n批量图片生成完成，成功处理 {success_chapters}/{len(chapter_dirs)} 个章节")
        return success_chapters > 0
        
    except Exception as e:
        print(f"批量生成图片时发生错误: {e}")
        return False

def count_total_closeups(data_dir):
    """
    统计所有章节的图片特写总数
    
    Args:
        data_dir: 数据目录路径
    
    Returns:
        tuple: (总特写数量, 章节统计详情)
    """
    total_closeups = 0
    chapter_stats = {}
    
    try:
        if not os.path.exists(data_dir):
            return 0, {}
        
        # 查找所有章节目录
        chapter_dirs = []
        for item in os.listdir(data_dir):
            item_path = os.path.join(data_dir, item)
            if os.path.isdir(item_path) and item.startswith('chapter_'):
                chapter_dirs.append(item_path)
        
        chapter_dirs.sort()
        
        for chapter_dir in chapter_dirs:
            chapter_name = os.path.basename(chapter_dir)
            narration_file = os.path.join(chapter_dir, "narration.txt")
            
            if os.path.exists(narration_file):
                scenes, _, _ = parse_narration_file(narration_file)
                chapter_closeups = sum(len(scene['closeups']) for scene in scenes)
                chapter_stats[chapter_name] = chapter_closeups
                total_closeups += chapter_closeups
        
        return total_closeups, chapter_stats
        
    except Exception as e:
        print(f"统计图片特写数量时发生错误: {e}")
        return 0, {}

def check_and_retry_failed_tasks(async_tasks_dir='async_tasks', max_retries=3):
    """
    检查async_tasks目录中的失败任务并重试
    
    Args:
        async_tasks_dir: 异步任务目录
        max_retries: 最大重试次数
    
    Returns:
        tuple: (重试成功数量, 重试失败数量)
    """
    if not os.path.exists(async_tasks_dir):
        return 0, 0
    
    retry_success = 0
    retry_failed = 0
    
    print(f"\n=== 检查并重试失败任务 ===")
    
    # 获取所有任务文件
    task_files = [f for f in os.listdir(async_tasks_dir) if f.endswith('.txt')]
    
    for task_file in task_files:
        task_path = os.path.join(async_tasks_dir, task_file)
        
        try:
            with open(task_path, 'r', encoding='utf-8') as f:
                task_info = json.load(f)
            
            # 检查任务状态
            status = task_info.get('status', 'unknown')
            task_id = task_info.get('task_id')
            
            # 如果任务没有task_id或状态为失败，需要重试
            if not task_id or status in ['failed', 'error']:
                print(f"发现需要重试的任务: {task_info.get('filename', 'unknown')}")
                
                # 重新提交任务
                output_path = task_info.get('output_path')
                prompt = task_info.get('prompt')
                character_images = task_info.get('character_images', [])
                style = task_info.get('style')
                
                if output_path and prompt:
                    # 删除旧的任务文件
                    os.remove(task_path)
                    
                    # 重新提交任务
                    if generate_image_with_character_async(prompt, output_path, character_images, style, max_retries):
                        print(f"✓ 重试成功: {os.path.basename(output_path)}")
                        retry_success += 1
                    else:
                        print(f"✗ 重试失败: {os.path.basename(output_path)}")
                        retry_failed += 1
                else:
                    print(f"✗ 任务信息不完整，跳过重试")
                    retry_failed += 1
        
        except Exception as e:
            print(f"处理任务文件时发生错误 {task_file}: {e}")
            retry_failed += 1
    
    print(f"重试完成: 成功 {retry_success} 个，失败 {retry_failed} 个")
    return retry_success, retry_failed

def main():
    parser = argparse.ArgumentParser(description='独立的图片生成脚本')
    parser.add_argument('input_path', help='输入路径（可以是单个章节目录或包含多个章节的数据目录）')
    parser.add_argument('--retry-failed', action='store_true', help='检查并重试失败的任务')
    
    args = parser.parse_args()
    
    print(f"目标路径: {args.input_path}")
    
    # 如果是重试模式，只处理失败任务
    if args.retry_failed:
        print("\n=== 重试失败任务模式 ===")
        retry_success, retry_failed = check_and_retry_failed_tasks()
        if retry_success > 0 or retry_failed == 0:
            print(f"\n✓ 重试完成")
        else:
            print(f"\n✗ 重试失败")
            sys.exit(1)
        return
    
    # 检查输入路径是单个章节还是数据目录
    if os.path.isdir(args.input_path):
        # 检查是否是单个章节目录
        if os.path.basename(args.input_path).startswith('chapter_') and os.path.exists(os.path.join(args.input_path, 'narration.txt')):
            print("检测到单个章节目录")
            # 统计单个章节的特写数量
            narration_file = os.path.join(args.input_path, 'narration.txt')
            scenes, _, _ = parse_narration_file(narration_file)
            total_closeups = sum(len(scene['closeups']) for scene in scenes)
            print(f"该章节共有 {total_closeups} 个图片特写")
            
            success = generate_images_for_chapter(args.input_path)
        else:
            print("检测到数据目录，将处理所有章节")
            # 统计所有章节的特写数量
            total_closeups, chapter_stats = count_total_closeups(args.input_path)
            print(f"\n=== 图片特写统计 ===")
            print(f"总特写数量: {total_closeups}")
            for chapter, count in chapter_stats.items():
                print(f"  {chapter}: {count} 个特写")
            
            success = generate_images_from_scripts(args.input_path)
            
            # 生成完成后，检查并重试失败任务
            print(f"\n=== 第一轮生成完成，开始检查失败任务 ===")
            retry_success, retry_failed = check_and_retry_failed_tasks()
            
            if retry_failed > 0:
                print(f"\n仍有 {retry_failed} 个任务失败，请稍后使用 --retry-failed 参数重试")
    else:
        print(f"错误: 路径不存在 {args.input_path}")
        sys.exit(1)
    
    if success:
        print(f"\n✓ 图片生成完成")
    else:
        print(f"\n✗ 图片生成失败")
        sys.exit(1)
    
    print("\n=== 处理完成 ===")

if __name__ == '__main__':
    main()