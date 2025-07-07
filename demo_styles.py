#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
艺术风格演示脚本
展示不同艺术风格的图片生成效果
"""

import os
import sys

# 添加src目录到路径
sys.path.append(os.path.join(os.path.dirname(__file__), 'src'))

from generate import generate_image, ART_STYLES

def demo_all_styles():
    """
    演示所有艺术风格
    """
    # 演示用的prompt
    demo_prompt = "一个美丽的古代女子站在樱花树下，穿着华丽的汉服，微风吹动她的长发，背景是古典的亭台楼阁"
    
    # 确保输出目录存在
    output_dir = "data/demo_styles"
    os.makedirs(output_dir, exist_ok=True)
    
    print("=== 艺术风格演示 ===")
    print(f"演示prompt: {demo_prompt}")
    print("\n开始生成不同风格的图片...\n")
    
    # 为每种风格生成图片
    for style_name, style_desc in ART_STYLES.items():
        print(f"正在生成 {style_name} 风格...")
        output_path = os.path.join(output_dir, f"demo_{style_name}.jpg")
        
        success = generate_image(demo_prompt, output_path, style=style_name)
        
        if success:
            print(f"✅ {style_name} 风格生成成功: {output_path}")
        else:
            print(f"❌ {style_name} 风格生成失败")
        
        print("-" * 50)
    
    print("\n=== 演示完成 ===")
    print(f"所有图片已保存到: {output_dir}")
    print("\n风格说明:")
    for style_name, style_desc in ART_STYLES.items():
        print(f"- {style_name}: {style_desc.strip()}")

if __name__ == "__main__":
    demo_all_styles()