#!/usr/bin/env python3
"""
测试XML结构问题的检测
"""

import sys
import os
import re

# 添加项目根目录到路径
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from validate_narration import detect_incomplete_closeups_by_scene

def test_xml_structure_detection():
    """测试XML结构问题的检测"""
    
    # 读取测试文件
    test_file = "/Users/xunan/Projects/wrmVideo/test/test_xml_structure_issue.txt"
    with open(test_file, 'r', encoding='utf-8') as f:
        content = f.read()
    
    print("=== 测试内容 ===")
    print(content)
    print("\n=== 检测结果 ===")
    
    # 使用现有的检测函数
    issues = detect_incomplete_closeups_by_scene(content)
    
    if issues:
        for scene_num, scene_issues in issues.items():
            print(f"分镜 {scene_num}:")
            for issue in scene_issues:
                print(f"  - 图片特写{issue['closeup_number']}: {issue['details']}")
                print(f"    问题类型: {issue['issue_type']}")
                print(f"    原始内容: {repr(issue['original_content'][:100])}...")
    else:
        print("没有检测到问题")
    
    # 手动分析XML结构
    print("\n=== 手动分析 ===")
    
    # 查找所有图片特写开始标签
    start_tags = re.findall(r'<图片特写(\d+)>', content)
    print(f"找到的开始标签: {start_tags}")
    
    # 查找所有图片特写结束标签
    end_tags = re.findall(r'</图片特写(\d+)>', content)
    print(f"找到的结束标签: {end_tags}")
    
    # 查找孤立的图片prompt（没有被图片特写标签包围的）
    # 先移除所有完整的图片特写块
    temp_content = content
    complete_closeup_pattern = r'<图片特写\d+>.*?</图片特写\d+>'
    temp_content = re.sub(complete_closeup_pattern, '', temp_content, flags=re.DOTALL)
    
    # 在剩余内容中查找图片prompt
    orphan_prompts = re.findall(r'<图片prompt>.*?</图片prompt>', temp_content, re.DOTALL)
    print(f"找到的孤立图片prompt: {len(orphan_prompts)} 个")
    
    for i, prompt in enumerate(orphan_prompts):
        print(f"  孤立prompt {i+1}: {prompt[:50]}...")

if __name__ == "__main__":
    test_xml_structure_detection()