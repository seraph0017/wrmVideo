"""
权限检查模板标签

提供在模板中检查用户权限的标签和过滤器
"""

from django import template

register = template.Library()


@register.filter
def has_group(user, group_name):
    """
    检查用户是否属于指定组
    
    使用示例：
        {% if user|has_group:"管理员组" %}
            <p>您是管理员</p>
        {% endif %}
    
    Args:
        user: User对象
        group_name: 组名
    
    Returns:
        bool: 是否属于指定组
    """
    if not user or not user.is_authenticated:
        return False
    return user.groups.filter(name=group_name).exists()


@register.filter
def is_admin(user):
    """
    检查用户是否是管理员
    
    使用示例：
        {% if user|is_admin %}
            <a href="#" class="btn btn-danger">删除</a>
        {% endif %}
    
    Args:
        user: User对象
    
    Returns:
        bool: 是否是管理员
    """
    if not user or not user.is_authenticated:
        return False
    return user.groups.filter(name='管理员组').exists()


@register.filter
def is_reviewer(user):
    """
    检查用户是否是审核员（包括管理员）
    
    使用示例：
        {% if user|is_reviewer %}
            <a href="#" class="btn btn-primary">编辑</a>
        {% endif %}
    
    Args:
        user: User对象
    
    Returns:
        bool: 是否是审核员
    """
    if not user or not user.is_authenticated:
        return False
    return user.groups.filter(name__in=['管理员组', '审核组']).exists()


@register.filter
def in_any_group(user, group_names):
    """
    检查用户是否属于任一指定组（用逗号分隔）
    
    使用示例：
        {% if user|in_any_group:"管理员组,审核组" %}
            <p>您有权限查看此内容</p>
        {% endif %}
    
    Args:
        user: User对象
        group_names: 组名列表，用逗号分隔
    
    Returns:
        bool: 是否属于任一指定组
    """
    if not user or not user.is_authenticated:
        return False
    
    groups = [g.strip() for g in group_names.split(',')]
    return user.groups.filter(name__in=groups).exists()


@register.simple_tag
def user_groups(user):
    """
    获取用户所属的所有组
    
    使用示例：
        {% user_groups user as groups %}
        {% for group in groups %}
            <span class="badge">{{ group.name }}</span>
        {% endfor %}
    
    Args:
        user: User对象
    
    Returns:
        QuerySet: 用户所属的组
    """
    if not user or not user.is_authenticated:
        return []
    return user.groups.all()


@register.inclusion_tag('video/tags/permission_badge.html')
def permission_badge(user):
    """
    显示用户权限徽章
    
    使用示例：
        {% permission_badge user %}
    
    Args:
        user: User对象
    
    Returns:
        dict: 模板上下文
    """
    context = {
        'user': user,
        'is_admin': False,
        'is_reviewer': False,
        'groups': []
    }
    
    if user and user.is_authenticated:
        context['is_admin'] = user.groups.filter(name='管理员组').exists()
        context['is_reviewer'] = user.groups.filter(name__in=['管理员组', '审核组']).exists()
        context['groups'] = user.groups.all()
    
    return context

