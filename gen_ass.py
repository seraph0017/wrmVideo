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
    
    # 常见的中文姓氏
    common_surnames = [
        '李', '王', '张', '刘', '陈', '杨', '赵', '黄', '周', '吴',
        '徐', '孙', '胡', '朱', '高', '林', '何', '郭', '马', '罗',
        '梁', '宋', '郑', '谢', '韩', '唐', '冯', '于', '董', '萧',
        '程', '曹', '袁', '邓', '许', '傅', '沈', '曾', '彭', '吕',
        '苏', '卢', '蒋', '蔡', '贾', '丁', '魏', '薛', '叶', '阎',
        '余', '潘', '杜', '戴', '夏', '钟', '汪', '田', '任', '姜',
        '范', '方', '石', '姚', '谭', '廖', '邹', '熊', '金', '陆'
    ]
    
    # 检查当前位置前后是否有完整的姓名
    # 向前查找最多4个字符，向后查找最多4个字符
    start_search = max(0, position - 4)
    end_search = min(len(text), position + 5)
    
    # 在搜索范围内查找姓氏
    for i in range(start_search, min(end_search, len(text))):
        char = text[i]
        if char in common_surnames:
            # 找到姓氏，检查后面是否跟着1-3个汉字作为名字
            surname_pos = i
            name_start = surname_pos + 1
            name_end = name_start
            
            # 查找名字部分（1-3个汉字）
            for j in range(name_start, min(name_start + 3, len(text))):
                if '\u4e00' <= text[j] <= '\u9fff' and text[j] not in '，。！？；：、""''（）【】《》':
                    name_end = j + 1
                else:
                    break
            
            # 检查是否形成了有效的姓名（姓氏+1-3个字的名字）
            if name_end > name_start and (name_end - name_start) <= 3:
                # 当前位置在这个姓名范围内就保护
                if surname_pos <= position < name_end:
                    return True
    
    # 检查英文名模式
    english_name_pattern = r'[A-Z][a-z]+'
    matches = list(re.finditer(english_name_pattern, text))
    for match in matches:
        if match.start() <= position < match.end():
            return True
    
    return False

def is_word_boundary(text: str, position: int) -> bool:
    """检查指定位置是否为词汇边界（避免在词汇中间断句）"""
    if position <= 0 or position >= len(text):
        return True
    
    # 使用jieba分词检查是否在词汇中间
    words = list(jieba.cut(text, cut_all=False))
    current_pos = 0
    
    for word in words:
        word_start = current_pos
        word_end = current_pos + len(word)
        
        # 如果断句位置在词汇中间，返回False
        if word_start < position < word_end:
            return False
        
        current_pos = word_end
        if current_pos >= position:
            break
    
    return True

def is_short_word_boundary(text: str, position: int) -> bool:
    """检查指定位置是否会导致产生过短的词汇片段（避免一两个字的断句）"""
    if position <= 0 or position >= len(text):
        return True
    
    # 检查断句前后是否会产生过短的片段
    # 检查断句前的片段长度（从前一个标点或开头到当前位置）
    prev_punctuation_pos = -1
    for i in range(position - 1, -1, -1):
        if text[i] in '，。！？；：、':
            prev_punctuation_pos = i
            break
    
    # 计算前段的有效字符数（不包括标点）
    prev_segment = text[prev_punctuation_pos + 1:position]
    prev_char_count = len([c for c in prev_segment if c not in '，。！？；：、""''（）【】《》'])
    
    # 检查断句后的片段长度（从当前位置到下一个标点或结尾）
    next_punctuation_pos = len(text)
    for i in range(position, len(text)):
        if text[i] in '，。！？；：、':
            next_punctuation_pos = i
            break
    
    # 计算后段的有效字符数（不包括标点）
    next_segment = text[position:next_punctuation_pos]
    next_char_count = len([c for c in next_segment if c not in '，。！？；：、""''（）【】《》'])
    
    # 如果前段或后段的有效字符数少于6个，则不适合在此处断句
    # 进一步提高要求以避免产生一两个字的断句行
    if prev_char_count < 6 or next_char_count < 6:
        return False
    
    return True

