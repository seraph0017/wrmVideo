from django.http import JsonResponse, StreamingHttpResponse
from django.views.decorators.csrf import csrf_exempt
from django.views.decorators.http import require_http_methods
from celery.result import AsyncResult
import json
import logging
import time
from django.conf import settings
import os
from datetime import datetime, timedelta

logger = logging.getLogger(__name__)

@require_http_methods(["GET"])
def get_task_logs(request, task_id):
    """
    获取任务的实时日志
    
    Args:
        request: HTTP请求
        task_id: Celery任务ID
    
    Returns:
        JsonResponse: 包含日志信息的JSON响应
    """
    try:
        # 获取任务结果
        result = AsyncResult(task_id)
        
        # 获取任务状态和元数据
        task_info = {
            'task_id': task_id,
            'state': result.state,
            'info': result.info if result.info else {},
            'ready': result.ready(),
            'successful': result.successful() if result.ready() else False,
            'failed': result.failed() if result.ready() else False,
        }
        
        # 如果任务完成，获取结果
        if result.ready():
            if result.successful():
                task_info['result'] = result.result
            elif result.failed():
                task_info['error'] = str(result.info)
        
        # 获取日志文件内容
        logs = get_recent_logs(task_id)
        
        return JsonResponse({
            'success': True,
            'task_info': task_info,
            'logs': logs,
            'timestamp': datetime.now().isoformat()
        })
        
    except Exception as e:
        logger.error(f"获取任务日志失败: {e}")
        return JsonResponse({
            'success': False,
            'error': str(e)
        }, status=500)

def get_recent_logs(task_id=None, lines=100):
    """
    获取最近的日志记录
    
    Args:
        task_id: 任务ID（可选，用于过滤特定任务的日志）
        lines: 返回的日志行数
    
    Returns:
        list: 日志记录列表
    """
    logs = []
    
    try:
        # 优先读取Celery专用日志文件
        celery_log_file = os.path.join(settings.BASE_DIR, 'logs', 'celery.log')
        
        # 如果Celery日志文件不存在，尝试读取Django日志文件
        log_file = celery_log_file
        if not os.path.exists(celery_log_file):
            # 获取Django日志文件路径
            django_log_file = None
            if hasattr(settings, 'LOGGING'):
                handlers = settings.LOGGING.get('handlers', {})
                for handler_name, handler_config in handlers.items():
                    if handler_config.get('class') == 'logging.FileHandler':
                        django_log_file = handler_config.get('filename')
                        break
            
            if not django_log_file:
                # 默认日志文件路径
                django_log_file = os.path.join(settings.BASE_DIR, 'logs', 'django.log')
            
            log_file = django_log_file
        
        if os.path.exists(log_file):
            with open(log_file, 'r', encoding='utf-8') as f:
                all_lines = f.readlines()
                
                # 获取最后N行
                recent_lines = all_lines[-lines:] if len(all_lines) > lines else all_lines
                
                for line in recent_lines:
                    line = line.strip()
                    if line:
                        # 如果指定了task_id，只返回相关的日志
                        if task_id is None or task_id in line:
                            logs.append({
                                'timestamp': extract_timestamp(line),
                                'level': extract_log_level(line),
                                'message': line
                            })
        else:
            # 如果日志文件不存在，返回提示信息
            logs.append({
                'timestamp': datetime.now().isoformat(),
                'level': 'INFO',
                'message': f'日志文件不存在: {log_file}，请先启动Celery worker生成日志'
            })
        
    except Exception as e:
        logger.error(f"读取日志文件失败: {e}")
        logs.append({
            'timestamp': datetime.now().isoformat(),
            'level': 'ERROR',
            'message': f'读取日志文件失败: {e}'
        })
    
    return logs

