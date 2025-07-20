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

def is_person_name(text: str, position: int) -> bool:
    """检查指定位置是否为人名"""
    if position < 0 or position >= len(text):
        return False
    
    # 常见的人名模式
    name_patterns = [
        r'[\u4e00-\u9fff]{2,4}',  # 2-4个汉字的姓名
        r'[A-Z][a-z]+',           # 英文名
    ]
    
    # 检查当前位置前后的文本是否符合人名模式
    for pattern in name_patterns:
        matches = list(re.finditer(pattern, text))
        for match in matches:
            if match.start() <= position <= match.end():
                return True
    
    return False

def split_text_naturally(text: str, max_length: int = 20) -> List[str]:
    """自然切分文本，去掉标点符号用空格代替，在空格处积极分行，避免从人名处断句"""
    if not text:
        return []
    
    # 移除多余空格
    text = re.sub(r'\s+', '', text)
    
    # 将标点符号替换为空格，但保留句号、感叹号、问号作为强制断句点
    processed_text = ""
    for char in text:
        if char in '，；：、':
            processed_text += ' '  # 用空格替换标点符号
        else:
            processed_text += char
    
    segments = []
    current_segment = ""
    current_char_count = 0
    
    # 定义强制断句标点
    strong_breaks = '。！？'
    # 设置较短的分行阈值，避免句子过长
    soft_break_threshold = max_length * 0.3  # 约3-4字时开始考虑在空格处分行
    
    i = 0
    while i < len(processed_text):
        char = processed_text[i]
        current_segment += char
        
        # 计算实际字符数（不包括空格和标点）
        if char not in ' 。！？':
            current_char_count += 1
        
        # 检查是否到达强制断句点
        should_split = False
        
        # 强制断句点（句号、感叹号、问号）
        if char in strong_breaks:
            should_split = True
        
        # 在空格处进行软分行（当达到软阈值时）
        elif char == ' ' and current_char_count >= soft_break_threshold:
            # 检查这个位置是否在人名中间
            original_pos = i - len(current_segment) + 1
            if not is_person_name(text, original_pos):
                # 在空格处分行
                segments.append(current_segment.strip())
                current_segment = ""
                current_char_count = 0
                i += 1
                continue
        
        # 硬性长度限制检查
        elif current_char_count >= max_length:
            # 寻找最近的空格位置进行断句，但避免从人名处断句
            best_split_pos = -1
            
            # 从当前位置向前查找合适的断句点
            for j in range(len(current_segment) - 1, max(0, len(current_segment) - 8), -1):
                if current_segment[j] == ' ':
                    # 检查这个位置是否在人名中间
                    original_pos = i - (len(current_segment) - 1 - j)
                    if not is_person_name(text, original_pos):
                        best_split_pos = j
                        break
            
            if best_split_pos > 0:
                # 在找到的空格处断句
                segments.append(current_segment[:best_split_pos].strip())
                current_segment = current_segment[best_split_pos:].strip()
                current_char_count = len([c for c in current_segment if c not in ' 。！？'])
            else:
                # 没找到合适的断句点，强制断句
                should_split = True
        
        # 执行断句
        if should_split and current_char_count >= 3:  # 避免过短的段落
            segments.append(current_segment.strip())
            current_segment = ""
            current_char_count = 0
        
        i += 1
    
    # 添加剩余部分
    if current_segment.strip():
        # 如果最后一段太短，尝试与前一段合并
        final_char_count = len([c for c in current_segment if c not in ' 。！？'])
        if segments and final_char_count <= 2:
            segments[-1] += ' ' + current_segment.strip()
        else:
            segments.append(current_segment.strip())
    
    return segments

