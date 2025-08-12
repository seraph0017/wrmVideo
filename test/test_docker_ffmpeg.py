#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Docker环境FFmpeg配置检测脚本
专门用于检测Docker容器中的FFmpeg和NVIDIA GPU配置
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

def check_docker_environment():
    """
    检查Docker环境
    
    Returns:
        bool: 是否在Docker环境中
    """
    print("=== 检查Docker环境 ===")
    
    # 检查/.dockerenv文件
    dockerenv_exists = os.path.exists('/.dockerenv')
    
    # 检查cgroup信息
    cgroup_docker = False
    try:
        with open('/proc/1/cgroup', 'r') as f:
            cgroup_content = f.read()
            cgroup_docker = 'docker' in cgroup_content or 'containerd' in cgroup_content
    except:
        pass
    
    # 检查容器相关环境变量
    container_env = any([
        os.environ.get('DOCKER_CONTAINER'),
        os.environ.get('KUBERNETES_SERVICE_HOST'),
        os.environ.get('container')
    ])
    
    is_docker = dockerenv_exists or cgroup_docker or container_env
    
    if is_docker:
        print("✓ 检测到Docker容器环境")
        if dockerenv_exists:
            print("  - 发现/.dockerenv文件")
        if cgroup_docker:
            print("  - cgroup显示容器环境")
        if container_env:
            print("  - 发现容器环境变量")
    else:
        print("❌ 未检测到Docker环境")
    
    return is_docker

def check_nvidia_docker_runtime():
    """
    检查NVIDIA Docker运行时
    
    Returns:
        dict: NVIDIA Docker支持情况
    """
    print("\n=== 检查NVIDIA Docker运行时 ===")
    
    results = {
        'nvidia_visible_devices': False,
        'cuda_visible_devices': False,
        'nvidia_driver_capabilities': False,
        'proc_nvidia': False,
        'dev_nvidia': False
    }
    
    # 检查NVIDIA_VISIBLE_DEVICES环境变量
    nvidia_visible = os.environ.get('NVIDIA_VISIBLE_DEVICES')
    if nvidia_visible and nvidia_visible != 'void':
        print(f"✓ NVIDIA_VISIBLE_DEVICES: {nvidia_visible}")
        results['nvidia_visible_devices'] = True
    else:
        print("❌ NVIDIA_VISIBLE_DEVICES未设置或为void")
    
    # 检查CUDA_VISIBLE_DEVICES环境变量
    cuda_visible = os.environ.get('CUDA_VISIBLE_DEVICES')
    if cuda_visible and cuda_visible != '':
        print(f"✓ CUDA_VISIBLE_DEVICES: {cuda_visible}")
        results['cuda_visible_devices'] = True
    else:
        print("❌ CUDA_VISIBLE_DEVICES未设置")
    
    # 检查NVIDIA_DRIVER_CAPABILITIES
    driver_caps = os.environ.get('NVIDIA_DRIVER_CAPABILITIES')
    if driver_caps:
        print(f"✓ NVIDIA_DRIVER_CAPABILITIES: {driver_caps}")
        results['nvidia_driver_capabilities'] = True
        if 'video' not in driver_caps:
            print("  ⚠️  警告: 未包含'video'能力，可能影响NVENC")
    else:
        print("❌ NVIDIA_DRIVER_CAPABILITIES未设置")
    
    # 检查/proc/driver/nvidia/version
    if os.path.exists('/proc/driver/nvidia/version'):
        print("✓ 发现/proc/driver/nvidia/version")
        results['proc_nvidia'] = True
        try:
            with open('/proc/driver/nvidia/version', 'r') as f:
                version_info = f.read().strip()
                print(f"  驱动版本: {version_info}")
        except:
            pass
    else:
        print("❌ 未找到/proc/driver/nvidia/version")
    
    # 检查/dev/nvidia*设备
    nvidia_devices = [f for f in os.listdir('/dev') if f.startswith('nvidia')] if os.path.exists('/dev') else []
    if nvidia_devices:
        print(f"✓ 发现NVIDIA设备: {', '.join(nvidia_devices)}")
        results['dev_nvidia'] = True
    else:
        print("❌ 未找到NVIDIA设备文件")
    
    return results

def check_ffmpeg_in_docker():
    """
    检查Docker中的FFmpeg配置
    
    Returns:
        bool: FFmpeg是否可用
    """
    print("\n=== 检查Docker中的FFmpeg ===")
    
    # 检查FFmpeg版本
    returncode, stdout, stderr = run_command(['ffmpeg', '-version'])
    if returncode != 0:
        print(f"❌ FFmpeg不可用: {stderr}")
        return False
    
    # 提取版本信息
    lines = stdout.split('\n')
    version_line = lines[0] if lines else "未知版本"
    print(f"✓ {version_line}")
    
    # 检查编译配置
    config_line = next((line for line in lines if 'configuration:' in line), None)
    if config_line:
        if '--enable-nvenc' in config_line:
            print("✓ FFmpeg编译时启用了NVENC支持")
        else:
            print("⚠️  FFmpeg编译时可能未启用NVENC支持")
        
        if '--enable-cuda' in config_line:
            print("✓ FFmpeg编译时启用了CUDA支持")
        else:
            print("⚠️  FFmpeg编译时可能未启用CUDA支持")
    
    return True

