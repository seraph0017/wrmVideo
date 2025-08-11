#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
脚本生成模块
使用配置化的prompt模板
支持从小说文件直接生成章节解说文案
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
        self.model = ARK_CONFIG.get('model', 'doubao-seed-1-6-flash-250615')
        print(f"使用模型: {self.model}")
    
    def read_novel_file(self, file_path: str) -> str:
        """
        读取小说文件，支持多种编码格式、RAR压缩文件和ZIP压缩文件
        
        Args:
            file_path: 文件路径
        
        Returns:
            str: 文件内容
        """
        # 检查是否为RAR文件
        if file_path.lower().endswith('.rar'):
            return self._read_rar_file(file_path)
        
        # 检查是否为ZIP文件
        if file_path.lower().endswith('.zip'):
            return self._read_zip_file(file_path)
        
        # 尝试多种编码格式
        encodings = ['utf-8', 'gbk', 'gb2312', 'gb18030', 'big5', 'latin1']
        
        for encoding in encodings:
            try:
                with open(file_path, 'r', encoding=encoding) as f:
                    content = f.read()
                    print(f"成功使用 {encoding} 编码读取文件")
                    return content
            except UnicodeDecodeError:
                continue
            except Exception as e:
                print(f"使用 {encoding} 编码读取文件时出错：{e}")
                continue
        
        print(f"无法读取文件 {file_path}，尝试了所有编码格式都失败")
        return ""
    
    def _detect_zip_encoding(self, filename_bytes):
        """
        检测ZIP文件名的正确编码
        """
        encodings = ['gbk', 'gb2312', 'utf-8', 'big5']
        
        for encoding in encodings:
            try:
                decoded = filename_bytes.decode(encoding)
                # 检查是否包含中文字符
                if any('\u4e00' <= char <= '\u9fff' for char in decoded):
                    return decoded, encoding
            except (UnicodeDecodeError, UnicodeError):
                continue
        
        # 如果都失败了，尝试cp437->gbk的转换（常见的Windows->Unix问题）
        try:
            decoded = filename_bytes.decode('gbk')
            return decoded, 'cp437->gbk'
        except (UnicodeDecodeError, UnicodeError):
            pass
        
        # 最后尝试忽略错误
        return filename_bytes.decode('utf-8', errors='ignore'), 'utf-8-ignore'
    
    def _read_zip_file(self, zip_path: str) -> str:
        """
        读取ZIP文件中的小说内容，自动修复中文编码问题
        
        Args:
            zip_path: ZIP文件路径
        
        Returns:
            str: 小说内容
        """
        print(f"🔧 正在处理ZIP文件: {zip_path}")
        
        try:
            with zipfile.ZipFile(zip_path, 'r') as zip_file:
                # 查找文本文件
                text_files = []
                
                for file_info in zip_file.filelist:
                    original_filename = file_info.filename
                    
                    # 跳过macOS的隐藏文件和目录
                    if '__MACOSX' in original_filename or file_info.is_dir():
                        continue
                    
                    # 修复文件名编码
                    try:
                        filename_bytes = original_filename.encode('cp437')
                        correct_filename, detected_encoding = self._detect_zip_encoding(filename_bytes)
                    except (UnicodeDecodeError, UnicodeEncodeError):
                        correct_filename = original_filename
                        detected_encoding = 'original'
                    
                    # 检查是否为文本文件
                    if correct_filename.lower().endswith(('.txt', '.md', '.text')):
                        text_files.append((file_info, correct_filename, detected_encoding))
                        print(f"📄 找到文本文件: {correct_filename} (编码: {detected_encoding})")
                
                if not text_files:
                    print("❌ ZIP文件中未找到文本文件")
                    return ""
                
                # 按章节号排序文件
                def extract_chapter_number(filename_tuple):
                    """从文件名中提取章节号进行排序"""
                    file_info, correct_filename, detected_encoding = filename_tuple
                    # 提取文件名中的数字
                    numbers = re.findall(r'\d+', os.path.basename(correct_filename))
                    return int(numbers[0]) if numbers else 0
                
                text_files.sort(key=extract_chapter_number)
                print(f"📋 按章节号排序后的文件顺序:")
                for i, (file_info, correct_filename, detected_encoding) in enumerate(text_files, 1):
                    print(f"  {i}. {correct_filename}")
                
                # 读取所有文本文件内容
                all_content = []
                
                for file_info, correct_filename, detected_encoding in text_files:
                    try:
                        with zip_file.open(file_info) as f:
                            file_content = f.read()
                        
                        # 尝试多种编码解码文件内容
                        content = self._decode_file_content(file_content, correct_filename)
                        
                        if content:
                            all_content.append(f"\n=== {correct_filename} ===\n{content}")
                            print(f"✅ 成功读取: {correct_filename} ({len(content)} 字符)")
                        
                    except Exception as e:
                        print(f"⚠️ 读取文件失败: {correct_filename}, 错误: {e}")
                        continue
                
                if all_content:
                    result = "\n\n".join(all_content)
                    print(f"📚 ZIP文件处理完成，总共 {len(result)} 字符")
                    return result
                else:
                    print("❌ 无法读取ZIP文件中的任何内容")
                    return ""
                    
        except Exception as e:
            print(f"❌ 处理ZIP文件时发生错误: {e}")
            return ""
    
    def _decode_file_content(self, file_content: bytes, filename: str) -> str:
        """
        解码文件内容，尝试多种编码格式
        
        Args:
            file_content: 文件字节内容
            filename: 文件名（用于日志）
        
        Returns:
            str: 解码后的文本内容
        """
        encodings = ['utf-8', 'gbk', 'gb2312', 'gb18030', 'big5', 'latin1']
        
        for encoding in encodings:
            try:
                content = file_content.decode(encoding)
                print(f"  📝 使用 {encoding} 编码成功解码文件内容")
                return content
            except UnicodeDecodeError:
                continue
            except Exception as e:
                print(f"  ⚠️ 使用 {encoding} 编码解码时出错: {e}")
                continue
        
        print(f"  ❌ 无法解码文件内容: {filename}")
        return ""
    
    def _read_rar_file(self, rar_path: str) -> str:
        """
        读取RAR文件中的txt文件，按文件名排序并合并
        
        Args:
            rar_path: RAR文件路径
        
        Returns:
            str: 合并后的文件内容
        """
        if rarfile is None:
            print("错误：需要安装 rarfile 库来处理RAR文件")
            print("请运行：pip install rarfile")
            return ""
        
        # 首先尝试使用rarfile库
        try:
            with rarfile.RarFile(rar_path) as rf:
                # 获取所有txt文件
                txt_files = [f for f in rf.namelist() if f.lower().endswith('.txt')]
                
                if not txt_files:
                    print(f"RAR文件中没有找到txt文件")
                    return ""
                
                # 按文件名排序（提取数字进行排序）
                def extract_number(filename):
                    # 提取文件名中的数字
                    numbers = re.findall(r'\d+', os.path.basename(filename))
                    return int(numbers[0]) if numbers else 0
                
                txt_files.sort(key=extract_number)
                print(f"找到 {len(txt_files)} 个txt文件，尝试使用rarfile库读取...")
                
                # 读取并合并所有txt文件
                merged_content = ""
                encodings = ['utf-8', 'gbk', 'gb2312', 'gb18030', 'big5', 'latin1']
                successful_reads = 0
                
                for txt_file in txt_files:
                    try:
                        # 直接从RAR中读取文件内容
                        file_data = rf.read(txt_file)
                        
                        # 尝试多种编码解码文件内容
                        file_content = ""
                        for encoding in encodings:
                            try:
                                file_content = file_data.decode(encoding)
                                break
                            except UnicodeDecodeError:
                                continue
                            except Exception:
                                continue
                        
                        if file_content:
                            merged_content += file_content + "\n\n"
                            successful_reads += 1
                    
                    except Exception:
                        # 如果rarfile库读取失败，跳过这个文件
                        continue
                
                if successful_reads > 0:
                    print(f"成功使用rarfile库读取 {successful_reads}/{len(txt_files)} 个文件")
                    return merged_content.strip()
                else:
                    print("rarfile库无法读取文件内容，尝试使用系统命令...")
                    
        except Exception as e:
            print(f"rarfile库读取失败：{e}，尝试使用系统命令...")
        
        # 如果rarfile库失败，尝试使用系统命令提取
        return self._extract_rar_with_system_command(rar_path)
    
    def _extract_rar_with_system_command(self, rar_path: str) -> str:
        """
        使用系统命令提取RAR文件
        
        Args:
            rar_path: RAR文件路径
        
        Returns:
            str: 合并后的文件内容
        """
        import subprocess
        import shutil
        
        # 创建临时目录
        temp_dir = tempfile.mkdtemp()
        
        try:
            # 尝试使用不同的解压命令
            commands = [
                ['unrar', 'x', '-y', rar_path, temp_dir],
                ['7z', 'x', '-y', f'-o{temp_dir}', rar_path],
                ['unar', '-o', temp_dir, rar_path]
            ]
            
            extracted = False
            for cmd in commands:
                try:
                    # 检查命令是否存在
                    if shutil.which(cmd[0]) is None:
                        continue
                    
                    print(f"尝试使用 {cmd[0]} 命令提取RAR文件...")
                    result = subprocess.run(cmd, capture_output=True, text=False, timeout=300)
                    
                    if result.returncode == 0:
                        print(f"成功使用 {cmd[0]} 提取文件")
                        extracted = True
                        break
                    else:
                        # 安全地解码stderr，忽略无法解码的字符
                        try:
                            stderr_text = result.stderr.decode('utf-8', errors='ignore')
                        except:
                            stderr_text = str(result.stderr)
                        print(f"{cmd[0]} 提取失败：{stderr_text}")
                        
                except subprocess.TimeoutExpired:
                    print(f"{cmd[0]} 命令超时")
                    continue
                except Exception as e:
                    print(f"{cmd[0]} 命令执行出错：{e}")
                    continue
            
            if not extracted:
                print("所有解压命令都失败了，请手动解压RAR文件")
                return ""
            
            # 读取提取的txt文件
            merged_content = ""
            txt_files = []
            
            # 递归查找所有txt文件
            for root, dirs, files in os.walk(temp_dir):
                for file in files:
                    if file.lower().endswith('.txt'):
                        txt_files.append(os.path.join(root, file))
            
            if not txt_files:
                print("提取后没有找到txt文件")
                return ""
            
            # 按文件名排序
            def extract_number(filepath):
                filename = os.path.basename(filepath)
                numbers = re.findall(r'\d+', filename)
                return int(numbers[0]) if numbers else 0
            
            txt_files.sort(key=extract_number)
            print(f"找到 {len(txt_files)} 个txt文件，开始读取...")
            
            # 读取所有文件
            encodings = ['utf-8', 'gbk', 'gb2312', 'gb18030', 'big5', 'latin1']
            
            for txt_file in txt_files:
                for encoding in encodings:
                    try:
                        with open(txt_file, 'r', encoding=encoding) as f:
                            content = f.read()
                            merged_content += content + "\n\n"
                            break
                    except UnicodeDecodeError:
                        continue
                    except Exception:
                        continue
            
            print(f"成功合并 {len(txt_files)} 个文件，总长度：{len(merged_content)} 字符")
            return merged_content.strip()
            
        finally:
            # 清理临时目录
            try:
                shutil.rmtree(temp_dir)
            except Exception:
                pass
    
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
    
    def generate_script_for_chunks_async(self, chunks: List[str], max_workers: int = 5, **kwargs) -> List[str]:
        """
        使用多线程为所有文本块生成脚本

        Args:
            chunks: 文本块列表
            max_workers: 最大线程数
            **kwargs: 其他参数

        Returns:
            List[str]: 生成的脚本列表
        """
        results = [""] * len(chunks)  # 预分配结果列表
        
        with ThreadPoolExecutor(max_workers=max_workers) as executor:
            # 提交所有任务
            future_to_index = {
                executor.submit(self.generate_script_for_chunk, chunk, i, len(chunks), **kwargs): i
                for i, chunk in enumerate(chunks)
            }
            
            # 收集结果
            for future in as_completed(future_to_index):
                index = future_to_index[future]
                try:
                    result = future.result()
                    results[index] = result if result else ""
                    print(f"线程 {threading.current_thread().name}: 第 {index + 1}/{len(chunks)} 个脚本片段完成")
                except Exception as e:
                    print(f"线程 {threading.current_thread().name}: 第 {index + 1} 个脚本片段生成失败: {e}")
                    results[index] = ""
        
        return results
    
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
            print(f"输入内容长度: {len(content)} 字符")
            print(f"Prompt长度: {len(prompt)} 字符")
            
            # 调用API
            completion = self.client.chat.completions.create(
                model=self.model,
                messages=[
                    {"role": "user", "content": prompt}
                ],
                max_tokens=32*1024,
                stream=False
            )
            
            response = completion.choices[0].message.content
            print(f"第 {chunk_index + 1} 个片段生成完成")
            print(f"API响应长度: {len(response) if response else 0} 字符")
            
            if not response or len(response.strip()) == 0:
                print(f"⚠️ 警告：第 {chunk_index + 1} 个片段的API响应为空！")
                print(f"API响应详情: {repr(response)}")
                return ""
            
            return response
            
        except Exception as e:
            print(f"生成脚本时出错：{e}")
            import traceback
            print(f"详细错误信息：{traceback.format_exc()}")
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
    
    def split_novel_into_chapters(self, novel_content: str, target_chapters: int = 50) -> List[str]:
        """
        将小说内容智能分割成指定数量的章节
        
        Args:
            novel_content: 小说内容
            target_chapters: 目标章节数量（默认50）
        
        Returns:
            List[str]: 分割后的章节内容列表
        """
        # 计算每章大致长度
        total_length = len(novel_content)
        avg_chapter_length = total_length // target_chapters
        
        chapters = []
        current_pos = 0
        
        for i in range(target_chapters):
            if i == target_chapters - 1:  # 最后一章包含剩余所有内容
                chapter_content = novel_content[current_pos:]
            else:
                # 寻找合适的分割点（句号、感叹号、问号后）
                end_pos = current_pos + avg_chapter_length
                
                # 在目标位置前后寻找合适的分割点
                search_range = min(200, avg_chapter_length // 4)  # 搜索范围
                best_split = end_pos
                
                # 向后搜索分割点
                for j in range(end_pos, min(end_pos + search_range, total_length)):
                    if novel_content[j] in ['。', '！', '？']:
                        best_split = j + 1
                        break
                
                # 如果向后没找到，向前搜索
                if best_split == end_pos:
                    for j in range(end_pos, max(current_pos, end_pos - search_range), -1):
                        if novel_content[j] in ['。', '！', '？']:
                            best_split = j + 1
                            break
                
                chapter_content = novel_content[current_pos:best_split]
                current_pos = best_split
            
            if chapter_content.strip():  # 只添加非空章节
                chapters.append(chapter_content.strip())
        
        return chapters
    
    def extract_narration_content(self, narration_file_content: str) -> str:
        """
        从narration文件内容中提取所有解说内容
        
        Args:
            narration_file_content: narration文件的完整内容
        
        Returns:
            str: 提取出的所有解说内容，用空格连接
        """
        try:
            # 使用正则表达式提取所有<解说内容>标签中的内容
            narration_pattern = r'<解说内容>(.*?)</解说内容>'
            narration_matches = re.findall(narration_pattern, narration_file_content, re.DOTALL)
            
            # 清理并合并所有解说内容
            clean_narrations = []
            for narration in narration_matches:
                clean_narration = narration.strip()
                if clean_narration:
                    clean_narrations.append(clean_narration)
            
            # 将所有解说内容合并为一个字符串
            combined_narration = ' '.join(clean_narrations)
            return combined_narration
            
        except Exception as e:
            print(f"提取解说内容时出错：{e}")
            return ""
    
    def validate_narration_content(self, narration: str, min_length: int = 800, max_length: int = 1500) -> Tuple[bool, str]:
        """
        验证解说文案是否符合要求
        
        Args:
            narration: 解说文案内容
            min_length: 最小长度要求
            max_length: 最大长度要求
        
        Returns:
            Tuple[bool, str]: (是否有效, 错误信息)
        """
        if not narration or not narration.strip():
            return False, "解说文案为空"
        
        content_length = len(narration.strip())
        if content_length < min_length:
            return False, f"解说文案长度不足，当前{content_length}字，要求至少{min_length}字"
        
        if content_length > max_length:
            return False, f"解说文案长度过长，当前{content_length}字，要求不超过{max_length}字"
        
        # 检查是否包含基本的叙述结构（仅提醒，不作为强制约束）
        if not any(keyword in narration for keyword in ['故事', '情节', '主角', '角色', '场景']):
            print(f"提醒：解说文案可能缺少基本的故事元素，建议检查内容质量")
        
        return True, ""
    
    def generate_chapter_narration_with_retry(self, chapter_content: str, chapter_num: int, 
                                            total_chapters: int, max_retries: int = 3) -> str:
        """
        为单个章节生成1500字左右解说文案，带重试机制
        
        Args:
            chapter_content: 章节内容
            chapter_num: 章节编号
            total_chapters: 总章节数
            max_retries: 最大重试次数
        
        Returns:
            str: 生成的解说文案
        """
        for attempt in range(max_retries + 1):
            try:
                if attempt > 0:
                    print(f"第{chapter_num}章解说文案第{attempt + 1}次尝试生成...")
                    time.sleep(2)  # 重试前等待2秒
                
                narration = self.generate_chapter_narration(chapter_content, chapter_num, total_chapters)
                
                if narration:
                    # 提取<解说内容>标签内的内容进行验证
                    extracted_content = self.extract_narration_content(narration)
                    content_length = len(extracted_content)
                    print(f"第{chapter_num}章解说文案生成完成，<解说内容>标签内容长度：{content_length}字")
                    
                    # 验证提取的解说内容（调整长度限制为2000字）
                    is_valid, error_msg = self.validate_narration_content(extracted_content, min_length=800, max_length=2000)
                    if is_valid:
                        print(f"第{chapter_num}章解说文案验证通过")
                        return narration
                    else:
                        print(f"第{chapter_num}章解说文案验证失败：{error_msg}")
                        if attempt < max_retries:
                            print(f"将进行第{attempt + 2}次重试...")
                        continue
                else:
                    print(f"第{chapter_num}章解说文案生成失败")
                    if attempt < max_retries:
                        print(f"将进行第{attempt + 2}次重试...")
                    continue
                    
            except Exception as e:
                print(f"生成第{chapter_num}章解说文案时出错：{e}")
                if attempt < max_retries:
                    print(f"将进行第{attempt + 2}次重试...")
                    time.sleep(2)
                continue
        
        print(f"第{chapter_num}章解说文案生成失败，已达到最大重试次数")
        return ""
    
    def validate_existing_chapters(self, output_dir: str) -> Tuple[List[int], List[int], List[int]]:
        """
        验证已生成的章节，返回详细的验证结果
        
        Args:
            output_dir: 输出目录或单个章节目录
        
        Returns:
            Tuple[List[int], List[int], List[int]]: (所有无效章节, 长度不足章节, 其他问题章节)
        """
        all_invalid_chapters = []
        length_insufficient_chapters = []
        other_invalid_chapters = []
        
        if not os.path.exists(output_dir):
            print(f"输出目录不存在：{output_dir}")
            return all_invalid_chapters, length_insufficient_chapters, other_invalid_chapters
        
        # 检查是否是单个章节目录
        if os.path.basename(output_dir).startswith('chapter_'):
            # 单个章节目录验证
            try:
                chapter_num = int(os.path.basename(output_dir).split('_')[1])
                narration_file = os.path.join(output_dir, 'narration.txt')
                
                # 验证这个章节
                validation_result = self._validate_single_chapter(chapter_num, output_dir, narration_file)
                if validation_result == 'length_insufficient':
                    all_invalid_chapters.append(chapter_num)
                    length_insufficient_chapters.append(chapter_num)
                elif validation_result == 'other_invalid':
                    all_invalid_chapters.append(chapter_num)
                    other_invalid_chapters.append(chapter_num)
                # validation_result == 'valid' 时不添加到任何列表
                    
            except ValueError:
                print(f"无法解析章节编号：{os.path.basename(output_dir)}")
            except Exception as e:
                print(f"验证单个章节时出错：{e}")
        else:
            # 多个章节目录验证
            for item in os.listdir(output_dir):
                if item.startswith('chapter_') and os.path.isdir(os.path.join(output_dir, item)):
                    try:
                        # 提取章节编号
                        chapter_num = int(item.split('_')[1])
                        chapter_dir = os.path.join(output_dir, item)
                        narration_file = os.path.join(chapter_dir, 'narration.txt')
                        
                        # 验证这个章节
                        validation_result = self._validate_single_chapter(chapter_num, chapter_dir, narration_file)
                        if validation_result == 'length_insufficient':
                            all_invalid_chapters.append(chapter_num)
                            length_insufficient_chapters.append(chapter_num)
                        elif validation_result == 'other_invalid':
                            all_invalid_chapters.append(chapter_num)
                            other_invalid_chapters.append(chapter_num)
                        # validation_result == 'valid' 时不添加到任何列表
                        
                    except ValueError:
                        # 无法解析章节编号，跳过
                        continue
                    except Exception as e:
                        print(f"处理章节目录 {item} 时出错：{e}")
                        continue
        
        # 排序结果
        all_invalid_chapters.sort()
        length_insufficient_chapters.sort()
        other_invalid_chapters.sort()
        
        if all_invalid_chapters:
            print(f"发现 {len(all_invalid_chapters)} 个需要重新生成的章节：{all_invalid_chapters}")
            if length_insufficient_chapters:
                print(f"其中 {len(length_insufficient_chapters)} 个章节长度不足：{length_insufficient_chapters}")
            if other_invalid_chapters:
                print(f"其中 {len(other_invalid_chapters)} 个章节存在其他问题：{other_invalid_chapters}")
        else:
            print("所有章节验证通过")
        
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
            # 检查narration文件是否存在
            if not os.path.exists(narration_file):
                print(f"第{chapter_num}章缺少narration.txt文件")
                return 'other_invalid'
            
            # 读取并验证narration内容
            try:
                with open(narration_file, 'r', encoding='utf-8') as f:
                    narration_file_content = f.read()
                
                # 提取解说内容
                extracted_narration = self.extract_narration_content(narration_file_content)
                
                if not extracted_narration:
                    print(f"第{chapter_num}章narration文件中未找到解说内容")
                    return 'other_invalid'
                
                # 验证提取出的解说内容（使用2000字最大长度限制）
                is_valid, error_msg = self.validate_narration_content(extracted_narration, min_length=800, max_length=2000)
                if not is_valid:
                    print(f"第{chapter_num}章narration文件验证失败：{error_msg}")
                    
                    # 判断是否为长度不足问题
                    if "长度不足" in error_msg:
                        return 'length_insufficient'
                    else:
                        return 'other_invalid'
                else:
                    print(f"第{chapter_num}章narration文件验证通过")
                    return 'valid'
                    
            except Exception as e:
                print(f"读取第{chapter_num}章narration文件时出错：{e}")
                return 'other_invalid'
                
        except Exception as e:
            print(f"验证第{chapter_num}章时出错：{e}")
            return 'other_invalid'
    
    def regenerate_invalid_chapters(self, output_dir: str, invalid_chapters: List[int], max_retries: int = 3) -> bool:
        """
        重新生成无效的章节
        
        Args:
            output_dir: 输出目录
            invalid_chapters: 需要重新生成的章节编号列表
            max_retries: 最大重试次数
        
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
            
            # 检查原始内容文件是否存在
            if not os.path.exists(original_content_file):
                print(f"第{chapter_num}章缺少original_content.txt文件，跳过重新生成")
                continue
            
            try:
                # 读取原始章节内容
                with open(original_content_file, 'r', encoding='utf-8') as f:
                    chapter_content = f.read()
                
                print(f"\n--- 重新生成第 {chapter_num} 章 ---")
                
                # 使用带重试的生成方法
                narration = self.generate_chapter_narration_with_retry(
                    chapter_content, chapter_num, len(invalid_chapters), max_retries
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
    
    def generate_chapter_narration(self, chapter_content: str, chapter_num: int, total_chapters: int) -> str:
        """
        为单个章节生成1200字解说文案
        
        Args:
            chapter_content: 章节内容
            chapter_num: 章节编号
            total_chapters: 总章节数
        
        Returns:
            str: 生成的解说文案
        """
        try:
            # 设置模板环境
            template_dir = os.path.join(os.path.dirname(__file__))
            env = Environment(loader=FileSystemLoader(template_dir))
            # template = env.get_template('chapter_narration_prompt_simple.j2')
            template = env.get_template('chapter_narration_prompt.j2')
            
            # 渲染模板
            custom_prompt = template.render(
                chapter_num=chapter_num,
                total_chapters=total_chapters,
                chapter_content=chapter_content
            )
            
            print(f"正在为第{chapter_num}章生成解说文案...")
            
            # 调用API生成解说
            completion = self.client.chat.completions.create(
                model=self.model,
                messages=[
                    {"role": "user", "content": custom_prompt}
                ],
                max_tokens=32*1024,
                stream=False
            )
            
            narration = completion.choices[0].message.content.strip()
            print(f"第{chapter_num}章解说文案生成完成，长度：{len(narration)}字")
            
            return narration
            
        except Exception as e:
            print(f"生成第{chapter_num}章解说文案时出错：{e}")
            return ""
    
    def generate_script_from_novel_new(self, novel_file: str, output_dir: str, target_chapters: int = 50, max_workers: int = 5) -> bool:
        """
        新的小说脚本生成函数，支持章节分割和1200字解说生成
        
        Args:
            novel_file: 小说文件路径
            output_dir: 输出目录
            target_chapters: 目标章节数量（默认50）
            max_workers: 最大并发线程数（默认5）
        
        Returns:
            bool: 是否成功
        """
        try:
            print(f"=== 开始新的脚本生成流程 ===")
            print(f"输入文件: {novel_file}")
            print(f"输出目录: {output_dir}")
            print(f"目标章节数: {target_chapters}")
            
            # 检查输入文件
            if not os.path.exists(novel_file):
                print(f"错误: 小说文件不存在 {novel_file}")
                return False
            
            # 读取小说内容，支持多种编码格式
            novel_content = self.read_novel_file(novel_file)
            
            if not novel_content.strip():
                print("错误: 小说文件内容为空")
                return False
            
            print(f"小说总长度: {len(novel_content)}字")
            
            # 分割小说为章节
            print("\n=== 开始分割章节 ===")
            chapters = self.split_novel_into_chapters(novel_content, target_chapters)
            print(f"成功分割为 {len(chapters)} 个章节")
            
            # 创建输出目录
            os.makedirs(output_dir, exist_ok=True)
            
            # 为每个章节生成解说文案
            print("\n=== 开始生成章节解说文案 ===")
            success_count = 0
            
            for i, chapter_content in enumerate(chapters, 1):
                print(f"\n--- 处理第 {i}/{len(chapters)} 章 ---")
                print(f"章节内容长度: {len(chapter_content)}字")
                
                # 创建章节目录
                chapter_dir = os.path.join(output_dir, f"chapter_{i:03d}")
                os.makedirs(chapter_dir, exist_ok=True)
                
                # 保存原始章节内容
                chapter_file = os.path.join(chapter_dir, "original_content.txt")
                with open(chapter_file, 'w', encoding='utf-8') as f:
                    f.write(chapter_content)
                
                # 生成1200字解说文案（带重试机制）
                narration = self.generate_chapter_narration_with_retry(chapter_content, i, len(chapters))
                
                if narration:
                    # 保存解说文案
                    narration_file = os.path.join(chapter_dir, "narration.txt")
                    with open(narration_file, 'w', encoding='utf-8') as f:
                        f.write(narration)
                    
                    print(f"✓ 第{i}章解说文案已保存")
                    success_count += 1
                else:
                    print(f"✗ 第{i}章解说文案生成失败")
            
            print(f"\n=== 初始脚本生成完成 ===")
            print(f"成功生成 {success_count}/{len(chapters)} 个章节的解说文案")
            
            # 验证所有章节并重新生成无效的章节
            print(f"\n=== 开始验证章节质量 ===")
            invalid_chapters = self.validate_existing_chapters(output_dir)
            
            if invalid_chapters:
                print(f"\n发现 {len(invalid_chapters)} 个章节需要重新生成")
                retry_success = self.regenerate_invalid_chapters(output_dir, invalid_chapters)
                
                if retry_success:
                    print(f"\n=== 所有章节重新生成成功 ===")
                else:
                    print(f"\n=== 部分章节重新生成失败，请检查日志 ===")
                
                # 最终验证
                print(f"\n=== 最终验证 ===")
                final_invalid = self.validate_existing_chapters(output_dir)
                if final_invalid:
                    print(f"仍有 {len(final_invalid)} 个章节存在问题：{final_invalid}")
                else:
                    print("所有章节最终验证通过")
            
            print(f"\n=== 脚本生成完成 ===")
            print(f"输出目录: {output_dir}")
            
            return success_count > 0
            
        except Exception as e:
            print(f"生成脚本时发生错误: {e}")
            return False

    def generate_script(self, novel_content: str, output_dir: str = "output", 
                       max_workers: int = 5, **kwargs) -> bool:
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
                
                # 多线程生成脚本
                print(f"使用 {max_workers} 个线程并发处理")
                scripts = self.generate_script_for_chunks_async(chunks, max_workers=max_workers, **kwargs)
                # 过滤掉空结果
                scripts = [s for s in scripts if s and s.strip()]
            
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
    主函数，处理命令行参数
    """
    parser = argparse.ArgumentParser(description='小说脚本生成工具')
    parser.add_argument('novel_file', nargs='?', help='小说文件路径（验证模式下可选）')
    parser.add_argument('--output', '-o', default=None, help='输出目录（默认为小说文件所在目录）')
    parser.add_argument('--chapters', '-c', type=int, default=50, help='目标章节数量（默认50）')
    parser.add_argument('--max-workers', '-w', type=int, default=5, help='最大并发线程数（默认5）')
    parser.add_argument('--validate', '-v', action='store_true', help='验证现有章节的narration文件是否符合标准')
    parser.add_argument('--validate-dir', default=None, help='指定要验证的目录路径（仅在验证模式下使用）')
    
    args = parser.parse_args()
    
    # 创建脚本生成器
    generator = ScriptGenerator()
    
    # 验证模式
    if args.validate:
        # 确定验证目录
        if args.validate_dir:
            validate_dir = args.validate_dir
        elif args.novel_file:
            # 使用小说文件所在目录
            novel_dir = os.path.dirname(os.path.abspath(args.novel_file))
            validate_dir = novel_dir
        else:
            print("错误: 验证模式下需要指定 --validate-dir 或提供小说文件路径")
            return False
        
        if not os.path.exists(validate_dir):
            print(f"错误: 验证目录不存在 {validate_dir}")
            return False
        
        print(f"=== 开始验证章节质量 ===")
        print(f"验证目录: {validate_dir}")
        
        # 验证现有章节
        all_invalid, length_insufficient, other_invalid = generator.validate_existing_chapters(validate_dir)
        
        regenerated_any = False
        
        # 处理长度不足的章节
        if length_insufficient:
            print(f"\n发现 {len(length_insufficient)} 个章节长度不足: {length_insufficient}")
            try:
                user_input = input("是否重新生成这些长度不足的章节？(y/n): ").strip().lower()
                if user_input in ['y', 'yes', '是']:
                    print("\n=== 开始重新生成长度不足的章节 ===")
                    retry_success = generator.regenerate_invalid_chapters(validate_dir, length_insufficient)
                    if retry_success:
                        print("✓ 长度不足的章节重新生成成功")
                        regenerated_any = True
                    else:
                        print("✗ 部分长度不足的章节重新生成失败")
                else:
                    print("跳过重新生成长度不足的章节")
            except EOFError:
                print("跳过重新生成长度不足的章节（无输入）")
        
        # 处理其他问题的章节
        if other_invalid:
            print(f"\n发现 {len(other_invalid)} 个章节存在其他问题: {other_invalid}")
            try:
                user_input = input("是否重新生成这些有问题的章节？(y/n): ").strip().lower()
                if user_input in ['y', 'yes', '是']:
                    print("\n=== 开始重新生成有问题的章节 ===")
                    retry_success = generator.regenerate_invalid_chapters(validate_dir, other_invalid)
                    if retry_success:
                        print("✓ 有问题的章节重新生成成功")
                        regenerated_any = True
                    else:
                        print("✗ 部分有问题的章节重新生成失败")
                else:
                    print("跳过重新生成有问题的章节")
            except EOFError:
                print("跳过重新生成有问题的章节（无输入）")
        
        # 如果有重新生成，进行最终验证
        if regenerated_any:
            print("\n=== 最终验证 ===")
            final_all_invalid, final_length_insufficient, final_other_invalid = generator.validate_existing_chapters(validate_dir)
            if final_all_invalid:
                print(f"仍有 {len(final_all_invalid)} 个章节存在问题: {final_all_invalid}")
                return False
            else:
                print("所有章节最终验证通过")
                return True
        elif not all_invalid:
            print("\n✅ 所有章节验证通过，质量符合标准")
            return True
        else:
            print("\n跳过所有重新生成操作")
            return False
    
    # 生成模式
    else:
        # 检查输入文件
        if not args.novel_file:
            print("错误: 生成模式下必须提供小说文件路径")
            return False
        
        if not os.path.exists(args.novel_file):
            print(f"错误: 小说文件不存在 {args.novel_file}")
            return False
        
        # 确定输出目录
        if args.output:
            output_dir = args.output
        else:
            # 使用小说文件所在目录作为输出目录
            novel_dir = os.path.dirname(os.path.abspath(args.novel_file))
            output_dir = novel_dir
        
        print(f"输入文件: {args.novel_file}")
        print(f"输出目录: {output_dir}")
        print(f"目标章节数: {args.chapters}")
        print(f"最大并发线程数: {args.max_workers}")
        
        # 生成脚本
        success = generator.generate_script_from_novel_new(
            args.novel_file, 
            output_dir, 
            args.chapters,
            max_workers=args.max_workers
        )
        
        if success:
            print("\n=== 脚本生成成功！ ===")
            return True
        else:
            print("\n=== 脚本生成失败！ ===")
            return False

if __name__ == "__main__":
    main()