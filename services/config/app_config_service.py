"""
应用程序配置服务

负责应用程序配置的管理，包括界面、文件、性能等配置。
提供配置的加载、保存、验证和迁移功能。

作者: TTS开发团队
版本: 2.0.0
创建时间: 2024
"""

import json
import os
from pathlib import Path
from typing import Optional, Dict, Any
from datetime import datetime

from models.config_models import AppConfig, UIConfig, FileConfig, PerformanceConfig, UserPreferences
from utils.log_manager import LogManager


class AppConfigService:
    """
    应用程序配置服务
    
    负责应用程序配置的管理，包括界面、文件、性能等配置。
    提供配置的加载、保存、验证和迁移功能。
    """
    
    def __init__(self, config_dir: str = "configs/app"):
        self.logger = LogManager().get_logger("AppConfigService")
        self.config_dir = Path(config_dir)
        self.config_dir.mkdir(parents=True, exist_ok=True)
        
        # 配置文件路径
        self.main_config_file = self.config_dir / "main.json"
        self.ui_config_file = self.config_dir / "ui.json"
        self.files_config_file = self.config_dir / "files.json"
        self.performance_config_file = self.config_dir / "performance.json"
        self.preferences_config_file = self.config_dir / "preferences.json"
        
        # 当前配置
        self._current_config: Optional[AppConfig] = None
    
    def load_config(self) -> AppConfig:
        """
        加载应用程序配置
        
        Returns:
            AppConfig: 应用程序配置对象
        """
        try:
            # 加载主配置
            main_config = self._load_json_file(self.main_config_file, {})
            
            # 加载各个子配置
            ui_config = self._load_ui_config()
            files_config = self._load_files_config()
            performance_config = self._load_performance_config()
            preferences_config = self._load_preferences_config()
            
            # 创建配置对象
            config = AppConfig(
                version=main_config.get("version", "2.0.0"),
                ui=ui_config,
                files=files_config,
                performance=performance_config,
                preferences=preferences_config,
                debug_mode=main_config.get("debug_mode", False),
                log_level=main_config.get("log_level", "INFO"),
                created_at=main_config.get("created_at", ""),
                updated_at=main_config.get("updated_at", "")
            )
            
            self._current_config = config
            self.logger.info("应用程序配置加载成功")
            return config
            
        except Exception as e:
            self.logger.error(f"加载应用程序配置失败: {e}")
            # 返回默认配置
            return self._create_default_config()
    
    def save_config(self, config: AppConfig) -> bool:
        """
        保存应用程序配置
        
        Args:
            config (AppConfig): 应用程序配置对象
            
        Returns:
            bool: 保存是否成功
        """
        try:
            # 更新配置时间戳
            config.updated_at = datetime.now().isoformat()
            if not config.created_at:
                config.created_at = config.updated_at
            
            # 保存主配置
            main_config = {
                "version": config.version,
                "debug_mode": config.debug_mode,
                "log_level": config.log_level,
                "created_at": config.created_at,
                "updated_at": config.updated_at
            }
            self._save_json_file(self.main_config_file, main_config)
            
            # 保存各个子配置
            self._save_ui_config(config.ui)
            self._save_files_config(config.files)
            self._save_performance_config(config.performance)
            self._save_preferences_config(config.preferences)
            
            self._current_config = config
            self.logger.info("应用程序配置保存成功")
            return True
            
        except Exception as e:
            self.logger.error(f"保存应用程序配置失败: {e}")
            return False
    
    def get_config(self) -> AppConfig:
        """
        获取当前配置
        
        Returns:
            AppConfig: 当前配置对象
        """
        if self._current_config is None:
            self._current_config = self.load_config()
        return self._current_config
    
    def update_config(self, **kwargs) -> bool:
        """
        更新配置
        
        Args:
            **kwargs: 要更新的配置项
            
        Returns:
            bool: 更新是否成功
        """
        try:
            config = self.get_config()
            
            # 更新配置项
            for key, value in kwargs.items():
                if hasattr(config, key):
                    setattr(config, key, value)
                elif hasattr(config.ui, key):
                    setattr(config.ui, key, value)
                elif hasattr(config.files, key):
                    setattr(config.files, key, value)
                elif hasattr(config.performance, key):
                    setattr(config.performance, key, value)
                elif hasattr(config.preferences, key):
                    setattr(config.preferences, key, value)
            
            return self.save_config(config)
            
        except Exception as e:
            self.logger.error(f"更新配置失败: {e}")
            return False
    
    def reset_to_defaults(self) -> bool:
        """
        重置为默认配置
        
        Returns:
            bool: 重置是否成功
        """
        try:
            default_config = self._create_default_config()
            return self.save_config(default_config)
            
        except Exception as e:
            self.logger.error(f"重置配置失败: {e}")
            return False
    
    def _load_ui_config(self) -> UIConfig:
        """加载界面配置"""
        data = self._load_json_file(self.ui_config_file, {})
        return UIConfig(
            theme=data.get("theme", "light"),
            language=data.get("language", "zh-CN"),
            window_width=data.get("window_width", 1200),
            window_height=data.get("window_height", 800),
            window_x=data.get("window_x", 100),
            window_y=data.get("window_y", 100),
            font_size=data.get("font_size", 12),
            font_family=data.get("font_family", "Microsoft YaHei"),
            auto_save=data.get("auto_save", True),
            auto_save_interval=data.get("auto_save_interval", 300)
        )
    
    def _load_files_config(self) -> FileConfig:
        """加载文件配置"""
        data = self._load_json_file(self.files_config_file, {})
        return FileConfig(
            input_dir=data.get("input_dir", "./input"),
            output_dir=data.get("output_dir", "./output"),
            temp_dir=data.get("temp_dir", "./temp"),
            cache_dir=data.get("cache_dir", "./cache"),
            backup_dir=data.get("backup_dir", "./backups"),
            max_file_size_mb=data.get("max_file_size_mb", 100),
            auto_clean_temp=data.get("auto_clean_temp", True),
            auto_clean_interval=data.get("auto_clean_interval", 3600)
        )
    
    def _load_performance_config(self) -> PerformanceConfig:
        """加载性能配置"""
        data = self._load_json_file(self.performance_config_file, {})
        return PerformanceConfig(
            max_concurrent_tasks=data.get("max_concurrent_tasks", 2),
            memory_limit_mb=data.get("memory_limit_mb", 1024),
            enable_hardware_acceleration=data.get("enable_hardware_acceleration", False),
            enable_caching=data.get("enable_caching", True),
            cache_duration=data.get("cache_duration", 3600),
            max_cache_size=data.get("max_cache_size", 100),
            enable_profiling=data.get("enable_profiling", False)
        )
    
    def _load_preferences_config(self) -> UserPreferences:
        """加载用户偏好配置"""
        data = self._load_json_file(self.preferences_config_file, {})
        return UserPreferences(
            default_engine=data.get("default_engine", "piper_tts"),
            default_voice=data.get("default_voice", "default"),
            default_rate=data.get("default_rate", 1.0),
            default_pitch=data.get("default_pitch", 0.0),
            default_volume=data.get("default_volume", 1.0),
            default_language=data.get("default_language", "zh-CN"),
            default_format=data.get("default_format", "wav"),
            remember_settings=data.get("remember_settings", True),
            show_tooltips=data.get("show_tooltips", True),
            auto_update_check=data.get("auto_update_check", True)
        )
    
    def _save_ui_config(self, config: UIConfig):
        """保存界面配置"""
        data = {
            "theme": config.theme,
            "language": config.language,
            "window_width": config.window_width,
            "window_height": config.window_height,
            "window_x": config.window_x,
            "window_y": config.window_y,
            "font_size": config.font_size,
            "font_family": config.font_family,
            "auto_save": config.auto_save,
            "auto_save_interval": config.auto_save_interval
        }
        self._save_json_file(self.ui_config_file, data)
    
    def _save_files_config(self, config: FileConfig):
        """保存文件配置"""
        data = {
            "input_dir": config.input_dir,
            "output_dir": config.output_dir,
            "temp_dir": config.temp_dir,
            "cache_dir": config.cache_dir,
            "backup_dir": config.backup_dir,
            "max_file_size_mb": config.max_file_size_mb,
            "auto_clean_temp": config.auto_clean_temp,
            "auto_clean_interval": config.auto_clean_interval
        }
        self._save_json_file(self.files_config_file, data)
    
    def _save_performance_config(self, config: PerformanceConfig):
        """保存性能配置"""
        data = {
            "max_concurrent_tasks": config.max_concurrent_tasks,
            "memory_limit_mb": config.memory_limit_mb,
            "enable_hardware_acceleration": config.enable_hardware_acceleration,
            "enable_caching": config.enable_caching,
            "cache_duration": config.cache_duration,
            "max_cache_size": config.max_cache_size,
            "enable_profiling": config.enable_profiling
        }
        self._save_json_file(self.performance_config_file, data)
    
    def _save_preferences_config(self, config: UserPreferences):
        """保存用户偏好配置"""
        data = {
            "default_engine": config.default_engine,
            "default_voice": config.default_voice,
            "default_rate": config.default_rate,
            "default_pitch": config.default_pitch,
            "default_volume": config.default_volume,
            "default_language": config.default_language,
            "default_format": config.default_format,
            "remember_settings": config.remember_settings,
            "show_tooltips": config.show_tooltips,
            "auto_update_check": config.auto_update_check
        }
        self._save_json_file(self.preferences_config_file, data)
    
    def _load_json_file(self, file_path: Path, default: Any = None) -> Any:
        """加载JSON文件"""
        try:
            if file_path.exists():
                with open(file_path, 'r', encoding='utf-8') as f:
                    return json.load(f)
            return default
        except Exception as e:
            self.logger.error(f"加载JSON文件失败 {file_path}: {e}")
            return default
    
    def _save_json_file(self, file_path: Path, data: Any) -> bool:
        """保存JSON文件"""
        try:
            with open(file_path, 'w', encoding='utf-8') as f:
                json.dump(data, f, indent=2, ensure_ascii=False)
            return True
        except Exception as e:
            self.logger.error(f"保存JSON文件失败 {file_path}: {e}")
            return False
    
    def _create_default_config(self) -> AppConfig:
        """创建默认配置"""
        return AppConfig(
            version="2.0.0",
            ui=UIConfig(),
            files=FileConfig(),
            performance=PerformanceConfig(),
            preferences=UserPreferences(),
            debug_mode=False,
            log_level="INFO",
            created_at=datetime.now().isoformat(),
            updated_at=datetime.now().isoformat()
        )
