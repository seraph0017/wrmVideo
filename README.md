# 🎬 AI视频生成系统

一个基于AI的自动化视频生成系统，能够将小说文本转换为带有解说、图片和字幕的视频内容。系统集成了豆包大模型、火山引擎TTS和图像生成服务，实现从文本到视频的全自动化流程。

## ✨ 最新更新

- 🚀 **FFmpeg参数优化**: 全面优化视频编码参数以提升合成速度，在保证输出标准的前提下：
  - **NVIDIA GPU**: 使用更快的预设(p2)和低延迟调优(ll)，减少前瞻帧数和B帧数量
  - **CPU编码**: 使用fast预设，优化运动估计和参考帧设置，显著提升编码速度
  - **智能检测**: 自动检测GPU环境并应用相应的优化参数
- 🔄 **gen_video.py 重构**: 彻底重写 `gen_video.py` 脚本，现在作为流程编排器，按顺序执行 `concat_first_video.py`、`concat_narration_video.py` 和 `concat_finish_video.py`，实现模块化的视频生成流程
- 🎵 **音频混合优化**: 修复 `concat_finish_video.py` 中BGM盖住原有narration音频的问题，使用FFmpeg的amix滤镜将原有音频（音量1.0）与BGM（音量0.3）进行混合，确保解说声音清晰可听
- 📊 **统计逻辑优化**: 优化语音生成统计逻辑，添加文件存在检查和跳过机制，统计结果更准确
- 🛠️ **错误处理改进**: 改进语音生成错误处理，增加详细错误信息显示，提升调试体验
- 🔊 **语音生成优化**: 优化语音生成日志输出，移除详细API响应日志（包含phone、start_time、end_time等字段），减少终端输出冗余信息
- 📁 **文件重命名**: 将 `gen_video_async.py` 重命名为 `gen_first_video_async.py`，更好地反映其功能定位
- 🎯 **图片生成规则优化**: 每个章节固定生成30张图片（10个分镜×3张图片），确保视频内容的一致性
- 🔄 **智能生成策略**: 先尝试API生成图片，失败后自动从Character_Images目录复制补足
- 🛡️ **图片生成保障**: 精确任务统计和智能重试机制，确保所有图片都能成功生成
- 🔄 **智能重试系统**: 自动检测失败任务并重试，支持单独重试失败任务
- 📊 **任务状态管理**: 完成的任务自动移动到done_tasks目录，保持任务目录整洁
- 🔧 **完整工作流**: 从任务提交到图片下载的完整自动化流程
- 📈 **实时监控**: 提供任务状态监控和自动下载功能
- 🔄 **同步/异步双模式**: 支持同步和异步两种图片生成模式
- 📁 **目录结构优化**: Character_Images目录移至根目录，便于管理
- 🎨 **角色图片系统**: 完整的五层角色图片目录结构（性别/年龄/风格/文化/气质）
- ⚡ **性能优化**: 改进的图片生成和视频合成流程

## 🚀 功能特性

### 核心功能
- **🤖 智能文本处理**: 自动将长篇小说分割成适合的章节，支持大文本智能分块
- **📝 AI解说生成**: 使用豆包模型生成详细的解说文案，支持多种开场风格
- **🎨 图片自动生成**: 根据文本内容生成配套图片，支持720x1280竖屏格式
- **🎵 语音合成**: 将解说文案转换为自然语音，支持多种音色
- **🎬 视频合成**: 自动合成图片、音频和字幕为完整视频
- **📺 智能字幕系统**: 自动字幕生成、居中对齐、透明背景、智能断句

### 高级特性
- **⚡ 批量处理**: 支持批量生成多个章节视频
- **🎯 智能断句**: 优化字幕显示效果，支持换行后居中对齐
- **🔧 多格式支持**: 支持多种音频和视频格式
- **⚙️ 配置灵活**: 可自定义各种生成参数
- **🛡️ 内容规避**: 自动规避敏感内容，确保合规性
- **🎪 多种开场**: 支持热开场、前提开场、冷开场等多种风格
- **🎨 多种艺术风格**: 支持漫画、写实、水彩、油画四种图片生成风格

### 最新优化功能
- **📖 智能断句功能**: 根据标点符号和语义进行智能断句，提升观看体验
- **🖼️ 多音频共图**: 多个音频文件可共用一张图片，提高资源利用效率
- **🎨 字体样式优化**: 字幕居中对齐、透明背景、去除首尾标点符号
- **⚡ 性能提升**: 优化处理流程，提升生成速度和稳定性
- **📺 单行字幕显示**: 优化字幕生成逻辑，确保视频中只显示单行字幕，避免多行字幕影响观看体验

