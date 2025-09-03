#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
测试角色姓名提取功能
验证gen_character_image.py中的角色姓名解析是否正确处理嵌套的<角色姓名>标签
"""

import sys
import os

# 添加项目根目录到路径
project_root = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, project_root)

from gen_character_image import parse_character_info

def test_character_name_extraction():
    """
    测试角色姓名提取功能
    """
    print("=== 测试角色姓名提取功能 ===")
    
    # 测试data/006/chapter_007/narration.txt中的角色11
    test_file = "/Users/xunan/Projects/wrmVideo/data/006/chapter_007/narration.txt"
    
    if not os.path.exists(test_file):
        print(f"错误: 测试文件不存在 {test_file}")
        return False
    
    print(f"解析文件: {test_file}")
    
    # 解析角色信息
    characters, drawing_style = parse_character_info(test_file)
    
    if not characters:
        print("错误: 未找到角色信息")
        return False
    
    print(f"\n找到 {len(characters)} 个角色:")
    
    # 查找角色11（玉箫天女）
    target_character = None
    for i, character in enumerate(characters, 1):
        character_name = character['name']
        print(f"  角色{i}: {character_name}")
        
        if character_name == "玉箫天女":
            target_character = character
            print(f"    ✓ 找到目标角色: {character_name}")
        elif "玉箫天女" in character_name:
            target_character = character
            print(f"    ✓ 找到包含目标名称的角色: {character_name}")
    
    if target_character:
        print(f"\n=== 角色详细信息 ===")
        print(f"姓名: {target_character['name']}")
        print(f"性别: {target_character.get('gender', '未知')}")
        print(f"描述: {target_character.get('description', '无描述')}")
        print(f"时代: {target_character.get('era', 'single')}")
        print("\n✓ 角色姓名提取成功！")
        return True
    else:
        print("\n✗ 未找到玉箫天女角色，姓名提取可能有问题")
        return False

if __name__ == "__main__":
    success = test_character_name_extraction()
    if success:
        print("\n🎉 测试通过！角色姓名提取功能正常工作")
    else:
        print("\n❌ 测试失败！需要检查角色姓名提取逻辑")
    
    sys.exit(0 if success else 1)