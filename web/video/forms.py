from django import forms
from .models import Novel, Chapter, Character, Narration


class TaskForm(forms.Form):
    """
    创建新任务的表单
    """
    project = forms.ChoiceField(
        label='选择项目',
        choices=[
            ('', '请选择项目...'),
            ('1', '西游记'),
            ('2', '红楼梦'),
            ('3', '水浒传'),
        ],
        required=True,
    )
    chapter = forms.CharField(
        label='章节',
        max_length=100,
        required=True,
        widget=forms.TextInput(attrs={'placeholder': '输入章节名称'})
    )
    description = forms.CharField(
        label='描述',
        required=False,
        widget=forms.Textarea(attrs={'rows': 3})
    )


class NovelForm(forms.ModelForm):
    """
    小说表单类
    """
    class Meta:
        model = Novel
        fields = ['original_file']
        widgets = {
            'original_file': forms.FileInput(attrs={'class': 'form-control', 'accept': '.txt,.doc,.docx,.pdf', 'required': True}),
        }
        labels = {
            'original_file': '上传文件',
        }
        help_texts = {
            'original_file': '支持上传 .txt, .doc, .docx, .pdf 格式的文件，系统将自动提取内容、计算字数并从文件名获取小说名称',
        }


class ChapterForm(forms.ModelForm):
    """
    章节表单类
    """
    class Meta:
        model = Chapter
        fields = ['title', 'word_count', 'format', 'novel', 'video_path']
        widgets = {
            'title': forms.TextInput(attrs={'class': 'form-control', 'placeholder': '请输入章节标题'}),
            'word_count': forms.NumberInput(attrs={'class': 'form-control', 'placeholder': '请输入字数'}),
            'format': forms.TextInput(attrs={'class': 'form-control', 'placeholder': '请输入章节风格'}),
            'novel': forms.Select(attrs={'class': 'form-control'}),
            'video_path': forms.TextInput(attrs={'class': 'form-control', 'placeholder': '请输入视频路径（可选）'}),
        }
        labels = {
            'title': '章节标题',
            'word_count': '字数',
            'format': '章节风格',
            'novel': '所属小说',
            'video_path': '视频路径',
        }


class CharacterForm(forms.ModelForm):
    """
    出镜人物表单类
    """
    class Meta:
        model = Character
        fields = ['name', 'gender', 'age_group', 'hair_style', 'hair_color', 
                 'face_features', 'body_features', 'special_notes', 'chapter']
        widgets = {
            'name': forms.TextInput(attrs={'class': 'form-control', 'placeholder': '请输入人物姓名'}),
            'gender': forms.Select(attrs={'class': 'form-control'}),
            'age_group': forms.Select(attrs={'class': 'form-control'}),
            'hair_style': forms.TextInput(attrs={'class': 'form-control', 'placeholder': '请输入发型'}),
            'hair_color': forms.TextInput(attrs={'class': 'form-control', 'placeholder': '请输入发色'}),
            'face_features': forms.Textarea(attrs={'class': 'form-control', 'rows': 3, 'placeholder': '请输入面部特征'}),
            'body_features': forms.Textarea(attrs={'class': 'form-control', 'rows': 3, 'placeholder': '请输入身材特征'}),
            'special_notes': forms.Textarea(attrs={'class': 'form-control', 'rows': 3, 'placeholder': '请输入特殊标记'}),
            'chapter': forms.Select(attrs={'class': 'form-control'}),
        }
        labels = {
            'name': '姓名',
            'gender': '性别',
            'age_group': '年龄段',
            'hair_style': '发型',
            'hair_color': '发色',
            'face_features': '面部特征',
            'body_features': '身材特征',
            'special_notes': '特殊标记',
            'chapter': '对应章节',
        }


class NarrationForm(forms.ModelForm):
    """
    解说表单类
    """
    class Meta:
        model = Narration
        fields = ['scene_number', 'featured_character', 'chapter', 'narration', 
                 'image_prompt', 'narration_mp3_path', 'tts_response', 
                 'subtitle_content', 'narration_mp4_path']
        widgets = {
            'scene_number': forms.TextInput(attrs={'class': 'form-control', 'placeholder': '请输入分镜序号'}),
            'featured_character': forms.TextInput(attrs={'class': 'form-control', 'placeholder': '请输入特写人物'}),
            'chapter': forms.Select(attrs={'class': 'form-control'}),
            'narration': forms.Textarea(attrs={'class': 'form-control', 'rows': 4, 'placeholder': '请输入解说内容'}),
            'image_prompt': forms.Textarea(attrs={'class': 'form-control', 'rows': 4, 'placeholder': '请输入图片prompt'}),
            'narration_mp3_path': forms.TextInput(attrs={'class': 'form-control', 'placeholder': '请输入解说mp3路径（可选）'}),
            'tts_response': forms.Textarea(attrs={'class': 'form-control', 'rows': 3, 'placeholder': '请输入tts response（可选）'}),
            'subtitle_content': forms.Textarea(attrs={'class': 'form-control', 'rows': 3, 'placeholder': '请输入字幕文件内容（可选）'}),
            'narration_mp4_path': forms.TextInput(attrs={'class': 'form-control', 'placeholder': '请输入解说mp4路径（可选）'}),
        }
        labels = {
            'scene_number': '分镜序号',
            'featured_character': '特写人物',
            'chapter': '对应章节',
            'narration': '解说内容',
            'image_prompt': '图片prompt',
            'narration_mp3_path': '解说mp3路径',
            'tts_response': 'TTS响应',
            'subtitle_content': '字幕内容',
            'narration_mp4_path': '解说mp4路径',
        }


class SearchForm(forms.Form):
    """
    搜索表单类
    """
    search = forms.CharField(
        max_length=100,
        required=False,
        widget=forms.TextInput(attrs={
            'class': 'form-control',
            'placeholder': '请输入搜索关键词',
            'style': 'margin-bottom: 10px;'
        }),
        label='搜索'
    )