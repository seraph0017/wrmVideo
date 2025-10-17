#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
解说内容字数验证和自动改写脚本
用于检查指定数据目录下所有章节的narration.txt文件中分镜1的第一个和第二个图片特写的解说内容字数
确保字数控制在30-32字，并检查总解说内容字数在850-1200字之间，自动调用模型API改写不符合要求的内容

使用方法:
python validate_narration.py data/xxx
python validate_narration.py data/xxx --auto-rewrite
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
    如果所有重试都无法达到30-32字要求，选择字数最少的那次结果保存
    
    Args:
        client: Ark客户端实例
        original_text (str): 原始解说内容
        max_retries (int): 最大重试次数，默认5次
        
    Returns:
        str: 改写后的解说内容，如果所有重试都失败则返回字数最少的结果
    """
    original_char_count = count_chinese_characters(original_text)
    print(f"  原文字数: {original_char_count}字")
    
    # 记录所有尝试的结果
    attempts_results = []
    
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
            
            # 记录这次尝试的结果
            attempts_results.append({
                'text': rewritten_text,
                'char_count': char_count,
                'attempt': attempt + 1
            })
            
            if 30 <= char_count <= 32:
                print(f"  改写成功: 满足30-32字要求")
                return rewritten_text
            else:
                print(f"  字数不符合要求({char_count}字)，继续重试...")
                
        except Exception as e:
            print(f"  第{attempt+1}次改写失败: {e}")
            
    # 如果所有重试都失败，选择最接近30-32字范围的结果
    if attempts_results:
        # 选择最接近30-32字范围的结果
        def distance_to_target(char_count):
            if char_count < 30:
                return 30 - char_count
            elif char_count > 32:
                return char_count - 32
            else:
                return 0  # 在范围内，距离为0
        
        best_result = min(attempts_results, key=lambda x: distance_to_target(x['char_count']))
        print(f"  所有{max_retries}次重试都未达到30-32字要求")
        print(f"  选择最接近30-32字的第{best_result['attempt']}次结果: {best_result['char_count']}字")
        print(f"  最终选择: {best_result['text']}")
        return best_result['text']
    else:
        print(f"  所有{max_retries}次重试都失败，保持原文")
        return original_text

def extract_all_narration_content(content):
    """
    提取narration.txt文件中所有的解说内容
    
    Args:
        content (str): narration.txt文件的完整内容
        
    Returns:
        list: 所有解说内容的列表
    """
    # 查找所有解说内容
    narration_pattern = r'<解说内容>(.*?)</解说内容>'
    narration_matches = re.findall(narration_pattern, content, re.DOTALL)
    
    # 清理并返回解说内容
    return [match.strip() for match in narration_matches if match.strip()]

def rewrite_entire_narration_with_llm(client, all_narrations, max_retries=3):
    """
    使用LLM重写整个narration文件的解说内容，将总字数控制在900-1200字之间
    
    Args:
        client: Ark客户端实例
        all_narrations (list): 所有解说内容的列表
        max_retries (int): 最大重试次数，默认3次
        
    Returns:
        list: 重写后的解说内容列表，如果失败则返回原列表
    """
    total_chars = sum(count_chinese_characters(narration) for narration in all_narrations)
    print(f"  原总字数: {total_chars}字")
    
    # 将所有解说内容合并为一个文本进行重写
    combined_text = "\n\n".join([f"解说{i+1}: {narration}" for i, narration in enumerate(all_narrations)])
    
    for attempt in range(max_retries):
        if attempt == 0:
            emphasis = "总字数必须控制在900-1200字之间"
        elif attempt == 1:
            emphasis = "总字数必须严格控制在900-1200字之间，这是硬性要求"
        else:
            emphasis = f"总字数必须在900-1200字之间，当前是第{attempt+1}次尝试，请务必满足字数要求"
            
        prompt = f"""请重写以下解说内容，要求：
1. {emphasis}（中文字符）
2. 保持原文的核心意思和情感色彩
3. 删除冗余词汇，保留关键情节
4. 语言要流畅自然，适合旁白解说
5. 保持解说的数量和顺序不变
6. 每个解说用"解说X: "开头，解说之间用两个换行符分隔
7. 只返回重写后的内容，不要任何解释

原文：
{combined_text}

重写后："""
        
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
            
            # 解析重写后的内容
            rewritten_narrations = []
            lines = rewritten_text.split('\n\n')
            for line in lines:
                if line.strip() and '解说' in line and ':' in line:
                    # 提取解说内容（去掉"解说X: "前缀）
                    content = line.split(':', 1)[1].strip()
                    if content:
                        rewritten_narrations.append(content)
            
            # 如果解析失败，尝试直接按换行分割
            if len(rewritten_narrations) != len(all_narrations):
                rewritten_narrations = [line.strip() for line in rewritten_text.split('\n') if line.strip()]
            
            # 验证重写后的总字数
            if len(rewritten_narrations) == len(all_narrations):
                total_chars = sum(count_chinese_characters(narration) for narration in rewritten_narrations)
                print(f"  第{attempt+1}次尝试: {total_chars}字")
                
                if 900 <= total_chars <= 1200:
                    print(f"  重写成功: 满足900-1200字要求")
                    return rewritten_narrations
                else:
                    print(f"  字数不符合要求({total_chars}字)，需要在900-1200字之间，继续重试...")
            else:
                print(f"  解说数量不匹配(原{len(all_narrations)}个，重写后{len(rewritten_narrations)}个)，继续重试...")
                
        except Exception as e:
            print(f"  第{attempt+1}次重写失败: {e}")
            
    print(f"  所有{max_retries}次重试都失败，保持原文")
    return all_narrations

def extract_character_names(content):
    """
    提取出镜人物列表中的所有角色姓名
    
    Args:
        content (str): narration.txt文件的完整内容
        
    Returns:
        set: 出镜人物的姓名集合
    """
    character_names = set()
    # 查找所有角色姓名（支持嵌套的<角色姓名>标签）
    name_pattern = r'<姓名>(.*?)</姓名>'
    names = re.findall(name_pattern, content, re.DOTALL)
    for name in names:
        name_content = name.strip()
        # 检查是否有嵌套的<角色姓名>标签
        role_name_match = re.search(r'<角色姓名>([^<]+)</角色姓名>', name_content)
        if role_name_match:
            character_names.add(role_name_match.group(1).strip())
        else:
            character_names.add(name_content)
    return character_names

def extract_closeup_characters(content):
    """
    从narration.txt内容中提取所有特写人物的姓名
    
    Args:
        content (str): narration.txt文件内容
        
    Returns:
        list: 特写人物姓名列表
    """
    closeup_characters = []
    
    # 查找所有特写人物
    closeup_pattern = r'<特写人物>(.*?)</特写人物>'
    matches = re.findall(closeup_pattern, content, re.DOTALL)
    
    for match in matches:
        character_name = match.strip()
        if character_name:
            closeup_characters.append(character_name)
    
    return closeup_characters

def generate_character_definition(character_name, context_content=""):
    """
    为缺失的角色生成默认的角色定义，根据角色名称和上下文内容智能推断性别和外貌特征
    
    Args:
        character_name (str): 角色姓名
        context_content (str): 相关的解说内容和图片描述，用于推断角色特征
        
    Returns:
        str: 角色定义的XML格式字符串
    """
    # 根据角色名称和上下文推断性别
    def infer_gender(name, context):
        # 女性相关关键词
        female_keywords = ['天女', '仙女', '公主', '娘娘', '夫人', '小姐', '姑娘', '妃', '后', '嫔', 
                          '美人', '佳人', '女', '妹', '姐', '母', '婆', '奶', '嫂', '媳', '姨', '姑',
                          '她', '女子', '女人', '女性', '少女', '女童', '女孩', '女儿', '女士']
        # 男性相关关键词
        male_keywords = ['王', '帝', '君', '公', '侯', '爷', '老爷', '少爷', '大人', '先生', 
                        '将军', '元帅', '统领', '长老', '掌门', '宗主', '祖师', '真人', '道长',
                        '他', '男子', '男人', '男性', '少年', '男童', '男孩', '儿子', '男士']
        
        # 首先检查角色名称
        for keyword in female_keywords:
            if keyword in name:
                return 'Female'
        
        for keyword in male_keywords:
            if keyword in name:
                return 'Male'
        
        # 然后检查上下文内容
        context_lower = context.lower()
        female_context_score = 0
        male_context_score = 0
        
        # 在上下文中查找与该角色相关的性别线索
        for keyword in female_keywords:
            if keyword in context and name in context:
                # 检查关键词和角色名是否在相近位置
                name_pos = context.find(name)
                keyword_pos = context.find(keyword)
                if abs(name_pos - keyword_pos) < 50:  # 在50个字符范围内
                    female_context_score += 1
        
        for keyword in male_keywords:
            if keyword in context and name in context:
                name_pos = context.find(name)
                keyword_pos = context.find(keyword)
                if abs(name_pos - keyword_pos) < 50:
                    male_context_score += 1
        
        # 根据上下文评分决定性别
        if female_context_score > male_context_score:
            return 'Female'
        elif male_context_score > female_context_score:
            return 'Male'
        
        # 默认返回Male
        return 'Male'
    
    # 根据性别生成对应的外貌和服装
    gender = infer_gender(character_name, context_content)
    
    if gender == 'Female':
        # 女性角色的外貌和服装
        character_def = f"""<角色>
