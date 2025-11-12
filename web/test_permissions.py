"""
权限系统测试脚本

测试权限组和权限分配是否正确
"""

import os
import sys
import django

# 设置Django环境
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'web.settings')
django.setup()

from django.contrib.auth.models import User, Group, Permission
from video.models import Novel, Chapter, Character, Narration


def test_permissions():
    """
    测试权限系统
    """
    print("=" * 60)
    print("Django权限系统测试")
    print("=" * 60)
    
    # 1. 检查组是否存在
    print("\n1. 检查权限组...")
    try:
        admin_group = Group.objects.get(name='管理员组')
        print(f"   ✓ 管理员组存在 - {admin_group.permissions.count()} 个权限")
    except Group.DoesNotExist:
        print("   ✗ 管理员组不存在！请运行: python manage.py setup_permissions")
        return
    
    try:
        reviewer_group = Group.objects.get(name='审核组')
        print(f"   ✓ 审核组存在 - {reviewer_group.permissions.count()} 个权限")
    except Group.DoesNotExist:
        print("   ✗ 审核组不存在！请运行: python manage.py setup_permissions")
        return
    
    # 2. 显示管理员组权限
    print("\n2. 管理员组权限列表:")
    for perm in admin_group.permissions.all()[:10]:
        print(f"   - {perm.codename}: {perm.name}")
    if admin_group.permissions.count() > 10:
        print(f"   ... 还有 {admin_group.permissions.count() - 10} 个权限")
    
    # 3. 显示审核组权限
    print("\n3. 审核组权限列表:")
    for perm in reviewer_group.permissions.all():
        print(f"   - {perm.codename}: {perm.name}")
    
    # 4. 检查权限差异
    print("\n4. 权限对比:")
    admin_perms = set(admin_group.permissions.values_list('codename', flat=True))
    reviewer_perms = set(reviewer_group.permissions.values_list('codename', flat=True))
    
    only_admin = admin_perms - reviewer_perms
    print(f"   管理员独有权限 ({len(only_admin)} 个):")
    for perm in sorted(only_admin):
        print(f"   - {perm}")
    
    # 5. 检查用户
    print("\n5. 检查用户分组:")
    users = User.objects.all()
    if users.exists():
        for user in users[:5]:
            groups = user.groups.all()
            if groups.exists():
                group_names = ', '.join([g.name for g in groups])
                print(f"   - {user.username}: {group_names}")
            else:
                print(f"   - {user.username}: 无组")
    else:
        print("   没有用户")
    
    # 6. 创建测试用户示例
    print("\n6. 创建测试用户示例:")
    print("   要创建测试用户，请运行以下命令:")
    print("   ")
    print("   # 创建管理员用户")
    print("   python manage.py shell")
    print("   >>> from django.contrib.auth.models import User, Group")
    print("   >>> user = User.objects.create_user('admin_user', 'admin@example.com', 'password')")
    print("   >>> admin_group = Group.objects.get(name='管理员组')")
    print("   >>> user.groups.add(admin_group)")
    print("   ")
    print("   # 创建审核员用户")
    print("   >>> user = User.objects.create_user('reviewer_user', 'reviewer@example.com', 'password')")
    print("   >>> reviewer_group = Group.objects.get(name='审核组')")
    print("   >>> user.groups.add(reviewer_group)")
    
    print("\n" + "=" * 60)
    print("测试完成！")
    print("=" * 60)


def show_usage_examples():
    """
    显示使用示例
    """
    print("\n" + "=" * 60)
    print("使用示例")
    print("=" * 60)
    
    print("\n在视图中使用权限装饰器:")
    print("""
from video.permissions import admin_required, reviewer_required

@admin_required
def delete_novel(request, novel_id):
    # 只有管理员可以访问
    pass

@reviewer_required
def edit_chapter(request, chapter_id):
    # 管理员和审核员都可以访问
    pass
    """)
    
    print("\n在类视图中使用Mixin:")
    print("""
from video.permissions import AdminRequiredMixin, ReviewerRequiredMixin

class NovelDeleteView(AdminRequiredMixin, DeleteView):
    model = Novel
    # 只有管理员可以访问

class ChapterUpdateView(ReviewerRequiredMixin, UpdateView):
    model = Chapter
    # 管理员和审核员都可以访问
    """)
    
    print("\n在模板中检查权限:")
    print("""
{% load permission_tags %}

{% if user|is_admin %}
    <a href="#" class="btn btn-danger">删除</a>
{% endif %}

{% if user|is_reviewer %}
    <a href="#" class="btn btn-primary">编辑</a>
{% endif %}

{% if user|has_group:"管理员组" %}
    <p>您是管理员</p>
{% endif %}
    """)


if __name__ == '__main__':
    test_permissions()
    show_usage_examples()

