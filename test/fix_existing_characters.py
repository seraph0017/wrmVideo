#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
修复已存在的错误角色定义
特别是修复"玉箫天女"和"兰心天女"等被错误定义为男性的角色
"""

import sys
import os
import re
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from validate_narration import generate_character_definition

def fix_character_definitions(file_path):
    """
    修复文件中错误的角色定义
    
    Args:
        file_path (str): narration.txt文件路径
    """
    print(f"正在修复文件: {file_path}")
    
    with open(file_path, 'r', encoding='utf-8') as f:
        content = f.read()
    
    # 查找需要修复的角色（包含"天女"但性别为Male的角色）
    # 修改正则表达式以匹配复杂的姓名标签格式
    pattern = r'<角色(\d+)>\s*<姓名>.*?天女.*?</姓名>.*?<性别>Male</性别>.*?</角色\1>'
    role_matches = re.findall(pattern, content, re.DOTALL)
    
    # 提取角色编号和完整的角色定义
    matches = []
    for role_num in role_matches:
        # 找到完整的角色定义
        full_pattern = r'<角色' + role_num + r'>.*?</角色' + role_num + r'>'
        full_match = re.search(full_pattern, content, re.DOTALL)
        if full_match:
            role_def = full_match.group(0)
            # 从角色定义中提取角色姓名
            name_pattern = r'<角色姓名>([^<]+)</角色姓名>'
            name_match = re.search(name_pattern, role_def)
            if name_match and '天女' in name_match.group(1):
                matches.append((role_num, name_match.group(1), role_def))
    
    if not matches:
        print("  未发现需要修复的角色")
        return False
    
    updated_content = content
    fixed_count = 0
    
    for role_num, character_name, role_def in matches:
        print(f"  发现错误角色: {character_name} (角色{role_num}) - 性别被错误设置为Male")
        
        # 角色名称已经是干净的
        clean_name = character_name
        
        # 提取相关上下文
        context_content = ""
        
        # 查找包含该角色名的解说内容
        narration_pattern = r'<解说内容>([^<]*?' + re.escape(clean_name) + r'[^<]*?)</解说内容>'
        narration_matches = re.findall(narration_pattern, content, re.DOTALL)
        if narration_matches:
            context_content += " ".join(narration_matches)
        
        # 查找包含该角色名的图片描述
        image_desc_pattern = r'<图片描述>([^<]*?' + re.escape(clean_name) + r'[^<]*?)</图片描述>'
        image_desc_matches = re.findall(image_desc_pattern, content, re.DOTALL)
        if image_desc_matches:
            context_content += " " + " ".join(image_desc_matches)
        
        print(f"    提取的上下文: {context_content[:100]}...")
        
        # 生成新的角色定义
        new_char_def = generate_character_definition(clean_name, context_content)
        
        # 添加角色编号
        new_char_def = new_char_def.replace('<角色>', f'<角色{role_num}>')
        new_char_def = new_char_def.replace('</角色>', f'</角色{role_num}>')
        
        # 保持原有的姓名格式（包含所有原始标签）
        original_name_pattern = r'<姓名>.*?</姓名>'
        original_name_match = re.search(original_name_pattern, role_def, re.DOTALL)
        if original_name_match:
            original_name_tag = original_name_match.group(0)
            new_char_def = new_char_def.replace(f'<姓名>{clean_name}</姓名>', original_name_tag)
        
        # 替换原有的角色定义
        updated_content = updated_content.replace(role_def, new_char_def)
        
        # 提取新定义中的性别
        gender_match = re.search(r'<性别>([^<]+)</性别>', new_char_def)
        new_gender = gender_match.group(1) if gender_match else "Unknown"
        
        print(f"    已修复: {clean_name} -> 性别: {new_gender}")
        fixed_count += 1
    
    if fixed_count > 0:
        # 写回文件
        with open(file_path, 'w', encoding='utf-8') as f:
            f.write(updated_content)
        print(f"  已修复 {fixed_count} 个角色定义并保存文件")
        return True
    
    return False

def main():
    """
    主函数
    """
    # 修复chapter_007中的角色定义
    file_path = "/Users/xunan/Projects/wrmVideo/data/006/chapter_007/narration.txt"
    
    if os.path.exists(file_path):
        success = fix_character_definitions(file_path)
        if success:
            print("\n修复完成！")
        else:
            print("\n无需修复或修复失败")
    else:
        print(f"文件不存在: {file_path}")

if __name__ == "__main__":
    main()