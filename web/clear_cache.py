#!/usr/bin/env python
"""
清理 Django 缓存工具
用于手动清除控制面板的缓存数据
"""
import os
import sys
import django

# 设置Django环境
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'web.settings')
django.setup()

from django.core.cache import cache

def clear_dashboard_cache():
    """清除控制面板缓存"""
    print("=" * 60)
    print("清理控制面板缓存")
    print("=" * 60)
    
    # 清除管理员缓存
    admin_key = 'dashboard_admin_stats'
    if cache.delete(admin_key):
        print(f"\n✅ 已清除: {admin_key}")
    else:
        print(f"\n⚠️  未找到缓存: {admin_key}")
    
    # 清除所有审核员缓存（通过模式匹配）
    # 注意：locmem 缓存不支持模式匹配，需要手动清除
    print("\n💡 提示: 审核员缓存会在3分钟后自动过期")
    print("   如需立即清除所有缓存，请重启 Django 服务器")
    
    print("\n" + "=" * 60)
    print("✅ 缓存清理完成")
    print("=" * 60)

def clear_all_cache():
    """清除所有缓存"""
    print("=" * 60)
    print("清理所有缓存")
    print("=" * 60)
    
    cache.clear()
    print("\n✅ 已清除所有缓存")
    
    print("\n" + "=" * 60)
    print("✅ 缓存清理完成")
    print("=" * 60)

def show_cache_info():
    """显示缓存信息"""
    print("=" * 60)
    print("缓存系统信息")
    print("=" * 60)
    
    from django.conf import settings
    
    cache_config = settings.CACHES['default']
    print(f"\n缓存后端: {cache_config['BACKEND']}")
    print(f"缓存位置: {cache_config.get('LOCATION', 'N/A')}")
    print(f"默认超时: {cache_config.get('TIMEOUT', 300)} 秒")
    
    # 测试缓存是否工作
    test_key = 'test_cache_key'
    test_value = 'test_value'
    cache.set(test_key, test_value, 10)
    result = cache.get(test_key)
    
    if result == test_value:
        print("\n✅ 缓存系统工作正常")
        cache.delete(test_key)
    else:
        print("\n❌ 缓存系统异常")
    
    print("\n" + "=" * 60)

if __name__ == '__main__':
    import argparse
    
    parser = argparse.ArgumentParser(description='Django 缓存管理工具')
    parser.add_argument('action', choices=['clear', 'clear-all', 'info'], 
                       help='操作类型: clear(清除控制面板缓存), clear-all(清除所有缓存), info(显示缓存信息)')
    
    args = parser.parse_args()
    
    if args.action == 'clear':
        clear_dashboard_cache()
    elif args.action == 'clear-all':
        clear_all_cache()
    elif args.action == 'info':
        show_cache_info()

