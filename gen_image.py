# !/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
独立的图片生成脚本（同步版本）
遍历章节目录，为每个分镜生成图片
"""

import os
import re
import argparse
import base64
import sys
import json
import time
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
    解析narration.txt文件中的角色定义
    
    Args:
        content: narration.txt文件内容
    
    Returns:
        dict: 角色编号到角色信息的映射
    """
    character_map = {}
    
    # 解析主角定义
    protagonist_pattern = r'<主角(\d+)>(.*?)</主角\d+>'
    protagonist_matches = re.findall(protagonist_pattern, content, re.DOTALL)
    
    for num, char_content in protagonist_matches:
        char_info = {}
        
        # 提取角色属性
        name_match = re.search(r'<姓名>([^<]+)</姓名>', char_content)
        gender_match = re.search(r'<性别>([^<]+)</性别>', char_content)
        age_match = re.search(r'<年龄段>([^<]+)</年龄段>', char_content)
        style_match = re.search(r'<风格>([^<]+)</风格>', char_content)
        culture_match = re.search(r'<文化>([^<]+)</文化>', char_content)
        temperament_match = re.search(r'<气质>([^<]+)</气质>', char_content)
        number_match = re.search(r'<角色编号>([^<]+)</角色编号>', char_content)
        
        if name_match:
            char_info['name'] = name_match.group(1).strip()
        if gender_match:
            char_info['gender'] = gender_match.group(1).strip()
        if age_match:
            char_info['age_group'] = age_match.group(1).strip()
        if style_match:
            char_info['character_style'] = style_match.group(1).strip()
        if culture_match:
            char_info['culture'] = culture_match.group(1).strip()
        if temperament_match:
            char_info['temperament'] = temperament_match.group(1).strip()
        if number_match:
            char_info['number'] = number_match.group(1).strip()
        
        # 使用多种可能的键来映射角色
        keys = [f'主角{num}', f'主角{int(num):02d}']
        if number_match:
            keys.append(number_match.group(1).strip())
        
        for key in keys:
            character_map[key] = char_info
    
    # 解析配角定义
    supporting_pattern = r'<配角(\d+)>(.*?)</配角\d+>'
    supporting_matches = re.findall(supporting_pattern, content, re.DOTALL)
    
    for num, char_content in supporting_matches:
        char_info = {}
        
        # 提取角色属性
        name_match = re.search(r'<姓名>([^<]+)</姓名>', char_content)
        gender_match = re.search(r'<性别>([^<]+)</性别>', char_content)
        age_match = re.search(r'<年龄段>([^<]+)</年龄段>', char_content)
        style_match = re.search(r'<风格>([^<]+)</风格>', char_content)
        culture_match = re.search(r'<文化>([^<]+)</文化>', char_content)
        temperament_match = re.search(r'<气质>([^<]+)</气质>', char_content)
        number_match = re.search(r'<角色编号>([^<]+)</角色编号>', char_content)
        
        if name_match:
            char_info['name'] = name_match.group(1).strip()
        if gender_match:
            char_info['gender'] = gender_match.group(1).strip()
        if age_match:
            char_info['age_group'] = age_match.group(1).strip()
        if style_match:
            char_info['character_style'] = style_match.group(1).strip()
        if culture_match:
            char_info['culture'] = culture_match.group(1).strip()
        if temperament_match:
            char_info['temperament'] = temperament_match.group(1).strip()
        if number_match:
            char_info['number'] = number_match.group(1).strip()
        
        # 使用多种可能的键来映射角色
        keys = [f'配角{num}', f'配角{int(num):02d}']
        if number_match:
            keys.append(number_match.group(1).strip())
        
        for key in keys:
            character_map[key] = char_info
    
    return character_map

