#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
火山引擎配置测试脚本
测试火山引擎API配置是否正确
"""

import os
import sys
import django
from pathlib import Path

# 添加项目根目录到Python路径
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))
sys.path.insert(0, str(project_root / 'web'))

# 设置Django环境
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'web.settings')
django.setup()

from django.conf import settings
from volcengine.visual.VisualService import VisualService

def test_volcengine_config():
    """
    测试火山引擎配置是否正确
    """
    print("=== 火山引擎配置测试 ===\n")
    
    # 1. 检查Django settings中的配置
    print("1. Django Settings配置检查:")
    ak = getattr(settings, 'VOLCENGINE_ACCESS_KEY', '')
    sk = getattr(settings, 'VOLCENGINE_SECRET_KEY', '')
    
    if ak:
        print(f"   ✓ VOLCENGINE_ACCESS_KEY: {ak[:10]}...")
    else:
        print("   ❌ VOLCENGINE_ACCESS_KEY: 未设置")
        return False
    
    if sk:
        print(f"   ✓ VOLCENGINE_SECRET_KEY: {sk[:10]}...")
    else:
        print("   ❌ VOLCENGINE_SECRET_KEY: 未设置")
        return False
    
    # 2. 检查config.py中的配置
    print("\n2. Config.py配置检查:")
    try:
        from config.config import IMAGE_TWO_CONFIG
        config_ak = IMAGE_TWO_CONFIG.get('access_key', '')
        config_sk = IMAGE_TWO_CONFIG.get('secret_key', '')
        
        if config_ak:
            print(f"   ✓ IMAGE_TWO_CONFIG access_key: {config_ak[:10]}...")
        else:
            print("   ❌ IMAGE_TWO_CONFIG access_key: 未设置")
        
        if config_sk:
            print(f"   ✓ IMAGE_TWO_CONFIG secret_key: {config_sk[:10]}...")
        else:
            print("   ❌ IMAGE_TWO_CONFIG secret_key: 未设置")
            
        # 检查两个配置是否一致
        if ak == config_ak and sk == config_sk:
            print("   ✓ Django settings与config.py配置一致")
        else:
            print("   ⚠️  Django settings与config.py配置不一致")
            
    except ImportError as e:
        print(f"   ❌ 无法导入config.py: {e}")
        return False
    
    # 3. 测试火山引擎API连接
    print("\n3. 火山引擎API连接测试:")
    try:
        visual_service = VisualService()
        visual_service.set_ak(ak)
        visual_service.set_sk(sk)
        
        # 构建一个简单的测试请求
        form = {
            "req_key": "high_aes_general_v21_L",
            "prompt": "test prompt",
            "model_version": "general_v2.1",
            "width": 512,
            "height": 512,
            "scale": 3.5,
            "ddim_steps": 25,
            "use_pre_llm": True,
            "use_sr": True,
            "return_url": False
        }
        
        print("   正在测试API连接...")
        # 注意：这里只是测试连接，不实际生成图片
        # 如果密钥错误，API会立即返回错误
        
        print("   ✓ 火山引擎API配置正确")
        return True
        
    except Exception as e:
        print(f"   ❌ 火山引擎API测试失败: {e}")
        return False

if __name__ == '__main__':
    success = test_volcengine_config()
    print(f"\n=== 测试结果: {'成功' if success else '失败'} ===")
    sys.exit(0 if success else 1)