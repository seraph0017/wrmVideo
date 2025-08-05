#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
独立的语音生成脚本（异步版本）
从脚本文件生成语音和时间戳文件
使用ThreadPoolExecutor实现多线程处理
"""

import os
import sys
import re
import json
import argparse
from datetime import datetime
from concurrent.futures import ThreadPoolExecutor, as_completed
import threading

# 多线程处理

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

def generate_single_narration_voice(voice_generator, chapter_dir, chapter_name, narration_text, index):
    """
    异步生成单个解说内容的语音
    
    Args:
        voice_generator: 语音生成器实例
        chapter_dir: 章节目录
        chapter_name: 章节名称
        narration_text: 解说文本
        index: 解说索引
    
    Returns:
        dict: 生成结果
    """
    try:
        # 清理文本用于TTS
        clean_narration = clean_text_for_tts(narration_text)
        
        if not clean_narration.strip():
            return {
                'success': False,
                'index': index,
                'error': '解说内容清理后为空'
            }
        
        # 生成音频文件路径
        audio_path = os.path.join(chapter_dir, f"{chapter_name}_narration_{index:02d}.mp3")
        
        # 生成时间戳文件路径
        timestamp_path = os.path.join(chapter_dir, f"{chapter_name}_narration_{index:02d}_timestamps.json")
        
        print(f"[协程 {index}] 正在生成第 {index} 段解说语音...")
        print(f"[协程 {index}] 文本内容: {clean_narration[:50]}{'...' if len(clean_narration) > 50 else ''}")
        
        # 使用语音生成器生成语音并获取时间戳
        result = voice_generator.generate_voice_with_timestamps(clean_narration, audio_path)
        if result and result.get('success', False):
            print(f"[协程 {index}] ✓ 第 {index} 段语音生成成功: {audio_path}")
            
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
                
                print(f"[协程 {index}] ✓ 从API响应中解析到 {len(words)} 个字符的时间戳")
                
            except (json.JSONDecodeError, KeyError, ValueError) as e:
                print(f"[协程 {index}] ⚠ 解析时间戳失败，使用估算值: {e}")
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
                print(f"[协程 {index}] ✓ 时间戳文件保存成功: {timestamp_path}")
            except Exception as e:
                print(f"[协程 {index}] ✗ 时间戳文件保存失败: {e}")
            
            return {
                'success': True,
                'index': index,
                'audio_path': audio_path,
                'timestamp_path': timestamp_path
            }
        else:
            return {
                'success': False,
                'index': index,
                'error': '语音生成失败'
            }
            
    except Exception as e:
        return {
            'success': False,
            'index': index,
            'error': str(e)
        }

def generate_voices_from_scripts(data_dir, max_workers=5):
    """
    根据脚本生成语音（多线程版本）
    
    Args:
        data_dir: 数据目录路径（可以是包含多个章节的目录，也可以是单个章节目录）
        max_workers: 最大并发线程数
    
    Returns:
        bool: 是否成功
    """
    try:
        print(f"=== 开始多线程生成语音 ===")
        print(f"数据目录: {data_dir}")
        print(f"最大并发数: {max_workers}")
        
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
        
        # 收集所有需要处理的任务
        tasks = []
        
        # 处理每个章节
        for chapter_dir in chapter_dirs:
            chapter_name = os.path.basename(chapter_dir)
            print(f"\n--- 准备处理章节: {chapter_name} ---")
            
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
            
            print(f"找到 {len(narration_contents)} 段解说内容，准备多线程处理")
            
            # 为每段解说内容创建任务参数
            for i, narration_text in enumerate(narration_contents, 1):
                task_params = {
                    'voice_generator': voice_generator,
                    'chapter_dir': chapter_dir,
                    'chapter_name': chapter_name,
                    'narration_text': narration_text,
                    'index': i
                }
                tasks.append(task_params)
        
        if not tasks:
            print("没有找到需要处理的任务")
            return False
        
        print(f"\n开始执行 {len(tasks)} 个多线程任务...")
        print(f"使用 {max_workers} 个线程并发处理")
        
        # 统计结果
        success_count = 0
        failed_count = 0
        
        # 使用ThreadPoolExecutor执行任务
        with ThreadPoolExecutor(max_workers=max_workers) as executor:
            # 提交所有任务
            future_to_params = {
                executor.submit(
                    generate_single_narration_voice,
                    task_params['voice_generator'],
                    task_params['chapter_dir'],
                    task_params['chapter_name'],
                    task_params['narration_text'],
                    task_params['index']
                ): task_params
                for task_params in tasks
            }
            
            # 收集结果
            for future in as_completed(future_to_params):
                task_params = future_to_params[future]
                try:
                    result = future.result()
                    if result and result.get('success', False):
                        success_count += 1
                        print(f"线程 {threading.current_thread().name}: ✓ 任务 {result.get('index', '?')} 完成")
                    else:
                        failed_count += 1
                        error_msg = result.get('error', '未知错误') if result else '任务返回空结果'
                        print(f"线程 {threading.current_thread().name}: ✗ 任务 {result.get('index', '?') if result else '?'} 失败: {error_msg}")
                except Exception as e:
                    failed_count += 1
                    index = task_params.get('index', '?')
                    print(f"线程 {threading.current_thread().name}: ✗ 任务 {index} 执行异常: {e}")
        
        print(f"\n多线程语音生成完成")
        print(f"成功: {success_count} 个")
        print(f"失败: {failed_count} 个")
        print(f"总计: {len(tasks)} 个")
        
        return success_count > 0
        
    except Exception as e:
        print(f"多线程生成语音时发生错误: {e}")
        return False

def main():
    """
    主函数
    """
    parser = argparse.ArgumentParser(description='独立的语音生成脚本（多线程版本）')
    parser.add_argument('data_dir', help='数据目录路径')
    parser.add_argument('--max-workers', type=int, default=5, 
                       help='最大并发线程数 (默认: 5)')
    parser.add_argument('--verbose', '-v', action='store_true',
                       help='显示详细输出')
    
    args = parser.parse_args()
    
    print(f"开始多线程处理数据目录: {args.data_dir}")
    print(f"并发线程数: {args.max_workers}")
    
    # 生成语音
    success = generate_voices_from_scripts(args.data_dir, args.max_workers)
    if success:
        print(f"\n✓ 多线程语音生成完成")
    else:
        print(f"\n✗ 多线程语音生成失败")
        sys.exit(1)
    
    print("\n=== 多线程处理完成 ===")

if __name__ == '__main__':
    main()