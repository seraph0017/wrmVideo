#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
LLM旁白图片分析工具

该脚本专门用于检测chapter文件夹中的旁白图片（chapter_xxx_image_xx.jpeg格式），
检查衽领、V领、交领、y字型领以及三只手等问题，并支持自动重新生成。

功能特性:
- 专门检测chapter_xxx_image_xx.jpeg格式的旁白图片
- 支持批量处理目录下所有旁白图片或单独处理指定图片文件
- 领口审查：检测衽领、V领、交领、y字型领等会露出脖子以下皮肤的领口类型
- 手部检测：检测是否存在三只手或多余手臂的情况
- 内容审查：检测图片中的乱码或文字内容
- 自动重新生成：检测到失败图片时自动调用图片生成模块重新生成
- 自定义重新生成提示词：支持用户自定义图片修改要求（如"去掉眼镜"、"换成短发"等）
- 支持常见图片格式(jpg, jpeg, png, gif, bmp, webp)
- 使用base64编码处理图片
- 详细的进度反馈和错误处理
- 自动记录失败的图片到fail.txt文件（批量模式）

使用方法:
    # 批量检查data/004目录下所有chapter中的旁白图片
    python llm_narration_image.py data/004
    
    # 自定义分析提示词
    python llm_narration_image.py data/004 --prompt "自定义检查提示词"
    
    # 限制处理数量
    python llm_narration_image.py data/004 --max-images 10
    
    # 启用自动重新生成失败图片
    python llm_narration_image.py data/004 --auto-regenerate
    
    # 单独处理指定图片文件
    python llm_narration_image.py data/006/chapter_003/chapter_003_image_08.jpeg --auto-regenerate
    
    # 单独处理图片并使用自定义重新生成提示词
    python llm_narration_image.py data/006/chapter_003/chapter_003_image_08.jpeg --auto-regenerate --custom-prompt "去掉眼镜"

配置要求:
    需要在 config/config.py 中配置 ARK_CONFIG['api_key']
