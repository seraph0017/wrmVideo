#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
基础生成器类
提供生成器的通用功能实现
"""

import os
import time
import logging
from typing import Any, Dict, List, Optional
from abc import ABC

from .interfaces import (
    IGenerator, IEventHandler, ILogger, IConfigManager,
    GenerationResult, GenerationStatus
)


class DefaultLogger(ILogger):
    """默认日志记录器实现"""
    
    def __init__(self, name: str = "generator"):
        self.logger = logging.getLogger(name)
        if not self.logger.handlers:
            handler = logging.StreamHandler()
            formatter = logging.Formatter(
                '%(asctime)s - %(name)s - %(levelname)s - %(message)s'
            )
            handler.setFormatter(formatter)
            self.logger.addHandler(handler)
            self.logger.setLevel(logging.INFO)
    
    def debug(self, message: str, **kwargs) -> None:
        self.logger.debug(message, extra=kwargs)
    
    def info(self, message: str, **kwargs) -> None:
        self.logger.info(message, extra=kwargs)
    
    def warning(self, message: str, **kwargs) -> None:
        self.logger.warning(message, extra=kwargs)
    
    def error(self, message: str, **kwargs) -> None:
        self.logger.error(message, extra=kwargs)


class DefaultEventHandler(IEventHandler):
    """默认事件处理器实现"""
    
    def __init__(self, logger: ILogger = None):
        self.logger = logger or DefaultLogger("event_handler")
    
    def on_generation_start(self, generator_type: str, input_data: Any) -> None:
        self.logger.info(f"开始生成 {generator_type}")
    
    def on_generation_complete(self, generator_type: str, result: GenerationResult) -> None:
        if result.is_success:
            self.logger.info(f"{generator_type} 生成成功: {result.output_path}")
        else:
            self.logger.error(f"{generator_type} 生成失败: {result.error_message}")
    
    def on_generation_error(self, generator_type: str, error: Exception) -> None:
        self.logger.error(f"{generator_type} 生成异常: {str(error)}")


class BaseGenerator(IGenerator, ABC):
    """基础生成器类
    
    提供所有生成器的通用功能：
    - 配置管理
    - 事件处理
    - 日志记录
    - 错误处理
    - 性能监控
    """
    
    def __init__(self, 
                 config_manager: IConfigManager = None,
                 event_handler: IEventHandler = None,
                 logger: ILogger = None,
                 name: str = None):
        """
        初始化基础生成器
        
        Args:
            config_manager: 配置管理器
            event_handler: 事件处理器
            logger: 日志记录器
            name: 生成器名称
        """
        self.name = name or self.__class__.__name__
        self.config_manager = config_manager
        self.event_handler = event_handler or DefaultEventHandler()
        self.logger = logger or DefaultLogger(self.name)
        
        # 性能统计
        self._generation_count = 0
        self._total_duration = 0.0
        self._success_count = 0
        self._error_count = 0
    
    def generate(self, input_data: Any, output_path: str, **kwargs) -> GenerationResult:
        """生成内容的通用流程"""
        start_time = time.time()
        self._generation_count += 1
        
        try:
            # 触发开始事件
            self.event_handler.on_generation_start(self.name, input_data)
            
            # 验证输入
            if not self.validate_input(input_data):
                raise ValueError(f"无效的输入数据: {type(input_data)}")
            
            # 确保输出目录存在
            self._ensure_output_directory(output_path)
            
            # 执行具体的生成逻辑
            result = self._do_generate(input_data, output_path, **kwargs)
            
            # 计算耗时
            duration = time.time() - start_time
            result.duration = duration
            self._total_duration += duration
            
            # 更新统计
            if result.is_success:
                self._success_count += 1
            else:
                self._error_count += 1
            
            # 触发完成事件
            self.event_handler.on_generation_complete(self.name, result)
            
            return result
            
        except Exception as e:
            # 处理异常
            duration = time.time() - start_time
            self._error_count += 1
            
            error_result = GenerationResult(
                status=GenerationStatus.FAILED,
                error_message=str(e),
                duration=duration
            )
            
            # 触发错误事件
            self.event_handler.on_generation_error(self.name, e)
            
            return error_result
    
    def _do_generate(self, input_data: Any, output_path: str, **kwargs) -> GenerationResult:
        """具体的生成逻辑，由子类实现"""
        raise NotImplementedError("子类必须实现 _do_generate 方法")
    
    def _ensure_output_directory(self, output_path: str) -> None:
        """确保输出目录存在"""
        output_dir = os.path.dirname(output_path)
        if output_dir and not os.path.exists(output_dir):
            os.makedirs(output_dir, exist_ok=True)
            self.logger.debug(f"创建输出目录: {output_dir}")
    
    def get_config(self, key: str, default: Any = None) -> Any:
        """获取配置值"""
        if self.config_manager:
            return self.config_manager.get_config(key, default)
        return default
    
    def get_statistics(self) -> Dict[str, Any]:
        """获取生成器统计信息"""
        avg_duration = self._total_duration / max(self._generation_count, 1)
        success_rate = self._success_count / max(self._generation_count, 1)
        
        return {
            "name": self.name,
            "generation_count": self._generation_count,
            "success_count": self._success_count,
            "error_count": self._error_count,
            "success_rate": success_rate,
            "total_duration": self._total_duration,
            "average_duration": avg_duration
        }
    
    def reset_statistics(self) -> None:
        """重置统计信息"""
        self._generation_count = 0
        self._total_duration = 0.0
        self._success_count = 0
        self._error_count = 0
        self.logger.info(f"{self.name} 统计信息已重置")
    
    def validate_input(self, input_data: Any) -> bool:
        """默认的输入验证"""
        return input_data is not None
    
    def get_supported_formats(self) -> List[str]:
        """默认支持的格式"""
        return []
    
    def __str__(self) -> str:
        return f"{self.name}(生成次数: {self._generation_count}, 成功率: {self._success_count/max(self._generation_count, 1):.2%})"
    
    def __repr__(self) -> str:
        return f"{self.__class__.__name__}(name='{self.name}')"


class BatchGenerator(BaseGenerator):
    """批量生成器基类
    
    提供批量处理的通用功能
    """
    
    def __init__(self, batch_size: int = 10, **kwargs):
        super().__init__(**kwargs)
        self.batch_size = batch_size
    
    def generate_batch(self, input_list: List[Any], output_dir: str, **kwargs) -> List[GenerationResult]:
        """批量生成"""
        results = []
        total_items = len(input_list)
        
        self.logger.info(f"开始批量生成，总数: {total_items}，批次大小: {self.batch_size}")
        
        for i in range(0, total_items, self.batch_size):
            batch = input_list[i:i + self.batch_size]
            batch_results = self._process_batch(batch, output_dir, i, **kwargs)
            results.extend(batch_results)
            
            # 进度报告
            completed = min(i + self.batch_size, total_items)
            progress = completed / total_items * 100
            self.logger.info(f"批量生成进度: {completed}/{total_items} ({progress:.1f}%)")
        
        # 统计结果
        success_count = sum(1 for r in results if r.is_success)
        self.logger.info(f"批量生成完成，成功: {success_count}/{total_items}")
        
        return results
    
    def _process_batch(self, batch: List[Any], output_dir: str, batch_index: int, **kwargs) -> List[GenerationResult]:
        """处理单个批次，由子类实现"""
        results = []
        for i, item in enumerate(batch):
            output_path = os.path.join(output_dir, f"item_{batch_index + i:03d}")
            result = self.generate(item, output_path, **kwargs)
            results.append(result)
        return results