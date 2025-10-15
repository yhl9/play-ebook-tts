"""
配置注册表

提供配置注册表功能，管理所有配置的注册、发现和依赖关系。
支持配置的动态加载和热更新。

作者: TTS开发团队
版本: 2.0.0
创建时间: 2024
"""

from typing import Dict, Any, List, Optional, Callable, Tuple
from models.config_models import ConfigRegistry, AppConfig, EngineConfig
from utils.log_manager import LogManager


class ConfigRegistry:
    """
    配置注册表
    
    提供配置注册表功能，管理所有配置的注册、发现和依赖关系。
    支持配置的动态加载和热更新。
    """
    
    def __init__(self):
        self.logger = LogManager().get_logger("ConfigRegistry")
        self._app_config: Optional[AppConfig] = None
        self._engine_configs: Dict[str, EngineConfig] = {}
        self._config_version: str = "2.0.0"
        self._last_updated: str = ""
        
        # 配置变更监听器
        self._change_listeners: List[Callable] = []
        
        # 配置依赖关系
        self._dependencies: Dict[str, List[str]] = {}
    
    def register_app_config(self, config: AppConfig) -> bool:
        """
        注册应用程序配置
        
        Args:
            config (AppConfig): 应用程序配置对象
            
        Returns:
            bool: 注册是否成功
        """
        try:
            self._app_config = config
            self._notify_change("app_config", config)
            self.logger.info("应用程序配置注册成功")
            return True
        except Exception as e:
            self.logger.error(f"注册应用程序配置失败: {e}")
            return False
    
    def register_engine_config(self, engine_id: str, config: EngineConfig) -> bool:
        """
        注册引擎配置
        
        Args:
            engine_id (str): 引擎ID
            config (EngineConfig): 引擎配置对象
            
        Returns:
            bool: 注册是否成功
        """
        try:
            self._engine_configs[engine_id] = config
            self._notify_change("engine_config", engine_id, config)
            self.logger.info(f"引擎配置注册成功: {engine_id}")
            return True
        except Exception as e:
            self.logger.error(f"注册引擎配置失败 {engine_id}: {e}")
            return False
    
    def unregister_engine_config(self, engine_id: str) -> bool:
        """
        注销引擎配置
        
        Args:
            engine_id (str): 引擎ID
            
        Returns:
            bool: 注销是否成功
        """
        try:
            if engine_id in self._engine_configs:
                del self._engine_configs[engine_id]
                self._notify_change("engine_unregistered", engine_id)
                self.logger.info(f"引擎配置注销成功: {engine_id}")
                return True
            else:
                self.logger.warning(f"引擎配置不存在: {engine_id}")
                return False
        except Exception as e:
            self.logger.error(f"注销引擎配置失败 {engine_id}: {e}")
            return False
    
    def get_app_config(self) -> Optional[AppConfig]:
        """
        获取应用程序配置
        
        Returns:
            Optional[AppConfig]: 应用程序配置对象
        """
        return self._app_config
    
    def get_engine_config(self, engine_id: str) -> Optional[EngineConfig]:
        """
        获取引擎配置
        
        Args:
            engine_id (str): 引擎ID
            
        Returns:
            Optional[EngineConfig]: 引擎配置对象
        """
        return self._engine_configs.get(engine_id)
    
    def set_engine_config(self, engine_id: str, config: EngineConfig) -> bool:
        """
        设置引擎配置
        
        Args:
            engine_id (str): 引擎ID
            config (EngineConfig): 引擎配置对象
            
        Returns:
            bool: 设置是否成功
        """
        try:
            self._engine_configs[engine_id] = config
            self._notify_change("engine_config", engine_id, config)
            self.logger.info(f"引擎配置设置成功: {engine_id}")
            return True
        except Exception as e:
            self.logger.error(f"设置引擎配置失败 {engine_id}: {e}")
            return False
    
    def get_all_engine_configs(self) -> Dict[str, EngineConfig]:
        """
        获取所有引擎配置
        
        Returns:
            Dict[str, EngineConfig]: 所有引擎配置字典
        """
        return self._engine_configs.copy()
    
    def get_available_engines(self) -> List[str]:
        """
        获取可用引擎列表
        
        Returns:
            List[str]: 可用引擎ID列表
        """
        return [
            engine_id for engine_id, config in self._engine_configs.items()
            if config.enabled and config.status.status.value == "available"
        ]
    
    def get_engine_priority_order(self) -> List[str]:
        """
        获取引擎优先级顺序
        
        Returns:
            List[str]: 按优先级排序的引擎ID列表
        """
        return sorted(
            self._engine_configs.keys(),
            key=lambda x: self._engine_configs[x].priority,
            reverse=True
        )
    
    def get_engines_by_language(self, language: str) -> List[str]:
        """
        根据语言获取引擎列表
        
        Args:
            language (str): 语言代码
            
        Returns:
            List[str]: 支持该语言的引擎ID列表
        """
        return [
            engine_id for engine_id, config in self._engine_configs.items()
            if config.enabled and language in config.info.supported_languages
        ]
    
    def get_engines_by_format(self, output_format: str) -> List[str]:
        """
        根据输出格式获取引擎列表
        
        Args:
            output_format (str): 输出格式
            
        Returns:
            List[str]: 支持该格式的引擎ID列表
        """
        return [
            engine_id for engine_id, config in self._engine_configs.items()
            if config.enabled and output_format in config.info.supported_formats
        ]
    
    def update_engine_status(self, engine_id: str, status, error_message: str = "") -> bool:
        """
        更新引擎状态
        
        Args:
            engine_id (str): 引擎ID
            status (str): 新状态
            error_message (str): 错误信息
            
        Returns:
            bool: 更新是否成功
        """
        try:
            if engine_id in self._engine_configs:
                config = self._engine_configs[engine_id]
                # 处理状态类型（可能是字符串或EngineStatusEnum）
                if hasattr(status, 'value'):
                    config.status.status = status
                else:
                    # 如果是字符串，转换为EngineStatusEnum
                    from models.config_models import EngineStatusEnum
                    config.status.status = EngineStatusEnum(status)
                config.status.error_message = error_message
                self._notify_change("engine_status_updated", engine_id, status)
                self.logger.info(f"引擎状态更新成功: {engine_id} -> {status}")
                return True
            else:
                self.logger.warning(f"引擎配置不存在: {engine_id}")
                return False
        except Exception as e:
            self.logger.error(f"更新引擎状态失败 {engine_id}: {e}")
            return False
    
    def add_change_listener(self, listener: Callable) -> bool:
        """
        添加配置变更监听器
        
        Args:
            listener (Callable): 监听器函数
            
        Returns:
            bool: 添加是否成功
        """
        try:
            self._change_listeners.append(listener)
            self.logger.info("配置变更监听器添加成功")
            return True
        except Exception as e:
            self.logger.error(f"添加配置变更监听器失败: {e}")
            return False
    
    def remove_change_listener(self, listener: Callable) -> bool:
        """
        移除配置变更监听器
        
        Args:
            listener (Callable): 监听器函数
            
        Returns:
            bool: 移除是否成功
        """
        try:
            if listener in self._change_listeners:
                self._change_listeners.remove(listener)
                self.logger.info("配置变更监听器移除成功")
                return True
            else:
                self.logger.warning("配置变更监听器不存在")
                return False
        except Exception as e:
            self.logger.error(f"移除配置变更监听器失败: {e}")
            return False
    
    def add_dependency(self, config_id: str, depends_on: List[str]) -> bool:
        """
        添加配置依赖关系
        
        Args:
            config_id (str): 配置ID
            depends_on (List[str]): 依赖的配置ID列表
            
        Returns:
            bool: 添加是否成功
        """
        try:
            self._dependencies[config_id] = depends_on
            self.logger.info(f"配置依赖关系添加成功: {config_id} -> {depends_on}")
            return True
        except Exception as e:
            self.logger.error(f"添加配置依赖关系失败 {config_id}: {e}")
            return False
    
    def get_dependencies(self, config_id: str) -> List[str]:
        """
        获取配置依赖关系
        
        Args:
            config_id (str): 配置ID
            
        Returns:
            List[str]: 依赖的配置ID列表
        """
        return self._dependencies.get(config_id, [])
    
    def validate_dependencies(self) -> Tuple[bool, List[str]]:
        """
        验证配置依赖关系
        
        Returns:
            Tuple[bool, List[str]]: (是否有效, 错误信息列表)
        """
        errors = []
        
        for config_id, dependencies in self._dependencies.items():
            for dep_id in dependencies:
                if dep_id not in self._engine_configs and dep_id != "app_config":
                    errors.append(f"配置 {config_id} 依赖的配置 {dep_id} 不存在")
        
        return len(errors) == 0, errors
    
    def _notify_change(self, change_type: str, *args, **kwargs):
        """通知配置变更"""
        for listener in self._change_listeners:
            try:
                listener(change_type, *args, **kwargs)
            except Exception as e:
                self.logger.error(f"配置变更监听器执行失败: {e}")
    
    def get_config_summary(self) -> Dict[str, Any]:
        """
        获取配置摘要
        
        Returns:
            Dict[str, Any]: 配置摘要信息
        """
        return {
            "config_version": self._config_version,
            "last_updated": self._last_updated,
            "app_config_loaded": self._app_config is not None,
            "engine_count": len(self._engine_configs),
            "available_engines": len(self.get_available_engines()),
            "engine_list": list(self._engine_configs.keys()),
            "listener_count": len(self._change_listeners),
            "dependency_count": len(self._dependencies)
        }
    
    def clear_all(self):
        """清空所有配置"""
        self._app_config = None
        self._engine_configs.clear()
        self._change_listeners.clear()
        self._dependencies.clear()
        self.logger.info("所有配置已清空")
