#!/usr/bin/env python3
"""
测试validate_narration.py中新增的不完整图片特写修复功能
"""

import sys
import os
import shutil
import tempfile

# 添加项目根目录到Python路径
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from validate_narration import detect_incomplete_closeups_by_scene, fix_incomplete_closeup_with_llm

def test_detect_incomplete_closeups():
    """测试检测不完整图片特写的功能"""
    print("=== 测试检测不完整图片特写功能 ===")
    
    # 读取测试文件
    test_file = "/Users/xunan/Projects/wrmVideo/test/test_incomplete_closeup.txt"
    with open(test_file, 'r', encoding='utf-8') as f:
        content = f.read()
    
    # 检测不完整的图片特写
    issues_by_scene = detect_incomplete_closeups_by_scene(content)
    
    # 统计总的不完整特写数量
    total_issues = sum(len(issues) for issues in issues_by_scene.values())
    print(f"检测到 {total_issues} 个不完整的图片特写:")
    
    detected_positions = []
    for scene_num, issues in issues_by_scene.items():
        for issue in issues:
            closeup_num = issue['closeup_number']
            issue_type = issue['issue_type']
            details = issue['details']
            
            print(f"  - 分镜{scene_num} 图片特写{closeup_num}")
            print(f"    问题类型: {issue_type}")
            print(f"    详情: {details}")
            print()
            
            detected_positions.append((scene_num, closeup_num))
    
    # 验证检测结果
    expected_incomplete = [
        (1, 2),  # 分镜1的图片特写2
        (2, 1),  # 分镜2的图片特写1  
        (2, 3),  # 分镜2的图片特写3
    ]
    
    if sorted(detected_positions) == sorted(expected_incomplete):
        print("✓ 检测功能正常，成功识别所有不完整的图片特写")
        return True
    else:
        print(f"✗ 检测功能异常")
        print(f"  期望: {sorted(expected_incomplete)}")
        print(f"  实际: {sorted(detected_positions)}")
        return False

def test_fix_incomplete_closeup():
    """测试修复不完整图片特写的功能"""
    print("\n=== 测试修复不完整图片特写功能 ===")
    
    # 测试用例：只有图片prompt的特写
    incomplete_closeup = """<图片特写2>
<图片prompt>一个神秘的黑衣人出现在森林中，面容隐藏在阴影里</图片prompt>
</图片特写2>"""
    
    scene_context = "这是一个武侠故事的场景，主角吴双正在寻找失踪的朋友。"
    
    print("原始不完整特写:")
    print(incomplete_closeup)
    print()
    
    try:
        # 创建LLM客户端（需要有效的API配置）
        from config.config import ARK_CONFIG
        from volcenginesdkarkruntime import Ark
        
        client = Ark(
            base_url=ARK_CONFIG['base_url'],
            api_key=ARK_CONFIG['api_key']
        )
        
        # 尝试修复（注意：这需要有效的API配置）
        fixed_closeup = fix_incomplete_closeup_with_llm(
            client=client,
            closeup_content=incomplete_closeup,
            scene_number=1,
            closeup_number=2,
            issue_type='only_image_prompt',
            context_content=scene_context
        )
        
        print("修复后的特写:")
        print(fixed_closeup)
        print()
        
        # 检查修复结果是否包含必要的标签
        required_tags = ['<特写人物>', '<解说内容>', '<图片prompt>']
        missing_tags = [tag for tag in required_tags if tag not in fixed_closeup]
        
        if not missing_tags:
            print("✓ 修复功能正常，包含所有必要标签")
            return True
        else:
            print(f"✗ 修复功能异常，缺少标签: {missing_tags}")
            return False
            
    except Exception as e:
        print(f"✗ 修复功能测试失败: {str(e)}")
        print("  注意：这可能是由于API配置问题导致的")
        return False

def main():
    """主测试函数"""
    print("开始测试不完整图片特写修复功能...\n")
    
    # 测试检测功能
    detect_success = test_detect_incomplete_closeups()
    
    # 测试修复功能（可能因为API配置而失败）
    fix_success = test_fix_incomplete_closeup()
    
    print("\n=== 测试结果汇总 ===")
    print(f"检测功能: {'✓ 通过' if detect_success else '✗ 失败'}")
    print(f"修复功能: {'✓ 通过' if fix_success else '✗ 失败'}")
    
    if detect_success:
        print("\n核心检测功能正常工作！")
    else:
        print("\n检测功能存在问题，需要进一步调试。")

if __name__ == "__main__":
    main()