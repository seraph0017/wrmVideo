#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
最终测试：批量生成章节分镜图片功能
验证修复后的章节目录查找逻辑
"""

import os
import sys
import django
from pathlib import Path

# 设置项目根目录
project_root = Path(__file__).resolve().parent.parent
os.chdir(str(project_root / 'web'))
sys.path.insert(0, str(project_root / 'web'))

# 设置Django环境
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'web.settings')
django.setup()

from video.models import Novel, Chapter
from video.tasks import batch_generate_chapter_images_async
from video.utils import get_chapter_number_from_filesystem, get_chapter_directory_path

def test_chapter_directory_resolution():
    """
    测试章节目录解析功能
    """
    print("🔍 测试章节目录解析功能...")
    
    try:
        # 获取小说ID 17的第2章
        chapter = Chapter.objects.filter(novel__id=17, title="第2章").first()
        if not chapter:
            print("❌ 未找到测试章节")
            return False
            
        print(f"📖 测试章节: {chapter.title} (ID: {chapter.id})")
        
        # 测试章节编号解析
        chapter_number = get_chapter_number_from_filesystem(17, chapter)
        print(f"📁 解析的章节编号: {chapter_number}")
        
        if not chapter_number:
            print("❌ 无法解析章节编号")
            return False
            
        # 测试目录路径构建
        chapter_dir = get_chapter_directory_path(17, chapter_number)
        print(f"📂 章节目录路径: {chapter_dir}")
        
        # 检查目录是否存在
        if os.path.exists(chapter_dir):
            print(f"✅ 章节目录存在")
            
            # 检查narration.txt文件
            narration_file = os.path.join(chapter_dir, "narration.txt")
            if os.path.exists(narration_file):
                print(f"✅ narration.txt文件存在")
                return True
            else:
                print(f"❌ narration.txt文件不存在")
                return False
        else:
            print(f"❌ 章节目录不存在")
            return False
            
    except Exception as e:
        print(f"❌ 测试失败: {str(e)}")
        return False

def test_batch_generation_task():
    """
    测试批量生成任务
    """
    print("\n🚀 测试批量生成任务...")
    
    try:
        # 获取测试章节
        chapter = Chapter.objects.filter(novel__id=17, title="第2章").first()
        if not chapter:
            print("❌ 未找到测试章节")
            return False
            
        # 重置章节状态
        chapter.batch_image_status = 'idle'
        chapter.batch_image_task_id = None
        chapter.batch_image_progress = 0
        chapter.batch_image_message = None
        chapter.batch_image_error = None
        chapter.batch_image_started_at = None
        chapter.batch_image_completed_at = None
        chapter.save()
        
        print(f"📖 测试章节: {chapter.title} (ID: {chapter.id})")
        
        # 直接调用任务函数（同步执行）
        result = batch_generate_chapter_images_async(17, chapter.id)
        
        print(f"📊 任务执行结果: {result}")
        
        # 刷新章节状态
        chapter.refresh_from_db()
        
        print(f"📊 最终状态: {chapter.batch_image_status}")
        print(f"📊 进度: {chapter.batch_image_progress}%")
        print(f"📊 消息: {chapter.batch_image_message}")
        
        if chapter.batch_image_error:
            print(f"❌ 错误: {chapter.batch_image_error}")
            
        return chapter.batch_image_status == 'success'
        
    except Exception as e:
        print(f"❌ 任务执行失败: {str(e)}")
        return False

def main():
    """
    主测试函数
    """
    print("🧪 开始最终测试：批量生成章节分镜图片功能\n")
    
    # 测试1：章节目录解析
    test1_result = test_chapter_directory_resolution()
    
    # 测试2：批量生成任务
    test2_result = test_batch_generation_task()
    
    print("\n📋 测试结果汇总:")
    print(f"章节目录解析测试: {'✅ 通过' if test1_result else '❌ 失败'}")
    print(f"批量生成任务测试: {'✅ 通过' if test2_result else '❌ 失败'}")
    
    if test1_result and test2_result:
        print("\n🎉 所有测试通过！批量生成章节分镜图片功能修复成功")
    else:
        print("\n❌ 部分测试失败，需要进一步检查")

if __name__ == '__main__':
    main()