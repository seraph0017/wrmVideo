#!/usr/bin/env python
"""
检查admin用户的组成员关系
"""
import os
import sys
import django

# 设置Django环境
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'web.settings')
django.setup()

from django.contrib.auth.models import User, Group

def check_admin_user():
    """检查admin用户的组成员关系"""
    print("=" * 60)
    print("检查 admin 用户的组成员关系")
    print("=" * 60)
    
    # 查找admin用户
    try:
        admin_user = User.objects.get(username='admin')
        print(f"\n✅ 找到用户: {admin_user.username}")
        print(f"   - ID: {admin_user.id}")
        print(f"   - Email: {admin_user.email}")
        print(f"   - is_superuser: {admin_user.is_superuser}")
        print(f"   - is_staff: {admin_user.is_staff}")
        print(f"   - is_active: {admin_user.is_active}")
    except User.DoesNotExist:
        print("\n❌ 未找到 admin 用户")
        return
    
    # 检查用户所属的组
    user_groups = admin_user.groups.all()
    print(f"\n当前所属组 ({user_groups.count()} 个):")
    if user_groups.exists():
        for group in user_groups:
            print(f"   - {group.name}")
    else:
        print("   ❌ 用户不属于任何组！")
    
    # 检查管理员组是否存在
    print("\n系统中的所有组:")
    all_groups = Group.objects.all()
    if all_groups.exists():
        for group in all_groups:
            member_count = group.user_set.count()
            is_member = admin_user in group.user_set.all()
            status = "✅ (admin是成员)" if is_member else "❌ (admin不是成员)"
            print(f"   - {group.name} ({member_count} 个成员) {status}")
    else:
        print("   ❌ 系统中没有任何组！")
    
    # 检查是否在管理员组
    print("\n检查管理员组成员关系:")
    try:
        admin_group = Group.objects.get(name='管理员组')
        if admin_user in admin_group.user_set.all():
            print("   ✅ admin 用户已在管理员组中")
        else:
            print("   ❌ admin 用户不在管理员组中！")
            print("\n修复建议:")
            print("   1. 运行: python manage.py shell")
            print("   2. 执行以下代码:")
            print("      from django.contrib.auth.models import User, Group")
            print("      admin = User.objects.get(username='admin')")
            print("      admin_group = Group.objects.get(name='管理员组')")
            print("      admin.groups.add(admin_group)")
            print("      print('已将 admin 添加到管理员组')")
    except Group.DoesNotExist:
        print("   ❌ 管理员组不存在！")
        print("\n修复建议:")
        print("   运行: python manage.py setup_permissions")
    
    print("\n" + "=" * 60)

if __name__ == '__main__':
    check_admin_user()

