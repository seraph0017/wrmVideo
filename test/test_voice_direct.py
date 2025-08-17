#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
直接测试VoiceGenerator的JSON解析
"""

import sys
import os

# 添加项目根目录到Python路径
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from src.voice.gen_voice import VoiceGenerator
from config.config import TTS_CONFIG

def test_voice_generator():
    """直接测试VoiceGenerator"""
    
    # 创建语音生成器
    voice_gen = VoiceGenerator(TTS_CONFIG)
    
    # 测试文本 - 使用实际的解说内容
    test_text = '''"太子殿下！陛下请您进宫！"一声沉稳喝问打破寂静，四周甲士如潮水般涌出，瞬间将李承乾团团围住！为首将领身高八尺，铁甲威风凛凛，手中铁槊寒光慑人——竟是有"单鞭挣定李乾坤"之称的程知节！李承乾眯眼冷笑，李世民竟派这位铁杆心腹来"请"他，倒是给足了排面。"孤乃大唐太子李承乾！你见了本宫安敢不拜！"他声音陡然拔高，往日的怯懦荡然无存。程知节脸上闪过诧异，刚要发怒，却被李承乾眼中的决绝震慑。"你若不拜，就杀了孤，把尸体抬进太极殿！"锵然一声，李承乾拔剑直指程知节鼻尖，剑锋映着晨光，亮得刺眼。程知节神色变幻，最终还是不情愿地躬身："臣程知节，奉陛下旨，请太子殿下进宫！"'''
    
    print(f"测试文本: {test_text}")
    print(f"文本长度: {len(test_text)}")
    
    # 生成语音（带时间戳）
    output_path = "/tmp/test_voice.mp3"
    
    print(f"\n=== 开始生成语音 ===")
    result = voice_gen.generate_voice_with_timestamps(
        text=test_text,
        output_path=output_path,
        preset='default'
    )
    
    print(f"\n=== 生成结果 ===")
    print(f"成功: {result.get('success', False)}")
    if result.get('error_message'):
        print(f"错误: {result['error_message']}")
    if result.get('timestamps'):
        print(f"时间戳数量: {len(result['timestamps'])}")
        print(f"前3个时间戳: {result['timestamps'][:3]}")

if __name__ == "__main__":
    test_voice_generator()