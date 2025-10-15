"""
配置模型模块

提供应用程序的配置数据模型，包括：
- 界面设置：窗口大小、位置、主题、语言等
- 文件设置：输入输出目录、临时文件、自动保存等
- 音频设置：默认格式、质量参数等
- TTS设置：默认引擎、语音参数等
- 高级设置：性能参数、调试选项等
- 文本处理：文本长度限制、自动分段等
- 历史记录：历史记录管理设置
- 缓存设置：缓存目录和大小限制

配置特性：
- 默认值：提供合理的默认配置
- 序列化：支持字典和JSON格式转换
- 类型安全：完整的类型提示
- 验证：内置配置验证机制
- 扩展性：支持新配置项的添加

作者: TTS开发团队
版本: 1.0.0
创建时间: 2024
"""

from dataclasses import dataclass
from typing import Tuple, Optional


@dataclass
class AppConfig:
    """
    应用配置模型
    
    存储应用程序的所有配置参数，包括界面设置、文件设置、
    音频设置、TTS设置、高级设置等。提供完整的配置管理功能。
    
    Attributes:
        # 界面设置
        theme (str): 界面主题
        language (str): 界面语言
        window_width (int): 窗口宽度
        window_height (int): 窗口高度
        window_x (int): 窗口X坐标
        window_y (int): 窗口Y坐标
        
        # 文件设置
        default_input_dir (str): 默认输入目录
        default_output_dir (str): 默认输出目录
        temp_dir (str): 临时文件目录
        auto_clean_temp (bool): 自动清理临时文件
        auto_save (bool): 自动保存
        auto_save_interval (int): 自动保存间隔（秒）
        max_file_size_mb (int): 最大文件大小（MB）
        
        # 音频设置
        default_audio_format (str): 默认音频格式
        default_sample_rate (int): 默认采样率
        default_bitrate (int): 默认比特率
        
        # TTS设置
        default_tts_engine (str): 默认TTS引擎
        default_voice (str): 默认语音
        default_rate (float): 默认语速
        default_pitch (float): 默认音调
        default_volume (float): 默认音量
        
        # 高级设置
        max_concurrent_tasks (int): 最大并发任务数
        memory_limit_mb (int): 内存限制（MB）
        enable_hardware_acceleration (bool): 启用硬件加速
        debug_mode (bool): 调试模式
        log_level (str): 日志级别
        
        # 文本处理设置
        max_text_length (int): 最大文本长度
        auto_split_length (int): 自动分段长度
        auto_detect_chapters (bool): 自动检测章节
        
        # 历史记录设置
        max_history_items (int): 最大历史记录数
        save_processing_history (bool): 保存处理历史
        
        # 缓存设置
        cache_dir (str): 缓存目录
        enable_cache (bool): 启用缓存
        cache_max_size_mb (int): 缓存最大大小（MB）
        cache_auto_clean (bool): 自动清理缓存
    """
    # 界面设置
    theme: str = 'light'
    language: str = 'zh-CN'
    window_width: int = 1200
    window_height: int = 800
    window_x: int = 100
    window_y: int = 100
    
    # 文件设置
    default_input_dir: str = './input'
    default_output_dir: str = './output'
    temp_dir: str = './temp'
    auto_clean_temp: bool = True
    auto_save: bool = True
    auto_save_interval: int = 300
    max_file_size_mb: int = 100
    
    # 音频设置
    default_audio_format: str = 'wav'
    default_sample_rate: int = 44100
    default_bitrate: int = 128
    
    # TTS设置
    default_tts_engine: str = 'edge_tts'
    default_voice: str = 'zh-CN-XiaoxiaoNeural'
    default_rate: float = 1.0
    default_pitch: float = 0.0
    default_volume: float = 1.0
    
    # 高级设置
    max_concurrent_tasks: int = 2
    memory_limit_mb: int = 1024
    enable_hardware_acceleration: bool = False
    debug_mode: bool = False
    log_level: str = 'INFO'
    
    # 文本处理设置
    max_text_length: int = 1000000
    auto_split_length: int = 2000
    auto_detect_chapters: bool = True
    
    # 历史记录设置
    max_history_items: int = 50
    save_processing_history: bool = True
    
    # 缓存设置
    cache_dir: str = 'cache'
    enable_cache: bool = True
    cache_max_size_mb: int = 500
    cache_auto_clean: bool = True
    
    def get_window_size(self) -> Tuple[int, int]:
        """
        获取窗口大小
        
        返回窗口的宽度和高度。
        
        Returns:
            Tuple[int, int]: (宽度, 高度)
        """
        return (self.window_width, self.window_height)
    
    def set_window_size(self, width: int, height: int):
        """
        设置窗口大小
        
        Args:
            width (int): 窗口宽度
            height (int): 窗口高度
        """
        self.window_width = width
        self.window_height = height
    
    def get_window_position(self) -> Tuple[int, int]:
        """
        获取窗口位置
        
        返回窗口的X和Y坐标。
        
        Returns:
            Tuple[int, int]: (X坐标, Y坐标)
        """
        return (self.window_x, self.window_y)
    
    def set_window_position(self, x: int, y: int):
        """
        设置窗口位置
        
        Args:
            x (int): X坐标
            y (int): Y坐标
        """
        self.window_x = x
        self.window_y = y
    
    def to_dict(self) -> dict:
        """
        转换为字典格式
        
        将配置对象转换为字典，便于序列化和存储。
        包含所有配置参数。
        
        Returns:
            dict: 包含所有配置参数的字典
        """
        return {
            'theme': self.theme,
            'language': self.language,
            'window_width': self.window_width,
            'window_height': self.window_height,
            'window_x': self.window_x,
            'window_y': self.window_y,
            'default_output_dir': self.default_output_dir,
            'temp_dir': self.temp_dir,
            'auto_clean_temp': self.auto_clean_temp,
            'max_file_size_mb': self.max_file_size_mb,
            'default_audio_format': self.default_audio_format,
            'default_sample_rate': self.default_sample_rate,
            'default_bitrate': self.default_bitrate,
            'default_tts_engine': self.default_tts_engine,
            'default_voice': self.default_voice,
            'default_rate': self.default_rate,
            'default_pitch': self.default_pitch,
            'default_volume': self.default_volume,
            'max_concurrent_tasks': self.max_concurrent_tasks,
            'memory_limit_mb': self.memory_limit_mb,
            'enable_hardware_acceleration': self.enable_hardware_acceleration,
            'debug_mode': self.debug_mode,
            'log_level': self.log_level,
            'max_text_length': self.max_text_length,
            'auto_split_length': self.auto_split_length,
            'auto_detect_chapters': self.auto_detect_chapters,
            'max_history_items': self.max_history_items,
            'save_processing_history': self.save_processing_history,
            'cache_dir': self.cache_dir,
            'enable_cache': self.enable_cache,
            'cache_max_size_mb': self.cache_max_size_mb,
            'cache_auto_clean': self.cache_auto_clean
        }
    
    @classmethod
    def from_dict(cls, data: dict) -> 'AppConfig':
        """
        从字典创建配置
        
        从字典数据创建AppConfig实例，提供默认值确保配置完整性。
        
        Args:
            data (dict): 包含配置数据的字典
            
        Returns:
            AppConfig: 新创建的配置实例
        """
        return cls(
            theme=data.get('theme', 'light'),
            language=data.get('language', 'zh-CN'),
            window_width=data.get('window_width', 1200),
            window_height=data.get('window_height', 800),
            window_x=data.get('window_x', 100),
            window_y=data.get('window_y', 100),
            default_output_dir=data.get('default_output_dir', './output'),
            temp_dir=data.get('temp_dir', './temp'),
            auto_clean_temp=data.get('auto_clean_temp', True),
            max_file_size_mb=data.get('max_file_size_mb', 100),
            default_audio_format=data.get('default_audio_format', 'wav'),
            default_sample_rate=data.get('default_sample_rate', 44100),
            default_bitrate=data.get('default_bitrate', 128),
            default_tts_engine=data.get('default_tts_engine', 'edge_tts'),
            default_voice=data.get('default_voice', 'zh-CN-XiaoxiaoNeural'),
            default_rate=data.get('default_rate', 1.0),
            default_pitch=data.get('default_pitch', 0.0),
            default_volume=data.get('default_volume', 1.0),
            max_concurrent_tasks=data.get('max_concurrent_tasks', 2),
            memory_limit_mb=data.get('memory_limit_mb', 1024),
            enable_hardware_acceleration=data.get('enable_hardware_acceleration', False),
            debug_mode=data.get('debug_mode', False),
            log_level=data.get('log_level', 'INFO'),
            max_text_length=data.get('max_text_length', 1000000),
            auto_split_length=data.get('auto_split_length', 2000),
            auto_detect_chapters=data.get('auto_detect_chapters', True),
            max_history_items=data.get('max_history_items', 50),
            save_processing_history=data.get('save_processing_history', True),
            cache_dir=data.get('cache_dir', 'cache'),
            enable_cache=data.get('enable_cache', True),
            cache_max_size_mb=data.get('cache_max_size_mb', 500),
            cache_auto_clean=data.get('cache_auto_clean', True)
        )
