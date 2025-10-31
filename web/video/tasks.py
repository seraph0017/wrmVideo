# -*- coding: utf-8 -*-
"""
Celery异步任务
用于处理视频生成相关的异步任务
"""

from celery import shared_task
import time
import logging
import os
import subprocess
import json
import sys
from pathlib import Path
from django.conf import settings
from django.utils import timezone
from .models import CharacterImageTask, Character, Chapter
from volcengine.visual.VisualService import VisualService

# 添加项目根目录到Python路径，以便导入check_async_tasks模块
project_root = Path(__file__).resolve().parent.parent.parent
sys.path.insert(0, str(project_root))

try:
    from check_async_tasks import (
        process_all_data_directories,
        process_chapter_async_tasks,
        get_all_task_files,
        check_all_tasks
    )
except ImportError as e:
    logger.warning(f"无法导入check_async_tasks模块: {e}")
    process_all_data_directories = None
    process_chapter_async_tasks = None
    get_all_task_files = None
    check_all_tasks = None

# 导入Celery任务扫描器
try:
    from .celery_task_scanner import scan_all_celery_tasks
except ImportError as e:
    logger.warning(f"无法导入celery_task_scanner模块: {e}")
    scan_all_celery_tasks = None

logger = logging.getLogger(__name__)


@shared_task
def test_task(message):
    """
    测试任务
    
    Args:
        message (str): 测试消息
        
    Returns:
        str: 处理结果
    """
    logger.info(f"开始执行测试任务: {message}")
    time.sleep(5)  # 模拟耗时操作
    result = f"任务完成: {message}"
    logger.info(result)
    return result


@shared_task
def generate_video_async(novel_id, chapter_id):
    """
    异步生成视频任务
    
    Args:
        novel_id (int): 小说ID
        chapter_id (int): 章节ID
        
    Returns:
        dict: 处理结果
    """
    logger.info(f"开始异步生成视频: 小说ID={novel_id}, 章节ID={chapter_id}")
    
    try:
        # 这里可以调用现有的视频生成脚本
        # 例如: python gen_video.py data/{novel_id:03d}
        
        # 模拟视频生成过程
        time.sleep(10)
        
        result = {
            'status': 'success',
            'novel_id': novel_id,
            'chapter_id': chapter_id,
            'message': '视频生成完成'
        }
        return result
        
    except Exception as e:
        logger.error(f"视频生成失败: {str(e)}")
        return {
            'status': 'error',
            'novel_id': novel_id,
            'chapter_id': chapter_id,
            'message': f'视频生成失败: {str(e)}'
        }


@shared_task
def generate_character_images_async(novel_id):
    """
    异步生成角色图片任务
    
    Args:
        novel_id (int): 小说ID
        
    Returns:
        dict: 处理结果
    """
    logger.info(f"开始异步生成角色图片: 小说ID={novel_id}")
    
    try:
        # 这里可以调用现有的角色图片生成脚本
        # 例如: python gen_character_image.py data/{novel_id:03d}
        
        # 模拟角色图片生成过程
        time.sleep(15)
        
        result = {
            'status': 'success',
            'novel_id': novel_id,
            'message': '角色图片生成完成'
        }
        
        logger.info(f"角色图片生成完成: {result}")
        return result
        
    except Exception as e:
        logger.error(f"角色图片生成失败: {str(e)}")
        return {
            'status': 'error',
            'novel_id': novel_id,
            'message': f'角色图片生成失败: {str(e)}'
        }


@shared_task(bind=True)
def generate_script_async(self, novel_id, script_params=None):
    """
    异步生成解说文案任务 - 对应 gen_script_v2.py 的操作
    """
    logger.info(f"[TASK START] 开始异步生成解说文案任务 - 小说ID: {novel_id}")
    logger.info(f"[TASK PARAMS] 脚本参数: {script_params}")
    
    # 更新任务状态为开始
    self.update_state(
        state='PROGRESS',
        meta={'current': 0, 'total': 100, 'status': '正在初始化...'}
    )
    
    try:
        # 导入Django模型
        from .models import Novel
        import subprocess
        import os
        
        logger.info(f"[DATABASE] 正在查询小说信息...")
        # 获取小说对象
        try:
            novel = Novel.objects.get(id=novel_id)
            logger.info(f"[DATABASE] 找到小说: {novel.name} (ID: {novel.id})")
        except Novel.DoesNotExist:
            logger.error(f"[DATABASE] 小说 ID {novel_id} 不存在")
            raise Exception(f"小说 ID {novel_id} 不存在")
        
        # 更新进度
        self.update_state(
            state='PROGRESS',
            meta={'current': 10, 'total': 100, 'status': '检查小说文件...'}
        )
        
        # 检查小说文件是否存在
        logger.info(f"[FILE CHECK] 检查小说文件: {novel.original_file}")
        if not novel.original_file or not os.path.exists(novel.original_file.path):
            # 更新任务状态为失败
            logger.error(f"[FILE CHECK] 小说文件不存在: {novel.original_file}")
            novel.task_status = 'script_failed'
            novel.task_message = f'小说文件不存在: {novel.original_file}'
            novel.current_task_id = None
            novel.save()
            raise Exception(f"小说文件不存在: {novel.original_file}")
        logger.info(f"[FILE CHECK] 小说文件存在，路径: {novel.original_file.path}")
        
        # 更新进度
        self.update_state(
            state='PROGRESS',
            meta={'current': 20, 'total': 100, 'status': '准备数据目录...'}
        )
        
        # 构建数据目录路径
        data_dir = f"data/{novel_id:03d}"
        project_root = os.path.join(os.path.dirname(os.path.dirname(os.path.dirname(__file__))))
        full_data_dir = os.path.join(project_root, data_dir)
        logger.info(f"[DIRECTORY] 数据目录: {data_dir}")
        logger.info(f"[DIRECTORY] 完整路径: {full_data_dir}")
        
        # 确保数据目录存在
        os.makedirs(full_data_dir, exist_ok=True)
        logger.info(f"[DIRECTORY] 数据目录已创建或已存在")
        
        # 更新进度
        self.update_state(
            state='PROGRESS',
            meta={'current': 30, 'total': 100, 'status': '构建命令参数...'}
        )
        
        # 构建命令行参数
        cmd = ['python', 'gen_script_v2.py', novel.original_file.path, '--output', data_dir]
        logger.info(f"[COMMAND] 基础命令: {' '.join(cmd)}")
        
        # 如果有参数配置，添加到命令行
        if script_params:
            logger.info(f"[COMMAND] 添加脚本参数...")
            if script_params.get('chapters'):
                cmd.extend(['--chapters', str(script_params['chapters'])])
                logger.info(f"[COMMAND] 添加参数: --chapters {script_params['chapters']}")
            if script_params.get('limit'):
                cmd.extend(['--limit', str(script_params['limit'])])
                logger.info(f"[COMMAND] 添加参数: --limit {script_params['limit']}")
            if script_params.get('workers'):
                cmd.extend(['--workers', str(script_params['workers'])])
                logger.info(f"[COMMAND] 添加参数: --workers {script_params['workers']}")
            if script_params.get('min_length'):
                cmd.extend(['--min-length', str(script_params['min_length'])])
                logger.info(f"[COMMAND] 添加参数: --min-length {script_params['min_length']}")
            if script_params.get('max_length'):
                cmd.extend(['--max-length', str(script_params['max_length'])])
                logger.info(f"[COMMAND] 添加参数: --max-length {script_params['max_length']}")
            if script_params.get('max_retries'):
                cmd.extend(['--max-retries', str(script_params['max_retries'])])
                logger.info(f"[COMMAND] 添加参数: --max-retries {script_params['max_retries']}")
            if script_params.get('validate_only'):
                cmd.append('--validate-only')
                logger.info(f"[COMMAND] 添加参数: --validate-only")
            if script_params.get('regenerate'):
                cmd.append('--regenerate')
                logger.info(f"[COMMAND] 添加参数: --regenerate")
        
        logger.info(f"[COMMAND] 最终命令: {' '.join(cmd)}")
        
        # 更新进度
        self.update_state(
            state='PROGRESS',
            meta={'current': 40, 'total': 100, 'status': '开始执行解说文案生成...'}
        )
        
        # 使用改进的日志记录系统调用 gen_script_v2.py 脚本
        from .logging_utils import run_command_with_logging, create_progress_callback
        
        progress_callback = create_progress_callback(self, base_progress=40, max_progress=80)
        result = run_command_with_logging(
            cmd,
            cwd=project_root,
            progress_callback=progress_callback,
            task_self=self
        )
        
        # 更新进度
        self.update_state(
            state='PROGRESS',
            meta={'current': 80, 'total': 100, 'status': '处理执行结果...'}
        )
        
        if result.returncode == 0:
            logger.info(f"[SCRIPT SUCCESS] 小说 {novel_id} 解说文案生成完成")
            logger.info(f"[SCRIPT OUTPUT] 脚本输出: {result.stdout[:500]}..." if len(result.stdout) > 500 else f"[SCRIPT OUTPUT] 脚本输出: {result.stdout}")
            
            # 更新进度
            self.update_state(
                state='PROGRESS',
                meta={'current': 85, 'total': 100, 'status': '解析解说文案并保存到数据库...'}
            )
            
            # 解析解说文案并保存到数据库
            try:
                from .utils import parse_narration_file
                from .models import Chapter, Character, Narration
                import glob
                
                # 查找生成的解说文案文件
                narration_files = glob.glob(os.path.join(full_data_dir, 'chapter_*/narration.txt'))
                logger.info(f"[PARSE] 找到 {len(narration_files)} 个解说文案文件")
                
                for narration_file in narration_files:
                    logger.info(f"[PARSE] 正在处理文件: {narration_file}")
                    # 读取解说文案内容
                    with open(narration_file, 'r', encoding='utf-8') as f:
                        narration_content = f.read()
                    logger.info(f"[PARSE] 文件内容长度: {len(narration_content)} 字符")
                    
                    # 解析解说文案
                    parsed_data = parse_narration_file(narration_content)
                    
                    # 获取章节信息
                    chapter_info = parsed_data['chapter_info']
                    chapter_title = chapter_info.get('title')
                    
                    # 如果没有标题，尝试从章节号生成
                    if not chapter_title and chapter_info.get('chapter_number'):
                        chapter_title = f"第{chapter_info['chapter_number']}章"
                    
                    # 如果还是没有标题，从文件路径推断
                    if not chapter_title:
                        import re
                        match = re.search(r'chapter_(\d+)', narration_file)
                        if match:
                            chapter_title = f"第{match.group(1)}章"
                        else:
                            chapter_title = "未命名章节"
                    
                    if chapter_title:
                        
                        # 创建或更新章节记录
                        chapter, created = Chapter.objects.get_or_create(
                            novel=novel,
                            title=chapter_title,
                            defaults={
                                'format': parsed_data['chapter_info'].get('format', ''),
                                'word_count': 0
                            }
                        )
                        
                        # 如果章节已存在，更新格式信息
                        if not created and parsed_data['chapter_info'].get('format'):
                            chapter.format = parsed_data['chapter_info']['format']
                            chapter.save()
                        
                        # 保存角色信息
                        for char_info in parsed_data['characters']:
                            if char_info.get('name'):
                                character, char_created = Character.objects.get_or_create(
                                    name=char_info['name'],
                                    chapter=chapter,
                                    defaults={
                                        'gender': char_info.get('gender', '其他'),
                                        'age_group': char_info.get('age_group', '青年')
                                    }
                                )
                        
                        # 清除该章节的旧解说记录
                        Narration.objects.filter(chapter=chapter).delete()
                        
                        # 保存分镜解说信息
                        for narration_info in parsed_data['narrations']:
                            Narration.objects.create(
                                scene_number=narration_info['scene_number'],
                                featured_character=narration_info['featured_character'],
                                chapter=chapter,
                                narration=narration_info['narration'],
                                image_prompt=narration_info['image_prompt']
                            )
                        
                        logger.info(f"[DATABASE] 章节 '{chapter_title}' 的解说数据已保存到数据库")
                        logger.info(f"[DATABASE] 保存了 {len(parsed_data['characters'])} 个角色，{len(parsed_data['narrations'])} 个分镜")
                
                logger.info(f"[DATABASE] 小说 {novel_id} 所有解说数据已保存到数据库")
                
            except Exception as parse_error:
                logger.warning(f"解析解说文案时出错: {str(parse_error)}，但解说文案生成成功")
            
            # 更新进度
            self.update_state(
                state='PROGRESS',
                meta={'current': 95, 'total': 100, 'status': '更新任务状态...'}
            )
            
            # 重新获取novel对象并更新任务状态为完成
            novel = Novel.objects.get(id=novel_id)
            novel.task_status = 'script_completed'
            novel.task_message = '解说文案生成成功'
            novel.current_task_id = None
            novel.save()
            logger.info(f"[STATUS] 小说 {novel_id} 任务状态已更新为: script_completed")
            
            return {
                'status': 'success',
                'message': f'小说 {novel_id} 解说文案生成成功',
                'novel_id': novel_id,
                'output': result.stdout
            }
        else:
            logger.error(f"[SCRIPT ERROR] 小说 {novel_id} 解说文案生成失败")
            logger.error(f"[SCRIPT ERROR] 错误输出: {result.stderr}")
            logger.error(f"[SCRIPT ERROR] 返回码: {result.returncode}")
            
            # 重新获取novel对象并更新任务状态为失败
            novel = Novel.objects.get(id=novel_id)
            novel.task_status = 'script_failed'
            novel.task_message = f'解说文案生成失败: {result.stderr}'
            novel.current_task_id = None
            novel.save()
            logger.info(f"[STATUS] 小说 {novel_id} 任务状态已更新为: script_failed")
            
            return {
                'status': 'error',
                'message': f'解说文案生成失败: {result.stderr}',
                'novel_id': novel_id
            }
        
    except Exception as e:
        import traceback
        logger.error(f"[EXCEPTION] 小说 {novel_id} 解说文案生成异常: {str(e)}")
        logger.error(f"[EXCEPTION] 异常类型: {type(e).__name__}")
        logger.error(f"[EXCEPTION] 详细堆栈: {traceback.format_exc()}")
        
        # 更新任务状态为失败
        try:
            novel = Novel.objects.get(id=novel_id)
            novel.task_status = 'script_failed'
            novel.task_message = f'解说文案生成失败: {str(e)}'
            novel.current_task_id = None
            novel.save()
            logger.info(f"[STATUS] 小说 {novel_id} 异常状态已更新为: script_failed")
        except Exception as status_error:
            logger.error(f"[STATUS ERROR] 更新小说状态失败: {str(status_error)}")
        
        return {
            'status': 'error',
            'message': f'解说文案生成失败: {str(e)}',
            'novel_id': novel_id
        }


