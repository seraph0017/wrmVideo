#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
综合测试脚本：验证所有修复的文件都能正确解析角色姓名
测试嵌套的<角色姓名>标签解析功能
"""

import sys
import os
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from gen_image_async_v3 import NarrationParser as NarrationParserV3
from gen_image_async_v2 import NarrationParser as NarrationParserV2
from gen_character_image import parse_character_info
from validate_narration import extract_character_names

def test_gen_image_async_v3():
    """测试gen_image_async_v3.py的角色解析功能"""
    print("=== 测试 gen_image_async_v3.py ===")
    
    narration_file = "/Users/xunan/Projects/wrmVideo/data/021/chapter_004/narration.txt"
    if not os.path.exists(narration_file):
        print(f"警告: 测试文件不存在: {narration_file}")
        return False
    
    try:
        parser = NarrationParserV3(narration_file)
        characters = parser.parse_characters()
        
        print(f"解析到的角色数量: {len(characters)}")
        for name, info in characters.items():
            print(f"  - {name}: {info.get('gender', '未知性别')}, {info.get('age_group', '未知年龄')}")
        
        # 检查是否找到了"吴毅"
        if "吴毅" in characters:
            print("✅ 成功找到角色 '吴毅'")
            return True
        else:
            print("❌ 未找到角色 '吴毅'")
            return False
            
    except Exception as e:
        print(f"❌ 测试失败: {e}")
        return False

def test_gen_image_async_v2():
    """测试gen_image_async_v2.py的角色解析功能"""
    print("\n=== 测试 gen_image_async_v2.py ===")
    
    narration_file = "/Users/xunan/Projects/wrmVideo/data/021/chapter_004/narration.txt"
    if not os.path.exists(narration_file):
        print(f"警告: 测试文件不存在: {narration_file}")
        return False
    
    try:
        parser = NarrationParserV2(narration_file)
        characters = parser.parse_characters()
        
        print(f"解析到的角色数量: {len(characters)}")
        for name, info in characters.items():
            print(f"  - {name}: {info.get('gender', '未知性别')}, {info.get('age_group', '未知年龄')}")
        
        # 检查是否找到了"吴毅"
        if "吴毅" in characters:
            print("✅ 成功找到角色 '吴毅'")
            return True
        else:
            print("❌ 未找到角色 '吴毅'")
            return False
            
    except Exception as e:
        print(f"❌ 测试失败: {e}")
        return False

def test_gen_character_image():
    """测试gen_character_image.py的角色解析功能"""
    print("\n=== 测试 gen_character_image.py ===")
    
    narration_file = "/Users/xunan/Projects/wrmVideo/data/021/chapter_004/narration.txt"
    if not os.path.exists(narration_file):
        print(f"警告: 测试文件不存在: {narration_file}")
        return False
    
    try:
        result = parse_character_info(narration_file)
        
        # gen_character_image.py 返回元组 (characters, drawing_style)
        if isinstance(result, tuple) and len(result) >= 1:
            characters = result[0]  # 第一个元素是角色列表
            print(f"解析结果类型: {type(result)}, 角色列表类型: {type(characters)}")
        elif isinstance(result, list):
            characters = result
        else:
            characters = result
        
        print(f"解析到的角色数量: {len(characters)}")
        for char in characters:
            # 处理字典和列表两种可能的返回格式
            if isinstance(char, dict):
                name = char.get('name', '未知姓名')
                gender = char.get('gender', '未知性别')
                age_group = char.get('age_group', '未知年龄')
            else:
                # 如果是其他格式，尝试转换为字符串
                name = str(char)
                gender = '未知性别'
                age_group = '未知年龄'
            print(f"  - {name}: {gender}, {age_group}")
        
        # 检查是否找到了"吴毅"
        wu_yi_found = False
        for char in characters:
            if isinstance(char, dict):
                if char.get('name') == '吴毅':
                    wu_yi_found = True
                    break
            else:
                if str(char) == '吴毅':
                    wu_yi_found = True
                    break
        
        if wu_yi_found:
            print("✅ 成功找到角色 '吴毅'")
            return True
        else:
            print("❌ 未找到角色 '吴毅'")
            return False
            
    except Exception as e:
        print(f"❌ 测试失败: {e}")
        import traceback
        traceback.print_exc()
        return False

def test_validate_narration():
    """测试validate_narration.py的角色解析功能"""
    print("\n=== 测试 validate_narration.py ===")
    
    narration_file = "/Users/xunan/Projects/wrmVideo/data/021/chapter_004/narration.txt"
    if not os.path.exists(narration_file):
        print(f"警告: 测试文件不存在: {narration_file}")
        return False
    
    try:
        with open(narration_file, 'r', encoding='utf-8') as f:
            content = f.read()
        
        character_names = extract_character_names(content)
        
        print(f"解析到的角色姓名数量: {len(character_names)}")
        for name in sorted(character_names):
            print(f"  - {name}")
        
        # 检查是否找到了"吴毅"
        if "吴毅" in character_names:
            print("✅ 成功找到角色 '吴毅'")
            return True
        else:
            print("❌ 未找到角色 '吴毅'")
            return False
            
    except Exception as e:
        print(f"❌ 测试失败: {e}")
        return False

def main():
    """运行所有测试"""
    print("开始综合测试所有角色解析修复...")
    
    results = []
    
    # 运行所有测试
    results.append(test_gen_image_async_v3())
    results.append(test_gen_image_async_v2())
    results.append(test_gen_character_image())
    results.append(test_validate_narration())
    
    # 汇总结果
    print("\n" + "="*50)
    print("测试结果汇总:")
    print(f"✅ 通过: {sum(results)}")
    print(f"❌ 失败: {len(results) - sum(results)}")
    
    if all(results):
        print("\n🎉 所有测试通过！角色解析修复成功！")
        return True
    else:
        print("\n⚠️  部分测试失败，需要进一步检查")
        return False

if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1)