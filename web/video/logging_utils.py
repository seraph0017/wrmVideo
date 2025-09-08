import subprocess
import logging
import threading
import queue
import time
from typing import Callable, Optional

logger = logging.getLogger(__name__)

def run_command_with_logging(cmd, cwd=None, progress_callback: Optional[Callable] = None, task_self=None):
    """
    执行命令并实时记录输出到日志
    
    Args:
        cmd: 要执行的命令列表
        cwd: 工作目录
        progress_callback: 进度回调函数
        task_self: Celery任务实例，用于更新状态
    
    Returns:
        subprocess.CompletedProcess: 执行结果
    """
    logger.info(f"开始执行命令: {' '.join(cmd)}")
    logger.info(f"工作目录: {cwd}")
    
    # 创建进程
    process = subprocess.Popen(
        cmd,
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
        text=True,
        cwd=cwd,
        bufsize=1,
        universal_newlines=True
    )
    
    # 创建队列来收集输出
    stdout_queue = queue.Queue()
    stderr_queue = queue.Queue()
    
    def read_output(pipe, output_queue, prefix):
        """读取管道输出并放入队列"""
        try:
            for line in iter(pipe.readline, ''):
                if line:
                    line = line.rstrip('\n')
                    output_queue.put((prefix, line))
                    logger.info(f"{prefix}: {line}")
        except Exception as e:
            logger.error(f"读取{prefix}输出时出错: {e}")
        finally:
            pipe.close()
    
    # 启动输出读取线程
    stdout_thread = threading.Thread(
        target=read_output, 
        args=(process.stdout, stdout_queue, "STDOUT")
    )
    stderr_thread = threading.Thread(
        target=read_output, 
        args=(process.stderr, stderr_queue, "STDERR")
    )
    
    stdout_thread.daemon = True
    stderr_thread.daemon = True
    stdout_thread.start()
    stderr_thread.start()
    
    # 收集所有输出
    all_stdout = []
    all_stderr = []
    
    # 监控进程执行
    start_time = time.time()
    last_update_time = start_time
    
    while process.poll() is None:
        # 收集stdout输出
        try:
            while True:
                prefix, line = stdout_queue.get_nowait()
                if prefix == "STDOUT":
                    all_stdout.append(line)
                    
                    # 更新任务状态（如果提供了task_self）
                    if task_self and progress_callback:
                        progress_callback(line)
        except queue.Empty:
            pass
        
        # 收集stderr输出
        try:
            while True:
                prefix, line = stderr_queue.get_nowait()
                if prefix == "STDERR":
                    all_stderr.append(line)
        except queue.Empty:
            pass
        
        # 每5秒更新一次状态
        current_time = time.time()
        if task_self and current_time - last_update_time > 5:
            elapsed_time = current_time - start_time
            task_self.update_state(
                state='PROGRESS',
                meta={
                    'current': 50,
                    'total': 100,
                    'status': f'命令执行中... (已运行 {elapsed_time:.1f}s)',
                    'elapsed_time': elapsed_time
                }
            )
            last_update_time = current_time
        
        time.sleep(0.1)  # 短暂休眠避免CPU占用过高
    
    # 等待线程结束
    stdout_thread.join(timeout=5)
    stderr_thread.join(timeout=5)
    
    # 收集剩余输出
    try:
        while True:
            prefix, line = stdout_queue.get_nowait()
            if prefix == "STDOUT":
                all_stdout.append(line)
    except queue.Empty:
        pass
    
    try:
        while True:
            prefix, line = stderr_queue.get_nowait()
            if prefix == "STDERR":
                all_stderr.append(line)
    except queue.Empty:
        pass
    
    # 获取返回码
    returncode = process.wait()
    
    # 记录执行结果
    elapsed_time = time.time() - start_time
    logger.info(f"命令执行完成，返回码: {returncode}，耗时: {elapsed_time:.2f}s")
    
    if returncode == 0:
        logger.info("命令执行成功")
    else:
        logger.error(f"命令执行失败，返回码: {returncode}")
        if all_stderr:
            logger.error("错误输出:")
            for line in all_stderr:
                logger.error(f"  {line}")
    
    # 创建类似subprocess.run的返回对象
    class CompletedProcess:
        def __init__(self, args, returncode, stdout, stderr):
            self.args = args
            self.returncode = returncode
            self.stdout = stdout
            self.stderr = stderr
    
    return CompletedProcess(
        args=cmd,
        returncode=returncode,
        stdout='\n'.join(all_stdout),
        stderr='\n'.join(all_stderr)
    )

