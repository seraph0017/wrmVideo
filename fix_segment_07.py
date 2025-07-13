#!/usr/bin/env python3
# -*- coding: utf-8 -*-

import json
import os
import sys
import subprocess

# 添加项目根目录到Python路径
sys.path.append('/Users/xunan/Projects/wrmProject')

from generate import split_text_by_timestamps, create_video_segment_with_timing

def fix_segment_07():
    """
    修复第7个段落的问题：调整时间戳以匹配实际音频时长
    """
    base_dir = '/Users/xunan/Projects/wrmProject/data/002/chapter_001'
    timestamp_file = os.path.join(base_dir, 'chapter_001_narration_05_timestamps.json')
    audio_file = os.path.join(base_dir, 'chapter_001_narration_05.mp3')
    
    try:
        # 获取实际音频时长
        cmd = ['ffprobe', '-v', 'quiet', '-print_format', 'json', '-show_format', audio_file]
        result = subprocess.run(cmd, capture_output=True, text=True)
        if result.returncode != 0:
            print(f"无法获取音频信息: {result.stderr}")
            return False
        
        info = json.loads(result.stdout)
        actual_duration = float(info['format']['duration'])
        print(f"实际音频时长: {actual_duration:.6f}s")
        
        # 读取时间戳文件
        with open(timestamp_file, 'r', encoding='utf-8') as f:
            timestamp_data = json.load(f)
        
        text = timestamp_data.get('text', '')
        character_timestamps = timestamp_data.get('character_timestamps', [])
        recorded_duration = timestamp_data.get('duration', 0)
        
        print(f"记录的音频时长: {recorded_duration:.6f}s")
        print(f"时长差异: {abs(actual_duration - recorded_duration):.6f}s")
        
        # 方案1：按比例缩放所有时间戳
        scale_factor = actual_duration / recorded_duration
        print(f"\n=== 方案1：按比例缩放时间戳 ===")
        print(f"缩放因子: {scale_factor:.6f}")
        
        # 创建缩放后的时间戳
        scaled_timestamps = []
        for ts in character_timestamps:
            scaled_start = ts['start_time'] * scale_factor
            scaled_end = ts['end_time'] * scale_factor
            
            # 确保不超出实际音频时长
            if scaled_end > actual_duration:
                scaled_end = actual_duration
            if scaled_start > actual_duration:
                scaled_start = actual_duration - 0.01  # 至少保留0.01秒
            
            scaled_timestamps.append({
                'character': ts['character'],
                'start_time': scaled_start,
                'end_time': scaled_end
            })
        
        # 使用缩放后的时间戳重新分割文本
        segments = split_text_by_timestamps(text, scaled_timestamps, max_chars_per_segment=40)
        print(f"缩放后分割段落数量: {len(segments)}")
        
        # 检查第7个段落
        if len(segments) >= 7:
            segment_7 = segments[6]
            segment_text, start_time, end_time = segment_7
            
            print(f"\n=== 修复后的第7个段落 ===")
            print(f"文本: '{segment_text}'")
            print(f"开始时间: {start_time:.6f}s")
            print(f"结束时间: {end_time:.6f}s")
            print(f"持续时间: {end_time - start_time:.6f}s")
            print(f"是否在有效范围内: {end_time <= actual_duration}")
            
            if end_time <= actual_duration:
                # 尝试重新生成第7个段落的视频
                image_file = os.path.join(base_dir, 'chapter_001_image_05.jpg')
                fixed_output = os.path.join(base_dir, 'chapter_001_narration_05_segment_07_fixed.mp4')
                
                print(f"\n=== 重新生成第7个段落视频 ===")
                print(f"输出路径: {fixed_output}")
                
                # 删除已存在的文件
                if os.path.exists(fixed_output):
                    os.remove(fixed_output)
                
                success = create_video_segment_with_timing(
                    image_file,
                    audio_file,
                    segment_text,
                    start_time,
                    end_time,
                    fixed_output,
                    is_first_segment=False
                )
                
                if success and os.path.exists(fixed_output):
                    size = os.path.getsize(fixed_output)
                    print(f"✓ 修复成功！生成的视频大小: {size} 字节")
                    
                    # 可选：替换原始的空文件
                    original_file = os.path.join(base_dir, 'chapter_001_narration_05_segment_07.mp4')
                    backup_file = os.path.join(base_dir, 'chapter_001_narration_05_segment_07_backup.mp4')
                    
                    # 备份原始空文件
                    if os.path.exists(original_file):
                        os.rename(original_file, backup_file)
                        print(f"原始空文件已备份为: {backup_file}")
                    
                    # 复制修复的文件
                    import shutil
                    shutil.copy2(fixed_output, original_file)
                    print(f"✓ 已替换原始文件: {original_file}")
                    
                    return True
                else:
                    print(f"✗ 修复失败")
                    return False
            else:
                print(f"✗ 修复后的时间戳仍然超出音频范围")
                return False
        else:
            print(f"✗ 缩放后没有第7个段落")
            return False
            
    except Exception as e:
        print(f"修复过程中发生错误: {e}")
        import traceback
        traceback.print_exc()
        return False

if __name__ == '__main__':
    success = fix_segment_07()
    if success:
        print(f"\n🎉 第7个段落修复成功！")
    else:
        print(f"\n❌ 第7个段落修复失败")