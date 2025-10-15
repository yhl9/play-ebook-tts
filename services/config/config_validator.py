"""
配置验证器

提供配置验证功能，包括格式验证、值范围验证、依赖验证等。
确保配置的正确性和一致性。

作者: TTS开发团队
版本: 2.0.0
创建时间: 2024
"""

from typing import Dict, Any, List, Tuple, Optional
from models.config_models import AppConfig, EngineConfig, UIConfig, FileConfig, PerformanceConfig, UserPreferences
from utils.log_manager import LogManager


class ConfigValidator:
    """
    配置验证器
    
    提供配置验证功能，包括格式验证、值范围验证、依赖验证等。
    确保配置的正确性和一致性。
    """
    
    def __init__(self):
        self.logger = LogManager().get_logger("ConfigValidator")
        self._validation_rules = self._load_validation_rules()
    
    def validate_app_config(self, config: AppConfig) -> Tuple[bool, List[str]]:
        """
        验证应用程序配置
        
        Args:
            config (AppConfig): 应用程序配置对象
            
        Returns:
            Tuple[bool, List[str]]: (是否有效, 错误信息列表)
        """
        errors = []
        
        try:
            # 验证版本
            if not self._validate_version(config.version):
                errors.append("无效的版本号格式")
            
            # 验证UI配置
            ui_valid, ui_errors = self.validate_ui_config(config.ui)
            if not ui_valid:
                errors.extend([f"UI配置错误: {error}" for error in ui_errors])
            
            # 验证文件配置
            files_valid, files_errors = self.validate_file_config(config.files)
            if not files_valid:
                errors.extend([f"文件配置错误: {error}" for error in files_errors])
            
            # 验证性能配置
            performance_valid, performance_errors = self.validate_performance_config(config.performance)
            if not performance_valid:
                errors.extend([f"性能配置错误: {error}" for error in performance_errors])
            
            # 验证用户偏好配置
            preferences_valid, preferences_errors = self.validate_preferences_config(config.preferences)
            if not preferences_valid:
                errors.extend([f"用户偏好配置错误: {error}" for error in preferences_errors])
            
            # 验证日志级别
            if config.log_level not in ["DEBUG", "INFO", "WARNING", "ERROR", "CRITICAL"]:
                errors.append("无效的日志级别")
            
            is_valid = len(errors) == 0
            if is_valid:
                self.logger.info("应用程序配置验证通过")
            else:
                self.logger.warning(f"应用程序配置验证失败: {errors}")
            
            return is_valid, errors
            
        except Exception as e:
            error_msg = f"配置验证异常: {e}"
            self.logger.error(error_msg)
            return False, [error_msg]
    
    def validate_ui_config(self, config: UIConfig) -> Tuple[bool, List[str]]:
        """验证UI配置"""
        errors = []
        
        # 验证主题
        if config.theme not in ["light", "dark", "blue", "green", "purple"]:
            errors.append("无效的主题")
        
        # 验证语言
        if config.language not in ["zh-CN", "en-US", "ja-JP"]:
            errors.append("不支持的语言")
        
        # 验证窗口大小
        if not (800 <= config.window_width <= 2560):
            errors.append("窗口宽度超出有效范围 (800-2560)")
        
        if not (600 <= config.window_height <= 1440):
            errors.append("窗口高度超出有效范围 (600-1440)")
        
        # 验证窗口位置
        if config.window_x < 0 or config.window_y < 0:
            errors.append("窗口位置不能为负数")
        
        # 验证字体大小
        if not (8 <= config.font_size <= 24):
            errors.append("字体大小超出有效范围 (8-24)")
        
        # 验证自动保存间隔
        if not (60 <= config.auto_save_interval <= 3600):
            errors.append("自动保存间隔超出有效范围 (60-3600秒)")
        
        return len(errors) == 0, errors
    
    def validate_file_config(self, config: FileConfig) -> Tuple[bool, List[str]]:
        """验证文件配置"""
        errors = []
        
        # 验证目录路径
        for dir_name, dir_path in [
            ("输入目录", config.input_dir),
            ("输出目录", config.output_dir),
            ("临时目录", config.temp_dir),
            ("缓存目录", config.cache_dir),
            ("备份目录", config.backup_dir)
        ]:
            if not dir_path or not isinstance(dir_path, str):
                errors.append(f"{dir_name}路径不能为空")
            elif not self._is_valid_path(dir_path):
                errors.append(f"{dir_name}路径格式无效: {dir_path}")
        
        # 验证文件大小限制
        if not (1 <= config.max_file_size_mb <= 1024):
            errors.append("最大文件大小超出有效范围 (1-1024MB)")
        
        # 验证清理间隔
        if not (300 <= config.auto_clean_interval <= 86400):
            errors.append("自动清理间隔超出有效范围 (300-86400秒)")
        
        return len(errors) == 0, errors
    
    def validate_performance_config(self, config: PerformanceConfig) -> Tuple[bool, List[str]]:
        """验证性能配置"""
        errors = []
        
        # 验证并发任务数
        if not (1 <= config.max_concurrent_tasks <= 16):
            errors.append("最大并发任务数超出有效范围 (1-16)")
        
        # 验证内存限制
        if not (256 <= config.memory_limit_mb <= 8192):
            errors.append("内存限制超出有效范围 (256-8192MB)")
        
        # 验证缓存配置
        if config.enable_caching:
            if not (60 <= config.cache_duration <= 86400):
                errors.append("缓存持续时间超出有效范围 (60-86400秒)")
            
            if not (10 <= config.max_cache_size <= 1000):
                errors.append("最大缓存大小超出有效范围 (10-1000)")
        
        return len(errors) == 0, errors
    
    def validate_preferences_config(self, config: UserPreferences) -> Tuple[bool, List[str]]:
        """验证用户偏好配置"""
        errors = []
        
        # 验证默认引擎
        valid_engines = ["piper_tts", "emotivoice_tts_api", "pyttsx3", "index_tts_api_15"]
        if config.default_engine not in valid_engines:
            errors.append(f"无效的默认引擎: {config.default_engine}")
        
        # 验证语速
        if not (0.1 <= config.default_rate <= 3.0):
            errors.append("默认语速超出有效范围 (0.1-3.0)")
        
        # 验证音调
        if not (-50 <= config.default_pitch <= 50):
            errors.append("默认音调超出有效范围 (-50-50)")
        
        # 验证音量
        if not (0.0 <= config.default_volume <= 2.0):
            errors.append("默认音量超出有效范围 (0.0-2.0)")
        
        # 验证语言
        if config.default_language not in ["zh-CN", "en-US", "ja-JP"]:
            errors.append("不支持默认语言")
        
        # 验证格式
        valid_formats = ["wav", "mp3", "ogg", "m4a", "aac"]
        if config.default_format not in valid_formats:
            errors.append(f"不支持的默认格式: {config.default_format}")
        
        return len(errors) == 0, errors
    
    def validate_engine_config(self, config: EngineConfig) -> Tuple[bool, List[str]]:
        """验证引擎配置"""
        errors = []
        
        # 验证引擎信息
        if not config.info.id or not config.info.name:
            errors.append("引擎ID和名称不能为空")
        
        # 验证版本号
        if not self._validate_version(config.info.version):
            errors.append("无效的引擎版本号格式")
        
        # 验证参数
        if not (0.1 <= config.parameters.rate <= 3.0):
            errors.append("语速超出有效范围 (0.1-3.0)")
        
        if not (-50 <= config.parameters.pitch <= 50):
            errors.append("音调超出有效范围 (-50-50)")
        
        if not (0.0 <= config.parameters.volume <= 2.0):
            errors.append("音量超出有效范围 (0.0-2.0)")
        
        # 验证优先级
        if not (0 <= config.priority <= 100):
            errors.append("优先级超出有效范围 (0-100)")
        
        return len(errors) == 0, errors
    
    def validate_config_consistency(self, app_config: AppConfig, engine_configs: Dict[str, EngineConfig]) -> Tuple[bool, List[str]]:
        """验证配置一致性"""
        errors = []
        
        # 验证默认引擎是否存在
        default_engine = app_config.preferences.default_engine
        if default_engine not in engine_configs:
            errors.append(f"默认引擎 {default_engine} 未注册")
        elif not engine_configs[default_engine].enabled:
            errors.append(f"默认引擎 {default_engine} 已禁用")
        
        # 验证引擎配置一致性
        for engine_id, engine_config in engine_configs.items():
            if engine_config.enabled:
                # 验证引擎参数与应用程序设置的一致性
                if engine_config.parameters.language != app_config.preferences.default_language:
                    self.logger.warning(f"引擎 {engine_id} 语言设置与默认语言不一致")
                
                if engine_config.parameters.output_format != app_config.preferences.default_format:
                    self.logger.warning(f"引擎 {engine_id} 输出格式与默认格式不一致")
        
        return len(errors) == 0, errors
    
    def _validate_version(self, version: str) -> bool:
        """验证版本号格式"""
        try:
            parts = version.split('.')
            if len(parts) != 3:
                return False
            
            for part in parts:
                if not part.isdigit():
                    return False
                if int(part) < 0:
                    return False
            
            return True
        except:
            return False
    
    def _is_valid_path(self, path: str) -> bool:
        """验证路径格式"""
        try:
            import os
            # 检查路径是否包含非法字符
            invalid_chars = '<>:"|?*'
            for char in invalid_chars:
                if char in path:
                    return False
            
            # 检查路径长度
            if len(path) > 260:
                return False
            
            return True
        except:
            return False
    
    def _load_validation_rules(self) -> Dict[str, Any]:
        """加载验证规则"""
        return {
            "version_pattern": r"^\d+\.\d+\.\d+$",
            "window_size": {"min_width": 800, "max_width": 2560, "min_height": 600, "max_height": 1440},
            "font_size": {"min": 8, "max": 24},
            "rate_range": {"min": 0.1, "max": 3.0},
            "pitch_range": {"min": -50, "max": 50},
            "volume_range": {"min": 0.0, "max": 2.0},
            "concurrent_tasks": {"min": 1, "max": 16},
            "memory_limit": {"min": 256, "max": 8192},
            "cache_duration": {"min": 60, "max": 86400},
            "max_cache_size": {"min": 10, "max": 1000}
        }
