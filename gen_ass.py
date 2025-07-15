#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
ASS字幕生成器
根据timestamps.json文件生成ASS格式字幕文件
"""

import os
import json
import argparse
import re
from typing import List, Dict, Any
import jieba
import jieba.posseg as pseg

def format_time_for_ass(seconds: float) -> str:
    """将秒数转换为ASS时间格式 (H:MM:SS.CC)"""
    hours = int(seconds // 3600)
    minutes = int((seconds % 3600) // 60)
    secs = seconds % 60
    return f"{hours}:{minutes:02d}:{secs:05.2f}"

def identify_key_word(text: str) -> str:
    """识别文本中的关键词用于高亮显示"""
    if not text:
        return ""
    
    # 移除标点符号进行分词
    clean_text = re.sub(r'[，。！？；：、]', '', text)
    
    # 使用jieba进行词性标注
    words = pseg.cut(clean_text)
    
    # 定义关键词优先级
    priority_pos = {
        'n': 3,    # 名词
        'nr': 4,   # 人名
        'ns': 4,   # 地名
        'nt': 3,   # 机构名
        'nz': 3,   # 其他专名
        'v': 2,    # 动词
        'vn': 2,   # 名动词
        'a': 2,    # 形容词
        'ad': 1,   # 副形词
        'an': 2,   # 名形词
    }
    
    candidates = []
    for word, pos in words:
        if len(word) >= 2:  # 至少2个字符
            priority = priority_pos.get(pos, 0)
            if priority > 0:
                candidates.append((word, priority, len(word)))
    
    if not candidates:
        # 如果没有找到合适的词，选择最长的词
        words_only = [word for word, pos in pseg.cut(clean_text) if len(word) >= 2]
        if words_only:
            return max(words_only, key=len)
        return ""
    
    # 按优先级和长度排序，选择最佳关键词
    candidates.sort(key=lambda x: (x[1], x[2]), reverse=True)
    return candidates[0][0]

def split_text_naturally(text: str, max_length: int = 15) -> List[str]:
    """自然切分文本，基于语义和语法结构进行智能断句"""
    if not text:
        return []
    
    # 移除多余空格
    text = re.sub(r'\s+', '', text)
    
    segments = []
    current_segment = ""
    current_char_count = 0
    
    # 定义语义切分优先级
    strong_breaks = '。！？'  # 强制断句标点
    medium_breaks = '，；'    # 中等优先级断句标点
    weak_breaks = '：、'      # 弱断句标点
    
    # 常见的语义单元模式
    semantic_patterns = [
        r'(\w+)，(\w+)，',  # 并列结构
        r'(\w{2,4})地',     # 副词结构
        r'(\w{2,4})着',     # 进行时结构
        r'(\w{2,4})的',     # 定语结构
    ]
    
    i = 0
    while i < len(text):
        char = text[i]
        current_segment += char
        
        # 只计算非标点符号的字符
        if char not in '，。！？；：、':
            current_char_count += 1
        
        # 检查是否到达切分点
        should_split = False
        split_priority = 0
        
        # 强制断句点（最高优先级）
        if char in strong_breaks:
            should_split = True
            split_priority = 3
        
        # 中等优先级断句点
        elif char in medium_breaks:
            # 检查是否形成完整的语义单元
            if current_char_count >= 8:  # 至少8个字符才考虑在逗号处断句
                should_split = True
                split_priority = 2
        
        # 弱断句点
        elif char in weak_breaks and current_char_count >= 10:
            should_split = True
            split_priority = 1
        
        # 长度限制检查
        if current_char_count >= max_length:
            if not should_split:
                # 寻找最近的合适断句点
                for j in range(len(current_segment) - 1, max(0, len(current_segment) - 5), -1):
                    if current_segment[j] in medium_breaks + weak_breaks:
                        # 在最近的标点处断句
                        segments.append(current_segment[:j+1].strip())
                        current_segment = current_segment[j+1:]
                        current_char_count = len([c for c in current_segment if c not in '，。！？；：、'])
                        should_split = False
                        break
                else:
                    # 没找到合适断句点，强制断句
                    should_split = True
                    split_priority = 0
        
        # 避免过短的段落（少于3个字符）
        if should_split and current_char_count >= 3:
            segments.append(current_segment.strip())
            current_segment = ""
            current_char_count = 0
        elif should_split and current_char_count < 3:
            # 如果当前段落太短，继续累积
            should_split = False
        
        i += 1
    
    # 添加剩余部分
    if current_segment.strip():
        # 如果最后一段太短，尝试与前一段合并
        final_char_count = len([c for c in current_segment if c not in '，。！？；：、'])
        if segments and final_char_count <= 2:
            segments[-1] += current_segment.strip()
        else:
            segments.append(current_segment.strip())
    
    return segments

def calculate_segment_timestamps(segments: List[str], character_timestamps: List[Dict]) -> List[Dict]:
    """为每个文本段计算时间戳"""
    segment_timestamps = []
    char_index = 0
    
    for segment in segments:
        if char_index >= len(character_timestamps):
            break
            
        # 计算段落的开始时间
        start_time = character_timestamps[char_index]['start_time']
        
        # 计算段落中字符的数量（包括标点符号）
        segment_length = len(segment)
        end_char_index = char_index + segment_length - 1
        
        # 确保不超出数组边界
        end_char_index = min(end_char_index, len(character_timestamps) - 1)
        end_time = character_timestamps[end_char_index]['end_time']
        
        segment_timestamps.append({
            'text': segment,
            'start_time': start_time,
            'end_time': end_time
        })
        
        # 更新字符索引
        char_index += segment_length
    
    return segment_timestamps

def generate_ass_content(segment_timestamps: List[Dict], title: str = "Generated Subtitle") -> str:
    """生成ASS格式内容"""
    # ASS文件头部
    ass_header = f"""[Script Info]
