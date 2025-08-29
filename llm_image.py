#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
LLM图片分析工具

该脚本用于对角色图片进行领口审查和内容审查，
使用火山引擎Ark API对图片进行智能分析。

功能特性:
- 支持两种模式：数据目录模式和普通目录模式
- 数据目录模式：遍历指定数据目录下所有chapter文件夹中的角色图片
- 普通目录模式：遍历指定目录下的所有图片文件
- 领口审查：检测衽领、V领、交领等会露出脖子以下皮肤的领口类型
- 内容审查：检测图片中的乱码或文字内容
- 自动重新生成：检测到失败图片时自动调用图片生成模块重新生成
- 支持常见图片格式(jpg, jpeg, png, gif, bmp, webp)
- 使用base64编码处理图片
- 批量分析图片内容
- 详细的进度反馈和错误处理
- 自动记录失败的图片到fail.txt文件

使用方法:
    # 数据目录模式 - 检查data/004目录下所有chapter中的角色图片
    python llm_image.py data/004
    
    # 普通目录模式 - 检查指定目录下的所有图片
    python llm_image.py --directory /path/to/images
    
    # 自定义分析提示词
    python llm_image.py data/004 --prompt "自定义检查提示词"
    
    # 限制处理数量
    python llm_image.py data/004 --max-images 10
    
    # 启用自动重新生成失败图片
    python llm_image.py data/004 --auto-regenerate

配置要求:
    需要在 config/config.py 中配置 ARK_CONFIG['api_key']
