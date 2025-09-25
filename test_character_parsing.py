#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
测试角色解析功能
"""

import sys
import os
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from gen_image_async_v3 import NarrationParser

def test_character_parsing():
    """测试角色解析功能"""
    
    # 测试文件路径
    narration_file = "/Users/xunan/Projects/wrmVideo/data/021/chapter_004/narration.txt"
    
    if not os.path.exists(narration_file):
        print(f"错误：测试文件不存在 {narration_file}")
        return False
    
    # 创建解析器
    parser = NarrationParser(narration_file)
    
    # 解析角色信息
    characters = parser.parse_characters()
    
    print(f"解析到 {len(characters)} 个角色:")
    for name, info in characters.items():
        print(f"  - {name}: {info}")
    
    # 检查是否能找到吴毅
    if "吴毅" in characters:
        print(f"\n✓ 成功找到角色 '吴毅': {characters['吴毅']}")
        return True
    else:
        print(f"\n✗ 未找到角色 '吴毅'")
        print(f"可用角色: {list(characters.keys())}")
        return False

if __name__ == "__main__":
    success = test_character_parsing()
    sys.exit(0 if success else 1)