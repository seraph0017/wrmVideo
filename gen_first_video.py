#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
生成第一个视频的脚本
遍历每个章节目录，使用每个章节的第一张和第二张图片生成视频
"""

import os
import sys
import time
import json
import base64
import uuid
import urllib.request
import subprocess
from volcenginesdkarkruntime import Ark

# 添加config目录到路径
config_dir = os.path.join(os.path.dirname(__file__), 'config')
sys.path.insert(0, config_dir)

# 导入配置
from config import ARK_CONFIG, IMAGE_TO_VIDEO_CONFIG

def create_video_from_single_image(image_path, duration, output_path):
    """
    使用单张图片生成视频
    
    Args:
        image_path: 图片路径
        duration: 视频时长
        output_path: 输出视频路径
    
    Returns:
        bool: 是否成功生成视频
    """
    try:
        print(f"开始生成视频: {image_path}")
        
        # 将图片转换为base64编码的data URL
        image_url = upload_image_to_server(image_path)
        
        if not image_url:
            print("图片处理失败")
            return False
        
        # 创建视频生成任务
        client = Ark(api_key=ARK_CONFIG["api_key"])
        
        resp = client.content_generation.tasks.create(
            model="doubao-seedance-1-0-lite-i2v-250428",
            content=[
                {
                    "type": "text",
                    "text": f"画面有轻微的动态效果，保持画面稳定 --ratio adaptive --dur {duration}"
                },
                {
                    "type": "image_url",
                    "image_url": {
                        "url": image_url
                    }
                }
            ]
        )
        
        task_id = resp.id
        print(f"视频生成任务创建成功，任务ID: {task_id}")
        
        # 等待任务完成
        max_wait_time = 300  # 最大等待5分钟
        wait_interval = 10   # 每10秒检查一次
        waited_time = 0
        
        while waited_time < max_wait_time:
            time.sleep(wait_interval)
            waited_time += wait_interval
            
            # 查询任务状态
            status_resp = client.content_generation.tasks.get(task_id=task_id)
            
            if status_resp.status == "succeeded":
                video_url = status_resp.content.video_url
                print(f"视频生成成功，下载URL: {video_url}")
                
                # 下载视频
                if download_video(video_url, output_path):
                    print(f"视频下载成功: {output_path}")
                    return True
                else:
                    print("视频下载失败")
                    return False
            elif status_resp.status == "failed":
                print(f"视频生成失败: {status_resp}")
                return False
            else:
                print(f"视频生成中... 状态: {status_resp.status}")
        
        print("视频生成超时")
        return False
        
    except Exception as e:
        print(f"生成视频时发生错误: {e}")
        return False

def merge_videos_with_ffmpeg(video1_path, video2_path, output_path):
    """
    使用ffmpeg合并两个视频，在转场处添加fuceng1.mov效果
    
    Args:
        video1_path: 第一个视频路径
        video2_path: 第二个视频路径
        output_path: 输出视频路径
    
    Returns:
        bool: 是否成功合并视频
    """
    try:
        import ffmpeg
        print(f"开始合并视频（带转场效果）: {video1_path} + {video2_path} -> {output_path}")
        
        # 定义fuceng1.mov文件路径
        banner_dir = os.path.join(os.path.dirname(os.path.abspath(__file__)), "src", "banner")
        fuceng_path = os.path.join(banner_dir, "fuceng1.mov")
        
        # 获取视频信息
        video1_info = ffmpeg.probe(video1_path)
        video2_info = ffmpeg.probe(video2_path)
        
        # 获取视频尺寸
        width = int(video1_info['streams'][0]['width'])
        height = int(video1_info['streams'][0]['height'])
        
        # 输入视频流
        video1_input = ffmpeg.input(video1_path)
        video2_input = ffmpeg.input(video2_path)
        
        # 检查fuceng1.mov是否存在并添加转场效果
        if os.path.exists(fuceng_path):
            print(f"添加转场效果: {fuceng_path}")
            
            # 获取转场视频的时长
            fuceng_info = ffmpeg.probe(fuceng_path)
            fuceng_duration = float(fuceng_info['streams'][0]['duration'])
            
            # 检查输入视频是否有音频流
            video1_has_audio = any(stream['codec_type'] == 'audio' for stream in video1_info['streams'])
            video2_has_audio = any(stream['codec_type'] == 'audio' for stream in video2_info['streams'])
            
            # 处理fuceng1.mov：缩放到视频尺寸并过滤暗色
            fuceng_input = ffmpeg.input(fuceng_path, an=None)  # 禁用音频流，只使用视频流
            fuceng_processed = (
                fuceng_input
                .filter('scale', width, height)  # 缩放到视频尺寸
                .filter('colorkey', color='0x000000', similarity=0.99, blend=0.0)  # 极致过滤纯黑
                .filter('colorkey', color='0x010101', similarity=0.95, blend=0.0)  # 过滤接近黑色
                .filter('colorkey', color='0x020202', similarity=0.9, blend=0.0)   # 过滤深灰色
                .filter('colorkey', color='0x030303', similarity=0.85, blend=0.0)  # 过滤更深灰色
                .filter('colorkey', color='0x040404', similarity=0.8, blend=0.0)   # 过滤暗灰色
                .filter('colorkey', color='0x050505', similarity=0.75, blend=0.0)  # 过滤深色调
                .filter('colorkey', color='0x0a0a0a', similarity=0.7, blend=0.0)   # 过滤极深色
            )
            
            # 将转场效果overlay到第二个视频的开头
            video2_with_transition = ffmpeg.filter([video2_input, fuceng_processed], 'overlay', 
                                                   x=0, y=0, enable=f'lt(t,{fuceng_duration})')  # 只在转场时长内显示
            
            # 如果输入视频有音频流，则处理音频；否则只处理视频
            if video1_has_audio and video2_has_audio:
                # 分别处理视频和音频流
                video1_v = video1_input.video
                video1_a = video1_input.audio
                video2_a = video2_input.audio
                
                # 拼接视频流和音频流
                concatenated_v = ffmpeg.concat(video1_v, video2_with_transition, v=1, a=0)
                concatenated_a = ffmpeg.concat(video1_a, video2_a, v=0, a=1)
                
                # 合并视频和音频流，添加关键帧设置确保与后续视频拼接兼容
                concatenated = ffmpeg.output(concatenated_v, concatenated_a, output_path, 
                                           vcodec='libx264', acodec='aac', r=30,
                                           **{'g': 30, 'keyint_min': 30})  # 设置关键帧间隔和帧率，每1秒一个关键帧
            else:
                # 只处理视频流
                video1_v = video1_input.video
                concatenated_v = ffmpeg.concat(video1_v, video2_with_transition, v=1, a=0)
                concatenated = ffmpeg.output(concatenated_v, output_path, 
                                           vcodec='libx264', r=30,
                                           **{'g': 30, 'keyint_min': 30})  # 设置关键帧间隔和帧率，每1秒一个关键帧
        else:
            print(f"警告: fuceng1.mov文件不存在: {fuceng_path}，使用普通拼接")
            # 如果转场文件不存在，使用普通拼接
            concatenated = ffmpeg.concat(video1_input, video2_input, v=1, a=1)
        
        # 输出最终视频
        if hasattr(concatenated, 'overwrite_output'):
            # 如果是带转场效果的输出对象
            (
                concatenated
                .overwrite_output()
                .run(quiet=False, capture_stdout=True, capture_stderr=True)
            )
        else:
            # 如果是普通的拼接流
            (
                concatenated
                .output(output_path, vcodec='libx264', acodec='aac', r=30,
                       **{'g': 30, 'keyint_min': 30})  # 设置关键帧间隔和帧率，每1秒一个关键帧
                .overwrite_output()
                .run(quiet=False, capture_stdout=True, capture_stderr=True)
            )
        
        print(f"视频合并成功: {output_path}")
        return True
            
    except Exception as e:
        print(f"合并视频时发生错误: {e}")
        if hasattr(e, 'stderr') and e.stderr:
            print(f"FFmpeg 错误详情: {e.stderr.decode('utf-8') if isinstance(e.stderr, bytes) else e.stderr}")
        # 如果ffmpeg方式失败，回退到原始方法
        try:
            print("回退到原始合并方法...")
            # 创建临时文件列表
            temp_list_file = output_path + ".temp_list.txt"
            with open(temp_list_file, 'w') as f:
                f.write(f"file '{os.path.abspath(video1_path)}'\n")
                f.write(f"file '{os.path.abspath(video2_path)}'\n")
            
            # 使用ffmpeg合并视频，添加关键帧设置确保与后续视频拼接兼容
            cmd = [
                'ffmpeg',
                '-f', 'concat',
                '-safe', '0',
                '-i', temp_list_file,
                '-c:v', 'libx264',  # 重新编码视频以设置关键帧
                '-c:a', 'aac',      # 重新编码音频
                '-r', '30',         # 帧率
                '-g', '30',         # 关键帧间隔
                '-keyint_min', '30', # 最小关键帧间隔
                '-y',  # 覆盖输出文件
                output_path
            ]
            
            result = subprocess.run(cmd, capture_output=True, text=True)
            
            # 删除临时文件
            if os.path.exists(temp_list_file):
                os.remove(temp_list_file)
            
            if result.returncode == 0:
                print(f"视频合并成功（原始方法）: {output_path}")
                return True
            else:
                print(f"视频合并失败: {result.stderr}")
                return False
        except Exception as fallback_e:
            print(f"回退方法也失败: {fallback_e}")
            return False

def create_video_from_images(first_image_path, second_image_path, duration, output_path):
    """
    使用两张图片生成视频（分别生成5秒视频然后合并）
    
    Args:
        first_image_path: 第一张图片路径
        second_image_path: 第二张图片路径
        duration: 视频时长（总时长，会平分给两个视频）
        output_path: 输出视频路径
    
    Returns:
        bool: 是否成功生成视频
    """
    try:
        print(f"开始生成视频: {first_image_path} + {second_image_path}")
        
        # 计算每个视频的时长（总时长的一半，但至少5秒）
        single_duration = max(5, duration // 2)
        
        # 生成临时视频文件路径
        temp_dir = os.path.dirname(output_path)
        base_name = os.path.splitext(os.path.basename(output_path))[0]
        
        temp_video1 = os.path.join(temp_dir, f"{base_name}_temp1.mp4")
        temp_video2 = os.path.join(temp_dir, f"{base_name}_temp2.mp4")
        
        # 生成第一个视频
        print("生成第一个视频...")
        if not create_video_from_single_image(first_image_path, single_duration, temp_video1):
            print("第一个视频生成失败")
            return False
        
        # 生成第二个视频
        print("生成第二个视频...")
        if not create_video_from_single_image(second_image_path, single_duration, temp_video2):
            print("第二个视频生成失败")
            # 清理第一个临时文件
            if os.path.exists(temp_video1):
                os.remove(temp_video1)
            return False
        
        # 合并两个视频
        print("合并视频...")
        success = merge_videos_with_ffmpeg(temp_video1, temp_video2, output_path)
        
        # 清理临时文件
        if os.path.exists(temp_video1):
            os.remove(temp_video1)
        if os.path.exists(temp_video2):
            os.remove(temp_video2)
        
        if success:
            print(f"视频生成完成: {output_path}")
            return True
        else:
            print("视频合并失败")
            return False
        
    except Exception as e:
        print(f"生成视频时发生错误: {e}")
        return False

def upload_image_to_server(image_path):
    """
    将图片转换为base64编码的data URL
    
    Args:
        image_path: 图片路径
    
    Returns:
        str: base64编码的data URL，失败返回None
    """
    try:
        print(f"处理图片: {image_path}")
        
        # 读取图片文件并转换为base64
        with open(image_path, 'rb') as image_file:
            image_data = image_file.read()
            base64_encoded = base64.b64encode(image_data).decode('utf-8')
        
        # 根据文件扩展名确定MIME类型
        file_ext = os.path.splitext(image_path)[1].lower()
        if file_ext in ['.jpg', '.jpeg']:
            mime_type = 'image/jpeg'
        elif file_ext == '.png':
            mime_type = 'image/png'
        elif file_ext == '.gif':
            mime_type = 'image/gif'
        elif file_ext == '.bmp':
            mime_type = 'image/bmp'
        else:
            mime_type = 'image/jpeg'  # 默认使用jpeg
        
        # 返回data URL格式
        data_url = f"data:{mime_type};base64,{base64_encoded}"
        print(f"图片转换成功: {os.path.basename(image_path)}")
        return data_url
        
    except Exception as e:
        print(f"处理图片时发生错误: {e}")
        return None

def download_video(video_url, output_path):
    """
    下载视频文件
    
    Args:
        video_url: 视频URL
        output_path: 输出路径
    
    Returns:
        bool: 是否下载成功
    """
    try:
        print(f"开始下载视频: {video_url}")
        urllib.request.urlretrieve(video_url, output_path)
        print(f"视频下载完成: {output_path}")
        return True
    except Exception as e:
        print(f"下载视频时发生错误: {e}")
        return False

def get_chapter_images(chapter_path):
    """
    获取章节目录中的前两张图片
    优先查找特定命名格式：chapter_XXX_image_01_1.jpeg 和 chapter_XXX_image_01_2.jpeg
    如果找不到，则回退到原来的逻辑
    
    Args:
        chapter_path: 章节目录路径
    
    Returns:
        tuple: (第一张图片路径, 第二张图片路径) 或 (None, None)
    """
    try:
        chapter_name = os.path.basename(chapter_path)
        
        # 优先查找特定命名格式的图片
        first_image_name = f"{chapter_name}_image_01_1.jpeg"
        second_image_name = f"{chapter_name}_image_01_2.jpeg"
        
        first_image_path = os.path.join(chapter_path, first_image_name)
        second_image_path = os.path.join(chapter_path, second_image_name)
        
        if os.path.exists(first_image_path) and os.path.exists(second_image_path):
            print(f"找到特定命名格式的图片: {first_image_name}, {second_image_name}")
            return first_image_path, second_image_path
        
        # 如果找不到特定命名格式，回退到原来的逻辑
        print(f"未找到特定命名格式的图片，使用通用查找方式")
        
        # 获取目录中的所有图片文件
        image_extensions = ['.jpg', '.jpeg', '.png', '.bmp', '.gif']
        image_files = []
        
        for file in os.listdir(chapter_path):
            if any(file.lower().endswith(ext) for ext in image_extensions):
                image_files.append(os.path.join(chapter_path, file))
        
        # 按文件名排序
        image_files.sort()
        
        if len(image_files) >= 2:
            return image_files[0], image_files[1]
        elif len(image_files) == 1:
            print(f"警告: 章节 {chapter_path} 只有一张图片，无法生成视频")
            return None, None
        else:
            print(f"警告: 章节 {chapter_path} 没有找到图片文件")
            return None, None
            
    except Exception as e:
        print(f"获取章节图片时发生错误: {e}")
        return None, None

def process_chapters(data_dir):
    """
    处理所有章节目录，为每个章节生成视频
    
    Args:
        data_dir: 数据目录路径
    """
    try:
        if not os.path.exists(data_dir):
            print(f"错误: 数据目录不存在: {data_dir}")
            return
        
        # 获取所有章节目录
        chapter_dirs = []
        for item in os.listdir(data_dir):
            item_path = os.path.join(data_dir, item)
            if os.path.isdir(item_path) and item.startswith('chapter'):
                chapter_dirs.append(item_path)
        
        # 按章节名称排序
        chapter_dirs.sort()
        
        if not chapter_dirs:
            print(f"警告: 在 {data_dir} 中没有找到章节目录")
            return
        
        print(f"找到 {len(chapter_dirs)} 个章节目录")
        
        # 处理每个章节
        for chapter_dir in chapter_dirs:
            chapter_name = os.path.basename(chapter_dir)
            print(f"\n处理章节: {chapter_name}")
            
            # 获取章节的前两张图片
            first_image, second_image = get_chapter_images(chapter_dir)
            
            if first_image and second_image:
                # 生成输出视频路径
                output_video = os.path.join(chapter_dir, f"{chapter_name}_first_video.mp4")
                
                # 生成视频（默认10秒时长）
                duration = 10
                success = create_video_from_images(first_image, second_image, duration, output_video)
                
                if success:
                    print(f"✓ 章节 {chapter_name} 视频生成成功: {output_video}")
                else:
                    print(f"✗ 章节 {chapter_name} 视频生成失败")
            else:
                print(f"✗ 章节 {chapter_name} 跳过，图片不足")
        
        print("\n所有章节处理完成")
        
    except Exception as e:
        print(f"处理章节时发生错误: {e}")

def main():
    """
    主函数
    """
    if len(sys.argv) == 2:
        # 原有的批量处理模式
        data_dir = sys.argv[1]
        print(f"开始处理数据目录: {data_dir}")
        print("注意: 请确保已正确配置 ARK_CONFIG 中的 api_key")
        
        # 检查配置
        if not ARK_CONFIG.get("api_key") or ARK_CONFIG["api_key"] == "your_api_key_here":
            print("警告: 请先在 config/config.py 中配置正确的 API 密钥")
            print("请编辑 config/config.py 文件，设置正确的 ARK_CONFIG['api_key']")
            sys.exit(1)
        
        process_chapters(data_dir)
    elif len(sys.argv) == 4:
        # 新的单个视频生成模式
        first_image_path = sys.argv[1]
        second_image_path = sys.argv[2]
        output_path = sys.argv[3]
        
        print(f"使用指定图片生成视频:")
        print(f"第一张图片: {first_image_path}")
        print(f"第二张图片: {second_image_path}")
        print(f"输出路径: {output_path}")
        print("注意: 请确保已正确配置 ARK_CONFIG 中的 api_key")
        
        # 检查配置
        if not ARK_CONFIG.get("api_key") or ARK_CONFIG["api_key"] == "your_api_key_here":
            print("警告: 请先在 config/config.py 中配置正确的 API 密钥")
            print("请编辑 config/config.py 文件，设置正确的 ARK_CONFIG['api_key']")
            sys.exit(1)
        
        # 检查图片文件是否存在
        if not os.path.exists(first_image_path):
            print(f"错误: 第一张图片不存在: {first_image_path}")
            sys.exit(1)
        
        if not os.path.exists(second_image_path):
            print(f"错误: 第二张图片不存在: {second_image_path}")
            sys.exit(1)
        
        # 创建输出目录（如果不存在）
        output_dir = os.path.dirname(output_path)
        if output_dir and not os.path.exists(output_dir):
            os.makedirs(output_dir, exist_ok=True)
        
        # 生成视频（默认10秒时长）
        duration = 10
        success = create_video_from_images(first_image_path, second_image_path, duration, output_path)
        
        if success:
            print(f"✓ 视频生成成功: {output_path}")
        else:
            print(f"✗ 视频生成失败")
            sys.exit(1)
    else:
        print("用法:")
        print("  批量处理模式: python gen_first_video.py <数据目录>")
        print("  示例: python gen_first_video.py data/002")
        print("")
        print("  单个视频生成模式: python gen_first_video.py <第一张图片> <第二张图片> <输出视频路径>")
        print("  示例: python gen_first_video.py data/003/chapter_001/chapter_001_image_01.jpeg data/003/chapter_001/chapter_001_image_02.jpeg output_video.mp4")
        sys.exit(1)

if __name__ == "__main__":
    main()