<姓名>{character_name}</姓名>
<性别>Female</性别>
<年龄段>21-30_YoungAdult</年龄段>
<外貌特征>
<发型>长发，发髻</发型>
<发色>黑色</发色>
<面部特征>容貌秀美，眼神温婉</面部特征>
<身材特征>身材窈窕，体态优雅</身材特征>
<特殊标记>无</特殊标记>
</外貌特征>
<服装风格>
<上衣>古代女装，仙裙或宫装，色彩淡雅</上衣>
<下装>长裙，飘逸</下装>
<配饰>发饰，玉佩等精美饰品</配饰>
</服装风格>
</角色>"""
    else:
        # 男性角色的外貌和服装
        character_def = f"""<角色>
<姓名>{character_name}</姓名>
<性别>Male</性别>
<年龄段>31-45_MiddleAged</年龄段>
<外貌特征>
<发型>束发</发型>
<发色>黑色</发色>
<面部特征>面容威武，眼神坚毅</面部特征>
<身材特征>中等身材，体态端正</身材特征>
<特殊标记>无</特殊标记>
</外貌特征>
<服装风格>
<上衣>宋朝圆领袍，深色，丝质，领口高立</上衣>
<下装>同色系长裤，束脚</下装>
<配饰>腰带，无其他饰品</配饰>
</服装风格>
</角色>"""
    
    return character_def

def validate_and_fix_xml_tags(content):
    """
    检验和修复narration.txt文件中的XML标签闭合问题
    
    Args:
        content (str): narration.txt文件的完整内容
        
    Returns:
        tuple: (修复后的内容, 是否有修复, 错误列表)
    """
    errors = []
    fixed_content = content
    has_fixes = False
    
    # 检查常见的标签闭合问题
    tag_patterns = [
        (r'<特写人物>', r'</特写人物>'),
        (r'<角色姓名>', r'</角色姓名>'),
        (r'<时代背景>', r'</时代背景>'),
        (r'<角色形象>', r'</角色形象>'),
        (r'<解说内容>', r'</解说内容>'),
        (r'<图片prompt>', r'</图片prompt>'),
        (r'<图片特写\d+>', r'</图片特写\d+>'),
        (r'<分镜\d+>', r'</分镜\d+>')
    ]
    
    # 检查每种标签的开始和结束标签是否匹配
    for open_pattern, close_pattern in tag_patterns:
        open_tags = re.findall(open_pattern, fixed_content)
        close_tags = re.findall(close_pattern, fixed_content)
        
        if len(open_tags) != len(close_tags):
            errors.append(f"标签不匹配: {open_pattern} 开始标签{len(open_tags)}个，结束标签{len(close_tags)}个")
    
    # 特殊处理<特写人物>标签的闭合问题
    # 查找所有<特写人物>块，检查是否正确闭合
    closeup_blocks = re.finditer(r'<特写人物>(.*?)(?=<解说内容>|<图片prompt>|</图片特写\d+>|<图片特写\d+>|$)', fixed_content, re.DOTALL)
    
    for match in closeup_blocks:
        block_content = match.group(1)
        block_start = match.start()
        block_end = match.end()
        
        # 检查这个块是否有正确的</特写人物>标签
        if '</特写人物>' not in block_content:
            # 查找块内最后一个有效内容的位置
            last_tag_match = None
            for tag in ['</角色形象>', '</时代背景>', '</角色姓名>']:
                matches = list(re.finditer(re.escape(tag), block_content))
                if matches:
                    if last_tag_match is None or matches[-1].end() > last_tag_match.end():
                        last_tag_match = matches[-1]
            
            if last_tag_match:
                # 在最后一个标签后添加</特写人物>
                insert_pos = block_start + 1 + last_tag_match.end()  # +1 for '<特写人物>'
                fixed_content = (fixed_content[:insert_pos] + 
                               '\n</特写人物>' + 
                               fixed_content[insert_pos:])
                has_fixes = True
                errors.append(f"修复了缺失的</特写人物>标签")
    
    # 检查并修复多余的闭合标签
    # 使用栈来匹配开始和结束标签
    
    # 找到所有<特写人物>和</特写人物>标签的位置
    all_tags = []
    for match in re.finditer(r'<特写人物>', fixed_content):
        all_tags.append((match.start(), match.end(), 'open'))
    for match in re.finditer(r'</特写人物>', fixed_content):
        all_tags.append((match.start(), match.end(), 'close'))
    
    # 按位置排序
    all_tags.sort(key=lambda x: x[0])
    
    # 使用栈匹配标签，找出多余的闭合标签
    stack = []
    redundant_closes = []
    
    for start_pos, end_pos, tag_type in all_tags:
        if tag_type == 'open':
            stack.append((start_pos, end_pos))
        else:  # close
            if stack:
                stack.pop()  # 匹配成功
            else:
                # 没有对应的开始标签，这是多余的闭合标签
                redundant_closes.append((start_pos, end_pos))
    
    # 删除多余的闭合标签（从后往前删除，避免位置偏移）
    if redundant_closes:
        redundant_closes.sort(key=lambda x: x[0], reverse=True)
        for start_pos, end_pos in redundant_closes:
            # 删除多余的标签及其前后的空白字符
            before_tag = fixed_content[:start_pos].rstrip()
            after_tag = fixed_content[end_pos:].lstrip()
            fixed_content = before_tag + after_tag
            has_fixes = True
            errors.append(f"删除了多余的</特写人物>标签")
    
    return fixed_content, has_fixes, errors


def extract_scene_closeup_numbers(scene_content):
    """
    提取场景内容中的场景编号和特写编号
    
    Args:
        scene_content (str): 场景内容
        
    Returns:
        tuple: (场景编号, 特写编号列表)
    """
    # 提取场景编号
    scene_pattern = r'<scene_(\d+)>'
    scene_match = re.search(scene_pattern, scene_content)
    scene_number = int(scene_match.group(1)) if scene_match else None
    
    # 提取特写编号
    closeup_pattern = r'<closeup_(\d+)>'
    closeup_matches = re.findall(closeup_pattern, scene_content)
    closeup_numbers = [int(num) for num in closeup_matches]
    
    return scene_number, closeup_numbers


def validate_xml_structure_integrity(content):
    """
    检测XML结构的完整性，包括中文标签的场景和特写的编号连续性
    
    Args:
        content (str): narration.txt文件的完整内容
        
    Returns:
        list: 问题列表，每个问题是一个字典，包含scene_number, issue_type, details等字段
    """
    issues = []
    
    # 提取所有分镜（中文标签）
    scene_pattern = r'<分镜(\d+)>(.*?)(?=</分镜\1>|<分镜\d+>|$)'
    scene_matches = re.findall(scene_pattern, content, re.DOTALL)
    
    if not scene_matches:
        issues.append({
            'scene_number': None,
            'issue_type': 'no_scenes',
            'details': ['未找到任何分镜标签']
        })
        return issues
    
    # 检查分镜编号连续性
    scene_numbers = [int(num) for num, _ in scene_matches]
    expected_scene_numbers = list(range(1, len(scene_numbers) + 1))
    
    if scene_numbers != expected_scene_numbers:
        issues.append({
            'scene_number': None,
            'issue_type': 'discontinuous_scenes',
            'details': [f"分镜编号不连续: 期望 {expected_scene_numbers}, 实际 {scene_numbers}"]
        })
    
    # 检查每个分镜内的图片特写编号连续性和结构完整性
    for scene_num, scene_content in scene_matches:
        scene_num = int(scene_num)
        
        # 提取图片特写编号
        closeup_pattern = r'<图片特写(\d+)>'
        closeup_numbers = [int(num) for num in re.findall(closeup_pattern, scene_content)]
        
        if not closeup_numbers:
            issues.append({
                'scene_number': scene_num,
                'issue_type': 'no_closeups',
                'details': [f"分镜{scene_num}: 未找到任何图片特写"]
            })
            continue
        
        # 检查特写编号是否从1开始连续
        expected_closeup_numbers = list(range(1, len(closeup_numbers) + 1))
        
        if closeup_numbers != expected_closeup_numbers:
            issues.append({
                'scene_number': scene_num,
                'issue_type': 'discontinuous_closeups',
                'details': [f"分镜{scene_num}: 图片特写编号不连续，期望 {expected_closeup_numbers}, 实际 {closeup_numbers}"]
            })
        
        # 检查每个图片特写的结构完整性
        for closeup_num in closeup_numbers:
            # 检查是否有对应的结束标签
            closeup_start_pattern = f'<图片特写{closeup_num}>'
            closeup_end_pattern = f'</图片特写{closeup_num}>'
            
            start_matches = len(re.findall(closeup_start_pattern, scene_content))
            end_matches = len(re.findall(closeup_end_pattern, scene_content))
            
            if start_matches != end_matches:
                issues.append({
                    'scene_number': scene_num,
                    'issue_type': 'unmatched_tags',
                    'details': [f"分镜{scene_num}图片特写{closeup_num}: 开始标签({start_matches})和结束标签({end_matches})数量不匹配"]
                })
            
            # 检查图片特写内容的完整性
            closeup_content_pattern = f'<图片特写{closeup_num}>(.*?)(?=</图片特写{closeup_num}>|<图片特写\d+>|</分镜{scene_num}>|$)'
            closeup_match = re.search(closeup_content_pattern, scene_content, re.DOTALL)
            
            if closeup_match:
                closeup_content = closeup_match.group(1)
                required_tags = ['<特写人物>', '<解说内容>', '<图片prompt>']
                missing_tags = []
                
                for tag in required_tags:
                    if tag not in closeup_content:
                        missing_tags.append(tag)
                
                if missing_tags:
                    issues.append({
                        'scene_number': scene_num,
                        'issue_type': 'missing_tags',
                        'details': [f"分镜{scene_num}图片特写{closeup_num}: 缺少必要标签 {missing_tags}"]
                    })
    
    return issues


def fix_scene_structure_with_llm(client, scene_content, scene_number, issue_info, max_retries=3):
    """
    使用LLM修复分镜的XML结构问题
    
    Args:
        client: Ark客户端实例
        scene_content (str): 有问题的分镜内容
        scene_number (int): 分镜编号
        issue_info (dict): 问题信息，包含issue_type和details
        max_retries (int): 最大重试次数
        
    Returns:
        str: 修复后的内容（如果修复失败则返回原内容）
    """
    issue_type = issue_info.get('issue_type', 'unknown')
    details = issue_info.get('details', '')
    
    # 构建问题描述
    if issue_type == 'discontinuous_closeups':
        problem_desc = f"特写编号不连续: {details}"
    elif issue_type == 'no_closeups':
        problem_desc = "缺少特写内容"
    elif issue_type == 'missing_tags':
        problem_desc = f"缺少必要的XML标签: {details}"
    else:
        problem_desc = f"XML结构问题: {details}"
    
    for attempt in range(max_retries):
        prompt = f"""请修复以下分镜{scene_number}的XML结构问题。

