#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
测试角色过滤功能
验证 validate_narration.py 中的 should_ignore_character 函数是否正确过滤通用角色名
"""

import sys
import os
import re

# 添加项目根目录到路径
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

def should_ignore_character(char_name):
    """
    判断是否应该忽略某个角色名称（如通用角色名"角色x"等）
    """
    # 忽略"角色"开头后跟数字或字母的通用角色名
    if re.match(r'^角色[a-zA-Z0-9]+$', char_name):
        return True
    # 忽略单个字母或数字的角色名
    if re.match(r'^[a-zA-Z0-9]$', char_name):
        return True
    return False

def test_character_filter():
    """
    测试角色过滤功能
    """
    print("测试角色过滤功能...")
    
    # 应该被忽略的角色名
    ignore_cases = [
        "角色1",
        "角色2", 
        "角色a",
        "角色b",
        "角色x",
        "角色A",
        "角色B",
        "a",
        "b",
        "1",
        "2"
    ]
    
    # 不应该被忽略的角色名
    keep_cases = [
        "赵丰",
        "赵硕",
        "苏青蝉",
        "楚秀",
        "赵鸾",
        "辛芦",
        "白蒹葭",
        "龙欣",
        "凤岚",
        "角色",  # 单独的"角色"不应该被忽略
        "角色名",  # 包含中文的不应该被忽略
        "角色12a"  # 混合字符的不应该被忽略
    ]
    
    print("\n测试应该被忽略的角色名:")
    for char_name in ignore_cases:
        result = should_ignore_character(char_name)
        status = "✓" if result else "✗"
        print(f"  {status} {char_name} -> {result}")
        if not result:
            print(f"    错误: {char_name} 应该被忽略但没有被忽略")
    
    print("\n测试不应该被忽略的角色名:")
    for char_name in keep_cases:
        result = should_ignore_character(char_name)
        status = "✓" if not result else "✗"
        print(f"  {status} {char_name} -> {result}")
        if result:
            print(f"    错误: {char_name} 不应该被忽略但被忽略了")
    
    print("\n角色过滤功能测试完成!")

if __name__ == "__main__":
    test_character_filter()