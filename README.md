# 视频生成系统

一个基于AI的自动化视频生成系统，能够将小说文本转换为带有解说、图片和字幕的视频内容。系统集成了豆包大模型、火山引擎TTS和图像生成服务，实现从文本到视频的全自动化流程。

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
├── config/                 # 配置目录
│   └── prompt_config.py   # Prompt配置管理
├── data/                   # 数据存储目录
│   ├── 001/                # 项目数据目录
│   │   ├── chapter01/      # 章节目录
│   │   │   ├── chapter01_script.txt  # 章节脚本
│   │   │   ├── *.mp3       # 生成的音频文件
│   │   │   ├── *.jpg       # 生成的图片文件
│   │   │   ├── *.mp4       # 生成的视频片段
│   │   │   └── chapter01_complete.mp4  # 完整章节视频
│   │   └── final_complete_video.mp4    # 最终合并视频
│   └── test1/              # 测试数据目录
├── generate.py             # 主程序入口
├── requirements.txt        # 项目依赖
├── src/                    # 源代码目录
│   ├── concat.py          # 视频合成模块
│   ├── config.example.py  # 配置文件示例
│   ├── gen_pic.py         # AI图像生成模块（兼容版本）
│   ├── gen_script.py      # AI解说文案生成模块（兼容版本）
│   ├── gen_voice.py       # TTS语音合成模块（兼容版本）
│   ├── pic/               # 图片生成模块（新版本）
│   │   └── gen_pic.py
│   ├── script/            # 脚本生成模块（新版本）
│   │   └── gen_script.py
│   └── voice/             # 语音生成模块（新版本）
│       └── gen_voice.py


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

## 🚀 使用方法

### 1. 环境配置

首先安装依赖：
```bash
pip install -r requirements.txt
```

配置API密钥：
```bash
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

### 3. 快速开始

#### 准备小说文本
将小说文本保存为 `.txt` 文件，放置在项目目录中。

#### 运行主程序
```bash
python generate.py
```

程序将自动执行以下流程：
1. 📖 读取并分析小说文本
2. ✂️ 智能分割成章节
3. 🤖 生成AI解说文案
4. 🎨 生成配套图片
5. 🎵 合成语音
6. 📺 添加字幕
7. 🎬 合成最终视频

### 单独模块使用

#### 生成解说文案
```bash
cd src
python gen_script.py
```

#### 生成语音
```bash
cd src
python gen_voice.py
```

#### 生成图片（支持多种艺术风格）
```bash
cd src
python gen_pic.py
```

可选的艺术风格：
- `manga`: 漫画风格（默认）
- `realistic`: 写实风格
- `watercolor`: 水彩画风格
- `oil_painting`: 油画风格

#### 合成视频
```bash
cd src
python concat.py
```

### 批量处理

```bash
# 处理整个项目（所有章节）
python generate.py data/001

