#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
TTS引擎基础抽象类模块

提供所有TTS引擎的通用接口和基础实现，包括：
- 抽象基类定义：统一TTS引擎接口规范
- 数据模型：语音信息、质量等级、引擎类型等
- 通用功能：文件命名、路径处理、错误处理等
- 生命周期管理：初始化、配置加载、资源清理等

设计模式：
- 模板方法模式：定义TTS引擎的标准流程
- 策略模式：支持多种TTS引擎实现
- 工厂模式：通过引擎类型创建具体实例

作者: TTS开发团队
版本: 1.0.0
创建时间: 2024
"""

import os
import tempfile
import time
import re
from abc import ABC, abstractmethod
from typing import List, Dict, Any, Optional, Union
from dataclasses import dataclass, field
from enum import Enum

from models.audio_model import VoiceConfig
from utils.log_manager import LogManager


class TTSEngineType(Enum):
    """
    TTS引擎类型枚举
    
    定义TTS引擎的运行模式，影响引擎的初始化和使用方式。
    """
    ONLINE = "online"      # 在线引擎：需要网络连接，如Edge TTS、EmotiVoice
    OFFLINE = "offline"    # 离线引擎：本地运行，如Piper TTS、pyttsx3
    HYBRID = "hybrid"      # 混合引擎：支持在线和离线两种模式


class TTSQuality(Enum):
    """
    TTS质量等级枚举
    
    定义语音合成的质量等级，影响音频的采样率、比特深度等参数。
    """
    LOW = "low"        # 低质量：快速合成，文件小
    MEDIUM = "medium"  # 中等质量：平衡质量和速度
    HIGH = "high"      # 高质量：较好的音质
    ULTRA = "ultra"    # 超高质量：最佳音质，文件较大


@dataclass
class TTSVoiceInfo:
    """
    TTS语音信息数据类
    
    存储单个语音的完整信息，包括基本属性、音频参数和自定义属性。
    支持不同TTS引擎的语音配置需求。
    
    Attributes:
        id (str): 语音唯一标识符
        name (str): 语音显示名称
        language (str): 语音语言代码（如'zh-CN', 'en-US'）
        gender (str): 语音性别（'male', 'female', 'unknown'）
        description (str): 语音描述信息
        engine (str): 所属引擎标识
        quality (TTSQuality): 语音质量等级
        sample_rate (int): 采样率（Hz）
        bit_depth (int): 比特深度（位）
        channels (int): 声道数
        custom_attributes (Dict[str, Any]): 自定义属性字典
    """
    id: str
    name: str
    language: str
    gender: str = "unknown"
    description: str = ""
    engine: str = ""
    quality: TTSQuality = TTSQuality.MEDIUM
    sample_rate: int = 22050
    bit_depth: int = 16
    channels: int = 1
    custom_attributes: Dict[str, Any] = field(default_factory=dict)


@dataclass
class TTSCommonParams:
    """
    TTS通用参数数据类
    
    定义所有TTS引擎都支持的通用参数，包括基础参数、音频质量参数、
    输出参数、性能参数和错误处理参数。子类可以扩展特定参数。
    
    Attributes:
        voice_name (str): 语音名称
        rate (float): 语速倍率（1.0为正常速度）
        volume (float): 音量倍率（1.0为正常音量）
        language (str): 语言代码
        output_format (str): 输出音频格式
        sample_rate (int): 音频采样率
        bit_depth (int): 音频比特深度
        channels (int): 音频声道数
        output_dir (str): 输出目录
        filename_template (str): 文件名模板
        enable_caching (bool): 是否启用缓存
        cache_duration (int): 缓存持续时间（秒）
        max_cache_size (int): 最大缓存条目数
        max_retries (int): 最大重试次数
        retry_delay (float): 重试延迟时间（秒）
        timeout (int): 超时时间（秒）
    """
    # 基础参数（所有引擎都支持）
    voice_name: str = ""
    rate: float = 1.0
    volume: float = 1.0
    language: str = "zh-CN"
    output_format: str = "wav"
    
    # 音频质量参数
    sample_rate: int = 22050
    bit_depth: int = 16
    channels: int = 1
    
    # 输出参数
    output_dir: str = ""
    filename_template: str = "{voice_name}_{timestamp}"
    
    # 性能参数
    enable_caching: bool = True
    cache_duration: int = 3600  # 秒
    max_cache_size: int = 100
    
    # 错误处理参数
    max_retries: int = 3
    retry_delay: float = 1.0
    timeout: int = 30


@dataclass
class TTSResult:
    """
    TTS合成结果数据类
    
    封装TTS合成的结果信息，包括成功状态、音频数据、输出路径等。
    提供统一的返回格式，便于上层调用者处理结果。
    
    Attributes:
        success (bool): 合成是否成功
        audio_data (Optional[bytes]): 音频数据（字节）
        output_path (Optional[str]): 输出文件路径
        duration (float): 音频时长（秒）
        sample_rate (int): 音频采样率
        bit_depth (int): 音频比特深度
        channels (int): 音频声道数
        format (str): 音频格式
        error_message (str): 错误信息（失败时）
        metadata (Dict[str, Any]): 元数据字典
    """
    success: bool
    audio_data: Optional[bytes] = None
    output_path: Optional[str] = None
    duration: float = 0.0
    sample_rate: int = 22050
    bit_depth: int = 16
    channels: int = 1
    format: str = 'wav'
    error_message: str = ""
    metadata: Dict[str, Any] = field(default_factory=dict)


class BaseTTSEngine(ABC):
    """
    TTS引擎基础抽象类
    
    定义所有TTS引擎必须实现的接口和通用功能。
    采用模板方法模式，提供标准化的引擎生命周期管理。
    
    子类必须实现以下抽象方法：
    - _load_engine(): 加载引擎特定资源
    - _load_voices(): 加载可用语音列表
    - _synthesize_audio(): 执行音频合成
    
    特性：
    - 统一接口：所有TTS引擎使用相同的接口
    - 生命周期管理：初始化、配置、清理
    - 错误处理：统一的异常处理机制
    - 日志记录：完整的操作日志
    - 参数管理：通用参数和引擎特定参数
    """
    
    def __init__(self, engine_id: str, engine_name: str, engine_type: TTSEngineType):
        """
        初始化TTS引擎
        
        Args:
            engine_id (str): 引擎唯一标识符
            engine_name (str): 引擎显示名称
            engine_type (TTSEngineType): 引擎类型（在线/离线/混合）
        """
        self.engine_id = engine_id
        self.engine_name = engine_name
        self.engine_type = engine_type
        self.logger = LogManager().get_logger(f"TTS_{engine_id}")
        
        # 引擎状态管理
        self._initialized = False    # 是否已初始化
        self._available = False      # 是否可用
        self._voices = {}           # 可用语音字典
        self._common_params = TTSCommonParams()  # 通用参数
        
        # 初始化引擎
        self._init_engine()
    
    @property
    def is_initialized(self) -> bool:
        """
        检查引擎是否已初始化
        
        Returns:
            bool: 已初始化返回True，否则返回False
        """
        return self._initialized
    
    @property
    def is_available(self) -> bool:
        """
        检查引擎是否可用
        
        Returns:
            bool: 可用返回True，否则返回False
        """
        return self._available
    
    @property
    def voices(self) -> Dict[str, TTSVoiceInfo]:
        """
        获取可用语音列表
        
        Returns:
            Dict[str, TTSVoiceInfo]: 语音ID到语音信息的映射字典
        """
        return self._voices.copy()
    
    @property
    def common_params(self) -> TTSCommonParams:
        """
        获取通用参数
        
        Returns:
            TTSCommonParams: 通用参数对象
        """
        return self._common_params
    
    def _init_engine(self):
        """初始化引擎（子类实现）"""
        try:
            self._load_engine()
            self._load_voices()
            self._initialized = True
            self._available = True
            self.logger.info(f"{self.engine_name} 引擎初始化成功")
        except Exception as e:
            self.logger.error(f"{self.engine_name} 引擎初始化失败: {e}")
            self._initialized = False
            self._available = False
            raise
    
    @abstractmethod
    def _load_engine(self):
        """加载引擎（子类必须实现）"""
        pass
    
    @abstractmethod
    def _load_voices(self):
        """加载语音列表（子类必须实现）"""
        pass
    
    @abstractmethod
    def _synthesize_audio(self, text: str, voice_config: VoiceConfig) -> bytes:
        """合成音频数据（子类必须实现）"""
        pass
    
    def synthesize(self, text: str, voice_config: VoiceConfig) -> TTSResult:
        """合成语音（通用接口）"""
        try:
            if not self._available:
                return TTSResult(
                    success=False,
                    error_message=f"{self.engine_name} 引擎不可用"
                )
            
            if not text.strip():
                return TTSResult(
                    success=True,
                    audio_data=b"",
                    duration=0.0
                )
            
            self.logger.info(f"开始 {self.engine_name} 合成，语音: {voice_config.voice_name}")
            
            # 合成音频数据
            start_time = time.time()
            audio_data = self._synthesize_audio(text, voice_config)
            duration = time.time() - start_time
            
            return TTSResult(
                success=True,
                audio_data=audio_data,
                duration=duration,
                sample_rate=self._common_params.sample_rate,
                bit_depth=self._common_params.bit_depth,
                channels=self._common_params.channels
            )
            
        except Exception as e:
            self.logger.error(f"{self.engine_name} 合成失败: {e}")
            return TTSResult(
                success=False,
                error_message=f"{self.engine_name} 合成失败: {e}"
            )
    
    def synthesize_to_file(self, text: str, voice_config: VoiceConfig, 
                          output_path: str = None, output_config=None, 
                          chapter_info=None) -> TTSResult:
        """合成语音到文件（通用接口）"""
        try:
            if not self._available:
                return TTSResult(
                    success=False,
                    error_message=f"{self.engine_name} 引擎不可用"
                )
            
            if not text.strip():
                return TTSResult(
                    success=True,
                    output_path="",
                    duration=0.0
                )
            
            # 生成输出文件路径
            if not output_path:
                output_path = self._generate_output_path(voice_config, output_config, text, chapter_info)
            
            # 确保输出目录存在
            os.makedirs(os.path.dirname(output_path), exist_ok=True)
            
            # 合成音频数据
            result = self.synthesize(text, voice_config)
            if not result.success:
                return result
            
            # 检查是否需要格式转换
            target_format = self._get_target_format(output_path, output_config)
            source_format = getattr(result, 'format', 'wav')
            
            if target_format != source_format:
                # 需要进行格式转换
                self.logger.info(f"检测到格式不匹配，进行转换: {source_format} -> {target_format}")
                converted_data = self._convert_audio_format(result.audio_data, source_format, target_format, output_config)
                if converted_data:
                    # 保存转换后的音频数据
                    with open(output_path, "wb") as f:
                        f.write(converted_data)
                    self.logger.info(f"{self.engine_name} 格式转换完成: {output_path}")
                else:
                    # 转换失败，保存原始数据并记录警告
                    with open(output_path, "wb") as f:
                        f.write(result.audio_data)
                    self.logger.warning(f"格式转换失败，保存原始{source_format}格式到{target_format}文件: {output_path}")
            else:
                # 格式匹配，直接保存
                with open(output_path, "wb") as f:
                    f.write(result.audio_data)
                self.logger.info(f"{self.engine_name} 合成完成: {output_path}")
            
            return TTSResult(
                success=True,
                output_path=output_path,
                duration=result.duration,
                sample_rate=result.sample_rate,
                bit_depth=result.bit_depth,
                channels=result.channels
            )
            
        except Exception as e:
            self.logger.error(f"{self.engine_name} 文件合成失败: {e}")
            return TTSResult(
                success=False,
                error_message=f"{self.engine_name} 文件合成失败: {e}"
            )
    
    def _get_target_format(self, output_path: str, output_config) -> str:
        """获取目标音频格式"""
        try:
            # 从文件扩展名获取格式
            file_ext = os.path.splitext(output_path)[1].lower()
            if file_ext.startswith('.'):
                file_ext = file_ext[1:]  # 移除点号
            
            # 如果扩展名有效，使用扩展名
            if file_ext in ['wav', 'mp3', 'ogg', 'm4a', 'aac', 'flac']:
                return file_ext
            
            # 否则从输出配置获取
            if output_config and hasattr(output_config, 'format'):
                return output_config.format.lower()
            
            # 默认返回wav
            return 'wav'
            
        except Exception as e:
            self.logger.error(f"获取目标格式失败: {e}")
            return 'wav'
    
    def _convert_audio_format(self, audio_data: bytes, source_format: str, 
                            target_format: str, output_config) -> bytes:
        """转换音频格式"""
        try:
            # 导入AudioService
            from services.audio_service import AudioService
            from models.audio_model import AudioModel
            
            # 创建AudioService实例
            audio_service = AudioService()
            
            # 创建AudioModel
            audio_model = AudioModel(
                audio_data=audio_data,
                voice_config=VoiceConfig(),  # 创建默认VoiceConfig
                format=source_format,
                sample_rate=getattr(output_config, 'sample_rate', 44100) if output_config else 44100,
                channels=getattr(output_config, 'channels', 2) if output_config else 2,
                bitrate=getattr(output_config, 'bitrate', 128) if output_config else 128
            )
            
            # 转换格式
            converted_audio = audio_service.convert_format(audio_model, target_format)
            
            self.logger.info(f"音频格式转换成功: {source_format} -> {target_format}")
            return converted_audio.audio_data
            
        except Exception as e:
            self.logger.error(f"音频格式转换失败: {e}")
            return None
    
    def _generate_output_path(self, voice_config: VoiceConfig, output_config, 
                            text: str, chapter_info=None) -> str:
        """生成输出文件路径（通用实现）"""
        try:
            # 获取输出目录
            output_dir = getattr(output_config, 'output_dir', tempfile.gettempdir())
            os.makedirs(output_dir, exist_ok=True)
            
            # 获取文件格式
            file_format = getattr(output_config, 'format', self._common_params.output_format)
            if not file_format.startswith('.'):
                file_format = f'.{file_format}'
            
            # 获取命名模式
            naming_mode = getattr(output_config, 'naming_mode', '章节序号 + 标题')
            custom_template = getattr(output_config, 'custom_template', '{chapter_num:02d}_{title}')
            name_length_limit = getattr(output_config, 'name_length_limit', 50)
            
            # 生成文件名
            filename = self._generate_filename(naming_mode, custom_template, 
                                            chapter_info, text, voice_config, name_length_limit)
            
            return os.path.join(output_dir, f"{filename}{file_format}")
            
        except Exception as e:
            self.logger.error(f"生成输出路径失败: {e}")
            return os.path.join(tempfile.gettempdir(), f"{self.engine_id}_{int(time.time())}.wav")
    
    def _generate_filename(self, naming_mode: str, custom_template: str, 
                          chapter_info, text: str, voice_config: VoiceConfig, 
                          name_length_limit: int) -> str:
        """生成文件名（通用实现）"""
        try:
            # 支持键值和中文显示文本的比较，确保向后兼容性
            if naming_mode in ["custom", "自定义"]:
                filename = self._apply_custom_template(custom_template, chapter_info, text)
            elif naming_mode in ["chapter_number_title", "章节序号 + 标题"]:
                filename = self._generate_chapter_title_name(chapter_info, text)
            elif naming_mode in ["sequence_title", "顺序号 + 标题"]:
                filename = self._generate_number_title_name(chapter_info, text)
            elif naming_mode in ["title_only", "仅标题"]:
                filename = self._generate_title_only_name(chapter_info, text)
            elif naming_mode in ["sequence_only", "仅顺序号"]:
                filename = self._generate_number_only_name(chapter_info, text)
            elif naming_mode in ["original_filename", "原始文件名"]:
                filename = self._generate_original_filename(chapter_info, text)
            else:
                # 默认使用时间戳
                filename = f"{voice_config.voice_name}_{int(time.time())}"
            
            # 限制文件名长度
            if len(filename) > name_length_limit:
                filename = filename[:name_length_limit]
            
            # 清理文件名中的非法字符
            filename = re.sub(r'[<>:"/\\|?*]', '_', filename)
            
            return filename
            
        except Exception as e:
            self.logger.error(f"生成文件名失败: {e}")
            return f"{self.engine_id}_{int(time.time())}"
    
    def _apply_custom_template(self, template: str, chapter_info, text: str) -> str:
        """应用自定义模板"""
        try:
            if not chapter_info:
                return f"custom_{int(time.time())}"
            
            chapter_num = getattr(chapter_info, 'number', 1)
            title = getattr(chapter_info, 'title', 'untitled')
            
            return template.format(
                chapter_num=chapter_num,
                title=title,
                text=text[:20] if text else 'untitled',
                voice_name=getattr(chapter_info, 'voice_name', 'unknown'),
                timestamp=int(time.time())
            )
        except Exception as e:
            self.logger.error(f"应用自定义模板失败: {e}")
            return f"custom_{int(time.time())}"
    
    def _generate_chapter_title_name(self, chapter_info, text: str) -> str:
        """生成章节标题格式的文件名"""
        if not chapter_info:
            return f"chapter_{int(time.time())}"
        
        chapter_num = getattr(chapter_info, 'number', 1)
        title = getattr(chapter_info, 'title', 'untitled')
        
        return f"{chapter_num:02d}_{title}"
    
    def _generate_number_only_name(self, chapter_info, text: str) -> str:
        """生成仅序号格式的文件名"""
        if not chapter_info:
            return f"audio_{int(time.time())}"
        
        chapter_num = getattr(chapter_info, 'number', 1)
        return f"{chapter_num:02d}"
    
    def _generate_number_title_name(self, chapter_info, text: str) -> str:
        """生成序号+标题格式的文件名"""
        if not chapter_info:
            return f"audio_{int(time.time())}"
        
        chapter_num = getattr(chapter_info, 'number', 1)
        title = getattr(chapter_info, 'title', 'untitled')
        
        return f"{chapter_num:02d}_{title}"
    
    def _generate_title_only_name(self, chapter_info, text: str) -> str:
        """生成仅标题格式的文件名"""
        if not chapter_info:
            return f"audio_{int(time.time())}"
        
        title = getattr(chapter_info, 'title', 'untitled')
        return title
    
    def _generate_original_filename(self, chapter_info, text: str) -> str:
        """生成原始文件名格式的文件名"""
        if not chapter_info:
            return f"original_{int(time.time())}"
        
        # 尝试从章节信息中获取原始文件名
        original_filename = getattr(chapter_info, 'original_filename', None)
        if original_filename:
            # 移除文件扩展名
            name_without_ext = os.path.splitext(original_filename)[0]
            return f"{name_without_ext}_{int(time.time())}"
        
        # 如果没有原始文件名，使用标题
        title = getattr(chapter_info, 'title', 'untitled')
        return f"{title}_{int(time.time())}"
    
    def get_available_voices(self) -> List[TTSVoiceInfo]:
        """获取可用语音列表"""
        return list(self._voices.values())
    
    def get_voice_info(self, voice_id: str) -> Optional[TTSVoiceInfo]:
        """获取指定语音信息"""
        return self._voices.get(voice_id)
    
    def get_engine_info(self) -> Dict[str, Any]:
        """获取引擎信息"""
        return {
            'engine_id': self.engine_id,
            'engine_name': self.engine_name,
            'engine_type': self.engine_type.value,
            'is_available': self._available,
            'is_initialized': self._initialized,
            'voice_count': len(self._voices),
            'supported_formats': [self._common_params.output_format],
            'supported_languages': list(set(voice.language for voice in self._voices.values())),
            'common_params': self._common_params.__dict__
        }
    
    def update_common_params(self, params: TTSCommonParams):
        """更新通用参数"""
        self._common_params = params
        self.logger.info(f"更新 {self.engine_name} 通用参数")
    
    def validate_voice_config(self, voice_config: VoiceConfig) -> bool:
        """验证语音配置"""
        try:
            # 检查语音是否存在
            if voice_config.voice_name and voice_config.voice_name not in self._voices:
                self.logger.warning(f"语音 {voice_config.voice_name} 不存在，将使用默认语音")
                return False
            
            # 检查参数范围
            if not (0.1 <= voice_config.rate <= 3.0):
                self.logger.warning(f"语速 {voice_config.rate} 超出范围 [0.1, 3.0]")
                return False
            
            if not (0.0 <= voice_config.volume <= 2.0):
                self.logger.warning(f"音量 {voice_config.volume} 超出范围 [0.0, 2.0]")
                return False
            
            return True
            
        except Exception as e:
            self.logger.error(f"验证语音配置失败: {e}")
            return False
