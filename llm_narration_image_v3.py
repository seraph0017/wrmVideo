#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
LLM旁白图片分析工具 V3版本 - 基于火山方舟SDK

该脚本专门用于检测chapter文件夹中的旁白图片（chapter_xxx_image_xx.jpeg格式），
检查衽领、V领、交领、y字型领以及三只手等问题，并支持自动重新生成。

V3版本特性:
- 使用火山方舟SDK (volcenginesdkarkruntime.Ark) 进行图片生成
- 支持本地base64编码图片作为参考，替代URL模式
- 保留原版的图片分析逻辑和批量处理功能
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
    python llm_narration_image_v3.py data/004
    
    # 自定义分析提示词
    python llm_narration_image_v3.py data/004 --prompt "自定义检查提示词"
    
    # 限制处理数量
    python llm_narration_image_v3.py data/004 --max-images 10
    
    # 启用自动重新生成失败图片
    python llm_narration_image_v3.py data/004 --auto-regenerate
    
    # 单独处理指定图片文件
    python llm_narration_image_v3.py data/006/chapter_003/chapter_003_image_08.jpeg --auto-regenerate
    
    # 单独处理图片并使用自定义重新生成提示词
    python llm_narration_image_v3.py data/006/chapter_003/chapter_003_image_08.jpeg --auto-regenerate --custom-prompt "去掉眼镜"

配置要求:
    需要在 config/config.py 中配置 ARK_CONFIG['api_key']
    需要在环境变量中设置 ARK_API_KEY
