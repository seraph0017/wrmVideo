from django.db import models

# Create your models here.

class Novel(models.Model):
    """
    小说模型
    """
    TASK_STATUS_CHOICES = (
        ('idle', '空闲'),
        ('generating_script', '生成解说文案中'),
        ('script_completed', '解说文案已完成'),
        ('script_failed', '解说文案生成失败'),
        ('validating_script', '校验解说文案中'),
        ('validation_completed', '解说文案校验完成'),
        ('validation_failed', '解说文案校验失败'),
    )
    
    id = models.AutoField(primary_key=True, verbose_name='ID')
    name = models.CharField(max_length=100, verbose_name='名称')
    word_count = models.IntegerField(default=0, verbose_name='字数')
    type = models.CharField(max_length=50, blank=True, null=True, verbose_name='类型')
    # 文件上传相关字段
    original_file = models.FileField(upload_to='novels/', blank=True, null=True, verbose_name='原始文件')
    content = models.TextField(blank=True, null=True, verbose_name='小说内容')
    upload_date = models.DateTimeField(auto_now_add=True, verbose_name='上传时间')
    last_modified = models.DateTimeField(auto_now=True, verbose_name='最后修改时间')
    
    # 任务状态相关字段
    task_status = models.CharField(max_length=50, choices=TASK_STATUS_CHOICES, default='idle', verbose_name='任务状态')
    current_task_id = models.CharField(max_length=100, blank=True, null=True, verbose_name='当前任务ID')
    task_message = models.TextField(blank=True, null=True, verbose_name='任务消息')
    task_updated_at = models.DateTimeField(auto_now=True, verbose_name='任务状态更新时间')
    
    def __str__(self):
        return self.name
    
    class Meta:
        verbose_name = '小说'
        verbose_name_plural = '小说'


class Chapter(models.Model):
    """
    章节模型
    """
    id = models.AutoField(primary_key=True, verbose_name='ID')
    title = models.CharField(max_length=200, verbose_name='章节名')
    word_count = models.IntegerField(default=0, verbose_name='字数')
    format = models.CharField(max_length=50, verbose_name='章节风格')
    novel = models.ForeignKey(Novel, on_delete=models.CASCADE, related_name='chapters', verbose_name='对应小说')
    video_path = models.CharField(max_length=255, blank=True, null=True, verbose_name='视频路径')
    
    def __str__(self):
        return f"{self.novel.name} - {self.title}"
    
    class Meta:
        verbose_name = '章节'
        verbose_name_plural = '章节'


class Character(models.Model):
    """
    出镜人物模型
    """
    GENDER_CHOICES = (
        ('男', '男'),
        ('女', '女'),
        ('其他', '其他'),
    )
    
    AGE_GROUP_CHOICES = (
        ('儿童', '儿童'),
        ('青少年', '青少年'),
        ('青年', '青年'),
        ('中年', '中年'),
        ('老年', '老年'),
    )
    
    id = models.AutoField(primary_key=True, verbose_name='ID')
    name = models.CharField(max_length=100, verbose_name='姓名')
    gender = models.CharField(max_length=10, choices=GENDER_CHOICES, verbose_name='性别')
    age_group = models.CharField(max_length=20, choices=AGE_GROUP_CHOICES, verbose_name='年龄段')
    hair_style = models.CharField(max_length=100, blank=True, null=True, verbose_name='发型')
    hair_color = models.CharField(max_length=50, blank=True, null=True, verbose_name='发色')
    face_features = models.TextField(blank=True, null=True, verbose_name='面部特征')
    body_features = models.TextField(blank=True, null=True, verbose_name='身材特征')
    special_notes = models.TextField(blank=True, null=True, verbose_name='特殊标记')
    image_path = models.CharField(max_length=255, blank=True, null=True, verbose_name='角色图片路径')
    chapter = models.ForeignKey(Chapter, on_delete=models.CASCADE, related_name='characters', verbose_name='对应章节')
    
    def __str__(self):
        return self.name
    
    class Meta:
        verbose_name = '出镜人物'
        verbose_name_plural = '出镜人物'


