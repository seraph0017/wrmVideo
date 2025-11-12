"""
章节审核相关视图

提供章节审核功能的视图和API
"""

from django.shortcuts import render, redirect, get_object_or_404
from django.contrib import messages
from django.contrib.auth.decorators import login_required
from django.http import JsonResponse
from django.views.decorators.http import require_http_methods
from django.utils import timezone
from django.db.models import Q

from video.models import Chapter
from video.permissions import reviewer_required, is_reviewer


@login_required
@reviewer_required
def chapter_review_list(request):
    """
    章节审核列表页面
    
    功能：
    - 审核组只能看到审核中（reviewing）的章节
    - 管理员可以看到所有状态的章节
    - 支持按状态筛选
    - 支持搜索
    
    Args:
        request: HTTP请求对象
    
    Returns:
        HttpResponse: 渲染的审核列表页面
    """
    from video.permissions import is_admin
    
    # 获取筛选参数
    status = request.GET.get('status', 'reviewing')
    search = request.GET.get('search', '')
    
    # 构建查询
    chapters = Chapter.objects.select_related('novel', 'reviewed_by')
    
    # 权限控制：审核组只能看到审核中的章节，管理员可以看到所有
    if not is_admin(request.user):
        # 审核组只能看到审核中的章节
        chapters = chapters.filter(review_status='reviewing')
        # 强制状态筛选为reviewing
        status = 'reviewing'
    else:
        # 管理员可以看到所有状态
        chapters = chapters.all()
        # 状态筛选
        if status and status != 'all':
            chapters = chapters.filter(review_status=status)
    
    # 搜索
    if search:
        chapters = chapters.filter(
            Q(title__icontains=search) | 
            Q(novel__name__icontains=search)
        )
    
    # 排序：审核中优先，然后按创建时间倒序
    chapters = chapters.order_by(
        '-id'
    )
    
    context = {
        'chapters': chapters,
        'current_status': status,
        'search': search,
        'status_choices': Chapter.REVIEW_STATUS_CHOICES,
    }
    
    return render(request, 'video/chapter_review_list.html', context)


@login_required
@reviewer_required
def chapter_review_detail(request, chapter_id):
    """
    章节审核详情页面
    
    功能：
    - 显示章节详细信息
    - 提供审核操作（通过/拒绝）
    
    Args:
        request: HTTP请求对象
        chapter_id: 章节ID
    
    Returns:
        HttpResponse: 渲染的审核详情页面
    """
    chapter = get_object_or_404(Chapter, id=chapter_id)
    
    context = {
        'chapter': chapter,
    }
    
    return render(request, 'video/chapter_review_detail.html', context)


@require_http_methods(["POST"])
@login_required
@reviewer_required
def chapter_approve(request, chapter_id):
    """
    审核通过章节
    
    功能：
    - 将章节状态设置为"审核通过"
    - 记录审核人和审核时间
    
    Args:
        request: HTTP请求对象
        chapter_id: 章节ID
    
    Returns:
        JsonResponse: 操作结果
    """
    try:
        chapter = get_object_or_404(Chapter, id=chapter_id)
        
        # 更新审核状态
        chapter.review_status = 'approved'
        chapter.review_reason = None  # 清空失败原因
        chapter.reviewed_by = request.user
        chapter.reviewed_at = timezone.now()
        chapter.save()
        
        return JsonResponse({
            'success': True,
            'message': f'章节《{chapter.title}》审核通过',
            'review_status': chapter.review_status,
            'reviewed_by': chapter.reviewed_by.username,
            'reviewed_at': chapter.reviewed_at.strftime('%Y-%m-%d %H:%M:%S')
        })
        
    except Exception as e:
        return JsonResponse({
            'success': False,
            'message': f'审核失败：{str(e)}'
        }, status=500)


