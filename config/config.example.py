# TTS配置示例
TTS_CONFIG = {
    "appid": "your_appid_here",
    "access_token": "your_access_token_here",
    "cluster": "volcano_tts",
    "voice_type": "BV701_streaming",
    "host": "openspeech.bytedance.com"
}

# Ark配置示例
ARK_CONFIG = {
    "base_url": "https://ark.cn-beijing.volces.com/api/v3",
    "api_key": "your_api_key_here"
}

# 图片生成配置
IMAGE_CONFIG = {
    "default_style": "manga",  # 默认艺术风格: manga, realistic, watercolor, oil_painting
    "size": "720x1280",       # 图片尺寸（竖屏格式）
    "watermark": False,       # 是否添加水印
    "model": "doubao-seedream-3-0-t2i-250415"  # 使用的图像生成模型
}