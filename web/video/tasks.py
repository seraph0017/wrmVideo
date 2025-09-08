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
from django.conf import settings
from django.utils import timezone
from .models import CharacterImageTask, Character, Chapter

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
        
        logger.info(f"视频生成完成: {result}")
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
        
        # 构建数据目录路径
        data_dir = f"data/{novel_id:03d}"
        
        # 确保数据目录存在
        if not os.path.exists(data_dir):
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
        
        # 构建命令行参数
        project_root = os.path.join(os.path.dirname(os.path.dirname(os.path.dirname(__file__))))
        cmd = ['python', 'validate_narration.py', data_dir]
        
        # 根据参数添加选项
        if validation_params.get('auto_rewrite', False):
            cmd.append('--auto-rewrite')
        if validation_params.get('auto_fix_characters', False):
            cmd.append('--auto-fix-characters')
        if validation_params.get('auto_fix_tags', False):
            cmd.append('--auto-fix-tags')
        
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
            'NOVEL_ID': str(novel_id),
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
        
        # 从章节标题中提取章节编号（如"第2章" -> "002"）
        import re
        chapter_match = re.search(r'第(\d+)章', chapter.title)
        if chapter_match:
            chapter_number = chapter_match.group(1).zfill(3)
        else:
            # 如果无法从标题提取，使用章节ID
            chapter_number = str(chapter_id).zfill(3)
        
        # 构建数据目录路径
        data_dir = os.path.join(settings.BASE_DIR, '..', 'data', f'{novel_id:03d}', f'chapter_{chapter_number}')
        
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
                chapter_name = f'chapter_{chapter_id:03d}'
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
                chapter_name = f'chapter_{chapter_id:03d}'
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
        chapter_name = f'chapter_{chapter_id:03d}'
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


def generate_ass_subtitle(timestamp_file_path, output_path):
    """
    根据时间戳文件生成ASS字幕
    
    Args:
        timestamp_file_path (str): 时间戳文件路径
        output_path (str): 输出ASS文件路径
        
    Returns:
        bool: 是否成功
    """
    try:
        import re
        
        # 读取时间戳文件
        with open(timestamp_file_path, 'r', encoding='utf-8') as f:
            timestamp_data = json.load(f)
        
        text = timestamp_data.get('text', '')
        character_timestamps = timestamp_data.get('character_timestamps', [])
        
        if not text or not character_timestamps:
            logger.error(f"时间戳数据无效: {timestamp_file_path}")
            return False
        
        # ASS字幕格式化函数
        def format_time_for_ass(seconds):
            hours = int(seconds // 3600)
            minutes = int((seconds % 3600) // 60)
            secs = seconds % 60
            return f"{hours}:{minutes:02d}:{secs:05.2f}"
        
        # 清理字幕文本
        def clean_subtitle_text(text):
            text = re.sub(r'[，。；：、！？""''（）【】《》〈〉「」『』〔〕\[\]｛｝｜～·…—–,.;:!?"\':{}|~\n]', '', text)
            text = re.sub(r'\s+', '', text)
            return text
        
        # 文本分割函数
        def split_text_naturally(text, max_length=12):
            if len(clean_subtitle_text(text)) <= max_length:
                return [text]
            
            # 简单按长度分割
            segments = []
            current_segment = ""
            clean_text = clean_subtitle_text(text)
            
            for char in clean_text:
                if len(current_segment) < max_length:
                    current_segment += char
                else:
                    if current_segment:
                        segments.append(current_segment)
                    current_segment = char
            
            if current_segment:
                segments.append(current_segment)
            
            return segments
        
        # 计算段落时间戳
        def calculate_segment_timestamps(segments, character_timestamps, original_text):
            segment_timestamps = []
            current_char_index = 0
            
            for segment in segments:
                clean_segment = clean_subtitle_text(segment)
                
                # 查找段落在原文中的位置
                segment_start_index = -1
                segment_end_index = -1
                
                clean_original = clean_subtitle_text(original_text)
                for start_pos in range(current_char_index, len(clean_original)):
                    if start_pos + len(clean_segment) <= len(clean_original):
                        if clean_original[start_pos:start_pos + len(clean_segment)] == clean_segment:
                            segment_start_index = start_pos
                            segment_end_index = start_pos + len(clean_segment) - 1
                            break
                
                if segment_start_index != -1 and segment_end_index != -1:
                    if (segment_start_index < len(character_timestamps) and 
                        segment_end_index < len(character_timestamps)):
                        start_time = character_timestamps[segment_start_index]['start_time']
                        end_time = character_timestamps[segment_end_index]['end_time']
                        current_char_index = segment_end_index + 1
                    else:
                        # 使用估算时间
                        if segment_timestamps:
                            start_time = segment_timestamps[-1]['end_time'] + 0.1
                        else:
                            start_time = 0
                        end_time = start_time + len(clean_segment) * 0.3
                else:
                    # 使用估算时间
                    if segment_timestamps:
                        start_time = segment_timestamps[-1]['end_time'] + 0.1
                    else:
                        start_time = 0
                    end_time = start_time + len(clean_segment) * 0.3
                
                # 检查并修正重叠
                if segment_timestamps:
                    prev_end_time = segment_timestamps[-1]['end_time']
                    if start_time < prev_end_time:
                        start_time = prev_end_time + 0.1
                        if start_time >= end_time:
                            end_time = start_time + len(clean_segment) * 0.3
                
                segment_timestamps.append({
                    'text': segment,
                    'start_time': start_time,
                    'end_time': end_time
                })
            
            return segment_timestamps
        
        # 分割文本
        segments = split_text_naturally(text)
        
        # 计算段落时间戳
        segment_timestamps = calculate_segment_timestamps(segments, character_timestamps, text)
        
        # 生成ASS文件内容
        ass_content = """[Script Info]
Title: Auto-generated Subtitle
ScriptType: v4.00+

[V4+ Styles]
Format: Name, Fontname, Fontsize, PrimaryColour, SecondaryColour, OutlineColour, BackColour, Bold, Italic, Underline, StrikeOut, ScaleX, ScaleY, Spacing, Angle, BorderStyle, Outline, Shadow, Alignment, MarginL, MarginR, MarginV, Encoding
Style: Default,Arial,20,&H00FFFFFF,&H000000FF,&H00000000,&H80000000,0,0,0,0,100,100,0,0,1,2,0,2,10,10,10,1

[Events]
Format: Layer, Start, End, Style, Name, MarginL, MarginR, MarginV, Effect, Text
"""
        
        # 添加字幕事件
        for segment_data in segment_timestamps:
            start_time = format_time_for_ass(segment_data['start_time'])
            end_time = format_time_for_ass(segment_data['end_time'])
            text = segment_data['text']
            
            ass_content += f"Dialogue: 0,{start_time},{end_time},Default,,0,0,0,,{text}\n"
        
        # 写入ASS文件
        with open(output_path, 'w', encoding='utf-8') as f:
            f.write(ass_content)
        
        logger.info(f"ASS字幕文件生成成功: {output_path}")
        return True
        
    except Exception as e:
        logger.error(f"生成ASS字幕失败: {str(e)}")
        return False
        
    except Exception as e:
        error_msg = str(e)
        logger.error(f"角色图片生成异常: {task_id}, 错误: {error_msg}")
        
        try:
            task.status = 'failed'
            task.progress = 100
            task.error_message = error_msg
            task.log_message = f'任务执行异常: {error_msg}'
            task.save()
        except Exception as save_error:
            logger.error(f"保存任务状态失败: {save_error}")
        
        return {
            'status': 'error',
            'task_id': task_id,
            'error': error_msg
        }