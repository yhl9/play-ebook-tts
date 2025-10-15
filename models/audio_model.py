"""
音频模型模块

提供TTS应用程序的音频相关数据模型，包括：
- 语音配置：TTS引擎参数、语音设置、音频格式等
- 输出配置：音频输出设置、文件命名、质量参数等
- 音频模型：音频数据、元信息、处理结果等

数据模型特性：
- 配置验证：内置参数验证和错误检查
- 序列化支持：支持字典和JSON格式的转换
- 默认值管理：提供合理的默认配置
- 引擎适配：支持不同TTS引擎的参数映射
- 安全获取：提供安全的参数获取方法

支持的TTS引擎：
- Edge TTS：微软在线TTS服务
- Piper TTS：本地高质量TTS引擎
- pyttsx3：跨平台系统TTS
- EmotiVoice：情感化TTS服务
- IndexTTS：语音克隆服务

作者: TTS开发团队
版本: 1.0.0
创建时间: 2024
"""

from dataclasses import dataclass, field
from typing import Optional, Dict, Any, List
from pydub import AudioSegment


@dataclass
class VoiceConfig:
    """
    语音配置模型
    
    存储TTS语音合成的所有配置参数，包括引擎设置、语音参数、
    音频格式等。支持多种TTS引擎的参数映射和验证。
    
    Attributes:
        engine (str): TTS引擎标识符
        voice_name (str): 语音名称或ID
        rate (float): 语速倍率（1.0为正常速度）
        pitch (float): 音调偏移（-50到+50）
        volume (float): 音量倍率（0.0到2.0）
        language (str): 语言代码（如'zh-CN', 'en-US'）
        output_format (str): 输出音频格式
        emotion (str): 情感参数（EmotiVoice专用）
        extra_params (Dict[str, Any]): 引擎特定参数
        _is_validated (bool): 内部验证状态
        _validation_errors (List[str]): 验证错误列表
    """
    engine: str = 'piper_tts'
    voice_name: str = 'default'  # 使用通用默认值，避免硬编码特定引擎的语音ID
    rate: float = 1.0
    pitch: float = 0.0
    volume: float = 1.0
    language: str = 'zh-CN'
    output_format: str = 'wav'
    emotion: str = '自然'  # EmotiVoice情感参数
    
    extra_params: Dict[str, Any] = field(default_factory=dict)
    _is_validated: bool = field(default=False, init=False)  # 内部验证状态
    _validation_errors: List[str] = field(default_factory=list, init=False)  # 验证错误
    
    def to_dict(self) -> dict:
        """
        转换为字典格式
        
        将语音配置对象转换为字典，便于序列化和存储。
        包含所有基础参数和额外参数。
        
        Returns:
            dict: 包含所有配置参数的字典
        """
        result = {
            'engine': self.engine,
            'voice_name': self.voice_name,
            'rate': self.rate,
            'pitch': self.pitch,
            'volume': self.volume,
            'language': self.language,
            'output_format': self.output_format,
            'emotion': self.emotion
        }
        # 添加额外参数
        result.update(self.extra_params)
        return result
    
    @classmethod
    def from_dict(cls, data: dict) -> 'VoiceConfig':
        """
        从字典创建语音配置
        
        从字典数据创建VoiceConfig实例，支持基础参数和额外参数。
        提供默认值确保配置的完整性。
        
        Args:
            data (dict): 包含配置数据的字典
            
        Returns:
            VoiceConfig: 新创建的语音配置实例
        """
        # 基础参数
        basic_params = {
            'engine': data.get('engine', 'edge_tts'),
            'voice_name': data.get('voice_name', 'zh-CN-XiaoxiaoNeural'),
            'rate': data.get('rate', 1.0),
            'pitch': data.get('pitch', 0.0),
            'volume': data.get('volume', 1.0),
            'language': data.get('language', 'zh-CN'),
            'output_format': data.get('output_format', 'wav'),
            'emotion': data.get('emotion', '自然')
        }
        
        # 额外参数
        extra_params = {k: v for k, v in data.items() if k not in basic_params}
        
        return cls(**basic_params, extra_params=extra_params)
    
    def validate(self) -> bool:
        """
        验证配置的有效性
        
        检查所有配置参数是否符合要求，包括类型检查、范围检查等。
        验证结果存储在内部状态中，可通过其他方法获取。
        
        Returns:
            bool: 配置有效返回True，否则返回False
        """
        self._validation_errors = []
        
        # 验证引擎
        if not self.engine or not isinstance(self.engine, str):
            self._validation_errors.append("引擎必须是有效的字符串")
        
        # 验证语音名称
        if not self.voice_name or not isinstance(self.voice_name, str):
            self._validation_errors.append("语音名称必须是有效的字符串")
        
        # 验证数值范围
        if not isinstance(self.rate, (int, float)) or self.rate <= 0:
            self._validation_errors.append("语速必须是正数")
        
        if not isinstance(self.volume, (int, float)) or self.volume < 0:
            self._validation_errors.append("音量必须是非负数")
        
        if not isinstance(self.pitch, (int, float)):
            self._validation_errors.append("音调必须是数字")
        
        # 验证语言
        if not self.language or not isinstance(self.language, str):
            self._validation_errors.append("语言必须是有效的字符串")
        
        # 验证输出格式
        valid_formats = ['wav', 'mp3', 'ogg', 'm4a']
        if self.output_format not in valid_formats:
            self._validation_errors.append(f"输出格式必须是以下之一: {valid_formats}")
        
        self._is_validated = True
        return len(self._validation_errors) == 0
    
    def get_validation_errors(self) -> List[str]:
        """
        获取验证错误列表
        
        返回配置验证过程中发现的所有错误信息。
        如果尚未验证，会自动执行验证。
        
        Returns:
            List[str]: 验证错误信息列表
        """
        if not self._is_validated:
            self.validate()
        return self._validation_errors.copy()
    
    def is_valid(self) -> bool:
        """
        检查配置是否有效
        
        快速检查配置是否通过验证，不返回具体错误信息。
        如果尚未验证，会自动执行验证。
        
        Returns:
            bool: 配置有效返回True，否则返回False
        """
        if not self._is_validated:
            self.validate()
        return len(self._validation_errors) == 0
    
    def safe_get_voice_name(self, available_voices: Optional[List[Dict]] = None) -> str:
        """
        安全获取语音名称
        
        从可用语音列表中选择合适的语音名称，如果当前配置的语音不存在，
        则返回第一个可用语音或默认值。
        
        Args:
            available_voices (Optional[List[Dict]]): 可用语音列表
            
        Returns:
            str: 安全的语音名称
        """
        if not available_voices:
            return self.voice_name
        
        # 检查当前语音是否存在
        for voice in available_voices:
            if (voice.get('id') == self.voice_name or 
                voice.get('name') == self.voice_name):
                return self.voice_name
        
        # 如果不存在，返回第一个可用语音
        if available_voices:
            first_voice = available_voices[0]
            return first_voice.get('id', first_voice.get('name', 'default'))
        
        return 'default'
    
    def apply_engine_defaults(self, engine: str):
        """
        应用引擎特定的默认值
        
        根据指定的TTS引擎应用相应的默认配置参数。
        用于确保配置与特定引擎的兼容性。
        
        Args:
            engine (str): TTS引擎标识符
        """
        from services.robust_config_service import robust_config_service
        
        template = robust_config_service.get_engine_template(engine)
        if template:
            self.engine = engine
            if not self.voice_name or self.voice_name == 'default':
                self.voice_name = template.default_voice_id
            
            # 应用其他默认值
            for param, default_value in template.optional_params.items():
                if not hasattr(self, param) or getattr(self, param) is None:
                    setattr(self, param, default_value)
    
    def clone(self) -> 'VoiceConfig':
        """
        克隆配置
        
        创建当前配置的深拷贝，包括所有参数和额外参数。
        用于配置备份或创建变体配置。
        
        Returns:
            VoiceConfig: 新的配置实例
        """
        return VoiceConfig(
            engine=self.engine,
            voice_name=self.voice_name,
            rate=self.rate,
            pitch=self.pitch,
            volume=self.volume,
            language=self.language,
            output_format=self.output_format,
            emotion=self.emotion,
            extra_params=self.extra_params.copy()
        )


