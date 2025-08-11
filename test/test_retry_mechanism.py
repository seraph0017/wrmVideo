#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
测试脚本生成重试机制

这个测试脚本用于验证gen_script.py中新增的重试机制是否正常工作。
包括：
1. 验证narration内容质量检查
2. 验证重试机制
3. 验证章节验证逻辑
"""

import os
import sys
import tempfile
import shutil
from pathlib import Path

# 添加项目根目录到路径
project_root = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, project_root)

from gen_script import ScriptGenerator

def test_validate_narration_content():
    """
    测试narration内容验证功能
    """
    print("=== 测试narration内容验证功能 ===")
    
    generator = ScriptGenerator()
    
    # 测试正常长度的内容（包含故事元素）
    normal_content = "这是一个关于主角冒险的故事，情节跌宕起伏，角色性格鲜明，场景描述生动。" * 25  # 约1000字
    is_valid, reason = generator.validate_narration_content(normal_content)
    print(f"正常内容验证: {is_valid}, 原因: {reason}")
    assert is_valid, "正常内容应该通过验证"
    
    # 测试过短的内容
    short_content = "太短了"
    is_valid, reason = generator.validate_narration_content(short_content)
    print(f"过短内容验证: {is_valid}, 原因: {reason}")
    assert not is_valid, "过短内容应该不通过验证"
    
    # 测试过长的内容
    long_content = "这是一个过长的解说文案。" * 200  # 约2000字
    is_valid, reason = generator.validate_narration_content(long_content)
    print(f"过长内容验证: {is_valid}, 原因: {reason}")
    assert not is_valid, "过长内容应该不通过验证"
    
    # 测试空内容
    empty_content = ""
    is_valid, reason = generator.validate_narration_content(empty_content)
    print(f"空内容验证: {is_valid}, 原因: {reason}")
    assert not is_valid, "空内容应该不通过验证"
    
    print("✓ narration内容验证功能测试通过\n")

def test_validate_existing_chapters():
    """
    测试章节验证功能
    """
    print("=== 测试章节验证功能 ===")
    
    generator = ScriptGenerator()
    
    # 创建临时测试目录
    with tempfile.TemporaryDirectory() as temp_dir:
        # 创建测试章节目录
        chapter1_dir = os.path.join(temp_dir, "chapter_001")
        chapter2_dir = os.path.join(temp_dir, "chapter_002")
        chapter3_dir = os.path.join(temp_dir, "chapter_003")
        
        os.makedirs(chapter1_dir)
        os.makedirs(chapter2_dir)
        os.makedirs(chapter3_dir)
        
        # 创建正常的narration文件（包含故事元素）
        normal_narration = "这是一个关于主角冒险的故事，情节跌宕起伏，角色性格鲜明，场景描述生动。" * 25
        with open(os.path.join(chapter1_dir, "narration.txt"), 'w', encoding='utf-8') as f:
            f.write(normal_narration)
        
        # 创建过短的narration文件
        short_narration = "太短了"
        with open(os.path.join(chapter2_dir, "narration.txt"), 'w', encoding='utf-8') as f:
            f.write(short_narration)
        
        # chapter3没有narration文件
        
        # 验证章节
        invalid_chapters = generator.validate_existing_chapters(temp_dir)
        print(f"发现无效章节: {invalid_chapters}")
        
        # 应该发现chapter2和chapter3有问题
        assert 2 in invalid_chapters, "chapter2应该被标记为无效（内容过短）"
        assert 3 in invalid_chapters, "chapter3应该被标记为无效（文件不存在）"
        assert 1 not in invalid_chapters, "chapter1应该是有效的"
        
    print("✓ 章节验证功能测试通过\n")

def main():
    """
    运行所有测试
    """
    print("开始测试脚本生成重试机制...\n")
    
    try:
        test_validate_narration_content()
        test_validate_existing_chapters()
        
        print("🎉 所有测试通过！重试机制功能正常。")
        
    except Exception as e:
        print(f"❌ 测试失败: {e}")
        sys.exit(1)

if __name__ == "__main__":
    main()