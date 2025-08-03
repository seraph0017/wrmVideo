#!/usr/bin/env python3
# -*- coding: utf-8 -*-

import sys
import os
import json
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from gen_ass import split_text_naturally, calculate_segment_timestamps

# 加载实际的timestamps数据
timestamps_file = '/Users/nathan/Projects/wrmVideo/data/005/chapter_001/chapter_001_narration_01_timestamps.json'

with open(timestamps_file, 'r', encoding='utf-8') as f:
    data = json.load(f)

original_text = data['text']
character_timestamps = data['character_timestamps']

print("原始文本:")
print(original_text)
print(f"\n字符时间戳数量: {len(character_timestamps)}")
print(f"原始文本长度: {len(original_text)}")

# 测试分割
print("\n=== 文本分割测试 ===")
segments = split_text_naturally(original_text, max_length=12)
for i, segment in enumerate(segments, 1):
    print(f"{i}. {segment}")

print(f"\n总共分割为 {len(segments)} 段")

# 测试时间戳计算
print("\n=== 时间戳计算测试 ===")

# 重定向标准输出以捕获警告信息
import io
import sys
old_stdout = sys.stdout
sys.stdout = captured_output = io.StringIO()

segment_timestamps = calculate_segment_timestamps(segments, character_timestamps, original_text)

# 恢复标准输出并获取捕获的内容
sys.stdout = old_stdout
captured_warnings = captured_output.getvalue()

print(f"成功计算时间戳的段落数: {len(segment_timestamps)}")
if captured_warnings:
    print("警告信息:")
    print(captured_warnings)

for i, segment_data in enumerate(segment_timestamps, 1):
    print(f"{i}. {segment_data['text']} ({segment_data['start_time']:.2f}s - {segment_data['end_time']:.2f}s)")

# 检查是否包含完整的引号内容
print("\n=== 引号内容检查 ===")
for i, segment_data in enumerate(segment_timestamps, 1):
    text = segment_data['text']
    if "这般气象" in text or "我以后" in text or "看不到" in text:
        print(f"段落 {i} 包含引号相关内容: {text} ({segment_data['start_time']:.2f}s - {segment_data['end_time']:.2f}s)")

# 检查最后几个字符的时间戳
print("\n=== 最后几个字符的时间戳 ===")
for i in range(max(0, len(character_timestamps)-10), len(character_timestamps)):
    char_data = character_timestamps[i]
    print(f"字符 '{char_data['character']}': {char_data['start_time']:.3f}s - {char_data['end_time']:.3f}s")