问题描述: {problem_desc}

要求:
1. 确保图片特写编号从1开始连续递增（<图片特写1>, <图片特写2>, <图片特写3>...）
2. 每个图片特写必须包含以下标签：
   - <特写人物>（包含<角色姓名>）
   - <解说内容>
   - <图片prompt>
3. 保持原有内容的语义和风格
4. 确保XML标签正确闭合
5. 只返回修复后的分镜内容，不要包含<分镜{scene_number}>和</分镜{scene_number}>标签

原始分镜内容:
{scene_content}

修复后的分镜内容:"""

        try:
            resp = client.chat.completions.create(
                model="doubao-seed-1-6-flash-250715",
                messages=[
                    {
                        "role": "user",
                        "content": prompt
                    }
                ],
                temperature=0.3,
                max_tokens=4000
            )
            
            fixed_content = resp.choices[0].message.content.strip()
            
            # 验证修复后的内容
            test_content = f"<分镜{scene_number}>\n{fixed_content}\n</分镜{scene_number}>"
            test_issues = validate_xml_structure_integrity(test_content)
            
            if len(test_issues) == 0:
                print(f"  ✓ 场景{scene_number}结构修复成功（第{attempt+1}次尝试）")
                return fixed_content
            else:
                print(f"  ⚠ 场景{scene_number}修复后仍有{len(test_issues)}个问题（第{attempt+1}次尝试）")
                if attempt == max_retries - 1:
                    print(f"  ✗ 场景{scene_number}修复失败，已达到最大重试次数")
                    
        except Exception as e:
            print(f"  ✗ 场景{scene_number}修复时发生错误（第{attempt+1}次尝试）: {str(e)}")
            if attempt == max_retries - 1:
                print(f"  ✗ 场景{scene_number}修复失败，已达到最大重试次数")
    
    return scene_content

def clean_duplicate_tags(content):
    """
    清理重复的XML结束标签
    """
    import re
    
    # 清理重复的结束标签，使用更简单直接的方法
    # 匹配连续的相同结束标签
    pattern = r'(</[^>]+>)\1+'
    
    def replace_duplicates(match):
        return match.group(1)  # 只保留第一个标签
    
    # 重复执行直到没有更多重复标签
    prev_content = ""
    iterations = 0
    max_iterations = 10  # 防止无限循环
    
    while prev_content != content and iterations < max_iterations:
        prev_content = content
        content = re.sub(pattern, replace_duplicates, content)
        iterations += 1
        
        # 调试信息
        if iterations > 1:
            print(f"  清理重复标签第{iterations}轮")
    
    return content


def fix_closeup_structure_with_llm(client, closeup_content, scene_number, closeup_number, max_retries=3):
    """
    使用LLM修复单个图片特写的结构问题
    
    Args:
        client: LLM客户端
        closeup_content: 图片特写的原始内容
        scene_number: 分镜编号
        closeup_number: 图片特写编号
        max_retries: 最大重试次数
    
    Returns:
        修复后的图片特写内容
    """
    if not client:
        print(f"    警告: 未提供LLM客户端，跳过分镜{scene_number}图片特写{closeup_number}的修复")
        return closeup_content
    
    print(f"    使用LLM修复分镜{scene_number}图片特写{closeup_number}的结构问题...")
    
    prompt = f"""请修复以下图片特写的XML结构，确保包含所有必要的标签。

