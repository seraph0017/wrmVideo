# ZIP文件中文编码修复工具

## 问题描述

当在Windows系统上创建包含中文文件名的ZIP文件，然后在macOS或Linux系统上解压时，经常会出现中文文件名显示为乱码的问题。这是由于不同操作系统使用不同的默认字符编码导致的：

- Windows通常使用GBK或GB2312编码
- macOS/Linux通常使用UTF-8编码

## 解决方案

我们提供了一个Python脚本 `fix_zip_encoding.py` 来自动检测和修复ZIP文件的中文编码问题。

## 使用方法

### 基本用法

```bash
# 自动检测编码并修复（推荐）
python fix_zip_encoding.py your_file.zip

# 指定输出目录
python fix_zip_encoding.py your_file.zip ./output_directory

# 指定编码格式
python fix_zip_encoding.py your_file.zip ./output_directory gbk

# 使用自动检测编码
python fix_zip_encoding.py your_file.zip ./output_directory auto
```

### 参数说明

1. **zip_file**: ZIP文件路径（必需）
2. **output_dir**: 输出目录（可选，默认为ZIP文件同目录下的`_fixed`文件夹）
3. **encoding**: 编码格式（可选，默认为`gbk`）
   - `gbk`: 简体中文（推荐）
   - `gb2312`: 简体中文（较老标准）
   - `big5`: 繁体中文
   - `utf-8`: UTF-8编码
   - `auto`: 自动检测编码（推荐）

## 功能特性

- ✅ 自动检测多种中文编码格式
- ✅ 支持简体中文和繁体中文
- ✅ 自动跳过macOS系统文件（`__MACOSX`目录）
- ✅ 保持原始目录结构
- ✅ 详细的处理进度显示
- ✅ 错误处理和回退机制

## 示例

### 处理本项目中的ZIP文件

```bash
# 修复data/003/2_chapters.zip文件
python fix_zip_encoding.py /Users/nathan/Projects/wrmVideo/data/003/2_chapters.zip

# 结果将保存在：/Users/nathan/Projects/wrmVideo/data/003/2_chapters_fixed/
```

### 处理结果

修复前的文件名（乱码）：
```
2_chapters/048_绗48绔 鐩哥湅濠氫簨.txt
2_chapters/219_绗219绔 闂诲傞庣殑鑰冨嵎锛氥婄儰楦璁恒.txt
```

修复后的文件名（正常）：
```
2_chapters/048_第48章 相看婚事.txt
2_chapters/219_第219章 闻如风的考卷：《烤鸭论》.txt
```

## 技术原理

1. **编码检测**: 脚本会尝试多种常见的中文编码格式
2. **字符验证**: 检查解码后的字符串是否包含有效的中文字符
3. **回退机制**: 如果自动检测失败，会使用原始文件名
4. **兼容性处理**: 特别处理Windows到Unix系统的编码转换

## 常见问题

### Q: 为什么会出现中文乱码？
A: 这是由于ZIP文件格式本身不包含编码信息，不同系统使用不同的默认编码导致的。

### Q: 哪种编码格式最好？
A: 建议使用`auto`自动检测，脚本会尝试多种编码并选择最合适的。

### Q: 如果修复后仍有乱码怎么办？
A: 可以尝试手动指定其他编码格式，如`big5`（繁体中文）或`gb2312`。

### Q: 脚本是否会修改原始ZIP文件？
A: 不会，脚本只会读取原始ZIP文件，并将修复后的内容提取到新目录中。

## 依赖要求

- Python 3.6+
- 标准库模块：`zipfile`, `os`, `sys`, `shutil`, `pathlib`

## 许可证

本工具遵循MIT许可证，可自由使用和修改。