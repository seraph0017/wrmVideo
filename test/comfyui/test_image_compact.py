#!/usr/bin/env python
# encoding: utf-8
"""
ComfyUI 图像工作流测试
参考 test_comfyui.py 的结构，直接读取 image_compact.json 作为工作流参数，
提交到 ComfyUI 后轮询产出并下载到本地 downloads 目录。

用法示例：
python test/comfyui/test_image_compact.py \
  --api_url http://115.190.188.138:8188/api/prompt \
  --workflow_json test/comfyui/image_compact.json \
  --output_dir test/comfyui/downloads
"""

import os
import json
import time
import argparse
import logging
from dataclasses import dataclass
from typing import Dict, Any, Optional, Tuple

import requests


# 日志配置
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)


# 默认配置
COMFYUI_API_URL = "http://115.190.188.138:8188/api/prompt"


@dataclass
class ComfyUIConfig:
    api_url: str = COMFYUI_API_URL
    timeout: int = 30
    max_retries: int = 3
    retry_delay: int = 1


class ComfyUIClient:
    """ComfyUI API 客户端"""

    def __init__(self, config: ComfyUIConfig = None):
        self.config = config or ComfyUIConfig()
        self.session = requests.Session()
        self.session.headers.update({"Content-Type": "application/json"})

    def _api_base(self) -> str:
        root = self.config.api_url.split('/api')[0]
        return f"{root}/api"

    def submit_workflow(self, workflow_payload: Dict[str, Any]) -> Tuple[bool, Optional[Dict[str, Any]], Optional[str]]:
        """提交工作流到 ComfyUI"""
        api_payload = {"prompt": workflow_payload, "client_id": "python_client"}

        for attempt in range(self.config.max_retries):
            try:
                logger.info(f"提交工作流到 ComfyUI (尝试 {attempt + 1}/{self.config.max_retries})")
                resp = self.session.post(self.config.api_url, json=api_payload, timeout=self.config.timeout)
                if resp.status_code == 200:
                    try:
                        data = resp.json()
                    except json.JSONDecodeError:
                        data = {"raw": resp.text}
                    logger.info("工作流提交成功")
                    return True, data, None
                else:
                    err = f"HTTP错误: {resp.status_code} - {resp.text}"
                    logger.error(err)
                    if attempt < self.config.max_retries - 1:
                        time.sleep(self.config.retry_delay)
                        continue
                    return False, None, err
            except requests.exceptions.Timeout:
                err = f"请求超时 (超过 {self.config.timeout} 秒)"
                logger.error(err)
                if attempt < self.config.max_retries - 1:
                    time.sleep(self.config.retry_delay)
                    continue
                return False, None, err
            except requests.exceptions.ConnectionError:
                err = "连接错误：无法连接到 ComfyUI 服务器"
                logger.error(err)
                if attempt < self.config.max_retries - 1:
                    time.sleep(self.config.retry_delay)
                    continue
                return False, None, err
            except Exception as e:
                err = f"未知错误: {e}"
                logger.error(err)
                return False, None, err
        return False, None, "所有重试尝试都失败了"

    def wait_for_output_filename(self, prompt_id: str, poll_interval: float = 1.0, max_wait: int = 300):
        """轮询 /api/history/{prompt_id} 获取 outputs.images[*].filename"""
        base_api = self._api_base()
        url = f"{base_api}/history/{prompt_id}"
        end_ts = time.time() + max_wait

        while time.time() < end_ts:
            try:
                resp = self.session.get(url, timeout=self.config.timeout)
                if resp.status_code == 200:
                    try:
                        data = resp.json()
                    except json.JSONDecodeError:
                        data = {}

                    obj = data
                    if isinstance(obj, dict):
                        if prompt_id in obj and isinstance(obj[prompt_id], dict):
                            obj = obj[prompt_id]
                        elif 'history' in obj and isinstance(obj['history'], dict):
                            obj = obj['history'].get(prompt_id) or next(iter(obj['history'].values()), {})

                    outputs = obj.get('outputs') if isinstance(obj, dict) else {}
                    if outputs:
                        for _, node_val in outputs.items():
                            images = node_val.get('images') if isinstance(node_val, dict) else None
                            if images:
                                for item in images:
                                    fname = item.get('filename')
                                    subfolder = item.get('subfolder', '')
                                    type_ = item.get('type', 'output')
                                    if fname:
                                        logger.info(f"获取到输出文件: {fname} (subfolder={subfolder}, type={type_})")
                                        return fname, subfolder, type_
                time.sleep(poll_interval)
            except requests.RequestException as e:
                logger.warning(f"轮询历史接口异常: {e}")
                time.sleep(poll_interval)

        logger.error("轮询等待超时，未获取到输出文件名")
        return None, None, None

    def download_view_file(self, filename: str, subfolder: str = '', type_: str = 'output', output_dir: str = 'downloads') -> Optional[str]:
        """从 /api/view 下载文件到本地 output_dir"""
        base_api = self._api_base()
        params = f"filename={filename}&type={type_}" + (f"&subfolder={subfolder}" if subfolder else "")
        url = f"{base_api}/view?{params}"
        try:
            resp = self.session.get(url, stream=True, timeout=self.config.timeout)
            if resp.status_code == 200:
                os.makedirs(output_dir, exist_ok=True)
                local_path = os.path.join(output_dir, filename)
                with open(local_path, 'wb') as f:
                    for chunk in resp.iter_content(chunk_size=8192):
                        if chunk:
                            f.write(chunk)
                logger.info(f"文件已下载到: {local_path}")
                return local_path
            else:
                logger.error(f"下载失败，状态码: {resp.status_code}")
                return None
        except requests.RequestException as e:
            logger.error(f"下载异常: {e}")
            return None


