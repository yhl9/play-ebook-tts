"""
设置控制器
"""

from typing import Optional, Dict, Any
from abc import ABC, abstractmethod

from models.config_model import AppConfig
from services.json_config_service import JsonConfigService, ConfigurationError
from utils.log_manager import LogManager


class ISettingsController(ABC):
    """设置控制器接口"""
    
    @abstractmethod
    def load_settings(self) -> AppConfig:
        pass
    
    @abstractmethod
    def save_settings(self, config: AppConfig):
        pass
    
    @abstractmethod
    def get_setting(self, section: str, key: str, default_value: Any = None):
        pass
    
    @abstractmethod
    def set_setting(self, section: str, key: str, value: Any):
        pass


class SettingsController(ISettingsController):
    """设置控制器实现"""
    
    def __init__(self, config_file: str = 'config.json'):
        self.logger = LogManager().get_logger("SettingsController")
        self.config_service = JsonConfigService(config_file)
        self.current_config: Optional[AppConfig] = None
    
    def load_settings(self) -> AppConfig:
        """加载设置"""
        try:
            self.logger.info("加载应用设置")
            
            self.current_config = self.config_service.load_config()
            
            self.logger.info("应用设置加载成功")
            return self.current_config
            
        except Exception as e:
            self.logger.error(f"加载设置失败: {e}")
            raise ConfigurationError(f"加载设置失败: {e}")
    
    def save_settings(self, config: AppConfig):
        """保存设置"""
        try:
            self.logger.info("保存应用设置")
            
            self.config_service.save_config(config)
            self.current_config = config
            
            self.logger.info("应用设置保存成功")
            
        except Exception as e:
            self.logger.error(f"保存设置失败: {e}")
            raise ConfigurationError(f"保存设置失败: {e}")
    
    def get_setting(self, section: str, key: str, default_value: Any = None):
        """获取设置值"""
        try:
            return self.config_service.get_config_value(section, key, default_value)
        except Exception as e:
            self.logger.error(f"获取设置失败: {e}")
            return default_value
    
    def set_setting(self, section: str, key: str, value: Any):
        """设置值"""
        try:
            self.config_service.set_config_value(section, key, str(value))
        except Exception as e:
            self.logger.error(f"设置值失败: {e}")
            raise ConfigurationError(f"设置值失败: {e}")
    
    def get_current_config(self) -> Optional[AppConfig]:
        """获取当前配置"""
        return self.current_config
    
    def update_config(self, **kwargs):
        """更新配置"""
        try:
            if not self.current_config:
                self.current_config = self.load_settings()
            
            # 更新配置属性
            for key, value in kwargs.items():
                if hasattr(self.current_config, key):
                    setattr(self.current_config, key, value)
                else:
                    self.logger.warning(f"未知配置项: {key}")
            
            # 保存配置
            self.save_settings(self.current_config)
            
        except Exception as e:
            self.logger.error(f"更新配置失败: {e}")
            raise ConfigurationError(f"更新配置失败: {e}")
    
    def reset_to_defaults(self):
        """重置为默认设置"""
        try:
            self.logger.info("重置设置为默认值")
            
            self.config_service.reset_config()
            self.current_config = self.load_settings()
            
            self.logger.info("设置已重置为默认值")
            
        except Exception as e:
            self.logger.error(f"重置设置失败: {e}")
            raise ConfigurationError(f"重置设置失败: {e}")
    
    def export_settings(self, export_path: str):
        """导出设置"""
        try:
            self.logger.info(f"导出设置到: {export_path}")
            
            self.config_service.export_config(export_path)
            
            self.logger.info("设置导出成功")
            
        except Exception as e:
            self.logger.error(f"导出设置失败: {e}")
            raise ConfigurationError(f"导出设置失败: {e}")
    
    def import_settings(self, import_path: str):
        """导入设置"""
        try:
            self.logger.info(f"从 {import_path} 导入设置")
            
            self.config_service.import_config(import_path)
            self.current_config = self.load_settings()
            
            self.logger.info("设置导入成功")
            
        except Exception as e:
            self.logger.error(f"导入设置失败: {e}")
            raise ConfigurationError(f"导入设置失败: {e}")
    
    def get_ui_settings(self) -> Dict[str, Any]:
        """获取UI设置"""
        try:
            if not self.current_config:
                self.current_config = self.load_settings()
            
            return {
                'theme': self.current_config.theme,
                'language': self.current_config.language,
                'window_width': self.current_config.window_width,
                'window_height': self.current_config.window_height,
                'window_x': self.current_config.window_x,
                'window_y': self.current_config.window_y
            }
            
        except Exception as e:
            self.logger.error(f"获取UI设置失败: {e}")
            return {}
    
    def update_ui_settings(self, **kwargs):
        """更新UI设置"""
        try:
            ui_keys = ['theme', 'language', 'window_width', 'window_height', 'window_x', 'window_y']
            
            for key, value in kwargs.items():
                if key in ui_keys:
                    self.update_config(**{key: value})
                else:
                    self.logger.warning(f"未知UI设置项: {key}")
                    
        except Exception as e:
            self.logger.error(f"更新UI设置失败: {e}")
            raise ConfigurationError(f"更新UI设置失败: {e}")
    
    def get_audio_settings(self) -> Dict[str, Any]:
        """获取音频设置"""
        try:
            if not self.current_config:
                self.current_config = self.load_settings()
            
            return {
                'default_audio_format': self.current_config.default_audio_format,
                'default_sample_rate': self.current_config.default_sample_rate,
                'default_bitrate': self.current_config.default_bitrate
            }
            
        except Exception as e:
            self.logger.error(f"获取音频设置失败: {e}")
            return {}
    
    def update_audio_settings(self, **kwargs):
        """更新音频设置"""
        try:
            audio_keys = ['default_audio_format', 'default_sample_rate', 'default_bitrate']
            
            for key, value in kwargs.items():
                if key in audio_keys:
                    self.update_config(**{key: value})
                else:
                    self.logger.warning(f"未知音频设置项: {key}")
                    
        except Exception as e:
            self.logger.error(f"更新音频设置失败: {e}")
            raise ConfigurationError(f"更新音频设置失败: {e}")
    
    def get_tts_settings(self) -> Dict[str, Any]:
        """获取TTS设置"""
        try:
            if not self.current_config:
                self.current_config = self.load_settings()
            
            return {
                'default_tts_engine': self.current_config.default_tts_engine,
                'default_voice': self.current_config.default_voice,
                'default_rate': self.current_config.default_rate,
                'default_pitch': self.current_config.default_pitch,
                'default_volume': self.current_config.default_volume
            }
            
        except Exception as e:
            self.logger.error(f"获取TTS设置失败: {e}")
            return {}
    
    def update_tts_settings(self, **kwargs):
        """更新TTS设置"""
        try:
            tts_keys = ['default_tts_engine', 'default_voice', 'default_rate', 'default_pitch', 'default_volume']
            
            for key, value in kwargs.items():
                if key in tts_keys:
                    self.update_config(**{key: value})
                else:
                    self.logger.warning(f"未知TTS设置项: {key}")
                    
        except Exception as e:
            self.logger.error(f"更新TTS设置失败: {e}")
            raise ConfigurationError(f"更新TTS设置失败: {e}")
    
    def get_advanced_settings(self) -> Dict[str, Any]:
        """获取高级设置"""
        try:
            if not self.current_config:
                self.current_config = self.load_settings()
            
            return {
                'max_concurrent_tasks': self.current_config.max_concurrent_tasks,
                'memory_limit_mb': self.current_config.memory_limit_mb,
                'enable_hardware_acceleration': self.current_config.enable_hardware_acceleration,
                'debug_mode': self.current_config.debug_mode,
                'log_level': self.current_config.log_level
            }
            
        except Exception as e:
            self.logger.error(f"获取高级设置失败: {e}")
            return {}
    
    def update_advanced_settings(self, **kwargs):
        """更新高级设置"""
        try:
            advanced_keys = ['max_concurrent_tasks', 'memory_limit_mb', 'enable_hardware_acceleration', 'debug_mode', 'log_level']
            
            for key, value in kwargs.items():
                if key in advanced_keys:
                    self.update_config(**{key: value})
                else:
                    self.logger.warning(f"未知高级设置项: {key}")
                    
        except Exception as e:
            self.logger.error(f"更新高级设置失败: {e}")
            raise ConfigurationError(f"更新高级设置失败: {e}")
    
    def validate_settings(self, config: AppConfig) -> Dict[str, Any]:
        """验证设置"""
        try:
            validation_result = {
                'valid': True,
                'issues': []
            }
            
            # 验证窗口大小
            if config.window_width < 800 or config.window_height < 600:
                validation_result['issues'].append("窗口大小过小")
            
            # 验证音频设置
            if config.default_sample_rate not in [8000, 16000, 22050, 44100, 48000]:
                validation_result['issues'].append("不支持的采样率")
            
            if config.default_bitrate < 64 or config.default_bitrate > 320:
                validation_result['issues'].append("比特率超出范围")
            
            # 验证TTS设置
            if config.default_rate < 0.1 or config.default_rate > 3.0:
                validation_result['issues'].append("语速超出范围")
            
            if config.default_pitch < -50 or config.default_pitch > 50:
                validation_result['issues'].append("音调超出范围")
            
            if config.default_volume < 0.0 or config.default_volume > 1.0:
                validation_result['issues'].append("音量超出范围")
            
            # 验证高级设置
            if config.max_concurrent_tasks < 1 or config.max_concurrent_tasks > 10:
                validation_result['issues'].append("并发任务数超出范围")
            
            if config.memory_limit_mb < 256 or config.memory_limit_mb > 8192:
                validation_result['issues'].append("内存限制超出范围")
            
            if validation_result['issues']:
                validation_result['valid'] = False
            
            return validation_result
            
        except Exception as e:
            self.logger.error(f"验证设置失败: {e}")
            return {
                'valid': False,
                'issues': [f"验证失败: {e}"]
            }
    
    def get_settings_summary(self) -> Dict[str, Any]:
        """获取设置摘要"""
        try:
            if not self.current_config:
                self.current_config = self.load_settings()
            
            return {
                'ui': self.get_ui_settings(),
                'audio': self.get_audio_settings(),
                'tts': self.get_tts_settings(),
                'advanced': self.get_advanced_settings(),
                'validation': self.validate_settings(self.current_config)
            }
            
        except Exception as e:
            self.logger.error(f"获取设置摘要失败: {e}")
            return {}
