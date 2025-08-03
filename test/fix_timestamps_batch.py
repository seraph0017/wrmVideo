#!/usr/bin/env python3
# -*- coding: utf-8 -*-

import json
import os
import sys
import subprocess
import shutil
from pathlib import Path

# 添加项目根目录到Python路径
sys.path.append('/Users/xunan/Projects/wrmProject')

def get_audio_duration(audio_file):
    """
    获取音频文件的实际时长
    """
    try:
        cmd = ['ffprobe', '-v', 'quiet', '-print_format', 'json', '-show_format', audio_file]
        result = subprocess.run(cmd, capture_output=True, text=True)
        if result.returncode == 0:
            info = json.loads(result.stdout)
            return float(info['format']['duration'])
        else:
            print(f"警告: 无法获取音频信息 {audio_file}: {result.stderr}")
            return None
    except Exception as e:
        print(f"错误: 检查音频文件 {audio_file} 时出错: {e}")
        return None

def fix_timestamps_file(timestamp_file, audio_file):
    """
    修复单个时间戳文件
    """
    try:
        # 获取实际音频时长
        actual_duration = get_audio_duration(audio_file)
        if actual_duration is None:
            return False
        
        # 读取时间戳文件
        with open(timestamp_file, 'r', encoding='utf-8') as f:
            timestamp_data = json.load(f)
        
        character_timestamps = timestamp_data.get('character_timestamps', [])
        recorded_duration = timestamp_data.get('duration', 0)
        
        if not character_timestamps:
            print(f"警告: {timestamp_file} 中没有字符时间戳数据")
            return False
        
        # 检查是否需要修复
        max_end_time = max(ts['end_time'] for ts in character_timestamps)
        duration_diff = abs(actual_duration - recorded_duration)
        
        print(f"  记录时长: {recorded_duration:.3f}s")
        print(f"  实际时长: {actual_duration:.3f}s")
        print(f"  最大时间戳: {max_end_time:.3f}s")
        print(f"  时长差异: {duration_diff:.3f}s")
        
        # 如果时长差异小于0.1秒且最大时间戳在有效范围内，则不需要修复
        if duration_diff < 0.1 and max_end_time <= actual_duration:
            print(f"  ✓ 时间戳数据正常，无需修复")
            return True
        
        # 需要修复：按比例缩放时间戳
        if recorded_duration > 0:
            scale_factor = actual_duration / recorded_duration
        else:
            scale_factor = 1.0
        
        print(f"  🔧 需要修复，缩放因子: {scale_factor:.6f}")
        
        # 创建备份
        backup_file = timestamp_file + '.backup'
        shutil.copy2(timestamp_file, backup_file)
        print(f"  📁 已创建备份: {backup_file}")
        
        # 缩放时间戳
        fixed_timestamps = []
        for ts in character_timestamps:
            scaled_start = ts['start_time'] * scale_factor
            scaled_end = ts['end_time'] * scale_factor
            
            # 确保不超出实际音频时长
            if scaled_end > actual_duration:
                scaled_end = actual_duration
            if scaled_start > actual_duration:
                scaled_start = max(0, actual_duration - 0.01)
            
            fixed_timestamps.append({
                'character': ts['character'],
                'start_time': scaled_start,
                'end_time': scaled_end
            })
        
        # 更新时间戳数据
        timestamp_data['character_timestamps'] = fixed_timestamps
        timestamp_data['duration'] = actual_duration
        
        # 保存修复后的文件
        with open(timestamp_file, 'w', encoding='utf-8') as f:
            json.dump(timestamp_data, f, ensure_ascii=False, indent=2)
        
        print(f"  ✅ 时间戳文件已修复")
        return True
        
    except Exception as e:
        print(f"  ❌ 修复失败: {e}")
        return False

def fix_timestamps_batch(data_dir):
    """
    批量修复指定目录下所有章节的时间戳问题
    """
    print(f"=== 批量修复时间戳数据 ===")
    print(f"目标目录: {data_dir}")
    
    if not os.path.exists(data_dir):
        print(f"错误: 目录不存在 {data_dir}")
        return False
    
    # 查找所有章节目录
    chapter_dirs = []
    for item in os.listdir(data_dir):
        item_path = os.path.join(data_dir, item)
        if os.path.isdir(item_path) and item.startswith('chapter_'):
            chapter_dirs.append(item_path)
    
    if not chapter_dirs:
        print(f"错误: 在 {data_dir} 中没有找到章节目录")
        return False
    
    chapter_dirs.sort()
    print(f"找到 {len(chapter_dirs)} 个章节目录")
    
    total_fixed = 0
    total_files = 0
    
    # 处理每个章节
    for chapter_dir in chapter_dirs:
        chapter_name = os.path.basename(chapter_dir)
        print(f"\n--- 处理章节: {chapter_name} ---")
        
        # 查找时间戳文件和对应的音频文件
        timestamp_files = [f for f in os.listdir(chapter_dir) if f.endswith('_timestamps.json')]
        
        if not timestamp_files:
            print(f"  警告: 没有找到时间戳文件")
            continue
        
        for timestamp_file in sorted(timestamp_files):
            timestamp_path = os.path.join(chapter_dir, timestamp_file)
            
            # 找到对应的音频文件
            base_name = timestamp_file.replace('_timestamps.json', '')
            audio_file = base_name + '.mp3'
            audio_path = os.path.join(chapter_dir, audio_file)
            
            print(f"\n  处理: {timestamp_file}")
            total_files += 1
            
            if not os.path.exists(audio_path):
                print(f"  ❌ 找不到对应的音频文件: {audio_file}")
                continue
            
            if fix_timestamps_file(timestamp_path, audio_path):
                total_fixed += 1
    
    print(f"\n=== 修复完成 ===")
    print(f"总共处理文件: {total_files}")
    print(f"成功修复文件: {total_fixed}")
    print(f"修复成功率: {total_fixed/total_files*100:.1f}%" if total_files > 0 else "无文件处理")
    
    return total_fixed > 0

def clean_empty_videos(data_dir):
    """
    清理空的视频文件
    """
    print(f"\n=== 清理空视频文件 ===")
    
    empty_files = []
    
    for root, dirs, files in os.walk(data_dir):
        for file in files:
            if file.endswith('.mp4'):
                file_path = os.path.join(root, file)
                if os.path.getsize(file_path) == 0:
                    empty_files.append(file_path)
    
    if empty_files:
        print(f"找到 {len(empty_files)} 个空视频文件:")
        for file_path in empty_files:
            rel_path = os.path.relpath(file_path, data_dir)
            print(f"  - {rel_path}")
        
        # 删除空文件
        for file_path in empty_files:
            try:
                os.remove(file_path)
                print(f"  ✅ 已删除: {os.path.relpath(file_path, data_dir)}")
            except Exception as e:
                print(f"  ❌ 删除失败 {os.path.relpath(file_path, data_dir)}: {e}")
    else:
        print(f"✓ 没有发现空视频文件")

def main():
    """
    主函数
    """
    if len(sys.argv) < 2:
        print("使用方法: python fix_timestamps_batch.py <数据目录>")
        print("示例: python fix_timestamps_batch.py data/002")
        return
    
    data_dir = sys.argv[1]
    
    # 修复时间戳
    success = fix_timestamps_batch(data_dir)
    
    # 清理空视频文件
    clean_empty_videos(data_dir)
    
    if success:
        print(f"\n🎉 批量修复完成！现在可以重新运行: python generate.py concat {data_dir}")
    else:
        print(f"\n❌ 修复过程中遇到问题，请检查错误信息")

if __name__ == '__main__':
    main()