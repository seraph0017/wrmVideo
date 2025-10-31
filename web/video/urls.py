from django.urls import path
from django.views.generic.base import RedirectView

from . import views
from . import log_views

app_name = 'video'

urlpatterns = [
    path("", RedirectView.as_view(url='dashboard/', permanent=True), name="index"),
    path("login/", views.user_login, name="login"),
    path("logout/", views.user_logout, name="logout"),
    path("dashboard/", views.dashboard, name="dashboard"),
    path("test-modal/", views.test_modal, name="test_modal"),
    
    # 小说URL
    path("novels/", views.NovelListView.as_view(), name="novel_list"),
    path("novels/<int:pk>/", views.NovelDetailView.as_view(), name="novel_detail"),
    path("novels/create/", views.NovelCreateView.as_view(), name="novel_create"),
    path("novels/<int:pk>/edit/", views.NovelUpdateView.as_view(), name="novel_update"),
    path("novels/<int:pk>/delete/", views.NovelDeleteView.as_view(), name="novel_delete"),
    path("novels/<int:pk>/ai-process/", views.novel_ai_process, name="novel_ai_process"),
    path("novels/<int:pk>/ai-generate/", views.novel_ai_generate, name="novel_ai_generate"),
    path("novels/<int:pk>/ai-validate/", views.novel_ai_validate, name="novel_ai_validate"),
    path("novels/<int:pk>/generate-script/", views.novel_generate_script, name="novel_generate_script"),
    path("novels/<int:pk>/task-status/", views.novel_task_status, name="novel_task_status"),
    path("novels/<int:pk>/validate-narration/", views.novel_validate_narration, name="novel_validate_narration"),
    path("novels/<int:pk>/ai-validation/", views.novel_ai_validation, name="novel_ai_validation"),
    path("novels/<int:pk>/validation-status/<str:task_id>/", views.validation_status, name="validation_status"),
    path("novels/<int:pk>/task-log/", views.get_task_log, name="get_task_log"),
    path("novels/<int:pk>/stop-task/", views.stop_task, name="stop_task"),
    
    # 章节URL
    path("chapters/", views.ChapterListView.as_view(), name="chapter_list"),
    path("chapters/<int:pk>/", views.ChapterDetailView.as_view(), name="chapter_detail"),
    path("chapters/create/", views.ChapterCreateView.as_view(), name="chapter_create"),
    path("chapters/<int:pk>/edit/", views.ChapterUpdateView.as_view(), name="chapter_update"),
    path("chapters/<int:pk>/delete/", views.ChapterDeleteView.as_view(), name="chapter_delete"),
    
    # 角色URL
    path("characters/", views.CharacterListView.as_view(), name="character_list"),
    path("characters/<int:pk>/", views.CharacterDetailView.as_view(), name="character_detail"),
    path("characters/create/", views.CharacterCreateView.as_view(), name="character_create"),
    path("characters/<int:pk>/edit/", views.CharacterUpdateView.as_view(), name="character_update"),
    path("characters/<int:pk>/delete/", views.CharacterDeleteView.as_view(), name="character_delete"),
    
    # 解说URL
    path("narrations/", views.NarrationListView.as_view(), name="narration_list"),
    path("narrations/<int:pk>/", views.NarrationDetailView.as_view(), name="narration_detail"),
    path("narrations/create/", views.NarrationCreateView.as_view(), name="narration_create"),
    path("narrations/<int:pk>/edit/", views.NarrationUpdateView.as_view(), name="narration_update"),
    path("narrations/<int:pk>/delete/", views.NarrationDeleteView.as_view(), name="narration_delete"),
    
    # API路由
    path('monitor/', views.task_monitor, name='task_monitor'),
    path('api/task/<str:task_id>/', views.task_status_api, name='task_status_api'),
    path('api/tasks/', views.task_list_api, name='task_list_api'),
    path('api/task/<str:task_id>/revoke/', views.task_revoke_api, name='task_revoke_api'),
    
    # 角色图片生成API
    path('api/generate-character-image/', views.generate_character_image, name='generate_character_image'),
    path('api/batch_generate_character_images/', views.batch_generate_character_images, name='batch_generate_character_images'),
    path('api/character/<int:character_id>/thumbnail/', views.get_character_thumbnail, name='get_character_thumbnail'),
    path('api/check-task-status/', views.check_task_status, name='check_task_status'),
    
    # 音频生成API
    path('api/novels/<int:novel_id>/chapters/<int:chapter_id>/generate-audio/', views.generate_audio, name='generate_audio'),
    path('api/audio-task/<str:task_id>/status/', views.check_audio_task_status, name='check_audio_task_status'),
    path('api/novels/<int:novel_id>/chapters/<int:chapter_id>/audio-files/', views.get_chapter_audio_files, name='get_chapter_audio_files'),
    path('api/novels/<int:novel_id>/chapters/<int:chapter_id>/files/<str:filename>/', views.serve_audio_file, name='serve_audio_file'),
    
    # 解说字幕API
    path('api/narrations/<int:narration_id>/subtitle/', views.get_narration_subtitle, name='get_narration_subtitle'),
    path('api/novels/<int:novel_id>/chapters/<int:chapter_id>/generate-ass/', views.generate_ass_subtitles, name='generate_ass_subtitles'),
    
    # 解说分镜图片API
    path('api/narrations/<int:narration_id>/images/status/', views.get_narration_images_status, name='get_narration_images_status'),
    path('api/narrations/<int:narration_id>/generate-images/', views.generate_narration_images, name='generate_narration_images'),
    path('api/narrations/<int:narration_id>/images/', views.get_narration_images, name='get_narration_images'),
    path('api/novels/<int:novel_id>/chapters/<int:chapter_id>/narrations/<int:narration_id>/images/<str:filename>/', views.serve_narration_image, name='serve_narration_image'),
    path('api/novels/<int:novel_id>/chapters/<int:chapter_id>/narrations/<int:narration_id>/regenerate-image/', views.regenerate_narration_image, name='regenerate_narration_image'),
    
    # 章节角色图片API
    path('api/chapters/<int:chapter_id>/character-images/', views.get_chapter_character_images, name='get_chapter_character_images'),
    path('api/chapters/<int:chapter_id>/character-images/<str:filename>/', views.serve_character_image, name='serve_character_image'),
    
    # 批量生成分镜图片
    path('api/chapters/<int:chapter_id>/batch-generate-images/', views.batch_generate_images, name='batch_generate_images'),
    path('api/chapters/<int:chapter_id>/batch-generate-images-v4/', views.batch_generate_images_v4, name='batch_generate_images_v4'),
    path('api/chapters/<int:chapter_id>/batch-generate-chapter-images/', views.batch_generate_chapter_images, name='batch_generate_chapter_images'),
    path('api/chapters/<int:chapter_id>/batch-image-status/', views.get_chapter_batch_image_status, name='get_chapter_batch_image_status'),
    path('api/chapters/<int:chapter_id>/batch-generate-audio/', views.batch_generate_audio, name='batch_generate_audio'),

    path('api/chapters/<int:chapter_id>/validate-narration-images-llm/', views.validate_narration_images_llm, name='validate_narration_images_llm'),
    path('api/chapters/<int:chapter_id>/generate-first-video/', views.generate_first_video, name='generate_first_video'),
    path('api/chapters/<int:chapter_id>/batch-generate-videos/', views.batch_generate_videos, name='batch_generate_videos'),
    path('api/chapters/<int:chapter_id>/batch-generate-all-videos/', views.batch_generate_all_videos, name='batch_generate_all_videos'),
    path('api/narrations/<int:narration_id>/get-image-result/', views.get_image_generation_result, name='get_image_generation_result'),
    
    # 任务日志
    path('task-logs/', views.task_logs_view, name='task_logs_view'),
    path('api/task/<str:task_id>/logs/', log_views.get_task_logs, name='task_logs_api'),
    path('api/task/<str:task_id>/logs/stream/', log_views.stream_task_logs, name='task_logs_stream'),
    path('api/tasks/active/', log_views.get_all_active_tasks, name='active_tasks_api'),
    
    # 视频预览URL
    path('api/chapters/<int:chapter_id>/video/', views.serve_chapter_video, name='serve_chapter_video'),
]