def is_phrase_boundary(text: str, position: int) -> bool:
    """检查指定位置是否为短语边界，避免分割常见短语"""
    if position <= 0 or position >= len(text):
        return True
    
    # 定义常见的不应分割的短语模式
    protected_phrases = [
        # 数量词相关
        r'一\w*面',     # 一面、一方面等
        r'一\w*两\w*个\w*字',  # 一两个字等
        r'一\w*些',     # 一些
        r'一\w*点',     # 一点
        r'一\w*下',     # 一下
        r'一\w*起',     # 一起
        r'一\w*直',     # 一直
        r'一\w*边',     # 一边
        r'一\w*旁',     # 一旁
        r'一\w*侧',     # 一侧
        r'两\w*个\w*字', # 两个字
        r'三\w*个\w*字', # 三个字
        r'几\w*个\w*字', # 几个字
        
        # 方位词相关
        r'东\w*市',     # 东市
        r'西\w*市',     # 西市
        r'南\w*市',     # 南市
        r'北\w*市',     # 北市
        r'东\w*宫',     # 东宫
        r'西\w*宫',     # 西宫
        
        # 颜色相关
        r'\w*金色',     # 金色相关
        r'\w*银色',     # 银色相关
        r'\w*红色',     # 红色相关
        r'\w*蓝色',     # 蓝色相关
        
        # 环境相关
        r'\w*环境',     # 环境相关
        r'\w*喧嚣',     # 喧嚣相关
        r'\w*嘈杂',     # 嘈杂相关
        r'光线\w*',     # 光线相关
        
        # 人名相关（补充保护）
        r'李\w{1,3}',   # 李姓人名
        r'王\w{1,3}',   # 王姓人名
        r'张\w{1,3}',   # 张姓人名
        r'刘\w{1,3}',   # 刘姓人名
        r'陈\w{1,3}',   # 陈姓人名
        r'\w*乾',       # 以乾结尾的人名
        r'\w*泰',       # 以泰结尾的人名
        r'\w*帝',       # 以帝结尾的称谓
        r'\w*王',       # 以王结尾的称谓
        r'\w*公',       # 以公结尾的称谓
        
        # 时间相关
        r'\w*时候',     # 时候相关
        r'\w*时间',     # 时间相关
        r'\w*瞬间',     # 瞬间相关
        r'\w*刹那',     # 刹那相关
        
        # 动作相关
        r'\w*之后',     # 之后
        r'\w*之前',     # 之前
        r'\w*之中',     # 之中
        r'\w*之间',     # 之间
        r'\w*而已',     # 而已
        r'\w*罢了',     # 罢了
    ]
    
    # 检查当前位置前后的文本是否匹配保护短语
    for pattern in protected_phrases:
        # 在当前位置前后查找匹配的短语
        start_search = max(0, position - 15)
        end_search = min(len(text), position + 15)
        search_text = text[start_search:end_search]
        
        matches = re.finditer(pattern, search_text)
        for match in matches:
            phrase_start = start_search + match.start()
            phrase_end = start_search + match.end()
            
            # 如果断句位置在短语中间，返回False
            if phrase_start < position < phrase_end:
                return False
    
    return True

