#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Prompt配置管理
用于管理所有模板的配置参数
"""

import os
from jinja2 import Environment, FileSystemLoader

# 模板目录
TEMPLATE_DIR = os.path.join(os.path.dirname(os.path.dirname(__file__)), 'templates')

# 初始化Jinja2环境
env = Environment(loader=FileSystemLoader(TEMPLATE_DIR))

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
        import json
        return json.loads(config_str)

# 艺术风格配置
ART_STYLES = {
    'manga': {
        'name': '漫画风格',
        'description': '动漫插画，精美细腻的画风，鲜艳的色彩，清晰的线条'
    },
    'realistic': {
        'name': '写实风格',
        'description': '真实感强，细节丰富，高清画质，专业摄影'
    },
    'watercolor': {
        'name': '水彩画风格',
        'description': '柔和的色彩，艺术感强，手绘质感，淡雅的色调'
    },
    'oil_painting': {
        'name': '油画风格',
        'description': '厚重的笔触，丰富的色彩层次，古典艺术感'
    },
    'chinese_ink': {
        'name': '中国水墨画风格',
        'description': '墨色浓淡变化，意境深远，传统国画技法'
    },
    'cyberpunk': {
        'name': '赛博朋克风格',
        'description': '霓虹灯光，未来科技感，暗色调，电子元素'
    }
}

# 语音配置预设
VOICE_PRESETS = {
    'default': {
        'speed_ratio': 1.2,
        'volume_ratio': 1.0,
        'pitch_ratio': 1.0,
        'sample_rate': 44100,
        'bitrate': 192000
    },
    'slow': {
        'speed_ratio': 0.9,
        'volume_ratio': 1.0,
        'pitch_ratio': 1.0,
        'sample_rate': 44100,
        'bitrate': 192000
    },
    'fast': {
        'speed_ratio': 1.5,
        'volume_ratio': 1.0,
        'pitch_ratio': 1.0,
        'sample_rate': 44100,
        'bitrate': 192000
    },
    'deep': {
        'speed_ratio': 1.0,
        'volume_ratio': 1.2,
        'pitch_ratio': 0.8,
        'sample_rate': 44100,
        'bitrate': 192000
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

def get_art_style_list():
    """
    获取所有可用的艺术风格列表
    
    Returns:
        list: 风格列表
    """
    return list(ART_STYLES.keys())

def get_voice_preset_list():
    """
    获取所有可用的语音预设列表
    
    Returns:
        list: 预设列表
    """
    return list(VOICE_PRESETS.keys())

def validate_style(style):
    """
    验证艺术风格是否有效
    
    Args:
        style: 风格名称
    
    Returns:
        bool: 是否有效
    """
    return style in ART_STYLES

def validate_voice_preset(preset):
    """
    验证语音预设是否有效
    
    Args:
        preset: 预设名称
    
    Returns:
        bool: 是否有效
    """
    return preset in VOICE_PRESETS