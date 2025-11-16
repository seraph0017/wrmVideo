#!/usr/bin/env python
"""
测试 CSRF 配置
"""
import os
import sys
import django

# 设置Django环境
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'web.settings')
django.setup()

from django.conf import settings

print("=" * 60)
print("CSRF 配置检查")
print("=" * 60)

# 检查 CSRF 相关设置
print("\n1. CSRF 中间件配置:")
middleware = settings.MIDDLEWARE
csrf_middleware = [m for m in middleware if 'csrf' in m.lower()]
if csrf_middleware:
    for m in csrf_middleware:
        print(f"   ✅ {m}")
else:
    print("   ❌ 未找到 CSRF 中间件")

print("\n2. CSRF 相关设置:")
csrf_settings = {
    'CSRF_COOKIE_SECURE': getattr(settings, 'CSRF_COOKIE_SECURE', False),
    'CSRF_COOKIE_HTTPONLY': getattr(settings, 'CSRF_COOKIE_HTTPONLY', False),
    'CSRF_COOKIE_SAMESITE': getattr(settings, 'CSRF_COOKIE_SAMESITE', 'Lax'),
    'CSRF_USE_SESSIONS': getattr(settings, 'CSRF_USE_SESSIONS', False),
    'CSRF_COOKIE_NAME': getattr(settings, 'CSRF_COOKIE_NAME', 'csrftoken'),
}

for key, value in csrf_settings.items():
    print(f"   {key}: {value}")

print("\n3. DEBUG 模式:")
print(f"   DEBUG = {settings.DEBUG}")

print("\n4. ALLOWED_HOSTS:")
print(f"   {settings.ALLOWED_HOSTS}")

print("\n5. 登录 URL:")
print(f"   LOGIN_URL = {getattr(settings, 'LOGIN_URL', '/accounts/login/')}")

print("\n" + "=" * 60)
print("✅ CSRF 配置检查完成")
print("=" * 60)

print("\n💡 提示:")
print("   1. 确保浏览器允许 cookies")
print("   2. 清除浏览器缓存和 cookies 后重试")
print("   3. 确保访问的是正确的域名（localhost:8000）")
print("   4. 检查浏览器控制台是否有 JavaScript 错误")