@shared_task(bind=True)
def validate_narration_async(self, novel_id, validation_params=None):
    """
    异步校验解说文案任务 - 集成 validate_narration.py 的功能
    """
    if validation_params is None:
        validation_params = {}
    
    logger.info(f"开始校验小说 {novel_id} 的解说文案，参数: {validation_params}")
    
    try:
        import subprocess
        import os
        from pathlib import Path
        
        # 更新任务状态
        self.update_state(
            state='PROGRESS',
            meta={
                'current': 0,
                'total': 100,
                'status': '正在初始化校验任务...'
            }
        )
        
        # 构建数据目录路径（使用项目根目录确保路径正确）
        data_dir = f"data/{novel_id:03d}"
        project_root = os.path.join(os.path.dirname(os.path.dirname(os.path.dirname(__file__))))
        full_data_dir = os.path.join(project_root, data_dir)
        
        # 确保数据目录存在（检查绝对路径，避免工作目录差异导致误报）
        if not os.path.exists(full_data_dir):
            raise Exception(f"数据目录 {data_dir} 不存在")
        
        # 更新任务状态
        self.update_state(
            state='PROGRESS',
            meta={
                'current': 10,
                'total': 100,
                'status': f'正在扫描目录 {data_dir}...'
            }
        )
        
        # 构建命令行参数（在项目根目录执行，传递相对路径 data_dir）
        cmd = ['python', 'validate_narration.py', data_dir]

        # 优先采用统一的 --auto-fix 开关，以满足页面映射到命令的需求
        # 如果前端未显式传入，默认启用 --auto-fix（更贴近用户期望的行为）
        auto_fix = validation_params.get('auto_fix', True)
        if auto_fix:
            cmd.append('--auto-fix')
        else:
            # 兼容旧参数：如果未启用统一开关，则根据旧参数分别添加
            if validation_params.get('auto_rewrite', False):
                cmd.append('--auto-rewrite')
            if validation_params.get('auto_fix_characters', False):
                cmd.append('--auto-fix-characters')
            if validation_params.get('auto_fix_tags', False):
                cmd.append('--auto-fix-tags')
            if validation_params.get('auto_fix_structure', False):
                cmd.append('--auto-fix-structure')

        logger.info(f"[VALIDATION CMD] 运行命令: {' '.join(cmd)} (cwd={project_root})")
        
        # 更新任务状态
        self.update_state(
            state='PROGRESS',
            meta={
                'current': 20,
                'total': 100,
                'status': '正在执行校验脚本...'
            }
        )
        
        # 调用 validate_narration.py 脚本
        result = subprocess.run(
            cmd,
            capture_output=True,
            text=True,
            cwd=project_root
        )
        
        # 更新任务状态
        self.update_state(
            state='PROGRESS',
            meta={
                'current': 80,
                'total': 100,
                'status': '正在处理校验结果...'
            }
        )
        
        if result.returncode == 0:
            # 更新任务状态
            self.update_state(
                state='PROGRESS',
                meta={
                    'current': 90,
                    'total': 100,
                    'status': '正在更新数据库...'
                }
            )
            
            # 校验成功后重新解析并保存解说数据到数据库
            try:
                from .utils import parse_narration_file
                from .models import Novel, Chapter, Character, Narration
                import glob
                
                novel = Novel.objects.get(id=novel_id)
                full_data_dir = os.path.join(os.path.dirname(os.path.dirname(os.path.dirname(__file__))), data_dir)
                
                # 查找生成的解说文案文件
                narration_files = glob.glob(os.path.join(full_data_dir, 'chapter_*/narration.txt'))
                
                for narration_file in narration_files:
                    # 读取解说文案内容
                    with open(narration_file, 'r', encoding='utf-8') as f:
                        narration_content = f.read()
                    
                    # 解析解说文案
                    parsed_data = parse_narration_file(narration_content)
                    
                    # 获取章节信息
                    chapter_info = parsed_data['chapter_info']
                    chapter_title = chapter_info.get('title')
                    
                    # 如果没有标题，尝试从章节号生成
                    if not chapter_title and chapter_info.get('chapter_number'):
                        chapter_title = f"第{chapter_info['chapter_number']}章"
                    
                    # 如果还是没有标题，从文件路径推断
                    if not chapter_title:
                        import re
                        match = re.search(r'chapter_(\d+)', narration_file)
                        if match:
                            chapter_title = f"第{match.group(1)}章"
                        else:
                            chapter_title = "未命名章节"
                    
                    if chapter_title:
                        # 创建或更新章节记录
                        chapter, created = Chapter.objects.get_or_create(
                            novel=novel,
                            title=chapter_title,
                            defaults={
                                'format': parsed_data['chapter_info'].get('format', ''),
                                'word_count': 0
                            }
                        )
                        
                        # 如果章节已存在，更新格式信息
                        if not created and parsed_data['chapter_info'].get('format'):
                            chapter.format = parsed_data['chapter_info']['format']
                            chapter.save()
                        
                        # 保存角色信息
                        for char_info in parsed_data['characters']:
                            if char_info.get('name'):
                                character, char_created = Character.objects.get_or_create(
                                    name=char_info['name'],
                                    defaults={
                                        'gender': char_info.get('gender', '其他'),
                                        'age_group': char_info.get('age_group', '青年')
                                    }
                                )
                                
                                # 关联角色到章节
                                character.chapter = chapter
                                character.save()
                        
                        # 清除该章节的旧解说记录
                        Narration.objects.filter(chapter=chapter).delete()
                        
                        # 保存分镜解说信息
                        for narration_info in parsed_data['narrations']:
                            Narration.objects.create(
                                scene_number=narration_info['scene_number'],
                                featured_character=narration_info['featured_character'],
                                chapter=chapter,
                                narration=narration_info['narration'],
                                image_prompt=narration_info['image_prompt']
                            )
                        
                        logger.info(f"章节 '{chapter_title}' 的校验后解说数据已保存到数据库")
                
                logger.info(f"小说 {novel_id} 校验后所有解说数据已保存到数据库")
                
                # 更新数据库中的小说状态
                novel.task_status = 'validation_completed'
                novel.task_message = '解说文案校验完成'
                novel.current_task_id = None
                novel.save()
                logger.info(f"小说 {novel_id} 数据库状态已更新")
                
            except Exception as db_error:
                logger.error(f"更新数据库失败: {str(db_error)}")
                # 即使数据库更新失败，也要更新小说状态
                try:
                    novel = Novel.objects.get(id=novel_id)
                    novel.task_status = 'validation_completed'
                    novel.task_message = f'解说文案校验完成，但数据库更新部分失败: {str(db_error)}'
                    novel.current_task_id = None
                    novel.save()
                except Exception as status_error:
                    logger.error(f"更新小说状态也失败: {str(status_error)}")
            
            # 更新任务状态
            self.update_state(
                state='PROGRESS',
                meta={
                    'current': 100,
                    'total': 100,
                    'status': '校验完成！'
                }
            )
            
            logger.info(f"小说 {novel_id} 解说文案校验完成")
            return {
                'status': 'success',
                'message': f'小说 {novel_id} 解说文案校验成功',
                'novel_id': novel_id,
                'output': result.stdout,
                'validation_params': validation_params
            }
        else:
            # 校验失败时也要更新数据库状态
            try:
                from .models import Novel
                novel = Novel.objects.get(id=novel_id)
                novel.task_status = 'validation_failed'
                novel.task_message = f'解说文案校验失败: {result.stderr}'
                novel.current_task_id = None
                novel.save()
                logger.info(f"小说 {novel_id} 校验失败状态已更新到数据库")
            except Exception as db_error:
                logger.error(f"更新数据库失败: {str(db_error)}")
            
            logger.error(f"小说 {novel_id} 解说文案校验失败: {result.stderr}")
            return {
                'status': 'error',
                'message': f'解说文案校验失败: {result.stderr}',
                'novel_id': novel_id,
                'validation_params': validation_params
            }
        
    except Exception as e:
        # 异常情况下也要更新数据库状态
        try:
            from .models import Novel
            novel = Novel.objects.get(id=novel_id)
            novel.task_status = 'validation_failed'
            novel.task_message = f'解说文案校验异常: {str(e)}'
            novel.current_task_id = None
            novel.save()
            logger.info(f"小说 {novel_id} 校验异常状态已更新到数据库")
        except Exception as db_error:
            logger.error(f"更新数据库失败: {str(db_error)}")
        
        logger.error(f"小说 {novel_id} 解说文案校验失败: {str(e)}")
        return {
            'status': 'error',
            'message': f'解说文案校验失败: {str(e)}',
            'novel_id': novel_id,
            'validation_params': validation_params
        }


@shared_task(bind=True)
def generate_character_image_async(self, task_id, character_id, chapter_id, image_style='realistic', image_quality='standard', image_count=1, custom_prompt=''):
    """
    异步生成角色图片任务
    
    Args:
        task_id (str): 任务ID
        character_id (int): 角色ID
        chapter_id (int): 章节ID
        image_style (str): 图片风格
        image_quality (str): 图片质量
        image_count (int): 生成图片数量
        custom_prompt (str): 自定义提示词
        
    Returns:
        dict: 处理结果
    """
    logger.info(f"开始执行角色图片生成任务: {task_id}")
    
    try:
        # 获取任务记录
        task = CharacterImageTask.objects.get(task_id=task_id)
        character = Character.objects.get(id=character_id)
        chapter = Chapter.objects.get(id=chapter_id)
        
        # 更新任务状态为进行中
        task.status = 'running'
        task.progress = 10
        task.log_message = '正在准备生成角色图片...'
        task.save()
        
        # 构建数据目录路径
        novel_id = chapter.novel.id
        data_dir = os.path.join(settings.BASE_DIR, '..', 'data', f'{novel_id:03d}')
        
        # 从章节标题中提取编号，如果失败则使用章节ID
        try:
            import re
            chapter_match = re.search(r'第(\d+)章', chapter.title)
            if chapter_match:
                chapter_num = int(chapter_match.group(1))
            else:
                chapter_num = chapter.id
        except:
            chapter_num = chapter.id
            
        chapter_dir = os.path.join(data_dir, f'chapter_{chapter_num:03d}')
        
        # 确保数据目录存在
        if not os.path.exists(data_dir):
            os.makedirs(data_dir, exist_ok=True)
        if not os.path.exists(chapter_dir):
            os.makedirs(chapter_dir, exist_ok=True)
        
        # 更新进度
        task.progress = 30
        task.log_message = f'正在为角色 "{character.name}" 生成图片...'
        task.save()
        
        # 构建命令参数
        cmd = [
            'python', 
            os.path.join(settings.BASE_DIR, '..', 'gen_single_character_image.py')
        ]
        
        # 设置环境变量传递参数
        env = os.environ.copy()
        
        # 调试日志：记录角色和章节信息
        logger.info(f"角色信息: ID={character.id}, 名称={character.name}, 性别={character.gender}, 年龄组={character.age_group}")
        logger.info(f"章节信息: ID={chapter.id}, 标题={chapter.title}, 章节号={chapter_num}")
        logger.info(f"数据目录: {data_dir}")
        logger.info(f"章节目录: {chapter_dir}")
        
        # 构建角色描述信息
        character_description = []
        if character.face_features:
            character_description.append(f"面部特征: {character.face_features}")
        if character.body_features:
            character_description.append(f"身材特征: {character.body_features}")
        if character.hair_style:
            character_description.append(f"发型: {character.hair_style}")
        if character.hair_color:
            character_description.append(f"发色: {character.hair_color}")
        if character.special_notes:
            character_description.append(f"特殊标记: {character.special_notes}")
        
        description_text = '; '.join(character_description) if character_description else ''
        
        env_vars = {
            'CHARACTER_ID': str(character_id),
            'CHARACTER_NAME': character.name,
            'CHARACTER_GENDER': character.gender,
            'CHARACTER_AGE_GROUP': character.age_group,
            'CHARACTER_DESCRIPTION': description_text,
            'IMAGE_STYLE': image_style,
            'IMAGE_QUALITY': image_quality,
            'IMAGE_COUNT': str(image_count),
            'CUSTOM_PROMPT': custom_prompt,
            'TASK_ID': task_id,
            'CHAPTER_PATH': chapter_dir,
            'NOVEL_ID': f'{novel_id:03d}',
            'CHAPTER_ID': f'chapter_{chapter_num:03d}'
        }
        
        # 调试日志：记录环境变量
        logger.info(f"设置环境变量: {env_vars}")
        
        env.update(env_vars)
        
        # 更新进度
        task.progress = 50
        task.log_message = '正在执行图片生成脚本...'
        task.save()
        
        # 执行生成脚本
        logger.info(f"执行命令: {' '.join(cmd)}")
        result = subprocess.run(
            cmd,
            cwd=os.path.join(settings.BASE_DIR, '..'),
            env=env,
            capture_output=True,
            text=True,
            timeout=600  # 10分钟超时
        )
        
        # 更新进度
        task.progress = 80
        task.log_message = '正在处理生成结果...'
        task.save()
        
        if result.returncode == 0:
            # 脚本执行成功
            logger.info(f"角色图片生成成功: {task_id}")
            
            # 解析生成的图片路径（假设脚本输出JSON格式的结果）
            try:
                output_lines = result.stdout.strip().split('\n')
                # 查找JSON输出行
                json_output = None
                for line in output_lines:
                    if line.strip().startswith('{') and 'generated_images' in line:
                        json_output = json.loads(line.strip())
                        break
                
                if json_output and 'generated_images' in json_output:
                    generated_images = json_output['generated_images']
                else:
                    # 如果没有JSON输出，尝试从Character_Images目录查找
                    character_images_dir = os.path.join(settings.BASE_DIR, '..', 'Character_Images')
                    generated_images = []
                    if os.path.exists(character_images_dir):
                        for file in os.listdir(character_images_dir):
                            if file.startswith(f'{character.name}_') and file.endswith(('.png', '.jpg', '.jpeg')):
                                generated_images.append(os.path.join(character_images_dir, file))
                
            except (json.JSONDecodeError, KeyError) as e:
                logger.warning(f"解析生成结果失败: {e}，使用默认路径")
                generated_images = []
            
            # 更新角色的image_path字段
            if generated_images:
                # 使用第一张生成的图片作为角色的主图片
                # 如果图片在章节images目录中，使用相对于项目根目录的路径
                image_path = generated_images[0]
                
                # 检查是否是章节images目录中的图片
                if 'data/' in image_path and '/images/' in image_path:
                    # 构建相对于项目根目录的路径
                    if image_path.startswith('/'):
                        # 绝对路径，转换为相对路径
                        project_root = os.path.dirname(os.path.dirname(settings.BASE_DIR))
                        if image_path.startswith(project_root):
                            image_path = os.path.relpath(image_path, project_root)
                    
                    # 确保路径格式正确
                    if not image_path.startswith('data/'):
                        # 如果路径不是以data/开头，尝试从路径中提取data部分
                        parts = image_path.split('/')
                        if 'data' in parts:
                            data_index = parts.index('data')
                            image_path = '/'.join(parts[data_index:])
                
                character.image_path = image_path
                character.save()
                logger.info(f"已更新角色 {character.name} 的图片路径: {image_path}")
            
            # 更新任务状态为成功
            task.status = 'success'
            task.progress = 100
            task.log_message = f'角色图片生成完成！共生成 {len(generated_images)} 张图片'
            task.generated_images = generated_images
            task.completed_at = timezone.now()
            task.save()
            
            return {
                'status': 'success',
                'task_id': task_id,
                'generated_images': generated_images,
                'message': '角色图片生成成功'
            }
        else:
            # 脚本执行失败
            error_msg = result.stderr or result.stdout or '未知错误'
            logger.error(f"角色图片生成失败: {task_id}, 错误: {error_msg}")
            
            task.status = 'failed'
            task.progress = 100
            task.error_message = error_msg
            task.log_message = f'角色图片生成失败: {error_msg}'
            task.save()
            
            return {
                'status': 'error',
                'task_id': task_id,
                'error': error_msg
            }
            
    except subprocess.TimeoutExpired:
        error_msg = '任务执行超时（超过10分钟）'
        logger.error(f"角色图片生成超时: {task_id}")
        
        task.status = 'failed'
        task.progress = 100
        task.error_message = error_msg
        task.log_message = error_msg
        task.save()
        
        return {
            'status': 'error',
            'task_id': task_id,
            'error': error_msg
        }


