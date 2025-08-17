#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
gen_script_v2.py - 增强版脚本生成器

基于gen_script.py的增强版本，新增功能：
1. 自动章节质量验证
2. 不达标章节自动重新生成
3. 支持指定生成前N个章节
4. 增强的验证和重试机制

使用方法:
    python gen_script_v2.py novel.txt --output data/001 --chapters 5
    python gen_script_v2.py novel.txt --output data/001 --validate-only
"""

import os
import sys
import re
import json
import argparse
import tempfile
import zipfile
import shutil
import time
from pathlib import Path
from typing import List, Dict, Optional, Tuple
from concurrent.futures import ThreadPoolExecutor, as_completed
import threading
from volcenginesdkarkruntime import Ark
from jinja2 import Environment, FileSystemLoader
try:
    import rarfile
except ImportError:
    rarfile = None

# 添加项目根目录到路径
project_root = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, project_root)

from config.prompt_config import prompt_config, SCRIPT_CONFIG
from config.config import ARK_CONFIG

class ScriptGeneratorV2:
    """
    增强版脚本生成器
    
    新增功能：
    - 自动章节质量验证
    - 不达标章节重新生成
    - 支持指定生成章节数量
    - 增强的验证机制
    """
    
    def __init__(self, api_key: Optional[str] = None):
        """
        初始化脚本生成器
        
        Args:
            api_key: API密钥，如果不提供则从配置文件读取
        """
        self.api_key = api_key or ARK_CONFIG.get('api_key')
        if not self.api_key:
            raise ValueError("API密钥未配置")
        
        self.client = Ark(api_key=self.api_key)
        self.model = ARK_CONFIG.get('model', 'doubao-seed-1-6-flash-250615')
        self.lock = threading.Lock()
        print(f"使用模型: {self.model}")
        
        # 验证配置
        self.validation_config = {
            'min_length': 1200,  # 根据模板要求，解说内容总字数约1500字
            'max_length': 1800,  # 允许一定范围的浮动
            'max_retries': 3,
            'quality_threshold': 0.8  # 质量阈值
        }
    
    def read_novel_file(self, file_path: str) -> str:
        """
        读取小说文件，支持多种格式和编码
        
        Args:
            file_path: 小说文件路径
            
        Returns:
            str: 小说内容
        """
        if not os.path.exists(file_path):
            raise FileNotFoundError(f"文件不存在：{file_path}")
        
        file_ext = os.path.splitext(file_path)[1].lower()
        
        if file_ext == '.zip':
            return self._read_zip_file(file_path)
        elif file_ext == '.rar':
            return self._read_rar_file(file_path)
        else:
            # 普通文本文件
            encodings = ['utf-8', 'gbk', 'gb2312', 'utf-16']
            for encoding in encodings:
                try:
                    with open(file_path, 'r', encoding=encoding) as f:
                        content = f.read()
                    print(f"成功使用 {encoding} 编码读取文件")
                    return content
                except UnicodeDecodeError:
                    continue
            
            raise ValueError(f"无法解码文件：{file_path}")
    
    def _read_zip_file(self, zip_path: str) -> str:
        """读取ZIP文件中的文本内容"""
        with zipfile.ZipFile(zip_path, 'r') as zip_file:
            file_list = zip_file.namelist()
            txt_files = [f for f in file_list if f.lower().endswith('.txt')]
            
            if not txt_files:
                raise ValueError("ZIP文件中没有找到.txt文件")
            
            # 选择第一个txt文件
            txt_file = txt_files[0]
            print(f"从ZIP文件中读取：{txt_file}")
            
            with zip_file.open(txt_file) as f:
                file_content = f.read()
            
            return self._decode_file_content(file_content, txt_file)
    
    def _read_rar_file(self, rar_path: str) -> str:
        """读取RAR文件中的文本内容"""
        if rarfile is None:
            raise ImportError("需要安装rarfile库来处理RAR文件")
        
        with rarfile.RarFile(rar_path) as rar_file:
            file_list = rar_file.namelist()
            txt_files = [f for f in file_list if f.lower().endswith('.txt')]
            
            if not txt_files:
                raise ValueError("RAR文件中没有找到.txt文件")
            
            txt_file = txt_files[0]
            print(f"从RAR文件中读取：{txt_file}")
            
            with rar_file.open(txt_file) as f:
                file_content = f.read()
            
            return self._decode_file_content(file_content, txt_file)
    
    def _decode_file_content(self, file_content: bytes, filename: str) -> str:
        """解码文件内容"""
        encodings = ['utf-8', 'gbk', 'gb2312', 'utf-16']
        
        for encoding in encodings:
            try:
                content = file_content.decode(encoding)
                print(f"成功使用 {encoding} 编码解码文件 {filename}")
                return content
            except UnicodeDecodeError:
                continue
        
        raise ValueError(f"无法解码文件内容：{filename}")
    
    def split_novel_into_chapters(self, novel_content: str, target_chapters: int = 50) -> List[str]:
        """
        将小说内容分割成指定数量的章节
        
        Args:
            novel_content: 小说内容
            target_chapters: 目标章节数量
            
        Returns:
            List[str]: 章节内容列表
        """
        # 清理文本
        novel_content = re.sub(r'\n\s*\n', '\n\n', novel_content)
        novel_content = novel_content.strip()
        
        # 尝试按章节标题分割
        chapter_patterns = [
            r'第[一二三四五六七八九十百千万\d]+章[^\n]*',
            r'第[\d]+章[^\n]*',
            r'Chapter\s*\d+[^\n]*',
            r'章节\s*\d+[^\n]*'
        ]
        
        chapters = []
        for pattern in chapter_patterns:
            matches = list(re.finditer(pattern, novel_content, re.IGNORECASE))
            if len(matches) >= 2:
                for i, match in enumerate(matches):
                    start = match.start()
                    end = matches[i + 1].start() if i + 1 < len(matches) else len(novel_content)
                    chapter_content = novel_content[start:end].strip()
                    if len(chapter_content) > 100:
                        chapters.append(chapter_content)
                break
        
        # 如果没有找到章节标题，按长度分割
        if not chapters:
            total_length = len(novel_content)
            chunk_size = total_length // target_chapters
            
            for i in range(target_chapters):
                start = i * chunk_size
                end = (i + 1) * chunk_size if i < target_chapters - 1 else total_length
                chapter_content = novel_content[start:end].strip()
                if chapter_content:
                    chapters.append(chapter_content)
        
        # 如果章节数量超过目标，合并较短的章节
        if len(chapters) > target_chapters:
            merged_chapters = []
            current_chapter = ""
            target_length = sum(len(ch) for ch in chapters) // target_chapters
            
            for chapter in chapters:
                if len(current_chapter) < target_length:
                    current_chapter += "\n\n" + chapter if current_chapter else chapter
                else:
                    merged_chapters.append(current_chapter)
                    current_chapter = chapter
            
            if current_chapter:
                if merged_chapters:
                    merged_chapters[-1] += "\n\n" + current_chapter
                else:
                    merged_chapters.append(current_chapter)
            
            chapters = merged_chapters[:target_chapters]
        
        print(f"成功分割为 {len(chapters)} 个章节")
        return chapters
    
    def generate_chapter_narration(self, chapter_content: str, chapter_num: int, total_chapters: int) -> str:
        """
        为单个章节生成解说文案
        
        Args:
            chapter_content: 章节内容
            chapter_num: 章节编号
            total_chapters: 总章节数
            
        Returns:
            str: 生成的解说文案
        """
        try:
            # 使用Jinja2模板生成提示词
            template_path = os.path.join(project_root, 'chapter_narration_prompt.j2')
            
            if not os.path.exists(template_path):
                raise FileNotFoundError(f"模板文件不存在：{template_path}")
            
            # 设置Jinja2环境
            env = Environment(loader=FileSystemLoader(project_root))
            template = env.get_template('chapter_narration_prompt.j2')
            
            # 渲染模板
            prompt = template.render(
                chapter_num=chapter_num,
                total_chapters=total_chapters,
                chapter_content=chapter_content
            )
            
            # 调用API生成
            with self.lock:
                response = self.client.chat.completions.create(
                    model=self.model,
                    messages=[
                        {"role": "user", "content": prompt}
                    ],
                    max_tokens=32*1024,  # 增加token限制以适应更复杂的输出格式
                    temperature=0.7
                )
            
            narration = response.choices[0].message.content.strip()
            return narration
            
        except Exception as e:
            print(f"生成第{chapter_num}章解说时出错：{e}")
            return ""
    
    def validate_narration_content(self, narration: str, min_length: int = 1200, max_length: int = 1800) -> Tuple[bool, str]:
        """
        验证解说内容的质量（检查字数、自动修复XML标签闭合、移除不需要的标签）
        
        Args:
            narration: 完整的narration内容
            min_length: 解说文本的最小长度
            max_length: 解说文本的最大长度
            
        Returns:
            Tuple[bool, str]: (是否有效, 错误信息或修正后的内容)
        """
        if not narration or not narration.strip():
            return False, "解说内容为空"
        
        narration = narration.strip()
        
        # 检查并移除不需要的标签
        cleaned_narration = self._remove_unwanted_tags(narration)
        
        # 提取所有<解说内容>标签内的文本进行字数统计
        import re
        explanation_pattern = r'<解说内容>(.*?)</解说内容>'
        explanation_matches = re.findall(explanation_pattern, cleaned_narration, re.DOTALL)
        
        if not explanation_matches:
            return False, "未找到解说内容标签"
        
        # 计算所有解说内容的总字数
        total_explanation_text = ''.join(explanation_matches)
        explanation_length = len(total_explanation_text.strip())
        
        if explanation_length < min_length:
            return False, f"解说文本长度不足，当前{explanation_length}字，最少需要{min_length}字"
        
        if explanation_length > max_length:
            return False, f"解说文本过长，当前{explanation_length}字，最多允许{max_length}字"
        
        # 自动修复XML标签闭合
        fixed_narration = self._fix_xml_tags(cleaned_narration)
        
        return True, fixed_narration
    
    def _remove_unwanted_tags(self, content: str) -> str:
        """
        移除不需要的标签
        
        Args:
            content: 原始内容
            
        Returns:
            str: 移除不需要标签后的内容
        """
        import re
        
        # 定义需要移除的标签列表
        unwanted_tags = [
            '角色编号', '角色类型', '风格', '文化', '气质'
        ]
        
        cleaned_content = content
        removed_tags = []
        
        # 移除不需要的标签及其内容
        for tag in unwanted_tags:
            # 匹配开始和结束标签之间的内容
            pattern = f'<{tag}>.*?</{tag}>'
            matches = re.findall(pattern, cleaned_content, re.DOTALL)
            if matches:
                removed_tags.extend([tag] * len(matches))
                cleaned_content = re.sub(pattern, '', cleaned_content, flags=re.DOTALL)
            
            # 移除单独的开始标签（如果存在）
            single_tag_pattern = f'<{tag}>'
            if re.search(single_tag_pattern, cleaned_content):
                removed_tags.append(f'{tag}(单标签)')
                cleaned_content = re.sub(single_tag_pattern, '', cleaned_content)
            
            # 移除单独的结束标签（如果存在）
            end_tag_pattern = f'</{tag}>'
            if re.search(end_tag_pattern, cleaned_content):
                removed_tags.append(f'{tag}(结束标签)')
                cleaned_content = re.sub(end_tag_pattern, '', cleaned_content)
        
        # 如果移除了标签，输出日志
        if removed_tags:
            print(f"自动移除不需要的标签：{', '.join(removed_tags)}")
        
        # 清理多余的空行
        cleaned_content = re.sub(r'\n\s*\n', '\n', cleaned_content)
        
        return cleaned_content.strip()
    
    def _fix_xml_tags(self, content: str) -> str:
        """
        自动修复XML标签闭合问题
        
        Args:
            content: 原始内容
            
        Returns:
            str: 修复后的内容
        """
        import re
        
        # 查找所有开始标签
        open_tags = re.findall(r'<([^/\s>]+)[^>]*>', content)
        # 查找所有结束标签
        close_tags = re.findall(r'</([^\s>]+)>', content)
        
        # 找出未闭合的标签
        unclosed_tags = []
        for tag in open_tags:
            if tag not in close_tags:
                unclosed_tags.append(tag)
        
        # 在内容末尾添加缺失的闭合标签
        fixed_content = content
        for tag in reversed(unclosed_tags):  # 反向添加，保持嵌套结构
            if f'</{tag}>' not in fixed_content:
                fixed_content += f'</{tag}>'
                print(f"自动修复：添加缺失的闭合标签 </{tag}>")
        
        return fixed_content
    

    
    def generate_chapter_narration_with_retry(self, chapter_content: str, chapter_num: int, 
                                            total_chapters: int, max_retries: int = 3) -> str:
        """
        带重试机制的章节解说生成（内存优化版）
        
        Args:
            chapter_content: 章节内容
            chapter_num: 章节编号
            total_chapters: 总章节数
            max_retries: 最大重试次数
            
        Returns:
            str: 生成的解说文案
        """
        for attempt in range(max_retries):
            try:
                print(f"正在生成第{chapter_num}章解说文案（尝试 {attempt + 1}/{max_retries}）...")
                
                narration = self.generate_chapter_narration(chapter_content, chapter_num, total_chapters)
                
                if narration:
                    # 验证并修复生成的内容
                    is_valid, result = self.validate_narration_content(
                        narration, 
                        self.validation_config['min_length'], 
                        self.validation_config['max_length']
                    )
                    
                    if is_valid:
                        # result是修复后的内容
                        fixed_narration = result
                        print(f"✓ 第{chapter_num}章解说文案生成成功（{len(fixed_narration)}字）")
                        # 释放原始narration内存
                        del narration
                        return fixed_narration
                    else:
                        # result是错误信息
                        print(f"✗ 第{chapter_num}章解说文案验证失败：{result}")
                        # 立即释放失败的narration内存
                        del narration
                        if attempt < max_retries - 1:
                            print(f"将进行第 {attempt + 2} 次尝试...")
                            time.sleep(2)  # 等待2秒后重试
                else:
                    print(f"✗ 第{chapter_num}章解说文案生成失败")
                    
            except Exception as e:
                print(f"生成第{chapter_num}章解说时出错（尝试 {attempt + 1}）：{e}")
                if attempt < max_retries - 1:
                    time.sleep(2)
        
        print(f"✗ 第{chapter_num}章解说文案生成最终失败")
        return ""
    
    def save_chapter(self, chapter_content: str, narration: str, chapter_num: int, output_dir: str) -> bool:
        """
        保存章节内容和解说文案（内存优化版）
        
        Args:
            chapter_content: 章节原始内容
            narration: 解说文案
            chapter_num: 章节编号
            output_dir: 输出目录
            
        Returns:
            bool: 是否保存成功
        """
        try:
            chapter_dir = os.path.join(output_dir, f"chapter_{chapter_num:03d}")
            os.makedirs(chapter_dir, exist_ok=True)
            
            # 保存原始章节内容（立即写入，不缓存）
            with open(os.path.join(chapter_dir, "original_content.txt"), 'w', encoding='utf-8') as f:
                f.write(chapter_content)
                f.flush()  # 强制刷新缓冲区
            
            # 保存解说文案（立即写入，不缓存）
            with open(os.path.join(chapter_dir, "narration.txt"), 'w', encoding='utf-8') as f:
                f.write(narration)
                f.flush()  # 强制刷新缓冲区
            
            print(f"✓ 第{chapter_num}章文件保存成功")
            return True
            
        except Exception as e:
            print(f"保存第{chapter_num}章时出错：{e}")
            return False
    
    def _force_garbage_collection(self):
        """
        强制执行垃圾回收以释放内存
        """
        import gc
        gc.collect()
    
    def validate_existing_chapters(self, output_dir: str, chapter_range: Optional[Tuple[int, int]] = None) -> Tuple[List[int], List[int], List[int]]:
        """
        验证已生成的章节
        
        Args:
            output_dir: 输出目录
            chapter_range: 章节范围 (start, end)，如果为None则验证所有章节
            
        Returns:
            Tuple[List[int], List[int], List[int]]: (所有无效章节, 长度不足章节, 其他问题章节)
        """
        all_invalid_chapters = []
        length_insufficient_chapters = []
        other_invalid_chapters = []
        
        if not os.path.exists(output_dir):
            print(f"输出目录不存在：{output_dir}")
            return all_invalid_chapters, length_insufficient_chapters, other_invalid_chapters
        
        # 获取要验证的章节列表
        chapter_dirs = []
        for item in os.listdir(output_dir):
            if item.startswith('chapter_') and os.path.isdir(os.path.join(output_dir, item)):
                try:
                    chapter_num = int(item.split('_')[1])
                    if chapter_range is None or (chapter_range[0] <= chapter_num <= chapter_range[1]):
                        chapter_dirs.append((chapter_num, item))
                except ValueError:
                    continue
        
        chapter_dirs.sort(key=lambda x: x[0])  # 按章节编号排序
        
        print(f"开始验证 {len(chapter_dirs)} 个章节...")
        
        for chapter_num, chapter_dir_name in chapter_dirs:
            chapter_dir = os.path.join(output_dir, chapter_dir_name)
            narration_file = os.path.join(chapter_dir, 'narration.txt')
            
            validation_result = self._validate_single_chapter(chapter_num, chapter_dir, narration_file)
            if validation_result == 'length_insufficient':
                all_invalid_chapters.append(chapter_num)
                length_insufficient_chapters.append(chapter_num)
            elif validation_result == 'other_invalid':
                all_invalid_chapters.append(chapter_num)
                other_invalid_chapters.append(chapter_num)
        
        # 输出验证结果
        if all_invalid_chapters:
            print(f"\n发现 {len(all_invalid_chapters)} 个需要重新生成的章节：{all_invalid_chapters}")
            if length_insufficient_chapters:
                print(f"其中 {len(length_insufficient_chapters)} 个章节长度不足：{length_insufficient_chapters}")
            if other_invalid_chapters:
                print(f"其中 {len(other_invalid_chapters)} 个章节存在其他问题：{other_invalid_chapters}")
        else:
            print("\n✓ 所有章节验证通过")
        
        return all_invalid_chapters, length_insufficient_chapters, other_invalid_chapters
    
    def _validate_single_chapter(self, chapter_num: int, chapter_dir: str, narration_file: str) -> str:
        """
        验证单个章节
        
        Args:
            chapter_num: 章节编号
            chapter_dir: 章节目录
            narration_file: narration文件路径
            
        Returns:
            str: 'valid', 'length_insufficient', 'other_invalid'
        """
        try:
            if not os.path.exists(narration_file):
                print(f"第{chapter_num}章缺少narration.txt文件")
                return 'other_invalid'
            
            with open(narration_file, 'r', encoding='utf-8') as f:
                narration_content = f.read()
            
            if not narration_content.strip():
                print(f"第{chapter_num}章narration文件为空")
                return 'other_invalid'
            
            # 验证并修复内容质量
            is_valid, result = self.validate_narration_content(
                narration_content, 
                self.validation_config['min_length'], 
                self.validation_config['max_length']
            )
            
            if not is_valid:
                print(f"第{chapter_num}章验证失败：{result}")
                if "过短" in result:
                    return 'length_insufficient'
                else:
                    return 'other_invalid'
            else:
                # 如果内容被修复了，保存修复后的内容
                if result != narration_content:
                    print(f"第{chapter_num}章XML标签已自动修复，正在保存...")
                    with open(narration_file, 'w', encoding='utf-8') as f:
                        f.write(result)
                        f.flush()
                
                print(f"第{chapter_num}章验证通过")
                return 'valid'
                
        except Exception as e:
            print(f"验证第{chapter_num}章时出错：{e}")
            return 'other_invalid'
    
    def regenerate_invalid_chapters(self, output_dir: str, invalid_chapters: List[int]) -> bool:
        """
        重新生成无效的章节
        
        Args:
            output_dir: 输出目录
            invalid_chapters: 需要重新生成的章节编号列表
            
        Returns:
            bool: 是否全部重新生成成功
        """
        if not invalid_chapters:
            return True
        
        print(f"\n=== 开始重新生成 {len(invalid_chapters)} 个无效章节 ===")
        success_count = 0
        
        for chapter_num in invalid_chapters:
            chapter_dir = os.path.join(output_dir, f"chapter_{chapter_num:03d}")
            original_content_file = os.path.join(chapter_dir, "original_content.txt")
            
            if not os.path.exists(original_content_file):
                print(f"第{chapter_num}章缺少original_content.txt文件，跳过重新生成")
                continue
            
            try:
                with open(original_content_file, 'r', encoding='utf-8') as f:
                    chapter_content = f.read()
                
                print(f"\n--- 重新生成第 {chapter_num} 章 ---")
                
                # 使用带重试的生成方法
                narration = self.generate_chapter_narration_with_retry(
                    chapter_content, chapter_num, len(invalid_chapters), 
                    self.validation_config['max_retries']
                )
                
                if narration:
                    # 保存重新生成的解说文案
                    narration_file = os.path.join(chapter_dir, "narration.txt")
                    with open(narration_file, 'w', encoding='utf-8') as f:
                        f.write(narration)
                    
                    print(f"✓ 第{chapter_num}章重新生成成功")
                    success_count += 1
                else:
                    print(f"✗ 第{chapter_num}章重新生成失败")
                    
            except Exception as e:
                print(f"重新生成第{chapter_num}章时出错：{e}")
                continue
        
        print(f"\n=== 重新生成完成 ===")
        print(f"成功重新生成 {success_count}/{len(invalid_chapters)} 个章节")
        
        return success_count == len(invalid_chapters)
    
    def generate_script_from_novel(self, novel_file: str, output_dir: str, 
                                 target_chapters: int = 50, max_workers: int = 5,
                                 chapter_limit: Optional[int] = None) -> bool:
        """
        从小说文件生成解说脚本（增强版）
        
        Args:
            novel_file: 小说文件路径
            output_dir: 输出目录
            target_chapters: 目标章节数量
            max_workers: 最大并发线程数
            chapter_limit: 限制生成的章节数量（前N个章节）
            
        Returns:
            bool: 是否生成成功
        """
        try:
            print(f"=== 开始生成解说脚本 ===")
            print(f"小说文件：{novel_file}")
            print(f"输出目录：{output_dir}")
            print(f"目标章节数：{target_chapters}")
            if chapter_limit:
                print(f"限制生成：前{chapter_limit}个章节")
            
            # 创建输出目录
            os.makedirs(output_dir, exist_ok=True)
            
            # 读取小说内容
            print("\n--- 读取小说文件 ---")
            novel_content = self.read_novel_file(novel_file)
            print(f"小说总长度：{len(novel_content)}字")
            
            # 分割章节
            print("\n--- 分割章节 ---")
            chapters = self.split_novel_into_chapters(novel_content, target_chapters)
            
            # 应用章节限制
            if chapter_limit and chapter_limit < len(chapters):
                chapters = chapters[:chapter_limit]
                print(f"应用章节限制，实际生成：{len(chapters)}个章节")
            
            # 释放小说原始内容内存（已分割完成）
            del novel_content
            
            # 生成解说文案
            print(f"\n--- 生成解说文案（{len(chapters)}个章节）---")
            
            def generate_single_chapter(chapter_data):
                chapter_num, chapter_content = chapter_data
                try:
                    narration = self.generate_chapter_narration_with_retry(
                        chapter_content, chapter_num, len(chapters),
                        self.validation_config['max_retries']
                    )
                    
                    if narration:
                        success = self.save_chapter(chapter_content, narration, chapter_num, output_dir)
                        # 立即释放内存
                        del narration
                        del chapter_content
                        return chapter_num, success
                    else:
                        # 释放章节内容内存
                        del chapter_content
                        return chapter_num, False
                except Exception as e:
                    print(f"处理第{chapter_num}章时发生异常：{e}")
                    # 确保在异常情况下也释放内存
                    if 'chapter_content' in locals():
                        del chapter_content
                    if 'narration' in locals():
                        del narration
                    return chapter_num, False
            
            # 使用线程池并发生成（内存优化：分批处理）
            success_count = 0
            failed_chapters = []
            batch_size = min(max_workers * 2, 10)  # 限制批次大小以控制内存使用
            
            for i in range(0, len(chapters), batch_size):
                batch_chapters = chapters[i:i + batch_size]
                chapter_data = [(i + j + 1, content) for j, content in enumerate(batch_chapters)]
                
                print(f"处理批次 {i//batch_size + 1}/{(len(chapters) + batch_size - 1)//batch_size}，章节 {i+1}-{min(i+batch_size, len(chapters))}")
                
                with ThreadPoolExecutor(max_workers=max_workers) as executor:
                    future_to_chapter = {executor.submit(generate_single_chapter, data): data[0] 
                                       for data in chapter_data}
                    
                    for future in as_completed(future_to_chapter):
                        chapter_num = future_to_chapter[future]
                        try:
                            result_chapter_num, success = future.result()
                            if success:
                                success_count += 1
                            else:
                                failed_chapters.append(result_chapter_num)
                        except Exception as e:
                            print(f"处理第{chapter_num}章时出错：{e}")
                            failed_chapters.append(chapter_num)
                
                # 释放当前批次的章节内容
                del batch_chapters
                del chapter_data
                
                # 强制垃圾回收以释放内存
                self._force_garbage_collection()
                print(f"第 {i//batch_size + 1} 批处理完成，已释放内存")
            
            print(f"\n--- 初始生成完成 ---")
            print(f"成功生成：{success_count}/{len(chapters)}个章节")
            if failed_chapters:
                print(f"失败章节：{failed_chapters}")
            
            # 验证所有章节质量
            print(f"\n--- 验证章节质量 ---")
            all_invalid, length_insufficient, other_invalid = self.validate_existing_chapters(
                output_dir, (1, len(chapters))
            )
            
            # 重新生成无效章节
            if all_invalid:
                print(f"\n--- 重新生成无效章节 ---")
                regenerate_success = self.regenerate_invalid_chapters(output_dir, all_invalid)
                
                if regenerate_success:
                    print("\n✓ 所有无效章节重新生成成功")
                else:
                    print("\n⚠ 部分章节重新生成失败")
                
                # 最终验证
                print(f"\n--- 最终验证 ---")
                final_invalid, _, _ = self.validate_existing_chapters(
                    output_dir, (1, len(chapters))
                )
                
                if not final_invalid:
                    print("\n🎉 所有章节最终验证通过！")
                else:
                    print(f"\n⚠ 仍有 {len(final_invalid)} 个章节存在问题：{final_invalid}")
            
            print(f"\n=== 脚本生成完成 ===")
            print(f"输出目录：{output_dir}")
            print(f"生成章节数：{len(chapters)}")
            
            return True
            
        except Exception as e:
            print(f"生成脚本时出错：{e}")
            return False

def main():
    """
    主函数，处理命令行参数
    """
    parser = argparse.ArgumentParser(description='增强版脚本生成器 - 支持章节质量验证和重新生成')
    parser.add_argument('novel_file', help='小说文件路径')
    parser.add_argument('--output', '-o', help='输出目录（默认：自动根据小说文件路径确定，如data/004/xxx.txt则输出到data/004）')
    parser.add_argument('--chapters', '-c', type=int, default=50, help='目标章节数量（默认：50）')
    parser.add_argument('--limit', '-l', type=int, help='限制生成前N个章节')
    parser.add_argument('--workers', '-w', type=int, default=5, help='最大并发线程数（默认：5）')
    parser.add_argument('--validate-only', action='store_true', help='仅验证现有章节，不生成新内容')
    parser.add_argument('--regenerate', action='store_true', help='重新生成无效章节')
    parser.add_argument('--min-length', type=int, default=800, help='解说文案最小长度（默认：800）')
    parser.add_argument('--max-length', type=int, default=2000, help='解说文案最大长度（默认：2000）')
    parser.add_argument('--max-retries', type=int, default=3, help='最大重试次数（默认：3）')
    
    args = parser.parse_args()
    
    # 如果没有指定输出目录，则根据小说文件路径自动生成输出目录
    if not args.output:
        # 检查小说文件是否在data目录下的子目录中
        novel_path = os.path.abspath(args.novel_file)
        if 'data/' in novel_path:
            # 提取data目录下的子目录作为输出目录
            data_index = novel_path.find('data/')
            relative_path = novel_path[data_index:]
            # 获取data/xxx部分
            path_parts = relative_path.split(os.sep)
            if len(path_parts) >= 2:  # data/xxx
                args.output = os.path.join(path_parts[0], path_parts[1])
            else:
                # 如果不在data子目录中，使用小说文件名
                novel_filename = os.path.splitext(os.path.basename(args.novel_file))[0]
                args.output = f'data/{novel_filename}'
        else:
            # 如果不在data目录中，使用小说文件名
            novel_filename = os.path.splitext(os.path.basename(args.novel_file))[0]
            args.output = f'data/{novel_filename}'
    
    try:
        # 创建生成器实例
        generator = ScriptGeneratorV2()
        
        # 更新验证配置
        generator.validation_config.update({
            'min_length': args.min_length,
            'max_length': args.max_length,
            'max_retries': args.max_retries
        })
        
        if args.validate_only:
            # 仅验证模式
            print("=== 验证模式 ===")
            chapter_range = None
            if args.limit:
                chapter_range = (1, args.limit)
                print(f"验证范围：前{args.limit}个章节")
            
            all_invalid, length_insufficient, other_invalid = generator.validate_existing_chapters(
                args.output, chapter_range
            )
            
            if args.regenerate and all_invalid:
                print("\n=== 重新生成模式 ===")
                generator.regenerate_invalid_chapters(args.output, all_invalid)
        
        else:
            # 生成模式
            success = generator.generate_script_from_novel(
                args.novel_file,
                args.output,
                args.chapters,
                args.workers,
                args.limit
            )
            
            if success:
                print("\n🎉 脚本生成成功！")
            else:
                print("\n❌ 脚本生成失败！")
                sys.exit(1)
    
    except Exception as e:
        print(f"程序执行出错：{e}")
        sys.exit(1)

if __name__ == "__main__":
    main()