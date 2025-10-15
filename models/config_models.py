"""
配置数据模型模块

提供分离后的配置数据模型，包括应用程序配置、引擎配置等。
采用清晰的数据结构，支持配置验证和类型安全。

作者: TTS开发团队
版本: 2.0.0
创建时间: 2024
"""

from dataclasses import dataclass, field
from typing import Dict, Any, List, Optional, Union
from enum import Enum


class ConfigType(Enum):
    """配置类型枚举"""
    APP = "app"           # 应用程序配置
    ENGINE = "engine"     # 引擎配置
    UI = "ui"            # 界面配置
    PERFORMANCE = "performance"  # 性能配置
    USER = "user"        # 用户配置


class EngineStatusEnum(Enum):
    """引擎状态枚举"""
    AVAILABLE = "available"     # 可用
    UNAVAILABLE = "unavailable" # 不可用
    ERROR = "error"            # 错误
    LOADING = "loading"        # 加载中


@dataclass
class UIConfig:
    """界面配置"""
    theme: str = "light"
    language: str = "zh-CN"
    window_width: int = 1200
    window_height: int = 800
    window_x: int = 100
    window_y: int = 100
    font_size: int = 12
    font_family: str = "Microsoft YaHei"
    auto_save: bool = True
    auto_save_interval: int = 300


@dataclass
class FileConfig:
    """文件配置"""
    input_dir: str = "./input"
    output_dir: str = "./output"
    temp_dir: str = "./temp"
    cache_dir: str = "./cache"
    backup_dir: str = "./backups"
    max_file_size_mb: int = 100
    auto_clean_temp: bool = True
    auto_clean_interval: int = 3600


@dataclass
class PerformanceConfig:
    """性能配置"""
    max_concurrent_tasks: int = 2
    memory_limit_mb: int = 1024
    enable_hardware_acceleration: bool = False
    enable_caching: bool = True
    cache_duration: int = 3600
    max_cache_size: int = 100
    enable_profiling: bool = False


@dataclass
class UserPreferences:
    """用户偏好配置"""
    default_engine: str = "piper_tts"
    default_voice: str = "default"
    default_rate: float = 1.0
    default_pitch: float = 0.0
    default_volume: float = 1.0
    default_language: str = "zh-CN"
    default_format: str = "wav"
    remember_settings: bool = True
    show_tooltips: bool = True
    auto_update_check: bool = True


@dataclass
class AppConfig:
    """应用程序配置"""
    version: str = "2.0.0"
    ui: UIConfig = field(default_factory=UIConfig)
    files: FileConfig = field(default_factory=FileConfig)
    performance: PerformanceConfig = field(default_factory=PerformanceConfig)
    preferences: UserPreferences = field(default_factory=UserPreferences)
    debug_mode: bool = False
    log_level: str = "INFO"
    created_at: str = ""
    updated_at: str = ""


@dataclass
class EngineInfo:
    """引擎信息"""
    id: str
    name: str
    version: str
    description: str
    author: str
    website: str
    license: str
    supported_languages: List[str] = field(default_factory=list)
    supported_formats: List[str] = field(default_factory=list)
    is_online: bool = False
    requires_auth: bool = False


@dataclass
class EngineParameters:
    """引擎参数"""
    voice_name: str = "default"
    rate: float = 1.0
    pitch: float = 0.0
    volume: float = 1.0
    language: str = "zh-CN"
    output_format: str = "wav"
    extra_params: Dict[str, Any] = field(default_factory=dict)


@dataclass
class EngineStatus:
    """引擎状态"""
    status: EngineStatusEnum = EngineStatusEnum.UNAVAILABLE
    last_check: str = ""
    error_message: str = ""
    available_voices: List[Dict[str, Any]] = field(default_factory=list)
    performance_metrics: Dict[str, Any] = field(default_factory=dict)


@dataclass
class EngineConfig:
    """引擎配置"""
    info: EngineInfo
    parameters: EngineParameters
    status: EngineStatus
    config_version: str = "1.0.0"
    enabled: bool = True
    priority: int = 0
    created_at: str = ""
    updated_at: str = ""


@dataclass
class ConfigRegistry:
    """配置注册表"""
    app_config: AppConfig = field(default_factory=AppConfig)
    engine_configs: Dict[str, EngineConfig] = field(default_factory=dict)
    config_version: str = "2.0.0"
    last_updated: str = ""
    
    def get_engine_config(self, engine_id: str) -> Optional[EngineConfig]:
        """获取引擎配置"""
        return self.engine_configs.get(engine_id)
    
    def set_engine_config(self, engine_id: str, config: EngineConfig):
        """设置引擎配置"""
        self.engine_configs[engine_id] = config
    
    def remove_engine_config(self, engine_id: str):
        """移除引擎配置"""
        if engine_id in self.engine_configs:
            del self.engine_configs[engine_id]
    
    def get_available_engines(self) -> List[str]:
        """获取可用引擎列表"""
        return [
            engine_id for engine_id, config in self.engine_configs.items()
            if config.enabled and config.status.status == EngineStatusEnum.AVAILABLE
        ]
    
    def get_engine_priority_order(self) -> List[str]:
        """获取引擎优先级顺序"""
        return sorted(
            self.engine_configs.keys(),
            key=lambda x: self.engine_configs[x].priority,
            reverse=True
        )
