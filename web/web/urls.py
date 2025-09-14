"""
URL configuration for web project.

The `urlpatterns` list routes URLs to views. For more information please see:
    https://docs.djangoproject.com/en/4.2/topics/http/urls/
Examples:
Function views
    1. Add an import:  from my_app import views
    2. Add a URL to urlpatterns:  path('', views.home, name='home')
Class-based views
    1. Add an import:  from other_app.views import Home
    2. Add a URL to urlpatterns:  path('', Home.as_view(), name='home')
Including another URLconf
    1. Import the include() function: from django.urls import include, path
    2. Add a URL to urlpatterns:  path('blog/', include('blog.urls'))
"""
from django.contrib import admin
from django.urls import path, include
from django.views.generic.base import RedirectView
from django.conf import settings
from django.conf.urls.static import static

urlpatterns = [
    path('admin/', admin.site.urls),
    path('video/', include('video.urls')),
    # 添加chapters的直接路由，重定向到video应用
    path('chapters/<int:pk>/', RedirectView.as_view(url='/video/chapters/%(pk)s/', permanent=True), name='chapter-redirect'),
    path('', RedirectView.as_view(url='/video/dashboard/', permanent=True), name='root-redirect'),
]

# 在开发环境中提供媒体文件和静态文件服务
if settings.DEBUG:
    urlpatterns += static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)
    urlpatterns += static(settings.STATIC_URL, document_root=settings.STATIC_ROOT)
    # 为data目录提供静态文件服务
    urlpatterns += static('/data/', document_root=settings.BASE_DIR.parent / 'data')
