#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
测试gen_image_async_v3.py的新参数功能
- response_format: b64_json
- watermark: false
"""

import os
import sys
import tempfile
import base64

# 添加项目根目录到路径
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from gen_image_async_v3 import ArkImageGenerator


def test_v3_new_params():
    """测试v3版本的新参数功能"""
    print("=== 测试gen_image_async_v3.py新参数功能 ===")
    
    try:
        # 创建临时目录
        with tempfile.TemporaryDirectory() as temp_dir:
            print(f"使用临时目录: {temp_dir}")
            
            # 创建图片生成器
            generator = ArkImageGenerator(temp_dir)
            
            # 测试prompt
            test_prompt = "画面风格是强调强烈线条、鲜明对比和现代感造型，色彩饱和，带有动态夸张与都市叙事视觉冲击力的国风漫画风格。一只可爱的小猫咪，坐在花园里，阳光明媚"
            
            # 输出路径
            output_path = os.path.join(temp_dir, "test_image_01.jpeg")
            
            print(f"测试Prompt: {test_prompt[:50]}...")
            print("正在生成图片（使用base64格式，无水印）...")
            
            # 调用我们修改的方法
            success = generator.generate_image_sync(test_prompt, output_path, 1)
            
            if success:
                print("✓ 图片生成成功")
                
                # 检查文件是否存在
                if os.path.exists(output_path):
                    print(f"✓ 图片文件已保存: {output_path}")
                    
                    # 检查文件大小
                    file_size = os.path.getsize(output_path)
                    print(f"✓ 文件大小: {file_size} bytes")
                    
                    # 验证是否为有效的JPEG文件
                    with open(output_path, 'rb') as f:
                        header = f.read(10)
                        if header.startswith(b'\xff\xd8\xff'):
                            print("✓ 文件格式验证: 有效的JPEG文件")
                        else:
                            print("✗ 文件格式验证: 不是有效的JPEG文件")
                            return False
                    
                    return True
                else:
                    print("✗ 图片文件未找到")
                    return False
            else:
                print("✗ 图片生成失败")
                return False
                
    except Exception as e:
        print(f"✗ 测试失败: {e}")
        import traceback
        traceback.print_exc()
        return False


def main():
    """主测试函数"""
    print("开始测试gen_image_async_v3.py的新参数功能")
    print("=" * 50)
    
    # 运行测试
    success = test_v3_new_params()
    
    print("\n" + "=" * 50)
    if success:
        print("✓ 所有测试通过")
    else:
        print("✗ 测试失败")
    
    return success


if __name__ == "__main__":
    main()