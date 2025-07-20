#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
角色图片生成脚本
根据narration.txt中的角色信息生成角色图片
"""

import os
import re
import argparse
import sys
import base64
from config.prompt_config import ART_STYLES
from config.config import STORY_STYLE, IMAGE_TWO_CONFIG
from volcengine.visual.VisualService import VisualService

def parse_character_info(narration_file_path):
    """
    从narration.txt文件中解析角色信息和绘画风格
    
    Args:
        narration_file_path: narration.txt文件路径
    
    Returns:
        tuple: (角色信息列表, 绘画风格)
    """
    characters = []
    
    try:
        if not os.path.exists(narration_file_path):
            print(f"错误: narration.txt文件不存在: {narration_file_path}")
            return characters, None
        
        with open(narration_file_path, 'r', encoding='utf-8') as f:
            content = f.read()
        
        # 解析绘画风格
        style_match = re.search(r'<绘画风格>([^<]+)</绘画风格>', content)
        drawing_style = style_match.group(1) if style_match else None
        
        # 查找本章出镜人物部分
        character_section_match = re.search(r'<本章出镜人物>(.*?)</本章出镜人物>', content, re.DOTALL)
        if not character_section_match:
            print("警告: 未找到本章出镜人物信息")
            return characters, drawing_style
        
        character_section = character_section_match.group(1)
        
        # 解析每个角色
        character_matches = re.findall(r'<角色\d+>(.*?)</角色\d+>', character_section, re.DOTALL)
        
        for i, character_content in enumerate(character_matches, 1):
            character_info = {}
            
            # 提取角色名
            name_match = re.search(r'<角色名>([^<]+)</角色名>', character_content)
            if name_match:
                character_info['name'] = name_match.group(1)
            else:
                character_info['name'] = f'角色{i}'
            
            # 提取各项信息
            fields = ['性别', '年龄', '发型', '发色', '面部细节', '面部表情', '衣着款式', '衣着颜色', '其他特点']
            details = []
            
            for field in fields:
                field_match = re.search(f'<{field}>([^<]+)</{field}>', character_content)
                if field_match:
                    value = field_match.group(1)
                    if value and value != '未提及':
                        if field == '性别':
                            details.append(value)
                        elif field == '年龄':
                            details.append(f'{value}人')
                        elif field == '发型' or field == '发色':
                            details.append(value)
                        elif field == '面部细节':
                            details.append(value)
                        elif field == '面部表情':
                            details.append(f'表情{value}')
                        elif field == '衣着款式':
                            details.append(value)
                        elif field == '衣着颜色':
                            details.append(f'{value}色')
                        elif field == '其他特点':
                            details.append(value)
            
            character_info['description'] = '，'.join(details)
            characters.append(character_info)
            
            print(f"解析到角色: {character_info['name']} -> {character_info['description']}")
        
        return characters, drawing_style
        
    except Exception as e:
        print(f"解析角色信息时发生错误: {e}")
        return characters, None

def generate_image(prompt, output_path, style=None, chapter_path=None):
    """
    生成图片文件
    
    Args:
        prompt: 图片描述
        output_path: 输出文件路径
        style: 艺术风格，如果为None则使用配置文件中的默认风格
        chapter_path: 章节路径，用于获取人物描述信息
    
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
        full_prompt = "无任何形式的文字, 字母, 数字, 符号, 水印, 签名  （包括标识、符号、背景纹理里的隐藏字）\n\n" + style_prompt + "\n\n以下面描述为内容，生成一张故事图片\n" + prompt + "\n\n"
        
        print("这里是完整的prompt===>>>{}".format(full_prompt))
        # 请求参数 - 使用配置文件中的值
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
            "return_url": IMAGE_TWO_CONFIG['return_url'],  # 返回base64格式
            "negetive_prompt": IMAGE_TWO_CONFIG['negative_prompt'],
            "logo_info": {
                "add_logo": False,
                "position": 0,
                "language": 0,
                "opacity": 0.3,
                "logo_text_content": "这里是明水印内容"
            }
        }
        
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

