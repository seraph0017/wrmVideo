#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
脚本生成模块
使用配置化的prompt模板
"""

import os
import sys
import re
import json
from typing import List, Dict, Optional, Tuple
from volcenginesdkarkruntime import Ark

# 添加项目根目录到路径
project_root = os.path.dirname(os.path.dirname(os.path.dirname(__file__)))
sys.path.insert(0, project_root)

from config.prompt_config import prompt_config, SCRIPT_CONFIG
from config.config import ARK_CONFIG

class ScriptGenerator:
    """
    脚本生成器类
    """
    
    def __init__(self, api_key: Optional[str] = None):
        """
        初始化脚本生成器
        
        Args:
            api_key: API密钥
        """
        self.api_key = api_key or ARK_CONFIG.get('api_key') or os.getenv('ARK_API_KEY')
        if not self.api_key:
            raise ValueError("请设置ARK_API_KEY环境变量或在config.py中配置api_key参数")
        
        self.client = Ark(api_key=self.api_key)
        self.model = ARK_CONFIG.get('model', 'doubao-seed-1.6-250615')
    
    def read_novel_file(self, file_path: str) -> str:
        """
        读取小说文件
        
        Args:
            file_path: 文件路径
        
        Returns:
            str: 文件内容
        """
        try:
            with open(file_path, 'r', encoding='utf-8') as f:
                return f.read()
        except Exception as e:
            print(f"读取文件失败：{e}")
            return ""
    
    def split_text(self, text: str, chunk_size: int = None) -> List[str]:
        """
        将文本分割成块
        
        Args:
            text: 要分割的文本
            chunk_size: 块大小
        
        Returns:
            List[str]: 分割后的文本块
        """
        if chunk_size is None:
            chunk_size = SCRIPT_CONFIG['chunk_size']
        
        chunks = []
        for i in range(0, len(text), chunk_size):
            chunk = text[i:i + chunk_size]
            chunks.append(chunk)
        
        return chunks
    
    def generate_script_for_chunk(self, content: str, chunk_index: int = 0, 
                                total_chunks: int = 1, **kwargs) -> str:
        """
        为文本块生成脚本
        
        Args:
            content: 文本内容
            chunk_index: 当前块索引
            total_chunks: 总块数
            **kwargs: 其他参数
        
        Returns:
            str: 生成的脚本
        """
        try:
            # 使用配置管理器生成prompt
            prompt = prompt_config.get_script_prompt(
                content=content,
                is_chunk=(total_chunks > 1),
                chunk_index=chunk_index,
                total_chunks=total_chunks,
                **kwargs
            )
            
            print(f"正在生成第 {chunk_index + 1}/{total_chunks} 个脚本片段...")
            
            # 调用API
            completion = self.client.chat.completions.create(
                model=self.model,
                messages=[
                    {"role": "user", "content": prompt}
                ],
                stream=False
            )
            
            response = completion.choices[0].message.content
            print(f"第 {chunk_index + 1} 个片段生成完成")
            
            return response
            
        except Exception as e:
            print(f"生成脚本时出错：{e}")
            return ""
    
    def fix_xml_tags(self, content: str) -> str:
        """
        修复XML标签
        
        Args:
            content: 原始内容
        
        Returns:
            str: 修复后的内容
        """
        # 移除可能的markdown代码块标记
        content = re.sub(r'```xml\s*', '', content)
        content = re.sub(r'```\s*$', '', content)
        
        # 确保有根标签
        if not content.strip().startswith('<script>'):
            content = f'<script>\n{content}\n</script>'
        
        # 修复常见的XML问题
        content = re.sub(r'<([^>]+)>([^<]*)</([^>]+)>', 
                        lambda m: f'<{m.group(1)}>{m.group(2)}</{m.group(1)}>' 
                        if m.group(1) == m.group(3) else m.group(0), content)
        
        return content
    
    def split_chapters(self, script_content: str) -> List[Dict]:
        """
        将脚本内容按章节分割，支持每个章节包含多个分镜
        
        Args:
            script_content: 脚本内容
        
        Returns:
            List[Dict]: 章节列表，每个章节包含多个分镜
        """
        chapters = []
        
        # 查找所有章节 - 支持两种格式：<第X章节> 和 <chapter>
        chapter_pattern1 = r'<第(\d+)章节>(.*?)</第\d+章节>'
        chapter_pattern2 = r'<chapter\s+id="(\d+)"[^>]*>(.*?)</chapter>'
        
        # 先尝试第一种格式
        matches = re.findall(chapter_pattern1, script_content, re.DOTALL)
        if not matches:
            # 如果没有匹配，尝试第二种格式
            matches = re.findall(chapter_pattern2, script_content, re.DOTALL)
        
        if matches:
            # 有明确的章节标签
            for chapter_id, chapter_content in matches:
                # 提取所有解说内容和图片prompt对
                narration_matches = re.findall(r'<(?:解说内容|narration)>(.*?)</(?:解说内容|narration)>', 
                                             chapter_content, re.DOTALL)
                image_matches = re.findall(r'<(?:图片prompt|image_prompt)>(.*?)</(?:图片prompt|image_prompt)>', 
                                         chapter_content, re.DOTALL)
                
                # 确保解说内容和图片prompt数量匹配
                max_scenes = max(len(narration_matches), len(image_matches))
                
                if max_scenes > 0:
                    # 如果有多个分镜，创建包含所有分镜的章节
                    scenes = []
                    for i in range(max_scenes):
                        narration = narration_matches[i].strip() if i < len(narration_matches) else ""
                        image_prompt = image_matches[i].strip() if i < len(image_matches) else ""
                        scenes.append({
                            'narration': narration,
                            'image_prompt': image_prompt
                        })
                    
                    chapters.append({
                        'id': int(chapter_id),
                        'scenes': scenes,
                        # 为了向后兼容，保留原有的narration和image_prompt字段（使用第一个分镜）
                        'narration': scenes[0]['narration'] if scenes else "",
                        'image_prompt': scenes[0]['image_prompt'] if scenes else ""
                    })
                else:
                    # 如果没有找到分镜，创建空章节
                    chapters.append({
                        'id': int(chapter_id),
                        'scenes': [],
                        'narration': "",
                        'image_prompt': ""
                    })
        else:
            # 没有明确的章节标签，尝试直接提取解说内容和图片prompt
            narration_pattern = r'<(?:解说内容|narration)>(.*?)</(?:解说内容|narration)>'
            image_pattern = r'<(?:图片prompt|image_prompt)>(.*?)</(?:图片prompt|image_prompt)>'
            
            narration_matches = re.findall(narration_pattern, script_content, re.DOTALL)
            image_matches = re.findall(image_pattern, script_content, re.DOTALL)
            
            # 将每对解说内容和图片prompt组合成一个章节
            max_chapters = max(len(narration_matches), len(image_matches))
            for i in range(max_chapters):
                narration = narration_matches[i].strip() if i < len(narration_matches) else ""
                image_prompt = image_matches[i].strip() if i < len(image_matches) else ""
                
                chapters.append({
                    'id': i + 1,
                    'scenes': [{'narration': narration, 'image_prompt': image_prompt}],
                    'narration': narration,
                    'image_prompt': image_prompt
                })
        
        return chapters
    
    def save_chapters_to_folders(self, chapters: List[Dict], base_dir: str) -> bool:
        """
        将章节保存到文件夹，支持每个章节包含多个分镜
        
        Args:
            chapters: 章节列表
            base_dir: 基础目录
        
        Returns:
            bool: 是否保存成功
        """
        try:
            os.makedirs(base_dir, exist_ok=True)
            
            for chapter in chapters:
                chapter_dir = os.path.join(base_dir, f"chapter_{chapter['id']:03d}")
                os.makedirs(chapter_dir, exist_ok=True)
                
                # 检查是否有多个分镜
                if 'scenes' in chapter and chapter['scenes']:
                    # 有多个分镜，为每个分镜创建单独的文件
                    for i, scene in enumerate(chapter['scenes']):
                        scene_num = i + 1
                        
                        # 保存解说文本
                        narration_file = os.path.join(chapter_dir, f"narration_{scene_num:02d}.txt")
                        with open(narration_file, 'w', encoding='utf-8') as f:
                            f.write(scene['narration'])
                        
                        # 保存图片prompt
                        prompt_file = os.path.join(chapter_dir, f"image_prompt_{scene_num:02d}.txt")
                        with open(prompt_file, 'w', encoding='utf-8') as f:
                            f.write(scene['image_prompt'])
                    
                    # 同时保存合并的文件（向后兼容）
                    all_narrations = '\n\n'.join([scene['narration'] for scene in chapter['scenes'] if scene['narration']])
                    all_prompts = '\n\n'.join([scene['image_prompt'] for scene in chapter['scenes'] if scene['image_prompt']])
                    
                    narration_file = os.path.join(chapter_dir, "narration.txt")
                    with open(narration_file, 'w', encoding='utf-8') as f:
                        f.write(all_narrations)
                    
                    prompt_file = os.path.join(chapter_dir, "image_prompt.txt")
                    with open(prompt_file, 'w', encoding='utf-8') as f:
                        f.write(all_prompts)
                    
                    print(f"章节 {chapter['id']} 已保存到 {chapter_dir}（包含 {len(chapter['scenes'])} 个分镜）")
                else:
                    # 向后兼容：只有单个分镜的情况
                    narration_file = os.path.join(chapter_dir, "narration.txt")
                    with open(narration_file, 'w', encoding='utf-8') as f:
                        f.write(chapter.get('narration', ''))
                    
                    prompt_file = os.path.join(chapter_dir, "image_prompt.txt")
                    with open(prompt_file, 'w', encoding='utf-8') as f:
                        f.write(chapter.get('image_prompt', ''))
                    
                    print(f"章节 {chapter['id']} 已保存到 {chapter_dir}（单个分镜）")
            
            return True
            
        except Exception as e:
            print(f"保存章节时出错：{e}")
            return False
    
    def merge_and_format_scripts(self, scripts: List[str]) -> str:
        """
        合并和格式化脚本
        
        Args:
            scripts: 脚本列表
        
        Returns:
            str: 合并后的脚本
        """
        merged_content = ""
        chapter_counter = 1
        
        for script in scripts:
            if not script.strip():
                continue
            
            # 修复XML标签
            fixed_script = self.fix_xml_tags(script)
            
            # 提取章节内容
            chapters = self.split_chapters(fixed_script)
            
            for chapter in chapters:
                # 重新编号章节
                chapter_xml = f'''<chapter id="{chapter_counter}">\n<narration>{chapter['narration']}</narration>\n<image_prompt>{chapter['image_prompt']}</image_prompt>\n</chapter>\n\n'''
                merged_content += chapter_xml
                chapter_counter += 1
        
        # 添加根标签
        final_script = f'<script>\n{merged_content}</script>'
        
        return final_script
    
    def generate_script(self, novel_content: str, output_dir: str = "output", 
                       **kwargs) -> bool:
        """
        生成完整脚本
        
        Args:
            novel_content: 小说内容
            output_dir: 输出目录
            **kwargs: 其他参数
        
        Returns:
            bool: 是否生成成功
        """
        try:
            print(f"开始生成脚本，内容长度：{len(novel_content)} 字符")
            
            # 检查内容长度
            max_chunk_size = SCRIPT_CONFIG['max_chunk_size']
            if len(novel_content) <= max_chunk_size:
                # 单次处理
                print("内容较短，使用单次处理模式")
                script = self.generate_script_for_chunk(novel_content, **kwargs)
                scripts = [script] if script else []
            else:
                # 分块处理
                print("内容较长，使用分块处理模式")
                chunks = self.split_text(novel_content)
                print(f"分割为 {len(chunks)} 个块")
                
                scripts = []
                for i, chunk in enumerate(chunks):
                    script = self.generate_script_for_chunk(
                        chunk, i, len(chunks), **kwargs
                    )
                    if script:
                        scripts.append(script)
            
            if not scripts:
                print("没有生成任何脚本内容")
                return False
            
            # 合并脚本
            print("正在合并脚本...")
            print(f"待合并的脚本数量: {len(scripts)}")
            for i, script in enumerate(scripts):
                print(f"脚本 {i+1} 长度: {len(script)} 字符")
            
            merged_script = self.merge_and_format_scripts(scripts)
            print(f"合并后脚本长度: {len(merged_script)} 字符")
            
            # 保存合并后的脚本
            os.makedirs(output_dir, exist_ok=True)
            script_file = os.path.join(output_dir, "merged_script.xml")
            with open(script_file, 'w', encoding='utf-8') as f:
                f.write(merged_script)
            
            print(f"合并脚本已保存：{script_file}")
            
            # 分割章节并保存
            chapters = self.split_chapters(merged_script)
            print(f"从合并脚本中解析到 {len(chapters)} 个章节")
            
            if chapters:
                print(f"共生成 {len(chapters)} 个章节")
                success = self.save_chapters_to_folders(chapters, output_dir)
                if success:
                    print(f"所有章节已保存到：{output_dir}")
                    return True
                else:
                    print("保存章节失败")
                    return False
            else:
                print("没有解析到任何章节")
                print(f"合并脚本内容预览: {merged_script[:200]}...")
                return False
            
        except Exception as e:
            print(f"生成脚本时出错：{e}")
            return False

def main():
    """
    主函数，用于测试
    """
    print("脚本生成模块测试")
    print("=" * 50)
    
    # 检查API密钥
    api_key = os.getenv('ARK_API_KEY')
    if not api_key:
        print("请设置ARK_API_KEY环境变量")
        return
    
    # 创建脚本生成器
    generator = ScriptGenerator()
    
    # 测试文本
    test_content = """
    在一个遥远的古代王国里，有一位年轻的剑客名叫李明。他从小就展现出了非凡的武艺天赋，
    但是他的师父告诉他，真正的武者不仅要有高超的剑术，更要有一颗善良的心。
    
    一天，李明在山中修炼时，遇到了一群山贼正在劫掠一个商队。商队中有老人和孩子，
    他们惊恐地哭喊着。李明毫不犹豫地冲了出去，用他的剑法击退了山贼，救下了商队。
    
    商队的领头人是一位富商，他感激地要给李明重金作为报酬，但李明拒绝了。
    他说："行侠仗义是武者的本分，不需要报酬。"
    """
    
    # 生成脚本
    print("\n开始生成测试脚本...")
    success = generator.generate_script(test_content, "test_output")
    
    if success:
        print("\n✓ 脚本生成成功！")
    else:
        print("\n✗ 脚本生成失败！")

if __name__ == "__main__":
    main()