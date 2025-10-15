#!/usr/bin/env python3
"""
音频转换服务模块

提供音频格式转换功能，支持通过FFmpeg进行各种音频格式之间的转换。
主要用于将WAV格式转换为其他格式（如MP3、OGG等）。

支持的转换：
- WAV -> MP3
- WAV -> OGG
- WAV -> M4A
- WAV -> FLAC
- 其他格式之间的转换

依赖工具：
- FFmpeg：音频转换的核心工具

作者: TTS开发团队
版本: 1.0.0
创建时间: 2024
"""

import os
import tempfile
import subprocess
from pathlib import Path
from typing import Optional, Dict, Any
from utils.log_manager import LogManager


class AudioConverter:
    """音频转换器"""
    
    def __init__(self):
        self.logger = LogManager().get_logger("AudioConverter")
        self.temp_dir = tempfile.gettempdir()
    
    def convert_audio(self, input_path: str, output_path: str, 
                     target_format: str, quality_params: Dict[str, Any] = None) -> bool:
        """
        转换音频格式
        
        Args:
            input_path (str): 输入文件路径
            output_path (str): 输出文件路径
            target_format (str): 目标格式
            quality_params (Dict[str, Any]): 质量参数
            
        Returns:
            bool: 转换是否成功
        """
        try:
            if not os.path.exists(input_path):
                self.logger.error(f"输入文件不存在: {input_path}")
                return False
            
            # 确保输出目录存在
            output_dir = os.path.dirname(output_path)
            if output_dir:  # 只有当output_dir不为空时才创建目录
                os.makedirs(output_dir, exist_ok=True)
            
            # 构建FFmpeg命令
            cmd = self._build_ffmpeg_command(input_path, output_path, target_format, quality_params)
            
            self.logger.info(f"开始转换音频: {input_path} -> {output_path}")
            self.logger.debug(f"FFmpeg命令: {' '.join(cmd)}")
            
            # 检查命令中的空字符串
            for i, arg in enumerate(cmd):
                if not arg or arg.strip() == '':
                    self.logger.error(f"命令参数 {i} 为空: '{arg}'")
                    return False
            
            # 执行转换
            result = subprocess.run(
                cmd,
                capture_output=True,
                text=True,
                timeout=300  # 5分钟超时
            )
            
            if result.returncode == 0:
                self.logger.info(f"音频转换成功: {output_path}")
                return True
            else:
                self.logger.error(f"音频转换失败: {result.stderr}")
                return False
                
        except subprocess.TimeoutExpired:
            self.logger.error("音频转换超时")
            return False
        except Exception as e:
            self.logger.error(f"音频转换异常: {e}")
            return False
    
    def _build_ffmpeg_command(self, input_path: str, output_path: str, 
                             target_format: str, quality_params: Dict[str, Any] = None) -> list:
        """构建FFmpeg命令"""
        cmd = ["ffmpeg", "-i", input_path, "-y"]  # -y 覆盖输出文件
        
        # 根据目标格式设置参数
        if target_format.lower() == "mp3":
            cmd.extend(["-acodec", "libmp3lame"])
            if quality_params and quality_params.get('bitrate'):
                cmd.extend(["-b:a", f"{quality_params['bitrate']}k"])
            else:
                cmd.extend(["-b:a", "128k"])  # 默认128k比特率
                
        elif target_format.lower() == "ogg":
            cmd.extend(["-acodec", "libvorbis"])
            if quality_params and quality_params.get('bitrate'):
                cmd.extend(["-b:a", f"{quality_params['bitrate']}k"])
            else:
                cmd.extend(["-b:a", "128k"])
                
        elif target_format.lower() == "m4a":
            cmd.extend(["-acodec", "aac"])
            if quality_params and quality_params.get('bitrate'):
                cmd.extend(["-b:a", f"{quality_params['bitrate']}k"])
            else:
                cmd.extend(["-b:a", "128k"])
                
        elif target_format.lower() == "flac":
            cmd.extend(["-acodec", "flac"])
            # FLAC是无损格式，不需要比特率参数
            
        # 设置采样率
        if quality_params and quality_params.get('sample_rate'):
            cmd.extend(["-ar", str(quality_params['sample_rate'])])
        
        # 设置声道数
        if quality_params and quality_params.get('channels'):
            channels = quality_params['channels']
            if channels == 1:
                cmd.extend(["-ac", "1"])
            elif channels == 2:
                cmd.extend(["-ac", "2"])
        
        cmd.append(output_path)
        return cmd
    
    def convert_wav_to_format(self, wav_path: str, target_format: str, 
                             output_dir: str, quality_params: Dict[str, Any] = None) -> Optional[str]:
        """
        将WAV文件转换为指定格式
        
        Args:
            wav_path (str): WAV文件路径
            target_format (str): 目标格式
            output_dir (str): 输出目录
            quality_params (Dict[str, Any]): 质量参数
            
        Returns:
            Optional[str]: 转换后的文件路径，失败返回None
        """
        try:
            # 生成输出文件名
            wav_name = os.path.basename(wav_path)
            name, _ = os.path.splitext(wav_name)
            output_filename = f"{name}.{target_format.lower()}"
            output_path = os.path.join(output_dir, output_filename)
            
            # 执行转换
            success = self.convert_audio(wav_path, output_path, target_format, quality_params)
            
            if success and os.path.exists(output_path):
                return output_path
            else:
                return None
                
        except Exception as e:
            self.logger.error(f"WAV转换失败: {e}")
            return None
    
    def is_ffmpeg_available(self) -> bool:
        """检查FFmpeg是否可用"""
        try:
            result = subprocess.run(
                ["ffmpeg", "-version"],
                capture_output=True,
                text=True,
                timeout=10
            )
            return result.returncode == 0
        except Exception:
            return False
    
    def get_supported_formats(self) -> list:
        """获取支持的音频格式"""
        return ["wav", "mp3", "ogg", "m4a", "flac", "aac", "wma"]
