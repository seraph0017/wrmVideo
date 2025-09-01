#!/usr/bin/env python3
# -*- coding: utf-8 -*-

import sys
import os
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from validate_narration import extract_character_names, extract_closeup_characters, validate_narration_file

def test_character_validation():
    """
    测试角色验证和自动修复功能
    """
    narration_file = "/Users/xunan/Projects/wrmVideo/data/006/chapter_001/narration.txt"
    
    print("=== 测试角色验证功能 ===")
    
    # 读取文件内容
    with open(narration_file, 'r', encoding='utf-8') as f:
        content = f.read()
    
    # 提取出镜人物和特写人物
    character_names = extract_character_names(content)
    closeup_characters = extract_closeup_characters(content)
    
    print(f"出镜人物列表: {sorted(character_names)}")
    print(f"特写人物列表: {sorted(set(closeup_characters))}")
    
    # 找出缺失的角色
    missing_characters = []
    for closeup_char in closeup_characters:
        if closeup_char not in character_names:
            missing_characters.append(closeup_char)
    
    print(f"缺失的角色: {sorted(set(missing_characters))}")
    
    # 测试验证函数（不启用自动修复）
    print("\n=== 测试验证函数（不启用自动修复） ===")
    result = validate_narration_file(narration_file, auto_fix_characters=False)
    print(f"角色验证结果: {result['character_validation']}")
    
    # 测试验证函数（启用自动修复）
    print("\n=== 测试验证函数（启用自动修复） ===")
    result = validate_narration_file(narration_file, auto_fix_characters=True)
    print(f"角色验证结果: {result['character_validation']}")
    
    # 重新检查文件内容
    print("\n=== 检查修复后的文件内容 ===")
    with open(narration_file, 'r', encoding='utf-8') as f:
        updated_content = f.read()
    
    updated_character_names = extract_character_names(updated_content)
    print(f"修复后出镜人物列表: {sorted(updated_character_names)}")
    
    # 检查是否添加了赵丰
    if "赵丰" in updated_character_names:
        print("✓ 赵丰已成功添加到出镜人物列表")
    else:
        print("✗ 赵丰未添加到出镜人物列表")

if __name__ == "__main__":
    test_character_validation()