- **🧠 智能字幕处理**: 自动截取过长文本并添加省略号，移除换行符，确保字幕简洁易读

## 📁 项目结构

```
wrmVideo/
├── .gitignore
├── README.md               # 项目说明（包含完整功能介绍和优化总结）
├── main.md                 # 主要使用说明
├── config/                 # 配置目录
│   └── prompt_config.py   # Prompt配置管理
├── data/                   # 数据存储目录
│   ├── 001/                # 项目数据目录
│   │   ├── chapter01/      # 章节目录
│   │   │   ├── chapter01_script.txt  # 章节脚本
│   │   │   ├── *.mp3       # 生成的音频文件
│   │   │   ├── *.jpeg      # 生成的图片文件
│   │   │   ├── *.mp4       # 生成的视频片段
│   │   │   └── chapter01_complete.mp4  # 完整章节视频
│   │   └── final_complete_video.mp4    # 最终合并视频
│   └── test1/              # 测试数据目录
├── test/                   # 测试文件目录
│   ├── test_*.py           # 各种测试脚本
│   └── debug_*.py          # 调试脚本
├── Character_Images/       # 角色图片库（已移至根目录）
├── src/                    # 源代码目录
│   ├── core/               # 核心模块
│   ├── bgm/                # 背景音乐
│   └── sound_effects/      # 音效库
└── utils/                  # 工具模块
├── async_tasks/            # 异步任务目录（进行中的任务）
├── done_tasks/             # 已完成任务目录（自动移动）
├── generate.py             # 主程序入口
├── gen_image.py            # 同步图片生成脚本
├── gen_image_async.py      # 异步图片生成脚本（支持统计、重试和失败任务处理）
├── check_and_retry_images.py  # 图片任务检查和重试脚本
├── check_async_tasks.py    # 异步任务状态查询和下载脚本
├── generate_all_images.py  # 完整图片生成流程脚本
├── gen_script.py           # 解说文案生成脚本
├── gen_audio.py            # 音频生成脚本
├── gen_first_video_async.py # 第一个narration视频生成脚本（异步生成video_1和video_2）
├── concat_first_video.py   # 合并video_1与video_2并加入转场特效脚本
├── concat_narration_video.py # 生成主视频（添加旁白、BGM、音效等）
├── concat_finish_video.py  # 生成完整视频（添加片尾视频）
├── gen_video.py            # 视频生成流程编排器（依次执行上述三个脚本）
├── requirements.txt        # 项目依赖

### 核心脚本说明

#### 图片生成相关

- **`gen_image.py`**: 同步图片生成，适合小批量处理
- **`gen_image_async.py`**: 异步图片生成脚本，新增功能：
  - 自动统计所有narration文件中的图片特写数量
  - 逐一发起请求并存储响应到async_tasks目录
  - 自动检查并重试失败任务，确保所有任务都返回task_id
  - 支持`--retry-failed`参数单独重试失败任务
- **`check_async_tasks.py`**: 异步任务状态查询和下载脚本：
  - 检查任务状态并下载完成的图片
  - 自动将下载成功的任务文件移动到done_tasks目录
  - 支持单次检查和持续监控模式
- **`check_and_retry_images.py`**: 图片生成检查和重试脚本（旧版本）
- **`generate_all_images.py`**: 完整的图片生成流程，集成任务提交、监控和重试


├── test/                   # 测试脚本目录
│   ├── test_audio.py      # 音频测试
│   ├── test_chapter.txt
│   ├── test_chapter_split.py # 章节分割测试
│   ├── test_chapters/
│   ├── test_generate_modes.py # 生成模式测试脚本
│   ├── test_long_text.py  # 长文本处理测试
│   ├── test_optimized_features.py
│   ├── test_output_new.txt
│   ├── test_small.txt
│   ├── test_split.py      # 文本分割测试
│   ├── test_subtitle.py   # 字幕相关测试
│   ├── test_subtitle_fix.py
│   └── test_subtitle_improvements.py
└── utils/                  # 工具脚本目录
    ├── demo_styles.py     # 艺术风格演示脚本
    ├── fix_audio_quality.py # 音频质量修复工具
    └── init.py            # 初始化清理脚本
```

## 🔧 环境要求

- **Python**: 3.6 或更高版本
- **FFmpeg**: 用于视频处理（需要系统安装）
- **火山引擎账号**: 用于TTS和图像生成服务
- **豆包API**: 用于AI文案生成
- **网络连接**: 稳定的网络环境

