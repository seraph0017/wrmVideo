#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
替换regenerated图片脚本
将Character_Images目录下所有regenerated图片替换为原始图片
"""

import os
import json
import shutil
from pathlib import Path
from typing import List, Tuple

def find_regenerated_tasks() -> List[str]:
    """
    查找所有regenerated任务文件
    
    Returns:
        List[str]: 任务文件路径列表
    """
    done_tasks_dir = Path("done_tasks")
    if not done_tasks_dir.exists():
        print(f"错误: {done_tasks_dir} 目录不存在")
        return []
    
    task_files = list(done_tasks_dir.glob("regenerate_*.txt"))
    print(f"找到 {len(task_files)} 个regenerated任务文件")
    return [str(f) for f in task_files]

def parse_task_file(task_file: str) -> Tuple[str, str]:
    """
    解析任务文件，获取原始路径和regenerated路径
    
    Args:
        task_file (str): 任务文件路径
        
    Returns:
        Tuple[str, str]: (original_path, regenerated_path)
    """
    try:
        with open(task_file, 'r', encoding='utf-8') as f:
            content = f.read()
            
        # 解析JSON内容
        task_data = json.loads(content)
        original_path = task_data.get('original_path', '')
        output_path = task_data.get('output_path', '')
        
        return original_path, output_path
    except Exception as e:
        print(f"解析任务文件 {task_file} 失败: {e}")
        return '', ''

def replace_regenerated_images(dry_run: bool = True) -> None:
    """
    替换所有regenerated图片
    
    Args:
        dry_run (bool): 是否为试运行模式
    """
    task_files = find_regenerated_tasks()
    if not task_files:
        print("没有找到任何regenerated任务文件")
        return
    
    replaced_count = 0
    skipped_count = 0
    error_count = 0
    
    print(f"\n{'=' * 60}")
    print(f"开始处理 {len(task_files)} 个regenerated图片")
    print(f"模式: {'试运行' if dry_run else '实际替换'}")
    print(f"{'=' * 60}\n")
    
    for i, task_file in enumerate(task_files, 1):
        print(f"[{i}/{len(task_files)}] 处理: {os.path.basename(task_file)}")
        
        original_path, regenerated_path = parse_task_file(task_file)
        
        if not original_path or not regenerated_path:
            print(f"  ❌ 跳过: 无法解析路径信息")
            skipped_count += 1
            continue
            
        # 检查文件是否存在
        if not os.path.exists(regenerated_path):
            print(f"  ❌ 跳过: regenerated图片不存在 - {regenerated_path}")
            skipped_count += 1
            continue
            
        if not os.path.exists(original_path):
            print(f"  ⚠️  警告: 原始图片不存在 - {original_path}")
            
        try:
            if dry_run:
                print(f"  🔍 将替换: {original_path}")
                print(f"     使用: {regenerated_path}")
            else:
                # 创建原始文件的备份
                if os.path.exists(original_path):
                    backup_path = original_path + ".backup"
                    shutil.copy2(original_path, backup_path)
                    print(f"  💾 备份原始文件: {backup_path}")
                
                # 复制regenerated图片到原始位置
                shutil.copy2(regenerated_path, original_path)
                print(f"  ✅ 替换成功: {os.path.basename(original_path)}")
                
            replaced_count += 1
            
        except Exception as e:
            print(f"  ❌ 替换失败: {e}")
            error_count += 1
    
    # 输出统计信息
    print(f"\n{'=' * 60}")
    print(f"处理完成统计:")
    print(f"  成功处理: {replaced_count} 个")
    print(f"  跳过文件: {skipped_count} 个")
    print(f"  错误文件: {error_count} 个")
    print(f"  总计文件: {len(task_files)} 个")
    print(f"{'=' * 60}")
    
    if dry_run:
        print("\n💡 这是试运行模式，没有实际修改文件")
        print("   如需实际替换，请运行: python replace_regenerated_images.py --execute")

def main():
    """
    主函数
    """
    import sys
    
    # 检查命令行参数
    dry_run = True
    if len(sys.argv) > 1 and sys.argv[1] == '--execute':
        dry_run = False
        
    print("Regenerated图片替换工具")
    print("=" * 40)
    
    if dry_run:
        print("⚠️  试运行模式 - 不会实际修改文件")
        print("   如需实际替换，请添加 --execute 参数")
    else:
        print("🚀 执行模式 - 将实际替换文件")
        response = input("确认要替换所有regenerated图片吗？(y/N): ")
        if response.lower() != 'y':
            print("操作已取消")
            return
    
    replace_regenerated_images(dry_run=dry_run)

if __name__ == "__main__":
    main()