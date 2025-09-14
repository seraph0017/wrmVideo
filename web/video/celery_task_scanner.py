#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Celery任务扫描器
用于扫描数据库中保存的Celery任务ID并检查任务状态
"""

import logging
from celery.result import AsyncResult
from django.utils import timezone
from datetime import timedelta
from .models import Chapter, CharacterImageTask, Narration
from celery import current_app

logger = logging.getLogger(__name__)

def scan_chapter_batch_image_tasks():
    """
    扫描章节批量图片生成任务
    检查数据库中保存的Celery任务ID状态
    
    Returns:
        dict: 扫描结果统计
    """
    logger.info("开始扫描章节批量图片生成任务")
    
    stats = {
        'total': 0,
        'completed': 0,
        'failed': 0,
        'processing': 0,
        'updated': 0
    }
    
    try:
        # 只扫描最近24小时内更新的任务，提高性能
        recent_time = timezone.now() - timedelta(hours=24)
        chapters = Chapter.objects.filter(
            batch_image_task_id__isnull=False,
            batch_image_started_at__gte=recent_time  # 只扫描最近24小时的任务
        ).exclude(
            batch_image_status='completed'  # 只排除已标记为completed的任务
        )
        
        stats['total'] = chapters.count()
        logger.info(f"找到 {stats['total']} 个处理中的章节批量图片任务")
        
        for chapter in chapters:
            try:
                # 获取Celery任务结果
                task_result = AsyncResult(chapter.batch_image_task_id)
                
                logger.info(f"检查章节 {chapter.id} 的任务状态: {task_result.status}, 当前数据库状态: {chapter.batch_image_status}")
                
                if task_result.ready():
                    if task_result.successful():
                        # 任务成功完成
                        result = task_result.result
                        if chapter.batch_image_status != 'completed':
                            chapter.batch_image_status = 'completed'
                            chapter.batch_image_progress = 100
                            chapter.batch_image_message = result.get('message', '批量生成完成')
                            chapter.batch_image_completed_at = timezone.now()
                            chapter.save()
                            stats['updated'] += 1
                            logger.info(f"章节 {chapter.id} 批量图片生成任务已完成，状态已更新")
                        stats['completed'] += 1
                        
                    else:
                        # 任务失败
                        error_info = str(task_result.info) if task_result.info else '未知错误'
                        if chapter.batch_image_status != 'failed':
                            chapter.batch_image_status = 'failed'
                            chapter.batch_image_message = f'任务失败: {error_info}'
                            chapter.batch_image_error = error_info
                            chapter.batch_image_completed_at = timezone.now()
                            chapter.save()
                            stats['updated'] += 1
                            logger.error(f"章节 {chapter.id} 批量图片生成任务失败，状态已更新: {error_info}")
                        stats['failed'] += 1
                        
                else:
                    # 任务仍在进行中
                    if task_result.status == 'PENDING':
                        # 任务还在队列中等待
                        if chapter.batch_image_status != 'pending':
                            chapter.batch_image_status = 'pending'
                            chapter.save()
                            stats['updated'] += 1
                    else:
                        # 其他状态（如STARTED, RETRY等）
                        if chapter.batch_image_status != 'processing':
                            chapter.batch_image_status = 'processing'
                            chapter.save()
                            stats['updated'] += 1
                    
                    stats['processing'] += 1
                    
                    # 如果有进度信息，更新进度
                    if task_result.status == 'PROGRESS' and task_result.info:
                        progress_info = task_result.info
                        if isinstance(progress_info, dict):
                            current_progress = progress_info.get('current', chapter.batch_image_progress)
                            status_message = progress_info.get('status', chapter.batch_image_message)
                            
                            if current_progress != chapter.batch_image_progress or status_message != chapter.batch_image_message:
                                chapter.batch_image_progress = current_progress
                                chapter.batch_image_message = status_message
                                chapter.save()
                                stats['updated'] += 1
                                logger.info(f"更新章节 {chapter.id} 任务进度: {current_progress}%")
                    
            except Exception as e:
                logger.error(f"检查章节 {chapter.id} 任务状态失败: {str(e)}")
                # 可以选择将任务标记为失败或保持原状态
                continue
                
    except Exception as e:
        logger.error(f"扫描章节批量图片任务失败: {str(e)}")
        
    logger.info(f"章节批量图片任务扫描完成: {stats}")
    return stats

def scan_character_image_tasks():
    """
    扫描角色图片生成任务
    检查CharacterImageTask表中的任务状态
    
    Returns:
        dict: 扫描结果统计
    """
    logger.info("开始扫描角色图片生成任务")
    
    stats = {
        'total': 0,
        'completed': 0,
        'failed': 0,
        'processing': 0,
        'updated': 0
    }
    
    try:
        # 只扫描最近24小时内更新的任务，提高性能
        recent_time = timezone.now() - timedelta(hours=24)
        tasks = CharacterImageTask.objects.filter(
            status__in=['pending', 'processing'],
            created_at__gte=recent_time  # 只扫描最近24小时的任务
        )
        
        stats['total'] = tasks.count()
        logger.info(f"找到 {stats['total']} 个待处理的角色图片任务")
        
        for task in tasks:
            try:
                # 这里可以根据task的volcengine_task_id查询火山引擎API状态
                # 或者根据其他逻辑更新任务状态
                # 暂时跳过，因为需要具体的API调用逻辑
                stats['processing'] += 1
                
            except Exception as e:
                logger.error(f"检查角色图片任务 {task.task_id} 状态失败: {str(e)}")
                continue
                
    except Exception as e:
        logger.error(f"扫描角色图片任务失败: {str(e)}")
        
    logger.info(f"角色图片任务扫描完成: {stats}")
    return stats

def scan_narration_image_tasks():
    """
    扫描旁白图片生成任务
    检查Narration表中有celery_task_id的记录
    
    Returns:
        dict: 扫描结果统计
    """
    logger.info("开始扫描旁白图片生成任务")
    
    stats = {
        'total': 0,
        'completed': 0,
        'failed': 0,
        'processing': 0,
        'updated': 0
    }
    
    try:
        # 只扫描最近24小时内更新的任务，提高性能
        recent_time = timezone.now() - timedelta(hours=24)
        narrations = Narration.objects.filter(
            celery_task_id__isnull=False,
            image_task_status='processing',
            image_task_started_at__gte=recent_time  # 只扫描最近24小时的任务
        )
        
        stats['total'] = narrations.count()
        logger.info(f"找到 {stats['total']} 个处理中的旁白图片任务")
        
        for narration in narrations:
            try:
                # 获取Celery任务结果
                task_result = AsyncResult(narration.celery_task_id)
                
                logger.info(f"检查旁白 {narration.id} 的任务状态: {task_result.status}")
                
                if task_result.ready():
                    if task_result.successful():
                        # 任务成功完成
                        result = task_result.result
                        narration.image_task_status = 'completed'
                        narration.image_task_progress = 100
                        narration.image_task_message = result.get('message', '图片生成完成')
                        narration.save()
                        
                        stats['completed'] += 1
                        stats['updated'] += 1
                        logger.info(f"旁白 {narration.id} 图片生成任务已完成")
                        
                    else:
                        # 任务失败
                        error_info = str(task_result.info) if task_result.info else '未知错误'
                        narration.image_task_status = 'failed'
                        narration.image_task_message = f'任务失败: {error_info}'
                        narration.image_task_error = error_info
                        narration.save()
                        
                        stats['failed'] += 1
                        stats['updated'] += 1
                        logger.error(f"旁白 {narration.id} 图片生成任务失败: {error_info}")
                        
                else:
                    # 任务仍在进行中
                    stats['processing'] += 1
                    
                    # 如果有进度信息，更新进度
                    if task_result.status == 'PROGRESS' and task_result.info:
                        progress_info = task_result.info
                        if isinstance(progress_info, dict):
                            current_progress = progress_info.get('current', narration.image_task_progress)
                            status_message = progress_info.get('status', narration.image_task_message)
                            
                            if current_progress != narration.image_task_progress or status_message != narration.image_task_message:
                                narration.image_task_progress = current_progress
                                narration.image_task_message = status_message
                                narration.save()
                                stats['updated'] += 1
                                logger.info(f"更新旁白 {narration.id} 任务进度: {current_progress}%")
                    
            except Exception as e:
                logger.error(f"检查旁白 {narration.id} 任务状态失败: {str(e)}")
                continue
                
    except Exception as e:
        logger.error(f"扫描旁白图片任务失败: {str(e)}")
        
    logger.info(f"旁白图片任务扫描完成: {stats}")
    return stats

def scan_all_celery_tasks():
    """
    扫描所有数据库中的Celery任务
    
    Returns:
        dict: 总体扫描结果统计
    """
    logger.info("开始扫描所有数据库中的Celery任务")
    
    total_stats = {
        'chapter_batch_images': {},
        'character_images': {},
        'narration_images': {},
        'total_updated': 0
    }
    
    try:
        # 扫描章节批量图片任务
        total_stats['chapter_batch_images'] = scan_chapter_batch_image_tasks()
        
        # 扫描角色图片任务
        total_stats['character_images'] = scan_character_image_tasks()
        
        # 扫描旁白图片任务
        total_stats['narration_images'] = scan_narration_image_tasks()
        
        # 计算总更新数
        total_stats['total_updated'] = (
            total_stats['chapter_batch_images'].get('updated', 0) +
            total_stats['character_images'].get('updated', 0) +
            total_stats['narration_images'].get('updated', 0)
        )
        
        logger.info(f"所有Celery任务扫描完成，总共更新了 {total_stats['total_updated']} 个任务")
        
    except Exception as e:
        logger.error(f"扫描所有Celery任务失败: {str(e)}")
        
    return total_stats