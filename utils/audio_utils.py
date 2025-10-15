"""
音频工具类
"""

import io
from typing import List, Optional, Tuple
from pathlib import Path

from pydub import AudioSegment
from pydub.utils import which

from utils.log_manager import LogManager


class AudioUtils:
    """音频工具类"""
    
    def __init__(self):
        self.logger = LogManager().get_logger("AudioUtils")
        self.supported_formats = ['mp3', 'wav', 'ogg', 'm4a', 'aac']
    
    def is_audio_file(self, file_path: str) -> bool:
        """检查是否为音频文件"""
        try:
            extension = Path(file_path).suffix.lower().lstrip('.')
            return extension in self.supported_formats
        except Exception:
            return False
    
    def get_audio_duration(self, file_path: str) -> float:
        """获取音频时长（秒）"""
        try:
            audio = AudioSegment.from_file(file_path)
            return len(audio) / 1000.0
        except Exception as e:
            self.logger.error(f"获取音频时长失败: {file_path}, 错误: {e}")
            return 0.0
    
    def get_audio_info(self, file_path: str) -> dict:
        """获取音频信息"""
        try:
            audio = AudioSegment.from_file(file_path)
            
            return {
                'duration': len(audio) / 1000.0,
                'sample_rate': audio.frame_rate,
                'channels': audio.channels,
                'format': Path(file_path).suffix.lower().lstrip('.'),
                'bitrate': audio.frame_rate * audio.channels * 16,  # 估算比特率
                'size_mb': Path(file_path).stat().st_size / (1024 * 1024)
            }
        except Exception as e:
            self.logger.error(f"获取音频信息失败: {file_path}, 错误: {e}")
            return {}
    
    def convert_audio_format(self, input_path: str, output_path: str, 
                           target_format: str, bitrate: str = "128k") -> bool:
        """转换音频格式"""
        try:
            audio = AudioSegment.from_file(input_path)
            audio.export(output_path, format=target_format, bitrate=bitrate)
            return True
        except Exception as e:
            self.logger.error(f"音频格式转换失败: {input_path} -> {output_path}, 错误: {e}")
            return False
    
    def merge_audio_files(self, input_paths: List[str], output_path: str) -> bool:
        """合并音频文件"""
        try:
            if not input_paths:
                return False
            
            # 加载第一个音频文件
            merged_audio = AudioSegment.from_file(input_paths[0])
            
            # 合并其他音频文件
            for path in input_paths[1:]:
                audio = AudioSegment.from_file(path)
                merged_audio += audio
            
            # 导出合并后的音频
            merged_audio.export(output_path, format="mp3")
            return True
            
        except Exception as e:
            self.logger.error(f"音频合并失败: {output_path}, 错误: {e}")
            return False
    
    def trim_audio(self, input_path: str, output_path: str, 
                  start_ms: int, end_ms: int) -> bool:
        """裁剪音频"""
        try:
            audio = AudioSegment.from_file(input_path)
            trimmed_audio = audio[start_ms:end_ms]
            trimmed_audio.export(output_path, format="mp3")
            return True
        except Exception as e:
            self.logger.error(f"音频裁剪失败: {input_path}, 错误: {e}")
            return False
    
    def normalize_audio(self, input_path: str, output_path: str) -> bool:
        """标准化音频音量"""
        try:
            audio = AudioSegment.from_file(input_path)
            normalized_audio = audio.normalize()
            normalized_audio.export(output_path, format="mp3")
            return True
        except Exception as e:
            self.logger.error(f"音频标准化失败: {input_path}, 错误: {e}")
            return False
    
    def add_silence(self, input_path: str, output_path: str, 
                   silence_duration_ms: int) -> bool:
        """添加静音"""
        try:
            audio = AudioSegment.from_file(input_path)
            silence = AudioSegment.silent(duration=silence_duration_ms)
            audio_with_silence = audio + silence
            audio_with_silence.export(output_path, format="mp3")
            return True
        except Exception as e:
            self.logger.error(f"添加静音失败: {input_path}, 错误: {e}")
            return False
    
    def change_speed(self, input_path: str, output_path: str, 
                    speed_factor: float) -> bool:
        """改变音频速度"""
        try:
            audio = AudioSegment.from_file(input_path)
            
            # 改变播放速度
            new_sample_rate = int(audio.frame_rate * speed_factor)
            audio_with_new_speed = audio._spawn(audio.raw_data, overrides={"frame_rate": new_sample_rate})
            audio_with_new_speed = audio_with_new_speed.set_frame_rate(audio.frame_rate)
            
            audio_with_new_speed.export(output_path, format="mp3")
            return True
        except Exception as e:
            self.logger.error(f"改变音频速度失败: {input_path}, 错误: {e}")
            return False
    
    def get_audio_peak_level(self, file_path: str) -> float:
        """获取音频峰值电平"""
        try:
            audio = AudioSegment.from_file(file_path)
            return audio.max_dBFS
        except Exception as e:
            self.logger.error(f"获取音频峰值电平失败: {file_path}, 错误: {e}")
            return 0.0
    
    def is_ffmpeg_available(self) -> bool:
        """检查FFmpeg是否可用"""
        return which("ffmpeg") is not None
    
    def get_supported_formats(self) -> List[str]:
        """获取支持的音频格式"""
        return self.supported_formats.copy()
    
    def validate_audio_file(self, file_path: str) -> bool:
        """验证音频文件"""
        try:
            if not Path(file_path).exists():
                return False
            
            if not self.is_audio_file(file_path):
                return False
            
            # 尝试加载音频文件
            AudioSegment.from_file(file_path)
            return True
            
        except Exception as e:
            self.logger.error(f"音频文件验证失败: {file_path}, 错误: {e}")
            return False
    
    def get_audio_metadata(self, file_path: str) -> dict:
        """获取音频元数据"""
        try:
            audio = AudioSegment.from_file(file_path)
            
            return {
                'duration_ms': len(audio),
                'duration_seconds': len(audio) / 1000.0,
                'sample_rate': audio.frame_rate,
                'channels': audio.channels,
                'sample_width': audio.sample_width,
                'frame_rate': audio.frame_rate,
                'frame_count': audio.frame_count(),
                'max_possible_amplitude': audio.max_possible_amplitude,
                'max_dBFS': audio.max_dBFS,
                'rms': audio.rms
            }
        except Exception as e:
            self.logger.error(f"获取音频元数据失败: {file_path}, 错误: {e}")
            return {}
    
    def create_silence(self, duration_ms: int, sample_rate: int = 44100, 
                      channels: int = 2) -> AudioSegment:
        """创建静音音频段"""
        try:
            return AudioSegment.silent(
                duration=duration_ms,
                frame_rate=sample_rate
            ).set_channels(channels)
        except Exception as e:
            self.logger.error(f"创建静音失败: {e}")
            return AudioSegment.silent(duration=0)
    
    def fade_in_out(self, input_path: str, output_path: str, 
                   fade_in_ms: int = 0, fade_out_ms: int = 0) -> bool:
        """添加淡入淡出效果"""
        try:
            audio = AudioSegment.from_file(input_path)
            
            if fade_in_ms > 0:
                audio = audio.fade_in(fade_in_ms)
            
            if fade_out_ms > 0:
                audio = audio.fade_out(fade_out_ms)
            
            audio.export(output_path, format="mp3")
            return True
            
        except Exception as e:
            self.logger.error(f"添加淡入淡出效果失败: {input_path}, 错误: {e}")
            return False