要求：
1. 必须包含以下标签结构：
   <图片特写{closeup_number}>
   <特写人物>
   <角色姓名>角色的姓名</角色姓名>
   <时代背景>现代/古代</时代背景>
   <角色形象>现代形象/古代形象</角色形象>
   </特写人物>
   <解说内容>约50字左右的解说内容</解说内容>
   <图片prompt>详细的图片描述</图片prompt>
   </图片特写{closeup_number}>

2. 保持原有内容的语义不变
3. 如果缺少某些信息，请根据上下文合理推断
4. 确保XML标签正确闭合
5. 只返回修复后的图片特写内容，不要任何解释

原始内容：
{closeup_content}

修复后的内容："""

    for attempt in range(max_retries):
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
            
            fixed_content = resp.choices[0].message.content.strip()
            
            # 后处理：清理重复的结束标签
            fixed_content = clean_duplicate_tags(fixed_content)
            
            # 验证修复后的内容是否包含必要标签
            required_tags = [
                f'<图片特写{closeup_number}>',
                f'</图片特写{closeup_number}>',
                '<特写人物>',
                '</特写人物>',
                '<角色姓名>',
                '</角色姓名>',
                '<解说内容>',
                '</解说内容>',
                '<图片prompt>',
                '</图片prompt>'
            ]
            
            missing_tags = [tag for tag in required_tags if tag not in fixed_content]
            
            if not missing_tags:
                print(f"    分镜{scene_number}图片特写{closeup_number}修复成功")
                return fixed_content
            else:
                print(f"    第{attempt+1}次尝试失败，缺少标签: {missing_tags}")
                
        except Exception as e:
            print(f"    第{attempt+1}次LLM调用失败: {str(e)}")
    
    print(f"    分镜{scene_number}图片特写{closeup_number}修复失败，返回原内容")
    return closeup_content


def fix_all_closeups_with_llm(content, client):
    """
    逐个修复所有分镜中的图片特写结构问题
    
    Args:
        content: narration.txt的完整内容
        client: LLM客户端
    
    Returns:
        修复后的完整内容
    """
    if not client:
        print("警告: 未提供LLM客户端，跳过图片特写修复")
        return content
    
    print("开始逐个修复所有图片特写的结构问题...")
    
    # 首先检测所有XML结构问题
    issues = validate_xml_structure_integrity(content)
    if not issues:
        print("未发现XML结构问题，无需修复")
        return content
    
    modified_content = content
    
    # 按分镜编号分组处理问题
    scene_issues = {}
    for issue in issues:
        scene_num = issue['scene_number']
        if scene_num not in scene_issues:
            scene_issues[scene_num] = []
        scene_issues[scene_num].append(issue)
    
    # 逐个分镜处理
    for scene_num in sorted(scene_issues.keys()):
        print(f"\n处理分镜{scene_num}的问题...")
        
        # 提取分镜内容
        scene_pattern = f'<分镜{scene_num}>(.*?)</分镜{scene_num}>'
        scene_match = re.search(scene_pattern, modified_content, re.DOTALL)
        
        if not scene_match:
            print(f"  未找到分镜{scene_num}的内容，跳过")
            continue
        
        scene_content = scene_match.group(1)
        original_scene_full = scene_match.group(0)
        
        # 提取所有图片特写
        closeup_pattern = r'<图片特写(\d+)>(.*?)(?=</图片特写\1>|<图片特写\d+>|</分镜\d+>|$)'
        closeup_matches = re.finditer(closeup_pattern, scene_content, re.DOTALL)
        
        modified_scene_content = scene_content
        
        # 逐个修复图片特写
        for closeup_match in closeup_matches:
            closeup_num = int(closeup_match.group(1))
            closeup_content = closeup_match.group(2)
            original_closeup = f"<图片特写{closeup_num}>{closeup_content}"
            
            # 检查这个图片特写是否有问题
            has_issues = any(
                f"图片特写{closeup_num}" in str(issue.get('details', []))
                for issue in scene_issues[scene_num]
            )
            
            if has_issues:
                print(f"  修复图片特写{closeup_num}...")
                
                # 使用LLM修复单个图片特写
                fixed_closeup = fix_closeup_structure_with_llm(
                    client, original_closeup, scene_num, closeup_num
                )
                
                # 替换修复后的内容
                if fixed_closeup != original_closeup:
                    # 确保修复后的内容以正确的结束标签结尾
                    if not fixed_closeup.endswith(f"</图片特写{closeup_num}>"):
                        fixed_closeup += f"</图片特写{closeup_num}>"
                    
                    modified_scene_content = modified_scene_content.replace(
                        original_closeup, fixed_closeup
                    )
                    print(f"  图片特写{closeup_num}修复完成")
                else:
                    print(f"  图片特写{closeup_num}修复失败")
        
        # 替换整个分镜的内容
        modified_scene_full = f"<分镜{scene_num}>{modified_scene_content}</分镜{scene_num}>"
        modified_content = modified_content.replace(original_scene_full, modified_scene_full)
    
    print("\n所有图片特写修复完成")
    return modified_content


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

def validate_narration_file(narration_file_path, client=None, auto_rewrite=False, auto_fix_characters=False, auto_fix_tags=False, auto_fix_structure=False):
    """
    验证单个narration.txt文件中分镜1的第一个和第二个图片特写的解说内容字数，以及总解说内容字数
    
    Args:
        narration_file_path (str): narration.txt文件路径
        client: Ark客户端实例，用于自动改写
        auto_rewrite (bool): 是否自动改写超长内容
        auto_fix_characters (bool): 是否自动修复缺失的角色定义
        auto_fix_tags (bool): 是否自动修复XML标签闭合问题
        
    Returns:
        dict: 验证结果，包含特写序号、内容、字数和是否符合要求，以及总字数信息
    """
    results = {
        'file_path': narration_file_path,
        'first_closeup': {'content': '', 'char_count': 0, 'valid': False, 'exists': False, 'rewritten': False},
        'second_closeup': {'content': '', 'char_count': 0, 'valid': False, 'exists': False, 'rewritten': False},
        'total_narration': {'total_char_count': 0, 'valid': True, 'rewritten': False},
        'character_validation': {'valid': True, 'invalid_characters': [], 'missing_characters': []},
        'tag_validation': {'valid': True, 'errors': [], 'fixed': False}
    }
    
    try:
        with open(narration_file_path, 'r', encoding='utf-8') as f:
            content = f.read()
            
        # 初始化更新内容变量
        updated_content = content
        content_updated = False
        
        # 检验和修复XML标签闭合问题
        fixed_content, has_tag_fixes, tag_errors = validate_and_fix_xml_tags(updated_content)
        
        # 更新标签验证结果
        results['tag_validation'] = {
            'valid': len(tag_errors) == 0 or has_tag_fixes,
            'errors': tag_errors,
            'fixed': has_tag_fixes
        }
        
        # 如果启用自动修复标签且有修复
        if auto_fix_tags and has_tag_fixes:
            print(f"  检测到标签闭合问题，正在自动修复...")
            for error in tag_errors:
                print(f"    {error}")
            updated_content = fixed_content
            content_updated = True
        elif tag_errors and not auto_fix_tags:
            print(f"  检测到标签闭合问题（使用--auto-fix可自动修复）:")
            for error in tag_errors:
                print(f"    {error}")
            
        # 验证特写人物是否在出镜人物列表中
        character_names = extract_character_names(updated_content)
        closeup_characters = extract_closeup_characters(updated_content)
        
        def should_ignore_character(char_name):
            """
            判断是否应该忽略某个角色名称（如通用角色名"角色x"等）
            """
            # 忽略"角色"开头后跟数字或字母的通用角色名
            if re.match(r'^角色[a-zA-Z0-9]+$', char_name):
                return True
            # 忽略单个字母或数字的角色名
            if re.match(r'^[a-zA-Z0-9]$', char_name):
                return True
            return False
        
        invalid_characters = []
        for closeup_char in closeup_characters:
            if closeup_char not in character_names and not should_ignore_character(closeup_char):
                invalid_characters.append(closeup_char)
        
        character_validation_valid = len(invalid_characters) == 0
        results['character_validation'] = {
            'valid': character_validation_valid,
            'invalid_characters': list(set(invalid_characters)),  # 去重
            'missing_characters': list(set(invalid_characters))   # 这里和invalid_characters相同
        }
        
        # XML结构完整性验证
        structure_issues = validate_xml_structure_integrity(updated_content)
        structure_validation_valid = len(structure_issues) == 0
        results['structure_validation'] = {
            'valid': structure_validation_valid,
            'issues': structure_issues
        }
        
        # 如果启用自动修复结构且存在结构问题
        if auto_fix_structure and not structure_validation_valid and client:
            print(f"  检测到{len(structure_issues)}个XML结构问题，正在使用LLM逐个修复图片特写...")
            
            # 使用新的修复函数修复所有图片特写
            fixed_content = fix_all_closeups_with_llm(updated_content, client)
            
            if fixed_content and fixed_content != updated_content:
                updated_content = fixed_content
                content_updated = True
                
                # 重新验证结构
                new_structure_issues = validate_xml_structure_integrity(updated_content)
                results['structure_validation'] = {
                    'valid': len(new_structure_issues) == 0,
                    'issues': new_structure_issues
                }
                if len(new_structure_issues) == 0:
                    print(f"  XML结构修复完成")
                else:
                    print(f"  XML结构修复后仍存在{len(new_structure_issues)}个问题")
            else:
                print(f"  XML结构修复失败或无需修复")
        elif len(structure_issues) > 0 and not auto_fix_structure:
            print(f"  检测到{len(structure_issues)}个XML结构问题（使用--auto-fix-structure可自动修复）:")
            for issue in structure_issues:
                print(f"    场景{issue['scene_number']}: {issue['issue_type']} - {issue['details']}")
        
        # 图片特写完整性检查和修复
        if auto_fix_structure and client:
            print(f"  检查图片特写完整性...")
            fixed_content, has_closeup_fixes = fix_incomplete_closeups_by_scene(client, updated_content)
            
            if has_closeup_fixes:
                updated_content = fixed_content
                content_updated = True
                print(f"  图片特写完整性修复完成")
            else:
                print(f"  所有图片特写都完整，无需修复")
        
        # 如果启用自动修复角色且存在缺失角色
        if auto_fix_characters and invalid_characters:
            print(f"  检测到缺失角色: {invalid_characters}，正在自动添加...")
            
            # 找到出镜人物列表的结束位置
            end_pattern = r'</出镜人物>'
            end_match = re.search(end_pattern, updated_content)
            
            if end_match:
                # 为每个缺失的角色生成定义
                new_characters_def = ""
                existing_role_numbers = re.findall(r'<角色(\d+)>', updated_content)
                next_role_number = max([int(num) for num in existing_role_numbers]) + 1 if existing_role_numbers else 1
                
                for char_name in set(invalid_characters):  # 去重
                    # 提取与该角色相关的上下文内容（解说内容和图片描述）
                    context_content = ""
                    
                    # 查找包含该角色名的解说内容
                    narration_pattern = r'<解说内容>([^<]*?' + re.escape(char_name) + r'[^<]*?)</解说内容>'
                    narration_matches = re.findall(narration_pattern, updated_content, re.DOTALL)
                    if narration_matches:
                        context_content += " ".join(narration_matches)
                    
                    # 查找包含该角色名的图片描述
                    image_desc_pattern = r'<图片描述>([^<]*?' + re.escape(char_name) + r'[^<]*?)</图片描述>'
                    image_desc_matches = re.findall(image_desc_pattern, updated_content, re.DOTALL)
                    if image_desc_matches:
                        context_content += " " + " ".join(image_desc_matches)
                    
                    char_def = generate_character_definition(char_name, context_content)
                    # 添加角色编号
                    char_def = char_def.replace('<角色>', f'<角色{next_role_number}>')
                    char_def = char_def.replace('</角色>', f'</角色{next_role_number}>')
                    new_characters_def += char_def + "\n"
                    next_role_number += 1
                
                # 在</出镜人物>之前插入新角色定义
                insert_position = end_match.start()
                updated_content = (updated_content[:insert_position] + 
                                 new_characters_def + 
                                 updated_content[insert_position:])
                content_updated = True
                
                # 更新验证结果
                results['character_validation']['valid'] = True
                results['character_validation']['invalid_characters'] = []
                results['character_validation']['missing_characters'] = []
                
                print(f"  已成功添加缺失角色: {list(set(invalid_characters))}")
        
        # 查找分镜1的第一个和第二个图片特写
        first_closeup, second_closeup = find_scene_closeups(content)
        
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
        
        # 检查总解说内容字数
        all_narrations = extract_all_narration_content(updated_content)
        total_char_count = sum(count_chinese_characters(narration) for narration in all_narrations)
        total_valid = 850 <= total_char_count <= 1200
        total_rewritten = False
        
        # 如果总字数不符合要求且启用自动改写
        if not total_valid and auto_rewrite and client:
            print(f"  总解说内容字数不符合要求({total_char_count}字)，需要在850-1200字之间，正在重写...")
            rewritten_narrations = rewrite_entire_narration_with_llm(client, all_narrations)
            
            if rewritten_narrations != all_narrations:
                total_rewritten = True
                # 替换文件中的所有解说内容
                temp_content = updated_content
                for i, (original, rewritten) in enumerate(zip(all_narrations, rewritten_narrations)):
                    if original != rewritten:
                        temp_content = temp_content.replace(f'<解说内容>{original}</解说内容>', f'<解说内容>{rewritten}</解说内容>', 1)
                
                updated_content = temp_content
                content_updated = True
                total_char_count = sum(count_chinese_characters(narration) for narration in rewritten_narrations)
                total_valid = 850 <= total_char_count <= 1200
        
        results['total_narration'] = {
            'total_char_count': total_char_count,
            'valid': total_valid,
            'rewritten': total_rewritten
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

def extract_character_descriptions(content):
    """
    从narration.txt内容中提取所有人物的详细描述
    
    Args:
        content (str): narration.txt文件的完整内容
        
    Returns:
        dict: 人物名称到描述的映射，格式为 {人物名称: 详细描述}
    """
    character_descriptions = {}
    
    # 匹配角色定义部分 - 修正为实际的XML标签格式
    character_pattern = r'<角色\d+>(.*?)</角色\d+>'
    character_matches = re.findall(character_pattern, content, re.DOTALL)
    
    for character_block in character_matches:
        # 提取人物名称 - 修正为实际的XML标签格式
        name_match = re.search(r'<角色姓名>(.*?)</角色姓名>', character_block)
        if not name_match:
            continue
        
        character_name = name_match.group(1).strip()
        
        # 提取各个描述字段
        description_parts = []
        
        # 性别
        gender_match = re.search(r'<性别>(.*?)</性别>', character_block)
        if gender_match:
            gender_text = gender_match.group(1).strip()
            # 转换英文性别为中文
            if gender_text.lower() == 'male':
                description_parts.append("性别：男")
            elif gender_text.lower() == 'female':
                description_parts.append("性别：女")
            else:
                description_parts.append(f"性别：{gender_text}")
        
        # 年龄段
        age_match = re.search(r'<年龄段>(.*?)</年龄段>', character_block)
        if age_match:
            age_text = age_match.group(1).strip()
            # 解析年龄段格式，如 "16-30_Young"
            if '_' in age_text:
                age_range = age_text.split('_')[0]
                description_parts.append(f"年龄：{age_range}岁")
            else:
                description_parts.append(f"年龄：{age_text}")
        
        # 外貌特征
        appearance_match = re.search(r'<外貌特征>(.*?)</外貌特征>', character_block, re.DOTALL)
        if appearance_match:
            appearance_text = appearance_match.group(1).strip()
            
            # 发型和发色
            hair_style_match = re.search(r'<发型>(.*?)</发型>', appearance_text)
            hair_color_match = re.search(r'<发色>(.*?)</发色>', appearance_text)
            if hair_style_match and hair_color_match:
                hair_style = hair_style_match.group(1).strip()
                hair_color = hair_color_match.group(1).strip()
                description_parts.append(f"头发：{hair_color}{hair_style}")
            elif hair_style_match:
                description_parts.append(f"发型：{hair_style_match.group(1).strip()}")
            
            # 面部特征
            face_match = re.search(r'<面部特征>(.*?)</面部特征>', appearance_text)
            if face_match:
                description_parts.append(f"面部：{face_match.group(1).strip()}")
            
            # 身材特征
            body_match = re.search(r'<身材特征>(.*?)</身材特征>', appearance_text)
            if body_match:
                description_parts.append(f"身材：{body_match.group(1).strip()}")
        
        # 服装风格
        clothing_match = re.search(r'<服装风格>(.*?)</服装风格>', character_block, re.DOTALL)
        if clothing_match:
            clothing_text = clothing_match.group(1).strip()
            
            # 上衣
            top_match = re.search(r'<上衣>(.*?)</上衣>', clothing_text)
            if top_match:
                description_parts.append(f"上衣：{top_match.group(1).strip()}")
            
            # 下装
            bottom_match = re.search(r'<下装>(.*?)</下装>', clothing_text)
            if bottom_match:
                description_parts.append(f"下装：{bottom_match.group(1).strip()}")
        
        # 组合完整描述
        if description_parts:
            character_descriptions[character_name] = "，".join(description_parts)
    
    return character_descriptions


def merge_character_description_to_prompt(prompt, character_name, character_descriptions):
    """
    将人物描述融合到图片prompt中
    
    Args:
        prompt (str): 原始图片prompt
        character_name (str): 人物名称
        character_descriptions (dict): 人物描述字典
        
    Returns:
        str: 融合了人物描述的新prompt
    """
    if character_name not in character_descriptions:
        return prompt
    
    character_desc = character_descriptions[character_name]
    
    # 如果prompt中已经包含了人物名称，则在其后添加描述
    if character_name in prompt:
        # 替换人物名称为"人物名称（描述）"的格式
        enhanced_prompt = prompt.replace(character_name, f"{character_name}（{character_desc}）")
    else:
        # 如果prompt中没有人物名称，则在开头添加人物描述
        enhanced_prompt = f"{character_name}（{character_desc}），{prompt}"
    
    return enhanced_prompt


def split_narration_by_closeups(narration_file_path, output_dir=None):
    """
    按人物特写拆分narration.txt文件，并融合人物描述到图片prompt中
    
    Args:
        narration_file_path (str): narration.txt文件路径
        output_dir (str): 输出目录，默认为narration.txt所在目录
        
    Returns:
        dict: 拆分结果统计信息
    """
    if output_dir is None:
        output_dir = os.path.dirname(narration_file_path)
    
    try:
        with open(narration_file_path, 'r', encoding='utf-8') as f:
            content = f.read()
    except Exception as e:
        return {"success": False, "error": f"读取文件失败: {str(e)}"}
    
    # 提取人物描述
    character_descriptions = extract_character_descriptions(content)
    
    # 提取所有分镜 - 修正为实际的XML标签格式
    scene_pattern = r'<分镜\d+>(.*?)</分镜\d+>'
    scene_matches = re.findall(scene_pattern, content, re.DOTALL)
    
    split_results = {
        "success": True,
        "total_scenes": len(scene_matches),
        "total_closeups": 0,
        "files_created": [],
        "character_descriptions_found": len(character_descriptions)
    }
    
    closeup_counter = 1
    
    for scene_idx, scene_content in enumerate(scene_matches, 1):
        # 提取该分镜中的所有图片特写 - 修正为实际的XML标签格式
        closeup_pattern = r'<图片特写\d+>(.*?)</图片特写\d+>'
        closeup_matches = re.findall(closeup_pattern, scene_content, re.DOTALL)
        
        for closeup_idx, closeup_content in enumerate(closeup_matches, 1):
            # 提取特写人物信息 - 修正为实际的XML标签格式
            character_match = re.search(r'<特写人物>(.*?)</特写人物>', closeup_content, re.DOTALL)
            if not character_match:
                continue
            
            character_info = character_match.group(1)
            
            # 提取角色姓名
            name_match = re.search(r'<角色姓名>(.*?)</角色姓名>', character_info)
            if not name_match:
                continue
            character_name = name_match.group(1).strip()
            
            # 提取时代背景（如果存在）
            era_match = re.search(r'<时代背景>(.*?)</时代背景>', character_info)
            era_background = era_match.group(1).strip() if era_match else ""
            
            # 提取角色形象（如果存在）
            image_match = re.search(r'<角色形象>(.*?)</角色形象>', character_info)
            character_image = image_match.group(1).strip() if image_match else ""
            
            # 提取解说内容
            narration_match = re.search(r'<解说内容>(.*?)</解说内容>', closeup_content)
            narration_content = narration_match.group(1).strip() if narration_match else ""
            
            # 提取图片prompt
            prompt_match = re.search(r'<图片prompt>(.*?)</图片prompt>', closeup_content)
            original_prompt = prompt_match.group(1).strip() if prompt_match else ""
            
            # 融合人物描述到prompt中
            enhanced_prompt = merge_character_description_to_prompt(
                original_prompt, character_name, character_descriptions
            )
            
            # 生成输出文件名 - 按照新的命名格式：scene_X_closeup_Y_角色名.txt
            # 处理文件名中的特殊字符
            safe_character_name = character_name.replace("/", "_").replace("\\", "_").replace(":", "_").replace("*", "_").replace("?", "_").replace("\"", "_").replace("<", "_").replace(">", "_").replace("|", "_")
            filename = f"scene_{scene_idx}_closeup_{closeup_idx}_{safe_character_name}.txt"
            output_file_path = os.path.join(output_dir, filename)
            
            # 生成输出内容
            output_content = f"""角色姓名: {character_name}
