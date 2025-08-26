#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
测试gen_image_async.py中的时代背景图片匹配功能
"""

import os
import sys
sys.path.append('/Users/xunan/Projects/wrmVideo')

from gen_image_async import parse_narration_file, find_character_image

def test_era_image_matching():
    """
    测试时代背景图片匹配功能
    """
    print("=== 测试gen_image_async.py时代背景图片匹配功能 ===")
    
    # 测试解析narration.txt文件
    test_narration_path = "/Users/xunan/Projects/wrmVideo/data/006/chapter_001/narration.txt"
    
    if not os.path.exists(test_narration_path):
        print(f"❌ 测试文件不存在: {test_narration_path}")
        return False
    
    print(f"\n1. 测试解析narration.txt文件: {test_narration_path}")
    
    try:
        scenes, drawing_style, character_map = parse_narration_file(test_narration_path)
        print(f"✓ 成功解析，共 {len(scenes)} 个场景")
        
        # 检查是否有包含时代背景信息的特写
        era_closeups = []
        for i, scene in enumerate(scenes):
            for closeup in scene['closeups']:
                era_background = closeup.get('era_background', '')
                if era_background:
                    era_closeups.append({
                        'scene': i + 1,
                        'character': closeup.get('character', ''),
                        'era_background': era_background
                    })
        
        print(f"\n2. 找到 {len(era_closeups)} 个包含时代背景信息的特写:")
        for closeup in era_closeups:
            print(f"   场景 {closeup['scene']}: {closeup['character']} - {closeup['era_background']}")
        
        # 测试图片查找功能
        print(f"\n3. 测试时代背景图片查找功能:")
        chapter_dir = "/Users/xunan/Projects/wrmVideo/data/006/chapter_001"
        
        for closeup in era_closeups:
            character = closeup['character']
            era_background = closeup['era_background']
            
            print(f"\n   测试角色: {character}, 时代背景: {era_background}")
            
            # 测试带时代背景的查找
            image_path = find_character_image(chapter_dir, character, era_background)
            if image_path:
                print(f"   ✓ 找到时代背景图片: {os.path.basename(image_path)}")
            else:
                print(f"   ⚠️  未找到时代背景图片，尝试通用图片")
                # 测试不带时代背景的查找
                image_path = find_character_image(chapter_dir, character)
                if image_path:
                    print(f"   ✓ 找到通用图片: {os.path.basename(image_path)}")
                else:
                    print(f"   ❌ 未找到任何图片")
        
        # 测试不同时代背景的查找
        print(f"\n4. 测试不同时代背景的图片查找:")
        test_character = "赵硕"  # 假设这个角色存在
        
        for era in ["现代", "古代", None]:
            print(f"\n   测试 {test_character} - {era if era else '无时代背景'}:")
            image_path = find_character_image(chapter_dir, test_character, era)
            if image_path:
                print(f"   ✓ 找到图片: {os.path.basename(image_path)}")
            else:
                print(f"   ❌ 未找到图片")
        
        print(f"\n=== 测试完成 ===")
        return True
        
    except Exception as e:
        print(f"❌ 测试过程中发生错误: {e}")
        import traceback
        traceback.print_exc()
        return False

if __name__ == "__main__":
    test_era_image_matching()