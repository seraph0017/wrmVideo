#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
语音生成模块
使用配置化的TTS参数
"""

import os
import sys
import requests
import json
import uuid
from typing import Optional, Dict, Any

# 添加项目根目录到路径
project_root = os.path.dirname(os.path.dirname(os.path.dirname(__file__)))
sys.path.insert(0, project_root)

from config.prompt_config import prompt_config, VOICE_PRESETS, validate_voice_preset

# TTS配置
TTS_CONFIG = {
    "appid": "6359073393",
    "cluster": "volcano_tts",
    "voice_type": "BV700_streaming"
}

class VoiceGenerator:
    """
    语音生成器类
    """
    
    def __init__(self, tts_config: Optional[Dict] = None):
        """
        初始化语音生成器
        
        Args:
            tts_config: TTS配置，如果为None则使用默认配置
        """
        self.tts_config = tts_config or TTS_CONFIG
        self.api_url = "https://openspeech.bytedance.com/api/v1/tts"
    
    def generate_voice(self, text: str, output_path: str, 
                      preset: str = 'default', **kwargs) -> bool:
        """
        生成语音文件
        
        Args:
            text: 要转换的文本
            output_path: 输出文件路径
            preset: 语音预设，可选值见VOICE_PRESETS
            **kwargs: 其他参数
        
        Returns:
            bool: 是否生成成功
        """
        
        # 验证预设
        if not validate_voice_preset(preset):
            print(f"错误：不支持的语音预设 '{preset}'")
            print(f"可用预设：{list(VOICE_PRESETS.keys())}")
            return False
        
        try:
            # 生成请求ID
            request_id = str(uuid.uuid4())
            
            # 获取预设参数
            preset_params = VOICE_PRESETS[preset].copy()
            preset_params.update(kwargs)  # 允许覆盖预设参数
            
            # 使用配置管理器生成请求配置
            request_config = prompt_config.get_voice_config(
                text=text,
                request_id=request_id,
                tts_config=self.tts_config,
                **preset_params
            )
            
            print(f"使用语音预设：{preset}")
            print(f"请求ID：{request_id}")
            print(f"文本长度：{len(text)} 字符")
            
            # 发送请求
            headers = {
                'Authorization': f'Bearer; {self.tts_config["appid"]}',
                'Content-Type': 'application/json'
            }
            
            print("正在生成语音...")
            response = requests.post(
                self.api_url,
                headers=headers,
                json=request_config,
                timeout=30
            )
            
            if response.status_code == 200:
                # 保存音频文件
                os.makedirs(os.path.dirname(output_path), exist_ok=True)
                with open(output_path, 'wb') as f:
                    f.write(response.content)
                
                print(f"语音文件已生成：{output_path}")
                return True
            else:
                print(f"API请求失败，状态码：{response.status_code}")
                print(f"响应内容：{response.text}")
                return False
                
        except Exception as e:
            print(f"生成语音时出错：{e}")
            return False
    
    def generate_voice_batch(self, text_list: list, output_dir: str, 
                           preset: str = 'default', **kwargs) -> Dict[str, bool]:
        """
        批量生成语音文件
        
        Args:
            text_list: 文本列表
            output_dir: 输出目录
            preset: 语音预设
            **kwargs: 其他参数
        
        Returns:
            Dict[str, bool]: 每个文件的生成结果
        """
        results = {}
        
        for i, text in enumerate(text_list):
            output_path = os.path.join(output_dir, f"voice_{i+1:03d}.mp3")
            success = self.generate_voice(text, output_path, preset, **kwargs)
            results[output_path] = success
            
            if success:
                print(f"✓ 第 {i+1}/{len(text_list)} 个语音文件生成成功")
            else:
                print(f"✗ 第 {i+1}/{len(text_list)} 个语音文件生成失败")
        
        return results

def list_available_presets():
    """
    列出所有可用的语音预设
    """
    print("可用的语音预设：")
    for preset_key, preset_config in VOICE_PRESETS.items():
        print(f"  {preset_key}:")
        for param, value in preset_config.items():
            print(f"    {param}: {value}")
        print()

def main():
    """
    主函数，用于测试
    """
    print("语音生成模块测试")
    print("=" * 50)
    
    # 列出可用预设
    list_available_presets()
    
    # 创建语音生成器
    generator = VoiceGenerator()
    
    # 测试文本
    test_text = "这是一个测试文本，用于验证语音生成功能是否正常工作。"
    
    # 测试不同预设
    for preset in ['default', 'slow', 'fast']:
        print(f"\n测试预设：{preset}")
        print("-" * 30)
        output_path = f"test_voice_{preset}.mp3"
        generator.generate_voice(test_text, output_path, preset)

if __name__ == "__main__":
    main()