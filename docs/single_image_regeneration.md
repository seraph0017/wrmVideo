# 单图片重新生成功能说明

## 功能概述

为章节详情页增加了单张图片重新生成能力，用户可以在Web界面中对任意图片点击"重新生成"按钮，系统会异步重新生成该图片。

## 核心改动

### 1. gen_image_async_v4.py 支持单图片模式

#### 新增参数
- `--scene <场景编号>`: 指定生成单个场景的图片（1-based索引）

#### 使用示例

```bash
# 生成整个章节的所有图片（原有功能）
python gen_image_async_v4.py data/020/chapter_002

# 只生成第1个场景的图片（新功能）
python gen_image_async_v4.py data/020/chapter_002 --scene 1

# 指定API地址
python gen_image_async_v4.py data/020/chapter_002 --scene 3 --api_url http://115.190.186.199:8188/api/prompt
```

#### 配置集成
- API地址自动从`config/config.py`的`COMFYUI_CONFIG`读取
- 默认使用`COMFYUI_CONFIG['default_host']`作为ComfyUI主机地址
- 支持通过`--api_url`参数覆盖配置

#### 智能覆盖
- 单图片模式（指定`--scene`）下，即使图片文件已存在也会重新生成
- 批量模式（不指定`--scene`）下，跳过已存在的图片文件

### 2. Celery任务优化

#### regenerate_single_image_task
- 位置：`web/video/tasks.py`
- 改动：直接调用`gen_image_async_v4.py --scene`而不是单独的脚本
- 优势：
  - 复用现有的完整逻辑（角色解析、prompt构建、ComfyUI客户端）
  - 减少代码重复
  - 统一维护入口

#### 命令示例
```python
cmd = [
    sys.executable,
    str(gen_image_script),  # gen_image_async_v4.py
    str(chapter_dir),
    '--scene', str(scene_number),
    '--workflow_json', str(workflow_json),
]
```

### 3. Web界面集成

#### 章节详情页 (chapter_detail.html)
- 每个narration行都有"重新生成"按钮
- 点击后调用`regenerateImage()`函数
- 函数流程：
  1. 发送POST请求到`/video/api/chapters/regenerate-single-image/`
  2. 后端提交Celery任务
  3. 前端轮询任务状态
  4. 任务完成后自动刷新页面

#### API端点
- URL: `/video/api/chapters/regenerate-single-image/`
- 方法: POST
- 参数:
  ```json
  {
    "novel_id": 20,
    "chapter_title": "chapter_002",
    "scene_number": 1
  }
  ```
- 响应:
  ```json
  {
    "success": true,
    "task_id": "1684542b-ad2c-42c4-8517-1d43c05114bf",
    "message": "场景 1 图片重新生成任务已提交"
  }
  ```

## 技术细节

### process_chapter_with_comfyui 函数改动

```python
def process_chapter_with_comfyui(
    chapter_dir: str, 
    client: ComfyUIClient, 
    workflow_template: Dict, 
    poll_interval: float, 
    max_wait: int, 
    delay_between_requests: float = 1.0, 
    scene_number: Optional[int] = None  # 新增参数
) -> int:
```

#### 逻辑分支
- 如果`scene_number is not None`：
  - 只处理指定的场景
  - 即使文件存在也重新生成
  - 返回成功生成的数量（0或1）
- 如果`scene_number is None`：
  - 遍历所有场景
  - 跳过已存在的图片文件
  - 返回成功生成的总数

### 配置文件 (config/config.py)

```python
COMFYUI_CONFIG = {
    "default_host": "115.190.186.199:8188",
    "timeout": 300,
    "poll_interval": 1.0
}
```

### main函数改动

```python
parser.add_argument(
    '--api_url', 
    default=f"http://{COMFYUI_CONFIG['default_host']}/api/prompt",
    help='ComfyUI api/prompt 地址'
)
parser.add_argument(
    '--scene', 
    type=int, 
    help='指定生成单个场景编号（单图片模式）'
)
```

## 测试验证

### 测试命令
```bash
cd /Users/xunan/Projects/wrmVideo
/Users/xunan/miniconda3/envs/wrmVideo/bin/python \
  gen_image_async_v4.py data/020/chapter_002 --scene 1
```