def extract_timestamp(log_line):
    """
    从日志行中提取时间戳
    
    Args:
        log_line: 日志行
    
    Returns:
        str: ISO格式的时间戳
    """
    try:
        # 尝试从日志行开头提取时间戳
        # 假设格式类似: "2024-01-15 10:30:45,123 INFO ..."
        parts = log_line.split(' ')
        if len(parts) >= 2:
            date_part = parts[0]
            time_part = parts[1].split(',')[0]  # 移除毫秒部分
            timestamp_str = f"{date_part} {time_part}"
            
            # 尝试解析时间戳
            dt = datetime.strptime(timestamp_str, "%Y-%m-%d %H:%M:%S")
            return dt.isoformat()
    except:
        pass
    
    # 如果无法提取，返回当前时间
    return datetime.now().isoformat()

def extract_log_level(log_line):
    """
    从日志行中提取日志级别
    
    Args:
        log_line: 日志行
    
    Returns:
        str: 日志级别
    """
    levels = ['DEBUG', 'INFO', 'WARNING', 'ERROR', 'CRITICAL']
    
    for level in levels:
        if level in log_line.upper():
            return level
    
    return 'INFO'  # 默认级别

@require_http_methods(["GET"])
def stream_task_logs(request, task_id):
    """
    流式传输任务日志（Server-Sent Events）
    
    Args:
        request: HTTP请求
        task_id: Celery任务ID
    
    Returns:
        StreamingHttpResponse: SSE响应
    """
    def event_stream():
        last_log_count = 0
        
        while True:
            try:
                # 获取任务状态
                result = AsyncResult(task_id)
                
                # 获取最新日志
                logs = get_recent_logs(task_id, lines=200)
                
                # 只发送新的日志
                if len(logs) > last_log_count:
                    new_logs = logs[last_log_count:]
                    
                    for log in new_logs:
                        data = json.dumps({
                            'type': 'log',
                            'data': log
                        })
                        yield f"data: {data}\n\n"
                    
                    last_log_count = len(logs)
                
                # 发送任务状态更新
                task_data = {
                    'type': 'status',
                    'data': {
                        'state': result.state,
                        'info': result.info if result.info else {},
                        'ready': result.ready()
                    }
                }
                yield f"data: {json.dumps(task_data)}\n\n"
                
                # 如果任务完成，停止流式传输
                if result.ready():
                    final_data = {
                        'type': 'complete',
                        'data': {
                            'successful': result.successful(),
                            'result': result.result if result.successful() else None,
                            'error': str(result.info) if result.failed() else None
                        }
                    }
                    yield f"data: {json.dumps(final_data)}\n\n"
                    break
                
                time.sleep(2)  # 每2秒更新一次
                
            except Exception as e:
                error_data = {
                    'type': 'error',
                    'data': {'message': str(e)}
                }
                yield f"data: {json.dumps(error_data)}\n\n"
                break
    
    response = StreamingHttpResponse(
        event_stream(),
        content_type='text/event-stream'
    )
    response['Cache-Control'] = 'no-cache'
    response['Connection'] = 'keep-alive'
    response['Access-Control-Allow-Origin'] = '*'
    
    return response

@require_http_methods(["GET"])
def get_all_active_tasks(request):
    """
    获取所有活跃的任务
    
    Returns:
        JsonResponse: 包含活跃任务列表的JSON响应
    """
    try:
        from celery import current_app
        
        # 获取活跃任务
        active_tasks = current_app.control.inspect().active()
        
        # 格式化任务信息
        formatted_tasks = []
        if active_tasks:
            for worker, tasks in active_tasks.items():
                for task in tasks:
                    formatted_tasks.append({
                        'task_id': task['id'],
                        'name': task['name'],
                        'worker': worker,
                        'args': task.get('args', []),
                        'kwargs': task.get('kwargs', {}),
                        'time_start': task.get('time_start')
                    })
        
        return JsonResponse({
            'success': True,
            'tasks': formatted_tasks,
            'count': len(formatted_tasks)
        })
        
    except Exception as e:
        logger.error(f"获取活跃任务失败: {e}")
        return JsonResponse({
            'success': False,
            'error': str(e)
        }, status=500)