#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
音频质量检测和修复工具
用于检测和修复低质量的音频文件
"""

import os
import subprocess
import ffmpeg
from pathlib import Path

def check_audio_quality(audio_path):
    """
    检查音频文件的质量参数
    
    Args:
        audio_path: 音频文件路径
    
    Returns:
        dict: 音频质量信息
    """
    try:
        result = subprocess.run([
            'ffprobe', '-v', 'quiet', '-show_entries', 
            'stream=codec_name,sample_rate,channels,bit_rate',
            '-select_streams', 'a:0', '-of', 'csv=p=0', audio_path
        ], capture_output=True, text=True)
        
        if result.returncode == 0 and result.stdout.strip():
            parts = result.stdout.strip().split(',')
            if len(parts) >= 4:
                return {
                    'codec': parts[0],
                    'sample_rate': int(parts[1]) if parts[1].isdigit() else 0,
                    'channels': int(parts[2]) if parts[2].isdigit() else 0,
                    'bit_rate': int(parts[3]) if parts[3].isdigit() else 0,
                    'is_low_quality': int(parts[1]) < 44100 if parts[1].isdigit() else True
                }
    except Exception as e:
        print(f"检查音频质量时出错: {e}")
    
    return None

def enhance_audio_quality(input_path, output_path):
    """
    提升音频质量
    
    Args:
        input_path: 输入音频文件路径
        output_path: 输出音频文件路径
    
    Returns:
        bool: 是否成功
    """
    try:
        print(f"正在提升音频质量: {os.path.basename(input_path)}")
        
        # 确保输出目录存在
        os.makedirs(os.path.dirname(output_path), exist_ok=True)
        
        # 使用ffmpeg提升音频质量
        (
            ffmpeg
            .input(input_path)
            .output(
                output_path,
                acodec='libmp3lame',  # 使用高质量MP3编码器
                ar=44100,             # 采样率44.1kHz
                ab='192k',            # 比特率192kbps
                ac=1                  # 单声道
            )
            .overwrite_output()
            .run(quiet=True)
        )
        
        if os.path.exists(output_path):
            print(f"音频质量提升完成: {output_path}")
            return True
        else:
            print("音频质量提升失败")
            return False
            
    except Exception as e:
        print(f"提升音频质量时出错: {e}")
        return False

def scan_and_fix_directory(directory_path, backup=True):
    """
    扫描目录中的所有音频文件并修复低质量音频
    
    Args:
        directory_path: 要扫描的目录路径
        backup: 是否备份原文件
    
    Returns:
        dict: 处理结果统计
    """
    stats = {
        'total_files': 0,
        'low_quality_files': 0,
        'fixed_files': 0,
        'failed_files': 0
    }
    
    print(f"\n=== 扫描目录: {directory_path} ===")
    
    # 查找所有音频文件
    audio_extensions = ['.mp3', '.wav', '.m4a', '.aac']
    audio_files = []
    
    for ext in audio_extensions:
        audio_files.extend(Path(directory_path).rglob(f'*{ext}'))
    
    stats['total_files'] = len(audio_files)
    print(f"找到 {stats['total_files']} 个音频文件")
    
    for audio_file in audio_files:
        audio_path = str(audio_file)
        print(f"\n检查: {audio_file.name}")
        
        # 检查音频质量
        quality_info = check_audio_quality(audio_path)
        
        if quality_info:
            print(f"  采样率: {quality_info['sample_rate']} Hz")
            print(f"  比特率: {quality_info['bit_rate']} bps")
            print(f"  编码: {quality_info['codec']}")
            
            if quality_info['is_low_quality']:
                stats['low_quality_files'] += 1
                print(f"  ⚠️  检测到低质量音频 (采样率: {quality_info['sample_rate']} Hz)")
                
                # 备份原文件
                if backup:
                    backup_path = audio_path + '.backup'
                    if not os.path.exists(backup_path):
                        os.rename(audio_path, backup_path)
                        print(f"  📁 已备份原文件: {backup_path}")
                        source_path = backup_path
                    else:
                        source_path = backup_path
                else:
                    source_path = audio_path
                
                # 提升音频质量
                if enhance_audio_quality(source_path, audio_path):
                    stats['fixed_files'] += 1
                    print(f"  ✅ 音频质量已提升")
                else:
                    stats['failed_files'] += 1
                    print(f"  ❌ 音频质量提升失败")
            else:
                print(f"  ✅ 音频质量良好")
        else:
            print(f"  ❌ 无法检查音频质量")
    
    return stats

def main():
    """
    主函数
    """
    import sys
    
    if len(sys.argv) < 2:
        print("使用方法:")
        print("  python fix_audio_quality.py <目录路径>")
        print("  python fix_audio_quality.py <音频文件路径>")
        print("\n示例:")
        print("  python fix_audio_quality.py data/001/chapter01")
        print("  python fix_audio_quality.py data/001/chapter01/audio.mp3")
        return
    
    target_path = sys.argv[1]
    
    if not os.path.exists(target_path):
        print(f"错误: 路径不存在 {target_path}")
        return
    
    if os.path.isfile(target_path):
        # 处理单个文件
        print(f"检查单个文件: {target_path}")
        quality_info = check_audio_quality(target_path)
        
        if quality_info:
            print(f"采样率: {quality_info['sample_rate']} Hz")
            print(f"比特率: {quality_info['bit_rate']} bps")
            print(f"编码: {quality_info['codec']}")
            
            if quality_info['is_low_quality']:
                print("⚠️  检测到低质量音频")
                
                # 生成输出文件名
                base_name = os.path.splitext(target_path)[0]
                output_path = f"{base_name}_enhanced.mp3"
                
                if enhance_audio_quality(target_path, output_path):
                    print(f"✅ 高质量音频已保存: {output_path}")
                else:
                    print("❌ 音频质量提升失败")
            else:
                print("✅ 音频质量良好")
        else:
            print("❌ 无法检查音频质量")
    
    elif os.path.isdir(target_path):
        # 处理目录
        stats = scan_and_fix_directory(target_path)
        
        print(f"\n=== 处理完成 ===")
        print(f"总文件数: {stats['total_files']}")
        print(f"低质量文件: {stats['low_quality_files']}")
        print(f"成功修复: {stats['fixed_files']}")
        print(f"修复失败: {stats['failed_files']}")
        
        if stats['fixed_files'] > 0:
            print(f"\n✅ 已成功修复 {stats['fixed_files']} 个音频文件")
            print("原文件已备份为 .backup 文件")
    
    else:
        print(f"错误: 无效的路径 {target_path}")

if __name__ == "__main__":
    main()