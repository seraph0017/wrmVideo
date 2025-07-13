# -*- coding: utf-8 -*-
"""
工作流编排器 - 重构版本

遵循SRP原则：专注于工作流编排
遵循DI原则：通过依赖注入获取各个生成器
遵循OCP原则：通过接口扩展工作流
"""

import os
import json
from typing import Dict, List, Any, Optional, Callable
from dataclasses import dataclass
from enum import Enum

from .interfaces import (
    IWorkflowOrchestrator, IScriptGenerator, IImageGenerator, 
    IVoiceGenerator, IVideoGenerator, IEventHandler, ILogger,
    GenerationResult, GenerationStatus
)
from .config_manager import ConfigManager


class WorkflowStep(Enum):
    """工作流步骤枚举"""
    SCRIPT_GENERATION = "script_generation"
    IMAGE_GENERATION = "image_generation"
    VOICE_GENERATION = "voice_generation"
    VIDEO_GENERATION = "video_generation"
    POST_PROCESSING = "post_processing"


@dataclass
class WorkflowConfig:
    """工作流配置"""
    steps: List[WorkflowStep]
    parallel_steps: List[List[WorkflowStep]]  # 可并行执行的步骤组
    retry_count: int = 3
    timeout: int = 3600  # 超时时间（秒）
    output_dir: str = "output"
    cleanup_on_failure: bool = True


@dataclass
class StepResult:
    """步骤执行结果"""
    step: WorkflowStep
    status: GenerationStatus
    result: Optional[GenerationResult] = None
    error_message: Optional[str] = None
    execution_time: float = 0.0
    retry_count: int = 0


