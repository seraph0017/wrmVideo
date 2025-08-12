# 火山云L4 GPU环境依赖清单

本文档详细列出了在火山云L4 GPU机器上运行`gen_video.py`及其所有相关方法所需的完整依赖。

## 🚀 系统环境要求

### 操作系统
- **推荐**: Ubuntu 20.04/22.04 LTS
- **支持**: CentOS 7/8, RHEL 7/8
- **架构**: x86_64

### 硬件要求
- **GPU**: NVIDIA Tesla L4 (24GB GDDR6)
- **内存**: 建议 32GB+ RAM
- **存储**: 建议 500GB+ SSD
- **CPU**: 建议 8核+

## 🔧 NVIDIA GPU 驱动和CUDA环境

### 1. NVIDIA驱动
```bash
# 检查当前驱动版本
nvidia-smi

# 推荐驱动版本
# Driver Version: 535.xx+ (支持CUDA 12.x)
# 或 Driver Version: 470.xx+ (支持CUDA 11.x)
```

### 2. CUDA Toolkit
```bash
# CUDA 12.0+ (推荐)
wget https://developer.download.nvidia.com/compute/cuda/12.0.0/local_installers/cuda_12.0.0_525.60.13_linux.run
sudo sh cuda_12.0.0_525.60.13_linux.run

# 或 CUDA 11.8
wget https://developer.download.nvidia.com/compute/cuda/11.8.0/local_installers/cuda_11.8.0_520.61.05_linux.run
sudo sh cuda_11.8.0_520.61.05_linux.run

# 设置环境变量
export PATH=/usr/local/cuda/bin:$PATH
export LD_LIBRARY_PATH=/usr/local/cuda/lib64:$LD_LIBRARY_PATH
```

### 3. cuDNN (可选，用于深度学习加速)
```bash
# 下载并安装cuDNN 8.x
# 从 https://developer.nvidia.com/cudnn 下载对应CUDA版本的cuDNN
tar -xzvf cudnn-linux-x86_64-8.x.x.x_cudaX.Y-archive.tar.xz
sudo cp cudnn-*-archive/include/cudnn*.h /usr/local/cuda/include
sudo cp -P cudnn-*-archive/lib/libcudnn* /usr/local/cuda/lib64
sudo chmod a+r /usr/local/cuda/include/cudnn*.h /usr/local/cuda/lib64/libcudnn*
```

## 📦 FFmpeg 编译依赖

### 1. 系统依赖包
```bash
# Ubuntu/Debian
sudo apt update
sudo apt install -y \
    build-essential \
    cmake \
    git \
    pkg-config \
    yasm \
    nasm \
    libx264-dev \
    libx265-dev \
    libvpx-dev \
    libfdk-aac-dev \
    libmp3lame-dev \
    libopus-dev \
    libvorbis-dev \
    libtheora-dev \
    libfreetype6-dev \
    libfontconfig1-dev \
    libfribidi-dev \
    libharfbuzz-dev \
    libass-dev \
    libva-dev \
    libvdpau-dev \
    libxcb1-dev \
    libxcb-shm0-dev \
    libxcb-xfixes0-dev \
    texinfo \
    wget \
    libnuma-dev

# CentOS/RHEL
sudo yum groupinstall -y "Development Tools"
sudo yum install -y \
    cmake3 \
    git \
    pkgconfig \
    yasm \
    nasm \
    x264-devel \
    x265-devel \
    libvpx-devel \
    fdk-aac-devel \
    lame-devel \
    opus-devel \
    libvorbis-devel \
    libtheora-devel \
    freetype-devel \
    fontconfig-devel \
    fribidi-devel \
    harfbuzz-devel \
    libass-devel \
    libva-devel \
    libvdpau-devel \
    libxcb-devel \
    texinfo \
    wget \
    numactl-devel
```

### 2. NVIDIA Video Codec SDK
```bash
# 下载 nv-codec-headers
git clone https://git.videolan.org/git/ffmpeg/nv-codec-headers.git
cd nv-codec-headers
make install
cd ..
```

