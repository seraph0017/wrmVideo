#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
gen_image_async_v3.py - 根据narration.txt生成场景图片（使用方舟SDK）

功能：
1. 遍历指定data目录下的每个chapter
2. 解析narration.txt文件，提取角色信息和图片prompt
3. 根据国风漫画风格生成完整prompt
4. 调用方舟SDK的doubao-seedream-3-0-t2i-250415模型生成图片

使用方法：
python gen_image_async_v3.py data/xxx
"""

import os
import sys
import re
import json
import time
import logging
import asyncio
from pathlib import Path
from typing import Dict, List, Tuple, Optional

# 导入方舟SDK
from volcenginesdkarkruntime import Ark

# 导入现有模块
sys.path.append(os.path.dirname(os.path.abspath(__file__)))
from config.config import ARK_CONFIG

# 配置日志
# 确保logs目录存在
os.makedirs('logs', exist_ok=True)

logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler('logs/gen_image_async_v3.log'),
        logging.StreamHandler()
    ]
)
logger = logging.getLogger(__name__)


class NarrationParser:
    """narration.txt文件解析器"""
    
    def __init__(self, narration_file: str):
        """
        初始化解析器
        
        Args:
            narration_file: narration.txt文件路径
        """
        self.narration_file = narration_file
        self.characters = {}
        self.scenes = []
        
    def parse_characters(self) -> Dict[str, Dict]:
        """
        解析角色信息
        
        Returns:
            Dict: 角色信息字典，key为角色姓名，value为角色详细信息
        """
        try:
            with open(self.narration_file, 'r', encoding='utf-8') as f:
                content = f.read()
            
            # 提取角色信息
            character_pattern = r'<角色\d+>(.*?)</角色\d+>'
            character_matches = re.findall(character_pattern, content, re.DOTALL)
            
            for match in character_matches:
                character_info = self._parse_single_character(match)
                if character_info and 'name' in character_info:
                    self.characters[character_info['name']] = character_info
                    
            logger.info(f"解析到 {len(self.characters)} 个角色")
            return self.characters
            
        except Exception as e:
            logger.error(f"解析角色信息失败: {e}")
            return {}
    
    def _parse_single_character(self, character_text: str) -> Optional[Dict]:
        """
        解析单个角色信息
        
        Args:
            character_text: 角色文本内容
            
        Returns:
            Dict: 角色信息字典
        """
        try:
            character_info = {}
            
            # 提取姓名
            name_match = re.search(r'<姓名>(.*?)</姓名>', character_text)
            if name_match:
                character_info['name'] = name_match.group(1).strip()
            
            # 提取性别
            gender_match = re.search(r'<性别>(.*?)</性别>', character_text)
            if gender_match:
                character_info['gender'] = gender_match.group(1).strip()
            
            # 提取年龄段
            age_match = re.search(r'<年龄段>(.*?)</年龄段>', character_text)
            if age_match:
                character_info['age'] = age_match.group(1).strip()
            
            # 提取外貌特征
            appearance_match = re.search(r'<外貌特征>(.*?)</外貌特征>', character_text, re.DOTALL)
            if appearance_match:
                appearance_text = appearance_match.group(1)
                character_info['appearance'] = self._parse_appearance(appearance_text)
            
            # 提取服装风格
            clothing_match = re.search(r'<服装风格>(.*?)</服装风格>', character_text, re.DOTALL)
            if clothing_match:
                clothing_text = clothing_match.group(1)
                character_info['clothing'] = self._parse_clothing(clothing_text)
            
            return character_info
            
        except Exception as e:
            logger.error(f"解析单个角色信息失败: {e}")
            return None
    
    def _parse_appearance(self, appearance_text: str) -> Dict:
        """解析外貌特征"""
        appearance = {}
        
        # 发型
        hair_style_match = re.search(r'<发型>(.*?)</发型>', appearance_text)
        if hair_style_match:
            appearance['hair_style'] = hair_style_match.group(1).strip()
        
        # 发色
        hair_color_match = re.search(r'<发色>(.*?)</发色>', appearance_text)
        if hair_color_match:
            appearance['hair_color'] = hair_color_match.group(1).strip()
        
        # 面部特征
        face_match = re.search(r'<面部特征>(.*?)</面部特征>', appearance_text)
        if face_match:
            appearance['face'] = face_match.group(1).strip()
        
        # 身材特征
        body_match = re.search(r'<身材特征>(.*?)</身材特征>', appearance_text)
        if body_match:
            appearance['body'] = body_match.group(1).strip()
        
        return appearance
    
    def _parse_clothing(self, clothing_text: str) -> Dict:
        """解析服装风格"""
        clothing = {}
        
        # 上衣
        top_match = re.search(r'<上衣>(.*?)</上衣>', clothing_text)
        if top_match:
            clothing['top'] = top_match.group(1).strip()
        
        # 下装
        bottom_match = re.search(r'<下装>(.*?)</下装>', clothing_text)
        if bottom_match:
            clothing['bottom'] = bottom_match.group(1).strip()
        
        # 配饰
        accessory_match = re.search(r'<配饰>(.*?)</配饰>', clothing_text)
        if accessory_match:
            clothing['accessory'] = accessory_match.group(1).strip()
        
        return clothing
    
    def parse_scenes(self) -> List[Dict]:
        """
        解析场景信息
        
        Returns:
            List[Dict]: 场景信息列表
        """
        try:
            with open(self.narration_file, 'r', encoding='utf-8') as f:
                content = f.read()
            
            # 提取分镜信息
            scene_pattern = r'<分镜\d+>(.*?)</分镜\d+>'
            scene_matches = re.findall(scene_pattern, content, re.DOTALL)
            
            for scene_match in scene_matches:
                scene_shots = self._parse_scene_shots(scene_match)
                self.scenes.extend(scene_shots)
            
            logger.info(f"解析到 {len(self.scenes)} 个场景镜头")
            return self.scenes
            
        except Exception as e:
            logger.error(f"解析场景信息失败: {e}")
            return []
    
    def _parse_scene_shots(self, scene_text: str) -> List[Dict]:
        """解析单个分镜中的所有镜头"""
        shots = []
        
        # 提取图片特写
        shot_pattern = r'<图片特写\d+>(.*?)</图片特写\d+>'
        shot_matches = re.findall(shot_pattern, scene_text, re.DOTALL)
        
        for shot_match in shot_matches:
            shot_info = self._parse_single_shot(shot_match)
            if shot_info:
                shots.append(shot_info)
        
        return shots
    
    def _parse_single_shot(self, shot_text: str) -> Optional[Dict]:
        """解析单个镜头信息"""
        try:
            shot_info = {}
            
            # 提取特写人物
            character_match = re.search(r'<角色姓名>(.*?)</角色姓名>', shot_text)
            if character_match:
                shot_info['character'] = character_match.group(1).strip()
            
            # 提取解说内容
            narration_match = re.search(r'<解说内容>(.*?)</解说内容>', shot_text)
            if narration_match:
                shot_info['narration'] = narration_match.group(1).strip()
            
            # 提取图片prompt
            prompt_match = re.search(r'<图片prompt>(.*?)</图片prompt>', shot_text)
            if prompt_match:
                shot_info['scene_prompt'] = prompt_match.group(1).strip()
            
            return shot_info
            
        except Exception as e:
            logger.error(f"解析单个镜头信息失败: {e}")
            return None


class ImagePromptBuilder:
    """图片prompt构建器"""
    
    def __init__(self):
        """初始化prompt构建器"""
        # 国风漫画风格描述
        self.style_prompt = (
            "画面风格是强调强烈线条、鲜明对比和现代感造型，色彩饱和，"
            "带有动态夸张与都市叙事视觉冲击力的国风漫画风格"
        )
    
    def build_character_description(self, character_info: Dict) -> str:
        """
        构建角色描述
        
        Args:
            character_info: 角色信息字典
            
        Returns:
            str: 角色描述文本
        """
        try:
            description_parts = []
            
            # 基本信息
            if 'gender' in character_info:
                gender_desc = "男性" if character_info['gender'] == 'Male' else "女性"
                description_parts.append(f"一位{gender_desc}")
            
            # 外貌特征
            if 'appearance' in character_info:
                appearance = character_info['appearance']
                
                # 面部特征
                if 'face' in appearance:
                    description_parts.append(appearance['face'])
                
                # 发型和发色
                if 'hair_style' in appearance and 'hair_color' in appearance:
                    description_parts.append(f"{appearance['hair_color']}{appearance['hair_style']}")
                
                # 身材特征
                if 'body' in appearance:
                    description_parts.append(appearance['body'])
            
            # 服装描述
            if 'clothing' in character_info:
                clothing = character_info['clothing']
                clothing_parts = []
                
                if 'top' in clothing:
                    clothing_parts.append(clothing['top'])
                if 'bottom' in clothing:
                    clothing_parts.append(clothing['bottom'])
                if 'accessory' in clothing and clothing['accessory'] != '无其他装饰':
                    clothing_parts.append(clothing['accessory'])
                
                if clothing_parts:
                    description_parts.append(f"身着{', '.join(clothing_parts)}")
            
            return "，".join(description_parts)
            
        except Exception as e:
            logger.error(f"构建角色描述失败: {e}")
            return ""
    
    def build_complete_prompt(self, character_info: Dict, scene_prompt: str) -> str:
        """
        构建完整的图片prompt
        
        Args:
            character_info: 角色信息
            scene_prompt: 场景prompt
            
        Returns:
            str: 完整的prompt
        """
        try:
            # 1. 画面风格
            style_part = self.style_prompt
            
            # 2. 人物描写
            character_part = self.build_character_description(character_info)
            
            # 3. 场景描述（包含远景近景）
            scene_part = scene_prompt
            
            # 组合完整prompt
            complete_prompt = f"{style_part}。{character_part}。{scene_part}"
            
            logger.debug(f"生成完整prompt: {complete_prompt}")
            return complete_prompt
            
        except Exception as e:
            logger.error(f"构建完整prompt失败: {e}")
            return scene_prompt  # 降级返回原始场景prompt


def save_task_info(task_id: str, task_info: Dict, tasks_dir: str = "tasks"):
    """
    保存任务信息到txt文件
    
    Args:
        task_id: 任务ID
        task_info: 任务信息
        tasks_dir: 任务文件保存目录
    """
    task_file = os.path.join(tasks_dir, f"{task_id}.txt")
    
    # 确保目录存在
    os.makedirs(tasks_dir, exist_ok=True)
    
    # 保存任务信息
    with open(task_file, 'w', encoding='utf-8') as f:
        json.dump(task_info, f, ensure_ascii=False, indent=2)
    
    logger.info(f"任务信息已保存: {task_file}")


class ArkImageGenerator:
    """方舟SDK图片生成器"""
    
    def __init__(self, data_dir: str):
        """
        初始化图片生成器
        
        Args:
            data_dir: 数据目录路径
        """
        self.data_dir = data_dir
        self.prompt_builder = ImagePromptBuilder()
        
        # 初始化方舟客户端
        self.client = Ark(
            base_url=ARK_CONFIG['base_url'],
            api_key=ARK_CONFIG['t2i_v3']  # 使用t2i_v3作为API key
        )
        
        # 模型名称
        self.model = "doubao-seedream-3-0-t2i-250415"
    
    def generate_image_sync(self, prompt: str, output_path: str, scene_number: int, max_retries: int = 3) -> bool:
        """
        同步生成图片并保存到本地
        
        Args:
            prompt: 图片prompt
            output_path: 输出路径
            scene_number: 场景编号
            max_retries: 最大重试次数
            
        Returns:
            bool: 是否成功生成并保存图片
        """
        for retry in range(max_retries):
            try:
                logger.info(f"正在生成场景 {scene_number} 的图片...")
                logger.info(f"Prompt: {prompt}")
                
                # 调用方舟SDK生成图片，使用base64格式返回，不添加水印
                images_response = self.client.images.generate(
                    model=self.model,
                    prompt=prompt,
                    response_format="b64_json",  # 返回base64格式
                    watermark=False,  # 不添加水印
                    size="720x1280",  # 图片尺寸
                )
                
                # 检查响应
                if images_response and images_response.data and len(images_response.data) > 0:
                    # 获取base64数据
                    b64_json = images_response.data[0].b64_json
                    logger.info(f"✓ 图片生成成功，获得base64数据")
                    
                    # 保存base64图片到本地
                    success = self._save_base64_image(b64_json, output_path)
                    if success:
                        logger.info(f"✓ 图片已保存到: {output_path}")
                        
                        # 保存prompt信息
                        prompt_saved = self._save_prompt_info(prompt, output_path, scene_number)
                        if not prompt_saved:
                            logger.warning(f"⚠ Prompt信息保存失败，但图片已成功保存")
                        
                        return True
                    else:
                        logger.error(f"✗ 图片保存失败: {output_path}")
                        return False
                else:
                    logger.error(f"✗ 图片生成失败，响应为空或无效")
                    return False
                    
            except Exception as e:
                error_str = str(e)
                
                # 检查是否是API限制错误
                if 'rate limit' in error_str.lower() or 'too many requests' in error_str.lower():
                    wait_time = (retry + 1) * 5  # 递增等待时间
                    logger.warning(f"API限制错误，等待 {wait_time} 秒后重试 (第 {retry + 1}/{max_retries} 次): {e}")
                    time.sleep(wait_time)
                    continue
                else:
                    logger.error(f"生成图片失败: {e}")
                    return False
        
        logger.error(f"场景 {scene_number} 在 {max_retries} 次重试后仍然失败")
        return False
    
    def _download_image(self, image_url: str, output_path: str) -> bool:
        """
        从URL下载图片到本地
        
        Args:
            image_url: 图片URL
            output_path: 本地保存路径
            
        Returns:
            bool: 是否下载成功
        """
        try:
            import requests
            
            # 确保输出目录存在
            os.makedirs(os.path.dirname(output_path), exist_ok=True)
            
            # 下载图片
            response = requests.get(image_url, timeout=30)
            response.raise_for_status()
            
            # 保存到本地
            with open(output_path, 'wb') as f:
                f.write(response.content)
            
            return True
            
        except Exception as e:
            logger.error(f"下载图片失败: {e}")
            return False
    
    def _save_base64_image(self, b64_data: str, output_path: str) -> bool:
        """
        保存base64格式的图片到本地
        
        Args:
            b64_data: base64编码的图片数据
            output_path: 输出路径
            
        Returns:
            bool: 是否保存成功
        """
        try:
            import base64
            
            # 解码base64数据
            image_data = base64.b64decode(b64_data)
            
            # 确保目录存在
            os.makedirs(os.path.dirname(output_path), exist_ok=True)
            
            # 保存图片
            with open(output_path, 'wb') as f:
                f.write(image_data)
            
            return True
        except Exception as e:
            logger.error(f"保存base64图片失败: {e}")
            return False
    
    def _save_prompt_info(self, prompt: str, output_path: str, scene_number: int) -> bool:
        """
        保存prompt信息到JSON文件
        
        Args:
            prompt: 图片生成的prompt
            output_path: 图片输出路径
            scene_number: 场景编号
            
        Returns:
            bool: 是否保存成功
        """
        try:
            from datetime import datetime
            
            # 生成prompt文件路径（与图片文件同目录，扩展名为.prompt.json）
            prompt_path = os.path.splitext(output_path)[0] + '.prompt.json'
            
            # 构建prompt信息
            prompt_info = {
                "image_file": os.path.basename(output_path),
                "prompt": prompt,
                "timestamp": datetime.now().isoformat(),
                "scene_number": scene_number,
                "model": self.model,
                "generation_params": {
                    "response_format": "b64_json",
                    "watermark": False
                }
            }
            
            # 确保目录存在
            os.makedirs(os.path.dirname(prompt_path), exist_ok=True)
            
            # 保存prompt信息到JSON文件
            with open(prompt_path, 'w', encoding='utf-8') as f:
                json.dump(prompt_info, f, ensure_ascii=False, indent=2)
            
            logger.info(f"✓ Prompt信息已保存到: {prompt_path}")
            return True
            
        except Exception as e:
            logger.error(f"保存prompt信息失败: {e}")
            return False


def process_chapter(chapter_dir: str, delay_between_requests: float = 2.0) -> int:
    """
    处理单个章节
    
    Args:
        chapter_dir: 章节目录路径
        delay_between_requests: 请求间延迟时间（秒）
        
    Returns:
        int: 成功生成的图片数量
    """
    try:
        narration_file = os.path.join(chapter_dir, 'narration.txt')
        if not os.path.exists(narration_file):
            logger.warning(f"narration.txt文件不存在: {narration_file}")
            return 0
        
        logger.info(f"开始处理章节: {chapter_dir}")
        
        # 解析narration.txt
        parser = NarrationParser(narration_file)
        characters = parser.parse_characters()
        scenes = parser.parse_scenes()
        
        if not characters or not scenes:
            logger.warning(f"章节 {chapter_dir} 没有找到角色或场景信息")
            return 0
        
        # 创建图片生成器
        generator = ArkImageGenerator(chapter_dir)
        
        # 获取章节名称用于文件命名
        chapter_name = os.path.basename(chapter_dir)
        
        # 处理每个场景
        success_count = 0
        for i, scene in enumerate(scenes, 1):
            if 'character' not in scene or 'scene_prompt' not in scene:
                logger.warning(f"场景 {i} 缺少必要信息，跳过")
                continue

            character_name = scene['character']
            if character_name not in characters:
                logger.warning(f"角色 {character_name} 信息未找到，跳过场景 {i}")
                continue

            # 构建完整prompt
            character_info = characters[character_name]
            complete_prompt = generator.prompt_builder.build_complete_prompt(
                character_info, scene['scene_prompt']
            )

            # 构建输出路径 - 新格式：chapter_xxx_image_02.jpeg
            output_filename = f"{chapter_name}_image_{i:02d}.jpeg"
            output_path = os.path.join(chapter_dir, output_filename)
            
            # 检查文件是否已存在
            if os.path.exists(output_path):
                logger.info(f"图片已存在，跳过: {output_path}")
                success_count += 1
                continue
            
            # 生成图片
            success = generator.generate_image_sync(complete_prompt, output_path, i)
            if success:
                success_count += 1
                logger.info(f"✓ 场景 {i} 图片生成成功")
            else:
                logger.error(f"✗ 场景 {i} 图片生成失败")
            
            # 请求间延迟
            if delay_between_requests > 0:
                time.sleep(delay_between_requests)
        
        logger.info(f"章节 {chapter_dir} 处理完成，成功生成 {success_count}/{len(scenes)} 张图片")
        return success_count
        
    except Exception as e:
        logger.error(f"处理章节失败: {e}")
        return 0


def is_chapter_directory(path: str) -> bool:
    """
    检测给定路径是否为章节目录
    
    Args:
        path: 要检测的目录路径
        
    Returns:
        bool: 如果是章节目录返回True，否则返回False
    """
    if not os.path.isdir(path):
        return False
    
    # 检查目录名是否以chapter_开头
    dir_name = os.path.basename(path)
    if not dir_name.startswith('chapter_'):
        return False
    
    # 检查是否包含narration.txt文件
    narration_file = os.path.join(path, 'narration.txt')
    return os.path.exists(narration_file)


def find_chapter_directories(data_dir: str) -> List[str]:
    """
    在数据目录中查找所有章节目录
    
    Args:
        data_dir: 数据目录路径
        
    Returns:
        List[str]: 章节目录路径列表，已排序
    """
    chapter_dirs = []
    for item in os.listdir(data_dir):
        item_path = os.path.join(data_dir, item)
        if is_chapter_directory(item_path):
            chapter_dirs.append(item_path)
    
    return sorted(chapter_dirs)


def main():
    """主函数"""
    if len(sys.argv) != 2:
        print("使用方法: python gen_image_async_v3.py data/xxx")
        print("支持处理:")
        print("  - 数据目录 (如: data/001) - 处理该目录下所有章节")
        print("  - 单个章节目录 (如: data/001/chapter_001) - 只处理该章节")
        sys.exit(1)
    
    input_path = sys.argv[1]
    
    if not os.path.exists(input_path):
        logger.error(f"路径不存在: {input_path}")
        sys.exit(1)
    
    # 判断输入路径类型并获取要处理的章节目录列表
    chapter_dirs = []
    
    if is_chapter_directory(input_path):
        # 输入的是单个章节目录
        chapter_dirs = [input_path]
        logger.info(f"开始处理单个章节: {input_path}")
    else:
        # 输入的是数据目录，查找其下的所有章节目录
        logger.info(f"开始处理数据目录: {input_path}")
        chapter_dirs = find_chapter_directories(input_path)
        
        if not chapter_dirs:
            logger.warning(f"在 {input_path} 中没有找到章节目录")
            logger.info("请确保:")
            logger.info("  1. 目录下包含以 'chapter_' 开头的子目录")
            logger.info("  2. 每个章节目录中包含 'narration.txt' 文件")
            return
    
    logger.info(f"找到 {len(chapter_dirs)} 个章节目录")
    
    # 处理每个章节
    total_success = 0
    total_chapters = len(chapter_dirs)
    
    for i, chapter_dir in enumerate(chapter_dirs, 1):
        logger.info(f"处理章节 {i}/{total_chapters}: {chapter_dir}")
        success_count = process_chapter(chapter_dir)
        total_success += success_count
        
        # 章节间延迟
        if i < total_chapters:
            time.sleep(1)
    
    logger.info(f"所有章节处理完成，总共成功生成 {total_success} 张图片")


if __name__ == "__main__":
    main()