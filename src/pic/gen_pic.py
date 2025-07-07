#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
图片生成模块
使用配置化的prompt模板
"""

import os
import sys
import requests
import json
from typing import Optional

# 添加项目根目录到路径
project_root = os.path.dirname(os.path.dirname(os.path.dirname(__file__)))
sys.path.insert(0, project_root)

from config.prompt_config import prompt_config, ART_STYLES, validate_style

def generate_image_with_style(description: str, style: str = 'manga', 
                            output_path: Optional[str] = None, **kwargs) -> bool:
    """
    根据描述和风格生成图片
    
    Args:
        description: 图片描述
        style: 艺术风格，可选值见ART_STYLES
        output_path: 输出路径，如果为None则自动生成
        **kwargs: 其他参数
    
    Returns:
        bool: 是否生成成功
    """
    
    # 验证风格
    if not validate_style(style):
        print(f"错误：不支持的艺术风格 '{style}'")
        print(f"可用风格：{list(ART_STYLES.keys())}")
        return False
    
    try:
        # 使用配置管理器生成prompt
        prompt = prompt_config.get_pic_prompt(
            description=description,
            style=style,
            **kwargs
        )
        
        print(f"使用风格：{ART_STYLES[style]['name']}")
        print(f"生成的prompt：{prompt}")
        
        # 这里应该调用实际的图片生成API
        # 目前只是模拟
        print(f"正在生成图片...")
        
        # 模拟API调用
        # response = requests.post(api_url, json={"prompt": prompt})
        
        # 如果没有指定输出路径，自动生成
        if output_path is None:
            output_path = f"generated_image_{style}.png"
        
        print(f"图片已生成：{output_path}")
        return True
        
    except Exception as e:
        print(f"生成图片时出错：{e}")
        return False

def list_available_styles():
    """
    列出所有可用的艺术风格
    """
    print("可用的艺术风格：")
    for style_key, style_info in ART_STYLES.items():
        print(f"  {style_key}: {style_info['name']} - {style_info['description']}")

def main():
    """
    主函数，用于测试
    """
    print("图片生成模块测试")
    print("=" * 50)
    
    # 列出可用风格
    list_available_styles()
    print()
    
    # 测试生成图片
    test_description = "一个美丽的古代城市，有高耸的塔楼和繁华的街道"
    
    for style in ['manga', 'realistic', 'watercolor']:
        print(f"\n测试风格：{style}")
        print("-" * 30)
        generate_image_with_style(test_description, style)

if __name__ == "__main__":
    main()