#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
解说内容字数验证和自动改写脚本
用于检查指定数据目录下所有章节的narration.txt文件中分镜1的第一个和第二个图片特写的解说内容字数
确保字数控制在30-32字，并检查总解说内容字数在1200-1700字之间，自动调用模型API改写不符合要求的内容

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
    使用LLM重写整个narration文件的解说内容，将总字数控制在1300-1700字之间
    
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
            emphasis = "总字数必须控制在1300-1700字之间"
        elif attempt == 1:
            emphasis = "总字数必须严格控制在1300-1700字之间，这是硬性要求"
        else:
            emphasis = f"总字数必须在1300-1700字之间，当前是第{attempt+1}次尝试，请务必满足字数要求"
            
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
                
                if 1300 <= total_chars <= 1700:
                    print(f"  重写成功: 满足1300-1700字要求")
                    return rewritten_narrations
                else:
                    print(f"  字数不符合要求({total_chars}字)，需要在1300-1700字之间，继续重试...")
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
    # 查找所有角色姓名
    name_pattern = r'<姓名>(.*?)</姓名>'
    names = re.findall(name_pattern, content)
    for name in names:
        character_names.add(name.strip())
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

def validate_narration_file(narration_file_path, client=None, auto_rewrite=False, auto_fix_characters=False, auto_fix_tags=False):
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
        total_valid = 1200 <= total_char_count <= 1700
        total_rewritten = False
        
        # 如果总字数不符合要求且启用自动改写
        if not total_valid and auto_rewrite and client:
            print(f"  总解说内容字数不符合要求({total_char_count}字)，需要在1200-1700字之间，正在重写...")
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
                total_valid = 1200 <= total_char_count <= 1700
        
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

def validate_data_directory(data_dir, auto_rewrite=False, auto_fix_characters=False, auto_fix_tags=False):
    """
    验证数据目录下所有章节的narration.txt文件
    
    Args:
        data_dir (str): 数据目录路径
        auto_rewrite (bool): 是否自动改写超长内容
        auto_fix_characters (bool): 是否自动修复缺失的角色定义
        auto_fix_tags (bool): 是否自动修复XML标签闭合问题
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
        results = validate_narration_file(str(narration_file), client, auto_rewrite, auto_fix_characters, auto_fix_tags)
        
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
        print(f"总解说字数: {total_status} {total_narration['total_char_count']}字{total_rewrite_info} (要求: 1300-1700字)")
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
            print("  - 总解说内容字数应控制在1300-1700字之间")
        else:
            print("\n建议: ")
            print("  - 分镜1的第一个和第二个特写解说字数应精准控制在30-32字之间")
            print("  - 总解说内容字数应控制在1300-1700字之间")
            print("提示: 使用 --auto-rewrite 参数可自动改写不符合要求的内容")
    else:
        print("\n所有章节的解说内容字数都符合要求！")

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
    
    # 兼容旧的命令行格式
    if len(sys.argv) == 2 and not sys.argv[1].startswith('-'):
        # 旧格式: python validate_narration.py data/xxx
        data_dir = sys.argv[1]
        auto_rewrite = False
        auto_fix_characters = False
        auto_fix_tags = False
    else:
        # 新格式: python validate_narration.py data/xxx --auto-fix
        args = parser.parse_args()
        data_dir = args.data_dir
        
        # 如果使用了新的--auto-fix参数，或者使用了旧的参数，都启用相应功能
        auto_rewrite = args.auto_fix or args.auto_rewrite
        auto_fix_characters = args.auto_fix or args.auto_fix_characters
        auto_fix_tags = args.auto_fix  # XML标签修复功能集成到--auto-fix中
        
        # 如果使用了旧参数，给出提示
        if args.auto_rewrite or args.auto_fix_characters:
            print("提示: --auto-rewrite 和 --auto-fix-characters 参数已合并为 --auto-fix")
            print("建议使用: python validate_narration.py data/xxx --auto-fix")
    
    validate_data_directory(data_dir, auto_rewrite, auto_fix_characters, auto_fix_tags)

if __name__ == "__main__":
    main()