时代背景: {era_background}
角色形象: {character_image}
解说内容: {narration_content}
原始图片prompt: {original_prompt}
增强图片prompt: {enhanced_prompt}
分镜编号: {scene_idx}
特写编号: {closeup_idx}
"""
            
            # 写入文件
            try:
                with open(output_file_path, 'w', encoding='utf-8') as f:
                    f.write(output_content)
                
                split_results["files_created"].append(filename)
                split_results["total_closeups"] += 1
                closeup_counter += 1
                
            except Exception as e:
                split_results["success"] = False
                split_results["error"] = f"写入文件 {filename} 失败: {str(e)}"
                return split_results
    
    return split_results


def validate_data_directory(data_dir, auto_rewrite=False, auto_fix_characters=False, auto_fix_tags=False, auto_fix_structure=False):
    """
    验证数据目录下所有章节的narration.txt文件
    
    Args:
        data_dir (str): 数据目录路径
        auto_rewrite (bool): 是否自动改写超长内容
        auto_fix_characters (bool): 是否自动修复缺失的角色定义
        auto_fix_tags (bool): 是否自动修复XML标签闭合问题
        auto_fix_structure (bool): 是否自动修复XML结构问题
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
        results = validate_narration_file(str(narration_file), client, auto_rewrite, auto_fix_characters, auto_fix_tags, auto_fix_structure)
        
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
        
        # 检查总解说内容字数
        total_narration = results['total_narration']
        total_status = "✓" if total_narration['valid'] else "✗"
        total_rewrite_info = " (已重写)" if total_narration['rewritten'] else ""
        print(f"总解说字数: {total_status} {total_narration['total_char_count']}字{total_rewrite_info} (要求: 850-1200字)")
        if total_narration['rewritten']:
            rewritten_count += 1
        if not total_narration['valid']:
            chapter_valid = False
            issues_found.append(f"{chapter_dir.name} 总解说字数: {total_narration['total_char_count']}字")
        
        # 检查特写人物验证
        character_validation = results['character_validation']
        char_status = "✓" if character_validation['valid'] else "✗"
        print(f"特写人物验证: {char_status}", end="")
        if not character_validation['valid']:
            invalid_chars = character_validation['invalid_characters']
            print(f" (未在出镜人物中定义: {', '.join(invalid_chars)})")
            chapter_valid = False
            issues_found.append(f"{chapter_dir.name} 特写人物验证: 未定义角色 {', '.join(invalid_chars)}")
        else:
            print(" (所有特写人物均已在出镜人物中定义)")
        
        # 检查XML标签验证
        tag_validation = results['tag_validation']
        tag_status = "✓" if tag_validation['valid'] else "✗"
        print(f"XML标签验证: {tag_status}", end="")
        if not tag_validation['valid']:
            print(f" (发现{len(tag_validation['errors'])}个标签问题)")
            if not tag_validation['fixed']:
                chapter_valid = False
                issues_found.append(f"{chapter_dir.name} XML标签验证: {len(tag_validation['errors'])}个标签问题")
        elif tag_validation['fixed']:
            print(" (已自动修复标签问题)")
        else:
            print(" (所有XML标签正确闭合)")
        
        # 检查XML结构验证
        if 'structure_validation' in results:
            structure_validation = results['structure_validation']
            structure_status = "✓" if structure_validation['valid'] else "✗"
            print(f"XML结构验证: {structure_status}", end="")
            if not structure_validation['valid']:
                issue_count = len(structure_validation['issues'])
                print(f" (发现{issue_count}个结构问题)")
                if not auto_fix_structure:
                    chapter_valid = False
                    issues_found.append(f"{chapter_dir.name} XML结构验证: {issue_count}个结构问题")
            else:
                print(" (XML结构完整正确)")
        
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
            print("\n建议: ")
            print("  - 分镜1的第一个和第二个特写解说字数应精准控制在30-32字之间")
            print("  - 总解说内容字数应控制在850-1200字之间")
        else:
            print("\n建议: ")
            print("  - 分镜1的第一个和第二个特写解说字数应精准控制在30-32字之间")
            print("  - 总解说内容字数应控制在850-1200字之间")
            print("提示: 使用 --auto-rewrite 参数可自动改写不符合要求的内容")
    else:
        print("\n所有章节的解说内容字数都符合要求！")
    
    # 执行人物特写拆分
    print("\n" + "=" * 80)
    print("开始按人物特写拆分narration.txt文件...")
    
    split_summary = {
        "total_chapters_processed": 0,
        "total_files_created": 0,
        "total_closeups": 0,
        "chapters_with_errors": []
    }
    
    for chapter_dir in chapter_dirs:
        narration_file = chapter_dir / 'narration.txt'
        
        if not narration_file.exists():
            continue
        
        print(f"\n处理章节: {chapter_dir.name}")
        split_results = split_narration_by_closeups(str(narration_file))
        
        if split_results["success"]:
            split_summary["total_chapters_processed"] += 1
            split_summary["total_files_created"] += len(split_results["files_created"])
            split_summary["total_closeups"] += split_results["total_closeups"]
            
            print(f"  ✓ 成功拆分 {split_results['total_closeups']} 个人物特写")
            print(f"  ✓ 发现 {split_results['character_descriptions_found']} 个人物描述")
            print(f"  ✓ 创建文件: {', '.join(split_results['files_created'])}")
        else:
            split_summary["chapters_with_errors"].append({
                "chapter": chapter_dir.name,
                "error": split_results.get("error", "未知错误")
            })
            print(f"  ✗ 拆分失败: {split_results.get('error', '未知错误')}")
    
    # 输出拆分总结
    print("\n" + "=" * 80)
    print("拆分完成!")
    print(f"处理章节数: {split_summary['total_chapters_processed']}")
    print(f"创建文件数: {split_summary['total_files_created']}")
    print(f"总特写数量: {split_summary['total_closeups']}")
    
    if split_summary["chapters_with_errors"]:
        print(f"拆分失败章节: {len(split_summary['chapters_with_errors'])}")
        for error_info in split_summary["chapters_with_errors"]:
            print(f"  - {error_info['chapter']}: {error_info['error']}")
    else:
        print("所有章节都成功完成拆分！")

