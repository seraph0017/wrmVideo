#!/usr/bin/env python
# encoding: utf-8
"""
单元测试：验证 ComfyUIClient._api_base() 的端点归一化行为
- 支持基础地址、/api、/api/prompt、/prompt 四种形式
- 统一返回以 /api 结尾的基础 API 地址
"""

import os
import sys
import pytest


def _import_comfyui_client():
    """
    动态导入 test/comfyui/test_comfyui.py 中的 ComfyUIClient 和 ComfyUIConfig，
    以避免路径包结构问题。
    """
    base_dir = os.path.dirname(os.path.abspath(__file__))
    comfy_dir = os.path.join(base_dir, 'comfyui')
    if comfy_dir not in sys.path:
        sys.path.insert(0, comfy_dir)
    import test_comfyui as tc
    return tc.ComfyUIClient, tc.ComfyUIConfig


@pytest.mark.parametrize(
    "input_url, expected_api_base",
    [
        ("http://127.0.0.1:8188", "http://127.0.0.1:8188/api"),
        ("http://127.0.0.1:8188/api", "http://127.0.0.1:8188/api"),
        ("http://127.0.0.1:8188/api/prompt", "http://127.0.0.1:8188/api"),
        ("http://127.0.0.1:8188/prompt", "http://127.0.0.1:8188/api"),
        ("http://127.0.0.1:8188/", "http://127.0.0.1:8188/api"),
        ("http://127.0.0.1:8188/api/", "http://127.0.0.1:8188/api"),
        ("http://127.0.0.1:8188/api/prompt/", "http://127.0.0.1:8188/api"),
    ],
)
def test_api_base_normalization(input_url, expected_api_base):
    """
    验证 _api_base() 对不同形式端点的归一化输出是否一致。
    """
    ComfyUIClient, ComfyUIConfig = _import_comfyui_client()
    client = ComfyUIClient(config=ComfyUIConfig(api_url=input_url))
    assert client._api_base() == expected_api_base