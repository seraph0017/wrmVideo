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

def parse_narration_file(narration_file_path):
    """
    解析narration.txt文件，提取分镜信息、图片prompt和绘画风格
    
    Args:
        narration_file_path: narration.txt文件路径
    
    Returns:
        tuple: (分镜信息列表, 绘画风格)
    """
    scenes = []
    drawing_style = None
    
    try:
        if not os.path.exists(narration_file_path):
            print(f"警告: narration.txt文件不存在: {narration_file_path}")
            return scenes, drawing_style
        
        with open(narration_file_path, 'r', encoding='utf-8') as f:
            content = f.read()
        
        # 解析绘画风格
        style_match = re.search(r'<绘画风格>([^<]+)</绘画风格>', content)
        drawing_style = style_match.group(1) if style_match else None
        
        # 提取分镜信息
        scene_pattern = r'<分镜\d+>(.*?)</分镜\d+>'
        scene_matches = re.findall(scene_pattern, content, re.DOTALL)
        
        for scene_content in scene_matches:
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
                    
                    # 提取特写人物信息
                    gender_match = re.search(r'<性别>([^<]+)</性别>', closeup_content)
                    age_match = re.search(r'<年龄段>([^<]+)</年龄段>', closeup_content)
                    style_match = re.search(r'<风格>([^<]+)</风格>', closeup_content)
                    
                    if gender_match and age_match and style_match:
                        closeup_info['gender'] = gender_match.group(1).strip().replace('根据章节内容选择：', '')
                        closeup_info['age_group'] = age_match.group(1).strip().replace('根据章节内容选择：', '')
                        closeup_info['character_style'] = style_match.group(1).strip().replace('根据章节内容选择：', '')
                    
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
        
        return scenes, drawing_style
        
    except Exception as e:
        print(f"解析narration文件时发生错误: {e}")
        return scenes, drawing_style

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

def generate_image_with_character_async(prompt, output_path, character_images=None, style=None):
    """
    使用角色图片异步生成图片
    
    Args:
        prompt: 图片描述
        output_path: 输出文件路径
        character_images: 角色图片路径列表
        style: 艺术风格，如果为None则使用配置文件中的默认风格
    
    Returns:
        bool: 是否成功提交任务
    """
    try:
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
        
        print("这里是完整的prompt===>>>{}".format(full_prompt))
        
        # 构建请求参数 - 使用配置文件中的值
        form = {
            "req_key": IMAGE_TWO_CONFIG['req_key'],
            "prompt": full_prompt,
            "llm_seed": -1,
            "seed": 10,
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
        print("这里是响应前===============")
        resp = visual_service.cv_sync2async_submit_task(form)
        # resp = visual_service.cv_submit_task(form)
        print("这里是响应参数===============")
        print(resp)
        print("这里是响应参数===============")
        
        # 检查响应
        if 'data' in resp and 'task_id' in resp['data']:
            task_id = resp['data']['task_id']
            print(f"任务提交成功，Task ID: {task_id}")
            
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
                'status': 'submitted'
            }
            
            # 使用统一的保存函数
            async_tasks_dir = 'async_tasks'
            save_task_info(task_id, task_info, async_tasks_dir)
            return True
        else:
            print(f"任务提交失败: {resp}")
            return False
            
    except Exception as e:
        print(f"生成图片时发生错误: {e}")
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
        scenes, drawing_style = parse_narration_file(narration_file)
        
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
                gender = closeup.get('gender', '')
                age_group = closeup.get('age_group', '')
                character_style = closeup.get('character_style', '')
                
                print(f"    生成特写 {j}: {chapter_name}_image_{i:02d}_{j}.jpeg")
                print(f"    特写人物: {gender}/{age_group}/{character_style}")
                
                # 查找当前特写的角色图片（基于Character_Images目录结构）
                character_images = []
                if gender and age_group and character_style:
                    print(f"    查找角色图片: {gender}/{age_group}/{character_style}")
                    char_img_path = find_character_image_by_attributes(gender, age_group, character_style)
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
            scenes, drawing_style = parse_narration_file(narration_file)
            
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
                    
                    print(f"    生成特写 {j}: {chapter_name}_image_{i:02d}_{j}.jpeg")
                    print(f"    特写角色: {character}")
                    
                    # 查找当前特写的角色图片
                    character_images = []
                    if character:
                        char_img_path = find_character_image(chapter_dir, character)
                        if char_img_path:
                            character_images.append(char_img_path)
                    
                    # 根据角色性别调整视角
                    view_angle_prompt = ""
                    if character:
                        # 重新读取narration文件内容来解析性别
                        with open(narration_file, 'r', encoding='utf-8') as f:
                            narration_content = f.read()
                        
                        character_gender = parse_character_gender(narration_content, character)
                        print(f"    角色性别: {character_gender}")
                        
                        # 根据性别决定视角
                        if character_gender == '女':
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

def main():
    parser = argparse.ArgumentParser(description='独立的图片生成脚本')
    parser.add_argument('input_path', help='输入路径（可以是单个章节目录或包含多个章节的数据目录）')
    
    args = parser.parse_args()
    
    print(f"目标路径: {args.input_path}")
    
    # 检查输入路径是单个章节还是数据目录
    if os.path.isdir(args.input_path):
        # 检查是否是单个章节目录
        if os.path.basename(args.input_path).startswith('chapter_') and os.path.exists(os.path.join(args.input_path, 'narration.txt')):
            print("检测到单个章节目录")
            success = generate_images_for_chapter(args.input_path)
        else:
            print("检测到数据目录，将处理所有章节")
            success = generate_images_from_scripts(args.input_path)
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