def split_text_naturally(text: str, max_length: int = 20) -> List[str]:
    """按标点符号优先分割文本，标点符号之间的内容尽量独立成行"""
    if not text:
        return []
    
    # 移除多余空格
    text = re.sub(r'\s+', '', text)
    
    segments = []
    
    # 首先按强制断句标点分割
    strong_breaks = '。！？'
    sentences = []
    current_sentence = ""
    
    for char in text:
        current_sentence += char
        if char in strong_breaks:
            sentences.append(current_sentence.strip())
            current_sentence = ""
    
    # 添加剩余部分
    if current_sentence.strip():
        sentences.append(current_sentence.strip())
    
    # 对每个句子进行进一步分割
    for sentence in sentences:
        if not sentence:
            continue
            
        # 按逗号、分号等标点分割，但对顿号特殊处理
        soft_punctuation = '，；：'
        parts = []
        current_part = ""
        
        for char in sentence:
            current_part += char
            if char in soft_punctuation:
                parts.append(current_part.strip())
                current_part = ""
            elif char == '、':
                # 顿号特殊处理：检查前后是否为人名
                temp_part = current_part.strip()
                if temp_part:
                    # 检查是否为人名列表（如：刘备、关羽、张飞）
                    char_count = len([c for c in temp_part if c not in '，；：、。！？'])
                    if char_count <= 7:  # 可能是人名，暂不分割
                        continue
                    else:
                        parts.append(temp_part)
                        current_part = ""
        
        # 添加剩余部分
        if current_part.strip():
            parts.append(current_part.strip())
        
        # 合并过短的片段
        merged_parts = []
        i = 0
        while i < len(parts):
            current_part = parts[i]
            char_count = len([c for c in current_part if c not in '，；：、。！？'])
            
            # 如果当前片段过短且不是最后一个，尝试与下一个合并
            if char_count <= 7 and i + 1 < len(parts):
                next_part = parts[i + 1]
                next_char_count = len([c for c in next_part if c not in '，；：、。！？'])
                combined_count = char_count + next_char_count
                
                # 如果合并后不会过长，则合并
                if combined_count <= max_length:
                    merged_parts.append(current_part + next_part)
                    i += 2  # 跳过下一个片段
                    continue
            
            # 如果当前片段过短且不是第一个，尝试与前一个合并
            if char_count <= 7 and merged_parts:
                last_part = merged_parts[-1]
                last_char_count = len([c for c in last_part if c not in '，；：、。！？'])
                combined_count = char_count + last_char_count
                
                # 如果合并后不会过长，则合并
                if combined_count <= max_length:
                    merged_parts[-1] = last_part + current_part
                    i += 1
                    continue
            
            merged_parts.append(current_part)
            i += 1
        
        # 检查每个部分的长度，如果过长则进一步分割
        for part in merged_parts:
            if not part:
                continue
                
            # 计算实际字符数（不包括标点）
            char_count = len([c for c in part if c not in '，；：、。！？'])
            
            if char_count <= max_length:
                # 长度合适，直接添加
                segments.append(part)
            else:
                # 长度过长，需要进一步分割
                sub_segments = split_long_part(part, max_length)
                segments.extend(sub_segments)
    
    # 清理每个段落的标点符号
    cleaned_segments = []
    for segment in segments:
        if segment.strip():
            cleaned_segment = clean_subtitle_text(segment.strip())
            if cleaned_segment.strip():  # 只保留非空的段落
                cleaned_segments.append(cleaned_segment)
    
    # 最终合并过短的片段
    final_segments = []
    i = 0
    while i < len(cleaned_segments):
        current_segment = cleaned_segments[i]
        char_count = len([c for c in current_segment if c not in '，；：、。！？'])
        
        # 如果当前片段过短且不是最后一个，尝试与下一个合并
        if char_count < 6 and i + 1 < len(cleaned_segments):
            next_segment = cleaned_segments[i + 1]
            next_char_count = len([c for c in next_segment if c not in '，；：、。！？'])
            combined_count = char_count + next_char_count
            
            # 放宽合并条件，允许稍微超过max_length
            if combined_count <= max_length + 3:
                final_segments.append(current_segment + next_segment)
                i += 2  # 跳过下一个片段
                continue
        
        # 如果当前片段过短且不是第一个，尝试与前一个合并
        if char_count < 6 and final_segments:
            last_segment = final_segments[-1]
            last_char_count = len([c for c in last_segment if c not in '，；：、。！？'])
            combined_count = char_count + last_char_count
            
            # 放宽合并条件，允许稍微超过max_length
            if combined_count <= max_length + 3:
                final_segments[-1] = last_segment + current_segment
                i += 1
                continue
        
        final_segments.append(current_segment)
        i += 1
    
    return final_segments

