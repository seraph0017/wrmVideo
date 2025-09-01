#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Prompt配置管理
用于管理所有模板的配置参数
"""

import os
from jinja2 import Environment, FileSystemLoader

# 模板目录 - 现在分散在各个模块目录中
SRC_DIR = os.path.join(os.path.dirname(os.path.dirname(__file__)), 'src')
PIC_TEMPLATE_DIR = os.path.join(SRC_DIR, 'pic')
SCRIPT_TEMPLATE_DIR = os.path.join(SRC_DIR, 'script')
VOICE_TEMPLATE_DIR = os.path.join(SRC_DIR, 'voice')

# 初始化Jinja2环境 - 支持多个模板目录
env = Environment(loader=FileSystemLoader([PIC_TEMPLATE_DIR, SCRIPT_TEMPLATE_DIR, VOICE_TEMPLATE_DIR]))

class PromptConfig:
    """
    Prompt配置管理类
    """
    
    def __init__(self):
        self.env = env
    
    def get_pic_prompt(self, description, style='manga', **kwargs):
        """
        获取图片生成prompt
        
        Args:
            description: 图片描述
            style: 艺术风格
            **kwargs: 其他参数
        
        Returns:
            str: 生成的prompt
        """
        template = self.env.get_template('pic_generation.j2')
        return template.render(
            description=description,
            style=style,
            **kwargs
        )
    
    def get_script_prompt(self, content, is_chunk=False, **kwargs):
        """
        获取脚本生成prompt
        
        Args:
            content: 小说内容
            is_chunk: 是否为片段处理
            **kwargs: 其他参数
        
        Returns:
            str: 生成的prompt
        """
        template = self.env.get_template('script_generation.j2')
        return template.render(
            content=content,
            is_chunk=is_chunk,
            **kwargs
        )
    
    def get_voice_config(self, text, request_id, tts_config, **kwargs):
        """
        获取语音生成配置
        
        Args:
            text: 要转换的文本
            request_id: 请求ID
            tts_config: TTS配置
            **kwargs: 其他参数
        
        Returns:
            dict: 生成的配置
        """
        template = self.env.get_template('voice_config.j2')
        config_str = template.render(
            text=text,
            request_id=request_id,
            tts_config=tts_config,
            **kwargs
        )
        
        print(f"\n=== 语音配置模板渲染结果 ===")
        print(f"配置字符串长度: {len(config_str)}")
        print(f"配置字符串前500字符: {config_str[:500]}...")
        print(f"=== 模板渲染结果结束 ===\n")
        
        import json
        try:
            return json.loads(config_str)
        except json.JSONDecodeError as e:
            print(f"\n=== 语音配置JSON解析失败 ===")
            print(f"JSON解析错误: {e}")
            print(f"错误位置: line {e.lineno}, column {e.colno}, char {e.pos}")
            print(f"完整配置字符串:\n{config_str}")
            print(f"=== JSON解析失败信息结束 ===\n")
            raise

# 艺术风格配置已移除，简化提示词生成逻辑

# 语音配置预设
VOICE_PRESETS = {
    'default': {
        'speed_ratio': 1.0,
        'volume_ratio': 1.0,
        'pitch_ratio': 1.0,
        'sample_rate': 44100,
        'bitrate': 192000,
        'voice_type': 'BV701_streaming'
    },
    'slow': {
        'speed_ratio': 0.9,
        'volume_ratio': 1.0,
        'pitch_ratio': 1.0,
        'sample_rate': 44100,
        'bitrate': 192000,
        'voice_type': 'BV701_streaming'
    },
    'fast': {
        'speed_ratio': 1.5,
        'volume_ratio': 1.0,
        'pitch_ratio': 1.0,
        'sample_rate': 44100,
        'bitrate': 192000,
        'voice_type': 'BV701_streaming'
    },
    'deep': {
        'speed_ratio': 1.0,
        'volume_ratio': 1.2,
        'pitch_ratio': 0.8,
        'sample_rate': 44100,
        'bitrate': 192000,
        'voice_type': 'BV701_streaming'
    }
}

# 脚本生成配置
SCRIPT_CONFIG = {
    'max_chapters': 60,
    'chunk_size': 80000,
    'max_chunk_size': 100000,
    'target_duration_minutes': 4,
    'enable_thinking': False  # 是否启用深度思考
}

# 全局配置实例
prompt_config = PromptConfig()

# 艺术风格相关函数已移除

def get_voice_preset_list():
    """
    获取所有可用的语音预设列表
    
    Returns:
        list: 预设列表
    """
    return list(VOICE_PRESETS.keys())



def validate_voice_preset(preset):
    """
    验证语音预设是否有效
    
    Args:
        preset: 预设名称
    
    Returns:
        bool: 是否有效
    """
    return preset in VOICE_PRESETS