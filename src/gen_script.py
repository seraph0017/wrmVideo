#!/usr/bin/env python3
# -*- coding: utf-8 -*-

import os
import sys
# 升级方舟 SDK 到最新版本 pip install -U 'volcengine-python-sdk[ark]'
from volcenginesdkarkruntime import Ark
from config import ARK_CONFIG

def read_novel_file(file_path):
    """
    读取小说文件内容
    
    Args:
        file_path: 小说文件路径
    
    Returns:
        str: 文件内容
    """
    try:
        with open(file_path, 'r', encoding='utf-8') as f:
            content = f.read().strip()
        return content
    except Exception as e:
        print(f"读取小说文件失败: {e}")
        return None

def split_text(text, max_chars=100000):
    """
    将长文本分割成较小的片段
    
    Args:
        text: 原始文本
        max_chars: 每个片段的最大字符数
    
    Returns:
        list: 文本片段列表
    """
    if len(text) <= max_chars:
        return [text]
    
    chunks = []
    start = 0
    
    while start < len(text):
        end = start + max_chars
        
        # 如果不是最后一个片段，尝试在句号或段落处分割
        if end < len(text):
            # 向前查找合适的分割点
            for i in range(end, max(start + max_chars // 2, end - 1000), -1):
                if text[i] in ['。', '！', '？', '\n\n']:
                    end = i + 1
                    break
        
        chunks.append(text[start:end])
        start = end
    
    return chunks

def generate_script_for_chunk(client, chunk_content, chunk_index, total_chunks, start_chapter_num=1):
    """
    为单个文本片段生成解说文案
    
    Args:
        client: Ark客户端
        chunk_content: 文本片段内容
        chunk_index: 当前片段索引（从1开始）
        total_chunks: 总片段数
        start_chapter_num: 起始章节编号
    
    Returns:
        str: 生成的解说文案
    """
    print(f"正在处理第 {chunk_index}/{total_chunks} 个文本片段...")
    
    response = client.chat.completions.create(
        model="doubao-seed-1.6-250615",
        messages=[
            {"role": "user", "content": f"""
            你的任务是根据给定的小说片段生成详细解说文案，每个文案要能撑起3 - 4分钟的音视频，需要对小说情节进行细致的描述和解读，而非概要，且要包含细节的台词。同时，为每个章节的解说文案分段映射不同的用于生成图片的prompt，以便配合解说文案一起合成视频。

重要要求：
1. 这是第 {chunk_index} 个片段，共 {total_chunks} 个片段
2. 章节编号从第{start_chapter_num}章开始，按顺序递增
3. 严格按照以下XML格式输出，确保格式完全一致：

<小说片段>
{chunk_content}
</小说片段>
### 解说文案内容要求
- 单个文案要能撑起3 - 4分钟的音视频，故事开头必须有包点，洗成白话，直白易懂。
- 根据片段内容生成相应数量的章节解说文案。
- 字幕注意断句，视频结尾不能突兀，要保证内容完整，不要话没说完就结束。

### 开场要求
开场可以从以下多个方向突出：
#### 热开场
- **高潮先行**：把精彩的部分提到前面。
- **动作引爆**：有一个人物有动作调度的事情。
- **强烈情绪**：把喜怒哀乐氛围瞬间拉到顶。
- **疑问开头**：以人为什么死了、人去哪了、人为什么被害了、人为什么被打了等疑问的方式作开头。
#### 前提开场
如玄幻小说，可采用"混沌未开，天地乱"这类引用章节或全书引述部分内容作开场。
#### 冷开场

### 规避内容要求
- 涉及士兵、军官的服装不能具象化出现，用同色制服代替。
- 台词内容不要涉及时政（类似发展类字眼）。
- 坚决不能出现对未成年人造成伤害的内容，例如：囚禁，伤害，辱骂，殴打，遗弃等。
- 带有明确不良影响的台词规避掉。
- 玄幻古装类的剧规避掉双修字眼。
- 现代言情类的规避掉：初夜，第一次，成人用品等字眼以及剧情。
- 类似"亲吻，脖颈"等台词避免出现，床上拥抱的画面禁止出现。

### 音效和音乐要求
- 为每个章节的解说文案推荐合适的音效和音乐。
- 开场要有吸引人的文案，氛围感要拉满。
- 背景音乐要和解说文案的声音一起结束。

### 输出格式要求（必须严格遵守）
请严格按照以下XML格式输出，不要添加任何额外的标签或分隔符：

<第X章节>
<解说内容>解说文案段落1</解说内容>
<图片prompt>用于生成图片的详细描述</图片prompt>

<解说内容>解说文案段落2</解说内容>
<图片prompt>用于生成图片的详细描述</图片prompt>
</第X章节>



so            """}
        ],
        thinking={
             "type": "disabled" # 不使用深度思考能力,
             # "type": "enabled" # 使用深度思考能力
             # "type": "auto" # 模型自行判断是否使用深度思考能力
        },
    )
    
    return response.choices[0].message.content

def fix_xml_tags(content):
    """
    修正XML标签对不上的问题
    
    Args:
        content: 原始内容
    
    Returns:
        str: 修正后的内容
    """
    import re
    
    # 修正章节标签
    content = re.sub(r'<第(\d+)章节([^>]*)>', r'<第\1章节>', content)
    content = re.sub(r'</第(\d+)章节([^>]*)>', r'</第\1章节>', content)
    
    # 修正解说内容标签
    content = re.sub(r'<解说内容([^>]*)>', r'<解说内容>', content)
    content = re.sub(r'</解说内容([^>]*)>', r'</解说内容>', content)
    
    # 修正图片prompt标签
    content = re.sub(r'<图片prompt([^>]*)>', r'<图片prompt>', content)
    content = re.sub(r'</图片prompt([^>]*)>', r'</图片prompt>', content)
    
    # 确保每个开始标签都有对应的结束标签
    lines = content.split('\n')
    fixed_lines = []
    
    for line in lines:
        line = line.strip()
        if not line:
            continue
            
        # 处理章节标签
        if re.match(r'<第\d+章节>', line):
            fixed_lines.append(line)
        elif re.match(r'</第\d+章节>', line):
            fixed_lines.append(line)
        # 处理解说内容
        elif line.startswith('<解说内容>'):
            if not line.endswith('</解说内容>'):
                # 如果没有结束标签，添加结束标签
                content_text = line[5:]  # 移除开始标签
                fixed_lines.append(f'<解说内容>{content_text}</解说内容>')
            else:
                fixed_lines.append(line)
        # 处理图片prompt
        elif line.startswith('<图片prompt>'):
            if not line.endswith('</图片prompt>'):
                # 如果没有结束标签，添加结束标签
                prompt_text = line[7:]  # 移除开始标签
                fixed_lines.append(f'<图片prompt>{prompt_text}</图片prompt>')
            else:
                fixed_lines.append(line)
        else:
            # 普通文本行，检查是否需要包装在标签中
            if line and not line.startswith('<') and not line.endswith('>'):
                # 如果是在章节内的普通文本，可能需要包装
                fixed_lines.append(line)
            else:
                fixed_lines.append(line)
    
    return '\n'.join(fixed_lines)

def split_chapters(script_content):
    """
    将脚本内容按章节分割
    
    Args:
        script_content: 完整的脚本内容
    
    Returns:
        list: 章节列表，每个元素是(章节号, 章节内容)
    """
    import re
    
    print(f"开始分割章节，内容长度: {len(script_content)}")
    
    # 修正XML标签
    script_content = fix_xml_tags(script_content)
    
    # 移除外层的<解说文案>标签
    script_content = re.sub(r'^<解说文案>\s*', '', script_content, flags=re.MULTILINE)
    script_content = re.sub(r'\s*</解说文案>\s*$', '', script_content, flags=re.MULTILINE)
    
    print("清理后的内容前100字符:", script_content[:100])
    
    # 按章节分割 - 更精确的模式，匹配对应的结束标签
    chapter_pattern = r'<第(\d+)章节>\s*(.*?)\s*</第\1章节>'
    chapters = re.findall(chapter_pattern, script_content, re.DOTALL)
    
    result = []
    for chapter_num, content in chapters:
        # 清理内容
        content = content.strip()
        if content:
            result.append((int(chapter_num), content))
            print(f"找到章节 {chapter_num}，内容长度: {len(content)}")
    
    # 如果没有找到完整的章节标签，尝试简单分割
    if not result:
        print("未找到完整章节标签，尝试简单分割...")
        # 尝试只匹配开始标签到下一个开始标签或结尾
        simple_pattern = r'<第(\d+)章节>\s*(.*?)(?=<第\d+章节>|$)'
        chapters = re.findall(simple_pattern, script_content, re.DOTALL)
        
        for chapter_num, content in chapters:
            content = content.strip()
            # 移除可能的结束标签
            content = re.sub(r'</第\d+章节>\s*$', '', content)
            if content:
                result.append((int(chapter_num), content))
                print(f"简单分割找到章节 {chapter_num}，内容长度: {len(content)}")
    
    print(f"总共找到 {len(result)} 个章节")
    return result

def save_chapters_to_folders(chapters, base_dir):
    """
    将章节保存到独立的文件夹中
    
    Args:
        chapters: 章节列表
        base_dir: 基础目录
    """
    import os
    
    for chapter_num, content in chapters:
        # 创建章节文件夹
        chapter_folder = os.path.join(base_dir, f'chapter{chapter_num:02d}')
        os.makedirs(chapter_folder, exist_ok=True)
        
        # 保存章节脚本
        script_file = os.path.join(chapter_folder, f'chapter{chapter_num:02d}_script.txt')
        
        # 构建完整的章节内容
        full_content = f'<第{chapter_num}章节>\n{content}\n</第{chapter_num}章节>'
        
        with open(script_file, 'w', encoding='utf-8') as f:
            f.write(full_content)
        
        print(f'章节 {chapter_num} 已保存到: {script_file}')

def merge_and_format_scripts(script_list):
    """
    合并多个脚本片段并统一格式
    
    Args:
        script_list: 脚本片段列表
    
    Returns:
        str: 格式化后的完整脚本
    """
    if not script_list:
        return ""
    
    # 移除每个片段开头的<解说文案>标签（如果存在）
    cleaned_scripts = []
    for script in script_list:
        if script:
            # 移除开头的<解说文案>标签
            cleaned = script.strip()
            if cleaned.startswith('<解说文案>'):
                cleaned = cleaned[5:].strip()
            if cleaned.endswith('</解说文案>'):
                cleaned = cleaned[:-6].strip()
            cleaned_scripts.append(cleaned)
    
    # 合并所有脚本
    merged_content = '\n\n'.join(cleaned_scripts)
    
    # 修正XML标签
    merged_content = fix_xml_tags(merged_content)
    
    # 重新编号章节，确保连续性
    import re
    
    # 找到所有章节标签
    chapter_pattern = r'<第(\d+)章节>'
    chapters = re.findall(chapter_pattern, merged_content)
    
    # 重新编号
    chapter_num = 1
    def replace_chapter(match):
        nonlocal chapter_num
        result = f'<第{chapter_num}章节>'
        chapter_num += 1
        return result
    
    # 替换章节编号
    formatted_content = re.sub(chapter_pattern, replace_chapter, merged_content)
    
    # 统一格式：将[内容]格式转换为<解说内容>格式
    # 处理解说内容
    formatted_content = re.sub(r'\[([^\]]+)\](?=\s*\n|\s*$)', r'<解说内容>\1</解说内容>', formatted_content)
    
    # 处理图片prompt格式统一
    formatted_content = re.sub(r'\[prompt:\s*([^\]]+)\]', r'<图片prompt>\1</图片prompt>', formatted_content)
    formatted_content = re.sub(r'<图片prompt>([^<]+)</图片prompt>', r'<图片prompt>\1</图片prompt>', formatted_content)
    
    # 添加根标签
    final_content = f'<解说文案>\n{formatted_content}\n</解说文案>'
    
    return final_content

def generate_script(novel_content, output_file=None):
    """
    生成解说文案
    
    Args:
        novel_content: 小说内容
        output_file: 输出文件路径（可选）
    
    Returns:
        str: 生成的解说文案
    """
    client = Ark(
        base_url=ARK_CONFIG['base_url'],
        api_key=ARK_CONFIG['api_key'],
        # 深度思考模型耗费时间会较长，请您设置较大的超时时间，避免超时，推荐30分钟以上
        timeout=1800,
    )
    
    # 检查文本长度，如果过长则分块处理
    if len(novel_content) > 100000:  # 约10万字符
        print(f"小说内容较长（{len(novel_content)}字符），将分块处理...")
        
        # 分割文本
        chunks = split_text(novel_content, max_chars=80000)
        print(f"已分割为 {len(chunks)} 个片段")
        
        all_scripts = []
        current_chapter_num = 1
        
        # 逐个处理片段
        for i, chunk in enumerate(chunks, 1):
            try:
                script_chunk = generate_script_for_chunk(client, chunk, i, len(chunks), current_chapter_num)
                all_scripts.append(script_chunk)
                print(f"第 {i} 个片段处理完成")
                
                # 计算下一个片段的起始章节号
                chapter_count = script_chunk.count('<第') if script_chunk else 0
                current_chapter_num += chapter_count
                
            except Exception as e:
                print(f"处理第 {i} 个片段时出错: {e}")
                continue
        
        # 合并所有解说文案并统一格式
        script_content = merge_and_format_scripts(all_scripts)
    else:
        print("正在生成解说文案，请耐心等待...")
        
        response = client.chat.completions.create(
            model="doubao-seed-1.6-250615",
            messages=[
                {"role": "user", "content": f"""
                你的任务是根据给定的小说生成不超过60个章节的详细解说文案，每个文案要能撑起3 - 4分钟的音视频，需要对小说情节进行细致的描述和解读，而非概要，且要包含细节的台词。同时，为每个章节的解说文案分段映射不同的用于生成图片的prompt，以便配合解说文案一起合成视频。以下是具体要求：
<小说>
{novel_content}
</小说>
### 解说文案内容要求
- 单个文案要能撑起3 - 4分钟的音视频，故事开头必须有包点，洗成白话，直白易懂。
- 共生成不超过60个章节的解说文案。
- 字幕注意断句，视频结尾不能突兀，要保证内容完整，不要话没说完就结束。

### 开场方式
#### 悬疑开头
- **悬疑开头**：以悬疑的方式作开头，如"这个男人为什么要杀死自己的妻子"、"这个女人为什么要背叛自己的丈夫"等。
- **反转开头**：以反转的方式作开头，如"你以为他是好人，其实他是坏人"、"你以为她是坏人，其实她是好人"等。
- **对比开头**：以对比的方式作开头，如"他是一个富二代，她是一个穷丫头"、"他是一个学霸，她是一个学渣"等。
- **疑问开头**：以人为什么死了、人去哪了、人为什么被害了、人为什么被打了等疑问的方式作开头。
#### 前提开场
如玄幻小说，可采用"混沌未开，天地乱"这类引用章节或全书引述部分内容作开场。
#### 冷开场

### 内容规避要求
- 避免出现敏感词汇和内容。
- 避免出现政治敏感内容。
- 避免出现暴力血腥内容的详细描述。
- 玄幻古装类的剧规避掉双修字眼。
- 现代言情类的规避掉：初夜，第一次，成人用品等字眼以及剧情。
- 类似"亲吻，脖颈"等台词避免出现，床上拥抱的画面禁止出现。

### 音效和音乐要求
- 背景音乐要符合剧情氛围。
- 音效要和画面同步。
- 背景音乐要和解说文案的声音一起结束。

### 输出格式要求（必须严格遵守）
请严格按照以下XML格式输出，不要添加任何额外的标签或分隔符：

<第X章节>
<解说内容>解说文案段落1</解说内容>
<图片prompt>用于生成图片的详细描述</图片prompt>

<解说内容>解说文案段落2</解说内容>
<图片prompt>用于生成图片的详细描述</图片prompt>
</第X章节>

                """}],
            thinking={
                 "type": "disabled" # 不使用深度思考能力,
                 # "type": "enabled" # 使用深度思考能力
                 # "type": "auto" # 模型自行判断是否使用深度思考能力
            },
        )
        
        script_content = response.choices[0].message.content
     
     # 如果指定了输出文件，则保存到文件
    if output_file and output_file.strip():
        try:
            # 确保输出目录存在
            output_dir = os.path.dirname(output_file)
            if output_dir:
                os.makedirs(output_dir, exist_ok=True)
            
            with open(output_file, 'w', encoding='utf-8') as f:
                f.write(script_content)
            print(f"解说文案已保存到: {output_file}")
        except Exception as e:
            print(f"保存文件失败: {e}")
    
    return script_content

def main():
    """
    主函数
    """
    if len(sys.argv) < 2:
        print("使用方法: python gen_script.py <小说文件路径> [输出文件路径]")
        print("示例: python gen_script.py data/novel.txt data/script.txt")
        sys.exit(1)
    
    novel_file = sys.argv[1]
    output_file = sys.argv[2] if len(sys.argv) > 2 else None
    
    # 检查小说文件是否存在
    if not os.path.exists(novel_file):
        print(f"错误: 小说文件 {novel_file} 不存在")
        sys.exit(1)
    
    print(f"开始处理小说文件: {novel_file}")
    
    # 读取小说内容
    novel_content = read_novel_file(novel_file)
    if not novel_content:
        print("读取小说内容失败")
        sys.exit(1)
    
    print(f"小说内容长度: {len(novel_content)} 字符")
    
    # 生成解说文案
    script_content = generate_script(novel_content, output_file)
    
    # 按章节分割并保存到独立文件夹
    if script_content:
        # 获取基础目录（小说文件所在目录）
        base_dir = os.path.dirname(novel_file)
        
        # 分割章节
        chapters = split_chapters(script_content)
        
        if chapters:
            print(f"\n检测到 {len(chapters)} 个章节，正在创建章节文件夹...")
            
            # 保存章节到独立文件夹
            save_chapters_to_folders(chapters, base_dir)
            
            print(f"\n所有章节已保存到 {base_dir} 目录下的各个章节文件夹中")
        else:
            print("\n警告: 未检测到有效的章节内容")
    
    if not output_file:
        print("\n=== 生成的解说文案 ===")
        print(script_content)
    
    print("\n=== 处理完成 ===")

if __name__ == '__main__':
    main()