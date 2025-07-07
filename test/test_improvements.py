#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
测试改进功能：单行字幕
"""

import os
import sys
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from generate import wrap_text, generate_image

def test_single_line_subtitle():
    """
    测试单行字幕功能
    """
    print("=== 测试单行字幕功能 ===")
    
    # 测试用例
    test_cases = [
        "这是一个短文本",
        "这是一个比较长的文本，应该被截取并添加省略号",
        "这是一个包含\n换行符的\r文本，应该被处理为单行",
        "这是一个非常非常非常非常非常非常长的文本，超过了最大字符数限制，应该被截取"
    ]
    
    for i, text in enumerate(test_cases, 1):
        result = wrap_text(text, max_chars_per_line=30)
        print(f"测试 {i}:")
        print(f"  输入: {repr(text)}")
        print(f"  输出: {repr(result)}")
        print(f"  长度: {len(result)}")
        has_newline = '\n' in result
        print(f"  包含换行: {'是' if has_newline else '否'}")
        print()
    
    print("单行字幕测试完成！")





if __name__ == "__main__":
    print("开始测试改进功能...\n")
    
    # 运行所有测试
    test_single_line_subtitle()
    print("\n" + "="*50 + "\n")
    

    print("\n所有测试完成！")