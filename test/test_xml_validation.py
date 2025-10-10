#!/usr/bin/env python3
"""
测试现有的XML结构验证功能
"""

import sys
import os

# 添加项目根目录到路径
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from validate_narration import validate_xml_structure_integrity

def test_xml_validation():
    """测试XML结构验证功能"""
    
    # 读取测试文件
    test_file = "/Users/xunan/Projects/wrmVideo/test/test_xml_structure_issue.txt"
    with open(test_file, 'r', encoding='utf-8') as f:
        content = f.read()
    
    print("=== 测试内容 ===")
    print(content)
    print("\n=== XML结构验证结果 ===")
    
    # 使用现有的XML结构验证功能
    issues = validate_xml_structure_integrity(content)
    
    if issues:
        for issue in issues:
            print(f"分镜 {issue['scene_number']}: {issue['issue_type']}")
            for detail in issue['details']:
                print(f"  - {detail}")
    else:
        print("没有检测到XML结构问题")

if __name__ == "__main__":
    test_xml_validation()