def calculate_segment_timestamps(segments: List[str], character_timestamps: List[Dict], original_text: str) -> List[Dict]:
    """为每个文本段计算时间戳"""
    segment_timestamps = []
    
    # 创建一个去除标点符号的原文，用于匹配
    clean_original = ''.join(char for char in original_text if char not in '，。！？；：、"')
    
    # 当前在clean_original中的位置
    current_pos = 0
    
    for segment in segments:
        if current_pos >= len(character_timestamps):
            break
            
        # 清理段落文本（移除空格和引号）
        clean_segment = segment.strip().replace(' ', '').replace('"', '')
        
        if not clean_segment:  # 跳过空段落
            continue
        
        # 在clean_original中查找这个段落
        segment_start_in_clean = clean_original.find(clean_segment, current_pos)
        
        if segment_start_in_clean == -1:
            # 如果找不到完整匹配，尝试查找段落的前几个字符
            for i in range(min(len(clean_segment), 5), 0, -1):
                partial_segment = clean_segment[:i]
                segment_start_in_clean = clean_original.find(partial_segment, current_pos)
                if segment_start_in_clean != -1:
                    clean_segment = partial_segment
                    break
        
        if segment_start_in_clean == -1:
            # 仍然找不到，跳过这个段落
            continue
        
        # 计算在原文中的实际位置
        # 需要考虑标点符号的存在
        original_start_pos = 0
        clean_char_count = 0
        
        # 找到对应的原文位置
        for i, char in enumerate(original_text):
            if char not in '，。！？；：、"':
                if clean_char_count == segment_start_in_clean:
                    original_start_pos = i
                    break
                clean_char_count += 1
        
        # 计算结束位置
        segment_length = len(clean_segment)
        original_end_pos = original_start_pos
        found_chars = 0
        
        for i in range(original_start_pos, len(original_text)):
            if original_text[i] not in '，。！？；：、"':
                found_chars += 1
                if found_chars == segment_length:
                    original_end_pos = i
                    break
        
        # 获取时间戳
        if (original_start_pos < len(character_timestamps) and 
            original_end_pos < len(character_timestamps)):
            
            start_time = character_timestamps[original_start_pos]['start_time']
            end_time = character_timestamps[original_end_pos]['end_time']
            
            segment_timestamps.append({
                'text': segment.strip(),
                'start_time': start_time,
                'end_time': end_time
            })
        
        # 更新当前位置
        current_pos = segment_start_in_clean + segment_length
    
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

def process_chapter(chapter_path: str, max_length: int = 12) -> bool:
    """处理单个章节"""
    chapter_name = os.path.basename(chapter_path)
    print(f"\n=== 处理章节: {chapter_name} ===")
    
    # 查找所有timestamps文件
    timestamps_files = []
    for file in os.listdir(chapter_path):
        if file.endswith('_timestamps.json') and 'narration' in file:
            timestamps_files.append(os.path.join(chapter_path, file))
    
    timestamps_files.sort()  # 按文件名排序
    
    if not timestamps_files:
        print(f"❌ 未找到timestamps文件")
        return False
    
    print(f"找到 {len(timestamps_files)} 个timestamps文件")
    
    success_count = 0
    for timestamps_file in timestamps_files:
        # 从文件名提取narration编号
        filename = os.path.basename(timestamps_file)
        narration_match = re.search(r'narration_(\d+)', filename)
        if narration_match:
            narration_num = narration_match.group(1)
        else:
            narration_num = "01"
        
        print(f"\n--- 处理 {filename} ---")
        
        try:
            # 读取timestamps数据
            with open(timestamps_file, 'r', encoding='utf-8') as f:
                data = json.load(f)
            
            original_text = data.get('text', '')
            character_timestamps = data.get('character_timestamps', [])
            
            if not original_text or not character_timestamps:
                print(f"❌ timestamps文件格式不正确")
                continue
            
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
            segment_timestamps = calculate_segment_timestamps(segments, character_timestamps, original_text)
            
            # 生成ASS内容
            ass_content = generate_ass_content(segment_timestamps, f"{chapter_name} Narration {narration_num} Subtitle")
            
            # 保存ASS文件
            ass_filename = f"{chapter_name}_narration_{narration_num}.ass"
            ass_filepath = os.path.join(chapter_path, ass_filename)
            
            with open(ass_filepath, 'w', encoding='utf-8') as f:
                f.write(ass_content)
            
            print(f"✓ ASS文件生成成功: {ass_filename}")
            success_count += 1
            
        except Exception as e:
            print(f"❌ 处理文件失败: {str(e)}")
            continue
    
    print(f"\n章节 {chapter_name} 处理完成: {success_count}/{len(timestamps_files)} 个文件成功")
    return success_count > 0

def main():
    """主函数"""
    parser = argparse.ArgumentParser(description='生成ASS字幕文件')
    parser.add_argument('data_dir', help='数据目录路径')
    parser.add_argument('--max-length', type=int, default=12, help='每段最大字符数（默认12）')
    
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