### 3. FFmpeg 编译配置
```bash
# 下载FFmpeg源码
wget https://ffmpeg.org/releases/ffmpeg-6.0.tar.xz
tar -xf ffmpeg-6.0.tar.xz
cd ffmpeg-6.0

# L4 GPU优化编译配置
./configure \
    --enable-gpl \
    --enable-version3 \
    --enable-nonfree \
    --enable-cuda-nvcc \
    --enable-nvenc \
    --enable-nvdec \
    --enable-cuvid \
    --enable-libx264 \
    --enable-libx265 \
    --enable-libvpx \
    --enable-libfdk-aac \
    --enable-libmp3lame \
    --enable-libopus \
    --enable-libvorbis \
    --enable-libtheora \
    --enable-libfreetype \
    --enable-libfontconfig \
    --enable-libfribidi \
    --enable-libharfbuzz \
    --enable-libass \
    --enable-vaapi \
    --enable-vdpau \
    --extra-cflags="-I/usr/local/cuda/include" \
    --extra-ldflags="-L/usr/local/cuda/lib64" \
    --nvccflags="-gencode arch=compute_89,code=sm_89" \
    --prefix=/usr/local/ffmpeg

# 编译和安装
make -j$(nproc)
sudo make install

# 添加到PATH
export PATH=/usr/local/ffmpeg/bin:$PATH
```

## 🐍 Python 环境

### 1. Python 版本
```bash
# 推荐 Python 3.8+
python3 --version
# Python 3.8.x 或更高版本
```

### 2. Python 包依赖
```bash
# 安装项目依赖
pip install -r requirements.txt

# 核心依赖详细列表：
pip install \
    requests==2.31.0 \
    volcengine-python-sdk[ark]==1.0.98 \
    volcengine==1.0.98 \
    ffmpeg-python==0.2.0 \
    jinja2>=3.0.0 \
    Pillow>=10.0.0 \
    moviepy>=1.0.3 \
    numpy>=1.21.0 \
    jieba>=0.42.1 \
    PyYAML>=6.0 \
    aiofiles>=23.0.0
```

## 🐳 Docker 环境（可选）

### 1. Docker 和 NVIDIA Container Toolkit
```bash
# 安装Docker
curl -fsSL https://get.docker.com -o get-docker.sh
sudo sh get-docker.sh

# 安装NVIDIA Container Toolkit
distribution=$(. /etc/os-release;echo $ID$VERSION_ID)
curl -s -L https://nvidia.github.io/nvidia-docker/gpgkey | sudo apt-key add -
curl -s -L https://nvidia.github.io/nvidia-docker/$distribution/nvidia-docker.list | sudo tee /etc/apt/sources.list.d/nvidia-docker.list

sudo apt-get update && sudo apt-get install -y nvidia-docker2
sudo systemctl restart docker
```

### 2. L4 GPU优化的Docker镜像
```dockerfile
# Dockerfile.l4
FROM nvidia/cuda:12.0-devel-ubuntu22.04

# 安装系统依赖
RUN apt-get update && apt-get install -y \
    build-essential cmake git pkg-config yasm nasm \
    libx264-dev libx265-dev libvpx-dev libfdk-aac-dev \
    libmp3lame-dev libopus-dev libvorbis-dev libtheora-dev \
    libfreetype6-dev libfontconfig1-dev libfribidi-dev \
    libharfbuzz-dev libass-dev python3 python3-pip \
    && rm -rf /var/lib/apt/lists/*

# 编译FFmpeg with NVENC支持
RUN git clone https://git.videolan.org/git/ffmpeg/nv-codec-headers.git && \
    cd nv-codec-headers && make install && cd .. && \
    wget https://ffmpeg.org/releases/ffmpeg-6.0.tar.xz && \
    tar -xf ffmpeg-6.0.tar.xz && cd ffmpeg-6.0 && \
    ./configure --enable-gpl --enable-nonfree --enable-cuda-nvcc \
                --enable-nvenc --enable-nvdec --enable-cuvid \
                --enable-libx264 --enable-libx265 --enable-libass \
                --nvccflags="-gencode arch=compute_89,code=sm_89" && \
    make -j$(nproc) && make install

# 安装Python依赖
COPY requirements.txt /app/
RUN pip3 install -r /app/requirements.txt

WORKDIR /workspace
```

## 🔧 配置文件

### 1. 环境变量配置
```bash
# ~/.bashrc 或 ~/.zshrc
export CUDA_HOME=/usr/local/cuda
export PATH=$CUDA_HOME/bin:$PATH
export LD_LIBRARY_PATH=$CUDA_HOME/lib64:$LD_LIBRARY_PATH
export FFMPEG_PATH=/usr/local/ffmpeg/bin
export PATH=$FFMPEG_PATH:$PATH

# 火山引擎API配置
export ARK_API_KEY="your_ark_api_key"
export VOLC_ACCESS_KEY="your_volc_access_key"
export VOLC_SECRET_KEY="your_volc_secret_key"
```

