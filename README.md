# WRM Video 项目

一个基于火山引擎的多媒体内容生成工具，支持文本转语音(TTS)和文本生成图像功能。

## 功能特性

- **文本转语音(TTS)**: 使用火山引擎TTS服务将文本转换为高质量音频
- **文本生成图像**: 使用豆包AI模型根据文本描述生成图像
- **配置管理**: 统一的配置文件管理，支持敏感信息保护

## 项目结构

```
wrmVideo/
├── src/
│   ├── main.py           # 图像生成主程序
│   ├── tts.py            # 文本转语音程序
│   ├── config.py         # 配置文件(需要自行创建)
│   └── config.example.py # 配置文件示例
├── test_data/
│   └── list.txt          # 测试数据
├── .gitignore
└── README.md
```

## 环境要求

- Python 3.6 或更高版本
- 火山引擎 TTS API 访问权限
- 火山引擎 Ark API 访问权限

## 安装依赖

```bash
pip install requests
pip install 'volcengine-python-sdk[ark]'
```

## 配置设置

1. 复制配置示例文件：
```bash
cp src/config.example.py src/config.py
```

2. 编辑 `src/config.py` 文件，填入你的API密钥：

```python
# TTS配置
TTS_CONFIG = {
    "appid": "你的应用ID",
    "access_token": "你的访问令牌",
    "cluster": "volcano_tts",
    "voice_type": "BV701_streaming",
    "host": "openspeech.bytedance.com"
}

# Ark配置
ARK_CONFIG = {
    "base_url": "https://ark.cn-beijing.volces.com/api/v3",
    "api_key": "你的API密钥"
}
```

## 使用方法

### 文本生成图像

运行图像生成程序：

```bash
cd src
python main.py
```

程序将根据预设的文本描述生成图像，并输出图像URL。

### 文本转语音

运行TTS程序：

```bash
cd src
python tts.py
```

程序将把预设的文本转换为MP3音频文件 `test2_submit.mp3`。

## API说明

### TTS API参数

- `voice_type`: 语音类型，默认为 "BV701_streaming"
- `encoding`: 音频编码格式，支持 "mp3"
- `speed_ratio`: 语速比例，默认为 1.0
- `volume_ratio`: 音量比例，默认为 1.0
- `pitch_ratio`: 音调比例，默认为 1.0

### 图像生成API参数

- `model`: 使用的模型，默认为 "doubao-seedream-3-0-t2i-250415"
- `size`: 图像尺寸，默认为 "720x1280"
- `watermark`: 是否添加水印，默认为 false

## 注意事项

1. **配置文件安全**: `config.py` 文件包含敏感信息，已添加到 `.gitignore` 中，不会被提交到版本控制
2. **API限制**: 请注意火山引擎API的调用频率限制和费用
3. **文件输出**: TTS生成的音频文件会保存在当前目录下

## 故障排除

### 常见问题

1. **配置文件未找到**
   - 确保已创建 `src/config.py` 文件
   - 检查配置文件路径是否正确

2. **API调用失败**
   - 验证API密钥是否正确
   - 检查网络连接
   - 确认API服务状态

3. **依赖包安装失败**
   - 使用 `pip install --upgrade pip` 更新pip
   - 尝试使用虚拟环境

## 开发说明

如需修改文本内容或调整参数，请直接编辑对应的Python文件。项目采用模块化设计，配置与业务逻辑分离，便于维护和扩展。

## 许可证

本项目仅供学习和研究使用。使用火山引擎API时请遵守相关服务条款。