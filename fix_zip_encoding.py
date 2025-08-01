#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
修复ZIP文件中文编码问题的工具
解决Windows创建的ZIP文件在macOS/Linux上显示乱码的问题
"""

import zipfile
import os
import sys
import shutil
from pathlib import Path

def detect_encoding(filename_bytes):
    """
    尝试检测文件名的正确编码
    """
    encodings = ['gbk', 'gb2312', 'utf-8', 'big5']
    
    for encoding in encodings:
        try:
            decoded = filename_bytes.decode(encoding)
            # 检查是否包含中文字符
            if any('\u4e00' <= char <= '\u9fff' for char in decoded):
                return decoded, encoding
        except (UnicodeDecodeError, UnicodeError):
            continue
    
    # 如果都失败了，尝试cp437->gbk的转换（常见的Windows->Unix问题）
    try:
        # filename_bytes已经是bytes，不需要再encode
        decoded = filename_bytes.decode('gbk')
        return decoded, 'cp437->gbk'
    except (UnicodeDecodeError, UnicodeError):
        pass
    
    # 最后尝试忽略错误
    return filename_bytes.decode('utf-8', errors='ignore'), 'utf-8-ignore'

def fix_zip_encoding(zip_path, output_dir=None, encoding='gbk'):
    """
    修复ZIP文件的中文编码问题
    
    Args:
        zip_path: ZIP文件路径
        output_dir: 输出目录，如果为None则在ZIP文件同目录下创建
        encoding: 尝试使用的编码，默认为gbk
    """
    zip_path = Path(zip_path)
    
    if not zip_path.exists():
        print(f"错误: ZIP文件不存在: {zip_path}")
        return False
    
    if output_dir is None:
        output_dir = zip_path.parent / f"{zip_path.stem}_fixed"
    else:
        output_dir = Path(output_dir)
    
    # 创建输出目录
    output_dir.mkdir(exist_ok=True)
    
    print(f"正在处理ZIP文件: {zip_path}")
    print(f"输出目录: {output_dir}")
    
    try:
        with zipfile.ZipFile(zip_path, 'r') as zip_file:
            total_files = len(zip_file.filelist)
            extracted_count = 0
            
            for file_info in zip_file.filelist:
                # 获取原始文件名
                original_filename = file_info.filename
                
                # 尝试检测正确的编码
                try:
                    if encoding == 'auto':
                        # 先转换为字节再检测编码
                        filename_bytes = original_filename.encode('cp437')
                        correct_filename, detected_encoding = detect_encoding(filename_bytes)
                        print(f"检测到编码: {detected_encoding} -> {correct_filename}")
                    else:
                        # 先转换为字节再用指定编码解码
                        filename_bytes = original_filename.encode('cp437')
                        correct_filename = filename_bytes.decode(encoding)
                except (UnicodeDecodeError, UnicodeEncodeError):
                    print(f"警告: 无法解码文件名，使用原始名称: {original_filename}")
                    correct_filename = original_filename
                
                # 跳过macOS的隐藏文件
                if '.__MACOSX' in correct_filename or correct_filename.startswith('__MACOSX'):
                    continue
                
                # 构建输出路径
                output_path = output_dir / correct_filename
                
                # 创建目录
                if file_info.is_dir():
                    output_path.mkdir(parents=True, exist_ok=True)
                    print(f"创建目录: {correct_filename}")
                else:
                    # 确保父目录存在
                    output_path.parent.mkdir(parents=True, exist_ok=True)
                    
                    # 提取文件
                    with zip_file.open(file_info) as source:
                        with open(output_path, 'wb') as target:
                            shutil.copyfileobj(source, target)
                    
                    extracted_count += 1
                    print(f"提取文件 ({extracted_count}/{total_files}): {correct_filename}")
            
            print(f"\n成功提取 {extracted_count} 个文件到: {output_dir}")
            return True
            
    except Exception as e:
        print(f"错误: 处理ZIP文件时发生异常: {e}")
        return False

def main():
    if len(sys.argv) < 2:
        print("用法: python fix_zip_encoding.py <zip_file> [output_dir] [encoding]")
        print("")
        print("参数说明:")
        print("  zip_file    : ZIP文件路径")
        print("  output_dir  : 输出目录（可选，默认为ZIP文件同目录下的_fixed文件夹）")
        print("  encoding    : 编码格式（可选，默认为gbk，可选: gbk, gb2312, utf-8, big5, auto）")
        print("")
        print("示例:")
        print("  python fix_zip_encoding.py data.zip")
        print("  python fix_zip_encoding.py data.zip ./output")
        print("  python fix_zip_encoding.py data.zip ./output gbk")
        print("  python fix_zip_encoding.py data.zip ./output auto  # 自动检测编码")
        return
    
    zip_path = sys.argv[1]
    output_dir = sys.argv[2] if len(sys.argv) > 2 else None
    encoding = sys.argv[3] if len(sys.argv) > 3 else 'gbk'
    
    success = fix_zip_encoding(zip_path, output_dir, encoding)
    
    if success:
        print("\n✅ ZIP文件编码修复完成！")
    else:
        print("\n❌ ZIP文件编码修复失败！")
        sys.exit(1)

if __name__ == "__main__":
    main()