@dataclass
class OutputConfig:
    """
    输出配置模型
    
    定义音频输出的所有配置参数，包括文件格式、质量设置、
    文件命名、合并选项等。提供完整的音频输出控制。
    
    Attributes:
        output_dir (str): 输出目录路径
        format (str): 音频格式（mp3, wav, ogg等）
        bitrate (int): 音频比特率（kbps）
        sample_rate (int): 采样率（Hz）
        channels (int): 声道数
        merge_files (bool): 是否合并文件
        merge_filename (str): 合并文件名
        chapter_markers (bool): 是否添加章节标记
        chapter_interval (int): 章节间隔（秒）
        normalize (bool): 是否标准化音量
        noise_reduction (bool): 是否降噪
        concurrent_workers (int): 并发工作线程数
        cleanup_temp (bool): 是否清理临时文件
        naming_mode (str): 文件命名模式
        custom_template (str): 自定义命名模板
        name_length_limit (int): 文件名长度限制
    """
    output_dir: str = './output'
    format: str = 'wav'
    bitrate: int = 128
    sample_rate: int = 44100
    channels: int = 2
    merge_files: bool = False
    merge_filename: str = '完整音频'
    chapter_markers: bool = True
    chapter_interval: int = 2
    normalize: bool = True
    noise_reduction: bool = False
    concurrent_workers: int = 2
    cleanup_temp: bool = True
    
    # 文件命名设置
    naming_mode: str = 'chapter_number_title'
    custom_template: str = '{chapter_num:02d}_{title}'
    name_length_limit: int = 50
    
    # 字幕生成设置
    generate_subtitle: bool = False  # 是否生成字幕
    subtitle_format: str = 'lrc'  # 字幕格式：lrc, srt, vtt, ass, ssa
    subtitle_encoding: str = 'utf-8'  # 字幕文件编码
    subtitle_offset: float = 0.0  # 字幕时间偏移（秒）
    subtitle_style: Dict[str, Any] = field(default_factory=dict)  # 字幕样式（ASS/SSA格式）
    
    def __post_init__(self):
        """
        初始化后处理
        
        在对象创建后自动执行，用于标准化输出目录路径。
        确保输出目录存在且路径格式正确。
        """
        self.output_dir = self._normalize_output_dir(self.output_dir)
    
    def _normalize_output_dir(self, path: str) -> str:
        """
        标准化输出目录路径
        
        确保输出目录路径是绝对路径且目录存在。
        如果路径工具不可用，使用基本的路径处理。
        
        Args:
            path (str): 原始路径
            
        Returns:
            str: 标准化后的路径
        """
        try:
            from utils.path_utils import normalize_path, ensure_directory_exists
            return ensure_directory_exists(path)
        except Exception:
            # 如果导入失败，使用简单的路径处理
            import os
            if not os.path.isabs(path):
                path = os.path.abspath(path)
            os.makedirs(path, exist_ok=True)
            return path
    
    def to_dict(self) -> dict:
        """
        转换为字典格式
        
        将输出配置对象转换为字典，便于序列化和存储。
        
        Returns:
            dict: 包含所有配置参数的字典
        """
        return {
            'output_dir': self.output_dir,
            'format': self.format,
            'bitrate': self.bitrate,
            'sample_rate': self.sample_rate,
            'channels': self.channels,
            'merge_files': self.merge_files,
            'merge_filename': self.merge_filename,
            'chapter_markers': self.chapter_markers,
            'chapter_interval': self.chapter_interval,
            'normalize': self.normalize,
            'noise_reduction': self.noise_reduction,
            'concurrent_workers': self.concurrent_workers,
            'cleanup_temp': self.cleanup_temp,
            'naming_mode': self.naming_mode,
            'custom_template': self.custom_template,
            'name_length_limit': self.name_length_limit,
            'generate_subtitle': self.generate_subtitle,
            'subtitle_format': self.subtitle_format,
            'subtitle_encoding': self.subtitle_encoding,
            'subtitle_offset': self.subtitle_offset,
            'subtitle_style': self.subtitle_style
        }
    
    @classmethod
    def from_dict(cls, data: dict) -> 'OutputConfig':
        """
        从字典创建输出配置
        
        从字典数据创建OutputConfig实例，提供默认值确保配置完整性。
        
        Args:
            data (dict): 包含配置数据的字典
            
        Returns:
            OutputConfig: 新创建的输出配置实例
        """
        return cls(
            output_dir=data.get('output_dir', './output'),
            format=data.get('format', 'mp3'),
            bitrate=data.get('bitrate', 128),
            sample_rate=data.get('sample_rate', 44100),
            channels=data.get('channels', 2),
            merge_files=data.get('merge_files', False),
            merge_filename=data.get('merge_filename', '完整音频'),
            chapter_markers=data.get('chapter_markers', True),
            chapter_interval=data.get('chapter_interval', 2),
            normalize=data.get('normalize', True),
            noise_reduction=data.get('noise_reduction', False),
            concurrent_workers=data.get('concurrent_workers', 2),
            cleanup_temp=data.get('cleanup_temp', True),
            naming_mode=data.get('naming_mode', 'chapter_number_title'),
            custom_template=data.get('custom_template', '{chapter_num:02d}_{title}'),
            name_length_limit=data.get('name_length_limit', 50),
            generate_subtitle=data.get('generate_subtitle', False),
            subtitle_format=data.get('subtitle_format', 'lrc'),
            subtitle_encoding=data.get('subtitle_encoding', 'utf-8'),
            subtitle_offset=data.get('subtitle_offset', 0.0),
            subtitle_style=data.get('subtitle_style', {})
        )


