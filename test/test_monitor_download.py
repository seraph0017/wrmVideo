#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
测试监控和下载分镜图片功能
"""

import os
import sys
import django
import time

# 添加项目路径
sys.path.append('/Users/nathan/Projects/wrmVideo')
sys.path.append('/Users/nathan/Projects/wrmVideo/web')

# 设置Django环境
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'web.settings')
django.setup()

from video.tasks import generate_narration_images_async
from video.models import Narration
from celery.result import AsyncResult

def test_monitor_download():
    """
    测试监控和下载功能
    """
    print("=== 测试监控和下载分镜图片功能 ===")
    
    # 查找一个解说记录
    try:
        narration = Narration.objects.first()
        if not narration:
            print("❌ 没有找到解说记录")
            return
        
        print(f"找到解说记录: ID={narration.id}, 场景={narration.scene_number}")
        print(f"解说内容: {narration.narration[:50]}...")
        
        print("\n调用 generate_narration_images_async 任务...")
        
        # 调用任务
        task = generate_narration_images_async.delay(narration.id)
        print(f"任务已提交，任务ID: {task.id}")
        
        print("等待任务完成...")
        
        # 等待任务完成
        result = task.get(timeout=120)  # 等待最多2分钟
        
        print("\n任务执行结果:")
        print(f"状态: {result.get('status')}")
        
        if result.get('status') == 'success':
            print(f"火山引擎任务ID: {result.get('task_id')}")
            print(f"监控任务ID: {result.get('monitor_task_id')}")
            print(f"消息: {result.get('message')}")
            
            # 检查监控任务状态
            monitor_task_id = result.get('monitor_task_id')
            if monitor_task_id:
                print(f"\n监控任务 {monitor_task_id} 已启动")
                print("监控任务将在后台运行，定期查询火山引擎任务状态并在完成时自动下载图片")
                print("可以通过celery worker日志查看监控进度")
                
                # 检查监控任务状态
                monitor_result = AsyncResult(monitor_task_id)
                print(f"监控任务当前状态: {monitor_result.status}")
                
                if monitor_result.status == 'PENDING':
                    print("监控任务正在等待执行")
                elif monitor_result.status == 'RETRY':
                    print("监控任务正在重试中")
                elif monitor_result.status == 'SUCCESS':
                    print("监控任务已完成")
                    monitor_data = monitor_result.get()
                    if monitor_data.get('downloaded_images'):
                        print(f"已下载 {len(monitor_data['downloaded_images'])} 张图片:")
                        for img in monitor_data['downloaded_images']:
                            print(f"  - {img['filename']}: {img['path']}")
                
            print("\n✅ 任务执行成功！新的监控和下载机制已启动。")
        else:
            print(f"❌ 任务执行失败: {result.get('error')}")
            
    except Exception as e:
        print(f"❌ 测试过程中出现异常: {str(e)}")
        import traceback
        traceback.print_exc()

if __name__ == '__main__':
    test_monitor_download()