Title: {title}
ScriptType: v4.00+
WrapStyle: 0
ScaledBorderAndShadow: yes
YCbCr Matrix: TV.601
PlayResX: 1920
PlayResY: 1080

[V4+ Styles]
Format: Name, Fontname, Fontsize, PrimaryColour, SecondaryColour, OutlineColour, BackColour, Bold, Italic, Underline, StrikeOut, ScaleX, ScaleY, Spacing, Angle, BorderStyle, Outline, Shadow, Alignment, MarginL, MarginR, MarginV, Encoding
Style: Default,Microsoft YaHei,48,&H00FFFFFF,&H000000FF,&H00000000,&H80000000,0,0,0,0,100,100,0,0,1,2,2,2,10,10,360,1
Style: Highlight,Microsoft YaHei,48,&H0000FFFF,&H000000FF,&H00000000,&H80000000,1,0,0,0,100,100,0,0,1,2,2,2,10,10,360,1

[Events]
Format: Layer, Start, End, Style, Name, MarginL, MarginR, MarginV, Effect, Text
"""
    
    # 生成字幕事件
    events = []
    for i, segment in enumerate(segment_timestamps):
        start_time = format_time_for_ass(segment['start_time'])
        end_time = format_time_for_ass(segment['end_time'])
        text = segment['text']
        
        # 识别关键词并添加高亮效果
        key_word = identify_key_word(text)
        if key_word and key_word in text:
            # 使用ASS标签为关键词添加黄色加粗效果
            highlighted_text = text.replace(key_word, f"{{\\c&H0000FFFF&\\b1}}{key_word}{{\\c&H00FFFFFF&\\b0}}", 1)
        else:
            highlighted_text = text
        
        event_line = f"Dialogue: 0,{start_time},{end_time},Default,,0,0,0,,{highlighted_text}"
        events.append(event_line)
    
    return ass_header + "\n".join(events)

def process_chapter(chapter_path: str, max_length: int = 15) -> bool:
    """处理单个章节"""
    chapter_name = os.path.basename(chapter_path)
    print(f"\n=== 处理章节: {chapter_name} ===")
    
    # 查找timestamps文件
    timestamps_file = None
    for file in os.listdir(chapter_path):
        if file.endswith('_timestamps.json') and 'narration_01' in file:
            timestamps_file = os.path.join(chapter_path, file)
            break
    
    if not timestamps_file:
        print(f"❌ 未找到timestamps文件")
        return False
    
    try:
        # 读取timestamps数据
        with open(timestamps_file, 'r', encoding='utf-8') as f:
            data = json.load(f)
        
        original_text = data.get('text', '')
        character_timestamps = data.get('character_timestamps', [])
        
        if not original_text or not character_timestamps:
            print(f"❌ timestamps文件格式不正确")
            return False
        
        print(f"原始文本: {original_text}")
        print(f"字符数: {len(original_text)}")
        
        # 自然切分文本
        segments = split_text_naturally(original_text, max_length)
        print(f"分割为 {len(segments)} 段:")
        
        for i, segment in enumerate(segments, 1):
            char_count = len([c for c in segment if c not in '，。！？；：、'])
            key_word = identify_key_word(segment)
            if key_word:
                print(f"  {i}. {segment} ({char_count}字) [关键词: {key_word}]")
            else:
                print(f"  {i}. {segment} ({char_count}字) [无关键词]")
        
        # 计算时间戳
        segment_timestamps = calculate_segment_timestamps(segments, character_timestamps)
        
        # 生成ASS内容
        ass_content = generate_ass_content(segment_timestamps, f"{chapter_name} Subtitle")
        
        # 保存ASS文件
        ass_filename = f"{chapter_name}_narration_01.ass"
        ass_filepath = os.path.join(chapter_path, ass_filename)
        
        with open(ass_filepath, 'w', encoding='utf-8') as f:
            f.write(ass_content)
        
        print(f"✓ ASS文件生成成功: {ass_filename}")
        return True
        
    except Exception as e:
        print(f"❌ 处理章节失败: {str(e)}")
        return False

def main():
    """主函数"""
    parser = argparse.ArgumentParser(description='生成ASS字幕文件')
    parser.add_argument('data_dir', help='数据目录路径')
    parser.add_argument('--max-length', type=int, default=15, help='每段最大字符数（默认15）')
    
    args = parser.parse_args()
    
    if not os.path.exists(args.data_dir):
        print(f"❌ 数据目录不存在: {args.data_dir}")
        return
    
    # 查找所有章节目录
    chapter_dirs = []
    for item in os.listdir(args.data_dir):
        item_path = os.path.join(args.data_dir, item)
        if os.path.isdir(item_path) and item.startswith('chapter'):
            chapter_dirs.append(item_path)
    
    chapter_dirs.sort()
    
    if not chapter_dirs:
        print(f"❌ 在 {args.data_dir} 中未找到章节目录")
        return
    
    print(f"找到 {len(chapter_dirs)} 个章节目录")
    
    # 处理每个章节
    success_count = 0
    for chapter_dir in chapter_dirs:
        if process_chapter(chapter_dir, args.max_length):
            success_count += 1
    
    print(f"\n=== 处理完成 ===")
    print(f"成功: {success_count}/{len(chapter_dirs)}")
    
    if success_count == len(chapter_dirs):
        print("✓ 所有章节处理成功！")
    else:
        print(f"⚠️  有 {len(chapter_dirs) - success_count} 个章节处理失败")

if __name__ == '__main__':
    main()