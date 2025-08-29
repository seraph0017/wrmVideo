#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
解说内容字数验证和自动改写脚本
用于检查指定数据目录下所有章节的narration.txt文件中分镜1的第一个和第二个图片特写的解说内容字数
确保字数控制在30-32字，并自动调用模型API改写超长内容

使用方法:
python validate_narration.py data/xxx
"""

import os
import sys
import re
from pathlib import Path
from volcenginesdkarkruntime import Ark

# 导入配置
try:
    from config.config import ARK_CONFIG
except ImportError:
    print("错误: 无法导入配置文件，请确保config/config.py存在并配置了ARK_CONFIG")
    sys.exit(1)

def extract_narration_content(line):
    """
    从解说行中提取解说内容
    
    Args:
        line (str): 包含解说标签的行
        
    Returns:
        str: 提取的解说内容，如果没有找到则返回空字符串
    """
    match = re.search(r'<解说内容>(.*?)</解说内容>', line)
    if match:
        return match.group(1).strip()
    return ""

def count_chinese_characters(text):
    """
    计算文本中的中文字符数量
    
    Args:
        text (str): 要计算的文本
        
    Returns:
        int: 中文字符数量
    """
    # 匹配中文字符（包括中文标点符号）
    chinese_chars = re.findall(r'[\u4e00-\u9fff\u3000-\u303f\uff00-\uffef]', text)
    return len(chinese_chars)

def rewrite_narration_with_llm(client, original_text, max_retries=5):
    """
    使用LLM改写解说内容，将字数精准控制在30-32字，支持重试直到满足标准
    
    Args:
        client: Ark客户端实例
        original_text (str): 原始解说内容
        max_retries (int): 最大重试次数，默认5次
        
    Returns:
        str: 改写后的解说内容，如果所有重试都失败则返回原文
    """
    original_char_count = count_chinese_characters(original_text)
    print(f"  原文字数: {original_char_count}字")
    
    for attempt in range(max_retries):
        # 根据重试次数调整提示词的严格程度
        if attempt == 0:
            emphasis = "字数必须精准控制在30-32字"
        elif attempt == 1:
            emphasis = "字数必须严格控制在30-32字，不能多一字也不能少一字"
        elif attempt == 2:
            emphasis = "字数必须恰好在30-32字之间，这是硬性要求"
        else:
            emphasis = f"字数必须在30-32字之间，当前是第{attempt+1}次尝试，请务必满足字数要求"
            
        prompt = f"""请将以下解说内容改写，要求：
1. {emphasis}（中文字符）
2. 保持原文的核心意思和情感色彩
3. 删除冗余词汇，保留关键情节
4. 语言要流畅自然，适合旁白解说
5. 只返回改写后的内容，不要任何解释

原文：{original_text}

