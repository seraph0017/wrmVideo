#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
根据缺失图片报告生成缺失图片的脚本

读取CSV报告文件，为每个不完整的目录生成缺失的图片编号对应的图片。

作者: AI Assistant
日期: 2024
"""

import os
import re
import csv
import json
import random
import time
import sys
from pathlib import Path

# 添加项目根目录到Python路径
sys.path.append('/Users/xunan/Projects/wrmVideo')

from config.prompt_config import ART_STYLES
from config.config import STORY_STYLE, IMAGE_TWO_CONFIG
from volcengine.visual.VisualService import VisualService

def parse_directory_info(dir_path):
    """
    从目录路径解析年龄、风格、文化、气质信息
    
    Args:
        dir_path: 目录路径，如 Male/15-22_Youth/Ancient/Chinese/Chivalrous
    
    Returns:
        dict: 包含gender, age, style, culture, temperament的字典
    """
    parts = dir_path.split(os.sep)
    
    # 解析性别
    gender = "男" if "Male" in parts else "女" if "Female" in parts else "未知"
    
    # 解析年龄
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
        
        # 风格匹配 (Ancient, Fantasy, Modern, SciFi)
        if part in ["Ancient", "Fantasy", "Modern", "SciFi"]:
            style = part
        
        # 文化匹配 (Chinese, Western)
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
        "temperament": temperament
    }

def generate_character_variation(seed=None):
    """
    生成单个角色变化描述
    
    Args:
        seed: 随机种子，用于生成一致的变化
        
    Returns:
        dict: 包含角色变化信息的字典
    """
    if seed is not None:
        random.seed(seed)
    
    hair_colors = ["黑色", "棕色", "金色", "银色", "白色", "红色"]
    hair_styles = ["短发", "长发", "中长发", "盘发", "辫子", "卷发"]
    expressions = ["微笑", "严肃", "温和", "坚毅", "冷漠", "神秘", "慈祥", "狡猾"]
    clothing_details = ["简约", "华丽", "朴素", "精致", "破旧", "奢华"]
    accessories = ["无饰品", "项链", "耳环", "头饰", "手镯", "戒指"]
    skin_tones = ["白皙", "健康", "古铜色", "偏黄"]
    
    hair_color = random.choice(hair_colors)
    hair_style = random.choice(hair_styles)
    expression = random.choice(expressions)
    clothing = random.choice(clothing_details)
    accessory = random.choice(accessories)
    skin_tone = random.choice(skin_tones)
    
    return {
        "hair_color": hair_color,
        "hair_style": hair_style,
        "expression": expression,
        "clothing": clothing,
        "accessory": accessory,
        "skin_tone": skin_tone
    }

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
                print(f"提交任务: {task_info['filename']}")
                print(f"完整prompt: {full_prompt}")
            else:
                print(f"重试提交任务 (第{attempt}次): {task_info['filename']}")
            
            # 请求参数
            form = {
                "req_key": "high_aes_general_v21_L",
                "prompt": full_prompt,
                "llm_seed": -1,
                "seed": -1,
                "scale": 3.5,
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
    task_file = os.path.join(tasks_dir, f"{task_id}.txt")
    
    # 确保目录存在
    os.makedirs(tasks_dir, exist_ok=True)
    
    # 保存任务信息
    with open(task_file, 'w', encoding='utf-8') as f:
        json.dump(task_info, f, ensure_ascii=False, indent=2)
    
    print(f"任务信息已保存: {task_file}")

def read_missing_images_report(csv_file):
    """
    读取缺失图片报告CSV文件
    
    Args:
        csv_file: CSV文件路径
        
    Returns:
        list: 包含缺失图片信息的列表
    """
    missing_images = []
    
    with open(csv_file, 'r', encoding='utf-8') as f:
        reader = csv.DictReader(f)
        
        for row in reader:
            dir_path = row['目录路径']
            missing_numbers_str = row['缺失编号']
            
            # 解析缺失编号
            missing_numbers = []
            if missing_numbers_str.strip():
                # 分割并清理编号
                numbers = missing_numbers_str.split(',')
                for num in numbers:
                    num = num.strip()
                    if num.isdigit():
                        missing_numbers.append(int(num))
            
            if missing_numbers:
                missing_images.append({
                    'dir_path': dir_path,
                    'missing_numbers': missing_numbers,
                    'current_count': row['现有文件数'],
                    'missing_count': len(missing_numbers)
                })
    
    return missing_images

def generate_missing_images(missing_images, base_dir, tasks_dir):
    """
    为缺失的图片生成异步任务
    
    Args:
        missing_images: 缺失图片信息列表
        base_dir: Character_Images基础目录
        tasks_dir: 任务文件保存目录
        
    Returns:
        int: 成功提交的任务数量
    """
    submitted_count = 0
    total_missing = sum(item['missing_count'] for item in missing_images)
    
    print(f"\n=== 开始生成缺失图片 ===")
    print(f"需要处理 {len(missing_images)} 个目录")
    print(f"总共需要生成 {total_missing} 张图片\n")
    
    for i, item in enumerate(missing_images, 1):
        dir_path = item['dir_path']
        missing_numbers = item['missing_numbers']
        
        print(f"\n--- 处理目录 ({i}/{len(missing_images)}): {dir_path} ---")
        print(f"缺失编号: {missing_numbers}")
        
        # 构建完整目录路径
        full_dir_path = os.path.join(base_dir, dir_path)
        
        if not os.path.exists(full_dir_path):
            print(f"  ❌ 目录不存在: {full_dir_path}")
            continue
        
        # 解析目录信息
        dir_info = parse_directory_info(dir_path)
        print(f"  解析信息: {dir_info}")
        
        # 为每个缺失的编号生成图片
        for missing_num in missing_numbers:
            print(f"\n  生成编号 {missing_num:02d} 的图片...")
            
            # 生成角色变化（使用编号作为种子确保一致性）
            variation = generate_character_variation(seed=missing_num * 100 + hash(dir_path) % 1000)
            
            # 构建prompt
            gender_desc = "男性" if dir_info["gender"] == "男" else "女性"
            view_angle = "背部视角，看不到领口和正面" if dir_info["gender"] == "女" else "正面视角，清晰面部特征"
            
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
            
            # 配饰描述
            accessory_desc = "" if variation['accessory'] == "无饰品" else f"，佩戴{variation['accessory']}"
            
            # 根据文化背景调整服装和风格描述
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
            
            prompt = f"""图片风格为「动漫」，宫崎骏，{culture_desc}