## 📦 安装依赖

### 1. 安装Python依赖
```bash
pip install -r requirements.txt
```

### 2. 安装FFmpeg

**macOS:**
```bash
brew install ffmpeg
```

**Ubuntu/Debian:**
```bash
sudo apt update
sudo apt install ffmpeg
```

**Windows:**
下载FFmpeg并添加到系统PATH中

## ⚙️ 配置设置

### 1. 创建配置文件
```bash
cp config/config.example.py config/config.py
```

### 2. 配置API密钥
编辑 `config/config.py` 文件，填入你的API密钥：

```python
# TTS语音合成配置
TTS_CONFIG = {
    "appid": "your_appid_here",           # 火山引擎应用ID
    "access_token": "your_access_token",  # 访问令牌
    "cluster": "volcano_tts",             # 集群名称
    "voice_type": "BV701_streaming",      # 音色类型
    "host": "openspeech.bytedance.com"    # 服务地址
}

# AI模型配置（豆包）
ARK_CONFIG = {
    "base_url": "https://ark.cn-beijing.volces.com/api/v3",
    "api_key": "your_api_key_here"        # 豆包API密钥
}

# 图片生成配置
IMAGE_CONFIG = {
    "default_style": "manga",  # 默认艺术风格: manga, realistic, watercolor, oil_painting
    "size": "720x1280",       # 图片尺寸（竖屏格式）
    "watermark": False,       # 是否添加水印
    "model": "doubao-seedream-3-0-t2i-250415"  # 使用的图像生成模型
}
```

