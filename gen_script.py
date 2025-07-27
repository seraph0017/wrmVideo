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
from typing import List, Dict, Optional, Tuple
from volcenginesdkarkruntime import Ark
from jinja2 import Environment, FileSystemLoader
try:
    import rarfile
except ImportError:
    rarfile = None

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
        读取小说文件，支持多种编码格式和RAR压缩文件
        
        Args:
            file_path: 文件路径
        
        Returns:
            str: 文件内容
        """
        # 检查是否为RAR文件
        if file_path.lower().endswith('.rar'):
            return self._read_rar_file(file_path)
        
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
                    result = subprocess.run(cmd, capture_output=True, text=True, timeout=300)
                    
                    if result.returncode == 0:
                        print(f"成功使用 {cmd[0]} 提取文件")
                        extracted = True
                        break
                    else:
                        print(f"{cmd[0]} 提取失败：{result.stderr}")
                        
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
                max_tokens=32*1024,
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
            template = env.get_template('chapter_narration_prompt.j2')
            
            # 示例人物数据（实际使用时可以从章节内容中提取或预定义）
            characters = [
                {
                    'name': '主角',
                    'height_build': '身材高大（约180cm），体型匀称',
                    'hair_color': '乌黑色',
                    'hair_style': '短发寸头',
                    'hair_texture': '直发',
                    'eye_color': '深棕色',
                    'eye_shape': '丹凤眼',
                    'eye_expression': '眼神犀利专注',
                    'face_shape': '方形脸',
                    'chin_shape': '方形下巴',
                    'skin_tone': '健康肤色',
                    'clothing_color': '深蓝色',
                    'clothing_style': '长款羊毛风衣',
                    'clothing_material': '羊毛',
                    'glasses': '黑框眼镜',
                    'jewelry': '银色金属表带手表',
                    'other_accessories': '无',
                    'expression_posture': '给人可靠专业的感觉'
                }
            ]
            
            # 渲染模板
            custom_prompt = template.render(
                chapter_num=chapter_num,
                total_chapters=total_chapters,
                chapter_content=chapter_content,
                characters=characters
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
    
    def generate_script_from_novel_new(self, novel_file: str, output_dir: str, target_chapters: int = 50) -> bool:
        """
        新的小说脚本生成函数，支持章节分割和1200字解说生成
        
        Args:
            novel_file: 小说文件路径
            output_dir: 输出目录
            target_chapters: 目标章节数量（默认50）
        
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
                
                # 生成1200字解说文案
                narration = self.generate_chapter_narration(chapter_content, i, len(chapters))
                
                if narration:
                    # 保存解说文案
                    narration_file = os.path.join(chapter_dir, "narration.txt")
                    with open(narration_file, 'w', encoding='utf-8') as f:
                        f.write(narration)
                    
                    print(f"✓ 第{i}章解说文案已保存")
                    success_count += 1
                else:
                    print(f"✗ 第{i}章解说文案生成失败")
            
            print(f"\n=== 脚本生成完成 ===")
            print(f"成功生成 {success_count}/{len(chapters)} 个章节的解说文案")
            print(f"输出目录: {output_dir}")
            
            return success_count > 0
            
        except Exception as e:
            print(f"生成脚本时发生错误: {e}")
            return False

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
    主函数，处理命令行参数
    """
    parser = argparse.ArgumentParser(description='小说脚本生成工具')
    parser.add_argument('novel_file', help='小说文件路径')
    parser.add_argument('--output', '-o', default=None, help='输出目录（默认为小说文件所在目录）')
    parser.add_argument('--chapters', '-c', type=int, default=50, help='目标章节数量（默认50）')
    
    args = parser.parse_args()
    
    # 检查输入文件
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
    
    # 创建脚本生成器
    generator = ScriptGenerator()
    
    # 生成脚本
    success = generator.generate_script_from_novel_new(
        args.novel_file, 
        output_dir, 
        args.chapters
    )
    
    if success:
        print("\n=== 脚本生成成功！ ===")
        return True
    else:
        print("\n=== 脚本生成失败！ ===")
        return False

if __name__ == "__main__":
    main()