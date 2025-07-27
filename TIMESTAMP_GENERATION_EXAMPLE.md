# 时间戳生成功能使用说明

## 概述

`gen_audio.py` 脚本已经更新，现在可以从真实的TTS API响应中提取精确的字符级时间戳信息，而不是使用模拟的估算值。

## 真实API响应格式

脚本现在支持以下格式的API响应：

```json
{
    "reqid": "reqid",
    "code": 3000,
    "operation": "query",
    "message": "Success",
    "sequence": -1,
    "data": "base64 encoded binary data",
    "addition": {
        "description": "...",
        "duration": "1960",
        "frontend": "{
            \"words\": [{
                \"word\": \"字\",
                \"start_time\": 0.025,
                \"end_time\": 0.185
            },
            ...
            {
                \"word\": \"。\",
                \"start_time\": 1.85,
                \"end_time\": 1.955
            }],
            \"phonemes\": [...]
        }"
    }
}
```

## 生成的时间戳文件格式

脚本会生成如下格式的时间戳JSON文件：

```json
{
    "text": "原始文本内容",
    "audio_file": "音频文件路径",
    "duration": 实际音频时长（秒）,
    "character_timestamps": [
        {
            "character": "字",
            "start_time": 0.025,
            "end_time": 0.185
        },
        {
            "character": "符",
            "start_time": 0.185,
            "end_time": 0.345
        }
        // ... 更多字符
    ],
    "generated_at": "2025-07-19T17:53:08.670768"
}
```

## 主要改进

1. **真实时间戳**: 从TTS API的实际响应中提取精确的字符级时间戳
2. **准确时长**: 使用API返回的实际音频时长，而不是估算值
3. **错误处理**: 如果API响应解析失败，会自动回退到估算方式
4. **向后兼容**: 保持与现有时间戳文件格式的兼容性

## 使用方法

```bash
# 为单个章节生成语音和时间戳
python gen_audio.py data/003/chapter_001

# 为整个系列生成语音和时间戳
python gen_audio.py data/003
```

## 技术细节

### VoiceGenerator 新增方法

- `generate_voice_with_timestamps()`: 生成语音文件并返回包含API响应的完整结果
- 返回格式包含：
  - `success`: 是否生成成功
  - `output_path`: 输出文件路径
  - `api_response`: 完整的API响应数据
  - `error_message`: 错误信息（如果有）

### 时间戳解析逻辑

1. 从API响应的 `addition.frontend` 字段解析JSON数据
2. 提取 `words` 数组中的字符级时间戳
3. 如果解析失败，自动回退到基于音频时长的估算方式
4. 保存为标准的时间戳JSON格式

## 注意事项

- 确保TTS API配置正确，包括access_token等认证信息
- API响应中的 `duration` 字段单位为毫秒，脚本会自动转换为秒
- `frontend` 字段可能是字符串格式的JSON，脚本会自动处理解析
- 如果API响应格式发生变化，脚本会自动回退到估算模式，确保功能正常