"""

import os
import argparse
import base64
import sys
import re
from pathlib import Path
from typing import List, Optional
from volcenginesdkarkruntime import Ark

# 导入配置
from config.config import ARK_CONFIG

# 导入图片生成功能
try:
    from gen_image_async import generate_image_with_character_async, get_random_character_image, save_task_info, encode_image_to_base64 as gen_encode_image_to_base64
    from volcengine.visual.VisualService import VisualService
    from config.config import IMAGE_TWO_CONFIG
    # ART_STYLES 配置已移除
    import time
    import json
except ImportError:
    print("警告: 无法导入图片生成模块，重新生成功能将不可用")
    generate_image_with_character_async = None
    get_random_character_image = None
    save_task_info = None
    gen_encode_image_to_base64 = None
    VisualService = None
    IMAGE_TWO_CONFIG = None
    ART_STYLES = None

# 支持的图片格式
SUPPORTED_FORMATS = {'.jpg', '.jpeg', '.png', '.gif', '.bmp', '.webp'}

# 旁白图片文件名模式：chapter_xxx_image_xx.jpeg
NARRATION_IMAGE_PATTERN = re.compile(r'^chapter_\d+_image_\d+\.jpeg$', re.IGNORECASE)

def resize_image_if_needed(image_path: str, max_size_mb: float = 4.7) -> str:
    """
    处理图片：转换为JPG格式，如果大小超过限制则压缩
    
    Args:
        image_path: 图片文件路径
        max_size_mb: 最大文件大小（MB）
        
    Returns:
        str: 处理后的图片路径（临时文件路径）
    """
    try:
        from PIL import Image
        import tempfile
        
        # 检查文件大小
        file_size_mb = os.path.getsize(image_path) / (1024 * 1024)
        
        # 检查是否已经是JPG格式
        file_extension = Path(image_path).suffix.lower()
        is_jpg = file_extension in ['.jpg', '.jpeg']
        
        # 如果是JPG格式且大小符合要求，直接返回原路径
        if is_jpg and file_size_mb <= max_size_mb:
            return image_path
        
        # 需要处理的情况：非JPG格式或大小超限
        if not is_jpg:
            print(f"转换图片格式为JPG: {os.path.basename(image_path)}")
        if file_size_mb > max_size_mb:
            print(f"图片大小 {file_size_mb:.2f}MB 超过限制 {max_size_mb}MB，正在压缩...")
        
        # 打开图片
        with Image.open(image_path) as img:
            # 转换为RGB模式（如果是RGBA或其他模式）
            if img.mode in ('RGBA', 'LA', 'P'):
                # 创建白色背景
                background = Image.new('RGB', img.size, (255, 255, 255))
                if img.mode == 'P':
                    img = img.convert('RGBA')
                background.paste(img, mask=img.split()[-1] if img.mode == 'RGBA' else None)
                img = background
            elif img.mode != 'RGB':
                img = img.convert('RGB')
            
            # 创建临时文件
            temp_fd, temp_path = tempfile.mkstemp(suffix='.jpg')
            os.close(temp_fd)
            
            # 如果文件大小符合要求，直接转换格式
            if file_size_mb <= max_size_mb:
                img.save(temp_path, 'JPEG', quality=95, optimize=True)
                temp_size_mb = os.path.getsize(temp_path) / (1024 * 1024)
                print(f"格式转换完成: {file_size_mb:.2f}MB -> {temp_size_mb:.2f}MB (JPG)")
                return temp_path
            
            # 需要压缩的情况
            # 计算压缩比例
            target_ratio = max_size_mb / file_size_mb
            scale_factor = min(0.9, target_ratio ** 0.5)  # 保守的缩放因子
            
            # 计算新尺寸
            new_width = int(img.width * scale_factor)
            new_height = int(img.height * scale_factor)
            
            # 调整图片尺寸
            img_resized = img.resize((new_width, new_height), Image.Resampling.LANCZOS)
            
            # 保存压缩后的图片，调整质量
            quality = 85
            while quality > 20:
                img_resized.save(temp_path, 'JPEG', quality=quality, optimize=True)
                
                # 检查文件大小
                temp_size_mb = os.path.getsize(temp_path) / (1024 * 1024)
                if temp_size_mb <= max_size_mb:
                    print(f"压缩完成: {file_size_mb:.2f}MB -> {temp_size_mb:.2f}MB (质量: {quality})")
                    return temp_path
                
                quality -= 10
            
            # 如果还是太大，进一步缩小尺寸
            scale_factor *= 0.8
            new_width = int(img.width * scale_factor)
            new_height = int(img.height * scale_factor)
            img_resized = img.resize((new_width, new_height), Image.Resampling.LANCZOS)
            img_resized.save(temp_path, 'JPEG', quality=70, optimize=True)
            
            temp_size_mb = os.path.getsize(temp_path) / (1024 * 1024)
            print(f"强制压缩完成: {file_size_mb:.2f}MB -> {temp_size_mb:.2f}MB")
            return temp_path
            
    except ImportError:
        print("警告: PIL库未安装，无法处理图片")
        return image_path
    except Exception as e:
        print(f"处理图片失败: {e}")
        return image_path

def encode_image_to_base64(image_path: str) -> Optional[str]:
    """
    将图片文件编码为base64格式，会先转换为JPG格式并在必要时进行压缩
    
    Args:
        image_path: 图片文件路径
        
    Returns:
        base64编码的图片数据，格式为 data:image/<format>;base64,<data>
        如果编码失败返回None
    """
    temp_path = None
    try:
        # 处理图片：转换为JPG格式，如果过大则压缩
        processed_path = resize_image_if_needed(image_path)
        temp_path = processed_path if processed_path != image_path else None
        
        with open(processed_path, 'rb') as image_file:
            # 读取图片二进制数据
            image_data = image_file.read()
            # 编码为base64
            base64_data = base64.b64encode(image_data).decode('utf-8')
            
            # 获取图片格式 - 根据实际文件内容而不是扩展名
            import imghdr
            detected_format = imghdr.what(processed_path)
            if detected_format:
                # 使用检测到的实际格式
                image_format = detected_format
            else:
                # 如果检测失败，回退到扩展名判断
                file_extension = Path(processed_path).suffix.lower()
                if file_extension == '.jpg':
                    image_format = 'jpeg'
                else:
                    image_format = file_extension[1:]  # 去掉点号
            
            # 构造完整的data URL
            return f"data:image/{image_format};base64,{base64_data}"
            
    except Exception as e:
        print(f"编码图片失败 {image_path}: {e}")
        return None
    finally:
        # 清理临时文件
        if temp_path and os.path.exists(temp_path):
            try:
                os.unlink(temp_path)
            except:
                pass

def find_narration_images_in_chapters(data_directory: str) -> List[str]:
    """
    查找指定数据目录下所有chapter文件夹中的旁白图片（chapter_xxx_image_xx.jpeg格式）
    如果输入的是chapter目录，则直接在该目录下查找图片文件
    
    Args:
        data_directory: 数据目录路径 (如: data/004) 或 chapter目录路径 (如: data/004/chapter_001)
        
    Returns:
        旁白图片文件路径列表
    """
    narration_images = []
    data_path = Path(data_directory)
    
    if not data_path.exists():
        print(f"目录不存在: {data_directory}")
        return narration_images
    
    # 检查输入路径是否是chapter目录
    if data_path.name.startswith('chapter'):
        print(f"检测到chapter目录，直接在目录下查找图片: {data_directory}")
        chapter_dirs = [data_path]
    else:
        # 查找所有chapter文件夹
        chapter_dirs = [d for d in data_path.iterdir() if d.is_dir() and d.name.startswith('chapter')]
        
        if not chapter_dirs:
            print(f"在 {data_directory} 中未找到任何chapter文件夹")
            return narration_images
        
        print(f"找到 {len(chapter_dirs)} 个chapter文件夹")
    
    # 遍历每个chapter文件夹
    for chapter_dir in sorted(chapter_dirs):
        print(f"正在扫描: {chapter_dir}")
        
        # 直接在chapter目录下查找图片文件（不使用rglob递归查找）
        for file_path in chapter_dir.iterdir():
            if file_path.is_file() and file_path.suffix.lower() in SUPPORTED_FORMATS:
                # 检查是否为旁白图片（匹配chapter_xxx_image_xx.jpeg格式）
                if NARRATION_IMAGE_PATTERN.match(file_path.name):
                    narration_images.append(str(file_path))
                    print(f"  找到旁白图片: {file_path.name}")
    
    print(f"总共找到 {len(narration_images)} 张旁白图片")
    return sorted(narration_images)

def analyze_image_with_llm(client: Ark, image_base64: str, prompt: str = "\
    请仔细观察这张旁白图片，进行以下全面审查：\n\n【领口审查标准】\n✅ 通过的领口类型：圆领、立领、高领、方领、一字领等完全遮盖脖子和胸部的领口\n❌ 失败的领口类型：\n\
        - 交领/衽领：左右衣襟交叉重叠，形成V字形开口，露出脖子和胸部皮肤\n- V领：任何形式的V字形领口\n- y字型领：形成Y字形状的领口\n- 低领：领口过低，露出脖子以下皮肤\n\
            - 开胸装：胸前有明显开口或缝隙\n\n【皮肤暴露检查 - 严格标准】\n检查角色是否存在以下问题（任何一项都视为失败）：\n- 脖子暴露：脖子部位不能有任何皮肤暴露，必须完全被服装遮盖\n\
                - 后背脖子以下皮肤暴露：后背脖子以下区域不能有皮肤暴露\n- 胸部皮肤暴露：胸前不能有皮肤暴露\n\n【身体部位异常检查 - 严格标准】\
                    \n检查角色是否存在以下身体部位异常（任何一项都视为失败）：\n- 多手：角色有超过2只手臂或手\n- 多脚：角色有超过2只脚或腿\n- 多手指：单只手有超过5根手指\n- \
                    手指异常：手指形状扭曲、融合或数量明显错误\n- 肢体畸形：手臂、腿部或其他肢体出现明显的解剖学错误\n- 身体比例异常：头部、四肢比例严重失调\n\n【\
                        禁止头部和身体不协调\
                        亲密行为检查 - 严格标准】\n检查图片中是否存在以下亲密行为（任何一项都视为失败）：\n- 拥抱：两人或多人相互拥抱的姿势\n- 勾肩搭背：手臂搭在他人肩膀或背部的亲密姿势\n- 亲密接触：任何形式的身体亲密接触或暧昧姿势\n- 过度亲近：角色之间距离过近，呈现亲密关系的画面\n\n【内容审查】\n检查图片中是否存在文字、乱码、水印等不当内容\n\n【判断要求】\n请重点关注：\n1. 领口是否露出脖子以下的皮肤区域\n2. 脖子是否有任何暴露（即使是很小的暴露也不允许）\n3. 后背脖子以下是否有皮肤暴露\n4. 仔细检查角色的手、脚、手指数量是否正常\n5. 观察身体各部位的解剖学正确性\n6. 如果角色穿着交领袍服、汉服等传统服装，要特别注意交领处是否形成开口露出胸部\n7. 检查是否存在拥抱、勾肩搭背等亲密行为\n\n如果发现任何问题，请返回'失败'并详细说明原因。如果完全符合要求，请返回'通过'。") -> tuple[Optional[str], dict]:
    """
    使用LLM分析图片内容
    
    Args:
        client: Ark客户端实例
        image_base64: base64编码的图片数据
        prompt: 分析提示词
        
    Returns:
        tuple: (LLM分析结果, token使用情况字典)
        token使用情况字典包含: prompt_tokens, completion_tokens, total_tokens
    """
    token_usage = {"prompt_tokens": 0, "completion_tokens": 0, "total_tokens": 0}
    
    try:
        resp = client.chat.completions.create(
            model="doubao-seed-1-6-flash-250715",
            messages=[
                {
                    "content": [
                        {
                            "image_url": {"url": image_base64},
                            "type": "image_url"
                        },
                        {
                            "text": prompt,
                            "type": "text"
                        }
                    ],
                    "role": "user"
                }
            ],
        )
        
        # 获取 token 使用情况
        if hasattr(resp, 'usage') and resp.usage:
            token_usage = {
                "prompt_tokens": resp.usage.prompt_tokens,
                "completion_tokens": resp.usage.completion_tokens,
                "total_tokens": resp.usage.total_tokens
            }
            print(f"Token使用情况: 输入={resp.usage.prompt_tokens}, 输出={resp.usage.completion_tokens}, 总计={resp.usage.total_tokens}")
        
        return resp.choices[0].message.content, token_usage
    except Exception as e:
        print(f"LLM分析失败: {e}")
        return None, token_usage

def generate_image_with_character_to_chapter_async(prompt: str, output_path: str, character_images=None, style=None, max_retries=3) -> bool:
    """
    使用角色图片异步生成图片，将任务保存到对应chapter的async_tasks目录
    基于gen_image_async.py中的实现方法
    
    Args:
        prompt: 图片描述
        output_path: 输出文件路径
        character_images: 角色图片路径列表
        style: 艺术风格，如果为None则使用配置文件中的默认风格
        max_retries: 最大重试次数
        
    Returns:
        bool: 是否成功提交任务
    """
    if not all([VisualService, IMAGE_TWO_CONFIG, save_task_info, gen_encode_image_to_base64]):
        print("错误: 图片生成模块不可用")
        return False
    
    # 检查图片是否已存在
    if os.path.exists(output_path):
        print(f"✓ 图片已存在，跳过生成: {os.path.basename(output_path)}")
    
    # 确定chapter目录和async_tasks目录
    output_dir = os.path.dirname(output_path)
    # 查找包含chapter的路径部分
    path_parts = Path(output_path).parts
    chapter_dir = None
    for i, part in enumerate(path_parts):
        if part.startswith('chapter_'):
            chapter_dir = os.path.join(*path_parts[:i+1])
            break
    
    if not chapter_dir:
        print(f"错误: 无法确定chapter目录，路径: {output_path}")
        return False
    
    # 创建chapter下的async_tasks目录
    chapter_async_tasks_dir = os.path.join(chapter_dir, 'async_tasks')
    os.makedirs(chapter_async_tasks_dir, exist_ok=True)
    
    try:
        # 初始化视觉服务
        visual_service = VisualService()
        
        # 设置访问密钥
        visual_service.set_ak(IMAGE_TWO_CONFIG['access_key'])
        visual_service.set_sk(IMAGE_TWO_CONFIG['secret_key'])
        
        # 使用固定的艺术风格提示词
        style_prompt = '动漫插画，精美细腻的画风，鲜艳的色彩，清晰的线条'
        
        for attempt in range(max_retries + 1):
            # 构建完整提示词，特别强调领口、皮肤暴露和手部要求
            full_prompt = "女性衣服不能漏膝盖以上,去掉衽领，交领，V领，y字型领，换成高领圆领袍\n\
                领口不能是V领，领口不能是衽领，领口不能是交领，领口不能是任何y字型或者v字型的领子\n\
                    脖子必须完全被服装遮盖不能有任何暴露，后背脖子以下不能有皮肤暴露，胸部不能有皮肤暴露\n\
                        角色只能有两只手，不能有三只手或更多手臂,手指数量要正常,不能有多余的手指\n\
                        把眼镜都去掉，身体和头部的比例和正反也要修正\n\
                            角色之间不能有拥抱、挽手、亲密接触等行为，角色之间要保持适当距离,也不能对视\n\n" + style_prompt + "\n\n" + prompt + "\n\n"
            
            if attempt == 0:  # 只在第一次尝试时打印完整prompt
                print("完整的prompt: {}".format(full_prompt))
            
            # 构建请求参数
            form = {
                "req_key": "byteedit_v2.0",
                "prompt": full_prompt,
                "seed": 10 + attempt,  # 每次重试使用不同的seed
                "scale": 0.4,
                "return_url": IMAGE_TWO_CONFIG['return_url'],
                "negative_prompt": IMAGE_TWO_CONFIG['negative_prompt'] + ", three hands, multiple hands, extra hands, extra arms, deformed hands",
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
                print(f"开始处理 {len(character_images)} 个角色图片")
                binary_data_list = []
                for img_path in character_images:
                    if img_path and os.path.exists(img_path):
                        base64_data = gen_encode_image_to_base64(img_path)
                        if base64_data:
                            # 从data URL中提取纯base64数据（去掉"data:image/xxx;base64,"前缀）
                            if base64_data.startswith('data:'):
                                pure_base64 = base64_data.split(',')[1]
                            else:
                                pure_base64 = base64_data
                            binary_data_list.append(pure_base64)
                            print(f"成功添加角色图片: {img_path}")
                        else:
                            print(f"角色图片编码失败: {img_path}")
                    else:
                        print(f"角色图片不存在: {img_path}")
                
                if binary_data_list:
                    form["binary_data_base64"] = binary_data_list
                    print(f"总共添加了 {len(binary_data_list)} 个角色图片")
                else:
                    print("警告: 没有有效的角色图片")
            
            # 调用异步API提交任务
            print("提交异步任务...")
            resp = visual_service.cv_sync2async_submit_task(form)
            
            # 检查响应
            if 'data' in resp and 'task_id' in resp['data']:
                task_id = resp['data']['task_id']
                print(f"✓ 任务提交成功，Task ID: {task_id}")
                
                # 保存任务信息到chapter的async_tasks目录
                task_info = {
                    'task_id': task_id,
                    'output_path': output_path,
                    'filename': os.path.basename(output_path),
                    'prompt': prompt,
                    'full_prompt': full_prompt,
                    'character_images': character_images or [],
                    'submit_time': time.time(),
                    'status': 'submitted',
                    'attempt': attempt + 1
                }
                
                # 保存到chapter的async_tasks目录
                save_task_info(task_id, task_info, chapter_async_tasks_dir)
                print(f"任务信息已保存到: {chapter_async_tasks_dir}")
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
        print(f"✗ 生成图片时发生错误: {e}")
        return False
    
    return False

def regenerate_failed_image(image_path: str) -> bool:
    """
    重新生成失败的旁白图片
    将异步任务保存到对应chapter的async_tasks目录
    使用原始失败图片作为参考进行改进
    
    Args:
        image_path: 失败图片的路径
        
    Returns:
        bool: 是否成功重新生成
    """
    if not all([VisualService, IMAGE_TWO_CONFIG, save_task_info]):
        print("错误: 图片生成模块不可用")
        return False
    
    try:
        # 检查原始图片是否存在
        if not os.path.exists(image_path):
            print(f"错误: 原始图片不存在: {image_path}")
            return False
        
        # 构建生成提示词，强调领口、皮肤暴露和手部要求
        regenerate_prompt = "基于原图进行改进，\
            领口必须是立领或高领，绝对不能是V领、交领、衽领、y字型领或其他露出脖子以下皮肤的领型，\
                脖子必须完全被服装遮盖不能有任何暴露，后背脖子以下不能有皮肤暴露，\
                    胸部不能有皮肤暴露，角色只能有两只手，不能有三只手或更多手臂，画面清晰，细节丰富，手指数量要正常,不能有多余的手指\
                        角色之间不能有拥抱、挽手、亲密接触等行为，角色之间要保持适当距离，也不能对视"
        
        print(f"正在重新生成图片: {image_path}")
        print(f"生成提示词: {regenerate_prompt}")
        print("注意: 使用原始失败图片作为参考进行改进")
        
        # 先压缩原始图片，然后使用压缩后的版本作为参考
        compressed_image_path = resize_image_if_needed(image_path)
        
        # 调用新的异步生成函数，将任务保存到对应chapter的async_tasks目录
        # 使用压缩后的图片作为参考
        character_images_to_use = [compressed_image_path] if compressed_image_path != image_path else [image_path]
        
        success = generate_image_with_character_to_chapter_async(
            prompt=regenerate_prompt,
            output_path=image_path,  # 直接替换原图片
            character_images=character_images_to_use,  # 使用压缩后的图片作为参考
            style='manga',  # 使用manga风格
            max_retries=3
        )
        
        # 清理临时压缩文件
        if compressed_image_path != image_path and os.path.exists(compressed_image_path):
            try:
                os.unlink(compressed_image_path)
                print(f"已清理临时压缩文件: {compressed_image_path}")
            except:
                pass
        
        if success:
            print(f"✓ 重新生成任务已提交: {os.path.basename(image_path)}")
            print(f"任务已保存到对应chapter的async_tasks目录")
            print(f"请稍后使用 check_async_tasks.py 检查生成结果")
            return True
        else:
            print(f"✗ 重新生成任务提交失败: {os.path.basename(image_path)}")
            return False
            
    except Exception as e:
        print(f"重新生成图片时发生错误: {str(e)}")
        return False

def process_single_image(image_path: str, prompt: str, auto_regenerate: bool = False, custom_prompt: Optional[str] = None, skip_analysis: bool = False):
    """
    处理单个图片文件的分析和重新生成
    
    Args:
        image_path: 图片文件路径
        prompt: 分析提示词
        auto_regenerate: 是否自动重新生成失败的图片
        custom_prompt: 自定义重新生成提示词
        skip_analysis: 是否跳过分析直接重新生成
    """
    # 检查文件是否存在
    if not os.path.exists(image_path):
        print(f"错误: 图片文件不存在: {image_path}")
        return
    
    # 检查是否为支持的图片格式
    file_extension = Path(image_path).suffix.lower()
    if file_extension not in SUPPORTED_FORMATS:
        print(f"错误: 不支持的图片格式: {file_extension}")
        print(f"支持的格式: {', '.join(SUPPORTED_FORMATS)}")
        return
    
    # 检查是否为旁白图片格式
    filename = os.path.basename(image_path)
    if not NARRATION_IMAGE_PATTERN.match(filename):
        print(f"警告: 图片文件名不符合旁白图片格式 (chapter_xxx_image_xx.jpeg): {filename}")
        print("将继续处理，但建议使用标准命名格式")
    
    # 从配置文件获取API密钥
    api_key = ARK_CONFIG.get("api_key")
    if not api_key:
        print("错误: 请在 config/config.py 中配置 ARK_CONFIG['api_key']")
        return
    
    # 初始化客户端
    client = Ark(api_key=api_key)
    
    print(f"正在分析图片: {filename}")
    print(f"完整路径: {image_path}")
    print("-" * 60)
    
    # 如果跳过分析且启用自动重新生成，直接重新生成
    if skip_analysis and auto_regenerate:
        print("跳过分析，直接重新生成图片...")
        try:
            if custom_prompt:
                print(f"使用自定义提示词: {custom_prompt}")
                success = regenerate_single_image_with_custom_prompt(image_path, custom_prompt)
            else:
                print("使用默认重新生成逻辑")
                success = regenerate_failed_image(image_path)
            
            if success:
                print("✓ 重新生成任务已提交")
                print("请稍后使用 check_async_tasks.py 检查生成结果")
            else:
                print("✗ 重新生成任务提交失败")
        except Exception as e:
            print(f"重新生成图片时发生错误: {e}")
        return
    
    # 编码图片
    image_base64 = encode_image_to_base64(image_path)
    if not image_base64:
        print(f"✗ 图片编码失败")
        return
    
    # 分析图片
    result, token_usage = analyze_image_with_llm(client, image_base64, prompt)
    
    print(f"Token使用统计:")
    print(f"输入Token: {token_usage['prompt_tokens']:,}")
    print(f"输出Token: {token_usage['completion_tokens']:,}")
    print(f"总Token: {token_usage['total_tokens']:,}")
    
    if result:
        print(f"\n分析结果: {result}")
        
        # 判断是否通过检查
        if "通过" in result or "pass" in result.lower():
            print("\n✓ 图片检查通过")
        else:
            print("\n✗ 图片检查失败")
            
            # 如果启用自动重新生成
            if auto_regenerate:
                print("\n开始重新生成图片...")
                
                # 使用自定义提示词或默认提示词
                if custom_prompt:
                    print(f"使用自定义提示词: {custom_prompt}")
                    success = regenerate_single_image_with_custom_prompt(image_path, custom_prompt)
                else:
                    print("使用默认重新生成逻辑")
                    success = regenerate_failed_image(image_path)
                
                if success:
                    print("✓ 重新生成任务已提交")
                    print("请稍后使用 check_async_tasks.py 检查生成结果")
                else:
                    print("✗ 重新生成任务提交失败")
            else:
                print("\n提示: 使用 --auto-regenerate 参数可自动重新生成失败的图片")
                if custom_prompt:
                    print("提示: 使用 --custom-prompt 参数可自定义重新生成的提示词")
    else:
        print("\n✗ 图片分析失败")
    
    print("\n分析完成!")

def regenerate_single_image_with_custom_prompt(image_path: str, custom_prompt: str) -> bool:
    """
    使用自定义提示词重新生成单个图片
    
    Args:
        image_path: 图片文件路径
        custom_prompt: 自定义提示词
        
    Returns:
        bool: 是否成功提交重新生成任务
    """
    if not all([VisualService, IMAGE_TWO_CONFIG, save_task_info]):
        print("错误: 图片生成模块不可用")
        return False
    
    try:
        # 检查原始图片是否存在
        if not os.path.exists(image_path):
            print(f"错误: 原始图片不存在: {image_path}")
            return False
        
        # 直接使用自定义提示词，不添加额外约束
        regenerate_prompt = custom_prompt
        
        # 先压缩原始图片，然后使用压缩后的版本作为参考
        compressed_image_path = resize_image_if_needed(image_path)
        
        # 调用新的异步生成函数，将任务保存到对应chapter的async_tasks目录
        # 使用压缩后的图片作为参考
        character_images_to_use = [compressed_image_path] if compressed_image_path != image_path else [image_path]
        
        success = generate_image_with_character_to_chapter_async(
            prompt=regenerate_prompt,
            output_path=image_path,  # 直接替换原图片
            character_images=character_images_to_use,  # 使用压缩后的图片作为参考
            style='manga',  # 使用manga风格
            max_retries=3
        )
        
        # 清理临时压缩文件
        if compressed_image_path != image_path and os.path.exists(compressed_image_path):
            try:
                os.unlink(compressed_image_path)
                print(f"已清理临时压缩文件: {compressed_image_path}")
            except:
                pass
        
        return success
        
    except Exception as e:
        print(f"✗ 重新生成图片时发生错误: {e}")
        return False

def process_narration_images(data_directory: str, prompt: str = "请仔细观察这张旁白图片，进行以下全面审查：\n\n【领口审查标准】\n✅ 通过的领口类型：圆领、立领、高领、方领、一字领等完全遮盖脖子和胸部的领口\n❌ 失败的领口类型：\n- 交领/衽领：左右衣襟交叉重叠，形成V字形开口，露出脖子和胸部皮肤\n- V领：任何形式的V字形领口\n- y字型领：形成Y字形状的领口\n- 低领：领口过低，露出脖子以下皮肤\n- 开胸装：胸前有明显开口或缝隙\n\n【皮肤暴露检查】\n检查角色是否存在以下问题：\n- 脖子暴露：脖子部位不能有任何皮肤暴露\n- 后背脖子以下皮肤暴露：后背脖子以下区域不能有皮肤暴露\n- 胸部皮肤暴露：胸前不能有皮肤暴露\n\n【手部检测】\n检查角色是否存在以下问题：\n- 三只手或更多手臂\n- 多余的手指\n- 手部位置不合理\n- 手部形状异常\n\n【内容审查】\n检查图片中是否存在文字、乱码、水印等不当内容\n\n【判断要求】\n请重点关注：\n1. 领口是否露出脖子以下的皮肤区域\n2. 脖子是否有任何暴露\n3. 后背脖子以下是否有皮肤暴露\n4. 角色手部数量是否正常（最多两只手）\n5. 如果角色穿着交领袍服、汉服等传统服装，要特别注意交领处是否形成开口露出胸部\n\n如果发现任何问题，请返回'失败'并详细说明原因。如果完全符合要求，请返回'通过'。", max_images: Optional[int] = None, start_from: Optional[str] = None, auto_regenerate: bool = False):
    """
    批量处理旁白图片分析
    
    Args:
        data_directory: 数据目录路径
        prompt: 分析提示词
        max_images: 最大处理图片数量，None表示处理所有图片
        start_from: 从指定图片开始处理，None表示从头开始
        auto_regenerate: 是否自动重新生成失败的图片
    """
    # 从配置文件获取API密钥
    api_key = ARK_CONFIG.get("api_key")
    if not api_key:
        print("错误: 请在 config/config.py 中配置 ARK_CONFIG['api_key']")
        return
    
    # 初始化客户端
    client = Ark(api_key=api_key)
    
    # 查找旁白图片文件
    print(f"正在搜索数据目录中的旁白图片: {data_directory}")
    image_files = find_narration_images_in_chapters(data_directory)
    
    if not image_files:
        print("未找到任何旁白图片文件")
        return
    
    # 查找起始位置
    start_index = 0
    if start_from:
        try:
            start_index = image_files.index(start_from)
            print(f"从指定图片开始: {start_from} (索引: {start_index + 1})")
        except ValueError:
            print(f"警告: 未找到指定的起始图片 {start_from}，将从头开始处理")
            start_index = 0
    
    # 从指定位置开始处理
    if start_index > 0:
        image_files = image_files[start_index:]
        print(f"跳过前 {start_index} 张图片")
    
    # 限制处理数量
    if max_images and len(image_files) > max_images:
        image_files = image_files[:max_images]
        print(f"限制处理前 {max_images} 张图片")
    
    print(f"找到 {len(image_files)} 张旁白图片，开始分析...")
    print(f"分析提示词: {prompt}")
    print("-" * 80)
    
    # Token 统计变量
    total_prompt_tokens = 0
    total_completion_tokens = 0
    total_tokens = 0
    
    # 失败图片记录文件路径
    script_dir = os.path.dirname(os.path.abspath(__file__))
    data_dir = os.path.join(script_dir, "data")
    # 确保data目录存在
    os.makedirs(data_dir, exist_ok=True)
    failed_file_path = os.path.join(data_dir, "fail.txt")
    
    # 如果是从头开始，清空之前的失败记录文件；如果是续传，则追加模式
    if start_index == 0:
        with open(failed_file_path, 'w', encoding='utf-8') as f:
            pass  # 创建空文件
        print("已清空失败记录文件")
    else:
        print("续传模式，将追加到现有失败记录文件")
    
    # 统计变量
    processed_count = 0
    passed_count = 0
    failed_count = 0
    error_count = 0
    regenerated_count = 0
    
    # 处理每张图片
    for i, image_path in enumerate(image_files, 1):
        print(f"\n[{i}/{len(image_files)}] 正在分析: {os.path.basename(image_path)}")
        print(f"完整路径: {image_path}")
        
        # 检查文件是否存在
        if not os.path.exists(image_path):
            print(f"✗ 文件不存在，跳过")
            error_count += 1
            continue
        
        # 编码图片
        image_base64 = encode_image_to_base64(image_path)
        if not image_base64:
            print(f"✗ 图片编码失败，跳过")
            error_count += 1
            continue
        
        # 分析图片
        result, token_usage = analyze_image_with_llm(client, image_base64, prompt)
        
        # 更新token统计
        total_prompt_tokens += token_usage["prompt_tokens"]
        total_completion_tokens += token_usage["completion_tokens"]
        total_tokens += token_usage["total_tokens"]
        
        processed_count += 1
        
        if result:
            print(f"分析结果: {result}")
            
            # 判断是否通过 - 修复逻辑：优先检查失败关键词
            if "失败" in result or "fail" in result.lower():
                print(f"✗ 检查失败")
                failed_count += 1
                
                # 记录失败图片到文件
                with open(failed_file_path, 'a', encoding='utf-8') as f:
                    f.write(f"{image_path}\n")
                    f.write(f"失败原因: {result}\n")
                    f.write("-" * 50 + "\n")
                
                # 如果启用自动重新生成
                if auto_regenerate:
                    print(f"正在尝试重新生成失败的图片...")
                    if regenerate_failed_image(image_path):
                        regenerated_count += 1
                        print(f"✓ 重新生成任务已提交")
                    else:
                        print(f"✗ 重新生成失败")
                        
            elif "通过" in result or "pass" in result.lower():
                print(f"✓ 检查通过")
                passed_count += 1
            else:
                print(f"? 结果不明确，默认为失败")
                failed_count += 1
                
                # 记录失败图片到文件
                with open(failed_file_path, 'a', encoding='utf-8') as f:
                    f.write(f"{image_path}\n")
                    f.write(f"失败原因: {result}\n")
                    f.write("-" * 50 + "\n")
                
                # 如果启用自动重新生成
                if auto_regenerate:
                    print(f"正在尝试重新生成失败的图片...")
                    if regenerate_failed_image(image_path):
                        regenerated_count += 1
                        print(f"✓ 重新生成任务已提交")
                    else:
                        print(f"✗ 重新生成失败")
        else:
            print(f"✗ LLM分析失败")
            error_count += 1
    
    # 输出统计结果
    print("\n" + "=" * 80)
    print("处理完成统计")
    print("=" * 80)
    print(f"总处理数量: {processed_count}")
    print(f"检查通过: {passed_count}")
    print(f"检查失败: {failed_count}")
    print(f"处理错误: {error_count}")
    if auto_regenerate:
        print(f"重新生成: {regenerated_count}")
    print(f"\nToken使用统计:")
    print(f"输入Token: {total_prompt_tokens:,}")
    print(f"输出Token: {total_completion_tokens:,}")
    print(f"总Token: {total_tokens:,}")
    
    if failed_count > 0:
        print(f"\n失败图片已记录到: {failed_file_path}")
        if auto_regenerate:
            print(f"已提交 {regenerated_count} 个重新生成任务")
            print(f"请稍后使用 check_async_tasks.py 检查生成结果")
    
    print("\n分析完成!")

def main():
    """
    主函数 - 处理命令行参数并执行旁白图片分析
    """
    parser = argparse.ArgumentParser(
        description="LLM旁白图片分析工具 - 批量检查chapter_xxx_image_xx.jpeg格式的旁白图片或单独处理指定图片",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
示例用法:
  # 批量处理目录下所有旁白图片
  python llm_narration_image.py data/004                    # 检查data/004目录下所有chapter中的旁白图片
  python llm_narration_image.py data/004 --prompt "自定义检查提示词"
  python llm_narration_image.py data/004 --max-images 10
  python llm_narration_image.py data/004 --start-from "/path/to/specific/image.jpg"
  python llm_narration_image.py data/004 --auto-regenerate  # 自动重新生成失败的图片
  
  # 单独处理指定图片文件
  python llm_narration_image.py data/006/chapter_003/chapter_003_image_08.jpeg --auto-regenerate
  python llm_narration_image.py data/006/chapter_003/chapter_003_image_08.jpeg --auto-regenerate --custom-prompt "去掉眼镜"
        """
    )
    
    # 位置参数：数据目录或图片文件路径
    parser.add_argument(
        'input_path',
        help='数据目录路径 (如: data/004) 或单个图片文件路径 (如: data/006/chapter_003/chapter_003_image_08.jpeg)'
    )
    
    parser.add_argument(
        '--prompt', '-p',
        default='请仔细观察这张旁白图片，进行以下全面审查：\n\n【领口审查标准】\n✅ 通过的领口类型：圆领、立领、高领、方领、一字领等完全遮盖脖子和胸部的领口\n❌ 失败的领口类型：\n- 交领/衽领：左右衣襟交叉重叠，形成V字形开口，露出脖子和胸部皮肤\n- V领：任何形式的V字形领口\n- y字型领：形成Y字形状的领口\n- 低领：领口过低，露出脖子以下皮肤\n- 开胸装：胸前有明显开口或缝隙\n\n【皮肤暴露检查】\n检查角色是否存在以下问题：\n- 脖子暴露：脖子部位不能有任何皮肤暴露\n- 后背脖子以下皮肤暴露：后背脖子以下区域不能有皮肤暴露\n- 胸部皮肤暴露：胸前不能有皮肤暴露\n\n【手部检测】\n检查角色是否存在以下问题：\n- 三只手或更多手臂\n- 多余的手指\n- 手部位置不合理\n- 手部形状异常\n\n【内容审查】\n检查图片中是否存在文字、乱码、水印等不当内容\n\n【判断要求】\n请重点关注：\n1. 领口是否露出脖子以下的皮肤区域\n2. 脖子是否有任何暴露\n3. 后背脖子以下是否有皮肤暴露\n4. 角色手部数量是否正常（最多两只手）\n5. 如果角色穿着交领袍服、汉服等传统服装，要特别注意交领处是否形成开口露出胸部\n\n如果发现任何问题，请返回"失败"并详细说明原因。如果完全符合要求，请返回"通过"。',
        help='LLM分析提示词 (默认: 检查领口类型、手部数量和内容)'
    )
    
    parser.add_argument(
        '--max-images', '-m',
        type=int,
        help='最大处理图片数量 (默认: 处理所有图片)'
    )
    
    parser.add_argument(
        '--start-from', '-s',
        help='从指定图片开始处理 (提供完整的图片路径)'
    )
    
    parser.add_argument(
        '--auto-regenerate', '-r',
        action='store_true',
        help='自动重新生成检测失败的图片'
    )
    
    parser.add_argument(
        '--custom-prompt', '-c',
        help='自定义重新生成图片的提示词 (如: "去掉眼镜", "换成短发")，仅在处理单个图片且启用--auto-regenerate时有效'
    )
    
    parser.add_argument(
        '--skip-analysis', '-k',
        action='store_true',
        help='跳过图片分析，直接重新生成图片（仅在处理单个图片且启用--auto-regenerate时有效）'
    )
    
    args = parser.parse_args()
    
    print("=" * 80)
    print("LLM旁白图片分析工具")
    print("=" * 80)
    
    # 判断输入是目录还是单个文件
    input_path = args.input_path
    is_single_file = os.path.isfile(input_path)
    
    if is_single_file:
        print(f"单个图片文件: {input_path}")
        if args.custom_prompt:
            print(f"自定义提示词: {args.custom_prompt}")
        if args.auto_regenerate:
            print(f"自动重新生成: 启用")
        else:
            print(f"自动重新生成: 禁用")
        
        # 检查custom_prompt参数的使用
        if args.custom_prompt and not args.auto_regenerate:
            print("警告: --custom-prompt 参数仅在启用 --auto-regenerate 时有效")
        
        # 检查skip_analysis参数的使用
        if args.skip_analysis and not args.auto_regenerate:
            print("警告: --skip-analysis 参数仅在启用 --auto-regenerate 时有效")
        
        print()
        
        # 处理单个图片文件
        process_single_image(input_path, args.prompt, args.auto_regenerate, args.custom_prompt, args.skip_analysis)
    else:
        print(f"数据目录: {input_path}")
        print(f"分析提示: {args.prompt}")
        if args.max_images:
            print(f"最大数量: {args.max_images}")
        if args.start_from:
            print(f"起始图片: {args.start_from}")
        if args.auto_regenerate:
            print(f"自动重新生成: 启用")
        else:
            print(f"自动重新生成: 禁用")
        if args.custom_prompt:
            print(f"警告: --custom-prompt 参数仅在处理单个图片时有效，将被忽略")
        print()
        
        # 执行批量旁白图片分析
        process_narration_images(input_path, args.prompt, args.max_images, args.start_from, args.auto_regenerate)

if __name__ == "__main__":
    main()