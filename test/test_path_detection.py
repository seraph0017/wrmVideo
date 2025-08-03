#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
测试路径检测逻辑
"""

import os
import sys

def test_path_detection(input_path):
    """
    测试路径检测逻辑
    """
    print(f"测试路径: {input_path}")
    
    # 检查输入路径是单个章节还是数据目录
    if os.path.isdir(input_path):
        # 检查是否是单个章节目录
        if os.path.basename(input_path).startswith('chapter_') and os.path.exists(os.path.join(input_path, 'narration.txt')):
            print("✓ 检测到单个章节目录")
            print(f"  - 章节名: {os.path.basename(input_path)}")
            print(f"  - narration.txt存在: {os.path.exists(os.path.join(input_path, 'narration.txt'))}")
            return "single_chapter"
        else:
            print("✓ 检测到数据目录，将处理所有章节")
            # 查找所有章节目录
            chapter_dirs = []
            for item in os.listdir(input_path):
                item_path = os.path.join(input_path, item)
                if os.path.isdir(item_path) and item.startswith('chapter_'):
                    chapter_dirs.append(item)
            
            chapter_dirs.sort()
            print(f"  - 找到 {len(chapter_dirs)} 个章节目录: {chapter_dirs}")
            return "data_directory"
    else:
        print(f"✗ 错误: 路径不存在 {input_path}")
        return "not_exist"

def main():
    test_paths = [
        "data/001",
        "data/001/chapter_001",
        "data/001/chapter_002",
        "data/003",
        "data/003/chapter_001",
        "nonexistent_path"
    ]
    
    print("=== 路径检测测试 ===\n")
    
    for path in test_paths:
        result = test_path_detection(path)
        print(f"结果: {result}\n")

if __name__ == '__main__':
    main()