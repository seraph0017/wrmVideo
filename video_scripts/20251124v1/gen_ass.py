#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
ASS字幕生成器
根据timestamps.json文件生成ASS格式字幕文件

使用方法:
python video_scripts/20251124v1/gen_ass.py data/xxx
python video_scripts/20251124v1/gen_ass.py data/xxx --chapter chapter_001
"""

import os
import sys
import json
import argparse
import re
from typing import List, Dict, Any

# 添加项目根目录到Python路径
# 当前文件路径: video_scripts/20251124v1/gen_ass.py
# 项目根目录: video_scripts/20251124v1/gen_ass.py -> ../../
current_dir = os.path.dirname(os.path.abspath(__file__))
project_root = os.path.dirname(os.path.dirname(current_dir))
if project_root not in sys.path:
    sys.path.insert(0, project_root)

import jieba
import jieba.posseg as pseg

def format_time_for_ass(seconds: float) -> str:
    """将秒数转换为ASS时间格式 (H:MM:SS.CC)"""
    hours = int(seconds // 3600)
    minutes = int((seconds % 3600) // 60)
    secs = seconds % 60
    return f"{hours}:{minutes:02d}:{secs:05.2f}"

def identify_key_word(text: str) -> str:
    """识别文本中的关键词（人名、地名等）"""
    # 使用jieba进行词性标注
    words = pseg.cut(text)
    
    # 优先级：人名 > 地名 > 机构名 > 其他专有名词
    priority_tags = ['nr', 'ns', 'nt', 'nz']
    
    candidates = []
    for word, flag in words:
        if len(word) >= 2:  # 至少2个字符
            if flag in priority_tags:
                candidates.append((word, priority_tags.index(flag)))
    
    if candidates:
        # 按优先级排序，返回优先级最高的词
        candidates.sort(key=lambda x: x[1])
        return candidates[0][0]
    
    return ""

def split_text_naturally(text: str, max_length: int = 12) -> List[str]:
    """按句子自然分割文本，确保每句话尽量完整，对于过长句子选择自然断开位置"""
    # 首先按句子分割，保留原始标点符号用于句子识别
    sentence_endings = ['。', '！', '？', '；', '…', '：']
    
    # 分割成句子
    sentences = []
    current_sentence = ""
    
    for char in text:
        current_sentence += char
        if char in sentence_endings:
            if current_sentence.strip():
                sentences.append(current_sentence.strip())
            current_sentence = ""
    
    # 添加最后一个句子（如果没有以句号结尾）
    if current_sentence.strip():
        sentences.append(current_sentence.strip())
    
    # 如果没有明显的句子分割，按逗号等次级标点分割
    if len(sentences) == 1 and len(sentences[0]) > max_length * 2:
        secondary_endings = ['，', '、', '；']
        temp_sentences = []
        for sentence in sentences:
            current_part = ""
            for char in sentence:
                current_part += char
                if char in secondary_endings:
                    if current_part.strip():
                        temp_sentences.append(current_part.strip())
                    current_part = ""
            if current_part.strip():
                temp_sentences.append(current_part.strip())
        sentences = temp_sentences
    
    segments = []
    
    for sentence in sentences:
        # 清理句子，去除标点符号用于长度计算
        cleaned_sentence = clean_subtitle_text(sentence)
        
        if len(cleaned_sentence) <= max_length:
            # 句子长度合适，直接添加
            segments.append(cleaned_sentence)
        else:
            # 句子太长，需要智能分割
            sentence_segments = _split_long_sentence_naturally(cleaned_sentence, max_length)
            segments.extend(sentence_segments)
    
    # 过滤空段落和单字符段落
    filtered_segments = []
    for i, seg in enumerate(segments):
        if not seg.strip():
            continue
        
        # 检查是否为单字符段落
        clean_seg = clean_subtitle_text(seg)
        if len(clean_seg) == 1:
            # 单字符段落，尝试与前一个或后一个段落合并
            if filtered_segments:
                # 与前一个段落合并
                filtered_segments[-1] += seg
            elif i + 1 < len(segments) and segments[i + 1].strip():
                # 与下一个段落合并
                segments[i + 1] = seg + segments[i + 1]
            else:
                # 无法合并，保留单字符（避免丢失内容）
                filtered_segments.append(seg)
        else:
            filtered_segments.append(seg)
    
    return filtered_segments

def _split_long_sentence_naturally(sentence: str, max_length: int) -> List[str]:
    """智能分割过长的句子，选择自然的断开位置"""
    segments = []
    
    # 定义自然断开位置的优先级（数字越小优先级越高）
    break_points = {
        '，': 1,  # 逗号 - 最自然的断开位置
        '、': 2,  # 顿号
        '；': 3,  # 分号
        '：': 4,  # 冒号
        '的': 5,  # "的"字后面
        '了': 6,  # "了"字后面
        '着': 7,  # "着"字后面
        '过': 8,  # "过"字后面
        '与': 9,  # "与"字后面
        '和': 10, # "和"字后面
        '或': 11, # "或"字后面
        '但': 12, # "但"字前面
        '而': 13, # "而"字前面
        '却': 14, # "却"字前面
        '则': 15, # "则"字前面
    }
    
    # 使用jieba分词获取词汇边界
    words = list(jieba.cut(sentence, cut_all=False))
    current_segment = ""
    
    for word in words:
        clean_word = clean_subtitle_text(word)
        if not clean_word:
            continue
        
        potential_segment = current_segment + clean_word
        
        if len(potential_segment) <= max_length:
            current_segment = potential_segment
        else:
            # 超出长度限制，需要断开
            if current_segment:
                # 尝试在当前段落中找到最佳断开位置
                best_segment = _find_best_break_point(current_segment, max_length, break_points)
                if best_segment:
                    segments.append(best_segment['before'])
                    current_segment = best_segment['after'] + clean_word
                else:
                    # 没有找到合适的断开位置，直接保存当前段落
                    segments.append(current_segment)
                    current_segment = clean_word
            else:
                current_segment = clean_word
            
            # 如果单个词过长，强制按字符分割
            if len(current_segment) > max_length:
                char_segments = _split_by_characters(current_segment, max_length)
                segments.extend(char_segments[:-1])
                current_segment = char_segments[-1] if char_segments else ""
    
    # 添加最后一个段落
    if current_segment:
        segments.append(current_segment)
    
    return segments

def _find_best_break_point(text: str, max_length: int, break_points: dict) -> dict:
    """在文本中找到最佳的自然断开位置"""
    best_break = None
    best_priority = float('inf')
    
    # 从理想长度位置向前搜索自然断开点
    search_start = min(max_length - 1, len(text) - 1)
    search_end = max(0, max_length // 2)  # 至少保留一半长度
    
    for i in range(search_start, search_end - 1, -1):
        char = text[i]
        
        if char in break_points:
            priority = break_points[char]
            if priority < best_priority:
                best_priority = priority
                # 对于标点符号，断开位置在标点符号之后
                if char in ['，', '、', '；', '：']:
                    break_pos = i + 1
                else:
                    # 对于"的"、"了"等字，断开位置也在字后面
                    break_pos = i + 1
                
                best_break = {
                    'before': text[:break_pos].strip(),
                    'after': text[break_pos:].strip(),
                    'position': break_pos,
                    'priority': priority
                }
    
    return best_break

def _split_by_characters(text: str, max_length: int) -> List[str]:
    """按字符强制分割文本，确保每段不超过最大长度"""
    if len(text) <= max_length:
        return [text]
    
    segments = []
    start = 0
    
    while start < len(text):
        end = start + max_length
        if end >= len(text):
            # 最后一段
            segments.append(text[start:])
            break
        else:
            # 分割当前段
            segments.append(text[start:end])
            start = end
    
    return segments

def _is_inside_paired_symbols(text: str, paired_symbols: dict) -> bool:
    """检查文本是否在成对符号内部（未闭合）"""
    stack = []
    for char in text:
        if char in paired_symbols:
            stack.append(paired_symbols[char])
        elif char in paired_symbols.values():
            if stack and stack[-1] == char:
                stack.pop()
    return len(stack) > 0

def _find_safe_split_point(text: str, max_length: int, punctuation_priority: dict, paired_symbols: dict) -> tuple:
    """寻找安全的分割点，确保不破坏语义完整性"""
    if len(text) <= max_length:
        return None
    
    best_split_pos = -1
    best_priority = float('inf')
    
    # 从理想长度位置向前搜索
    search_start = min(max_length, len(text) - 1)
    search_end = max(0, search_start - 8)  # 向前搜索8个字符
    
    for i in range(search_start, search_end, -1):
        char = text[i]
        
        # 检查是否为合适的分割点
        if char in punctuation_priority:
            # 检查分割后是否破坏成对符号
            left_part = text[:i + 1]
            if not _is_inside_paired_symbols(left_part, paired_symbols):
                priority = punctuation_priority[char]
                if priority < best_priority:
                    best_priority = priority
                    best_split_pos = i
    
    if best_split_pos != -1:
        left_part = text[:best_split_pos + 1]
        right_part = text[best_split_pos + 1:]
        return (left_part, right_part)
    
    return None

def _merge_semantic_words(words: List[str], semantic_patterns: List[List[str]]) -> List[str]:
    """合并语义相关的词汇"""
    merged_words = []
    i = 0
    
    while i < len(words):
        current_word = words[i]
        merged = False
        
        # 检查是否与下一个词语义相关
        if i + 1 < len(words):
            next_word = words[i + 1]
            for pattern in semantic_patterns:
                if len(pattern) == 2 and pattern[0] == current_word and pattern[1] == next_word:
                    merged_words.append(current_word + next_word)
                    i += 2
                    merged = True
                    break
        
        if not merged:
            merged_words.append(current_word)
            i += 1
    
    return merged_words

def _is_semantic_incomplete(current_segment: str, next_word: str) -> bool:
    """检查当前段落是否语义不完整，需要与下一个词合并"""
    # 检查是否以不完整的结构结尾
    incomplete_endings = [
        '决定', '联手', '听得', '感叹', '皆是', '与此', '终于', '按捺',
        '对视', '眼中', '杀意', '兄弟', '血海', '宋式', '死亡'
    ]
    
    for ending in incomplete_endings:
        if current_segment.endswith(ending):
            return True
    
    # 检查是否以动词结尾但缺少宾语
    if current_segment.endswith(('攻', '进', '听', '看', '说', '做', '来', '去')):
        return True
    
    return False

def _optimize_segments(segments: List[str], max_length: int) -> List[str]:
    """优化段落，合并过短的段落并确保语义完整性"""
    if not segments:
        return segments
    
    # 第一步：合并过短的段落
    merged_segments = []
    current_segment = segments[0]
    
    for i in range(1, len(segments)):
        next_segment = segments[i]
        
        # 如果当前段落很短，且与下一段落合并后不超过限制，则合并
        if (len(current_segment) < max_length // 2 and 
            len(current_segment + next_segment) <= max_length + 3):
            current_segment += next_segment
        else:
            merged_segments.append(current_segment)
            current_segment = next_segment
    
    merged_segments.append(current_segment)
    
    # 第二步：检查语义完整性
    final_segments = []
    for i, segment in enumerate(merged_segments):
        # 检查段落是否以不完整的词汇结尾
        if (i + 1 < len(merged_segments) and 
            _is_semantic_incomplete(segment, merged_segments[i + 1])):
            # 尝试与下一段合并
            combined = segment + merged_segments[i + 1]
            if len(combined) <= max_length + 5:
                final_segments.append(combined)
                # 跳过下一段
                merged_segments[i + 1] = ""
            else:
                final_segments.append(segment)
        elif segment:  # 非空段落
            final_segments.append(segment)
    
    return final_segments

def calculate_segment_timestamps(segments: List[str], character_timestamps: List[Dict], original_text: str) -> List[Dict]:
    """为分割后的段落计算时间戳，确保不会出现重叠"""
    segment_timestamps = []
    current_char_index = 0
    
    # 预处理：创建清理后文本到原始字符索引的映射
    clean_to_original_mapping = []
    clean_original_text = ""
    
    for i, char_data in enumerate(character_timestamps):
        char = char_data.get('character', '')
        # 跳过标点符号和特殊字符，但记录映射关系
        if char not in '，。；：、！？""''（）【】《》〈〉「」『』〔〕\[\]｛｝｜～·…—–,.;:!?"\':[]{}|~\npau':
            clean_original_text += char
            clean_to_original_mapping.append(i)
    
    print(f"原始文本长度: {len(original_text)}, 清理后长度: {len(clean_original_text)}")
    
    for segment_idx, segment in enumerate(segments):
        # 清理段落文本（移除标点符号用于匹配）
        clean_segment = clean_subtitle_text(segment)
        
        print(f"\n处理段落 {segment_idx + 1}: '{segment}' -> '{clean_segment}'")
        
        # 在清理后的文本中查找段落位置
        segment_start_clean_index = -1
        segment_end_clean_index = -1
        
        # 从当前位置开始搜索
        search_start = min(current_char_index, len(clean_original_text) - 1)
        
        # 在清理后的文本中查找匹配
        for start_pos in range(search_start, len(clean_original_text)):
            if start_pos + len(clean_segment) <= len(clean_original_text):
                if clean_original_text[start_pos:start_pos + len(clean_segment)] == clean_segment:
                    segment_start_clean_index = start_pos
                    segment_end_clean_index = start_pos + len(clean_segment) - 1
                    break
        
        if segment_start_clean_index == -1 or segment_end_clean_index == -1:
            print(f"警告: 无法找到段落 '{clean_segment}' 在清理后文本中的位置")
            # 使用估算时间
            if segment_timestamps:
                start_time = segment_timestamps[-1]['end_time'] + 0.1  # 添加小间隔避免重叠
            else:
                start_time = 0
            end_time = start_time + len(clean_segment) * 0.3  # 估算每字0.3秒
        else:
             # 安全地将清理后的索引映射回原始字符索引
             if (segment_start_clean_index < len(clean_to_original_mapping) and 
                 segment_end_clean_index < len(clean_to_original_mapping)):
                 
                 original_start_index = clean_to_original_mapping[segment_start_clean_index]
                 original_end_index = clean_to_original_mapping[segment_end_clean_index]
                 
                 # 确保索引在有效范围内
                 if (original_start_index < len(character_timestamps) and 
                     original_end_index < len(character_timestamps)):
                     
                     # 根据字符索引获取时间戳
                     start_time = character_timestamps[original_start_index]['start_time']
                     end_time = character_timestamps[original_end_index]['end_time']
                     
                     print(f"找到匹配: 清理索引 {segment_start_clean_index}-{segment_end_clean_index}, 原始索引 {original_start_index}-{original_end_index}")
                     print(f"时间戳: {start_time:.2f}-{end_time:.2f}")
                     
                     # 更新当前字符索引
                     current_char_index = segment_end_clean_index + 1
                 else:
                     print(f"警告: 原始索引超出范围 {original_start_index}-{original_end_index}, 字符时间戳长度: {len(character_timestamps)}")
                     # 使用估算时间
                     if segment_timestamps:
                         start_time = segment_timestamps[-1]['end_time'] + 0.1
                     else:
                         start_time = 0
                     end_time = start_time + len(clean_segment) * 0.3
             else:
                 print(f"警告: 清理索引超出范围 {segment_start_clean_index}-{segment_end_clean_index}, 映射长度: {len(clean_to_original_mapping)}")
                 # 使用估算时间
                 if segment_timestamps:
                     start_time = segment_timestamps[-1]['end_time'] + 0.1
                 else:
                     start_time = 0
                 end_time = start_time + len(clean_segment) * 0.3
        
        # 检查并修正重叠问题
        if segment_timestamps:
            prev_end_time = segment_timestamps[-1]['end_time']
            if start_time < prev_end_time:
                print(f"检测到重叠: 前一段结束时间 {prev_end_time:.2f}, 当前段开始时间 {start_time:.2f}")
                # 修正重叠：将当前段的开始时间设置为前一段结束时间 + 0.1秒
                start_time = prev_end_time + 0.1
                # 如果修正后开始时间大于等于结束时间，则调整结束时间
                if start_time >= end_time:
                    end_time = start_time + len(clean_segment) * 0.3
                print(f"修正后时间戳: {start_time:.2f}-{end_time:.2f}")
            # 额外检查：确保当前段的结束时间不会与开始时间重叠
            elif end_time <= start_time:
                print(f"检测到无效时间戳: 开始时间 {start_time:.2f} >= 结束时间 {end_time:.2f}")
                end_time = start_time + len(clean_segment) * 0.3
                print(f"修正后结束时间: {end_time:.2f}")
        
        segment_timestamps.append({
            'text': segment,  # 使用原始段落文本（包含标点符号）
            'start_time': start_time,
            'end_time': end_time
        })
    
    # 最终检查：确保所有时间戳都是递增的且无重叠
    for i in range(1, len(segment_timestamps)):
        prev_segment = segment_timestamps[i-1]
        curr_segment = segment_timestamps[i]
        
        # 检查当前段开始时间是否早于前一段结束时间
        if curr_segment['start_time'] < prev_segment['end_time']:
            print(f"最终修正: 段落 {i+1} 时间戳重叠 - 前段: {prev_segment['start_time']:.2f}-{prev_segment['end_time']:.2f}, 当前段: {curr_segment['start_time']:.2f}-{curr_segment['end_time']:.2f}")
            
            # 修正策略1：调整当前段开始时间
            new_start_time = prev_segment['end_time'] + 0.1
            duration = curr_segment['end_time'] - curr_segment['start_time']
            
            # 如果原始持续时间太短，设置最小持续时间
            if duration < 0.5:
                duration = max(0.5, len(clean_subtitle_text(curr_segment['text'])) * 0.3)
            
            segment_timestamps[i]['start_time'] = new_start_time
            segment_timestamps[i]['end_time'] = new_start_time + duration
            
            print(f"修正后: {segment_timestamps[i]['start_time']:.2f}-{segment_timestamps[i]['end_time']:.2f}")
        
        # 检查时间戳有效性
        if curr_segment['start_time'] >= curr_segment['end_time']:
            print(f"修正无效时间戳: 段落 {i+1}")
            segment_timestamps[i]['end_time'] = segment_timestamps[i]['start_time'] + 1.0
    
    return segment_timestamps

def clean_subtitle_text(text: str) -> str:
    """清理字幕文本，移除所有标点符号和多余空格，但保留ASS格式标签"""
    # 移除所有空格
    text = re.sub(r'\s+', '', text)
    
    # 保护ASS标签，先提取所有ASS标签
    ass_tags = []
    tag_pattern = r'\{[^}]*\}'
    
    # 找到所有ASS标签并用占位符替换
    def replace_tag(match):
        ass_tags.append(match.group(0))
        return f'__ASS_TAG_{len(ass_tags)-1}__'
    
    text_with_placeholders = re.sub(tag_pattern, replace_tag, text)
    
    # 移除所有标点符号
    cleaned_text = re.sub(r'[，。；：、！？""""''（）【】《》〈〉「」『』〔〕\[\]｛｝｜～·…—–,.;:!?"\'()\[\]{}|~`@#$%^&*+=<>/\\-]', '', text_with_placeholders)
    
    # 恢复ASS标签
    for i, tag in enumerate(ass_tags):
        cleaned_text = cleaned_text.replace(f'__ASS_TAG_{i}__', tag)
    
    return cleaned_text

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
Style: Default,Microsoft YaHei,36,&H00FFFFFF,&H000000FF,&H00000000,&H80000000,0,0,0,0,100,100,0,0,1,2,2,2,10,10,427,1
Style: Highlight,Microsoft YaHei,36,&H0000FFFF,&H000000FF,&H00000000,&H80000000,1,0,0,0,100,100,0,0,1,2,2,2,10,10,427,1

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
        
        # 转义ASS字幕中的特殊字符，特别是汉字双引号
        escaped_text = highlighted_text.replace('"', '\\"').replace('"', '\\"').replace('"', '\\"')
        
        # 生成事件行
        event_line = f"Dialogue: 0,{start_time},{end_time},Default,,0,0,0,,{escaped_text}"
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
    parser.add_argument('path', help='数据目录路径或单个章节目录路径')
    parser.add_argument('--max-length', type=int, default=12, help='每段最大字符数（默认12）')
    parser.add_argument('--chapter', help='指定要处理的章节名称（如：chapter_001）')
    
    args = parser.parse_args()
    
    if not os.path.exists(args.path):
        print(f"❌ 路径不存在: {args.path}")
        return
    
    # 如果指定了--chapter参数，只处理指定的章节
    if args.chapter:
        chapter_path = os.path.join(args.path, args.chapter)
        if not os.path.exists(chapter_path):
            print(f"❌ 指定的章节目录不存在: {chapter_path}")
            return
        
        print(f"处理指定章节: {args.chapter}")
        if process_chapter(chapter_path, args.max_length):
            print("✓ 章节处理成功！")
        else:
            print("❌ 章节处理失败")
        return
    
    # 判断是单个章节目录还是数据目录
    if os.path.basename(args.path).startswith('chapter'):
        # 单个章节目录
        print(f"处理单个章节: {os.path.basename(args.path)}")
        if process_chapter(args.path, args.max_length):
            print("✓ 章节处理成功！")
        else:
            print("❌ 章节处理失败")
    else:
        # 数据目录，查找所有章节目录
        chapter_dirs = []
        for item in os.listdir(args.path):
            item_path = os.path.join(args.path, item)
            if os.path.isdir(item_path) and item.startswith('chapter'):
                chapter_dirs.append(item_path)
        
        chapter_dirs.sort()
        
        if not chapter_dirs:
            print(f"❌ 在 {args.path} 中未找到章节目录")
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

