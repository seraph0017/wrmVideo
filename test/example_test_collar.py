#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
领口审查示例测试

展示如何使用优化后的prompt测试图片领口
"""

import sys
import os
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

def run_collar_test_example():
    """
    运行领口审查测试示例
    """
    print("=" * 80)
    print("🔍 图片领口审查测试示例")
    print("=" * 80)
    print()
    
    print("📋 使用方法:")
    print("1. 单张图片测试:")
    print("   python test/test_optimized_prompt.py /path/to/image.jpg")
    print()
    
    print("2. 批量目录测试:")
    print("   python llm_image.py data/004 --auto-regenerate")
    print()
    
    print("3. 自定义prompt测试:")
    print("   python llm_image.py data/004 --prompt \"自定义审查提示词\"")
    print()
    
    print("🎯 优化后的prompt特点:")
    print("✅ 明确定义通过的领口类型: 圆领、立领、高领、方领、一字领")
    print("❌ 重点识别失败的领口类型:")
    print("   - 交领/衽领: 左右衣襟交叉重叠，形成V字形开口")
    print("   - V领: 任何形式的V字形领口")
    print("   - 低领: 领口过低，露出脖子以下皮肤")
    print("   - 开胸装: 胸前有明显开口或缝隙")
    print()
    
    print("🔍 特别关注:")
    print("- 传统汉服、古装的交领设计")
    print("- 是否露出脖子以下皮肤区域")
    print("- 图片中的文字、乱码、水印等内容")
    print()
    
    print("📊 测试结果判断:")
    print("✅ 成功: 正确识别出交领等问题并返回'失败'")
    print("❌ 失败: 未能识别问题或错误返回'通过'")
    print("⚠️  注意: 关注失败原因的准确性")
    print()
    
    print("🚀 自动重新生成功能:")
    print("使用 --auto-regenerate 参数可在检测到失败图片时自动调用图片生成模块重新生成")
    print()
    
    print("=" * 80)
    print("💡 提示: 请确保已在 config/config.py 中配置 ARK_CONFIG['api_key']")
    print("=" * 80)

if __name__ == "__main__":
    run_collar_test_example()