#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
测试解说文案解析功能
"""

import os
import sys
import django

# 添加项目根目录到Python路径
project_root = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, project_root)
sys.path.insert(0, os.path.join(project_root, 'web'))

# 设置Django环境
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'web.settings')
django.setup()

from video.utils import parse_narration_file


def test_parse_narration_file():
    """
    测试解说文案解析函数
    """
    print("开始测试解说文案解析功能...")
    
    # 测试文件路径
    test_file = os.path.join(project_root, 'data/001/chapter_001/narration.txt')
    
    if not os.path.exists(test_file):
        print(f"测试文件不存在: {test_file}")
        return False
    
    try:
        # 读取测试文件
        with open(test_file, 'r', encoding='utf-8') as f:
            content = f.read()
        
        print(f"读取文件成功，内容长度: {len(content)} 字符")
        
        # 解析文件内容
        result = parse_narration_file(content)
        
        print("\n=== 解析结果 ===")
        print(f"章节信息: {result['chapter_info']}")
        print(f"角色数量: {len(result['characters'])}")
        print(f"分镜数量: {len(result['narrations'])}")
        
        # 显示角色信息
        print("\n=== 角色信息 ===")
        for i, char in enumerate(result['characters']):
            print(f"角色 {i+1}: {char}")
        
        # 显示前3个分镜信息
        print("\n=== 分镜信息 (前3个) ===")
        for i, narration in enumerate(result['narrations'][:3]):
            print(f"分镜 {i+1}:")
            print(f"  场景编号: {narration['scene_number']}")
            print(f"  特写人物: {narration['featured_character']}")
            print(f"  解说内容: {narration['narration'][:100]}...")
            print(f"  图片提示: {narration['image_prompt'][:100]}...")
            print()
        
        print("解析测试完成！")
        return True
        
    except Exception as e:
        print(f"解析测试失败: {str(e)}")
        import traceback
        traceback.print_exc()
        return False


def test_database_integration():
    """
    测试数据库集成功能
    """
    print("\n开始测试数据库集成功能...")
    
    try:
        from video.models import Novel, Chapter, Character, Narration
        
        # 查找测试小说
        try:
            novel = Novel.objects.get(id=1)
            print(f"找到测试小说: {novel.name}")
        except Novel.DoesNotExist:
            print("未找到ID为1的小说，创建测试小说...")
            novel = Novel.objects.create(
                name="测试小说",
                word_count=10000,
                type="玄幻"
            )
            print(f"创建测试小说: {novel.name}")
        
        # 查看相关的章节
        chapters = Chapter.objects.filter(novel=novel)
        print(f"小说章节数量: {chapters.count()}")
        
        for chapter in chapters:
            print(f"章节: {chapter.title}, 格式: {chapter.format}")
            
            # 查看章节的角色
            characters = chapter.characters.all()
            print(f"  角色数量: {characters.count()}")
            for char in characters:
                print(f"    - {char.name} ({char.gender}, {char.age_group})")
            
            # 查看章节的解说
            narrations = chapter.narrations.all()
            print(f"  分镜数量: {narrations.count()}")
            for narration in narrations[:3]:  # 只显示前3个
                print(f"    - 分镜{narration.scene_number}: {narration.featured_character}")
        
        print("数据库集成测试完成！")
        return True
        
    except Exception as e:
        print(f"数据库集成测试失败: {str(e)}")
        import traceback
        traceback.print_exc()
        return False


if __name__ == '__main__':
    print("=" * 50)
    print("解说文案解析功能测试")
    print("=" * 50)
    
    # 测试解析功能
    parse_success = test_parse_narration_file()
    
    # 测试数据库集成
    db_success = test_database_integration()
    
    print("\n=== 测试总结 ===")
    print(f"解析功能测试: {'通过' if parse_success else '失败'}")
    print(f"数据库集成测试: {'通过' if db_success else '失败'}")
    
    if parse_success and db_success:
        print("\n🎉 所有测试通过！解说文案自动匹配功能已就绪。")
    else:
        print("\n❌ 部分测试失败，请检查相关功能。")