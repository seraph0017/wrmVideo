#!/usr/bin/env python
"""
将admin用户添加到管理员组
"""
import os
import sys
import django

# 设置Django环境
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'web.settings')
django.setup()

from django.contrib.auth.models import User, Group

def add_admin_to_group():
    """将admin用户添加到管理员组"""
    print("=" * 60)
    print("将 admin 用户添加到管理员组")
    print("=" * 60)
    
    try:
        # 获取admin用户
        admin_user = User.objects.get(username='admin')
        print(f"\n✅ 找到用户: {admin_user.username}")
        
        # 获取管理员组
        admin_group = Group.objects.get(name='管理员组')
        print(f"✅ 找到组: {admin_group.name}")
        
        # 检查是否已经在组中
        if admin_user in admin_group.user_set.all():
            print(f"\n⚠️  用户 {admin_user.username} 已经在 {admin_group.name} 中")
        else:
            # 添加到组
            admin_user.groups.add(admin_group)
            print(f"\n✅ 成功将 {admin_user.username} 添加到 {admin_group.name}")
        
        # 验证
        print("\n验证结果:")
        user_groups = admin_user.groups.all()
        print(f"用户 {admin_user.username} 当前所属组:")
        for group in user_groups:
            print(f"   - {group.name}")
        
        # 测试 is_admin 函数
        from video.permissions import is_admin
        result = is_admin(admin_user)
        print(f"\nis_admin(admin_user) = {result}")
        if result:
            print("✅ 权限检查通过！admin 用户现在可以访问所有功能")
        else:
            print("❌ 权限检查失败！请检查配置")
        
    except User.DoesNotExist:
        print("\n❌ 错误: 未找到 admin 用户")
        print("请先创建 admin 用户: python manage.py createsuperuser")
    except Group.DoesNotExist:
        print("\n❌ 错误: 未找到管理员组")
        print("请先运行: python manage.py setup_permissions")
    except Exception as e:
        print(f"\n❌ 错误: {str(e)}")
    
    print("\n" + "=" * 60)

if __name__ == '__main__':
    add_admin_to_group()

