from django.shortcuts import render, get_object_or_404, redirect
from django.http import HttpResponse, JsonResponse
from django.views.generic import ListView, DetailView, CreateView, UpdateView, DeleteView
from django.urls import reverse_lazy
from django.contrib import messages
from django.contrib.auth import login, logout
from django.contrib.auth.decorators import login_required
from django.contrib.auth.mixins import LoginRequiredMixin
from django.db.models import Q
from django.views.decorators.csrf import csrf_exempt
from django.views.decorators.http import require_http_methods
from django.core.paginator import Paginator
from .forms import TaskForm, NovelForm, ChapterForm, CharacterForm, NarrationForm, SearchForm, CustomLoginForm
from .models import Novel, Chapter, Character, Narration, CharacterImageTask
from .utils import handle_uploaded_file, save_uploaded_file, upload_novel_to_tos, get_chapter_number_from_filesystem, get_chapter_directory_path
from .tasks import generate_script_async, validate_narration_async, generate_audio_async
from celery import current_app
from datetime import datetime
import json
import logging
import redis
import os
import subprocess
from django.conf import settings
from datetime import datetime

logger = logging.getLogger(__name__)


def get_default_character_image(character):
    """
    根据角色性别和年龄段获取默认图片路径
    
    Args:
        character: Character对象
    
    Returns:
        str: 默认图片路径
    """
    # 基础默认图片
    base_path = '/static/images/default_character'
    
    # 根据性别选择图片
    if character.gender == '男':
        if character.age_group in ['青年', '中年']:
            return f'{base_path}_male_adult.svg'
        elif character.age_group == '少年':
            return f'{base_path}_male_young.svg'
        elif character.age_group in ['老年', '长者']:
            return f'{base_path}_male_elder.svg'
        else:
            return f'{base_path}_male.svg'
    elif character.gender == '女':
        if character.age_group in ['青年', '中年']:
            return f'{base_path}_female_adult.svg'
        elif character.age_group == '少年':
            return f'{base_path}_female_young.svg'
        elif character.age_group in ['老年', '长者']:
            return f'{base_path}_female_elder.svg'
        else:
            return f'{base_path}_female.svg'
    else:
        # 未知性别或其他情况
        return f'{base_path}.svg'


def find_character_image_in_chapter(chapter_path, character_name):
    """
    在指定章节的images目录中查找角色图片
    
    Args:
        chapter_path: 章节目录路径
        character_name: 角色名称
    
    Returns:
        str: 角色图片文件路径，如果未找到返回None
    """
    try:
        # 移除角色名称中的特殊字符
        safe_character_name = character_name.replace('&', '')
        
        # 构建绝对路径（从项目根目录开始）
        # __file__ 是 /Users/xunan/Projects/wrmVideo/web/video/views.py
        # 需要向上两级到达项目根目录 /Users/xunan/Projects/wrmVideo
        project_root = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
        images_dir = os.path.join(project_root, chapter_path, "images")
        
        print(f"DEBUG: 查找角色图片 - 角色名称: {character_name}")
        print(f"DEBUG: 查找角色图片 - 安全角色名称: {safe_character_name}")
        print(f"DEBUG: 查找角色图片 - 章节路径: {chapter_path}")
        print(f"DEBUG: 查找角色图片 - 图片目录: {images_dir}")
        logger.debug(f"查找角色图片 - 角色名称: {character_name}")
        logger.debug(f"查找角色图片 - 安全角色名称: {safe_character_name}")
        logger.debug(f"查找角色图片 - 章节路径: {chapter_path}")
        logger.debug(f"查找角色图片 - 图片目录: {images_dir}")
        
        if not os.path.exists(images_dir):
            logger.debug(f"Images目录不存在: {images_dir}")
            return None
        
        # 支持的图片格式
        image_extensions = ['.jpg', '.jpeg', '.png', '.webp', '.bmp']
        
        # 列出目录中的所有文件
        files_in_dir = os.listdir(images_dir)
        logger.debug(f"目录中的文件: {files_in_dir}")
        
        # 查找匹配的图片文件
        for filename in files_in_dir:
            logger.debug(f"检查文件: {filename}")
            # 检查文件扩展名
            if any(filename.lower().endswith(ext) for ext in image_extensions):
                logger.debug(f"文件 {filename} 是图片格式")
                # 检查文件名是否包含角色名称
                if safe_character_name in filename or character_name in filename:
                    # 返回相对于项目根目录的路径
                    relative_path = os.path.join(chapter_path, "images", filename)
                    logger.debug(f"找到角色图片: {relative_path}")
                    return relative_path
                else:
                    logger.debug(f"文件 {filename} 不包含角色名称 '{character_name}' 或 '{safe_character_name}'")
            else:
                logger.debug(f"文件 {filename} 不是支持的图片格式")
        
        logger.debug(f"未找到角色 {character_name} 的图片文件")
        return None
        
    except Exception as e:
        logger.error(f"查找角色图片时发生错误: {e}")
        return None


def user_login(request):
    """
    用户登录视图
    """
    if request.user.is_authenticated:
        return redirect('video:dashboard')
    
    if request.method == 'POST':
        form = CustomLoginForm(request, data=request.POST)
        if form.is_valid():
            user = form.get_user()
            login(request, user)
            messages.success(request, f'欢迎回来，{user.username}！')
            # 获取next参数，如果没有则重定向到dashboard
            next_url = request.GET.get('next', 'video:dashboard')
            return redirect(next_url)
        else:
            messages.error(request, '登录失败，请检查用户名和密码。')
    else:
        form = CustomLoginForm()
    
    return render(request, 'video/login.html', {'form': form})


def user_logout(request):
    """
    用户登出视图
    """
    if request.user.is_authenticated:
        username = request.user.username
        logout(request)
        messages.success(request, f'再见，{username}！您已成功登出。')
    return redirect('video:login')


def index(request):
    return HttpResponse("Hello, world. You're at the polls index.")

def test_modal(request):
    """
    测试模态窗口功能的视图
    """
    return render(request, 'test_modal.html')


@login_required
def dashboard(request):
    """
    显示系统控制面板
    """
    form = TaskForm()
    
    if request.method == 'POST':
        form = TaskForm(request.POST)
        if form.is_valid():
            # 这里可以处理表单提交
            pass
    
    # 获取统计数据
    novel_count = Novel.objects.count()
    chapter_count = Chapter.objects.count()
    character_count = Character.objects.count()
    narration_count = Narration.objects.count()
    
    context = {
        'form': form,
        'novel_count': novel_count,
        'chapter_count': chapter_count,
        'character_count': character_count,
        'narration_count': narration_count,
    }
    return render(request, 'dashboard.html', context)


# 小说视图
class NovelListView(LoginRequiredMixin, ListView):
    """
    小说列表视图
    """
    model = Novel
    template_name = 'video/novel_list.html'
    context_object_name = 'novels'
    paginate_by = 10
    
    def get_queryset(self):
        """
        获取查询集，支持搜索功能
        审核组可以看到有审核相关章节的小说（审核中、已通过、已拒绝）
        """
        from video.permissions import is_admin
        
        queryset = Novel.objects.all()
        
        # 审核组权限过滤：显示有审核相关章节的小说（审核中、已通过、已拒绝）
        if not is_admin(self.request.user):
            queryset = queryset.filter(
                chapters__review_status__in=['reviewing', 'approved', 'rejected']
            ).distinct()
        
        search_query = self.request.GET.get('search')
        if search_query:
            queryset = queryset.filter(
                Q(name__icontains=search_query) |
                Q(type__icontains=search_query)
            )
        return queryset.order_by('-last_modified')
    
    def get_context_data(self, **kwargs):
        """
        添加搜索表单和章节数据到上下文
        审核组可以看到审核相关的章节
        """
        from video.permissions import is_admin
        
        context = super().get_context_data(**kwargs)
        context['search_form'] = SearchForm(self.request.GET)
        # 添加章节数据，用于批量生成功能中的章节选择
        # 审核组可以看到审核中、已通过、已拒绝的章节
        if is_admin(self.request.user):
            context['chapters'] = Chapter.objects.all().order_by('id')
        else:
            context['chapters'] = Chapter.objects.filter(
                review_status__in=['reviewing', 'approved', 'rejected']
            ).order_by('id')
        return context


class NovelDetailView(LoginRequiredMixin, DetailView):
    """
    小说详情视图
    """
    model = Novel
    template_name = 'video/novel_detail.html'
    context_object_name = 'novel'
    
    def get_queryset(self):
        """
        审核组可以访问有审核相关章节的小说（审核中、已通过、已拒绝）
        """
        from video.permissions import is_admin
        
        queryset = Novel.objects.all()
        
        # 审核组权限过滤：可以访问有审核相关章节的小说
        if not is_admin(self.request.user):
            queryset = queryset.filter(
                chapters__review_status__in=['reviewing', 'approved', 'rejected']
            ).distinct()
        
        return queryset
    
    def get_context_data(self, **kwargs):
        """
        审核组可以看到审核相关的章节（审核中、已通过、已拒绝）
        """
        from video.permissions import is_admin
        
        context = super().get_context_data(**kwargs)
        # 获取该小说的章节，审核组可以看到审核相关的章节
        if is_admin(self.request.user):
            context['chapters'] = self.object.chapters.all()
        else:
            context['chapters'] = self.object.chapters.filter(
                review_status__in=['reviewing', 'approved', 'rejected']
            )
        return context


class NovelCreateView(LoginRequiredMixin, CreateView):
    """
    小说创建视图
    """
    model = Novel
    form_class = NovelForm
    template_name = 'video/novel_form.html'
    success_url = reverse_lazy('video:novel_list')
    
    def form_valid(self, form):
        """
        处理表单验证成功后的逻辑，包括文件上传处理
        """
        try:
            # 获取上传的文件
            uploaded_file = self.request.FILES.get('original_file')
            
            if not uploaded_file:
                messages.error(self.request, '请上传小说文件')
                return self.form_invalid(form)
            
            # 从文件名自动提取小说名称（去掉扩展名）
            import os
            file_name = uploaded_file.name
            novel_name = os.path.splitext(file_name)[0]  # 去掉文件扩展名
            form.instance.name = novel_name
            
            # 提取文件内容
            try:
                extracted_content = handle_uploaded_file(uploaded_file)
                
                # 自动填充内容
                form.instance.content = extracted_content
                
                # 保存文件
                file_path = save_uploaded_file(uploaded_file, novel_name)
                form.instance.original_file = file_path
                
                # 自动计算字数
                form.instance.word_count = len(extracted_content.replace(' ', '').replace('\n', ''))
                
                # 根据内容自动判断类型（简单的关键词匹配）
                content_lower = extracted_content.lower()
                if any(keyword in content_lower for keyword in ['修仙', '仙侠', '灵气', '修炼', '丹药']):
                    form.instance.type = '仙侠'
                elif any(keyword in content_lower for keyword in ['都市', '现代', '都市生活', '职场']):
                    form.instance.type = '都市'
                elif any(keyword in content_lower for keyword in ['玄幻', '魔法', '异世界', '穿越']):
                    form.instance.type = '玄幻'
                elif any(keyword in content_lower for keyword in ['历史', '古代', '朝廷', '皇帝']):
                    form.instance.type = '历史'
                else:
                    form.instance.type = '其他'
                        
            except ValueError as e:
                # 检查是否为AJAX请求
                if self.request.headers.get('X-Requested-With') == 'XMLHttpRequest':
                    return JsonResponse({
                        'success': False,
                        'message': f'文件处理失败: {str(e)}'
                    })
                else:
                    messages.error(self.request, f'文件处理失败: {str(e)}')
                    return self.form_invalid(form)
            
            # 先保存实例到数据库
            response = super().form_valid(form)
            
            # 上传文件到TOS
            try:
                if form.instance.original_file:
                    upload_result = upload_novel_to_tos(form.instance.id, form.instance.original_file.path, uploaded_file.name)
                    if upload_result['success']:
                        print(f"TOS上传成功: {upload_result['message']}")
                    else:
                        print(f"TOS上传失败: {upload_result['message']}")
            except Exception as e:
                print(f"TOS上传异常: {str(e)}")
            
            # 检查是否为AJAX请求
            if self.request.headers.get('X-Requested-With') == 'XMLHttpRequest':
                return JsonResponse({
                    'success': True,
                    'message': '小说创建成功！',
                    'novel_id': form.instance.id,
                    'novel_name': form.instance.name
                })
            else:
                messages.success(self.request, '小说创建成功！')
                return response
            
        except Exception as e:
            # 检查是否为AJAX请求
            if self.request.headers.get('X-Requested-With') == 'XMLHttpRequest':
                return JsonResponse({
                    'success': False,
                    'message': f'创建失败: {str(e)}'
                })
            else:
                messages.error(self.request, f'创建失败: {str(e)}')
                return self.form_invalid(form)
    
    def form_invalid(self, form):
        """
        处理表单验证失败的情况
        """
        # 检查是否为AJAX请求
        if self.request.headers.get('X-Requested-With') == 'XMLHttpRequest':
            errors = {}
            for field, error_list in form.errors.items():
                errors[field] = [str(error) for error in error_list]
            return JsonResponse({
                'success': False,
                'message': '表单验证失败',
                'errors': errors
            })
        else:
            return super().form_invalid(form)


class NovelUpdateView(LoginRequiredMixin, UpdateView):
    """
    小说更新视图
    """
    model = Novel
    form_class = NovelForm
    template_name = 'video/novel_form.html'
    success_url = reverse_lazy('video:novel_list')
    
    def form_valid(self, form):
        """
        处理表单验证成功后的逻辑，包括文件上传处理
        """
        try:
            # 获取上传的文件
            uploaded_file = self.request.FILES.get('original_file')
            
            if uploaded_file:
                # 从文件名自动提取小说名称（去掉扩展名）
                import os
                file_name = uploaded_file.name
                novel_name = os.path.splitext(file_name)[0]  # 去掉文件扩展名
                form.instance.name = novel_name
                
                # 提取文件内容
                try:
                    extracted_content = handle_uploaded_file(uploaded_file)
                    
                    # 自动填充内容
                    form.instance.content = extracted_content
                    
                    # 保存文件
                    file_path = save_uploaded_file(uploaded_file, novel_name)
                    form.instance.original_file = file_path
                    
                    # 自动计算字数
                    form.instance.word_count = len(extracted_content.replace(' ', '').replace('\n', ''))
                    
                    # 根据内容自动判断类型（简单的关键词匹配）
                    content_lower = extracted_content.lower()
                    if any(keyword in content_lower for keyword in ['修仙', '仙侠', '灵气', '修炼', '丹药']):
                        form.instance.type = '仙侠'
                    elif any(keyword in content_lower for keyword in ['都市', '现代', '都市生活', '职场']):
                        form.instance.type = '都市'
                    elif any(keyword in content_lower for keyword in ['玄幻', '魔法', '异世界', '穿越']):
                        form.instance.type = '玄幻'
                    elif any(keyword in content_lower for keyword in ['历史', '古代', '朝廷', '皇帝']):
                        form.instance.type = '历史'
                    else:
                        form.instance.type = '其他'
                        
                except ValueError as e:
                    messages.error(self.request, f'文件处理失败: {str(e)}')
                    return self.form_invalid(form)
            
            # 保存小说到数据库
            response = super().form_valid(form)
            
            # 如果有上传文件，则上传到TOS
            if uploaded_file and hasattr(form.instance, 'id'):
                import logging
                logger = logging.getLogger(__name__)
                
                try:
                    logger.info(f"[Django视图] 准备上传文件到TOS，小说ID: {form.instance.id}")
                    logger.info(f"[Django视图] 上传文件名: {uploaded_file.name}")
                    
                    # 获取保存的文件路径
                    import os
                    from django.conf import settings
                    local_file_path = os.path.join(settings.MEDIA_ROOT, form.instance.original_file)
                    logger.info(f"[Django视图] 本地文件路径: {local_file_path}")
                    logger.info(f"[Django视图] MEDIA_ROOT: {settings.MEDIA_ROOT}")
                    logger.info(f"[Django视图] original_file字段值: {form.instance.original_file}")
                    
                    # 检查文件是否存在
                    if os.path.exists(local_file_path):
                        logger.info(f"[Django视图] 本地文件存在，开始调用TOS上传函数")
                    else:
                        logger.error(f"[Django视图] 本地文件不存在: {local_file_path}")
                    
                    # 上传到TOS
                    upload_result = upload_novel_to_tos(
                        novel_id=form.instance.id,
                        file_path=local_file_path,
                        original_filename=uploaded_file.name
                    )
                    
                    logger.info(f"[Django视图] TOS上传结果: {upload_result}")
                    
                    if upload_result['success']:
                        logger.info(f"[Django视图] TOS上传成功: {upload_result['object_key']}")
                        messages.success(self.request, f'小说更新成功！文件已上传到TOS: {upload_result["object_key"]}')
                    else:
                        logger.error(f"[Django视图] TOS上传失败: {upload_result['message']}")
                        messages.warning(self.request, f'小说更新成功，但TOS上传失败: {upload_result["message"]}')
                        
                except Exception as e:
                    logger.error(f"[Django视图] TOS上传异常: {str(e)}")
                    logger.error(f"[Django视图] 异常类型: {type(e).__name__}")
                    messages.warning(self.request, f'小说更新成功，但TOS上传失败: {str(e)}')
            else:
                import logging
                logger = logging.getLogger(__name__)
                if not uploaded_file:
                    logger.info(f"[Django视图] 没有上传文件，跳过TOS上传")
                elif not hasattr(form.instance, 'id'):
                    logger.info(f"[Django视图] 小说实例没有ID，跳过TOS上传")
                messages.success(self.request, '小说更新成功！')
            
            return response
            
        except Exception as e:
            messages.error(self.request, f'更新失败: {str(e)}')
            return self.form_invalid(form)


