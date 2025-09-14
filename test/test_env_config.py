#!/usr/bin/env python
"""
测试环境变量配置是否正确加载
"""

import os
import sys
from pathlib import Path

# 添加Django项目路径
sys.path.append(str(Path(__file__).parent.parent / 'web'))

# 设置Django环境
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'web.settings')

import django
django.setup()

from django.conf import settings

def test_volcengine_config():
    """
    测试火山引擎配置是否正确加载
    """
    print("=== 测试火山引擎配置 ===")
    
    # 检查环境变量
    env_ak = os.environ.get('VOLCENGINE_ACCESS_KEY', '')
    env_sk = os.environ.get('VOLCENGINE_SECRET_KEY', '')
    
    print(f"环境变量 VOLCENGINE_ACCESS_KEY: {'已设置' if env_ak else '未设置'}")
    print(f"环境变量 VOLCENGINE_SECRET_KEY: {'已设置' if env_sk else '未设置'}")
    
    # 检查Django settings
    settings_ak = getattr(settings, 'VOLCENGINE_ACCESS_KEY', '')
    settings_sk = getattr(settings, 'VOLCENGINE_SECRET_KEY', '')
    
    print(f"Django settings VOLCENGINE_ACCESS_KEY: {'已设置' if settings_ak else '未设置'}")
    print(f"Django settings VOLCENGINE_SECRET_KEY: {'已设置' if settings_sk else '未设置'}")
    
    # 检查.env文件路径
    env_path = Path(__file__).parent.parent / '.env'
    print(f".env文件路径: {env_path}")
    print(f".env文件存在: {'是' if env_path.exists() else '否'}")
    
    if env_path.exists():
        with open(env_path, 'r') as f:
            content = f.read()
            has_volcengine_ak = 'VOLCENGINE_ACCESS_KEY' in content
            has_volcengine_sk = 'VOLCENGINE_SECRET_KEY' in content
            print(f".env文件包含VOLCENGINE_ACCESS_KEY: {'是' if has_volcengine_ak else '否'}")
            print(f".env文件包含VOLCENGINE_SECRET_KEY: {'是' if has_volcengine_sk else '否'}")
    
    return settings_ak and settings_sk

if __name__ == '__main__':
    success = test_volcengine_config()
    print(f"\n配置测试结果: {'成功' if success else '失败'}")
    sys.exit(0 if success else 1)