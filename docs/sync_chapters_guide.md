# 章节数据库同步工具使用指南

## 📋 功能概述

当你使用脚本（如 `gen_script_v2.py`）生成章节文件后，这些章节只存在于文件系统中（`data/xxx/chapter_xxx/`），但Django数据库中没有对应的记录。这个工具可以自动扫描文件系统中的章节，并将它们同步到数据库中。

## 🚀 快速开始

### 方式一：使用独立脚本（推荐）

```bash
# 在项目根目录执行

# 同步所有小说的章节
python sync_chapters_to_db.py

# 同步指定小说（如小说ID=20）
python sync_chapters_to_db.py --novel-id 20

# 同步指定数据目录
python sync_chapters_to_db.py --data-dir data/020
```

### 方式二：使用Django管理命令

```bash
# 进入web目录
cd web

# 同步所有小说
python manage.py sync_chapters

# 同步指定小说
python manage.py sync_chapters --novel-id 20

# 同步指定数据目录
python manage.py sync_chapters --data-dir ../data/020
```

## 📊 功能说明

### 自动提取的信息

1. **章节标题**：从目录名提取（如 `chapter_001`）
2. **章节字数**：从 `narration.txt` 中提取所有 `<解说内容>` 标签的文字总数
3. **章节风格**：从 `<章节风格>` 标签提取（如果存在）
4. **视频路径**：自动检测章节目录下的完整视频文件（`*_complete.mp4`）

### 同步逻辑

- **Novel记录**：
  - 如果数据库中不存在，自动创建（名称为 `小说XXX`）
  - 如果已存在，使用现有记录
  - 自动更新小说的总字数

- **Chapter记录**：
  - 使用 `novel` + `title` 作为唯一标识
  - 如果不存在，创建新记录
  - 如果已存在，更新字数、风格、视频路径等信息

## 📁 目录结构要求

```
data/
├── 001/                    # 小说目录（3位数字）
│   ├── chapter_001/        # 章节目录
│   │   ├── narration.txt   # 必需：解说文案文件
│   │   ├── *_complete.mp4  # 可选：完整视频文件
│   │   └── ...
│   ├── chapter_002/
│   └── ...
├── 002/
└── ...
```

## 💡 使用场景

### 场景1：初次使用Web系统

如果你已经用脚本生成了很多章节，但Web系统中看不到：

```bash
# 一次性同步所有章节
python sync_chapters_to_db.py
```

### 场景2：新增了一个小说的章节

```bash
# 只同步这个小说
python sync_chapters_to_db.py --novel-id 25
```

### 场景3：更新了某个章节的内容

```bash
# 重新同步会自动更新字数等信息
python sync_chapters_to_db.py --data-dir data/020
```

### 场景4：定期同步

建议在以下情况后执行同步：
- 运行 `gen_script_v2.py` 生成新章节后
- 运行 `gen_video.py` 生成完整视频后
- 修改了 `narration.txt` 文件后

## 📋 输出示例

```
同步指定小说: ID=20
============================================================
✓ 找到小说记录: ID=20, 名称=无敌但是有点大病(一条幺鸡)(2)
  ✓ 创建章节: chapter_001 (字数: 904, 视频: 无)
  ✓ 创建章节: chapter_002 (字数: 895, 视频: 无)
  ✓ 更新章节: chapter_003 (字数: 1217, 视频: 有)
  ...
✓ 更新小说总字数: 52314

============================================================
同步完成！统计信息：
  创建章节数: 45
  更新章节数: 2
  跳过章节数: 0
============================================================
```

## ⚠️ 注意事项

1. **narration.txt必需**：只有包含 `narration.txt` 文件的章节目录才会被同步
2. **不会删除**：同步工具只会创建或更新记录，不会删除数据库中的章节
3. **幂等操作**：可以多次执行，不会产生重复记录
4. **视频检测**：会自动检测 `*_complete.mp4`、`complete.mp4` 或任何 `.mp4` 文件

## 🔧 高级用法

### 自定义data目录位置

```bash
# 如果你的data目录不在默认位置
python sync_chapters_to_db.py --data-root /path/to/your/data
```

### 在代码中调用

```python
import os
import sys
from pathlib import Path

# 添加项目路径
project_root = Path(__file__).parent
web_root = project_root / 'web'
sys.path.insert(0, str(web_root))

# 设置Django环境
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'web.settings')
import django
django.setup()

from video.models import Novel, Chapter

# 你的同步逻辑...
```

## 🐛 故障排除

### 问题1：找不到Django模块

```bash
# 确保在正确的conda环境中
conda activate wrmvideo

# 或确保Django已安装
pip install django
```

### 问题2：数据库连接失败

```bash
# 检查web/web/settings.py中的数据库配置
# 确保MySQL服务正在运行
```

### 问题3：章节没有被同步

检查以下几点：
- 章节目录名是否符合 `chapter_XXX` 格式
- 是否存在 `narration.txt` 文件
- `narration.txt` 文件是否包含 `<解说内容>` 标签

## 📞 获取帮助

```bash
# 查看帮助信息
python sync_chapters_to_db.py --help

# 或
cd web
python manage.py sync_chapters --help
```