"""

import os
import argparse
import base64
import sys
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
    from config.prompt_config import ART_STYLES
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

def encode_image_to_base64(image_path: str) -> Optional[str]:
    """
    将图片文件编码为base64格式
    
    Args:
        image_path: 图片文件路径
        
    Returns:
        base64编码的图片数据，格式为 data:image/<format>;base64,<data>
        如果编码失败返回None
    """
    try:
        with open(image_path, 'rb') as image_file:
            # 读取图片二进制数据
            image_data = image_file.read()
            # 编码为base64
            base64_data = base64.b64encode(image_data).decode('utf-8')
            
            # 获取图片格式 - 根据实际文件内容而不是扩展名
            import imghdr
            detected_format = imghdr.what(image_path)
            if detected_format:
                # 使用检测到的实际格式
                image_format = detected_format
            else:
                # 如果检测失败，回退到扩展名判断
                file_extension = Path(image_path).suffix.lower()
                if file_extension == '.jpg':
                    image_format = 'jpeg'
                else:
                    image_format = file_extension[1:]  # 去掉点号
            
            # 构造完整的data URL
            return f"data:image/{image_format};base64,{base64_data}"
            
    except Exception as e:
        print(f"编码图片失败 {image_path}: {e}")
        return None

def find_image_files(directory: str) -> List[str]:
    """
    递归查找目录下的所有图片文件
    
    Args:
        directory: 要搜索的目录路径
        
    Returns:
        图片文件路径列表
    """
    image_files = []
    directory_path = Path(directory)
    
    if not directory_path.exists():
        print(f"目录不存在: {directory}")
        return image_files
    
    # 递归遍历目录
    for file_path in directory_path.rglob('*'):
        if file_path.is_file() and file_path.suffix.lower() in SUPPORTED_FORMATS:
            image_files.append(str(file_path))
    
    return sorted(image_files)

def find_character_images_in_chapters(data_directory: str) -> List[str]:
    """
    查找指定数据目录下所有chapter文件夹中的角色图片
    
    Args:
        data_directory: 数据目录路径 (如: data/004)
        
    Returns:
        角色图片文件路径列表
    """
    character_images = []
    data_path = Path(data_directory)
    
    if not data_path.exists():
        print(f"数据目录不存在: {data_directory}")
        return character_images
    
    # 查找所有chapter文件夹
    chapter_dirs = [d for d in data_path.iterdir() if d.is_dir() and d.name.startswith('chapter')]
    
    if not chapter_dirs:
        print(f"在 {data_directory} 中未找到任何chapter文件夹")
        return character_images
    
    print(f"找到 {len(chapter_dirs)} 个chapter文件夹")
    
    # 遍历每个chapter文件夹
    for chapter_dir in sorted(chapter_dirs):
        print(f"正在扫描: {chapter_dir}")
        
        # 查找该chapter目录下的所有图片文件
        for file_path in chapter_dir.rglob('*'):
            if file_path.is_file() and file_path.suffix.lower() in SUPPORTED_FORMATS:
                # 检查是否为角色图片（文件名包含"character"）
                if 'character' in file_path.name.lower():
                    character_images.append(str(file_path))
                    print(f"  找到角色图片: {file_path.name}")
    
    print(f"总共找到 {len(character_images)} 张角色图片")
    return sorted(character_images)

def analyze_image_with_llm(client: Ark, image_base64: str, prompt: str = "请仔细观察这张角色图片，进行以下全面审查：\n\n【领口审查标准】\n✅ 通过的类型：完全遮盖脖子到胸口的皮肤的衣服\n❌ 失败的类型：\n- 露出脖子和胸部皮肤\n- V领：任何形式的V字形领口\n- 低领：领口过低，露出脖子以下皮肤\n- 开胸装：胸前有明显开口或缝隙\n\n【皮肤暴露检查 - 严格标准】\n检查角色是否存在以下问题（任何一项都视为失败）：\n- 脖子暴露：脖子部位不能有任何皮肤暴露，必须完全被服装遮盖\n- 后背脖子以下皮肤暴露：后背脖子以下区域不能有皮肤暴露\n- 胸部皮肤暴露：胸前不能有皮肤暴露\n\n【身体部位异常检查 - 严格标准】\n检查角色是否存在以下身体部位异常（任何一项都视为失败）：\n- 多手：角色有超过2只手臂或手\n- 多脚：角色有超过2只脚或腿\n- 多手指：单只手有超过5根手指\n- 手指异常：手指形状扭曲、融合或数量明显错误\n- 肢体畸形：手臂、腿部或其他肢体出现明显的解剖学错误\n- 身体比例异常：头部、四肢比例严重失调\n\n【亲密行为检查 - 严格标准】\n检查图片中是否存在以下亲密行为（任何一项都视为失败）：\n- 拥抱：两人或多人相互拥抱的姿势\n- 勾肩搭背：手臂搭在他人肩膀或背部的亲密姿势\n- 亲密接触：任何形式的身体亲密接触或暧昧姿势\n- 过度亲近：角色之间距离过近，呈现亲密关系的画面\n\n【内容审查】\n检查图片中是否存在文字、乱码、水印等不当内容\n\n【判断要求】\n请重点关注：\n1. 领口是否露出脖子以下的皮肤区域\n2. 脖子是否有任何暴露（即使是很小的暴露也不允许）\n3. 后背脖子以下是否有皮肤暴露\n4. 如果角色穿着交领袍服、汉服等传统服装，要特别注意交领处是否形成开口露出胸部\n5. 仔细检查角色的手、脚、手指数量是否正常\n6. 观察身体各部位的解剖学正确性\n7. 检查是否存在拥抱、勾肩搭背等亲密行为\n\n如果发现任何问题，请返回'失败'并详细说明原因。如果完全符合要求，请返回'通过'。") -> tuple[Optional[str], dict]:
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
    if not all([VisualService, IMAGE_TWO_CONFIG, ART_STYLES, save_task_info, gen_encode_image_to_base64]):
        print("错误: 图片生成模块不可用")
        return False
    
    # 对于重新生成模式，不检查文件是否存在，直接强制重新生成
    # 只有在非重新生成模式下才检查文件存在性
    # 注意：此函数主要用于重新生成失败图片，所以应该强制替换
    
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
        
        # 获取艺术风格提示词
        if style and style in ART_STYLES:
            style_prompt = ART_STYLES[style]['description']
        else:
            style_prompt = ART_STYLES.get('manga', {}).get('description', '动漫插画，精美细腻的画风，鲜艳的色彩，清晰的线条')
        
        for attempt in range(max_retries + 1):
            # 构建完整提示词
            full_prompt = "女性衣服不能漏膝盖以上遮盖掉,把胸口到脖子的皮肤全部覆盖住,去掉衽领，交领，V领，换成高领圆领袍\n领口不能是V领，领口不能是衽领，领口不能是交领，领口不能是任何y字型或者v字型的领子\n手指数量修改到正常\n角色之间不能有拥抱、挽手、亲密接触等行为，角色之间要保持适当距离\n" + style_prompt + "\n\n" + prompt + "\n\n"
            
            if attempt == 0:  # 只在第一次尝试时打印完整prompt
                print("完整的prompt: {}".format(full_prompt))
            
            # 构建请求参数
            form = {
                "req_key": "byteedit_v2.0",
                "prompt": full_prompt,
                "seed": 10 + attempt,  # 每次重试使用不同的seed
                "scale": 0.4,
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
            
            # 如果有角色图片，添加到请求中
            if character_images:
                print(f"开始处理 {len(character_images)} 个角色图片")
                binary_data_list = []
                for img_path in character_images:
                    if img_path and os.path.exists(img_path):
                        base64_data = gen_encode_image_to_base64(img_path)
                        if base64_data:
                            binary_data_list.append(base64_data)
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
                    'style': style,
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
    重新生成失败的图片
    将异步任务保存到对应chapter的async_tasks目录
    使用原始失败图片作为参考进行改进
    
    Args:
        image_path: 失败图片的路径
        
    Returns:
        bool: 是否成功重新生成
    """
    if not all([VisualService, IMAGE_TWO_CONFIG, ART_STYLES, save_task_info]):
        print("错误: 图片生成模块不可用")
        return False
    
    try:
        # 检查原始图片是否存在
        if not os.path.exists(image_path):
            print(f"错误: 原始图片不存在: {image_path}")
            return False
        
        # 构建生成提示词，强调领口和皮肤暴露要求
        regenerate_prompt = "基于原图进行改进，领口必须是圆领、立领或高领，绝对不能是V领、交领、衽领或其他露出脖子以下皮肤的领型，脖子必须完全被服装遮盖不能有任何暴露，后背脖子以下不能有皮肤暴露，胸部不能有皮肤暴露，手指数量要正常，画面清晰，细节丰富，"
        
        print(f"正在重新生成图片: {image_path}")
        print(f"生成提示词: {regenerate_prompt}")
        print("注意: 使用原始失败图片作为参考进行改进")
        
        # 调用新的异步生成函数，将任务保存到对应chapter的async_tasks目录
        # 传入原始失败图片作为character_images参数
        success = generate_image_with_character_to_chapter_async(
            prompt=regenerate_prompt,
            output_path=image_path,  # 直接替换原图片
            character_images=[image_path],  # 使用原始失败图片作为参考
            style='manga',  # 使用manga风格
            max_retries=3
        )
        
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


