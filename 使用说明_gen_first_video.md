# gen_first_video.py 使用说明

这个脚本支持两种模式来生成视频：

## 模式1：批量处理模式（原有功能）

处理指定数据目录下的所有章节，为每个章节自动选择前两张图片生成视频。

```bash
python gen_first_video.py <数据目录>
```

示例：
```bash
python gen_first_video.py data/002
```

## 模式2：单个视频生成模式（新增功能）

使用指定的两张图片生成单个视频。

```bash
python gen_first_video.py <第一张图片> <第二张图片> <输出视频路径>
```

示例：
```bash
# 使用绝对路径
python gen_first_video.py /Users/xunan/Projects/wrmProject/data/003/chapter_001/image1.jpeg /Users/xunan/Projects/wrmProject/data/003/chapter_001/image2.jpeg output_video.mp4

# 使用相对路径
python gen_first_video.py data/003/chapter_001/chapter_001_image_01.jpeg data/003/chapter_001/chapter_001_image_02.jpeg test_video.mp4
```

## 注意事项

1. **API配置**：使用前请确保在 `config/config.py` 中正确配置了 `ARK_CONFIG['api_key']`

2. **图片文件**：
   - 支持的图片格式：.jpg, .jpeg, .png, .gif, .bmp
   - 确保指定的图片文件存在且可读
   - 图片文件路径可以是相对路径或绝对路径

3. **输出目录**：
   - 如果输出路径的目录不存在，脚本会自动创建
   - 建议使用 .mp4 作为输出文件扩展名

4. **视频参数**：
   - 默认视频时长：10秒
   - 转场效果：慢慢过渡转场

## 当前状态检查

根据检查，`data/003/chapter_001/` 目录中目前没有图片文件。如果您想测试单个视频生成功能，您需要：

1. 先运行图片生成脚本来创建图片：
   ```bash
   python gen_image.py data/003
   ```

2. 或者使用其他已存在的图片文件进行测试

3. 或者将您想要使用的图片文件复制到相应目录中

## 测试脚本

我们还创建了一个测试脚本 `test_single_video.py`，您可以修改其中的图片路径来测试功能：

```bash
python test_single_video.py
```

在运行测试脚本之前，请确保修改脚本中的图片路径指向实际存在的图片文件。