@require_http_methods(["POST"])
@login_required
@reviewer_required
def chapter_reject(request, chapter_id):
    """
    审核拒绝章节
    
    功能：
    - 将章节状态设置为"审核失败"
    - 记录审核失败原因
    - 记录审核人和审核时间
    
    Args:
        request: HTTP请求对象
        chapter_id: 章节ID
    
    Returns:
        JsonResponse: 操作结果
    """
    try:
        chapter = get_object_or_404(Chapter, id=chapter_id)
        
        # 获取失败原因
        reason = request.POST.get('reason', '').strip()
        if not reason:
            return JsonResponse({
                'success': False,
                'message': '请填写审核失败原因'
            }, status=400)
        
        # 更新审核状态
        chapter.review_status = 'rejected'
        chapter.review_reason = reason
        chapter.reviewed_by = request.user
        chapter.reviewed_at = timezone.now()
        chapter.save()
        
        return JsonResponse({
            'success': True,
            'message': f'章节《{chapter.title}》审核失败',
            'review_status': chapter.review_status,
            'review_reason': chapter.review_reason,
            'reviewed_by': chapter.reviewed_by.username,
            'reviewed_at': chapter.reviewed_at.strftime('%Y-%m-%d %H:%M:%S')
        })
        
    except Exception as e:
        return JsonResponse({
            'success': False,
            'message': f'审核失败：{str(e)}'
        }, status=500)


@require_http_methods(["POST"])
@login_required
@reviewer_required
def chapter_reset_review(request, chapter_id):
    """
    重置章节审核状态
    
    功能：
    - 将章节状态重置为"未审核"
    - 清空审核信息
    
    Args:
        request: HTTP请求对象
        chapter_id: 章节ID
    
    Returns:
        JsonResponse: 操作结果
    """
    try:
        chapter = get_object_or_404(Chapter, id=chapter_id)
        
        # 重置审核状态
        chapter.review_status = 'pending'
        chapter.review_reason = None
        chapter.reviewed_by = None
        chapter.reviewed_at = None
        chapter.save()
        
        return JsonResponse({
            'success': True,
            'message': f'章节《{chapter.title}》审核状态已重置',
            'review_status': chapter.review_status
        })
        
    except Exception as e:
        return JsonResponse({
            'success': False,
            'message': f'重置失败：{str(e)}'
        }, status=500)


@require_http_methods(["POST"])
@login_required
@reviewer_required
def batch_approve_chapters(request):
    """
    批量审核通过章节
    
    功能：
    - 批量将多个章节状态设置为"审核通过"
    
    Args:
        request: HTTP请求对象
    
    Returns:
        JsonResponse: 操作结果
    """
    try:
        import json
        chapter_ids = json.loads(request.body).get('chapter_ids', [])
        
        if not chapter_ids:
            return JsonResponse({
                'success': False,
                'message': '请选择要审核的章节'
            }, status=400)
        
        # 批量更新
        updated_count = Chapter.objects.filter(id__in=chapter_ids).update(
            review_status='approved',
            review_reason=None,
            reviewed_by=request.user,
            reviewed_at=timezone.now()
        )
        
        return JsonResponse({
            'success': True,
            'message': f'成功审核通过 {updated_count} 个章节',
            'count': updated_count
        })
        
    except Exception as e:
        return JsonResponse({
            'success': False,
            'message': f'批量审核失败：{str(e)}'
        }, status=500)


@require_http_methods(["GET"])
@login_required
def get_chapter_review_status(request, chapter_id):
    """
    获取章节审核状态
    
    功能：
    - 返回章节的审核状态信息
    
    Args:
        request: HTTP请求对象
        chapter_id: 章节ID
    
    Returns:
        JsonResponse: 审核状态信息
    """
    try:
        chapter = get_object_or_404(Chapter, id=chapter_id)
        
        data = {
            'success': True,
            'review_status': chapter.review_status,
            'review_status_display': chapter.get_review_status_display(),
            'review_reason': chapter.review_reason,
            'reviewed_by': chapter.reviewed_by.username if chapter.reviewed_by else None,
            'reviewed_at': chapter.reviewed_at.strftime('%Y-%m-%d %H:%M:%S') if chapter.reviewed_at else None
        }
        
        return JsonResponse(data)
        
    except Exception as e:
        return JsonResponse({
            'success': False,
            'message': f'获取审核状态失败：{str(e)}'
        }, status=500)

