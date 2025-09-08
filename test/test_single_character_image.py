#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
测试单个角色图片生成脚本
"""

import os
import sys
import subprocess
import tempfile
import shutil

def test_single_character_image():
    """
    测试单个角色图片生成功能
    """
    print("=== 测试单个角色图片生成 ===")
    
    # 创建临时测试目录
    test_dir = tempfile.mkdtemp(prefix="test_character_")
    print(f"测试目录: {test_dir}")
    
    try:
        # 设置环境变量
        env = os.environ.copy()
        env.update({
            'CHARACTER_ID': 'test_001',
            'CHARACTER_NAME': '测试角色',
            'CHARACTER_GENDER': '女',
            'CHARACTER_AGE_GROUP': '青年',
            'CHARACTER_DESCRIPTION': '一个美丽的女性角色，有着长长的黑发和明亮的眼睛',
            'IMAGE_STYLE': '动漫风格',
            'IMAGE_QUALITY': 'high',
            'IMAGE_COUNT': '1',
            'CUSTOM_PROMPT': '高质量，精美细节',
            'TASK_ID': 'test_task_001',
            'CHAPTER_PATH': test_dir
        })
        
        print("设置的环境变量:")
        for key, value in env.items():
            if key.startswith(('CHARACTER_', 'TASK_', 'CHAPTER_', 'IMAGE_')):
                print(f"  {key}: {value}")
        
        # 运行角色图片生成脚本
        script_path = os.path.join(os.path.dirname(os.path.dirname(__file__)), 'gen_single_character_image.py')
        print(f"\n运行脚本: {script_path}")
        
        result = subprocess.run(
            [sys.executable, script_path],
            env=env,
            capture_output=True,
            text=True,
            cwd=os.path.dirname(script_path)
        )
        
        print(f"\n=== 脚本输出 ===")
        if result.stdout:
            print("标准输出:")
            print(result.stdout)
        
        if result.stderr:
            print("错误输出:")
            print(result.stderr)
        
        print(f"\n退出码: {result.returncode}")
        
        # 检查生成的文件
        character_dir = os.path.join(test_dir, "Character_Images/测试角色_test_001")
        if os.path.exists(character_dir):
            print(f"\n生成的文件:")
            for file in os.listdir(character_dir):
                file_path = os.path.join(character_dir, file)
                file_size = os.path.getsize(file_path)
                print(f"  {file} ({file_size} bytes)")
        else:
            print(f"\n未找到输出目录: {character_dir}")
        
        return result.returncode == 0
        
    except Exception as e:
        print(f"测试过程中发生错误: {str(e)}")
        import traceback
        traceback.print_exc()
        return False
    
    finally:
        # 清理测试目录
        try:
            shutil.rmtree(test_dir)
            print(f"\n已清理测试目录: {test_dir}")
        except Exception as e:
            print(f"清理测试目录失败: {str(e)}")

def test_missing_env_vars():
    """
    测试缺少环境变量的情况
    """
    print("\n=== 测试缺少环境变量的情况 ===")
    
    # 清除相关环境变量
    env = os.environ.copy()
    for key in list(env.keys()):
        if key.startswith(('CHARACTER_', 'TASK_', 'CHAPTER_')):
            del env[key]
    
    script_path = os.path.join(os.path.dirname(os.path.dirname(__file__)), 'gen_single_character_image.py')
    
    result = subprocess.run(
        [sys.executable, script_path],
        env=env,
        capture_output=True,
        text=True,
        cwd=os.path.dirname(script_path)
    )
    
    print(f"退出码: {result.returncode}")
    if result.stdout:
        print("标准输出:")
        print(result.stdout)
    if result.stderr:
        print("错误输出:")
        print(result.stderr)
    
    # 应该返回非零退出码
    return result.returncode != 0

if __name__ == '__main__':
    print("开始测试单个角色图片生成功能...\n")
    
    # 测试缺少环境变量的情况
    test1_success = test_missing_env_vars()
    print(f"测试1 (缺少环境变量): {'通过' if test1_success else '失败'}")
    
    # 测试正常情况
    test2_success = test_single_character_image()
    print(f"测试2 (正常生成): {'通过' if test2_success else '失败'}")
    
    overall_success = test1_success and test2_success
    print(f"\n=== 总体测试结果: {'通过' if overall_success else '失败'} ===")
    
    sys.exit(0 if overall_success else 1)