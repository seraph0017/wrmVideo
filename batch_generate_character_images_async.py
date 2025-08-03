#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
批量生成角色图片脚本 - 异步版本
遍历Character_Images目录，为每个子目录异步提交生成任务，保存taskid到txt文件
"""

import os
import re
import json
import random
import time
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

def generate_character_variations():
    """
    生成8种不同的角色变化描述
    
    Returns:
        list: 包含8种不同描述的列表
    """
    hair_colors = ["黑色", "棕色", "金色", "银色", "白色", "红色"]
    hair_styles = ["短发", "长发", "中长发", "盘发", "辫子", "卷发"]
    expressions = ["微笑", "严肃", "温和", "坚毅", "冷漠", "神秘", "慈祥", "狡猾"]
    clothing_details = ["简约", "华丽", "朴素", "精致", "破旧", "奢华"]
    accessories = ["无饰品", "项链", "耳环", "头饰", "手镯", "戒指"]
    skin_tones = ["白皙", "健康", "古铜色", "偏黄"]
    
    variations = []
    
    # 生成8种组合
    for i in range(8):
        hair_color = random.choice(hair_colors)
        hair_style = random.choice(hair_styles)
        expression = random.choice(expressions)
        clothing = random.choice(clothing_details)
        accessory = random.choice(accessories)
        skin_tone = random.choice(skin_tones)
        
        variation = {
            "hair_color": hair_color,
            "hair_style": hair_style,
            "expression": expression,
            "clothing": clothing,
            "accessory": accessory,
            "skin_tone": skin_tone
        }
        variations.append(variation)
    
    return variations

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
            full_prompt = "以下内容为描述生成图片\n宫崎骏动漫风格，数字插画,高饱和度,卡通,简约画风,完整色块,整洁的画面,宫崎骏艺术风格,高饱和的色彩和柔和的阴影,童话色彩风格。 人物着装：圆领袍，高领设计，严禁V领，绝对不能露出脖子\n\n" + prompt + "\n\n"
            
            if attempt == 0:
                print(f"提交任务: {task_info['filename']}")
                print(f"完整prompt: {full_prompt}")
            else:
                print(f"重试提交任务 (第{attempt}次): {task_info['filename']}")
            
            # 请求参数
            form = {
                "req_key": IMAGE_TWO_CONFIG['req_key'],
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
    task_file = os.path.join(tasks_dir, f"{task_id}.txt")
    
    # 确保目录存在
    os.makedirs(tasks_dir, exist_ok=True)
    
    # 保存任务信息
    with open(task_file, 'w', encoding='utf-8') as f:
        json.dump(task_info, f, ensure_ascii=False, indent=2)
    
    print(f"任务信息已保存: {task_file}")

def check_existing_images(directory):
    """
    检查目录中已存在的图片数量
    
    Args:
        directory: 目录路径
    
    Returns:
        int: 图片数量
    """
    if not os.path.exists(directory):
        return 0
    
    image_files = [f for f in os.listdir(directory) 
                   if f.lower().endswith(('.jpeg', '.jpg', '.png'))]
    return len(image_files)

def process_directory(base_dir, gender_dir, tasks_dir, filter_age=None, filter_style=None, filter_temperament=None):
    """
    处理单个性别目录下的所有子目录，提交异步任务
    
    Args:
        base_dir: 基础目录路径
        gender_dir: 性别目录名 (Male/Female)
        tasks_dir: 任务文件保存目录
        filter_age: 筛选年龄段 (可选)
        filter_style: 筛选风格 (可选)
        filter_temperament: 筛选气质 (可选)
    
    Returns:
        int: 成功提交的任务数量
    """
    gender_path = os.path.join(base_dir, gender_dir)
    submitted_count = 0
    processed_count = 0
    
    print(f"\n=== 处理 {gender_dir} 目录 ===")
    
    # 遍历所有子目录
    for root, dirs, files in os.walk(gender_path):
        # 跳过根目录
        if root == gender_path:
            continue
        
        # 只处理最深层的目录（包含具体气质的目录）
        if not dirs:  # 没有子目录，说明是最深层
            relative_path = os.path.relpath(root, base_dir)
            
            # 解析目录信息
            dir_info = parse_directory_info(relative_path)
            
            # 应用筛选条件
            if filter_age and dir_info['age'] != filter_age:
                continue
            if filter_style and dir_info['style'] != filter_style:
                continue
            if filter_temperament and dir_info['temperament'] != filter_temperament:
                continue
            
            processed_count += 1
            print(f"\n--- 处理目录 ({processed_count}): {relative_path} ---")
            print(f"解析信息: {dir_info}")
            
            # 检查已存在的图片数量
            existing_count = check_existing_images(root)
            if existing_count >= 4:
                print(f"  发现 {existing_count} 张已存在的图片（>=4），跳过生成")
                continue
            
            # 生成8种变化
            variations = generate_character_variations()
            
            for i, variation in enumerate(variations, 1):
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
                filename = f"{dir_info['age']}_{dir_info['style']}_{dir_info['culture']}_{dir_info['temperament']}_{i:02d}.jpeg"
                output_path = os.path.join(root, filename)
                
                # 准备任务信息
                task_info = {
                    "prompt": prompt,
                    "output_path": output_path,
                    "filename": filename,
                    "directory": root,
                    "dir_info": dir_info,
                    "variation": variation,
                    "variation_index": i,
                    "status": "submitted"
                }
                
                # 提交任务
                task_id = submit_image_task(prompt, task_info)
                if task_id:
                    task_info["task_id"] = task_id
                    save_task_info(task_id, task_info, tasks_dir)
                    submitted_count += 1
                    print(f"  ✓ 成功提交第 {i}/8 个任务")
                else:
                    print(f"  ✗ 第 {i}/8 个任务提交失败")
                
                # 添加请求间隔，避免API频率限制
                if i < len(variations):  # 不是最后一个任务
                    time.sleep(1)  # 等待1秒
    
    return submitted_count

def count_total_directories(base_dir):
    """
    统计需要处理的目录总数
    
    Args:
        base_dir: 基础目录路径
    
    Returns:
        int: 目录总数
    """
    total_dirs = 0
    for gender in ["Male", "Female"]:
        gender_path = os.path.join(base_dir, gender)
        if os.path.exists(gender_path):
            for root, dirs, files in os.walk(gender_path):
                if root != gender_path and not dirs:  # 最深层目录
                    # 检查是否已有足够图片
                    existing_count = check_existing_images(root)
                    if existing_count < 4:
                        total_dirs += 1
    return total_dirs

def main():
    """
    主函数
    """
    # 检查新旧目录结构
    new_base_dir = "Character_Images_New"
    old_base_dir = "Character_Images"
    
    if os.path.exists(new_base_dir):
        base_dir = new_base_dir
        print("使用新的中式/西式分类目录结构")
    elif os.path.exists(old_base_dir):
        base_dir = old_base_dir
        print("使用旧的目录结构")
    else:
        print(f"错误: 目录不存在 {new_base_dir} 或 {old_base_dir}")
        return
    
    # 任务文件保存目录
    tasks_dir = "async_tasks"
    
    print(f"=== 批量生成角色图片 - 异步版本 ===\n")
    print(f"使用目录: {base_dir}\n")
    print(f"任务文件保存目录: {tasks_dir}\n")
    
    # 统计总目录数
    total_dirs = count_total_directories(base_dir)
    print(f"发现 {total_dirs} 个需要处理的角色类型目录")
    print(f"预计提交 {total_dirs * 8} 个异步任务\n")
    
    # 询问用户是否继续
    user_input = input("是否继续提交所有异步任务？(y/n): ").strip().lower()
    if user_input not in ['y', 'yes', '是']:
        print("已取消提交")
        return
    
    total_submitted = 0
    
    # 处理Male目录
    print("\n开始处理男性角色...")
    male_submitted = process_directory(base_dir, "Male", tasks_dir)
    total_submitted += male_submitted
    
    # 处理Female目录
    print("\n开始处理女性角色...")
    female_submitted = process_directory(base_dir, "Female", tasks_dir)
    total_submitted += female_submitted
    
    print(f"\n=== 任务提交完成 ===")
    print(f"总共成功提交 {total_submitted} 个异步任务")
    print(f"男性角色: {male_submitted} 个任务")
    print(f"女性角色: {female_submitted} 个任务")
    print(f"任务文件保存在: {tasks_dir} 目录")
    print(f"\n请运行 check_async_tasks.py 来查询任务状态并下载结果")

if __name__ == '__main__':
    main()