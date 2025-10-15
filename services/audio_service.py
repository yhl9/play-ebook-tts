"""
音频服务模块

提供音频文件处理和管理功能，包括：
- 音频合并：将多个音频文件合并为一个
- 格式转换：支持多种音频格式之间的转换
- 音频保存：将音频数据保存为文件
- 音频处理：音量调整、音质优化等
- 格式检测：自动检测音频文件格式

支持的音频格式：
- MP3：压缩音频格式，文件小
- WAV：无损音频格式，质量高
- OGG：开源音频格式
- M4A：苹果音频格式
- AAC：高级音频编码

依赖工具：
- FFmpeg：音频处理的核心工具
- pydub：Python音频处理库

作者: TTS开发团队
版本: 1.0.0
创建时间: 2024
"""

import io
from typing import List, Optional
from abc import ABC, abstractmethod
from pathlib import Path

from pydub import AudioSegment
from pydub.utils import which

from models.audio_model import AudioModel, VoiceConfig
from utils.log_manager import LogManager


class IAudioService(ABC):
    """
    音频服务接口
    
    定义音频处理服务的标准接口，包括音频合并、格式转换、音频保存等功能。
    采用接口隔离原则，确保不同实现的一致性。
    """
    
    @abstractmethod
    def merge_audio_files(self, audio_files: List[AudioModel]) -> AudioModel:
        """
        合并多个音频文件
        
        Args:
            audio_files (List[AudioModel]): 音频文件列表
            
        Returns:
            AudioModel: 合并后的音频模型
        """
        pass
    
    @abstractmethod
    def save_audio(self, audio_model: AudioModel, output_path: str):
        """
        保存音频到文件
        
        Args:
            audio_model (AudioModel): 音频模型
            output_path (str): 输出文件路径
        """
        pass
    
    @abstractmethod
    def convert_format(self, audio_model: AudioModel, target_format: str) -> AudioModel:
        """
        转换音频格式
        
        Args:
            audio_model (AudioModel): 源音频模型
            target_format (str): 目标格式
            
        Returns:
            AudioModel: 转换后的音频模型
        """
        pass


