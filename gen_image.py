# !/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
独立的图片生成脚本
从generate.py中提取的图像生成逻辑
"""

import os
import re
import argparse
import base64
import requests
from volcenginesdkarkruntime import Ark
import sys
from config.config import IMAGE_TWO_CONFIG, ART_STYLES, STORY_STYLE

from volcengine.visual.VisualService import VisualService

def parse_character_details(narration_file_path):
    """
    从narration.txt文件中解析主要人物的详细信息
    
    Args:
        narration_file_path: narration.txt文件路径
    
    Returns:
        dict: 人物名称到详细描述的映射
    """
    character_details = {}
    
    try:
        if not os.path.exists(narration_file_path):
            print(f"警告: narration.txt文件不存在: {narration_file_path}")
            return character_details
        
        with open(narration_file_path, 'r', encoding='utf-8') as f:
            content = f.read()
        
        # 提取主要人物部分
        main_characters_match = re.search(r'<主要人物>(.*?)</主要人物>', content, re.DOTALL)
        character_matches = []
        
        if main_characters_match:
            main_characters_content = main_characters_match.group(1)
            # 解析主要人物
            main_character_matches = re.findall(r'<人物\d+>(.*?)</人物\d+>', main_characters_content, re.DOTALL)
            character_matches.extend(main_character_matches)
        
        # 提取次要人物部分
        minor_characters_match = re.search(r'<次要人物>(.*?)</次要人物>', content, re.DOTALL)
        if minor_characters_match:
            minor_characters_content = minor_characters_match.group(1)
            # 解析次要人物
            minor_character_matches = re.findall(r'<次要人物\d+>(.*?)</次要人物\d+>', minor_characters_content, re.DOTALL)
            character_matches.extend(minor_character_matches)
        
        if not character_matches:
            print("警告: 未找到任何人物信息")
            return character_details
        
        for character_content in character_matches:
            # 提取姓名
            name_match = re.search(r'<姓名>&([^&]+)&</姓名>', character_content)
            if not name_match:
                continue
            
            character_name = name_match.group(1)
            
            # 提取各项详细信息
            details = []
            
            # 身高体型
            height_match = re.search(r'<身高体型>([^<]+)</身高体型>', character_content)
            if height_match:
                details.append(height_match.group(1))
            
            # 头发细节
            hair_color_match = re.search(r'<发色>([^<]+)</发色>', character_content)
            hair_style_match = re.search(r'<发型>([^<]+)</发型>', character_content)
            if hair_color_match and hair_style_match:
                details.append(f"{hair_color_match.group(1)}{hair_style_match.group(1)}")
            
            # 眼睛细节
            eye_color_match = re.search(r'<眼睛颜色>([^<]+)</眼睛颜色>', character_content)
            eye_type_match = re.search(r'<眼型>([^<]+)</眼型>', character_content)
            eye_trait_match = re.search(r'<眼神特点>([^<]+)</眼神特点>', character_content)
            if eye_color_match and eye_type_match:
                eye_desc = f"{eye_color_match.group(1)}{eye_type_match.group(1)}"
                if eye_trait_match:
                    eye_desc += f"眼神{eye_trait_match.group(1)}"
                details.append(eye_desc)
            
            # 脸型轮廓
            face_match = re.search(r'<脸型>([^<]+)</脸型>', character_content)
            chin_match = re.search(r'<下巴形状>([^<]+)</下巴形状>', character_content)
            if face_match and chin_match:
                details.append(f"{face_match.group(1)}{chin_match.group(1)}")
            
            # 肤色
            skin_match = re.search(r'<肤色>([^<]+)</肤色>', character_content)
            if skin_match:
                details.append(f"{skin_match.group(1)}肤色")
            
            # 服装细节
            clothing_color_match = re.search(r'<服装细节>.*?<颜色>([^<]+)</颜色>.*?<款式>([^<]+)</款式>', character_content, re.DOTALL)
            if clothing_color_match:
                details.append(f"{clothing_color_match.group(1)}{clothing_color_match.group(2)}")
            
            # 配饰细节
            glasses_match = re.search(r'<眼镜>([^<]+)</眼镜>', character_content)
            if glasses_match and glasses_match.group(1) != '无':
                details.append(glasses_match.group(1))
            
            jewelry_match = re.search(r'<首饰>([^<]+)</首饰>', character_content)
            if jewelry_match and jewelry_match.group(1) != '无':
                details.append(jewelry_match.group(1))
            
            # 组合所有描述
            character_details[character_name] = '，'.join(details)
            print(f"解析到人物: {character_name} -> {character_details[character_name]}")
        
        return character_details
        
    except Exception as e:
        print(f"解析人物详情时发生错误: {e}")
        return character_details

def enhance_prompt_with_character_details(prompt, chapter_path):
    """
    根据人物标记增强prompt描述
    
    Args:
        prompt: 原始prompt
        chapter_path: 章节目录路径
    
    Returns:
        str: 增强后的prompt
    """
    try:
        # 查找narration.txt文件
        narration_file = os.path.join(chapter_path, 'narration.txt')
        
        # 解析人物详情
        character_details = parse_character_details(narration_file)
        
        if not character_details:
            return prompt
        
        # 查找prompt中的人名标记
        enhanced_prompt = prompt
        
        for character_name, details in character_details.items():
            # 查找&人名&模式
            pattern = f'&{character_name}&'
            if pattern in enhanced_prompt:
                # 替换为详细描述
                replacement = f'{character_name}（{details}）'
                enhanced_prompt = enhanced_prompt.replace(pattern, replacement)
                print(f"增强描述: {pattern} -> {replacement}")
        
        return enhanced_prompt
        
    except Exception as e:
        print(f"增强prompt时发生错误: {e}")
        return prompt

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
        
        style_prompt = ART_STYLES.get(style, ART_STYLES['manga'])
        
        print(f"正在生成{style}风格图片: {os.path.basename(output_path)}")
        
        # 如果提供了章节路径，则增强人物描述
        enhanced_prompt = prompt
        if chapter_path:
            enhanced_prompt = enhance_prompt_with_character_details(prompt, chapter_path)
        
        # 构建完整的prompt
        full_prompt = "无任何形式的文字, 字母, 数字, 符号, 水印, 签名  （包括标识、符号、背景纹理里的隐藏字）\n\n" + style_prompt + "\n\n以下面描述为内容，生成一张故事图片\n" + enhanced_prompt + "\n\n"
        
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

def generate_images_from_scripts(data_dir):
    # 复制 generate.py 中的完整 generate_images_from_scripts 函数内容
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
            
            # 读取narration内容
            with open(narration_file, 'r', encoding='utf-8') as f:
                narration_content = f.read().strip()
            
            if not narration_content:
                print(f"警告: narration内容为空")
                continue
            
            # 提取风格信息
            story_style = "玄幻修真"  # 默认风格
            style_pattern = r'<风格>\s*([^<]+)\s*</风格>'
            style_match = re.search(style_pattern, narration_content)
            if style_match:
                story_style = style_match.group(1).strip()
                print(f"检测到故事风格: {story_style}")
            
            # 获取风格配置
            style_config = STORY_STYLE.get(story_style, STORY_STYLE["玄幻修真"])
            model_prompt = style_config.get("model_prompt", "")
            core_style = style_config.get("core_style", "")
            
            # 如果model_prompt是列表，取第一个
            if isinstance(model_prompt, list):
                model_prompt = model_prompt[0]
            
            print(f"使用风格配置: {core_style}")
            print(f"模型提示词: {model_prompt}")
            
            # 提取人物信息
            characters = {}
            character_pattern = r'<主要人物>\s*([\s\S]*?)(?=<|$)'
            character_match = re.search(character_pattern, narration_content)
            if character_match:
                character_text = character_match.group(1)
                # 解析每个人物的信息
                char_blocks = re.split(r'\n(?=\S)', character_text.strip())
                for block in char_blocks:
                    if block.strip():
                        lines = block.strip().split('\n')
                        if lines:
                            name = lines[0].strip().rstrip('：:')
                            details = []
                            for line in lines[1:]:
                                line = line.strip()
                                if line and not line.startswith('-'):
                                    details.append(line)
                            if details:
                                characters[name] = '，'.join(details)
            
            # 提取图片prompts
            prompt_pattern = r'<图片prompt>\s*([\s\S]*?)(?=<|$)'
            prompts = re.findall(prompt_pattern, narration_content)
            
            if not prompts:
                print(f"警告: 未找到图片prompt")
                continue
            
            print(f"找到 {len(prompts)} 个图片prompt")
            
            # 为每个prompt生成图片
            for i, prompt in enumerate(prompts, 1):
                prompt = prompt.strip()
                if not prompt:
                    continue
                
                # 增强prompt：添加风格信息
                enhanced_prompt = f"{model_prompt}，{core_style}，{prompt}"
                
                # 如果包含人名，添加人物细节
                for char_name in characters:
                    if char_name in prompt:
                        char_details = characters[char_name]
                        enhanced_prompt = enhanced_prompt.replace(char_name, f"{char_name}（{char_details}）")
                
                print(f"  生成第 {i}/{len(prompts)} 张图片: {chapter_name}_image_{i:02d}.jpeg")
                print(f"  风格增强prompt: {enhanced_prompt[:150]}...")
                
                # 生成图片
                image_path = os.path.join(chapter_dir, f"{chapter_name}_image_{i:02d}.jpeg")
                
                if generate_image(enhanced_prompt, image_path, chapter_path=chapter_dir):
                    print(f"  ✓ 图片生成成功")
                    success_count += 1
                else:
                    print(f"  ✗ 图片生成失败")
            
            print(f"章节 {chapter_name} 处理完成，成功生成 {len([p for p in prompts if p.strip()])} 张图片")
        
        print(f"\n图片生成完成，成功生成 {success_count} 张图片")
        return success_count > 0
        
    except Exception as e:
        print(f"生成图片时发生错误: {e}")
        return False

def main():
    parser = argparse.ArgumentParser(description='独立的图片生成脚本')
    parser.add_argument('path', help='数据目录路径')
    
    args = parser.parse_args()
    
    print(f"目标路径: {args.path}")
    
    success = generate_images_from_scripts(args.path)
    if success:
        print(f"\n✓ 图片生成完成")
    else:
        print(f"\n✗ 图片生成失败")
        sys.exit(1)
    
    print("\n=== 处理完成 ===")

if __name__ == '__main__':
    main()