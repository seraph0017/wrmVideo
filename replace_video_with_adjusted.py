#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
替换视频文件脚本
将调整后的视频替换原始视频，并创建备份
"""

import os
import sys
import shutil
from datetime import datetime

def replace_video_with_backup(original_path, adjusted_path, create_backup=True):
    """替换视频文件并创建备份
    
    Args:
        original_path: 原始视频文件路径
        adjusted_path: 调整后的视频文件路径
        create_backup: 是否创建备份
    """
    print(f"=== 视频文件替换 ===")
    print(f"原始文件: {original_path}")
    print(f"调整后文件: {adjusted_path}")
    print()
    
    # 检查文件是否存在
    if not os.path.exists(original_path):
        print(f"❌ 原始视频文件不存在: {original_path}")
        return False
    
    if not os.path.exists(adjusted_path):
        print(f"❌ 调整后视频文件不存在: {adjusted_path}")
        return False
    
    # 获取文件大小信息
    original_size = os.path.getsize(original_path) / (1024 * 1024)
    adjusted_size = os.path.getsize(adjusted_path) / (1024 * 1024)
    
    print(f"📊 文件大小对比:")
    print(f"   原始文件: {original_size:.2f}MB")
    print(f"   调整后文件: {adjusted_size:.2f}MB")
    print(f"   大小变化: {adjusted_size - original_size:+.2f}MB")
    print()
    
    try:
        # 创建备份
        if create_backup:
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            backup_path = original_path.replace('.mp4', f'_backup_{timestamp}.mp4')
            
            print(f"📦 创建备份: {backup_path}")
            shutil.copy2(original_path, backup_path)
            print(f"✅ 备份创建成功")
        
        # 替换文件
        print(f"🔄 替换原始文件...")
        shutil.move(adjusted_path, original_path)
        print(f"✅ 文件替换成功")
        
        print()
        print(f"🎉 操作完成!")
        if create_backup:
            print(f"   原始文件已备份到: {backup_path}")
        print(f"   调整后的视频已替换原始文件: {original_path}")
        
        return True
        
    except Exception as e:
        print(f"❌ 替换文件失败: {e}")
        return False

def main():
    if len(sys.argv) < 3:
        print("用法: python replace_video_with_adjusted.py <原始视频> <调整后视频> [--no-backup]")
        print("")
        print("参数:")
        print("  原始视频: 要被替换的原始视频文件路径")
        print("  调整后视频: 时长调整后的视频文件路径")
        print("  --no-backup: 不创建备份文件（可选）")
        print("")
        print("示例:")
        print("  python replace_video_with_adjusted.py video.mp4 video_adjusted.mp4")
        print("  python replace_video_with_adjusted.py video.mp4 video_adjusted.mp4 --no-backup")
        sys.exit(1)
    
    original_path = sys.argv[1]
    adjusted_path = sys.argv[2]
    create_backup = '--no-backup' not in sys.argv
    
    success = replace_video_with_backup(original_path, adjusted_path, create_backup)
    
    if success:
        print(f"\n✅ 视频替换成功!")
        sys.exit(0)
    else:
        print(f"\n❌ 视频替换失败!")
        sys.exit(1)

if __name__ == "__main__":
    main()