def process_images(directory: str, prompt: str = "请仔细观察这张角色图片的服装领口设计，进行以下审查：\n\n【领口审查标准】\n✅ 通过的领口类型：圆领、立领、高领、方领、一字领等完全遮盖脖子和胸部的领口\n❌ 失败的领口类型：\n- 交领/衽领：左右衣襟交叉重叠，形成V字形开口，露出脖子和胸部皮肤\n- V领：任何形式的V字形领口\n- 低领：领口过低，露出脖子以下皮肤\n- 开胸装：胸前有明显开口或缝隙\n\n【皮肤暴露检查】\n检查角色是否存在以下问题：\n- 脖子暴露：脖子部位不能有任何皮肤暴露\n- 后背脖子以下皮肤暴露：后背脖子以下区域不能有皮肤暴露\n- 胸部皮肤暴露：胸前不能有皮肤暴露\n\n【内容审查】\n检查图片中是否存在文字、乱码、水印等不当内容\n\n【判断要求】\n请重点关注：\n1. 领口是否露出脖子以下的皮肤区域\n2. 脖子是否有任何暴露\n3. 后背脖子以下是否有皮肤暴露\n4. 如果角色穿着交领袍服、汉服等传统服装，要特别注意交领处是否形成开口露出胸部\n\n如果发现任何问题，请返回'失败'并详细说明原因。如果完全符合要求，请返回'通过'。", max_images: Optional[int] = None, start_from: Optional[str] = None, is_data_directory: bool = False, auto_regenerate: bool = False):
    """
    批量处理图片分析
    
    Args:
        directory: 图片目录路径
        prompt: 分析提示词
        max_images: 最大处理图片数量，None表示处理所有图片
        start_from: 从指定图片开始处理，None表示从头开始
        is_data_directory: 是否为数据目录模式
        auto_regenerate: 是否自动重新生成失败的图片
    """
    # 从配置文件获取API密钥
    api_key = ARK_CONFIG.get("api_key")
    if not api_key:
        print("错误: 请在 config/config.py 中配置 ARK_CONFIG['api_key']")
        return
    
    # 初始化客户端
    client = Ark(api_key=api_key)
    
    # 查找图片文件
    if is_data_directory:
        print(f"正在搜索数据目录中的角色图片: {directory}")
        image_files = find_character_images_in_chapters(directory)
    else:
        print(f"正在搜索目录: {directory}")
        image_files = find_image_files(directory)
    
    if not image_files:
        if is_data_directory:
            print("未找到任何角色图片文件")
        else:
            print("未找到任何图片文件")
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
    
    print(f"找到 {len(image_files)} 张图片，开始分析...")
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
        print(f"续传模式，失败记录将追加到: {failed_file_path}")
    
    failed_count = 0
    
    # 处理每张图片
    success_count = 0
    for i, image_path in enumerate(image_files, 1):
        # 计算实际的全局索引
        global_index = start_index + i
        print(f"\n[{global_index}/{start_index + len(image_files)}] 处理: {image_path}")
        
        # 编码图片
        image_base64 = encode_image_to_base64(image_path)
        if not image_base64:
            print("跳过: 图片编码失败")
            continue
        
        # LLM分析
        result, token_info = analyze_image_with_llm(client, image_base64, prompt)
        if result:
            print(f"分析结果: {result}")
            success_count += 1
            # 累计 token 统计
            total_prompt_tokens += token_info["prompt_tokens"]
            total_completion_tokens += token_info["completion_tokens"]
            total_tokens += token_info["total_tokens"]
            
            # 检查是否失败
            if "失败" in result:
                failed_info = f"{image_path} - {result.strip()}"
                # 立即写入失败记录
                with open(failed_file_path, 'a', encoding='utf-8') as f:
                    f.write(f"{failed_info}\n")
                failed_count += 1
                print(f"检测失败: {image_path} - {result.strip()}")
                print(f"失败记录已写入: {failed_file_path}")
                
                # 如果启用自动重新生成
                if auto_regenerate:
                    print(f"正在重新生成图片: {image_path}")
                    if regenerate_failed_image(image_path):
                        print(f"重新生成任务已提交: {image_path}")
                    else:
                        print(f"重新生成失败: {image_path}")
        else:
            print("跳过: LLM分析失败")
    
    # 输出失败统计
    if failed_count > 0:
        print(f"失败图片已记录到: {failed_file_path}")
        print(f"失败图片数量: {failed_count}")
    
    print("-" * 80)
    print(f"处理完成! 成功分析 {success_count}/{len(image_files)} 张图片")
    print(f"Token统计: 输入={total_prompt_tokens}, 输出={total_completion_tokens}, 总计={total_tokens}")

