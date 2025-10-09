#!/usr/bin/env python3
"""
XML结构修复功能完整测试
测试validate_narration.py中的XML结构验证和自动修复功能
"""

import os
import sys
import tempfile
from pathlib import Path

# 添加项目根目录到Python路径
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))

from validate_narration import validate_narration_file

def create_test_narration_with_issues():
    """
    创建一个包含XML结构问题的测试解说文件
    
    Returns:
        str: 测试文件内容
    """
    content = """<scene_1>
<closeup_1>
<character>
<name>李明</name>
<era>现代都市</era>
<appearance>年轻商务男性，西装革履</appearance>
</character>
<narration>李明走进了公司大楼，准备开始新的一天工作。</narration>
<image_prompt>一个穿着西装的年轻男性走进现代化的办公大楼</image_prompt>
</closeup_1>

<closeup_3>
<character>
<name>李明</name>
</character>
<narration>他乘坐电梯来到了二十层的办公室。</narration>
</closeup_3>
</scene_1>

<scene_2>
<closeup_1>
<character>
<name>张总</name>
<era>现代都市</era>
<appearance>中年商务人士，气质沉稳</appearance>
</character>
<narration>张总正在办公室里等待着李明的到来。</narration>
<image_prompt>一个中年商务人士坐在办公室里</image_prompt>
</closeup_1>
</scene_2>"""
    
    return content

def test_xml_structure_validation_only():
    """
    测试仅验证XML结构（不修复）
    """
    print("测试XML结构验证功能（不修复）...")
    
    # 创建临时文件
    with tempfile.NamedTemporaryFile(mode='w', suffix='.txt', delete=False, encoding='utf-8') as f:
        content = create_test_narration_with_issues()
        f.write(content)
        temp_file = f.name
    
    try:
        # 验证但不修复
        result = validate_narration_file(
            temp_file, 
            auto_fix_structure=False
        )
        
        print(f"✓ 验证完成，文件: {temp_file}")
        print(f"  - 结构验证: {'通过' if result['structure_validation']['valid'] else '失败'}")
        
        if not result['structure_validation']['valid']:
            issues = result['structure_validation']['issues']
            print(f"  - 检测到{len(issues)}个结构问题:")
            for issue in issues:
                print(f"    * 场景{issue['scene_number']}: {issue['issue_type']} - {issue['details']}")
        
        return len(result['structure_validation']['issues']) > 0
        
    finally:
        # 清理临时文件
        os.unlink(temp_file)

def test_xml_structure_fix_without_llm():
    """
    测试XML结构修复功能（不使用LLM，仅测试框架）
    """
    print("\n测试XML结构修复框架...")
    
    # 创建临时文件
    with tempfile.NamedTemporaryFile(mode='w', suffix='.txt', delete=False, encoding='utf-8') as f:
        content = create_test_narration_with_issues()
        f.write(content)
        temp_file = f.name
    
    try:
        # 尝试修复（没有LLM客户端，应该跳过修复）
        result = validate_narration_file(
            temp_file, 
            auto_fix_structure=True,
            client=None  # 没有LLM客户端
        )
        
        print(f"✓ 修复测试完成，文件: {temp_file}")
        print(f"  - 结构验证: {'通过' if result['structure_validation']['valid'] else '失败'}")
        
        if not result['structure_validation']['valid']:
            issues = result['structure_validation']['issues']
            print(f"  - 仍有{len(issues)}个结构问题（预期，因为没有LLM客户端）")
        
        return True
        
    finally:
        # 清理临时文件
        os.unlink(temp_file)

def main():
    """
    运行所有测试
    """
    print("开始XML结构修复功能测试...")
    print("=" * 50)
    
    try:
        # 测试1: 仅验证
        has_issues = test_xml_structure_validation_only()
        if not has_issues:
            print("✗ 测试失败：应该检测到结构问题")
            return False
        
        # 测试2: 修复框架测试
        framework_ok = test_xml_structure_fix_without_llm()
        if not framework_ok:
            print("✗ 测试失败：修复框架测试失败")
            return False
        
        print("\n" + "=" * 50)
        print("✅ 所有XML结构修复功能测试通过！")
        print("\n注意：完整的LLM修复功能需要配置ARK_CONFIG才能测试")
        return True
        
    except Exception as e:
        print(f"\n✗ 测试过程中发生错误: {str(e)}")
        import traceback
        traceback.print_exc()
        return False

if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1)