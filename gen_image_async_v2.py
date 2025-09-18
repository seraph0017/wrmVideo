#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
gen_image_async_v2.py - 根据narration.txt生成场景图片

功能：
1. 遍历指定data目录下的每个chapter
2. 解析narration.txt文件，提取角色信息和图片prompt
3. 根据国风漫画风格生成完整prompt
4. 调用high_aes_general_v21_L接口生成图片

使用方法：
python gen_image_async_v2.py data/xxx
"""

import os
import sys
import re
import json
import time
import logging
from pathlib import Path
from typing import Dict, List, Tuple, Optional

# 导入现有模块
sys.path.append(os.path.dirname(os.path.abspath(__file__)))
from config.config import IMAGE_TWO_CONFIG
from volcengine.visual.VisualService import VisualService

# 配置日志
# 确保logs目录存在
os.makedirs('logs', exist_ok=True)

logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler('logs/gen_image_async_v2.log'),
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
            "强调强烈线条、鲜明对比和现代感造型，色彩饱和，"
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


class ImageGenerator:
    """图片生成器"""
    
    def __init__(self, data_dir: str):
        """
        初始化图片生成器
        
        Args:
            data_dir: 数据目录路径
        """
        self.data_dir = data_dir
        self.prompt_builder = ImagePromptBuilder()
        
        # 初始化VisualService
        self.visual_service = VisualService()
        self.visual_service.set_ak(IMAGE_TWO_CONFIG['access_key'])
        self.visual_service.set_sk(IMAGE_TWO_CONFIG['secret_key'])
    
    def generate_image_async(self, prompt: str, output_path: str, scene_number: int, max_retries: int = 3) -> Optional[str]:
        """
        异步生成图片
        
        Args:
            prompt: 图片prompt
            output_path: 输出路径
            scene_number: 场景编号
            max_retries: 最大重试次数
            
        Returns:
            str: 任务ID，如果失败返回None
        """
        for retry in range(max_retries):
            try:
                # 构建请求参数
                form_data = {
                    'prompt': prompt,
                    'seed': -1,
                    'negative_prompt': IMAGE_TWO_CONFIG.get('negative_prompt', ''),
                    'req_key': IMAGE_TWO_CONFIG.get('req_key', 'high_aes_general_v20_L'),
                    'width': IMAGE_TWO_CONFIG.get('default_width', 720),
                    'height': IMAGE_TWO_CONFIG.get('default_height', 1280),
                    'scale': IMAGE_TWO_CONFIG.get('scale', 3.5),
                    'ddim_steps': IMAGE_TWO_CONFIG.get('ddim_steps', 25),
                    'use_pre_llm': IMAGE_TWO_CONFIG.get('use_pre_llm', True),
                    'use_sr': IMAGE_TWO_CONFIG.get('use_sr', True),
                    'return_url': IMAGE_TWO_CONFIG.get('return_url', False)
                }
                
                logger.info("prompt ===>>> {}".format(json.dumps(form_data, indent=2, ensure_ascii=False))) 
                # 调用API
                resp = self.visual_service.cv_sync2async_submit_task(form_data)
                
                logger.info("resp ===>>> {}".format(json.dumps(resp, indent=2, ensure_ascii=False)))
                
                # 检查响应格式 - 支持两种格式：新格式(code/data)和旧格式(ResponseMetadata)
                if resp and (
                    (resp.get('code') == 10000 and 'data' in resp and 'task_id' in resp['data']) or
                    ('ResponseMetadata' in resp and resp['ResponseMetadata']['Error']['Code'] == '')
                ):
                    # 获取task_id - 支持两种响应格式
                    if 'data' in resp and 'task_id' in resp['data']:
                        task_id = resp['data']['task_id']
                    else:
                        task_id = resp['Result']['task_id']
                    
                    logger.info(f"✓ 任务提交成功，Task ID: {task_id}")
                    
                    # 保存任务信息到async_tasks目录 - 参考gen_image_async.py的格式
                    task_info = {
                        'task_id': task_id,
                        'output_path': output_path,
                        'filename': os.path.basename(output_path),
                        'prompt': prompt,
                        'full_prompt': prompt,  # 在这个版本中prompt就是完整的prompt
                        'character_images': [],  # 这个版本没有角色图片
                        'submit_time': time.time(),
                        'status': 'submitted',
                        'attempt': retry + 1,
                        'scene_number': scene_number
                    }
                    
                    # 使用async_tasks目录保存
                    async_tasks_dir = 'async_tasks'
                    save_task_info(task_id, task_info, async_tasks_dir)
                    logger.info(f"提交图片生成任务: {task_id}, 场景: {scene_number}")
                    return task_id
                else:
                    # 处理错误信息 - 支持两种格式
                    if resp and 'message' in resp:
                        error_msg = resp.get('message', '未知错误')
                    elif resp and 'ResponseMetadata' in resp:
                        error_msg = resp.get('ResponseMetadata', {}).get('Error', {}).get('Message', '未知错误')
                    else:
                        error_msg = '请求失败'
                    
                    # 检查是否是API限制错误
                    if 'API Limit' in str(error_msg) or '50429' in str(error_msg):
                        wait_time = (retry + 1) * 5  # 递增等待时间
                        logger.warning(f"API限制错误，等待 {wait_time} 秒后重试 (第 {retry + 1}/{max_retries} 次)")
                        time.sleep(wait_time)
                        continue
                    else:
                        logger.error(f"提交图片生成任务失败，场景: {scene_number}, 错误: {error_msg}")
                        return None
                        
            except Exception as e:
                error_str = str(e)
                
                # 检查是否是API限制错误
                if 'API Limit' in error_str or '50429' in error_str:
                    wait_time = (retry + 1) * 5  # 递增等待时间
                    logger.warning(f"API限制错误，等待 {wait_time} 秒后重试 (第 {retry + 1}/{max_retries} 次): {e}")
                    time.sleep(wait_time)
                    continue
                else:
                    logger.error(f"生成图片失败: {e}")
                    return None
        
        logger.error(f"场景 {scene_number} 在 {max_retries} 次重试后仍然失败")
        return None


def process_chapter(chapter_dir: str, delay_between_requests: float = 2.0) -> int:
    """
    处理单个章节
    
    Args:
        chapter_dir: 章节目录路径
        delay_between_requests: 请求间延迟时间（秒）
        
    Returns:
        int: 成功提交的任务数量
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
        generator = ImageGenerator(chapter_dir)
        
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
            
            # 提交生成任务
            task_id = generator.generate_image_async(complete_prompt, output_path, i)
            if task_id:
                success_count += 1
            
            # 添加延迟避免API限制
            if i < len(scenes):  # 最后一个请求不需要延迟
                logger.debug(f"等待 {delay_between_requests} 秒后处理下一个场景...")
                time.sleep(delay_between_requests)
        
        logger.info(f"章节 {chapter_dir} 处理完成，成功提交 {success_count}/{len(scenes)} 个任务")
        return success_count
        
    except Exception as e:
        logger.error(f"处理章节失败 {chapter_dir}: {e}")
        return 0


def main():
    """主函数"""
    if len(sys.argv) != 2:
        print("使用方法: python gen_image_async_v2.py data/xxx")
        sys.exit(1)
    
    data_path = sys.argv[1]
    if not os.path.exists(data_path):
        logger.error(f"数据目录不存在: {data_path}")
        sys.exit(1)
    
    logger.info(f"开始处理数据目录: {data_path}")
    
    # 查找所有章节目录
    chapter_dirs = []
    for item in os.listdir(data_path):
        item_path = os.path.join(data_path, item)
        if os.path.isdir(item_path) and item.startswith('chapter_'):
            chapter_dirs.append(item_path)
    
    if not chapter_dirs:
        logger.error(f"在 {data_path} 中没有找到章节目录")
        sys.exit(1)
    
    # 按章节编号排序
    chapter_dirs.sort()
    
    # 处理每个章节
    total_chapters = len(chapter_dirs)
    total_tasks = 0
    
    for chapter_dir in chapter_dirs:
        task_count = process_chapter(chapter_dir)
        total_tasks += task_count
    
    logger.info(f"处理完成，总共提交 {total_tasks} 个图片生成任务")


if __name__ == "__main__":
    main()