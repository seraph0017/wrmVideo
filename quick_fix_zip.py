#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
快速修复ZIP文件中文编码问题
简化版本，一键修复
"""

import zipfile
import os
import sys
from pathlib import Path

def quick_fix_zip(zip_path):
    """
    快速修复ZIP文件的中文编码问题
    """
    zip_path = Path(zip_path)
    
    if not zip_path.exists():
        print(f"❌ 错误: ZIP文件不存在: {zip_path}")
        return False
    
    # 输出目录
    output_dir = zip_path.parent / f"{zip_path.stem}_fixed"
    output_dir.mkdir(exist_ok=True)
    
    print(f"🔧 正在修复ZIP文件: {zip_path.name}")
    print(f"📁 输出目录: {output_dir}")
    
    try:
        with zipfile.ZipFile(zip_path, 'r') as zip_file:
            extracted_count = 0
            
            for file_info in zip_file.filelist:
                original_filename = file_info.filename
                
                # 跳过macOS的隐藏文件
                if '__MACOSX' in original_filename:
                    continue
                
                # 尝试修复编码
                try:
                    # 尝试cp437->gbk转换（最常见的情况）
                    filename_bytes = original_filename.encode('cp437')
                    correct_filename = filename_bytes.decode('gbk')
                    
                    # 验证是否包含中文字符
                    if not any('\u4e00' <= char <= '\u9fff' for char in correct_filename):
                        # 如果没有中文字符，尝试UTF-8
                        correct_filename = filename_bytes.decode('utf-8', errors='ignore')
                        
                except (UnicodeDecodeError, UnicodeEncodeError):
                    # 如果失败，使用原始文件名
                    correct_filename = original_filename
                
                # 构建输出路径
                output_path = output_dir / correct_filename
                
                # 创建目录或提取文件
                if file_info.is_dir():
                    output_path.mkdir(parents=True, exist_ok=True)
                else:
                    output_path.parent.mkdir(parents=True, exist_ok=True)
                    
                    with zip_file.open(file_info) as source:
                        with open(output_path, 'wb') as target:
                            target.write(source.read())
                    
                    extracted_count += 1
                    if extracted_count % 50 == 0:
                        print(f"📄 已处理 {extracted_count} 个文件...")
            
            print(f"\n✅ 成功修复！提取了 {extracted_count} 个文件")
            print(f"📂 文件位置: {output_dir}")
            return True
            
    except Exception as e:
        print(f"❌ 错误: {e}")
        return False

def main():
    if len(sys.argv) != 2:
        print("🔧 ZIP文件中文编码快速修复工具")
        print("")
        print("用法: python quick_fix_zip.py <zip_file>")
        print("")
        print("示例:")
        print("  python quick_fix_zip.py data.zip")
        print("  python quick_fix_zip.py /path/to/your/file.zip")
        return
    
    zip_path = sys.argv[1]
    success = quick_fix_zip(zip_path)
    
    if not success:
        sys.exit(1)

if __name__ == "__main__":
    main()