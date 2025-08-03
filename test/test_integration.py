#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
测试gen_script.py和gen_image.py的集成
"""

import os
import sys
import tempfile

# 添加项目根目录到Python路径
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from gen_script import ScriptGenerator
from gen_image import parse_narration_file, find_character_image_by_attributes

def test_integration():
    """
    测试脚本生成和图片解析的集成
    """
    print("=== 测试gen_script.py和gen_image.py集成 ===")
    
    # 创建测试小说内容
    test_novel_content = """
第一章 初入江湖

少年李明站在山崖边，望着远方的江湖。他身穿白色长袍，手持长剑，眼中闪烁着坚定的光芒。

"师父，我已经准备好了。"李明转身对着身后的老者说道。

老者点了点头，"去吧，孩子。记住，江湖险恶，要保护好自己。"

李明深深鞠了一躬，然后纵身跃下山崖，开始了他的江湖之路。
    """
    
    # 创建临时文件
    with tempfile.NamedTemporaryFile(mode='w', suffix='.txt', delete=False, encoding='utf-8') as f:
        f.write(test_novel_content)
        temp_novel_file = f.name
    
    try:
        # 创建临时输出目录
        temp_output_dir = tempfile.mkdtemp()
        print(f"临时输出目录: {temp_output_dir}")
        
        # 测试脚本生成
        print("\n=== 步骤1: 测试脚本生成 ===")
        script_generator = ScriptGenerator()
        
        # 生成章节解说
        narration = script_generator.generate_chapter_narration(
            chapter_content=test_novel_content,
            chapter_num=1,
            total_chapters=1
        )
        
        if narration:
            print(f"✅ 解说文案生成成功，长度: {len(narration)} 字符")
            print(f"前100字符: {narration[:100]}...")
            
            # 保存到临时文件
            narration_file = os.path.join(temp_output_dir, 'narration.txt')
            with open(narration_file, 'w', encoding='utf-8') as f:
                f.write(narration)
            print(f"解说文案已保存到: {narration_file}")
            
            # 测试解析
            print("\n=== 步骤2: 测试解说文案解析 ===")
            scenes, drawing_style = parse_narration_file(narration_file)
            
            if scenes:
                print(f"✅ 解析成功，找到 {len(scenes)} 个分镜")
                print(f"绘画风格: {drawing_style}")
                
                # 测试特写人物信息
                print("\n=== 步骤3: 测试特写人物信息 ===")
                for i, scene in enumerate(scenes[:3], 1):  # 只测试前3个分镜
                    print(f"\n分镜 {i}:")
                    print(f"  特写数量: {len(scene['closeups'])}")
                    
                    for j, closeup in enumerate(scene['closeups'][:2], 1):  # 只测试前2个特写
                        print(f"  特写 {j}:")
                        gender = closeup.get('gender', '')
                        age_group = closeup.get('age_group', '')
                        character_style = closeup.get('character_style', '')
                        
                        print(f"    性别: {gender}")
                        print(f"    年龄段: {age_group}")
                        print(f"    风格: {character_style}")
                        
                        # 测试角色图片查找
                        if gender and age_group and character_style:
                            char_img_path = find_character_image_by_attributes(
                                gender, age_group, character_style
                            )
                            if char_img_path:
                                print(f"    ✅ 找到角色图片: {os.path.basename(char_img_path)}")
                            else:
                                print(f"    ⚠️ 未找到角色图片")
                        else:
                            print(f"    ❌ 特写人物信息不完整")
                
                print("\n=== 集成测试完成 ===")
                return True
            else:
                print("❌ 解析失败，未找到分镜信息")
                return False
        else:
            print("❌ 解说文案生成失败")
            return False
            
    except Exception as e:
        print(f"❌ 测试过程中发生错误: {e}")
        return False
    finally:
        # 清理临时文件
        try:
            os.unlink(temp_novel_file)
            import shutil
            shutil.rmtree(temp_output_dir)
        except Exception:
            pass

if __name__ == '__main__':
    test_integration()