@shared_task(bind=True)
def gen_image_async_v2_task(self, novel_id, chapter_id):
    """
    使用gen_image_async_v2.py脚本为指定章节生成分镜图片
    
    Args:
        novel_id: 小说ID
        chapter_id: 章节ID
        
    Returns:
        dict: 任务执行结果
    """
    try:
        # 获取章节对象
        from .models import Chapter
        chapter = Chapter.objects.get(id=chapter_id)
        
        # 更新章节状态
        chapter.batch_image_status = 'processing'
        chapter.batch_image_task_id = self.request.id
        chapter.batch_image_progress = 10
        chapter.batch_image_message = '正在使用gen_image_async_v2生成分镜图片...'
        chapter.batch_image_started_at = timezone.now()
        chapter.save()
        
        logger.info(f"开始为章节 {chapter.id} 使用gen_image_async_v2生成分镜图片")
        
        # 使用工具函数获取正确的章节编号和路径
        from .utils import get_chapter_number_from_filesystem, get_chapter_directory_path
        
        chapter_number = get_chapter_number_from_filesystem(novel_id, chapter)
        if not chapter_number:
            error_msg = f"无法在文件系统中找到章节 {chapter.title} 的目录"
            logger.error(error_msg)
            
            chapter.batch_image_status = 'failed'
            chapter.batch_image_progress = 100
            chapter.batch_image_error = error_msg
            chapter.batch_image_message = '无法找到章节目录'
            chapter.batch_image_completed_at = timezone.now()
            chapter.save()
            
            return {
                'status': 'error',
                'novel_id': novel_id,
                'chapter_id': chapter_id,
                'error': error_msg
            }
        
        # 获取章节目录路径
        chapter_dir = get_chapter_directory_path(novel_id, chapter_number)
        if not chapter_dir or not os.path.exists(chapter_dir):
            error_msg = f"章节目录不存在: {chapter_dir}"
            logger.error(error_msg)
            
            chapter.batch_image_status = 'failed'
            chapter.batch_image_progress = 100
            chapter.batch_image_error = error_msg
            chapter.batch_image_message = '章节目录不存在'
            chapter.batch_image_completed_at = timezone.now()
            chapter.save()
            
            return {
                'status': 'error',
                'novel_id': novel_id,
                'chapter_id': chapter_id,
                'error': error_msg
            }
        
        # 检查gen_image_async_v2.py脚本是否存在
        gen_image_script = os.path.join(project_root, 'gen_image_async_v2.py')
        if not os.path.exists(gen_image_script):
            error_msg = f"gen_image_async_v2.py脚本不存在: {gen_image_script}"
            logger.error(error_msg)
            
            chapter.batch_image_status = 'failed'
            chapter.batch_image_progress = 100
            chapter.batch_image_error = error_msg
            chapter.batch_image_message = 'gen_image_async_v2.py脚本不存在'
            chapter.batch_image_completed_at = timezone.now()
            chapter.save()
            
            return {
                'status': 'error',
                'novel_id': novel_id,
                'chapter_id': chapter_id,
                'error': error_msg
            }
        
        # 更新进度
        chapter.batch_image_progress = 30
        chapter.batch_image_message = '正在执行gen_image_async_v2.py脚本...'
        chapter.save()
        
        # 执行gen_image_async_v2.py脚本，传入章节目录路径
        cmd = ['python', gen_image_script, chapter_dir]
        logger.info(f"执行命令: {' '.join(cmd)}")
        
        result = subprocess.run(
            cmd,
            cwd=project_root,
            capture_output=True,
            text=True,
            timeout=1800  # 30分钟超时
        )
        
        # 更新进度
        chapter.batch_image_progress = 80
        chapter.batch_image_message = '正在检查生成结果...'
        chapter.save()
        
        if result.returncode == 0:
            logger.info(f"gen_image_async_v2.py执行成功")
            logger.info(f"stdout: {result.stdout}")
            
            # 检查是否有图片生成
            images_dir = os.path.join(chapter_dir, 'images')
            if os.path.exists(images_dir):
                image_files = [f for f in os.listdir(images_dir) if f.lower().endswith(('.png', '.jpg', '.jpeg'))]
                image_count = len(image_files)
                
                chapter.batch_image_status = 'completed'
                chapter.batch_image_progress = 100
                chapter.batch_image_message = f'成功生成 {image_count} 张分镜图片'
                chapter.batch_image_completed_at = timezone.now()
                chapter.save()
                
                logger.info(f"章节 {chapter.id} 分镜图片生成完成，共生成 {image_count} 张图片")
                
                return {
                    'status': 'success',
                    'novel_id': novel_id,
                    'chapter_id': chapter_id,
                    'message': f'成功生成 {image_count} 张分镜图片',
                    'image_count': image_count
                }
            else:
                error_msg = "gen_image_async_v2.py执行成功但未找到生成的图片目录"
                logger.warning(error_msg)
                
                chapter.batch_image_status = 'completed'
                chapter.batch_image_progress = 100
                chapter.batch_image_message = '脚本执行完成，但未找到生成的图片'
                chapter.batch_image_completed_at = timezone.now()
                chapter.save()
                
                return {
                    'status': 'warning',
                    'novel_id': novel_id,
                    'chapter_id': chapter_id,
                    'message': error_msg
                }
        else:
            error_msg = f"gen_image_async_v2.py执行失败，返回码: {result.returncode}"
            logger.error(error_msg)
            logger.error(f"stdout: {result.stdout}")
            logger.error(f"stderr: {result.stderr}")
            
            chapter.batch_image_status = 'failed'
            chapter.batch_image_progress = 100
            chapter.batch_image_error = f"{error_msg}\nstderr: {result.stderr}"
            chapter.batch_image_message = 'gen_image_async_v2.py执行失败'
            chapter.batch_image_completed_at = timezone.now()
            chapter.save()
            
            return {
                'status': 'error',
                'novel_id': novel_id,
                'chapter_id': chapter_id,
                'error': error_msg,
                'stderr': result.stderr
            }
            
    except subprocess.TimeoutExpired:
        error_msg = "gen_image_async_v2.py执行超时"
        logger.error(error_msg)
        
        chapter.batch_image_status = 'failed'
        chapter.batch_image_progress = 100
        chapter.batch_image_error = error_msg
        chapter.batch_image_message = '脚本执行超时'
        chapter.batch_image_completed_at = timezone.now()
        chapter.save()
        
        return {
            'status': 'error',
            'novel_id': novel_id,
            'chapter_id': chapter_id,
            'error': error_msg
        }
        
    except Exception as e:
        error_msg = f"gen_image_async_v2任务执行异常: {str(e)}"
        logger.error(error_msg)
        
        try:
            chapter.batch_image_status = 'failed'
            chapter.batch_image_progress = 100
            chapter.batch_image_error = error_msg
            chapter.batch_image_message = '任务执行异常'
            chapter.batch_image_completed_at = timezone.now()
            chapter.save()
        except Exception as save_error:
            logger.error(f"保存章节状态失败: {save_error}")
        
        return {
            'status': 'error',
            'novel_id': novel_id,
            'chapter_id': chapter_id,
            'error': error_msg
        }


@shared_task(bind=True)
def batch_generate_chapter_images_async(self, novel_id, chapter_id):
    """
    批量生成章节分镜图片的Celery任务
    按章节生成21张分镜图片（7个分镜，每个分镜3张图片）
    
    Args:
        novel_id (int): 小说ID
        chapter_id (int): 章节ID
        
    Returns:
        dict: 处理结果
    """
    from .models import Chapter, Novel
    from django.utils import timezone
    import sys
    import os
    from pathlib import Path
    
    logger.info(f"开始执行章节分镜图片批量生成任务: novel_id={novel_id}, chapter_id={chapter_id}")
    
    try:
        # 获取章节对象
        chapter = Chapter.objects.get(id=chapter_id, novel_id=novel_id)
        novel = chapter.novel
        
        # 更新章节状态
        chapter.batch_image_status = 'processing'
        chapter.batch_image_task_id = self.request.id
        chapter.batch_image_progress = 10
        chapter.batch_image_message = '正在准备批量生成分镜图片...'
        chapter.batch_image_started_at = timezone.now()
        chapter.save()
        
        logger.info(f"开始为章节 {chapter.id} 批量生成分镜图片")
        
        # 导入gen_image_async模块 - 添加项目根目录到路径
        project_root = Path(__file__).resolve().parent.parent.parent
        if str(project_root) not in sys.path:
            sys.path.insert(0, str(project_root))
        
        try:
            from gen_image_async import generate_images_for_chapter
        except ImportError as e:
            error_msg = f"无法导入gen_image_async模块: {e}"
            logger.error(error_msg)
            
            chapter.batch_image_status = 'failed'
            chapter.batch_image_progress = 100
            chapter.batch_image_error = error_msg
            chapter.batch_image_message = '导入模块失败'
            chapter.batch_image_completed_at = timezone.now()
            chapter.save()
            
            return {
                'status': 'error',
                'novel_id': novel_id,
                'chapter_id': chapter_id,
                'error': error_msg
            }
        
        # 使用工具函数获取正确的章节编号
        from .utils import get_chapter_number_from_filesystem, get_chapter_directory_path
        
        chapter_number = get_chapter_number_from_filesystem(novel_id, chapter)
        if not chapter_number:
            error_msg = f"无法在文件系统中找到章节 {chapter.title} 的目录"
            logger.error(error_msg)
            
            chapter.batch_image_status = 'failed'
            chapter.batch_image_progress = 100
            chapter.batch_image_error = error_msg
            chapter.batch_image_message = '无法找到章节目录'
            chapter.batch_image_completed_at = timezone.now()
            chapter.save()
            
            return {
                'status': 'error',
                'novel_id': novel_id,
                'chapter_id': chapter_id,
                'error': error_msg
            }
        
        # 构建章节目录路径
        chapter_dir = get_chapter_directory_path(novel_id, chapter_number)
        
        if not os.path.exists(chapter_dir):
            error_msg = f"章节目录不存在: {chapter_dir}"
            logger.error(error_msg)
            
            chapter.batch_image_status = 'failed'
            chapter.batch_image_progress = 100
            chapter.batch_image_error = error_msg
            chapter.batch_image_message = '章节目录不存在'
            chapter.batch_image_completed_at = timezone.now()
            chapter.save()
            
            return {
                'status': 'error',
                'novel_id': novel_id,
                'chapter_id': chapter_id,
                'error': error_msg
            }
        
        # 更新进度
        chapter.batch_image_progress = 30
        chapter.batch_image_message = '正在生成分镜图片...'
        chapter.save()
        
        logger.info(f"章节目录: {chapter_dir}")
        
        # 调用gen_image_async的generate_images_for_chapter函数
        success = generate_images_for_chapter(chapter_dir)
        
        if success:
            # 生成成功
            chapter.batch_image_status = 'success'
            chapter.batch_image_progress = 100
            chapter.batch_image_message = '分镜图片生成完成'
            chapter.batch_image_completed_at = timezone.now()
            chapter.save()
            
            logger.info(f"章节 {chapter.id} 分镜图片生成成功")
            
            return {
                'status': 'success',
                'novel_id': novel_id,
                'chapter_id': chapter_id,
                'message': '分镜图片生成完成',
                'chapter_dir': chapter_dir
            }
        else:
            # 生成失败
            error_msg = "分镜图片生成失败"
            
            chapter.batch_image_status = 'failed'
            chapter.batch_image_progress = 100
            chapter.batch_image_error = error_msg
            chapter.batch_image_message = '分镜图片生成失败'
            chapter.batch_image_completed_at = timezone.now()
            chapter.save()
            
            logger.error(f"章节 {chapter.id} 分镜图片生成失败")
            
            return {
                'status': 'error',
                'novel_id': novel_id,
                'chapter_id': chapter_id,
                'error': error_msg
            }
            
    except Chapter.DoesNotExist:
        error_msg = f"章节不存在: novel_id={novel_id}, chapter_id={chapter_id}"
        logger.error(error_msg)
        return {
            'status': 'error',
            'novel_id': novel_id,
            'chapter_id': chapter_id,
            'error': error_msg
        }
    except Exception as e:
        error_msg = f"批量生成章节分镜图片时发生错误: {str(e)}"
        logger.error(error_msg)
        
        try:
            chapter = Chapter.objects.get(id=chapter_id, novel_id=novel_id)
            chapter.batch_image_status = 'failed'
            chapter.batch_image_progress = 100
            chapter.batch_image_error = error_msg
            chapter.batch_image_message = '任务执行异常'
            chapter.batch_image_completed_at = timezone.now()
            chapter.save()
        except:
            pass
        
        return {
            'status': 'error',
            'novel_id': novel_id,
            'chapter_id': chapter_id,
            'error': error_msg
        }


