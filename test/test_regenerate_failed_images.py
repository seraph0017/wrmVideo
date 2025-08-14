#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
测试重新生成失败图片脚本
验证脚本的各项功能是否正常工作

使用方法:
    python test/test_regenerate_failed_images.py
"""

import os
import sys
import tempfile
import json
from pathlib import Path

# 添加项目根目录到Python路径
sys.path.insert(0, str(Path(__file__).parent.parent))

from regenerate_failed_images import (
    parse_fail_txt,
    parse_image_path_info,
    generate_enhanced_prompt,
    generate_new_filename
)

def test_parse_fail_txt():
    """
    测试解析fail.txt文件功能
    """
    print("=== 测试解析fail.txt文件 ===")
    
    # 创建临时测试文件
    test_content = """\n/Users/xunan/Projects/wrmVideo/Character_Images/Female/15-22_Youth/Ancient/Chinese/Assassin/Youth_Ancient_Chinese_Assassin_02.jpeg - 失败+领口为衽领（交领），不属于圆领、立领、高领，且里面无高领内衬。
/Users/xunan/Projects/wrmVideo/Character_Images/Male/23-35_Adult/Fantasy/Western/Knight/Adult_Fantasy_Western_Knight_01.jpeg - 失败+V领且无高领内衬
/Users/xunan/Projects/wrmVideo/Character_Images/Female/15-22_Youth/Modern/Chinese/Cool/Youth_Modern_Chinese_Cool_03.jpeg - 失败+衽领且里面没有高领内衬
"""
    
    with tempfile.NamedTemporaryFile(mode='w', suffix='.txt', delete=False, encoding='utf-8') as f:
        f.write(test_content)
        temp_file = f.name
    
    try:
        # 测试解析
        failed_paths = parse_fail_txt(temp_file)
        
        print(f"解析到 {len(failed_paths)} 个失败图片路径:")
        for i, path in enumerate(failed_paths, 1):
            print(f"  {i}. {path}")
        
        # 验证结果
        expected_count = 3
        if len(failed_paths) == expected_count:
            print("✓ 解析数量正确")
        else:
            print(f"✗ 解析数量错误，期望 {expected_count}，实际 {len(failed_paths)}")
        
        # 验证路径格式
        all_valid = all(path.endswith('.jpeg') for path in failed_paths)
        if all_valid:
            print("✓ 所有路径格式正确")
        else:
            print("✗ 存在格式错误的路径")
    
    finally:
        # 清理临时文件
        os.unlink(temp_file)
    
    print()

def test_parse_image_path_info():
    """
    测试解析图片路径信息功能
    """
    print("=== 测试解析图片路径信息 ===")
    
    test_paths = [
        "/Users/xunan/Projects/wrmVideo/Character_Images/Female/15-22_Youth/Ancient/Chinese/Assassin/Youth_Ancient_Chinese_Assassin_02.jpeg",
        "/Users/xunan/Projects/wrmVideo/Character_Images/Male/23-35_Adult/Fantasy/Western/Knight/Adult_Fantasy_Western_Knight_01.jpeg",
        "/Users/xunan/Projects/wrmVideo/Character_Images/Female/36-50_MiddleAge/Modern/Chinese/Scientist/MiddleAge_Modern_Chinese_Scientist_05.jpeg"
    ]
    
    for i, path in enumerate(test_paths, 1):
        print(f"\n测试路径 {i}: {os.path.basename(path)}")
        
        info = parse_image_path_info(path)
        if info:
            print(f"  性别: {info['gender']}")
            print(f"  年龄: {info['age']}")
            print(f"  风格: {info['style']}")
            print(f"  文化: {info['culture']}")
            print(f"  气质: {info['temperament']}")
            print(f"  文件名: {info['filename']}")
            print("✓ 解析成功")
        else:
            print("✗ 解析失败")
    
    print()

def test_generate_enhanced_prompt():
    """
    测试生成增强prompt功能
    """
    print("=== 测试生成增强prompt ===")
    
    test_info = {
        "gender": "女",
        "age": "Youth",
        "style": "Ancient",
        "culture": "Chinese",
        "temperament": "Assassin",
        "original_path": "/test/path/image.jpeg",
        "directory": "/test/path",
        "filename": "image.jpeg"
    }
    
    prompt = generate_enhanced_prompt(test_info)
    
    print("生成的prompt:")
    print("-" * 50)
    print(prompt)
    print("-" * 50)
    
    # 检查关键词
    required_keywords = [
        "圆领", "高领", "严禁V领", "严禁衽领", "不能露出脖子",
        "女性", "Ancient", "Chinese", "动漫风格"
    ]
    
    missing_keywords = []
    for keyword in required_keywords:
        if keyword not in prompt:
            missing_keywords.append(keyword)
    
    if not missing_keywords:
        print("✓ 所有必需关键词都包含在prompt中")
    else:
        print(f"✗ 缺少关键词: {missing_keywords}")
    
    print()

def test_generate_new_filename():
    """
    测试生成新文件名功能
    """
    print("=== 测试生成新文件名 ===")
    
    test_paths = [
        "/Users/xunan/Projects/wrmVideo/Character_Images/Female/15-22_Youth/Ancient/Chinese/Assassin/Youth_Ancient_Chinese_Assassin_02.jpeg",
        "/path/to/image.jpg",
        "/another/path/test_image.png"
    ]
    
    for i, original_path in enumerate(test_paths, 1):
        new_path = generate_new_filename(original_path)
        
        print(f"测试 {i}:")
        print(f"  原始路径: {original_path}")
        print(f"  新路径: {new_path}")
        
        # 验证新文件名
        original_name = os.path.basename(original_path)
        new_name = os.path.basename(new_path)
        
        if "_regenerated" in new_name:
            print("  ✓ 新文件名包含_regenerated后缀")
        else:
            print("  ✗ 新文件名缺少_regenerated后缀")
        
        # 验证目录相同
        if os.path.dirname(original_path) == os.path.dirname(new_path):
            print("  ✓ 目录保持不变")
        else:
            print("  ✗ 目录发生变化")
        
        print()

def test_config_availability():
    """
    测试配置文件可用性
    """
    print("=== 测试配置文件可用性 ===")
    
    try:
        from config.config import IMAGE_TWO_CONFIG
        print("✓ 成功导入IMAGE_TWO_CONFIG")
        
        required_keys = ['access_key', 'secret_key', 'req_key', 'negative_prompt']
        missing_keys = []
        
        for key in required_keys:
            if key not in IMAGE_TWO_CONFIG:
                missing_keys.append(key)
        
        if not missing_keys:
            print("✓ 所有必需的配置项都存在")
        else:
            print(f"✗ 缺少配置项: {missing_keys}")
    
    except ImportError as e:
        print(f"✗ 无法导入配置文件: {e}")
    
    try:
        from config.prompt_config import ART_STYLES
        print("✓ 成功导入ART_STYLES")
    except ImportError as e:
        print(f"✗ 无法导入prompt配置: {e}")
    
    print()

def test_real_fail_file():
    """
    测试真实的fail.txt文件（如果存在）
    """
    print("=== 测试真实fail.txt文件 ===")
    
    fail_file = "data/fail.txt"
    
    if os.path.exists(fail_file):
        print(f"发现fail.txt文件: {fail_file}")
        
        failed_paths = parse_fail_txt(fail_file)
        print(f"解析到 {len(failed_paths)} 个失败图片")
        
        if failed_paths:
            print("\n前5个失败图片路径:")
            for i, path in enumerate(failed_paths[:5], 1):
                print(f"  {i}. {os.path.basename(path)}")
            
            # 测试解析第一个路径
            first_path = failed_paths[0]
            info = parse_image_path_info(first_path)
            if info:
                print(f"\n第一个图片解析结果:")
                print(f"  性别: {info['gender']}")
                print(f"  年龄: {info['age']}")
                print(f"  风格: {info['style']}")
                print(f"  文化: {info['culture']}")
                print(f"  气质: {info['temperament']}")
                print("✓ 真实文件解析成功")
            else:
                print("✗ 真实文件解析失败")
        else:
            print("✗ 未解析到任何失败图片")
    else:
        print(f"未找到fail.txt文件: {fail_file}")
        print("这是正常的，如果您还没有生成失败图片列表")
    
    print()

def main():
    """
    主测试函数
    """
    print("重新生成失败图片脚本测试")
    print("=" * 50)
    
    # 运行所有测试
    test_parse_fail_txt()
    test_parse_image_path_info()
    test_generate_enhanced_prompt()
    test_generate_new_filename()
    test_config_availability()
    test_real_fail_file()
    
    print("=" * 50)
    print("测试完成！")
    print("\n如果所有测试都通过，您可以安全地使用 regenerate_failed_images.py 脚本")
    print("使用方法: python regenerate_failed_images.py")

if __name__ == '__main__':
    main()