def parse_narration_file(narration_file_path):
    """
    解析narration.txt文件，提取分镜信息、图片prompt和绘画风格
    
    Args:
        narration_file_path: narration.txt文件路径
    
    Returns:
        tuple: (分镜信息列表, 绘画风格, 角色映射)
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
        print(f"解析到 {len(character_map)} 个角色映射")
        
        # 解析绘画风格
        style_match = re.search(r'<绘画风格>([^<]+)</绘画风格>', content)
        drawing_style = style_match.group(1) if style_match else None
        
        # 提取分镜信息
        scene_pattern = r'<分镜\d+>(.*?)</分镜\d+>'
        scene_matches = re.findall(scene_pattern, content, re.DOTALL)
        
        for scene_content in scene_matches:
            scene_info = {}
            
            # 提取解说内容
            narration_match = re.search(r'<解说内容>([^<]+)</解说内容>', scene_content, re.DOTALL)
            if narration_match:
                scene_info['narration'] = narration_match.group(1).strip()
            
            # 提取所有特写
            scene_info['closeups'] = []
            # 动态检测特写数量，最多支持10个特写
            for i in range(1, 11):  # 图片特写1到图片特写10
                closeup_pattern = f'<图片特写{i}>(.*?)</图片特写{i}>'
                closeup_match = re.search(closeup_pattern, scene_content, re.DOTALL)
                if closeup_match:
                    closeup_content = closeup_match.group(1)
                    closeup_info = {}
                    
                    # 首先尝试提取特写人物和角色编号
                    character_match = re.search(r'<特写人物>([^<]+)</特写人物>', closeup_content)
                    character_id_match = re.search(r'<角色编号>([^<]+)</角色编号>', closeup_content)
                    
                    if character_match and character_id_match:
                        character_name = character_match.group(1).strip()
                        character_id = character_id_match.group(1).strip()
                        
                        # 从角色映射中获取角色信息
                        if character_id in character_map:
                            char_info = character_map[character_id]
                            closeup_info['gender'] = char_info.get('gender', '')
                            closeup_info['age_group'] = char_info.get('age_group', '')
                            closeup_info['character_style'] = char_info.get('character_style', '')
                            closeup_info['culture'] = char_info.get('culture', 'Chinese')
                            closeup_info['temperament'] = char_info.get('temperament', 'Common')
                            closeup_info['character_name'] = char_info.get('name', character_name)
                            closeup_info['character_id'] = character_id
                            closeup_info['number'] = char_info.get('number', '')
                        else:
                            print(f"警告: 未找到角色编号 {character_id} 的定义")
                            # 使用默认值
                            closeup_info['gender'] = ''
                            closeup_info['age_group'] = ''
                            closeup_info['character_style'] = ''
                            closeup_info['culture'] = 'Chinese'
                            closeup_info['temperament'] = 'Common'
                            closeup_info['character_name'] = character_name
                            closeup_info['character_id'] = character_id
                    else:
                        # 回退到原有的解析方式（兼容旧格式）
                        gender_match = re.search(r'<性别>([^<]+)</性别>', closeup_content)
                        age_match = re.search(r'<年龄段>([^<]+)</年龄段>', closeup_content)
                        style_match = re.search(r'<风格>([^<]+)</风格>', closeup_content)
                        
                        if gender_match and age_match and style_match:
                            closeup_info['gender'] = gender_match.group(1).strip().replace('根据章节内容选择：', '')
                            closeup_info['age_group'] = age_match.group(1).strip().replace('根据章节内容选择：', '')
                            closeup_info['character_style'] = style_match.group(1).strip().replace('根据章节内容选择：', '')
                            closeup_info['culture'] = 'Chinese'
                            closeup_info['temperament'] = 'Common'
                    
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

def find_character_image(chapter_path, character_name):
    """
    查找角色图片文件（旧版本兼容）
    
    Args:
        chapter_path: 章节目录路径
        character_name: 角色名称
    
    Returns:
        str: 角色图片文件路径，如果未找到返回None
    """
    try:
        chapter_name = os.path.basename(chapter_path)
        # 移除角色名称中的&符号
        safe_character_name = character_name.replace('&', '')
        # 构造角色图片文件名模式
        pattern = f"{chapter_name}_character_*_{safe_character_name}.jpeg"
        
        # 在章节目录中查找匹配的文件
        for filename in os.listdir(chapter_path):
            if filename.endswith(f"_{safe_character_name}.jpeg") and "character" in filename:
                image_path = os.path.join(chapter_path, filename)
                print(f"找到角色图片: {image_path}")
                return image_path
        
        print(f"未找到角色 {character_name} 的图片文件")
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

def download_image(image_data_base64, output_path):
    """
    将base64编码的图片数据保存到文件
    
    Args:
        image_data_base64: base64编码的图片数据
        output_path: 输出文件路径
    
    Returns:
        bool: 是否成功保存
    """
    try:
        # 确保输出目录存在
        os.makedirs(os.path.dirname(output_path), exist_ok=True)
        
        # 解码base64数据
        image_data = base64.b64decode(image_data_base64)
        
        # 保存到文件
        with open(output_path, 'wb') as f:
            f.write(image_data)
        
        print(f"图片已保存: {output_path}")
        return True
        
    except Exception as e:
        print(f"保存图片时发生错误: {e}")
        return False

def generate_image_with_character(prompt, output_path, character_images=None, style=None):
    """
    使用角色图片同步生成图片
    
    Args:
        prompt: 图片描述
        output_path: 输出文件路径
        character_images: 角色图片路径列表
        style: 艺术风格，如果为None则使用配置文件中的默认风格
    
    Returns:
        bool: 是否成功生成图片
    """
    try:
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
        full_prompt = "以以下内容为描述生成图片\n宫崎骏动漫风格，数字插画,高饱和度,卡通,简约画风,完整色块,整洁的画面,宫崎骏艺术风格,高饱和的色彩和柔和的阴影,童话色彩,人物着装：圆领袍 \n\n" + style_prompt + "\n\n" + prompt + "\n\n"
        
        print("这里是完整的prompt===>>>{}".format(full_prompt))
        
        # 构建请求参数 - 使用配置文件中的值
        form = {
            "req_key": IMAGE_TWO_CONFIG['req_key'],
            "prompt": full_prompt,
            "llm_seed": -1,
            "seed": 10,
            "scale": IMAGE_TWO_CONFIG['scale'],
            "ddim_steps": IMAGE_TWO_CONFIG['ddim_steps'],
            "width": IMAGE_TWO_CONFIG['default_width'],
            "height": IMAGE_TWO_CONFIG['default_height'],
            "use_pre_llm": IMAGE_TWO_CONFIG['use_pre_llm'],
            "use_sr": IMAGE_TWO_CONFIG['use_sr'],
            "return_url": IMAGE_TWO_CONFIG['return_url'],  # 返回base64格式
            "negative_prompt": IMAGE_TWO_CONFIG['negative_prompt'],
            "ref_ip_weight": 0,
            "ref_id_weight": 0.4,
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
            binary_data_list = []
            for img_path in character_images:
                print(f"处理角色图片: {img_path}")
                if img_path and os.path.exists(img_path):
                    base64_data = encode_image_to_base64(img_path)
                    if base64_data:
                        binary_data_list.append(base64_data)
                        print(f"成功添加角色图片: {img_path}")
                    else:
                        print(f"角色图片编码失败: {img_path}")
                else:
                    print(f"角色图片不存在: {img_path}")
            
            if binary_data_list:
                form["binary_data_base64"] = binary_data_list
                print(f"已添加 {len(binary_data_list)} 个角色图片到请求中")
            else:
                print("没有有效的角色图片数据，尝试随机选择角色图片")
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
        
        # 调用同步API
        resp = visual_service.cv_process(form)
        print(resp)
        
        # 检查响应
        if 'data' in resp and 'image_urls' in resp['data']:
            image_urls = resp['data']['image_urls']
            if image_urls:
                # 获取第一张图片的base64数据
                image_data_base64 = image_urls[0]
                
                # 保存图片
                if download_image(image_data_base64, output_path):
                    print(f"✓ 图片生成成功: {output_path}")
                    return True
                else:
                    print(f"✗ 图片保存失败: {output_path}")
                    return False
            else:
                print(f"✗ 响应中没有图片数据")
                return False
        else:
            print(f"✗ 图片生成失败: {resp}")
            return False
            
    except Exception as e:
        print(f"生成图片时发生错误: {e}")
        return False

def generate_images_for_chapter(chapter_dir):
    """
    为单个章节生成图片
    
    Args:
        chapter_dir: 章节目录路径
    
    Returns:
        bool: 是否成功生成图片
    """
    try:
        chapter_name = os.path.basename(chapter_dir)
        print(f"=== 开始为章节 {chapter_name} 生成图片 ===")
        print(f"章节目录: {chapter_dir}")
        
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
        
        print(f"找到 {len(scenes)} 个分镜")
        
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
        
        # 为每个分镜的每个特写生成图片
        for i, scene in enumerate(scenes, 1):
            closeups = scene['closeups']
            
            print(f"\n  处理第 {i}/{len(scenes)} 个分镜，包含 {len(closeups)} 个特写")
            
            # 为每个特写生成图片
            for j, closeup in enumerate(closeups, 1):
                prompt = closeup['prompt']
                gender = closeup.get('gender', '')
                age_group = closeup.get('age_group', '')
                character_style = closeup.get('character_style', '')
                culture = closeup.get('culture', 'Chinese')
                temperament = closeup.get('temperament', 'Common')
                character_name = closeup.get('character_name', '')
                character_id = closeup.get('character_id', '')
                
                print(f"    生成特写 {j}: {chapter_name}_image_{i:02d}_{j}.jpeg")
                if character_name and character_id:
                    print(f"    特写人物: {character_name} ({character_id}) - {gender}/{age_group}/{character_style}/{culture}/{temperament}")
                else:
                    print(f"    特写人物: {gender}/{age_group}/{character_style}/{culture}/{temperament}")
                
                # 查找当前特写的角色图片（基于Character_Images目录结构）
                character_images = []
                if gender and age_group and character_style:
                    print(f"    查找角色图片: {gender}/{age_group}/{character_style}/{culture}/{temperament}")
                    char_img_path = find_character_image_by_attributes(gender, age_group, character_style, culture, temperament, prompt)
                    if char_img_path:
                        character_images.append(char_img_path)
                        print(f"    找到角色图片: {char_img_path}")
                    else:
                        print(f"    未找到角色图片")
                else:
                    print(f"    角色信息不完整，跳过角色图片查找")
                
                # 根据角色性别调整视角
                view_angle_prompt = ""
                if gender:
                    print(f"    角色性别: {gender}")
                    
                    # 根据性别决定视角
                    if gender.lower() in ['female', '女']:
                        view_angle_prompt = "，背部视角，看不到领口和正面"
                    else:
                        view_angle_prompt = "，正面视角，清晰面部特征"
                
                # 构建完整的prompt，加入风格提示和视角要求
                if style_prompt:
                    full_prompt = f"{prompt}{view_angle_prompt}，{style_prompt}"
                else:
                    full_prompt = f"{prompt}{view_angle_prompt}"
                
                # 生成图片
                image_path = os.path.join(chapter_dir, f"{chapter_name}_image_{i:02d}_{j}.jpeg")
                
                if generate_image_with_character(full_prompt, image_path, character_images, drawing_style):
                    print(f"    ✓ 特写 {j} 生成成功")
                    success_count += 1
                else:
                    print(f"    ✗ 特写 {j} 生成失败")
        
        # 计算该章节生成的图片总数
        total_images = sum(len(scene['closeups']) for scene in scenes)
        print(f"\n章节 {chapter_name} 处理完成，共 {len(scenes)} 个分镜，成功生成 {success_count}/{total_images} 张图片")
        return success_count > 0
        
    except Exception as e:
        print(f"生成章节图片时发生错误: {e}")
        return False

def generate_images_from_scripts(data_dir):
    """
    遍历数据目录，为每个章节的分镜生成图片
    
    Args:
        data_dir: 数据目录路径
    
    Returns:
        bool: 是否成功生成图片
    """
    try:
        print(f"=== 开始生成图片 ===")
        print(f"数据目录: {data_dir}")
        
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
        
        success_count = 0
        
        # 处理每个章节
        for chapter_dir in chapter_dirs:
            chapter_name = os.path.basename(chapter_dir)
            print(f"\n--- 处理章节: {chapter_name} ---")
            
            # 查找narration文件
            narration_file = os.path.join(chapter_dir, "narration.txt")
            if not os.path.exists(narration_file):
                print(f"警告: narration文件不存在 {narration_file}")
                continue
            
            # 解析narration文件
            scenes, drawing_style, character_map = parse_narration_file(narration_file)
            
            if not scenes:
                print(f"警告: 未找到分镜信息")
                continue
            
            print(f"找到 {len(scenes)} 个分镜")
            
            # 获取绘画风格的model_prompt
            style_prompt = ""
            if drawing_style and drawing_style in STORY_STYLE:
                style_config = STORY_STYLE[drawing_style]
                if isinstance(style_config.get('model_prompt'), list):
                    style_prompt = style_config['model_prompt'][0]  # 取第一个
                else:
                    style_prompt = style_config.get('model_prompt', '')
                print(f"使用风格提示: {style_prompt}")
            
            # 为每个分镜的每个特写生成图片
            for i, scene in enumerate(scenes, 1):
                closeups = scene['closeups']
                
                print(f"\n  处理第 {i}/{len(scenes)} 个分镜，包含 {len(closeups)} 个特写")
                
                # 为每个特写生成图片
                for j, closeup in enumerate(closeups, 1):
                    prompt = closeup['prompt']
                    gender = closeup.get('gender', '')
                    age_group = closeup.get('age_group', '')
                    character_style = closeup.get('character_style', '')
                    culture = closeup.get('culture', 'Chinese')
                    temperament = closeup.get('temperament', 'Common')
                    character_name = closeup.get('character_name', '')
                    character_id = closeup.get('character_id', '')
                    
                    print(f"    生成特写 {j}: {chapter_name}_image_{i:02d}_{j}.jpeg")
                    if character_name and character_id:
                        print(f"    特写人物: {character_name} ({character_id}) - {gender}/{age_group}/{character_style}/{culture}/{temperament}")
                    else:
                        print(f"    特写人物: {gender}/{age_group}/{character_style}/{culture}/{temperament}")
                    
                    # 查找当前特写的角色图片（基于Character_Images目录结构）
                    character_images = []
                    if gender and age_group and character_style:
                        print(f"    查找角色图片: {gender}/{age_group}/{character_style}/{culture}/{temperament}")
                        char_img_path = find_character_image_by_attributes(gender, age_group, character_style, culture, temperament, prompt)
                        if char_img_path:
                            character_images.append(char_img_path)
                            print(f"    找到角色图片: {char_img_path}")
                        else:
                            print(f"    未找到角色图片")
                    else:
                        print(f"    角色信息不完整，跳过角色图片查找")
                    
                    # 根据角色性别调整视角
                    view_angle_prompt = ""
                    if gender:
                        print(f"    角色性别: {gender}")
                        
                        # 根据性别决定视角
                        if gender.lower() in ['female', '女']:
                            view_angle_prompt = "，背部视角，看不到领口和正面"
                        else:
                            view_angle_prompt = "，正面视角，清晰面部特征"
                    
                    # 构建完整的prompt，加入风格提示和视角要求
                    if style_prompt:
                        full_prompt = f"{prompt}{view_angle_prompt}，{style_prompt}"
                    else:
                        full_prompt = f"{prompt}{view_angle_prompt}"
                    
                    # 生成图片
                    image_path = os.path.join(chapter_dir, f"{chapter_name}_image_{i:02d}_{j}.jpeg")
                    
                    if generate_image_with_character(full_prompt, image_path, character_images, drawing_style):
                        print(f"    ✓ 特写 {j} 生成成功")
                        success_count += 1
                    else:
                        print(f"    ✗ 特写 {j} 生成失败")
            
            # 计算该章节生成的图片总数
            chapter_image_count = sum(len(scene['closeups']) for scene in scenes)
            print(f"章节 {chapter_name} 处理完成，共 {len(scenes)} 个分镜，成功生成 {chapter_image_count} 张图片")
        
        print(f"\n图片生成完成，成功生成 {success_count} 张图片")
        return success_count > 0
        
    except Exception as e:
        print(f"生成图片时发生错误: {e}")
        return False

def main():
    parser = argparse.ArgumentParser(description='独立的图片生成脚本（同步版本）')
    parser.add_argument('input_path', help='输入路径（可以是单个章节目录或包含多个章节的数据目录）')
    
    args = parser.parse_args()
    
    print(f"目标路径: {args.input_path}")
    
    # 检查输入路径是单个章节还是数据目录
    if os.path.isdir(args.input_path):
        # 检查是否是单个章节目录
        if os.path.basename(args.input_path).startswith('chapter_') and os.path.exists(os.path.join(args.input_path, 'narration.txt')):
            print("检测到单个章节目录")
            success = generate_images_for_chapter(args.input_path)
        else:
            print("检测到数据目录，将处理所有章节")
            success = generate_images_from_scripts(args.input_path)
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