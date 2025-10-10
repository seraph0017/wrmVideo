#!/usr/bin/env python3
"""
测试分镜结构修复功能
验证能否正确检测和修复data/025中的XML结构问题
"""

import sys
import os
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from validate_narration import (
    validate_xml_structure_integrity,
    detect_incomplete_closeups_by_scene,
    fix_scene_structure_with_llm,
    fix_incomplete_closeups_by_scene
)
from volcenginesdkarkruntime import Ark
from config.config import ARK_CONFIG

def test_scene_structure_detection():
    """测试分镜结构问题检测"""
    print("=== 测试分镜结构问题检测 ===")
    
    # 读取有问题的文件
    test_file = "/Users/xunan/Projects/wrmVideo/data/025/chapter_001/narration.txt"
    
    if not os.path.exists(test_file):
        print(f"测试文件不存在: {test_file}")
        return False
    
    with open(test_file, 'r', encoding='utf-8') as f:
        content = f.read()
    
    # 检测XML结构问题
    print("1. 检测XML结构完整性...")
    xml_issues = validate_xml_structure_integrity(content)
    print(f"   发现 {len(xml_issues)} 个XML结构问题:")
    for issue in xml_issues:
        print(f"   - {issue}")
    
    # 检测分镜级别的问题
    print("\n2. 检测分镜级别的问题...")
    scene_issues = detect_incomplete_closeups_by_scene(content)
    print(f"   发现 {len(scene_issues)} 个分镜问题:")
    for scene_num, issues in scene_issues.items():
        print(f"   分镜{scene_num}: {len(issues)} 个问题")
        for issue in issues:
            print(f"     - {issue}")
    
    return len(xml_issues) > 0 or len(scene_issues) > 0

def test_scene_structure_fix():
    """测试分镜结构修复功能"""
    print("\n=== 测试分镜结构修复功能 ===")
    
    # 初始化Ark客户端
    try:
        api_key = ARK_CONFIG.get("api_key") or os.getenv("ARK_API_KEY")
        if not api_key:
            print("错误: 未找到API密钥")
            print("请在config/config.py中配置ARK_CONFIG['api_key']或设置ARK_API_KEY环境变量")
            return False
            
        client = Ark(
            api_key=api_key,
            base_url=ARK_CONFIG.get("base_url", "https://ark.cn-beijing.volces.com/api/v3")
        )
    except Exception as e:
        print(f"无法初始化Ark客户端: {e}")
        return False
    
    # 读取有问题的文件
    test_file = "/Users/xunan/Projects/wrmVideo/data/025/chapter_001/narration.txt"
    
    with open(test_file, 'r', encoding='utf-8') as f:
        content = f.read()
    
    # 创建备份
    backup_file = test_file + ".backup"
    with open(backup_file, 'w', encoding='utf-8') as f:
        f.write(content)
    print(f"已创建备份文件: {backup_file}")
    
    # 尝试修复
    print("\n开始修复分镜结构问题...")
    try:
        fixed_content = fix_incomplete_closeups_by_scene(content, client)
        
        # 验证修复结果
        print("\n验证修复结果...")
        xml_issues_after = validate_xml_structure_integrity(fixed_content)
        scene_issues_after = detect_incomplete_closeups_by_scene(fixed_content)
        
        print(f"修复后XML结构问题: {len(xml_issues_after)} 个")
        print(f"修复后分镜问题: {len(scene_issues_after)} 个")
        
        if len(xml_issues_after) == 0 and len(scene_issues_after) == 0:
            print("✓ 修复成功！所有结构问题已解决")
            
            # 保存修复后的内容
            fixed_file = test_file.replace('.txt', '_fixed.txt')
            with open(fixed_file, 'w', encoding='utf-8') as f:
                f.write(fixed_content)
            print(f"修复后的内容已保存到: {fixed_file}")
            return True
        else:
            print("⚠ 修复后仍有问题存在")
            if xml_issues_after:
                for issue in xml_issues_after:
                    print(f"   XML问题: {issue}")
            if scene_issues_after:
                for scene_num, issues in scene_issues_after.items():
                    print(f"   分镜{scene_num}问题: {issues}")
            return False
            
    except Exception as e:
        print(f"修复过程中发生错误: {e}")
        return False

def main():
    """主测试函数"""
    print("开始测试分镜结构修复功能\n")
    
    # 检查API密钥配置
    api_key = ARK_CONFIG.get("api_key") or os.getenv("ARK_API_KEY")
    if not api_key:
        print("错误: 未找到API密钥")
        print("请在config/config.py中配置ARK_CONFIG['api_key']或设置ARK_API_KEY环境变量")
        return
    
    # 测试检测功能
    has_issues = test_scene_structure_detection()
    
    if not has_issues:
        print("未检测到结构问题，测试结束")
        return
    
    # 测试修复功能
    fix_success = test_scene_structure_fix()
    
    if fix_success:
        print("\n🎉 测试完成：分镜结构修复功能正常工作")
    else:
        print("\n❌ 测试失败：分镜结构修复功能需要进一步调试")

if __name__ == "__main__":
    main()