class NovelDeleteView(LoginRequiredMixin, DeleteView):
    """
    小说删除视图
    """
    model = Novel
    template_name = 'video/novel_confirm_delete.html'
    success_url = reverse_lazy('video:novel_list')
    
    def delete(self, request, *args, **kwargs):
        messages.success(self.request, '小说删除成功！')
        return super().delete(request, *args, **kwargs)


# 章节视图
class ChapterListView(LoginRequiredMixin, ListView):
    """
    章节列表视图
    """
    model = Chapter
    template_name = 'video/chapter_list.html'
    context_object_name = 'chapters'
    paginate_by = 10
    
    def get_queryset(self):
        """
        获取查询集，支持搜索功能
        审核组可以看到审核中、已通过、已拒绝的章节
        """
        from video.permissions import is_admin
        
        queryset = Chapter.objects.select_related('novel')
        
        # 审核组权限过滤：可以看到审核中、已通过、已拒绝的章节
        if is_admin(self.request.user):
            queryset = queryset.all()
        else:
            queryset = queryset.filter(review_status__in=['reviewing', 'approved', 'rejected'])
        
        search_query = self.request.GET.get('search')
        if search_query:
            queryset = queryset.filter(
                Q(title__icontains=search_query) |
                Q(novel__name__icontains=search_query) |
                Q(format__icontains=search_query)
            )
        return queryset.order_by('-id')
    
    def get_context_data(self, **kwargs):
        """
        添加搜索表单到上下文
        """
        context = super().get_context_data(**kwargs)
        context['search_form'] = SearchForm(self.request.GET)
        return context


class ChapterDetailView(LoginRequiredMixin, DetailView):
    """
    章节详情视图
    """
    model = Chapter
    template_name = 'video/chapter_detail.html'
    context_object_name = 'chapter'
    
    def get_queryset(self):
        """
        审核组可以访问审核中、已通过、已拒绝的章节（不能看未提交的）
        """
        from video.permissions import is_admin
        
        queryset = Chapter.objects.select_related('novel')
        
        # 审核组权限过滤：可以看到审核中、已通过、已拒绝的章节
        if not is_admin(self.request.user):
            queryset = queryset.filter(review_status__in=['reviewing', 'approved', 'rejected'])
        
        return queryset
    
    def get_context_data(self, **kwargs):
        from pathlib import Path
        import glob
        import os
        
        context = super().get_context_data(**kwargs)
        
        # 从数据库获取narrations
        context['narrations'] = self.object.narrations.all()
        
        # 从文件系统获取narration文件信息
        project_root = settings.BASE_DIR.parent
        novel_id = self.object.novel.id
        chapter_title = self.object.title
        
        # 构建章节目录路径
        chapter_dir = project_root / 'data' / f'{novel_id:03d}' / chapter_title
        
        # 读取文件系统中的narration信息
        file_narrations = []
        if chapter_dir.exists():
            # 查找所有音频文件
            audio_files = sorted(glob.glob(str(chapter_dir / '*.mp3')))
            
            for audio_file in audio_files:
                audio_name = os.path.basename(audio_file)
                # 提取编号，如 chapter_001_narration_01.mp3 -> 01
                import re
                match = re.search(r'narration_(\d+)', audio_name)
                if match:
                    number = int(match.group(1))
                    
                    # 查找对应的字幕文件（使用完整的命名模式）
                    subtitle_pattern = str(chapter_dir / f'chapter_*_narration_{number:02d}.ass')
                    subtitle_files = glob.glob(subtitle_pattern)
                    subtitle_file = Path(subtitle_files[0]) if subtitle_files else None
                    
                    # 查找对应的图片文件（过滤掉.json文件）
                    image_pattern = str(chapter_dir / f'chapter_*_image_{number:02d}.*')
                    all_image_files = glob.glob(image_pattern)
                    # 只保留图片文件，排除.json等非图片文件
                    image_files = [f for f in all_image_files if f.lower().endswith(('.jpeg', '.jpg', '.png', '.gif', '.webp'))]
                    
                    # 构建相对于项目根目录的路径（data/xxx/...）
                    audio_rel_path = os.path.relpath(audio_file, project_root)
                    subtitle_rel_path = os.path.relpath(subtitle_file, project_root) if subtitle_file and subtitle_file.exists() else None
                    image_rel_path = os.path.relpath(image_files[0], project_root) if image_files else None
                    
                    file_narrations.append({
                        'number': number,
                        'audio_path': audio_rel_path,
                        'audio_name': audio_name,
                        'subtitle_path': subtitle_rel_path,
                        'subtitle_exists': subtitle_file is not None and subtitle_file.exists(),
                        'image_path': image_rel_path,
                        'image_exists': len(image_files) > 0,
                        'image_count': len(image_files)
                    })
        
        context['file_narrations'] = file_narrations
        
        # 提取视频文件名用于显示
        if self.object.video_path:
            context['video_filename'] = os.path.basename(self.object.video_path)
        else:
            context['video_filename'] = '未设置'
            
        return context


class ChapterCreateView(LoginRequiredMixin, CreateView):
    """
    章节创建视图
    """
    model = Chapter
    form_class = ChapterForm
    template_name = 'video/chapter_form.html'
    success_url = reverse_lazy('video:chapter_list')
    
    def form_valid(self, form):
        messages.success(self.request, '章节创建成功！')
        return super().form_valid(form)


class ChapterUpdateView(LoginRequiredMixin, UpdateView):
    """
    章节更新视图
    """
    model = Chapter
    form_class = ChapterForm
    template_name = 'video/chapter_form.html'
    success_url = reverse_lazy('video:chapter_list')
    
    def form_valid(self, form):
        messages.success(self.request, '章节更新成功！')
        return super().form_valid(form)


class ChapterDeleteView(LoginRequiredMixin, DeleteView):
    """
    章节删除视图
    """
    model = Chapter
    template_name = 'video/chapter_confirm_delete.html'
    success_url = reverse_lazy('video:chapter_list')
    
    def delete(self, request, *args, **kwargs):
        messages.success(self.request, '章节删除成功！')
        return super().delete(request, *args, **kwargs)


# 角色视图
class CharacterListView(LoginRequiredMixin, ListView):
    """
    角色列表视图
    """
    model = Character
    template_name = 'video/character_list.html'
    context_object_name = 'characters'
    paginate_by = 10
    
    def get_queryset(self):
        """
        获取查询集，支持搜索功能
        """
        queryset = Character.objects.select_related('chapter').all()
        search_query = self.request.GET.get('search')
        if search_query:
            queryset = queryset.filter(
                Q(name__icontains=search_query) |
                Q(gender__icontains=search_query) |
                Q(age_group__icontains=search_query)
            )
        return queryset.order_by('-id')
    
    def get_context_data(self, **kwargs):
        """
        添加搜索表单到上下文
        """
        context = super().get_context_data(**kwargs)
        context['search_form'] = SearchForm(self.request.GET)
        return context


class CharacterDetailView(LoginRequiredMixin, DetailView):
    """
    角色详情视图
    """
    model = Character
    template_name = 'video/character_detail.html'
    context_object_name = 'character'
    
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        # 角色现在只关联一个章节，不需要传递chapters列表
        return context


class CharacterCreateView(LoginRequiredMixin, CreateView):
    """
    角色创建视图
    """
    model = Character
    form_class = CharacterForm
    template_name = 'video/character_form.html'
    success_url = reverse_lazy('video:character_list')
    
    def form_valid(self, form):
        messages.success(self.request, '角色创建成功！')
        return super().form_valid(form)


class CharacterUpdateView(LoginRequiredMixin, UpdateView):
    """
    角色更新视图
    """
    model = Character
    form_class = CharacterForm
    template_name = 'video/character_form.html'
    success_url = reverse_lazy('video:character_list')
    
    def form_valid(self, form):
        messages.success(self.request, '角色更新成功！')
        return super().form_valid(form)


class CharacterDeleteView(LoginRequiredMixin, DeleteView):
    """
    角色删除视图
    """
    model = Character
    template_name = 'video/character_confirm_delete.html'
    success_url = reverse_lazy('video:character_list')
    
    def delete(self, request, *args, **kwargs):
        messages.success(self.request, '角色删除成功！')
        return super().delete(request, *args, **kwargs)


# 解说视图
class NarrationListView(LoginRequiredMixin, ListView):
    """
    解说列表视图
    """
    model = Narration
    template_name = 'video/narration_list.html'
    context_object_name = 'narrations'
    paginate_by = 10
    
    def get_queryset(self):
        """
        获取查询集，支持搜索功能
        """
        queryset = Narration.objects.select_related('chapter__novel').all()
        search_query = self.request.GET.get('search')
        if search_query:
            queryset = queryset.filter(
                Q(scene_number__icontains=search_query) |
                Q(featured_character__icontains=search_query) |
                Q(chapter__title__icontains=search_query) |
                Q(narration__icontains=search_query)
            )
        return queryset.order_by('-id')
    
    def get_context_data(self, **kwargs):
        """
        添加搜索表单到上下文
        """
        context = super().get_context_data(**kwargs)
        context['search_form'] = SearchForm(self.request.GET)
        return context


class NarrationDetailView(LoginRequiredMixin, DetailView):
    """
    解说详情视图
    """
    model = Narration
    template_name = 'video/narration_detail.html'
    context_object_name = 'narration'
    
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['chapter'] = self.object.chapter
        return context


class NarrationCreateView(LoginRequiredMixin, CreateView):
    """
    解说创建视图
    """
    model = Narration
    form_class = NarrationForm
    template_name = 'video/narration_form.html'
    success_url = reverse_lazy('video:narration_list')
    
    def form_valid(self, form):
        messages.success(self.request, '解说创建成功！')
        return super().form_valid(form)


class NarrationUpdateView(LoginRequiredMixin, UpdateView):
    """
    解说更新视图
    """
    model = Narration
    form_class = NarrationForm
    template_name = 'video/narration_form.html'
    success_url = reverse_lazy('video:narration_list')
    
    def form_valid(self, form):
        messages.success(self.request, '解说更新成功！')
        return super().form_valid(form)


class NarrationDeleteView(LoginRequiredMixin, DeleteView):
    """
    解说删除视图
    """
    model = Narration
    template_name = 'video/narration_confirm_delete.html'
    success_url = reverse_lazy('video:narration_list')
    
    def delete(self, request, *args, **kwargs):
        messages.success(self.request, '解说删除成功！')
        return super().delete(request, *args, **kwargs)


@login_required
def novel_ai_process(request, pk):
    """
    小说AI处理视图
    处理小说的AI分析，包括章节分割、角色提取、解说生成等
    """
    if request.method != 'POST':
        return JsonResponse({'success': False, 'message': '仅支持POST请求'})
    
    try:
        novel = get_object_or_404(Novel, pk=pk)
        
        # 检查小说是否有内容
        if not novel.content:
            return JsonResponse({
                'success': False, 
                'message': '小说内容为空，无法进行AI处理'
            })
        
        # 模拟AI处理过程（这里可以集成实际的AI处理逻辑）
        import time
        import re
        
        # 1. 自动识别小说类型（如果类型为空）
        if not novel.type:
            content_lower = novel.content.lower()
            if any(keyword in content_lower for keyword in ['修仙', '仙侠', '灵气', '修炼', '丹药', '法宝', '元婴', '金丹']):
                novel.type = '仙侠'
            elif any(keyword in content_lower for keyword in ['都市', '现代', '都市生活', '职场', '白领', '公司']):
                novel.type = '都市'
            elif any(keyword in content_lower for keyword in ['玄幻', '魔法', '异世界', '穿越', '系统', '魔兽']):
                novel.type = '玄幻'
            elif any(keyword in content_lower for keyword in ['历史', '古代', '朝廷', '皇帝', '大臣', '宫廷']):
                novel.type = '历史'
            elif any(keyword in content_lower for keyword in ['科幻', '未来', '机器人', '太空', '星际', '外星']):
                novel.type = '科幻'
            elif any(keyword in content_lower for keyword in ['武侠', '江湖', '武功', '侠客', '剑客', '武林']):
                novel.type = '武侠'
            elif any(keyword in content_lower for keyword in ['言情', '爱情', '恋爱', '情感', '浪漫']):
                novel.type = '言情'
            else:
                novel.type = '其他'
            novel.save()
        
        # 2. 自动章节分割
        content = novel.content
        # 简单的章节分割逻辑：按照"第X章"或"第X回"等模式分割
        chapter_pattern = r'第[一二三四五六七八九十百千万\d]+[章回节]'
        chapters = re.split(chapter_pattern, content)
        
        # 创建章节记录
        created_chapters = 0
        for i, chapter_content in enumerate(chapters[1:], 1):  # 跳过第一个空元素
            if chapter_content.strip():  # 确保章节内容不为空
                chapter_title = f"第{i}章"
                # 检查是否已存在该章节
                if not Chapter.objects.filter(novel=novel, title=chapter_title).exists():
                    Chapter.objects.create(
                        novel=novel,
                        title=chapter_title,
                        content=chapter_content.strip()[:1000],  # 限制内容长度
                        order=i
                    )
                    created_chapters += 1
        
        # 3. 角色提取（简单的关键词匹配）
        character_keywords = ['主角', '男主', '女主', '师父', '师傅', '长老', '掌门']
        created_characters = 0
        for keyword in character_keywords:
            if keyword in content and not Character.objects.filter(novel=novel, name=keyword).exists():
                Character.objects.create(
                    novel=novel,
                    name=keyword,
                    description=f"从小说《{novel.name}》中提取的角色",
                    role='主要角色' if keyword in ['主角', '男主', '女主'] else '次要角色'
                )
                created_characters += 1
        
        # 4. 生成解说文案（简单示例）
        created_narrations = 0
        if not Narration.objects.filter(novel=novel).exists():
            Narration.objects.create(
                novel=novel,
                title="开篇解说",
                content=f"欢迎来到小说《{novel.name}》的世界。这是一部{novel.type}类型的作品，共有{novel.word_count}字。让我们一起走进这个精彩的故事...",
                order=1
            )
            created_narrations += 1
        
        # 返回处理结果
        type_info = f"- 识别类型：{novel.type}\n" if novel.type else ""
        message = f"AI处理完成！\n" \
                 f"{type_info}" \
                 f"- 创建章节：{created_chapters}个\n" \
                 f"- 提取角色：{created_characters}个\n" \
                 f"- 生成解说：{created_narrations}个"
        
        return JsonResponse({
            'success': True,
            'message': message,
            'data': {
                'chapters_created': created_chapters,
                'characters_created': created_characters,
                'narrations_created': created_narrations
            }
        })
        
    except Exception as e:
        return JsonResponse({
            'success': False,
            'message': f'AI处理过程中发生错误：{str(e)}'
        })


