#!/usr/bin/env python3
# -*- coding: utf-8 -*-

import sys
import os
sys.path.append('../src')

from src.script.gen_script import ScriptGenerator

# 为了兼容性，创建函数别名
def split_chapters(text):
    generator = ScriptGenerator()
    return generator.split_chapters(text)

def save_chapters_to_folders(chapters, base_folder):
    generator = ScriptGenerator()
    return generator.save_chapters_to_folders(chapters, base_folder)

# 读取测试文件
with open('test_chapter.txt', 'r', encoding='utf-8') as f:
    content = f.read()

print("原始内容:")
print(content)
print("\n" + "="*50 + "\n")

# 分割章节
chapters = split_chapters(content)
print(f'找到 {len(chapters)} 个章节')

for i, (chapter_num, chapter_content) in enumerate(chapters):
    print(f"章节 {chapter_num}:")
    print(chapter_content[:100] + "..." if len(chapter_content) > 100 else chapter_content)
    print()

# 保存章节到文件夹
if chapters:
    save_chapters_to_folders(chapters, '.')
else:
    print("没有找到章节，无法保存")