@shared_task(bind=True)
def batch_generate_all_videos_async(self, novel_id, chapter_id):
    """
    批量生成全部视频的异步任务 - 包含完整的视频制作流程
    
    这个任务会执行以下步骤：
    1. 生成音频 (gen_audio.py)
    2. 生成字幕 (gen_ass.py)
    3. 生成分镜图片 (gen_image_async.py)
    4. 校验分镜图片 (llm_narration_image.py)
    5. 生成分镜视频 (gen_video.py)
    6. 生成完整视频 (concat_finish_video.py)
    
    Args:
        novel_id (int): 小说ID
        chapter_id (int): 章节ID
        
    Returns:
        dict: 处理结果
    """
    logger.info(f"开始批量生成全部视频: 小说ID={novel_id}, 章节ID={chapter_id}")
    
    try:
        # 获取章节对象
        from .models import Chapter
        chapter = Chapter.objects.get(id=chapter_id)
        
        # 使用工具函数获取文件系统中的章节编号
        from .utils import get_chapter_number_from_filesystem
        chapter_number = get_chapter_number_from_filesystem(novel_id, chapter)
        
        if not chapter_number:
            raise Exception(f'无法在文件系统中找到章节 {chapter.title} 的目录')
        
        # 构建数据目录路径
        data_dir = f'data/{novel_id:03d}'
        
        # 检查数据目录是否存在
        project_root = settings.BASE_DIR.parent
        full_data_path = os.path.join(project_root, data_dir)
        
        if not os.path.exists(full_data_path):
            raise Exception(f'数据目录不存在: {full_data_path}')
        
        # 切换到项目根目录执行
        logger.info(f"执行目录: {project_root}")
        
        # 执行步骤列表 - 只执行最后一个步骤
        steps = [
            ('生成完整视频', 'concat_finish_video.py')
        ]
        
        results = []
        
        for step_name, script_name in steps:
            try:
                logger.info(f"执行步骤: {step_name} ({script_name})")
                
                # 构建脚本路径
                script_path = os.path.join(project_root, script_name)
                
                if not os.path.exists(script_path):
                    logger.warning(f"脚本文件不存在，跳过: {script_path}")
                    results.append({
                        'step': step_name,
                        'script': script_name,
                        'status': 'skipped',
                        'message': '脚本文件不存在'
                    })
                    continue
                
                # 执行脚本
                if script_name == 'concat_finish_video.py':
                    # 为concat_finish_video.py添加--chapter参数，只处理当前章节
                    cmd = ['python', script_path, data_dir, '--chapter', f'{int(chapter_number):03d}']
                else:
                    cmd = ['python', script_path, data_dir]
                logger.info(f"执行命令: {' '.join(cmd)}")
                
                # 设置超时时间（根据步骤调整）
                timeout = 3600  # 默认1小时
                if script_name in ['gen_image_async.py', 'gen_video.py', 'concat_finish_video.py']:
                    timeout = 7200  # 2小时
                
                result = subprocess.run(
                    cmd,
                    cwd=str(project_root),
                    capture_output=True,
                    text=True,
                    timeout=timeout
                )
                
                if result.returncode == 0:
                    logger.info(f"步骤完成: {step_name}")
                    results.append({
                        'step': step_name,
                        'script': script_name,
                        'status': 'success',
                        'message': '执行成功',
                        'output': result.stdout[:500] if result.stdout else ''  # 限制输出长度
                    })
                else:
                    logger.error(f"步骤失败: {step_name} - {result.stderr}")
                    results.append({
                        'step': step_name,
                        'script': script_name,
                        'status': 'error',
                        'message': f'执行失败: {result.stderr[:500]}',
                        'output': result.stdout[:500] if result.stdout else ''
                    })
                    
                    # 如果是关键步骤失败，可以选择继续或停止
                    if script_name in ['gen_audio.py', 'gen_ass.py']:
                        logger.warning(f"关键步骤失败，但继续执行后续步骤: {step_name}")
                    
            except subprocess.TimeoutExpired:
                logger.error(f"步骤超时: {step_name}")
                results.append({
                    'step': step_name,
                    'script': script_name,
                    'status': 'timeout',
                    'message': f'执行超时 (>{timeout}秒)'
                })
                
            except Exception as e:
                logger.error(f"步骤异常: {step_name} - {str(e)}")
                results.append({
                    'step': step_name,
                    'script': script_name,
                    'status': 'exception',
                    'message': f'执行异常: {str(e)}'
                })
        
        # 统计结果
        success_count = sum(1 for r in results if r['status'] == 'success')
        total_count = len(results)
        
        logger.info(f"批量生成全部视频完成: 小说ID={novel_id}, 章节ID={chapter_id}, 成功步骤: {success_count}/{total_count}")
        
        return {
            'status': 'completed',
            'novel_id': novel_id,
            'chapter_id': chapter_id,
            'chapter_number': chapter_number,
            'message': f'批量生成全部视频完成，成功步骤: {success_count}/{total_count}',
            'results': results,
            'success_count': success_count,
            'total_count': total_count
        }
        
    except Chapter.DoesNotExist:
        logger.error(f"章节不存在: chapter_id={chapter_id}")
        return {
            'status': 'error',
            'novel_id': novel_id,
            'chapter_id': chapter_id,
            'message': f'章节不存在: {chapter_id}'
        }
        
    except Exception as e:
        logger.error(f"批量生成全部视频失败: {str(e)}")
        return {
            'status': 'error',
            'novel_id': novel_id,
            'chapter_id': chapter_id,
            'message': f'批量生成全部视频失败: {str(e)}'
        }


@shared_task(bind=True)
def generate_first_video_async(self, novel_id, chapter_id):
    """
    异步执行gen_first_video_async.py脚本生成首视频
    
    Args:
        novel_id (int): 小说ID
        chapter_id (int): 章节ID
        
    Returns:
        dict: 处理结果
    """
    logger.info(f"开始异步生成首视频: 小说ID={novel_id}, 章节ID={chapter_id}")
    
    try:
        # 获取章节对象
        from .models import Chapter
        chapter = Chapter.objects.get(id=chapter_id)
        
        # 使用工具函数获取文件系统中的章节编号
        from .utils import get_chapter_number_from_filesystem
        chapter_number = get_chapter_number_from_filesystem(novel_id, chapter)
        
        if not chapter_number:
            raise Exception(f'无法在文件系统中找到章节 {chapter.title} 的目录')
        
        # 构建数据目录路径（不包含章节）
        data_dir = f'data/{novel_id:03d}'
        chapter_name = f'chapter_{chapter_number}'
        
        # 检查数据目录是否存在
        project_root = settings.BASE_DIR.parent
        full_data_path = os.path.join(project_root, data_dir)
        full_chapter_path = os.path.join(full_data_path, chapter_name)
        
        if not os.path.exists(full_data_path):
            raise Exception(f'数据目录不存在: {full_data_path}')
            
        if not os.path.exists(full_chapter_path):
            raise Exception(f'章节目录不存在: {full_chapter_path}')
        
        # 构建脚本路径
        script_path = os.path.join(settings.BASE_DIR.parent, 'gen_first_video_async.py')
        
        if not os.path.exists(script_path):
            raise Exception(f'脚本文件不存在: {script_path}')
        
        # 执行gen_first_video_async.py脚本，针对特定章节
        # 传递数据目录和章节名称
        cmd = ['python', script_path, data_dir, '--chapter', chapter_name]
        
        logger.info(f"执行命令: {' '.join(cmd)}")
        
        # 切换到项目根目录执行
        project_root = settings.BASE_DIR.parent
        
        logger.info(f"执行目录: {project_root}")
        logger.info(f"完整命令: {' '.join(cmd)}")
        
        result = subprocess.run(
            cmd,
            cwd=str(project_root),  # 确保路径是字符串
            capture_output=True,
            text=True,
            timeout=3600  # 1小时超时
        )
        
        if result.returncode == 0:
            logger.info(f"首视频生成完成: 小说ID={novel_id}, 章节ID={chapter_id}")
            return {
                'status': 'success',
                'novel_id': novel_id,
                'chapter_id': chapter_id,
                'message': '首视频生成成功',
                'output': result.stdout
            }
        else:
            error_msg = f"首视频生成失败: {result.stderr}"
            logger.error(error_msg)
            return {
                'status': 'error',
                'novel_id': novel_id,
                'chapter_id': chapter_id,
                'error': error_msg,
                'output': result.stdout
            }
            
    except subprocess.TimeoutExpired:
        error_msg = f"首视频生成超时: 小说ID={novel_id}, 章节ID={chapter_id}"
        logger.error(error_msg)
        return {
            'status': 'error',
            'novel_id': novel_id,
            'chapter_id': chapter_id,
            'error': error_msg
        }
        
    except Exception as e:
        error_msg = f"首视频生成异常: {str(e)}"
        logger.error(f"首视频生成异常: 小说ID={novel_id}, 章节ID={chapter_id}, 错误: {error_msg}")
        return {
            'status': 'error',
            'novel_id': novel_id,
            'chapter_id': chapter_id,
            'error': error_msg
        }


@shared_task(bind=True)
def scan_and_process_async_tasks(self, data_dir='data'):
    """
    定时扫描和处理所有异步任务
    
    这是一个Celery Beat定时任务，用于：
    1. 扫描所有数据目录下的异步任务文件
    2. 检查任务状态并下载完成的图片/视频
    3. 移动已完成的任务到done_tasks目录
    4. 记录处理统计信息
    
    Args:
        data_dir (str): 数据根目录路径，默认为'data'
        
    Returns:
        dict: 处理结果统计
    """
    logger.info(f"开始执行定时异步任务扫描: 数据目录={data_dir}")
    
    try:
        # 检查是否成功导入了check_async_tasks模块
        if process_all_data_directories is None:
            error_msg = "check_async_tasks模块未正确导入，无法执行定时任务"
            logger.error(error_msg)
            return {
                'success': False,
                'error': error_msg,
                'stats': {}
            }
        
        # 切换到项目根目录
        original_cwd = os.getcwd()
        os.chdir(project_root)
        
        try:
            # 调用check_async_tasks的主要处理函数
            stats = process_all_data_directories(data_dir)
            
            logger.info(f"异步任务扫描完成: {stats}")
            
            return {
                'success': True,
                'message': '异步任务扫描处理完成',
                'stats': stats,
                'data_dir': data_dir,
                'processed_at': timezone.now().isoformat()
            }
            
        finally:
            # 恢复原始工作目录
            os.chdir(original_cwd)
            
    except Exception as e:
        error_msg = f"定时异步任务扫描失败: {str(e)}"
        logger.error(error_msg, exc_info=True)
        return {
            'success': False,
            'error': error_msg,
            'stats': {},
            'data_dir': data_dir,
            'processed_at': timezone.now().isoformat()
        }


@shared_task(bind=True)
def scan_specific_async_tasks(self, tasks_dir='async_tasks'):
    """
    扫描指定目录的异步任务
    
    这是一个Celery任务，用于扫描指定的async_tasks目录：
    1. 检查所有任务文件的状态
    2. 下载完成的图片/视频
    3. 移动已完成的任务
    
    Args:
        tasks_dir (str): 任务目录路径，默认为'async_tasks'
        
    Returns:
        dict: 处理结果统计
    """
    logger.info(f"开始扫描指定异步任务目录: {tasks_dir}")
    
    try:
        # 检查是否成功导入了check_async_tasks模块
        if check_all_tasks is None:
            error_msg = "check_async_tasks模块未正确导入，无法执行任务"
            logger.error(error_msg)
            return {
                'success': False,
                'error': error_msg,
                'stats': {}
            }
        
        # 切换到项目根目录
        original_cwd = os.getcwd()
        os.chdir(project_root)
        
        try:
            # 检查任务目录是否存在
            if not os.path.exists(tasks_dir):
                logger.warning(f"任务目录不存在: {tasks_dir}")
                return {
                    'success': True,
                    'message': f'任务目录不存在: {tasks_dir}',
                    'stats': {
                        'total': 0,
                        'completed': 0,
                        'processing': 0,
                        'pending': 0,
                        'failed': 0
                    }
                }
            
            # 调用check_async_tasks的检查函数
            stats = check_all_tasks(tasks_dir)
            
            logger.info(f"异步任务目录扫描完成: {stats}")
            
            return {
                'success': True,
                'message': '异步任务目录扫描完成',
                'stats': stats,
                'tasks_dir': tasks_dir,
                'processed_at': timezone.now().isoformat()
            }
            
        finally:
            # 恢复原始工作目录
            os.chdir(original_cwd)
            
    except Exception as e:
        error_msg = f"异步任务目录扫描失败: {str(e)}"
        logger.error(error_msg, exc_info=True)
        return {
            'success': False,
            'error': error_msg,
            'stats': {},
            'tasks_dir': tasks_dir,
            'processed_at': timezone.now().isoformat()
        }



