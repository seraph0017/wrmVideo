#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
测试gen_image_async_v3.py的prompt保存功能
验证在生成图片时是否正确保存了对应的prompt信息
"""

import os
import sys
import tempfile
import json
import shutil

# 添加项目根目录到路径
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from gen_image_async_v3 import ArkImageGenerator


def test_prompt_save_functionality():
    """
    测试prompt保存功能
    """
    print("开始测试prompt保存功能...")
    
    # 创建临时测试目录
    test_dir = tempfile.mkdtemp(prefix="test_prompt_save_")
    print(f"测试目录: {test_dir}")
    
    try:
        # 初始化图片生成器
        generator = ArkImageGenerator(test_dir)
        
        # 测试数据
        test_prompt = "一个美丽的风景，蓝天白云，绿草如茵"
        test_output_path = os.path.join(test_dir, "test_scene_001.jpg")
        test_scene_number = 1
        
        print(f"测试prompt: {test_prompt}")
        print(f"输出路径: {test_output_path}")
        
        # 生成图片（这会同时保存prompt）
        success = generator.generate_image_sync(
            prompt=test_prompt,
            output_path=test_output_path,
            scene_number=test_scene_number
        )
        
        if success:
            print("✓ 图片生成成功")
            
            # 检查图片文件是否存在
            if os.path.exists(test_output_path):
                print("✓ 图片文件已保存")
            else:
                print("✗ 图片文件未找到")
                return False
            
            # 检查prompt文件是否存在
            prompt_path = os.path.splitext(test_output_path)[0] + '.prompt.json'
            if os.path.exists(prompt_path):
                print("✓ Prompt文件已保存")
                
                # 验证prompt文件内容
                with open(prompt_path, 'r', encoding='utf-8') as f:
                    prompt_data = json.load(f)
                
                print("Prompt文件内容:")
                print(json.dumps(prompt_data, ensure_ascii=False, indent=2))
                
                # 验证必要字段
                required_fields = ['image_file', 'prompt', 'timestamp', 'scene_number', 'model', 'generation_params']
                missing_fields = [field for field in required_fields if field not in prompt_data]
                
                if missing_fields:
                    print(f"✗ 缺少必要字段: {missing_fields}")
                    return False
                else:
                    print("✓ 所有必要字段都存在")
                
                # 验证prompt内容是否正确
                if prompt_data['prompt'] == test_prompt:
                    print("✓ Prompt内容正确")
                else:
                    print(f"✗ Prompt内容不匹配: 期望 '{test_prompt}', 实际 '{prompt_data['prompt']}'")
                    return False
                
                # 验证场景编号是否正确
                if prompt_data['scene_number'] == test_scene_number:
                    print("✓ 场景编号正确")
                else:
                    print(f"✗ 场景编号不匹配: 期望 {test_scene_number}, 实际 {prompt_data['scene_number']}")
                    return False
                
                # 验证生成参数
                expected_params = {"response_format": "b64_json", "watermark": False}
                if prompt_data['generation_params'] == expected_params:
                    print("✓ 生成参数正确")
                else:
                    print(f"✗ 生成参数不匹配: 期望 {expected_params}, 实际 {prompt_data['generation_params']}")
                    return False
                
                print("✓ 所有验证通过，prompt保存功能正常")
                return True
                
            else:
                print("✗ Prompt文件未找到")
                return False
        else:
            print("✗ 图片生成失败")
            return False
            
    except Exception as e:
        print(f"✗ 测试过程中发生错误: {e}")
        return False
    finally:
        # 清理测试目录
        if os.path.exists(test_dir):
            shutil.rmtree(test_dir)
            print(f"已清理测试目录: {test_dir}")


def test_prompt_save_method_only():
    """
    单独测试_save_prompt_info方法
    """
    print("\n开始测试_save_prompt_info方法...")
    
    # 创建临时测试目录
    test_dir = tempfile.mkdtemp(prefix="test_prompt_method_")
    print(f"测试目录: {test_dir}")
    
    try:
        # 初始化图片生成器
        generator = ArkImageGenerator(test_dir)
        
        # 测试数据
        test_prompt = "测试prompt内容"
        test_output_path = os.path.join(test_dir, "test_image.jpg")
        test_scene_number = 5
        
        # 直接调用_save_prompt_info方法
        success = generator._save_prompt_info(test_prompt, test_output_path, test_scene_number)
        
        if success:
            print("✓ _save_prompt_info方法执行成功")
            
            # 检查生成的文件
            prompt_path = os.path.splitext(test_output_path)[0] + '.prompt.json'
            if os.path.exists(prompt_path):
                print("✓ Prompt文件已创建")
                
                with open(prompt_path, 'r', encoding='utf-8') as f:
                    prompt_data = json.load(f)
                
                print("生成的prompt文件内容:")
                print(json.dumps(prompt_data, ensure_ascii=False, indent=2))
                return True
            else:
                print("✗ Prompt文件未创建")
                return False
        else:
            print("✗ _save_prompt_info方法执行失败")
            return False
            
    except Exception as e:
        print(f"✗ 测试过程中发生错误: {e}")
        return False
    finally:
        # 清理测试目录
        if os.path.exists(test_dir):
            shutil.rmtree(test_dir)
            print(f"已清理测试目录: {test_dir}")


if __name__ == "__main__":
    print("=" * 60)
    print("测试prompt保存功能")
    print("=" * 60)
    
    # 先测试单独的方法
    method_test_result = test_prompt_save_method_only()
    
    # 再测试完整功能（需要API调用）
    print("\n" + "=" * 60)
    print("注意: 完整功能测试需要有效的API配置")
    print("=" * 60)
    
    try:
        full_test_result = test_prompt_save_functionality()
    except Exception as e:
        print(f"完整功能测试跳过（可能是API配置问题）: {e}")
        full_test_result = None
    
    print("\n" + "=" * 60)
    print("测试结果总结:")
    print(f"方法测试: {'✓ 通过' if method_test_result else '✗ 失败'}")
    if full_test_result is not None:
        print(f"完整功能测试: {'✓ 通过' if full_test_result else '✗ 失败'}")
    else:
        print("完整功能测试: 跳过（API配置问题）")
    print("=" * 60)