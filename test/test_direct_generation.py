#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
直接测试批量生成章节分镜图片功能
"""

import os
import sys
import django
from pathlib import Path

# 添加项目根目录到Python路径
project_root = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(project_root))
sys.path.insert(0, str(project_root / 'web'))

# 设置Django环境
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'web.settings')
os.chdir(str(project_root / 'web'))
django.setup()

from video.models import Novel, Chapter
from video.tasks import batch_generate_chapter_images_async

def test_direct_generation():
    """
    直接测试批量生成功能
    """
    print("🧪 开始直接测试批量生成章节分镜图片功能")
    
    # 查找一个测试章节
    try:
        chapter = Chapter.objects.filter(novel__id=17).first()
        if not chapter:
            print("❌ 未找到测试章节")
            return
            
        print(f"📖 测试章节: {chapter.title} (ID: {chapter.id})")
        print(f"📚 所属小说: {chapter.novel.name} (ID: {chapter.novel.id})")
        
        # 直接调用任务函数（同步执行）
        print("🚀 开始执行批量生成任务...")
        result = batch_generate_chapter_images_async(chapter.novel.id, chapter.id)
        
        print(f"✅ 任务执行结果: {result}")
        
        # 检查章节状态
        chapter.refresh_from_db()
        print(f"📊 最终状态: {chapter.batch_image_status}")
        print(f"📊 进度: {chapter.batch_image_progress}%")
        print(f"📊 消息: {chapter.batch_image_message}")
        if chapter.batch_image_error:
            print(f"❌ 错误: {chapter.batch_image_error}")
            
    except Exception as e:
        print(f"❌ 测试过程中发生错误: {e}")
        import traceback
        traceback.print_exc()

if __name__ == '__main__':
    test_direct_generation()