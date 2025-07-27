#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
独立的语音生成脚本
从脚本文件生成语音和时间戳文件
"""

import os
import sys
import re
import json
import argparse
from datetime import datetime

# 添加src目录到路径
src_dir = os.path.join(os.path.dirname(__file__), 'src')
sys.path.insert(0, src_dir)

from config.config import TTS_CONFIG
from src.voice.gen_voice import VoiceGenerator

def clean_text_for_tts(text):
    """
    清理文本用于TTS生成，移除括号内的内容和&符号
    
    Args:
        text: 原始文本
    
    Returns:
        str: 清理后的文本
    """
    # 移除各种括号及其内容
    text = re.sub(r'\([^)]*\)', '', text)  # 移除圆括号内容
    text = re.sub(r'\[[^\]]*\]', '', text)  # 移除方括号内容
    text = re.sub(r'\{[^}]*\}', '', text)  # 移除花括号内容
    text = re.sub(r'（[^）]*）', '', text)  # 移除中文圆括号内容
    text = re.sub(r'【[^】]*】', '', text)  # 移除中文方括号内容
    
    # 移除&符号
    text = text.replace('&', '')
    
    # 清理多余的空格
    text = re.sub(r'\s+', ' ', text).strip()
    
    return text

def extract_narration_content(narration_file_path):
    """
    从narration.txt文件中提取解说内容
    
    Args:
        narration_file_path: narration.txt文件路径
    
    Returns:
        list: 解说内容列表
    """
    narration_contents = []
    
    try:
        if not os.path.exists(narration_file_path):
            print(f"警告: narration.txt文件不存在: {narration_file_path}")
            return narration_contents
        
        with open(narration_file_path, 'r', encoding='utf-8') as f:
            content = f.read()
        
        # 调试：检查是否包含解说内容标签
        if '<解说内容>' in content:
            print(f"调试：文件中包含<解说内容>标签")
        else:
            print(f"调试：文件中不包含<解说内容>标签")
        
        # 调试：查找第一个解说内容标签的位置
        start_pos = content.find('<解说内容>')
        if start_pos != -1:
            end_pos = content.find('</解说内容>', start_pos)
            if end_pos != -1:
                first_content = content[start_pos:end_pos+6]
                print(f"调试：第一个解说内容标签: {first_content}")
                # 检查标签内容的字符编码
                inner_content = content[start_pos+5:end_pos]
                print(f"调试：标签内容长度: {len(inner_content)}")
                print(f"调试：标签内容前100字符: {repr(inner_content[:100])}")
            else:
                print(f"调试：找到开始标签但未找到结束标签")
        else:
            print(f"调试：未找到开始标签")
        
        # 使用正则表达式提取所有<解说内容>标签中的内容
        # 注意：文件中的解说内容标签没有结束标签，内容直接跟在开始标签后面直到下一个标签
        narration_matches = re.findall(r'<解说内容>([^<]+)', content, re.DOTALL)
        
        print(f"调试：正则匹配结果数量: {len(narration_matches)}")
        if narration_matches:
            print(f"调试：第一个匹配结果: {narration_matches[0][:100]}")
        
        for narration in narration_matches:
            # 清理文本，移除多余的空白字符
            clean_narration = narration.strip()
            if clean_narration:
                narration_contents.append(clean_narration)
        
        print(f"从 {narration_file_path} 中提取到 {len(narration_contents)} 段解说内容")
        return narration_contents
        
    except Exception as e:
        print(f"提取解说内容时发生错误: {e}")
        return narration_contents

def generate_voices_from_scripts(data_dir):
    """
    根据脚本生成语音
    
    Args:
        data_dir: 数据目录路径（可以是包含多个章节的目录，也可以是单个章节目录）
    
    Returns:
        bool: 是否成功
    """
    try:
        print(f"=== 开始生成语音 ===")
        print(f"数据目录: {data_dir}")
        
        if not os.path.exists(data_dir):
            print(f"错误: 数据目录不存在 {data_dir}")
            return False
        
        # 检查是否是单个章节目录
        if os.path.basename(data_dir).startswith('chapter_'):
            # 单个章节目录
            chapter_dirs = [data_dir]
            print(f"检测到单个章节目录: {os.path.basename(data_dir)}")
        else:
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
        
        # 创建语音生成器
        voice_generator = VoiceGenerator()
        
        success_count = 0
        
        # 处理每个章节
        for chapter_dir in chapter_dirs:
            chapter_name = os.path.basename(chapter_dir)
            print(f"\n--- 处理章节: {chapter_name} ---")
            
            # 查找解说文件
            narration_file = os.path.join(chapter_dir, "narration.txt")
            if not os.path.exists(narration_file):
                print(f"警告: 解说文件不存在 {narration_file}")
                continue
            
            # 提取解说内容
            narration_contents = extract_narration_content(narration_file)
            
            if not narration_contents:
                print(f"警告: 未找到解说内容")
                continue
            
            print(f"找到 {len(narration_contents)} 段解说内容")
            
            # 为每段解说内容生成语音
            for i, narration_text in enumerate(narration_contents, 1):
                # 清理文本用于TTS
                clean_narration = clean_text_for_tts(narration_text)
                
                if not clean_narration.strip():
                    print(f"警告: 第 {i} 段解说内容清理后为空")
                    continue
                
                # 生成音频文件路径
                audio_path = os.path.join(chapter_dir, f"{chapter_name}_narration_{i:02d}.mp3")
                
                # 生成时间戳文件路径
                timestamp_path = os.path.join(chapter_dir, f"{chapter_name}_narration_{i:02d}_timestamps.json")
                
                print(f"正在生成第 {i} 段解说语音...")
                print(f"文本内容: {clean_narration[:50]}{'...' if len(clean_narration) > 50 else ''}")
                
                # 使用语音生成器生成语音并获取时间戳
                result = voice_generator.generate_voice_with_timestamps(clean_narration, audio_path)
                if result and result.get('success', False):
                    print(f"✓ 第 {i} 段语音生成成功: {audio_path}")
                    
                    # 从API响应中提取时间戳信息
                    api_response = result.get('api_response', {})
                    
                    # 构建时间戳数据结构
                    timestamp_data = {
                        "text": clean_narration,
                        "audio_file": audio_path,
                        "duration": float(api_response.get('addition', {}).get('duration', 0)) / 1000.0,  # 转换为秒
                        "character_timestamps": [],
                        "generated_at": datetime.now().isoformat()
                    }
                    
                    # 从API响应中解析字符级时间戳
                    try:
                        addition = api_response.get('addition', {})
                        frontend_str = addition.get('frontend', '{}')
                        if isinstance(frontend_str, str):
                            frontend_data = json.loads(frontend_str)
                        else:
                            frontend_data = frontend_str
                        
                        words = frontend_data.get('words', [])
                        
                        for word_info in words:
                            timestamp_data["character_timestamps"].append({
                                "character": word_info.get('word', ''),
                                "start_time": float(word_info.get('start_time', 0)),
                                "end_time": float(word_info.get('end_time', 0))
                            })
                        
                        print(f"✓ 从API响应中解析到 {len(words)} 个字符的时间戳")
                        
                    except (json.JSONDecodeError, KeyError, ValueError) as e:
                        print(f"⚠ 解析时间戳失败，使用估算值: {e}")
                        # 如果解析失败，回退到估算方式
                        current_time = 0.0
                        char_duration = timestamp_data["duration"] / len(clean_narration) if clean_narration else 0.15
                        for char_idx, char in enumerate(clean_narration):
                            timestamp_data["character_timestamps"].append({
                                "character": char,
                                "start_time": current_time,
                                "end_time": current_time + char_duration
                            })
                            current_time += char_duration
                    
                    # 保存时间戳文件
                    try:
                        with open(timestamp_path, 'w', encoding='utf-8') as f:
                            json.dump(timestamp_data, f, ensure_ascii=False, indent=2)
                        print(f"✓ 时间戳文件保存成功: {timestamp_path}")
                    except Exception as e:
                        print(f"✗ 时间戳文件保存失败: {e}")
                    
                    success_count += 1
                else:
                    print(f"✗ 第 {i} 段语音生成失败")
        
        print(f"\n语音生成完成，成功生成 {success_count} 个语音文件")
        return success_count > 0
        
    except Exception as e:
        print(f"生成语音时发生错误: {e}")
        return False

def main():
    """
    主函数
    """
    parser = argparse.ArgumentParser(description='独立的语音生成脚本')
    parser.add_argument('data_dir', help='数据目录路径')
    
    args = parser.parse_args()
    
    print(f"开始处理数据目录: {args.data_dir}")
    
    # 生成语音
    success = generate_voices_from_scripts(args.data_dir)
    if success:
        print(f"\n✓ 语音生成完成")
    else:
        print(f"\n✗ 语音生成失败")
        sys.exit(1)
    
    print("\n=== 处理完成 ===")

if __name__ == '__main__':
    main()