#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
test_dynamic_characters.py - 测试动态角色生成功能

测试修改后的章节解说生成器是否能够：
1. 动态识别章节中的角色
2. 生成相应数量的角色信息
3. 在分镜中正确引用这些角色
"""

import os
import sys

# 添加项目根目录到路径
project_root = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, project_root)

from gen_script_v2 import ScriptGeneratorV2

def test_dynamic_character_generation():
    """
    测试动态角色生成功能
    """
    print("=== 测试动态角色生成功能 ===")
    
    # 创建脚本生成器实例
    try:
        generator = ScriptGeneratorV2()
        print("✓ 脚本生成器初始化成功")
    except Exception as e:
        print(f"✗ 脚本生成器初始化失败：{e}")
        return False
    
    # 测试章节内容 - 包含多个角色
    test_chapter_content = """
    第一章 初入江湖
    
    &李逍遥&是一个十八岁的少年，住在余杭镇的客栈里。这天早上，他正在院子里练剑，
    突然听到门外传来马蹄声。一位身穿白衣的女子&赵灵儿&骑马而来，她看起来约十六岁，
    容貌绝美，但神情焦急。
    
    "公子，请问这里是李家客栈吗？"&赵灵儿&下马问道。
    
    &李逍遥&放下手中的木剑，"正是，姑娘有何贵干？"
    
    这时，客栈老板&李大叔&从屋里走出来，他是&李逍遥&的叔叔，五十多岁，
    为人和善。"灵儿姑娘，你怎么来了？"
    
    原来&赵灵儿&是来寻求帮助的。她的师父&林月如&被妖怪抓走了，
    &林月如&是一位三十岁的女剑客，武功高强。现在&赵灵儿&需要找人帮忙救援。
    
    "我愿意帮助姑娘！"&李逍遥&毫不犹豫地说道。
    
    就在这时，一个神秘的黑衣人&神秘剑客&出现在屋顶上，他的年龄不详，
    只露出一双锐利的眼睛。"想救人？先过我这一关！"
    """
    
    print("\n测试章节内容包含角色：")
    print("- 李逍遥（18岁少年，主角）")
    print("- 赵灵儿（16岁女子，重要配角）")
    print("- 李大叔（50多岁，客栈老板）")
    print("- 林月如（30岁女剑客，被抓角色）")
    print("- 神秘剑客（年龄不详，反派角色）")
    
    # 生成章节解说
    print("\n正在生成章节解说...")
    try:
        narration = generator.generate_chapter_narration(
            chapter_content=test_chapter_content,
            chapter_num=1,
            total_chapters=10
        )
        
        if narration:
            print("✓ 章节解说生成成功")
            
            # 保存生成结果
            output_file = os.path.join(project_root, "test_dynamic_characters_output.txt")
            with open(output_file, 'w', encoding='utf-8') as f:
                f.write("=== 动态角色生成测试结果 ===\n\n")
                f.write(f"测试章节内容：\n{test_chapter_content}\n\n")
                f.write("=== 生成的解说文案 ===\n\n")
                f.write(narration)
            
            print(f"✓ 生成结果已保存到：{output_file}")
            
            # 简单分析生成结果
            analyze_generated_content(narration)
            
            return True
        else:
            print("✗ 章节解说生成失败")
            return False
            
    except Exception as e:
        print(f"✗ 生成过程出错：{e}")
        return False

def analyze_generated_content(narration):
    """
    分析生成的内容，检查角色是否正确识别
    """
    print("\n=== 生成内容分析 ===")
    
    # 检查是否包含角色信息
    if "<出镜人物>" in narration:
        print("✓ 包含出镜人物信息")
    else:
        print("✗ 缺少出镜人物信息")
    
    # 检查角色标签格式
    import re
    character_tags = re.findall(r'<角色\d+>', narration)
    if character_tags:
        print(f"✓ 找到角色标签：{character_tags}")
        print(f"✓ 识别到 {len(character_tags)} 个角色")
    else:
        print("✗ 未找到角色标签")
    
    # 检查角色姓名
    expected_names = ["李逍遥", "赵灵儿", "李大叔", "林月如", "神秘剑客"]
    found_names = []
    for name in expected_names:
        if name in narration:
            found_names.append(name)
    
    if found_names:
        print(f"✓ 识别到的角色姓名：{found_names}")
    else:
        print("✗ 未识别到预期的角色姓名")
    
    # 检查分镜数量
    scene_tags = re.findall(r'<分镜\d+>', narration)
    if scene_tags:
        print(f"✓ 生成了 {len(scene_tags)} 个分镜")
    else:
        print("✗ 未找到分镜信息")

def main():
    """
    主函数
    """
    print("动态角色生成功能测试")
    print("=" * 50)
    
    success = test_dynamic_character_generation()
    
    print("\n=== 测试结果 ===")
    if success:
        print("✓ 动态角色生成功能测试通过")
        print("\n请查看生成的输出文件以验证角色是否正确识别和生成")
    else:
        print("✗ 动态角色生成功能测试失败")
    
    print("\n测试完成")

if __name__ == "__main__":
    main()