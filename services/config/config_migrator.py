"""
配置迁移器

提供配置迁移功能，支持不同版本配置之间的转换。
确保配置升级的平滑过渡。

作者: TTS开发团队
版本: 2.0.0
创建时间: 2024
"""

import json
import os
from pathlib import Path
from typing import Dict, Any, List, Tuple, Optional
from datetime import datetime

from models.config_models import AppConfig, EngineConfig, ConfigRegistry
from utils.log_manager import LogManager


class ConfigMigrator:
    """
    配置迁移器
    
    提供配置迁移功能，支持不同版本配置之间的转换。
    确保配置升级的平滑过渡。
    """
    
    def __init__(self, migration_dir: str = "configs/migrations"):
        self.logger = LogManager().get_logger("ConfigMigrator")
        self.migration_dir = Path(migration_dir)
        self.migration_dir.mkdir(parents=True, exist_ok=True)
        
        # 迁移规则
        self._migration_rules = self._load_migration_rules()
    
    def migrate_config(self, source_path: str, target_path: str, 
                      source_version: str, target_version: str) -> bool:
        """
        迁移配置文件
        
        Args:
            source_path (str): 源配置文件路径
            target_path (str): 目标配置文件路径
            source_version (str): 源版本
            target_version (str): 目标版本
            
        Returns:
            bool: 迁移是否成功
        """
        try:
            # 加载源配置
            source_config = self._load_config_file(source_path)
            if source_config is None:
                self.logger.error(f"无法加载源配置文件: {source_path}")
                return False
            
            # 执行迁移
            migrated_config = self._migrate_config_data(
                source_config, source_version, target_version
            )
            
            if migrated_config is None:
                self.logger.error("配置迁移失败")
                return False
            
            # 保存目标配置
            if self._save_config_file(target_path, migrated_config):
                self.logger.info(f"配置迁移成功: {source_path} -> {target_path}")
                return True
            else:
                self.logger.error(f"保存目标配置文件失败: {target_path}")
                return False
                
        except Exception as e:
            self.logger.error(f"配置迁移异常: {e}")
            return False
    
    def migrate_from_old_config(self, old_config_path: str) -> Tuple[bool, Optional[AppConfig]]:
        """
        从旧配置迁移到新配置
        
        Args:
            old_config_path (str): 旧配置文件路径
            
        Returns:
            Tuple[bool, Optional[AppConfig]]: (是否成功, 新配置对象)
        """
        try:
            # 加载旧配置
            old_config = self._load_config_file(old_config_path)
            if old_config is None:
                self.logger.error(f"无法加载旧配置文件: {old_config_path}")
                return False, None
            
            # 检测旧配置版本
            old_version = self._detect_config_version(old_config)
            self.logger.info(f"检测到旧配置版本: {old_version}")
            
            # 执行迁移
            new_config = self._migrate_from_v1_to_v2(old_config)
            if new_config is None:
                self.logger.error("从v1迁移到v2失败")
                return False, None
            
            self.logger.info("配置迁移成功: v1 -> v2")
            return True, new_config
            
        except Exception as e:
            self.logger.error(f"从旧配置迁移异常: {e}")
            return False, None
    
    def migrate_engine_configs(self, old_engine_configs: Dict[str, Any]) -> Dict[str, EngineConfig]:
        """
        迁移引擎配置
        
        Args:
            old_engine_configs (Dict[str, Any]): 旧引擎配置
            
        Returns:
            Dict[str, EngineConfig]: 新引擎配置
        """
        new_engine_configs = {}
        
        for engine_id, old_config in old_engine_configs.items():
            try:
                new_config = self._migrate_single_engine_config(engine_id, old_config)
                if new_config:
                    new_engine_configs[engine_id] = new_config
                    self.logger.info(f"引擎配置迁移成功: {engine_id}")
                else:
                    self.logger.warning(f"引擎配置迁移失败: {engine_id}")
            except Exception as e:
                self.logger.error(f"引擎配置迁移异常 {engine_id}: {e}")
        
        return new_engine_configs
    
    def _migrate_from_v1_to_v2(self, old_config: Dict[str, Any]) -> Optional[AppConfig]:
        """从v1配置迁移到v2配置"""
        try:
            # 创建新的应用程序配置
            app_config = AppConfig(
                version="2.0.0",
                debug_mode=old_config.get("debug_mode", False),
                log_level=old_config.get("log_level", "INFO"),
                created_at=datetime.now().isoformat(),
                updated_at=datetime.now().isoformat()
            )
            
            # 迁移UI配置
            if "ui" in old_config:
                ui_data = old_config["ui"]
                app_config.ui.theme = ui_data.get("theme", "light")
                app_config.ui.language = ui_data.get("language", "zh-CN")
                app_config.ui.window_width = ui_data.get("window_width", 1200)
                app_config.ui.window_height = ui_data.get("window_height", 800)
                app_config.ui.window_x = ui_data.get("window_x", 100)
                app_config.ui.window_y = ui_data.get("window_y", 100)
                app_config.ui.font_size = ui_data.get("font_size", 12)
                app_config.ui.font_family = ui_data.get("font_family", "Microsoft YaHei")
                app_config.ui.auto_save = ui_data.get("auto_save", True)
                app_config.ui.auto_save_interval = ui_data.get("auto_save_interval", 300)
            
            # 迁移文件配置
            if "files" in old_config:
                files_data = old_config["files"]
                app_config.files.input_dir = files_data.get("input_dir", "./input")
                app_config.files.output_dir = files_data.get("output_dir", "./output")
                app_config.files.temp_dir = files_data.get("temp_dir", "./temp")
                app_config.files.cache_dir = files_data.get("cache_dir", "./cache")
                app_config.files.backup_dir = files_data.get("backup_dir", "./backups")
                app_config.files.max_file_size_mb = files_data.get("max_file_size_mb", 100)
                app_config.files.auto_clean_temp = files_data.get("auto_clean_temp", True)
                app_config.files.auto_clean_interval = files_data.get("auto_clean_interval", 3600)
            
            # 迁移性能配置
            if "performance" in old_config:
                perf_data = old_config["performance"]
                app_config.performance.max_concurrent_tasks = perf_data.get("max_concurrent_tasks", 2)
                app_config.performance.memory_limit_mb = perf_data.get("memory_limit_mb", 1024)
                app_config.performance.enable_hardware_acceleration = perf_data.get("enable_hardware_acceleration", False)
                app_config.performance.enable_caching = perf_data.get("enable_caching", True)
                app_config.performance.cache_duration = perf_data.get("cache_duration", 3600)
                app_config.performance.max_cache_size = perf_data.get("max_cache_size", 100)
                app_config.performance.enable_profiling = perf_data.get("enable_profiling", False)
            
            # 迁移用户偏好配置
            if "preferences" in old_config:
                pref_data = old_config["preferences"]
                app_config.preferences.default_engine = pref_data.get("default_engine", "piper_tts")
                app_config.preferences.default_voice = pref_data.get("default_voice", "default")
                app_config.preferences.default_rate = pref_data.get("default_rate", 1.0)
                app_config.preferences.default_pitch = pref_data.get("default_pitch", 0.0)
                app_config.preferences.default_volume = pref_data.get("default_volume", 1.0)
                app_config.preferences.default_language = pref_data.get("default_language", "zh-CN")
                app_config.preferences.default_format = pref_data.get("default_format", "wav")
                app_config.preferences.remember_settings = pref_data.get("remember_settings", True)
                app_config.preferences.show_tooltips = pref_data.get("show_tooltips", True)
                app_config.preferences.auto_update_check = pref_data.get("auto_update_check", True)
            
            return app_config
            
        except Exception as e:
            self.logger.error(f"v1到v2配置迁移异常: {e}")
            return None
    
    def _migrate_single_engine_config(self, engine_id: str, old_config: Dict[str, Any]) -> Optional[EngineConfig]:
        """迁移单个引擎配置"""
        try:
            from models.config_models import EngineInfo, EngineParameters, EngineStatus, EngineStatusEnum
            
            # 创建引擎信息
            engine_info = EngineInfo(
                id=engine_id,
                name=old_config.get("name", engine_id),
                version=old_config.get("version", "1.0.0"),
                description=old_config.get("description", ""),
                author=old_config.get("author", ""),
                website=old_config.get("website", ""),
                license=old_config.get("license", ""),
                supported_languages=old_config.get("supported_languages", []),
                supported_formats=old_config.get("supported_formats", []),
                is_online=old_config.get("is_online", False),
                requires_auth=old_config.get("requires_auth", False)
            )
            
            # 创建引擎参数
            engine_parameters = EngineParameters(
                voice_name=old_config.get("voice_name", "default"),
                rate=old_config.get("rate", 1.0),
                pitch=old_config.get("pitch", 0.0),
                volume=old_config.get("volume", 1.0),
                language=old_config.get("language", "zh-CN"),
                output_format=old_config.get("output_format", "wav"),
                extra_params=old_config.get("extra_params", {})
            )
            
            # 创建引擎状态
            engine_status = EngineStatus(
                status=EngineStatusEnum.UNAVAILABLE,
                last_check="",
                error_message="",
                available_voices=[],
                performance_metrics={}
            )
            
            # 创建引擎配置
            engine_config = EngineConfig(
                info=engine_info,
                parameters=engine_parameters,
                status=engine_status,
                config_version="1.0.0",
                enabled=old_config.get("enabled", True),
                priority=old_config.get("priority", 0),
                created_at=datetime.now().isoformat(),
                updated_at=datetime.now().isoformat()
            )
            
            return engine_config
            
        except Exception as e:
            self.logger.error(f"单个引擎配置迁移异常 {engine_id}: {e}")
            return None
    
    def _detect_config_version(self, config: Dict[str, Any]) -> str:
        """检测配置版本"""
        version = config.get("version", "1.0.0")
        
        # 根据配置结构判断版本
        if "ui" in config and "files" in config and "performance" in config:
            return "1.0.0"
        elif "config_version" in config:
            return config["config_version"]
        else:
            return "1.0.0"
    
    def _migrate_config_data(self, config: Dict[str, Any], 
                           source_version: str, target_version: str) -> Optional[Dict[str, Any]]:
        """迁移配置数据"""
        try:
            # 根据版本执行相应的迁移规则
            if source_version == "1.0.0" and target_version == "2.0.0":
                return self._migrate_v1_to_v2_data(config)
            else:
                self.logger.warning(f"不支持的迁移版本: {source_version} -> {target_version}")
                return None
                
        except Exception as e:
            self.logger.error(f"配置数据迁移异常: {e}")
            return None
    
    def _migrate_v1_to_v2_data(self, config: Dict[str, Any]) -> Dict[str, Any]:
        """v1到v2的数据迁移"""
        # 这里可以实现具体的v1到v2数据迁移逻辑
        # 目前返回原配置
        return config
    
    def _load_config_file(self, file_path: str) -> Optional[Dict[str, Any]]:
        """加载配置文件"""
        try:
            if os.path.exists(file_path):
                with open(file_path, 'r', encoding='utf-8') as f:
                    return json.load(f)
            return None
        except Exception as e:
            self.logger.error(f"加载配置文件失败 {file_path}: {e}")
            return None
    
    def _save_config_file(self, file_path: str, config: Dict[str, Any]) -> bool:
        """保存配置文件"""
        try:
            os.makedirs(os.path.dirname(file_path), exist_ok=True)
            with open(file_path, 'w', encoding='utf-8') as f:
                json.dump(config, f, indent=2, ensure_ascii=False)
            return True
        except Exception as e:
            self.logger.error(f"保存配置文件失败 {file_path}: {e}")
            return False
    
    def _load_migration_rules(self) -> Dict[str, Any]:
        """加载迁移规则"""
        return {
            "1.0.0_to_2.0.0": {
                "description": "从v1.0.0迁移到v2.0.0",
                "changes": [
                    "分离应用程序配置和引擎配置",
                    "重构配置数据结构",
                    "添加配置验证和迁移功能"
                ]
            }
        }
