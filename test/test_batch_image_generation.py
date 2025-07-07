#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
测试批量图片生成功能
"""

import os
import sys
import tempfile
import shutil

# 添加项目根目录到Python路径
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from generate import generate_images_batch, generate_image

def test_batch_image_generation():
    """
    测试批量图片生成功能
    """
    print("=== 测试批量图片生成功能 ===")
    
    # 创建临时测试目录
    test_dir = "test_batch_images"
    os.makedirs(test_dir, exist_ok=True)
    
    try:
        # 准备测试数据：多个图片prompt和输出路径
        test_prompts_and_paths = [
            (
                "一个古代的书房，书桌上放着毛笔和墨水，窗外是竹林",
                os.path.join(test_dir, "image_1_古代书房.jpg")
            ),
            (
                "现代都市的咖啡厅，阳光透过玻璃窗洒在桌子上",
                os.path.join(test_dir, "image_2_现代咖啡厅.jpg")
            ),
            (
                "夜晚的海边，月亮倒映在平静的海面上，远处有灯塔",
                os.path.join(test_dir, "image_3_夜晚海边.jpg")
            )
        ]
        
        print(f"准备批量生成{len(test_prompts_and_paths)}张测试图片...")
        
        # 显示每个图片的prompt
        for i, (prompt, path) in enumerate(test_prompts_and_paths, 1):
            print(f"图片{i}: {prompt}")
            print(f"  输出路径: {os.path.basename(path)}")
        
        print("\n开始批量生成...")
        
        # 测试批量生成功能
        successful_paths = generate_images_batch(test_prompts_and_paths)
        
        print(f"\n批量生成结果:")
        print(f"成功生成: {len(successful_paths)}/{len(test_prompts_and_paths)} 张图片")
        
        # 验证生成的图片文件
        for i, (prompt, expected_path) in enumerate(test_prompts_and_paths, 1):
            if expected_path in successful_paths and os.path.exists(expected_path):
                file_size = os.path.getsize(expected_path)
                print(f"✓ 图片{i} 生成成功: {os.path.basename(expected_path)} ({file_size} bytes)")
            else:
                print(f"✗ 图片{i} 生成失败: {os.path.basename(expected_path)}")
        
        # 对比测试：单独生成同样的图片
        print("\n=== 对比测试：单独生成模式 ===")
        
        single_test_prompts_and_paths = [
            (
                "一个古代的书房，书桌上放着毛笔和墨水，窗外是竹林",
                os.path.join(test_dir, "single_image_1_古代书房.jpg")
            ),
            (
                "现代都市的咖啡厅，阳光透过玻璃窗洒在桌子上",
                os.path.join(test_dir, "single_image_2_现代咖啡厅.jpg")
            )
        ]
        
        single_successful = 0
        for prompt, path in single_test_prompts_and_paths:
            if generate_image(prompt, path):
                single_successful += 1
                file_size = os.path.getsize(path)
                print(f"✓ 单独生成成功: {os.path.basename(path)} ({file_size} bytes)")
            else:
                print(f"✗ 单独生成失败: {os.path.basename(path)}")
        
        print(f"\n单独生成结果: {single_successful}/{len(single_test_prompts_and_paths)} 张图片")
        
        # 总结
        print("\n=== 测试总结 ===")
        print(f"批量生成成功率: {len(successful_paths)}/{len(test_prompts_and_paths)} = {len(successful_paths)/len(test_prompts_and_paths)*100:.1f}%")
        print(f"单独生成成功率: {single_successful}/{len(single_test_prompts_and_paths)} = {single_successful/len(single_test_prompts_and_paths)*100:.1f}%")
        
        if len(successful_paths) > 0:
            print("\n✓ 批量图片生成功能测试通过")
            print("\n生成的测试图片:")
            for path in successful_paths:
                print(f"  - {path}")
        else:
            print("\n✗ 批量图片生成功能测试失败")
        
        return len(successful_paths) > 0
        
    except Exception as e:
        print(f"测试过程中发生错误: {e}")
        return False
    
    finally:
        # 清理测试文件（可选，保留用于检查）
        # shutil.rmtree(test_dir, ignore_errors=True)
        print(f"\n测试文件保存在: {test_dir}/")
        print("请检查生成的图片质量和内容是否符合预期")

def test_empty_batch():
    """
    测试空批次的处理
    """
    print("\n=== 测试空批次处理 ===")
    
    result = generate_images_batch([])
    if result == []:
        print("✓ 空批次处理正确")
        return True
    else:
        print("✗ 空批次处理错误")
        return False

if __name__ == "__main__":
    print("批量图片生成功能测试")
    print("=" * 50)
    
    # 运行测试
    test1_result = test_batch_image_generation()
    test2_result = test_empty_batch()
    
    print("\n" + "=" * 50)
    print("测试完成")
    
    if test1_result and test2_result:
        print("✓ 所有测试通过")
    else:
        print("✗ 部分测试失败")
        if not test1_result:
            print("  - 批量图片生成测试失败")
        if not test2_result:
            print("  - 空批次处理测试失败")