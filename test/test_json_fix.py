#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
测试JSON修复是否有效
"""

import sys
import os
import json

# 添加项目根目录到Python路径
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from config.prompt_config import PromptConfig

def test_json_fix():
    """测试JSON修复"""
    
    # 创建配置管理器
    config = PromptConfig()
    
    # 测试包含双引号的文本
    test_text = '''"太子殿下！陛下请您进宫！"一声沉稳喝问打破寂静，四周甲士如潮水般涌出，瞬间将李承乾团团围住！'''
    
    print(f"测试文本: {test_text}")
    print(f"文本长度: {len(test_text)}")
    
    # 创建模拟的 TTS 配置
    mock_tts_config = {
        "appid": "test_appid",
        "access_token": "test_token",
        "cluster": "volcano_tts"
    }
    
    try:
        # 生成语音配置
        voice_config = config.get_voice_config(
            text=test_text,
            request_id="test_123",
            tts_config=mock_tts_config,
            voice_type="BV701_streaming"
        )
        
        print("\n✓ JSON配置生成成功！")
        print(f"配置类型: {type(voice_config)}")
        
        if isinstance(voice_config, dict):
            print(f"配置包含的键: {list(voice_config.keys())}")
            if 'request' in voice_config and 'text' in voice_config['request']:
                print(f"文本字段: {voice_config['request']['text'][:100]}...")
        
        return True
        
    except Exception as e:
        print(f"\n✗ JSON配置生成失败: {e}")
        return False

if __name__ == "__main__":
    success = test_json_fix()
    if success:
        print("\n🎉 JSON修复测试通过！")
    else:
        print("\n❌ JSON修复测试失败！")
        sys.exit(1)