def main():
    """
    主函数 - 处理命令行参数并执行图片分析
    """
    parser = argparse.ArgumentParser(
        description="LLM图片分析工具 - 批量检查角色图片的领口类型和内容",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
示例用法:
  python llm_image.py data/004                    # 检查data/004目录下所有chapter中的角色图片
  python llm_image.py --directory /path/to/images # 检查指定目录下的所有图片
  python llm_image.py data/004 --prompt "自定义检查提示词"
  python llm_image.py data/004 --max-images 10
  python llm_image.py data/004 --start-from "/path/to/specific/image.jpg"
  python llm_image.py data/004 --auto-regenerate  # 自动重新生成失败的图片
        """
    )
    
    # 位置参数：数据目录
    parser.add_argument(
        'data_directory',
        nargs='?',  # 可选的位置参数
        help='数据目录路径 (如: data/004)，用于检查该目录下所有chapter中的角色图片'
    )
    
    parser.add_argument(
        '--directory', '-d',
        default='/Users/xunan/Projects/wrmVideo/Character_Images',
        help='图片目录路径 (默认: Character_Images)，当未提供数据目录时使用'
    )
    
    parser.add_argument(
        '--prompt', '-p',
        default='请仔细观察这张角色图片的服装领口设计，进行以下审查：\n\n【领口审查标准】\n✅ 通过的领口类型：圆领、立领、高领、方领、一字领等完全遮盖脖子和胸部的领口\n❌ 失败的领口类型：\n- 交领/衽领：左右衣襟交叉重叠，形成V字形开口，露出脖子和胸部皮肤\n- V领：任何形式的V字形领口\n- 低领：领口过低，露出脖子以下皮肤\n- 开胸装：胸前有明显开口或缝隙\n\n【内容审查】\n检查图片中是否存在文字、乱码、水印等不当内容\n\n【判断要求】\n请重点关注领口是否露出脖子以下的皮肤区域。如果角色穿着交领袍服、汉服等传统服装，要特别注意交领处是否形成开口露出胸部。\n\n如果发现任何问题，请返回"失败"并详细说明原因。如果完全符合要求，请返回"通过"。',
        help='LLM分析提示词 (默认: 检查领口类型和内容)'
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
    
    args = parser.parse_args()
    
    # 确定处理模式和目标目录
    if args.data_directory:
        # 数据目录模式：检查指定数据目录下的角色图片
        target_directory = args.data_directory
        is_data_mode = True
        mode_description = "数据目录模式 - 检查chapter文件夹中的角色图片"
    else:
        # 普通目录模式：检查指定目录下的所有图片
        target_directory = args.directory
        is_data_mode = False
        mode_description = "普通目录模式 - 检查目录下的所有图片"
    
    print("=" * 80)
    print("LLM图片分析工具")
    print("=" * 80)
    print(f"处理模式: {mode_description}")
    print(f"目标目录: {target_directory}")
    print(f"分析提示: {args.prompt}")
    if args.max_images:
        print(f"最大数量: {args.max_images}")
    if args.start_from:
        print(f"起始图片: {args.start_from}")
    if args.auto_regenerate:
        print(f"自动重新生成: 启用")
    else:
        print(f"自动重新生成: 禁用")
    print()
    
    # 执行图片分析
    process_images(target_directory, args.prompt, args.max_images, args.start_from, is_data_mode, args.auto_regenerate)

if __name__ == "__main__":
    main()