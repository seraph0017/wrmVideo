#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
测试XML结构验证和修复功能
"""

import os
import sys
import tempfile
import shutil
from pathlib import Path

# 添加项目根目录到Python路径
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))

from validate_narration import (
    extract_scene_closeup_numbers,
    validate_xml_structure_integrity,
    fix_scene_structure_with_llm
)

def test_extract_scene_closeup_numbers():
    """测试提取场景和特写编号功能"""
    print("测试提取场景和特写编号功能...")
    
    # 测试正常情况
    scene_content = """
    <scene_1>
        <closeup_1>
            <character_image>角色1</character_image>
            <narration>这是第一个特写</narration>
        </closeup_1>
        <closeup_2>
            <character_image>角色2</character_image>
            <narration>这是第二个特写</narration>
        </closeup_2>
    </scene_1>
    """
    
    scene_num, closeup_nums = extract_scene_closeup_numbers(scene_content)
    assert scene_num == 1, f"期望场景编号为1，实际为{scene_num}"
    assert closeup_nums == [1, 2], f"期望特写编号为[1, 2]，实际为{closeup_nums}"
    print("✓ 正常情况测试通过")
    
    # 测试缺失特写的情况
    scene_content_missing = """
    <scene_2>
        <closeup_1>
            <character_image>角色1</character_image>
            <narration>这是第一个特写</narration>
        </closeup_1>
        <closeup_3>
            <character_image>角色3</character_image>
            <narration>这是第三个特写</narration>
        </closeup_3>
    </scene_2>
    """
    
    scene_num, closeup_nums = extract_scene_closeup_numbers(scene_content_missing)
    assert scene_num == 2, f"期望场景编号为2，实际为{scene_num}"
    assert closeup_nums == [1, 3], f"期望特写编号为[1, 3]，实际为{closeup_nums}"
    print("✓ 缺失特写情况测试通过")

def test_validate_xml_structure_integrity():
    """测试XML结构完整性验证功能"""
    print("\n测试XML结构完整性验证功能...")
    
    # 测试正常的XML结构
    normal_content = """
    <scene_1>
        <closeup_1>
            <character_image>角色1</character_image>
            <narration>这是第一个特写</narration>
            <image_prompt>图片提示1</image_prompt>
        </closeup_1>
        <closeup_2>
            <character_image>角色2</character_image>
            <narration>这是第二个特写</narration>
            <image_prompt>图片提示2</image_prompt>
        </closeup_2>
    </scene_1>
    <scene_2>
        <closeup_1>
            <character_image>角色3</character_image>
            <narration>这是第三个特写</narration>
            <image_prompt>图片提示3</image_prompt>
        </closeup_1>
    </scene_2>
    """
    
    issues = validate_xml_structure_integrity(normal_content)
    if len(issues) > 0:
        print(f"检测到的问题:")
        for issue in issues:
            print(f"  - 场景{issue['scene_number']}: {issue['issue_type']}")
            if issue['details']:
                for detail in issue['details']:
                    print(f"    {detail}")
    assert len(issues) == 0, f"正常内容不应有问题，但发现了{len(issues)}个问题"
    print("✓ 正常XML结构验证通过")
    
    # 测试有问题的XML结构
    problematic_content = """
    <scene_1>
        <closeup_1>
            <character_image>角色1</character_image>
            <narration>这是第一个特写</narration>
        </closeup_1>
        <closeup_3>
            <character_image>角色3</character_image>
            <narration>这是第三个特写，缺少closeup_2</narration>
            <image_prompt>图片提示3</image_prompt>
        </closeup_3>
    </scene_1>
    <scene_2>
        <closeup_1>
            <character_image>角色4</character_image>
            <narration>这是第四个特写，缺少image_prompt</narration>
        </closeup_1>
    </scene_2>
    """
    
    issues = validate_xml_structure_integrity(problematic_content)
    assert len(issues) > 0, "有问题的内容应该被检测出来"
    print(f"✓ 检测到{len(issues)}个结构问题")
    
    # 检查具体问题类型
    scene_1_issues = [issue for issue in issues if issue['scene_number'] == 1]
    scene_2_issues = [issue for issue in issues if issue['scene_number'] == 2]
    
    assert len(scene_1_issues) > 0, "场景1应该有特写编号不连续的问题"
    assert len(scene_2_issues) > 0, "场景2应该有缺少子标签的问题"
    print("✓ 问题类型检测正确")

def create_test_narration_file():
    """创建测试用的narration.txt文件"""
    content = """
<scene_1>
    <closeup_1>
        <character_image>小明</character_image>
        <narration>小明走进了教室，看到同学们都在认真学习。</narration>
        <image_prompt>一个年轻的学生走进教室</image_prompt>
    </closeup_1>
    <closeup_3>
        <character_image>老师</character_image>
        <narration>老师正在黑板上写着数学公式，专注而认真。</narration>
    </closeup_3>
</scene_1>
<scene_2>
    <closeup_1>
        <character_image>小红</character_image>
        <narration>小红举手回答问题，声音清晰响亮。</narration>
        <image_prompt>一个女学生举手发言</image_prompt>
    </closeup_1>
</scene_2>
"""
    return content

def test_integration():
    """集成测试：测试完整的验证和修复流程"""
    print("\n进行集成测试...")
    
    # 创建临时目录和文件
    with tempfile.TemporaryDirectory() as temp_dir:
        test_file = os.path.join(temp_dir, "narration.txt")
        
        # 写入测试内容
        test_content = create_test_narration_file()
        with open(test_file, 'w', encoding='utf-8') as f:
            f.write(test_content)
        
        print(f"✓ 创建测试文件: {test_file}")
        
        # 验证XML结构
        issues = validate_xml_structure_integrity(test_content)
        print(f"✓ 检测到{len(issues)}个结构问题")
        
        # 验证问题类型
        for issue in issues:
            print(f"  - 场景{issue['scene_number']}: {issue['issue_type']}")
            if issue['details']:
                for detail in issue['details']:
                    print(f"    {detail}")
        
        print("✓ 集成测试完成")

def main():
    """运行所有测试"""
    print("开始XML结构验证功能测试...")
    print("=" * 50)
    
    try:
        test_extract_scene_closeup_numbers()
        test_validate_xml_structure_integrity()
        test_integration()
        
        print("\n" + "=" * 50)
        print("✅ 所有测试通过！")
        
    except Exception as e:
        print(f"\n❌ 测试失败: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)

if __name__ == "__main__":
    main()