"""

import os
import argparse
import base64
import sys
import re
import json
import time
from pathlib import Path
from typing import List, Optional, Tuple
from volcenginesdkarkruntime import Ark

# 导入配置
from config.config import ARK_CONFIG

# 支持的图片格式
SUPPORTED_FORMATS = {'.jpg', '.jpeg', '.png', '.gif', '.bmp', '.webp'}

# 旁白图片文件名模式：chapter_xxx_image_xx.jpeg
NARRATION_IMAGE_PATTERN = re.compile(r'^chapter_\d+_image_\d+\.jpeg$', re.IGNORECASE)

def encode_image_to_base64(image_path: str) -> Optional[str]:
    """
    将图片文件编码为base64字符串
    
    Args:
        image_path: 图片文件路径
        
    Returns:
        Optional[str]: base64编码的图片数据，失败时返回None
    """
    try:
        with open(image_path, 'rb') as image_file:
            image_data = image_file.read()
            base64_data = base64.b64encode(image_data).decode('utf-8')
            return base64_data
    except Exception as e:
        print(f"编码图片失败: {e}")
        return None

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
            
            # 尝试不同的质量设置
            for quality in [85, 75, 65, 55]:
                img_resized.save(temp_path, 'JPEG', quality=quality, optimize=True)
                temp_size_mb = os.path.getsize(temp_path) / (1024 * 1024)
                
                if temp_size_mb <= max_size_mb:
                    print(f"压缩完成: {file_size_mb:.2f}MB -> {temp_size_mb:.2f}MB (质量: {quality})")
                    return temp_path
            
            # 如果还是太大，继续缩小尺寸
            scale_factor = 0.8
            new_width = int(new_width * scale_factor)
            new_height = int(new_height * scale_factor)
            img_resized = img.resize((new_width, new_height), Image.Resampling.LANCZOS)
            img_resized.save(temp_path, 'JPEG', quality=55, optimize=True)
            
            temp_size_mb = os.path.getsize(temp_path) / (1024 * 1024)
            print(f"最终压缩完成: {file_size_mb:.2f}MB -> {temp_size_mb:.2f}MB")
            return temp_path
            
    except ImportError:
        print("警告: 未安装PIL库，无法处理图片格式转换和压缩")
        return image_path
    except Exception as e:
        print(f"处理图片时发生错误: {e}")
        return image_path

def analyze_image_with_llm(client: Ark, image_base64: str, prompt: str) -> Tuple[Optional[str], Optional[dict]]:
    """
    使用LLM分析图片内容
    
    Args:
        client: Ark客户端实例
        image_base64: base64编码的图片数据
        prompt: 分析提示词
        
    Returns:
        Tuple[Optional[str], Optional[dict]]: (分析结果, token使用情况)
    """
    try:
        # 构建消息
        messages = [
            {
                "role": "user",
                "content": [
                    {
                        "type": "text",
                        "text": prompt
                    },
                    {
                        "type": "image_url",
                        "image_url": {
                            "url": f"data:image/jpeg;base64,{image_base64}"
                        }
                    }
                ]
            }
        ]
        
        # 调用API
        response = client.chat.completions.create(
            model=ARK_CONFIG.get("model", "doubao-seed-1-6-250615"),
            messages=messages,
            max_tokens=1000,
            temperature=0.1
        )
        
        # 提取结果
        if response.choices and len(response.choices) > 0:
            result = response.choices[0].message.content
            token_usage = {
                "prompt_tokens": response.usage.prompt_tokens if response.usage else 0,
                "completion_tokens": response.usage.completion_tokens if response.usage else 0,
                "total_tokens": response.usage.total_tokens if response.usage else 0
            }
            return result, token_usage
        else:
            print("API响应中没有找到有效内容")
            return None, None
            
    except Exception as e:
        print(f"LLM分析失败: {e}")
        return None, None

def regenerate_image_with_ark(image_path: str, custom_prompt: Optional[str] = None) -> bool:
    """
    使用火山方舟SDK重新生成图片
    基于用户提供的API示例实现
    
    Args:
        image_path: 原始图片路径
        custom_prompt: 自定义生成提示词
        
    Returns:
        bool: 是否成功重新生成
    """
    try:
        # 检查环境变量中的API Key
        api_key = os.environ.get("ARK_API_KEY")
        if not api_key:
            # 尝试从配置文件获取
            api_key = ARK_CONFIG.get("t2i_v3")
            if not api_key:
                print("错误: 未找到ARK_API_KEY，请在环境变量或配置文件中设置")
                return False
        
        # 获取t2i_v3模型ID
        model_id = "doubao-seededit-3-0-i2i-250628"
        if not model_id:
            print("错误: 未找到t2i_v3模型ID，请在配置文件中设置")
            return False
        
        # 初始化Ark客户端，按照用户提供的示例
        client = Ark(
            # 此为默认路径，您可根据业务所在地域进行配置
            base_url="https://ark.cn-beijing.volces.com/api/v3",
            # 从环境变量中获取您的 API Key。此为默认方式，您可根据需要进行修改
            api_key=api_key,
        )
        
        # 检查原始图片是否存在
        if not os.path.exists(image_path):
            print(f"错误: 原始图片不存在: {image_path}")
            return False
        
        # 压缩图片（如果需要）
        processed_image_path = resize_image_if_needed(image_path, max_size_mb=4.7)
        
        # 将图片编码为base64
        image_base64 = encode_image_to_base64(processed_image_path)
        if not image_base64:
            print("错误: 图片编码失败")
            return False
        
        # 构建生成提示词
        if custom_prompt:
            prompt = f"基于原图进行改进，{custom_prompt}，同时确保：领口必须是立领或高领，绝对不能是V领、交领、衽领、y字型领或其他露出脖子以下皮肤的领型，脖子必须完全被服装遮盖不能有任何暴露，角色只能有两只手，不能有三只手或更多手臂，画面清晰，细节丰富"
        else:
            prompt = "基于原图进行改进，同时确保：领口必须是立领或高领，绝对不能是V领、交领、衽领、y字型领或其他露出脖子以下皮肤的领型，脖子必须完全被服装遮盖不能有任何暴露，角色只能有两只手，不能有三只手或更多手臂，画面清晰，细节丰富"
        
        print(f"正在重新生成图片: {os.path.basename(image_path)}")
        print(f"生成提示词: {prompt}")
        
        # 调用图片生成API，按照用户提供的示例
        imagesResponse = client.images.generate(
            model=model_id,  # 使用配置文件中的t2i_v3模型ID
            prompt=prompt,
            image=f"data:image/jpeg;base64,{image_base64}",  # 使用data URL格式的base64编码图片
            seed=123,
            guidance_scale=5.5,
            size="adaptive",
            watermark=False,
            response_format="b64_json"
        )
        
        # 检查API响应是否有错误
        if hasattr(imagesResponse, 'error') and imagesResponse.error:
            print(f"错误: API返回错误信息: {imagesResponse.error}")
            return False
        
        # 检查响应数据
        if not hasattr(imagesResponse, 'data') or not imagesResponse.data or len(imagesResponse.data) == 0:
            print("错误: API响应中没有图片数据")
            return False
        
        # 获取生成的图片数据
        generated_image_data = imagesResponse.data[0]
        
        # 处理返回的图片数据
        image_data = None
        
        # 根据API文档，data数组中的每个元素包含图片信息
        if hasattr(generated_image_data, 'b64_json') and generated_image_data.b64_json:
            # 如果返回的是base64数据
            try:
                image_data = base64.b64decode(generated_image_data.b64_json)
                print("✓ 成功获取base64格式的图片数据")
            except Exception as e:
                print(f"错误: 解码base64图片数据失败: {e}")
                return False
        elif hasattr(generated_image_data, 'url') and generated_image_data.url:
            # 如果返回的是URL，下载图片
            print(f"生成的图片URL: {generated_image_data.url}")
            try:
                import requests
                response = requests.get(generated_image_data.url, timeout=30)
                if response.status_code == 200:
                    image_data = response.content
                    print("✓ 成功从URL下载图片数据")
                else:
                    print(f"错误: 下载图片失败，状态码: {response.status_code}")
                    return False
            except Exception as e:
                print(f"错误: 下载图片时发生异常: {e}")
                return False
        else:
            print("错误: 无法获取生成的图片数据，响应中既没有b64_json也没有url")
            return False
        
        if not image_data:
            print("错误: 图片数据为空")
            return False
        
        # 保存新图片，替换原图片
        with open(image_path, 'wb') as f:
            f.write(image_data)
        
        print(f"✓ 图片重新生成成功: {os.path.basename(image_path)}")
        
        # 清理临时文件
        if processed_image_path != image_path and os.path.exists(processed_image_path):
            try:
                os.unlink(processed_image_path)
                print(f"已清理临时文件: {processed_image_path}")
            except:
                pass
        
        return True
        
    except Exception as e:
        print(f"✗ 重新生成图片时发生错误: {e}")
        return False

def find_narration_images(data_directory: str) -> List[str]:
    """
    查找数据目录下所有的旁白图片文件
    
    Args:
        data_directory: 数据目录路径
        
    Returns:
        List[str]: 旁白图片文件路径列表
    """
    image_files = []
    
    # 检查目录是否存在
    if not os.path.exists(data_directory):
        print(f"错误: 数据目录不存在: {data_directory}")
        return image_files
    
    # 遍历所有chapter子目录
    for item in os.listdir(data_directory):
        item_path = os.path.join(data_directory, item)
        
        # 检查是否为chapter目录
        if os.path.isdir(item_path) and item.startswith('chapter_'):
            print(f"扫描目录: {item}")
            
            # 查找该目录下的旁白图片
            for file in os.listdir(item_path):
                if NARRATION_IMAGE_PATTERN.match(file):
                    file_path = os.path.join(item_path, file)
                    image_files.append(file_path)
    
    # 按文件名排序
    image_files.sort()
    
    print(f"找到 {len(image_files)} 个旁白图片文件")
    return image_files

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
    api_key = ARK_CONFIG.get("t2i_v3")
    if not api_key:
        print("错误: 未在配置文件中找到ARK API密钥")
        print("请在 config/config.py 中设置 ARK_CONFIG['t2i_v3']")
        return
    
    # 初始化Ark客户端
    try:
        client = Ark(
            base_url=ARK_CONFIG.get("base_url", "https://ark.cn-beijing.volces.com/api/v3"),
            api_key=api_key
        )
    except Exception as e:
        print(f"初始化Ark客户端失败: {e}")
        return
    
    # 如果跳过分析，直接重新生成
    if skip_analysis and auto_regenerate:
        print("跳过图片分析，直接重新生成...")
        success = regenerate_image_with_ark(image_path, custom_prompt)
        if success:
            print("✓ 图片重新生成完成")
        else:
            print("✗ 图片重新生成失败")
        return
    
    # 编码图片
    image_base64 = encode_image_to_base64(image_path)
    if not image_base64:
        print(f"✗ 图片编码失败，跳过")
        return
    
    # 分析图片
    print("正在分析图片...")
    result, token_usage = analyze_image_with_llm(client, image_base64, prompt)
    
    if result is None:
        print("✗ 图片分析失败")
        return
    
    # 显示分析结果
    print(f"分析结果: {result}")
    if token_usage:
        print(f"Token使用: {token_usage['total_tokens']} (输入: {token_usage['prompt_tokens']}, 输出: {token_usage['completion_tokens']})")
    
    # 判断是否通过检查
    result_lower = result.lower()
    is_passed = any(keyword in result_lower for keyword in ['通过', '合格', '符合要求', '没有问题', '正常'])
    is_failed = any(keyword in result_lower for keyword in ['失败', '不合格', '不符合', '问题', '错误', 'v领', '交领', '衽领', '三只手', '多余', '暴露'])
    
    if is_passed and not is_failed:
        print("✓ 图片检查通过")
    else:
        print("✗ 图片检查失败")
        
        # 如果启用自动重新生成
        if auto_regenerate:
            print("正在自动重新生成图片...")
            success = regenerate_image_with_ark(image_path, custom_prompt)
            if success:
                print("✓ 图片重新生成完成")
            else:
                print("✗ 图片重新生成失败")

def process_narration_images(
    data_directory: str, 
    prompt: str = None,
    max_images: Optional[int] = None, 
    start_from: Optional[str] = None, 
    auto_regenerate: bool = False
):
    """
    批量处理旁白图片分析
    
    Args:
        data_directory: 数据目录路径
        prompt: 分析提示词
        max_images: 最大处理图片数量，None表示处理所有图片
        start_from: 从指定图片开始处理，None表示从头开始
        auto_regenerate: 是否自动重新生成失败的图片
    """
    # 设置默认prompt
    if prompt is None:
        prompt = """请仔细观察这张旁白图片，进行以下全面审查：

