#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
TTS引擎注册和工厂系统
管理TTS引擎的注册、创建和生命周期
"""

import importlib
import inspect
from typing import Dict, Type, List, Optional, Any
from pathlib import Path

from .base_tts_engine import BaseTTSEngine, TTSResult
from .tts_engine_config import TTSEngineConfigManager, TTSEngineConfig
from models.audio_model import VoiceConfig
from utils.log_manager import LogManager


class TTSEngineRegistry:
    """TTS引擎注册表"""
    
    def __init__(self):
        self.logger = LogManager().get_logger("TTSEngineRegistry")
        self._engines: Dict[str, Type[BaseTTSEngine]] = {}
        self._instances: Dict[str, BaseTTSEngine] = {}
        self._config_manager = TTSEngineConfigManager()
    
    def register_engine(self, engine_id: str, engine_class: Type[BaseTTSEngine]):
        """注册TTS引擎类"""
        try:
            # 验证引擎类
            if not issubclass(engine_class, BaseTTSEngine):
                raise ValueError(f"引擎类 {engine_class} 必须继承自 BaseTTSEngine")
            
            self._engines[engine_id] = engine_class
            self.logger.info(f"注册TTS引擎: {engine_id} -> {engine_class.__name__}")
            
        except Exception as e:
            self.logger.error(f"注册TTS引擎失败 {engine_id}: {e}")
            raise
    
    def unregister_engine(self, engine_id: str):
        """注销TTS引擎"""
        try:
            if engine_id in self._engines:
                del self._engines[engine_id]
                self.logger.info(f"注销TTS引擎: {engine_id}")
            
            # 清理实例
            if engine_id in self._instances:
                del self._instances[engine_id]
                
        except Exception as e:
            self.logger.error(f"注销TTS引擎失败 {engine_id}: {e}")
    
    def get_engine_class(self, engine_id: str) -> Optional[Type[BaseTTSEngine]]:
        """获取引擎类"""
        return self._engines.get(engine_id)
    
    def get_registered_engines(self) -> List[str]:
        """获取已注册的引擎列表"""
        return list(self._engines.keys())
    
    def is_engine_registered(self, engine_id: str) -> bool:
        """检查引擎是否已注册"""
        return engine_id in self._engines


class TTSEngineFactory:
    """TTS引擎工厂"""
    
    def __init__(self):
        self.logger = LogManager().get_logger("TTSEngineFactory")
        self.registry = TTSEngineRegistry()
        self.config_manager = TTSEngineConfigManager()
        
        # 自动注册引擎
        self._auto_register_engines()
    
    def _auto_register_engines(self):
        """自动注册所有可用的TTS引擎"""
        try:
            # 获取所有引擎配置
            engine_configs = self.config_manager.get_all_engine_configs()
            
            for engine_id, config in engine_configs.items():
                if not config.is_enabled:
                    continue
                
                try:
                    # 动态导入引擎类
                    engine_class = self._import_engine_class(config.engine_class)
                    if engine_class:
                        self.registry.register_engine(engine_id, engine_class)
                        
                except Exception as e:
                    self.logger.warning(f"自动注册引擎失败 {engine_id}: {e}")
            
            self.logger.info(f"自动注册了 {len(self.registry.get_registered_engines())} 个TTS引擎")
            
        except Exception as e:
            self.logger.error(f"自动注册引擎失败: {e}")
    
    def _import_engine_class(self, class_path: str) -> Optional[Type[BaseTTSEngine]]:
        """动态导入引擎类"""
        try:
            # 解析类路径
            module_path, class_name = class_path.rsplit('.', 1)
            
            # 导入模块
            module = importlib.import_module(module_path)
            
            # 获取类
            engine_class = getattr(module, class_name)
            
            # 验证类
            if not issubclass(engine_class, BaseTTSEngine):
                self.logger.error(f"类 {class_name} 不是 BaseTTSEngine 的子类")
                return None
            
            return engine_class
            
        except Exception as e:
            self.logger.error(f"导入引擎类失败 {class_path}: {e}")
            return None
    
    def create_engine(self, engine_id: str, **kwargs) -> Optional[BaseTTSEngine]:
        """创建TTS引擎实例"""
        try:
            # 检查是否已有实例
            if engine_id in self.registry._instances:
                return self.registry._instances[engine_id]
            
            # 获取引擎类
            engine_class = self.registry.get_engine_class(engine_id)
            if not engine_class:
                self.logger.error(f"未找到引擎类: {engine_id}")
                return None
            
            # 获取引擎配置
            config = self.config_manager.get_engine_config(engine_id)
            if not config:
                self.logger.error(f"未找到引擎配置: {engine_id}")
                return None
            
            # 检查依赖项
            dependencies = self.config_manager.check_dependencies(engine_id)
            missing_deps = [dep for dep, available in dependencies.items() if not available]
            if missing_deps:
                self.logger.warning(f"引擎 {engine_id} 缺少依赖项: {missing_deps}")
                # 可以选择继续或返回None
            
            # 创建引擎实例
            engine_instance = engine_class(
                engine_id=config.engine_id,
                engine_name=config.engine_name,
                engine_type=config.engine_type,
                **kwargs
            )
            
            # 更新通用参数
            engine_instance.update_common_params(config.common_params)
            
            # 缓存实例
            self.registry._instances[engine_id] = engine_instance
            
            self.logger.info(f"创建TTS引擎实例: {engine_id}")
            return engine_instance
            
        except Exception as e:
            self.logger.error(f"创建TTS引擎失败 {engine_id}: {e}")
            return None
    
    def get_engine(self, engine_id: str) -> Optional[BaseTTSEngine]:
        """获取TTS引擎实例"""
        return self.registry._instances.get(engine_id)
    
    def get_available_engines(self) -> List[str]:
        """获取可用的引擎列表"""
        available_engines = []
        
        for engine_id in self.registry.get_registered_engines():
            try:
                engine = self.create_engine(engine_id)
                if engine and engine.is_available:
                    available_engines.append(engine_id)
            except Exception as e:
                self.logger.warning(f"检查引擎可用性失败 {engine_id}: {e}")
        
        return available_engines
    
    def get_engine_info(self, engine_id: str) -> Optional[Dict[str, Any]]:
        """获取引擎信息"""
        try:
            engine = self.get_engine(engine_id)
            if engine:
                return engine.get_engine_info()
            
            # 如果引擎未创建，尝试从配置获取基本信息
            config = self.config_manager.get_engine_config(engine_id)
            if config:
                return {
                    'engine_id': config.engine_id,
                    'engine_name': config.engine_name,
                    'engine_type': config.engine_type.value,
                    'is_available': False,
                    'is_initialized': False,
                    'voice_count': 0,
                    'description': config.description,
                    'version': config.version,
                    'author': config.author,
                    'homepage': config.homepage
                }
            
            return None
            
        except Exception as e:
            self.logger.error(f"获取引擎信息失败 {engine_id}: {e}")
            return None
    
    def get_all_engines_info(self) -> Dict[str, Dict[str, Any]]:
        """获取所有引擎信息"""
        engines_info = {}
        
        for engine_id in self.registry.get_registered_engines():
            info = self.get_engine_info(engine_id)
            if info:
                engines_info[engine_id] = info
        
        return engines_info
    
    def destroy_engine(self, engine_id: str):
        """销毁TTS引擎实例"""
        try:
            if engine_id in self.registry._instances:
                del self.registry._instances[engine_id]
                self.logger.info(f"销毁TTS引擎实例: {engine_id}")
                
        except Exception as e:
            self.logger.error(f"销毁TTS引擎失败 {engine_id}: {e}")
    
    def destroy_all_engines(self):
        """销毁所有TTS引擎实例"""
        try:
            engine_ids = list(self.registry._instances.keys())
            for engine_id in engine_ids:
                self.destroy_engine(engine_id)
                
            self.logger.info("销毁所有TTS引擎实例")
            
        except Exception as e:
            self.logger.error(f"销毁所有TTS引擎失败: {e}")
    
    def reload_engine(self, engine_id: str):
        """重新加载TTS引擎"""
        try:
            # 销毁现有实例
            self.destroy_engine(engine_id)
            
            # 重新创建
            engine = self.create_engine(engine_id)
            if engine:
                self.logger.info(f"重新加载TTS引擎成功: {engine_id}")
                return engine
            else:
                self.logger.error(f"重新加载TTS引擎失败: {engine_id}")
                return None
                
        except Exception as e:
            self.logger.error(f"重新加载TTS引擎失败 {engine_id}: {e}")
            return None
    
    def validate_engine(self, engine_id: str) -> bool:
        """验证TTS引擎"""
        try:
            # 检查引擎是否注册
            if not self.registry.is_engine_registered(engine_id):
                return False
            
            # 检查配置是否有效
            if not self.config_manager.validate_engine_config(engine_id):
                return False
            
            # 尝试创建引擎实例
            engine = self.create_engine(engine_id)
            if not engine:
                return False
            
            # 检查引擎是否可用
            return engine.is_available
            
        except Exception as e:
            self.logger.error(f"验证TTS引擎失败 {engine_id}: {e}")
            return False
    
    def get_engines_by_type(self, engine_type: str) -> List[str]:
        """根据类型获取引擎列表"""
        try:
            from .base_tts_engine import TTSEngineType
            
            if engine_type not in [e.value for e in TTSEngineType]:
                return []
            
            engine_type_enum = TTSEngineType(engine_type)
            configs = self.config_manager.get_engines_by_type(engine_type_enum)
            
            return [engine_id for engine_id in configs.keys() 
                   if engine_id in self.get_available_engines()]
            
        except Exception as e:
            self.logger.error(f"根据类型获取引擎失败 {engine_type}: {e}")
            return []
    
    def get_engines_by_priority(self) -> List[str]:
        """按优先级获取引擎列表"""
        try:
            configs = self.config_manager.get_engines_by_priority()
            available_engines = self.get_available_engines()
            
            return [config.engine_id for config in configs 
                   if config.engine_id in available_engines]
            
        except Exception as e:
            self.logger.error(f"按优先级获取引擎失败: {e}")
            return []


# 全局工厂实例
_tts_factory = None

def get_tts_factory() -> TTSEngineFactory:
    """获取全局TTS工厂实例"""
    global _tts_factory
    if _tts_factory is None:
        _tts_factory = TTSEngineFactory()
    return _tts_factory
