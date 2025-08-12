#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Docker环境FFmpeg配置检测脚本
专门用于检测Docker容器中的FFmpeg和NVIDIA GPU配置

使用方法:
    python test_docker_ffmpeg.py              # 检测当前环境
    python test_docker_ffmpeg.py --test-run   # 测试Docker运行命令
    python test_docker_ffmpeg.py --help       # 显示帮助信息
"""

import subprocess
import sys
import os
import argparse

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

def test_docker_run_command():
    """
    测试Docker运行命令是否可用
    
    Returns:
        dict: 测试结果
    """
    print("\n=== 测试Docker运行命令 ===")
    
    results = {
        'docker_available': False,
        'nvidia_docker_available': False,
        'gpu_support': False
    }
    
    # 测试基本docker命令
    print("检查Docker是否可用...")
    returncode, stdout, stderr = run_command(['docker', '--version'])
    if returncode == 0:
        results['docker_available'] = True
        print(f"✓ Docker可用: {stdout.strip()}")
    else:
        print(f"❌ Docker不可用: {stderr}")
        return results
    
    # 测试nvidia-docker运行时
    print("\n检查NVIDIA Docker运行时...")
    test_cmd = [
        'docker', 'run', '--rm', '--gpus', 'all',
        'nvidia/cuda:11.0-base', 'nvidia-smi'
    ]
    
    returncode, stdout, stderr = run_command(test_cmd, timeout=30)
    if returncode == 0:
        results['nvidia_docker_available'] = True
        results['gpu_support'] = True
        print("✓ NVIDIA Docker运行时可用")
        print("✓ GPU设备可以正常访问")
        # 显示GPU信息的前几行
        gpu_lines = stdout.split('\n')[:5]
        for line in gpu_lines:
            if line.strip():
                print(f"   {line}")
    else:
        print(f"❌ NVIDIA Docker运行时测试失败: {stderr}")
        
        # 尝试不使用GPU的基本测试
        basic_test_cmd = ['docker', 'run', '--rm', 'hello-world']
        returncode, stdout, stderr = run_command(basic_test_cmd, timeout=15)
        if returncode == 0:
            print("✓ 基本Docker功能正常")
        else:
            print(f"❌ 基本Docker功能也有问题: {stderr}")
    
    return results

def test_ffmpeg_docker_command(image_name="jrottenberg/ffmpeg:latest"):
    """
    测试FFmpeg Docker镜像是否可用
    
    Args:
        image_name: FFmpeg Docker镜像名称
    
    Returns:
        bool: 是否可用
    """
    print(f"\n=== 测试FFmpeg Docker镜像 ({image_name}) ===")
    
    # 测试FFmpeg版本
    test_cmd = [
        'docker', 'run', '--rm', image_name,
        'ffmpeg', '-version'
    ]
    
    returncode, stdout, stderr = run_command(test_cmd, timeout=20)
    if returncode == 0:
        # 提取版本信息
        lines = stdout.split('\n')
        version_line = lines[0] if lines else "未知版本"
        print(f"✓ FFmpeg Docker镜像可用: {version_line}")
        
        # 检查NVENC支持
        if 'enable-nvenc' in stdout:
            print("✓ 镜像支持NVENC编码器")
        else:
            print("⚠️  镜像可能不支持NVENC编码器")
        
        return True
    else:
        print(f"❌ FFmpeg Docker镜像测试失败: {stderr}")
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
    print("  -w /workspace \\")
    print("  your-ffmpeg-image:latest")
    
    print("\n# 或使用nvidia-docker (旧版本):")
    print("nvidia-docker run \\")
    print("  -v /path/to/your/project:/workspace \\")
    print("  -w /workspace \\")
    print("  your-ffmpeg-image:latest")
    
    print("\n# 测试命令示例:")
    print("docker run --gpus all --rm \\")
    print("  -e NVIDIA_VISIBLE_DEVICES=all \\")
    print("  -e NVIDIA_DRIVER_CAPABILITIES=compute,video,utility \\")
    print("  jrottenberg/ffmpeg:latest \\")
    print("  ffmpeg -f lavfi -i testsrc=duration=1:size=320x240:rate=1 -c:v h264_nvenc -f null -")

def parse_arguments():
    """
    解析命令行参数
    
    Returns:
        argparse.Namespace: 解析后的参数
    """
    parser = argparse.ArgumentParser(
        description='Docker环境FFmpeg配置检测脚本',
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
示例用法:
  python test_docker_ffmpeg.py                    # 检测当前环境
  python test_docker_ffmpeg.py --test-run         # 测试Docker运行命令
  python test_docker_ffmpeg.py --test-run --image jrottenberg/ffmpeg:latest
        """
    )
    
    parser.add_argument(
        '--test-run', 
        action='store_true',
        help='测试Docker运行命令（在宿主机上运行）'
    )
    
    parser.add_argument(
        '--image',
        default='jrottenberg/ffmpeg:latest',
        help='指定要测试的FFmpeg Docker镜像（默认: jrottenberg/ffmpeg:latest）'
    )
    
    parser.add_argument(
        '--skip-pull',
        action='store_true',
        help='跳过Docker镜像拉取，使用本地镜像'
    )
    
    return parser.parse_args()

def main():
    """
    主函数
    """
    args = parse_arguments()
    
    print("Docker环境FFmpeg配置检测")
    print("=" * 50)
    
    if args.test_run:
        # 强制测试Docker运行命令模式
        print("\n=== 测试Docker运行命令模式 ===")
        docker_test_results = test_docker_run_command()
        
        # 测试指定的FFmpeg Docker镜像
        if docker_test_results['docker_available']:
            test_ffmpeg_docker_command(args.image)
        
        # 生成Docker运行建议
        print("\n=== Docker运行建议 ===")
        if docker_test_results['nvidia_docker_available']:
            print("🚀 推荐使用GPU加速的Docker命令:")
            print(f"docker run --gpus all --rm \\")
            print(f"  -e NVIDIA_VISIBLE_DEVICES=all \\")
            print(f"  -e NVIDIA_DRIVER_CAPABILITIES=compute,video,utility \\")
            print(f"  -v $(pwd):/workspace \\")
            print(f"  -w /workspace \\")
            print(f"  {args.image}")
        elif docker_test_results['docker_available']:
            print("✅ 推荐使用CPU的Docker命令:")
            print(f"docker run --rm \\")
            print(f"  -v $(pwd):/workspace \\")
            print(f"  -w /workspace \\")
            print(f"  {args.image}")
        
        return
    
    # 检查Docker环境
    docker_env = check_docker_environment()
    
    # 如果不在Docker环境中，提示使用--test-run参数
    docker_test_results = None
    if not docker_env:
        print("\n当前不在Docker容器中。")
        print("提示: 使用 --test-run 参数可以测试Docker运行命令")
        print("例如: python test_docker_ffmpeg.py --test-run")
        return
    
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
    if docker_env:
        if ffmpeg_ok and nvenc_works:
            print("🚀 Docker环境配置完美，支持NVIDIA GPU硬件加速")
        elif ffmpeg_ok:
            print("✅ Docker环境基本配置正常，但GPU加速需要调整")
        else:
            print("⚠️  Docker环境检测到，但FFmpeg配置有问题")
    else:
        print("❌ 未检测到Docker环境或配置有严重问题")

if __name__ == "__main__":
    main()