### 测试结果
```
2025-11-12 08:37:33,993 - INFO - 加载工作流模板: test/comfyui/image_compact.json
2025-11-12 08:37:33,993 - INFO - ComfyUI API 地址: http://115.190.186.199:8188/api/prompt
2025-11-12 08:37:33,993 - INFO - 单图片模式：将生成场景 1
2025-11-12 08:37:33,994 - INFO - 开始处理章节: data/020/chapter_002
2025-11-12 08:37:33,994 - INFO - 解析到 10 个角色
2025-11-12 08:37:33,994 - INFO - 解析到 21 个场景镜头
2025-11-12 08:37:33,995 - INFO - 单图片模式：只生成场景 1
2025-11-12 08:37:34,077 - INFO - prompt_id: 6d582adb-8bc6-4aa7-b307-fff27f134398
2025-11-12 08:38:49,298 - INFO - 获取到输出文件: ComfyUI_02027_.png (subfolder=, type=output)
2025-11-12 08:38:49,843 - INFO - 文件已下载到: data/020/chapter_002/chapter_002_image_01.jpeg
2025-11-12 08:38:49,844 - INFO - ✓ Prompt信息已保存到: data/020/chapter_002/chapter_002_image_01.prompt.json
2025-11-12 08:38:49,844 - INFO - ✓ 场景 1 图片生成成功: data/020/chapter_002/chapter_002_image_01.jpeg
2025-11-12 08:38:50,846 - INFO - 章节 data/020/chapter_002 处理完成，成功生成 1/21 张图片
```

### 生成文件验证
```bash
$ ls -lh data/020/chapter_002/chapter_002_image_01.*
-rw-r--r--@ 1 xunan  staff   1.2M Nov 12 08:38 chapter_002_image_01.jpeg
-rw-r--r--@ 1 xunan  staff   799B Nov 12 08:38 chapter_002_image_01.prompt.json

$ cat data/020/chapter_002/chapter_002_image_01.prompt.json
{
  "image_file": "chapter_002_image_01.jpeg",
  "prompt": "画面风格是强调强烈线条、鲜明对比和现代感造型，色彩饱和，带有动态夸张与都市叙事视觉冲击力的国风漫画风格。一位男性，面容威武，眼神坚毅，黑色束发，中等身材，体态端正，身着宋朝圆领袍，深色，丝质，领口高立, 同色系长裤，束脚, 腰带，无其他饰品。古风玄幻风格，宋朝背景，中年男子陆川，短发黑发，面部有皱纹眼神锐利，身穿深蓝色圆领长袍长袖，站在庭院石桌旁，右手抬起作踢物状，表情严肃，背景有躺椅和竹林，日光充足，单人特写，上半身构图。",
  "timestamp": "2025-11-12T08:38:49.843689",
  "workflow": "image_compact.json",
  "scene_number": 1
}
```

## 用户体验

### 操作流程
1. 用户进入章节详情页
2. 查看narration列表，每行显示图片缩略图、音频、字幕和prompt信息
3. 对不满意的图片点击"重新生成"按钮
4. 按钮变为"生成中..."状态，禁用点击
5. 后台Celery任务开始执行
6. 前端每3秒轮询任务状态
7. 任务完成后，页面自动刷新，显示新图片

### 优势
- **无需手动删除文件**：系统自动覆盖
- **异步处理**：不阻塞Web界面
- **实时反馈**：按钮状态变化 + 自动刷新
- **完整Prompt**：使用与批量生成相同的prompt构建逻辑
- **统一配置**：从config.py读取ComfyUI地址

## 注意事项

### 1. 场景编号
- 场景编号从1开始，与narration.txt中的`<图片特写X>`标签一致
- 场景编号必须在有效范围内（1 到场景总数）

### 2. Conda环境
- Celery任务使用`sys.executable`，会自动使用正确的Python环境
- 手动执行脚本时，需要激活wrmVideo环境：
  ```bash
  /Users/xunan/miniconda3/envs/wrmVideo/bin/python gen_image_async_v4.py ...
  ```

### 3. 多章节限制
- 单图片模式（`--scene`）只能用于单个章节目录
- 如果传入数据目录（如`data/020`）且指定`--scene`，会报错：
  ```
  单图片模式（--scene）只能用于单个章节目录，不支持数据目录
  ```

### 4. 网络访问
- 需要能访问ComfyUI API（默认：115.190.186.199:8188）
- 确保防火墙允许相关端口

## 相关文件

### 修改的文件
1. `gen_image_async_v4.py` - 添加单图片模式支持
2. `web/video/tasks.py` - 更新regenerate_single_image_task
3. `web/templates/video/chapter_detail.html` - 前端界面和JavaScript
4. `web/video/views.py` - regenerate_single_image API端点
5. `web/video/urls.py` - URL路由配置
6. `README.md` - 功能文档更新

### 配置文件
- `config/config.py` - COMFYUI_CONFIG配置

### 测试文件
- 测试章节：`data/020/chapter_002`
- 测试场景：scene 1
- 工作流JSON：`test/comfyui/image_compact.json`

## 未来优化方向

1. **进度显示**：在Web界面显示图片生成的实时进度（如"正在解析角色...""正在生成图片..."）
2. **批量重新生成**：支持选择多个场景批量重新生成
3. **Prompt编辑**：允许用户在重新生成前编辑prompt
4. **历史版本**：保存每次生成的图片历史版本，方便对比
5. **质量评分**：AI自动评估生成图片的质量，提示是否需要重新生成

