"""
配置管理服务模块

提供分离后的配置管理功能，包括应用程序配置、引擎配置等。
采用清晰的服务架构，支持配置验证、迁移和备份。

作者: TTS开发团队
版本: 2.0.0
创建时间: 2024
"""

from .app_config_service import AppConfigService
from .engine_config_service import EngineConfigService
from .config_registry import ConfigRegistry
from .config_validator import ConfigValidator
from .config_migrator import ConfigMigrator
from .config_backup import ConfigBackup

# 导出所有配置服务类
__all__ = [
    'AppConfigService',      # 应用程序配置服务
    'EngineConfigService',   # 引擎配置服务
    'ConfigRegistry',        # 配置注册表
    'ConfigValidator',       # 配置验证器
    'ConfigMigrator',        # 配置迁移器
    'ConfigBackup'          # 配置备份
]