@shared_task(bind=True)
def scan_database_celery_tasks(self):
    """
    扫描数据库中保存的Celery任务ID并更新任务状态
    
    这是一个Celery Beat定时任务，用于：
    1. 扫描Chapter表中的batch_image_task_id字段
    2. 扫描CharacterImageTask表中的任务
    3. 扫描Narration表中的celery_task_id字段
    4. 检查这些Celery任务的状态并更新数据库
    
    Returns:
        dict: 扫描结果统计
    """
    logger.info("开始执行数据库Celery任务扫描")
    
    try:
        # 检查是否成功导入了celery_task_scanner模块
        if scan_all_celery_tasks is None:
            error_msg = "celery_task_scanner模块未正确导入，无法执行任务扫描"
            logger.error(error_msg)
            return {
                'success': False,
                'error': error_msg,
                'stats': {}
            }
        
        # 执行扫描
        stats = scan_all_celery_tasks()
        
        logger.info(f"数据库Celery任务扫描完成: {stats}")
        
        return {
            'success': True,
            'message': '数据库Celery任务扫描完成',
            'stats': stats,
            'total_updated': stats.get('total_updated', 0)
        }
        
    except Exception as e:
        logger.error(f"数据库Celery任务扫描失败: {str(e)}")
        return {
            'success': False,
            'error': str(e),
            'stats': {}
        }



@shared_task(bind=True)
def concat_narration_video_async(self, novel_id, chapter_id):
    """
    异步执行concat_narration_video.py脚本生成主视频
    
    Args:
        novel_id (int): 小说ID
        chapter_id (int): 章节ID
        
    Returns:
        dict: 处理结果
    """
    logger.info(f"开始异步生成主视频: 小说ID={novel_id}, 章节ID={chapter_id}")
    
    try:
        # 获取章节对象
        from .models import Chapter
        chapter = Chapter.objects.get(id=chapter_id)
        
        # 使用工具函数获取文件系统中的章节编号
        from .utils import get_chapter_number_from_filesystem
        chapter_number = get_chapter_number_from_filesystem(novel_id, chapter)
        
        if not chapter_number:
            raise Exception(f'无法在文件系统中找到章节 {chapter.title} 的目录')
        
        # 构建数据目录路径
        data_dir = f'data/{novel_id:03d}'
        
        # 构建脚本路径
        script_path = os.path.join(settings.BASE_DIR.parent, 'concat_narration_video.py')
        
        if not os.path.exists(script_path):
            raise Exception(f'脚本文件不存在: {script_path}')
        
        # 执行concat_narration_video.py脚本
        cmd = ['python', script_path, data_dir]
        
        logger.info(f"执行命令: {' '.join(cmd)}")
        
        # 切换到项目根目录执行
        project_root = settings.BASE_DIR.parent
        
        result = subprocess.run(
            cmd,
            cwd=project_root,
            capture_output=True,
            text=True,
            timeout=3600  # 1小时超时
        )
        
        if result.returncode == 0:
            logger.info(f"主视频生成成功: {result.stdout}")
            
            # 主视频生成成功后，自动执行concat_finish_video.py脚本
            try:
                concat_finish_script = os.path.join(settings.BASE_DIR.parent, 'concat_finish_video.py')
                
                if os.path.exists(concat_finish_script):
                    logger.info(f"开始执行concat_finish_video.py脚本: 小说ID={novel_id}, 章节ID={chapter_id}")
                    
                    # 执行concat_finish_video.py脚本，添加--chapter参数只处理当前章节
                    finish_cmd = ['python', concat_finish_script, data_dir, '--chapter', f'{int(chapter_number):03d}']
                    
                    logger.info(f"执行命令: {' '.join(finish_cmd)}")
                    
                    finish_result = subprocess.run(
                        finish_cmd,
                        cwd=project_root,
                        capture_output=True,
                        text=True,
                        timeout=1800  # 30分钟超时
                    )
                    
                    if finish_result.returncode == 0:
                        logger.info(f"完整视频生成成功: {finish_result.stdout}")
                        return {
                            'status': 'success',
                            'novel_id': novel_id,
                            'chapter_id': chapter_id,
                            'chapter_number': chapter_number,
                            'message': '完整视频生成完成（包含片尾）',
                            'output': result.stdout + '\n\n--- concat_finish_video.py 输出 ---\n' + finish_result.stdout
                        }
                    else:
                        logger.error(f"完整视频生成失败: {finish_result.stderr}")
                        return {
                            'status': 'partial_success',
                            'novel_id': novel_id,
                            'chapter_id': chapter_id,
                            'chapter_number': chapter_number,
                            'message': '主视频生成完成，但片尾视频生成失败',
                            'output': result.stdout,
                            'finish_error': finish_result.stderr
                        }
                else:
                    logger.warning(f"concat_finish_video.py脚本不存在: {concat_finish_script}")
                    return {
                        'status': 'partial_success',
                        'novel_id': novel_id,
                        'chapter_id': chapter_id,
                        'chapter_number': chapter_number,
                        'message': '主视频生成完成，但concat_finish_video.py脚本不存在',
                        'output': result.stdout
                    }
                    
            except subprocess.TimeoutExpired:
                logger.error(f"完整视频生成超时: 小说ID={novel_id}, 章节ID={chapter_id}")
                return {
                    'status': 'partial_success',
                    'novel_id': novel_id,
                    'chapter_id': chapter_id,
                    'chapter_number': chapter_number,
                    'message': '主视频生成完成，但片尾视频生成超时',
                    'output': result.stdout
                }
            except Exception as e:
                logger.error(f"执行concat_finish_video.py失败: {str(e)}")
                return {
                    'status': 'partial_success',
                    'novel_id': novel_id,
                    'chapter_id': chapter_id,
                    'chapter_number': chapter_number,
                    'message': f'主视频生成完成，但片尾视频生成失败: {str(e)}',
                    'output': result.stdout
                }
        else:
            logger.error(f"主视频生成失败: {result.stderr}")
            return {
                'status': 'error',
                'novel_id': novel_id,
                'chapter_id': chapter_id,
                'message': f'主视频生成失败: {result.stderr}',
                'output': result.stdout
            }
        
    except subprocess.TimeoutExpired:
        logger.error(f"主视频生成超时: 小说ID={novel_id}, 章节ID={chapter_id}")
        return {
            'status': 'error',
            'novel_id': novel_id,
            'chapter_id': chapter_id,
            'message': '主视频生成超时（超过1小时）'
        }
    except Exception as e:
        logger.error(f"主视频生成失败: {str(e)}")
        return {
            'status': 'error',
            'novel_id': novel_id,
            'chapter_id': chapter_id,
            'message': f'主视频生成失败: {str(e)}'
        }


@shared_task(bind=True, rate_limit='2/s')
def generate_narration_images_async(self, narration_id):
    """
    异步生成解说分镜图片任务 - 参考generate_character_image_async的实现模式
    使用火山引擎同步转异步API，包含完整的状态管理和进度跟踪
    
    Args:
        narration_id (int): 解说ID
        
    Returns:
        dict: 处理结果
    """
    from .models import Narration
    from django.utils import timezone
    import sys
    import os
    
    logger.info(f"开始执行解说分镜图片生成任务: {narration_id}")
    
    try:
        # 获取解说对象
        narration = Narration.objects.get(id=narration_id)
        chapter = narration.chapter
        
        # 更新任务状态为进行中
        narration.image_task_status = 'processing'
        narration.image_task_progress = 10
        narration.image_task_message = '正在准备生成解说分镜图片...'
        narration.image_task_started_at = timezone.now()
        narration.celery_task_id = self.request.id
        narration.save()
        
        logger.info(f"开始为解说 {narration.scene_number} 生成分镜图片")
        
        # 导入配置文件 - 添加项目根目录到路径
        project_root = os.path.join(os.path.dirname(os.path.dirname(os.path.dirname(__file__))))
        if project_root not in sys.path:
            sys.path.insert(0, project_root)
        
        try:
            from config.config import IMAGE_TWO_CONFIG, build_scene_prompt
        except ImportError:
            error_msg = "无法导入 IMAGE_TWO_CONFIG 配置文件"
            logger.error(error_msg)
            
            # 更新任务状态为失败
            narration.image_task_status = 'failed'
            narration.image_task_progress = 100
            narration.image_task_error = error_msg
            narration.image_task_message = f'配置文件导入失败: {error_msg}'
            narration.save()
            
            return {
                'status': 'error',
                'narration_id': narration_id,
                'error': error_msg
            }
        
        # 更新进度
        narration.image_task_progress = 30
        narration.image_task_message = f'正在为解说 "{narration.scene_number}" 生成分镜图片...'
        narration.save()
        
        # 初始化火山引擎视觉服务
        visual_service = VisualService()
        
        # 使用配置文件中的AK和SK
        visual_service.set_ak(IMAGE_TWO_CONFIG['access_key'])
        visual_service.set_sk(IMAGE_TWO_CONFIG['secret_key'])
        
        # 构建完整的prompt - 使用配置文件中的函数
        full_prompt = build_scene_prompt(narration.narration)
        
        logger.info(f"构建的完整prompt: {full_prompt[:100]}...")
        
        # 更新进度
        narration.image_task_progress = 50
        narration.image_task_message = '正在提交火山引擎图片生成任务...'
        narration.save()
        
        # 构建请求参数 - 使用与gen_image_async.py完全相同的配置
        form = {
            "req_key": "high_aes_ip_v20",  # 使用与gen_image_async.py相同的req_key
            "prompt": full_prompt,
            "llm_seed": -1,
            "seed": 10,
            "scale": 3.5,
            "ddim_steps": IMAGE_TWO_CONFIG['ddim_steps'],
            "width": IMAGE_TWO_CONFIG['default_width'],
            "height": IMAGE_TWO_CONFIG['default_height'],
            "use_pre_llm": IMAGE_TWO_CONFIG['use_pre_llm'],
            "use_sr": IMAGE_TWO_CONFIG['use_sr'],
            "return_url": IMAGE_TWO_CONFIG['return_url'],
            "negative_prompt": IMAGE_TWO_CONFIG['negative_prompt'],
            "ref_ip_weight": 0,
            "ref_id_weight": 0.6,
            "logo_info": {
                "add_logo": False,
                "position": 0,
                "language": 0,
                "opacity": 0.3,
                "logo_text_content": "这里是明水印内容"
            }
        }
        
        logger.info(f"提交火山引擎图片生成任务，解说内容: {narration.narration[:50]}...")
        
        # 调用同步转异步提交任务接口
        resp = visual_service.cv_sync2async_submit_task(form)
        
        # 添加详细的响应日志
        logger.info(f"火山引擎API响应: {resp}")
        
        if resp.get('ResponseMetadata', {}).get('Error'):
            error_msg = f"火山引擎API调用失败: {resp['ResponseMetadata']['Error']}"
            logger.error(error_msg)
            
            # 检查是否是API限制错误(50429)，如果是则重试
            if '50429' in str(resp) or 'API Limit' in str(resp):
                if self.request.retries < 3:  # 最多重试3次
                    retry_delay = (self.request.retries + 1) * 30  # 递增延迟：30s, 60s, 90s
                    logger.info(f"遇到API限制错误，{retry_delay}秒后重试 (第{self.request.retries + 1}/3次)")
                    
                    # 更新重试状态
                    narration.image_task_message = f'遇到API限制，{retry_delay}秒后重试 (第{self.request.retries + 1}/3次)'
                    narration.save()
                    
                    raise self.retry(countdown=retry_delay, max_retries=3)
            
            # 更新任务状态为失败
            narration.image_task_status = 'failed'
            narration.image_task_progress = 100
            narration.image_task_error = error_msg
            narration.image_task_message = f'火山引擎API调用失败: {error_msg}'
            narration.save()
            
            return {
                'status': 'error',
                'narration_id': narration_id,
                'error': error_msg
            }
        
        # 获取任务ID - 修复响应结构解析
        task_id = resp.get('data', {}).get('task_id') or resp.get('Result', {}).get('task_id')
        
        if not task_id:
            error_msg = f"未获取到火山引擎任务ID，响应结构: {resp}"
            logger.error(error_msg)
            
            # 更新任务状态为失败
            narration.image_task_status = 'failed'
            narration.image_task_progress = 100
            narration.image_task_error = error_msg
            narration.image_task_message = f'未获取到火山引擎任务ID'
            narration.save()
            
            return {
                'status': 'error',
                'narration_id': narration_id,
                'error': error_msg,
                'response': resp
            }
        
        # 更新进度和火山引擎任务ID
        narration.image_task_progress = 80
        narration.image_task_message = '火山引擎任务已提交，正在启动监控任务...'
        narration.volcengine_task_id = task_id
        narration.save()
        
        logger.info(f"解说 {narration.scene_number} 图片生成任务已提交，任务ID: {task_id}")
        
        # 自动启动监控和下载任务
        logger.info(f"启动解说 {narration.scene_number} 的监控和下载任务")
        monitor_task = monitor_and_download_narration_images.delay(
            narration_id=narration_id,
            volcengine_task_id=task_id,
            max_retries=30,  # 最多重试30次（30分钟）
            retry_interval=60  # 每60秒重试一次
        )
        
        # 更新任务状态为等待监控
        narration.image_task_status = 'pending'
        narration.image_task_progress = 100
        narration.image_task_message = f'解说 {narration.scene_number} 分镜图片生成任务已提交到火山引擎，监控任务已启动'
        narration.save()
        
        return {
            'status': 'success',
            'narration_id': narration_id,
            'task_id': task_id,
            'celery_task_id': monitor_task.id,
            'message': f'解说 {narration.scene_number} 分镜图片生成任务已提交到火山引擎，监控任务已启动',
            'volcengine_response': resp
        }
            
    except Exception as e:
        error_msg = f"解说 {narration_id} 分镜图片生成异常: {str(e)}"
        logger.error(error_msg)
        
        # 更新任务状态为失败
        try:
            narration = Narration.objects.get(id=narration_id)
            narration.image_task_status = 'failed'
            narration.image_task_progress = 100
            narration.image_task_error = error_msg
            narration.image_task_message = f'任务执行异常: {str(e)}'
            narration.save()
        except:
            pass
        
        return {
            'status': 'error',
            'narration_id': narration_id,
            'error': error_msg
        }


