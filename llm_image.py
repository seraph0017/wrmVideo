#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
LLM图片分析工具

该脚本用于遍历Character_Images目录下的所有图片文件，
使用火山引擎Ark API对图片进行内容分析。

功能特性:
- 自动遍历指定目录下的所有图片文件
- 支持常见图片格式(jpg, jpeg, png, gif, bmp, webp)
- 使用base64编码处理图片
- 批量分析图片内容
- 详细的进度反馈和错误处理

使用方法:
    python llm_image.py
    python llm_image.py --directory /path/to/images
    python llm_image.py --prompt "描述这张图片的风格和特点"

配置要求:
    需要在 config/config.py 中配置 ARK_CONFIG['api_key']
"""

import os
import argparse
import base64
from pathlib import Path
from typing import List, Optional
from volcenginesdkarkruntime import Ark

# 导入配置
from config.config import ARK_CONFIG

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
            
            # 获取图片格式
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

def analyze_image_with_llm(client: Ark, image_base64: str, prompt: str = "图中人物着装在领口处，是不是圆领，或者立领，或者高领，如果不是这三种领口，且是V领，那就是失败，反之通过。如果失败，请说明失败的原因（如：V领、其他领型等）。只给我返回通过或者失败+原因") -> tuple[Optional[str], dict]:
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

def process_images(directory: str, prompt: str = "图中人物着装在领口处，是不是圆领，或者立领，或者高领，如果不是这三种领口，且是V领，那就是失败，反之通过。如果失败，请说明失败的原因（如：V领、其他领型等）。只给我返回通过或者失败+原因", max_images: Optional[int] = None):
    """
    批量处理图片分析
    
    Args:
        directory: 图片目录路径
        prompt: 分析提示词
        max_images: 最大处理图片数量，None表示处理所有图片
    """
    # 从配置文件获取API密钥
    api_key = ARK_CONFIG.get("api_key")
    if not api_key:
        print("错误: 请在 config/config.py 中配置 ARK_CONFIG['api_key']")
        return
    
    # 初始化客户端
    client = Ark(api_key=api_key)
    
    # 查找图片文件
    print(f"正在搜索目录: {directory}")
    image_files = find_image_files(directory)
    
    if not image_files:
        print("未找到任何图片文件")
        return
    
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
    
    # 清空之前的失败记录文件
    with open(failed_file_path, 'w', encoding='utf-8') as f:
        pass  # 创建空文件
    
    failed_count = 0
    
    # 处理每张图片
    success_count = 0
    for i, image_path in enumerate(image_files, 1):
        print(f"\n[{i}/{len(image_files)}] 处理: {image_path}")
        
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
        description="LLM图片分析工具 - 批量检查Character_Images目录下图片的人物着装领口类型",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
示例用法:
  python llm_image.py
  python llm_image.py --directory /path/to/images
  python llm_image.py --prompt "自定义检查提示词"
  python llm_image.py --max-images 10
        """
    )
    
    parser.add_argument(
        '--directory', '-d',
        default='/Users/xunan/Projects/wrmVideo/Character_Images',
        help='图片目录路径 (默认: Character_Images)'
    )
    
    parser.add_argument(
        '--prompt', '-p',
        default='图中人物着装在领口处，是不是圆领，或者立领，或者高领，如果不是这三种领口，且是V领，或者衽领，并且里面没有内衬的，那就是失败，反之通过。如果失败，请说明失败的原因（如：V领、其他领型等）。只给我返回通过或者失败+原因',
        help='LLM分析提示词 (默认: 检查人物着装领口类型)')
    
    parser.add_argument(
        '--max-images', '-m',
        type=int,
        help='最大处理图片数量 (默认: 处理所有图片)'
    )
    
    args = parser.parse_args()
    
    print("=" * 80)
    print("LLM图片分析工具")
    print("=" * 80)
    print(f"目标目录: {args.directory}")
    print(f"分析提示: {args.prompt}")
    if args.max_images:
        print(f"最大数量: {args.max_images}")
    print()
    
    # 执行图片分析
    process_images(args.directory, args.prompt, args.max_images)

if __name__ == "__main__":
    main()