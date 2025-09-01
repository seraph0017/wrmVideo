#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
重新生成失败图片脚本
基于fail.txt文件中的失败图片路径，重新生成符合要求的角色图片

使用方法:
    python regenerate_failed_images.py
    python regenerate_failed_images.py --batch-size 10
    python regenerate_failed_images.py --start-index 0 --end-index 100
"""

import os
import re
import json
import random
import time
import argparse
from pathlib import Path
# ART_STYLES 配置已移除
from config.config import IMAGE_TWO_CONFIG
from volcengine.visual.VisualService import VisualService

def parse_fail_txt(fail_file_path):
    """
    解析fail.txt文件，提取失败的图片路径
    
    Args:
        fail_file_path: fail.txt文件路径
    
    Returns:
        list: 失败图片路径列表
    """
    failed_paths = []
    
    try:
        with open(fail_file_path, 'r', encoding='utf-8') as f:
            for line in f:
                line = line.strip()
                if line and ' - ' in line:
                    # 提取路径部分（在" - "之前的部分）
                    path = line.split(' - ')[0].strip()
                    if path.endswith('.jpeg') or path.endswith('.jpg') or path.endswith('.png'):
                        failed_paths.append(path)
    except Exception as e:
        print(f"读取fail.txt文件时出错: {e}")
        return []
    
    return failed_paths

def parse_image_path_info(image_path):
    """
    从图片路径解析角色信息
    
    Args:
        image_path: 图片文件路径
    
    Returns:
        dict: 包含gender, age, style, culture, temperament等信息的字典
    """
    # 提取相对路径部分
    if 'Character_Images' in image_path:
        relative_path = image_path.split('Character_Images')[1]
        if relative_path.startswith('/'):
            relative_path = relative_path[1:]
    else:
        return None
    
    parts = relative_path.split(os.sep)
    
    # 解析性别
    gender = "男" if "Male" in parts else "女" if "Female" in parts else "未知"
    
    # 解析年龄、风格、文化、气质
    age = "未知"
    style = "未知"
    culture = "未知"
    temperament = "未知"
    
    for part in parts:
        # 年龄匹配
        if "_" in part and any(char.isdigit() for char in part):
            age_match = re.search(r'(\d+-\d+)_(.+)', part)
            if age_match:
                age = age_match.group(2)  # 取后面的描述部分
        
        # 风格匹配
        if part in ["Ancient", "Fantasy", "Modern", "SciFi"]:
            style = part
        
        # 文化匹配
        if part in ["Chinese", "Western"]:
            culture = part
        
        # 气质匹配
        if part in ["Chivalrous", "Common", "Royal", "Scholarly", "Knight", "Mage", "Mythic", 
                   "Cool", "Gentle", "Sunny", "Tough", "Scientist", "Survivor", "Warrior",
                   "Villain", "Mysterious", "Merchant", "Assassin", "Monk", "Beggar"]:
            temperament = part
    
    return {
        "gender": gender,
        "age": age,
        "style": style,
        "culture": culture,
        "temperament": temperament,
        "original_path": image_path,
        "directory": os.path.dirname(image_path),
        "filename": os.path.basename(image_path)
    }

def generate_enhanced_prompt(dir_info):
    """
    生成增强的prompt，特别强调领口要求
    
    Args:
        dir_info: 目录信息字典
    
    Returns:
        str: 生成的prompt
    """
    # 基础信息
    gender_desc = "男性" if dir_info["gender"] == "男" else "女性"
    
    # 根据气质调整描述
    temperament_desc = {
        "Villain": "邪恶反派，阴险狡诈",
        "Mysterious": "神秘莫测，深不可测", 
        "Merchant": "精明商人，和善可亲",
        "Assassin": "冷酷杀手，眼神锐利",
        "Monk": "慈悲僧侣，宁静祥和",
        "Beggar": "落魄乞丐，沧桑憔悴",
        "Chivalrous": "侠义英雄，正气凛然",
        "Common": "平民百姓，朴实无华",
        "Royal": "皇室贵族，高贵典雅",
        "Scholarly": "文人学者，书卷气息",
        "Knight": "骑士武士，英勇无畏",
        "Mage": "法师术士，神秘智慧",
        "Mythic": "神话传说，超凡脱俗",
        "Cool": "冷酷帅气，个性十足",
        "Gentle": "温柔善良，亲和力强",
        "Sunny": "阳光开朗，活力四射",
        "Tough": "坚韧不拔，意志坚强",
        "Scientist": "科学家，理性睿智",
        "Survivor": "幸存者，坚毅顽强",
        "Warrior": "战士勇者，勇猛无敌"
    }.get(dir_info['temperament'], dir_info['temperament'])
    
    # 根据文化背景调整服装描述
    culture_desc = ""
    clothing_style = ""
    if dir_info['culture'] == "Chinese":
        culture_desc = "中式古典风格"
        clothing_style = "中式传统服装，汉服、唐装或古代袍服"
    elif dir_info['culture'] == "Western":
        culture_desc = "西式风格"
        clothing_style = "西式服装，欧美风格"
    else:
        culture_desc = "混合风格"
        clothing_style = "传统服装"
    
    # 生成随机变化
    hair_colors = ["黑色", "棕色", "金色", "银色", "白色", "红色"]
    hair_styles = ["短发", "长发", "中长发", "盘发", "辫子", "卷发"]
    expressions = ["微笑", "严肃", "温和", "坚毅", "冷漠", "神秘", "慈祥"]
    clothing_details = ["简约", "华丽", "朴素", "精致"]
    skin_tones = ["白皙", "健康", "古铜色", "偏黄"]
    
    hair_color = random.choice(hair_colors)
    hair_style = random.choice(hair_styles)
    expression = random.choice(expressions)
    clothing = random.choice(clothing_details)
    skin_tone = random.choice(skin_tones)
    
    # 强化的领口要求
    collar_requirements = [
        "必须是圆领袍",
        "高领设计",
        "立领或高领",
        "严禁V领",
        "严禁低领",
        "严禁衽领",
        "严禁交领",
        "绝对不能露出脖子部位",
        "领口要完全遮盖脖子",
        "高领内衬",
        "领口紧贴脖子"
    ]
    
    collar_desc = "，".join(random.sample(collar_requirements, 6))
    
    prompt = f"""图片风格为「动漫」，宫崎骏，{culture_desc}
