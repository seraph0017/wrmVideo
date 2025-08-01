#!/usr/bin/env python3
# -*- coding: utf-8 -*-

import sys
import os
sys.path.append('src')

from sound_effects_processor import SoundEffectsProcessor

# 测试音效处理
processor = SoundEffectsProcessor('src/sound_effects')

# 解析ASS文件
ass_file = 'data/003/chapter_002/temp_videos/merged_subtitles.ass'
if not os.path.exists(ass_file):
    print(f"ASS文件不存在: {ass_file}")
    sys.exit(1)

dialogues = processor.parse_ass_file(ass_file)
print(f"解析到 {len(dialogues)} 条对话")

# 显示前3条对话
print("\n前3条对话:")
for i, dialogue in enumerate(dialogues[:3]):
    print(f"对话 {i+1}: {dialogue['start_time']}s-{dialogue['end_time']}s")
    print(f"  内容: {dialogue['text'][:50]}...")
    print(f"  数据类型: start_time={type(dialogue['start_time'])}, end_time={type(dialogue['end_time'])}")
    print(f"  完整数据: {dialogue}")
    print()

# 匹配音效
print("\n开始匹配音效...")
sound_events = processor.match_sound_effects(dialogues)
print(f"匹配到 {len(sound_events)} 个音效事件")

# 显示所有音效事件
print("\n所有音效事件:")
for i, event in enumerate(sound_events):
    print(f"音效 {i+1}: {event['keyword']} 在 {event['start_time']:.2f}s, 音量 {event['volume']:.2f}")
    print(f"  文件: {os.path.basename(event['sound_file'])}")

# 过滤重叠音效
print("\n开始过滤重叠音效...")
filtered_events = processor.filter_overlapping_effects(sound_events)
print(f"过滤后剩余 {len(filtered_events)} 个音效事件")

# 显示过滤后的音效事件
print("\n过滤后的音效事件:")
for i, event in enumerate(filtered_events):
    print(f"过滤后音效 {i+1}: {event['keyword']} 在 {event['start_time']:.2f}s-{event['end_time']:.2f}s, 音量 {event['volume']:.2f}")
    print(f"  文件: {os.path.basename(event['sound_file'])}")

print(f"\n音效过滤统计:")
print(f"原始音效数量: {len(sound_events)}")
print(f"过滤后数量: {len(filtered_events)}")
print(f"过滤掉数量: {len(sound_events) - len(filtered_events)}")

# 统计重复音效文件
file_count = {}
for event in sound_events:
    filename = os.path.basename(event['sound_file'])
    file_count[filename] = file_count.get(filename, 0) + 1

print("\n重复使用的音效文件:")
for filename, count in file_count.items():
    if count > 1:
        print(f"  {filename}: {count} 次")