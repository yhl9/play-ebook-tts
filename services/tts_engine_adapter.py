#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
TTS引擎适配器
将新的BaseTTSEngine适配到旧的ITTSService接口
"""

from typing import List, Dict, Any, Optional
from .base_tts_engine import BaseTTSEngine, TTSResult
from .tts_service import ITTSService, AudioGenerationError
from models.audio_model import VoiceConfig
from utils.log_manager import LogManager


class TTSEngineAdapter(ITTSService):
    """TTS引擎适配器 - 将BaseTTSEngine适配到ITTSService接口"""
    
    def __init__(self, engine: BaseTTSEngine):
        """初始化适配器"""
        self.engine = engine
        self.logger = LogManager().get_logger(f"TTSEngineAdapter_{engine.engine_id}")
        super().__init__()
    
    def _init_engine(self):
        """初始化引擎（适配器不需要额外初始化）"""
        pass
    
    def synthesize(self, text: str, voice_config: VoiceConfig) -> TTSResult:
        """合成语音为TTSResult"""
        try:
            result = self.engine.synthesize(text, voice_config)
            if isinstance(result, TTSResult):
                return result
            elif isinstance(result, bytes):
                # 为兼容性创建TTSResult
                return TTSResult(
                    success=True,
                    audio_data=result,
                    format='wav'  # 默认格式，旧引擎可能返回bytes
                )
            else:
                raise AudioGenerationError(f"引擎返回了不支持的音频数据类型: {type(result)}")
        except Exception as e:
            self.logger.error(f"引擎合成失败: {e}")
            return TTSResult(
                success=False,
                error_message=f"引擎合成失败: {e}"
            )
    
    def synthesize_to_file(self, text: str, voice_config: VoiceConfig, output_path: str = None, 
                          progress_callback=None, output_config=None, chapter_info=None) -> str:
        """合成语音到文件（支持进度回调）"""
        try:
            # 检查引擎是否支持progress_callback参数
            import inspect
            sig = inspect.signature(self.engine.synthesize_to_file)
            if 'progress_callback' in sig.parameters:
                # 支持progress_callback的引擎（如EmotiVoice、Edge-TTS）
                result = self.engine.synthesize_to_file(text, voice_config, output_path, progress_callback, output_config, chapter_info)
            else:
                # 不支持progress_callback的引擎
                result = self.engine.synthesize_to_file(text, voice_config, output_path, output_config, chapter_info)
            if isinstance(result, TTSResult):
                if result.success:
                    return result.output_path or ""
                else:
                    raise AudioGenerationError(f"引擎文件合成失败: {result.error_message}")
            elif isinstance(result, str):
                return result
            else:
                raise AudioGenerationError(f"引擎返回了不支持的文件路径类型: {type(result)}")
        except Exception as e:
            self.logger.error(f"引擎文件合成失败: {e}")
            raise AudioGenerationError(f"引擎文件合成失败: {e}")
    
    def get_available_voices(self) -> List[dict]:
        """获取可用语音列表"""
        try:
            voices = self.engine.get_available_voices()
            # 转换为旧格式
            result = []
            for voice in voices:
                if hasattr(voice, 'to_dict'):
                    result.append(voice.to_dict())
                else:
                    # 手动转换
                    voice_dict = {
                        'id': getattr(voice, 'id', ''),
                        'name': getattr(voice, 'name', ''),
                        'language': getattr(voice, 'language', ''),
                        'gender': getattr(voice, 'gender', 'unknown'),
                        'description': getattr(voice, 'description', ''),
                        'engine': getattr(voice, 'engine', self.engine.engine_id)
                    }
                    result.append(voice_dict)
            return result
        except Exception as e:
            self.logger.error(f"获取语音列表失败: {e}")
            return []
    
    def is_available(self) -> bool:
        """检查引擎是否可用"""
        try:
            return self.engine.is_available()
        except Exception:
            return False
    
    def get_engine_name(self) -> str:
        """获取引擎名称"""
        try:
            return self.engine.engine_name
        except Exception:
            return "Unknown Engine"
    
    def get_engine_info(self) -> dict:
        """获取引擎信息"""
        try:
            return {
                'name': self.engine.engine_name,
                'description': f'{self.engine.engine_name} TTS引擎',
                'available': self.engine.is_available,
                'online': self.engine.engine_type.value == 'online',
                'voice_count': len(self.engine.voices),
                'engine_id': self.engine.engine_id,
                'engine_type': self.engine.engine_type.value
            }
        except Exception as e:
            self.logger.error(f"获取引擎信息失败: {e}")
            return {
                'name': 'Unknown Engine',
                'description': '未知TTS引擎',
                'available': False,
                'online': False,
                'voice_count': 0
            }
