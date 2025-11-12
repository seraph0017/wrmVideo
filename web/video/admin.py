from django.contrib import admin
from .models import Novel, Chapter, Character, Narration, AudioGenerationTask

# Register your models here.

@admin.register(Novel)
class NovelAdmin(admin.ModelAdmin):
    list_display = ('id', 'name', 'word_count', 'type')
    search_fields = ('name', 'type')
    list_filter = ('type',)

@admin.register(Chapter)
class ChapterAdmin(admin.ModelAdmin):
    list_display = ('id', 'title', 'novel', 'word_count', 'format', 'review_status', 'reviewed_by', 'reviewed_at')
    search_fields = ('title', 'novel__name')
    list_filter = ('novel', 'format', 'review_status')
    readonly_fields = ('reviewed_by', 'reviewed_at')
    
    fieldsets = (
        ('基本信息', {
            'fields': ('title', 'novel', 'word_count', 'format', 'video_path')
        }),
        ('统计信息', {
            'fields': ('script_count', 'audio_count', 'subtitle_count', 'image_count')
        }),
        ('审核信息', {
            'fields': ('review_status', 'review_reason', 'reviewed_by', 'reviewed_at'),
            'classes': ('collapse',)
        }),
        ('批量图片生成', {
            'fields': ('batch_image_status', 'batch_image_task_id', 'batch_image_progress', 
                      'batch_image_message', 'batch_image_error', 'batch_image_started_at', 
                      'batch_image_completed_at'),
            'classes': ('collapse',)
        }),
    )

@admin.register(Character)
class CharacterAdmin(admin.ModelAdmin):
    list_display = ('id', 'name', 'gender', 'age_group')
    search_fields = ('name',)
    list_filter = ('gender', 'age_group')
    # filter_horizontal = ('chapters',)  # 不再需要，因为现在是ForeignKey关系

@admin.register(Narration)
class NarrationAdmin(admin.ModelAdmin):
    list_display = ('id', 'scene_number', 'chapter', 'featured_character')
    search_fields = ('scene_number', 'featured_character', 'chapter__title')
    list_filter = ('chapter',)
    readonly_fields = ('tts_response', 'subtitle_content')

@admin.register(AudioGenerationTask)
class AudioGenerationTaskAdmin(admin.ModelAdmin):
    list_display = ('id', 'task_id', 'chapter', 'status', 'progress', 'success_count', 'failed_count', 'created_at', 'completed_at')
    search_fields = ('task_id', 'chapter__title', 'chapter__novel__name')
    list_filter = ('status', 'created_at', 'completed_at')
    readonly_fields = ('task_id', 'created_at', 'updated_at', 'started_at', 'completed_at', 'generated_audio_files', 'generated_timestamp_files', 'generated_ass_files')
    fieldsets = (
        ('基本信息', {
            'fields': ('task_id', 'chapter', 'status')
        }),
        ('进度信息', {
            'fields': ('progress', 'total_segments', 'success_count', 'failed_count', 'skipped_count')
        }),
        ('日志信息', {
            'fields': ('log_message', 'error_message')
        }),
        ('生成文件', {
            'fields': ('generated_audio_files', 'generated_timestamp_files', 'generated_ass_files'),
            'classes': ('collapse',)
        }),
        ('时间信息', {
            'fields': ('created_at', 'updated_at', 'started_at', 'completed_at'),
            'classes': ('collapse',)
        })
    )