@login_required
def novel_ai_generate(request, pk):
    """
    小说AI生成视图
    处理小说的AI生成，包括章节分割、角色提取、解说生成等
    """
    if request.method != 'POST':
        return JsonResponse({'success': False, 'message': '仅支持POST请求'})
    
    try:
        novel = get_object_or_404(Novel, pk=pk)
        
        # 检查小说是否有内容
        if not novel.content:
            return JsonResponse({
                'success': False, 
                'message': '小说内容为空，无法进行AI生成'
            })
        
        # 模拟AI生成过程
        import time
        import re
        
        # 1. 自动识别小说类型（如果类型为空）
        if not novel.type:
            content_lower = novel.content.lower()
            if any(keyword in content_lower for keyword in ['修仙', '仙侠', '灵气', '修炼', '丹药', '法宝', '元婴', '金丹']):
                novel.type = '仙侠'
            elif any(keyword in content_lower for keyword in ['都市', '现代', '都市生活', '职场', '白领', '公司']):
                novel.type = '都市'
            elif any(keyword in content_lower for keyword in ['玄幻', '魔法', '异世界', '穿越', '系统', '魔兽']):
                novel.type = '玄幻'
            elif any(keyword in content_lower for keyword in ['历史', '古代', '朝廷', '皇帝', '大臣', '宫廷']):
                novel.type = '历史'
            elif any(keyword in content_lower for keyword in ['科幻', '未来', '机器人', '太空', '星际', '外星']):
                novel.type = '科幻'
            elif any(keyword in content_lower for keyword in ['武侠', '江湖', '武功', '侠客', '剑客', '武林']):
                novel.type = '武侠'
            elif any(keyword in content_lower for keyword in ['言情', '爱情', '恋爱', '情感', '浪漫']):
                novel.type = '言情'
            else:
                novel.type = '其他'
            novel.save()
        
        # 2. 自动章节分割
        content = novel.content
        chapter_pattern = r'第[一二三四五六七八九十百千万\d]+[章回节]'
        chapters = re.split(chapter_pattern, content)
        
        # 创建章节记录
        created_chapters = 0
        for i, chapter_content in enumerate(chapters[1:], 1):
            if chapter_content.strip():
                chapter_title = f"第{i}章"
                if not Chapter.objects.filter(novel=novel, title=chapter_title).exists():
                    Chapter.objects.create(
                        novel=novel,
                        title=chapter_title,
                        content=chapter_content.strip()[:1000],
                        order=i
                    )
                    created_chapters += 1
        
        # 3. 角色提取
        character_keywords = ['主角', '男主', '女主', '师父', '师傅', '长老', '掌门']
        created_characters = 0
        for keyword in character_keywords:
            if keyword in content and not Character.objects.filter(novel=novel, name=keyword).exists():
                Character.objects.create(
                    novel=novel,
                    name=keyword,
                    description=f"从小说《{novel.name}》中提取的角色",
                    role='主要角色' if keyword in ['主角', '男主', '女主'] else '次要角色'
                )
                created_characters += 1
        
        # 4. 生成解说文案
        created_narrations = 0
        if not Narration.objects.filter(novel=novel).exists():
            Narration.objects.create(
                novel=novel,
                title="开篇解说",
                content=f"欢迎来到小说《{novel.name}》的世界。这是一部{novel.type}类型的作品，共有{novel.word_count}字。让我们一起走进这个精彩的故事...",
                order=1
            )
            created_narrations += 1
        
        # 返回生成结果
        type_info = f"- 识别类型：{novel.type}\n" if novel.type else ""
        message = f"AI生成完成！\n" \
                 f"{type_info}" \
                 f"- 创建章节：{created_chapters}个\n" \
                 f"- 提取角色：{created_characters}个\n" \
                 f"- 生成解说：{created_narrations}个"
        
        return JsonResponse({
            'success': True,
            'message': message,
            'data': {
                'chapters_created': created_chapters,
                'characters_created': created_characters,
                'narrations_created': created_narrations
            }
        })
        
    except Exception as e:
        return JsonResponse({
            'success': False,
            'message': f'AI生成过程中发生错误：{str(e)}'
        })


@login_required
def novel_ai_validate(request, pk):
    """
    小说AI校验视图
    校验小说的完整性、一致性和质量
    """
    if request.method != 'POST':
        return JsonResponse({'success': False, 'message': '仅支持POST请求'})
    
    try:
        novel = get_object_or_404(Novel, pk=pk)
        
        # 检查小说是否有内容
        if not novel.content:
            return JsonResponse({
                'success': False, 
                'message': '小说内容为空，无法进行AI校验'
            })
        
        # 校验结果统计
        validation_results = []
        warnings = []
        errors = []
        
        # 1. 检查基本信息完整性
        if not novel.name:
            errors.append("小说名称为空")
        if not novel.type:
            warnings.append("小说类型未设置")
        if novel.word_count <= 0:
            warnings.append("字数统计异常")
        
        # 2. 检查章节完整性
        chapters = Chapter.objects.filter(novel=novel).order_by('order')
        if not chapters.exists():
            warnings.append("未找到任何章节")
        else:
            # 检查章节顺序
            expected_order = 1
            for chapter in chapters:
                if chapter.order != expected_order:
                    warnings.append(f"章节顺序异常：期望第{expected_order}章，实际第{chapter.order}章")
                expected_order += 1
            
            # 检查章节内容
            empty_chapters = chapters.filter(content__isnull=True).count()
            if empty_chapters > 0:
                warnings.append(f"发现{empty_chapters}个空章节")
        
        # 3. 检查角色一致性
        characters = Character.objects.filter(novel=novel)
        if not characters.exists():
            warnings.append("未找到任何角色")
        else:
            # 检查主要角色
            main_characters = characters.filter(role='主要角色')
            if not main_characters.exists():
                warnings.append("未找到主要角色")
            
            # 检查角色描述
            empty_desc_count = characters.filter(
                Q(face_features__isnull=True) | Q(face_features='') |
                Q(body_features__isnull=True) | Q(body_features='')
            ).count()
            if empty_desc_count > 0:
                warnings.append(f"发现{empty_desc_count}个角色缺少面部或身材特征描述")
        
        # 4. 检查解说文案质量
        narrations = Narration.objects.filter(novel=novel)
        if not narrations.exists():
            warnings.append("未找到任何解说文案")
        else:
            # 检查解说内容
            empty_narrations = narrations.filter(content__isnull=True).count()
            if empty_narrations > 0:
                warnings.append(f"发现{empty_narrations}个空解说")
            
            # 检查解说长度
            short_narrations = [n for n in narrations if n.content and len(n.content) < 50]
            if short_narrations:
                warnings.append(f"发现{len(short_narrations)}个解说内容过短")
        
        # 5. 内容质量检查
        content_issues = []
        if novel.content:
            # 检查重复内容
            lines = novel.content.split('\n')
            duplicate_lines = len(lines) - len(set(lines))
            if duplicate_lines > 10:
                content_issues.append(f"发现{duplicate_lines}行重复内容")
            
            # 检查特殊字符
            import re
            special_chars = re.findall(r'[^\u4e00-\u9fa5\w\s\.,;:!?""''()（）【】《》]', novel.content)
            if len(special_chars) > 50:
                content_issues.append(f"发现{len(special_chars)}个异常字符")
        
        if content_issues:
            warnings.extend(content_issues)
        
        # 生成校验报告
        total_issues = len(errors) + len(warnings)
        if total_issues == 0:
            status = "优秀"
            message = "AI校验完成！\n\n✅ 校验通过，未发现问题\n\n小说结构完整，内容质量良好。"
        elif len(errors) == 0:
            status = "良好"
            message = f"AI校验完成！\n\n⚠️ 发现{len(warnings)}个警告\n\n" + "\n".join([f"• {w}" for w in warnings[:5]])
            if len(warnings) > 5:
                message += f"\n\n还有{len(warnings) - 5}个其他警告..."
        else:
            status = "需要修复"
            message = f"AI校验完成！\n\n❌ 发现{len(errors)}个错误，{len(warnings)}个警告\n\n错误：\n" + "\n".join([f"• {e}" for e in errors])
            if warnings:
                message += "\n\n警告：\n" + "\n".join([f"• {w}" for w in warnings[:3]])
        
        return JsonResponse({
            'success': True,
            'message': message,
            'data': {
                'status': status,
                'errors_count': len(errors),
                'warnings_count': len(warnings),
                'chapters_count': chapters.count() if 'chapters' in locals() else 0,
                'characters_count': characters.count() if 'characters' in locals() else 0,
                'narrations_count': narrations.count() if 'narrations' in locals() else 0
            }
        })
        
    except Exception as e:
        return JsonResponse({
            'success': False,
            'message': f'AI校验过程中发生错误：{str(e)}'
        })


@login_required
def novel_generate_script(request, pk):
    """
    生成解说文案 - 对应 gen_script_v2.py 的操作
    """
    if request.method == 'POST':
        try:
            novel = get_object_or_404(Novel, pk=pk)
            
            # 检查是否已经在生成中
            if novel.task_status == 'generating_script':
                return JsonResponse({
                    'success': False,
                    'message': f'小说《{novel.name}》正在生成解说文案中，请稍后再试',
                    'task_status': novel.task_status
                })
            
            # 解析请求参数
            data = json.loads(request.body)
            parameters = data.get('parameters', {})
            
            # 设置默认参数值
            script_params = {
                'chapters': parameters.get('chapters', 50),
                'limit': parameters.get('limit'),
                'workers': parameters.get('workers', 5),
                'min_length': parameters.get('min_length', 1200),
                'max_length': parameters.get('max_length', 1700),
                'max_retries': parameters.get('max_retries', 3),
                'validate_only': parameters.get('validate_only', False),
                'regenerate': parameters.get('regenerate', False)
            }
            
            # 导入异步任务
            from .tasks import generate_script_async
            
            # 更新任务状态
            novel.task_status = 'generating_script'
            novel.task_message = '正在生成解说文案...'
            novel.save()
            
            # 启动异步任务，传递参数
            task = generate_script_async.delay(novel.id, script_params)
            
            # 保存任务ID
            novel.current_task_id = task.id
            novel.save()
            
            return JsonResponse({
                'success': True,
                'message': f'正在为小说《{novel.name}》生成解说文案...',
                'task_id': task.id,
                'task_status': novel.task_status,
                'parameters': script_params
            })
            
        except Exception as e:
            return JsonResponse({
                'success': False,
                'message': f'生成解说文案失败: {str(e)}'
            })
    else:
        return JsonResponse({
            'success': False,
            'message': '请求方法不支持'
        })


@login_required
def novel_task_status(request, pk):
    """
    获取小说任务状态
    """
    try:
        novel = get_object_or_404(Novel, pk=pk)
        
        return JsonResponse({
            'success': True,
            'task_status': novel.task_status,
            'task_message': novel.task_message,
            'current_task_id': novel.current_task_id,
            'task_updated_at': novel.task_updated_at.isoformat() if novel.task_updated_at else None
        })
        
    except Exception as e:
        return JsonResponse({
            'success': False,
            'message': f'获取任务状态失败: {str(e)}'
        })


def novel_validate_narration(request, pk):
    """
    校验解说文案 - 对应 validate_narration.py 的操作
    """
    novel = get_object_or_404(Novel, pk=pk)
    
    if request.method == 'GET':
        # 显示校验配置页面
        context = {
            'novel': novel,
            'page_title': f'AI校验解说文案 - {novel.name}'
        }
        return render(request, 'video/ai_validation.html', context)
    
    elif request.method == 'POST':
        try:
            # 获取校验参数
            auto_rewrite = request.POST.get('auto_rewrite', 'false') == 'true'
            auto_fix_characters = request.POST.get('auto_fix_characters', 'false') == 'true'
            auto_fix_tags = request.POST.get('auto_fix_tags', 'false') == 'true'
            check_closeup_length = request.POST.get('check_closeup_length', 'false') == 'true'
            check_total_length = request.POST.get('check_total_length', 'false') == 'true'
            
            # 导入异步任务
            from .tasks import validate_narration_async
            
            # 构建校验参数
            validation_params = {
                'auto_rewrite': auto_rewrite,
                'auto_fix_characters': auto_fix_characters,
                'auto_fix_tags': auto_fix_tags,
                'check_closeup_length': check_closeup_length,
                'check_total_length': check_total_length
            }
            
            # 启动异步任务
            task = validate_narration_async.delay(novel.id, validation_params)
            
            return JsonResponse({
                'success': True,
                'message': f'正在校验小说《{novel.name}》的解说文案...',
                'task_id': task.id
            })
            
        except Exception as e:
            return JsonResponse({
                'success': False,
                'message': f'校验解说文案失败: {str(e)}'
            })
    else:
        return JsonResponse({
            'success': False,
            'message': '请求方法不支持'
        })


@csrf_exempt
def novel_ai_validation(request, pk):
    """
    AI校验页面视图函数
    支持GET请求显示校验配置页面，POST请求执行校验任务
    """
    novel = get_object_or_404(Novel, pk=pk)
    
    if request.method == 'GET':
        # 显示校验配置页面
        context = {
            'novel': novel,
            'page_title': f'AI智能校验 - {novel.name}'
        }
        return render(request, 'video/ai_validation.html', context)
    
    elif request.method == 'POST':
        try:
            # 解析JSON请求体
            data = json.loads(request.body)
            parameters = data.get('parameters', {})
            
            # 获取校验参数
            validation_params = {
                'auto_fix': parameters.get('auto_fix', True),
                'check_closeup_length': parameters.get('check_closeup_length', False),
                'check_total_length': parameters.get('check_total_length', False),
                'auto_rewrite': parameters.get('auto_rewrite', False),
                'auto_fix_characters': parameters.get('auto_fix_characters', False),
                'auto_fix_tags': parameters.get('auto_fix_tags', False),
                'auto_fix_structure': parameters.get('auto_fix_structure', False),
            }
            
            # 启动异步校验任务
            task = validate_narration_async.apply_async(args=[novel.id, validation_params])
            
            # 更新数据库中的任务状态
            novel.task_status = 'validation_running'
            novel.task_message = '正在校验解说文案...'
            novel.current_task_id = task.id
            novel.save()
            
            return JsonResponse({
                'success': True,
                'task_id': task.id,
                'message': '校验任务已启动'
            })
            
        except Exception as e:
            logger.error(f"AI校验时发生错误: {str(e)}")
            return JsonResponse({
                'success': False,
                'message': f'启动校验任务失败: {str(e)}'
            })
    
    return JsonResponse({
        'success': False,
        'message': '不支持的请求方法'
    }, status=405)


@csrf_exempt
@require_http_methods(["GET"])
def task_monitor(request):
    """
    Celery任务监控页面
    """
    try:
        # 获取Celery应用实例
        celery_app = current_app
        
        # 获取活跃任务
        active_tasks = celery_app.control.inspect().active()
        
        # 获取已注册任务
        registered_tasks = celery_app.control.inspect().registered()
        
        # 获取统计信息
        stats = celery_app.control.inspect().stats()
        
        context = {
            'active_tasks': active_tasks or {},
            'registered_tasks': registered_tasks or {},
            'stats': stats or {},
            'current_time': datetime.now().strftime('%Y-%m-%d %H:%M:%S')
        }
        
        return render(request, 'video/task_monitor.html', context)
        
    except Exception as e:
        logger.error(f"任务监控页面错误: {str(e)}")
        return render(request, 'video/task_monitor.html', {
            'error': f'无法连接到Celery: {str(e)}',
            'current_time': datetime.now().strftime('%Y-%m-%d %H:%M:%S')
        })


