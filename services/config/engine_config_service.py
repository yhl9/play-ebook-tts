"""
引擎配置服务

负责TTS引擎配置的管理，包括引擎注册、参数配置、状态监控等。
提供引擎配置的加载、保存、验证和动态管理功能。

作者: TTS开发团队
版本: 2.0.0
创建时间: 2024
"""

import json
import os
from pathlib import Path
from typing import Optional, Dict, Any, List
from datetime import datetime

from models.config_models import (
    EngineConfig, EngineInfo, EngineParameters, EngineStatus, 
    EngineStatusEnum
)
from .config_registry import ConfigRegistry
from utils.log_manager import LogManager


class EngineConfigService:
    """
    引擎配置服务
    
    负责TTS引擎配置的管理，包括引擎注册、参数配置、状态监控等。
    提供引擎配置的加载、保存、验证和动态管理功能。
    """
    
    def __init__(self, config_dir: str = "configs/engines"):
        self.logger = LogManager().get_logger("EngineConfigService")
        self.config_dir = Path(config_dir)
        self.config_dir.mkdir(parents=True, exist_ok=True)
        
        # 配置文件路径
        self.registry_file = self.config_dir / "registry.json"
        
        # 引擎配置缓存
        self._engine_configs: Dict[str, EngineConfig] = {}
        self._registry: Optional[ConfigRegistry] = None
        
        # 引擎信息模板
        self._engine_templates = self._load_engine_templates()
    
    def load_registry(self) -> ConfigRegistry:
        """
        加载引擎注册表
        
        Returns:
            ConfigRegistry: 引擎注册表对象
        """
        try:
            if self.registry_file.exists():
                with open(self.registry_file, 'r', encoding='utf-8') as f:
                    data = json.load(f)
                
                registry = ConfigRegistry()
                registry._config_version = data.get("config_version", "2.0.0")
                registry._last_updated = data.get("last_updated", "")
                
                # 加载引擎配置
                for engine_id, engine_data in data.get("engines", {}).items():
                    engine_config = self._load_engine_config_from_data(engine_id, engine_data)
                    registry._engine_configs[engine_id] = engine_config
                
                self._registry = registry
                self.logger.info("引擎注册表加载成功")
                return registry
            else:
                # 创建默认注册表
                return self._create_default_registry()
                
        except Exception as e:
            self.logger.error(f"加载引擎注册表失败: {e}")
            return self._create_default_registry()
    
    def save_registry(self, registry: ConfigRegistry) -> bool:
        """
        保存引擎注册表
        
        Args:
            registry (ConfigRegistry): 引擎注册表对象
            
        Returns:
            bool: 保存是否成功
        """
        try:
            registry.last_updated = datetime.now().isoformat()
            
            data = {
                "config_version": registry._config_version,
                "last_updated": registry._last_updated,
                "engines": {}
            }
            
            # 保存引擎配置
            for engine_id, engine_config in registry._engine_configs.items():
                data["engines"][engine_id] = self._save_engine_config_to_data(engine_config)
            
            with open(self.registry_file, 'w', encoding='utf-8') as f:
                json.dump(data, f, indent=2, ensure_ascii=False)
            
            self._registry = registry
            self.logger.info("引擎注册表保存成功")
            return True
            
        except Exception as e:
            self.logger.error(f"保存引擎注册表失败: {e}")
            return False
    
    def get_engine_config(self, engine_id: str) -> Optional[EngineConfig]:
        """
        获取引擎配置
        
        Args:
            engine_id (str): 引擎ID
            
        Returns:
            Optional[EngineConfig]: 引擎配置对象
        """
        if self._registry is None:
            self._registry = self.load_registry()
        
        return self._registry.get_engine_config(engine_id)
    
    def set_engine_config(self, engine_id: str, config: EngineConfig) -> bool:
        """
        设置引擎配置
        
        Args:
            engine_id (str): 引擎ID
            config (EngineConfig): 引擎配置对象
            
        Returns:
            bool: 设置是否成功
        """
        if self._registry is None:
            self._registry = self.load_registry()
        
        self._registry.set_engine_config(engine_id, config)
        return self.save_registry(self._registry)
    
    def register_engine(self, engine_id: str, engine_info: EngineInfo, 
                       parameters: EngineParameters = None) -> bool:
        """
        注册新引擎
        
        Args:
            engine_id (str): 引擎ID
            engine_info (EngineInfo): 引擎信息
            parameters (EngineParameters): 引擎参数
            
        Returns:
            bool: 注册是否成功
        """
        try:
            if parameters is None:
                parameters = EngineParameters()
            
            engine_config = EngineConfig(
                info=engine_info,
                parameters=parameters,
                status=EngineStatus(status=EngineStatusEnum.UNAVAILABLE),
                config_version="1.0.0",
                enabled=True,
                priority=0,
                created_at=datetime.now().isoformat(),
                updated_at=datetime.now().isoformat()
            )
            
            return self.set_engine_config(engine_id, engine_config)
            
        except Exception as e:
            self.logger.error(f"注册引擎失败 {engine_id}: {e}")
            return False
    
    def unregister_engine(self, engine_id: str) -> bool:
        """
        注销引擎
        
        Args:
            engine_id (str): 引擎ID
            
        Returns:
            bool: 注销是否成功
        """
        try:
            if self._registry is None:
                self._registry = self.load_registry()
            
            self._registry.remove_engine_config(engine_id)
            return self.save_registry(self._registry)
            
        except Exception as e:
            self.logger.error(f"注销引擎失败 {engine_id}: {e}")
            return False
    
    def get_available_engines(self) -> List[str]:
        """
        获取可用引擎列表
        
        Returns:
            List[str]: 可用引擎ID列表
        """
        if self._registry is None:
            self._registry = self.load_registry()
        
        return self._registry.get_available_engines()
    
    def get_engine_priority_order(self) -> List[str]:
        """
        获取引擎优先级顺序
        
        Returns:
            List[str]: 按优先级排序的引擎ID列表
        """
        if self._registry is None:
            self._registry = self.load_registry()
        
        return self._registry.get_engine_priority_order()
    
    def get_current_engine(self) -> str:
        """
        获取当前引擎
        
        Returns:
            str: 当前引擎ID
        """
        if self._registry is None:
            self._registry = self.load_registry()
        
        # 获取可用引擎列表
        available_engines = self._registry.get_available_engines()
        if available_engines:
            return available_engines[0]  # 返回第一个可用引擎
        
        # 如果没有可用引擎，返回第一个注册的引擎
        if self._registry._engine_configs:
            return list(self._registry._engine_configs.keys())[0]
        
        return "piper_tts"  # 默认引擎
    
    def load_engine_config(self, engine_id: str) -> Optional[EngineConfig]:
        """
        加载引擎配置
        
        Args:
            engine_id (str): 引擎ID
            
        Returns:
            Optional[EngineConfig]: 引擎配置对象
        """
        return self.get_engine_config(engine_id)
    
    def update_engine_status(self, engine_id: str, status: EngineStatusEnum, 
                           error_message: str = "", available_voices: List[Dict] = None) -> bool:
        """
        更新引擎状态
        
        Args:
            engine_id (str): 引擎ID
            status (EngineStatusEnum): 引擎状态
            error_message (str): 错误信息
            available_voices (List[Dict]): 可用语音列表
            
        Returns:
            bool: 更新是否成功
        """
        try:
            engine_config = self.get_engine_config(engine_id)
            if engine_config is None:
                self.logger.warning(f"引擎配置不存在: {engine_id}")
                return False
            
            engine_config.status.status = status
            engine_config.status.last_check = datetime.now().isoformat()
            engine_config.status.error_message = error_message
            if available_voices:
                engine_config.status.available_voices = available_voices
            
            return self.set_engine_config(engine_id, engine_config)
            
        except Exception as e:
            self.logger.error(f"更新引擎状态失败 {engine_id}: {e}")
            return False
    
    def _load_engine_config_from_data(self, engine_id: str, data: Dict[str, Any]) -> EngineConfig:
        """从数据加载引擎配置"""
        # 加载引擎信息
        info_data = data.get("info", {})
        engine_info = EngineInfo(
            id=engine_id,
            name=info_data.get("name", engine_id),
            version=info_data.get("version", "1.0.0"),
            description=info_data.get("description", ""),
            author=info_data.get("author", ""),
            website=info_data.get("website", ""),
            license=info_data.get("license", ""),
            supported_languages=info_data.get("supported_languages", []),
            supported_formats=info_data.get("supported_formats", []),
            is_online=info_data.get("is_online", False),
            requires_auth=info_data.get("requires_auth", False)
        )
        
        # 加载引擎参数
        params_data = data.get("parameters", {})
        engine_parameters = EngineParameters(
            voice_name=params_data.get("voice_name", "default"),
            rate=params_data.get("rate", 1.0),
            pitch=params_data.get("pitch", 0.0),
            volume=params_data.get("volume", 1.0),
            language=params_data.get("language", "zh-CN"),
            output_format=params_data.get("output_format", "wav"),
            extra_params=params_data.get("extra_params", {})
        )
        
        # 加载引擎状态
        status_data = data.get("status", {})
        engine_status = EngineStatus(
            status=EngineStatusEnum(status_data.get("status", "unavailable")),
            last_check=status_data.get("last_check", ""),
            error_message=status_data.get("error_message", ""),
            available_voices=status_data.get("available_voices", []),
            performance_metrics=status_data.get("performance_metrics", {})
        )
        
        return EngineConfig(
            info=engine_info,
            parameters=engine_parameters,
            status=engine_status,
            config_version=data.get("config_version", "1.0.0"),
            enabled=data.get("enabled", True),
            priority=data.get("priority", 0),
            created_at=data.get("created_at", ""),
            updated_at=data.get("updated_at", "")
        )
    
    def _save_engine_config_to_data(self, config: EngineConfig) -> Dict[str, Any]:
        """将引擎配置保存为数据"""
        return {
            "info": {
                "name": config.info.name,
                "version": config.info.version,
                "description": config.info.description,
                "author": config.info.author,
                "website": config.info.website,
                "license": config.info.license,
                "supported_languages": config.info.supported_languages,
                "supported_formats": config.info.supported_formats,
                "is_online": config.info.is_online,
                "requires_auth": config.info.requires_auth
            },
            "parameters": {
                "voice_name": config.parameters.voice_name,
                "rate": config.parameters.rate,
                "pitch": config.parameters.pitch,
                "volume": config.parameters.volume,
                "language": config.parameters.language,
                "output_format": config.parameters.output_format,
                "extra_params": config.parameters.extra_params
            },
            "status": {
                "status": config.status.status.value,
                "last_check": config.status.last_check,
                "error_message": config.status.error_message,
                "available_voices": config.status.available_voices,
                "performance_metrics": config.status.performance_metrics
            },
            "config_version": config.config_version,
            "enabled": config.enabled,
            "priority": config.priority,
            "created_at": config.created_at,
            "updated_at": config.updated_at
        }
    
    def _load_engine_templates(self) -> Dict[str, Dict[str, Any]]:
        """加载引擎模板"""
        templates = {
            "piper_tts": {
                "name": "Piper TTS",
                "description": "高质量本地TTS引擎",
                "supported_languages": ["zh-CN", "en-US"],
                "supported_formats": ["wav", "mp3"],
                "is_online": False,
                "requires_auth": False
            },
            "emotivoice_tts_api": {
                "name": "EmotiVoice TTS API",
                "description": "支持情感控制的在线TTS服务",
                "supported_languages": ["zh-CN"],
                "supported_formats": ["wav", "mp3"],
                "is_online": True,
                "requires_auth": False
            },
            "pyttsx3": {
                "name": "pyttsx3",
                "description": "跨平台系统TTS引擎",
                "supported_languages": ["zh-CN", "en-US"],
                "supported_formats": ["wav"],
                "is_online": False,
                "requires_auth": False
            },
            "index_tts_api_15": {
                "name": "IndexTTS API 1.5",
                "description": "基于参考音频的语音克隆服务",
                "supported_languages": ["zh-CN"],
                "supported_formats": ["wav", "mp3"],
                "is_online": True,
                "requires_auth": False
            }
        }
        return templates
    
    def _create_default_registry(self) -> ConfigRegistry:
        """创建默认注册表"""
        registry = ConfigRegistry()
        registry._config_version = "2.0.0"
        registry._last_updated = datetime.now().isoformat()
        
        # 注册默认引擎
        for engine_id, template in self._engine_templates.items():
            engine_info = EngineInfo(
                id=engine_id,
                name=template["name"],
                version="1.0.0",
                description=template["description"],
                author="TTS开发团队",
                website="",
                license="",
                supported_languages=template["supported_languages"],
                supported_formats=template["supported_formats"],
                is_online=template["is_online"],
                requires_auth=template["requires_auth"]
            )
            
            engine_config = EngineConfig(
                info=engine_info,
                parameters=EngineParameters(),
                status=EngineStatus(status=EngineStatusEnum.UNAVAILABLE),
                config_version="1.0.0",
                enabled=True,
                priority=0,
                created_at=datetime.now().isoformat(),
                updated_at=datetime.now().isoformat()
            )
            
            registry._engine_configs[engine_id] = engine_config
        
        # 保存默认注册表
        self.save_registry(registry)
        return registry
