#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
测试角色性别推断功能
验证generate_character_definition函数是否能根据角色名称和上下文正确推断性别
"""

import sys
import os
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from validate_narration import generate_character_definition

def test_character_gender_inference():
    """
    测试角色性别推断功能
    """
    print("=== 测试角色性别推断功能 ===")
    
    # 测试用例1: 明显的女性角色名
    print("\n1. 测试明显的女性角色名:")
    test_cases_female = [
        ("玉箫天女", "玉箫天女轻抚琴弦，她的容貌如仙女般美丽"),
        ("公主", "公主穿着华丽的宫装，她优雅地走向宝座"),
        ("仙女", "仙女从天而降，她身着飘逸的白衣")
    ]
    
    for name, context in test_cases_female:
        char_def = generate_character_definition(name, context)
        gender = extract_gender_from_definition(char_def)
        print(f"  角色: {name}")
        print(f"  上下文: {context}")
        print(f"  推断性别: {gender}")
        print(f"  结果: {'✓ 正确' if gender == 'Female' else '✗ 错误'}")
        print()
    
    # 测试用例2: 明显的男性角色名
    print("\n2. 测试明显的男性角色名:")
    test_cases_male = [
        ("李将军", "李将军威武地站在城墙上，他指挥着士兵们"),
        ("王爷", "王爷坐在大堂中，他正在审理案件"),
        ("道长", "道长手持拂尘，他念着咒语")
    ]
    
    for name, context in test_cases_male:
        char_def = generate_character_definition(name, context)
        gender = extract_gender_from_definition(char_def)
        print(f"  角色: {name}")
        print(f"  上下文: {context}")
        print(f"  推断性别: {gender}")
        print(f"  结果: {'✓ 正确' if gender == 'Male' else '✗ 错误'}")
        print()
    
    # 测试用例3: 需要依赖上下文的角色名
    print("\n3. 测试需要依赖上下文的角色名:")
    test_cases_context = [
        ("小青", "小青是一位美丽的女子，她温柔地照顾着病人", "Female"),
        ("小明", "小明是个勇敢的男孩，他保护着村庄", "Male"),
        ("阿花", "阿花穿着花裙子，她在花园里采花", "Female")
    ]
    
    for name, context, expected in test_cases_context:
        char_def = generate_character_definition(name, context)
        gender = extract_gender_from_definition(char_def)
        print(f"  角色: {name}")
        print(f"  上下文: {context}")
        print(f"  推断性别: {gender}")
        print(f"  期望性别: {expected}")
        print(f"  结果: {'✓ 正确' if gender == expected else '✗ 错误'}")
        print()

def extract_gender_from_definition(char_def):
    """
    从角色定义中提取性别信息
    
    Args:
        char_def (str): 角色定义XML字符串
        
    Returns:
        str: 性别 (Male/Female)
    """
    import re
    gender_match = re.search(r'<性别>([^<]+)</性别>', char_def)
    if gender_match:
        return gender_match.group(1)
    return "Unknown"

def test_real_narration_case():
    """
    测试真实的narration.txt案例
    """
    print("\n=== 测试真实案例 ===")
    
    # 模拟玉箫天女在narration.txt中的上下文
    real_context = """
    玉箫天女轻抚琴弦，琴音如泣如诉，仿佛在诉说着千年的离愁别恨。
    她的容貌如仙女般美丽，身着飘逸的白衣，宛如从天而降的仙子。
    """
    
    char_def = generate_character_definition("玉箫天女", real_context)
    gender = extract_gender_from_definition(char_def)
    
    print(f"角色: 玉箫天女")
    print(f"上下文: {real_context.strip()}")
    print(f"推断性别: {gender}")
    print(f"结果: {'✓ 正确' if gender == 'Female' else '✗ 错误'}")
    print()
    print("生成的角色定义:")
    print(char_def)

if __name__ == "__main__":
    test_character_gender_inference()
    test_real_narration_case()
    print("\n测试完成！")