@dataclass
class AudioModel:
    """
    音频模型
    
    存储音频数据和相关元信息，包括音频内容、格式参数、
    语音配置等。提供音频信息的查询和格式化功能。
    
    Attributes:
        audio_data (bytes): 音频数据（字节）
        voice_config (VoiceConfig): 语音配置
        format (str): 音频格式
        sample_rate (int): 采样率（Hz）
        channels (int): 声道数
        duration (float): 音频时长（秒）
        bitrate (int): 比特率（kbps）
        metadata (Dict[str, Any]): 元数据字典
    """
    audio_data: bytes
    voice_config: VoiceConfig
    format: str = 'wav'
    sample_rate: int = 44100
    channels: int = 2
    duration: float = 0.0
    bitrate: int = 128
    metadata: Dict[str, Any] = field(default_factory=dict)
    
    def __post_init__(self):
        """
        初始化后处理
        
        在对象创建后自动执行，如果时长为0则自动计算。
        """
        if self.duration == 0.0 and self.audio_data:
            self.duration = self.get_duration()
    
    def get_duration(self) -> float:
        """
        获取音频时长（秒）
        
        通过解析音频数据计算实际时长，如果解析失败返回0。
        
        Returns:
            float: 音频时长（秒）
        """
        if self.duration == 0.0 and self.audio_data:
            try:
                audio_segment = AudioSegment.from_file(
                    io.BytesIO(self.audio_data), 
                    format=self.format
                )
                self.duration = len(audio_segment) / 1000.0
            except Exception:
                self.duration = 0.0
        return self.duration
    
    def get_duration_formatted(self) -> str:
        """
        获取格式化的时长字符串
        
        将时长转换为MM:SS格式的字符串。
        
        Returns:
            str: 格式化的时长字符串（如"03:45"）
        """
        duration = self.get_duration()
        minutes = int(duration // 60)
        seconds = int(duration % 60)
        return f"{minutes:02d}:{seconds:02d}"
    
    def get_size_mb(self) -> float:
        """
        获取音频文件大小（MB）
        
        计算音频数据的大小并转换为MB单位。
        
        Returns:
            float: 文件大小（MB）
        """
        return len(self.audio_data) / (1024 * 1024)
    
    def to_dict(self) -> dict:
        """
        转换为字典格式
        
        将音频模型对象转换为字典，便于序列化和存储。
        
        Returns:
            dict: 包含所有音频信息的字典
        """
        return {
            'format': self.format,
            'sample_rate': self.sample_rate,
            'channels': self.channels,
            'duration': self.get_duration(),
            'bitrate': self.bitrate,
            'size_mb': self.get_size_mb(),
            'voice_config': self.voice_config.to_dict()
        }
    
    def get_info(self) -> dict:
        """
        获取音频信息
        
        返回格式化的音频信息字典，用于显示和调试。
        
        Returns:
            dict: 格式化的音频信息字典
        """
        return {
            'format': self.format,
            'sample_rate': f"{self.sample_rate} Hz",
            'channels': f"{self.channels} 声道",
            'duration': self.get_duration_formatted(),
            'bitrate': f"{self.bitrate} kbps",
            'size': f"{self.get_size_mb():.2f} MB",
            'voice': self.voice_config.voice_name,
            'engine': self.voice_config.engine
        }
