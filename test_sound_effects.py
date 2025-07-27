#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
测试音效匹配系统
"""

import os
import sys

# 添加src目录到路径
sys.path.append(os.path.join(os.path.dirname(os.path.abspath(__file__)), 'src'))
from sound_effects_processor import SoundEffectsProcessor

def get_sound_effects_dir():
    """获取音效目录，优先使用 src/sound_effects，找不到时使用 sound"""
    base_dir = os.path.dirname(os.path.abspath(__file__))
    
    # 优先使用 src/sound_effects 目录
    primary_dir = os.path.join(base_dir, "src", "sound_effects")
    if os.path.exists(primary_dir):
        print(f"使用优先音效目录: {primary_dir}")
        return primary_dir
    
    # 备用目录 sound
    fallback_dir = os.path.join(base_dir, "sound")
    if os.path.exists(fallback_dir):
        print(f"使用备用音效目录: {fallback_dir}")
        return fallback_dir
    
    print("警告: 未找到任何音效目录")
    return None

def test_sound_effects_matching():
    """测试音效匹配功能"""
    
    # 初始化音效处理器
    sound_dir = get_sound_effects_dir()
    if not sound_dir:
        print("错误: 无法找到音效目录")
        return
    
    processor = SoundEffectsProcessor(sound_dir)
    
    print(f"音效目录: {sound_dir}")
    print(f"加载的音效文件数量: {len(processor.sound_effects_map)}")
    
    # 显示前10个音效文件
    print("\n前10个音效文件:")
    for i, (key, path) in enumerate(list(processor.sound_effects_map.items())[:10]):
        print(f"  {i+1}. {key} -> {os.path.basename(path)}")
    
    # 测试对话匹配
    test_dialogues = [
        {
            'start_seconds': 1.0,
            'end_seconds': 3.0,
            'text': '突然听到一声狗叫'
        },
        {
            'start_seconds': 5.0,
            'end_seconds': 7.0,
            'text': '汽车发动机的声音响起'
        },
        {
            'start_seconds': 10.0,
            'end_seconds': 12.0,
            'text': '门被打开了'
        },
        {
            'start_seconds': 15.0,
            'end_seconds': 17.0,
            'text': '雷声轰鸣'
        },
        {
            'start_seconds': 20.0,
            'end_seconds': 22.0,
            'text': '鸟儿在歌唱'
        }
    ]
    
    print("\n测试对话匹配:")
    sound_events = processor.match_sound_effects(test_dialogues)
    
    print(f"\n匹配结果: 找到 {len(sound_events)} 个音效事件")
    for event in sound_events:
        print(f"  时间: {event['start_time']:.1f}s, 关键词: {event['keyword']}, 文件: {os.path.basename(event['sound_file'])}")

if __name__ == "__main__":
    test_sound_effects_matching()