class Narration(models.Model):
    """
    解说模型
    """
    TASK_STATUS_CHOICES = (
        ('idle', '空闲'),
        ('pending', '等待中'),
        ('processing', '处理中'),
        ('success', '成功'),
        ('failed', '失败'),
        ('cancelled', '已取消'),
    )
    
    id = models.AutoField(primary_key=True, verbose_name='ID')
    scene_number = models.CharField(max_length=20, verbose_name='分镜序号')
    featured_character = models.CharField(max_length=100, verbose_name='特写人物')
    chapter = models.ForeignKey(Chapter, on_delete=models.CASCADE, related_name='narrations', verbose_name='对应章节')
    narration = models.TextField(verbose_name='解说内容')
    image_prompt = models.TextField(verbose_name='图片prompt')
    narration_mp3_path = models.CharField(max_length=255, blank=True, null=True, verbose_name='解说mp3路径')
    tts_response = models.TextField(blank=True, null=True, verbose_name='tts response')
    subtitle_content = models.TextField(blank=True, null=True, verbose_name='字幕文件内容')
    narration_mp4_path = models.CharField(max_length=255, blank=True, null=True, verbose_name='解说mp4路径')
    
    # 图片生成任务状态管理字段
    image_task_status = models.CharField(max_length=20, choices=TASK_STATUS_CHOICES, default='idle', verbose_name='图片任务状态')
    image_task_progress = models.IntegerField(default=0, verbose_name='图片任务进度百分比')
    image_task_message = models.TextField(blank=True, null=True, verbose_name='图片任务日志信息')
    image_task_error = models.TextField(blank=True, null=True, verbose_name='图片任务错误信息')
    volcengine_task_id = models.CharField(max_length=100, blank=True, null=True, verbose_name='火山引擎任务ID')
    celery_task_id = models.CharField(max_length=100, blank=True, null=True, verbose_name='Celery任务ID')
    generated_images = models.JSONField(default=list, blank=True, verbose_name='生成的图片路径列表')
    
    # 时间戳字段
    image_task_started_at = models.DateTimeField(blank=True, null=True, verbose_name='图片任务开始时间')
    image_task_completed_at = models.DateTimeField(blank=True, null=True, verbose_name='图片任务完成时间')
    created_at = models.DateTimeField(auto_now_add=True, verbose_name='创建时间')
    updated_at = models.DateTimeField(auto_now=True, verbose_name='更新时间')
    
    def __str__(self):
        return f"{self.chapter.title} - 解说{self.scene_number}"
    
    class Meta:
        verbose_name = '解说'
        verbose_name_plural = '解说'


