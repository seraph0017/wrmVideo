from django.shortcuts import render

# Create your views here.
from django.http import HttpResponse
from .forms import TaskForm


def index(request):
    return HttpResponse("Hello, world. You're at the polls index.")


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
    
    context = {
        'form': form,
    }
    return render(request, 'dashboard.html', context)