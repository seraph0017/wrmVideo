#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
测试改进后的解说图片异步任务
验证状态管理和监控功能
"""

import os
import sys
import django
from django.conf import settings

# 添加项目路径
sys.path.append('/Users/nathan/Projects/wrmVideo/web')

# 设置Django环境
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'web.settings')
django.setup()

from video.models import Narration
from video.tasks import generate_narration_images_async
import time

def test_narration_image_async():
    """
    测试解说图片异步任务的状态管理功能
    """
    print("=== 测试解说图片异步任务 ===")
    
    try:
        # 查找一个解说对象进行测试
        narration = Narration.objects.first()
        if not narration:
            print("❌ 没有找到解说对象，请先创建一些测试数据")
            return
        
        print(f"📝 找到解说对象: ID={narration.id}, 场景={narration.scene_number}")
        print(f"📝 解说内容: {narration.narration[:100]}...")
        
        # 重置任务状态
        narration.image_task_status = 'pending'
        narration.image_task_progress = 0
        narration.image_task_message = ''
        narration.image_task_error = ''
        narration.volcengine_task_id = ''
        narration.celery_task_id = ''
        narration.save()
        print("🔄 已重置任务状态")
        
        # 调用异步任务
        print("🚀 启动解说图片生成异步任务...")
        result = generate_narration_images_async.delay(narration.id)
        
        print(f"✅ 任务已提交，任务ID: {result.id}")
        print(f"📊 任务状态: {result.status}")
        
        # 等待一段时间让任务开始执行
        print("⏳ 等待5秒让任务开始执行...")
        time.sleep(5)
        
        # 检查数据库中的状态更新
        narration.refresh_from_db()
        print(f"\n📊 当前任务状态:")
        print(f"  - image_task_status: {narration.image_task_status}")
        print(f"  - image_task_progress: {narration.image_task_progress}%")
        print(f"  - image_task_message: {narration.image_task_message}")
        if narration.image_task_error:
            print(f"  - image_task_error: {narration.image_task_error}")
        if narration.volcengine_task_id:
            print(f"  - volcengine_task_id: {narration.volcengine_task_id}")
        if narration.celery_task_id:
            print(f"  - celery_task_id: {narration.celery_task_id}")
        
        print(f"\n🎯 Celery任务状态: {result.status}")
        if result.ready():
            try:
                task_result = result.get()
                print(f"📋 任务结果: {task_result}")
            except Exception as e:
                print(f"❌ 获取任务结果失败: {str(e)}")
        else:
            print("⏳ 任务仍在执行中...")
        
        print("\n✅ 测试完成！")
        print("💡 提示: 可以查看Celery worker日志了解详细执行情况")
        print("💡 提示: 如果配置了火山引擎API，监控任务会自动启动")
        
    except Exception as e:
        print(f"❌ 测试过程中出现异常: {str(e)}")
        import traceback
        traceback.print_exc()

if __name__ == '__main__':
    test_narration_image_async()