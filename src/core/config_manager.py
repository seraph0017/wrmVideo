#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
统一配置管理器
提供配置的统一管理、验证和环境变量支持
"""

import os
import json
import yaml
from typing import Any, Dict, Optional, Union, List
from pathlib import Path
from dataclasses import dataclass, field
from .interfaces import IConfigManager


@dataclass
class ConfigSchema:
    """配置模式定义"""
    key: str
    required: bool = False
    default: Any = None
    validator: Optional[callable] = None
    description: str = ""
    env_var: Optional[str] = None  # 对应的环境变量名


class ConfigManager(IConfigManager):
    """统一配置管理器
    
    功能：
    - 支持多种配置源（文件、环境变量、代码）
    - 配置验证
    - 配置热重载
    - 环境变量覆盖
    - 配置模式定义
    """
    
    def __init__(self, config_dir: str = None, env_prefix: str = "WRM"):
        """
        初始化配置管理器
        
        Args:
            config_dir: 配置文件目录
            env_prefix: 环境变量前缀
        """
        self.config_dir = Path(config_dir) if config_dir else Path(__file__).parent.parent.parent / "config"
        self.env_prefix = env_prefix
        self._config_data: Dict[str, Any] = {}
        self._schemas: Dict[str, ConfigSchema] = {}
        self._file_timestamps: Dict[str, float] = {}
        
        # 定义配置模式
        self._define_schemas()
        
        # 加载配置
        self.reload_config()
    
    def _define_schemas(self) -> None:
        """定义配置模式"""
        # TTS配置
        self.register_schema(ConfigSchema(
            key="tts.appid",
            required=True,
            env_var="TTS_APPID",
            description="TTS应用ID"
        ))
        
        self.register_schema(ConfigSchema(
            key="tts.access_token",
            required=True,
            env_var="TTS_ACCESS_TOKEN",
            description="TTS访问令牌"
        ))
        
        self.register_schema(ConfigSchema(
            key="tts.voice_type",
            default="BV115_streaming",
            env_var="TTS_VOICE_TYPE",
            description="TTS语音类型"
        ))
        
        self.register_schema(ConfigSchema(
            key="tts.sample_rate",
            default=44100,
            validator=lambda x: isinstance(x, int) and x > 0,
            description="TTS采样率"
        ))
        
        # ARK配置
        self.register_schema(ConfigSchema(
            key="ark.api_key",
            required=True,
            env_var="ARK_API_KEY",
            description="ARK API密钥"
        ))
        
        self.register_schema(ConfigSchema(
            key="ark.base_url",
            default="https://ark.cn-beijing.volces.com/api/v3",
            env_var="ARK_BASE_URL",
            description="ARK基础URL"
        ))
        
        self.register_schema(ConfigSchema(
            key="ark.model",
            default="doubao-seed-1-6-flash-250615",
            env_var="ARK_MODEL",
            description="ARK模型名称"
        ))
        
        # 图片生成配置
        self.register_schema(ConfigSchema(
            key="image.access_key",
            required=True,
            env_var="IMAGE_ACCESS_KEY",
            description="图片生成访问密钥"
        ))
        
        self.register_schema(ConfigSchema(
            key="image.secret_key",
            required=True,
            env_var="IMAGE_SECRET_KEY",
            description="图片生成密钥"
        ))
        
        self.register_schema(ConfigSchema(
            key="image.default_width",
            default=1024,
            validator=lambda x: isinstance(x, int) and x > 0,
            description="默认图片宽度"
        ))
        
        self.register_schema(ConfigSchema(
            key="image.default_height",
            default=1024,
            validator=lambda x: isinstance(x, int) and x > 0,
            description="默认图片高度"
        ))
        
        self.register_schema(ConfigSchema(
            key="image.default_style",
            default="manga",
            description="默认艺术风格"
        ))
        
        # 脚本生成配置
        self.register_schema(ConfigSchema(
            key="script.chunk_size",
            default=80000,
            validator=lambda x: isinstance(x, int) and x > 0,
            description="文本块大小"
        ))
        
        self.register_schema(ConfigSchema(
            key="script.max_chapters",
            default=60,
            validator=lambda x: isinstance(x, int) and x > 0,
            description="最大章节数"
        ))
    
    def register_schema(self, schema: ConfigSchema) -> None:
        """注册配置模式"""
        self._schemas[schema.key] = schema
    
    def reload_config(self) -> None:
        """重新加载配置"""
        # 清空现有配置
        self._config_data.clear()
        
        # 加载配置文件
        self._load_config_files()
        
        # 应用环境变量覆盖
        self._apply_env_overrides()
        
        # 应用默认值
        self._apply_defaults()
        
        # 验证配置
        if not self.validate_config():
            raise ValueError("配置验证失败")
    
    def _load_config_files(self) -> None:
        """加载配置文件"""
        config_files = [
            "config.py",
            "config.json",
            "config.yaml",
            "config.yml"
        ]
        
        for filename in config_files:
            file_path = self.config_dir / filename
            if file_path.exists():
                self._load_config_file(file_path)
    
    def _load_config_file(self, file_path: Path) -> None:
        """加载单个配置文件"""
        try:
            # 记录文件时间戳
            self._file_timestamps[str(file_path)] = file_path.stat().st_mtime
            
            if file_path.suffix == '.py':
                self._load_python_config(file_path)
            elif file_path.suffix == '.json':
                self._load_json_config(file_path)
            elif file_path.suffix in ['.yaml', '.yml']:
                self._load_yaml_config(file_path)
                
        except Exception as e:
            print(f"加载配置文件失败 {file_path}: {e}")
    
    def _load_python_config(self, file_path: Path) -> None:
        """加载Python配置文件"""
        import importlib.util
        
        spec = importlib.util.spec_from_file_location("config", file_path)
        config_module = importlib.util.module_from_spec(spec)
        spec.loader.exec_module(config_module)
        
        # 提取配置变量
        for attr_name in dir(config_module):
            if not attr_name.startswith('_'):
                attr_value = getattr(config_module, attr_name)
                if isinstance(attr_value, dict):
                    self._merge_config_dict(attr_name.lower(), attr_value)
    
    def _load_json_config(self, file_path: Path) -> None:
        """加载JSON配置文件"""
        with open(file_path, 'r', encoding='utf-8') as f:
            config_data = json.load(f)
            self._merge_config_dict("", config_data)
    
    def _load_yaml_config(self, file_path: Path) -> None:
        """加载YAML配置文件"""
        with open(file_path, 'r', encoding='utf-8') as f:
            config_data = yaml.safe_load(f)
            self._merge_config_dict("", config_data)
    
    def _merge_config_dict(self, prefix: str, config_dict: Dict[str, Any]) -> None:
        """合并配置字典"""
        for key, value in config_dict.items():
            full_key = f"{prefix}.{key}" if prefix else key
            
            if isinstance(value, dict):
                self._merge_config_dict(full_key, value)
            else:
                self._config_data[full_key.lower()] = value
    
    def _apply_env_overrides(self) -> None:
        """应用环境变量覆盖"""
        for schema in self._schemas.values():
            if schema.env_var:
                env_value = os.getenv(schema.env_var)
                if env_value is not None:
                    # 尝试转换类型
                    converted_value = self._convert_env_value(env_value, schema)
                    self._config_data[schema.key] = converted_value
    
    def _convert_env_value(self, env_value: str, schema: ConfigSchema) -> Any:
        """转换环境变量值"""
        # 根据默认值类型进行转换
        if schema.default is not None:
            if isinstance(schema.default, bool):
                return env_value.lower() in ('true', '1', 'yes', 'on')
            elif isinstance(schema.default, int):
                return int(env_value)
            elif isinstance(schema.default, float):
                return float(env_value)
        
        return env_value
    
    def _apply_defaults(self) -> None:
        """应用默认值"""
        for schema in self._schemas.values():
            if schema.key not in self._config_data and schema.default is not None:
                self._config_data[schema.key] = schema.default
    
    def get_config(self, key: str, default: Any = None) -> Any:
        """获取配置值"""
        return self._config_data.get(key.lower(), default)
    
    def set_config(self, key: str, value: Any) -> None:
        """设置配置值"""
        self._config_data[key.lower()] = value
    
    def validate_config(self) -> bool:
        """验证配置"""
        errors = []
        
        for schema in self._schemas.values():
            key = schema.key
            value = self._config_data.get(key)
            
            # 检查必需配置
            if schema.required and value is None:
                errors.append(f"缺少必需配置: {key}")
                continue
            
            # 验证配置值
            if value is not None and schema.validator:
                if not schema.validator(value):
                    errors.append(f"配置验证失败: {key} = {value}")
        
        if errors:
            for error in errors:
                print(f"配置错误: {error}")
            return False
        
        return True
    
    def get_config_group(self, prefix: str) -> Dict[str, Any]:
        """获取配置组"""
        prefix = prefix.lower()
        result = {}
        
        for key, value in self._config_data.items():
            if key.startswith(f"{prefix}."):
                sub_key = key[len(prefix) + 1:]
                result[sub_key] = value
        
        return result
    
    def has_config_changed(self) -> bool:
        """检查配置文件是否有变化"""
        for file_path, old_timestamp in self._file_timestamps.items():
            path = Path(file_path)
            if path.exists():
                current_timestamp = path.stat().st_mtime
                if current_timestamp != old_timestamp:
                    return True
        return False
    
    def get_all_configs(self) -> Dict[str, Any]:
        """获取所有配置"""
        return self._config_data.copy()
    
    def export_config(self, file_path: str, format: str = "json") -> None:
        """导出配置到文件"""
        if format.lower() == "json":
            with open(file_path, 'w', encoding='utf-8') as f:
                json.dump(self._config_data, f, indent=2, ensure_ascii=False)
        elif format.lower() in ["yaml", "yml"]:
            with open(file_path, 'w', encoding='utf-8') as f:
                yaml.dump(self._config_data, f, default_flow_style=False, allow_unicode=True)
        else:
            raise ValueError(f"不支持的导出格式: {format}")
    
    def __str__(self) -> str:
        return f"ConfigManager(配置项数量: {len(self._config_data)}, 模式数量: {len(self._schemas)})"


# 全局配置管理器实例
_global_config_manager: Optional[ConfigManager] = None


def get_config_manager() -> ConfigManager:
    """获取全局配置管理器实例"""
    global _global_config_manager
    if _global_config_manager is None:
        _global_config_manager = ConfigManager()
    return _global_config_manager


def set_config_manager(config_manager: ConfigManager) -> None:
    """设置全局配置管理器实例"""
    global _global_config_manager
    _global_config_manager = config_manager