@csrf_exempt
@require_http_methods(["GET"])
def task_status_api(request, task_id):
    """
    获取任务状态的API接口
    """
    try:
        # 获取任务结果
        from celery.result import AsyncResult
        result = AsyncResult(task_id)
        
        response_data = {
            'task_id': task_id,
            'status': result.status,
            'ready': result.ready(),
            'successful': result.successful() if result.ready() else None,
            'failed': result.failed() if result.ready() else None,
        }
        
        # 如果任务完成，获取结果
        if result.ready():
            if result.successful():
                response_data['result'] = result.result
            elif result.failed():
                response_data['error'] = str(result.info)
        else:
            # 如果任务正在进行，尝试获取进度信息
            if hasattr(result, 'info') and result.info:
                response_data['info'] = result.info
        
        return JsonResponse(response_data)
        
    except Exception as e:
        logger.error(f"获取任务状态错误: {str(e)}")
        return JsonResponse({
            'task_id': task_id,
            'status': 'ERROR',
            'error': str(e)
        })


@csrf_exempt
@require_http_methods(["GET"])
def task_list_api(request):
    """
    获取任务列表的API接口
    """
    try:
        celery_app = current_app
        
        # 获取活跃任务
        active_tasks = celery_app.control.inspect().active()
        
        # 获取预定任务
        scheduled_tasks = celery_app.control.inspect().scheduled()
        
        # 获取保留任务
        reserved_tasks = celery_app.control.inspect().reserved()
        
        response_data = {
            'active': active_tasks or {},
            'scheduled': scheduled_tasks or {},
            'reserved': reserved_tasks or {},
            'timestamp': datetime.now().isoformat()
        }
        
        return JsonResponse(response_data)
        
    except Exception as e:
        logger.error(f"获取任务列表错误: {str(e)}")
        return JsonResponse({
            'error': str(e),
            'timestamp': datetime.now().isoformat()
        })


@csrf_exempt
@require_http_methods(["POST"])
def task_revoke_api(request, task_id):
    """
    撤销任务的API接口
    """
    try:
        celery_app = current_app
        
        # 撤销任务
        celery_app.control.revoke(task_id, terminate=True)
        
        return JsonResponse({
            'success': True,
            'message': f'任务 {task_id} 已被撤销',
            'task_id': task_id
        })
        
    except Exception as e:
        logger.error(f"撤销任务错误: {str(e)}")
        return JsonResponse({
            'success': False,
            'error': str(e),
            'task_id': task_id
        })


@csrf_exempt
@require_http_methods(["GET"])
def get_task_log(request, pk):
    """
    获取任务实时日志的API接口
    """
    try:
        task_id = request.GET.get('task_id')
        if not task_id:
            return JsonResponse({
                'success': False,
                'message': '缺少task_id参数'
            })
        
        # 获取任务状态
        from celery.result import AsyncResult
        result = AsyncResult(task_id)
        
        # 从日志文件获取真实的日志数据
        from .log_views import get_recent_logs
        
        # 获取与该任务相关的日志（最近200行）
        all_logs = get_recent_logs(task_id=task_id, lines=200)
        
        # 格式化日志数据
        formatted_logs = []
        for log_entry in all_logs:
            # 确定日志级别对应的前端样式
            level = log_entry.get('level', 'INFO').lower()
            if level in ['error', 'critical']:
                display_level = 'error'
            elif level in ['warning', 'warn']:
                display_level = 'warning'
            else:
                display_level = 'info'
            
            formatted_logs.append({
                'message': log_entry.get('message', ''),
                'level': display_level,
                'timestamp': log_entry.get('timestamp', '')
            })
        
        # 如果没有找到相关日志，添加一些基础状态信息
        if not formatted_logs:
            if result.status == 'PENDING':
                formatted_logs = [
                    {'message': '任务已提交，等待执行...', 'level': 'info'},
                ]
            elif result.status == 'STARTED':
                formatted_logs = [
                    {'message': '任务已开始执行', 'level': 'info'},
                    {'message': '正在初始化参数...', 'level': 'info'},
                ]
            elif result.status == 'SUCCESS':
                formatted_logs = [
                    {'message': '任务执行成功！', 'level': 'info'},
                ]
            elif result.status == 'FAILURE':
                formatted_logs = [
                    {'message': '任务执行失败', 'level': 'error'},
                    {'message': f'错误信息: {str(result.info)}', 'level': 'error'},
                ]
        
        # 计算进度
        progress = 0
        if result.status == 'PENDING':
            progress = 0
        elif result.status == 'STARTED':
            progress = 10
        elif result.status == 'PROGRESS':
            if hasattr(result, 'info') and isinstance(result.info, dict):
                current_progress = result.info.get('current', 0)
                total_progress = result.info.get('total', 100)
                progress = int((current_progress / total_progress) * 100) if total_progress > 0 else 50
            else:
                progress = 50
        elif result.status == 'SUCCESS':
            progress = 100
        elif result.status == 'FAILURE':
            progress = 0
        
        response_data = {
            'success': True,
            'task_id': task_id,
            'status': result.status,
            'logs': formatted_logs,
            'progress': progress,
            'timestamp': datetime.now().isoformat()
        }
        
        return JsonResponse(response_data)
        
    except Exception as e:
        logger.error(f"获取任务日志错误: {str(e)}")
        return JsonResponse({
            'success': False,
            'task_id': task_id if 'task_id' in locals() else 'unknown',
            'status': 'ERROR',
            'logs': [{'message': f'获取日志失败: {str(e)}', 'level': 'error'}],
            'error': str(e),
            'timestamp': datetime.now().isoformat()
        })


@csrf_exempt
@require_http_methods(["POST"])
def stop_task(request, pk):
    """
    停止任务的API接口
    """
    try:
        data = json.loads(request.body)
        task_id = data.get('task_id')
        
        if not task_id:
            return JsonResponse({
                'success': False,
                'message': '缺少task_id参数'
            })
        
        # 撤销任务
        current_app.control.revoke(task_id, terminate=True)
        
        return JsonResponse({
            'success': True,
            'message': '任务停止请求已发送',
            'task_id': task_id
        })
        
    except Exception as e:
        logger.error(f"停止任务错误: {str(e)}")
        return JsonResponse({
            'success': False,
            'message': f'停止任务失败: {str(e)}'
        })

@require_http_methods(["GET"])
def task_logs_view(request):
    """
    显示任务日志监控页面
    
    Args:
        request: HTTP请求
    
    Returns:
        HttpResponse: 渲染的任务日志页面
    """
    task_id = request.GET.get('task_id')
    
    context = {
        'task_id': task_id,
        'current_time': datetime.now().strftime('%Y-%m-%d %H:%M:%S')
    }
    
    return render(request, 'video/task_logs.html', context)


@csrf_exempt
@require_http_methods(["GET"])
def validation_status(request, pk, task_id):
    """
    获取AI校验任务状态
    """
    try:
        novel = get_object_or_404(Novel, pk=pk)
        
        # 获取任务状态
        task_result = current_app.AsyncResult(task_id)
        
        if task_result.state == 'PENDING':
            response = {
                'status': 'pending',
                'progress': 0,
                'status_text': '任务等待中...'
            }
        elif task_result.state == 'PROGRESS':
            info = task_result.info
            response = {
                'status': 'running',
                'progress': info.get('progress', 0),
                'status_text': info.get('status', '正在校验...')
            }
        elif task_result.state == 'SUCCESS':
            result = task_result.result
            response = {
                'status': 'completed',
                'progress': 100,
                'status_text': '校验完成',
                'result': result
            }
        elif task_result.state == 'FAILURE':
            response = {
                'status': 'failed',
                'progress': 0,
                'status_text': '校验失败',
                'error': str(task_result.info)
            }
        else:
            response = {
                'status': 'unknown',
                'progress': 0,
                'status_text': f'未知状态: {task_result.state}'
            }
        
        return JsonResponse(response)
        
    except Exception as e:
        logger.error(f"获取校验状态失败: {str(e)}")
        return JsonResponse({
            'status': 'error',
            'error': f'获取状态失败: {str(e)}'
        }, status=500)


@csrf_exempt
@require_http_methods(["POST"])
def batch_generate_audio(request, chapter_id):
    """
    批量生成章节所有解说的音频API
    
    Args:
        request: HTTP请求对象
        chapter_id: 章节ID
        
    Returns:
        JsonResponse: 处理结果
    """
    try:
        # 获取章节对象
        chapter = get_object_or_404(Chapter, id=chapter_id)
        novel_id = chapter.novel.id
        
        # 获取章节下的所有解说
        narrations = chapter.narrations.all()
        
        if not narrations.exists():
            return JsonResponse({
                'success': False,
                'error': '该章节没有解说内容'
            }, status=400)
        
        logger.info(f"开始批量生成音频: 小说ID={novel_id}, 章节ID={chapter_id}, 解说数量={narrations.count()}")
        
        # 导入Celery任务
        from .tasks import generate_audio_async
        
        # 启动异步任务
        task = generate_audio_async.delay(novel_id, chapter_id)
        
        logger.info(f"批量生成音频任务已启动: task_id={task.id}")
        
        return JsonResponse({
            'success': True,
            'message': '批量生成音频任务已启动',
            'task_id': task.id,
            'novel_id': novel_id,
            'chapter_id': chapter_id,
            'count': narrations.count()
        })
        
    except Chapter.DoesNotExist:
        logger.error(f"章节不存在: chapter_id={chapter_id}")
        return JsonResponse({
            'success': False,
            'error': f'章节不存在: {chapter_id}'
        }, status=404)
        
    except Exception as e:
        logger.error(f"批量生成音频失败: {str(e)}")
        return JsonResponse({
            'success': False,
            'error': f'批量生成音频失败: {str(e)}'
        }, status=500)


@csrf_exempt
@require_http_methods(["GET"])
def serve_chapter_video(request, chapter_id):
    """
    提供章节视频文件服务
    
    Args:
        request: HTTP请求对象
        chapter_id: 章节ID
    
    Returns:
        HttpResponse: 视频文件响应或错误信息
    """
    try:
        # 获取章节对象
        chapter = get_object_or_404(Chapter, id=chapter_id)
        
        # 检查是否有视频路径
        if not chapter.video_path:
            return JsonResponse({
                'success': False,
                'message': '该章节还没有生成视频'
            }, status=404)
        
        # 检查视频文件是否存在
        if not os.path.exists(chapter.video_path):
            return JsonResponse({
                'success': False,
                'message': '视频文件不存在'
            }, status=404)
        
        # 获取文件大小
        file_size = os.path.getsize(chapter.video_path)
        
        # 处理Range请求（用于视频流播放）
        range_header = request.META.get('HTTP_RANGE')
        if range_header:
            # 解析Range头
            range_match = range_header.replace('bytes=', '').split('-')
            start = int(range_match[0]) if range_match[0] else 0
            end = int(range_match[1]) if range_match[1] else file_size - 1
            
            # 确保范围有效
            if start >= file_size:
                return HttpResponse(status=416)  # Range Not Satisfiable
            
            if end >= file_size:
                end = file_size - 1
            
            # 读取指定范围的文件内容
            with open(chapter.video_path, 'rb') as video_file:
                video_file.seek(start)
                chunk_size = end - start + 1
                video_data = video_file.read(chunk_size)
            
            # 创建部分内容响应
            response = HttpResponse(
                video_data,
                content_type='video/mp4',
                status=206  # Partial Content
            )
            response['Content-Range'] = f'bytes {start}-{end}/{file_size}'
            response['Accept-Ranges'] = 'bytes'
            response['Content-Length'] = str(chunk_size)
            
        else:
            # 完整文件响应
            with open(chapter.video_path, 'rb') as video_file:
                video_data = video_file.read()
            
            response = HttpResponse(
                video_data,
                content_type='video/mp4'
            )
            response['Content-Length'] = str(file_size)
            response['Accept-Ranges'] = 'bytes'
        
        # 设置缓存头
        response['Cache-Control'] = 'public, max-age=3600'
        response['Content-Disposition'] = f'inline; filename="{os.path.basename(chapter.video_path)}"'
        
        return response
        
    except Exception as e:
        logger.error(f"提供视频文件时出错: {str(e)}")
        return JsonResponse({
            'success': False,
            'message': f'服务器错误: {str(e)}'
        }, status=500)


@csrf_exempt
@require_http_methods(["POST"])
@csrf_exempt
@require_http_methods(["POST"])
def validate_narration_images_llm(request, chapter_id):
    """
    校验旁白图片API (使用LLM)
    
    Args:
        request: HTTP请求对象
        chapter_id: 章节ID
        
    Returns:
        JsonResponse: 处理结果
    """
    try:
        # 获取章节对象
        chapter = get_object_or_404(Chapter, id=chapter_id)
        novel_id = chapter.novel.id
        
        logger.info(f"开始校验旁白图片(LLM): 小说ID={novel_id}, 章节ID={chapter_id}")
        
        # 导入Celery任务
        from .tasks import validate_narration_images_llm_async
        
        # 启动异步任务
        task = validate_narration_images_llm_async.delay(novel_id, chapter_id)
        
        logger.info(f"校验旁白图片(LLM)任务已启动: task_id={task.id}")
        
        return JsonResponse({
            'success': True,
            'message': '校验旁白图片(LLM)任务已启动',
            'task_id': task.id,
            'novel_id': novel_id,
            'chapter_id': chapter_id
        })
        
    except Chapter.DoesNotExist:
        logger.error(f"章节不存在: chapter_id={chapter_id}")
        return JsonResponse({
            'success': False,
            'error': f'章节不存在: {chapter_id}'
        }, status=404)
        
    except Exception as e:
        logger.error(f"校验旁白图片(LLM)失败: {str(e)}")
        return JsonResponse({
            'success': False,
            'error': f'校验旁白图片(LLM)失败: {str(e)}'
        }, status=500)


@csrf_exempt
@require_http_methods(["POST"])
def batch_generate_videos(request, chapter_id):
    """
    批量生成视频API
    
    Args:
        request: HTTP请求对象
        chapter_id: 章节ID
        
    Returns:
        JsonResponse: 处理结果
    """
    try:
        # 获取章节对象
        chapter = get_object_or_404(Chapter, id=chapter_id)
        novel_id = chapter.novel.id
        
        logger.info(f"开始批量生成视频: 小说ID={novel_id}, 章节ID={chapter_id}")
        
        # 导入Celery任务
        from .tasks import concat_narration_video_async
        
        # 启动异步任务
        task = concat_narration_video_async.delay(novel_id, chapter_id)
        
        logger.info(f"批量生成视频任务已启动: task_id={task.id}")
        
        return JsonResponse({
            'success': True,
            'message': '批量生成视频任务已启动',
            'task_id': task.id,
            'novel_id': novel_id,
            'chapter_id': chapter_id
        })
        
    except Chapter.DoesNotExist:
        logger.error(f"章节不存在: chapter_id={chapter_id}")
        return JsonResponse({
            'success': False,
            'error': f'章节不存在: {chapter_id}'
        }, status=404)
        
    except Exception as e:
        logger.error(f"批量生成视频失败: {str(e)}")
        return JsonResponse({
            'success': False,
            'error': f'批量生成视频失败: {str(e)}'
        }, status=500)


@csrf_exempt
@require_http_methods(["POST"])
def generate_first_video(request, chapter_id):
    """
    生成首视频API
    
    Args:
        request: HTTP请求对象
        chapter_id: 章节ID
        
    Returns:
        JsonResponse: 处理结果
    """
    try:
        # 获取章节对象
        chapter = get_object_or_404(Chapter, id=chapter_id)
        novel_id = chapter.novel.id
        
        logger.info(f"开始生成首视频: 小说ID={novel_id}, 章节ID={chapter_id}")
        
        # 导入Celery任务
        from .tasks import generate_first_video_async
        
        # 启动异步任务
        task = generate_first_video_async.delay(novel_id, chapter_id)
        
        logger.info(f"生成首视频任务已启动: task_id={task.id}")
        
        return JsonResponse({
            'success': True,
            'message': '生成首视频任务已启动',
            'task_id': task.id,
            'novel_id': novel_id,
            'chapter_id': chapter_id
        })
        
    except Chapter.DoesNotExist:
        logger.error(f"章节不存在: chapter_id={chapter_id}")
        return JsonResponse({
            'success': False,
            'error': f'章节不存在: {chapter_id}'
        }, status=404)
        
    except Exception as e:
        logger.error(f"生成首视频失败: {str(e)}")
        return JsonResponse({
            'success': False,
            'error': f'生成首视频失败: {str(e)}'
        }, status=500)