改写后："""
        
        try:
            resp = client.chat.completions.create(
                model="doubao-seed-1-6-flash-250715",
                messages=[
                    {
                        "content": prompt,
                        "role": "user"
                    }
                ],
            )
            
            rewritten_text = resp.choices[0].message.content.strip()
            
            # 验证改写后的字数
            char_count = count_chinese_characters(rewritten_text)
            print(f"  第{attempt+1}次尝试: {char_count}字 - {rewritten_text}")
            
            if 30 <= char_count <= 32:
                print(f"  改写成功: 满足30-32字要求")
                return rewritten_text
            else:
                print(f"  字数不符合要求({char_count}字)，继续重试...")
                
        except Exception as e:
            print(f"  第{attempt+1}次改写失败: {e}")
            
    print(f"  所有{max_retries}次重试都失败，保持原文")
    return original_text

def find_scene_closeups(content):
    """
    查找分镜1下面的第一个和第二个图片特写的解说内容
    
    Args:
        content (str): narration.txt文件的完整内容
        
    Returns:
        tuple: (第一个特写解说内容, 第二个特写解说内容)
    """
    # 查找分镜1的开始位置
    scene1_match = re.search(r'<分镜1>', content)
    if not scene1_match:
        return None, None
    
    # 从分镜1开始查找
    scene1_start = scene1_match.end()
    scene1_content = content[scene1_start:]
    
    # 查找分镜1的结束位置（下一个分镜或文件结束）
    scene1_end_match = re.search(r'</分镜1>|<分镜2>', scene1_content)
    if scene1_end_match:
        scene1_content = scene1_content[:scene1_end_match.start()]
    
    # 查找所有图片特写的解说内容
    closeup_pattern = r'<图片特写\d+>.*?<解说内容>(.*?)</解说内容>.*?</图片特写\d+>'
    closeup_matches = re.findall(closeup_pattern, scene1_content, re.DOTALL)
    
    first_closeup = closeup_matches[0].strip() if len(closeup_matches) > 0 else None
    second_closeup = closeup_matches[1].strip() if len(closeup_matches) > 1 else None
    
    return first_closeup, second_closeup

def validate_narration_file(narration_file_path, client=None, auto_rewrite=False):
    """
    验证单个narration.txt文件中分镜1的第一个和第二个图片特写的解说内容字数
    
    Args:
        narration_file_path (str): narration.txt文件路径
        client: Ark客户端实例，用于自动改写
        auto_rewrite (bool): 是否自动改写超长内容
        
    Returns:
        dict: 验证结果，包含特写序号、内容、字数和是否符合要求
    """
    results = {
        'file_path': narration_file_path,
        'first_closeup': {'content': '', 'char_count': 0, 'valid': False, 'exists': False, 'rewritten': False},
        'second_closeup': {'content': '', 'char_count': 0, 'valid': False, 'exists': False, 'rewritten': False}
    }
    
    try:
        with open(narration_file_path, 'r', encoding='utf-8') as f:
            content = f.read()
            
        # 查找分镜1的第一个和第二个图片特写
        first_closeup, second_closeup = find_scene_closeups(content)
        
        # 标记是否需要更新文件
        content_updated = False
        updated_content = content
        
        # 检查第一个特写
        if first_closeup:
            char_count = count_chinese_characters(first_closeup)
            is_valid = 30 <= char_count <= 32  # 精准控制在30-32字
            
            rewritten_text = first_closeup
            rewritten = False
            
            # 如果不符合要求且启用自动改写
            if not is_valid and auto_rewrite and client:
                print(f"  第一个特写字数不符合要求({char_count}字)，正在改写...")
                rewritten_text = rewrite_narration_with_llm(client, first_closeup)
                if rewritten_text != first_closeup:
                    rewritten = True
                    # 更新文件内容
                    updated_content = updated_content.replace(f'<解说内容>{first_closeup}</解说内容>', f'<解说内容>{rewritten_text}</解说内容>')
                    content_updated = True
                    char_count = count_chinese_characters(rewritten_text)
                    is_valid = 30 <= char_count <= 32
            
            results['first_closeup'] = {
                'content': rewritten_text,
                'char_count': char_count,
                'valid': is_valid,
                'exists': True,
                'rewritten': rewritten
            }
        
        # 检查第二个特写
        if second_closeup:
            char_count = count_chinese_characters(second_closeup)
            is_valid = 30 <= char_count <= 32  # 精准控制在30-32字
            
            rewritten_text = second_closeup
            rewritten = False
            
            # 如果不符合要求且启用自动改写
            if not is_valid and auto_rewrite and client:
                print(f"  第二个特写字数不符合要求({char_count}字)，正在改写...")
                rewritten_text = rewrite_narration_with_llm(client, second_closeup)
                if rewritten_text != second_closeup:
                    rewritten = True
                    # 更新文件内容
                    updated_content = updated_content.replace(f'<解说内容>{second_closeup}</解说内容>', f'<解说内容>{rewritten_text}</解说内容>')
                    content_updated = True
                    char_count = count_chinese_characters(rewritten_text)
                    is_valid = 30 <= char_count <= 32
            
            results['second_closeup'] = {
                'content': rewritten_text,
                'char_count': char_count,
                'valid': is_valid,
                'exists': True,
                'rewritten': rewritten
            }
        
        # 如果内容有更新，写回文件
        if content_updated:
            with open(narration_file_path, 'w', encoding='utf-8') as f:
                f.write(updated_content)
            print(f"  文件已更新: {narration_file_path}")
                
    except FileNotFoundError:
        print(f"警告: 文件不存在 {narration_file_path}")
    except Exception as e:
        print(f"错误: 读取文件 {narration_file_path} 时出错: {e}")
    
    return results

def validate_data_directory(data_dir, auto_rewrite=False):
    """
    验证数据目录下所有章节的narration.txt文件
    
    Args:
        data_dir (str): 数据目录路径
        auto_rewrite (bool): 是否自动改写超长内容
    """
    data_path = Path(data_dir)
    
    if not data_path.exists():
        print(f"错误: 数据目录不存在 {data_dir}")
        return
    
    if not data_path.is_dir():
        print(f"错误: {data_dir} 不是一个目录")
        return
    
    # 查找所有chapter目录
    chapter_dirs = [d for d in data_path.iterdir() if d.is_dir() and d.name.startswith('chapter_')]
    chapter_dirs.sort()
    
    if not chapter_dirs:
        print(f"警告: 在 {data_dir} 中没有找到任何chapter目录")
        return
    
    # 初始化LLM客户端（如果启用自动改写）
    client = None
    if auto_rewrite:
        try:
            client = Ark(api_key=ARK_CONFIG['api_key'])
            print(f"已启用自动改写功能，将调用模型API改写超长内容")
        except Exception as e:
            print(f"警告: 无法初始化LLM客户端: {e}")
            print("将继续验证但不进行自动改写")
            auto_rewrite = False
    
    print(f"开始验证 {data_dir} 目录下的解说内容字数...")
    if auto_rewrite:
        print("自动改写模式: 启用")
    print("=" * 80)
    
    total_chapters = 0
    valid_chapters = 0
    issues_found = []
    rewritten_count = 0
    
    for chapter_dir in chapter_dirs:
        narration_file = chapter_dir / 'narration.txt'
        
        if not narration_file.exists():
            print(f"警告: {chapter_dir.name} 中没有找到 narration.txt 文件")
            continue
        
        total_chapters += 1
        results = validate_narration_file(str(narration_file), client, auto_rewrite)
        
        print(f"\n章节: {chapter_dir.name}")
        print(f"文件: {narration_file}")
        
        chapter_valid = True
        
        # 检查第一个特写
        first_closeup = results['first_closeup']
        if first_closeup['exists']:
            status = "✓" if first_closeup['valid'] else "✗"
            rewrite_info = " (已改写)" if first_closeup['rewritten'] else ""
            print(f"第一个特写: {status} {first_closeup['char_count']}字{rewrite_info} - {first_closeup['content'][:50]}{'...' if len(first_closeup['content']) > 50 else ''}")
            if first_closeup['rewritten']:
                rewritten_count += 1
            if not first_closeup['valid']:
                chapter_valid = False
                issues_found.append(f"{chapter_dir.name} 第一个特写: {first_closeup['char_count']}字")
        else:
            print("第一个特写: ✗ 未找到解说内容")
            chapter_valid = False
            issues_found.append(f"{chapter_dir.name} 第一个特写: 未找到解说内容")
        
        # 检查第二个特写
        second_closeup = results['second_closeup']
        if second_closeup['exists']:
            status = "✓" if second_closeup['valid'] else "✗"
            rewrite_info = " (已改写)" if second_closeup['rewritten'] else ""
            print(f"第二个特写: {status} {second_closeup['char_count']}字{rewrite_info} - {second_closeup['content'][:50]}{'...' if len(second_closeup['content']) > 50 else ''}")
            if second_closeup['rewritten']:
                rewritten_count += 1
            if not second_closeup['valid']:
                chapter_valid = False
                issues_found.append(f"{chapter_dir.name} 第二个特写: {second_closeup['char_count']}字")
        else:
            print("第二个特写: ✗ 未找到解说内容")
            chapter_valid = False
            issues_found.append(f"{chapter_dir.name} 第二个特写: 未找到解说内容")
        
        if chapter_valid:
            valid_chapters += 1
    
    # 输出总结
    print("\n" + "=" * 80)
    print(f"验证完成!")
    print(f"总章节数: {total_chapters}")
    print(f"符合要求的章节: {valid_chapters}")
    print(f"存在问题的章节: {total_chapters - valid_chapters}")
    if auto_rewrite:
        print(f"已改写的特写数量: {rewritten_count}")
    
    if issues_found:
        print("\n发现的问题:")
        for issue in issues_found:
            print(f"  - {issue}")
        if auto_rewrite:
            print("\n建议: 解说内容字数应精准控制在30-32字之间")
        else:
            print("\n建议: 解说内容字数应精准控制在30-32字之间")
            print("提示: 使用 --auto-rewrite 参数可自动改写超长内容")
    else:
        print("\n所有章节的解说内容字数都符合要求！")

def main():
    """
    主函数
    """
    import argparse
    
    parser = argparse.ArgumentParser(description='解说内容字数验证和自动改写脚本')
    parser.add_argument('data_dir', help='数据目录路径，例如: data/007')
    parser.add_argument('--auto-rewrite', action='store_true', 
                       help='启用自动改写功能，调用模型API改写超长内容')
    
    # 兼容旧的命令行格式
    if len(sys.argv) == 2 and not sys.argv[1].startswith('-'):
        # 旧格式: python validate_narration.py data/xxx
        data_dir = sys.argv[1]
        auto_rewrite = False
    else:
        # 新格式: python validate_narration.py data/xxx --auto-rewrite
        args = parser.parse_args()
        data_dir = args.data_dir
        auto_rewrite = args.auto_rewrite
    
    validate_data_directory(data_dir, auto_rewrite)

if __name__ == "__main__":
    main()