【领口审查标准】
✅ 通过的领口类型：圆领、立领、高领、方领、一字领等完全遮盖脖子和胸部的领口
❌ 失败的领口类型：
- 交领/衽领：左右衣襟交叉重叠，形成V字形开口
- V领：领口呈V字形，露出脖子和胸部皮肤
- 深V领：V字形开口更深，暴露更多皮肤
- y字型领：类似Y字形状的领口设计
- 低胸领：领口位置较低，露出胸部皮肤
- 任何其他露出脖子以下皮肤的领口设计

【手部检查标准】
✅ 通过：角色只有两只手，手指数量正常（每只手5根手指）
❌ 失败：
- 出现三只手或更多手臂
- 手指数量异常（多于或少于5根）
- 手部形状扭曲或不自然

【内容审查标准】
✅ 通过：画面清晰，无乱码文字，内容健康
❌ 失败：
- 出现乱码、不相关文字内容
- 画面模糊不清
- 包含不当内容

请逐项检查并给出明确的"通过"或"失败"结论，如果发现任何问题请详细说明。"""
    
    # 从配置文件获取API密钥
    api_key = ARK_CONFIG.get("t2i_v3")
    if not api_key:
        print("错误: 未在配置文件中找到ARK API密钥")
        print("请在 config/config.py 中设置 ARK_CONFIG['t2i_v3']")
        return
    
    # 初始化Ark客户端
    try:
        client = Ark(
            base_url=ARK_CONFIG.get("base_url", "https://ark.cn-beijing.volces.com/api/v3"),
            api_key=api_key
        )
    except Exception as e:
        print(f"初始化Ark客户端失败: {e}")
        return
    
    # 查找所有旁白图片
    image_files = find_narration_images(data_directory)
    
    if not image_files:
        print("未找到任何旁白图片文件")
        return
    
    # 处理起始位置
    start_index = 0
    if start_from:
        try:
            start_index = image_files.index(start_from)
            print(f"从指定图片开始: {os.path.basename(start_from)} (索引: {start_index})")
        except ValueError:
            print(f"警告: 未找到指定的起始图片: {start_from}")
            print("将从头开始处理")
    
    # 限制处理数量
    if max_images:
        end_index = min(start_index + max_images, len(image_files))
        image_files = image_files[start_index:end_index]
        print(f"限制处理数量: {max_images}，实际处理: {len(image_files)}")
    else:
        image_files = image_files[start_index:]
        print(f"处理图片数量: {len(image_files)}")
    
    # 创建失败记录文件
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
        
        if result is None:
            print(f"✗ 分析失败，跳过")
            error_count += 1
            continue
        
        processed_count += 1
        
        # 显示分析结果
        print(f"分析结果: {result}")
        if token_usage:
            print(f"Token使用: {token_usage['total_tokens']} (输入: {token_usage['prompt_tokens']}, 输出: {token_usage['completion_tokens']})")
        
        # 判断是否通过检查
        result_lower = result.lower()
        is_passed = any(keyword in result_lower for keyword in ['通过', '合格', '符合要求', '没有问题', '正常'])
        is_failed = any(keyword in result_lower for keyword in ['失败', '不合格', '不符合', '问题', '错误', 'v领', '交领', '衽领', '三只手', '多余', '暴露'])
        
        if is_passed and not is_failed:
            print("✓ 图片检查通过")
            passed_count += 1
        else:
            print("✗ 图片检查失败")
            failed_count += 1
            
            # 记录失败的图片
            with open(failed_file_path, 'a', encoding='utf-8') as f:
                f.write(f"{image_path}\n")
            
            # 如果启用自动重新生成
            if auto_regenerate:
                print("正在自动重新生成图片...")
                success = regenerate_image_with_ark(image_path)
                if success:
                    regenerated_count += 1
                    print("✓ 图片重新生成完成")
                else:
                    print("✗ 图片重新生成失败")
        
        # 添加延迟避免API限制
        time.sleep(1)
    
    # 显示统计结果
    print("\n" + "=" * 80)
    print("批量分析完成!")
    print("=" * 80)
    print(f"总计处理: {processed_count} 张图片")
    print(f"检查通过: {passed_count} 张")
    print(f"检查失败: {failed_count} 张")
    print(f"处理错误: {error_count} 张")
    
    if failed_count > 0:
        print(f"\n失败图片已记录到: {failed_file_path}")
        if auto_regenerate:
            print(f"已重新生成: {regenerated_count} 张图片")
    
    print("\n分析完成!")

def main():
    """
    主函数 - 处理命令行参数并执行旁白图片分析
    """
    parser = argparse.ArgumentParser(
        description="LLM旁白图片分析工具 V3版本 - 基于火山方舟SDK，批量检查chapter_xxx_image_xx.jpeg格式的旁白图片或单独处理指定图片",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
示例用法:
  # 批量处理目录下所有旁白图片
  python llm_narration_image_v3.py data/004                    # 检查data/004目录下所有chapter中的旁白图片
  python llm_narration_image_v3.py data/004 --prompt "自定义检查提示词"
  python llm_narration_image_v3.py data/004 --max-images 10
  python llm_narration_image_v3.py data/004 --start-from "/path/to/specific/image.jpg"
  python llm_narration_image_v3.py data/004 --auto-regenerate  # 自动重新生成失败的图片
  
  # 单独处理指定图片文件
  python llm_narration_image_v3.py data/006/chapter_003/chapter_003_image_08.jpeg --auto-regenerate
  python llm_narration_image_v3.py data/006/chapter_003/chapter_003_image_08.jpeg --auto-regenerate --custom-prompt "去掉眼镜"
        """
    )
    
    # 位置参数：数据目录或图片文件路径
    parser.add_argument(
        'input_path',
        help='数据目录路径 (如: data/004) 或单个图片文件路径 (如: data/006/chapter_003/chapter_003_image_08.jpeg)'
    )
    
    parser.add_argument(
        '--prompt', '-p',
        default='请仔细观察这张旁白图片，进行以下全面审查：\n\n【领口审查标准】\n✅ 通过的领口类型：圆领、立领、高领、方领、一字领等完全遮盖脖子和胸部的领口\n❌ 失败的领口类型：\n- 交领/衽领：左右衣襟交叉重叠，形成V字形开口\n- V领：领口呈V字形，露出脖子和胸部皮肤\n- 深V领：V字形开口更深，暴露更多皮肤\n- y字型领：类似Y字形状的领口设计\n- 低胸领：领口位置较低，露出胸部皮肤\n- 任何其他露出脖子以下皮肤的领口设计\n\n【手部检查标准】\n✅ 通过：角色只有两只手，手指数量正常（每只手5根手指）\n❌ 失败：\n- 出现三只手或更多手臂\n- 手指数量异常（多于或少于5根）\n- 手部形状扭曲或不自然\n\n【内容审查标准】\n✅ 通过：画面清晰，无乱码文字，内容健康\n❌ 失败：\n- 出现乱码、不相关文字内容\n- 画面模糊不清\n- 包含不当内容\n\n请逐项检查并给出明确的"通过"或"失败"结论，如果发现任何问题请详细说明。',
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
    print("LLM旁白图片分析工具 V3版本 - 基于火山方舟SDK")
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