@csrf_exempt
@require_http_methods(["POST"])
def get_image_generation_result(request, narration_id):
    """
    查询火山引擎图片生成任务结果
    
    Args:
        request: HTTP请求对象
        narration_id (int): 解说ID
        
    Returns:
        JsonResponse: 任务结果
    """
    from .tasks import get_volcengine_image_result
    
    try:
        # 从请求中获取火山引擎任务ID
        data = json.loads(request.body)
        volcengine_task_id = data.get('task_id')
        
        if not volcengine_task_id:
            return JsonResponse({
                'status': 'error',
                'message': '缺少task_id参数'
            }, status=400)
        
        logger.info(f"查询解说 {narration_id} 的火山引擎图片生成结果，任务ID: {volcengine_task_id}")
        
        # 启动查询任务
        task = get_volcengine_image_result.delay(narration_id, volcengine_task_id)
        
        return JsonResponse({
            'status': 'success',
            'task_id': task.id,
            'message': f'开始查询解说 {narration_id} 的图片生成结果'
        })
        
    except json.JSONDecodeError:
        return JsonResponse({
            'status': 'error',
            'message': '请求数据格式错误'
        }, status=400)
    except Exception as e:
        logger.error(f"查询解说 {narration_id} 图片生成结果异常: {str(e)}")
        return JsonResponse({
            'status': 'error',
            'message': f'查询图片生成结果失败: {str(e)}'
        }, status=500)


@csrf_exempt
@require_http_methods(["POST"])
def batch_generate_images(request, chapter_id):
    """
    使用gen_image_async_v2.py脚本批量生成章节分镜图片API
    """
    try:
        # 获取章节对象
        chapter = get_object_or_404(Chapter, id=chapter_id)
        
        # 检查章节是否有解说内容（可选检查）
        narrations = chapter.narrations.all()
        if not narrations.exists():
            return JsonResponse({
                'success': False,
                'error': '该章节没有解说内容'
            }, status=400)
        
        # 检查是否已有任务在运行
        if hasattr(chapter, 'batch_image_status') and chapter.batch_image_status == 'processing':
            return JsonResponse({
                'success': False,
                'error': '该章节已有分镜图片生成任务在运行中'
            }, status=400)
        
        # 导入新的异步任务
        from .tasks import gen_image_async_v2_task
        
        # 启动gen_image_async_v2异步任务
        task = gen_image_async_v2_task.delay(chapter.novel.id, chapter.id)
        
        return JsonResponse({
            'success': True,
            'message': f'正在使用gen_image_async_v2为章节 {chapter.title} 生成分镜图片...',
            'task_id': task.id,
            'chapter_id': chapter.id,
            'novel_id': chapter.novel.id,
            'note': '任务已提交，使用gen_image_async_v2.py脚本按章节生成分镜图片'
        })
        
    except Exception as e:
        return JsonResponse({
            'success': False,
            'error': str(e)
        }, status=500)


@csrf_exempt
@require_http_methods(["POST"])
def batch_generate_images_v4(request, chapter_id):
    """
    使用gen_image_async_v4.py脚本批量生成章节分镜图片API (ComfyUI版本)
    
    POST参数:
        api_url (可选): ComfyUI API地址，默认为 http://127.0.0.1:8188
        workflow_json (可选): 工作流JSON文件路径，默认为 test/comfyui/image_compact.json
    """
    try:
        # 获取章节对象
        chapter = get_object_or_404(Chapter, id=chapter_id)
        
        # 检查章节是否有解说内容（可选检查）
        narrations = chapter.narrations.all()
        if not narrations.exists():
            return JsonResponse({
                'success': False,
                'error': '该章节没有解说内容'
            }, status=400)
        
        # 检查是否已有任务在运行
        if hasattr(chapter, 'batch_image_status') and chapter.batch_image_status == 'processing':
            return JsonResponse({
                'success': False,
                'error': '该章节已有分镜图片生成任务在运行中'
            }, status=400)
        
        # 获取POST参数
        try:
            data = json.loads(request.body) if request.body else {}
        except json.JSONDecodeError:
            data = {}
        
        api_url = data.get('api_url', 'http://127.0.0.1:8188/api/prompt')
        # 兼容传入基础地址的情况：自动补全到 /api/prompt
        try:
            if isinstance(api_url, str):
                base = api_url.rstrip('/')
                if '/api/prompt' not in base:
                    # 若仅包含 /api 则追加 /prompt；若不包含，则追加 /api/prompt
                    if base.endswith('/api'):
                        api_url = base + '/prompt'
                    else:
                        api_url = base + '/api/prompt'
        except Exception:
            # 保底，不影响请求流程
            pass
        workflow_json = data.get('workflow_json', 'test/comfyui/image_compact.json')
        
        # 导入新的异步任务
        from .tasks import gen_image_async_v4_task
        
        # 启动gen_image_async_v4异步任务
        task = gen_image_async_v4_task.delay(
            chapter.novel.id, 
            chapter.id,
            api_url=api_url,
            workflow_json=workflow_json
        )
        
        return JsonResponse({
            'success': True,
            'message': f'正在使用gen_image_async_v4为章节 {chapter.title} 生成分镜图片...',
            'task_id': task.id,
            'chapter_id': chapter.id,
            'novel_id': chapter.novel.id,
            'api_url': api_url,
            'workflow_json': workflow_json,
            'note': '任务已提交，使用gen_image_async_v4.py脚本通过ComfyUI生成分镜图片'
        })
        
    except Exception as e:
        return JsonResponse({
            'success': False,
            'error': str(e)
        }, status=500)


@csrf_exempt
@require_http_methods(["POST"])
def regenerate_narration_image(request, novel_id, chapter_id, narration_id):
    """
    重新生成解说分镜图片API
    
    Args:
        novel_id: 小说ID
        chapter_id: 章节ID  
        narration_id: 解说ID
        
    POST参数:
        custom_prompt: 自定义提示词
        
    Returns:
        JSON响应包含操作结果
    """
    try:
        # 获取解说对象
        narration = get_object_or_404(Narration, id=narration_id, chapter_id=chapter_id, chapter__novel_id=novel_id)
        
        # 获取POST参数
        data = json.loads(request.body)
        custom_prompt = data.get('custom_prompt', '').strip()
        
        if not custom_prompt:
            return JsonResponse({
                'success': False,
                'error': '请输入自定义提示词'
            }, status=400)
        
        # 获取文件系统中的章节编号
        chapter_number = get_chapter_number_from_filesystem(novel_id, narration.chapter)
        if chapter_number is None:
            return JsonResponse({
                'success': False,
                'error': f'找不到章节对应的文件系统目录'
            }, status=404)
        
        # 解析scene_number获取图片编号
        scene_number = narration.scene_number
        try:
            if '-' in scene_number:
                # 解析"段-分镜"格式，转换为连续编号
                parts = scene_number.split('-')
                segment = int(parts[0])
                scene = int(parts[1])
                # 计算连续编号：(段-1)*3 + 分镜
                image_number = (segment - 1) * 3 + scene
            else:
                image_number = int(scene_number)
        except (ValueError, IndexError):
            image_number = 1
        
        # 构建图片文件路径
        image_filename = f'chapter_{chapter_number}_image_{image_number:02d}.jpeg'
        image_path = os.path.join(
            settings.BASE_DIR.parent,  # 回到项目根目录
            'data',
            f'{novel_id:03d}',
            f'chapter_{chapter_number}',
            image_filename
        )
        
        # 检查图片文件是否存在
        if not os.path.exists(image_path):
            return JsonResponse({
                'success': False,
                'error': f'图片文件不存在: {image_filename}'
            }, status=404)
        
        # 构建llm_narration_image.py脚本路径
        script_path = os.path.join(settings.BASE_DIR.parent, 'llm_narration_image.py')
        
        # 检查脚本是否存在
        if not os.path.exists(script_path):
            return JsonResponse({
                'success': False,
                'error': 'llm_narration_image.py脚本不存在'
            }, status=404)
        
        # 构建命令参数
        cmd = [
            'python',
            script_path,
            image_path,
            '--auto-regenerate',
            '--custom-prompt', custom_prompt,
            '--skip-analysis'
        ]
        
        # 执行命令
        try:
            # 设置工作目录为项目根目录
            cwd = settings.BASE_DIR.parent
            
            # 执行命令，捕获输出
            result = subprocess.run(
                cmd,
                cwd=cwd,
                capture_output=True,
                text=True,
                timeout=300  # 5分钟超时
            )
            
            if result.returncode == 0:
                return JsonResponse({
                    'success': True,
                    'message': '图片重新生成成功',
                    'output': result.stdout,
                    'image_path': image_filename
                })
            else:
                return JsonResponse({
                    'success': False,
                    'error': f'脚本执行失败: {result.stderr}',
                    'output': result.stdout
                }, status=500)
                
        except subprocess.TimeoutExpired:
            return JsonResponse({
                'success': False,
                'error': '脚本执行超时（超过5分钟）'
            }, status=500)
        except Exception as e:
            return JsonResponse({
                'success': False,
                'error': f'执行脚本时发生错误: {str(e)}'
            }, status=500)
        
    except json.JSONDecodeError:
        return JsonResponse({
            'success': False,
            'error': '无效的JSON数据'
        }, status=400)
    except Exception as e:
        return JsonResponse({
            'success': False,
            'error': str(e)
        }, status=500)


@csrf_exempt
@require_http_methods(["POST"])
def batch_generate_chapter_images(request, chapter_id):
    """
    批量生成章节分镜图片API - 直接关联gen_image_async.py
    按章节调用gen_image_async的generate_images_for_chapter函数
    
    Args:
        request: HTTP请求对象
        chapter_id: 章节ID
        
    Returns:
        JsonResponse: 任务提交结果
    """
    try:
        # 获取章节对象
        chapter = get_object_or_404(Chapter, id=chapter_id)
        
        # 检查是否已有任务在运行
        if chapter.batch_image_status == 'processing':
            return JsonResponse({
                'success': False,
                'error': f'章节 {chapter.title} 的分镜图片生成任务正在进行中，请等待完成后再试',
                'current_status': chapter.batch_image_status,
                'current_progress': chapter.batch_image_progress,
                'task_id': chapter.batch_image_task_id
            }, status=400)
        
        # 导入批量生成任务
        from .tasks import batch_generate_chapter_images_async
        
        # 启动异步任务
        task = batch_generate_chapter_images_async.delay(chapter.novel.id, chapter.id)
        
        return JsonResponse({
            'success': True,
            'message': f'已启动章节 {chapter.title} 的分镜图片批量生成任务',
            'task_id': task.id,
            'chapter_id': chapter.id,
            'chapter_title': chapter.title,
            'novel_id': chapter.novel.id,
            'status': 'submitted'
        })
        
    except Exception as e:
        logger.error(f"启动批量生成章节分镜图片任务失败: {str(e)}")
        return JsonResponse({
            'success': False,
            'error': str(e)
        }, status=500)


@csrf_exempt
@require_http_methods(["GET"])
def get_chapter_batch_image_status(request, chapter_id):
    """
    获取章节批量图片生成状态API
    
    Args:
        request: HTTP请求对象
        chapter_id: 章节ID
        
    Returns:
        JsonResponse: 任务状态信息
    """
    try:
        # 获取章节对象
        chapter = get_object_or_404(Chapter, id=chapter_id)
        
        return JsonResponse({
            'success': True,
            'chapter_id': chapter.id,
            'chapter_title': chapter.title,
            'status': chapter.batch_image_status,
            'progress': chapter.batch_image_progress,
            'message': chapter.batch_image_message,
            'error': chapter.batch_image_error,
            'task_id': chapter.batch_image_task_id,
            'started_at': chapter.batch_image_started_at.isoformat() if chapter.batch_image_started_at else None,
            'completed_at': chapter.batch_image_completed_at.isoformat() if chapter.batch_image_completed_at else None
        })
        
    except Exception as e:
        logger.error(f"获取章节批量图片生成状态失败: {str(e)}")
        return JsonResponse({
            'success': False,
            'error': str(e)
        }, status=500)


@csrf_exempt
@require_http_methods(["POST"])
def batch_generate_all_videos(request, chapter_id):
    """
    批量生成全部视频API - 包含完整的视频制作流程
    
    Args:
        request: HTTP请求对象
        chapter_id: 章节ID
        
    Returns:
        JsonResponse: 处理结果
    """
    try:
        # 获取章节对象
        chapter = get_object_or_404(Chapter, id=chapter_id)
        novel_id = chapter.novel.id
        
        # 获取章节下的所有解说
        narrations = chapter.narrations.all()
        
        if not narrations.exists():
            return JsonResponse({
                'success': False,
                'error': '该章节没有解说内容'
            }, status=400)
        
        logger.info(f"开始批量生成全部视频: 小说ID={novel_id}, 章节ID={chapter_id}, 解说数量={narrations.count()}")
        
        # 导入Celery任务
        from .tasks import batch_generate_all_videos_async
        
        # 启动异步任务
        task = batch_generate_all_videos_async.delay(novel_id, chapter_id)
        
        logger.info(f"批量生成全部视频任务已启动: task_id={task.id}")
        
        return JsonResponse({
            'success': True,
            'message': '批量生成全部视频任务已启动',
            'task_id': task.id,
            'novel_id': novel_id,
            'chapter_id': chapter_id,
            'count': narrations.count()
        })
        
    except Chapter.DoesNotExist:
        logger.error(f"章节不存在: chapter_id={chapter_id}")
        return JsonResponse({
            'success': False,
            'error': f'章节不存在: {chapter_id}'
        }, status=404)
        
    except Exception as e:
        logger.error(f"批量生成全部视频失败: {str(e)}")
        return JsonResponse({
            'success': False,
            'error': f'批量生成全部视频失败: {str(e)}'
        }, status=500)


@csrf_exempt
@require_http_methods(["GET"])
def get_chapter_character_images(request, chapter_id):
    """
    获取章节角色图片列表API
    """
    try:
        # 获取章节对象
        chapter = get_object_or_404(Chapter, id=chapter_id)
        novel_id = chapter.novel.id
        
        # 获取文件系统中的章节编号
        chapter_number = get_chapter_number_from_filesystem(novel_id, chapter)
        if chapter_number is None:
            return JsonResponse({
                'success': False,
                'error': f'找不到章节 {chapter.title} 对应的文件系统目录'
            }, status=404)
        
        # 构建角色图片目录路径
        images_dir = os.path.join(
            settings.BASE_DIR.parent,  # 回到项目根目录
            'data',
            f'{novel_id:03d}',
            f'chapter_{chapter_number}',
            'images'
        )
        
        images = []
        
        if os.path.exists(images_dir):
            # 获取图片文件列表
            image_extensions = ['.jpg', '.jpeg', '.png', '.gif', '.bmp', '.webp']
            for filename in sorted(os.listdir(images_dir)):
                if any(filename.lower().endswith(ext) for ext in image_extensions):
                    # 提取角色名称（去掉文件扩展名）
                    character_name = os.path.splitext(filename)[0]
                    
                    # 构建图片URL
                    image_url = f'/api/chapters/{chapter_id}/character-images/{filename}/'
                    images.append({
                        'filename': filename,
                        'character_name': character_name,
                        'url': image_url
                    })
        
        return JsonResponse({
            'success': True,
            'images': images
        })
        
    except Exception as e:
        return JsonResponse({
            'success': False,
            'error': str(e)
        }, status=500)


