#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
针对data/002目录下的章节生成图片
从narration.txt文件中提取图片prompt，并自动添加人物外貌细节确保图片一致性
"""

import os
import re
import sys
from typing import Dict, List, Tuple

# 添加src目录到路径
src_dir = os.path.join(os.path.dirname(__file__), 'src')
sys.path.insert(0, src_dir)

from src.image.gen_image import generate_image_with_volcengine

def parse_character_info(content: str) -> Dict[str, str]:
    """
    从章节内容中解析人物信息
    
    Args:
        content: 章节内容
    
    Returns:
        Dict[str, str]: 人物名称到外貌描述的映射
    """
    characters = {}
    
    # 查找所有人物信息
    character_pattern = r'<人物\d+>.*?</人物\d+>'
    character_matches = re.findall(character_pattern, content, re.DOTALL)
    
    for character_block in character_matches:
        # 提取姓名
        name_match = re.search(r'<姓名>(.*?)</姓名>', character_block)
        if not name_match:
            continue
        
        name = name_match.group(1).strip()
        
        # 提取各种外貌特征
        details = []
        
        # 身高体型
        height_match = re.search(r'<身高体型>(.*?)</身高体型>', character_block)
        if height_match:
            details.append(height_match.group(1).strip())
        
        # 头发细节
        hair_color_match = re.search(r'<发色>(.*?)</发色>', character_block)
        hair_style_match = re.search(r'<发型>(.*?)</发型>', character_block)
        hair_texture_match = re.search(r'<发质>(.*?)</发质>', character_block)
        
        hair_details = []
        if hair_color_match:
            hair_details.append(hair_color_match.group(1).strip())
        if hair_style_match:
            hair_details.append(hair_style_match.group(1).strip())
        if hair_texture_match:
            hair_details.append(hair_texture_match.group(1).strip())
        
        if hair_details:
            details.append('，'.join(hair_details))
        
        # 眼睛细节
        eye_color_match = re.search(r'<眼睛颜色>(.*?)</眼睛颜色>', character_block)
        eye_shape_match = re.search(r'<眼型>(.*?)</眼型>', character_block)
        eye_expression_match = re.search(r'<眼神特点>(.*?)</眼神特点>', character_block)
        
        eye_details = []
        if eye_color_match:
            eye_details.append(eye_color_match.group(1).strip())
        if eye_shape_match:
            eye_details.append(eye_shape_match.group(1).strip())
        if eye_expression_match:
            eye_details.append(eye_expression_match.group(1).strip())
        
        if eye_details:
            details.append('，'.join(eye_details))
        
        # 脸型轮廓
        face_shape_match = re.search(r'<脸型>(.*?)</脸型>', character_block)
        chin_shape_match = re.search(r'<下巴形状>(.*?)</下巴形状>', character_block)
        
        face_details = []
        if face_shape_match:
            face_details.append(face_shape_match.group(1).strip())
        if chin_shape_match:
            face_details.append(chin_shape_match.group(1).strip())
        
        if face_details:
            details.append('，'.join(face_details))
        
        # 肤色
        skin_match = re.search(r'<肤色>(.*?)</肤色>', character_block)
        if skin_match:
            details.append(skin_match.group(1).strip())
        
        # 服装细节
        clothing_color_match = re.search(r'<服装细节>.*?<颜色>(.*?)</颜色>.*?</服装细节>', character_block, re.DOTALL)
        clothing_style_match = re.search(r'<服装细节>.*?<款式>(.*?)</款式>.*?</服装细节>', character_block, re.DOTALL)
        clothing_material_match = re.search(r'<服装细节>.*?<材质>(.*?)</材质>.*?</服装细节>', character_block, re.DOTALL)
        
        clothing_details = []
        if clothing_color_match:
            clothing_details.append(clothing_color_match.group(1).strip())
        if clothing_style_match:
            clothing_details.append(clothing_style_match.group(1).strip())
        if clothing_material_match:
            clothing_details.append(clothing_material_match.group(1).strip())
        
        if clothing_details:
            details.append('，'.join(clothing_details))
        
        # 配饰细节
        glasses_match = re.search(r'<眼镜>(.*?)</眼镜>', character_block)
        jewelry_match = re.search(r'<首饰>(.*?)</首饰>', character_block)
        accessories_match = re.search(r'<其他配饰>(.*?)</其他配饰>', character_block)
        
        accessory_details = []
        if glasses_match and glasses_match.group(1).strip() != '无':
            accessory_details.append(glasses_match.group(1).strip())
        if jewelry_match and jewelry_match.group(1).strip() != '无':
            accessory_details.append(jewelry_match.group(1).strip())
        if accessories_match and accessories_match.group(1).strip() != '无':
            accessory_details.append(accessories_match.group(1).strip())
        
        if accessory_details:
            details.append('，'.join(accessory_details))
        
        # 表情姿态
        expression_match = re.search(r'<表情姿态>(.*?)</表情姿态>', character_block)
        if expression_match:
            details.append(expression_match.group(1).strip())
        
        # 组合所有细节
        if details:
            characters[name] = '，'.join(details)
    
    return characters

def extract_image_prompts(content: str) -> List[str]:
    """
    从章节内容中提取所有图片prompt
    
    Args:
        content: 章节内容
    
    Returns:
        List[str]: 图片prompt列表
    """
    prompts = []
    
    # 查找所有图片prompt
    prompt_pattern = r'<图片prompt>(.*?)</图片prompt>'
    prompt_matches = re.findall(prompt_pattern, content, re.DOTALL)
    
    for prompt in prompt_matches:
        prompts.append(prompt.strip())
    
    return prompts

def enhance_prompt_with_character_details(prompt: str, characters: Dict[str, str]) -> str:
    """
    在prompt中发现人名时，添加对应的外貌细节
    
    Args:
        prompt: 原始图片prompt
        characters: 人物名称到外貌描述的映射
    
    Returns:
        str: 增强后的prompt
    """
    enhanced_prompt = prompt
    
    # 检查prompt中是否包含人物名称
    for name, details in characters.items():
        if name in prompt:
            # 如果prompt中已经包含了该人物的详细描述，则不重复添加
            if details not in prompt:
                # 在人名后添加外貌细节
                enhanced_prompt = enhanced_prompt.replace(name, f"{name}（{details}）")
    
    return enhanced_prompt

def process_chapter(chapter_dir: str) -> bool:
    """
    处理单个章节，生成图片
    
    Args:
        chapter_dir: 章节目录路径
    
    Returns:
        bool: 是否成功处理
    """
    chapter_name = os.path.basename(chapter_dir)
    narration_file = os.path.join(chapter_dir, 'narration.txt')
    
    if not os.path.exists(narration_file):
        print(f"警告: {chapter_name} 中没有找到 narration.txt 文件")
        return False
    
    print(f"\n--- 处理章节: {chapter_name} ---")
    
    # 读取章节内容
    try:
        with open(narration_file, 'r', encoding='utf-8') as f:
            content = f.read()
    except Exception as e:
        print(f"错误: 无法读取 {narration_file}: {e}")
        return False
    
    # 解析人物信息
    characters = parse_character_info(content)
    print(f"找到 {len(characters)} 个人物: {list(characters.keys())}")
    
    # 提取图片prompts
    prompts = extract_image_prompts(content)
    print(f"找到 {len(prompts)} 个图片prompt")
    
    if not prompts:
        print(f"警告: {chapter_name} 中没有找到图片prompt")
        return False
    
    # 生成图片
    success_count = 0
    for i, prompt in enumerate(prompts, 1):
        # 增强prompt（添加人物外貌细节）
        enhanced_prompt = enhance_prompt_with_character_details(prompt, characters)
        
        # 输出文件路径
        image_filename = f"{chapter_name}_image_{i:02d}.jpeg"
        image_path = os.path.join(chapter_dir, image_filename)
        
        print(f"\n  生成第 {i}/{len(prompts)} 张图片: {image_filename}")
        print(f"  原始prompt: {prompt[:50]}...")
        if enhanced_prompt != prompt:
            print(f"  增强prompt: {enhanced_prompt[:50]}...")
        
        # 生成图片
        if generate_image_with_volcengine(enhanced_prompt, image_path):
            success_count += 1
            print(f"  ✓ 图片生成成功")
        else:
            print(f"  ✗ 图片生成失败")
    
    print(f"\n章节 {chapter_name} 处理完成，成功生成 {success_count}/{len(prompts)} 张图片")
    return success_count > 0

def main():
    """
    主函数
    """
    data_dir = "data/002"
    
    print("=== 开始为 data/002 目录生成图片 ===")
    print(f"目标目录: {data_dir}")
    
    if not os.path.exists(data_dir):
        print(f"错误: 目录不存在 {data_dir}")
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
    
    # 处理每个章节
    total_success = 0
    for chapter_dir in chapter_dirs:
        if process_chapter(chapter_dir):
            total_success += 1
    
    print(f"\n=== 处理完成 ===")
    print(f"成功处理 {total_success}/{len(chapter_dirs)} 个章节")
    
    if total_success == len(chapter_dirs):
        print("✓ 所有章节处理成功")
    elif total_success > 0:
        print(f"⚠ 部分章节处理成功 ({total_success}/{len(chapter_dirs)})")
    else:
        print("✗ 所有章节处理失败")
    
    return total_success > 0

if __name__ == '__main__':
    success = main()
    sys.exit(0 if success else 1)