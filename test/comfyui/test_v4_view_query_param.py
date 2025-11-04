#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
单元测试：验证 v4 客户端在 /api/view 下载请求中包含路由标识参数

目的：
- 确认 `download_view_file_as` 会在构造的 URL 上追加 `image=<chapter_xxx_image_xx.jpeg>` 参数
- 保持与实际下载文件名参数 `filename=<ComfyUI_XXXX.png>` 不冲突
"""

import os
import shutil
from typing import Optional
from pathlib import Path
import sys

# 将仓库根目录加入PYTHONPATH，保证可导入顶层脚本
ROOT = Path(__file__).resolve().parents[2]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from gen_image_async_v4 import ComfyUIClient


class _FakeResponse:
    def __init__(self, status_code: int = 200):
        self.status_code = status_code

    def iter_content(self, chunk_size: int):
        yield b"test"


def test_view_url_includes_image_param(tmp_path):
    client = ComfyUIClient(api_url="http://127.0.0.1:8188/api/prompt", timeout=5)

    captured_url: Optional[str] = None

    def fake_get(url, stream=True, timeout=None):
        nonlocal captured_url
        captured_url = url
        return _FakeResponse(200)

    # 替换 session.get 以捕获最终请求 URL
    client.session.get = fake_get

    save_dir = tmp_path / "downloads"
    save_as = "chapter_001_image_01.jpeg"

    # 执行下载（不会真实发起网络请求）
    local_path = client.download_view_file_as(
        filename="ComfyUI_00001.png",
        subfolder="",
        type_="output",
        save_dir=str(save_dir),
        save_as=save_as,
        filename_param="chapter_001_image_01.jpeg",
    )

    # 断言URL包含路由参数及真实文件名参数
    assert captured_url is not None
    assert "/api/view?" in captured_url
    assert "filename=ComfyUI_00001.png" in captured_url
    assert "image=chapter_001_image_01.jpeg" in captured_url

    # 清理生成的临时文件
    if local_path and os.path.exists(local_path):
        os.remove(local_path)
    if os.path.exists(save_dir):
        shutil.rmtree(save_dir)