@csrf_exempt
@require_http_methods(["GET"])
def serve_character_image(request, chapter_id, filename):
    """
    提供章节角色图片文件服务API
    """
    try:
        # 获取章节对象
        chapter = get_object_or_404(Chapter, id=chapter_id)
        novel_id = chapter.novel.id
        
        # 获取文件系统中的章节编号
        chapter_number = get_chapter_number_from_filesystem(novel_id, chapter)
        if chapter_number is None:
            return JsonResponse({
                'success': False,
                'error': f'找不到章节对应的文件系统目录'
            }, status=404)
        
        # 构建图片文件路径
        image_path = os.path.join(
            settings.BASE_DIR.parent,  # 回到项目根目录
            'data',
            f'{novel_id:03d}',
            f'chapter_{chapter_number}',
            'images',
            filename
        )
        
        # 检查文件是否存在
        if not os.path.exists(image_path):
            return JsonResponse({
                'success': False,
                'error': f'图片文件不存在: {filename}'
            }, status=404)
        
        # 确定MIME类型
        import mimetypes
        content_type, _ = mimetypes.guess_type(image_path)
        if content_type is None:
            content_type = 'application/octet-stream'
        
        # 返回图片文件
        with open(image_path, 'rb') as f:
            response = HttpResponse(f.read(), content_type=content_type)
            response['Content-Disposition'] = f'inline; filename="{filename}"'
            return response
        
    except Exception as e:
        return JsonResponse({
            'success': False,
            'error': str(e)
        }, status=500)


@csrf_exempt
@require_http_methods(["POST"])
def generate_character_image(request):
    """
    生成角色图片API
    """
    try:
        # 获取参数
        character_id = request.POST.get('character_id')
        chapter_id = request.POST.get('chapter_id')
        image_style = request.POST.get('image_style', 'realistic')
        image_quality = request.POST.get('image_quality', 'standard')
        image_count = int(request.POST.get('image_count', 1))
        custom_prompt = request.POST.get('custom_prompt', '')
        
        # 验证参数
        if not character_id or not chapter_id:
            return JsonResponse({
                'success': False,
                'error': '缺少必要参数'
            }, status=400)
        
        # 获取角色和章节对象
        try:
            character = Character.objects.get(id=character_id)
            chapter = Chapter.objects.get(id=chapter_id)
        except (Character.DoesNotExist, Chapter.DoesNotExist):
            return JsonResponse({
                'success': False,
                'error': '角色或章节不存在'
            }, status=404)
        
        # 生成任务ID
        import uuid
        task_id = f"char_img_{character_id}_{chapter_id}_{uuid.uuid4().hex[:8]}"
        
        # 创建任务记录
        task = CharacterImageTask.objects.create(
            task_id=task_id,
            character=character,
            chapter=chapter,
            image_style=image_style,
            image_quality=image_quality,
            image_count=image_count,
            custom_prompt=custom_prompt,
            status='pending',
            progress=0,
            log_message='任务已创建，等待处理...'
        )
        
        # 导入并启动异步任务
        from .tasks import generate_character_image_async
        celery_task = generate_character_image_async.delay(
            task_id=task_id,
            character_id=character_id,
            chapter_id=chapter_id,
            image_style=image_style,
            image_quality=image_quality,
            image_count=image_count,
            custom_prompt=custom_prompt
        )
        
        logger.info(f"角色图片生成任务已启动: {task_id}, Celery任务ID: {celery_task.id}")
        
        return JsonResponse({
            'success': True,
            'task_id': task_id,
            'celery_task_id': celery_task.id,
            'message': '任务已提交，正在处理中...'
        })
        
    except Exception as e:
        logger.error(f"生成角色图片失败: {str(e)}")
        return JsonResponse({
            'success': False,
            'error': f'任务提交失败: {str(e)}'
        }, status=500)


@csrf_exempt
@require_http_methods(["POST"])
def batch_generate_character_images(request):
    """
    批量生成角色图片API
    """
    try:
        # 获取参数
        data = json.loads(request.body)
        character_ids = data.get('character_ids', [])
        chapter_id = data.get('chapter_id')
        image_style = data.get('image_style', 'realistic')
        image_quality = data.get('image_quality', 'standard')
        image_count = int(data.get('image_count', 1))
        custom_prompt = data.get('custom_prompt', '')
        
        # 验证参数
        if not character_ids or not chapter_id:
            return JsonResponse({
                'success': False,
                'error': '缺少必要参数'
            }, status=400)
        
        # 获取章节对象
        try:
            chapter = Chapter.objects.get(id=chapter_id)
        except Chapter.DoesNotExist:
            return JsonResponse({
                'success': False,
                'error': '章节不存在'
            }, status=404)
        
        # 验证角色是否存在
        characters = Character.objects.filter(id__in=character_ids)
        if len(characters) != len(character_ids):
            return JsonResponse({
                'success': False,
                'error': '部分角色不存在'
            }, status=404)
        
        # 批量创建任务
        tasks = []
        celery_tasks = []
        
        for character in characters:
            # 生成任务ID
            import uuid
            task_id = f"char_img_{character.id}_{chapter_id}_{uuid.uuid4().hex[:8]}"
            
            # 创建任务记录
            task = CharacterImageTask.objects.create(
                task_id=task_id,
                character=character,
                chapter=chapter,
                image_style=image_style,
                image_quality=image_quality,
                image_count=image_count,
                custom_prompt=custom_prompt,
                status='pending',
                progress=0,
                log_message='任务已创建，等待处理...'
            )
            tasks.append(task)
            
            # 启动异步任务
            from .tasks import generate_character_image_async
            celery_task = generate_character_image_async.delay(
                task_id=task_id,
                character_id=character.id,
                chapter_id=chapter_id,
                image_style=image_style,
                image_quality=image_quality,
                image_count=image_count,
                custom_prompt=custom_prompt
            )
            celery_tasks.append(celery_task.id)
        
        logger.info(f"批量角色图片生成任务已启动: {len(tasks)}个任务")
        
        return JsonResponse({
            'success': True,
            'message': f'已提交{len(tasks)}个任务，正在处理中...',
            'tasks': [{
                'task_id': task.task_id,
                'character_name': task.character.name,
                'character_id': task.character.id
            } for task in tasks],
            'celery_task_ids': celery_tasks
        })
        
    except Exception as e:
        logger.error(f"批量生成角色图片失败: {str(e)}")
        return JsonResponse({
            'success': False,
            'error': f'任务提交失败: {str(e)}'
        }, status=500)


@csrf_exempt
@require_http_methods(["GET"])
def get_character_thumbnail(request, character_id):
    """
    获取角色缩略图API
    优先显示数据库中的image_path，然后从章节images目录查找，最后使用默认图片
    """
    try:
        print(f"DEBUG: get_character_thumbnail called with character_id={character_id}")
        character = Character.objects.get(id=character_id)
        print(f"DEBUG: 找到角色: {character.name}")
        
        # 第一优先级：检查角色数据库中的image_path字段
        if character.image_path and character.image_path.strip():
            print(f"DEBUG: 使用数据库中的image_path: {character.image_path}")
            # 数据库中的image_path格式为 data/001/chapter_001/images/角色名.png
            # 需要转换为正确的URL路径
            if character.image_path.startswith('data/'):
                image_path = f'/{character.image_path}'
            elif not character.image_path.startswith('/'):
                image_path = f'/static/{character.image_path}'
            else:
                image_path = character.image_path
            
            return JsonResponse({
                'success': True,
                'has_image': True,
                'image_path': image_path,
                'filename': os.path.basename(character.image_path),
                'source': 'character_database'
            })
        
        # 获取查询参数中的章节信息
        novel_id = request.GET.get('novel_id')
        chapter_id = request.GET.get('chapter_id')
        print(f"DEBUG: novel_id={novel_id}, chapter_id={chapter_id}")
        
        # 第二优先级：如果提供了章节信息，从章节images目录查找
        if novel_id and chapter_id:
            print(f"DEBUG: 开始从章节目录查找图片")
            # 使用新的工具函数获取章节路径
            from .utils import get_chapter_number_from_filesystem
            
            try:
                chapter = Chapter.objects.get(id=chapter_id)
                chapter_number = get_chapter_number_from_filesystem(int(novel_id), chapter.title)
                if chapter_number:
                    chapter_path = f"data/{novel_id.zfill(3)}/chapter_{chapter_number}"
                    print(f"DEBUG: 章节标题: {chapter.title}, 章节编号: {chapter_number}")
                    print(f"DEBUG: 章节路径: {chapter_path}")
                else:
                    # 如果无法获取章节编号，使用默认路径
                    chapter_path = f"data/{novel_id.zfill(3)}/chapter_{chapter_id.zfill(3)}"
                    print(f"DEBUG: 无法获取章节编号，使用默认路径: {chapter_path}")
            except Chapter.DoesNotExist:
                # 如果章节不存在，使用原来的逻辑
                chapter_path = f"data/{novel_id.zfill(3)}/chapter_{chapter_id.zfill(3)}"
                print(f"DEBUG: 章节不存在，使用默认路径: {chapter_path}")
            image_path = find_character_image_in_chapter(chapter_path, character.name)
            print(f"DEBUG: find_character_image_in_chapter 返回: {image_path}")
            
            if image_path:
                # 转换为相对于static目录的路径
                relative_path = image_path.replace('data/', '/static/data/')
                return JsonResponse({
                    'success': True,
                    'has_image': True,
                    'image_path': relative_path,
                    'filename': os.path.basename(image_path),
                    'source': 'chapter_images'
                })
        
        # 第三优先级：回退到数据库查找最新的成功生成的图片
        latest_task = CharacterImageTask.objects.filter(
            character=character,
            status='success',
            generated_images__isnull=False
        ).exclude(generated_images=[]).order_by('-completed_at').first()
        
        if latest_task and latest_task.generated_images:
            # 返回第一张生成的图片路径
            first_image = latest_task.generated_images[0]
            return JsonResponse({
                'success': True,
                'has_image': True,
                'image_path': first_image.get('path', ''),
                'filename': first_image.get('filename', ''),
                'task_id': latest_task.task_id,
                'source': 'generated_images'
            })
        else:
            # 最后：根据角色性别和年龄段返回不同的默认图片
            default_image_path = get_default_character_image(character)
            return JsonResponse({
                'success': True,
                'has_image': False,
                'default_image': default_image_path,
                'character_info': {
                    'name': character.name,
                    'gender': character.gender,
                    'age_group': character.age_group
                }
            })
            
    except Character.DoesNotExist:
        return JsonResponse({
            'success': False,
            'error': '角色不存在'
        }, status=404)
    except Exception as e:
        logger.error(f"获取角色缩略图失败: {str(e)}")
        return JsonResponse({
            'success': False,
            'error': f'获取缩略图失败: {str(e)}'
        }, status=500)


@csrf_exempt
@require_http_methods(["GET"])
def check_task_status(request):
    """
    检查任务状态API
    """
    try:
        task_id = request.GET.get('task_id')
        
        if not task_id:
            return JsonResponse({
                'success': False,
                'error': '缺少任务ID参数'
            }, status=400)
        
        # 查找任务记录
        try:
            task = CharacterImageTask.objects.get(task_id=task_id)
        except CharacterImageTask.DoesNotExist:
            return JsonResponse({
                'success': False,
                'error': '任务不存在'
            }, status=404)
        
        # 返回任务状态
        response_data = {
            'success': True,
            'task_id': task.task_id,
            'status': task.status,
            'progress': task.progress,
            'log': task.log_message or '',
            'created_at': task.created_at.isoformat(),
            'updated_at': task.updated_at.isoformat()
        }
        
        # 如果任务完成，添加结果信息
        if task.status == 'success':
            response_data['generated_images'] = task.generated_images
            if task.completed_at:
                response_data['completed_at'] = task.completed_at.isoformat()
        
        # 如果任务失败，添加错误信息
        if task.status == 'failed':
            response_data['error'] = task.error_message
        
        return JsonResponse(response_data)
        
    except Exception as e:
        logger.error(f"检查任务状态失败: {str(e)}")
        return JsonResponse({
            'success': False,
            'error': f'检查状态失败: {str(e)}'
        }, status=500)


@csrf_exempt
@require_http_methods(["POST"])
def generate_audio(request, novel_id, chapter_id):
    """
    启动音频生成任务API
    
    Args:
        novel_id: 小说ID
        chapter_id: 章节ID
        
    Returns:
        JsonResponse: 任务启动结果
    """
    try:
        # 验证小说和章节是否存在
        try:
            novel = Novel.objects.get(id=novel_id)
            chapter = Chapter.objects.get(id=chapter_id, novel=novel)
        except Novel.DoesNotExist:
            return JsonResponse({
                'success': False,
                'error': '小说不存在'
            }, status=404)
        except Chapter.DoesNotExist:
            return JsonResponse({
                'success': False,
                'error': '章节不存在'
            }, status=404)
        
        # 检查narration.txt文件是否存在
        # 使用工具函数获取文件系统中的章节编号
        chapter_number = get_chapter_number_from_filesystem(novel_id, chapter)
        if not chapter_number:
            return JsonResponse({
                'success': False,
                'error': f'无法在文件系统中找到章节 {chapter.title} 的目录'
            }, status=400)
        
        data_dir = get_chapter_directory_path(novel_id, chapter_number)
        narration_file = os.path.join(data_dir, 'narration.txt')
        
        if not os.path.exists(narration_file):
            return JsonResponse({
                'success': False,
                'error': '解说文件不存在，请先生成解说内容'
            }, status=400)
        
        # 启动音频生成任务
        task = generate_audio_async.delay(novel_id, chapter_id)
        
        logger.info(f"音频生成任务已启动: 小说ID={novel_id}, 章节ID={chapter_id}, 任务ID={task.id}")
        
        return JsonResponse({
            'success': True,
            'task_id': task.id,
            'message': '音频生成任务已启动',
            'novel_id': novel_id,
            'chapter_id': chapter_id
        })
        
    except Exception as e:
        logger.error(f"启动音频生成任务失败: {str(e)}")
        return JsonResponse({
            'success': False,
            'error': f'启动任务失败: {str(e)}'
        }, status=500)


@csrf_exempt
@require_http_methods(["GET"])
def check_audio_task_status(request, task_id):
    """
    检查音频生成任务状态API
    
    Args:
        task_id: Celery任务ID
        
    Returns:
        JsonResponse: 任务状态信息
    """
    try:
        # 获取Celery任务状态
        task_result = current_app.AsyncResult(task_id)
        
        response_data = {
            'success': True,
            'task_id': task_id,
            'status': task_result.status,
            'ready': task_result.ready()
        }
        
        # 如果任务正在进行中，获取进度信息
        if task_result.status == 'PROGRESS':
            meta = task_result.info or {}
            response_data.update({
                'current': meta.get('current', 0),
                'total': meta.get('total', 100),
                'status_message': meta.get('status', '处理中...')
            })
        
        # 如果任务成功完成，获取结果
        elif task_result.status == 'SUCCESS':
            result = task_result.result or {}
            response_data.update({
                'result': result,
                'message': result.get('message', '音频生成完成'),
                'success_count': result.get('success_count', 0),
                'failed_count': result.get('failed_count', 0),
                'skipped_count': result.get('skipped_count', 0),
                'ass_files_count': result.get('ass_files_count', 0)
            })
        
        # 如果任务失败，获取错误信息
        elif task_result.status == 'FAILURE':
            response_data.update({
                'error': str(task_result.info) if task_result.info else '任务执行失败'
            })
        
        # 如果任务被撤销
        elif task_result.status == 'REVOKED':
            response_data.update({
                'message': '任务已被取消'
            })
        
        return JsonResponse(response_data)
        
    except Exception as e:
        logger.error(f"检查音频任务状态失败: {str(e)}")
        return JsonResponse({
            'success': False,
            'error': f'检查任务状态失败: {str(e)}'
        }, status=500)


