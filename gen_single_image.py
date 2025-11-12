#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
gen_single_image.py - 生成单张图片（指定场景编号）

用法：
python gen_single_image.py <章节目录> --scene_number <场景编号> [--prompt "自定义prompt"]
"""

import os
import sys
import json
import time
import logging
from pathlib import Path

# 导入配置
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from config.config import COMFYUI_CONFIG

# 导入gen_image_async_v4的类
from gen_image_async_v4 import (
    ComfyUIClient,
    NarrationParser,
    ImagePromptBuilder,
    load_workflow_json,
    set_positive_prompt,
    save_prompt_info
)

# ComfyUI API地址从配置读取
DEFAULT_COMFYUI_HOST = COMFYUI_CONFIG.get("default_host", "127.0.0.1:8188")
DEFAULT_COMFYUI_PROMPT_URL = f"http://{DEFAULT_COMFYUI_HOST}/api/prompt"

# 日志配置
os.makedirs('logs', exist_ok=True)
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler('logs/gen_single_image.log'),
        logging.StreamHandler()
    ]
)
logger = logging.getLogger(__name__)


def generate_single_image(
    chapter_dir: str,
    scene_number: int,
    client: ComfyUIClient,
    workflow_template: dict,
    custom_prompt: str = None,
    poll_interval: float = 1.0,
    max_wait: int = 300
) -> bool:
    """
    生成单张图片
    
    Args:
        chapter_dir: 章节目录路径
        scene_number: 场景编号
        client: ComfyUI客户端
        workflow_template: 工作流模板
        custom_prompt: 自定义prompt（可选，如果提供则直接使用，否则从narration.txt解析）
        poll_interval: 轮询间隔
        max_wait: 最大等待时间
    
    Returns:
        bool: 是否生成成功
    """
    try:
        chapter_dir_path = Path(chapter_dir)
        chapter_name = chapter_dir_path.name
        
        # 构建输出文件名
        output_filename = f"{chapter_name}_image_{scene_number:02d}.jpeg"
        output_path = chapter_dir_path / output_filename
        
        logger.info(f"开始生成图片: {output_path}")
        
        # 如果提供了自定义prompt，直接使用
        if custom_prompt:
            complete_prompt = custom_prompt
            logger.info(f"使用自定义prompt")
        else:
            # 从narration.txt解析prompt
            narration_file = chapter_dir_path / 'narration.txt'
            if not narration_file.exists():
                logger.error(f"narration.txt文件不存在: {narration_file}")
                return False
            
            parser = NarrationParser(str(narration_file))
            characters = parser.parse_characters()
            scenes = parser.parse_scenes()
            
            if not characters or not scenes:
                logger.error(f"无法解析角色或场景信息")
                return False
            
            # 查找对应场景编号的场景
            if scene_number < 1 or scene_number > len(scenes):
                logger.error(f"场景编号 {scene_number} 超出范围 (1-{len(scenes)})")
                return False
            
            scene = scenes[scene_number - 1]
            
            if 'character' not in scene or 'scene_prompt' not in scene:
                logger.error(f"场景 {scene_number} 缺少必要信息")
                return False
            
            character_name = scene['character']
            if character_name not in characters:
                logger.error(f"角色 {character_name} 信息未找到")
                return False
            
            # 构建完整prompt
            prompt_builder = ImagePromptBuilder()
            character_info = characters[character_name]
            complete_prompt = prompt_builder.build_complete_prompt(
                character_info,
                scene['scene_prompt']
            )
        
        logger.info(f"Prompt长度: {len(complete_prompt)} 字符")
        logger.info(f"Prompt前100字符: {complete_prompt[:100]}...")
        
        # 替换工作流中的正向提示词
        wf = set_positive_prompt(workflow_template, complete_prompt)
        
        # 提交工作流
        ok, res, err = client.submit_workflow(wf, filename_param=output_filename)
        if not ok:
            logger.error(f"工作流提交失败: {err}")
            return False
        
        prompt_id = None
        if isinstance(res, dict):
            prompt_id = res.get('prompt_id') or (res.get('data') or {}).get('prompt_id')
        
        if not prompt_id:
            logger.error(f"未获取到 prompt_id，响应: {res}")
            return False
        
        logger.info(f"prompt_id: {prompt_id}")
        
        # 轮询输出文件名
        filename, subfolder, type_ = client.wait_for_output_filename(
            prompt_id,
            poll_interval=poll_interval,
            max_wait=max_wait,
            filename_param=output_filename
        )
        
        if not filename:
            logger.error(f"未获取到输出文件")
            return False
        
        # 下载并重命名到章节目录
        saved = client.download_view_file_as(
            filename,
            subfolder or '',
            type_ or 'output',
            save_dir=str(chapter_dir_path),
            save_as=output_filename,
            filename_param=output_filename
        )
        
        if not saved:
            logger.error(f"下载失败")
            return False
        
        # 保存prompt信息
        save_prompt_info(
            complete_prompt,
            str(output_path),
            workflow_name='image_compact.json',
            scene_number=scene_number
        )
        
        logger.info(f"✓ 图片生成成功: {output_path}")
        return True
        
    except Exception as e:
        logger.error(f"生成图片失败: {e}", exc_info=True)
        return False


def main():
    import argparse
    
    parser = argparse.ArgumentParser(description="生成单张图片")
    parser.add_argument('chapter_dir', help='章节目录路径(如 data/020/chapter_001)')
    parser.add_argument('--scene_number', type=int, required=True, help='场景编号')
    parser.add_argument('--prompt', help='自定义prompt（可选，不提供则从narration.txt解析）')
    parser.add_argument('--api_url', default=DEFAULT_COMFYUI_PROMPT_URL, help=f'ComfyUI api/prompt 地址 (默认: {DEFAULT_COMFYUI_PROMPT_URL})')
    parser.add_argument('--workflow_json', default=os.path.join('test', 'comfyui', 'image_compact.json'), help='工作流JSON模板路径')
    parser.add_argument('--timeout', type=int, default=COMFYUI_CONFIG.get('timeout', 300), help='请求超时(秒)')
    parser.add_argument('--max_retries', type=int, default=3, help='提交重试次数')
    parser.add_argument('--poll_interval', type=float, default=COMFYUI_CONFIG.get('poll_interval', 1.0), help='轮询history间隔(秒)')
    parser.add_argument('--max_wait', type=int, default=300, help='轮询最长等待(秒)')
    
    args = parser.parse_args()
    
    # 验证章节目录
    if not os.path.exists(args.chapter_dir):
        logger.error(f"章节目录不存在: {args.chapter_dir}")
        sys.exit(1)
    
    if not os.path.isdir(args.chapter_dir):
        logger.error(f"不是目录: {args.chapter_dir}")
        sys.exit(1)
    
    # 初始化客户端与工作流模板
    logger.info(f"ComfyUI API: {args.api_url}")
    client = ComfyUIClient(api_url=args.api_url, timeout=args.timeout, max_retries=args.max_retries)
    workflow_template = load_workflow_json(args.workflow_json)
    logger.info(f"加载工作流模板: {args.workflow_json}")
    
    # 生成图片
    success = generate_single_image(
        args.chapter_dir,
        args.scene_number,
        client,
        workflow_template,
        custom_prompt=args.prompt,
        poll_interval=args.poll_interval,
        max_wait=args.max_wait
    )
    
    if success:
        logger.info("✓ 图片生成成功")
        sys.exit(0)
    else:
        logger.error("✗ 图片生成失败")
        sys.exit(1)


if __name__ == '__main__':
    main()

