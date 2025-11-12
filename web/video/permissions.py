"""
权限系统工具模块

提供权限检查装饰器和Mixin类，用于视图权限控制
"""

from functools import wraps
from django.contrib.auth.decorators import login_required, user_passes_test
from django.contrib.auth.mixins import LoginRequiredMixin, UserPassesTestMixin
from django.core.exceptions import PermissionDenied
from django.shortcuts import redirect
from django.contrib import messages


def group_required(*group_names):
    """
    装饰器：检查用户是否属于指定的组
    
    使用示例：
        @group_required('管理员组')
        def my_view(request):
            pass
        
        @group_required('管理员组', '审核组')
        def my_view(request):
            pass
    
    Args:
        *group_names: 组名列表
    
    Returns:
        装饰器函数
    """
    def decorator(view_func):
        @wraps(view_func)
        @login_required
        def wrapper(request, *args, **kwargs):
            # 检查用户是否属于任一指定组
            if request.user.groups.filter(name__in=group_names).exists():
                return view_func(request, *args, **kwargs)
            
            # 用户不属于任何指定组，拒绝访问
            messages.error(request, f'您没有权限访问此页面。需要以下组之一：{", ".join(group_names)}')
            raise PermissionDenied(f'需要以下组之一：{", ".join(group_names)}')
        
        return wrapper
    return decorator


def admin_required(view_func):
    """
    装饰器：要求用户属于管理员组
    
    使用示例：
        @admin_required
        def my_admin_view(request):
            pass
    
    Args:
        view_func: 视图函数
    
    Returns:
        装饰后的函数
    """
    return group_required('管理员组')(view_func)


def reviewer_required(view_func):
    """
    装饰器：要求用户属于审核组或管理员组
    
    使用示例：
        @reviewer_required
        def my_review_view(request):
            pass
    
    Args:
        view_func: 视图函数
    
    Returns:
        装饰后的函数
    """
    return group_required('管理员组', '审核组')(view_func)


class GroupRequiredMixin(LoginRequiredMixin, UserPassesTestMixin):
    """
    Mixin类：检查用户是否属于指定的组
    
    使用示例：
        class MyView(GroupRequiredMixin, View):
            group_required = ['管理员组']
            
            def get(self, request):
                pass
    """
    
    # 需要的组名列表
    group_required = []
    
    def test_func(self):
        """
        测试用户是否属于指定组
        
        Returns:
            bool: 是否通过测试
        """
        if not self.group_required:
            return True
        
        return self.request.user.groups.filter(
            name__in=self.group_required
        ).exists()
    
    def handle_no_permission(self):
        """
        处理无权限情况
        
        Returns:
            HttpResponse: 重定向或错误页面
        """
        if not self.request.user.is_authenticated:
            return super().handle_no_permission()
        
        messages.error(
            self.request,
            f'您没有权限访问此页面。需要以下组之一：{", ".join(self.group_required)}'
        )
        raise PermissionDenied(f'需要以下组之一：{", ".join(self.group_required)}')


class AdminRequiredMixin(GroupRequiredMixin):
    """
    Mixin类：要求用户属于管理员组
    
    使用示例：
        class MyAdminView(AdminRequiredMixin, View):
            def get(self, request):
                pass
    """
    
    group_required = ['管理员组']


class ReviewerRequiredMixin(GroupRequiredMixin):
    """
    Mixin类：要求用户属于审核组或管理员组
    
    使用示例：
        class MyReviewView(ReviewerRequiredMixin, View):
            def get(self, request):
                pass
    """
    
    group_required = ['管理员组', '审核组']


def is_admin(user):
    """
    检查用户是否是管理员
    
    Args:
        user: User对象
    
    Returns:
        bool: 是否是管理员
    """
    return user.is_authenticated and user.groups.filter(name='管理员组').exists()


def is_reviewer(user):
    """
    检查用户是否是审核员（包括管理员）
    
    Args:
        user: User对象
    
    Returns:
        bool: 是否是审核员
    """
    return user.is_authenticated and user.groups.filter(
        name__in=['管理员组', '审核组']
    ).exists()


def has_group(user, *group_names):
    """
    检查用户是否属于指定的任一组
    
    Args:
        user: User对象
        *group_names: 组名列表
    
    Returns:
        bool: 是否属于指定组
    """
    return user.is_authenticated and user.groups.filter(
        name__in=group_names
    ).exists()

