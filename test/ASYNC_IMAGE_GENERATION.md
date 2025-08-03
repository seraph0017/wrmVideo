# 异步图片生成系统使用说明

## 概述

本系统已升级为异步图片生成模式，提高了处理效率和系统稳定性。图片生成任务将提交到火山引擎的异步API，然后通过独立的检查工具来获取生成结果。

## 主要变化

### 1. 异步任务提交
- `gen_image.py` 中的 `generate_image_with_character()` 函数现在提交异步任务而不是同步等待
- 任务信息保存在 `async_tasks/` 目录下，每个任务一个 JSON 文件
- 函数返回任务提交是否成功，而不是图片生成是否成功

### 2. 任务信息存储
每个提交的任务会在 `async_tasks/` 目录下创建一个以 `task_id` 命名的 JSON 文件，包含：
```json
{
  "task_id": "任务ID",
  "output_path": "图片保存路径",
  "filename": "文件名",
  "prompt": "原始提示词",
  "full_prompt": "完整提示词",
  "character_images": ["角色图片路径列表"],
  "style": "艺术风格",
  "submit_time": 1234567890.123,
  "status": "submitted"
}
```

### 3. 任务状态检查
使用 `check_async_tasks.py` 脚本来检查和处理异步任务：

#### 命令行模式
```bash
# 检查一次所有任务状态
python check_async_tasks.py --check-once

# 持续监控任务状态（每30秒检查一次）
python check_async_tasks.py --monitor

# 自定义监控间隔（每60秒检查一次）
python check_async_tasks.py --monitor --interval 60

# 指定任务目录
python check_async_tasks.py --check-once --tasks-dir custom_tasks
```

#### 交互式模式
```bash
python check_async_tasks.py
```
然后根据提示选择运行模式。

## 使用流程

### 1. 生成图片（提交任务）
```bash
# 使用现有的图片生成脚本
python gen_image.py [参数]

# 或者使用测试脚本
python test_async_image.py
```

### 2. 检查任务状态
```bash
# 快速检查一次
python check_async_tasks.py --check-once

# 持续监控直到完成
python check_async_tasks.py --monitor
```

### 3. 获取结果
- 完成的任务会自动下载图片到指定的 `output_path`
- 任务状态会更新为 `completed`
- 失败的任务状态会更新为 `failed`

## 任务状态说明

- **submitted**: 已提交，等待处理
- **processing**: 正在处理中
- **completed**: 已完成，图片已下载
- **failed**: 处理失败

## 目录结构

```
project/
├── async_tasks/          # 异步任务信息目录
│   ├── task_id_1.txt    # 任务1信息
│   ├── task_id_2.txt    # 任务2信息
│   └── ...
├── gen_image.py         # 图片生成脚本（异步版本）
├── check_async_tasks.py # 任务状态检查脚本
└── test_async_image.py  # 测试脚本
```

## 优势

1. **提高效率**: 可以批量提交多个任务，无需等待单个任务完成
2. **增强稳定性**: 避免长时间等待导致的超时问题
3. **更好的监控**: 可以随时查看任务进度和状态
4. **容错能力**: 失败的任务可以单独重试
5. **资源优化**: 减少API调用的阻塞时间

## 注意事项

1. 确保 `async_tasks/` 目录有写入权限
2. 任务文件包含敏感信息，注意保护
3. 定期清理已完成的任务文件以节省空间
4. 监控模式下使用 Ctrl+C 可以安全退出
5. 网络问题可能导致任务状态查询失败，可以稍后重试

## 兼容性

- 保留了原有的 `generate_image_with_character()` 函数名，现在内部调用异步版本
- 现有的调用代码无需修改，但行为已改为异步提交
- 返回值含义已改变：`True` 表示任务提交成功，`False` 表示提交失败

## 故障排除

### 任务提交失败
- 检查API配置是否正确
- 确认网络连接正常
- 查看错误日志

### 任务状态查询失败
- 检查任务ID是否有效
- 确认API访问权限
- 重试查询操作

### 图片下载失败
- 检查输出目录权限
- 确认磁盘空间充足
- 验证图片数据完整性