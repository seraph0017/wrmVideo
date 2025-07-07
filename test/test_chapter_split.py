#!/usr/bin/env python3
# -*- coding: utf-8 -*-

import sys
import os
sys.path.append('src')

from gen_script import split_chapters, save_chapters_to_folders

def test_chapter_split():
    """
    测试章节分割功能
    """
    # 创建测试内容
    test_content = '''<解说文案>
<第1章节>
<解说内容>这是第一章的解说内容，讲述了主人公的背景故事。</解说内容>
<图片prompt>一个年轻人站在城市的街头，背景是繁华的都市夜景</图片prompt>

<解说内容>主人公走进了一家神秘的店铺。</解说内容>
<图片prompt>一家古老神秘的店铺，门口挂着奇怪的符号</图片prompt>
</第1章节>

<第2章节>
<解说内容>第二章开始，主人公遇到了一位神秘的老人。</解说内容>
<图片prompt>一位白发苍苍的老人，眼神深邃，手持古书</图片prompt>

<解说内容>老人告诉了主人公一个惊人的秘密。</解说内容>
<图片prompt>老人和年轻人面对面交谈，周围环境昏暗神秘</图片prompt>
</第2章节>

<第3章节>
<解说内容>第三章，主人公开始了他的冒险之旅。</解说内容>
<图片prompt>主人公背着行囊，走在崎岖的山路上</图片prompt>
</第3章节>
</解说文案>'''
    
    print("=== 测试章节分割功能 ===")
    print(f"测试内容长度: {len(test_content)}")
    print("\n测试内容前200字符:")
    print(test_content[:200])
    
    # 测试章节分割
    chapters = split_chapters(test_content)
    
    print(f"\n=== 分割结果 ===")
    print(f"找到 {len(chapters)} 个章节")
    
    for chapter_num, content in chapters:
        print(f"\n--- 章节 {chapter_num} ---")
        print(f"内容长度: {len(content)}")
        print(f"内容预览: {content[:100]}...")
    
    # 测试保存到文件夹
    if chapters:
        print("\n=== 测试保存到文件夹 ===")
        test_dir = "test_chapters"
        save_chapters_to_folders(chapters, test_dir)
        print(f"章节已保存到 {test_dir} 目录")
        
        # 检查生成的文件
        if os.path.exists(test_dir):
            print("\n生成的文件夹:")
            for item in os.listdir(test_dir):
                item_path = os.path.join(test_dir, item)
                if os.path.isdir(item_path):
                    print(f"  文件夹: {item}")
                    for file in os.listdir(item_path):
                        file_path = os.path.join(item_path, file)
                        if os.path.isfile(file_path):
                            with open(file_path, 'r', encoding='utf-8') as f:
                                content = f.read()
                            print(f"    文件: {file} (长度: {len(content)})")
    else:
        print("\n错误: 没有找到章节")

if __name__ == '__main__':
    test_chapter_split()