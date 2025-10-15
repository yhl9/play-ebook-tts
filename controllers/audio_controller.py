"""
音频控制器
"""

from typing import List, Optional
from abc import ABC, abstractmethod

from models.audio_model import AudioModel, VoiceConfig
from services.audio_service import AudioService, AudioProcessingError
from services.tts_service import TTSService, AudioGenerationError, UnsupportedTTSEngineError
from utils.log_manager import LogManager


class IAudioController(ABC):
    """音频控制器接口"""
    
    @abstractmethod
    def generate_audio(self, text: str, voice_config: VoiceConfig) -> AudioModel:
        pass
    
    @abstractmethod
    def merge_audio_files(self, audio_files: List[AudioModel]) -> AudioModel:
        pass
    
    @abstractmethod
    def save_audio(self, audio_model: AudioModel, output_path: str):
        pass


class AudioController(IAudioController):
    """音频控制器实现"""
    
    def __init__(self):
        self.logger = LogManager().get_logger("AudioController")
        self.audio_service = AudioService()
        self.tts_service = None  # 延迟初始化
    
    def _ensure_tts_service(self):
        """确保TTS服务已初始化"""
        if self.tts_service is None:
            self.tts_service = TTSService()
    
    def generate_audio(self, text: str, voice_config: VoiceConfig) -> AudioModel:
        """生成音频"""
        try:
            self.logger.info(f"开始生成音频，文本长度: {len(text)}, 引擎: {voice_config.engine}")
            
            # 使用TTS服务生成音频
            self._ensure_tts_service()
            tts_result = self.tts_service.synthesize(text, voice_config)
            
            if not tts_result.success:
                raise AudioGenerationError(f"TTS合成失败: {tts_result.error_message}")
            
            # 创建音频模型，使用TTS结果中的正确格式信息
            audio_model = AudioModel(
                audio_data=tts_result.audio_data,
                voice_config=voice_config,
                format=tts_result.format,  # 使用TTS结果中的实际格式
                sample_rate=tts_result.sample_rate,
                channels=tts_result.channels,
                duration=tts_result.duration,
                metadata=tts_result.metadata  # 传递metadata（包含SRT内容）
            )
            
            self.logger.info(f"音频生成完成，格式: {tts_result.format}, 时长: {audio_model.get_duration_formatted()}")
            return audio_model
            
        except Exception as e:
            self.logger.error(f"音频生成失败: {e}")
            raise AudioGenerationError(f"音频生成失败: {e}")
    
    def merge_audio_files(self, audio_files: List[AudioModel]) -> AudioModel:
        """合并音频文件"""
        try:
            self.logger.info(f"开始合并 {len(audio_files)} 个音频文件")
            
            merged_audio = self.audio_service.merge_audio_files(audio_files)
            
            self.logger.info(f"音频合并完成，时长: {merged_audio.get_duration_formatted()}")
            return merged_audio
            
        except Exception as e:
            self.logger.error(f"音频合并失败: {e}")
            raise AudioProcessingError(f"音频合并失败: {e}")
    
    def save_audio(self, audio_model: AudioModel, output_path: str):
        """保存音频文件"""
        try:
            self.logger.info(f"保存音频文件: {output_path}")
            
            self.audio_service.save_audio(audio_model, output_path)
            
            self.logger.info("音频文件保存成功")
            
        except Exception as e:
            self.logger.error(f"保存音频文件失败: {e}")
            raise AudioProcessingError(f"保存音频文件失败: {e}")
    
    def get_available_voices(self) -> List[dict]:
        """获取可用语音列表"""
        try:
            self._ensure_tts_service()
            return self.tts_service.get_available_voices()
        except Exception as e:
            self.logger.error(f"获取语音列表失败: {e}")
            return []
    
    def get_all_available_voices(self) -> List[dict]:
        """获取所有引擎的可用语音列表"""
        try:
            self._ensure_tts_service()
            return self.tts_service.get_all_available_voices()
        except Exception as e:
            self.logger.error(f"获取所有语音列表失败: {e}")
            return []
    
    def is_engine_available(self, engine: str) -> bool:
        """检查TTS引擎是否可用"""
        try:
            self._ensure_tts_service()
            return self.tts_service.is_engine_available(engine)
        except Exception as e:
            self.logger.error(f"检查TTS引擎可用性失败: {e}")
            return False
    
    def get_engine_info(self, engine: str) -> dict:
        """获取TTS引擎信息"""
        try:
            self._ensure_tts_service()
            return self.tts_service.get_engine_info(engine)
        except Exception as e:
            self.logger.error(f"获取TTS引擎信息失败: {e}")
            return {}
    
    def convert_audio_format(self, audio_model: AudioModel, target_format: str) -> AudioModel:
        """转换音频格式"""
        try:
            self.logger.info(f"转换音频格式: {audio_model.format} -> {target_format}")
            
            converted_audio = self.audio_service.convert_format(audio_model, target_format)
            
            self.logger.info("音频格式转换完成")
            return converted_audio
            
        except Exception as e:
            self.logger.error(f"音频格式转换失败: {e}")
            raise AudioProcessingError(f"音频格式转换失败: {e}")
    
    def normalize_audio(self, audio_model: AudioModel) -> AudioModel:
        """标准化音频"""
        try:
            self.logger.info("标准化音频")
            
            normalized_audio = self.audio_service.normalize_audio(audio_model)
            
            self.logger.info("音频标准化完成")
            return normalized_audio
            
        except Exception as e:
            self.logger.error(f"音频标准化失败: {e}")
            return audio_model
    
    def trim_audio(self, audio_model: AudioModel, start_ms: int, end_ms: int) -> AudioModel:
        """裁剪音频"""
        try:
            self.logger.info(f"裁剪音频: {start_ms}ms - {end_ms}ms")
            
            trimmed_audio = self.audio_service.trim_audio(audio_model, start_ms, end_ms)
            
            self.logger.info("音频裁剪完成")
            return trimmed_audio
            
        except Exception as e:
            self.logger.error(f"音频裁剪失败: {e}")
            return audio_model
    
    def add_silence(self, audio_model: AudioModel, silence_duration_ms: int) -> AudioModel:
        """添加静音"""
        try:
            self.logger.info(f"添加静音: {silence_duration_ms}ms")
            
            audio_with_silence = self.audio_service.add_silence(audio_model, silence_duration_ms)
            
            self.logger.info("静音添加完成")
            return audio_with_silence
            
        except Exception as e:
            self.logger.error(f"添加静音失败: {e}")
            return audio_model
    
    def get_audio_info(self, audio_model: AudioModel) -> dict:
        """获取音频信息"""
        try:
            return self.audio_service.get_audio_info(audio_model)
        except Exception as e:
            self.logger.error(f"获取音频信息失败: {e}")
            return {}
    
    def validate_voice_config(self, voice_config: VoiceConfig) -> dict:
        """验证语音配置"""
        try:
            result = {
                'valid': True,
                'issues': []
            }
            
            # 检查引擎是否可用
            if not self.is_engine_available(voice_config.engine):
                result['valid'] = False
                result['issues'].append(f"TTS引擎不可用: {voice_config.engine}")
            
            # 检查语音参数范围
            if not 0.1 <= voice_config.rate <= 3.0:
                result['issues'].append(f"语速超出范围: {voice_config.rate}")
            
            if not -50 <= voice_config.pitch <= 50:
                result['issues'].append(f"音调超出范围: {voice_config.pitch}")
            
            if not 0.0 <= voice_config.volume <= 1.0:
                result['issues'].append(f"音量超出范围: {voice_config.volume}")
            
            # 检查语音名称
            if not voice_config.voice_name:
                result['issues'].append("语音名称不能为空")
            
            return result
            
        except Exception as e:
            self.logger.error(f"验证语音配置失败: {e}")
            return {
                'valid': False,
                'issues': [f"验证失败: {e}"]
            }
    
    def test_voice(self, text: str, voice_config: VoiceConfig) -> AudioModel:
        """测试语音"""
        try:
            self.logger.info(f"测试语音: {voice_config.voice_name}")
            
            # 使用较短的测试文本
            test_text = text[:100] if len(text) > 100 else text
            
            audio_model = self.generate_audio(test_text, voice_config)
            
            self.logger.info("语音测试完成")
            return audio_model
            
        except Exception as e:
            self.logger.error(f"语音测试失败: {e}")
            raise AudioGenerationError(f"语音测试失败: {e}")
    
    def batch_generate_audio(self, text_segments: List[str], voice_config: VoiceConfig) -> List[AudioModel]:
        """批量生成音频"""
        try:
            self.logger.info(f"批量生成音频，段落数: {len(text_segments)}")
            
            audio_models = []
            failed_segments = []
            
            for i, text in enumerate(text_segments):
                try:
                    audio_model = self.generate_audio(text, voice_config)
                    audio_models.append(audio_model)
                except Exception as e:
                    self.logger.error(f"生成第 {i+1} 段音频失败: {e}")
                    failed_segments.append({'index': i, 'text': text, 'error': str(e)})
            
            self.logger.info(f"批量生成完成，成功: {len(audio_models)}, 失败: {len(failed_segments)}")
            
            return audio_models
            
        except Exception as e:
            self.logger.error(f"批量生成音频失败: {e}")
            raise AudioGenerationError(f"批量生成音频失败: {e}")
    
    def estimate_audio_duration(self, text: str, voice_config: VoiceConfig) -> float:
        """估算音频时长"""
        try:
            # 基于文本长度和语音参数估算
            word_count = len(text.split())
            
            # 基础语速（每分钟字数）
            base_words_per_minute = 150
            
            # 根据语速调整
            adjusted_words_per_minute = base_words_per_minute * voice_config.rate
            
            # 计算时长（分钟）
            duration_minutes = word_count / adjusted_words_per_minute
            
            return duration_minutes * 60  # 转换为秒
            
        except Exception as e:
            self.logger.error(f"估算音频时长失败: {e}")
            return 0.0
    
    def get_audio_quality_info(self, audio_model: AudioModel) -> dict:
        """获取音频质量信息"""
        try:
            info = self.get_audio_info(audio_model)
            
            quality_info = {
                'duration': info.get('duration', 0),
                'sample_rate': info.get('sample_rate', 0),
                'channels': info.get('channels', 0),
                'bitrate': audio_model.bitrate,
                'format': audio_model.format,
                'size_mb': audio_model.get_size_mb(),
                'quality_rating': 'unknown'
            }
            
            # 评估音质
            if info.get('sample_rate', 0) >= 44100 and audio_model.bitrate >= 128:
                quality_info['quality_rating'] = 'high'
            elif info.get('sample_rate', 0) >= 22050 and audio_model.bitrate >= 64:
                quality_info['quality_rating'] = 'medium'
            else:
                quality_info['quality_rating'] = 'low'
            
            return quality_info
            
        except Exception as e:
            self.logger.error(f"获取音频质量信息失败: {e}")
            return {}
