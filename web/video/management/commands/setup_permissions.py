"""
Django管理命令：设置权限组和权限

功能：
- 创建管理员组和审核组
- 为每个组分配相应的权限
- 可重复执行，不会重复创建
"""

from django.core.management.base import BaseCommand
from django.contrib.auth.models import Group, Permission
from django.contrib.contenttypes.models import ContentType
from video.models import Novel, Chapter, Character, Narration, AudioGenerationTask, CharacterImageTask


class Command(BaseCommand):
    """
    设置权限组和权限的管理命令
    
    使用方法：
    python manage.py setup_permissions
    """
    
    help = '设置系统权限组（管理员组、审核组）和相应权限'

    def handle(self, *args, **options):
        """
        执行权限设置
        """
        self.stdout.write(self.style.SUCCESS('开始设置权限系统...'))
        
        # 1. 创建管理员组
        admin_group = self._create_admin_group()
        
        # 2. 创建审核组
        reviewer_group = self._create_reviewer_group()
        
        self.stdout.write(self.style.SUCCESS('\n权限系统设置完成！'))
        self.stdout.write(self.style.SUCCESS(f'管理员组: {admin_group.name} - {admin_group.permissions.count()} 个权限'))
        self.stdout.write(self.style.SUCCESS(f'审核组: {reviewer_group.name} - {reviewer_group.permissions.count()} 个权限'))
        
        self.stdout.write(self.style.WARNING('\n提示：'))
        self.stdout.write('- 使用 Django Admin 将用户添加到相应的组中')
        self.stdout.write('- 管理员组拥有所有权限')
        self.stdout.write('- 审核组只能查看和审核内容，不能删除')

    def _create_admin_group(self):
        """
        创建管理员组并分配所有权限
        
        Returns:
            Group: 管理员组对象
        """
        self.stdout.write('正在创建管理员组...')
        
        # 获取或创建管理员组
        admin_group, created = Group.objects.get_or_create(name='管理员组')
        
        if created:
            self.stdout.write(self.style.SUCCESS('  ✓ 管理员组创建成功'))
        else:
            self.stdout.write(self.style.WARNING('  - 管理员组已存在，更新权限'))
        
        # 清除现有权限
        admin_group.permissions.clear()
        
        # 获取所有模型的所有权限
        models = [Novel, Chapter, Character, Narration, AudioGenerationTask, CharacterImageTask]
        permissions = []
        
        for model in models:
            content_type = ContentType.objects.get_for_model(model)
            model_permissions = Permission.objects.filter(content_type=content_type)
            permissions.extend(model_permissions)
            self.stdout.write(f'  + 添加 {model.__name__} 的所有权限')
        
        # 批量添加权限
        admin_group.permissions.add(*permissions)
        
        self.stdout.write(self.style.SUCCESS(f'  ✓ 管理员组权限设置完成 ({len(permissions)} 个权限)'))
        
        return admin_group

    def _create_reviewer_group(self):
        """
        创建审核组并分配查看和修改权限（不包括删除权限）
        
        Returns:
            Group: 审核组对象
        """
        self.stdout.write('\n正在创建审核组...')
        
        # 获取或创建审核组
        reviewer_group, created = Group.objects.get_or_create(name='审核组')
        
        if created:
            self.stdout.write(self.style.SUCCESS('  ✓ 审核组创建成功'))
        else:
            self.stdout.write(self.style.WARNING('  - 审核组已存在，更新权限'))
        
        # 清除现有权限
        reviewer_group.permissions.clear()
        
        # 获取所有模型的查看和修改权限（不包括删除和添加）
        models = [Novel, Chapter, Character, Narration, AudioGenerationTask, CharacterImageTask]
        permissions = []
        
        for model in models:
            content_type = ContentType.objects.get_for_model(model)
            
            # 只添加 view 和 change 权限
            view_perm = Permission.objects.filter(
                content_type=content_type,
                codename__startswith='view_'
            ).first()
            
            change_perm = Permission.objects.filter(
                content_type=content_type,
                codename__startswith='change_'
            ).first()
            
            if view_perm:
                permissions.append(view_perm)
                self.stdout.write(f'  + 添加 {model.__name__} 的查看权限')
            
            if change_perm:
                permissions.append(change_perm)
                self.stdout.write(f'  + 添加 {model.__name__} 的修改权限')
        
        # 批量添加权限
        reviewer_group.permissions.add(*permissions)
        
        self.stdout.write(self.style.SUCCESS(f'  ✓ 审核组权限设置完成 ({len(permissions)} 个权限)'))
        self.stdout.write(self.style.WARNING('  ! 审核组不包括删除和添加权限'))
        
        return reviewer_group

