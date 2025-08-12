#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
线上服务器FFmpeg配置检测脚本
检查FFmpeg是否支持所需的编码器和功能
"""

import subprocess
import sys
import os

def run_command(cmd, timeout=10):
    """
    执行命令并返回结果
    
    Args:
        cmd: 命令列表
        timeout: 超时时间（秒）
    
    Returns:
        tuple: (returncode, stdout, stderr)
    """
    try:
        result = subprocess.run(cmd, capture_output=True, text=True, timeout=timeout)
        return result.returncode, result.stdout, result.stderr
    except subprocess.TimeoutExpired:
        return -1, "", "命令执行超时"
    except FileNotFoundError:
        return -1, "", "命令未找到"
    except Exception as e:
        return -1, "", str(e)

def check_ffmpeg_version():
    """
    检查FFmpeg版本
    
    Returns:
        bool: 是否成功检测到FFmpeg
    """
    print("=== 检查FFmpeg版本 ===")
    returncode, stdout, stderr = run_command(['ffmpeg', '-version'])
    
    if returncode != 0:
        print(f"❌ FFmpeg未安装或不可用: {stderr}")
        return False
    
    # 提取版本信息
    lines = stdout.split('\n')
    version_line = lines[0] if lines else "未知版本"
    print(f"✓ {version_line}")
    
    # 检查配置信息
    config_line = next((line for line in lines if 'configuration:' in line), None)
    if config_line:
        print(f"配置: {config_line[:100]}...")
    
    return True

def check_nvidia_gpu():
    """
    检查NVIDIA GPU支持
    
    Returns:
        bool: 是否支持NVIDIA GPU
    """
    print("\n=== 检查NVIDIA GPU支持 ===")
    
    # 检查nvidia-smi
    returncode, stdout, stderr = run_command(['nvidia-smi'])
    if returncode != 0:
        print("❌ 未检测到NVIDIA GPU或驱动")
        return False
    
    print("✓ 检测到NVIDIA GPU")
    # 显示GPU信息的第一行
    lines = stdout.split('\n')
    gpu_info = next((line for line in lines if 'NVIDIA' in line and 'Driver Version' in line), None)
    if gpu_info:
        print(f"GPU信息: {gpu_info.strip()}")
    
    return True

def check_encoders():
    """
    检查FFmpeg编码器支持
    
    Returns:
        dict: 编码器支持情况
    """
    print("\n=== 检查编码器支持 ===")
    
    # 获取所有编码器
    returncode, stdout, stderr = run_command(['ffmpeg', '-encoders'])
    if returncode != 0:
        print(f"❌ 无法获取编码器列表: {stderr}")
        return {}
    
    encoders = stdout.lower()
    
    # 检查关键编码器
    encoder_checks = {
        'h264_nvenc': 'NVIDIA H.264 硬件编码器',
        'hevc_nvenc': 'NVIDIA H.265 硬件编码器', 
        'h264_videotoolbox': 'Apple H.264 硬件编码器',
        'hevc_videotoolbox': 'Apple H.265 硬件编码器',
        'libx264': 'x264 软件编码器',
        'libx265': 'x265 软件编码器',
        'aac': 'AAC 音频编码器',
        'libmp3lame': 'MP3 音频编码器'
    }
    
    results = {}
    for encoder, description in encoder_checks.items():
        if encoder in encoders:
            print(f"✓ {description}: {encoder}")
            results[encoder] = True
        else:
            print(f"❌ {description}: {encoder} (不支持)")
            results[encoder] = False
    
    return results

def check_filters():
    """
    检查FFmpeg滤镜支持
    
    Returns:
        dict: 滤镜支持情况
    """
    print("\n=== 检查滤镜支持 ===")
    
    # 获取所有滤镜
    returncode, stdout, stderr = run_command(['ffmpeg', '-filters'])
    if returncode != 0:
        print(f"❌ 无法获取滤镜列表: {stderr}")
        return {}
    
    filters = stdout.lower()
    
    # 检查关键滤镜
    filter_checks = {
        'subtitles': '字幕滤镜',
        'overlay': '叠加滤镜',
        'scale': '缩放滤镜',
        'crop': '裁剪滤镜',
        'colorkey': '色键滤镜',
        'amix': '音频混合滤镜',
        'adelay': '音频延迟滤镜',
        'volume': '音量调节滤镜'
    }
    
    results = {}
    for filter_name, description in filter_checks.items():
        if filter_name in filters:
            print(f"✓ {description}: {filter_name}")
            results[filter_name] = True
        else:
            print(f"❌ {description}: {filter_name} (不支持)")
            results[filter_name] = False
    
    return results

def test_nvenc_encoding():
    """
    测试NVENC编码器是否实际可用
    
    Returns:
        bool: NVENC是否可用
    """
    print("\n=== 测试NVENC编码器 ===")
    
    # 创建测试命令
    test_cmd = [
        'ffmpeg', '-f', 'lavfi', '-i', 'testsrc=duration=1:size=320x240:rate=1',
        '-c:v', 'h264_nvenc', '-f', 'null', '-'
    ]
    
    returncode, stdout, stderr = run_command(test_cmd, timeout=15)
    
    if returncode == 0:
        print("✓ NVENC编码器测试成功")
        return True
    else:
        print(f"❌ NVENC编码器测试失败: {stderr}")
        return False

def test_cpu_encoding():
    """
    测试CPU编码器是否可用
    
    Returns:
        bool: CPU编码器是否可用
    """
    print("\n=== 测试CPU编码器 ===")
    
    # 创建测试命令
    test_cmd = [
        'ffmpeg', '-f', 'lavfi', '-i', 'testsrc=duration=1:size=320x240:rate=1',
        '-c:v', 'libx264', '-preset', 'ultrafast', '-f', 'null', '-'
    ]
    
    returncode, stdout, stderr = run_command(test_cmd, timeout=15)
    
    if returncode == 0:
        print("✓ CPU编码器测试成功")
        return True
    else:
        print(f"❌ CPU编码器测试失败: {stderr}")
        return False

def generate_recommendations(encoder_results, filter_results, gpu_available, nvenc_works):
    """
    生成配置建议
    
    Args:
        encoder_results: 编码器检测结果
        filter_results: 滤镜检测结果
        gpu_available: GPU是否可用
        nvenc_works: NVENC是否工作
    """
    print("\n=== 配置建议 ===")
    
    # 检查必需的编码器
    required_encoders = ['libx264', 'aac']
    missing_required = [enc for enc in required_encoders if not encoder_results.get(enc, False)]
    
    if missing_required:
        print(f"❌ 缺少必需的编码器: {', '.join(missing_required)}")
        print("   建议重新编译FFmpeg并启用这些编码器")
    else:
        print("✓ 所有必需的编码器都可用")
    
    # 检查必需的滤镜
    required_filters = ['subtitles', 'overlay', 'scale', 'amix']
    missing_filters = [flt for flt in required_filters if not filter_results.get(flt, False)]
    
    if missing_filters:
        print(f"❌ 缺少必需的滤镜: {', '.join(missing_filters)}")
        print("   建议重新编译FFmpeg并启用这些滤镜")
    else:
        print("✓ 所有必需的滤镜都可用")
    
    # GPU编码建议
    if gpu_available and nvenc_works:
        print("✓ 推荐使用NVIDIA GPU硬件加速编码")
        print("   编码器: h264_nvenc")
        print("   硬件加速: -hwaccel cuda")
    elif gpu_available and not nvenc_works:
        print("⚠️  检测到NVIDIA GPU但NVENC不可用")
        print("   可能需要更新驱动或重新编译FFmpeg")
        print("   当前将使用CPU编码")
    else:
        print("ℹ️  未检测到NVIDIA GPU，将使用CPU编码")
        print("   编码器: libx264")
        print("   建议使用较快的预设: -preset fast")
    
    # 性能优化建议
    print("\n=== 性能优化建议 ===")
    if gpu_available and nvenc_works:
        print("- 使用NVENC预设: -preset p2 (faster)")
        print("- 使用低延迟调优: -tune ll")
        print("- 减少前瞻帧: -rc-lookahead 8")
    else:
        print("- 使用快速CPU预设: -preset fast")
        print("- 限制参考帧: -refs 2")
        print("- 使用快速运动估计: -me_method hex")

def main():
    """
    主函数
    """
    print("线上服务器FFmpeg配置检测")
    print("=" * 50)
    
    # 检查FFmpeg
    if not check_ffmpeg_version():
        print("\n❌ FFmpeg检测失败，请先安装FFmpeg")
        sys.exit(1)
    
    # 检查GPU
    gpu_available = check_nvidia_gpu()
    
    # 检查编码器
    encoder_results = check_encoders()
    
    # 检查滤镜
    filter_results = check_filters()
    
    # 测试编码器
    nvenc_works = False
    if gpu_available and encoder_results.get('h264_nvenc', False):
        nvenc_works = test_nvenc_encoding()
    
    cpu_works = test_cpu_encoding()
    
    # 生成建议
    generate_recommendations(encoder_results, filter_results, gpu_available, nvenc_works)
    
    # 总结
    print("\n=== 检测总结 ===")
    if nvenc_works:
        print("🚀 服务器配置优秀，支持NVIDIA GPU硬件加速")
    elif cpu_works:
        print("✅ 服务器配置良好，支持CPU编码")
    else:
        print("❌ 服务器配置有问题，编码器不可用")
        sys.exit(1)

if __name__ == "__main__":
    main()