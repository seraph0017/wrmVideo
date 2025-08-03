#!/usr/bin/env python3
# -*- coding: utf-8 -*-

import os
import sys
sys.path.append('.')

from volcengine.visual.VisualService import VisualService
from config.config import IMAGE_TWO_CONFIG
import requests

def test_single_image_generation():
    """测试单张图片生成"""
    try:
        # 初始化图片生成服务
        visual_service = VisualService()
        visual_service.set_ak(IMAGE_TWO_CONFIG['access_key'])
        visual_service.set_sk(IMAGE_TWO_CONFIG['secret_key'])
        
        # 测试prompt
        prompt = "傍晚的城市街道场景，一个年轻女性站在停车位旁，穿着休闲装，表情从容"
        
        # 构建请求参数
        form = {
            "req_key": "high_aes_general_v21_L",
            "prompt": prompt,
            "llm_seed": -1,
            "seed": -1,
            "scale": 3.5,
            "ddim_steps": 25,
            "width": 720,
            "height": 1280,
            "use_pre_llm": True,
            "use_sr": True,
            "return_url": True,
            "logo_info": {
                "add_logo": False,
                "position": 0,
                "language": 0,
                "opacity": 0.3,
                "logo_text_content": "这里是明水印内容"
            }
        }
        
        print(f"正在生成图片: {prompt}")
        print(f"请求参数: {form}")
        
        resp = visual_service.cv_process(form)
        print(f"API响应: {resp}")
        
        # 处理响应
        if 'data' in resp and 'image_urls' in resp['data']:
            image_url = resp['data']['image_urls'][0]
            print(f"图片URL: {image_url}")
            
            # 下载图片
            img_response = requests.get(image_url)
            print(f"下载状态码: {img_response.status_code}")
            
            if img_response.status_code == 200:
                image_path = "test_image.jpg"
                with open(image_path, 'wb') as f:
                    f.write(img_response.content)
                print(f"✓ 图片已保存: {image_path}")
                print(f"文件大小: {os.path.getsize(image_path)} bytes")
                return True
            else:
                print(f"✗ 下载图片失败")
                return False
        else:
            print(f"✗ 图片生成失败: {resp}")
            return False
            
    except Exception as e:
        print(f"✗ 生成图片时发生错误: {e}")
        import traceback
        traceback.print_exc()
        return False

if __name__ == "__main__":
    print("=== 测试图片生成功能 ===")
    success = test_single_image_generation()
    if success:
        print("\n✓ 图片生成测试成功")
    else:
        print("\n✗ 图片生成测试失败")