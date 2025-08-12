#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
火山云L4 GPU环境FFmpeg配置检测和优化脚本
专门针对火山云新L4 GPU机器的生产环境配置

使用方法:
    python test_volcano_l4_ffmpeg.py              # 检测当前环境
    python test_volcano_l4_ffmpeg.py --optimize   # 生成优化配置
    python test_volcano_l4_ffmpeg.py --compile    # 生成编译脚本
    python test_volcano_l4_ffmpeg.py --help       # 显示帮助信息
"""

import subprocess
import sys
import os
import argparse
import json
from pathlib import Path

def run_command(cmd, timeout=30):
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

def check_volcano_environment():
    """
    检查火山云环境特征
    
    Returns:
        dict: 环境检测结果
    """
    print("=== 检查火山云环境 ===")
    
    results = {
        'is_volcano': False,
        'instance_type': None,
        'region': None,
        'gpu_info': None
    }
    
    # 检查火山云元数据服务
    try:
        # 火山云实例元数据API
        returncode, stdout, stderr = run_command([
            'curl', '-s', '--connect-timeout', '3',
            'http://100.96.0.96/volcstack/latest/meta-data/instance-id'
        ])
        
        if returncode == 0 and stdout.strip():
            results['is_volcano'] = True
            print("✓ 检测到火山云环境")
            
            # 获取实例类型
            returncode, stdout, stderr = run_command([
                'curl', '-s', '--connect-timeout', '3',
                'http://100.96.0.96/volcstack/latest/meta-data/instance-type'
            ])
            if returncode == 0:
                results['instance_type'] = stdout.strip()
                print(f"  实例类型: {results['instance_type']}")
            
            # 获取区域信息
            returncode, stdout, stderr = run_command([
                'curl', '-s', '--connect-timeout', '3',
                'http://100.96.0.96/volcstack/latest/meta-data/placement/region'
            ])
            if returncode == 0:
                results['region'] = stdout.strip()
                print(f"  区域: {results['region']}")
        else:
            print("❌ 未检测到火山云环境")
    except:
        print("❌ 无法访问火山云元数据服务")
    
    return results

def check_l4_gpu():
    """
    检查NVIDIA L4 GPU配置
    
    Returns:
        dict: L4 GPU检测结果
    """
    print("\n=== 检查NVIDIA L4 GPU ===")
    
    results = {
        'gpu_available': False,
        'gpu_model': None,
        'driver_version': None,
        'cuda_version': None,
        'compute_capability': None,
        'memory_total': None,
        'nvenc_sessions': None
    }
    
    # 检查nvidia-smi
    returncode, stdout, stderr = run_command(['nvidia-smi', '--query-gpu=name,driver_version,memory.total,compute_cap', '--format=csv,noheader,nounits'])
    
    if returncode != 0:
        print("❌ 未检测到NVIDIA GPU或驱动")
        return results
    
    # 解析GPU信息
    gpu_info = stdout.strip().split(', ')
    if len(gpu_info) >= 4:
        results['gpu_available'] = True
        results['gpu_model'] = gpu_info[0].strip()
        results['driver_version'] = gpu_info[1].strip()
        results['memory_total'] = gpu_info[2].strip()
        results['compute_capability'] = gpu_info[3].strip()
        
        print(f"✓ GPU型号: {results['gpu_model']}")
        print(f"  驱动版本: {results['driver_version']}")
        print(f"  显存容量: {results['memory_total']} MB")
        print(f"  计算能力: {results['compute_capability']}")
        
        # 检查是否为L4 GPU
        if 'L4' in results['gpu_model']:
            print("✓ 确认为NVIDIA L4 GPU")
        else:
            print(f"⚠️  检测到的GPU不是L4: {results['gpu_model']}")
    
    # 检查CUDA版本
    returncode, stdout, stderr = run_command(['nvidia-smi', '--query-gpu=cuda_version', '--format=csv,noheader,nounits'])
    if returncode == 0:
        results['cuda_version'] = stdout.strip()
        print(f"  CUDA版本: {results['cuda_version']}")
    
    # 检查NVENC会话限制
    returncode, stdout, stderr = run_command(['nvidia-smi', 'nvlink', '--status'])
    if returncode == 0:
        # L4 GPU通常支持3个并发NVENC会话
        results['nvenc_sessions'] = 3
        print(f"  NVENC并发会话限制: {results['nvenc_sessions']}")
    
    return results

def check_ffmpeg_l4_support():
    """
    检查FFmpeg对L4 GPU的支持情况
    
    Returns:
        dict: FFmpeg支持检测结果
    """
    print("\n=== 检查FFmpeg L4 GPU支持 ===")
    
    results = {
        'ffmpeg_available': False,
        'ffmpeg_version': None,
        'nvenc_support': False,
        'nvdec_support': False,
        'cuda_support': False,
        'supported_encoders': [],
        'supported_decoders': []
    }
    
    # 检查FFmpeg版本
    returncode, stdout, stderr = run_command(['ffmpeg', '-version'])
    if returncode != 0:
        print("❌ FFmpeg未安装")
        return results
    
    results['ffmpeg_available'] = True
    
    # 提取版本信息
    lines = stdout.split('\n')
    if lines:
        version_line = lines[0]
        results['ffmpeg_version'] = version_line
        print(f"✓ {version_line}")
    
    # 检查编译配置
    config_line = next((line for line in lines if 'configuration:' in line), None)
    if config_line:
        if '--enable-nvenc' in config_line:
            print("✓ FFmpeg编译时启用了NVENC支持")
        if '--enable-cuda' in config_line:
            results['cuda_support'] = True
            print("✓ FFmpeg编译时启用了CUDA支持")
        if '--enable-cuvid' in config_line:
            print("✓ FFmpeg编译时启用了CUVID支持")
    
    # 检查NVENC编码器
    returncode, stdout, stderr = run_command(['ffmpeg', '-encoders'])
    if returncode == 0:
        encoders = stdout.lower()
        nvenc_encoders = [
            'h264_nvenc', 'hevc_nvenc', 'av1_nvenc'
        ]
        
        for encoder in nvenc_encoders:
            if encoder in encoders:
                results['supported_encoders'].append(encoder)
                results['nvenc_support'] = True
                print(f"✓ 支持编码器: {encoder}")
            else:
                print(f"❌ 不支持编码器: {encoder}")
    
    # 检查NVDEC解码器
    returncode, stdout, stderr = run_command(['ffmpeg', '-decoders'])
    if returncode == 0:
        decoders = stdout.lower()
        nvdec_decoders = [
            'h264_cuvid', 'hevc_cuvid', 'av1_cuvid'
        ]
        
        for decoder in nvdec_decoders:
            if decoder in decoders:
                results['supported_decoders'].append(decoder)
                results['nvdec_support'] = True
                print(f"✓ 支持解码器: {decoder}")
            else:
                print(f"❌ 不支持解码器: {decoder}")
    
    return results

def test_l4_nvenc_performance():
    """
    测试L4 GPU NVENC编码性能
    
    Returns:
        dict: 性能测试结果
    """
    print("\n=== 测试L4 NVENC编码性能 ===")
    
    results = {
        'h264_nvenc_works': False,
        'hevc_nvenc_works': False,
        'encoding_speed': None,
        'recommended_preset': None
    }
    
    # 测试H.264 NVENC编码
    test_cmd = [
        'ffmpeg', '-y', '-f', 'lavfi', '-i', 'testsrc=duration=5:size=1920x1080:rate=30',
        '-c:v', 'h264_nvenc', '-preset', 'p4', '-b:v', '5M',
        '-f', 'null', '-'
    ]
    
    print("测试H.264 NVENC编码...")
    returncode, stdout, stderr = run_command(test_cmd)
    
    if returncode == 0:
        results['h264_nvenc_works'] = True
        print("✓ H.264 NVENC编码测试成功")
        
        # 从stderr中提取编码速度信息
        if 'fps=' in stderr:
            fps_info = [line for line in stderr.split('\n') if 'fps=' in line]
            if fps_info:
                print(f"  编码信息: {fps_info[-1].strip()}")
    else:
        print(f"❌ H.264 NVENC编码测试失败: {stderr}")
    
    # 测试HEVC NVENC编码
    test_cmd[5] = 'hevc_nvenc'
    print("测试HEVC NVENC编码...")
    returncode, stdout, stderr = run_command(test_cmd)
    
    if returncode == 0:
        results['hevc_nvenc_works'] = True
        print("✓ HEVC NVENC编码测试成功")
    else:
        print(f"❌ HEVC NVENC编码测试失败: {stderr}")
    
    # 推荐L4 GPU的最佳预设
    if results['h264_nvenc_works'] or results['hevc_nvenc_works']:
        results['recommended_preset'] = 'p4'  # L4 GPU的平衡预设
        print(f"✓ 推荐预设: {results['recommended_preset']} (质量与速度平衡)")
    
    return results

def generate_l4_optimization_config():
    """
    生成L4 GPU优化配置
    
    Returns:
        dict: 优化配置
    """
    print("\n=== 生成L4 GPU优化配置 ===")
    
    config = {
        'encoding': {
            'h264_nvenc': {
                'preset': 'p4',  # L4最佳平衡预设
                'profile': 'high',
                'level': '4.1',
                'rc': 'vbr',  # 可变比特率
                'cq': '23',   # 恒定质量
                'bf': '3',    # B帧数量
                'refs': '3',  # 参考帧数量
                'spatial_aq': '1',  # 空间自适应量化
                'temporal_aq': '1', # 时间自适应量化
                'rc_lookahead': '20',  # 前瞻帧数
                'surfaces': '32',      # 编码表面数量
                'extra_params': [
                    '-gpu', '0',
                    '-delay', '0',
                    '-no-scenecut', '1'
                ]
            },
            'hevc_nvenc': {
                'preset': 'p4',
                'profile': 'main',
                'level': '5.1',
                'rc': 'vbr',
                'cq': '25',
                'bf': '4',
                'refs': '3',
                'spatial_aq': '1',
                'temporal_aq': '1',
                'rc_lookahead': '20',
                'surfaces': '32',
                'extra_params': [
                    '-gpu', '0',
                    '-tier', 'main'
                ]
            }
        },
        'decoding': {
            'hwaccel': 'cuda',
            'hwaccel_output_format': 'cuda',
            'extra_hw_frames': '3'
        },
        'performance': {
            'threads': '0',  # 自动检测
            'thread_type': 'slice',
            'thread_queue_size': '1024'
        }
    }
    
    print("✓ L4 GPU优化配置已生成")
    print("  - H.264编码: 预设p4, CQ=23, 支持B帧和自适应量化")
    print("  - HEVC编码: 预设p4, CQ=25, 优化的GOP结构")
    print("  - 硬件解码: CUDA加速, 优化内存管理")
    
    return config

def generate_ffmpeg_compile_script():
    """
    生成针对L4 GPU的FFmpeg编译脚本
    
    Returns:
        str: 编译脚本内容
    """
    script = '''#!/bin/bash
# 火山云L4 GPU环境FFmpeg编译脚本
# 针对NVIDIA L4 GPU优化的生产环境配置

set -e

echo "=== 火山云L4 GPU FFmpeg编译脚本 ==="
echo "开始编译针对L4 GPU优化的FFmpeg..."

# 设置编译目录
BUILD_DIR="/tmp/ffmpeg-l4-build"
INSTALL_PREFIX="/usr/local/ffmpeg-l4"

# 创建编译目录
mkdir -p $BUILD_DIR
cd $BUILD_DIR

# 更新系统包
echo "更新系统包..."
sudo apt-get update

# 安装基础依赖
echo "安装编译依赖..."
sudo apt-get install -y \
    build-essential \
    cmake \
    git \
    pkg-config \
    yasm \
    nasm \
    libx264-dev \
    libx265-dev \
    libfdk-aac-dev \
    libmp3lame-dev \
    libopus-dev \
    libvpx-dev \
    libfreetype6-dev \
    libfontconfig1-dev \
    libass-dev \
    libva-dev \
    libvdpau-dev \
    libxcb1-dev \
    libxcb-shm0-dev \
    libxcb-xfixes0-dev \
    texinfo \
    wget \
    zlib1g-dev

# 检查CUDA安装
echo "检查CUDA环境..."
if ! command -v nvcc &> /dev/null; then
    echo "错误: 未找到CUDA，请先安装CUDA Toolkit"
    echo "建议安装CUDA 12.0或更高版本以支持L4 GPU"
    exit 1
fi

CUDA_VERSION=$(nvcc --version | grep "release" | awk '{print $6}' | cut -c2-)
echo "检测到CUDA版本: $CUDA_VERSION"

# 安装NVIDIA编解码头文件
echo "安装NVIDIA编解码头文件..."
if [ ! -d "nv-codec-headers" ]; then
    git clone https://git.videolan.org/git/ffmpeg/nv-codec-headers.git
fi
cd nv-codec-headers
sudo make install
cd ..

# 下载FFmpeg源码
echo "下载FFmpeg源码..."
FFMPEG_VERSION="6.1.1"
if [ ! -f "ffmpeg-${FFMPEG_VERSION}.tar.xz" ]; then
    wget https://ffmpeg.org/releases/ffmpeg-${FFMPEG_VERSION}.tar.xz
fi

if [ ! -d "ffmpeg-${FFMPEG_VERSION}" ]; then
    tar -xf ffmpeg-${FFMPEG_VERSION}.tar.xz
fi

cd ffmpeg-${FFMPEG_VERSION}

# 配置编译选项 - 针对L4 GPU优化
echo "配置FFmpeg编译选项..."
./configure \
    --prefix=$INSTALL_PREFIX \
    --enable-gpl \
    --enable-nonfree \
    --enable-version3 \
    --enable-shared \
    --disable-static \
    --enable-cuda-nvcc \
    --enable-nvenc \
    --enable-nvdec \
    --enable-cuvid \
    --enable-libnpp \
    --enable-libx264 \
    --enable-libx265 \
    --enable-libfdk-aac \
    --enable-libmp3lame \
    --enable-libopus \
    --enable-libvpx \
    --enable-libfreetype \
    --enable-libfontconfig \
    --enable-libass \
    --enable-vaapi \
    --enable-vdpau \
    --extra-cflags="-I/usr/local/cuda/include" \
    --extra-ldflags="-L/usr/local/cuda/lib64" \
    --extra-libs="-lpthread -lm" \
    --nvccflags="-gencode arch=compute_89,code=sm_89" # L4 GPU架构

# 编译
echo "开始编译FFmpeg (使用$(nproc)个CPU核心)..."
make -j$(nproc)

# 安装
echo "安装FFmpeg..."
sudo make install

# 配置库路径
echo "配置库路径..."
echo "$INSTALL_PREFIX/lib" | sudo tee /etc/ld.so.conf.d/ffmpeg-l4.conf
sudo ldconfig

# 创建符号链接
echo "创建符号链接..."
sudo ln -sf $INSTALL_PREFIX/bin/ffmpeg /usr/local/bin/ffmpeg-l4
sudo ln -sf $INSTALL_PREFIX/bin/ffprobe /usr/local/bin/ffprobe-l4

# 验证安装
echo "验证FFmpeg安装..."
$INSTALL_PREFIX/bin/ffmpeg -version
echo ""
echo "检查NVENC编码器支持:"
$INSTALL_PREFIX/bin/ffmpeg -encoders | grep nvenc
echo ""
echo "检查NVDEC解码器支持:"
$INSTALL_PREFIX/bin/ffmpeg -decoders | grep cuvid

echo "=== FFmpeg L4 GPU编译完成 ==="
echo "安装路径: $INSTALL_PREFIX"
echo "可执行文件: $INSTALL_PREFIX/bin/ffmpeg"
echo "库文件: $INSTALL_PREFIX/lib"
echo ""
echo "使用方法:"
echo "  $INSTALL_PREFIX/bin/ffmpeg -hwaccel cuda -c:v h264_cuvid -i input.mp4 -c:v h264_nvenc -preset p4 output.mp4"
echo ""
echo "环境变量设置 (添加到 ~/.bashrc):"
echo "  export PATH=$INSTALL_PREFIX/bin:\$PATH"
echo "  export LD_LIBRARY_PATH=$INSTALL_PREFIX/lib:\$LD_LIBRARY_PATH"
'''
    
    return script

def generate_docker_l4_config():
    """
    生成L4 GPU Docker配置
    
    Returns:
        dict: Docker配置
    """
    config = {
        'base_image': 'nvidia/cuda:12.0-devel-ubuntu22.04',
        'dockerfile': '''FROM nvidia/cuda:12.0-devel-ubuntu22.04

# 设置环境变量
ENV DEBIAN_FRONTEND=noninteractive
ENV NVIDIA_VISIBLE_DEVICES=all
ENV NVIDIA_DRIVER_CAPABILITIES=compute,video,utility

# 安装基础依赖
RUN apt-get update && apt-get install -y \
    build-essential \
    cmake \
    git \
    pkg-config \
    yasm \
    nasm \
    libx264-dev \
    libx265-dev \
    libfdk-aac-dev \
    libmp3lame-dev \
    libopus-dev \
    libvpx-dev \
    libfreetype6-dev \
    libfontconfig1-dev \
    libass-dev \
    wget \
    curl \
    && rm -rf /var/lib/apt/lists/*

# 安装NVIDIA编解码头文件
RUN git clone https://git.videolan.org/git/ffmpeg/nv-codec-headers.git && \
    cd nv-codec-headers && \
    make install && \
    cd .. && rm -rf nv-codec-headers

# 编译安装FFmpeg
RUN wget https://ffmpeg.org/releases/ffmpeg-6.1.1.tar.xz && \
    tar -xf ffmpeg-6.1.1.tar.xz && \
    cd ffmpeg-6.1.1 && \
    ./configure \
        --prefix=/usr/local/ffmpeg \
        --enable-gpl \
        --enable-nonfree \
        --enable-shared \
        --enable-cuda-nvcc \
        --enable-nvenc \
        --enable-nvdec \
        --enable-cuvid \
        --enable-libnpp \
        --enable-libx264 \
        --enable-libx265 \
        --enable-libfdk-aac \
        --extra-cflags="-I/usr/local/cuda/include" \
        --extra-ldflags="-L/usr/local/cuda/lib64" \
        --nvccflags="-gencode arch=compute_89,code=sm_89" && \
    make -j$(nproc) && \
    make install && \
    cd .. && rm -rf ffmpeg-6.1.1*

# 配置环境
ENV PATH=/usr/local/ffmpeg/bin:$PATH
ENV LD_LIBRARY_PATH=/usr/local/ffmpeg/lib:$LD_LIBRARY_PATH

# 创建工作目录
WORKDIR /workspace

# 验证安装
RUN ffmpeg -version && ffmpeg -encoders | grep nvenc

CMD ["/bin/bash"]
''',
        'docker_run_commands': [
            '# 基础运行命令',
            'docker run --gpus all --rm -it -v $(pwd):/workspace your-ffmpeg-l4:latest',
            '',
            '# 生产环境运行命令',
            'docker run --gpus all --rm \\',
            '  -e NVIDIA_VISIBLE_DEVICES=all \\',
            '  -e NVIDIA_DRIVER_CAPABILITIES=compute,video,utility \\',
            '  -v /path/to/input:/input \\',
            '  -v /path/to/output:/output \\',
            '  -w /workspace \\',
            '  your-ffmpeg-l4:latest \\',
            '  ffmpeg -hwaccel cuda -c:v h264_cuvid -i /input/video.mp4 \\',
            '         -c:v h264_nvenc -preset p4 -cq 23 /output/video_l4.mp4'
        ]
    }
    
    return config

def parse_arguments():
    """
    解析命令行参数
    
    Returns:
        argparse.Namespace: 解析后的参数
    """
    parser = argparse.ArgumentParser(
        description='火山云L4 GPU环境FFmpeg配置检测和优化脚本',
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog='''
示例用法:
  python test_volcano_l4_ffmpeg.py                    # 检测当前环境
  python test_volcano_l4_ffmpeg.py --optimize         # 生成优化配置
  python test_volcano_l4_ffmpeg.py --compile          # 生成编译脚本
  python test_volcano_l4_ffmpeg.py --docker           # 生成Docker配置
  python test_volcano_l4_ffmpeg.py --all              # 执行所有操作
        '''
    )
    
    parser.add_argument('--optimize', action='store_true',
                       help='生成L4 GPU优化配置')
    parser.add_argument('--compile', action='store_true',
                       help='生成FFmpeg编译脚本')
    parser.add_argument('--docker', action='store_true',
                       help='生成Docker配置')
    parser.add_argument('--all', action='store_true',
                       help='执行所有操作')
    parser.add_argument('--output-dir', default='./l4_config',
                       help='输出目录 (默认: ./l4_config)')
    
    return parser.parse_args()

def save_config_files(output_dir, optimization_config, compile_script, docker_config):
    """
    保存配置文件
    
    Args:
        output_dir: 输出目录
        optimization_config: 优化配置
        compile_script: 编译脚本
        docker_config: Docker配置
    """
    output_path = Path(output_dir)
    output_path.mkdir(exist_ok=True)
    
    # 保存优化配置
    if optimization_config:
        config_file = output_path / 'l4_optimization_config.json'
        with open(config_file, 'w', encoding='utf-8') as f:
            json.dump(optimization_config, f, indent=2, ensure_ascii=False)
        print(f"✓ 优化配置已保存: {config_file}")
    
    # 保存编译脚本
    if compile_script:
        script_file = output_path / 'compile_ffmpeg_l4.sh'
        with open(script_file, 'w', encoding='utf-8') as f:
            f.write(compile_script)
        os.chmod(script_file, 0o755)
        print(f"✓ 编译脚本已保存: {script_file}")
    
    # 保存Docker配置
    if docker_config:
        dockerfile = output_path / 'Dockerfile.l4'
        with open(dockerfile, 'w', encoding='utf-8') as f:
            f.write(docker_config['dockerfile'])
        print(f"✓ Dockerfile已保存: {dockerfile}")
        
        docker_commands = output_path / 'docker_commands.sh'
        with open(docker_commands, 'w', encoding='utf-8') as f:
            f.write('#!/bin/bash\n')
            f.write('# 火山云L4 GPU Docker运行命令\n\n')
            for cmd in docker_config['docker_run_commands']:
                f.write(cmd + '\n')
        os.chmod(docker_commands, 0o755)
        print(f"✓ Docker命令已保存: {docker_commands}")

def main():
    """
    主函数
    """
    args = parse_arguments()
    
    print("火山云L4 GPU环境FFmpeg配置检测和优化")
    print("=" * 60)
    
    # 检测环境
    volcano_env = check_volcano_environment()
    l4_gpu = check_l4_gpu()
    ffmpeg_support = check_ffmpeg_l4_support()
    
    # 性能测试
    if l4_gpu['gpu_available'] and ffmpeg_support['nvenc_support']:
        performance = test_l4_nvenc_performance()
    else:
        performance = {'h264_nvenc_works': False, 'hevc_nvenc_works': False}
    
    # 生成配置和脚本
    optimization_config = None
    compile_script = None
    docker_config = None
    
    if args.optimize or args.all:
        optimization_config = generate_l4_optimization_config()
    
    if args.compile or args.all:
        print("\n=== 生成FFmpeg编译脚本 ===")
        compile_script = generate_ffmpeg_compile_script()
        print("✓ L4 GPU优化编译脚本已生成")
    
    if args.docker or args.all:
        print("\n=== 生成Docker配置 ===")
        docker_config = generate_docker_l4_config()
        print("✓ L4 GPU Docker配置已生成")
    
    # 保存配置文件
    if optimization_config or compile_script or docker_config:
        save_config_files(args.output_dir, optimization_config, compile_script, docker_config)
    
    # 总结和建议
    print("\n=== 环境检测总结 ===")
    
    if volcano_env['is_volcano']:
        print(f"✓ 火山云环境: {volcano_env['instance_type']} ({volcano_env['region']})")
    else:
        print("⚠️  未检测到火山云环境")
    
    if l4_gpu['gpu_available']:
        if 'L4' in l4_gpu['gpu_model']:
            print(f"✓ NVIDIA L4 GPU: {l4_gpu['gpu_model']}")
            print(f"  驱动版本: {l4_gpu['driver_version']}")
            print(f"  显存容量: {l4_gpu['memory_total']} MB")
        else:
            print(f"⚠️  非L4 GPU: {l4_gpu['gpu_model']}")
    else:
        print("❌ 未检测到NVIDIA GPU")
    
    if ffmpeg_support['ffmpeg_available']:
        if ffmpeg_support['nvenc_support']:
            print("✓ FFmpeg支持NVENC硬件编码")
            if performance['h264_nvenc_works']:
                print("✓ H.264 NVENC编码测试通过")
            if performance['hevc_nvenc_works']:
                print("✓ HEVC NVENC编码测试通过")
        else:
            print("❌ FFmpeg不支持NVENC，需要重新编译")
    else:
        print("❌ 未安装FFmpeg")
    
    # 生产环境建议
    print("\n=== 生产环境配置建议 ===")
    
    if l4_gpu['gpu_available'] and 'L4' in l4_gpu['gpu_model']:
        print("🚀 L4 GPU生产环境优化建议:")
        print("  1. 使用预设p4获得质量与速度的最佳平衡")
        print("  2. 启用时间和空间自适应量化提升质量")
        print("  3. 设置合适的前瞻帧数(20)优化码率控制")
        print("  4. 限制并发NVENC会话数量(最多3个)")
        print("  5. 使用CUDA硬件解码减少CPU负载")
        
        if not ffmpeg_support['nvenc_support']:
            print("\n⚠️  需要重新编译FFmpeg以支持NVENC:")
            print(f"     运行: bash {args.output_dir}/compile_ffmpeg_l4.sh")
    else:
        print("⚠️  建议使用L4 GPU实例以获得最佳性能")
        print("     L4 GPU具有优秀的编码性能和成本效益")
    
    print(f"\n📁 配置文件输出目录: {args.output_dir}")
    print("\n🔧 使用生成的配置文件优化您的FFmpeg工作流程")

if __name__ == "__main__":
    main()