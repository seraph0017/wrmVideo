#!/bin/bash

# Django权限系统快速设置脚本
# 
# 功能：
# 1. 初始化权限组和权限
# 2. 创建测试用户（可选）
# 3. 运行权限测试
#
# 使用方法：
# chmod +x setup_permissions.sh
# ./setup_permissions.sh

echo "======================================"
echo "Django权限系统快速设置"
echo "======================================"
echo ""

# 检查是否在web目录
if [ ! -f "manage.py" ]; then
    echo "错误：请在web目录下运行此脚本"
    echo "cd /Users/xunan/Projects/wrmVideo/web"
    exit 1
fi

# 1. 运行权限初始化命令
echo "步骤 1/3: 初始化权限组和权限..."
python manage.py setup_permissions

if [ $? -ne 0 ]; then
    echo "错误：权限初始化失败"
    exit 1
fi

echo ""
echo "✓ 权限初始化完成"
echo ""

# 2. 询问是否创建测试用户
echo "步骤 2/3: 创建测试用户（可选）"
read -p "是否创建测试用户？(y/n): " create_users

if [ "$create_users" = "y" ] || [ "$create_users" = "Y" ]; then
    echo ""
    echo "创建管理员测试用户..."
    python manage.py shell << EOF
from django.contrib.auth.models import User, Group

# 创建管理员用户
try:
    admin_user = User.objects.create_user('admin_test', 'admin@test.com', 'admin123')
    admin_group = Group.objects.get(name='管理员组')
    admin_user.groups.add(admin_group)
    print('✓ 管理员用户创建成功: admin_test / admin123')
except Exception as e:
    print(f'管理员用户已存在或创建失败: {e}')

# 创建审核员用户
try:
    reviewer_user = User.objects.create_user('reviewer_test', 'reviewer@test.com', 'reviewer123')
    reviewer_group = Group.objects.get(name='审核组')
    reviewer_user.groups.add(reviewer_group)
    print('✓ 审核员用户创建成功: reviewer_test / reviewer123')
except Exception as e:
    print(f'审核员用户已存在或创建失败: {e}')
EOF
fi

echo ""

# 3. 运行权限测试
echo "步骤 3/3: 运行权限测试..."
python test_permissions.py

echo ""
echo "======================================"
echo "设置完成！"
echo "======================================"
echo ""
echo "下一步："
echo "1. 访问 http://127.0.0.1:8000/admin/ 管理用户和组"
echo "2. 查看 PERMISSIONS_README.md 了解详细使用方法"
echo "3. 在视图中使用权限装饰器和Mixin"
echo ""

if [ "$create_users" = "y" ] || [ "$create_users" = "Y" ]; then
    echo "测试用户："
    echo "- 管理员: admin_test / admin123"
    echo "- 审核员: reviewer_test / reviewer123"
    echo ""
fi