def generate_character_images(input_path):
    """
    为指定路径生成角色图片
    支持单个章节目录或包含多个章节的数据目录
    
    Args:
        input_path: 输入路径（可以是单个章节目录或数据目录）
    
    Returns:
        bool: 是否成功生成
    """
    try:
        print(f"=== 开始生成角色图片 ===")
        print(f"输入路径: {input_path}")
        
        if not os.path.exists(input_path):
            print(f"错误: 路径不存在 {input_path}")
            return False
        
        # 检测输入路径类型
        chapter_dirs = []
        
        # 检查是否是单个章节目录
        if os.path.basename(input_path).startswith('chapter_') and os.path.isfile(os.path.join(input_path, 'narration.txt')):
            # 单个章节目录
            chapter_dirs = [input_path]
            print(f"检测到单个章节目录: {os.path.basename(input_path)}")
        else:
            # 数据目录，查找所有章节目录
            for item in os.listdir(input_path):
                item_path = os.path.join(input_path, item)
                if os.path.isdir(item_path) and item.startswith('chapter_'):
                    chapter_dirs.append(item_path)
            
            if chapter_dirs:
                chapter_dirs.sort()
                print(f"检测到数据目录，找到 {len(chapter_dirs)} 个章节目录")
        
        if not chapter_dirs:
            print(f"错误: 在 {input_path} 中没有找到有效的章节目录")
            return False
        
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
            
            # 解析角色信息和绘画风格
            characters, drawing_style = parse_character_info(narration_file)
            
            if not characters:
                print(f"警告: 未找到角色信息")
                continue
            
            print(f"找到 {len(characters)} 个角色")
            if drawing_style:
                print(f"绘画风格: {drawing_style}")
            
            # 获取绘画风格的model_prompt
            style_prompt = ""
            if drawing_style and drawing_style in STORY_STYLE:
                style_config = STORY_STYLE[drawing_style]
                if isinstance(style_config.get('model_prompt'), list):
                    style_prompt = style_config['model_prompt'][0]  # 取第一个
                else:
                    style_prompt = style_config.get('model_prompt', '')
                print(f"使用风格提示: {style_prompt}")
            
            # 为每个角色生成图片
            for i, character in enumerate(characters, 1):
                character_name = character['name']
                character_desc = character['description']
                
                # 构建角色图片的prompt，加入风格提示
                if style_prompt:
                    character_prompt = f"单人肖像，{character_desc}，高质量角色设定图，正面视角，清晰面部特征，{style_prompt}"
                else:
                    character_prompt = f"单人肖像，{character_desc}，高质量角色设定图，正面视角，清晰面部特征，动漫风格"
                
                print(f"  生成第 {i}/{len(characters)} 个角色图片: {character_name}")
                print(f"  角色描述: {character_desc}")
                print(f"  完整提示词: {character_prompt}")
                
                # 生成图片
                image_path = os.path.join(chapter_dir, f"{chapter_name}_character_{i:02d}_{character_name}.jpeg")
                
                if generate_image(character_prompt, image_path, chapter_path=chapter_dir):
                    print(f"  ✓ 角色图片生成成功: {character_name}")
                    success_count += 1
                else:
                    print(f"  ✗ 角色图片生成失败: {character_name}")
            
            print(f"章节 {chapter_name} 处理完成，成功生成 {len(characters)} 张角色图片")
        
        print(f"\n角色图片生成完成，成功生成 {success_count} 张图片")
        return success_count > 0
        
    except Exception as e:
        print(f"生成角色图片时发生错误: {e}")
        return False

def main():
    parser = argparse.ArgumentParser(description='角色图片生成脚本')
    parser.add_argument('path', help='输入路径（可以是单个章节目录或包含多个章节的数据目录）')
    
    args = parser.parse_args()
    
    print(f"目标路径: {args.path}")
    
    success = generate_character_images(args.path)
    if success:
        print(f"\n✓ 角色图片生成完成")
    else:
        print(f"\n✗ 角色图片生成失败")
        sys.exit(1)
    
    print("\n=== 处理完成 ===")

if __name__ == '__main__':
    main()