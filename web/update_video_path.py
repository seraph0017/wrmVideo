#!/usr/bin/env python3
# -*- coding: utf-8 -*-

import os
import sys
import django

# 设置Django环境
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'web.settings')
django.setup()

from video.models import Chapter

def update_chapter_video_path():
    """更新章节的视频路径"""
    # 查找第2章
    try:
        chapter = Chapter.objects.get(novel_id=17, title='第2章')
        print(f"找到章节: ID={chapter.id}, 标题={chapter.title}")
        
        # 设置视频路径
        video_path = '/Users/xunan/Projects/wrmVideo/data/017/chapter_002/chapter_002_complete_video.mp4'
        
        # 检查文件是否存在
        if os.path.exists(video_path):
            chapter.video_path = video_path
            chapter.save()
            print(f"成功更新视频路径: {video_path}")
            print(f"文件大小: {os.path.getsize(video_path)} bytes")
        else:
            print(f"视频文件不存在: {video_path}")
            
    except Chapter.DoesNotExist:
        print("未找到第2章")
    except Exception as e:
        print(f"更新失败: {e}")

if __name__ == '__main__':
    update_chapter_video_path()