#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
上传完整视频文件到TOS存储服务

使用方法:
    python upload_tos.py data/002

功能:
    遍历指定目录下的chapter文件夹，找到所有的chapter_xxx_complete_video.mp4文件
    并上传到TOS存储服务的指定路径
    
配置说明:
    - TOS访问密钥从config.py的IMAGE_TWO_CONFIG中读取
    - 使用上海区域服务 (tos-cn-shanghai.volces.com)
    - 无需额外的环境变量配置
"""

import os
import sys
import argparse
import glob
from pathlib import Path
import tos
from config.config import IMAGE_TWO_CONFIG


def upload_video_to_tos(local_file_path, bucket_name, object_key, client):
    """
    上传单个视频文件到TOS
    
    Args:
        local_file_path (str): 本地文件路径
        bucket_name (str): TOS bucket名称
        object_key (str): TOS对象键名
        client: TOS客户端实例
    
    Returns:
        bool: 上传是否成功
    """
    try:
        print(f"开始上传: {local_file_path} -> tos://{bucket_name}/{object_key}")
        
        # 使用文件流方式上传
        with open(local_file_path, 'rb') as f:
            client.put_object(bucket_name, object_key, content=f)
        
        print(f"✓ 上传成功: {object_key}")
        return True
        
    except tos.exceptions.TosClientError as e:
        print(f"❌ 客户端错误: {e.message}, 原因: {e.cause}")
        return False
    except tos.exceptions.TosServerError as e:
        print(f"❌ 服务端错误: {e.code}")
        print(f"请求ID: {e.request_id}")
        print(f"错误信息: {e.message}")
        print(f"HTTP状态码: {e.status_code}")
        return False
    except Exception as e:
        print(f"❌ 未知错误: {e}")
        return False


def find_complete_videos(data_dir):
    """
    查找指定目录下所有的complete_video.mp4文件
    
    Args:
        data_dir (str): 数据目录路径
    
    Returns:
        list: 找到的视频文件路径列表
    """
    video_files = []
    data_path = Path(data_dir)
    
    if not data_path.exists():
        print(f"❌ 目录不存在: {data_dir}")
        return video_files
    
    # 遍历所有chapter目录
    chapter_dirs = [d for d in data_path.iterdir() 
                   if d.is_dir() and d.name.startswith('chapter_')]
    
    for chapter_dir in sorted(chapter_dirs):
        # 查找complete_video.mp4文件
        pattern = str(chapter_dir / "*_complete_video.mp4")
        found_files = glob.glob(pattern)
        
        for file_path in found_files:
            video_files.append(file_path)
            print(f"找到视频文件: {file_path}")
    
    return video_files


def main():
    """
    主函数：处理命令行参数并执行上传任务
    """
    parser = argparse.ArgumentParser(description='上传完整视频文件到TOS存储服务')
    parser.add_argument('data_dir', help='数据目录路径（如 data/002）')
    parser.add_argument('--bucket', default='rm-tos-001', help='TOS bucket名称')
    parser.add_argument('--prefix', help='TOS路径前缀（如 data002），默认从data_dir推导')
    
    args = parser.parse_args()
    
    # 从config.py获取TOS配置
    ak = IMAGE_TWO_CONFIG.get('access_key')
    sk = IMAGE_TWO_CONFIG.get('secret_key')
    endpoint = 'tos-cn-shanghai.volces.com'
    region = 'cn-shanghai'
    
    if not ak or not sk:
        print("❌ 请检查config.py中的IMAGE_TWO_CONFIG配置")
        return 1
    
    # 推导TOS路径前缀
    if args.prefix:
        tos_prefix = args.prefix
    else:
        # 从data_dir推导，如 data/002 -> data002
        dir_parts = Path(args.data_dir).parts
        if len(dir_parts) >= 2:
            tos_prefix = dir_parts[-2] + dir_parts[-1]  # data + 002 = data002
        else:
            tos_prefix = dir_parts[-1]
    
    print(f"TOS配置:")
    print(f"  Bucket: {args.bucket}")
    print(f"  路径前缀: {tos_prefix}")
    print(f"  Endpoint: {endpoint}")
    print(f"  Region: {region}")
    print()
    
    try:
        # 创建TOS客户端
        client = tos.TosClientV2(ak, sk, endpoint, region)
        
        # 查找所有complete_video.mp4文件
        video_files = find_complete_videos(args.data_dir)
        
        if not video_files:
            print("❌ 未找到任何complete_video.mp4文件")
            return 1
        
        print(f"\n找到 {len(video_files)} 个视频文件，开始上传...\n")
        
        # 上传每个视频文件
        success_count = 0
        for video_file in video_files:
            # 构建TOS对象键名
            file_name = Path(video_file).name
            object_key = f"{tos_prefix}/{file_name}"
            
            if upload_video_to_tos(video_file, args.bucket, object_key, client):
                success_count += 1
            print()  # 空行分隔
        
        print(f"上传完成: {success_count}/{len(video_files)} 个文件成功")
        
        if success_count == len(video_files):
            print("✓ 所有文件上传成功！")
            return 0
        else:
            print("⚠️ 部分文件上传失败")
            return 1
            
    except Exception as e:
        print(f"❌ 程序执行失败: {e}")
        return 1


if __name__ == '__main__':
    sys.exit(main())