"""
JSON配置服务
"""

import os
import json
from pathlib import Path
from typing import Optional, Dict, Any

from models.config_model import AppConfig
from models.audio_model import VoiceConfig, OutputConfig
from utils.log_manager import LogManager


class JsonConfigService:
    """JSON配置管理服务"""
    
    def __init__(self, config_file: str = 'config.json'):
        self.logger = LogManager().get_logger("JsonConfigService")
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
                json.dump(self.config_data, f, ensure_ascii=False, indent=2)
            
            self.logger.info(f"配置导出成功: {export_path}")
            
        except Exception as e:
            self.logger.error(f"配置导出失败: {e}")
            raise ConfigurationError(f"配置导出失败: {e}")
    
    def import_config(self, import_path: str):
        """导入配置"""
        try:
            import_path = Path(import_path)
            
            with open(import_path, 'r', encoding='utf-8') as f:
                imported_data = json.load(f)
            
            # 合并配置
            self.config_data.update(imported_data)
            
            # 保存合并后的配置
            self.save_config(self._parse_config())
            
            self.logger.info(f"配置导入成功: {import_path}")
            
        except Exception as e:
            self.logger.error(f"配置导入失败: {e}")
            raise ConfigurationError(f"配置导入失败: {e}")
    
    def load_voice_config(self) -> VoiceConfig:
        """加载语音配置"""
        try:
            # 确保配置文件已加载
            if not self.config_data:
                self.load_config()
            
            voice_data = self.config_data.get('voice_settings', {})
            
            # 从config.json中只读取基础参数
            engine = voice_data.get('engine', 'edge_tts')
            rate = voice_data.get('rate', 1.0)
            pitch = voice_data.get('pitch', 0.0)
            volume = voice_data.get('volume', 1.0)
            language = voice_data.get('language', 'zh-CN')
            
            # 创建基本的VoiceConfig对象
            voice_config = VoiceConfig(
                engine=engine,
                rate=rate,
                pitch=pitch,
                volume=volume,
                language=language
            )
            
            # 尝试从configs文件夹加载引擎特定的配置文件
            engine_config_path = Path(f"configs/{engine}.json")
            if engine_config_path.exists():
                with open(engine_config_path, 'r', encoding='utf-8') as f:
                    engine_config_data = json.load(f)
                    
                # 合并引擎特定的参数到voice_config
                voice_config.voice_name = engine_config_data.get('voice_name', voice_config.voice_name)
                voice_config.output_format = engine_config_data.get('output_format', 'wav')
                voice_config.extra_params = engine_config_data.get('extra_params', {})
                
                # 如果有额外的自定义字段，也添加进去
                for key, value in engine_config_data.items():
                    if key not in ['engine', 'rate', 'pitch', 'volume', 'language', 'voice_name', 'output_format', 'extra_params']:
                        setattr(voice_config, key, value)
                
                self.logger.info(f"成功加载引擎特定配置: {engine_config_path}")
            else:
                # 如果没有找到引擎配置文件，使用默认值
                self.logger.warning(f"未找到引擎配置文件: {engine_config_path}")
                voice_config.voice_name = 'default'
                voice_config.output_format = 'wav'
                voice_config.extra_params = {}
            
            return voice_config
            
        except Exception as e:
            self.logger.error(f"加载语音配置失败: {e}")
            return VoiceConfig()
    
    def save_voice_config(self, voice_config: VoiceConfig):
        """保存语音配置"""
        try:
            if 'voice_settings' not in self.config_data:
                self.config_data['voice_settings'] = {}
            
            # 只保存基础参数到config.json
            self.config_data['voice_settings'].update({
                'engine': voice_config.engine,
                'rate': voice_config.rate,
                'pitch': voice_config.pitch,
                'volume': voice_config.volume,
                'language': voice_config.language
            })
            
            # 保存到文件
            self.config_file.parent.mkdir(parents=True, exist_ok=True)
            with open(self.config_file, 'w', encoding='utf-8') as f:
                json.dump(self.config_data, f, ensure_ascii=False, indent=2)
            
            self.logger.info("语音配置保存成功")
            
        except Exception as e:
            self.logger.error(f"保存语音配置失败: {e}")
            raise ConfigurationError(f"保存语音配置失败: {e}")
    
    def load_output_config(self) -> OutputConfig:
        """加载输出配置"""
        try:
            # 确保配置文件已加载
            if not self.config_data:
                self.load_config()
            
            output_data = self.config_data.get('output_settings', {})
            
            output_config = OutputConfig(
                output_dir=output_data.get('output_dir', './output'),
                format=output_data.get('format', 'mp3'),
                bitrate=output_data.get('bitrate', 128),
                sample_rate=output_data.get('sample_rate', 44100),
                channels=output_data.get('channels', 2),
                merge_files=output_data.get('merge_files', False),
                merge_filename=output_data.get('merge_filename', '完整音频'),
                chapter_markers=output_data.get('chapter_markers', True),
                chapter_interval=output_data.get('chapter_interval', 2),
                normalize=output_data.get('normalize', True),
                noise_reduction=output_data.get('noise_reduction', False),
                concurrent_workers=output_data.get('concurrent_workers', 2),
                cleanup_temp=output_data.get('cleanup_temp', True),
                # 文件命名设置
                naming_mode=output_data.get('naming_mode', '章节序号 + 标题'),
                custom_template=output_data.get('custom_template', '{chapter_num:02d}_{title}'),
                name_length_limit=output_data.get('name_length_limit', 50),
                # 字幕设置
                generate_subtitle=output_data.get('generate_subtitle', False),
                subtitle_format=output_data.get('subtitle_format', 'lrc'),
                subtitle_encoding=output_data.get('subtitle_encoding', 'utf-8'),
                subtitle_offset=output_data.get('subtitle_offset', 0.0),
                subtitle_style=output_data.get('subtitle_style', {})
            )
            
            return output_config
            
        except Exception as e:
            self.logger.error(f"加载输出配置失败: {e}")
            return OutputConfig()
    
    def save_output_config(self, output_config: OutputConfig):
        """保存输出配置"""
        try:
            if 'output_settings' not in self.config_data:
                self.config_data['output_settings'] = {}
            
            self.config_data['output_settings'].update({
                'output_dir': output_config.output_dir,
                'format': output_config.format,
                'bitrate': output_config.bitrate,
                'sample_rate': output_config.sample_rate,
                'channels': output_config.channels,
                'merge_files': output_config.merge_files,
                'merge_filename': output_config.merge_filename,
                'chapter_markers': output_config.chapter_markers,
                'chapter_interval': output_config.chapter_interval,
                'normalize': output_config.normalize,
                'noise_reduction': output_config.noise_reduction,
                'concurrent_workers': output_config.concurrent_workers,
                'cleanup_temp': output_config.cleanup_temp,
                # 文件命名设置
                'naming_mode': output_config.naming_mode,
                'custom_template': output_config.custom_template,
                'name_length_limit': output_config.name_length_limit,
                # 字幕设置
                'generate_subtitle': output_config.generate_subtitle,
                'subtitle_format': output_config.subtitle_format,
                'subtitle_encoding': output_config.subtitle_encoding,
                'subtitle_offset': output_config.subtitle_offset,
                'subtitle_style': output_config.subtitle_style
            })
            
            # 保存到文件
            self.config_file.parent.mkdir(parents=True, exist_ok=True)
            with open(self.config_file, 'w', encoding='utf-8') as f:
                json.dump(self.config_data, f, ensure_ascii=False, indent=2)
            
            self.logger.info("输出配置保存成功")
            
        except Exception as e:
            self.logger.error(f"保存输出配置失败: {e}")
            raise ConfigurationError(f"保存输出配置失败: {e}")
    
    def _create_default_config(self) -> AppConfig:
        """创建默认配置"""
        return AppConfig()
    
    def _parse_config(self) -> AppConfig:
        """解析配置"""
        try:
            config = AppConfig()
            
            # 基本设置
            general = self.config_data.get('general', {})
            config.window_width = general.get('window_width', 1200)
            config.window_height = general.get('window_height', 800)
            config.window_x = general.get('window_x', 100)
            config.window_y = general.get('window_y', 100)
            config.theme = general.get('theme', 'light')
            config.language = general.get('language', 'zh-CN')
            
            # 文件设置
            files = self.config_data.get('files', {})
            config.default_input_dir = files.get('default_input_dir', './input')
            config.default_output_dir = files.get('default_output_dir', './output')
            config.auto_save = files.get('auto_save', True)
            config.auto_save_interval = files.get('auto_save_interval', 300)
            
            # 缓存设置
            cache = self.config_data.get('cache', {})
            config.cache_dir = cache.get('cache_dir', 'cache')
            config.enable_cache = cache.get('enable_cache', True)
            config.cache_max_size_mb = cache.get('cache_max_size_mb', 500)
            config.cache_auto_clean = cache.get('cache_auto_clean', True)
            
            # TTS设置
            tts = self.config_data.get('tts', {})
            config.default_tts_engine = tts.get('default_engine', 'piper_tts')
            config.default_voice = tts.get('default_voice', 'zh_CN-huayan-medium')
            config.default_rate = tts.get('default_rate', 1.0)
            config.default_pitch = tts.get('default_pitch', 0.0)
            config.default_volume = tts.get('default_volume', 1.0)
            
            # 高级设置
            advanced = self.config_data.get('advanced', {})
            config.max_concurrent_tasks = advanced.get('max_concurrent_tasks', 2)
            config.memory_limit_mb = advanced.get('memory_limit_mb', 1024)
            config.enable_hardware_acceleration = advanced.get('enable_hardware_acceleration', True)
            config.debug_mode = advanced.get('debug_mode', False)
            config.log_level = advanced.get('log_level', 'INFO')
            
            return config
            
        except Exception as e:
            self.logger.error(f"解析配置失败: {e}")
            return self._default_config
    
    def _update_config_data(self, app_config: AppConfig):
        """更新配置数据"""
        try:
            # 基本设置 - 增量更新，保留其他字段
            if 'general' not in self.config_data:
                self.config_data['general'] = {}
            
            self.config_data['general'].update({
                'window_width': app_config.window_width,
                'window_height': app_config.window_height,
                'window_x': app_config.window_x,
                'window_y': app_config.window_y,
                'theme': app_config.theme,
                'language': app_config.language
            })
            
            # 文件设置 - 增量更新，保留其他字段
            if 'files' not in self.config_data:
                self.config_data['files'] = {}
            
            self.config_data['files'].update({
                'default_input_dir': app_config.default_input_dir,
                'default_output_dir': app_config.default_output_dir,
                'auto_save': app_config.auto_save,
                'auto_save_interval': app_config.auto_save_interval
            })
            
            # TTS设置 - 增量更新，保留其他字段
            if 'tts' not in self.config_data:
                self.config_data['tts'] = {}
            
            self.config_data['tts'].update({
                'default_engine': app_config.default_tts_engine,
                'default_voice': app_config.default_voice,
                'default_rate': app_config.default_rate,
                'default_pitch': app_config.default_pitch,
                'default_volume': app_config.default_volume
            })
            
            # 高级设置 - 增量更新，保留其他字段
            if 'advanced' not in self.config_data:
                self.config_data['advanced'] = {}
            
            self.config_data['advanced'].update({
                'max_concurrent_tasks': app_config.max_concurrent_tasks,
                'memory_limit_mb': app_config.memory_limit_mb,
                'enable_hardware_acceleration': app_config.enable_hardware_acceleration,
                'debug_mode': app_config.debug_mode,
                'log_level': app_config.log_level
            })
            
        except Exception as e:
            self.logger.error(f"更新配置数据失败: {e}")
            raise ConfigurationError(f"更新配置数据失败: {e}")


class ConfigurationError(Exception):
    """配置错误异常"""
    pass