class WorkflowOrchestrator(IWorkflowOrchestrator):
    """
    工作流编排器实现
    
    负责协调各个生成器的执行顺序和依赖关系
    """
    
    def __init__(
        self,
        config_manager: ConfigManager,
        script_generator: IScriptGenerator = None,
        image_generator: IImageGenerator = None,
        voice_generator: IVoiceGenerator = None,
        video_generator: IVideoGenerator = None,
        event_handler: IEventHandler = None,
        logger: ILogger = None
    ):
        """
        初始化工作流编排器
        
        Args:
            config_manager: 配置管理器
            script_generator: 脚本生成器
            image_generator: 图片生成器
            voice_generator: 语音生成器
            video_generator: 视频生成器
            event_handler: 事件处理器
            logger: 日志记录器
        """
        self.config_manager = config_manager
        self.script_generator = script_generator
        self.image_generator = image_generator
        self.voice_generator = voice_generator
        self.video_generator = video_generator
        self.event_handler = event_handler
        self.logger = logger
        
        # 工作流状态
        self._current_workflow = None
        self._step_results: Dict[WorkflowStep, StepResult] = {}
        self._workflow_data: Dict[str, Any] = {}
        
        # 步骤处理器映射
        self._step_handlers = {
            WorkflowStep.SCRIPT_GENERATION: self._handle_script_generation,
            WorkflowStep.IMAGE_GENERATION: self._handle_image_generation,
            WorkflowStep.VOICE_GENERATION: self._handle_voice_generation,
            WorkflowStep.VIDEO_GENERATION: self._handle_video_generation,
            WorkflowStep.POST_PROCESSING: self._handle_post_processing
        }
    
    def execute_workflow(self, workflow_config: Dict[str, Any]) -> List[GenerationResult]:
        """执行完整工作流
        
        Args:
            workflow_config: 工作流配置字典
        
        Returns:
            List[GenerationResult]: 工作流执行结果列表
        """
        try:
            # 解析工作流配置
            steps = workflow_config.get('steps', [])
            output_dir = workflow_config.get('output_dir', 'output')
            input_data = workflow_config.get('input_data')
            
            # 创建WorkflowConfig对象
            from enum import Enum
            step_enums = []
            for step_name in steps:
                if hasattr(WorkflowStep, step_name.upper()):
                    step_enums.append(getattr(WorkflowStep, step_name.upper()))
            
            config = WorkflowConfig(
                steps=step_enums,
                parallel_steps=[],
                output_dir=output_dir
            )
            
            self._current_workflow = config
            self._step_results.clear()
            self._workflow_data.clear()
            
            # 初始化工作流数据
            self._workflow_data['input'] = input_data
            self._workflow_data['config'] = config
            self._workflow_data['kwargs'] = workflow_config.get('kwargs', {})
            
            # 创建输出目录
            os.makedirs(config.output_dir, exist_ok=True)
            
            self._log_info(f"开始执行工作流，包含 {len(config.steps)} 个步骤")
            
            # 执行工作流步骤
            results = []
            for step in config.steps:
                step_result = self._execute_step(step)
                self._step_results[step] = step_result
                
                if step_result.result:
                    results.append(step_result.result)
                
                if step_result.status == GenerationStatus.FAILED:
                    error_msg = f"步骤 {step.value} 执行失败: {step_result.error_message}"
                    self._log_error(error_msg)
                    
                    if config.cleanup_on_failure:
                        self._cleanup_on_failure()
                    
                    # 添加失败结果
                    results.append(GenerationResult(
                        status=GenerationStatus.FAILED,
                        error_message=error_msg,
                        metadata={
                            'failed_step': step.value,
                            'step_results': self._get_step_results_summary()
                        }
                    ))
                    return results
                
                self._log_info(f"步骤 {step.value} 执行成功")
            
            # 工作流执行成功
            self._log_info("工作流执行完成")
            
            # 添加总结结果
            results.append(GenerationResult(
                status=GenerationStatus.SUCCESS,
                output_path=config.output_dir,
                metadata={
                    'step_results': self._get_step_results_summary(),
                    'total_execution_time': sum(
                        result.execution_time for result in self._step_results.values()
                    )
                }
            ))
            
            return results
            
        except Exception as e:
            error_msg = f"工作流执行异常: {str(e)}"
            self._log_error(error_msg)
            
            return [GenerationResult(
                status=GenerationStatus.FAILED,
                error_message=error_msg
            )]
    
    def _execute_step(self, step: WorkflowStep) -> StepResult:
        """
        执行单个工作流步骤
        
        Args:
            step: 工作流步骤
        
        Returns:
            StepResult: 步骤执行结果
        """
        import time
        
        start_time = time.time()
        retry_count = 0
        max_retries = self._current_workflow.retry_count
        
        while retry_count <= max_retries:
            try:
                self._log_info(f"执行步骤: {step.value} (尝试 {retry_count + 1}/{max_retries + 1})")
                
                # 获取步骤处理器
                handler = self._step_handlers.get(step)
                if not handler:
                    raise ValueError(f"未找到步骤 {step.value} 的处理器")
                
                # 执行步骤
                result = handler()
                
                if result and result.status == GenerationStatus.SUCCESS:
                    execution_time = time.time() - start_time
                    return StepResult(
                        step=step,
                        status=GenerationStatus.SUCCESS,
                        result=result,
                        execution_time=execution_time,
                        retry_count=retry_count
                    )
                else:
                    retry_count += 1
                    if retry_count <= max_retries:
                        self._log_warning(f"步骤 {step.value} 执行失败，准备重试")
                        time.sleep(2 ** retry_count)  # 指数退避
                    
            except Exception as e:
                retry_count += 1
                error_msg = str(e)
                
                if retry_count <= max_retries:
                    self._log_warning(f"步骤 {step.value} 执行异常，准备重试: {error_msg}")
                    time.sleep(2 ** retry_count)
                else:
                    execution_time = time.time() - start_time
                    return StepResult(
                        step=step,
                        status=GenerationStatus.FAILED,
                        error_message=error_msg,
                        execution_time=execution_time,
                        retry_count=retry_count - 1
                    )
        
        # 所有重试都失败了
        execution_time = time.time() - start_time
        return StepResult(
            step=step,
            status=GenerationStatus.FAILED,
            error_message="达到最大重试次数",
            execution_time=execution_time,
            retry_count=max_retries
        )
    
    def _handle_script_generation(self) -> GenerationResult:
        """处理脚本生成步骤"""
        if not self.script_generator:
            raise ValueError("脚本生成器未配置")
        
        input_data = self._workflow_data['input']
        output_path = os.path.join(
            self._current_workflow.output_dir, 
            "script.xml"
        )
        
        result = self.script_generator.generate(input_data, output_path)
        
        # 保存脚本数据供后续步骤使用
        if result.status == GenerationStatus.SUCCESS:
            self._workflow_data['script_path'] = result.output_path
            # 解析脚本内容
            self._parse_script_content(result.output_path)
        
        return result
    
    def _handle_image_generation(self) -> GenerationResult:
        """处理图片生成步骤"""
        if not self.image_generator:
            raise ValueError("图片生成器未配置")
        
        # 从脚本数据中获取图片提示
        image_prompts = self._workflow_data.get('image_prompts', [])
        if not image_prompts:
            return GenerationResult(
                status=GenerationStatus.FAILED,
                error_message="未找到图片生成提示"
            )
        
        output_dir = os.path.join(self._current_workflow.output_dir, "images")
        
        result = self.image_generator.generate(image_prompts, output_dir)
        
        # 保存图片路径供后续步骤使用
        if result.status == GenerationStatus.SUCCESS:
            self._workflow_data['image_paths'] = result.metadata.get('successful_files', [])
        
        return result
    
    def _handle_voice_generation(self) -> GenerationResult:
        """处理语音生成步骤"""
        if not self.voice_generator:
            raise ValueError("语音生成器未配置")
        
        # 从脚本数据中获取解说文本
        narration_texts = self._workflow_data.get('narration_texts', [])
        if not narration_texts:
            return GenerationResult(
                status=GenerationStatus.FAILED,
                error_message="未找到解说文本"
            )
        
        output_dir = os.path.join(self._current_workflow.output_dir, "voices")
        
        result = self.voice_generator.generate(narration_texts, output_dir)
        
        # 保存语音路径供后续步骤使用
        if result.status == GenerationStatus.SUCCESS:
            self._workflow_data['voice_paths'] = result.metadata.get('successful_files', [])
        
        return result
    
    def _handle_video_generation(self) -> GenerationResult:
        """处理视频生成步骤"""
        if not self.video_generator:
            raise ValueError("视频生成器未配置")
        
        # 准备视频生成数据
        video_data = {
            'image_paths': self._workflow_data.get('image_paths', []),
            'voice_paths': self._workflow_data.get('voice_paths', []),
            'script_data': self._workflow_data.get('script_data', {})
        }
        
        output_path = os.path.join(
            self._current_workflow.output_dir, 
            "final_video.mp4"
        )
        
        result = self.video_generator.generate(video_data, output_path)
        
        return result
    
    def _handle_post_processing(self) -> GenerationResult:
        """处理后处理步骤"""
        # 生成工作流报告
        report_path = os.path.join(
            self._current_workflow.output_dir,
            "workflow_report.json"
        )
        
        report_data = {
            'workflow_config': {
                'steps': [step.value for step in self._current_workflow.steps],
                'output_dir': self._current_workflow.output_dir
            },
            'step_results': self._get_step_results_summary(),
            'generated_files': {
                'script': self._workflow_data.get('script_path'),
                'images': self._workflow_data.get('image_paths', []),
                'voices': self._workflow_data.get('voice_paths', []),
                'video': self._workflow_data.get('video_path')
            }
        }
        
        with open(report_path, 'w', encoding='utf-8') as f:
            json.dump(report_data, f, ensure_ascii=False, indent=2)
        
        return GenerationResult(
            status=GenerationStatus.SUCCESS,
            output_path=report_path,
            metadata={'report_data': report_data}
        )
    
    def _parse_script_content(self, script_path: str) -> None:
        """解析脚本内容，提取图片提示和解说文本"""
        try:
            with open(script_path, 'r', encoding='utf-8') as f:
                script_content = f.read()
            
            # 这里应该根据实际的脚本格式进行解析
            # 简化实现，假设脚本中包含特定的标签
            import re
            
            # 提取图片提示
            image_prompts = re.findall(r'<图片prompt>(.*?)</图片prompt>', script_content, re.DOTALL)
            self._workflow_data['image_prompts'] = [prompt.strip() for prompt in image_prompts]
            
            # 提取解说内容
            narration_texts = re.findall(r'<解说内容>(.*?)</解说内容>', script_content, re.DOTALL)
            self._workflow_data['narration_texts'] = [text.strip() for text in narration_texts]
            
            # 保存解析后的脚本数据
            self._workflow_data['script_data'] = {
                'image_prompts': self._workflow_data['image_prompts'],
                'narration_texts': self._workflow_data['narration_texts']
            }
            
        except Exception as e:
            self._log_error(f"解析脚本内容失败: {e}")
    
    def _get_step_results_summary(self) -> Dict[str, Any]:
        """获取步骤结果摘要"""
        summary = {}
        for step, result in self._step_results.items():
            summary[step.value] = {
                'status': result.status.value,
                'execution_time': result.execution_time,
                'retry_count': result.retry_count,
                'error_message': result.error_message
            }
        return summary
    
    def _cleanup_on_failure(self) -> None:
        """失败时清理临时文件"""
        try:
            # 清理已生成的文件
            import shutil
            if os.path.exists(self._current_workflow.output_dir):
                shutil.rmtree(self._current_workflow.output_dir)
                self._log_info("已清理临时文件")
        except Exception as e:
            self._log_error(f"清理临时文件失败: {e}")
    
    def _log_info(self, message: str) -> None:
        """记录信息日志"""
        if self.logger:
            self.logger.info(message)
        else:
            print(f"[INFO] {message}")
    
    def _log_warning(self, message: str) -> None:
        """记录警告日志"""
        if self.logger:
            self.logger.warning(message)
        else:
            print(f"[WARNING] {message}")
    
    def _log_error(self, message: str) -> None:
        """记录错误日志"""
        if self.logger:
            self.logger.error(message)
        else:
            print(f"[ERROR] {message}")
    
    def get_workflow_status(self, workflow_id: str = None) -> Dict[str, Any]:
        """获取工作流状态（实现IWorkflowOrchestrator接口）"""
        if not self._current_workflow:
            return {'status': 'not_started'}
        
        return {
            'status': 'running' if len(self._step_results) < len(self._current_workflow.steps) else 'completed',
            'completed_steps': len(self._step_results),
            'total_steps': len(self._current_workflow.steps),
            'step_results': self._get_step_results_summary()
        }
    
    def register_generator(self, name: str, generator) -> None:
        """注册生成器（实现IWorkflowOrchestrator接口）"""
        if name == 'script':
            self.script_generator = generator
        elif name == 'image':
            self.image_generator = generator
        elif name == 'voice':
            self.voice_generator = generator
        elif name == 'video':
            self.video_generator = generator
        else:
            raise ValueError(f"不支持的生成器类型: {name}")
        
        self._log_info(f"已注册生成器: {name}")
    
    def cancel_workflow(self) -> bool:
        """取消当前工作流"""
        # 实现工作流取消逻辑
        # 这里可以设置取消标志，在步骤执行中检查
        self._log_info("工作流已取消")
        return True