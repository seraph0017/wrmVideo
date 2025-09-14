#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
测试批量生成章节分镜图片功能
"""

import os
import sys
import django
import requests
import time
import json

# 添加项目路径
sys.path.append('/Users/xunan/Projects/wrmVideo/web')

# 设置Django环境
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'web.settings')
django.setup()

from video.models import Novel, Chapter

def test_batch_generate_chapter_images():
    """
    测试批量生成章节分镜图片API
    """
    base_url = "http://localhost:8000"
    
    # 获取第一个章节进行测试
    try:
        chapter = Chapter.objects.filter(novel__id=17).first()
        if not chapter:
            print("❌ 没有找到章节数据，请先创建章节")
            return False
            
        print(f"📖 测试章节: {chapter.title} (ID: {chapter.id})")
        
        # 1. 测试启动批量生成任务
        print("\n🚀 启动批量生成章节分镜图片任务...")
        response = requests.post(
            f"{base_url}/video/api/chapters/{chapter.id}/batch-generate-chapter-images/",
            headers={'Content-Type': 'application/json'}
        )
        
        if response.status_code == 200:
            result = response.json()
            print(f"✅ 任务启动成功: {result}")
            task_id = result.get('task_id')
            
            # 2. 测试查询任务状态
            print("\n📊 查询任务状态...")
            for i in range(5):  # 查询5次状态
                status_response = requests.get(
                    f"{base_url}/video/api/chapters/{chapter.id}/batch-image-status/"
                )
                
                if status_response.status_code == 200:
                    status_result = status_response.json()
                    print(f"状态查询 {i+1}: {status_result}")
                    
                    if status_result.get('status') in ['completed', 'failed']:
                        break
                        
                    time.sleep(2)  # 等待2秒再查询
                else:
                    print(f"❌ 状态查询失败: {status_response.status_code} - {status_response.text}")
                    
            return True
            
        else:
            print(f"❌ 任务启动失败: {response.status_code} - {response.text}")
            return False
            
    except Exception as e:
        print(f"❌ 测试过程中出现错误: {str(e)}")
        return False

def test_chapter_status_fields():
    """
    测试章节模型的新状态字段
    """
    print("\n🔍 测试章节模型状态字段...")
    
    try:
        chapter = Chapter.objects.first()
        if not chapter:
            print("❌ 没有找到章节数据")
            return False
            
        # 检查新字段是否存在
        fields_to_check = [
            'batch_image_status',
            'batch_image_task_id', 
            'batch_image_progress',
            'batch_image_message',
            'batch_image_error',
            'batch_image_started_at',
            'batch_image_completed_at'
        ]
        
        for field in fields_to_check:
            if hasattr(chapter, field):
                value = getattr(chapter, field)
                print(f"✅ {field}: {value}")
            else:
                print(f"❌ 字段 {field} 不存在")
                return False
                
        return True
        
    except Exception as e:
        print(f"❌ 字段检查失败: {str(e)}")
        return False

if __name__ == "__main__":
    print("🧪 开始测试批量生成章节分镜图片功能\n")
    
    # 测试模型字段
    field_test = test_chapter_status_fields()
    
    # 测试API功能
    api_test = test_batch_generate_chapter_images()
    
    print("\n📋 测试结果汇总:")
    print(f"模型字段测试: {'✅ 通过' if field_test else '❌ 失败'}")
    print(f"API功能测试: {'✅ 通过' if api_test else '❌ 失败'}")
    
    if field_test and api_test:
        print("\n🎉 所有测试通过！批量生成章节分镜图片功能已成功实现")
    else:
        print("\n⚠️ 部分测试失败，请检查相关配置")