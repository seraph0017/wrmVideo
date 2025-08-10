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
    """自然分割文本，优先在标点符号处分割"""
    if len(text) <= max_length:
        return [text]
    
    segments = []
    current_segment = ""
    
    # 标点符号优先级（越小优先级越高）
    punctuation_priority = {
        '。': 1, '！': 1, '？': 1,
        '；': 2, '：': 2,
        '，': 3, '、': 3,
        '）': 4, '】': 4, '》': 4, '」': 4, '』': 4,
        '（': 5, '【': 5, '《': 5, '「': 5, '『': 5
    }
    
    i = 0
    while i < len(text):
        char = text[i]
        current_segment += char
        
        # 检查是否需要分割
        if len(current_segment) >= max_length:
            # 寻找最佳分割点
            best_split_pos = -1
            best_priority = float('inf')
            
            # 从当前位置向前搜索标点符号
            for j in range(len(current_segment) - 1, max(0, len(current_segment) - 5), -1):
                if current_segment[j] in punctuation_priority:
                    priority = punctuation_priority[current_segment[j]]
                    if priority < best_priority:
                        best_priority = priority
                        best_split_pos = j
            
            if best_split_pos != -1:
                # 在标点符号后分割
                segments.append(current_segment[:best_split_pos + 1])
                current_segment = current_segment[best_split_pos + 1:]
            else:
                # 没找到合适的标点符号，强制分割
                if len(current_segment) > max_length + 3:  # 允许稍微超出
                    segments.append(current_segment[:-1])
                    current_segment = current_segment[-1:]
        
        i += 1
    
    if current_segment:
        segments.append(current_segment)
    
    return segments

def calculate_segment_timestamps(segments: List[str], character_timestamps: List[Dict], original_text: str) -> List[Dict]:
    """为分割后的段落计算时间戳"""
    segment_timestamps = []
    current_char_index = 0
    
    for segment in segments:
        # 清理段落文本（移除标点符号用于匹配）
        clean_segment = clean_subtitle_text(segment)
        
        # 在原始文本中找到这个段落的起始和结束字符索引
        segment_start_index = -1
        segment_end_index = -1
        
        # 从当前字符索引开始搜索
        temp_clean_text = ""
        char_count = 0
        
        for i, char_data in enumerate(character_timestamps[current_char_index:], current_char_index):
            if i >= len(character_timestamps):
                break
                
            char = char_data.get('character', '')
            
            # 跳过标点符号和特殊字符
            if char not in '，。；：、！？""''（）【】《》〈〉「」『』〔〕\[\]｛｝｜～·…—–,.;:!?"\':[]{}|~\npau':
                temp_clean_text += char
                
                if len(temp_clean_text) == 1:  # 第一个字符匹配
                    segment_start_index = i
                
                if segment_start_index != -1 and temp_clean_text == clean_segment:
                    segment_end_index = i
                    break
                    
                if segment_start_index != -1 and not clean_segment.startswith(temp_clean_text):
                    # 匹配失败，重置
                    temp_clean_text = ""
                    segment_start_index = -1
        
        if segment_start_index == -1 or segment_end_index == -1:
            print(f"警告: 无法找到段落 '{segment}' 在字符时间戳中的位置")
            # 使用估算时间
            if segment_timestamps:
                start_time = segment_timestamps[-1]['end_time']
            else:
                start_time = 0
            end_time = start_time + len(clean_segment) * 0.3  # 估算每字0.3秒
        else:
            # 根据字符索引获取时间戳
            start_time = character_timestamps[segment_start_index]['start_time']
            end_time = character_timestamps[segment_end_index]['end_time']
        
        segment_timestamps.append({
            'text': clean_segment,  # 使用已经清理过的文本
            'start_time': start_time,
            'end_time': end_time
        })
        
        # 更新当前字符索引到段落结束后
        current_char_index = segment_end_index + 1 if segment_end_index != -1 else current_char_index + len(clean_segment)
    
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