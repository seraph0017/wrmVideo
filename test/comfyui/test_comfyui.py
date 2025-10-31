#!/usr/bin/env python
# encoding: utf-8
"""
ComfyUI API 测试客户端
用于测试ComfyUI图像到视频生成功能
"""

import json
import logging
import os
import time
import argparse
import sys
from typing import Dict, Any, Optional, Tuple
import requests
from dataclasses import dataclass


# 配置日志
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)
COMFYUI_API_URL = "http://115.190.188.138:8188/api/prompt"
DEFAULT_IMAGE_FILENAME = "chapter_007_image_01.jpeg"
DEFAULT_LENGTH = 81
DEFAULT_FPS = 16


@dataclass
class ComfyUIConfig:
    """ComfyUI配置类"""
    api_url: str = COMFYUI_API_URL
    timeout: int = 30
    max_retries: int = 3
    retry_delay: int = 1


class ComfyUIClient:
    """ComfyUI API客户端类"""
    
    def __init__(self, config: ComfyUIConfig = None):
        """
        初始化ComfyUI客户端
        
        Args:
            config: ComfyUI配置对象，如果为None则使用默认配置
        """
        self.config = config or ComfyUIConfig()
        self.session = requests.Session()
        self.session.headers.update({"Content-Type": "application/json"})

    def upload_image(self, local_image_path: str, img_type: str = "input", subfolder: str = "") -> Tuple[bool, Optional[Dict[str, Any]], Optional[str]]:
        """
        上传本地图片到 ComfyUI (/api/upload/image)，返回 (success, result_json, error)
        """
        try:
            if not os.path.isfile(local_image_path):
                return False, None, f"文件不存在: {local_image_path}"
            api_base = self.config.api_url.split("/api/prompt")[0].rstrip("/")
            url = f"{api_base}/api/upload/image"
            filename = os.path.basename(local_image_path)
            with open(local_image_path, "rb") as f:
                files = {"image": (filename, f, "application/octet-stream")}
                data = {"type": img_type, "subfolder": subfolder}
                # 上传为 multipart/form-data，需移除会干扰的全局 Content-Type
                _ct = self.session.headers.pop("Content-Type", None)
                try:
                    resp = self.session.post(url, data=data, files=files, timeout=self.config.timeout)
                finally:
                    if _ct is not None:
                        self.session.headers["Content-Type"] = _ct
            if resp.status_code == 200:
                try:
                    return True, resp.json(), None
                except ValueError:
                    return True, {"raw": resp.text}, None
            else:
                return False, None, f"HTTP错误: {resp.status_code} - {resp.text}"
        except Exception as e:
            return False, None, str(e)
    
    def create_workflow_payload(
        self,
        image_filename: str,
        positive_prompt: str = "让他动起来",
        negative_prompt: str = "色调艳丽，过曝，静态，细节模糊不清，字幕，风格，作品，画作，画面，静止，整体发灰，最差质量，低质量，JPEG压缩残留，丑陋的，残缺的，多余的手指，画得不好的手部，画得不好的脸部，畸形的，毁容的，形态畸形的肢体，手指融合，静止不动的画面，杂乱的背景，三条腿，背景人很多，倒着走",
        width: int = 736,
        height: int = 1312,
        length: int = DEFAULT_LENGTH,
        fps: int = DEFAULT_FPS,
        noise_seed: int = 138073435077572
    ) -> Dict[str, Any]:
        """
        创建ComfyUI工作流载荷
        
        Args:
            image_filename: 输入图像文件名
            positive_prompt: 正向提示词
            negative_prompt: 负向提示词
            width: 视频宽度
            height: 视频高度
            length: 视频长度（帧数）
            fps: 帧率
            noise_seed: 噪声种子
            
        Returns:
            Dict: ComfyUI工作流配置字典
        """
        return {
            "84": {
                "inputs": {
                    "clip_name": "umt5_xxl_fp8_e4m3fn_scaled.safetensors",
                    "type": "wan",
                    "device": "default"
                },
                "class_type": "CLIPLoader",
                "_meta": {"title": "加载CLIP"}
            },
            "85": {
                "inputs": {
                    "add_noise": "disable",
                    "noise_seed": 0,
                    "steps": 4,
                    "cfg": 1,
                    "sampler_name": "euler",
                    "scheduler": "simple",
                    "start_at_step": 2,
                    "end_at_step": 4,
                    "return_with_leftover_noise": "disable",
                    "model": ["103", 0],
                    "positive": ["98", 0],
                    "negative": ["98", 1],
                    "latent_image": ["86", 0]
                },
                "class_type": "KSamplerAdvanced",
                "_meta": {"title": "K采样器（高级）"}
            },
            "86": {
                "inputs": {
                    "add_noise": "enable",
                    "noise_seed": noise_seed,
                    "steps": 4,
                    "cfg": 1,
                    "sampler_name": "euler",
                    "scheduler": "simple",
                    "start_at_step": 0,
                    "end_at_step": 2,
                    "return_with_leftover_noise": "enable",
                    "model": ["104", 0],
                    "positive": ["98", 0],
                    "negative": ["98", 1],
                    "latent_image": ["98", 2]
                },
                "class_type": "KSamplerAdvanced",
                "_meta": {"title": "K采样器（高级）"}
            },
            "87": {
                "inputs": {
                    "samples": ["85", 0],
                    "vae": ["90", 0]
                },
                "class_type": "VAEDecode",
                "_meta": {"title": "VAE解码"}
            },
            "89": {
                "inputs": {
                    "text": negative_prompt,
                    "clip": ["84", 0]
                },
                "class_type": "CLIPTextEncode",
                "_meta": {"title": "CLIP Text Encode (Negative Prompt)"}
            },
            "90": {
                "inputs": {
                    "vae_name": "wan_2.1_vae.safetensors"
                },
                "class_type": "VAELoader",
                "_meta": {"title": "加载VAE"}
            },
            "93": {
                "inputs": {
                    "text": positive_prompt,
                    "clip": ["84", 0]
                },
                "class_type": "CLIPTextEncode",
                "_meta": {"title": "CLIP Text Encode (Positive Prompt)"}
            },
            "94": {
                "inputs": {
                    "fps": fps,
                    "images": ["87", 0]
                },
                "class_type": "CreateVideo",
                "_meta": {"title": "创建视频"}
            },
            "95": {
                "inputs": {
                    "unet_name": "wan2.2_i2v_high_noise_14B_fp8_scaled.safetensors",
                    "weight_dtype": "default"
                },
                "class_type": "UNETLoader",
                "_meta": {"title": "UNet加载器"}
            },
            "96": {
                "inputs": {
                    "unet_name": "wan2.2_i2v_low_noise_14B_fp8_scaled.safetensors",
                    "weight_dtype": "default"
                },
                "class_type": "UNETLoader",
                "_meta": {"title": "UNet加载器"}
            },
            "97": {
                "inputs": {
                    "image": image_filename
                },
                "class_type": "LoadImage",
                "_meta": {"title": "加载图像"}
            },
            "98": {
                "inputs": {
                    "width": width,
                    "height": height,
                    "length": length,
                    "batch_size": 1,
                    "positive": ["93", 0],
                    "negative": ["89", 0],
                    "vae": ["90", 0],
                    "start_image": ["97", 0]
                },
                "class_type": "WanImageToVideo",
                "_meta": {"title": "Wan图像到视频"}
            },
            "101": {
                "inputs": {
                    "lora_name": "wan2.2_i2v_lightx2v_4steps_lora_v1_high_noise.safetensors",
                    "strength_model": 1.0000000000000002,
                    "model": ["95", 0]
                },
                "class_type": "LoraLoaderModelOnly",
                "_meta": {"title": "LoRA加载器（仅模型）"}
            },
            "102": {
                "inputs": {
                    "lora_name": "wan2.2_i2v_lightx2v_4steps_lora_v1_low_noise.safetensors",
                    "strength_model": 1.0000000000000002,
                    "model": ["96", 0]
                },
                "class_type": "LoraLoaderModelOnly",
                "_meta": {"title": "LoRA加载器（仅模型）"}
            },
            "103": {
                "inputs": {
                    "shift": 5.000000000000001,
                    "model": ["102", 0]
                },
                "class_type": "ModelSamplingSD3",
                "_meta": {"title": "采样算法（SD3）"}
            },
            "104": {
                "inputs": {
                    "shift": 5.000000000000001,
                    "model": ["101", 0]
                },
                "class_type": "ModelSamplingSD3",
                "_meta": {"title": "采样算法（SD3）"}
            },
            "108": {
                "inputs": {
                    "filename_prefix": "video/ComfyUI",
                    "format": "mp4",
                    "codec": "h264",
                    "video": ["94", 0]
                },
                "class_type": "SaveVideo",
                "_meta": {"title": "保存视频"}
            }
        }
    
    def submit_workflow(self, workflow_payload: Dict[str, Any]) -> Tuple[bool, Optional[Dict[str, Any]], Optional[str]]:
        """
        提交工作流到ComfyUI，自动处理端点归一化和 404/405 回退到 `/prompt`。
        返回三元组: (是否成功, 响应JSON或None, 错误文本或None)
        """
        api_payload = {"prompt": workflow_payload, "client_id": "python_client"}

        # 内联端点归一化，兼容 base、/api、/api/prompt、/prompt
        def _normalize_prompt_url(url: str) -> str:
            base = (url or '').strip().rstrip('/')
            if not base:
                base = 'http://127.0.0.1:8188'
            if base.endswith('/api/prompt') or '/api/prompt' in base:
                return base
            if base.endswith('/prompt') or ('/prompt' in base and '/api' not in base):
                return base
            if base.endswith('/api'):
                return base + '/prompt'
            if '/api' in base:
                return base.split('/api')[0].rstrip('/') + '/api/prompt'
            return base + '/api/prompt'

        primary = _normalize_prompt_url(self.config.api_url)
        root = primary.split('/api/prompt')[0] if '/api/prompt' in primary else primary.split('/prompt')[0]
        fallback = root.rstrip('/') + '/prompt'

        for attempt in range(self.config.max_retries):
            try:
                logger.info(f"提交工作流到ComfyUI (尝试 {attempt + 1}/{self.config.max_retries})")
                response = self.session.post(primary, json=api_payload, timeout=self.config.timeout)
                if response.status_code == 200:
                    try:
                        result = response.json()
                        logger.info("工作流提交成功")
                        return True, result, None
                    except json.JSONDecodeError as e:
                        error_msg = f"JSON解析失败: {str(e)}"
                        logger.error(error_msg)
                        return False, None, error_msg
                else:
                    if response.status_code in (404, 405):
                        logger.warning(f"主端点 {primary} 返回 {response.status_code}，尝试回退 {fallback}")
                        r2 = self.session.post(fallback, json=api_payload, timeout=self.config.timeout)
                        if r2.status_code == 200:
                            try:
                                result2 = r2.json()
                                logger.info("回退端点提交成功")
                                return True, result2, None
                            except json.JSONDecodeError as e:
                                error_msg = f"回退端点 JSON解析失败: {str(e)}"
                                logger.error(error_msg)
                                return False, None, error_msg
                        else:
                            err_fb = f"HTTP错误(回退): {r2.status_code} - {r2.text}"
                            logger.error(err_fb)
                            if attempt < self.config.max_retries - 1:
                                logger.info(f"等待 {self.config.retry_delay} 秒后重试...")
                                time.sleep(self.config.retry_delay)
                                continue
                            return False, None, err_fb
                    error_msg = f"HTTP错误: {response.status_code} - {response.text}"
                    logger.error(error_msg)
                    if attempt < self.config.max_retries - 1:
                        logger.info(f"等待 {self.config.retry_delay} 秒后重试...")
                        time.sleep(self.config.retry_delay)
                        continue
                    return False, None, error_msg

            except requests.exceptions.Timeout:
                error_msg = f"请求超时 (超过 {self.config.timeout} 秒)"
                logger.error(error_msg)
                if attempt < self.config.max_retries - 1:
                    logger.info(f"等待 {self.config.retry_delay} 秒后重试...")
                    time.sleep(self.config.retry_delay)
                    continue
                return False, None, error_msg

            except requests.exceptions.ConnectionError:
                error_msg = "连接错误：无法连接到ComfyUI服务器"
                logger.error(error_msg)
                if attempt < self.config.max_retries - 1:
                    logger.info(f"等待 {self.config.retry_delay} 秒后重试...")
                    time.sleep(self.config.retry_delay)
                    continue
                return False, None, error_msg

            except Exception as e:
                error_msg = f"未知错误: {str(e)}"
                logger.error(error_msg)
                return False, None, error_msg

        return False, None, "所有重试尝试都失败了"
        
    def _api_base(self) -> str:
        """
        返回 ComfyUI 基础 API 地址 (以 `/api` 结尾)，兼容 `/api/prompt` 与 `/prompt` 配置。
        """
        url = (self.config.api_url or '').strip().rstrip('/')
        if '/api/prompt' in url:
            root = url.split('/api/prompt')[0]
        elif '/prompt' in url:
            root = url.split('/prompt')[0]
        elif '/api' in url:
            root = url.split('/api')[0]
        else:
            root = url
        return f"{root}/api"
    
    def wait_for_output_filename(self, prompt_id: str, poll_interval: float = 1.0, max_wait: int = 300):
        """
        轮询 /api/history/{prompt_id}，直到拿到 outputs.images[*].filename
        返回 (filename, subfolder, type)，若超时则返回 (None, None, None)
        """
        base_api = self._api_base()
        url = f"{base_api}/history/{prompt_id}"
        end_time = time.time() + max_wait
        while time.time() < end_time:
            try:
                resp = self.session.get(url, timeout=self.config.timeout)
                if resp.status_code == 200:
                    try:
                        data = resp.json()
                    except json.JSONDecodeError as e:
                        logger.warning(f"历史接口 JSON 解析失败: {e}")
                        data = {}
                    obj = data
                    # 兼容三种历史返回结构：
                    # 1) {<prompt_id>: {...}}
                    # 2) {history: {<prompt_id>: {...}}}
                    # 3) 直接返回节点对象 {...}
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
                # 等待下一次轮询
                time.sleep(poll_interval)
            except requests.RequestException as e:
                logger.warning(f"轮询历史接口异常: {e}")
                time.sleep(poll_interval)
        logger.error("轮询等待超时，未获取到输出文件名")
        return None, None, None
    
    def download_view_file(self, filename: str, subfolder: str = 'video', type_: str = 'output', output_dir: str = 'downloads') -> Optional[str]:
        """
        从 /api/view 下载文件到本地
        返回本地保存路径或 None
        """
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
        
    def generate_video_from_image(
        self,
        image_filename: str,
        positive_prompt: str = "让他动起来",
        **kwargs
    ) -> Tuple[bool, Optional[Dict[str, Any]], Optional[str]]:
        """
        从图像生成视频的便捷方法
        
        Args:
            image_filename: 输入图像文件名
            positive_prompt: 正向提示词
            **kwargs: 其他参数传递给create_workflow_payload
            
        Returns:
            Tuple[bool, Optional[Dict], Optional[str]]: (成功标志, 响应数据, 错误信息)
        """
        logger.info(f"开始从图像 '{image_filename}' 生成视频")
        
        # 创建工作流载荷
        workflow_payload = self.create_workflow_payload(
            image_filename=image_filename,
            positive_prompt=positive_prompt,
            **kwargs
        )
        
        # 提交工作流
        return self.submit_workflow(workflow_payload)


