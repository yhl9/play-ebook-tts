"""
功能开关模块

提供功能开关管理，允许在运行时启用/禁用特定功能，
便于调试和逐步发布新功能。

作者: TTS开发团队
版本: 1.0.0
创建时间: 2024
"""

import os
from typing import Dict, Any
from utils.log_manager import LogManager


class FeatureFlags:
    """
    功能开关管理器
    
    管理应用程序的功能开关，支持环境变量和配置文件两种方式。
    提供功能启用/禁用的统一接口。
    """
    
    def __init__(self):
        self.logger = LogManager().get_logger("FeatureFlags")
        self._flags = self._load_flags()
    
    def _load_flags(self) -> Dict[str, bool]:
        """
        加载功能开关配置
        
        Returns:
            Dict[str, bool]: 功能开关字典
        """
        flags = {
            # 核心功能
            'voice_settings_defaults': True,  # 语音设置默认值功能
            'dynamic_parameter_ui': True,     # 动态参数UI
            'engine_auto_detection': True,    # 引擎自动检测
            
            # 调试功能
            'debug_logging': os.getenv('TTS_DEBUG', 'false').lower() == 'true',
            'verbose_errors': os.getenv('TTS_VERBOSE', 'false').lower() == 'true',
            'performance_monitoring': os.getenv('TTS_PERF', 'false').lower() == 'true',
            
            # 实验性功能
            'advanced_voice_preview': False,  # 高级语音预览
            'batch_processing': True,         # 批量处理
            'cloud_sync': False,             # 云同步
            
            # 兼容性功能
            'legacy_config_support': True,   # 旧配置支持
            'backward_compatibility': True,  # 向后兼容
        }
        
        # 从环境变量覆盖配置
        for key in flags:
            env_key = f'TTS_FEATURE_{key.upper()}'
            if env_key in os.environ:
                flags[key] = os.environ[env_key].lower() == 'true'
        
        self.logger.info(f"功能开关已加载: {flags}")
        return flags
    
    def is_enabled(self, feature: str) -> bool:
        """
        检查功能是否启用
        
        Args:
            feature (str): 功能名称
            
        Returns:
            bool: 功能是否启用
        """
        return self._flags.get(feature, False)
    
    def enable(self, feature: str):
        """
        启用功能
        
        Args:
            feature (str): 功能名称
        """
        self._flags[feature] = True
        self.logger.info(f"功能已启用: {feature}")
    
    def disable(self, feature: str):
        """
        禁用功能
        
        Args:
            feature (str): 功能名称
        """
        self._flags[feature] = False
        self.logger.info(f"功能已禁用: {feature}")
    
    def get_all_flags(self) -> Dict[str, bool]:
        """
        获取所有功能开关
        
        Returns:
            Dict[str, bool]: 所有功能开关字典
        """
        return self._flags.copy()
    
    def set_flag(self, feature: str, enabled: bool):
        """
        设置功能开关
        
        Args:
            feature (str): 功能名称
            enabled (bool): 是否启用
        """
        self._flags[feature] = enabled
        self.logger.info(f"功能开关已设置: {feature} = {enabled}")


# 全局功能开关实例
feature_flags = FeatureFlags()