class AudioGenerationTask(models.Model):
    """
    音频生成任务模型
    """
    TASK_STATUS_CHOICES = (
        ('pending', '等待中'),
        ('processing', '处理中'),
        ('success', '成功'),
        ('failed', '失败'),
        ('cancelled', '已取消'),
    )
    
    id = models.AutoField(primary_key=True, verbose_name='ID')
    task_id = models.CharField(max_length=100, unique=True, verbose_name='任务ID')
    chapter = models.ForeignKey(Chapter, on_delete=models.CASCADE, related_name='audio_tasks', verbose_name='章节')
    
    # 任务状态相关字段
    status = models.CharField(max_length=20, choices=TASK_STATUS_CHOICES, default='pending', verbose_name='任务状态')
    progress = models.IntegerField(default=0, verbose_name='进度百分比')
    log_message = models.TextField(blank=True, null=True, verbose_name='日志信息')
    error_message = models.TextField(blank=True, null=True, verbose_name='错误信息')
    
    # 生成结果统计
    total_segments = models.IntegerField(default=0, verbose_name='总段数')
    success_count = models.IntegerField(default=0, verbose_name='成功生成数')
    failed_count = models.IntegerField(default=0, verbose_name='失败数')
    skipped_count = models.IntegerField(default=0, verbose_name='跳过数')
    
    # 生成的文件路径列表
    generated_audio_files = models.JSONField(default=list, blank=True, verbose_name='生成的音频文件路径列表')
    generated_timestamp_files = models.JSONField(default=list, blank=True, verbose_name='生成的时间戳文件路径列表')
    generated_ass_files = models.JSONField(default=list, blank=True, verbose_name='生成的ASS字幕文件路径列表')
    
    # 时间戳字段
    created_at = models.DateTimeField(auto_now_add=True, verbose_name='创建时间')
    updated_at = models.DateTimeField(auto_now=True, verbose_name='更新时间')
    started_at = models.DateTimeField(blank=True, null=True, verbose_name='开始时间')
    completed_at = models.DateTimeField(blank=True, null=True, verbose_name='完成时间')
    
    def __str__(self):
        return f"{self.chapter.title} - 音频生成任务 ({self.status})"
    
    class Meta:
        verbose_name = '音频生成任务'
        verbose_name_plural = '音频生成任务'
        ordering = ['-created_at']


class CharacterImageTask(models.Model):
    """
    角色图片生成任务模型
    """
    TASK_STATUS_CHOICES = (
        ('pending', '等待中'),
        ('processing', '处理中'),
        ('success', '成功'),
        ('failed', '失败'),
        ('cancelled', '已取消'),
    )
    
    IMAGE_STYLE_CHOICES = (
        ('realistic', '写实风格'),
        ('anime', '动漫风格'),
        ('cartoon', '卡通风格'),
        ('oil_painting', '油画风格'),
    )
    
    IMAGE_QUALITY_CHOICES = (
        ('standard', '标准'),
        ('hd', '高清'),
        ('ultra', '超高清'),
    )
    
    id = models.AutoField(primary_key=True, verbose_name='ID')
    task_id = models.CharField(max_length=100, unique=True, verbose_name='任务ID')
    character = models.ForeignKey(Character, on_delete=models.CASCADE, related_name='image_tasks', verbose_name='角色')
    chapter = models.ForeignKey(Chapter, on_delete=models.CASCADE, related_name='character_image_tasks', verbose_name='章节')
    
    # 生成参数
    image_style = models.CharField(max_length=20, choices=IMAGE_STYLE_CHOICES, default='realistic', verbose_name='图片风格')
    image_quality = models.CharField(max_length=20, choices=IMAGE_QUALITY_CHOICES, default='standard', verbose_name='图片质量')
    image_count = models.IntegerField(default=1, verbose_name='生成数量')
    custom_prompt = models.TextField(blank=True, null=True, verbose_name='自定义提示词')
    
    # 任务状态
    status = models.CharField(max_length=20, choices=TASK_STATUS_CHOICES, default='pending', verbose_name='任务状态')
    progress = models.IntegerField(default=0, verbose_name='进度百分比')
    log_message = models.TextField(blank=True, null=True, verbose_name='日志信息')
    error_message = models.TextField(blank=True, null=True, verbose_name='错误信息')
    
    # 结果
    generated_images = models.JSONField(default=list, blank=True, verbose_name='生成的图片路径列表')
    
    # 时间戳
    created_at = models.DateTimeField(auto_now_add=True, verbose_name='创建时间')
    updated_at = models.DateTimeField(auto_now=True, verbose_name='更新时间')
    started_at = models.DateTimeField(blank=True, null=True, verbose_name='开始时间')
    completed_at = models.DateTimeField(blank=True, null=True, verbose_name='完成时间')
    
    def __str__(self):
        return f"{self.character.name} - {self.task_id}"
    
    class Meta:
        verbose_name = '角色图片生成任务'
        verbose_name_plural = '角色图片生成任务'
        ordering = ['-created_at']
