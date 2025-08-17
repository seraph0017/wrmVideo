#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
测试角色图片匹配功能
验证gen_image_async.py中根据角色姓名匹配角色图片的功能
"""

import os
import sys

# 添加项目根目录到Python路径
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from gen_image_async import parse_narration_file, find_character_image

def test_character_image_matching():
    """
    测试角色图片匹配功能
    """
    print("=== 测试角色图片匹配功能 ===")
    
    # 测试章节路径
    chapter_path = "/Users/xunan/Projects/wrmVideo/data/004/chapter_003"
    narration_file = os.path.join(chapter_path, "narration.txt")
    
    if not os.path.exists(narration_file):
        print(f"错误: narration文件不存在 {narration_file}")
        return False
    
    print(f"解析narration文件: {narration_file}")
    
    # 解析narration文件
    scenes, drawing_style, character_map = parse_narration_file(narration_file)
    
    print(f"\n解析结果:")
    print(f"- 分镜数量: {len(scenes)}")
    print(f"- 绘画风格: {drawing_style}")
    print(f"- 角色映射: {len(character_map)} 个角色")
    
    # 测试每个分镜中的角色
    for scene_idx, scene in enumerate(scenes):
        print(f"\n=== 分镜 {scene_idx + 1} ===")
        closeups = scene.get('closeups', [])
        print(f"特写数量: {len(closeups)}")
        
        for closeup_idx, closeup in enumerate(closeups):
            character = closeup.get('character', '')
            prompt = closeup.get('prompt', '')
            
            print(f"\n  特写 {closeup_idx + 1}:")
            print(f"  - 角色: {character}")
            print(f"  - prompt: {prompt[:50]}...")
            
            if character:
                # 测试角色图片查找
                print(f"  - 查找角色图片...")
                char_img_path = find_character_image(chapter_path, character)
                
                if char_img_path:
                    print(f"  ✓ 找到角色图片: {os.path.basename(char_img_path)}")
                    # 验证文件是否真实存在
                    if os.path.exists(char_img_path):
                        print(f"  ✓ 文件确实存在")
                    else:
                        print(f"  ✗ 文件不存在")
                else:
                    print(f"  ✗ 未找到角色图片")
                    
                    # 列出章节目录中的所有角色图片文件
                    print(f"  章节目录中的角色图片文件:")
                    for filename in os.listdir(chapter_path):
                        if "character" in filename and filename.endswith('.jpeg'):
                            print(f"    - {filename}")
    
    return True

if __name__ == '__main__':
    test_character_image_matching()