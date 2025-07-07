#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
测试优化后的功能：
1. 智能断句（按语气词断句）
2. 多个音频共用一张图片
3. 黑色粗体字幕
"""

import sys
import os

# 添加项目根目录到Python路径
project_root = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.append(project_root)

# 切换到项目根目录
os.chdir(project_root)

from generate import smart_split_text, parse_chapter_script, create_video_with_subtitle

def test_smart_split():
    """
    测试智能断句功能
    """
    print("=== 测试智能断句功能 ===")
    
    # 测试文本
    test_texts = [
        "这是一个很长的句子，包含了多个语气词呢，我们来看看它会怎么断句吧！",
        "主人公走进了神秘的森林，那里有很多奇怪的声音啊，让人感到害怕。",
        "老人告诉他一个秘密：这个世界并不是真实的，而是一个巨大的虚拟现实系统。",
        "短句测试"
    ]
    
    for i, text in enumerate(test_texts, 1):
        print(f"\n测试文本 {i}: {text}")
        print(f"原文长度: {len(text)} 字符")
        
        segments = smart_split_text(text, max_length=50)
        print(f"断句结果 ({len(segments)} 个部分):")
        
        for j, segment in enumerate(segments, 1):
            print(f"  部分 {j}: {segment} (长度: {len(segment)})")

def test_script_parsing():
    """
    测试脚本解析功能
    """
    print("\n\n=== 测试脚本解析功能 ===")
    
    # 创建测试脚本文件
    test_script_content = """<第1章节>
<解说内容>这是第一段解说，讲述了故事的开始。</解说内容>
<解说内容>紧接着第二段解说，继续描述情节发展。</解说内容>
<图片prompt>美丽的森林场景，阳光透过树叶</图片prompt>
<解说内容>第三段解说，描述主人公的心情变化。</解说内容>
<解说内容>第四段解说，引出新的角色登场。</解说内容>
<图片prompt>神秘的老人，手持古老的书籍</图片prompt>
</第1章节>"""
    
    # 写入测试文件
    test_script_path = "test_script_parsing.txt"
    with open(test_script_path, 'w', encoding='utf-8') as f:
        f.write(test_script_content)
    
    print(f"创建测试脚本文件: {test_script_path}")
    
    # 解析脚本
    segments = parse_chapter_script(test_script_path)
    
    print(f"\n解析结果 ({len(segments)} 个段落组):")
    for i, (narrations, prompt) in enumerate(segments, 1):
        print(f"\n段落组 {i}:")
        print(f"  图片prompt: {prompt}")
        print(f"  解说内容 ({len(narrations)} 个):")
        for j, narration in enumerate(narrations, 1):
            print(f"    {j}. {narration}")
    
    # 清理测试文件
    os.remove(test_script_path)
    print(f"\n已清理测试文件: {test_script_path}")

def test_subtitle_style():
    """
    测试新的字幕样式（黑色粗体）
    """
    print("\n\n=== 测试字幕样式 ===")
    
    # 检查是否有测试文件
    test_image = "test/test_chapters/chapter02/chapter02_segment_01.jpg"
    test_audio = "test/test_chapters/chapter02/chapter02_segment_02.mp3"
    
    if os.path.exists(test_image) and os.path.exists(test_audio):
        output_video = "test_black_bold_subtitle.mp4"
        test_subtitle = "这是黑色粗体字幕测试，带有白色描边效果。"
        
        print(f"使用图片: {test_image}")
        print(f"使用音频: {test_audio}")
        print(f"字幕文本: {test_subtitle}")
        print(f"输出视频: {output_video}")
        
        if create_video_with_subtitle(test_image, test_audio, test_subtitle, output_video):
            print("✅ 黑色粗体字幕视频生成成功！")
            print(f"请查看生成的视频文件: {output_video}")
            print("字幕应该是黑色粗体，带有白色描边")
        else:
            print("❌ 字幕视频生成失败")
    else:
        print("⚠️  测试文件不存在，跳过字幕样式测试")
        print(f"需要的文件: {test_image}, {test_audio}")

def main():
    """
    主测试函数
    """
    print("开始测试优化后的功能...\n")
    
    # 测试智能断句
    test_smart_split()
    
    # 测试脚本解析
    test_script_parsing()
    
    # 测试字幕样式
    test_subtitle_style()
    
    print("\n=== 所有测试完成 ===")

if __name__ == "__main__":
    main()