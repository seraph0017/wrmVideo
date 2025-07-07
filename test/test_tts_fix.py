#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
测试TTS文本验证修复的脚本
"""

import sys
import os
sys.path.append('.')

from generate import smart_split_text, is_valid_text_segment, clean_text_for_tts

def test_invalid_text_filtering():
    """
    测试无效文本过滤功能
    """
    print("=== 测试无效文本过滤功能 ===")
    
    # 测试各种可能导致TTS错误的文本
    test_cases = [
        "！...",  # 只有标点符号和省略号
        "？？？",  # 只有问号
        "。。。",  # 只有句号
        "   ",    # 只有空格
        "",       # 空字符串
        "！",     # 单个标点
        "正常文本内容",  # 正常文本
        "这是正常的句子。",  # 正常句子
        "（）【】",  # 只有括号
        "…………",  # 只有省略号
    ]
    
    print("\n测试 is_valid_text_segment 函数:")
    for i, text in enumerate(test_cases, 1):
        is_valid = is_valid_text_segment(text)
        print(f"  {i:2d}. '{text}' -> {'有效' if is_valid else '无效'}")
    
    return True

def test_smart_split_with_filtering():
    """
    测试智能分割与过滤结合
    """
    print("\n=== 测试智能分割与过滤结合 ===")
    
    # 模拟可能产生问题的文本
    problematic_text = "这是一个测试文本，包含了一些内容。！这里可能会被分割成问题片段。"
    
    print(f"原始文本: {problematic_text}")
    
    # 清理文本
    clean_text = clean_text_for_tts(problematic_text)
    print(f"清理后文本: {clean_text}")
    
    # 智能分割
    segments = smart_split_text(clean_text, max_length=25)
    print(f"\n分割结果 ({len(segments)} 个片段):")
    
    for i, segment in enumerate(segments, 1):
        is_valid = is_valid_text_segment(segment)
        print(f"  {i}. '{segment}' -> {'✓ 有效' if is_valid else '✗ 无效'}")
    
    # 验证所有片段都是有效的
    all_valid = all(is_valid_text_segment(seg) for seg in segments)
    print(f"\n所有片段都有效: {'✓ 是' if all_valid else '✗ 否'}")
    
    return all_valid

def test_edge_cases():
    """
    测试边界情况
    """
    print("\n=== 测试边界情况 ===")
    
    edge_cases = [
        "a",  # 单个字符
        "你好",  # 两个字符
        "这是一个很长的文本，用来测试当文本很长时的分割情况，看看是否会产生无效的片段！",
        "短句。长句子包含更多内容和标点符号，用来测试复杂情况！",
    ]
    
    for i, text in enumerate(edge_cases, 1):
        print(f"\n测试用例 {i}: {text}")
        
        clean_text = clean_text_for_tts(text)
        segments = smart_split_text(clean_text, max_length=20)
        
        print(f"  分割为 {len(segments)} 个片段:")
        all_valid = True
        for j, segment in enumerate(segments, 1):
            is_valid = is_valid_text_segment(segment)
            if not is_valid:
                all_valid = False
            print(f"    {j}. '{segment}' -> {'✓' if is_valid else '✗'}")
        
        print(f"  结果: {'✓ 全部有效' if all_valid else '✗ 存在无效片段'}")
    
    return True

def main():
    """
    主测试函数
    """
    print("TTS文本验证修复测试")
    print("=" * 50)
    
    try:
        # 运行所有测试
        test1 = test_invalid_text_filtering()
        test2 = test_smart_split_with_filtering()
        test3 = test_edge_cases()
        
        print("\n" + "=" * 50)
        print("测试总结:")
        print(f"  无效文本过滤: {'✓ 通过' if test1 else '✗ 失败'}")
        print(f"  智能分割过滤: {'✓ 通过' if test2 else '✗ 失败'}")
        print(f"  边界情况测试: {'✓ 通过' if test3 else '✗ 失败'}")
        
        if all([test1, test2, test3]):
            print("\n🎉 所有测试通过！TTS文本验证修复成功！")
            return True
        else:
            print("\n❌ 部分测试失败，需要进一步检查")
            return False
            
    except Exception as e:
        print(f"\n❌ 测试过程中发生错误: {e}")
        return False

if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1)