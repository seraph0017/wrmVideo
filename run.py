#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
自动化视频生成流程脚本
按顺序执行所有必要的步骤来生成完整的视频
"""

import os
import sys
import subprocess
import argparse
import time
from pathlib import Path

def run_command(command, description):
    """
    执行命令并处理错误
    
    Args:
        command: 要执行的命令列表
        description: 命令描述
    
    Returns:
        bool: 是否成功执行
    """
    print(f"\n{'='*50}")
    print(f"开始执行: {description}")
    print(f"命令: {' '.join(command)}")
    print(f"{'='*50}")
    
    try:
        start_time = time.time()
        result = subprocess.run(command, check=True, capture_output=False)
        end_time = time.time()
        
        print(f"\n✓ {description} 执行成功 (耗时: {end_time - start_time:.2f}秒)")
        return True
        
    except subprocess.CalledProcessError as e:
        print(f"\n✗ {description} 执行失败")
        print(f"错误代码: {e.returncode}")
        return False
    except Exception as e:
        print(f"\n✗ {description} 执行时发生错误: {e}")
        return False

def validate_input_file(novel_file):
    """
    验证输入的小说文件是否存在
    
    Args:
        novel_file: 小说文件路径
    
    Returns:
        bool: 文件是否存在
    """
    if not os.path.exists(novel_file):
        print(f"错误: 小说文件不存在: {novel_file}")
        return False
    
    if not novel_file.endswith('.txt'):
        print(f"警告: 文件不是.txt格式: {novel_file}")
    
    return True

def get_data_dir_from_novel_file(novel_file):
    """
    从小说文件路径推断数据目录
    
    Args:
        novel_file: 小说文件路径
    
    Returns:
        str: 数据目录路径
    """
    # 假设小说文件在 data/xxx/ 目录下
    novel_path = Path(novel_file)
    if novel_path.parent.name.startswith('data') or 'data' in str(novel_path.parent):
        return str(novel_path.parent)
    else:
        # 如果不在标准data目录下，使用文件所在目录
        return str(novel_path.parent)

def main():
    parser = argparse.ArgumentParser(description='自动化视频生成流程')
    parser.add_argument('novel_file', help='小说文件路径 (例如: data/001/xxx.txt)')
    parser.add_argument('--skip-steps', nargs='*', 
                       choices=['script', 'character', 'image', 'audio', 'timestamp', 'first_video', 'subtitle', 'video'],
                       help='跳过指定的步骤')
    parser.add_argument('--only-steps', nargs='*',
                       choices=['script', 'character', 'image', 'audio', 'timestamp', 'first_video', 'subtitle', 'video'],
                       help='只执行指定的步骤')
    
    args = parser.parse_args()
    
    # 验证输入文件
    if not validate_input_file(args.novel_file):
        sys.exit(1)
    
    # 获取数据目录
    data_dir = get_data_dir_from_novel_file(args.novel_file)
    
    print(f"小说文件: {args.novel_file}")
    print(f"数据目录: {data_dir}")
    
    # 定义执行步骤
    steps = [
        {
            'name': 'script',
            'command': ['python', 'gen_script.py', args.novel_file],
            'description': '生成解说文案'
        },
        {
            'name': 'character',
            'command': ['python', 'gen_character_image.py', data_dir],
            'description': '生成角色图片'
        },
        {
            'name': 'image',
            'command': ['python', 'gen_image.py', data_dir],
            'description': '生成场景图片'
        },
        {
            'name': 'audio',
            'command': ['python', 'gen_audio.py', data_dir],
            'description': '生成旁白音频'
        },
        {
            'name': 'timestamp',
            'command': ['python', 'fix_timestamps_batch.py', data_dir],
            'description': '修复字幕时间戳'
        },
        {
            'name': 'first_video',
            'command': ['python', 'gen_first_video.py', data_dir],
            'description': '生成第一个narration的视频'
        },
        {
            'name': 'subtitle',
            'command': ['python', 'gen_ass.py', data_dir],
            'description': '生成字幕文件'
        },
        {
            'name': 'video',
            'command': ['python', 'gen_video.py', data_dir],
            'description': '生成最终视频'
        }
    ]
    
    # 过滤要执行的步骤
    if args.only_steps:
        steps = [step for step in steps if step['name'] in args.only_steps]
    elif args.skip_steps:
        steps = [step for step in steps if step['name'] not in args.skip_steps]
    
    print(f"\n将执行 {len(steps)} 个步骤:")
    for i, step in enumerate(steps, 1):
        print(f"  {i}. {step['description']} ({step['name']})")
    
    # 确认执行
    try:
        response = input("\n是否继续执行? (y/N): ")
        if response.lower() not in ['y', 'yes', '是']:
            print("用户取消执行")
            sys.exit(0)
    except KeyboardInterrupt:
        print("\n用户取消执行")
        sys.exit(0)
    
    # 执行所有步骤
    success_count = 0
    total_start_time = time.time()
    
    for i, step in enumerate(steps, 1):
        print(f"\n进度: {i}/{len(steps)}")
        
        if run_command(step['command'], step['description']):
            success_count += 1
        else:
            print(f"\n步骤 '{step['description']}' 执行失败")
            response = input("是否继续执行后续步骤? (y/N): ")
            if response.lower() not in ['y', 'yes', '是']:
                break
    
    total_end_time = time.time()
    
    # 输出总结
    print(f"\n{'='*60}")
    print(f"执行完成")
    print(f"{'='*60}")
    print(f"成功执行: {success_count}/{len(steps)} 个步骤")
    print(f"总耗时: {total_end_time - total_start_time:.2f}秒")
    
    if success_count == len(steps):
        print(f"\n✓ 所有步骤执行成功!")
        print(f"生成的视频文件应该在: {data_dir}")
    else:
        print(f"\n⚠ 部分步骤执行失败，请检查错误信息")
        sys.exit(1)

if __name__ == '__main__':
    main()