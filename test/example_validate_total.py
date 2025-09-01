#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
解说内容总字数验证功能使用示例
演示如何使用validate_narration.py的新增总字数检查功能

使用方法:
python test/example_validate_total.py
"""

import os
import sys
import tempfile
from pathlib import Path

# 添加项目根目录到Python路径
sys.path.insert(0, str(Path(__file__).parent.parent))

from validate_narration import validate_narration_file, extract_all_narration_content, count_chinese_characters

def create_example_narration():
    """
    创建一个示例narration.txt文件用于演示
    """
    example_content = """
<分镜1>
<图片特写1>
<解说内容>在这个古老的修仙世界中，主角踏上了寻求真理的道路。</解说内容>
</图片特写1>
<图片特写2>
<解说内容>他的眼中闪烁着坚定的光芒，决心要突破重重困难。</解说内容>
</图片特写2>
</分镜1>

<分镜2>
<图片特写1>
<解说内容>面对强大的敌人，主角展现出了惊人的战斗天赋。</解说内容>
</图片特写1>
<图片特写2>
<解说内容>他的剑法如行云流水，每一招都蕴含着深厚的内力。</解说内容>
</图片特写2>
</分镜2>

<分镜3>
<图片特写1>
<解说内容>经过无数次的历练，主角终于领悟了修仙的真谛。</解说内容>
</图片特写1>
<图片特写2>
<解说内容>他的修为突飞猛进，成为了这个世界的传奇人物。</解说内容>
</图片特写2>
</分镜3>
"""
    return example_content

def demonstrate_total_validation():
    """
    演示总字数验证功能
    """
    print("=" * 60)
    print("解说内容总字数验证功能演示")
    print("=" * 60)
    
    # 创建示例文件
    example_content = create_example_narration()
    
    with tempfile.TemporaryDirectory() as temp_dir:
        # 创建测试文件
        test_file = os.path.join(temp_dir, 'narration.txt')
        with open(test_file, 'w', encoding='utf-8') as f:
            f.write(example_content)
        
        print(f"\n📁 创建示例文件: {test_file}")
        
        # 先展示原始内容分析
        print("\n📊 原始内容分析:")
        all_narrations = extract_all_narration_content(example_content)
        print(f"解说数量: {len(all_narrations)}个")
        
        for i, narration in enumerate(all_narrations, 1):
            char_count = count_chinese_characters(narration)
            print(f"  解说{i:2d}: {char_count:2d}字 - {narration}")
        
        total_chars = sum(count_chinese_characters(narration) for narration in all_narrations)
        print(f"\n总字数: {total_chars}字")
        print(f"字数状态: {'✓ 符合要求' if total_chars <= 1600 else '✗ 超过限制'}")
        
        # 执行验证
        print("\n🔍 执行验证检查...")
        results = validate_narration_file(test_file, client=None, auto_rewrite=False)
        
        # 显示验证结果
        print("\n📋 验证结果:")
        
        # 第一个特写
        first = results['first_closeup']
        if first['exists']:
            status = "✓" if first['valid'] else "✗"
            print(f"第一个特写: {status} {first['char_count']}字 (要求: 30-32字)")
        else:
            print("第一个特写: ✗ 未找到")
        
        # 第二个特写
        second = results['second_closeup']
        if second['exists']:
            status = "✓" if second['valid'] else "✗"
            print(f"第二个特写: {status} {second['char_count']}字 (要求: 30-32字)")
        else:
            print("第二个特写: ✗ 未找到")
        
        # 总字数检查
        total = results['total_narration']
        status = "✓" if total['valid'] else "✗"
        print(f"总解说字数: {status} {total['total_char_count']}字 (要求: 1300-1700字)")
        
        # 总体状态
        all_valid = (first.get('valid', False) and 
                    second.get('valid', False) and 
                    total['valid'])
        
        print(f"\n🎯 总体状态: {'✓ 全部符合要求' if all_valid else '✗ 存在问题'}")
        
        if not all_valid:
            print("\n💡 建议:")
            if not first.get('valid', False):
                print("  - 调整第一个特写的解说内容至30-32字")
            if not second.get('valid', False):
                print("  - 调整第二个特写的解说内容至30-32字")
            if not total['valid']:
                print("  - 调整总解说内容至1300-1700字之间")
            print("  - 使用 --auto-rewrite 参数可自动改写")

def demonstrate_command_usage():
    """
    演示命令行使用方法
    """
    print("\n" + "=" * 60)
    print("命令行使用方法")
    print("=" * 60)
    
    print("\n📝 基本验证（仅检查，不改写）:")
    print("python validate_narration.py data/001")
    
    print("\n🔧 自动改写模式（检查并自动改写不符合要求的内容）:")
    print("python validate_narration.py data/001 --auto-rewrite")
    
    print("\n📊 验证内容包括:")
    print("  ✓ 分镜1第一个特写解说字数 (30-32字)")
    print("  ✓ 分镜1第二个特写解说字数 (30-32字)")
    print("  ✓ 总解说内容字数 (1300-1700字)")
    
    print("\n🤖 自动改写功能:")
    print("  • 特写解说: 精准控制在30-32字，最多重试5次")
    print("  • 总解说内容: 调整至1300-1700字之间，最多重试3次")
    print("  • 保持原文核心意思和情感色彩")
    print("  • 自动保存改写后的内容")

def main():
    """
    主函数
    """
    try:
        demonstrate_total_validation()
        demonstrate_command_usage()
        
        print("\n" + "=" * 60)
        print("🎉 演示完成！")
        print("=" * 60)
        
    except Exception as e:
        print(f"❌ 演示过程中出错: {e}")
        sys.exit(1)

if __name__ == "__main__":
    main()