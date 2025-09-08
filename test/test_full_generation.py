#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
完整生成流程测试脚本
测试解说文案生成和数据库保存的完整流程
"""

import os
import sys
import django

# 添加项目路径
sys.path.append('/Users/xunan/Projects/wrmVideo')
sys.path.append('/Users/xunan/Projects/wrmVideo/web')

# 设置Django环境
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'web.settings')
django.setup()

from video.models import Novel, Chapter, Character, Narration
from video.tasks import generate_script_async
import time

def test_full_generation():
    """
    测试完整的解说文案生成和数据库保存流程
    """
    print("=== 开始完整生成流程测试 ===")
    
    # 查找测试小说
    try:
        novel = Novel.objects.get(id=13)
        print(f"找到测试小说: {novel.name}")
        print(f"当前任务状态: {novel.task_status}")
    except Novel.DoesNotExist:
        print("错误: 找不到ID为13的小说")
        return False
    
    # 清理之前的数据
    print("\n清理之前的测试数据...")
    chapters = Chapter.objects.filter(novel=novel)
    for chapter in chapters:
        narration_count = Narration.objects.filter(chapter=chapter).count()
        print(f"删除章节 '{chapter.title}' 的 {narration_count} 条解说")
        Narration.objects.filter(chapter=chapter).delete()
    chapters.delete()
    
    # 重置小说状态
    novel.task_status = 'pending'
    novel.task_message = ''
    novel.current_task_id = None
    novel.save()
    print(f"重置小说状态为: {novel.task_status}")
    
    print("\n=== 开始异步生成任务 ===")
    # 启动异步任务
    result = generate_script_async.delay(novel.id)
    print(f"任务已启动，任务ID: {result.id}")
    
    # 等待任务完成
    print("等待任务完成...")
    timeout = 300  # 5分钟超时
    start_time = time.time()
    
    while not result.ready():
        if time.time() - start_time > timeout:
            print("任务超时！")
            return False
        
        # 检查任务状态
        novel.refresh_from_db()
        print(f"当前状态: {novel.task_status} - {novel.task_message}")
        time.sleep(10)
    
    # 检查任务结果
    try:
        task_result = result.get()
        print(f"\n任务完成！结果: {task_result['status']}")
        print(f"消息: {task_result['message']}")
    except Exception as e:
        print(f"任务失败: {str(e)}")
        return False
    
    # 验证数据库数据
    print("\n=== 验证数据库数据 ===")
    novel.refresh_from_db()
    print(f"小说状态: {novel.task_status}")
    print(f"任务消息: {novel.task_message}")
    
    chapters = Chapter.objects.filter(novel=novel)
    print(f"章节数量: {chapters.count()}")
    
    total_narrations = 0
    total_characters = 0
    
    for chapter in chapters:
        narrations = Narration.objects.filter(chapter=chapter)
        characters = Character.objects.filter(chapters=chapter)
        
        print(f"  章节: {chapter.title}")
        print(f"    解说数量: {narrations.count()}")
        print(f"    角色数量: {characters.count()}")
        
        total_narrations += narrations.count()
        total_characters += characters.count()
    
    print(f"\n总计:")
    print(f"  解说总数: {total_narrations}")
    print(f"  角色总数: {total_characters}")
    
    # 验证成功条件
    success = (
        novel.task_status == 'script_completed' and
        chapters.count() > 0 and
        total_narrations > 0
    )
    
    if success:
        print("\n✅ 完整生成流程测试成功！")
    else:
        print("\n❌ 完整生成流程测试失败！")
    
    return success

if __name__ == '__main__':
    success = test_full_generation()
    sys.exit(0 if success else 1)