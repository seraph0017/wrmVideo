#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
测试解说内容总字数验证功能
用于验证validate_narration.py的总字数检查和重写功能

使用方法:
python test/test_validate_narration_total.py
"""

import os
import sys
import tempfile
from pathlib import Path

# 添加项目根目录到Python路径
sys.path.insert(0, str(Path(__file__).parent.parent))

from validate_narration import (
    extract_all_narration_content,
    count_chinese_characters,
    validate_narration_file
)

def create_test_narration_file(content, temp_dir):
    """
    创建测试用的narration.txt文件
    
    Args:
        content (str): 文件内容
        temp_dir (str): 临时目录路径
        
    Returns:
        str: 创建的文件路径
    """
    test_file = os.path.join(temp_dir, 'narration.txt')
    with open(test_file, 'w', encoding='utf-8') as f:
        f.write(content)
    return test_file

def test_extract_all_narration_content():
    """
    测试提取所有解说内容的功能
    """
    print("测试1: 提取所有解说内容")
    
    test_content = """
<分镜1>
<图片特写1>
<解说内容>这是第一个解说内容，用于测试字数统计功能。</解说内容>
</图片特写1>
<图片特写2>
<解说内容>这是第二个解说内容，同样用于测试。</解说内容>
</图片特写2>
</分镜1>

<分镜2>
<图片特写1>
<解说内容>这是第三个解说内容。</解说内容>
</图片特写1>
</分镜2>
"""
    
    narrations = extract_all_narration_content(test_content)
    print(f"提取到的解说数量: {len(narrations)}")
    
    total_chars = sum(count_chinese_characters(narration) for narration in narrations)
    print(f"总字数: {total_chars}字")
    
    for i, narration in enumerate(narrations, 1):
        char_count = count_chinese_characters(narration)
        print(f"解说{i}: {char_count}字 - {narration}")
    
    print("✓ 测试1通过\n")
    return narrations, total_chars

def test_validate_narration_file_total():
    """
    测试narration文件的总字数验证功能
    """
    print("测试2: 总字数验证功能")
    
    # 创建一个总字数较少的测试文件
    short_content = """
<分镜1>
<图片特写1>
<解说内容>短解说一。</解说内容>
</图片特写1>
<图片特写2>
<解说内容>短解说二。</解说内容>
</图片特写2>
</分镜1>
"""
    
    with tempfile.TemporaryDirectory() as temp_dir:
        test_file = create_test_narration_file(short_content, temp_dir)
        
        # 验证文件（不启用自动改写）
        results = validate_narration_file(test_file, client=None, auto_rewrite=False)
        
        print(f"文件路径: {results['file_path']}")
        print(f"总字数: {results['total_narration']['total_char_count']}字")
        print(f"总字数是否有效: {results['total_narration']['valid']}")
        print(f"是否已重写: {results['total_narration']['rewritten']}")
        
        # 验证总字数应该无效（少于1400字）
        assert results['total_narration']['valid'] == False, "总字数应该无效（少于1400字）"
        assert results['total_narration']['rewritten'] == False, "不应该被重写"
        
    print("✓ 测试2通过\n")

def test_long_narration_detection():
    """
    测试长解说内容的检测功能
    """
    print("测试3: 长解说内容检测")
    
    # 创建一个总字数超过1600字的测试文件
    long_narration = "这是一个很长的解说内容，" * 120  # 大约1800字
    long_content = f"""
<分镜1>
<图片特写1>
<解说内容>{long_narration}</解说内容>
</图片特写1>
<图片特写2>
<解说内容>{long_narration}</解说内容>
</图片特写2>
</分镜1>
"""
    
    with tempfile.TemporaryDirectory() as temp_dir:
        test_file = create_test_narration_file(long_content, temp_dir)
        
        # 验证文件（不启用自动改写）
        results = validate_narration_file(test_file, client=None, auto_rewrite=False)
        
        print(f"总字数: {results['total_narration']['total_char_count']}字")
        print(f"总字数是否有效: {results['total_narration']['valid']}")
        
        # 验证总字数应该无效（超过1700字）
        assert results['total_narration']['total_char_count'] > 1700, "总字数应该超过1700字"
        assert results['total_narration']['valid'] == False, "总字数应该无效（超过1700字）"
        
    print("✓ 测试3通过\n")

def test_valid_narration_range():
    """
    测试字数在1300-1700字之间的有效情况
    """
    print("测试4: 有效字数范围检测")
    
    # 创建一个总字数在1300-1700字之间的测试文件
    medium_narration = "这是一个中等长度的解说内容，用于测试字数在有效范围内的情况。" * 50  # 大约1500字
    medium_content = f"""
<分镜1>
<图片特写1>
<解说内容>{medium_narration}</解说内容>
</图片特写1>
</分镜1>
"""
    
    with tempfile.TemporaryDirectory() as temp_dir:
        test_file = create_test_narration_file(medium_content, temp_dir)
        
        # 验证文件（不启用自动改写）
        results = validate_narration_file(test_file, client=None, auto_rewrite=False)
        
        print(f"总字数: {results['total_narration']['total_char_count']}字")
        print(f"总字数是否有效: {results['total_narration']['valid']}")
        
        # 验证总字数应该有效（在1300-1700字之间）
        total_chars = results['total_narration']['total_char_count']
        assert 1300 <= total_chars <= 1700, f"总字数应该在1300-1700字之间，实际为{total_chars}字"
        assert results['total_narration']['valid'] == True, "总字数应该有效（在1300-1700字之间）"
        
    print("✓ 测试4通过\n")

def main():
    """
    运行所有测试
    """
    print("开始测试解说内容总字数验证功能...\n")
    
    try:
        # 运行测试
        test_extract_all_narration_content()
        test_validate_narration_file_total()
        test_long_narration_detection()
        test_valid_narration_range()
        
        print("🎉 所有测试通过！")
        print("\n功能验证完成:")
        print("✓ 解说内容提取功能正常")
        print("✓ 总字数统计功能正常")
        print("✓ 字数验证逻辑正确")
        print("✓ 超长内容检测正常")
        
    except Exception as e:
        print(f"❌ 测试失败: {e}")
        sys.exit(1)

if __name__ == "__main__":
    main()