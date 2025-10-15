"""
引擎配置管理器

提供统一的引擎配置管理接口，协调各个TTS引擎的配置加载和状态管理。
负责引擎的注册、发现、配置同步等功能。

作者: TTS开发团队
版本: 2.0.0
创建时间: 2024
"""

import time
from typing import Dict, Any, List, Optional, Tuple
from services.config.engine_config_service import EngineConfigService
from services.config.config_registry import ConfigRegistry
from services.config.engine_status_checker import EngineStatusChecker
from models.config_models import EngineConfig, EngineStatusEnum
from utils.log_manager import LogManager


class EngineManager:
    """
    引擎配置管理器
    
    提供统一的引擎配置管理接口，协调各个TTS引擎的配置加载和状态管理。
    负责引擎的注册、发现、配置同步等功能。
    """
    
    def __init__(self):
        self.logger = LogManager().get_logger("EngineManager")
        self.engine_config_service = EngineConfigService()
        self.registry = self.engine_config_service.load_registry()
        self.status_checker = EngineStatusChecker()
        
        # 引擎状态缓存
        self._engine_status_cache = {}
        
        # 初始化引擎状态
        self._initialize_engine_status()
    
    def get_available_engines(self) -> List[str]:
        """
        获取可用引擎列表
        
        Returns:
            List[str]: 可用引擎ID列表
        """
        return self.registry.get_available_engines()
    
    def get_engine_config(self, engine_id: str) -> Optional[EngineConfig]:
        """
        获取引擎配置
        
        Args:
            engine_id (str): 引擎ID
            
        Returns:
            Optional[EngineConfig]: 引擎配置对象
        """
        return self.registry.get_engine_config(engine_id)
    
    def get_all_engine_configs(self) -> Dict[str, EngineConfig]:
        """获取所有引擎配置"""
        return self.registry.get_all_engine_configs()
    
    def get_engine_status(self, engine_id: str) -> str:
        """
        获取引擎状态
        
        Args:
            engine_id (str): 引擎ID
            
        Returns:
            str: 引擎状态
        """
        engine_config = self.get_engine_config(engine_id)
        if engine_config:
            return engine_config.status.status.value
        return "unavailable"
    
    def update_engine_status(self, engine_id: str, status: str, 
                           error_message: str = "", available_voices: List[Dict] = None) -> bool:
        """
        更新引擎状态
        
        Args:
            engine_id (str): 引擎ID
            status (str): 新状态
            error_message (str): 错误信息
            available_voices (List[Dict]): 可用语音列表
            
        Returns:
            bool: 更新是否成功
        """
        try:
            # 更新注册表中的状态
            success = self.registry.update_engine_status(engine_id, status, error_message)
            
            if success:
                # 保存到配置文件
                self.engine_config_service.save_registry(self.registry)
                self.logger.info(f"引擎状态更新成功: {engine_id} -> {status}")
            
            return success
            
        except Exception as e:
            self.logger.error(f"更新引擎状态失败 {engine_id}: {e}")
            return False
    
    def get_engines_by_language(self, language: str) -> List[str]:
        """
        根据语言获取引擎列表
        
        Args:
            language (str): 语言代码
            
        Returns:
            List[str]: 支持该语言的引擎ID列表
        """
        return self.registry.get_engines_by_language(language)
    
    def get_engines_by_format(self, output_format: str) -> List[str]:
        """
        根据输出格式获取引擎列表
        
        Args:
            output_format (str): 输出格式
            
        Returns:
            List[str]: 支持该格式的引擎ID列表
        """
        return self.registry.get_engines_by_format(output_format)
    
    def get_engine_priority_order(self) -> List[str]:
        """
        获取引擎优先级顺序
        
        Returns:
            List[str]: 按优先级排序的引擎ID列表
        """
        return self.registry.get_engine_priority_order()
    
    def set_engine_priority(self, engine_id: str, priority: int) -> bool:
        """
        设置引擎优先级
        
        Args:
            engine_id (str): 引擎ID
            priority (int): 优先级 (0-100)
            
        Returns:
            bool: 设置是否成功
        """
        try:
            engine_config = self.get_engine_config(engine_id)
            if engine_config:
                engine_config.priority = priority
                self.registry.set_engine_config(engine_id, engine_config)
                self.engine_config_service.save_registry(self.registry)
                self.logger.info(f"引擎优先级设置成功: {engine_id} -> {priority}")
                return True
            return False
            
        except Exception as e:
            self.logger.error(f"设置引擎优先级失败 {engine_id}: {e}")
            return False
    
    def enable_engine(self, engine_id: str) -> bool:
        """
        启用引擎
        
        Args:
            engine_id (str): 引擎ID
            
        Returns:
            bool: 启用是否成功
        """
        return self._set_engine_enabled(engine_id, True)
    
    def disable_engine(self, engine_id: str) -> bool:
        """
        禁用引擎
        
        Args:
            engine_id (str): 引擎ID
            
        Returns:
            bool: 禁用是否成功
        """
        return self._set_engine_enabled(engine_id, False)
    
    def _set_engine_enabled(self, engine_id: str, enabled: bool) -> bool:
        """
        设置引擎启用状态
        
        Args:
            engine_id (str): 引擎ID
            enabled (bool): 是否启用
            
        Returns:
            bool: 设置是否成功
        """
        try:
            engine_config = self.get_engine_config(engine_id)
            if engine_config:
                engine_config.enabled = enabled
                self.registry.set_engine_config(engine_id, engine_config)
                self.engine_config_service.save_registry(self.registry)
                status = "启用" if enabled else "禁用"
                self.logger.info(f"引擎{status}成功: {engine_id}")
                return True
            return False
            
        except Exception as e:
            self.logger.error(f"设置引擎启用状态失败 {engine_id}: {e}")
            return False
    
    def get_engine_summary(self) -> Dict[str, Any]:
        """
        获取引擎摘要信息
        
        Returns:
            Dict[str, Any]: 引擎摘要信息
        """
        summary = {
            "total_engines": len(self.registry._engine_configs),
            "available_engines": len(self.get_available_engines()),
            "enabled_engines": len([e for e in self.registry._engine_configs.values() if e.enabled]),
            "online_engines": len([e for e in self.registry._engine_configs.values() if e.info.is_online]),
            "engines": {}
        }
        
        for engine_id, config in self.registry._engine_configs.items():
            summary["engines"][engine_id] = {
                "name": config.info.name,
                "version": config.info.version,
                "status": config.status.status.value,
                "enabled": config.enabled,
                "is_online": config.info.is_online,
                "priority": config.priority,
                "supported_languages": config.info.supported_languages,
                "supported_formats": config.info.supported_formats
            }
        
        return summary
    
    def _initialize_engine_status(self):
        """初始化引擎状态"""
        try:
            # 执行实际的引擎状态检查
            self.refresh_engine_status()
            self.logger.info("引擎状态初始化完成")
            
        except Exception as e:
            self.logger.error(f"初始化引擎状态失败: {e}")
    
    def check_engine_availability(self, engine_id: str) -> Tuple[bool, str, Dict[str, Any]]:
        """
        检查单个引擎的可用性
        
        Args:
            engine_id (str): 引擎ID
            
        Returns:
            Tuple[bool, str, Dict[str, Any]]: (是否可用, 状态信息, 详细信息)
        """
        try:
            engine_config = self.get_engine_config(engine_id)
            if not engine_config:
                return False, "引擎配置不存在", {}
            
            return self.status_checker.check_engine_status(engine_id, engine_config)
            
        except Exception as e:
            self.logger.error(f"检查引擎可用性失败 {engine_id}: {e}")
            return False, f"检查失败: {e}", {}
    
    def perform_health_check(self) -> Dict[str, Any]:
        """
        执行健康检查
        
        Returns:
            Dict[str, Any]: 健康检查结果
        """
        try:
            self.logger.info("开始执行引擎健康检查...")
            
            # 检查所有引擎
            check_results = self.status_checker.check_all_engines(self.registry._engine_configs)
            
            # 更新引擎状态
            for engine_id, result in check_results.items():
                status = EngineStatusEnum.AVAILABLE if result["available"] else EngineStatusEnum.UNAVAILABLE
                self.update_engine_status(
                    engine_id, 
                    status.value, 
                    result["status_message"]
                )
            
            # 生成健康检查报告
            health_report = {
                "check_time": time.time(),
                "total_engines": len(self.registry._engine_configs),
                "available_engines": len([r for r in check_results.values() if r["available"]]),
                "unavailable_engines": len([r for r in check_results.values() if not r["available"]]),
                "results": check_results
            }
            
            self.logger.info(f"引擎健康检查完成: {health_report['available_engines']}/{health_report['total_engines']} 可用")
            return health_report
            
        except Exception as e:
            self.logger.error(f"执行健康检查失败: {e}")
            return {"error": str(e)}
    
    def refresh_engine_status(self) -> Dict[str, str]:
        """
        刷新所有引擎状态
        
        Returns:
            Dict[str, str]: 引擎状态字典
        """
        status_dict = {}
        
        for engine_id in self.registry._engine_configs.keys():
            try:
                # 这里可以添加实际的引擎状态检查逻辑
                # 目前只是返回当前状态
                current_status = self.get_engine_status(engine_id)
                status_dict[engine_id] = current_status
                
            except Exception as e:
                self.logger.error(f"刷新引擎状态失败 {engine_id}: {e}")
                status_dict[engine_id] = "error"
        
        return status_dict
    
    def get_engine_parameters(self, engine_id: str) -> Optional[Dict[str, Any]]:
        """
        获取引擎参数
        
        Args:
            engine_id (str): 引擎ID
            
        Returns:
            Optional[Dict[str, Any]]: 引擎参数字典
        """
        engine_config = self.get_engine_config(engine_id)
        if engine_config:
            return {
                "voice_name": engine_config.parameters.voice_name,
                "rate": engine_config.parameters.rate,
                "pitch": engine_config.parameters.pitch,
                "volume": engine_config.parameters.volume,
                "language": engine_config.parameters.language,
                "output_format": engine_config.parameters.output_format,
                "extra_params": engine_config.parameters.extra_params
            }
        return None
    
    def update_engine_parameters(self, engine_id: str, parameters: Dict[str, Any]) -> bool:
        """
        更新引擎参数
        
        Args:
            engine_id (str): 引擎ID
            parameters (Dict[str, Any]): 参数字典
            
        Returns:
            bool: 更新是否成功
        """
        try:
            engine_config = self.get_engine_config(engine_id)
            if engine_config:
                # 更新参数
                for key, value in parameters.items():
                    if hasattr(engine_config.parameters, key):
                        setattr(engine_config.parameters, key, value)
                
                # 保存配置
                self.registry.set_engine_config(engine_id, engine_config)
                self.engine_config_service.save_registry(self.registry)
                
                self.logger.info(f"引擎参数更新成功: {engine_id}")
                return True
            return False
            
        except Exception as e:
            self.logger.error(f"更新引擎参数失败 {engine_id}: {e}")
            return False