def main():
    """
    主函数
    """
    import argparse
    
    parser = argparse.ArgumentParser(description='解说内容字数验证和自动改写脚本')
    parser.add_argument('data_dir', help='数据目录路径，例如: data/007')
    parser.add_argument('--auto-fix', action='store_true', 
                       help='启用自动修复功能，包括改写超长内容和添加缺失的角色定义')
    # 保持向后兼容性
    parser.add_argument('--auto-rewrite', action='store_true', 
                       help='启用自动改写功能（已合并到--auto-fix中，保留用于兼容性）')
    parser.add_argument('--auto-fix-characters', action='store_true',
                       help='启用自动修复角色功能（已合并到--auto-fix中，保留用于兼容性）')
    parser.add_argument('--auto-fix-tags', action='store_true',
                       help='启用自动修复XML标签功能（已合并到--auto-fix中，保留用于兼容性）')
    parser.add_argument('--auto-fix-structure', action='store_true',
                       help='启用自动修复XML结构功能（已合并到--auto-fix中，保留用于兼容性）')
    
    # 兼容旧的命令行格式
    if len(sys.argv) == 2 and not sys.argv[1].startswith('-'):
        # 旧格式: python validate_narration.py data/xxx - 默认启用auto-fix功能
        data_dir = sys.argv[1]
        auto_rewrite = True  # 默认启用
        auto_fix_characters = True  # 默认启用
        auto_fix_tags = True  # 默认启用
        auto_fix_structure = True  # 默认启用
        print("提示: 已默认启用自动修复功能（包括改写、角色修复、标签修复、结构修复）")
    else:
        # 新格式: python validate_narration.py data/xxx --auto-fix
        args = parser.parse_args()
        data_dir = args.data_dir
        
        # 如果使用了新的--auto-fix参数，或者使用了旧的参数，都启用相应功能
        auto_rewrite = args.auto_fix or args.auto_rewrite
        auto_fix_characters = args.auto_fix or args.auto_fix_characters
        auto_fix_tags = args.auto_fix or args.auto_fix_tags  # XML标签修复功能集成到--auto-fix中
        auto_fix_structure = args.auto_fix or args.auto_fix_structure  # XML结构修复功能集成到--auto-fix中
        
        # 如果使用了旧参数，给出提示
        if args.auto_rewrite or args.auto_fix_characters or args.auto_fix_tags or args.auto_fix_structure:
            print("提示: --auto-rewrite、--auto-fix-characters、--auto-fix-tags 和 --auto-fix-structure 参数已合并为 --auto-fix")
            print("建议使用: python validate_narration.py data/xxx --auto-fix")
    
    validate_data_directory(data_dir, auto_rewrite, auto_fix_characters, auto_fix_tags, auto_fix_structure)

