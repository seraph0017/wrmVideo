#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
测试角色信息解析功能
验证gen_character_image.py是否能正确解析新格式的角色信息
"""

import os
import sys
from gen_character_image import parse_character_info

def test_character_parsing():
    """测试角色信息解析功能"""
    
    # 测试文件路径
    test_file = "/Users/xunan/Projects/wrmVideo/data/004/chapter_002/narration.txt"
    
    if not os.path.exists(test_file):
        print(f"测试文件不存在: {test_file}")
        return False
    
    print(f"正在测试角色解析功能...")
    print(f"测试文件: {test_file}")
    print("=" * 60)
    
    try:
        # 解析角色信息
        characters, drawing_style = parse_character_info(test_file)
        
        print(f"解析结果:")
        print(f"绘画风格: {drawing_style}")
        print(f"角色数量: {len(characters)}")
        print("\n角色详情:")
        
        for i, char in enumerate(characters, 1):
            print(f"\n角色 {i}:")
            print(f"  姓名: {char.get('name', '未知')}")
            print(f"  性别: {char.get('gender', '未知')}")
            print(f"  年龄段: {char.get('age_group', '未知')}")
            print(f"  描述: {char.get('description', '无描述')}")
        
        if characters:
            print("\n✅ 角色解析成功!")
            return True
        else:
            print("\n❌ 未解析到任何角色信息")
            return False
            
    except Exception as e:
        print(f"\n❌ 解析过程中出现错误: {str(e)}")
        import traceback
        traceback.print_exc()
        return False

def main():
    """主函数"""
    print("角色信息解析测试")
    print("=" * 60)
    
    success = test_character_parsing()
    
    print("\n" + "=" * 60)
    if success:
        print("✅ 测试完成: 角色解析功能正常")
    else:
        print("❌ 测试失败: 角色解析功能异常")
    
    return 0 if success else 1

if __name__ == "__main__":
    sys.exit(main())