"""
配置服务模块

提供应用程序配置的管理功能，包括：
- 配置文件读写：支持JSON格式的配置文件
- 配置验证：确保配置项的有效性和完整性
- 默认配置：提供合理的默认配置值
- 配置迁移：支持配置格式的升级和迁移
- 配置备份：自动备份重要配置

支持的配置类型：
- 应用程序配置：窗口大小、主题、语言等
- 语音配置：TTS引擎、语音参数等
- 输出配置：音频格式、输出目录等
- 用户设置：个性化配置项

作者: TTS开发团队
版本: 1.0.0
创建时间: 2024
"""

import os
import json
from pathlib import Path
from typing import Optional, Dict, Any

from models.config_model import AppConfig
from models.audio_model import VoiceConfig, OutputConfig
from utils.log_manager import LogManager


class ConfigService:
    """
    配置管理服务类
    
    负责应用程序配置的加载、保存、验证和管理。
    提供统一的配置接口，支持多种配置类型和格式。
    
    特性：
    - 自动创建：首次运行时自动创建默认配置
    - 配置验证：确保配置项的有效性
    - 错误恢复：配置损坏时自动恢复默认配置
    - 备份机制：重要配置的自动备份
    - 格式支持：支持JSON格式的配置文件
    """
    
    def __init__(self, config_file: str = 'config.json'):
        self.logger = LogManager().get_logger("ConfigService")
        self.config_file = Path(config_file)
        self.config_data = {}
        self._default_config = self._create_default_config()
    
    def load_config(self) -> AppConfig:
        """加载配置"""
        try:
            if self.config_file.exists():
                with open(self.config_file, 'r', encoding='utf-8') as f:
                    self.config_data = json.load(f)
                self.logger.info(f"配置文件加载成功: {self.config_file}")
            else:
                self.logger.info("配置文件不存在，创建默认配置")
                self.create_default_config()
            
            return self._parse_config()
            
        except Exception as e:
            self.logger.error(f"配置加载失败: {e}")
            return self._default_config
    
    def save_config(self, app_config: AppConfig):
        """保存配置"""
        try:
            self._update_config_data(app_config)
            
            # 确保配置目录存在
            self.config_file.parent.mkdir(parents=True, exist_ok=True)
            
            # 保存配置文件
            with open(self.config_file, 'w', encoding='utf-8') as f:
                json.dump(self.config_data, f, ensure_ascii=False, indent=2)
            
            self.logger.info(f"配置保存成功: {self.config_file}")
            
        except Exception as e:
            self.logger.error(f"配置保存失败: {e}")
            raise ConfigurationError(f"配置保存失败: {e}")
    
    def create_default_config(self):
        """创建默认配置"""
        try:
            self._update_config_data(self._default_config)
            self.save_config(self._default_config)
            self.logger.info("默认配置创建成功")
            
        except Exception as e:
            self.logger.error(f"创建默认配置失败: {e}")
    
    def reset_config(self):
        """重置配置为默认值"""
        try:
            self.save_config(self._default_config)
            self.logger.info("配置已重置为默认值")
            
        except Exception as e:
            self.logger.error(f"重置配置失败: {e}")
    
    def export_config(self, export_path: str):
        """导出配置"""
        try:
            export_path = Path(export_path)
            export_path.parent.mkdir(parents=True, exist_ok=True)
            
            with open(export_path, 'w', encoding='utf-8') as f:
                self.config.write(f)
            
            self.logger.info(f"配置导出成功: {export_path}")
            
        except Exception as e:
            self.logger.error(f"配置导出失败: {e}")
            raise ConfigurationError(f"配置导出失败: {e}")
    
    def import_config(self, import_path: str):
        """导入配置"""
        try:
            import_path = Path(import_path)
            if not import_path.exists():
                raise FileNotFoundError(f"配置文件不存在: {import_path}")
            
            self.config.read(import_path, encoding='utf-8')
            self.save_config(self._parse_config())
            
            self.logger.info(f"配置导入成功: {import_path}")
            
        except Exception as e:
            self.logger.error(f"配置导入失败: {e}")
            raise ConfigurationError(f"配置导入失败: {e}")
    
    def _create_default_config(self) -> AppConfig:
        """创建默认配置对象"""
        return AppConfig()
    
    def _parse_config(self) -> AppConfig:
        """解析配置文件"""
        try:
            config_data = {}
            
            # 解析UI设置
            if self.config.has_section('UI'):
                config_data.update({
                    'theme': self.config.get('UI', 'theme', fallback='light'),
                    'language': self.config.get('UI', 'language', fallback='zh-CN'),
                    'window_width': self.config.getint('UI', 'window_width', fallback=1200),
                    'window_height': self.config.getint('UI', 'window_height', fallback=800),
                    'window_x': self.config.getint('UI', 'window_x', fallback=100),
                    'window_y': self.config.getint('UI', 'window_y', fallback=100)
                })
            
            # 解析文件设置
            if self.config.has_section('File'):
                config_data.update({
                    'default_output_dir': self.config.get('File', 'default_output_dir', fallback='./output'),
                    'temp_dir': self.config.get('File', 'temp_dir', fallback='./temp'),
                    'auto_clean_temp': self.config.getboolean('File', 'auto_clean_temp', fallback=True),
                    'max_file_size_mb': self.config.getint('File', 'max_file_size_mb', fallback=100)
                })
            
            # 解析音频设置
            if self.config.has_section('Audio'):
                config_data.update({
                    'default_audio_format': self.config.get('Audio', 'default_format', fallback='wav'),
                    'default_sample_rate': self.config.getint('Audio', 'default_sample_rate', fallback=44100),
                    'default_bitrate': self.config.getint('Audio', 'default_bitrate', fallback=128)
                })
            
            # 解析TTS设置
            if self.config.has_section('TTS'):
                config_data.update({
                    'default_tts_engine': self.config.get('TTS', 'default_engine', fallback='piper_tts'),
                    'default_voice': self.config.get('TTS', 'default_voice', fallback='zh_CN-huayan-medium'),
                    'default_rate': self.config.getfloat('TTS', 'default_rate', fallback=1.0),
                    'default_pitch': self.config.getfloat('TTS', 'default_pitch', fallback=0.0),
                    'default_volume': self.config.getfloat('TTS', 'default_volume', fallback=1.0)
                })
            
            # 解析高级设置
            if self.config.has_section('Advanced'):
                config_data.update({
                    'max_concurrent_tasks': self.config.getint('Advanced', 'max_concurrent_tasks', fallback=2),
                    'memory_limit_mb': self.config.getint('Advanced', 'memory_limit_mb', fallback=1024),
                    'enable_hardware_acceleration': self.config.getboolean('Advanced', 'enable_hardware_acceleration', fallback=False),
                    'debug_mode': self.config.getboolean('Advanced', 'debug_mode', fallback=False),
                    'log_level': self.config.get('Advanced', 'log_level', fallback='INFO')
                })
            
            return AppConfig.from_dict(config_data)
            
        except Exception as e:
            self.logger.error(f"配置解析失败: {e}")
            return self._default_config
    
    def _update_config_parser(self, app_config: AppConfig):
        """更新配置解析器"""
        try:
            # 清除现有配置
            self.config.clear()
            
            # UI设置
            self.config.add_section('UI')
            self.config.set('UI', 'theme', app_config.theme)
            self.config.set('UI', 'language', app_config.language)
            self.config.set('UI', 'window_width', str(app_config.window_width))
            self.config.set('UI', 'window_height', str(app_config.window_height))
            self.config.set('UI', 'window_x', str(app_config.window_x))
            self.config.set('UI', 'window_y', str(app_config.window_y))
            
            # 文件设置
            self.config.add_section('File')
            self.config.set('File', 'default_output_dir', app_config.default_output_dir)
            self.config.set('File', 'temp_dir', app_config.temp_dir)
            self.config.set('File', 'auto_clean_temp', str(app_config.auto_clean_temp))
            self.config.set('File', 'max_file_size_mb', str(app_config.max_file_size_mb))
            
            # 音频设置
            self.config.add_section('Audio')
            self.config.set('Audio', 'default_format', app_config.default_audio_format)
            self.config.set('Audio', 'default_sample_rate', str(app_config.default_sample_rate))
            self.config.set('Audio', 'default_bitrate', str(app_config.default_bitrate))
            
            # TTS设置
            self.config.add_section('TTS')
            self.config.set('TTS', 'default_engine', app_config.default_tts_engine)
            self.config.set('TTS', 'default_voice', app_config.default_voice)
            self.config.set('TTS', 'default_rate', str(app_config.default_rate))
            self.config.set('TTS', 'default_pitch', str(app_config.default_pitch))
            self.config.set('TTS', 'default_volume', str(app_config.default_volume))
            
            # 高级设置
            self.config.add_section('Advanced')
            self.config.set('Advanced', 'max_concurrent_tasks', str(app_config.max_concurrent_tasks))
            self.config.set('Advanced', 'memory_limit_mb', str(app_config.memory_limit_mb))
            self.config.set('Advanced', 'enable_hardware_acceleration', str(app_config.enable_hardware_acceleration))
            self.config.set('Advanced', 'debug_mode', str(app_config.debug_mode))
            self.config.set('Advanced', 'log_level', app_config.log_level)
            
        except Exception as e:
            self.logger.error(f"更新配置解析器失败: {e}")
            raise ConfigurationError(f"更新配置解析器失败: {e}")
    
    def get_config_value(self, section: str, key: str, default_value=None):
        """获取配置值"""
        try:
            if self.config.has_section(section) and self.config.has_option(section, key):
                return self.config.get(section, key)
            return default_value
        except Exception as e:
            self.logger.error(f"获取配置值失败: {e}")
            return default_value
    
    def set_config_value(self, section: str, key: str, value: str):
        """设置配置值"""
        try:
            if not self.config.has_section(section):
                self.config.add_section(section)
            self.config.set(section, key, str(value))
        except Exception as e:
            self.logger.error(f"设置配置值失败: {e}")
            raise ConfigurationError(f"设置配置值失败: {e}")
    
    def load_voice_config(self) -> VoiceConfig:
        """加载语音配置"""
        try:
            voice_config = VoiceConfig()
            
            if self.config.has_section('VoiceSettings'):
                voice_config.engine = self.get_config_value('VoiceSettings', 'engine', 'edge_tts')
                voice_config.voice_name = self.get_config_value('VoiceSettings', 'voice_name', 'zh-CN-XiaoxiaoNeural')
                voice_config.rate = float(self.get_config_value('VoiceSettings', 'rate', '1.0'))
                voice_config.pitch = float(self.get_config_value('VoiceSettings', 'pitch', '0.0'))
                voice_config.volume = float(self.get_config_value('VoiceSettings', 'volume', '1.0'))
                voice_config.language = self.get_config_value('VoiceSettings', 'language', 'zh-CN')
            else:
                # 创建默认语音配置
                self.save_voice_config(voice_config)
            
            return voice_config
            
        except Exception as e:
            self.logger.error(f"加载语音配置失败: {e}")
            return VoiceConfig()
    
    def save_voice_config(self, voice_config: VoiceConfig):
        """保存语音配置"""
        try:
            if not self.config.has_section('VoiceSettings'):
                self.config.add_section('VoiceSettings')
            
            self.config.set('VoiceSettings', 'engine', voice_config.engine)
            self.config.set('VoiceSettings', 'voice_name', voice_config.voice_name)
            self.config.set('VoiceSettings', 'rate', str(voice_config.rate))
            self.config.set('VoiceSettings', 'pitch', str(voice_config.pitch))
            self.config.set('VoiceSettings', 'volume', str(voice_config.volume))
            self.config.set('VoiceSettings', 'language', voice_config.language)
            
            # 保存到文件
            self.config_file.parent.mkdir(parents=True, exist_ok=True)
            with open(self.config_file, 'w', encoding='utf-8') as f:
                self.config.write(f)
            
            self.logger.info("语音配置保存成功")
            
        except Exception as e:
            self.logger.error(f"保存语音配置失败: {e}")
            raise ConfigurationError(f"保存语音配置失败: {e}")
    
    def load_output_config(self) -> OutputConfig:
        """加载输出配置"""
        try:
            output_config = OutputConfig()
            
            if self.config.has_section('OutputSettings'):
                output_config.output_dir = self.get_config_value('OutputSettings', 'output_dir', './output')
                output_config.format = self.get_config_value('OutputSettings', 'format', 'mp3')
                output_config.bitrate = int(self.get_config_value('OutputSettings', 'bitrate', '128'))
                output_config.sample_rate = int(self.get_config_value('OutputSettings', 'sample_rate', '44100'))
                output_config.channels = int(self.get_config_value('OutputSettings', 'channels', '2'))
                output_config.merge_files = self.get_config_value('OutputSettings', 'merge_files', 'False').lower() == 'true'
                output_config.merge_filename = self.get_config_value('OutputSettings', 'merge_filename', '完整音频')
                output_config.chapter_markers = self.get_config_value('OutputSettings', 'chapter_markers', 'True').lower() == 'true'
                output_config.chapter_interval = int(self.get_config_value('OutputSettings', 'chapter_interval', '2'))
                output_config.normalize = self.get_config_value('OutputSettings', 'normalize', 'True').lower() == 'true'
                output_config.noise_reduction = self.get_config_value('OutputSettings', 'noise_reduction', 'False').lower() == 'true'
                output_config.concurrent_workers = int(self.get_config_value('OutputSettings', 'concurrent_workers', '2'))
                output_config.cleanup_temp = self.get_config_value('OutputSettings', 'cleanup_temp', 'True').lower() == 'true'
            else:
                # 创建默认输出配置
                self.save_output_config(output_config)
            
            return output_config
            
        except Exception as e:
            self.logger.error(f"加载输出配置失败: {e}")
            return OutputConfig()
    
    def save_output_config(self, output_config: OutputConfig):
        """保存输出配置"""
        try:
            if not self.config.has_section('OutputSettings'):
                self.config.add_section('OutputSettings')
            
            self.config.set('OutputSettings', 'output_dir', output_config.output_dir)
            self.config.set('OutputSettings', 'format', output_config.format)
            self.config.set('OutputSettings', 'bitrate', str(output_config.bitrate))
            self.config.set('OutputSettings', 'sample_rate', str(output_config.sample_rate))
            self.config.set('OutputSettings', 'channels', str(output_config.channels))
            self.config.set('OutputSettings', 'merge_files', str(output_config.merge_files))
            self.config.set('OutputSettings', 'merge_filename', output_config.merge_filename)
            self.config.set('OutputSettings', 'chapter_markers', str(output_config.chapter_markers))
            self.config.set('OutputSettings', 'chapter_interval', str(output_config.chapter_interval))
            self.config.set('OutputSettings', 'normalize', str(output_config.normalize))
            self.config.set('OutputSettings', 'noise_reduction', str(output_config.noise_reduction))
            self.config.set('OutputSettings', 'concurrent_workers', str(output_config.concurrent_workers))
            self.config.set('OutputSettings', 'cleanup_temp', str(output_config.cleanup_temp))
            
            # 保存到文件
            self.config_file.parent.mkdir(parents=True, exist_ok=True)
            with open(self.config_file, 'w', encoding='utf-8') as f:
                self.config.write(f)
            
            self.logger.info("输出配置保存成功")
            
        except Exception as e:
            self.logger.error(f"保存输出配置失败: {e}")
            raise ConfigurationError(f"保存输出配置失败: {e}")
    
    def export_config(self, export_file: str):
        """导出配置"""
        try:
            import shutil
            shutil.copy2(self.config_file, export_file)
            self.logger.info(f"配置导出成功: {export_file}")
        except Exception as e:
            self.logger.error(f"配置导出失败: {e}")
            raise ConfigurationError(f"配置导出失败: {e}")
    
    def import_config(self, import_file: str):
        """导入配置"""
        try:
            import shutil
            shutil.copy2(import_file, self.config_file)
            # 重新加载配置
            self.config.read(self.config_file, encoding='utf-8')
            self.logger.info(f"配置导入成功: {import_file}")
        except Exception as e:
            self.logger.error(f"配置导入失败: {e}")
            raise ConfigurationError(f"配置导入失败: {e}")
    
    def reset_to_default(self):
        """重置为默认配置"""
        try:
            # 删除配置文件
            if self.config_file.exists():
                self.config_file.unlink()
            
            # 创建默认配置
            self.create_default_config()
            self.logger.info("配置已重置为默认值")
            
        except Exception as e:
            self.logger.error(f"重置配置失败: {e}")
            raise ConfigurationError(f"重置配置失败: {e}")


class ConfigurationError(Exception):
    """配置错误异常"""
    pass