### 2. 项目配置文件
```python
# config/config.py
ARK_CONFIG = {
    'api_key': 'your_ark_api_key',
    'base_url': 'https://ark.cn-beijing.volces.com/api/v3',
    'model': 'ep-20241022105718-xxxxxx'
}

TTS_CONFIG = {
    'access_key': 'your_volc_access_key',
    'secret_key': 'your_volc_secret_key',
    'app_id': 'your_app_id',
    'voice_type': 'BV700_streaming'
}

IMAGE_TWO_CONFIG = {
    'access_key': 'your_volc_access_key',
    'secret_key': 'your_volc_secret_key',
    'service_info': {
        'host': 'visual.volcengineapi.com',
        'header': {
            'Accept': 'application/json'
        }
    }
}
```

## 📁 目录结构要求

```
wrmVideo/
├── src/
│   ├── banner/
│   │   ├── finish.mp4          # 片尾视频
│   │   └── fuceng1.mov         # 转场特效
│   ├── bgm/                    # 背景音乐
│   │   ├── wn1.mp3
│   │   ├── wn2.mp3
│   │   └── ...
│   └── sound_effects/          # 音效文件
│       ├── action/
│       ├── combat/
│       ├── emotion/
│       └── misc/
├── Character_Images/           # 角色图片库
│   ├── 男/
│   ├── 女/
│   └── ...
├── data/                      # 数据目录
│   ├── 001/
│   │   ├── chapter_001/
│   │   ├── chapter_002/
│   │   └── ...
│   └── ...
└── config/
    ├── config.py              # 主配置文件
    └── prompt_config.py       # 提示词配置
```

## ✅ 环境验证

### 1. GPU环境检测
```bash
# 检测L4 GPU
python test/test_volcano_l4_ffmpeg.py

# 检测NVENC支持
ffmpeg -encoders | grep nvenc

# 测试L4 GPU编码
ffmpeg -f lavfi -i testsrc2=duration=10:size=1920x1080:rate=30 \
  -c:v h264_nvenc -preset p4 -rc vbr -cq 23 \
  -spatial_aq 1 -temporal_aq 1 -rc-lookahead 20 \
  test_l4.mp4
```

### 2. Python环境检测
```bash
# 检测Python依赖
python -c "import volcengine, ffmpeg, PIL, numpy, jieba; print('所有依赖已安装')"

# 检测API配置
python -c "from config.config import ARK_CONFIG, TTS_CONFIG; print('配置文件正常')"
```

### 3. 完整流程测试
```bash
# 测试完整视频生成流程
python gen_video.py data/001
```

## 🚨 常见问题解决

### 1. NVENC编码器不可用
```bash
# 检查NVIDIA驱动
nvidia-smi

# 重新编译FFmpeg with NVENC
# 确保安装了nv-codec-headers
```

### 2. CUDA版本不匹配
```bash
# 检查CUDA版本
nvcc --version
cuda-gdb --version

# 重新安装匹配的CUDA版本
```

### 3. Python包依赖冲突
```bash
# 使用虚拟环境
python -m venv venv
source venv/bin/activate
pip install -r requirements.txt
```

### 4. 内存不足
```bash
# 监控GPU内存使用
nvidia-smi -l 1

# 调整批处理大小
# 在脚本中减少并发数量
```

## 📊 性能优化建议

### 1. L4 GPU优化参数
- **预设**: p4 (平衡质量和速度)
- **码率控制**: VBR (可变比特率)
- **质量**: CQ 23 (恒定质量)
- **自适应量化**: 启用空间和时间AQ
- **前瞻帧数**: 20帧
- **编码表面**: 32个

### 2. 系统优化
```bash
# 设置GPU性能模式
sudo nvidia-smi -pm 1
sudo nvidia-smi -pl 300  # 设置功耗限制

# 优化系统参数
echo 'vm.swappiness=10' | sudo tee -a /etc/sysctl.conf
echo 'fs.file-max=2097152' | sudo tee -a /etc/sysctl.conf
```

### 3. 并发优化
- **图片生成**: 建议并发数 3-5
- **语音合成**: 建议并发数 5-8
- **视频编码**: 建议串行处理，避免GPU资源竞争

---

**注意**: 本文档基于火山云L4 GPU环境编写，其他GPU型号可能需要调整相应的CUDA架构参数和优化设置。