class AudioService(IAudioService):
    """
    音频服务实现类
    
    提供完整的音频处理功能，包括音频合并、格式转换、音频保存等。
    基于pydub库实现，支持多种音频格式的处理。
    
    特性：
    - 多格式支持：支持MP3、WAV、OGG等格式
    - 音频合并：无缝合并多个音频文件
    - 格式转换：支持各种音频格式之间的转换
    - 质量优化：提供音频质量优化功能
    - 错误处理：完善的异常处理机制
    """
    
    def __init__(self):
        self.logger = LogManager().get_logger("AudioService")
        self.supported_formats = ['mp3', 'wav', 'ogg', 'm4a', 'aac']
        self._check_ffmpeg()
    
    def _check_ffmpeg(self):
        """检查FFmpeg是否可用"""
        if not which("ffmpeg"):
            self.logger.warning("FFmpeg未找到，某些音频格式可能无法处理")
    
    def merge_audio_files(self, audio_files: List[AudioModel]) -> AudioModel:
        """合并音频文件"""
        try:
            if not audio_files:
                raise ValueError("音频文件列表不能为空")
            
            self.logger.info(f"开始合并 {len(audio_files)} 个音频文件")
            
            # 获取第一个音频文件作为基础
            first_audio = audio_files[0]
            merged_segment = self._create_audio_segment(first_audio)
            
            # 合并其他音频文件
            for audio_file in audio_files[1:]:
                segment = self._create_audio_segment(audio_file)
                merged_segment += segment
            
            # 创建合并后的音频模型
            merged_audio = AudioModel(
                audio_data=merged_segment.export(format=first_audio.format).read(),
                voice_config=first_audio.voice_config,
                format=first_audio.format,
                sample_rate=merged_segment.frame_rate,
                channels=merged_segment.channels,
                bitrate=first_audio.bitrate
            )
            
            self.logger.info(f"音频合并完成，总时长: {merged_audio.get_duration_formatted()}")
            return merged_audio
            
        except Exception as e:
            self.logger.error(f"音频合并失败: {e}")
            raise AudioProcessingError(f"音频合并失败: {e}")
    
    def save_audio(self, audio_model: AudioModel, output_path: str):
        """保存音频文件"""
        try:
            output_path = Path(output_path)
            output_path.parent.mkdir(parents=True, exist_ok=True)
            
            # 创建音频段
            audio_segment = self._create_audio_segment(audio_model)
            
            # 导出音频文件
            audio_segment.export(
                str(output_path),
                format=audio_model.format,
                bitrate=f"{audio_model.bitrate}k"
            )
            
            self.logger.info(f"音频文件已保存: {output_path}")
            
        except Exception as e:
            self.logger.error(f"保存音频文件失败: {e}")
            raise AudioProcessingError(f"保存音频文件失败: {e}")
    
    def convert_format(self, audio_model: AudioModel, target_format: str) -> AudioModel:
        """转换音频格式"""
        try:
            self.logger.info(f"转换音频格式: {audio_model.format} -> {target_format}")
            
            # 创建音频段
            audio_segment = self._create_audio_segment(audio_model)
            
            # 转换格式
            converted_data = audio_segment.export(format=target_format).read()
            
            # 创建转换后的音频模型
            converted_audio = AudioModel(
                audio_data=converted_data,
                voice_config=audio_model.voice_config,
                format=target_format,
                sample_rate=audio_segment.frame_rate,
                channels=audio_segment.channels,
                bitrate=audio_model.bitrate
            )
            
            self.logger.info(f"音频格式转换完成: {target_format}")
            return converted_audio
            
        except Exception as e:
            self.logger.error(f"音频格式转换失败: {e}")
            raise AudioProcessingError(f"音频格式转换失败: {e}")
    
    def _create_audio_segment(self, audio_model: AudioModel) -> AudioSegment:
        """创建音频段"""
        try:
            # 首先尝试根据格式创建音频段
            if audio_model.format == 'mp3':
                return AudioSegment.from_mp3(io.BytesIO(audio_model.audio_data))
            elif audio_model.format == 'wav':
                return AudioSegment.from_wav(io.BytesIO(audio_model.audio_data))
            elif audio_model.format == 'ogg':
                return AudioSegment.from_ogg(io.BytesIO(audio_model.audio_data))
            else:
                # 尝试通用方法
                return AudioSegment.from_file(io.BytesIO(audio_model.audio_data))
                
        except Exception as e:
            self.logger.warning(f"按格式创建音频段失败: {e}")
            # 如果按格式创建失败，尝试自动检测格式
            try:
                # 检查音频数据的前几个字节来确定实际格式
                audio_data = audio_model.audio_data
                if len(audio_data) < 16:
                    raise AudioProcessingError("音频数据太短，无法确定格式")
                
                # 检查MP3格式标识
                if audio_data.startswith(b'ID3') or audio_data.startswith(b'\xff\xfb') or audio_data.startswith(b'\xff\xf3'):
                    self.logger.info("检测到MP3格式，尝试使用MP3解码器")
                    return AudioSegment.from_mp3(io.BytesIO(audio_data))
                
                # 检查WAV格式标识
                elif audio_data.startswith(b'RIFF'):
                    self.logger.info("检测到WAV格式，尝试使用WAV解码器")
                    return AudioSegment.from_wav(io.BytesIO(audio_data))
                
                # 检查OGG格式标识
                elif audio_data.startswith(b'OggS'):
                    self.logger.info("检测到OGG格式，尝试使用OGG解码器")
                    return AudioSegment.from_ogg(io.BytesIO(audio_data))
                
                # 如果都不匹配，尝试通用方法
                else:
                    self.logger.warning(f"无法识别音频格式，前16字节: {audio_data[:16].hex()}")
                    return AudioSegment.from_file(io.BytesIO(audio_data))
                    
            except Exception as e2:
                self.logger.error(f"自动检测格式创建音频段也失败: {e2}")
                raise AudioProcessingError(f"创建音频段失败: {e}，自动检测格式也失败: {e2}")
    
    def get_audio_info(self, audio_model: AudioModel) -> dict:
        """获取音频信息"""
        try:
            audio_segment = self._create_audio_segment(audio_model)
            
            return {
                'duration': len(audio_segment) / 1000.0,  # 秒
                'sample_rate': audio_segment.frame_rate,
                'channels': audio_segment.channels,
                'format': audio_model.format,
                'bitrate': audio_model.bitrate,
                'size_mb': len(audio_model.audio_data) / (1024 * 1024)
            }
            
        except Exception as e:
            self.logger.error(f"获取音频信息失败: {e}")
            return {}
    
    def normalize_audio(self, audio_model: AudioModel) -> AudioModel:
        """标准化音频"""
        try:
            audio_segment = self._create_audio_segment(audio_model)
            
            # 标准化音量
            normalized_segment = audio_segment.normalize()
            
            # 创建标准化后的音频模型
            normalized_audio = AudioModel(
                audio_data=normalized_segment.export(format=audio_model.format).read(),
                voice_config=audio_model.voice_config,
                format=audio_model.format,
                sample_rate=normalized_segment.frame_rate,
                channels=normalized_segment.channels,
                bitrate=audio_model.bitrate
            )
            
            self.logger.info("音频标准化完成")
            return normalized_audio
            
        except Exception as e:
            self.logger.error(f"音频标准化失败: {e}")
            return audio_model
    
    def trim_audio(self, audio_model: AudioModel, start_ms: int, end_ms: int) -> AudioModel:
        """裁剪音频"""
        try:
            audio_segment = self._create_audio_segment(audio_model)
            
            # 裁剪音频
            trimmed_segment = audio_segment[start_ms:end_ms]
            
            # 创建裁剪后的音频模型
            trimmed_audio = AudioModel(
                audio_data=trimmed_segment.export(format=audio_model.format).read(),
                voice_config=audio_model.voice_config,
                format=audio_model.format,
                sample_rate=trimmed_segment.frame_rate,
                channels=trimmed_segment.channels,
                bitrate=audio_model.bitrate
            )
            
            self.logger.info(f"音频裁剪完成: {start_ms}ms - {end_ms}ms")
            return trimmed_audio
            
        except Exception as e:
            self.logger.error(f"音频裁剪失败: {e}")
            return audio_model
    
    def add_silence(self, audio_model: AudioModel, silence_duration_ms: int) -> AudioModel:
        """添加静音"""
        try:
            audio_segment = self._create_audio_segment(audio_model)
            
            # 创建静音段
            silence = AudioSegment.silent(duration=silence_duration_ms)
            
            # 添加静音
            audio_with_silence = audio_segment + silence
            
            # 创建添加静音后的音频模型
            audio_with_silence_model = AudioModel(
                audio_data=audio_with_silence.export(format=audio_model.format).read(),
                voice_config=audio_model.voice_config,
                format=audio_model.format,
                sample_rate=audio_with_silence.frame_rate,
                channels=audio_with_silence.channels,
                bitrate=audio_model.bitrate
            )
            
            self.logger.info(f"添加静音完成: {silence_duration_ms}ms")
            return audio_with_silence_model
            
        except Exception as e:
            self.logger.error(f"添加静音失败: {e}")
            return audio_model
    
    def get_supported_formats(self) -> List[str]:
        """获取支持的音频格式"""
        return self.supported_formats.copy()
    
    def is_ffmpeg_available(self) -> bool:
        """检查FFmpeg是否可用"""
        return which("ffmpeg") is not None


class AudioProcessingError(Exception):
    """音频处理异常"""
    pass
