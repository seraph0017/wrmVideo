#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
清理regenerated文件脚本
用于删除Character_Images目录下的regenerated文件和备份文件
"""

import os
import glob
from pathlib import Path
from typing import List

def find_files_to_cleanup() -> tuple[List[str], List[str]]:
    """
    查找需要清理的文件
    
    Returns:
        tuple[List[str], List[str]]: (regenerated_files, backup_files)
    """
    character_images_dir = Path("/Users/xunan/Projects/wrmVideo/Character_Images")
    
    # 查找所有regenerated文件
    regenerated_files = list(character_images_dir.rglob("*_regenerated.jpeg"))
    
    # 查找所有备份文件
    backup_files = list(character_images_dir.rglob("*.backup"))
    
    return [str(f) for f in regenerated_files], [str(f) for f in backup_files]

def cleanup_files(file_list: List[str], file_type: str, dry_run: bool = True) -> int:
    """
    清理指定类型的文件
    
    Args:
        file_list (List[str]): 文件列表
        file_type (str): 文件类型描述
        dry_run (bool): 是否为试运行模式
        
    Returns:
        int: 删除的文件数量
    """
    if not file_list:
        print(f"没有找到 {file_type} 文件")
        return 0
    
    print(f"\n找到 {len(file_list)} 个 {file_type} 文件")
    
    deleted_count = 0
    error_count = 0
    
    for i, file_path in enumerate(file_list, 1):
        try:
            if dry_run:
                print(f"  [{i}/{len(file_list)}] 将删除: {os.path.basename(file_path)}")
            else:
                os.remove(file_path)
                print(f"  [{i}/{len(file_list)}] ✅ 已删除: {os.path.basename(file_path)}")
            deleted_count += 1
        except Exception as e:
            print(f"  [{i}/{len(file_list)}] ❌ 删除失败: {os.path.basename(file_path)} - {e}")
            error_count += 1
    
    print(f"\n{file_type} 处理结果:")
    print(f"  成功处理: {deleted_count} 个")
    print(f"  失败: {error_count} 个")
    
    return deleted_count

def main():
    """
    主函数
    """
    import sys
    
    print("Regenerated文件清理工具")
    print("=" * 40)
    
    # 解析命令行参数
    dry_run = True
    cleanup_regenerated = False
    cleanup_backup = False
    
    if len(sys.argv) > 1:
        for arg in sys.argv[1:]:
            if arg == '--execute':
                dry_run = False
            elif arg == '--regenerated':
                cleanup_regenerated = True
            elif arg == '--backup':
                cleanup_backup = True
            elif arg == '--all':
                cleanup_regenerated = True
                cleanup_backup = True
    
    # 如果没有指定清理类型，默认显示帮助
    if not cleanup_regenerated and not cleanup_backup:
        print("使用方法:")
        print("  python cleanup_regenerated_files.py [选项]")
        print("")
        print("选项:")
        print("  --regenerated    清理regenerated文件")
        print("  --backup         清理备份文件")
        print("  --all            清理所有文件（regenerated + backup）")
        print("  --execute        实际执行删除（默认为试运行）")
        print("")
        print("示例:")
        print("  python cleanup_regenerated_files.py --regenerated          # 试运行，显示将删除的regenerated文件")
        print("  python cleanup_regenerated_files.py --backup --execute     # 实际删除备份文件")
        print("  python cleanup_regenerated_files.py --all --execute        # 实际删除所有文件")
        return
    
    if dry_run:
        print("⚠️  试运行模式 - 不会实际删除文件")
        print("   如需实际删除，请添加 --execute 参数")
    else:
        print("🚀 执行模式 - 将实际删除文件")
        
        # 确认操作
        actions = []
        if cleanup_regenerated:
            actions.append("regenerated文件")
        if cleanup_backup:
            actions.append("备份文件")
        
        response = input(f"确认要删除 {' 和 '.join(actions)} 吗？(y/N): ")
        if response.lower() != 'y':
            print("操作已取消")
            return
    
    # 查找文件
    regenerated_files, backup_files = find_files_to_cleanup()
    
    total_deleted = 0
    
    # 清理regenerated文件
    if cleanup_regenerated:
        total_deleted += cleanup_files(regenerated_files, "regenerated", dry_run)
    
    # 清理备份文件
    if cleanup_backup:
        total_deleted += cleanup_files(backup_files, "备份", dry_run)
    
    print(f"\n{'=' * 40}")
    if dry_run:
        print(f"试运行完成，共找到 {total_deleted} 个文件可删除")
        print("💡 如需实际删除，请添加 --execute 参数")
    else:
        print(f"清理完成，共删除 {total_deleted} 个文件")
    print(f"{'=' * 40}")

if __name__ == "__main__":
    main()