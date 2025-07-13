#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
核心接口定义
定义项目中各个组件的抽象接口，遵循开闭原则
"""

from abc import ABC, abstractmethod
from typing import Dict, List, Optional, Any, Union
from dataclasses import dataclass
from enum import Enum


class GenerationStatus(Enum):
    """生成状态枚举"""
    PENDING = "pending"
    PROCESSING = "processing"
    SUCCESS = "success"
    FAILED = "failed"
    CANCELLED = "cancelled"


@dataclass
class GenerationResult:
    """生成结果数据类"""
    status: GenerationStatus
    output_path: Optional[str] = None
    error_message: Optional[str] = None
    metadata: Optional[Dict[str, Any]] = None
    duration: Optional[float] = None

    @property
    def is_success(self) -> bool:
        """是否成功"""
        return self.status == GenerationStatus.SUCCESS

    @property
    def is_failed(self) -> bool:
        """是否失败"""
        return self.status == GenerationStatus.FAILED


class IConfigManager(ABC):
    """配置管理器接口"""
    
    @abstractmethod
    def get_config(self, key: str, default: Any = None) -> Any:
        """获取配置值"""
        pass
    
    @abstractmethod
    def set_config(self, key: str, value: Any) -> None:
        """设置配置值"""
        pass
    
    @abstractmethod
    def validate_config(self) -> bool:
        """验证配置"""
        pass
    
    @abstractmethod
    def reload_config(self) -> None:
        """重新加载配置"""
        pass


class IGenerator(ABC):
    """生成器基础接口"""
    
    @abstractmethod
    def generate(self, input_data: Any, output_path: str, **kwargs) -> GenerationResult:
        """生成内容"""
        pass
    
    @abstractmethod
    def validate_input(self, input_data: Any) -> bool:
        """验证输入数据"""
        pass
    
    @abstractmethod
    def get_supported_formats(self) -> List[str]:
        """获取支持的格式"""
        pass


class IScriptGenerator(IGenerator):
    """脚本生成器接口"""
    
    @abstractmethod
    def generate_script(self, novel_content: str, output_path: str, **kwargs) -> GenerationResult:
        """生成脚本"""
        pass
    
    @abstractmethod
    def split_chapters(self, script_content: str) -> List[Dict[str, Any]]:
        """分割章节"""
        pass
    
    @abstractmethod
    def validate_script_format(self, script_content: str) -> bool:
        """验证脚本格式"""
        pass


class IImageGenerator(IGenerator):
    """图片生成器接口"""
    
    @abstractmethod
    def generate_image(self, prompt: str, output_path: str, style: str = None, **kwargs) -> GenerationResult:
        """生成图片"""
        pass
    
    @abstractmethod
    def generate_images_batch(self, prompts: List[str], output_dir: str, **kwargs) -> List[GenerationResult]:
        """批量生成图片"""
        pass
    
    @abstractmethod
    def get_available_styles(self) -> List[str]:
        """获取可用的艺术风格"""
        pass
    
    @abstractmethod
    def enhance_prompt(self, prompt: str, context: Dict[str, Any] = None) -> str:
        """增强提示词"""
        pass


class IVoiceGenerator(IGenerator):
    """语音生成器接口"""
    
    @abstractmethod
    def generate_voice(self, text: str, output_path: str, preset: str = "default", **kwargs) -> GenerationResult:
        """生成语音"""
        pass
    
    @abstractmethod
    def generate_voices_batch(self, texts: List[str], output_dir: str, **kwargs) -> List[GenerationResult]:
        """批量生成语音"""
        pass
    
    @abstractmethod
    def get_available_presets(self) -> List[str]:
        """获取可用的语音预设"""
        pass
    
    @abstractmethod
    def clean_text_for_tts(self, text: str) -> str:
        """清理文本用于TTS"""
        pass


class IVideoGenerator(IGenerator):
    """视频生成器接口"""
    
    @abstractmethod
    def generate_video_from_images(self, image_paths: List[str], audio_path: str, 
                                 output_path: str, **kwargs) -> GenerationResult:
        """从图片和音频生成视频"""
        pass
    
    @abstractmethod
    def add_subtitles(self, video_path: str, subtitle_text: str, 
                     output_path: str, **kwargs) -> GenerationResult:
        """添加字幕"""
        pass
    
    @abstractmethod
    def get_video_info(self, video_path: str) -> Dict[str, Any]:
        """获取视频信息"""
        pass


class IWorkflowOrchestrator(ABC):
    """工作流编排器接口"""
    
    @abstractmethod
    def execute_workflow(self, workflow_config: Dict[str, Any]) -> List[GenerationResult]:
        """执行工作流"""
        pass
    
    @abstractmethod
    def register_generator(self, name: str, generator: IGenerator) -> None:
        """注册生成器"""
        pass
    
    @abstractmethod
    def get_workflow_status(self, workflow_id: str) -> Dict[str, Any]:
        """获取工作流状态"""
        pass


class IEventHandler(ABC):
    """事件处理器接口"""
    
    @abstractmethod
    def on_generation_start(self, generator_type: str, input_data: Any) -> None:
        """生成开始事件"""
        pass
    
    @abstractmethod
    def on_generation_complete(self, generator_type: str, result: GenerationResult) -> None:
        """生成完成事件"""
        pass
    
    @abstractmethod
    def on_generation_error(self, generator_type: str, error: Exception) -> None:
        """生成错误事件"""
        pass


class ILogger(ABC):
    """日志记录器接口"""
    
    @abstractmethod
    def debug(self, message: str, **kwargs) -> None:
        """调试日志"""
        pass
    
    @abstractmethod
    def info(self, message: str, **kwargs) -> None:
        """信息日志"""
        pass
    
    @abstractmethod
    def warning(self, message: str, **kwargs) -> None:
        """警告日志"""
        pass
    
    @abstractmethod
    def error(self, message: str, **kwargs) -> None:
        """错误日志"""
        pass