"""
配置模板管理器

提供配置模板的创建、管理和应用功能，包括：
- 预定义配置模板
- 自定义配置模板
- 模板应用和验证
- 模板导入导出

作者: TTS开发团队
版本: 2.0.0
创建时间: 2024
"""

import json
import os
from pathlib import Path
from typing import Dict, Any, List, Optional, Tuple
from datetime import datetime

from models.config_models import AppConfig, EngineConfig, EngineInfo, EngineParameters, EngineStatus, EngineStatusEnum
from utils.log_manager import LogManager


class ConfigTemplateManager:
    """
    配置模板管理器
    
    负责管理配置模板的创建、存储、应用和验证。
    支持预定义模板和用户自定义模板。
    """
    
    def __init__(self, templates_dir: str = 'configs/templates'):
        self.templates_dir = Path(templates_dir)
        self.templates_dir.mkdir(parents=True, exist_ok=True)
        self.logger = LogManager().get_logger("ConfigTemplateManager")
        
        # 预定义模板
        self._predefined_templates = {
            "default": self._create_default_template(),
            "high_performance": self._create_high_performance_template(),
            "low_resource": self._create_low_resource_template(),
            "development": self._create_development_template(),
            "production": self._create_production_template()
        }
        
        # 加载用户自定义模板
        self._user_templates = self._load_user_templates()
        
        self.logger.info(f"配置模板管理器初始化完成，模板目录: {self.templates_dir}")
    
    def _create_default_template(self) -> Dict[str, Any]:
        """创建默认配置模板"""
        return {
            "name": "默认配置",
            "description": "标准的TTS应用程序配置",
            "version": "2.0.0",
            "created_at": datetime.now().isoformat(),
            "app_config": {
                "version": "2.0.0",
                "debug_mode": False,
                "log_level": "INFO",
                "ui": {
                    "theme": "light",
                    "language": "zh-CN",
                    "window_width": 1200,
                    "window_height": 800,
                    "font_size": 12,
                    "font_family": "Microsoft YaHei"
                },
                "files": {
                    "input_dir": "./input",
                    "output_dir": "./output",
                    "temp_dir": "./temp",
                    "cache_dir": "./cache",
                    "backup_dir": "./backups",
                    "max_file_size_mb": 100,
                    "auto_clean_temp": True,
                    "auto_clean_interval": 3600
                },
                "performance": {
                    "max_concurrent_tasks": 2,
                    "memory_limit_mb": 1024,
                    "enable_hardware_acceleration": False,
                    "enable_caching": True,
                    "cache_duration": 3600
                },
                "preferences": {
                    "default_engine": "piper_tts",
                    "default_voice": "default",
                    "default_rate": 1.0,
                    "default_pitch": 0.0,
                    "default_volume": 1.0
                }
            },
            "engines": {
                "piper_tts": {
                    "enabled": True,
                    "priority": 1,
                    "parameters": {
                        "voice_name": "default",
                        "rate": 1.0,
                        "pitch": 0.0,
                        "volume": 1.0,
                        "language": "zh-CN",
                        "output_format": "wav"
                    }
                },
            }
        }
    
    def _create_high_performance_template(self) -> Dict[str, Any]:
        """创建高性能配置模板"""
        template = self._create_default_template()
        template["name"] = "高性能配置"
        template["description"] = "针对高性能需求优化的配置"
        
        # 优化性能设置
        template["app_config"]["performance"]["max_concurrent_tasks"] = 8
        template["app_config"]["performance"]["memory_limit_mb"] = 2048
        template["app_config"]["performance"]["cache_duration"] = 7200
        template["app_config"]["performance"]["enable_caching"] = True
        
        # 启用所有引擎
        for engine_id in template["engines"]:
            template["engines"][engine_id]["enabled"] = True
            template["engines"][engine_id]["priority"] = 1
        
        return template
    
    def _create_low_resource_template(self) -> Dict[str, Any]:
        """创建低资源消耗配置模板"""
        template = self._create_default_template()
        template["name"] = "低资源配置"
        template["description"] = "针对低资源环境优化的配置"
        
        # 降低资源消耗
        template["app_config"]["performance"]["max_concurrent_tasks"] = 1
        template["app_config"]["performance"]["memory_limit_mb"] = 512
        template["app_config"]["performance"]["cache_duration"] = 1800
        template["app_config"]["performance"]["enable_caching"] = False
        
        # 只启用基础引擎
        template["engines"]["piper_tts"]["enabled"] = True
        template["engines"]["piper_tts"]["priority"] = 1
        
        return template
    
    def _create_development_template(self) -> Dict[str, Any]:
        """创建开发环境配置模板"""
        template = self._create_default_template()
        template["name"] = "开发环境配置"
        template["description"] = "用于开发和调试的配置"
        
        # 启用调试模式
        template["app_config"]["debug_mode"] = True
        template["app_config"]["log_level"] = "DEBUG"
        
        # 启用所有引擎用于测试
        for engine_id in template["engines"]:
            template["engines"][engine_id]["enabled"] = True
        
        return template
    
    def _create_production_template(self) -> Dict[str, Any]:
        """创建生产环境配置模板"""
        template = self._create_default_template()
        template["name"] = "生产环境配置"
        template["description"] = "用于生产环境的稳定配置"
        
        # 生产环境设置
        template["app_config"]["debug_mode"] = False
        template["app_config"]["log_level"] = "WARNING"
        template["app_config"]["performance"]["max_concurrent_tasks"] = 4
        template["app_config"]["performance"]["enable_caching"] = True
        
        # 只启用稳定可靠的引擎
        template["engines"]["piper_tts"]["enabled"] = True
        template["engines"]["piper_tts"]["priority"] = 1
        
        return template
    
    def _load_user_templates(self) -> Dict[str, Dict[str, Any]]:
        """加载用户自定义模板"""
        user_templates = {}
        
        try:
            for template_file in self.templates_dir.glob("*.json"):
                if template_file.name.startswith("user_"):
                    with open(template_file, 'r', encoding='utf-8') as f:
                        template_data = json.load(f)
                        template_name = template_file.stem.replace("user_", "")
                        user_templates[template_name] = template_data
                        self.logger.debug(f"加载用户模板: {template_name}")
        except Exception as e:
            self.logger.error(f"加载用户模板失败: {e}")
        
        return user_templates
    
    def get_available_templates(self) -> List[str]:
        """获取可用模板列表"""
        return list(self._predefined_templates.keys()) + list(self._user_templates.keys())
    
    def get_template(self, template_name: str) -> Optional[Dict[str, Any]]:
        """获取指定模板"""
        if template_name in self._predefined_templates:
            return self._predefined_templates[template_name]
        elif template_name in self._user_templates:
            return self._user_templates[template_name]
        else:
            self.logger.warning(f"模板不存在: {template_name}")
            return None
    
    def create_template(self, name: str, description: str, 
                       app_config: AppConfig, engine_configs: Dict[str, EngineConfig]) -> bool:
        """
        创建用户自定义模板
        
        Args:
            name (str): 模板名称
            description (str): 模板描述
            app_config (AppConfig): 应用程序配置
            engine_configs (Dict[str, EngineConfig]): 引擎配置字典
            
        Returns:
            bool: 创建是否成功
        """
        try:
            # 构建模板数据
            template_data = {
                "name": name,
                "description": description,
                "version": "2.0.0",
                "created_at": datetime.now().isoformat(),
                "app_config": {
                    "version": app_config.version,
                    "debug_mode": app_config.debug_mode,
                    "log_level": app_config.log_level,
                    "ui": app_config.ui.__dict__,
                    "files": app_config.files.__dict__,
                    "performance": app_config.performance.__dict__,
                    "preferences": app_config.preferences.__dict__
                },
                "engines": {}
            }
            
            # 添加引擎配置
            for engine_id, engine_config in engine_configs.items():
                template_data["engines"][engine_id] = {
                    "enabled": engine_config.enabled,
                    "priority": engine_config.priority,
                    "parameters": engine_config.parameters.__dict__
                }
            
            # 保存模板文件
            template_file = self.templates_dir / f"user_{name}.json"
            with open(template_file, 'w', encoding='utf-8') as f:
                json.dump(template_data, f, indent=2, ensure_ascii=False)
            
            # 更新内存中的模板
            self._user_templates[name] = template_data
            
            self.logger.info(f"用户模板创建成功: {name}")
            return True
            
        except Exception as e:
            self.logger.error(f"创建模板失败 {name}: {e}")
            return False
    
    def apply_template(self, template_name: str, 
                      app_config_service, engine_config_service) -> bool:
        """
        应用配置模板
        
        Args:
            template_name (str): 模板名称
            app_config_service: 应用程序配置服务
            engine_config_service: 引擎配置服务
            
        Returns:
            bool: 应用是否成功
        """
        try:
            template = self.get_template(template_name)
            if not template:
                return False
            
            # 应用应用程序配置
            if "app_config" in template:
                app_config = self._template_to_app_config(template["app_config"])
                app_config_service.save_config(app_config)
                self.logger.info(f"应用程序配置已应用: {template_name}")
            
            # 应用引擎配置
            if "engines" in template:
                registry = engine_config_service.load_registry()
                
                for engine_id, engine_data in template["engines"].items():
                    engine_config = self._template_to_engine_config(engine_id, engine_data)
                    if engine_config:
                        registry.set_engine_config(engine_id, engine_config)
                
                engine_config_service.save_registry(registry)
                self.logger.info(f"引擎配置已应用: {template_name}")
            
            self.logger.info(f"模板应用成功: {template_name}")
            return True
            
        except Exception as e:
            self.logger.error(f"应用模板失败 {template_name}: {e}")
            return False
    
    def _template_to_app_config(self, template_app_config: Dict[str, Any]) -> AppConfig:
        """将模板数据转换为AppConfig对象"""
        from models.config_models import UIConfig, FileConfig, PerformanceConfig, UserPreferences
        
        return AppConfig(
            version=template_app_config.get("version", "2.0.0"),
            debug_mode=template_app_config.get("debug_mode", False),
            log_level=template_app_config.get("log_level", "INFO"),
            ui=UIConfig(**template_app_config.get("ui", {})),
            files=FileConfig(**template_app_config.get("files", {})),
            performance=PerformanceConfig(**template_app_config.get("performance", {})),
            preferences=UserPreferences(**template_app_config.get("preferences", {}))
        )
    
    def _template_to_engine_config(self, engine_id: str, engine_data: Dict[str, Any]) -> Optional[EngineConfig]:
        """将模板数据转换为EngineConfig对象"""
        try:
            # 创建引擎信息
            engine_info = EngineInfo(
                id=engine_id,
                name=engine_data.get("name", engine_id),
                version=engine_data.get("version", "1.0.0"),
                description=engine_data.get("description", ""),
                author=engine_data.get("author", ""),
                website=engine_data.get("website", ""),
                license=engine_data.get("license", ""),
                supported_languages=engine_data.get("supported_languages", ["zh-CN"]),
                supported_formats=engine_data.get("supported_formats", ["wav"]),
                is_online=engine_data.get("is_online", False),
                requires_auth=engine_data.get("requires_auth", False)
            )
            
            # 创建引擎参数
            parameters = EngineParameters(**engine_data.get("parameters", {}))
            
            # 创建引擎状态
            status = EngineStatus(
                status=EngineStatusEnum.UNAVAILABLE,
                last_check="",
                error_message="",
                available_voices=[],
                performance_metrics={}
            )
            
            return EngineConfig(
                info=engine_info,
                parameters=parameters,
                status=status,
                enabled=engine_data.get("enabled", True),
                priority=engine_data.get("priority", 0)
            )
            
        except Exception as e:
            self.logger.error(f"转换引擎配置失败 {engine_id}: {e}")
            return None
    
    def delete_template(self, template_name: str) -> bool:
        """删除用户模板"""
        try:
            if template_name in self._user_templates:
                # 删除文件
                template_file = self.templates_dir / f"user_{template_name}.json"
                if template_file.exists():
                    template_file.unlink()
                
                # 从内存中移除
                del self._user_templates[template_name]
                
                self.logger.info(f"用户模板删除成功: {template_name}")
                return True
            else:
                self.logger.warning(f"用户模板不存在: {template_name}")
                return False
                
        except Exception as e:
            self.logger.error(f"删除模板失败 {template_name}: {e}")
            return False
    
    def export_template(self, template_name: str, export_path: str) -> bool:
        """导出模板到指定路径"""
        try:
            template = self.get_template(template_name)
            if not template:
                return False
            
            with open(export_path, 'w', encoding='utf-8') as f:
                json.dump(template, f, indent=2, ensure_ascii=False)
            
            self.logger.info(f"模板导出成功: {template_name} -> {export_path}")
            return True
            
        except Exception as e:
            self.logger.error(f"导出模板失败 {template_name}: {e}")
            return False
    
    def import_template(self, import_path: str, template_name: str = None) -> bool:
        """从指定路径导入模板"""
        try:
            with open(import_path, 'r', encoding='utf-8') as f:
                template_data = json.load(f)
            
            # 如果没有指定名称，使用文件名
            if not template_name:
                template_name = Path(import_path).stem
            
            # 保存为用户模板
            template_file = self.templates_dir / f"user_{template_name}.json"
            with open(template_file, 'w', encoding='utf-8') as f:
                json.dump(template_data, f, indent=2, ensure_ascii=False)
            
            # 更新内存中的模板
            self._user_templates[template_name] = template_data
            
            self.logger.info(f"模板导入成功: {import_path} -> {template_name}")
            return True
            
        except Exception as e:
            self.logger.error(f"导入模板失败 {import_path}: {e}")
            return False
