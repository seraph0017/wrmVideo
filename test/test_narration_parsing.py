#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
测试narration.txt格式解析的兼容性
验证gen_image_async.py中的角色信息提取功能
"""

import sys
import os
import tempfile
import re

# 添加项目根目录到Python路径
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from gen_image_async import parse_narration_file

def test_normal_format():
    """测试正常格式的narration.txt"""
    content = """
<分镜1>
<图片特写1>
<特写人物>
<角色姓名>李世民</角色姓名>
<时代背景>古代</时代背景>
<角色形象>古代形象</角色形象>
</特写人物>
<解说内容>李世民登基为帝</解说内容>
<图片prompt>古代皇帝登基场景</图片prompt>
</图片特写1>
</分镜1>
    """
    
    with tempfile.NamedTemporaryFile(mode='w', suffix='.txt', delete=False, encoding='utf-8') as f:
        f.write(content)
        temp_file = f.name
    
    try:
        scenes, drawing_style, character_map = parse_narration_file(temp_file)
        print("=== 测试正常格式 ===")
        print(f"解析结果: {len(scenes)} 个分镜")
        if scenes:
            closeup = scenes[0]['closeups'][0]
            print(f"角色: {closeup.get('character', '未找到')}")
            print(f"时代背景: {closeup.get('era_background', '未找到')}")
            print(f"角色形象: {closeup.get('character_image', '未找到')}")
            return closeup.get('character') == '李世民'
    finally:
        os.unlink(temp_file)
    
    return False

def test_missing_start_tag():
    """测试缺少开始标签的格式"""
    content = """
<分镜1>
<图片特写1>
<角色姓名>程知节</角色姓名>
<时代背景>古代</时代背景>
<角色形象>古代形象</角色形象>
</特写人物>
<解说内容>程知节勇猛作战</解说内容>
<图片prompt>古代武将作战场景</图片prompt>
</图片特写1>
</分镜1>
    """
    
    with tempfile.NamedTemporaryFile(mode='w', suffix='.txt', delete=False, encoding='utf-8') as f:
        f.write(content)
        temp_file = f.name
    
    try:
        scenes, drawing_style, character_map = parse_narration_file(temp_file)
        print("\n=== 测试缺少开始标签格式 ===")
        print(f"解析结果: {len(scenes)} 个分镜")
        if scenes:
            closeup = scenes[0]['closeups'][0]
            print(f"角色: {closeup.get('character', '未找到')}")
            print(f"时代背景: {closeup.get('era_background', '未找到')}")
            print(f"角色形象: {closeup.get('character_image', '未找到')}")
            return closeup.get('character') == '程知节'
    finally:
        os.unlink(temp_file)
    
    return False

def test_no_character_block():
    """测试完全没有特写人物块的格式"""
    content = """
<分镜1>
<图片特写1>
<角色姓名>魏征</角色姓名>
<时代背景>古代</时代背景>
<角色形象>古代形象</角色形象>
<解说内容>魏征直言进谏</解说内容>
<图片prompt>古代大臣进谏场景</图片prompt>
</图片特写1>
</分镜1>
    """
    
    with tempfile.NamedTemporaryFile(mode='w', suffix='.txt', delete=False, encoding='utf-8') as f:
        f.write(content)
        temp_file = f.name
    
    try:
        scenes, drawing_style, character_map = parse_narration_file(temp_file)
        print("\n=== 测试无特写人物块格式 ===")
        print(f"解析结果: {len(scenes)} 个分镜")
        if scenes:
            closeup = scenes[0]['closeups'][0]
            print(f"角色: {closeup.get('character', '未找到')}")
            print(f"时代背景: {closeup.get('era_background', '未找到')}")
            print(f"角色形象: {closeup.get('character_image', '未找到')}")
            return closeup.get('character') == '魏征'
    finally:
        os.unlink(temp_file)
    
    return False

def main():
    """运行所有测试"""
    print("开始测试narration.txt格式解析兼容性...\n")
    
    tests = [
        ("正常格式", test_normal_format),
        ("缺少开始标签", test_missing_start_tag),
        ("无特写人物块", test_no_character_block)
    ]
    
    passed = 0
    total = len(tests)
    
    for test_name, test_func in tests:
        try:
            result = test_func()
            status = "✓ 通过" if result else "✗ 失败"
            print(f"\n{test_name}: {status}")
            if result:
                passed += 1
        except Exception as e:
            print(f"\n{test_name}: ✗ 异常 - {e}")
    
    print(f"\n=== 测试总结 ===")
    print(f"通过: {passed}/{total}")
    print(f"成功率: {passed/total*100:.1f}%")
    
    if passed == total:
        print("\n🎉 所有测试通过！narration.txt格式兼容性修复成功。")
    else:
        print(f"\n⚠️  有 {total-passed} 个测试失败，需要进一步检查。")

if __name__ == '__main__':
    main()