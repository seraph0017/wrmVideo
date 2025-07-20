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
from config.config import IMAGE_TWO_CONFIG, STORY_STYLE
from config.prompt_config import ART_STYLES
from volcengine.visual.VisualService import VisualService

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
            
            # 提取3个特写
            scene_info['closeups'] = []
            for i in range(1, 4):  # 图片特写1, 图片特写2, 图片特写3
                closeup_pattern = f'<图片特写{i}>(.*?)</图片特写{i}>'
                closeup_match = re.search(closeup_pattern, scene_content, re.DOTALL)
                if closeup_match:
                    closeup_content = closeup_match.group(1)
                    closeup_info = {}
                    
                    # 提取特写人物角色
                    character_match = re.search(r'<角色>([^<]+)</角色>', closeup_content)
                    if character_match:
                        closeup_info['character'] = character_match.group(1).strip()
                    
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
    查找角色图片文件
    
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

def generate_image_with_character(prompt, output_path, character_images=None, style=None):
    """
    使用角色图片生成图片
    
    Args:
        prompt: 图片描述
        output_path: 输出文件路径
        character_images: 角色图片路径列表
        style: 艺术风格，如果为None则使用配置文件中的默认风格
    
    Returns:
        bool: 是否成功生成
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
        full_prompt = "换个姿势 \n\n" + style_prompt + "\n\n以下面描述为内容，生成一张故事图片\n" + prompt + "\n\n"
        
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
            "negetive_prompt": IMAGE_TWO_CONFIG['negative_prompt'],
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
        if character_images:
            binary_data_list = []
            for img_path in character_images:
                if img_path and os.path.exists(img_path):
                    base64_data = encode_image_to_base64(img_path)
                    if base64_data:
                        binary_data_list.append(base64_data)
                        print(f"添加角色图片: {img_path}")
            
            if binary_data_list:
                form["binary_data_base64"] = binary_data_list
        
        # 调用API
        resp = visual_service.cv_process(form)
        
        # 检查响应
        if 'data' in resp and 'binary_data_base64' in resp['data']:
            # 获取base64图片数据
            base64_data = resp['data']['binary_data_base64'][0]  # 取第一张图片
            
            # 确保输出目录存在
            os.makedirs(os.path.dirname(output_path), exist_ok=True)
            
            # 解码并保存图片
            image_data = base64.b64decode(base64_data)
            with open(output_path, 'wb') as f:
                f.write(image_data)
            
            print(f"图片已保存: {output_path}")
            return True
        else:
            print(f"图片生成失败: {resp}")
            return False
            
    except Exception as e:
        print(f"生成图片时发生错误: {e}")
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
                    
                    # 构建完整的prompt，加入风格提示
                    if style_prompt:
                        full_prompt = f"{prompt}，{style_prompt}"
                    else:
                        full_prompt = prompt
                    
                    # 生成图片
                    image_path = os.path.join(chapter_dir, f"{chapter_name}_image_{i:02d}_{j}.jpeg")
                    
                    if generate_image_with_character(full_prompt, image_path, character_images, drawing_style):
                        print(f"    ✓ 特写 {j} 生成成功")
                        success_count += 1
                    else:
                        print(f"    ✗ 特写 {j} 生成失败")
            
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
    parser.add_argument('data_dir', help='数据目录路径')
    
    args = parser.parse_args()
    
    print(f"目标路径: {args.data_dir}")
    
    success = generate_images_from_scripts(args.data_dir)
    if success:
        print(f"\n✓ 图片生成完成")
    else:
        print(f"\n✗ 图片生成失败")
        sys.exit(1)
    
    print("\n=== 处理完成 ===")

if __name__ == '__main__':
    main()