@csrf_exempt
@require_http_methods(["GET"])
def get_chapter_audio_files(request, novel_id, chapter_id):
    """
    获取章节的音频文件列表API
    
    Args:
        novel_id: 小说ID
        chapter_id: 章节ID
        
    Returns:
        JsonResponse: 音频文件列表
    """
    try:
        # 验证小说和章节是否存在
        try:
            novel = Novel.objects.get(id=novel_id)
            chapter = Chapter.objects.get(id=chapter_id, novel=novel)
        except Novel.DoesNotExist:
            return JsonResponse({
                'success': False,
                'error': '小说不存在'
            }, status=404)
        except Chapter.DoesNotExist:
            return JsonResponse({
                'success': False,
                'error': '章节不存在'
            }, status=404)
        
        # 使用工具函数获取文件系统中的章节编号
        chapter_number = get_chapter_number_from_filesystem(novel_id, chapter)
        if not chapter_number:
            return JsonResponse({
                'success': False,
                'error': f'无法在文件系统中找到章节 {chapter.title} 的目录'
            }, status=400)
        
        # 使用新的工具函数获取章节目录路径
        from .utils import get_chapter_directory_path
        
        data_dir = get_chapter_directory_path(novel_id, chapter_number)
        
        if not os.path.exists(data_dir):
            return JsonResponse({
                'success': True,
                'audio_files': [],
                'ass_files': [],
                'message': '章节数据目录不存在'
            })
        
        # 查找音频文件和ASS字幕文件
        audio_files = []
        ass_files = []
        
        try:
            for filename in os.listdir(data_dir):
                file_path = os.path.join(data_dir, filename)
                
                # 检查是否为音频文件
                if filename.endswith('.mp3') and 'narration' in filename:
                    # 获取文件大小和修改时间
                    file_stat = os.stat(file_path)
                    file_size = file_stat.st_size
                    modified_time = datetime.fromtimestamp(file_stat.st_mtime).isoformat()
                    
                    # 查找对应的时间戳文件
                    timestamp_file = filename.replace('.mp3', '_timestamps.json')
                    timestamp_path = os.path.join(data_dir, timestamp_file)
                    has_timestamps = os.path.exists(timestamp_path)
                    
                    audio_files.append({
                        'filename': filename,
                        'file_path': file_path,
                        'file_size': file_size,
                        'modified_time': modified_time,
                        'has_timestamps': has_timestamps,
                        'timestamp_file': timestamp_file if has_timestamps else None
                    })
                
                # 检查是否为ASS字幕文件
                elif filename.endswith('.ass') and 'narration' in filename:
                    file_stat = os.stat(file_path)
                    file_size = file_stat.st_size
                    modified_time = datetime.fromtimestamp(file_stat.st_mtime).isoformat()
                    
                    ass_files.append({
                        'filename': filename,
                        'file_path': file_path,
                        'file_size': file_size,
                        'modified_time': modified_time
                    })
        
        except Exception as e:
            logger.error(f"读取目录文件失败: {str(e)}")
        
        # 按文件名排序
        audio_files.sort(key=lambda x: x['filename'])
        ass_files.sort(key=lambda x: x['filename'])
        
        return JsonResponse({
            'success': True,
            'novel_id': novel_id,
            'chapter_id': chapter_id,
            'audio_files': audio_files,
            'ass_files': ass_files,
            'total_audio_files': len(audio_files),
            'total_ass_files': len(ass_files)
        })
        
    except Exception as e:
        logger.error(f"获取章节音频文件失败: {str(e)}")
        return JsonResponse({
            'success': False,
            'error': f'获取音频文件失败: {str(e)}'
        }, status=500)


@csrf_exempt
@require_http_methods(["GET"])
def serve_audio_file(request, novel_id, chapter_id, filename):
    """
    提供音频文件下载/播放服务
    
    Args:
        novel_id: 小说ID
        chapter_id: 章节ID
        filename: 文件名
        
    Returns:
        HttpResponse: 音频文件响应
    """
    try:
        # 验证小说和章节是否存在
        try:
            novel = Novel.objects.get(id=novel_id)
            chapter = Chapter.objects.get(id=chapter_id, novel=novel)
        except (Novel.DoesNotExist, Chapter.DoesNotExist):
            return JsonResponse({
                'success': False,
                'error': '小说或章节不存在'
            }, status=404)
        
        # 构建文件路径
        # 使用工具函数获取文件系统中的实际章节编号
        chapter_number = get_chapter_number_from_filesystem(novel_id, chapter)
        data_dir = get_chapter_directory_path(novel_id, chapter_number)
        file_path = os.path.join(data_dir, filename)
        
        # 安全检查：确保文件在预期目录内
        if not os.path.abspath(file_path).startswith(os.path.abspath(data_dir)):
            return JsonResponse({
                'success': False,
                'error': '非法文件路径'
            }, status=400)
        
        # 检查文件是否存在
        if not os.path.exists(file_path):
            return JsonResponse({
                'success': False,
                'error': '文件不存在'
            }, status=404)
        
        # 检查文件类型
        if not (filename.endswith('.mp3') or filename.endswith('.ass')):
            return JsonResponse({
                'success': False,
                'error': '不支持的文件类型'
            }, status=400)
        
        # 读取文件内容
        with open(file_path, 'rb') as f:
            file_content = f.read()
        
        # 设置响应类型
        if filename.endswith('.mp3'):
            content_type = 'audio/mpeg'
        elif filename.endswith('.ass'):
            content_type = 'text/plain; charset=utf-8'
        else:
            content_type = 'application/octet-stream'
        
        response = HttpResponse(file_content, content_type=content_type)
        response['Content-Disposition'] = f'inline; filename="{filename}"'
        response['Content-Length'] = len(file_content)
        
        return response
        
    except Exception as e:
        logger.error(f"提供音频文件服务失败: {str(e)}")
        return JsonResponse({
            'success': False,
            'error': f'文件服务失败: {str(e)}'
        }, status=500)


@csrf_exempt
@require_http_methods(["GET"])
def get_narration_subtitle(request, narration_id):
    """
    获取解说的字幕内容API
    """
    try:
        # 获取解说对象
        narration = get_object_or_404(Narration, id=narration_id)
        
        # 构建ASS文件路径
        # 根据实际文件系统结构，文件存储在 data/{novel_id}/chapter_xxx/ 目录下
        # 文件名格式: chapter_{chapter_number:03d}_narration_{scene_number:02d}.ass
        novel_id = narration.chapter.novel.id
        chapter = narration.chapter
        scene_number = narration.scene_number
        
        # 获取文件系统中的章节编号
        chapter_number = get_chapter_number_from_filesystem(novel_id, chapter)
        if chapter_number is None:
            return JsonResponse({
                'success': False,
                'error': f'找不到章节 {chapter.title} 对应的文件系统目录'
            }, status=404)
        
        # 尝试解析scene_number中的数字部分
        # 对于"段-分镜"格式，需要转换为连续的图片编号
        try:
            if '-' in scene_number:
                # 解析"段-分镜"格式，如"2-1"
                parts = scene_number.split('-')
                if len(parts) == 2:
                    segment = int(parts[0])
                    shot = int(parts[1])
                    # 计算连续编号：前面段数*3 + 当前分镜编号
                    scene_num = (segment - 1) * 3 + shot
                else:
                    scene_num = int(scene_number.split('-')[-1])
            else:
                scene_num = int(scene_number)
        except (ValueError, IndexError):
            scene_num = 1
        
        # 使用文件系统中的章节编号构建路径
        ass_file_path = os.path.join(
            settings.BASE_DIR.parent,  # 回到项目根目录
            'data',
            f'{novel_id:03d}',
            f'chapter_{chapter_number}',
            f'chapter_{chapter_number}_narration_{scene_num:02d}.ass'
        )
        
        # 检查文件是否存在
        if not os.path.exists(ass_file_path):
            return JsonResponse({
                'success': False,
                'error': f'字幕文件不存在: {ass_file_path}'
            }, status=404)
        
        # 读取ASS文件内容
        try:
            with open(ass_file_path, 'r', encoding='utf-8') as f:
                subtitle_content = f.read()
        except UnicodeDecodeError:
            # 如果UTF-8解码失败，尝试其他编码
            try:
                with open(ass_file_path, 'r', encoding='gbk') as f:
                    subtitle_content = f.read()
            except UnicodeDecodeError:
                with open(ass_file_path, 'r', encoding='latin-1') as f:
                    subtitle_content = f.read()
        
        # 返回字幕内容
        return HttpResponse(
            subtitle_content,
            content_type='text/plain; charset=utf-8'
        )
        
    except Exception as e:
        logger.error(f"获取解说字幕失败: {str(e)}")
        return JsonResponse({
            'success': False,
            'error': f'获取字幕失败: {str(e)}'
        }, status=500)


@csrf_exempt
@require_http_methods(["POST"])
def generate_ass_subtitles(request, novel_id, chapter_id):
    """
    生成ASS字幕文件API
    """
    try:
        # 获取章节信息
        chapter = get_object_or_404(Chapter, id=chapter_id)
        
        # 使用工具函数获取文件系统中的章节编号
        from .utils import get_chapter_number_from_filesystem, get_chapter_directory_path
        
        # 获取文件系统中实际的章节编号
        chapter_number = get_chapter_number_from_filesystem(novel_id, chapter)
        if not chapter_number:
            return JsonResponse({
                'success': False,
                'error': f'无法在文件系统中找到章节 {chapter.title} 的目录'
            }, status=404)
        
        # 构建数据目录路径
        data_dir = get_chapter_directory_path(novel_id, chapter_number)
        
        if not os.path.exists(data_dir):
            return JsonResponse({
                'success': False,
                'error': f'章节数据目录不存在: {data_dir}'
            }, status=404)
        
        # 检查timestamps文件是否存在
        import glob
        timestamp_files = glob.glob(os.path.join(data_dir, '*_timestamps.json'))
        
        if not timestamp_files:
            return JsonResponse({
                'success': False,
                'error': f'未找到timestamps文件，请先生成音频文件'
            }, status=404)
        
        # 执行gen_ass.py脚本
        import subprocess
        project_root = settings.BASE_DIR.parent
        gen_ass_script = os.path.join(project_root, 'gen_ass.py')
        
        if not os.path.exists(gen_ass_script):
            return JsonResponse({
                'success': False,
                'error': f'gen_ass.py脚本不存在: {gen_ass_script}'
            }, status=500)
        
        # 获取章节名称
        chapter_name = os.path.basename(data_dir)
        
        # 获取数据目录的父目录（小说目录）
        novel_data_dir = os.path.dirname(data_dir)
        
        # 运行gen_ass.py脚本
        try:
            result = subprocess.run(
                ['python', gen_ass_script, novel_data_dir, '--chapter', chapter_name],
                cwd=project_root,
                capture_output=True,
                text=True,
                timeout=300  # 5分钟超时
            )
            
            if result.returncode != 0:
                logger.error(f"gen_ass.py执行失败: {result.stderr}")
                return JsonResponse({
                    'success': False,
                    'error': f'ASS文件生成失败: {result.stderr}'
                }, status=500)
            
            # 检查生成的ASS文件
            ass_files = glob.glob(os.path.join(data_dir, '*.ass'))
            
            if not ass_files:
                return JsonResponse({
                    'success': False,
                    'error': 'ASS文件生成失败，未找到生成的文件'
                }, status=500)
            
            # 更新数据库记录（可选：记录ASS文件生成时间）
            from django.utils import timezone
            chapter.updated_at = timezone.now()
            chapter.save()
            
            logger.info(f"成功生成ASS字幕文件: 小说ID={novel_id}, 章节ID={chapter_id}, 生成文件数={len(ass_files)}")
            
            return JsonResponse({
                'success': True,
                'message': f'成功生成 {len(ass_files)} 个ASS字幕文件',
                'files_generated': len(ass_files),
                'chapter_directory': data_dir,
                'output': result.stdout
            })
            
        except subprocess.TimeoutExpired:
            return JsonResponse({
                'success': False,
                'error': 'ASS文件生成超时（超过5分钟）'
            }, status=500)
        except Exception as e:
            logger.error(f"执行gen_ass.py脚本失败: {str(e)}")
            return JsonResponse({
                'success': False,
                'error': f'脚本执行失败: {str(e)}'
            }, status=500)
        
    except Exception as e:
        logger.error(f"生成ASS字幕失败: {str(e)}")
        return JsonResponse({
            'success': False,
            'error': f'生成ASS字幕失败: {str(e)}'
        }, status=500)


@csrf_exempt
@require_http_methods(["GET"])
def get_narration_images_status(request, narration_id):
    """
    检查解说分镜图片状态API
    """
    try:
        # 获取解说对象
        narration = get_object_or_404(Narration, id=narration_id)
        
        # 构建图片目录路径
        novel_id = narration.chapter.novel.id
        chapter = narration.chapter
        scene_number = narration.scene_number
        
        # 获取文件系统中的章节编号
        chapter_number = get_chapter_number_from_filesystem(novel_id, chapter)
        if chapter_number is None:
            return JsonResponse({
                'success': False,
                'error': f'找不到章节 {chapter.title} 对应的文件系统目录'
            }, status=404)
        
        # 尝试解析scene_number中的数字部分
        # 对于"段-分镜"格式，需要转换为连续的图片编号
        try:
            if '-' in scene_number:
                # 解析"段-分镜"格式，如"2-1"
                parts = scene_number.split('-')
                if len(parts) == 2:
                    segment = int(parts[0])
                    shot = int(parts[1])
                    # 计算连续编号：前面段数*3 + 当前分镜编号
                    scene_num = (segment - 1) * 3 + shot
                else:
                    scene_num = int(scene_number.split('-')[-1])
            else:
                scene_num = int(scene_number)
            print(f"DEBUG: get_narration_images - 原始scene_number: {scene_number}, 解析后: {scene_num}")
        except (ValueError, IndexError):
            scene_num = 1
            print(f"DEBUG: get_narration_images - scene_number解析失败，使用默认值: {scene_num}")
        
        # 构建章节目录路径
        chapter_dir = os.path.join(
            settings.BASE_DIR.parent,  # 回到项目根目录
            'data',
            f'{novel_id:03d}',
            f'chapter_{chapter_number}'
        )
        
        # 检查章节目录是否存在并统计分镜图片数量
        has_images = False
        image_count = 0
        
        if os.path.exists(chapter_dir):
            # 构建分镜图片文件名模式：chapter_XXX_image_YY.jpeg（修复：去掉末尾下划线）
            image_pattern_base = f'chapter_{chapter_number}_image_{scene_num:02d}'
            image_extensions = ['.jpg', '.jpeg', '.png', '.gif', '.bmp', '.webp']
            
            for filename in os.listdir(chapter_dir):
                # 检查文件名是否匹配分镜图片模式
                # 支持两种格式：chapter_XXX_image_YY.ext 和 chapter_XXX_image_YY_N.ext
                if filename.startswith(image_pattern_base):
                    # 检查是否是有效的图片文件
                    if any(filename.lower().endswith(ext) for ext in image_extensions):
                        # 验证文件名格式：确保是精确匹配或带序号的格式
                        name_without_ext = filename.rsplit('.', 1)[0]
                        if (name_without_ext == image_pattern_base or 
                            name_without_ext.startswith(image_pattern_base + '_')):
                            image_count += 1
            
            has_images = image_count > 0
        
        return JsonResponse({
            'success': True,
            'has_images': has_images,
            'image_count': image_count,
            'chapter_dir': chapter_dir
        })
        
    except Exception as e:
        return JsonResponse({
            'success': False,
            'error': str(e)
        }, status=500)


@csrf_exempt
@require_http_methods(["POST"])
def generate_narration_images(request, narration_id):
    """
    生成解说分镜图片API
    """
    try:
        # 获取解说对象
        narration = get_object_or_404(Narration, id=narration_id)
        
        # 导入异步任务
        from .tasks import generate_narration_images_async
        
        # 启动异步任务
        task = generate_narration_images_async.delay(narration_id)
        
        return JsonResponse({
            'success': True,
            'message': f'正在为解说 {narration.scene_number} 生成分镜图片...',
            'task_id': task.id
        })
        
    except Exception as e:
        return JsonResponse({
            'success': False,
            'error': str(e)
        }, status=500)