def main():
    """主函数：演示ComfyUI客户端的使用"""
    # 命令行参数：若未传参则使用静态常量
    parser = argparse.ArgumentParser(description="ComfyUI 测试客户端")
    parser.add_argument("--api_url", default=COMFYUI_API_URL, help="ComfyUI API地址，默认使用静态常量")
    parser.add_argument("--image_filename", default=DEFAULT_IMAGE_FILENAME, help="输入图像文件名，默认使用静态常量")
    parser.add_argument("--timeout", type=int, default=30, help="请求超时(秒)")
    parser.add_argument("--max_retries", type=int, default=3, help="最大重试次数")
    parser.add_argument("--poll_interval", type=float, default=1.0, help="轮询间隔(秒)")
    parser.add_argument("--max_wait", type=int, default=300, help="轮询最长等待(秒)")
    parser.add_argument("--output_dir", default="downloads", help="下载保存目录")
    parser.add_argument("--upload_image", help="本地图片路径，若提供则先上传再生成")
    parser.add_argument("--upload_type", default="input", choices=["input", "output"], help="上传类型")
    parser.add_argument("--upload_subfolder", default="", help="上传子目录")
    args = parser.parse_args()

    # 创建配置
    config = ComfyUIConfig(
        api_url=args.api_url,
        timeout=args.timeout,
        max_retries=args.max_retries
    )
    
    # 创建客户端
    client = ComfyUIClient(config)

    # 若传了本地图片，则先上传并用返回的 name 作为 filename
    image_to_use = args.image_filename
    if args.upload_image:
        print("开始上传本地图片以供 ComfyUI 使用…")
        up_ok, up_res, up_err = client.upload_image(args.upload_image, args.upload_type, args.upload_subfolder)
        if not up_ok:
            print("❌ 图片上传失败!")
            print(f"错误信息: {up_err}")
            return
        print(json.dumps(up_res, ensure_ascii=False, indent=2))
        image_to_use = up_res.get("name") or os.path.basename(args.upload_image)
        # 打印可视化链接
        base_api = client._api_base()
        view_url = f"{base_api}/view?type={up_res.get('type','input')}&filename={image_to_use}"
        if args.upload_subfolder:
            view_url += f"&subfolder={args.upload_subfolder}"
        print(f"View URL: {view_url}")

    # 生成视频
    success, result, error = client.generate_video_from_image(
        image_filename=image_to_use,
        positive_prompt="让他动起来",
        width=736,
        height=1312,
        length=DEFAULT_LENGTH,
        fps=DEFAULT_FPS
    )
    
    if success:
        print("✅ 工作流提交成功!")
        print(f"响应数据: {json.dumps(result, indent=2, ensure_ascii=False)}")
        prompt_id = (result or {}).get("prompt_id")
        if prompt_id:
            print(f"prompt_id: {prompt_id}")
            fname, subfolder, type_ = client.wait_for_output_filename(prompt_id, args.poll_interval, args.max_wait)
            if fname:
                local_path = client.download_view_file(fname, subfolder or "video", type_ or "output", args.output_dir)
                if local_path:
                    print(f"🎬 视频已下载: {local_path}")
                else:
                    print("下载失败：服务未返回文件内容")
            else:
                print("轮询超时：未获取到输出文件名")
        else:
            print("返回数据中未找到 prompt_id")
    else:
        print("❌ 工作流提交失败!")
        print(f"错误信息: {error}")


if __name__ == "__main__":
    main()