比例 「9:16」
服装要求：必须圆领袍，高领设计，严禁V领或低领，绝对不能露出脖子部位，领口要完全遮盖脖子
年龄：{dir_info['age']}
风格：{dir_info['style']}
文化：{dir_info['culture']}
气质：{temperament_desc}
角度：正面半身照

单人肖像，{gender_desc}，{variation['skin_tone']}肌肤，{variation['hair_color']}{variation['hair_style']}，表情{variation['expression']}，{clothing_style}，{variation['clothing']}风格{accessory_desc}，高质量角色设定图，{view_angle}，动漫风格"""
            
            # 生成文件名
            filename = f"{dir_info['age']}_{dir_info['style']}_{dir_info['culture']}_{dir_info['temperament']}_{missing_num:02d}.jpeg"
            output_path = os.path.join(full_dir_path, filename)
            
            # 准备任务信息
            task_info = {
                "prompt": prompt,
                "output_path": output_path,
                "filename": filename,
                "directory": full_dir_path,
                "dir_info": dir_info,
                "variation": variation,
                "variation_index": missing_num,
                "missing_number": missing_num,
                "status": "submitted",
                "source": "missing_images_report"
            }
            
            # 提交任务
            task_id = submit_image_task(prompt, task_info)
            if task_id:
                task_info["task_id"] = task_id
                save_task_info(task_id, task_info, tasks_dir)
                submitted_count += 1
                print(f"    ✓ 成功提交编号 {missing_num:02d} 的任务")
            else:
                print(f"    ✗ 编号 {missing_num:02d} 的任务提交失败")
            
            # 添加请求间隔，避免API频率限制
            time.sleep(1)
    
    return submitted_count

def main():
    """
    主函数
    """
    # 默认参数
    csv_file = "/Users/xunan/Projects/wrmVideo/test/missing_images_report_20250813_204300.csv"
    base_dir = "/Users/xunan/Projects/wrmVideo/Character_Images"
    tasks_dir = "/Users/xunan/Projects/wrmVideo/async_tasks"
    
    # 检查CSV文件是否存在
    if not os.path.exists(csv_file):
        print(f"❌ 错误: CSV报告文件不存在 {csv_file}")
        return
    
    # 检查基础目录是否存在
    if not os.path.exists(base_dir):
        print(f"❌ 错误: Character_Images目录不存在 {base_dir}")
        return
    
    print(f"=== 根据缺失图片报告生成图片 ===")
    print(f"CSV报告文件: {csv_file}")
    print(f"Character_Images目录: {base_dir}")
    print(f"任务文件保存目录: {tasks_dir}\n")
    
    # 读取缺失图片报告
    print("读取缺失图片报告...")
    missing_images = read_missing_images_report(csv_file)
    
    if not missing_images:
        print("✅ 没有发现缺失的图片，所有目录都已完整！")
        return
    
    print(f"发现 {len(missing_images)} 个不完整的目录")
    total_missing = sum(item['missing_count'] for item in missing_images)
    print(f"总共需要生成 {total_missing} 张图片")
    
    # 显示前5个需要处理的目录
    print("\n前5个需要处理的目录:")
    for i, item in enumerate(missing_images[:5], 1):
        missing_str = ', '.join([f"{num:02d}" for num in item['missing_numbers']])
        print(f"  {i}. {item['dir_path']} (缺少: {missing_str})")
    
    if len(missing_images) > 5:
        print(f"  ... 还有 {len(missing_images) - 5} 个目录")
    
    # 询问用户是否继续
    print(f"\n预计提交 {total_missing} 个异步任务")
    user_input = input("是否继续提交所有异步任务？(y/n): ").strip().lower()
    if user_input not in ['y', 'yes', '是']:
        print("已取消提交")
        return
    
    # 生成缺失图片
    submitted_count = generate_missing_images(missing_images, base_dir, tasks_dir)
    
    print(f"\n=== 任务提交完成 ===")
    print(f"总共成功提交 {submitted_count}/{total_missing} 个异步任务")
    print(f"任务文件保存在: {tasks_dir} 目录")
    print(f"\n请运行以下命令查询任务状态并下载结果:")
    print(f"python check_async_tasks.py")

if __name__ == '__main__':
    main()