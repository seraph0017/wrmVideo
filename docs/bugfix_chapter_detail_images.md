# 章节详情页图片和Prompt显示问题修复

## 问题描述

在章节详情页面（`/video/chapters/<chapter_id>/`），图片和Prompt无法正常显示，表现为：
- 图片列显示为空或显示"无"
- Prompt列显示"加载中..."或"--"

## 问题分析

### 根本原因

文件路径构建逻辑存在错误，导致URL中包含重复的`data/`前缀。

### 详细分析

1. **原始代码逻辑**（有问题）：
   ```python
   # 在 ChapterDetailView.get_context_data() 中
   audio_rel_path = os.path.relpath(audio_file, project_root)
   # 结果: 'data/020/chapter_002/chapter_002_image_01.jpeg'
   ```

2. **URL生成**：
   ```django
   {% url 'video:serve_data_file' file_path=narration.image_path %}
   ```
   - URL路由: `path('data/<path:file_path>', views.serve_data_file)`
   - 生成的URL: `/data/data/020/chapter_002/chapter_002_image_01.jpeg`（重复了data）

3. **serve_data_file处理**：
   ```python
   full_path = project_root / 'data' / file_path
   # file_path = 'data/020/chapter_002/...'
   # 最终路径: project_root/data/data/020/... (错误！)
   ```

## 修复方案

### 修改内容

修改 `web/video/views.py` 中的 `ChapterDetailView.get_context_data()` 方法：

```python
# 修改前（第659-662行）
audio_rel_path = os.path.relpath(audio_file, project_root)
subtitle_rel_path = os.path.relpath(subtitle_file, project_root) if subtitle_file and subtitle_file.exists() else None
image_rel_path = os.path.relpath(image_files[0], project_root) if image_files else None

# 修改后
data_dir = project_root / 'data'
audio_rel_path = os.path.relpath(audio_file, data_dir)
subtitle_rel_path = os.path.relpath(subtitle_file, data_dir) if subtitle_file and subtitle_file.exists() else None
image_rel_path = os.path.relpath(image_files[0], data_dir) if image_files else None
```

### 修复后的路径流程

1. **路径构建**：
   ```python
   image_rel_path = '020/chapter_002/chapter_002_image_01.jpeg'
   ```

2. **URL生成**：
   ```
   /data/020/chapter_002/chapter_002_image_01.jpeg
   ```

3. **serve_data_file处理**：
   ```python
   full_path = project_root / 'data' / '020/chapter_002/chapter_002_image_01.jpeg'
   # 正确的路径！
   ```

4. **JavaScript Prompt加载**：
   ```javascript
   // 从img.src提取: 'data/020/chapter_002/chapter_002_image_01.jpeg'
   // Prompt URL: '/data/020/chapter_002/chapter_002_image_01.prompt.json'
   ```

## 测试方法

### 1. 启动Web服务器

```bash
cd /Users/xunan/Projects/wrmVideo/web
python manage.py runserver
```

### 2. 访问章节详情页

访问URL: `http://localhost:8000/video/chapters/<chapter_id>/`

例如: `http://localhost:8000/video/chapters/2/`（对应小说020的chapter_002）

### 3. 验证功能

- [ ] **图片显示**: 每个narration行的图片列应该显示缩略图
- [ ] **Prompt显示**: Prompt列应该显示提示词内容（可能会截断）
- [ ] **音频播放**: 点击音频播放器应该能正常播放
- [ ] **字幕查看**: 点击"查看"按钮应该能显示字幕内容
- [ ] **图片放大**: 点击图片应该能在模态框中查看大图和完整Prompt

### 4. 浏览器控制台检查

打开浏览器开发者工具（F12），检查Console标签：

**正常情况应该看到**：
```
找到 21 个narration行
Narration 1 图片URL: /data/020/chapter_002/chapter_002_image_01.jpeg?t=...
Narration 1 相对路径: data/020/chapter_002/chapter_002_image_01.jpeg
加载Narration 1 的prompt: /data/020/chapter_002/chapter_002_image_01.prompt.json
Narration 1 prompt已加载
```

**如果出现错误**：
- 404错误: 检查文件路径是否正确
- 网络错误: 检查serve_data_file视图是否正常工作

### 5. 网络请求检查

在浏览器开发者工具的Network标签中，检查：

- 图片请求: `/data/020/chapter_002/chapter_002_image_01.jpeg`
  - 状态码应该是200
  - Content-Type应该是`image/jpeg`

- Prompt请求: `/data/020/chapter_002/chapter_002_image_01.prompt.json`
  - 状态码应该是200
  - Content-Type应该是`application/json`

## 影响范围

此修复影响以下功能：

1. ✅ 章节详情页的图片显示
2. ✅ 章节详情页的Prompt显示和编辑
3. ✅ 章节详情页的音频播放
4. ✅ 章节详情页的字幕查看
5. ✅ 图片放大查看功能
6. ✅ 单张图片重新生成功能

## 相关文件

- `web/video/views.py` - ChapterDetailView.get_context_data()
- `web/video/views.py` - serve_data_file()
- `web/templates/video/chapter_detail.html` - 前端模板和JavaScript
- `web/video/urls.py` - URL路由配置

## 注意事项

1. **路径一致性**: 确保所有使用`serve_data_file`的地方都使用相对于`data/`目录的路径
2. **URL路由**: URL路由中已经包含了`data/`前缀，视图中不应再次包含
3. **JavaScript兼容**: 前端JavaScript代码会从完整URL中提取路径，需要确保格式一致

## 验证脚本

可以使用以下Python脚本验证路径构建逻辑：

```python
from pathlib import Path
import os

project_root = Path('/Users/xunan/Projects/wrmVideo')
data_dir = project_root / 'data'
image_file = project_root / 'data' / '020' / 'chapter_002' / 'chapter_002_image_01.jpeg'

# 构建相对路径
image_rel_path = os.path.relpath(image_file, data_dir)
print(f'image_rel_path: {image_rel_path}')

# 验证serve_data_file路径
full_path = project_root / 'data' / image_rel_path
print(f'完整路径: {full_path}')
print(f'文件存在: {full_path.exists()}')
```

## 版本信息

- 修复日期: 2025-11-15
- 修复版本: v1.0.1
- 相关Issue: 章节详情页图片和Prompt显示问题

