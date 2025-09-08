#!/usr/bin/env python
# -*- coding: utf-8 -*-

import os
import sys
import django
import glob

# 添加项目路径
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

# 设置Django环境
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'web.settings')
django.setup()

from video.utils import parse_narration_file
from video.models import Novel, Chapter, Character, Narration

def test_parse_narration():
    """
    测试解析解说文案功能
    """
    novel_id = 13
    project_root = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
    data_dir = os.path.join(project_root, f"data/{novel_id:03d}")
    
    print(f"数据目录: {data_dir}")
    print(f"目录是否存在: {os.path.exists(data_dir)}")
    
    # 查找解说文案文件
    narration_files = glob.glob(os.path.join(data_dir, 'chapter_*/narration.txt'))
    print(f"找到解说文案文件: {len(narration_files)} 个")
    
    for narration_file in narration_files:
        print(f"\n处理文件: {narration_file}")
        
        try:
            # 读取文件内容
            with open(narration_file, 'r', encoding='utf-8') as f:
                content = f.read()
            
            print(f"文件大小: {len(content)} 字符")
            print(f"前100字符: {content[:100]}...")
            
            # 解析内容
            parsed_data = parse_narration_file(content)
            
            print(f"解析结果:")
            print(f"  章节信息: {parsed_data['chapter_info']}")
            print(f"  角色数量: {len(parsed_data['characters'])}")
            print(f"  分镜数量: {len(parsed_data['narrations'])}")
            
            # 显示角色信息
            for i, char in enumerate(parsed_data['characters']):
                print(f"    角色{i+1}: {char.get('name', '未知')} ({char.get('gender', '未知')}, {char.get('age_group', '未知')})")
            
            # 显示前3个分镜
            for i, narration in enumerate(parsed_data['narrations'][:3]):
                print(f"    分镜{i+1}: {narration['scene_number']} - {narration['featured_character']}")
                print(f"      解说: {narration['narration'][:50]}...")
            
            if len(parsed_data['narrations']) > 3:
                print(f"    ... 还有 {len(parsed_data['narrations']) - 3} 个分镜")
                
        except Exception as e:
            print(f"处理文件时出错: {str(e)}")
            import traceback
            traceback.print_exc()

if __name__ == '__main__':
    test_parse_narration()