比例 「9:16」
服装要求：{collar_desc}
年龄：{dir_info['age']}
风格：{dir_info['style']}
文化：{dir_info['culture']}
气质：{temperament_desc}
角度：正面半身照

单人肖像，{gender_desc}，{skin_tone}肌肤，{hair_color}{hair_style}，表情{expression}，{clothing_style}，{clothing}风格，高质量角色设定图，正面视角，清晰面部特征，动漫风格

特别要求：
- 领口必须完全遮盖脖子
- 不允许任何形式的V领或低领
- 必须是圆领、立领或高领设计
- 严禁衽领（交领）
- 如果是中式服装，必须有高领内衬"""
    
    return prompt

def submit_image_task(prompt, task_info, max_retries=3, retry_delay=2):
    """
    提交异步图片生成任务（带重试机制）
    
    Args:
        prompt: 图片描述
        task_info: 任务信息字典
        max_retries: 最大重试次数
        retry_delay: 重试间隔（秒）
    
    Returns:
        str: 任务ID，失败返回None
    """
    for attempt in range(max_retries + 1):
        try:
            visual_service = VisualService()
            
            # 设置访问密钥
            visual_service.set_ak(IMAGE_TWO_CONFIG['access_key'])
            visual_service.set_sk(IMAGE_TWO_CONFIG['secret_key'])
            
            # 构建完整的prompt
            full_prompt = """以下内容为描述生成图片
                            宫崎骏动漫风格，人物着装：圆领袍，高领设计，不漏脖子\n\n
            """ + prompt + "\n\n"
            
            if attempt == 0:
                print(f"提交重新生成任务: {task_info['filename']}")
                print(f"原始路径: {task_info['original_path']}")
            else:
                print(f"重试提交任务 (第{attempt}次): {task_info['filename']}")
            
            # 请求参数
            form = {
                "req_key": "high_aes_general_v21_L",
                "prompt": full_prompt,
                "llm_seed": -1,
                "seed": -1,
                "scale": IMAGE_TWO_CONFIG['scale'],
                "ddim_steps": IMAGE_TWO_CONFIG['ddim_steps'],
                "width": IMAGE_TWO_CONFIG['default_width'],
                "height": IMAGE_TWO_CONFIG['default_height'],
                "use_pre_llm": IMAGE_TWO_CONFIG['use_pre_llm'],
                "use_sr": IMAGE_TWO_CONFIG['use_sr'],
                "return_url": IMAGE_TWO_CONFIG['return_url'],
                "negative_prompt": IMAGE_TWO_CONFIG['negative_prompt'],
                "logo_info": {
                    "add_logo": False,
                    "position": 0,
                    "language": 0,
                    "opacity": 0.3,
                    "logo_text_content": "这里是明水印内容"
                }
            }
            
            # 提交异步任务
            resp = visual_service.cv_sync2async_submit_task(form)
            
            # 检查响应
            if 'data' in resp and 'task_id' in resp['data']:
                task_id = resp['data']['task_id']
                print(f"任务提交成功，task_id: {task_id}")
                return task_id
            else:
                error_msg = str(resp)
                print(f"任务提交失败: {error_msg}")
                
                # 如果是访问被拒绝错误且还有重试机会，则重试
                if attempt < max_retries and ("Access Denied" in error_msg or "Internal Error" in error_msg):
                    print(f"等待 {retry_delay} 秒后重试...")
                    time.sleep(retry_delay)
                    retry_delay *= 2  # 指数退避
                    continue
                else:
                    return None
                    
        except Exception as e:
            error_msg = str(e)
            print(f"提交任务时发生错误: {error_msg}")
            
            # 如果是访问被拒绝错误且还有重试机会，则重试
            if attempt < max_retries and ("Access Denied" in error_msg or "Internal Error" in error_msg):
                print(f"等待 {retry_delay} 秒后重试...")
                time.sleep(retry_delay)
                retry_delay *= 2  # 指数退避
                continue
            else:
                return None
    
    return None

def save_task_info(task_id, task_info, tasks_dir):
    """
    保存任务信息到txt文件
    
    Args:
        task_id: 任务ID
        task_info: 任务信息
        tasks_dir: 任务文件保存目录
    """
    task_file = os.path.join(tasks_dir, f"regenerate_{task_id}.txt")
    
    # 确保目录存在
    os.makedirs(tasks_dir, exist_ok=True)
    
    # 保存任务信息
    with open(task_file, 'w', encoding='utf-8') as f:
        json.dump(task_info, f, ensure_ascii=False, indent=2)
    
    print(f"任务信息已保存: {task_file}")

def generate_new_filename(original_path):
    """
    为重新生成的图片生成新的文件名
    
    Args:
        original_path: 原始图片路径
    
    Returns:
        str: 新的文件名
    """
    directory = os.path.dirname(original_path)
    original_filename = os.path.basename(original_path)
    name, ext = os.path.splitext(original_filename)
    
    # 添加_regenerated后缀
    new_filename = f"{name}_regenerated{ext}"
    new_path = os.path.join(directory, new_filename)
    
    return new_path

def process_failed_images(failed_paths, tasks_dir, start_index=0, end_index=None, batch_size=None):
    """
    处理失败的图片，重新生成
    
    Args:
        failed_paths: 失败图片路径列表
        tasks_dir: 任务文件保存目录
        start_index: 开始索引
        end_index: 结束索引
        batch_size: 批处理大小
    
    Returns:
        int: 成功提交的任务数量
    """
    if end_index is None:
        end_index = len(failed_paths)
    
    if batch_size:
        end_index = min(start_index + batch_size, len(failed_paths))
    
    end_index = min(end_index, len(failed_paths))
    
    print(f"\n=== 处理失败图片重新生成 ===")
    print(f"总共 {len(failed_paths)} 个失败图片")
    print(f"处理范围: {start_index} - {end_index-1}")
    print(f"本次处理: {end_index - start_index} 个图片\n")
    
    submitted_count = 0
    
    for i in range(start_index, end_index):
        image_path = failed_paths[i]
        
        print(f"\n--- 处理第 {i+1}/{len(failed_paths)} 个失败图片 ---")
        print(f"原始路径: {image_path}")
        
        # 解析图片路径信息
        dir_info = parse_image_path_info(image_path)
        if not dir_info:
            print(f"无法解析路径信息，跳过: {image_path}")
            continue
        
        print(f"解析信息: {dir_info['gender']}, {dir_info['age']}, {dir_info['style']}, {dir_info['culture']}, {dir_info['temperament']}")
        
        # 生成增强的prompt
        prompt = generate_enhanced_prompt(dir_info)
        
        # 生成新的文件名
        new_path = generate_new_filename(image_path)
        new_filename = os.path.basename(new_path)
        
        # 准备任务信息
        task_info = {
            "prompt": prompt,
            "output_path": new_path,
            "filename": new_filename,
            "directory": dir_info['directory'],
            "dir_info": dir_info,
            "original_path": image_path,
            "status": "submitted",
            "regeneration": True
        }
        
        # 提交任务
        task_id = submit_image_task(prompt, task_info)
        if task_id:
            task_info["task_id"] = task_id
            save_task_info(task_id, task_info, tasks_dir)
            submitted_count += 1
            print(f"  ✓ 成功提交重新生成任务")
        else:
            print(f"  ✗ 重新生成任务提交失败")
        
        # 添加请求间隔，避免API频率限制
        if i < end_index - 1:  # 不是最后一个任务
            time.sleep(1)  # 等待1秒
    
    return submitted_count

def main():
    """
    主函数
    """
    parser = argparse.ArgumentParser(
        description='重新生成失败图片脚本',
        formatter_class=argparse.RawDescriptionHelpFormatter
    )
    
    parser.add_argument(
        '--fail-file', '-f',
        default='data/fail.txt',
        help='失败图片列表文件路径 (默认: data/fail.txt)'
    )
    
    parser.add_argument(
        '--tasks-dir', '-t',
        default='async_tasks',
        help='任务文件保存目录 (默认: async_tasks)'
    )
    
    parser.add_argument(
        '--start-index', '-s',
        type=int,
        default=0,
        help='开始处理的索引 (默认: 0)'
    )
    
    parser.add_argument(
        '--end-index', '-e',
        type=int,
        help='结束处理的索引 (可选)'
    )
    
    parser.add_argument(
        '--batch-size', '-b',
        type=int,
        help='批处理大小 (可选)'
    )
    
    args = parser.parse_args()
    
    print(f"=== 重新生成失败图片脚本 ===")
    print(f"失败图片文件: {args.fail_file}")
    print(f"任务保存目录: {args.tasks_dir}\n")
    
    # 检查fail.txt文件是否存在
    if not os.path.exists(args.fail_file):
        print(f"错误: 文件不存在 {args.fail_file}")
        return
    
    # 解析失败图片路径
    print("正在解析失败图片列表...")
    failed_paths = parse_fail_txt(args.fail_file)
    
    if not failed_paths:
        print("未找到失败的图片路径")
        return
    
    print(f"发现 {len(failed_paths)} 个失败图片")
    
    # 显示处理范围
    start_idx = args.start_index
    end_idx = args.end_index if args.end_index else len(failed_paths)
    if args.batch_size:
        end_idx = min(start_idx + args.batch_size, len(failed_paths))
    
    print(f"处理范围: {start_idx} - {end_idx-1} ({end_idx - start_idx} 个图片)")
    
    # 询问用户是否继续
    user_input = input("\n是否继续提交重新生成任务？(y/n): ").strip().lower()
    if user_input not in ['y', 'yes', '是']:
        print("已取消提交")
        return
    
    # 处理失败图片
    submitted_count = process_failed_images(
        failed_paths, 
        args.tasks_dir, 
        start_idx, 
        end_idx, 
        args.batch_size
    )
    
    print(f"\n=== 重新生成任务提交完成 ===")
    print(f"成功提交 {submitted_count} 个重新生成任务")
    print(f"任务文件保存在: {args.tasks_dir} 目录")
    print(f"\n请运行 check_async_tasks.py 来查询任务状态并下载结果")

if __name__ == '__main__':
    main()