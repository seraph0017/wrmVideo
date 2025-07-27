#!/usr/bin/env python3
# -*- coding: utf-8 -*-

import json

# 加载数据
with open('data/005/chapter_001/chapter_001_narration_01_timestamps.json', 'r', encoding='utf-8') as f:
    data = json.load(f)

original_text = data['text']
character_timestamps = data['character_timestamps']

print(f"原文长度: {len(original_text)}")
print(f"字符时间戳数量: {len(character_timestamps)}")
print(f"原文最后10个字符: '{original_text[-10:]}'")
print(f"最后几个时间戳:")
for i in range(max(0, len(character_timestamps)-5), len(character_timestamps)):
    char_info = character_timestamps[i]
    print(f"  索引 {i}: '{char_info['character']}' ({char_info['start_time']:.3f}s - {char_info['end_time']:.3f}s)")

# 检查索引140是否存在
if len(character_timestamps) > 140:
    char_140 = character_timestamps[140]
    print(f"\n索引140: '{char_140['character']}' ({char_140['start_time']:.3f}s - {char_140['end_time']:.3f}s)")
else:
    print(f"\n索引140不存在，最大索引是 {len(character_timestamps)-1}")

# 检查原文中位置140的字符
if len(original_text) > 140:
    print(f"原文位置140的字符: '{original_text[140]}'")
else:
    print(f"原文位置140不存在，原文长度是 {len(original_text)}")