### 3. 获取API密钥
- **火山引擎TTS**: 访问[火山引擎控制台](https://console.volcengine.com/)获取
- **豆包API**: 访问[豆包开放平台](https://www.volcengine.com/product/doubao)获取

## 🚀 快速开始

### 1. 环境配置

```bash
# 安装依赖
pip install -r requirements.txt

# 配置API密钥
cp config/config.example.py config/config.py
# 编辑 config/config.py，填入你的API密钥
```

### 2. 配置化系统

项目现在支持基于Jinja2模板的配置化系统，所有prompt和配置都可以通过模板进行管理：

#### 配置文件说明
- `config/prompt_config.py`: 主配置管理文件
- `src/pic/pic_generation.j2`: 图片生成prompt模板
- `src/script/script_generation.j2`: 脚本生成prompt模板
- `src/voice/voice_config.j2`: 语音配置模板

#### 使用新的配置化模块
```python
from config.prompt_config import prompt_config, ART_STYLES, VOICE_PRESETS

# 图片生成
from src.pic.gen_pic import generate_image_with_style
generate_image_with_style("一个美丽的古代城市", style="manga")

# 语音生成
from src.voice.gen_voice import VoiceGenerator
generator = VoiceGenerator()
generator.generate_voice("测试文本", "output.mp3", preset="default")

# 脚本生成
from src.script.gen_script import ScriptGenerator
script_gen = ScriptGenerator()
script_gen.generate_script("小说内容", "output_dir")
```

### 2. 基本使用

#### 完整流程（推荐）
```bash
# 处理整个小说项目
python generate.py data/001

# 处理单个章节
python generate.py data/001/chapter_001
```

#### 分步骤处理
```bash
# 1. 生成解说文案
python gen_script.py data/001

# 2. 生成图片（推荐使用异步模式）
# 推荐方式 - 异步生成（每个章节固定30张图片：10个分镜×3张图片）
python gen_image_async.py data/001

# 单个章节生成
python gen_image_async.py data/001/chapter_001

# 单独重试失败任务
python gen_image_async.py data/001 --retry-failed

# 任务监控和下载
python check_async_tasks.py --check-once

# 持续监控直到所有任务完成
python check_async_tasks.py --monitor

# 其他选项：
# 同步生成（简单直接）
python gen_image.py data/001

# 完整流程脚本
python generate_all_images.py data/001

# 3. 生成第一个narration的视频（异步生成 video_1 和 video_2）
python gen_first_video_async.py data/001

# 检查异步视频任务状态
python check_async_tasks.py --check-once

# 4. 合并 video_1 和 video_2（加入转场特效）
python concat_first_video.py data/001

# 5. 生成音频
python gen_audio.py data/001

# 6. 生成字幕文件
python gen_ass.py data/001

# 7. 执行完整视频生成流程（推荐）
python gen_video.py data/001

# 或者分步执行：
# 7a. 合并 video_1 和 video_2（加入转场特效）
python concat_first_video.py data/001

# 7b. 生成主视频（添加旁白、BGM、音效等）
python concat_narration_video.py data/001

# 7c. 生成完整视频（添加片尾视频）
python concat_finish_video.py data/001
```

### 3. 图片生成规则

系统采用固定的图片生成规则，确保视频内容的一致性：

- **每个章节固定30张图片**：10个分镜 × 3张图片
- **智能生成策略**：
  1. 首先尝试通过API生成图片
  2. 如果API生成失败，自动从Character_Images目录复制图片补足
- **图片命名规则**：`chapter_XXX_image_YY_Z.jpeg`
  - `XXX`：章节编号（如001）
  - `YY`：分镜编号（01-10）
  - `Z`：该分镜下的图片编号（1-3）

### 4. 图片生成模式选择

#### 同步模式（推荐用于调试）
```bash
# 实时生成，立即返回结果
python gen_image.py data/001/chapter_001
```

#### 异步模式（推荐用于批量处理）
```bash
# 提交任务到队列，适合大批量处理
python gen_image_async.py data/001

# 检查异步任务状态
python check_async_tasks.py
```

### 5. 角色图片系统

系统支持基于角色属性的智能图片选择：

```
Character_Images/
├── Male/Female              # 性别
│   ├── 15-22_Youth          # 年龄段
│   │   ├── Ancient/Fantasy  # 风格
│   │   │   ├── Chinese/Western  # 文化
│   │   │   │   ├── Common/Royal # 气质
│   │   │   │   │   └── *.jpg    # 角色图片
```

#### 批量生成角色图片
```bash
# 生成所有角色类型的图片
python batch_generate_character_images.py

# 异步批量生成
python batch_generate_character_images_async.py
```

## 📋 核心功能说明

### 🤖 解说文案生成
- **智能分块**: 自动处理长文本，支持大型小说
- **多种开场**: 热开场、前提开场、冷开场
- **内容规避**: 自动规避敏感内容，确保合规
- **格式化输出**: 结构化XML格式，便于后续处理

### 🎨 AI图像生成
- **双模式支持**: 同步模式（实时）+ 异步模式（批量）
- **图片生成保障**: 智能重试机制确保每张图片都生成成功
  - 自动检测失败任务并重试
  - 支持最大重试次数配置
  - 实时任务状态监控
  - 完整的进度报告和错误日志
- **角色图片系统**: 基于属性的智能角色图片选择
- **高质量输出**: 720x1280竖屏格式，适合短视频
- **风格多样**: 支持古风、现代、奇幻、科幻等多种风格

### 🎵 语音合成
- **高质量TTS**: 火山引擎TTS服务，自然流畅
- **时间戳支持**: 精确的字符级时间戳信息
- **多种音色**: 支持不同性别和年龄的音色
- **参数可调**: 语速、音量、音调等参数可自定义

### 🎬 视频合成
- **智能字幕**: 自动居中对齐、透明背景、智能断句
- **高质量编码**: H.264视频编码，AAC音频编码
- **自动同步**: 音频、图片、字幕完美同步
- **音频混合**: 智能混合原有narration音频与BGM，确保解说声音清晰（原音频音量1.0，BGM音量0.3）
- **章节拼接**: 支持将多个narration视频按顺序拼接，自动添加随机BGM和片尾视频

## ⚠️ 注意事项

### 安全相关
1. **API密钥安全**: 请妥善保管API密钥，不要将其提交到版本控制系统
2. **配置文件**: `config.py` 文件已被添加到 `.gitignore` 中
3. **内容合规**: 系统已内置内容规避机制，确保生成内容合规

### 性能相关
1. **网络连接**: 确保网络连接稳定，API调用需要访问外部服务
2. **文件大小**: 长文本会自动分块处理，避免单次请求过大
3. **资源占用**: 视频生成过程会占用较多CPU和内存资源

### 兼容性
1. **Python版本**: 建议使用Python 3.8+以获得最佳兼容性
2. **FFmpeg版本**: 确保FFmpeg版本支持H.264编码
3. **依赖版本**: 建议使用最新版本的依赖包

## 🔧 故障排除

### 常见问题

#### 1. 环境问题
```bash
# 重新安装依赖
pip install -r requirements.txt --upgrade

# 检查FFmpeg安装
ffmpeg -version
```

#### 2. API相关
- **API调用失败**: 检查网络连接和API密钥配置
- **配额不足**: 确认API配额是否充足
- **权限错误**: 验证API密钥权限设置

#### 3. 文件处理
- **路径错误**: 确保输入文件路径正确
- **权限问题**: 检查输出目录写入权限
- **编码问题**: 确认文本文件为UTF-8编码

#### 4. 异步任务
```bash
# 检查异步任务状态
python check_async_tasks.py

# 查看任务详情
ls async_tasks/
```

### 错误代码
- `401`: API密钥错误或过期
- `403`: 权限不足或配额用尽
- `500`: 服务器内部错误
- `FileNotFoundError`: 文件路径错误

## 🛠️ 技术架构

### 核心技术栈
- **AI模型**: 豆包大模型（文案生成、图像生成）
- **语音合成**: 火山引擎TTS
- **视频处理**: FFmpeg
- **异步处理**: 任务队列系统

### 关键特性

#### 🎯 智能处理
- **智能断句**: 基于标点符号和语义的断句算法
- **角色识别**: 自动识别角色属性并匹配图片
- **内容规避**: 自动检测和规避敏感内容

#### ⚡ 性能优化
- **异步处理**: 支持大批量任务的异步处理
- **资源复用**: 图片资源智能复用机制
- **缓存机制**: 减少重复API调用

#### 🎨 视觉效果
- **高质量输出**: 720x1280竖屏格式
- **智能字幕**: 居中对齐、透明背景
- **多种风格**: 古风、现代、奇幻、科幻等

## 👨‍💻 开发说明

### 项目架构

```
核心流程:
文本输入 → 智能分割 → AI文案生成 → 图片生成 → 语音合成 → 字幕处理 → 视频合成
```

### 主要模块

- `generate.py`: 主程序入口，协调各模块工作
- `gen_script.py`: AI解说文案生成
- `gen_image.py` / `gen_image_async.py`: 图片生成（同步/异步）
- `gen_first_video_async.py`: 第一个narration视频生成（异步生成video_1和video_2）
- `gen_audio.py`: TTS语音合成
- `gen_video.py`: 视频生成流程编排器，按顺序执行三个阶段的视频处理
- `concat_first_video.py`: 第一阶段 - 合并video_1与video_2并加入转场特效
- `concat_narration_video.py`: 第二阶段 - 生成主视频（添加旁白、BGM、音效等）
- `concat_finish_video.py`: 第三阶段 - 生成完整视频（添加片尾视频）

### 扩展开发

#### 自定义配置
```python
# 在config/config.py中修改配置
IMAGE_CONFIG = {
    "default_style": "your_style",
    "size": "720x1280",
    # ... 其他配置
}
```

#### 测试
```bash
# 运行测试
python test/test_integration.py
python test/test_character_images.py
```

## 📋 项目特色

### ✨ 核心功能
- 🤖 **AI解说文案生成**: 基于豆包大模型的智能文案创作
- 🎨 **双模式图片生成**: 同步模式（实时）+ 异步模式（批量）
- 🎵 **高质量语音合成**: 火山引擎TTS，支持时间戳
- 🎬 **智能视频合成**: 音频、图片、字幕完美同步
- 👥 **角色图片系统**: 五层属性分类，智能角色匹配

### 🚀 技术亮点
- ⚡ **异步处理**: 支持大批量任务的异步处理
- 🎯 **智能断句**: 基于语义的字幕优化
- 📁 **模块化设计**: 清晰的代码结构和职责分离
- 🛡️ **内容安全**: 自动规避敏感内容
- 🔧 **配置灵活**: 丰富的自定义配置选项

## 📝 更新日志

### v3.0.0 (最新)
- 🔄 **双模式图片生成**: 新增同步/异步两种模式
- 📁 **目录结构优化**: Character_Images移至根目录
- 👥 **角色图片系统**: 完整的五层属性分类系统
- ⚡ **性能优化**: 异步处理和资源复用
- 🎯 **智能字幕**: 改进的断句和显示算法

### v2.0.0
- ✨ 智能断句功能
- 🎨 字幕样式优化
- 🛡️ 内容规避机制

### v1.0.0
- 🎉 初始版本发布
- 🤖 基础AI功能

## 🤝 贡献指南

欢迎提交Issue和Pull Request！

1. Fork本项目
2. 创建特性分支 (`git checkout -b feature/AmazingFeature`)
3. 提交更改 (`git commit -m 'Add some AmazingFeature'`)
4. 推送到分支 (`git push origin feature/AmazingFeature`)
5. 开启Pull Request

## 📄 许可证

本项目采用 MIT 许可证。详情请参阅 [LICENSE](LICENSE) 文件。

---

**⭐ 如果这个项目对你有帮助，请给个Star支持一下！**