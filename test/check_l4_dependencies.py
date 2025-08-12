#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
L4 GPU环境依赖检查脚本
快速检查gen_video.py运行所需的所有依赖

使用方法:
    python test/check_l4_dependencies.py
    python test/check_l4_dependencies.py --verbose
"""

import os
import sys
import subprocess
import argparse
from pathlib import Path

def run_command(cmd, timeout=10):
    """
    执行命令并返回结果
    
    Args:
        cmd: 命令列表或字符串
        timeout: 超时时间（秒）
    
    Returns:
        tuple: (returncode, stdout, stderr)
    """
    try:
        if isinstance(cmd, str):
            cmd = cmd.split()
        result = subprocess.run(cmd, capture_output=True, text=True, timeout=timeout)
        return result.returncode, result.stdout, result.stderr
    except subprocess.TimeoutExpired:
        return -1, "", "命令执行超时"
    except FileNotFoundError:
        return -1, "", "命令未找到"
    except Exception as e:
        return -1, "", str(e)

def check_system_info():
    """
    检查系统基本信息
    
    Returns:
        dict: 系统信息检查结果
    """
    print("=== 系统环境检查 ===")
    results = {}
    
    # 检查操作系统
    try:
        with open('/etc/os-release', 'r') as f:
            os_info = f.read()
            if 'Ubuntu' in os_info:
                results['os'] = 'Ubuntu'
                print("✓ 操作系统: Ubuntu")
            elif 'CentOS' in os_info:
                results['os'] = 'CentOS'
                print("✓ 操作系统: CentOS")
            else:
                results['os'] = 'Other'
                print("⚠️  操作系统: 其他Linux发行版")
    except:
        results['os'] = 'Unknown'
        print("❌ 无法检测操作系统")
    
    # 检查Python版本
    python_version = sys.version_info
    if python_version >= (3, 8):
        results['python'] = True
        print(f"✓ Python版本: {python_version.major}.{python_version.minor}.{python_version.micro}")
    else:
        results['python'] = False
        print(f"❌ Python版本过低: {python_version.major}.{python_version.minor}.{python_version.micro} (需要3.8+)")
    
    return results

def check_nvidia_gpu():
    """
    检查NVIDIA GPU和驱动
    
    Returns:
        dict: GPU检查结果
    """
    print("\n=== NVIDIA GPU检查 ===")
    results = {}
    
    # 检查nvidia-smi
    returncode, stdout, stderr = run_command(['nvidia-smi'])
    if returncode == 0:
        results['nvidia_smi'] = True
        print("✓ nvidia-smi 可用")
        
        # 检查是否为L4 GPU
        if 'L4' in stdout:
            results['is_l4'] = True
            print("✓ 检测到NVIDIA L4 GPU")
        else:
            results['is_l4'] = False
            print("⚠️  未检测到L4 GPU，检测到其他NVIDIA GPU")
        
        # 提取驱动版本
        lines = stdout.split('\n')
        for line in lines:
            if 'Driver Version:' in line:
                driver_version = line.split('Driver Version:')[1].split()[0]
                results['driver_version'] = driver_version
                print(f"✓ NVIDIA驱动版本: {driver_version}")
                break
    else:
        results['nvidia_smi'] = False
        results['is_l4'] = False
        print("❌ nvidia-smi 不可用")
        print(f"   错误: {stderr}")
    
    return results

def check_cuda():
    """
    检查CUDA环境
    
    Returns:
        dict: CUDA检查结果
    """
    print("\n=== CUDA环境检查 ===")
    results = {}
    
    # 检查nvcc
    returncode, stdout, stderr = run_command(['nvcc', '--version'])
    if returncode == 0:
        results['nvcc'] = True
        # 提取CUDA版本
        for line in stdout.split('\n'):
            if 'release' in line:
                cuda_version = line.split('release')[1].split(',')[0].strip()
                results['cuda_version'] = cuda_version
                print(f"✓ CUDA版本: {cuda_version}")
                break
    else:
        results['nvcc'] = False
        print("❌ nvcc 不可用")
        print("   请安装CUDA Toolkit")
    
    # 检查CUDA环境变量
    cuda_home = os.environ.get('CUDA_HOME') or os.environ.get('CUDA_PATH')
    if cuda_home:
        results['cuda_env'] = True
        print(f"✓ CUDA_HOME: {cuda_home}")
    else:
        results['cuda_env'] = False
        print("⚠️  CUDA_HOME 环境变量未设置")
    
    return results

def check_ffmpeg():
    """
    检查FFmpeg和NVENC支持
    
    Returns:
        dict: FFmpeg检查结果
    """
    print("\n=== FFmpeg检查 ===")
    results = {}
    
    # 检查FFmpeg是否安装
    returncode, stdout, stderr = run_command(['ffmpeg', '-version'])
    if returncode == 0:
        results['ffmpeg'] = True
        # 提取FFmpeg版本
        first_line = stdout.split('\n')[0]
        if 'ffmpeg version' in first_line:
            version = first_line.split('ffmpeg version')[1].split()[0]
            results['ffmpeg_version'] = version
            print(f"✓ FFmpeg版本: {version}")
    else:
        results['ffmpeg'] = False
        print("❌ FFmpeg 未安装")
        return results
    
    # 检查NVENC编码器
    returncode, stdout, stderr = run_command(['ffmpeg', '-encoders'])
    if returncode == 0:
        if 'h264_nvenc' in stdout:
            results['h264_nvenc'] = True
            print("✓ h264_nvenc 编码器可用")
        else:
            results['h264_nvenc'] = False
            print("❌ h264_nvenc 编码器不可用")
        
        if 'hevc_nvenc' in stdout:
            results['hevc_nvenc'] = True
            print("✓ hevc_nvenc 编码器可用")
        else:
            results['hevc_nvenc'] = False
            print("⚠️  hevc_nvenc 编码器不可用")
    
    # 检查CUDA支持
    if '--enable-cuda' in stdout or 'cuda' in stdout.lower():
        results['cuda_support'] = True
        print("✓ FFmpeg CUDA支持已启用")
    else:
        results['cuda_support'] = False
        print("❌ FFmpeg CUDA支持未启用")
    
    return results

def check_python_packages():
    """
    检查Python包依赖
    
    Returns:
        dict: Python包检查结果
    """
    print("\n=== Python包依赖检查 ===")
    results = {}
    
    required_packages = {
        'requests': 'requests',
        'volcengine': 'volcengine-python-sdk',
        'ffmpeg': 'ffmpeg-python',
        'jinja2': 'jinja2',
        'PIL': 'Pillow',
        'moviepy': 'moviepy',
        'numpy': 'numpy',
        'jieba': 'jieba',
        'yaml': 'PyYAML',
        'aiofiles': 'aiofiles'
    }
    
    for package, pip_name in required_packages.items():
        try:
            __import__(package)
            results[package] = True
            print(f"✓ {pip_name}")
        except ImportError:
            results[package] = False
            print(f"❌ {pip_name} 未安装")
    
    return results

def check_project_structure():
    """
    检查项目目录结构
    
    Returns:
        dict: 项目结构检查结果
    """
    print("\n=== 项目结构检查 ===")
    results = {}
    
    project_root = Path(__file__).parent.parent
    
    required_dirs = {
        'src': 'src',
        'src/banner': 'src/banner',
        'src/bgm': 'src/bgm',
        'src/sound_effects': 'src/sound_effects',
        'Character_Images': 'Character_Images',
        'config': 'config',
        'data': 'data'
    }
    
    for key, dir_path in required_dirs.items():
        full_path = project_root / dir_path
        if full_path.exists():
            results[key] = True
            print(f"✓ {dir_path}/")
        else:
            results[key] = False
            print(f"❌ {dir_path}/ 目录不存在")
    
    # 检查关键文件
    required_files = {
        'finish_video': 'src/banner/finish.mp4',
        'transition': 'src/banner/fuceng1.mov',
        'config_file': 'config/config.py',
        'prompt_config': 'config/prompt_config.py'
    }
    
    for key, file_path in required_files.items():
        full_path = project_root / file_path
        if full_path.exists():
            results[key] = True
            print(f"✓ {file_path}")
        else:
            results[key] = False
            print(f"❌ {file_path} 文件不存在")
    
    return results

def check_api_config():
    """
    检查API配置
    
    Returns:
        dict: API配置检查结果
    """
    print("\n=== API配置检查 ===")
    results = {}
    
    # 检查环境变量
    env_vars = {
        'ARK_API_KEY': 'ARK API密钥',
        'VOLC_ACCESS_KEY': '火山引擎Access Key',
        'VOLC_SECRET_KEY': '火山引擎Secret Key'
    }
    
    for var, desc in env_vars.items():
        if os.environ.get(var):
            results[var] = True
            print(f"✓ {desc} (环境变量)")
        else:
            results[var] = False
            print(f"⚠️  {desc} 环境变量未设置")
    
    # 检查配置文件
    try:
        sys.path.insert(0, str(Path(__file__).parent.parent))
        from config.config import ARK_CONFIG, TTS_CONFIG, IMAGE_TWO_CONFIG
        
        if ARK_CONFIG.get('api_key'):
            results['ark_config'] = True
            print("✓ ARK配置文件")
        else:
            results['ark_config'] = False
            print("❌ ARK配置文件缺少api_key")
        
        if TTS_CONFIG.get('access_key') and TTS_CONFIG.get('secret_key'):
            results['tts_config'] = True
            print("✓ TTS配置文件")
        else:
            results['tts_config'] = False
            print("❌ TTS配置文件缺少密钥")
        
        if IMAGE_TWO_CONFIG.get('access_key') and IMAGE_TWO_CONFIG.get('secret_key'):
            results['image_config'] = True
            print("✓ 图片生成配置文件")
        else:
            results['image_config'] = False
            print("❌ 图片生成配置文件缺少密钥")
    
    except ImportError as e:
        results['config_import'] = False
        print(f"❌ 无法导入配置文件: {e}")
    
    return results

def test_l4_performance():
    """
    测试L4 GPU性能
    
    Returns:
        dict: 性能测试结果
    """
    print("\n=== L4 GPU性能测试 ===")
    results = {}
    
    # 测试NVENC编码
    test_cmd = [
        'ffmpeg', '-f', 'lavfi', '-i', 'testsrc2=duration=5:size=1280x720:rate=30',
        '-c:v', 'h264_nvenc', '-preset', 'p4', '-rc', 'vbr', '-cq', '23',
        '-spatial_aq', '1', '-temporal_aq', '1', '-rc-lookahead', '20',
        '-y', '/tmp/test_l4_nvenc.mp4'
    ]
    
    print("正在测试NVENC编码性能...")
    returncode, stdout, stderr = run_command(test_cmd, timeout=30)
    
    if returncode == 0:
        results['nvenc_test'] = True
        print("✓ NVENC编码测试成功")
        
        # 检查输出文件
        if os.path.exists('/tmp/test_l4_nvenc.mp4'):
            file_size = os.path.getsize('/tmp/test_l4_nvenc.mp4')
            print(f"  输出文件大小: {file_size / 1024 / 1024:.2f} MB")
            os.remove('/tmp/test_l4_nvenc.mp4')
    else:
        results['nvenc_test'] = False
        print("❌ NVENC编码测试失败")
        print(f"   错误: {stderr}")
    
    return results

def generate_summary(all_results):
    """
    生成检查结果总结
    
    Args:
        all_results: 所有检查结果
    """
    print("\n" + "=" * 50)
    print("检查结果总结")
    print("=" * 50)
    
    # 统计通过的检查项
    total_checks = 0
    passed_checks = 0
    
    critical_issues = []
    warnings = []
    
    for category, results in all_results.items():
        for check, status in results.items():
            total_checks += 1
            if status:
                passed_checks += 1
            else:
                if category in ['nvidia_gpu', 'ffmpeg'] and check in ['nvidia_smi', 'ffmpeg', 'h264_nvenc']:
                    critical_issues.append(f"{category}.{check}")
                else:
                    warnings.append(f"{category}.{check}")
    
    print(f"\n总体状态: {passed_checks}/{total_checks} 项检查通过")
    
    if critical_issues:
        print("\n🚨 关键问题:")
        for issue in critical_issues:
            print(f"  - {issue}")
        print("\n这些问题会影响gen_video.py的正常运行，请优先解决。")
    
    if warnings:
        print("\n⚠️  警告:")
        for warning in warnings:
            print(f"  - {warning}")
        print("\n这些问题可能影响某些功能，建议解决。")
    
    if not critical_issues:
        if all_results['nvidia_gpu'].get('is_l4', False):
            print("\n🎉 恭喜！您的L4 GPU环境配置良好，可以运行gen_video.py")
        else:
            print("\n✅ 基本环境配置正常，但未检测到L4 GPU")
    
    print("\n📋 详细配置指南请参考: L4_GPU_DEPENDENCIES.md")

def main():
    """
    主函数
    """
    parser = argparse.ArgumentParser(
        description='L4 GPU环境依赖检查脚本',
        formatter_class=argparse.RawDescriptionHelpFormatter
    )
    
    parser.add_argument(
        '--verbose', '-v',
        action='store_true',
        help='显示详细输出'
    )
    
    parser.add_argument(
        '--performance', '-p',
        action='store_true',
        help='执行性能测试（需要更多时间）'
    )
    
    args = parser.parse_args()
    
    print("L4 GPU环境依赖检查脚本")
    print("=" * 50)
    
    # 执行所有检查
    all_results = {}
    
    all_results['system'] = check_system_info()
    all_results['nvidia_gpu'] = check_nvidia_gpu()
    all_results['cuda'] = check_cuda()
    all_results['ffmpeg'] = check_ffmpeg()
    all_results['python_packages'] = check_python_packages()
    all_results['project_structure'] = check_project_structure()
    all_results['api_config'] = check_api_config()
    
    if args.performance:
        all_results['performance'] = test_l4_performance()
    
    # 生成总结
    generate_summary(all_results)
    
    # 返回状态码
    critical_failed = (
        not all_results['nvidia_gpu'].get('nvidia_smi', False) or
        not all_results['ffmpeg'].get('ffmpeg', False) or
        not all_results['ffmpeg'].get('h264_nvenc', False)
    )
    
    return 1 if critical_failed else 0

if __name__ == "__main__":
    sys.exit(main())