@shared_task(bind=True)
def get_volcengine_image_result(self, narration_id, volcengine_task_id):
    """
    查询火山引擎图片生成任务结果
    
    Args:
        narration_id (int): 解说ID
        volcengine_task_id (str): 火山引擎任务ID
        
    Returns:
        dict: 处理结果
    """
    from .models import Narration
    
    try:
        # 获取解说对象
        narration = Narration.objects.get(id=narration_id)
        
        logger.info(f"查询解说 {narration.scene_number} 的火山引擎图片生成结果，任务ID: {volcengine_task_id}")
        
        # 初始化火山引擎视觉服务
        visual_service = VisualService()
        
        # 设置AK和SK
        ak = getattr(settings, 'VOLCENGINE_ACCESS_KEY', '')
        sk = getattr(settings, 'VOLCENGINE_SECRET_KEY', '')
        
        if not ak or not sk:
            error_msg = "火山引擎AK或SK未配置"
            logger.error(error_msg)
            # 更新任务状态为失败
            narration.image_task_status = 'failed'
            narration.image_task_error = error_msg
            narration.image_task_message = error_msg
            narration.save()
            return {
                'status': 'error',
                'narration_id': narration_id,
                'error': error_msg
            }
        
        visual_service.set_ak(ak)
        visual_service.set_sk(sk)
        
        # 构建查询请求参数
        form = {
            "req_key": "img2img_anime",
            "task_id": volcengine_task_id,
            "req_json": "{}"
        }
        
        # 调用同步转异步查询结果接口
        resp = visual_service.cv_sync2async_get_result(form)
        
        if resp.get('ResponseMetadata', {}).get('Error'):
            error_msg = f"火山引擎查询API调用失败: {resp['ResponseMetadata']['Error']}"
            logger.error(error_msg)
            return {
                'status': 'error',
                'narration_id': narration_id,
                'error': error_msg
            }
        
        # 检查任务状态
        result = resp.get('Result', {})
        task_status = result.get('status')
        
        if task_status == 'done':
            # 任务完成，获取图片URL
            data = result.get('data', {})
            image_urls = data.get('image_urls', [])
            
            if image_urls:
                logger.info(f"解说 {narration.scene_number} 图片生成完成，获取到 {len(image_urls)} 张图片")
                return {
                    'status': 'completed',
                    'narration_id': narration_id,
                    'image_urls': image_urls,
                    'message': f'解说 {narration.scene_number} 分镜图片生成完成',
                    'volcengine_response': resp
                }
            else:
                error_msg = "任务完成但未获取到图片URL"
                logger.error(error_msg)
                return {
                    'status': 'error',
                    'narration_id': narration_id,
                    'error': error_msg,
                    'volcengine_response': resp
                }
        elif task_status == 'running':
            logger.info(f"解说 {narration.scene_number} 图片生成任务仍在进行中")
            return {
                'status': 'running',
                'narration_id': narration_id,
                'message': f'解说 {narration.scene_number} 分镜图片生成中...',
                'volcengine_response': resp
            }
        elif task_status == 'failed':
            error_msg = f"火山引擎任务失败: {result.get('message', '未知错误')}"
            logger.error(error_msg)
            return {
                'status': 'failed',
                'narration_id': narration_id,
                'error': error_msg,
                'volcengine_response': resp
            }
        else:
            error_msg = f"未知任务状态: {task_status}"
            logger.error(error_msg)
            return {
                'status': 'error',
                'narration_id': narration_id,
                'error': error_msg,
                'volcengine_response': resp
            }
            
    except Exception as e:
        error_msg = f"查询解说 {narration_id} 图片生成结果异常: {str(e)}"
        logger.error(error_msg)
        return {
            'status': 'error',
            'narration_id': narration_id,
            'error': error_msg
        }


@shared_task(bind=True)
def monitor_and_download_narration_images(self, narration_id, volcengine_task_id, max_retries=30, retry_interval=60):
    """
    监控火山引擎图片生成任务并自动下载完成的图片
    参考 check_async_tasks.py 的监控机制
    
    Args:
        narration_id (int): 解说ID
        volcengine_task_id (str): 火山引擎任务ID
        max_retries (int): 最大重试次数，默认30次（30分钟）
        retry_interval (int): 重试间隔（秒），默认60秒
        
    Returns:
        dict: 处理结果
    """
    import base64
    import urllib.request
    from .models import Narration
    
    try:
        # 获取解说对象
        narration = Narration.objects.get(id=narration_id)
        
        # 更新监控任务状态为运行中
        narration.image_task_status = 'running'
        narration.image_task_progress = 10  # 开始监控
        narration.image_task_message = f"开始监控火山引擎任务 {volcengine_task_id}"
        narration.save()
        
        logger.info(f"开始监控解说 {narration.scene_number} 的火山引擎图片生成任务，任务ID: {volcengine_task_id}")
        
        # 如果是第一次执行，等待30秒让火山引擎任务初始化
        if self.request.retries == 0:
            logger.info(f"首次监控，等待30秒让火山引擎任务初始化...")
            time.sleep(30)
        
        # 初始化火山引擎视觉服务
        visual_service = VisualService()
        
        # 设置AK和SK
        ak = getattr(settings, 'VOLCENGINE_ACCESS_KEY', '')
        sk = getattr(settings, 'VOLCENGINE_SECRET_KEY', '')
        
        if not ak or not sk:
            error_msg = "火山引擎AK或SK未配置"
            logger.error(error_msg)
            return {
                'status': 'error',
                'narration_id': narration_id,
                'error': error_msg
            }
        
        visual_service.set_ak(ak)
        visual_service.set_sk(sk)
        
        # 构建查询请求参数
        form = {
            "req_key": "high_aes_ip_v20",  # 使用与生成任务一致的req_key
            "task_id": volcengine_task_id
        }
        
        # 查询任务状态
        resp = visual_service.cv_sync2async_get_result(form)
        
        if resp.get('ResponseMetadata', {}).get('Error'):
            error_msg = f"火山引擎查询API调用失败: {resp['ResponseMetadata']['Error']}"
            logger.error(error_msg)
            
            # 检查是否是API限制错误(50429)，如果是则使用更短的重试间隔
            if '50429' in str(resp) or 'API Limit' in str(resp):
                if self.request.retries < 5:  # API限制错误最多重试5次
                    api_retry_delay = (self.request.retries + 1) * 30  # 30s, 60s, 90s, 120s, 150s
                    logger.info(f"遇到API限制错误，{api_retry_delay}秒后重试 (第{self.request.retries + 1}/5次)")
                    
                    # 更新重试状态
                    narration.image_task_progress = 20 + (self.request.retries * 5)
                    narration.image_task_message = f'遇到API限制，{api_retry_delay}秒后重试 (第{self.request.retries + 1}/5次)'
                    narration.save()
                    
                    raise self.retry(countdown=api_retry_delay, max_retries=5)
            
            # 如果还有重试次数，延迟重试
            if self.request.retries < max_retries:
                # 更新重试状态
                narration.image_task_progress = 20 + (self.request.retries * 5)  # 递增进度
                narration.image_task_message = f"查询失败，{retry_interval}秒后重试 (第{self.request.retries + 1}/{max_retries}次)"
                narration.save()
                logger.info(f"查询失败，{retry_interval}秒后重试 (第{self.request.retries + 1}/{max_retries}次)")
                raise self.retry(countdown=retry_interval, max_retries=max_retries)
            
            # 最终失败
            narration.image_task_status = 'failed'
            narration.image_task_error = error_msg
            narration.image_task_message = error_msg
            narration.save()
            return {
                'status': 'error',
                'narration_id': narration_id,
                'error': error_msg
            }
        
        # 检查任务状态
        result = resp.get('data', {})  # 使用data字段而不是Result
        task_status = result.get('status')
        
        logger.info(f"解说 {narration.scene_number} 任务状态: {task_status}")
        
        if task_status == 'done':
            # 任务完成，下载图片
            binary_data_base64_list = result.get('binary_data_base64', [])
            
            if binary_data_base64_list:
                logger.info(f"解说 {narration.scene_number} 图片生成完成，开始下载 {len(binary_data_base64_list)} 张图片")
                
                # 创建输出目录
                chapter = narration.chapter
                novel = chapter.novel
                output_dir = os.path.join(settings.MEDIA_ROOT, 'novels', str(novel.id), f'chapter_{chapter.id:03d}', 'narration_images')
                os.makedirs(output_dir, exist_ok=True)
                
                downloaded_images = []
                
                # 下载每张图片
                for i, image_data_base64 in enumerate(binary_data_base64_list):
                    try:
                        # 解码base64图片数据
                        image_data = base64.b64decode(image_data_base64)
                        
                        # 生成文件名
                        filename = f"narration_{narration.scene_number}_{i+1}.png"
                        output_path = os.path.join(output_dir, filename)
                        
                        # 保存图片
                        with open(output_path, 'wb') as f:
                            f.write(image_data)
                        
                        downloaded_images.append({
                            'filename': filename,
                            'path': output_path,
                            'relative_path': os.path.relpath(output_path, settings.MEDIA_ROOT)
                        })
                        
                        logger.info(f"图片已保存: {output_path}")
                        
                    except Exception as e:
                        logger.error(f"下载第{i+1}张图片失败: {str(e)}")
                        continue
                
                if downloaded_images:
                    # 更新解说对象的图片路径和任务状态
                    narration.image_task_status = 'completed'
                    narration.image_task_progress = 100
                    narration.image_task_message = f'解说 {narration.scene_number} 分镜图片生成并下载完成，共{len(downloaded_images)}张图片'
                    narration.image_task_completed_at = timezone.now()
                    # 如果模型有图片路径字段，可以保存第一张图片的路径
                    # narration.image_path = downloaded_images[0]['relative_path']
                    narration.save()
                    
                    return {
                        'status': 'completed',
                        'narration_id': narration_id,
                        'downloaded_images': downloaded_images,
                        'message': f'解说 {narration.scene_number} 分镜图片生成并下载完成',
                        'volcengine_response': resp
                    }
                else:
                    error_msg = "所有图片下载失败"
                    logger.error(error_msg)
                    # 更新任务状态为失败
                    narration.image_task_status = 'failed'
                    narration.image_task_error = error_msg
                    narration.image_task_message = error_msg
                    narration.save()
                    return {
                        'status': 'error',
                        'narration_id': narration_id,
                        'error': error_msg,
                        'volcengine_response': resp
                    }
            else:
                error_msg = "任务完成但未获取到图片数据"
                logger.error(error_msg)
                # 更新任务状态为失败
                narration.image_task_status = 'failed'
                narration.image_task_error = error_msg
                narration.image_task_message = error_msg
                narration.save()
                return {
                    'status': 'error',
                    'narration_id': narration_id,
                    'error': error_msg,
                    'volcengine_response': resp
                }
                
        elif task_status in ['pending', 'running']:
            # 任务仍在进行中，继续等待
            logger.info(f"解说 {narration.scene_number} 图片生成任务仍在进行中，{retry_interval}秒后重试")
            
            # 如果还有重试次数，延迟重试
            if self.request.retries < max_retries:
                # 更新进度状态
                progress = 30 + min(self.request.retries * 2, 50)  # 30-80%的进度
                narration.image_task_progress = progress
                narration.image_task_message = f"图片生成任务进行中，状态: {task_status}，第{self.request.retries + 1}次检查"
                narration.save()
                raise self.retry(countdown=retry_interval, max_retries=max_retries)
            else:
                error_msg = f"任务超时，已重试{max_retries}次"
                logger.error(error_msg)
                # 更新任务状态为超时
                narration.image_task_status = 'failed'
                narration.image_task_error = error_msg
                narration.image_task_message = error_msg
                narration.save()
                return {
                    'status': 'timeout',
                    'narration_id': narration_id,
                    'error': error_msg,
                    'volcengine_response': resp
                }
                
        elif task_status == 'failed':
            error_msg = f"火山引擎任务失败: {result.get('reason', '未知错误')}"
            logger.error(error_msg)
            # 更新任务状态为失败
            narration.image_task_status = 'failed'
            narration.image_task_error = error_msg
            narration.image_task_message = error_msg
            narration.save()
            return {
                'status': 'failed',
                'narration_id': narration_id,
                'error': error_msg,
                'volcengine_response': resp
            }
        else:
            error_msg = f"未知任务状态: {task_status}"
            logger.error(error_msg)
            
            # 如果是未知状态，也尝试重试
            if self.request.retries < max_retries:
                # 更新重试状态
                narration.image_task_message = f"未知状态 {task_status}，{retry_interval}秒后重试 (第{self.request.retries + 1}/{max_retries}次)"
                narration.save()
                logger.info(f"未知状态，{retry_interval}秒后重试 (第{self.request.retries + 1}/{max_retries}次)")
                raise self.retry(countdown=retry_interval, max_retries=max_retries)
            
            # 最终失败
            narration.image_task_status = 'failed'
            narration.image_task_error = error_msg
            narration.image_task_message = error_msg
            narration.save()
            return {
                'status': 'error',
                'narration_id': narration_id,
                'error': error_msg,
                'volcengine_response': resp
            }
            
    except Exception as e:
        error_msg = f"监控解说 {narration_id} 图片生成任务异常: {str(e)}"
        logger.error(error_msg)
        
        try:
            # 尝试获取解说对象并更新状态
            narration = Narration.objects.get(id=narration_id)
            
            # 如果是网络错误等可重试的异常，尝试重试
            if self.request.retries < max_retries and "网络" in str(e):
                narration.image_task_message = f"网络异常，{retry_interval}秒后重试 (第{self.request.retries + 1}/{max_retries}次)"
                narration.save()
                logger.info(f"网络异常，{retry_interval}秒后重试 (第{self.request.retries + 1}/{max_retries}次)")
                raise self.retry(countdown=retry_interval, max_retries=max_retries)
            
            # 最终异常失败
            narration.image_task_status = 'failed'
            narration.image_task_error = error_msg
            narration.image_task_message = error_msg
            narration.save()
        except Exception as save_error:
            logger.error(f"保存异常状态失败: {str(save_error)}")
        
        return {
            'status': 'error',
            'narration_id': narration_id,
            'error': error_msg
        }