@csrf_exempt
@require_http_methods(["GET"])
def get_narration_images(request, narration_id):
    """
    获取解说分镜图片列表API
    """
    try:
        # 获取解说对象
        narration = get_object_or_404(Narration, id=narration_id)
        
        # 构建图片目录路径
        novel_id = narration.chapter.novel.id
        chapter = narration.chapter
        scene_number = narration.scene_number
        
        # 获取文件系统中的章节编号
        chapter_number = get_chapter_number_from_filesystem(novel_id, chapter)
        if chapter_number is None:
            return JsonResponse({
                'success': False,
                'error': f'找不到章节 {chapter.title} 对应的文件系统目录'
            }, status=404)
        
        # 尝试解析scene_number中的数字部分
        # 对于"段-分镜"格式，需要转换为连续的图片编号
        try:
            if '-' in scene_number:
                # 解析"段-分镜"格式，如"2-1"
                parts = scene_number.split('-')
                if len(parts) == 2:
                    segment = int(parts[0])
                    shot = int(parts[1])
                    # 计算连续编号：前面段数*3 + 当前分镜编号
                    scene_num = (segment - 1) * 3 + shot
                else:
                    scene_num = int(scene_number.split('-')[-1])
            else:
                scene_num = int(scene_number)
        except (ValueError, IndexError):
            scene_num = 1
        
        # 构建章节目录路径
        chapter_dir = os.path.join(
            settings.BASE_DIR.parent,  # 回到项目根目录
            'data',
            f'{novel_id:03d}',
            f'chapter_{chapter_number}'
        )
        
        images = []
        
        print(f"DEBUG: get_narration_images - 章节目录: {chapter_dir}")
        print(f"DEBUG: get_narration_images - 目录是否存在: {os.path.exists(chapter_dir)}")
        
        if os.path.exists(chapter_dir):
            # 构建分镜图片文件名模式：chapter_XXX_image_YY（重命名后的新格式）
            image_pattern_base = f'chapter_{chapter_number}_image_{scene_num:02d}'
            image_extensions = ['.jpg', '.jpeg', '.png', '.gif', '.bmp', '.webp']
            
            print(f"DEBUG: get_narration_images - 查找图片模式: {image_pattern_base}")
            
            all_files = sorted(os.listdir(chapter_dir))
            print(f"DEBUG: get_narration_images - 目录中的所有文件: {all_files[:10]}...")  # 只显示前10个文件
            
            for filename in all_files:
                # 检查文件名是否匹配分镜图片模式
                # 新格式：chapter_001_image_02.jpeg（重命名后的格式）
                if filename.startswith(image_pattern_base):
                    # 检查是否是有效的图片文件
                    if any(filename.lower().endswith(ext) for ext in image_extensions):
                        # 验证文件名格式：确保是精确匹配 chapter_XXX_image_YY.ext
                        name_without_ext = filename.rsplit('.', 1)[0]
                        if name_without_ext == image_pattern_base:
                            print(f"DEBUG: get_narration_images - 找到匹配文件: {filename}")
                            # 构建图片URL
                            image_url = f'/video/api/novels/{novel_id}/chapters/{chapter.id}/narrations/{narration_id}/images/{filename}/'
                            images.append({
                                'filename': filename,
                                'url': image_url
                            })
        else:
            print(f"DEBUG: get_narration_images - 章节目录不存在: {chapter_dir}")
        
        return JsonResponse({
            'success': True,
            'images': images
        })
        
    except Exception as e:
        return JsonResponse({
            'success': False,
            'error': str(e)
        }, status=500)


@csrf_exempt
@require_http_methods(["GET"])
def serve_narration_image(request, novel_id, chapter_id, narration_id, filename):
    """
    提供解说分镜图片文件服务API
    """
    try:
        # 获取解说对象
        narration = get_object_or_404(Narration, id=narration_id, chapter_id=chapter_id, chapter__novel_id=novel_id)
        
        # 获取文件系统中的章节编号
        chapter_number = get_chapter_number_from_filesystem(novel_id, narration.chapter)
        if chapter_number is None:
            return JsonResponse({
                'success': False,
                'error': f'找不到章节对应的文件系统目录'
            }, status=404)
        
        # 尝试解析scene_number中的数字部分
        scene_number = narration.scene_number
        try:
            if '-' in scene_number:
                # 解析"段-分镜"格式，转换为连续编号
                parts = scene_number.split('-')
                segment = int(parts[0])
                scene = int(parts[1])
                # 计算连续编号：(段-1)*3 + 分镜
                scene_num = (segment - 1) * 3 + scene
            else:
                scene_num = int(scene_number)
        except (ValueError, IndexError):
            scene_num = 1
        
        # 构建图片文件路径
        image_path = os.path.join(
            settings.BASE_DIR.parent,  # 回到项目根目录
            'data',
            f'{novel_id:03d}',
            f'chapter_{chapter_number}',
            filename
        )
        
        # 检查文件是否存在
        if not os.path.exists(image_path):
            return JsonResponse({
                'success': False,
                'error': f'图片文件不存在: {filename}'
            }, status=404)
        
        # 确定MIME类型
        import mimetypes
        content_type, _ = mimetypes.guess_type(image_path)
        if content_type is None:
            content_type = 'application/octet-stream'
        
        # 返回图片文件
        with open(image_path, 'rb') as f:
            response = HttpResponse(f.read(), content_type=content_type)
            response['Content-Disposition'] = f'inline; filename="{filename}"'
            return response
        
    except Exception as e:
        return JsonResponse({
            'success': False,
            'error': str(e)
        }, status=500)

@login_required
@require_http_methods(["POST"])
def novel_gen_script(request, novel_id):
    """
    生成小说脚本（解说文案）
    对应脚本：gen_script_v2.py
    """
    try:
        novel = get_object_or_404(Novel, pk=novel_id)
        
        # 先更新状态为"处理中"
        novel.task_status = 'generating_script'
        novel.task_message = '正在生成解说文案...'
        novel.save()
        
        # 调用Celery异步任务
        from .tasks import gen_script_task
        task = gen_script_task.delay(novel_id)
        
        # 保存任务ID
        novel.current_task_id = task.id
        novel.save()
        
        return JsonResponse({
            'success': True,
            'message': f'开始生成脚本，任务ID: {task.id}',
            'task_id': task.id
        })
    except Exception as e:
        logger.error(f"生成脚本失败: {str(e)}")
        return JsonResponse({
            'success': False,
            'message': f'生成脚本失败: {str(e)}'
        }, status=500)


@login_required
@require_http_methods(["POST"])
def novel_validate_script(request, novel_id):
    """
    校验小说脚本（解说文案）
    对应脚本：validate_narration.py --auto-fix
    """
    try:
        novel = get_object_or_404(Novel, pk=novel_id)
        
        # 先更新状态为"处理中"
        novel.task_status = 'validating_script'
        novel.task_message = '正在校验解说文案...'
        novel.save()
        
        # 调用Celery异步任务
        from .tasks import validate_script_task
        task = validate_script_task.delay(novel_id)
        
        # 保存任务ID
        novel.current_task_id = task.id
        novel.save()
        
        return JsonResponse({
            'success': True,
            'message': f'开始校验脚本，任务ID: {task.id}',
            'task_id': task.id
        })
    except Exception as e:
        logger.error(f"校验脚本失败: {str(e)}")
        return JsonResponse({
            'success': False,
            'message': f'校验脚本失败: {str(e)}'
        }, status=500)


@login_required
@require_http_methods(["POST"])
def novel_gen_audio(request, novel_id):
    """
    生成小说旁白音频
    对应脚本：gen_audio.py
    """
    try:
        novel = get_object_or_404(Novel, pk=novel_id)
        
        # 先更新状态为"处理中"
        novel.task_status = 'generating_audio'
        novel.task_message = '正在生成旁白音频...'
        novel.save()
        
        # 调用Celery异步任务
        from .tasks import gen_audio_task
        task = gen_audio_task.delay(novel_id)
        
        # 保存任务ID
        novel.current_task_id = task.id
        novel.save()
        
        return JsonResponse({
            'success': True,
            'message': f'开始生成旁白，任务ID: {task.id}',
            'task_id': task.id
        })
    except Exception as e:
        logger.error(f"生成旁白失败: {str(e)}")
        return JsonResponse({
            'success': False,
            'message': f'生成旁白失败: {str(e)}'
        }, status=500)


@login_required
@require_http_methods(["POST"])
def novel_gen_ass(request, novel_id):
    """
    生成小说字幕时间戳文件
    对应脚本：gen_ass.py
    """
    try:
        novel = get_object_or_404(Novel, pk=novel_id)
        
        # 先更新状态为"处理中"
        novel.task_status = 'generating_ass'
        novel.task_message = '正在生成字幕文件...'
        novel.save()
        
        # 调用Celery异步任务
        from .tasks import gen_ass_task
        task = gen_ass_task.delay(novel_id)
        
        # 保存任务ID
        novel.current_task_id = task.id
        novel.save()
        
        return JsonResponse({
            'success': True,
            'message': f'开始生成字幕，任务ID: {task.id}',
            'task_id': task.id
        })
    except Exception as e:
        logger.error(f"生成字幕失败: {str(e)}")
        return JsonResponse({
            'success': False,
            'message': f'生成字幕失败: {str(e)}'
        }, status=500)


@login_required
@require_http_methods(["POST"])
def novel_gen_image(request, novel_id):
    """
    生成小说分镜图片
    对应脚本：gen_image_async_v4.py
    """
    try:
        novel = get_object_or_404(Novel, pk=novel_id)
        
        # 先更新状态为"处理中"
        novel.task_status = 'generating_image'
        novel.task_message = '正在生成分镜图片...'
        novel.save()
        
        # 调用Celery异步任务
        from .tasks import gen_image_task
        task = gen_image_task.delay(novel_id)
        
        # 保存任务ID
        novel.current_task_id = task.id
        novel.save()
        
        return JsonResponse({
            'success': True,
            'message': f'开始生成图片，任务ID: {task.id}',
            'task_id': task.id
        })
    except Exception as e:
        logger.error(f"生成图片失败: {str(e)}")
        return JsonResponse({
            'success': False,
            'message': f'生成图片失败: {str(e)}'
        }, status=500)


@csrf_exempt
@require_http_methods(["POST"])
def regenerate_single_image(request):
    """
    重新生成单张图片的API接口
    """
    # 检查用户登录状态
    if not request.user.is_authenticated:
        return JsonResponse({
            'success': False,
            'message': '未登录，请先登录'
        }, status=401)
    
    try:
        import json
        
        # 记录请求信息
        logger.info(f"收到重新生成图片请求，用户: {request.user.username}")
        logger.info(f"Content-Type: {request.content_type}")
        logger.info(f"Request body length: {len(request.body)}")
        
        data = json.loads(request.body)
        
        novel_id = data.get('novel_id')
        chapter_title = data.get('chapter_title')
        scene_number = data.get('scene_number')
        custom_prompt = data.get('custom_prompt')  # 可选的自定义prompt
        
        if not all([novel_id, chapter_title, scene_number]):
            return JsonResponse({
                'success': False,
                'message': '缺少必要参数'
            }, status=400)
        
        # 调用Celery任务
        from .tasks import regenerate_single_image_task
        task = regenerate_single_image_task.delay(novel_id, chapter_title, scene_number, custom_prompt)
        
        if custom_prompt:
            logger.info(f"重新生成图片任务已提交（使用自定义Prompt）: novel_id={novel_id}, chapter={chapter_title}, scene={scene_number}, task_id={task.id}")
        else:
            logger.info(f"重新生成图片任务已提交: novel_id={novel_id}, chapter={chapter_title}, scene={scene_number}, task_id={task.id}")
        
        return JsonResponse({
            'success': True,
            'task_id': task.id,
            'message': f'场景 {scene_number} 图片重新生成任务已提交'
        })
        
    except Exception as e:
        logger.error(f"重新生成图片失败: {str(e)}", exc_info=True)
        return JsonResponse({
            'success': False,
            'message': f'提交失败: {str(e)}'
        }, status=500)


@csrf_exempt
@require_http_methods(["POST"])
def submit_chapter_for_review(request, chapter_id):
    """
    提交章节审核的API接口
    """
    # 检查用户登录状态
    if not request.user.is_authenticated:
        return JsonResponse({
            'success': False,
            'message': '未登录，请先登录'
        }, status=401)
    
    try:
        from .models import Chapter
        from django.utils import timezone
        
        # 获取章节
        chapter = Chapter.objects.get(pk=chapter_id)
        
        # 更新审核状态为审核中
        chapter.review_status = 'reviewing'
        chapter.reviewed_by = None
        chapter.reviewed_at = None
        chapter.review_reason = None
        chapter.save()
        
        logger.info(f"章节 {chapter.title} (ID:{chapter_id}) 已提交审核，操作人: {request.user.username}")
        
        return JsonResponse({
            'success': True,
            'message': f'章节 {chapter.title} 已提交审核'
        })
        
    except Chapter.DoesNotExist:
        return JsonResponse({
            'success': False,
            'message': '章节不存在'
        }, status=404)
    except Exception as e:
        logger.error(f"提交章节审核失败: {str(e)}", exc_info=True)
        return JsonResponse({
            'success': False,
            'message': f'提交失败: {str(e)}'
        }, status=500)


@csrf_exempt
@require_http_methods(["POST"])
def generate_video(request):
    """
    生成章节视频的API接口
    """
    # 检查用户登录状态
    if not request.user.is_authenticated:
        return JsonResponse({
            'success': False,
            'message': '未登录，请先登录'
        }, status=401)
    
    try:
        import json
        
        # 记录请求信息
        logger.info(f"收到生成视频请求，用户: {request.user.username}")
        
        data = json.loads(request.body)
        
        novel_id = data.get('novel_id')
        chapter_title = data.get('chapter_title')
        chapter_id = data.get('chapter_id')
        
        if not all([novel_id, chapter_title, chapter_id]):
            return JsonResponse({
                'success': False,
                'message': '缺少必要参数'
            }, status=400)
        
        # 调用Celery任务
        from .tasks import generate_chapter_video_task
        task = generate_chapter_video_task.delay(novel_id, chapter_title, chapter_id)
        
        logger.info(f"生成视频任务已提交: novel_id={novel_id}, chapter={chapter_title}, chapter_id={chapter_id}, task_id={task.id}")
        
        return JsonResponse({
            'success': True,
            'task_id': task.id,
            'message': f'章节 {chapter_title} 视频生成任务已提交'
        })
        
    except Exception as e:
        logger.error(f"生成视频失败: {str(e)}", exc_info=True)
        return JsonResponse({
            'success': False,
            'message': f'提交失败: {str(e)}'
        }, status=500)


@login_required
def serve_data_file(request, file_path):
    """
    提供data目录下文件的访问服务
    用于访问音频、字幕、图片等文件
    """
    from django.http import FileResponse, Http404
    from django.conf import settings
    import os
    import mimetypes
    
    logger.info(f"serve_data_file 请求路径: {file_path}")
    
    # 构建完整文件路径
    project_root = settings.BASE_DIR.parent
    full_path = project_root / file_path
    
    logger.info(f"完整文件路径: {full_path}")
    
    # 安全检查：确保文件在data目录下
    if not str(full_path).startswith(str(project_root / 'data')):
        logger.error(f"安全检查失败: 文件不在data目录下")
        raise Http404("File not found")
    
    # 检查文件是否存在
    if not os.path.exists(full_path):
        logger.error(f"文件不存在: {full_path}")
        raise Http404("File not found")
    
    # 获取文件MIME类型
    content_type, _ = mimetypes.guess_type(str(full_path))
    if content_type is None:
        content_type = 'application/octet-stream'
    
    logger.info(f"文件类型: {content_type}")
    
    # 返回文件
    response = FileResponse(open(full_path, 'rb'), content_type=content_type)
    response['Content-Disposition'] = f'inline; filename="{os.path.basename(full_path)}"'
    return response