def load_workflow_json(path: str) -> Dict[str, Any]:
    if not os.path.isfile(path):
        raise FileNotFoundError(f"工作流JSON不存在: {path}")
    with open(path, 'r', encoding='utf-8') as f:
        return json.load(f)


def main():
    parser = argparse.ArgumentParser(description="ComfyUI 图像工作流测试（使用 image_compact.json）")
    default_json = os.path.join(os.path.dirname(__file__), 'image_compact.json')
    default_output = os.path.join(os.path.dirname(__file__), 'downloads')

    parser.add_argument('--api_url', default=COMFYUI_API_URL, help='ComfyUI API 地址')
    parser.add_argument('--workflow_json', default=default_json, help='工作流 JSON 文件路径')
    parser.add_argument('--timeout', type=int, default=30, help='请求超时(秒)')
    parser.add_argument('--max_retries', type=int, default=3, help='最大重试次数')
    parser.add_argument('--poll_interval', type=float, default=1.0, help='轮询间隔(秒)')
    parser.add_argument('--max_wait', type=int, default=300, help='轮询最长等待(秒)')
    parser.add_argument('--output_dir', default=default_output, help='下载保存目录')

    args = parser.parse_args()

    config = ComfyUIConfig(api_url=args.api_url, timeout=args.timeout, max_retries=args.max_retries)
    client = ComfyUIClient(config)

    # 加载工作流
    workflow = load_workflow_json(args.workflow_json)
    logger.info(f"加载工作流 JSON: {args.workflow_json}")

    # 提交工作流
    ok, res, err = client.submit_workflow(workflow)
    if not ok:
        logger.error(f"工作流提交失败: {err}")
        return

    # 获取 prompt_id
    prompt_id = None
    if isinstance(res, dict):
        prompt_id = res.get('prompt_id') or (res.get('data') or {}).get('prompt_id')

    if not prompt_id:
        logger.error(f"未获取到 prompt_id，响应: {res}")
        return

    logger.info(f"prompt_id: {prompt_id}")

    # 轮询并获取输出文件名
    filename, subfolder, type_ = client.wait_for_output_filename(prompt_id, poll_interval=args.poll_interval, max_wait=args.max_wait)
    if not filename:
        logger.error("未获取到输出文件，下载终止")
        return

    # 下载输出文件到指定目录
    save_path = client.download_view_file(filename, subfolder=subfolder or '', type_=type_ or 'output', output_dir=args.output_dir)
    if not save_path:
        logger.error("下载失败")
        return

    logger.info("流程完成 ✅")


if __name__ == '__main__':
    main()