def split_long_part(text: str, max_length: int) -> List[str]:
    """分割过长的文本片段"""
    segments = []
    current_segment = ""
    current_char_count = 0
    
    i = 0
    while i < len(text):
        char = text[i]
        current_segment += char
        
        # 计算实际字符数（不包括标点）
        if char not in '，；：、。！？':
            current_char_count += 1
        
        # 检查是否需要分割
        if current_char_count >= max_length:
            # 寻找合适的分割点
            best_split_pos = find_best_split_position(current_segment, text, i)
            
            if best_split_pos > 0:
                # 在找到的位置分割
                segments.append(current_segment[:best_split_pos].strip())
                current_segment = current_segment[best_split_pos:].strip()
                current_char_count = len([c for c in current_segment if c not in '，；：、。！？'])
            else:
                # 没找到合适的分割点，强制分割
                segments.append(current_segment.strip())
                current_segment = ""
                current_char_count = 0
        
        i += 1
    
    # 添加剩余部分
    if current_segment.strip():
        segments.append(current_segment.strip())
    
    return segments

def find_best_split_position(current_segment: str, full_text: str, current_pos: int) -> int:
    """寻找最佳分割位置"""
    # 从后往前查找合适的分割点
    for j in range(len(current_segment) - 1, max(0, len(current_segment) - 8), -1):
        # 计算在原文中的位置
        original_pos = current_pos - (len(current_segment) - 1 - j)
        
        # 检查是否为合适的分割位置
        if (not is_person_name(full_text, original_pos) and
            is_word_boundary(full_text, original_pos) and
            is_phrase_boundary(full_text, original_pos) and
            is_short_word_boundary(full_text, original_pos)):
            return j + 1
    
    return -1

def calculate_segment_timestamps(segments: List[str], character_timestamps: List[Dict], original_text: str) -> List[Dict]:
    """为每个文本段计算时间戳"""
    segment_timestamps = []
    
    # 当前在原文中的位置
    current_original_pos = 0
    
    for segment in segments:
        if current_original_pos >= len(character_timestamps):
            break
            
        # 清理段落文本（移除空格和引号）
        clean_segment = segment.strip().replace(' ', '').replace('"', '')
        
        if not clean_segment:  # 跳过空段落
            continue
        
        # 在原文中从当前位置开始查找这个段落
        segment_start_pos = -1
        segment_end_pos = -1
        
        # 逐字符匹配，跳过标点符号
        segment_char_index = 0
        for i in range(current_original_pos, len(original_text)):
            char = original_text[i]
            
            # 跳过标点符号
            if char in '，。！？；：、"':
                continue
                
            # 匹配段落字符
            if segment_char_index < len(clean_segment) and char == clean_segment[segment_char_index]:
                if segment_char_index == 0:
                    segment_start_pos = i  # 记录段落开始位置
                segment_char_index += 1
                
                # 如果匹配完整个段落
                if segment_char_index == len(clean_segment):
                    segment_end_pos = i
                    break
            elif segment_char_index > 0:
                # 如果已经开始匹配但失败了，说明这不是正确的匹配位置
                # 重置并从下一个位置重新开始
                segment_char_index = 0
                segment_start_pos = -1
                # 重新检查当前字符是否是段落的开始
                if char == clean_segment[0]:
                    segment_start_pos = i
                    segment_char_index = 1
        
        if segment_start_pos == -1 or segment_char_index < len(clean_segment):
            # 找不到匹配，跳过这个段落
            print(f"警告: 无法找到段落 '{clean_segment}' 的匹配位置")
            continue
        
        # 获取时间戳
        # 确保结束位置不超过时间戳数组的范围
        actual_end_pos = min(segment_end_pos, len(character_timestamps) - 1)
        
        if (segment_start_pos < len(character_timestamps) and 
            actual_end_pos < len(character_timestamps)):
            
            start_time = character_timestamps[segment_start_pos]['start_time']
            end_time = character_timestamps[actual_end_pos]['end_time']
            
            segment_timestamps.append({
                'text': clean_segment,  # 使用已经清理过的文本
                'start_time': start_time,
                'end_time': end_time
            })
        
        # 更新当前位置到段落结束后
        current_original_pos = segment_end_pos + 1
    
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
    cleaned_text = re.sub(r'[，。；：、！？""''（）【】《》〈〉「」『』〔〕\[\]｛｝｜～·…—–,.;:!?"\'()\[\]{}|~`@#$%^&*+=<>/\\-]', '', text_with_placeholders)
    
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
        
        # 文本已经在分割阶段被清理过了，这里直接使用
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