"""
集成测试：调用新的 ComfyUI 版本批量生成分镜图片 API

说明：
- 该测试脚本通过 HTTP 请求调用 `batch-generate-images-v4` 接口，验证接口提交任务是否成功。
- 需要本地 Django 开发服务器运行在 `http://127.0.0.1:8000/`。
- 默认章节 ID 为 27，可通过环境变量 `CHAPTER_ID` 覆盖。
- 可通过环境变量配置 `COMFYUI_API_URL` 与 `WORKFLOW_JSON`。
"""

import os
import json
import requests


def get_env(key: str, default: str) -> str:
    """
    获取环境变量值，若不存在则返回默认值。

    参数:
        key: 环境变量键名
        default: 默认值

    返回:
        环境变量对应的字符串值
    """
    return os.environ.get(key, default)


def run_test() -> None:
    """
    运行一次接口调用测试，输出结果信息。

    流程:
    - 读取配置(章节ID、ComfyUI地址、工作流JSON)
    - 构造请求并调用 API
    - 打印返回结果并进行基本校验
    """
    base_url = get_env("BASE_URL", "http://127.0.0.1:8000")
    chapter_id = int(get_env("CHAPTER_ID", "27"))
    api_url = get_env("COMFYUI_API_URL", "http://127.0.0.1:8188")
    workflow_json = get_env("WORKFLOW_JSON", "test/comfyui/image_compact.json")

    url = f"{base_url}/video/api/chapters/{chapter_id}/batch-generate-images-v4/"
    payload = {
        "api_url": api_url,
        "workflow_json": workflow_json,
    }

    print("\n🧪 调用 ComfyUI 批量生成分镜图片 API...")
    print(f"URL: {url}")
    print(f"Payload: {json.dumps(payload, ensure_ascii=False)}\n")

    resp = requests.post(url, json=payload, timeout=30)
    print("HTTP Status:", resp.status_code)
    try:
        data = resp.json()
    except Exception:
        print("响应非JSON:", resp.text)
        raise

    print("响应:", json.dumps(data, ensure_ascii=False, indent=2))

    assert data.get("success") is True, "接口返回失败"
    assert "task_id" in data, "未返回 task_id"
    assert data.get("chapter_id") == chapter_id, "返回的章节ID不匹配"
    print("\n✅ 接口调用成功，任务已提交，task_id:", data["task_id"])


if __name__ == "__main__":
    run_test()