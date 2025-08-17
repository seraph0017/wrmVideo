#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
测试优化后的领口审查prompt

该脚本用于测试新的prompt是否能正确识别交领等问题领口类型
"""

import sys
import os
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from llm_image import encode_image_to_base64, analyze_image_with_llm
from volcenginesdkarkruntime import Ark
from config.config import ARK_CONFIG

def test_prompt_with_image(image_path: str):
    """
    测试指定图片的领口审查效果
    
    Args:
        image_path: 图片路径
    """
    # 获取API密钥
    api_key = ARK_CONFIG.get("api_key")
    if not api_key:
        print("错误: 请在 config/config.py 中配置 ARK_CONFIG['api_key']")
        return
    
    # 初始化客户端
    client = Ark(api_key=api_key)
    
    # 编码图片
    print(f"正在分析图片: {image_path}")
    image_base64 = encode_image_to_base64(image_path)
    if not image_base64:
        print("错误: 图片编码失败")
        return
    
    # 使用新的prompt进行分析
    result, token_info = analyze_image_with_llm(client, image_base64)
    
    print("=" * 80)
    print("分析结果:")
    print(result)
    print("=" * 80)
    print(f"Token使用: 输入={token_info['prompt_tokens']}, 输出={token_info['completion_tokens']}, 总计={token_info['total_tokens']}")
    
    # 判断是否正确识别了问题
    if result and "失败" in result:
        if "交领" in result or "衽领" in result or "V领" in result:
            print("✅ 成功识别出领口问题!")
        else:
            print("⚠️  识别为失败但原因可能不准确")
    elif result and "通过" in result:
        print("❌ 未能识别出领口问题")
    else:
        print("❓ 分析结果不明确")

def main():
    """
    主函数
    """
    if len(sys.argv) != 2:
        print("用法: python test_optimized_prompt.py <图片路径>")
        print("示例: python test_optimized_prompt.py /path/to/test_image.jpg")
        return
    
    image_path = sys.argv[1]
    
    if not os.path.exists(image_path):
        print(f"错误: 图片文件不存在: {image_path}")
        return
    
    test_prompt_with_image(image_path)

if __name__ == "__main__":
    main()