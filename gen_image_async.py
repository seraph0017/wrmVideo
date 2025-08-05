# !/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
独立的图片生成脚本
遍历章节目录，为每个分镜生成图片
"""

import os
import re
import argparse
import base64
import sys
import json
import time
from config.config import IMAGE_TWO_CONFIG, STORY_STYLE
from config.prompt_config import ART_STYLES
from volcengine.visual.VisualService import VisualService

def parse_character_gender(content, character_name):
    """
    从narration.txt内容中解析指定角色的性别
    
    Args:
        content: narration.txt文件内容
        character_name: 角色名称
    
    Returns:
        str: 角色性别（'男'/'女'/'未知'）
    """
    # 查找角色信息块
    character_pattern = rf'<角色>\s*{re.escape(character_name)}\s*</角色>(.*?)(?=<角色>|$)'
    character_match = re.search(character_pattern, content, re.DOTALL)
    
    if character_match:
        character_content = character_match.group(1)
        # 提取性别信息
        gender_match = re.search(r'<性别>([^<]+)</性别>', character_content)
        if gender_match:
            return gender_match.group(1).strip()
    
    return '未知'

def parse_character_definitions(content):
    """
    解析角色定义，建立角色编号映射
    
    Args:
        content: narration.txt文件内容
    
    Returns:
        dict: 角色编号映射字典，格式为 {"主角1": {"数字编号": "01", "性别": "Male", ...}}
    """
    character_map = {}
    
    # 解析主角定义
    protagonist_pattern = r'<主角(\d+)>(.*?)</主角\d+>'
    protagonist_matches = re.findall(protagonist_pattern, content, re.DOTALL)
    
    for char_num, char_content in protagonist_matches:
        char_key = f"主角{char_num}"
        char_info = {}
        
        # 提取各种属性
        name_match = re.search(r'<姓名>([^<]+)</姓名>', char_content)
        gender_match = re.search(r'<性别>([^<]+)</性别>', char_content)
        age_match = re.search(r'<年龄段>([^<]+)</年龄段>', char_content)
        style_match = re.search(r'<风格>([^<]+)</风格>', char_content)
        culture_match = re.search(r'<文化>([^<]+)</文化>', char_content)
        temperament_match = re.search(r'<气质>([^<]+)</气质>', char_content)
        number_match = re.search(r'<角色编号>([^<]+)</角色编号>', char_content)
        
        if name_match:
            char_info['姓名'] = name_match.group(1).strip()
        if gender_match:
            char_info['性别'] = gender_match.group(1).strip()
        if age_match:
            char_info['年龄段'] = age_match.group(1).strip()
        if style_match:
            char_info['风格'] = style_match.group(1).strip()
        if culture_match:
            char_info['文化'] = culture_match.group(1).strip()
        if temperament_match:
            char_info['气质'] = temperament_match.group(1).strip()
        if number_match:
            char_info['数字编号'] = number_match.group(1).strip()
        
        character_map[char_key] = char_info
    
    # 解析配角定义
    supporting_pattern = r'<配角(\d+)>(.*?)</配角\d+>'
    supporting_matches = re.findall(supporting_pattern, content, re.DOTALL)
    
    for char_num, char_content in supporting_matches:
        char_key = f"配角{char_num}"
        char_info = {}
        
        # 提取各种属性
        name_match = re.search(r'<姓名>([^<]+)</姓名>', char_content)
        gender_match = re.search(r'<性别>([^<]+)</性别>', char_content)
        age_match = re.search(r'<年龄段>([^<]+)</年龄段>', char_content)
        style_match = re.search(r'<风格>([^<]+)</风格>', char_content)
        culture_match = re.search(r'<文化>([^<]+)</文化>', char_content)
        temperament_match = re.search(r'<气质>([^<]+)</气质>', char_content)
        number_match = re.search(r'<角色编号>([^<]+)</角色编号>', char_content)
        
        if name_match:
            char_info['姓名'] = name_match.group(1).strip()
        if gender_match:
            char_info['性别'] = gender_match.group(1).strip()
        if age_match:
            char_info['年龄段'] = age_match.group(1).strip()
        if style_match:
            char_info['风格'] = style_match.group(1).strip()
        if culture_match:
            char_info['文化'] = culture_match.group(1).strip()
        if temperament_match:
            char_info['气质'] = temperament_match.group(1).strip()
        if number_match:
            char_info['数字编号'] = number_match.group(1).strip()
        
        character_map[char_key] = char_info
    
    return character_map

def parse_narration_file(narration_file_path):
    """
    解析narration.txt文件，提取分镜信息、图片prompt和绘画风格
    
    Args:
        narration_file_path: narration.txt文件路径
    
    Returns:
        tuple: (分镜信息列表, 绘画风格, 角色映射字典)
    """
    scenes = []
    drawing_style = None
    character_map = {}
    
    try:
        if not os.path.exists(narration_file_path):
            print(f"警告: narration.txt文件不存在: {narration_file_path}")
            return scenes, drawing_style, character_map
        
        with open(narration_file_path, 'r', encoding='utf-8') as f:
            content = f.read()
        
        # 解析角色定义
        character_map = parse_character_definitions(content)
        print(f"解析到 {len(character_map)} 个角色定义")
        for char_key, char_info in character_map.items():
            print(f"  {char_key}: {char_info.get('姓名', '未知')} (编号: {char_info.get('数字编号', '未知')})")
        
        # 解析绘画风格
        style_match = re.search(r'<绘画风格>([^<]+)</绘画风格>', content)
        drawing_style = style_match.group(1) if style_match else None
        
        # 提取分镜信息 - 修复正则表达式以匹配所有分镜格式
        scene_pattern = r'<分镜[^>]*>(.*?)</分镜[^>]*>'
        scene_matches = re.findall(scene_pattern, content, re.DOTALL)
        
        for idx, scene_content in enumerate(scene_matches):
            print(f"处理分镜 {idx+1}")
            scene_info = {}
            
            # 提取解说内容
            narration_match = re.search(r'<解说内容>([^<]+)</解说内容>', scene_content, re.DOTALL)
            if narration_match:
                scene_info['narration'] = narration_match.group(1).strip()
            
            # 提取所有特写
            scene_info['closeups'] = []
            # 动态检测特写数量，最多支持10个特写
            for i in range(1, 11):  # 图片特写1到图片特写10
                closeup_pattern = f'<图片特写{i}>(.*?)</图片特写{i}>'
                closeup_match = re.search(closeup_pattern, scene_content, re.DOTALL)
                if closeup_match:
                    closeup_content = closeup_match.group(1)
                    closeup_info = {}
                    
                    # 提取特写人物和角色编号
                    character_match = re.search(r'<特写人物>([^<]+)</特写人物>', closeup_content)
                    character_id_match = re.search(r'<角色编号>([^<]+)</角色编号>', closeup_content)
                    
                    if character_match:
                        character_name = character_match.group(1).strip()
                        closeup_info['character'] = character_name
                        
                        # 根据角色编号查找角色定义
                        if character_name in character_map:
                            char_info = character_map[character_name]
                            closeup_info['gender'] = char_info.get('性别', '')
                            closeup_info['age_group'] = char_info.get('年龄段', '')
                            closeup_info['character_style'] = char_info.get('风格', '')
                            closeup_info['culture'] = char_info.get('文化', 'Chinese')
                            closeup_info['temperament'] = char_info.get('气质', 'Common')
                            closeup_info['character_number'] = char_info.get('数字编号', '')
                    
                    # 提取图片prompt
                    prompt_match = re.search(r'<图片prompt>([^<]+)</图片prompt>', closeup_content, re.DOTALL)
                    if prompt_match:
                        closeup_info['prompt'] = prompt_match.group(1).strip()
                    
                    if 'prompt' in closeup_info:
                        scene_info['closeups'].append(closeup_info)
            
            if scene_info['closeups']:  # 只有当有特写时才添加分镜
                scenes.append(scene_info)
        
        print(f"解析到 {len(scenes)} 个分镜")
        if drawing_style:
            print(f"绘画风格: {drawing_style}")
        
        return scenes, drawing_style, character_map
        
    except Exception as e:
        print(f"解析narration文件时发生错误: {e}")
        return scenes, drawing_style, character_map

def find_character_image(chapter_path, character_name):
    """
    查找角色图片文件（旧版本兼容）
    
    Args:
        chapter_path: 章节目录路径
        character_name: 角色名称
    
    Returns:
        str: 角色图片文件路径，如果未找到返回None
    """
    try:
        chapter_name = os.path.basename(chapter_path)
        # 构造角色图片文件名模式
        pattern = f"{chapter_name}_character_*_{character_name}.jpeg"
        
        # 在章节目录中查找匹配的文件
        for filename in os.listdir(chapter_path):
            if filename.endswith(f"_{character_name}.jpeg") and "character" in filename:
                image_path = os.path.join(chapter_path, filename)
                print(f"找到角色图片: {image_path}")
                return image_path
        
        print(f"未找到角色 {character_name} 的图片文件")
        return None
        
    except Exception as e:
        print(f"查找角色图片时发生错误: {e}")
        return None

def find_character_image_by_attributes(gender, age_group, character_style, culture='Chinese', temperament='Common'):
    """
    根据角色属性查找Character_Images目录中的角色图片
    
    Args:
        gender: 性别 (Male/Female)
        age_group: 年龄段 (15-22_Youth/23-30_YoungAdult/25-40_FantasyAdult/31-45_MiddleAged)
        character_style: 风格 (Ancient/Fantasy/Modern/SciFi)
        culture: 文化类型 (Chinese/Western)，默认Chinese
        temperament: 气质类型 (Common/Royal/Chivalrous等)，默认Common
    
    Returns:
        str: 角色图片文件路径，如果未找到返回None
    """
    # 构建Character_Images目录路径
    script_dir = os.path.dirname(os.path.abspath(__file__))
    character_images_dir = os.path.join(script_dir, 'Character_Images')
    
    # 构建具体的角色目录路径（5层结构）
    character_dir = os.path.join(character_images_dir, gender, age_group, character_style, culture, temperament)
    
    if os.path.exists(character_dir):
        # 查找目录中的图片文件
        for file in os.listdir(character_dir):
            if file.lower().endswith(('.jpg', '.jpeg', '.png', '.webp')):
                print(f"    找到角色图片: {gender}/{age_group}/{character_style}/{culture}/{temperament}/{file}")
                return os.path.join(character_dir, file)
        
        # 如果没有图片文件，检查是否有prompt.txt
        prompt_file = os.path.join(character_dir, 'prompt.txt')
        if os.path.exists(prompt_file):
            print(f"    找到角色描述文件但无图片: {gender}/{age_group}/{character_style}/{culture}/{temperament}/prompt.txt")
            return None
    
    print(f"    警告: 未找到角色目录 {gender}/{age_group}/{character_style}/{culture}/{temperament}")
    return None

def encode_image_to_base64(image_path):
    """
    将图片文件编码为base64
    
    Args:
        image_path: 图片文件路径
    
    Returns:
        str: base64编码的图片数据
    """
    try:
        with open(image_path, 'rb') as f:
            image_data = f.read()
        return base64.b64encode(image_data).decode('utf-8')
    except Exception as e:
        print(f"编码图片为base64时发生错误: {e}")
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

def generate_image_with_character_async(prompt, output_path, character_images=None, style=None, max_retries=3):
    """
    使用角色图片异步生成图片，带重试机制
    
    Args:
        prompt: 图片描述
        output_path: 输出文件路径
        character_images: 角色图片路径列表
        style: 艺术风格，如果为None则使用配置文件中的默认风格
        max_retries: 最大重试次数
    
    Returns:
        bool: 是否成功提交任务
    """
    # 检查图片是否已存在
    if os.path.exists(output_path):
        print(f"✓ 图片已存在，跳过生成: {os.path.basename(output_path)}")
        return True
    
    for attempt in range(max_retries + 1):
        try:
            if attempt > 0:
                print(f"🔄 第 {attempt} 次重试生成图片: {os.path.basename(output_path)}")
                time.sleep(2 * attempt)  # 递增延迟
            
            visual_service = VisualService()
            
            # 设置访问密钥
            visual_service.set_ak(IMAGE_TWO_CONFIG['access_key'])
            visual_service.set_sk(IMAGE_TWO_CONFIG['secret_key'])
            
            # 获取风格设置
            if style is None:
                style = IMAGE_TWO_CONFIG.get('default_style', 'manga')
            
            style_config = ART_STYLES.get(style, ART_STYLES['manga'])
            style_prompt = style_config.get('description', style_config)
            
            print(f"正在生成{style}风格图片: {os.path.basename(output_path)}")
            
            # 构建完整的prompt
            full_prompt = "以以下内容为描述生成图片\n宫崎骏动漫风格，数字插画,高饱和度,卡通,简约画风,完整色块,整洁的画面,宫崎骏艺术风格,高饱和的色彩和柔和的阴影,童话色彩,人物着装：圆领袍 \n\n" + style_prompt + "\n\n" + prompt + "\n\n"
            
            if attempt == 0:  # 只在第一次尝试时打印完整prompt
                print("这里是完整的prompt===>>>{}".format(full_prompt))
            
            # 构建请求参数 - 使用配置文件中的值
            form = {
                "req_key": IMAGE_TWO_CONFIG['req_key'],
                "prompt": full_prompt,
                "llm_seed": -1,
                "seed": 10 + attempt,  # 每次重试使用不同的seed
                "scale": IMAGE_TWO_CONFIG['scale'],
                "ddim_steps": IMAGE_TWO_CONFIG['ddim_steps'],
                "width": IMAGE_TWO_CONFIG['default_width'],
                "height": IMAGE_TWO_CONFIG['default_height'],
                "use_pre_llm": IMAGE_TWO_CONFIG['use_pre_llm'],
                "use_sr": IMAGE_TWO_CONFIG['use_sr'],
                "return_url": IMAGE_TWO_CONFIG['return_url'],  # 返回base64格式
                "negative_prompt": IMAGE_TWO_CONFIG['negative_prompt'],
                "ref_ip_weight": 0,
                "ref_id_weight": 0.4,
                "logo_info": {
                    "add_logo": False,
                    "position": 0,
                    "language": 0,
                    "opacity": 0.3,
                    "logo_text_content": "这里是明水印内容"
                }
            }
            
            # 如果有角色图片，添加到请求中
            print(f"角色图片参数: {character_images}")
            if character_images:
                print(f"开始处理 {len(character_images)} 个角色图片")
                binary_data_list = []
                for img_path in character_images:
                    print(f"处理角色图片: {img_path}")
                    if img_path and os.path.exists(img_path):
                        base64_data = encode_image_to_base64(img_path)
                        if base64_data:
                            binary_data_list.append(base64_data)
                            print(f"成功添加角色图片: {img_path}")
                        else:
                            print(f"角色图片编码失败: {img_path}")
                    else:
                        print(f"角色图片不存在: {img_path}")
                
                if binary_data_list:
                    form["binary_data_base64"] = binary_data_list
                    print(f"已添加 {len(binary_data_list)} 个角色图片到请求中")
                else:
                    print("没有有效的角色图片数据")
            else:
                print("没有角色图片参数")
            
            # 调用异步API提交任务
            if attempt == 0:  # 只在第一次尝试时打印详细信息
                print("这里是响应前===============")
            resp = visual_service.cv_sync2async_submit_task(form)
            if attempt == 0:
                print("这里是响应参数===============")
                print(resp)
                print("这里是响应参数===============")
            
            # 检查响应
            if 'data' in resp and 'task_id' in resp['data']:
                task_id = resp['data']['task_id']
                print(f"✓ 任务提交成功，Task ID: {task_id}")
                
                # 保存任务信息到async_tasks目录
                task_info = {
                    'task_id': task_id,
                    'output_path': output_path,
                    'filename': os.path.basename(output_path),
                    'prompt': prompt,
                    'full_prompt': full_prompt,
                    'character_images': character_images or [],
                    'style': style,
                    'submit_time': time.time(),
                    'status': 'submitted',
                    'attempt': attempt + 1
                }
                
                # 使用统一的保存函数
                async_tasks_dir = 'async_tasks'
                save_task_info(task_id, task_info, async_tasks_dir)
                return True
            else:
                error_msg = resp.get('message', '未知错误')
                print(f"✗ 任务提交失败 (尝试 {attempt + 1}/{max_retries + 1}): {error_msg}")
                
                if attempt == max_retries:
                    print(f"✗ 达到最大重试次数，任务最终失败")
                    return False
                
                # 继续下一次重试
                continue
                
        except Exception as e:
            print(f"✗ 生成图片时发生错误 (尝试 {attempt + 1}/{max_retries + 1}): {e}")
            
            if attempt == max_retries:
                print(f"✗ 达到最大重试次数，任务最终失败")
                return False
            
            # 继续下一次重试
            continue
    
    return False

def generate_image_with_character(prompt, output_path, character_images=None, style=None):
    """
    兼容性函数：调用异步版本
    
    Args:
        prompt: 图片描述
        output_path: 输出文件路径
        character_images: 角色图片路径列表
        style: 艺术风格，如果为None则使用配置文件中的默认风格
    
    Returns:
        bool: 是否成功提交任务
    """
    return generate_image_with_character_async(prompt, output_path, character_images, style)

def generate_images_for_chapter(chapter_dir):
    """
    为单个章节生成图片
    
    Args:
        chapter_dir: 章节目录路径
    
    Returns:
        bool: 是否成功生成图片
    """
    try:
        chapter_name = os.path.basename(chapter_dir)
        print(f"=== 开始为章节 {chapter_name} 生成图片 ===")
        print(f"章节目录: {chapter_dir}")
        
        if not os.path.exists(chapter_dir):
            print(f"错误: 章节目录不存在 {chapter_dir}")
            return False
        
        # 查找narration文件
        narration_file = os.path.join(chapter_dir, "narration.txt")
        if not os.path.exists(narration_file):
            print(f"错误: narration文件不存在 {narration_file}")
            return False
        
        # 解析narration文件
        scenes, drawing_style, character_map = parse_narration_file(narration_file)
        
        if not scenes:
            print(f"错误: 未找到分镜信息")
            return False
        
        print(f"找到 {len(scenes)} 个分镜")
        
        # 获取绘画风格的model_prompt
        style_prompt = ""
        if drawing_style and drawing_style in STORY_STYLE:
            style_config = STORY_STYLE[drawing_style]
            if isinstance(style_config.get('model_prompt'), list):
                style_prompt = style_config['model_prompt'][0]  # 取第一个
            else:
                style_prompt = style_config.get('model_prompt', '')
            print(f"使用风格提示: {style_prompt}")
        
        success_count = 0
        
        # 为每个分镜的每个特写生成图片
        for i, scene in enumerate(scenes, 1):
            closeups = scene['closeups']
            
            print(f"\n  处理第 {i}/{len(scenes)} 个分镜，包含 {len(closeups)} 个特写")
            
            # 为每个特写生成图片
            for j, closeup in enumerate(closeups, 1):
                prompt = closeup['prompt']
                character = closeup.get('character', '')
                gender = closeup.get('gender', '')
                age_group = closeup.get('age_group', '')
                character_style = closeup.get('character_style', '')
                culture = closeup.get('culture', 'Chinese')
                temperament = closeup.get('temperament', 'Common')
                
                print(f"    生成特写 {j}: {chapter_name}_image_{i:02d}_{j}.jpeg")
                print(f"    特写人物: {character} ({gender}/{age_group}/{character_style})")
                
                # 查找当前特写的角色图片（基于Character_Images目录结构）
                character_images = []
                if gender and age_group and character_style:
                    print(f"    查找角色图片: {gender}/{age_group}/{character_style}/{culture}/{temperament}")
                    char_img_path = find_character_image_by_attributes(gender, age_group, character_style, culture, temperament)
                    if char_img_path:
                        character_images.append(char_img_path)
                        print(f"    找到角色图片: {char_img_path}")
                    else:
                        print(f"    未找到角色图片")
                else:
                    print(f"    角色信息不完整，跳过角色图片查找")
                
                # 根据角色性别调整视角
                view_angle_prompt = ""
                if gender:
                    print(f"    角色性别: {gender}")
                    
                    # 根据性别决定视角
                    if gender.lower() in ['female', '女']:
                        view_angle_prompt = "，背部视角，看不到领口和正面"
                    else:
                        view_angle_prompt = "，正面视角，清晰面部特征"
                
                # 构建完整的prompt，加入风格提示和视角要求
                if style_prompt:
                    full_prompt = f"{prompt}{view_angle_prompt}，{style_prompt}"
                else:
                    full_prompt = f"{prompt}{view_angle_prompt}"
                
                # 提交异步任务
                image_path = os.path.join(chapter_dir, f"{chapter_name}_image_{i:02d}_{j}.jpeg")
                
                if generate_image_with_character_async(full_prompt, image_path, character_images, drawing_style):
                    print(f"    ✓ 特写 {j} 任务提交成功")
                    success_count += 1
                else:
                    print(f"    ✗ 特写 {j} 任务提交失败")
        
        # 计算该章节生成的图片总数
        total_images = sum(len(scene['closeups']) for scene in scenes)
        print(f"\n章节 {chapter_name} 处理完成，共 {len(scenes)} 个分镜，成功生成 {success_count}/{total_images} 张图片")
        return success_count > 0
        
    except Exception as e:
        print(f"生成章节图片时发生错误: {e}")
        return False

def generate_images_from_scripts(data_dir):
    """
    遍历数据目录，为每个章节的分镜生成图片
    
    Args:
        data_dir: 数据目录路径
    
    Returns:
        bool: 是否成功生成图片
    """
    try:
        print(f"=== 开始生成图片 ===")
        print(f"数据目录: {data_dir}")
        
        if not os.path.exists(data_dir):
            print(f"错误: 数据目录不存在 {data_dir}")
            return False
        
        # 查找所有章节目录
        chapter_dirs = []
        for item in os.listdir(data_dir):
            item_path = os.path.join(data_dir, item)
            if os.path.isdir(item_path) and item.startswith('chapter_'):
                chapter_dirs.append(item_path)
        
        if not chapter_dirs:
            print(f"错误: 在 {data_dir} 中没有找到章节目录")
            return False
        
        chapter_dirs.sort()
        print(f"找到 {len(chapter_dirs)} 个章节目录")
        
        success_count = 0
        
        # 处理每个章节
        for chapter_dir in chapter_dirs:
            chapter_name = os.path.basename(chapter_dir)
            print(f"\n--- 处理章节: {chapter_name} ---")
            
            # 查找narration文件
            narration_file = os.path.join(chapter_dir, "narration.txt")
            if not os.path.exists(narration_file):
                print(f"警告: narration文件不存在 {narration_file}")
                continue
            
            # 解析narration文件
            scenes, drawing_style, character_map = parse_narration_file(narration_file)
            
            if not scenes:
                print(f"警告: 未找到分镜信息")
                continue
            
            print(f"找到 {len(scenes)} 个分镜")
            
            # 获取绘画风格的model_prompt
            style_prompt = ""
            if drawing_style and drawing_style in STORY_STYLE:
                style_config = STORY_STYLE[drawing_style]
                if isinstance(style_config.get('model_prompt'), list):
                    style_prompt = style_config['model_prompt'][0]  # 取第一个
                else:
                    style_prompt = style_config.get('model_prompt', '')
                print(f"使用风格提示: {style_prompt}")
            
            # 为每个分镜的每个特写生成图片
            for i, scene in enumerate(scenes, 1):
                closeups = scene['closeups']
                
                print(f"\n  处理第 {i}/{len(scenes)} 个分镜，包含 {len(closeups)} 个特写")
                
                # 为每个特写生成图片
                for j, closeup in enumerate(closeups, 1):
                    prompt = closeup['prompt']
                    character = closeup.get('character', '')
                    gender = closeup.get('gender', '')
                    age_group = closeup.get('age_group', '')
                    character_style = closeup.get('character_style', '')
                    culture = closeup.get('culture', 'Chinese')
                    temperament = closeup.get('temperament', 'Common')
                    
                    print(f"    生成特写 {j}: {chapter_name}_image_{i:02d}_{j}.jpeg")
                    print(f"    特写人物: {character} ({gender}/{age_group}/{character_style})")
                    
                    # 查找当前特写的角色图片（基于Character_Images目录结构）
                    character_images = []
                    if gender and age_group and character_style:
                        print(f"    查找角色图片: {gender}/{age_group}/{character_style}/{culture}/{temperament}")
                        char_img_path = find_character_image_by_attributes(gender, age_group, character_style, culture, temperament)
                        if char_img_path:
                            character_images.append(char_img_path)
                            print(f"    找到角色图片: {char_img_path}")
                        else:
                            print(f"    未找到角色图片")
                    else:
                        print(f"    角色信息不完整，跳过角色图片查找")
                    
                    # 根据角色性别调整视角
                    view_angle_prompt = ""
                    if gender:
                        print(f"    角色性别: {gender}")
                        
                        # 根据性别决定视角
                        if gender.lower() in ['female', '女']:
                            view_angle_prompt = "，背部视角，看不到领口和正面"
                        else:
                            view_angle_prompt = "，正面视角，清晰面部特征"
                    
                    # 构建完整的prompt，加入风格提示和视角要求
                    if style_prompt:
                        full_prompt = f"{prompt}{view_angle_prompt}，{style_prompt}"
                    else:
                        full_prompt = f"{prompt}{view_angle_prompt}"
                    
                    # 提交异步任务
                    image_path = os.path.join(chapter_dir, f"{chapter_name}_image_{i:02d}_{j}.jpeg")
                    
                    if generate_image_with_character_async(full_prompt, image_path, character_images, drawing_style):
                        print(f"    ✓ 特写 {j} 任务提交成功")
                        success_count += 1
                    else:
                        print(f"    ✗ 特写 {j} 任务提交失败")
            
            # 计算该章节生成的图片总数
            chapter_image_count = sum(len(scene['closeups']) for scene in scenes)
            print(f"章节 {chapter_name} 处理完成，共 {len(scenes)} 个分镜，成功生成 {chapter_image_count} 张图片")
        
        print(f"\n图片生成完成，成功生成 {success_count} 张图片")
        return success_count > 0
        
    except Exception as e:
        print(f"生成图片时发生错误: {e}")
        return False

def count_total_closeups(data_dir):
    """
    统计所有章节的图片特写总数
    
    Args:
        data_dir: 数据目录路径
    
    Returns:
        tuple: (总特写数量, 章节统计详情)
    """
    total_closeups = 0
    chapter_stats = {}
    
    try:
        if not os.path.exists(data_dir):
            return 0, {}
        
        # 查找所有章节目录
        chapter_dirs = []
        for item in os.listdir(data_dir):
            item_path = os.path.join(data_dir, item)
            if os.path.isdir(item_path) and item.startswith('chapter_'):
                chapter_dirs.append(item_path)
        
        chapter_dirs.sort()
        
        for chapter_dir in chapter_dirs:
            chapter_name = os.path.basename(chapter_dir)
            narration_file = os.path.join(chapter_dir, "narration.txt")
            
            if os.path.exists(narration_file):
                scenes, _, _ = parse_narration_file(narration_file)
                chapter_closeups = sum(len(scene['closeups']) for scene in scenes)
                chapter_stats[chapter_name] = chapter_closeups
                total_closeups += chapter_closeups
        
        return total_closeups, chapter_stats
        
    except Exception as e:
        print(f"统计图片特写数量时发生错误: {e}")
        return 0, {}

def check_and_retry_failed_tasks(async_tasks_dir='async_tasks', max_retries=3):
    """
    检查async_tasks目录中的失败任务并重试
    
    Args:
        async_tasks_dir: 异步任务目录
        max_retries: 最大重试次数
    
    Returns:
        tuple: (重试成功数量, 重试失败数量)
    """
    if not os.path.exists(async_tasks_dir):
        return 0, 0
    
    retry_success = 0
    retry_failed = 0
    
    print(f"\n=== 检查并重试失败任务 ===")
    
    # 获取所有任务文件
    task_files = [f for f in os.listdir(async_tasks_dir) if f.endswith('.txt')]
    
    for task_file in task_files:
        task_path = os.path.join(async_tasks_dir, task_file)
        
        try:
            with open(task_path, 'r', encoding='utf-8') as f:
                task_info = json.load(f)
            
            # 检查任务状态
            status = task_info.get('status', 'unknown')
            task_id = task_info.get('task_id')
            
            # 如果任务没有task_id或状态为失败，需要重试
            if not task_id or status in ['failed', 'error']:
                print(f"发现需要重试的任务: {task_info.get('filename', 'unknown')}")
                
                # 重新提交任务
                output_path = task_info.get('output_path')
                prompt = task_info.get('prompt')
                character_images = task_info.get('character_images', [])
                style = task_info.get('style')
                
                if output_path and prompt:
                    # 删除旧的任务文件
                    os.remove(task_path)
                    
                    # 重新提交任务
                    if generate_image_with_character_async(prompt, output_path, character_images, style, max_retries):
                        print(f"✓ 重试成功: {os.path.basename(output_path)}")
                        retry_success += 1
                    else:
                        print(f"✗ 重试失败: {os.path.basename(output_path)}")
                        retry_failed += 1
                else:
                    print(f"✗ 任务信息不完整，跳过重试")
                    retry_failed += 1
        
        except Exception as e:
            print(f"处理任务文件时发生错误 {task_file}: {e}")
            retry_failed += 1
    
    print(f"重试完成: 成功 {retry_success} 个，失败 {retry_failed} 个")
    return retry_success, retry_failed

def main():
    parser = argparse.ArgumentParser(description='独立的图片生成脚本')
    parser.add_argument('input_path', help='输入路径（可以是单个章节目录或包含多个章节的数据目录）')
    parser.add_argument('--retry-failed', action='store_true', help='检查并重试失败的任务')
    
    args = parser.parse_args()
    
    print(f"目标路径: {args.input_path}")
    
    # 如果是重试模式，只处理失败任务
    if args.retry_failed:
        print("\n=== 重试失败任务模式 ===")
        retry_success, retry_failed = check_and_retry_failed_tasks()
        if retry_success > 0 or retry_failed == 0:
            print(f"\n✓ 重试完成")
        else:
            print(f"\n✗ 重试失败")
            sys.exit(1)
        return
    
    # 检查输入路径是单个章节还是数据目录
    if os.path.isdir(args.input_path):
        # 检查是否是单个章节目录
        if os.path.basename(args.input_path).startswith('chapter_') and os.path.exists(os.path.join(args.input_path, 'narration.txt')):
            print("检测到单个章节目录")
            # 统计单个章节的特写数量
            narration_file = os.path.join(args.input_path, 'narration.txt')
            scenes, _, _ = parse_narration_file(narration_file)
            total_closeups = sum(len(scene['closeups']) for scene in scenes)
            print(f"该章节共有 {total_closeups} 个图片特写")
            
            success = generate_images_for_chapter(args.input_path)
        else:
            print("检测到数据目录，将处理所有章节")
            # 统计所有章节的特写数量
            total_closeups, chapter_stats = count_total_closeups(args.input_path)
            print(f"\n=== 图片特写统计 ===")
            print(f"总特写数量: {total_closeups}")
            for chapter, count in chapter_stats.items():
                print(f"  {chapter}: {count} 个特写")
            
            success = generate_images_from_scripts(args.input_path)
            
            # 生成完成后，检查并重试失败任务
            print(f"\n=== 第一轮生成完成，开始检查失败任务 ===")
            retry_success, retry_failed = check_and_retry_failed_tasks()
            
            if retry_failed > 0:
                print(f"\n仍有 {retry_failed} 个任务失败，请稍后使用 --retry-failed 参数重试")
    else:
        print(f"错误: 路径不存在 {args.input_path}")
        sys.exit(1)
    
    if success:
        print(f"\n✓ 图片生成完成")
    else:
        print(f"\n✗ 图片生成失败")
        sys.exit(1)
    
    print("\n=== 处理完成 ===")

if __name__ == '__main__':
    main()