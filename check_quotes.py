#!/usr/bin/env python3
# -*- coding: utf-8 -*-

import glob

# 检查原始ASS文件
files = glob.glob('/Users/nathan/Projects/wrmVideo/data/005/chapter_001/chapter_001_narration_*.ass')
quotes_found = set()

for file in files[:3]:  # 只检查前3个文件
    print(f'检查文件: {file}')
    with open(file, 'r', encoding='utf-8') as f:
        content = f.read()
        for char in content:
            if char in '""''"':
                quotes_found.add(char)

print(f'\n在原始ASS文件中找到的引号类型: {quotes_found}')
print(f'引号总数: {len(quotes_found)}')

# 显示每种引号的Unicode编码
for quote in quotes_found:
    print(f'引号 "{quote}" 的Unicode编码: U+{ord(quote):04X}')

# 也检查合并后的文件
print('\n检查合并后的文件:')
with open('/Users/nathan/Projects/wrmVideo/data/005/chapter_001/temp_videos/merged_subtitles.ass', 'r', encoding='utf-8') as f:
    content = f.read()
    merged_quotes = set()
    for char in content:
        if char in '""''"':
            merged_quotes.add(char)
    print(f'合并文件中的引号: {merged_quotes}')