@shared_task(bind=True)
def generate_audio_async(self, novel_id, chapter_id):
    """
    异步生成音频任务
    
    Args:
        novel_id (int): 小说ID
        chapter_id (int): 章节ID
        
    Returns:
        dict: 处理结果
    """
    logger.info(f"开始异步生成音频: 小说ID={novel_id}, 章节ID={chapter_id}")
    
    try:
        # 更新任务进度
        self.update_state(
            state='PROGRESS',
            meta={'current': 0, 'total': 100, 'status': '正在初始化音频生成...'}
        )
        
        # 获取章节信息以构建正确的数据目录路径
        from .models import Chapter, AudioGenerationTask
        from django.utils import timezone
        
        try:
            chapter = Chapter.objects.get(id=chapter_id)
        except Chapter.DoesNotExist:
            raise Exception(f"章节不存在: ID={chapter_id}")
        
        # 创建或获取音频生成任务记录
        audio_task, created = AudioGenerationTask.objects.get_or_create(
            task_id=self.request.id,
            defaults={
                'chapter': chapter,
                'status': 'processing',
                'started_at': timezone.now(),
                'log_message': '开始音频生成任务'
            }
        )
        
        if not created:
            # 如果任务已存在，更新状态
            audio_task.status = 'processing'
            audio_task.started_at = timezone.now()
            audio_task.log_message = '重新开始音频生成任务'
            audio_task.save()
        
        # 使用工具函数获取文件系统中的章节编号
        from .utils import get_chapter_number_from_filesystem, get_chapter_directory_path
        
        # 获取文件系统中实际的章节编号
        chapter_number = get_chapter_number_from_filesystem(novel_id, chapter)
        if not chapter_number:
            raise Exception(f"无法在文件系统中找到章节 {chapter.title} 的目录")
        
        # 构建数据目录路径
        data_dir = get_chapter_directory_path(novel_id, chapter_number)
        
        if not os.path.exists(data_dir):
            raise Exception(f"章节数据目录不存在: {data_dir}")
        
        # 检查narration.txt文件是否存在
        narration_file = os.path.join(data_dir, 'narration.txt')
        if not os.path.exists(narration_file):
            raise Exception(f"解说文件不存在: {narration_file}")
        
        # 更新进度
        self.update_state(
            state='PROGRESS',
            meta={'current': 10, 'total': 100, 'status': '正在提取解说内容...'}
        )
        
        # 导入音频生成相关模块
        import sys
        import re
        from datetime import datetime
        
        # 添加项目根目录到路径
        project_root = os.path.join(settings.BASE_DIR, '..')
        if project_root not in sys.path:
            sys.path.insert(0, project_root)
        
        # 导入语音生成器
        from src.voice.gen_voice import VoiceGenerator
        
        # 提取解说内容的函数
        def extract_narration_content(narration_file_path):
            narration_contents = []
            try:
                with open(narration_file_path, 'r', encoding='utf-8') as f:
                    content = f.read()
                
                # 使用正则表达式提取所有<解说内容>标签中的内容
                narration_matches = re.findall(r'<解说内容>([^<]+)', content, re.DOTALL)
                
                for narration in narration_matches:
                    clean_narration = narration.strip()
                    if clean_narration:
                        narration_contents.append(clean_narration)
                
                return narration_contents
            except Exception as e:
                logger.error(f"提取解说内容时发生错误: {e}")
                return []
        
        # 清理文本用于TTS
        def clean_text_for_tts(text):
            text = re.sub(r'\([^)]*\)', '', text)
            text = re.sub(r'\[[^\]]*\]', '', text)
            text = re.sub(r'\{[^}]*\}', '', text)
            text = re.sub(r'（[^）]*）', '', text)
            text = re.sub(r'【[^】]*】', '', text)
            text = text.replace('&', '')
            text = re.sub(r'\s+', ' ', text).strip()
            return text
        
        # 提取解说内容
        narration_contents = extract_narration_content(narration_file)
        
        if not narration_contents:
            raise Exception("未找到解说内容")
        
        logger.info(f"找到 {len(narration_contents)} 段解说内容")
        
        # 更新进度
        self.update_state(
            state='PROGRESS',
            meta={'current': 20, 'total': 100, 'status': f'开始生成 {len(narration_contents)} 段音频...'}
        )
        
        # 创建语音生成器
        voice_generator = VoiceGenerator()
        
        # 生成音频文件
        success_count = 0
        failed_count = 0
        skipped_count = 0
        generated_audio_files = []
        generated_timestamp_files = []
        
        # 更新任务记录的总段数
        audio_task.total_segments = len(narration_contents)
        audio_task.save()
        
        for i, narration_text in enumerate(narration_contents, 1):
            try:
                # 更新进度
                progress = 20 + (i * 60 // len(narration_contents))
                self.update_state(
                    state='PROGRESS',
                    meta={'current': progress, 'total': 100, 'status': f'正在生成第 {i}/{len(narration_contents)} 段音频...'}
                )
                
                # 更新数据库任务进度
                audio_task.progress = progress
                audio_task.log_message = f'正在生成第 {i}/{len(narration_contents)} 段音频'
                audio_task.save()
                
                # 清理文本
                clean_narration = clean_text_for_tts(narration_text)
                
                if not clean_narration.strip():
                    logger.warning(f"第 {i} 段解说内容清理后为空，跳过")
                    skipped_count += 1
                    continue
                
                # 生成音频文件路径
                chapter_name = f'chapter_{chapter_number}'
                audio_path = os.path.join(data_dir, f"{chapter_name}_narration_{i:02d}.mp3")
                timestamp_path = os.path.join(data_dir, f"{chapter_name}_narration_{i:02d}_timestamps.json")
                
                # 检查文件是否已存在
                if os.path.exists(audio_path) and os.path.exists(timestamp_path):
                    logger.info(f"第 {i} 段语音文件已存在，跳过生成")
                    skipped_count += 1
                    continue
                
                # 生成语音并获取时间戳
                result = voice_generator.generate_voice_with_timestamps(clean_narration, audio_path, speed_ratio=1.2)
                
                if result and result.get('success', False):
                    # 构建时间戳数据结构
                    api_response = result.get('api_response', {})
                    timestamp_data = {
                        "text": clean_narration,
                        "audio_file": audio_path,
                        "duration": float(api_response.get('addition', {}).get('duration', 0)) / 1000.0,
                        "character_timestamps": [],
                        "generated_at": datetime.now().isoformat()
                    }
                    
                    # 解析字符级时间戳
                    try:
                        addition = api_response.get('addition', {})
                        frontend_str = addition.get('frontend', '{}')
                        if isinstance(frontend_str, str):
                            frontend_data = json.loads(frontend_str)
                        else:
                            frontend_data = frontend_str
                        
                        words = frontend_data.get('words', [])
                        for word_info in words:
                            timestamp_data["character_timestamps"].append({
                                "character": word_info.get('word', ''),
                                "start_time": float(word_info.get('start_time', 0)),
                                "end_time": float(word_info.get('end_time', 0))
                            })
                    except (json.JSONDecodeError, KeyError, ValueError) as e:
                        logger.warning(f"解析时间戳失败，使用估算值: {e}")
                        # 回退到估算方式
                        current_time = 0.0
                        char_duration = timestamp_data["duration"] / len(clean_narration) if clean_narration else 0.15
                        for char in clean_narration:
                            timestamp_data["character_timestamps"].append({
                                "character": char,
                                "start_time": current_time,
                                "end_time": current_time + char_duration
                            })
                            current_time += char_duration
                    
                    # 保存时间戳文件
                    with open(timestamp_path, 'w', encoding='utf-8') as f:
                        json.dump(timestamp_data, f, ensure_ascii=False, indent=2)
                    
                    # 添加到生成文件列表
                    generated_audio_files.append(audio_path)
                    generated_timestamp_files.append(timestamp_path)
                    
                    success_count += 1
                    logger.info(f"第 {i} 段语音生成成功")
                    
                    # 更新数据库任务统计
                    audio_task.success_count = success_count
                    audio_task.failed_count = failed_count
                    audio_task.skipped_count = skipped_count
                    audio_task.generated_audio_files = generated_audio_files
                    audio_task.generated_timestamp_files = generated_timestamp_files
                    audio_task.save()
                else:
                    failed_count += 1
                    error_msg = result.get('error_message', '未知错误') if result else '任务返回空结果'
                    logger.error(f"第 {i} 段语音生成失败: {error_msg}")
                    
            except Exception as e:
                failed_count += 1
                logger.error(f"第 {i} 段语音生成异常: {str(e)}")
        
        # 更新进度
        self.update_state(
            state='PROGRESS',
            meta={'current': 80, 'total': 100, 'status': '音频生成完成，开始生成ASS字幕...'}
        )
        
        # 生成ASS字幕文件
        ass_files = []
        try:
            # 查找所有时间戳文件
            timestamp_files = []
            for i in range(1, len(narration_contents) + 1):
                chapter_name = f'chapter_{chapter_number}'
                timestamp_path = os.path.join(data_dir, f"{chapter_name}_narration_{i:02d}_timestamps.json")
                if os.path.exists(timestamp_path):
                    timestamp_files.append(timestamp_path)
            
            # 为每个时间戳文件生成ASS字幕
            for timestamp_file in timestamp_files:
                try:
                    # 生成ASS文件路径
                    base_name = os.path.splitext(os.path.basename(timestamp_file))[0].replace('_timestamps', '')
                    ass_file_path = os.path.join(data_dir, f"{base_name}.ass")
                    
                    # 调用ASS生成函数
                    if generate_ass_subtitle(timestamp_file, ass_file_path):
                        ass_files.append(ass_file_path)
                        logger.info(f"ASS字幕生成成功: {ass_file_path}")
                    else:
                        logger.error(f"ASS字幕生成失败: {ass_file_path}")
                        
                except Exception as e:
                    logger.error(f"生成ASS字幕时发生异常: {str(e)}")
        
        except Exception as e:
            logger.error(f"ASS字幕生成过程发生异常: {str(e)}")
        
        # 更新进度
        self.update_state(
            state='PROGRESS',
            meta={'current': 100, 'total': 100, 'status': '音频和字幕生成完成'}
        )
        
        # 更新数据库任务记录为完成状态
        audio_task.status = 'success'
        audio_task.progress = 100
        audio_task.success_count = success_count
        audio_task.failed_count = failed_count
        audio_task.skipped_count = skipped_count
        audio_task.generated_audio_files = generated_audio_files
        audio_task.generated_timestamp_files = generated_timestamp_files
        audio_task.generated_ass_files = ass_files
        audio_task.completed_at = timezone.now()
        audio_task.log_message = f'音频生成完成: 新生成 {success_count} 个，跳过 {skipped_count} 个，失败 {failed_count} 个'
        audio_task.save()
        
        # 更新Narration模型中的音频路径
        from .models import Narration
        narrations = Narration.objects.filter(chapter=chapter).order_by('id')
        
        # 收集所有存在的音频文件（包括新生成的和已存在的）
        all_audio_files = []
        chapter_name = f'chapter_{chapter_number}'
        for i in range(len(narrations)):
            # 音频文件索引从1开始，不是从0开始
            audio_path = os.path.join(data_dir, f"{chapter_name}_narration_{i+1:02d}.mp3")
            if os.path.exists(audio_path):
                all_audio_files.append(audio_path)
            else:
                all_audio_files.append(None)
        
        logger.info(f"开始更新Narration记录，章节ID: {chapter.id}, 找到音频文件数量: {len([f for f in all_audio_files if f])}, Narration记录数量: {len(narrations)}")
        
        for i, narration in enumerate(narrations):
            try:
                if i < len(all_audio_files) and all_audio_files[i]:
                    audio_file = all_audio_files[i]
                    logger.info(f"准备更新Narration记录 {i+1}: ID={narration.id}, Scene={narration.scene_number}")
                    narration.narration_mp3_path = audio_file
                    narration.save()
                    logger.info(f"成功更新Narration记录: {narration.scene_number} -> {audio_file}")
                else:
                    logger.warning(f"第 {i+1} 个Narration记录没有对应的音频文件")
            except Exception as e:
                logger.error(f"更新Narration记录失败: {str(e)}")
        
        result = {
            'status': 'success',
            'novel_id': novel_id,
            'chapter_id': chapter_id,
            'message': f'音频生成完成: 新生成 {success_count} 个，跳过 {skipped_count} 个，失败 {failed_count} 个',
            'success_count': success_count,
            'failed_count': failed_count,
            'skipped_count': skipped_count,
            'ass_files_count': len(ass_files)
        }
        
        logger.info(f"音频生成任务完成: {result}")
        return result
        
    except Exception as e:
        logger.error(f"音频生成失败: {str(e)}")
        
        # 更新数据库任务记录为失败状态
        try:
            audio_task.status = 'failed'
            audio_task.error_message = str(e)
            audio_task.completed_at = timezone.now()
            audio_task.log_message = f'音频生成失败: {str(e)}'
            audio_task.save()
        except Exception as save_error:
            logger.error(f"保存失败状态到数据库时出错: {str(save_error)}")
        
        return {
            'status': 'error',
            'novel_id': novel_id,
            'chapter_id': chapter_id,
            'message': f'音频生成失败: {str(e)}'
        }


@shared_task(bind=True)
def validate_narration_images_llm_async(self, novel_id, chapter_id):
    """
    异步执行llm_narration_image.py脚本校验旁白图片
    
    Args:
        novel_id (int): 小说ID
        chapter_id (int): 章节ID
        
    Returns:
        dict: 处理结果
    """
    logger.info(f"开始异步校验旁白图片(LLM): 小说ID={novel_id}, 章节ID={chapter_id}")
    
    try:
        # 获取章节对象
        from .models import Chapter
        chapter = Chapter.objects.get(id=chapter_id)
        
        # 使用工具函数获取文件系统中的章节编号
        from .utils import get_chapter_number_from_filesystem
        chapter_number = get_chapter_number_from_filesystem(novel_id, chapter)
        
        if not chapter_number:
            raise Exception(f'无法在文件系统中找到章节 {chapter.title} 的目录')
        
        # 构建章节目录路径
        chapter_dir = f'data/{novel_id:03d}/chapter_{chapter_number}'
        
        # 检查章节目录是否存在
        project_root = settings.BASE_DIR.parent
        full_chapter_path = os.path.join(project_root, chapter_dir)
        
        if not os.path.exists(full_chapter_path):
            raise Exception(f'章节目录不存在: {full_chapter_path}')
        
        # 构建脚本路径
        script_path = os.path.join(settings.BASE_DIR.parent, 'llm_narration_image.py')
        
        if not os.path.exists(script_path):
            raise Exception(f'脚本文件不存在: {script_path}')
        
        # 执行llm_narration_image.py脚本，针对特定章节
        cmd = ['python', script_path, chapter_dir, '--auto-regenerate']
        
        logger.info(f"执行命令: {' '.join(cmd)}")
        
        # 切换到项目根目录执行
        project_root = settings.BASE_DIR.parent
        
        result = subprocess.run(
            cmd,
            cwd=project_root,
            capture_output=True,
            text=True,
            timeout=3600  # 1小时超时
        )
        
        if result.returncode == 0:
            logger.info(f"旁白图片校验(LLM)完成: 小说ID={novel_id}, 章节ID={chapter_id}")
            
            return {
                'status': 'success',
                'message': '旁白图片校验(LLM)完成',
                'novel_id': novel_id,
                'chapter_id': chapter_id,
                'output': result.stdout
            }
        else:
            logger.error(f"旁白图片校验(LLM)失败: {result.stderr}")
            return {
                'status': 'error',
                'message': f'旁白图片校验(LLM)失败: {result.stderr}',
                'novel_id': novel_id,
                'chapter_id': chapter_id,
                'output': result.stdout,
                'error': result.stderr
            }
            
    except Exception as e:
        logger.error(f"旁白图片校验(LLM)异常: {str(e)}")
        return {
            'status': 'error',
            'message': f'旁白图片校验(LLM)异常: {str(e)}',
            'novel_id': novel_id,
            'chapter_id': chapter_id
        }


def generate_ass_subtitle(timestamp_file_path, output_path):
    """
    根据时间戳文件生成ASS字幕
    使用gen_ass.py脚本进行高质量的字幕生成
    
    Args:
        timestamp_file_path (str): 时间戳文件路径
        output_path (str): 输出ASS文件路径
        
    Returns:
        bool: 是否成功
    """
    try:
        # 获取章节目录路径（timestamp文件的父目录）
        chapter_dir = os.path.dirname(timestamp_file_path)
        
        # 获取项目根目录路径
        project_root = os.path.dirname(os.path.dirname(os.path.dirname(__file__)))
        gen_ass_script = os.path.join(project_root, 'gen_ass.py')
        
        # 检查gen_ass.py脚本是否存在
        if not os.path.exists(gen_ass_script):
            logger.error(f"gen_ass.py脚本不存在: {gen_ass_script}")
            return False
        
        # 检查时间戳文件是否存在
        if not os.path.exists(timestamp_file_path):
            logger.error(f"时间戳文件不存在: {timestamp_file_path}")
            return False
        
        # 调用gen_ass.py脚本处理单个章节
        import subprocess
        
        # 获取数据目录路径（章节目录的父目录）
        data_dir = os.path.dirname(chapter_dir)
        # 获取章节名称
        chapter_name = os.path.basename(chapter_dir)
        
        cmd = ['python', gen_ass_script, data_dir, '--chapter', chapter_name]
        logger.info(f"执行命令: {' '.join(cmd)}")
        
        result = subprocess.run(
            cmd,
            cwd=project_root,
            capture_output=True,
            text=True,
            timeout=300  # 5分钟超时
        )
        
        if result.returncode == 0:
            # 检查输出文件是否生成
            if os.path.exists(output_path):
                logger.info(f"ASS字幕文件生成成功: {output_path}")
                return True
            else:
                logger.error(f"gen_ass.py执行成功但输出文件不存在: {output_path}")
                logger.error(f"stdout: {result.stdout}")
                logger.error(f"stderr: {result.stderr}")
                return False
        else:
            logger.error(f"gen_ass.py执行失败，返回码: {result.returncode}")
            logger.error(f"stdout: {result.stdout}")
            logger.error(f"stderr: {result.stderr}")
            return False
        
    except subprocess.TimeoutExpired:
        logger.error(f"gen_ass.py执行超时: {timestamp_file_path}")
        return False
    except Exception as e:
        logger.error(f"生成ASS字幕失败: {str(e)}")
        return False


@shared_task(bind=True)
def gen_image_async_v4_task(self, novel_id, chapter_id, api_url='http://127.0.0.1:8188/api/prompt', workflow_json='test/comfyui/image_compact.json'):
    """
    使用 gen_image_async_v4.py 生成章节分镜图片的 Celery 任务。

    函数级说明：
    - 目录解析：不再直接用章节 ID 作为目录名，而是通过文件系统真实的章节编号
      构建路径，例如 `data/{novel_id:03d}/chapter_{chapter_number}`。
    - 任务流程：更新章节批量图片状态 → 执行外部脚本 → 汇总结果并写回状态。

    Args:
        novel_id (int): 小说 ID
        chapter_id (int): 章节 ID（数据库 ID）
        api_url (str): ComfyUI API 地址，默认本地 `http://127.0.0.1:8188`
        workflow_json (str): 工作流 JSON 文件路径或标识

    Returns:
        dict: 任务执行结果，包含状态、提示信息等
    """
    try:
        # 获取章节对象
        from .models import Chapter
        chapter = Chapter.objects.get(id=chapter_id, novel_id=novel_id)
        
        # 更新章节状态
        chapter.batch_image_status = 'processing'
        chapter.batch_image_progress = 0
        chapter.batch_image_error = ''
        chapter.batch_image_message = '开始生成分镜图片(v4)...'
        chapter.batch_image_started_at = timezone.now()
        chapter.save()
        
        # 使用工具函数解析文件系统章节编号并构建正确的章节目录路径
        from .utils import get_chapter_number_from_filesystem, get_chapter_directory_path

        chapter_number = get_chapter_number_from_filesystem(novel_id, chapter)
        if not chapter_number:
            error_msg = f"无法在文件系统中找到章节 {chapter.title} 的目录"
            logger.error(error_msg)

            chapter.batch_image_status = 'failed'
            chapter.batch_image_progress = 100
            chapter.batch_image_error = error_msg
            chapter.batch_image_message = '无法找到章节目录'
            chapter.batch_image_completed_at = timezone.now()
            chapter.save()

            return {
                'status': 'error',
                'novel_id': novel_id,
                'chapter_id': chapter_id,
                'error': error_msg
            }

        chapter_dir = get_chapter_directory_path(novel_id, chapter_number)
        
        # 检查章节目录是否存在
        if not os.path.exists(chapter_dir):
            error_msg = f"章节目录不存在: {chapter_dir}"
            logger.error(error_msg)
            
            chapter.batch_image_status = 'failed'
            chapter.batch_image_progress = 100
            chapter.batch_image_error = error_msg
            chapter.batch_image_message = '章节目录不存在'
            chapter.batch_image_completed_at = timezone.now()
            chapter.save()
            
            return {
                'status': 'error',
                'novel_id': novel_id,
                'chapter_id': chapter_id,
                'error': error_msg
            }
        
        # 获取项目根目录路径
        project_root = settings.BASE_DIR.parent
        gen_image_script = os.path.join(project_root, 'gen_image_async_v4.py')
        
        # 检查gen_image_async_v4.py脚本是否存在
        if not os.path.exists(gen_image_script):
            error_msg = f"gen_image_async_v4.py脚本不存在: {gen_image_script}"
            logger.error(error_msg)
            
            chapter.batch_image_status = 'failed'
            chapter.batch_image_progress = 100
            chapter.batch_image_error = error_msg
            chapter.batch_image_message = 'gen_image_async_v4.py脚本不存在'
            chapter.batch_image_completed_at = timezone.now()
            chapter.save()
            
            return {
                'status': 'error',
                'novel_id': novel_id,
                'chapter_id': chapter_id,
                'error': error_msg
            }
        
        # 更新进度
        chapter.batch_image_progress = 10
        chapter.batch_image_message = '准备执行gen_image_async_v4.py...'
        chapter.save()
        
        # 规范化 api_url，确保包含 /api/prompt
        normalized_api_url = api_url.rstrip('/')
        if '/api/prompt' not in normalized_api_url:
            if normalized_api_url.endswith('/api'):
                normalized_api_url = normalized_api_url + '/prompt'
            else:
                normalized_api_url = normalized_api_url + '/api/prompt'

        # 构建命令
        cmd = [
            'python', gen_image_script,
            chapter_dir,
            '--api_url', normalized_api_url,
            '--workflow_json', workflow_json,
            '--poll_interval', '5',
            '--max_wait', '300'
        ]
        
        logger.info(f"执行命令: {' '.join(cmd)}")
        
        # 更新进度
        chapter.batch_image_progress = 20
        chapter.batch_image_message = '正在生成分镜图片...'
        chapter.save()
        
        # 执行脚本
        result = subprocess.run(
            cmd,
            cwd=project_root,
            capture_output=True,
            text=True,
            timeout=1800  # 30分钟超时
        )
        
        if result.returncode == 0:
            logger.info(f"gen_image_async_v4.py执行成功: 小说ID={novel_id}, 章节ID={chapter_id}")
            
            # 检查生成的图片文件
            # 收集生成的图片文件
            # 注意：Path.glob 中 '**' 只能作为单独的路径组件；
            # 原逻辑使用 f"narration_*{ext}" 会变成 'narration_**.png' 触发异常。
            # 这里改为使用后缀列表，构造合法模式 'narration_*.png' 等。
            image_files = []
            for suffix in ['png', 'jpg', 'jpeg']:
                image_files.extend(Path(chapter_dir).glob(f'narration_*.{suffix}'))
            
            chapter.batch_image_status = 'completed'
            chapter.batch_image_progress = 100
            chapter.batch_image_error = ''
            chapter.batch_image_message = f'分镜图片生成完成，共生成{len(image_files)}张图片'
            chapter.batch_image_completed_at = timezone.now()
            chapter.save()
            
            return {
                'status': 'success',
                'novel_id': novel_id,
                'chapter_id': chapter_id,
                'message': f'分镜图片生成完成，共生成{len(image_files)}张图片',
                'image_count': len(image_files),
                'output': result.stdout
            }
        else:
            # 检查是否有部分成功的情况
            image_files = []
            for ext in ['*.png', '*.jpg', '*.jpeg']:
                image_files.extend(Path(chapter_dir).glob(f'narration_*{ext}'))
            
            if len(image_files) > 0:
                # 部分成功
                error_msg = f"gen_image_async_v4.py部分成功，返回码: {result.returncode}，已生成{len(image_files)}张图片"
                logger.warning(error_msg)
                logger.warning(f"stdout: {result.stdout}")
                logger.warning(f"stderr: {result.stderr}")
                
                chapter.batch_image_status = 'completed'
                chapter.batch_image_progress = 100
                chapter.batch_image_error = f"部分成功: {result.stderr}"
                chapter.batch_image_message = f'部分图片生成成功，共生成{len(image_files)}张图片'
                chapter.batch_image_completed_at = timezone.now()
                chapter.save()
                
                return {
                    'status': 'warning',
                    'novel_id': novel_id,
                    'chapter_id': chapter_id,
                    'message': error_msg,
                    'image_count': len(image_files),
                    'output': result.stdout,
                    'stderr': result.stderr
                }
            else:
                # 完全失败
                error_msg = f"gen_image_async_v4.py执行失败，返回码: {result.returncode}"
                logger.error(error_msg)
                logger.error(f"stdout: {result.stdout}")
                logger.error(f"stderr: {result.stderr}")
                
                chapter.batch_image_status = 'failed'
                chapter.batch_image_progress = 100
                chapter.batch_image_error = f"{error_msg}\nstderr: {result.stderr}"
                chapter.batch_image_message = 'gen_image_async_v4.py执行失败'
                chapter.batch_image_completed_at = timezone.now()
                chapter.save()
                
                return {
                    'status': 'error',
                    'novel_id': novel_id,
                    'chapter_id': chapter_id,
                    'error': error_msg,
                    'stderr': result.stderr
                }
                
    except subprocess.TimeoutExpired:
        error_msg = "gen_image_async_v4.py执行超时"
        logger.error(error_msg)
        
        chapter.batch_image_status = 'failed'
        chapter.batch_image_progress = 100
        chapter.batch_image_error = error_msg
        chapter.batch_image_message = '脚本执行超时'
        chapter.batch_image_completed_at = timezone.now()
        chapter.save()
        
        return {
            'status': 'error',
            'novel_id': novel_id,
            'chapter_id': chapter_id,
            'error': error_msg
        }
        
    except Exception as e:
        error_msg = f"gen_image_async_v4任务执行异常: {str(e)}"
        logger.error(error_msg)
        
        try:
            chapter.batch_image_status = 'failed'
            chapter.batch_image_progress = 100
            chapter.batch_image_error = error_msg
            chapter.batch_image_message = '任务执行异常'
            chapter.batch_image_completed_at = timezone.now()
            chapter.save()
        except Exception as save_error:
            logger.error(f"保存章节状态失败: {save_error}")
        
        return {
            'status': 'error',
            'novel_id': novel_id,
            'chapter_id': chapter_id,
            'error': error_msg
        }