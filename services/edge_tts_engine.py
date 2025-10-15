#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Edge TTS引擎实现 - 重构版本
基于微软Edge浏览器的TTS服务
简化版本，移除重复代码和冗余逻辑
"""

import asyncio
import os
import json
import time
import tempfile
import re
import io
from typing import List, Dict, Any

import edge_tts

from .base_tts_engine import BaseTTSEngine, TTSEngineType, TTSVoiceInfo, TTSQuality, TTSResult
from models.audio_model import VoiceConfig
from utils.log_manager import LogManager


class EdgeTTSEngine(BaseTTSEngine):
    """Edge TTS引擎实现 - 重构版本"""
    
    @staticmethod
    def convert_rate_to_percentage(rate: float) -> str:
        """将语速转换为百分比格式 (Edge TTS 7.x兼容)"""
        try:
            rate_percent = int((rate - 1.0) * 100)
            return f"{rate_percent:+d}%"
        except Exception:
            return "+0%"
    
    @staticmethod
    def convert_volume_to_percentage(volume: float) -> str:
        """将音量转换为百分比格式 (Edge TTS 7.x兼容)"""
        try:
            volume_percent = int((volume - 1.0) * 100)
            return f"{volume_percent:+d}%"
        except Exception:
            return "+0%"
    
    def __init__(self, engine_id: str = "edge_tts", engine_name: str = "Edge TTS", 
                 engine_type: TTSEngineType = TTSEngineType.ONLINE, **kwargs):
        # Edge TTS特有参数
        self.use_async = kwargs.get('use_async', True)
        self.voice_style = kwargs.get('voice_style', 'default')
        self.voice_role = kwargs.get('voice_role', 'default')
        self.timeout = kwargs.get('timeout', 30)
        self.max_retries = kwargs.get('max_retries', 3)
        self.retry_delay = kwargs.get('retry_delay', 1.0)
        self.enable_caching = kwargs.get('enable_caching', True)
        self.cache_duration = kwargs.get('cache_duration', 3600)
        self.max_cache_size = kwargs.get('max_cache_size', 100)
        self.concurrent_requests = kwargs.get('concurrent_requests', 3)
        
        # 确保 _voices 属性存在
        self._voices = {}
        self._config = {}
        
        # 加载配置
        self._load_config()
        
        # 调用父类初始化
        super().__init__(engine_id, engine_name, engine_type)
        
        # 网络连接检查
        self._network_available = True
    
    def _load_config(self):
        """加载配置文件"""
        try:
            print(f"开始加载Edge TTS配置文件...")
            config_path = os.path.join(os.path.dirname(os.path.dirname(__file__)), "configs", "edge_tts.json")
            print(f"配置文件路径: {config_path}")
            
            if os.path.exists(config_path):
                print(f"配置文件存在，开始读取...")
                with open(config_path, 'r', encoding='utf-8') as f:
                    config = json.load(f)
                print(f"配置文件读取成功，配置项数量: {len(config) if isinstance(config, dict) else 0}")
                
                # 更新参数
                extra_params = config.get('extra_params', {})
                print(f"额外参数数量: {len(extra_params)}")
                
                self.use_async = extra_params.get('use_async', self.use_async)
                self.voice_style = extra_params.get('voice_style', self.voice_style)
                self.voice_role = extra_params.get('voice_role', self.voice_role)
                self.timeout = extra_params.get('timeout', self.timeout)
                self.max_retries = extra_params.get('max_retries', self.max_retries)
                self.retry_delay = extra_params.get('retry_delay', self.retry_delay)
                self.enable_caching = extra_params.get('enable_caching', self.enable_caching)
                self.cache_duration = extra_params.get('cache_duration', self.cache_duration)
                self.max_cache_size = extra_params.get('max_cache_size', self.max_cache_size)
                self.concurrent_requests = extra_params.get('concurrent_requests', self.concurrent_requests)
                
                # 保存完整配置
                self._config = config
                
                print(f"配置参数更新完成:")
                print(f"  异步模式: {self.use_async}")
                print(f"  语音风格: {self.voice_style}")
                print(f"  语音角色: {self.voice_role}")
                print(f"  超时时间: {self.timeout}秒")
                print(f"  最大重试: {self.max_retries}次")
                print(f"  重试延迟: {self.retry_delay}秒")
                print(f"  启用缓存: {self.enable_caching}")
                print(f"  缓存时长: {self.cache_duration}秒")
                print(f"  最大缓存: {self.max_cache_size}个")
                print(f"  并发请求: {self.concurrent_requests}个")
            else:
                print(f"配置文件不存在: {config_path}")
                print(f"使用默认配置")
                
        except Exception as e:
            print(f"加载Edge TTS配置失败:")
            print(f"  错误类型: {type(e).__name__}")
            print(f"  错误信息: {e}")
            import traceback
            print(f"  堆栈跟踪: {traceback.format_exc()}")
            # 不抛出异常，使用默认配置
    
    def _load_engine(self):
        """加载Edge TTS引擎"""
        try:
            # Edge TTS不需要特殊的初始化
            self.logger.info("Edge TTS引擎加载成功")
            
        except Exception as e:
            self.logger.error(f"Edge TTS引擎加载失败: {e}")
            raise
    
    def _load_voices(self):
        """加载Edge TTS语音列表"""
        try:
            # 首先尝试从JSON文件加载完整语音列表
            voices_config_path = os.path.join(os.path.dirname(os.path.dirname(__file__)), "configs", "dicts", "edge_tts_voices.json")
            
            if os.path.exists(voices_config_path):
                self.logger.info(f"找到Edge TTS语音配置文件: {voices_config_path}")
                
                with open(voices_config_path, 'r', encoding='utf-8') as f:
                    voices_config = json.load(f)
                
                voices_data = voices_config.get('voices', {})
                metadata = voices_config.get('metadata', {})
                
                self.logger.info(f"从配置文件加载语音: {len(voices_data)} 个语音")
                self.logger.info(f"配置文件版本: {metadata.get('version', 'unknown')}")
                self.logger.info(f"数据源: {metadata.get('source', 'unknown')}")
                
                # 将JSON数据转换为TTSVoiceInfo对象
                for voice_id, voice_data in voices_data.items():
                    voice_info = TTSVoiceInfo(
                        id=voice_id,
                        name=voice_data.get('name', voice_id),
                        language=voice_data.get('language', 'zh-CN'),
                        gender=voice_data.get('gender', 'unknown').lower(),
                        description=voice_data.get('description', ''),
                        engine=self.engine_id,
                        quality=TTSQuality.HIGH,
                        sample_rate=22050,
                        bit_depth=16,
                        channels=1
                    )
                    
                    # 添加额外属性
                    voice_info.custom_attributes = {
                        'personalities': voice_data.get('personalities', []),
                        'is_popular': voice_data.get('is_popular', False),
                        'is_recommended': voice_data.get('is_recommended', False),
                        'source': 'json_config'
                    }
                    
                    self._voices[voice_id] = voice_info
                
                self.logger.info(f"Edge TTS语音配置加载完成: {len(self._voices)} 个语音")
                
            else:
                # 如果配置文件不存在，使用默认配置
                self.logger.warning(f"Edge TTS语音配置文件不存在: {voices_config_path}")
                self._load_default_voices()
            
        except Exception as e:
            self.logger.error(f"Edge TTS语音配置加载失败: {e}")
            self.logger.info("尝试加载默认语音配置...")
            self._load_default_voices()
    
    def _load_default_voices(self):
        """加载默认Edge TTS语音配置"""
        try:
            # 默认Edge TTS语音配置
            voice_configs = {
                # 中文语音
                'zh-CN-XiaoxiaoNeural': {
                    'name': '晓晓', 'language': 'zh-CN', 'gender': 'female',
                    'description': '温柔甜美的女性声音', 'quality': TTSQuality.HIGH
                },
                'zh-CN-YunxiNeural': {
                    'name': '云希', 'language': 'zh-CN', 'gender': 'male',
                    'description': '成熟稳重的男性声音', 'quality': TTSQuality.HIGH
                },
                'zh-CN-YunyangNeural': {
                    'name': '云扬', 'language': 'zh-CN', 'gender': 'male',
                    'description': '年轻活力的男性声音', 'quality': TTSQuality.HIGH
                },
                'zh-CN-XiaoyiNeural': {
                    'name': '晓伊', 'language': 'zh-CN', 'gender': 'female',
                    'description': '清新自然的女性声音', 'quality': TTSQuality.HIGH
                },
                'zh-CN-YunjianNeural': {
                    'name': '云健', 'language': 'zh-CN', 'gender': 'male',
                    'description': '专业商务的男性声音', 'quality': TTSQuality.HIGH
                },
                'zh-CN-XiaochenNeural': {
                    'name': '晓辰', 'language': 'zh-CN', 'gender': 'male',
                    'description': '温和亲切的男性声音', 'quality': TTSQuality.HIGH
                },
                'zh-CN-XiaohanNeural': {
                    'name': '晓涵', 'language': 'zh-CN', 'gender': 'female',
                    'description': '优雅知性的女性声音', 'quality': TTSQuality.HIGH
                },
                'zh-CN-XiaomengNeural': {
                    'name': '晓梦', 'language': 'zh-CN', 'gender': 'female',
                    'description': '活泼可爱的女性声音', 'quality': TTSQuality.HIGH
                },
                
                # 英文语音
                'en-US-AriaNeural': {
                    'name': 'Aria', 'language': 'en-US', 'gender': 'female',
                    'description': 'Professional female voice', 'quality': TTSQuality.HIGH
                },
                'en-US-GuyNeural': {
                    'name': 'Guy', 'language': 'en-US', 'gender': 'male',
                    'description': 'Professional male voice', 'quality': TTSQuality.HIGH
                },
                'en-US-JennyNeural': {
                    'name': 'Jenny', 'language': 'en-US', 'gender': 'female',
                    'description': 'Friendly female voice', 'quality': TTSQuality.HIGH
                },
                'en-US-DavisNeural': {
                    'name': 'Davis', 'language': 'en-US', 'gender': 'male',
                    'description': 'Friendly male voice', 'quality': TTSQuality.HIGH
                }
            }
            
            # 创建TTSVoiceInfo对象
            for voice_id, config in voice_configs.items():
                voice_info = TTSVoiceInfo(
                    id=voice_id,
                    name=config['name'],
                    language=config['language'],
                    gender=config['gender'],
                    description=config['description'],
                    engine=self.engine_id,
                    quality=config['quality'],
                    sample_rate=22050,
                    bit_depth=16,
                    channels=1
                )
                
                # 添加默认属性
                voice_info.custom_attributes = {
                    'personalities': [],
                    'is_popular': False,
                    'is_recommended': False,
                    'source': 'default_config'
                }
                
                self._voices[voice_id] = voice_info
            
            self.logger.info(f"Edge TTS默认语音配置加载完成: {len(self._voices)} 个语音")
            
        except Exception as e:
            self.logger.error(f"Edge TTS默认语音配置加载失败: {e}")
            raise
    
    def synthesize(self, text: str, voice_config: VoiceConfig) -> TTSResult:
        """合成语音（统一入口，返回TTSResult，支持长文本分割）"""
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
            
            # 验证语音配置
            if not self.validate_voice_config(voice_config):
                return TTSResult(
                    success=False,
                    error_message=f"Edge TTS语音配置无效: {voice_config.voice_name}"
                )
            
            # 检查网络连接
            if not self._check_network_connection():
                return TTSResult(
                    success=False,
                    error_message="网络连接不可用"
                )
            
            # 按长度分割文本（Edge TTS限制1000字符）
            from utils.text_utils import TextUtils
            segments = TextUtils.split_text_by_length(text, 1000)
            self.logger.info(f"文本分割完成，共 {len(segments)} 段")
            
            # 如果只有一段，直接合成
            if len(segments) == 1:
                return self._synthesize_single_segment(text, voice_config)
            
            # 多段文本，需要逐段合成并合并
            generated_audios = []
            all_srt_content = []
            
            # 逐段合成
            for idx, segment in enumerate(segments):
                self.logger.info(f"合成第 {idx + 1}/{len(segments)} 段，长度: {len(segment)} 字符")
                
                # 合成当前段
                result = self._synthesize_single_segment(segment, voice_config)
                if not result.success:
                    return result
                
                generated_audios.append(result.audio_data)
                
                # 收集SRT内容
                if hasattr(result, 'metadata') and result.metadata and result.metadata.get('srt_content'):
                    all_srt_content.append(result.metadata['srt_content'])
            
            # 合并音频数据
            merged_audio = self._merge_audio_data(generated_audios)
            
            # 合并SRT内容
            merged_srt = '\n\n'.join(all_srt_content) if all_srt_content else ""
            
            # 检测音频格式
            actual_format = self._detect_audio_format(merged_audio)
            self.logger.debug(f"检测到音频格式: {actual_format}")
            
            # 处理字幕内容
            metadata = {
                'srt_content': merged_srt,
                'has_subtitle': bool(merged_srt)
            }
            
            self.logger.info(f"Edge TTS合成完成，总音频大小: {len(merged_audio)} 字节")
            
            return TTSResult(
                success=True,
                audio_data=merged_audio,
                format=actual_format,
                duration=0.0,  # 需要计算
                sample_rate=self._common_params.sample_rate,
                bit_depth=self._common_params.bit_depth,
                channels=self._common_params.channels,
                metadata=metadata
            )
            
        except Exception as e:
            self.logger.error(f"{self.engine_name} 合成失败: {e}")
            return TTSResult(
                success=False,
                error_message=f"{self.engine_name} 合成失败: {e}"
            )
    
    def _synthesize_audio(self, text: str, voice_config: VoiceConfig) -> bytes:
        """合成音频数据（基类要求的抽象方法）"""
        try:
            # 直接调用统一的合成方法，只返回音频数据
            audio_data, _ = self._synthesize_with_subtitles(text, voice_config)
            return audio_data
        except Exception as e:
            self.logger.error(f"Edge TTS音频合成失败: {e}")
            raise
    
    def _synthesize_single_segment(self, text: str, voice_config: VoiceConfig) -> TTSResult:
        """合成单个文本段"""
        try:
            start_time = time.time()
            audio_data, srt_content = self._synthesize_with_subtitles(text, voice_config)
            duration = time.time() - start_time
            
            # 检测音频格式
            actual_format = self._detect_audio_format(audio_data)
            
            # 处理字幕内容
            metadata = {
                'srt_content': srt_content,
                'has_subtitle': bool(srt_content)
            }
            
            return TTSResult(
                success=True,
                audio_data=audio_data,
                format=actual_format,
                duration=duration,
                sample_rate=self._common_params.sample_rate,
                bit_depth=self._common_params.bit_depth,
                channels=self._common_params.channels,
                metadata=metadata
            )
            
        except Exception as e:
            self.logger.error(f"Edge TTS单段合成失败: {e}")
            return TTSResult(
                success=False,
                error_message=f"Edge TTS单段合成失败: {e}"
            )
    
    def _merge_audio_data(self, audio_data_list: List[bytes]) -> bytes:
        """合并多个音频数据"""
        try:
            if not audio_data_list:
                return b""
            
            if len(audio_data_list) == 1:
                return audio_data_list[0]
            
            # 使用pydub合并音频
            from pydub import AudioSegment
            
            merged_audio = AudioSegment.empty()
            
            for audio_data in audio_data_list:
                # 将字节数据转换为AudioSegment
                audio_segment = AudioSegment.from_file(io.BytesIO(audio_data))
                merged_audio += audio_segment
            
            # 转换回字节数据
            output = io.BytesIO()
            merged_audio.export(output, format="mp3")
            return output.getvalue()
            
        except Exception as e:
            self.logger.error(f"Edge TTS音频合并失败: {e}")
            # 如果合并失败，尝试简单拼接
            return b"".join(audio_data_list)
    
    def _synthesize_with_subtitles(self, text: str, voice_config: VoiceConfig) -> tuple[bytes, str]:
        """统一的合成方法，同时生成音频和SRT内容"""
        try:
            # 获取语音配置
            voice_name = voice_config.voice_name or 'zh-CN-XiaoxiaoNeural'
            
            # 检查语音是否存在
            if voice_name not in self._voices:
                # 尝试找到其他可用的中文语音
                chinese_voices = [v for v in self._voices.values() if v.language.startswith('zh')]
                if chinese_voices:
                    voice_name = chinese_voices[0].id
                    self.logger.warning(f"语音 '{voice_config.voice_name}' 不存在，使用中文语音: {voice_name}")
                    voice_config.voice_name = voice_name
                else:
                    # 使用第一个可用语音
                    voice_name = list(self._voices.keys())[0]
                    self.logger.warning(f"语音 '{voice_config.voice_name}' 不存在，使用默认语音: {voice_name}")
                    voice_config.voice_name = voice_name
            
            # 计算语速和音量
            rate_str = self.convert_rate_to_percentage(voice_config.rate)
            volume_str = self.convert_volume_to_percentage(voice_config.volume)
            
            # 创建TTS对象
            communicate = edge_tts.Communicate(text, voice_name, rate=rate_str, volume=volume_str)
            
            # 创建字幕生成器
            submaker = edge_tts.SubMaker()
            
            # 根据配置选择同步或异步合成
            if self.use_async:
                return self._run_async_synthesis(communicate, submaker)
            else:
                return self._run_sync_synthesis(communicate, submaker)
                
        except Exception as e:
            self.logger.error(f"Edge TTS合成失败: {e}")
            raise
    
    def _run_async_synthesis(self, communicate, submaker) -> tuple[bytes, str]:
        """运行异步合成"""
        try:
            # 创建事件循环
            loop = asyncio.new_event_loop()
            asyncio.set_event_loop(loop)
            
            try:
                return loop.run_until_complete(self._async_synthesize_core(communicate, submaker))
            finally:
                loop.close()
                
        except Exception as e:
            self.logger.error(f"Edge TTS异步合成失败: {e}")
            raise
    
    def _run_sync_synthesis(self, communicate, submaker) -> tuple[bytes, str]:
        """运行同步合成"""
        try:
            # 合成音频并收集字幕数据
            audio_data = b""
            for chunk in communicate.stream():
                if chunk["type"] == "audio":
                    audio_data += chunk["data"]
                elif chunk["type"] in ("WordBoundary", "SentenceBoundary"):
                    submaker.feed(chunk)
            
            # 生成SRT内容
            srt_content = submaker.get_srt()
            
            self.logger.debug(f"Edge TTS同步合成完成，音频大小: {len(audio_data)} 字节，SRT长度: {len(srt_content)} 字符")
            
            return audio_data, srt_content
            
        except Exception as e:
            self.logger.error(f"Edge TTS同步合成失败: {e}")
            raise
    
    async def _async_synthesize_core(self, communicate, submaker) -> tuple[bytes, str]:
        """异步合成核心逻辑"""
        try:
            # 合成音频并收集字幕数据
            audio_data = b""
            async for chunk in communicate.stream():
                if chunk["type"] == "audio":
                    audio_data += chunk["data"]
                elif chunk["type"] in ("WordBoundary", "SentenceBoundary"):
                    submaker.feed(chunk)
            
            # 生成SRT内容
            srt_content = submaker.get_srt()
            
            self.logger.debug(f"Edge TTS异步合成完成，音频大小: {len(audio_data)} 字节，SRT长度: {len(srt_content)} 字符")
            
            return audio_data, srt_content
            
        except Exception as e:
            self.logger.error(f"Edge TTS异步合成核心失败: {e}")
            raise
    
    def _check_network_connection(self) -> bool:
        """检查网络连接"""
        try:
            import socket
            
            # 尝试连接到Edge TTS服务
            sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
            sock.settimeout(5)
            result = sock.connect_ex(('speech.platform.bing.com', 443))
            sock.close()
            
            self._network_available = (result == 0)
            return self._network_available
            
        except Exception as e:
            self.logger.warning(f"网络连接检查失败: {e}")
            self._network_available = False
            return False
    
    def _detect_audio_format(self, audio_data: bytes) -> str:
        """检测音频数据格式"""
        try:
            if len(audio_data) < 16:
                return 'unknown'
            
            # 检查MP3格式标识
            if audio_data.startswith(b'ID3') or audio_data.startswith(b'\xff\xfb') or audio_data.startswith(b'\xff\xf3'):
                return 'mp3'
            
            # 检查WAV格式标识
            elif audio_data.startswith(b'RIFF'):
                return 'wav'
            
            # 检查OGG格式标识
            elif audio_data.startswith(b'OggS'):
                return 'ogg'
            
            # 检查M4A格式标识
            elif audio_data.startswith(b'\x00\x00\x00\x20ftypM4A'):
                return 'm4a'
            
            # 检查AAC格式标识
            elif audio_data.startswith(b'\xff\xf1') or audio_data.startswith(b'\xff\xf9'):
                return 'aac'
            
            else:
                # 记录前几个字节用于调试
                self.logger.warning(f"无法识别音频格式，前16字节: {audio_data[:16].hex()}")
                return 'unknown'
                
        except Exception as e:
            self.logger.error(f"检测音频格式失败: {e}")
            return 'unknown'
    
    def synthesize_to_file(self, text: str, voice_config: VoiceConfig, output_path: str = None, 
                          progress_callback=None, output_config=None, chapter_info=None) -> str:
        """合成语音到文件（支持长文本分割和进度估算）"""
        try:
            if not text.strip():
                return ""
            
            self.logger.info(f"开始Edge TTS文件合成，语音: {voice_config.voice_name}")
            
            # 启动进度估算
            if progress_callback:
                from services.progress_estimator import ProgressEstimator, TextComplexityAnalyzer
                estimator = ProgressEstimator()
                
                # 分析文本复杂度
                complexity = TextComplexityAnalyzer.analyze_complexity(text)
                
                # 开始估算
                estimator.start_estimation(len(text), complexity, "edge-tts", "edge_tts")
            
            # 生成输出文件路径
            if not output_path:
                if output_config and hasattr(output_config, 'naming_mode'):
                    # 使用输出设置中的文件命名规则
                    output_path = self._generate_output_path(voice_config, output_config, text, chapter_info)
                else:
                    # 使用统一的命名规则
                    output_path = os.path.join(tempfile.gettempdir(), f"edge_tts_{voice_config.voice_name}.wav")
            
            # 确保输出目录存在
            os.makedirs(os.path.dirname(output_path), exist_ok=True)
            
            # 按长度分割文本（Edge TTS限制1000字符）
            from utils.text_utils import TextUtils
            segments = TextUtils.split_text_by_length(text, 1000)
            self.logger.info(f"文本分割完成，共 {len(segments)} 段")
            
            # 如果只有一段，直接合成
            if len(segments) == 1:
                # 更新进度到处理阶段
                if progress_callback:
                    progress_callback(50)
                
                result = self._synthesize_single_segment(text, voice_config)
                if not result.success:
                    raise Exception(result.error_message)
                
                audio_data = result.audio_data
                srt_content = result.metadata.get('srt_content', '') if result.metadata else ''
                
                # 更新进度到完成阶段
                if progress_callback:
                    progress_callback(90)
                
                # 保存音频文件
                with open(output_path, "wb") as audio_file:
                    audio_file.write(audio_data)
                
                # 完成进度
                if progress_callback:
                    progress_callback(100)
                
                self.logger.info(f"Edge TTS合成完成: {output_path}")
                return output_path
            
            # 多段文本，需要逐段合成并合并
            generated_audios = []
            all_srt_content = []
            temp_dir = tempfile.gettempdir()
            
            # 逐段合成
            for idx, segment in enumerate(segments):
                self.logger.info(f"合成第 {idx + 1}/{len(segments)} 段，长度: {len(segment)} 字符")
                
                # 更新当前段进度
                if progress_callback:
                    # 计算当前段的进度百分比
                    segment_progress = int((idx / len(segments)) * 80)  # 0-80%用于段处理
                    progress_callback(segment_progress)
                
                # 合成当前段
                result = self._synthesize_single_segment(segment, voice_config)
                if not result.success:
                    raise Exception(result.error_message)
                
                audio_data = result.audio_data
                generated_audios.append(audio_data)
                
                # 收集SRT内容
                if result.metadata and result.metadata.get('srt_content'):
                    all_srt_content.append(result.metadata['srt_content'])
                
                # 标记段完成
                if progress_callback:
                    # 计算段完成后的进度百分比
                    segment_progress = int(((idx + 1) / len(segments)) * 80)  # 0-80%用于段处理
                    progress_callback(segment_progress)
            
            # 更新进度到合并阶段
            if progress_callback:
                progress_callback(90)
            
            # 合并音频数据
            merged_audio = self._merge_audio_data(generated_audios)
            
            # 合并SRT内容
            merged_srt = '\n\n'.join(all_srt_content) if all_srt_content else ""
            
            # 保存音频文件
            with open(output_path, "wb") as audio_file:
                audio_file.write(merged_audio)
            
            # 完成进度
            if progress_callback:
                progress_callback(100)
            
            # 生成并保存字幕文件
            base_path = os.path.splitext(output_path)[0]
            
            if merged_srt:
                # 检查是否有输出配置来生成字幕
                if output_config and getattr(output_config, 'generate_subtitle', False):
                    from utils.subtitle_utils import SubtitleGenerator
                    
                    # 创建字幕生成器
                    subtitle_gen = SubtitleGenerator(
                        format_type=getattr(output_config, 'subtitle_format', 'lrc'),
                        encoding=getattr(output_config, 'subtitle_encoding', 'utf-8'),
                        offset=getattr(output_config, 'subtitle_offset', 0.0)
                    )
                    
                    # 生成指定格式的字幕文件
                    subtitle_path = subtitle_gen.generate_subtitle_file(
                        merged_srt, 
                        base_path,
                        getattr(output_config, 'subtitle_style', {})
                    )
                    
                    self.logger.info(f"Edge TTS文件合成完成: {output_path}")
                    self.logger.info(f"字幕文件已生成: {subtitle_path} (格式: {getattr(output_config, 'subtitle_format', 'lrc')})")
                else:
                    # 不生成字幕文件，只记录日志
                    self.logger.info(f"Edge TTS文件合成完成: {output_path}")
                    self.logger.debug(f"SRT内容已生成但未保存文件（generate_subtitle=False）")
            else:
                self.logger.info(f"Edge TTS文件合成完成: {output_path}")
            
            # 检查是否需要格式转换
            target_format = self._get_target_format(output_path, output_config)
            actual_format = self._detect_audio_format(audio_data) if audio_data else 'wav'
            
            if target_format != actual_format:
                # 需要进行格式转换
                self.logger.info(f"检测到格式不匹配，进行转换: {actual_format} -> {target_format}")
                
                # 转换格式
                converted_data = self._convert_audio_format(audio_data, actual_format, target_format, output_config)
                if converted_data:
                    # 保存转换后的音频数据
                    with open(output_path, "wb") as f:
                        f.write(converted_data)
                    self.logger.info(f"Edge TTS 格式转换完成: {output_path}")
                else:
                    self.logger.warning(f"格式转换失败，保持原始{actual_format}格式: {output_path}")
            else:
                self.logger.info(f"Edge TTS文件合成完成: {output_path}")
            
            return output_path
            
        except Exception as e:
            self.logger.error(f"Edge TTS文件合成失败: {e}")
            raise
    
    def get_engine_info(self) -> Dict[str, Any]:
        """获取引擎信息"""
        info = super().get_engine_info()
        
        # 添加Edge TTS特有信息
        info.update({
            'use_async': self.use_async,
            'voice_style': self.voice_style,
            'voice_role': self.voice_role,
            'network_available': self._network_available,
            'supported_ssml': True,
            'supported_languages': ['zh-CN', 'en-US'],
            'max_text_length': 10000,
            'parameter_format': 'percentage',  # Edge TTS 7.x使用百分比格式
            'rate_range': '0.5x - 2.0x (对应 -50% 到 +100%)',
            'volume_range': '0.5 - 2.0 (对应 -50% 到 +100%)'
        })
        
        return info
    
    def _calculate_dynamic_timeout(self, text: str) -> int:
        """计算动态超时时间（基于Edge-TTS实际处理规则）"""
        try:
            text_length = len(text)
            
            # Edge-TTS处理规则：基础时间8秒，500字符。每超过500，增加7秒
            if text_length <= 500:
                base_timeout = 10  # 基础8秒
            else:
                extra_chars = text_length - 500
                extra_time = ((extra_chars + 499) // 500) * 8  # 每500字符增加7秒
                base_timeout = 10 + extra_time
            
            # 添加一些缓冲时间（考虑网络延迟、API处理等）
            buffer_time = 3  # 3秒缓冲时间
            dynamic_timeout = base_timeout + buffer_time
            
            # 设置合理的时间范围：最小10秒，最大5分钟
            dynamic_timeout = max(10, min(dynamic_timeout, 300))
            
            self.logger.info(f"Edge-TTS动态超时计算: 文本长度={text_length}, 基础超时={base_timeout}s, 缓冲时间={buffer_time}s, 最终超时={dynamic_timeout}s")
            
            return dynamic_timeout
            
        except Exception as e:
            self.logger.error(f"计算Edge-TTS动态超时时间失败: {e}")
            return 30  # 默认30秒