# 处理单个章节
python generate.py data/001/chapter01
```

#### 清理项目目录
```bash
python utils/init.py data/001
```

#### 艺术风格演示
```bash
# 演示所有艺术风格效果
python utils/demo_styles.py
```

## 📋 API说明

### 解说文案生成

`gen_script.py` 使用豆包模型生成详细解说文案：

- **智能分块**: 自动处理长文本
- **多种开场**: 热开场、前提开场、冷开场
- **内容规避**: 自动规避敏感内容
- **格式化输出**: XML格式，便于后续处理

### TTS语音合成

`gen_voice.py` 使用火山引擎TTS服务：

- `voice_type`: 音色类型（BV701_streaming等）
- `speed_ratio`: 语速比例（默认1.2）
- `volume_ratio`: 音量比例（默认1.0）
- `pitch_ratio`: 音调比例（默认1.0）

### AI图像生成

`gen_pic.py` 使用豆包AI模型生成图像：

- `model`: doubao-seedream-3-0-t2i-250415
- `prompt`: 图像描述文本
- `size`: 720x1280（竖屏格式）
- `watermark`: 无水印
- `style`: 艺术风格参数
  - `manga`: 漫画风格 - 动漫插画，精美细腻的画风，鲜艳色彩
  - `realistic`: 写实风格 - 真实感强，细节丰富，专业摄影质感
  - `watercolor`: 水彩画风格 - 柔和色彩，艺术感强，手绘质感
  - `oil_painting`: 油画风格 - 厚重笔触，丰富色彩层次，古典艺术感


### 视频合成

`concat.py` 使用FFmpeg合成视频：

- **智能字幕**: 自动居中对齐、透明背景
- **智能断句**: 根据标点符号优化显示
- **高质量输出**: H.264编码，AAC音频

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

#### 1. 导入错误
```bash
# 解决方案：重新安装依赖
pip install -r requirements.txt --upgrade
```

#### 2. API调用失败
- 检查网络连接
- 验证API密钥配置
- 确认API配额是否充足

#### 3. 视频生成失败
- 检查FFmpeg是否正确安装
- 确认输出目录权限
- 查看错误日志定位问题

#### 4. 字幕显示异常
- 检查字体文件是否存在
- 确认文本编码为UTF-8
- 验证字幕时间轴设置

#### 5. 音频质量问题
- 如果发现音频质量较低（采样率24kHz），可使用音频质量修复工具
- 运行 `python utils/fix_audio_quality.py <目录路径>` 自动检测和修复
- 新生成的音频将使用44.1kHz采样率和192kbps比特率

#### 6. 系统测试
- 使用 `python test/test_generate_modes.py` 验证系统功能
- 该脚本会测试单个章节和多章节处理模式
- 自动检查音频质量和显示使用示例

### 错误代码

- `401 Unauthorized`: API密钥错误或过期
- `403 Forbidden`: 权限不足或配额用尽
- `500 Internal Server Error`: 服务器内部错误，请稍后重试
- `FileNotFoundError`: 文件路径错误或文件不存在

## 🛠️ 技术实现

### 核心技术栈
- **AI模型**: 豆包大模型（文案生成、图像生成）
- **语音合成**: 火山引擎TTS
- **视频处理**: FFmpeg
- **字幕处理**: 自研字幕引擎

### 优化特性

#### 智能断句算法
- 基于标点符号的断句逻辑
- 语义完整性保护
- 字幕长度自适应调整

#### 多音频共图优化
- 图片资源复用机制
- 减少API调用次数
- 提升生成效率

#### 多种艺术风格系统
- 四种预设艺术风格：漫画、写实、水彩、油画
- 可配置的默认风格设置
- 智能prompt模板系统

#### 字幕样式优化
- 居中对齐算法
- 透明背景处理
- 首尾标点符号清理

### 性能指标
- **处理速度**: 相比优化前提升约30%
- **资源利用**: 图片生成调用减少50%
- **字幕质量**: 显示效果显著改善

## 👨‍💻 开发说明

### 项目架构

```
核心流程:
文本输入 → 智能分割 → AI文案生成 → 图片生成 → 语音合成 → 字幕处理 → 视频合成
```

### 模块说明

- `generate.py`: 主程序入口，协调各模块工作
- `src/script/gen_script.py`: AI解说文案生成，支持长文本分块处理
- `src/voice/gen_voice.py`: TTS语音合成，支持多种音色
- `src/pic/gen_pic.py`: AI图像生成，支持高质量图片输出
- `src/concat.py`: 视频合成，集成字幕处理
- `init.py`: 项目清理工具，支持批量清理

### 扩展开发

#### 添加新功能模块
1. 在 `src/` 目录下创建新模块
2. 在 `config.py` 中添加相应配置
3. 更新 `requirements.txt` 添加新依赖
4. 在 `generate.py` 中集成新功能

#### 自定义字幕样式
```python
# 在concat.py中修改字幕参数
subtitle_style = {
    'fontsize': 24,
    'fontcolor': 'white',
    'box': 1,
    'boxcolor': 'black@0.5'
}
```

#### 自定义艺术风格
```python
# 在generate.py中的ART_STYLES字典中添加新风格
ART_STYLES = {
    'your_style': (
        "你的风格描述，详细的艺术风格prompt，"
        "包含色彩、质感、技法等描述，"
    ),
    # ... 其他风格
}
```

然后在配置文件中设置默认风格：
```python
IMAGE_CONFIG = {
    "default_style": "your_style",  # 使用你的自定义风格
    # ... 其他配置
}
```

#### 添加新的音色
```python
# 在config.py中添加音色配置
VOICE_TYPES = {
    'female': 'BV701_streaming',
    'male': 'BV700_streaming',
    'child': 'BV702_streaming'
}
```

### 测试框架

项目包含完整的测试套件：
- `test/test_audio.py`: 音频生成测试
- `test/test_subtitle.py`: 字幕功能测试
- `test/test_split.py`: 文本分割测试
- `test/test_optimized_features.py`: 优化功能测试
- `test/test_config_system.py`: 配置系统测试

## 📋 项目总结

### 已完成功能

#### 核心功能
- ✅ **AI解说文案生成**：基于豆包大模型的智能文案创作
- ✅ **TTS语音合成**：高质量语音生成，支持多种音色
- ✅ **AI图像生成**：多风格图片生成，支持漫画、写实等风格
- ✅ **视频自动合成**：音频、图片、字幕的智能合成
- ✅ **多章节处理**：支持长篇小说的分章节处理

#### 配置化系统重构 🆕
- ✅ **Jinja2模板系统**：基于模板的prompt管理
- ✅ **配置集中管理**：统一的配置文件和参数管理
- ✅ **模块化架构**：独立的图片、语音、脚本生成模块
- ✅ **向后兼容性**：保持原有API的兼容性
- ✅ **配置验证系统**：完整的配置测试和验证

#### 优化功能
- ✅ **音频质量提升**：优化TTS参数，提高音频清晰度
- ✅ **视频合成优化**：改进编码参数，提升视频质量

- ✅ **错误处理机制**：完善的异常处理和日志记录
- ✅ **测试验证系统**：全面的功能测试脚本

#### 工具和辅助功能
- ✅ **音频质量修复工具**：`utils/fix_audio_quality.py`
- ✅ **生成模式测试**：`test/test_generate_modes.py`
- ✅ **配置系统测试**：`test/test_config_system.py`
- ✅ **项目初始化工具**：`utils/init.py`
- ✅ **样式演示脚本**：`utils/demo_styles.py`

## 📝 更新日志

### v2.0.0 (最新)
- ✨ 新增智能断句功能
- 🎨 优化字幕样式（居中对齐、透明背景）
- ⚡ 实现多音频共图优化
- 🛡️ 增强内容规避机制
- 📈 性能提升30%

### v1.0.0
- 🎉 初始版本发布
- 🤖 基础AI文案生成
- 🎵 TTS语音合成
- 🎨 AI图像生成
- 🎬 视频合成功能

## 🤝 贡献指南

欢迎提交Issue和Pull Request！

1. Fork本项目
2. 创建特性分支 (`git checkout -b feature/AmazingFeature`)
3. 提交更改 (`git commit -m 'Add some AmazingFeature'`)
4. 推送到分支 (`git push origin feature/AmazingFeature`)
5. 开启Pull Request

## 📄 许可证

本项目采用 MIT 许可证。详情请参阅 [LICENSE](LICENSE) 文件。

## 📞 联系方式

如有问题或建议，请通过以下方式联系：
- 提交 [Issue](https://github.com/your-repo/issues)
- 发送邮件至：your-email@example.com

---

**⭐ 如果这个项目对你有帮助，请给个Star支持一下！**