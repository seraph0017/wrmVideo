#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
本地ZIP文件处理脚本
直接解压ZIP文件并按章节号排序生成章节文件夹，无需网络调用
"""

import os
import sys
import re
import zipfile
import argparse
from pathlib import Path

def detect_zip_encoding(filename_bytes):
    """检测ZIP文件名编码"""
    encodings = ['utf-8', 'gbk', 'gb2312', 'gb18030', 'big5']
    
    for encoding in encodings:
        try:
            decoded = filename_bytes.decode(encoding)
            if '第' in decoded and '章' in decoded:
                return decoded, encoding
        except (UnicodeDecodeError, UnicodeEncodeError):
            continue
    
    # 如果都失败，返回原始文件名
    try:
        return filename_bytes.decode('utf-8', errors='ignore'), 'utf-8'
    except:
        return str(filename_bytes), 'bytes'

def decode_file_content(file_content, filename):
    """解码文件内容"""
    encodings = ['utf-8', 'gbk', 'gb2312', 'gb18030', 'big5', 'latin1']
    
    for encoding in encodings:
        try:
            content = file_content.decode(encoding)
            return content
        except UnicodeDecodeError:
            continue
        except Exception as e:
            continue
    
    return ""

def extract_chapter_number(filename):
    """从文件名中提取章节号"""
    # 提取文件名中的数字
    numbers = re.findall(r'\d+', os.path.basename(filename))
    return int(numbers[0]) if numbers else 0

def process_zip_file(zip_path, output_dir, max_chapters=10):
    """处理ZIP文件，按章节号排序并生成章节文件夹"""
    print(f"🔧 正在处理ZIP文件: {zip_path}")
    
    # 确保输出目录存在
    os.makedirs(output_dir, exist_ok=True)
    
    try:
        with zipfile.ZipFile(zip_path, 'r') as zip_file:
            # 查找文本文件
            text_files = []
            
            for file_info in zip_file.filelist:
                original_filename = file_info.filename
                
                # 跳过macOS的隐藏文件和目录
                if '__MACOSX' in original_filename or file_info.is_dir():
                    continue
                
                # 修复文件名编码
                try:
                    filename_bytes = original_filename.encode('cp437')
                    correct_filename, detected_encoding = detect_zip_encoding(filename_bytes)
                except (UnicodeDecodeError, UnicodeEncodeError):
                    correct_filename = original_filename
                    detected_encoding = 'original'
                
                # 检查是否为文本文件
                if correct_filename.lower().endswith(('.txt', '.md', '.text')):
                    text_files.append((file_info, correct_filename, detected_encoding))
                    print(f"📄 找到文本文件: {correct_filename} (编码: {detected_encoding})")
            
            if not text_files:
                print("❌ ZIP文件中未找到文本文件")
                return False
            
            # 按章节号排序文件
            text_files.sort(key=lambda x: extract_chapter_number(x[1]))
            print(f"📋 按章节号排序后的文件顺序:")
            for i, (file_info, correct_filename, detected_encoding) in enumerate(text_files[:20], 1):
                print(f"  {i}. {correct_filename}")
            if len(text_files) > 20:
                print(f"  ... 还有 {len(text_files) - 20} 个文件")
            
            # 读取并保存章节文件
            chapter_count = 0
            all_content = []
            
            for file_info, correct_filename, detected_encoding in text_files:
                if chapter_count >= max_chapters:
                    break
                    
                try:
                    with zip_file.open(file_info) as f:
                        file_content = f.read()
                    
                    # 解码文件内容
                    content = decode_file_content(file_content, correct_filename)
                    
                    if content:
                        # 提取章节标题
                        chapter_title = os.path.splitext(os.path.basename(correct_filename))[0]
                        
                        # 创建章节文件夹
                        chapter_count += 1
                        chapter_dir = os.path.join(output_dir, f"chapter_{chapter_count:03d}")
                        os.makedirs(chapter_dir, exist_ok=True)
                        
                        # 保存原始内容
                        original_file = os.path.join(chapter_dir, "original_content.txt")
                        with open(original_file, 'w', encoding='utf-8') as f:
                            f.write(f"=== {correct_filename} ===\n{content}")
                        
                        print(f"✅ 生成章节 {chapter_count}: {chapter_title}")
                        all_content.append(content)
                        
                except Exception as e:
                    print(f"⚠️ 处理文件失败: {correct_filename}, 错误: {e}")
                    continue
            
            print(f"🎉 成功处理 {chapter_count} 个章节")
            return True
            
    except Exception as e:
        print(f"❌ 处理ZIP文件时出错: {e}")
        return False

def main():
    parser = argparse.ArgumentParser(description='本地ZIP文件章节处理工具')
    parser.add_argument('zip_file', help='ZIP文件路径')
    parser.add_argument('--output', '-o', default='output', help='输出目录')
    parser.add_argument('--chapters', '-c', type=int, default=10, help='最大章节数')
    
    args = parser.parse_args()
    
    if not os.path.exists(args.zip_file):
        print(f"❌ 文件不存在: {args.zip_file}")
        return 1
    
    print(f"输入文件: {args.zip_file}")
    print(f"输出目录: {args.output}")
    print(f"最大章节数: {args.chapters}")
    print("=" * 50)
    
    success = process_zip_file(args.zip_file, args.output, args.chapters)
    
    if success:
        print("\n🎉 处理完成！")
        return 0
    else:
        print("\n❌ 处理失败！")
        return 1

if __name__ == "__main__":
    sys.exit(main())