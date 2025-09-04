from django import forms

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