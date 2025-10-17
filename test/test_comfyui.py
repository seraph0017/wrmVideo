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
from typing import Dict, Any, Optional, Tuple
import requests
from dataclasses import dataclass


# 配置日志
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)


@dataclass
class ComfyUIConfig:
    """ComfyUI配置类"""
    api_url: str = "http://115.190.188.138:8188/api/prompt"
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
    
    def create_workflow_payload(
        self,
        image_filename: str,
        positive_prompt: str = "让他动起来",
        negative_prompt: str = "色调艳丽，过曝，静态，细节模糊不清，字幕，风格，作品，画作，画面，静止，整体发灰，最差质量，低质量，JPEG压缩残留，丑陋的，残缺的，多余的手指，画得不好的手部，画得不好的脸部，畸形的，毁容的，形态畸形的肢体，手指融合，静止不动的画面，杂乱的背景，三条腿，背景人很多，倒着走",
        width: int = 736,
        height: int = 1312,
        length: int = 81,
        fps: int = 16,
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
        提交工作流到ComfyUI
        
        Args:
            workflow_payload: 工作流配置字典
            
        Returns:
            Tuple[bool, Optional[Dict], Optional[str]]: (成功标志, 响应数据, 错误信息)
        """
        # ComfyUI API需要特定的格式
        api_payload = {
            "prompt": workflow_payload,
            "client_id": "python_client"
        }
        
        for attempt in range(self.config.max_retries):
            try:
                logger.info(f"提交工作流到ComfyUI (尝试 {attempt + 1}/{self.config.max_retries})")
                
                response = self.session.post(
                    self.config.api_url,
                    json=api_payload,
                    timeout=self.config.timeout
                )
                
                # 检查HTTP状态码
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
    # 创建配置
    config = ComfyUIConfig(
        api_url="http://115.190.188.138:8188/api/prompt",
        timeout=30,
        max_retries=3
    )
    
    # 创建客户端
    client = ComfyUIClient(config)
    
    # 生成视频
    success, result, error = client.generate_video_from_image(
        image_filename="chapter_007_image_01.jpeg",
        positive_prompt="让他动起来",
        width=736,
        height=1312,
        length=81,
        fps=8
    )
    
    if success:
        print("✅ 工作流提交成功!")
        print(f"响应数据: {json.dumps(result, indent=2, ensure_ascii=False)}")
    else:
        print("❌ 工作流提交失败!")
        print(f"错误信息: {error}")


if __name__ == "__main__":
    main()