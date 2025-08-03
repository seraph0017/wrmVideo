#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
测试角色图片查找功能
"""

import os

def find_character_image_by_attributes(gender, age_group, character_style, culture='Chinese', temperament='Common'):
    """
    根据角色属性查找Character_Images目录中的角色图片
    """
    # 构建Character_Images目录路径
    script_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
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
            return None
    
    print(f"    警告: 未找到角色目录 {gender}/{age_group}/{character_style}/{culture}/{temperament}")
    return None

def test_character_image_finding():
    """
    测试角色图片查找功能
    """
    print("测试角色图片查找功能...")
    
    # 测试用例1: 已知存在的路径
    print("\n=== 测试用例1: Male/31-45_MiddleAged/SciFi/Western/Survivor ===")
    result1 = find_character_image_by_attributes(
        gender='Male',
        age_group='31-45_MiddleAged', 
        character_style='SciFi',
        culture='Western',
        temperament='Survivor'
    )
    print(f"结果: {result1}")
    
    # 测试用例2: 使用默认参数
    print("\n=== 测试用例2: Male/23-30_YoungAdult/Ancient (默认Chinese/Common) ===")
    result2 = find_character_image_by_attributes(
        gender='Male',
        age_group='23-30_YoungAdult',
        character_style='Ancient'
    )
    print(f"结果: {result2}")
    
    # 测试用例3: 不存在的路径
    print("\n=== 测试用例3: 不存在的组合 ===")
    result3 = find_character_image_by_attributes(
        gender='Male',
        age_group='99-99_NotExist',
        character_style='NotExist'
    )
    print(f"结果: {result3}")
    
    # 测试用例4: Female角色
    print("\n=== 测试用例4: Female角色 ===")
    result4 = find_character_image_by_attributes(
        gender='Female',
        age_group='23-30_YoungAdult',
        character_style='Fantasy',
        culture='Chinese',
        temperament='Royal'
    )
    print(f"结果: {result4}")
    
    print("\n=== 测试完成 ===")

if __name__ == '__main__':
    test_character_image_finding()