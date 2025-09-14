#!/usr/bin/env python3
# -*- coding: utf-8 -*-

import os
import sys
import django

# 设置Django环境
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'web.settings')
django.setup()

from video.models import Chapter

def check_chapter_status():
    """检查章节状态和视频路径"""
    chapters = Chapter.objects.filter(novel_id=17)
    print(f"小说17的所有章节 (共{chapters.count()}个):")
    
    for ch in chapters:
        print(f"ID: {ch.id}, 标题: {ch.title}")
        print(f"  视频路径: {ch.video_path}")
        print(f"  批量图片状态: {ch.batch_image_status}")
        
        # 检查视频文件是否存在
        if ch.video_path:
            video_exists = os.path.exists(ch.video_path)
            print(f"  视频文件存在: {video_exists}")
            if video_exists:
                file_size = os.path.getsize(ch.video_path)
                print(f"  文件大小: {file_size} bytes")
        else:
            print("  视频文件存在: False (路径为空)")
        print("-" * 50)

if __name__ == '__main__':
    check_chapter_status()