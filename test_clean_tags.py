#!/usr/bin/env python3
"""
测试清理重复标签功能
"""

import sys
import os
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from validate_narration import clean_duplicate_tags

def test_clean_duplicate_tags():
    """测试清理重复标签功能"""
    
    # 测试用例1：简单的重复标签
    test1 = "</图片特写2></图片特写2></图片特写2>"
    result1 = clean_duplicate_tags(test1)
    print(f"测试1:")
    print(f"输入: {test1}")
    print(f"输出: {result1}")
    print(f"期望: </图片特写2>")
    print(f"结果: {'✓' if result1 == '</图片特写2>' else '✗'}")
    print()
    
    # 测试用例2：多种标签的重复
    test2 = """<特写人物>
<角色姓名>吴毅</角色姓名>
<时代背景>古代</时代背景>
<角色形象>古代形象</角色形象>
</特写人物>
<解说内容>测试内容</解说内容>
<图片prompt>测试prompt</图片prompt>
</图片特写2></图片特写2></图片特写2></图片特写2></图片特写2></图片特写2></图片特写2>"""
    
    result2 = clean_duplicate_tags(test2)
    print(f"测试2:")
    print(f"输入末尾: ...{test2[-100:]}")
    print(f"输出末尾: ...{result2[-100:]}")
    print(f"是否包含重复标签: {'✗' if '</图片特写2></图片特写2>' in result2 else '✓'}")
    print()
    
    # 测试用例3：检查实际文件中的问题
    with open('data/025/chapter_001/narration.txt', 'r', encoding='utf-8') as f:
        content = f.read()
    
    # 查找分镜4图片特写2的内容
    import re
    pattern = r'<图片特写2>(.*?)</图片特写2>'
    matches = re.findall(pattern, content, re.DOTALL)
    
    if matches:
        print(f"测试3: 实际文件中的图片特写2")
        for i, match in enumerate(matches):
            if i >= 2:  # 只看前几个
                break
            lines = match.split('\n')
            print(f"图片特写2-{i+1} 末尾几行:")
            for line in lines[-5:]:
                if line.strip():
                    print(f"  {line}")
        
        # 检查结束标签
        end_pattern = r'</图片特写2>+'
        end_matches = re.findall(end_pattern, content)
        print(f"找到的结束标签: {end_matches[:5]}")  # 只显示前5个

if __name__ == "__main__":
    test_clean_duplicate_tags()