def test_docker_nvenc():
    """
    在Docker环境中测试NVENC编码器
    
    Returns:
        bool: NVENC是否可用
    """
    print("\n=== 测试Docker中的NVENC编码器 ===")
    
    # 创建测试命令
    test_cmd = [
        'ffmpeg', '-f', 'lavfi', '-i', 'testsrc=duration=1:size=320x240:rate=1',
        '-c:v', 'h264_nvenc', '-f', 'null', '-'
    ]
    
    returncode, stdout, stderr = run_command(test_cmd, timeout=20)
    
    if returncode == 0:
        print("✓ Docker中NVENC编码器测试成功")
        return True
    else:
        print(f"❌ Docker中NVENC编码器测试失败")
        print(f"错误信息: {stderr}")
        
        # 分析常见错误
        if 'No NVENC capable devices found' in stderr:
            print("  原因: 未找到支持NVENC的设备")
        elif 'Cannot load nvcuda.dll' in stderr or 'cannot open shared object file' in stderr:
            print("  原因: CUDA库未正确加载")
        elif 'Driver does not support NVENC' in stderr:
            print("  原因: 驱动不支持NVENC")
        
        return False

def generate_docker_recommendations(docker_env, nvidia_runtime, ffmpeg_ok, nvenc_works):
    """
    生成Docker环境配置建议
    
    Args:
        docker_env: 是否在Docker环境
        nvidia_runtime: NVIDIA运行时检测结果
        ffmpeg_ok: FFmpeg是否可用
        nvenc_works: NVENC是否工作
    """
    print("\n=== Docker环境配置建议 ===")
    
    if not docker_env:
        print("❌ 未检测到Docker环境，此脚本专用于Docker容器")
        return
    
    if not ffmpeg_ok:
        print("❌ FFmpeg不可用，请确保Docker镜像包含FFmpeg")
        return
    
    # NVIDIA GPU配置建议
    if nvenc_works:
        print("✅ Docker中NVIDIA GPU硬件加速配置完美")
        print("   可以使用h264_nvenc进行硬件编码")
    else:
        print("⚠️  Docker中NVIDIA GPU配置需要改进")
        
        if not nvidia_runtime['nvidia_visible_devices']:
            print("   建议: 启动容器时设置 --gpus all 或 -e NVIDIA_VISIBLE_DEVICES=all")
        
        if not nvidia_runtime['nvidia_driver_capabilities']:
            print("   建议: 设置 -e NVIDIA_DRIVER_CAPABILITIES=compute,video,utility")
        
        if not nvidia_runtime['proc_nvidia']:
            print("   建议: 确保宿主机安装了NVIDIA驱动")
        
        if not nvidia_runtime['dev_nvidia']:
            print("   建议: 确保容器可以访问NVIDIA设备文件")
    
    # Docker运行命令建议
    print("\n=== 推荐的Docker运行命令 ===")
    print("# 使用NVIDIA GPU的完整命令:")
    print("docker run --gpus all \\")
    print("  -e NVIDIA_VISIBLE_DEVICES=all \\")
    print("  -e NVIDIA_DRIVER_CAPABILITIES=compute,video,utility \\")
    print("  -v /path/to/your/project:/workspace \\")
    print("  your-ffmpeg-image:latest")
    
    print("\n# 或使用nvidia-docker (旧版本):")
    print("nvidia-docker run \\")
    print("  -v /path/to/your/project:/workspace \\")
    print("  your-ffmpeg-image:latest")

def main():
    """
    主函数
    """
    print("Docker环境FFmpeg配置检测")
    print("=" * 50)
    
    # 检查Docker环境
    docker_env = check_docker_environment()
    
    # 检查NVIDIA Docker运行时
    nvidia_runtime = check_nvidia_docker_runtime()
    
    # 检查FFmpeg
    ffmpeg_ok = check_ffmpeg_in_docker()
    
    # 测试NVENC
    nvenc_works = False
    if ffmpeg_ok:
        nvenc_works = test_docker_nvenc()
    
    # 生成建议
    generate_docker_recommendations(docker_env, nvidia_runtime, ffmpeg_ok, nvenc_works)
    
    # 总结
    print("\n=== 检测总结 ===")
    if docker_env and ffmpeg_ok and nvenc_works:
        print("🚀 Docker环境配置完美，支持NVIDIA GPU硬件加速")
    elif docker_env and ffmpeg_ok:
        print("✅ Docker环境基本配置正常，但GPU加速需要调整")
    elif docker_env:
        print("⚠️  Docker环境检测到，但FFmpeg配置有问题")
    else:
        print("❌ 未检测到Docker环境或配置有严重问题")

if __name__ == "__main__":
    main()