def create_progress_callback(task_self, base_progress=40, max_progress=80):
    """
    创建进度回调函数
    
    Args:
        task_self: Celery任务实例
        base_progress: 基础进度值
        max_progress: 最大进度值
    
    Returns:
        Callable: 进度回调函数
    """
    progress_state = {
        'current_progress': base_progress,
        'chapter_count': 0,
        'processed_chapters': 0,
        'current_step': '初始化'
    }
    
    def progress_callback(output_line):
        # 解析gen_script_v2.py的具体输出
        line = output_line.strip()
        
        # 检测章节总数
        if "找到章节" in line and "个" in line:
            try:
                import re
                match = re.search(r'找到章节\s*(\d+)\s*个', line)
                if match:
                    progress_state['chapter_count'] = int(match.group(1))
                    logger.info(f"检测到章节总数: {progress_state['chapter_count']}")
            except:
                pass
        
        # 检测当前处理的章节
        elif "处理章节" in line or "开始处理" in line:
            progress_state['current_step'] = '处理章节'
            if "章节" in line:
                try:
                    import re
                    match = re.search(r'章节\s*(\d+)', line)
                    if match:
                        chapter_num = int(match.group(1))
                        progress_state['processed_chapters'] = chapter_num
                except:
                    pass
        
        # 检测具体的处理步骤
        elif "生成解说文案" in line or "调用AI" in line:
            progress_state['current_step'] = '生成解说文案'
        elif "保存文件" in line or "写入文件" in line:
            progress_state['current_step'] = '保存文件'
        elif "验证" in line:
            progress_state['current_step'] = '验证内容'
        elif "完成" in line:
            progress_state['current_step'] = '处理完成'
            progress_state['current_progress'] = max_progress
        elif "错误" in line or "失败" in line:
            progress_state['current_step'] = '处理出错'
        
        # 计算进度
        if progress_state['chapter_count'] > 0 and progress_state['processed_chapters'] > 0:
            # 基于章节进度计算
            chapter_progress = (progress_state['processed_chapters'] / progress_state['chapter_count']) * (max_progress - base_progress)
            progress_state['current_progress'] = base_progress + chapter_progress
        else:
            # 基于关键词增量计算
            if "开始处理" in line:
                progress_state['current_progress'] = base_progress + 5
            elif "生成解说" in line:
                progress_state['current_progress'] = min(progress_state['current_progress'] + 10, max_progress - 10)
            elif "保存文件" in line:
                progress_state['current_progress'] = min(progress_state['current_progress'] + 5, max_progress - 5)
            elif "完成" in line:
                progress_state['current_progress'] = max_progress
        
        # 构建状态消息
        if progress_state['chapter_count'] > 0:
            status_msg = f"{progress_state['current_step']} - 章节 {progress_state['processed_chapters']}/{progress_state['chapter_count']}"
        else:
            status_msg = f"{progress_state['current_step']}: {line[:80]}..." if len(line) > 80 else f"{progress_state['current_step']}: {line}"
        
        # 更新任务状态
        task_self.update_state(
            state='PROGRESS',
            meta={
                'current': min(int(progress_state['current_progress']), max_progress),
                'total': 100,
                'status': status_msg,
                'step': progress_state['current_step'],
                'chapter_progress': f"{progress_state['processed_chapters']}/{progress_state['chapter_count']}" if progress_state['chapter_count'] > 0 else None,
                'last_output': line
            }
        )
    
    return progress_callback