def fix_incomplete_closeups_by_scene(client, content):
    """
    按分镜修复不完整的图片特写，使用LLM根据模板补全缺失的标签
    
    Args:
        client: Ark客户端实例
        content (str): narration.txt文件的完整内容
        
    Returns:
        tuple: (修复后的内容, 是否有修复)
    """
    has_fixes = False
    fixed_content = content
    
    # 模板参考
    template = """<图片特写X>
<特写人物>
<角色姓名>角色名</角色姓名>
</特写人物>
<解说内容>约50字的解说内容...</解说内容>
<图片prompt>详细的图片描述...</图片prompt>
</图片特写X>"""
    
    # 提取所有分镜
    scene_pattern = r'(<分镜\d+>)(.*?)(</分镜\d+>)'
    scenes = re.finditer(scene_pattern, content, re.DOTALL)
    
    for scene_match in scenes:
        scene_start_tag = scene_match.group(1)
        scene_content = scene_match.group(2)
        scene_end_tag = scene_match.group(3)
        scene_number = re.search(r'分镜(\d+)', scene_start_tag).group(1)
        
        print(f"检查{scene_start_tag}...")
        
        # 检查这个分镜中的图片特写是否完整
        closeup_pattern = r'<图片特写(\d+)>(.*?)</图片特写\1>'
        closeups = list(re.finditer(closeup_pattern, scene_content, re.DOTALL))
        
        scene_needs_fix = False
        for closeup_match in closeups:
            closeup_content = closeup_match.group(2)
            closeup_number = closeup_match.group(1)
            
            # 检查是否缺少必需标签
            has_character = '<特写人物>' in closeup_content and '</特写人物>' in closeup_content
            has_narration = '<解说内容>' in closeup_content and '</解说内容>' in closeup_content
            has_prompt = '<图片prompt>' in closeup_content and '</图片prompt>' in closeup_content
            
            if not (has_character and has_narration and has_prompt):
                print(f"  发现<图片特写{closeup_number}>不完整: 特写人物={has_character}, 解说内容={has_narration}, 图片prompt={has_prompt}")
                scene_needs_fix = True
                break
        
        # 如果分镜需要修复，使用LLM修复整个分镜
        if scene_needs_fix:
            print(f"  使用LLM修复{scene_start_tag}...")
            
            prompt = f"""请修复以下分镜内容，确保每个<图片特写X>都包含完整的三个标签：<特写人物>、<解说内容>、<图片prompt>

参考模板格式：
{template}

要求：
1. 保持原有的图片特写数量和编号
2. 如果缺少<特写人物>，根据<图片prompt>中的角色信息补充
3. 如果缺少<解说内容>，根据<图片prompt>生成约50字的解说
4. 保持原有内容不变，只补充缺失的标签
5. 只返回修复后的分镜内容，不要解释

原分镜内容：
{scene_start_tag}
{scene_content}
{scene_end_tag}

修复后："""
            
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
                
                fixed_scene = resp.choices[0].message.content.strip()
                
                # 替换原分镜内容
                original_scene = scene_match.group(0)
                fixed_content = fixed_content.replace(original_scene, fixed_scene)
                has_fixes = True
                print(f"  {scene_start_tag}修复完成")
                
            except Exception as e:
                print(f"  {scene_start_tag}修复失败: {e}")
    
    return fixed_content, has_fixes

if __name__ == "__main__":
    main()