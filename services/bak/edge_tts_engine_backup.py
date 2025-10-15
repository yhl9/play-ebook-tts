#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Edge TTS引擎实现
基于微软Edge浏览器的TTS服务
"""

import asyncio
import io
import os
import json
import wave
import time
import tempfile
import re
from typing import List, Dict, Any

import edge_tts

from .base_tts_engine import BaseTTSEngine, TTSEngineType, TTSVoiceInfo, TTSQuality, TTSResult
from models.audio_model import VoiceConfig
from utils.log_manager import LogManager


class EdgeTTSEngine(BaseTTSEngine):
    """Edge TTS引擎实现"""
    
    @staticmethod
    def convert_rate_to_percentage(rate: float) -> str:
        """将语速转换为百分比格式 (Edge TTS 7.x兼容)"""
        try:
            # 将倍速转换为百分比
            # 1.0 = +0%, 1.2 = +20%, 0.8 = -20%
            rate_percent = int((rate - 1.0) * 100)
            return f"{rate_percent:+d}%"
        except Exception:
            return "+0%"
    
    @staticmethod
    def convert_volume_to_percentage(volume: float) -> str:
        """将音量转换为百分比格式 (Edge TTS 7.x兼容)"""
        try:
            # 将音量值转换为百分比
            # 1.0 = +0%, 1.1 = +10%, 0.9 = -10%
            volume_percent = int((volume - 1.0) * 100)
            return f"{volume_percent:+d}%"
        except Exception:
            return "+0%"
    
    @staticmethod
    def convert_percentage_to_rate(rate_str: str) -> float:
        """将百分比格式转换为倍速 (向后兼容)"""
        try:
            if rate_str.endswith('%'):
                percent = int(rate_str[:-1])
                return 1.0 + (percent / 100.0)
            else:
                return float(rate_str)
        except Exception:
            return 1.0
    
    @staticmethod
    def convert_percentage_to_volume(volume_str: str) -> float:
        """将百分比格式转换为音量值 (向后兼容)"""
        try:
            if volume_str.endswith('%'):
                percent = int(volume_str[:-1])
                return 1.0 + (percent / 100.0)
            else:
                return float(volume_str)
        except Exception:
            return 1.0
    
    def __init__(self, engine_id: str = "edge_tts", engine_name: str = "Edge TTS", 
                 engine_type: TTSEngineType = TTSEngineType.ONLINE, **kwargs):
        # Edge TTS特有参数 - 在调用父类之前设置
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
            # 在父类初始化之前，logger 可能不存在，使用 print 代替
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
                'zh-CN-XiaomoNeural': {
                    'name': '晓墨', 'language': 'zh-CN', 'gender': 'male',
                    'description': '文艺清新的男性声音', 'quality': TTSQuality.HIGH
                },
                'zh-CN-XiaoqiuNeural': {
                    'name': '晓秋', 'language': 'zh-CN', 'gender': 'female',
                    'description': '成熟优雅的女性声音', 'quality': TTSQuality.HIGH
                },
                'zh-CN-XiaoruiNeural': {
                    'name': '晓睿', 'language': 'zh-CN', 'gender': 'male',
                    'description': '睿智博学的男性声音', 'quality': TTSQuality.HIGH
                },
                'zh-CN-XiaoshuangNeural': {
                    'name': '晓双', 'language': 'zh-CN', 'gender': 'female',
                    'description': '温柔体贴的女性声音', 'quality': TTSQuality.HIGH
                },
                'zh-CN-XiaoxuanNeural': {
                    'name': '晓萱', 'language': 'zh-CN', 'gender': 'female',
                    'description': '清新脱俗的女性声音', 'quality': TTSQuality.HIGH
                },
                'zh-CN-XiaoyanNeural': {
                    'name': '晓颜', 'language': 'zh-CN', 'gender': 'female',
                    'description': '美丽动人的女性声音', 'quality': TTSQuality.HIGH
                },
                'zh-CN-XiaoyouNeural': {
                    'name': '晓悠', 'language': 'zh-CN', 'gender': 'female',
                    'description': '悠闲自在的女性声音', 'quality': TTSQuality.HIGH
                },
                'zh-CN-XiaozhenNeural': {
                    'name': '晓甄', 'language': 'zh-CN', 'gender': 'female',
                    'description': '真诚善良的女性声音', 'quality': TTSQuality.HIGH
                },
                'zh-CN-YunfengNeural': {
                    'name': '云枫', 'language': 'zh-CN', 'gender': 'male',
                    'description': '深沉稳重的男性声音', 'quality': TTSQuality.HIGH
                },
                'zh-CN-YunhaoNeural': {
                    'name': '云浩', 'language': 'zh-CN', 'gender': 'male',
                    'description': '豪迈大气的男性声音', 'quality': TTSQuality.HIGH
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
                },
                'en-US-EmmaNeural': {
                    'name': 'Emma', 'language': 'en-US', 'gender': 'female',
                    'description': 'Energetic female voice', 'quality': TTSQuality.HIGH
                },
                'en-US-BrianNeural': {
                    'name': 'Brian', 'language': 'en-US', 'gender': 'male',
                    'description': 'Energetic male voice', 'quality': TTSQuality.HIGH
                },
                'en-US-AvaNeural': {
                    'name': 'Ava', 'language': 'en-US', 'gender': 'female',
                    'description': 'Calm female voice', 'quality': TTSQuality.HIGH
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
        """合成语音（重写基类方法，正确设置格式并生成SRT）"""
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
            
            # 使用带SRT生成的方法合成音频
            start_time = time.time()
            audio_data, srt_content = self._synthesize_with_srt_data(text, voice_config)
            duration = time.time() - start_time
            
            # 检测音频格式
            actual_format = self._detect_audio_format(audio_data)
            self.logger.debug(f"检测到音频格式: {actual_format}")
            
            # 将SRT内容存储到metadata中，供后续使用
            metadata = {
                'srt_content': srt_content,
                'has_srt': bool(srt_content)
            }
            
            return TTSResult(
                success=True,
                audio_data=audio_data,
                duration=duration,
                sample_rate=self._common_params.sample_rate,
                bit_depth=self._common_params.bit_depth,
                channels=self._common_params.channels,
                format=actual_format,  # 设置正确的格式
                metadata=metadata  # 包含SRT内容
            )
            
        except Exception as e:
            self.logger.error(f"{self.engine_name} 合成失败: {e}")
            return TTSResult(
                success=False,
                error_message=f"{self.engine_name} 合成失败: {e}"
            )
    
    def _synthesize_with_srt_data(self, text: str, voice_config: VoiceConfig) -> tuple[bytes, str]:
        """合成音频数据并生成SRT内容"""
        try:
            import asyncio
            
            # 创建事件循环
            loop = asyncio.new_event_loop()
            asyncio.set_event_loop(loop)
            
            try:
                return loop.run_until_complete(self._async_synthesize_with_srt_data(text, voice_config))
            finally:
                loop.close()
                
        except Exception as e:
            self.logger.error(f"Edge TTS带SRT数据合成失败: {e}")
            raise
    
    async def _async_synthesize_with_srt_data(self, text: str, voice_config: VoiceConfig) -> tuple[bytes, str]:
        """异步合成音频数据并生成SRT内容"""
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
                    # 更新voice_config中的voice_name
                    voice_config.voice_name = voice_name
                else:
                    # 使用第一个可用语音
                    voice_name = list(self._voices.keys())[0]
                    self.logger.warning(f"语音 '{voice_config.voice_name}' 不存在，使用默认语音: {voice_name}")
                    # 更新voice_config中的voice_name
                    voice_config.voice_name = voice_name
            
            # 计算语速和音量
            rate_str = self.convert_rate_to_percentage(voice_config.rate)
            volume_str = self.convert_volume_to_percentage(voice_config.volume)
            
            # 创建TTS对象 - 使用纯文本和参数，避免SSML可能的问题
            communicate = edge_tts.Communicate(text, voice_name, rate=rate_str, volume=volume_str)
            
            # 创建字幕生成器
            submaker = edge_tts.SubMaker()
            
            # 合成音频并收集字幕数据
            audio_data = b""
            async for chunk in communicate.stream():
                if chunk["type"] == "audio":
                    audio_data += chunk["data"]
                elif chunk["type"] in ("WordBoundary", "SentenceBoundary"):
                    submaker.feed(chunk)
            
            # 生成SRT内容
            srt_content = submaker.get_srt()
            
            self.logger.debug(f"Edge TTS带SRT数据合成完成，音频大小: {len(audio_data)} 字节，SRT长度: {len(srt_content)} 字符")
            
            return audio_data, srt_content
            
        except Exception as e:
            self.logger.error(f"Edge TTS异步带SRT数据合成失败: {e}")
            raise
    
    def _synthesize_audio(self, text: str, voice_config: VoiceConfig) -> bytes:
        """合成音频数据"""
        try:
            # 验证语音配置（包括语音映射）
            if not self.validate_voice_config(voice_config):
                raise Exception(f"Edge TTS语音配置无效: {voice_config.voice_name}")
            
            # 检查网络连接
            if not self._check_network_connection():
                raise Exception("网络连接不可用")
            
            # 使用异步方式合成
            if self.use_async:
                return self._synthesize_async(text, voice_config)
            else:
                return self._synthesize_sync(text, voice_config)
                
        except Exception as e:
            self.logger.error(f"Edge TTS合成失败: {e}")
            raise
    
    def _synthesize_async(self, text: str, voice_config: VoiceConfig) -> bytes:
        """异步合成音频"""
        try:
            # 创建事件循环
            loop = asyncio.new_event_loop()
            asyncio.set_event_loop(loop)
            
            try:
                return loop.run_until_complete(self._async_synthesize(text, voice_config))
            finally:
                loop.close()
                
        except Exception as e:
            self.logger.error(f"Edge TTS异步合成失败: {e}")
            raise
    
    async def _async_synthesize(self, text: str, voice_config: VoiceConfig) -> bytes:
        """异步合成实现"""
        try:
            self.logger.debug(f"原始文本: {text}")
            
            # 计算语速和音量 - 适配Edge TTS 7.x格式
            rate_str = self.convert_rate_to_percentage(voice_config.rate)
            volume_str = self.convert_volume_to_percentage(voice_config.volume)
            
            self.logger.debug(f"语音参数: voice={voice_config.voice_name}, rate={rate_str}, volume={volume_str}")
            
            # 创建TTS对象 - 使用纯文本和参数，避免SSML可能的问题
            tts = edge_tts.Communicate(text, voice_config.voice_name, rate=rate_str, volume=volume_str)
            
            # 合成音频
            audio_data = b""
            async for chunk in tts.stream():
                if chunk["type"] == "audio":
                    audio_data += chunk["data"]
            
            # Edge-TTS返回的是MP3格式的音频数据，需要验证格式
            if audio_data:
                # 检查音频数据格式
                if audio_data.startswith(b'ID3') or audio_data.startswith(b'\xff\xfb') or audio_data.startswith(b'\xff\xf3'):
                    # 这是MP3格式
                    self.logger.debug("Edge-TTS返回MP3格式音频数据")
                elif audio_data.startswith(b'RIFF'):
                    # 这是WAV格式
                    self.logger.debug("Edge-TTS返回WAV格式音频数据")
                else:
                    # 未知格式，记录前几个字节用于调试
                    self.logger.warning(f"Edge-TTS返回未知格式音频数据，前16字节: {audio_data[:16].hex()}")
            
            return audio_data
            
        except Exception as e:
            self.logger.error(f"Edge TTS异步合成失败: {e}")
            raise
    
    def _synthesize_sync(self, text: str, voice_config: VoiceConfig) -> bytes:
        """同步合成音频"""
        try:
            # 计算语速和音量 - 适配Edge TTS 7.x格式
            rate_str = self.convert_rate_to_percentage(voice_config.rate)
            volume_str = self.convert_volume_to_percentage(voice_config.volume)
            
            # 创建TTS对象 - 使用纯文本和参数，避免SSML可能的问题
            tts = edge_tts.Communicate(text, voice_config.voice_name, rate=rate_str, volume=volume_str)
            
            # 合成音频
            audio_data = b""
            for chunk in tts.stream():
                if chunk["type"] == "audio":
                    audio_data += chunk["data"]
            
            # Edge-TTS返回的是MP3格式的音频数据，需要验证格式
            if audio_data:
                # 检查音频数据格式
                if audio_data.startswith(b'ID3') or audio_data.startswith(b'\xff\xfb') or audio_data.startswith(b'\xff\xf3'):
                    # 这是MP3格式
                    self.logger.debug("Edge-TTS返回MP3格式音频数据")
                elif audio_data.startswith(b'RIFF'):
                    # 这是WAV格式
                    self.logger.debug("Edge-TTS返回WAV格式音频数据")
                else:
                    # 未知格式，记录前几个字节用于调试
                    self.logger.warning(f"Edge-TTS返回未知格式音频数据，前16字节: {audio_data[:16].hex()}")
            
            return audio_data
            
        except Exception as e:
            self.logger.error(f"Edge TTS同步合成失败: {e}")
            raise
    
    def _build_ssml(self, text: str, voice_config: VoiceConfig) -> str:
        """构建SSML"""
        try:
            # 基础SSML模板 - 移除换行和空格，避免被当作文本内容
            ssml_template = '<speak version="1.0" xmlns="http://www.w3.org/2001/10/synthesis" xml:lang="{language}"><voice name="{voice_name}"><prosody rate="{rate}" volume="{volume}">{text}</prosody></voice></speak>'
            
            # 计算语速和音量 - 适配Edge TTS 7.x格式
            rate_str = self.convert_rate_to_percentage(voice_config.rate)
            volume_str = self.convert_volume_to_percentage(voice_config.volume)
            
            # 构建SSML
            ssml = ssml_template.format(
                language=voice_config.language,
                voice_name=voice_config.voice_name,
                rate=rate_str,
                volume=volume_str,
                text=text
            )
            
            return ssml
            
        except Exception as e:
            self.logger.error(f"构建SSML失败: {e}")
            # 返回简单的SSML
            return f'<speak version="1.0" xmlns="http://www.w3.org/2001/10/synthesis" xml:lang="{voice_config.language}"><voice name="{voice_config.voice_name}">{text}</voice></speak>'
    
    
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
    
    def validate_voice_config(self, voice_config: VoiceConfig) -> bool:
        """验证语音配置"""
        if not super().validate_voice_config(voice_config):
            return False
        
        # Edge TTS特有验证
        if voice_config.voice_name and voice_config.voice_name not in self._voices:
            # 尝试使用语音映射服务进行映射
            try:
                from services.voice_mapping_service import voice_mapping_service
                available_voices = [{'id': vid, 'name': vinfo.name} for vid, vinfo in self._voices.items()]
                mapping = voice_mapping_service.map_voice_id(
                    voice_config.voice_name, 
                    voice_config.engine, 
                    'edge_tts', 
                    available_voices
                )
                
                if mapping.target_id in self._voices:
                    self.logger.info(f"语音映射成功: {voice_config.voice_name} -> {mapping.target_id}")
                    voice_config.voice_name = mapping.target_id
                else:
                    self.logger.warning(f"Edge TTS语音 {voice_config.voice_name} 不存在，映射后仍无效: {mapping.target_id}")
                    return False
            except Exception as e:
                self.logger.warning(f"Edge TTS语音 {voice_config.voice_name} 不存在，映射失败: {e}")
                return False
        
        # 检查语言支持
        if voice_config.voice_name:
            voice_info = self._voices.get(voice_config.voice_name)
            if voice_info and voice_info.language != voice_config.language:
                self.logger.warning(f"语音 {voice_config.voice_name} 不支持语言 {voice_config.language}")
                return False
        
        return True
    
    def get_available_voices(self) -> List[TTSVoiceInfo]:
        """获取可用语音列表"""
        try:
            # 如果还没有加载语音，先加载
            if not self._voices:
                self._load_voices()
            
            # 返回所有语音
            voices = list(self._voices.values())
            
            if voices:
                self.logger.info(f"Edge TTS返回 {len(voices)} 个可用语音")
                return voices
            else:
                self.logger.warning("Edge TTS没有找到可用语音")
                return []
                
        except Exception as e:
            self.logger.error(f"获取Edge TTS语音列表失败: {e}")
            return []
    
    def add_voice(self, voice_id: str, name: str, language: str = 'zh-CN', gender: str = 'unknown', 
                  description: str = '', personalities: List[str] = None, is_popular: bool = False, 
                  is_recommended: bool = False):
        """添加自定义语音配置"""
        try:
            if personalities is None:
                personalities = []
            
            voice_info = TTSVoiceInfo(
                id=voice_id,
                name=name,
                language=language,
                gender=gender.lower(),
                description=description,
                engine=self.engine_id,
                quality=TTSQuality.HIGH,
                sample_rate=22050,
                bit_depth=16,
                channels=1
            )
            
            # 添加自定义属性
            voice_info.custom_attributes = {
                'personalities': personalities,
                'is_popular': is_popular,
                'is_recommended': is_recommended,
                'source': 'custom_added'
            }
            
            self._voices[voice_id] = voice_info
            self.logger.info(f"添加自定义语音: {voice_id} - {name}")
            
        except Exception as e:
            self.logger.error(f"添加自定义语音失败: {e}")
            raise
    
    def remove_voice(self, voice_id: str):
        """移除语音配置"""
        try:
            if voice_id in self._voices:
                del self._voices[voice_id]
                self.logger.info(f"移除语音配置: {voice_id}")
            else:
                self.logger.warning(f"语音配置不存在: {voice_id}")
                
        except Exception as e:
            self.logger.error(f"移除语音配置失败: {e}")
            raise
    
    def get_voice_by_language(self, language: str) -> List[TTSVoiceInfo]:
        """根据语言获取语音列表"""
        try:
            voices = [v for v in self._voices.values() if v.language == language]
            self.logger.info(f"找到 {len(voices)} 个 {language} 语音")
            return voices
        except Exception as e:
            self.logger.error(f"根据语言获取语音失败: {e}")
            return []
    
    def get_popular_voices(self) -> List[TTSVoiceInfo]:
        """获取热门语音列表"""
        try:
            voices = [v for v in self._voices.values() 
                     if hasattr(v, 'custom_attributes') and v.custom_attributes.get('is_popular', False)]
            self.logger.info(f"找到 {len(voices)} 个热门语音")
            return voices
        except Exception as e:
            self.logger.error(f"获取热门语音失败: {e}")
            return []
    
    def get_recommended_voices(self) -> List[TTSVoiceInfo]:
        """获取推荐语音列表"""
        try:
            voices = [v for v in self._voices.values() 
                     if hasattr(v, 'custom_attributes') and v.custom_attributes.get('is_recommended', False)]
            self.logger.info(f"找到 {len(voices)} 个推荐语音")
            return voices
        except Exception as e:
            self.logger.error(f"获取推荐语音失败: {e}")
            return []
    
    def reload_voices(self):
        """重新加载语音配置"""
        try:
            self.logger.info("重新加载Edge TTS语音配置...")
            self._voices.clear()
            self._load_voices()
            self.logger.info("Edge TTS语音配置重新加载完成")
        except Exception as e:
            self.logger.error(f"重新加载语音配置失败: {e}")
            raise
    
    def get_config(self) -> Dict[str, Any]:
        """获取当前配置"""
        try:
            return {
                'engine_id': self.engine_id,
                'engine_name': self.engine_name,
                'use_async': self.use_async,
                'voice_style': self.voice_style,
                'voice_role': self.voice_role,
                'timeout': self.timeout,
                'max_retries': self.max_retries,
                'retry_delay': self.retry_delay,
                'enable_caching': self.enable_caching,
                'cache_duration': self.cache_duration,
                'max_cache_size': self.max_cache_size,
                'concurrent_requests': self.concurrent_requests,
                'network_available': self._network_available,
                'voices_count': len(self._voices)
            }
        except Exception as e:
            self.logger.error(f"获取配置失败: {e}")
            return {}
    
    def update_config(self, config_updates: Dict[str, Any]) -> bool:
        """更新配置参数"""
        try:
            self.logger.info(f"更新Edge TTS配置: {config_updates}")
            
            # 更新参数
            if 'use_async' in config_updates:
                self.use_async = config_updates['use_async']
            if 'voice_style' in config_updates:
                self.voice_style = config_updates['voice_style']
            if 'voice_role' in config_updates:
                self.voice_role = config_updates['voice_role']
            if 'timeout' in config_updates:
                self.timeout = config_updates['timeout']
            if 'max_retries' in config_updates:
                self.max_retries = config_updates['max_retries']
            if 'retry_delay' in config_updates:
                self.retry_delay = config_updates['retry_delay']
            if 'enable_caching' in config_updates:
                self.enable_caching = config_updates['enable_caching']
            if 'cache_duration' in config_updates:
                self.cache_duration = config_updates['cache_duration']
            if 'max_cache_size' in config_updates:
                self.max_cache_size = config_updates['max_cache_size']
            if 'concurrent_requests' in config_updates:
                self.concurrent_requests = config_updates['concurrent_requests']
            
            self.logger.info("Edge TTS配置更新成功")
            return True
            
        except Exception as e:
            self.logger.error(f"更新配置失败: {e}")
            return False
    
    def save_config(self, config_path: str = None) -> bool:
        """保存配置到文件"""
        try:
            if config_path is None:
                config_path = os.path.join(os.path.dirname(os.path.dirname(__file__)), "configs", "edge_tts.json")
            
            # 构建配置数据
            config_data = {
                "engine": "edge_tts",
                "voice_name": "zh-CN-XiaoxiaoNeural",
                "rate": 1.0,
                "pitch": 0,
                "volume": 1.0,
                "language": "zh-CN",
                "output_format": "wav",
                "extra_params": {
                    "voice_name": "zh-CN-XiaoxiaoNeural",
                    "use_async": self.use_async,
                    "voice_style": self.voice_style,
                    "voice_role": self.voice_role,
                    "timeout": self.timeout,
                    "max_retries": self.max_retries,
                    "retry_delay": self.retry_delay,
                    "enable_caching": self.enable_caching,
                    "cache_duration": self.cache_duration,
                    "max_cache_size": self.max_cache_size,
                    "concurrent_requests": self.concurrent_requests,
                    "parameter_format": "percentage",
                    "rate_range": "0.5x - 2.0x (对应 -50% 到 +100%)",
                    "volume_range": "0.5 - 2.0 (对应 -50% 到 +100%)"
                }
            }
            
            # 确保目录存在
            os.makedirs(os.path.dirname(config_path), exist_ok=True)
            
            # 保存配置
            with open(config_path, 'w', encoding='utf-8') as f:
                json.dump(config_data, f, indent=2, ensure_ascii=False)
            
            self.logger.info(f"Edge TTS配置已保存到: {config_path}")
            return True
            
        except Exception as e:
            self.logger.error(f"保存配置失败: {e}")
            return False
    
    def reload_config(self) -> bool:
        """重新加载配置"""
        try:
            self.logger.info("重新加载Edge TTS配置...")
            self._load_config()
            self.logger.info("Edge TTS配置重新加载完成")
            return True
        except Exception as e:
            self.logger.error(f"重新加载配置失败: {e}")
            return False
    
    def validate_config(self) -> Dict[str, Any]:
        """验证配置参数"""
        try:
            validation_results = {
                'valid': True,
                'errors': [],
                'warnings': []
            }
            
            # 验证超时时间
            if not isinstance(self.timeout, (int, float)) or self.timeout <= 0:
                validation_results['errors'].append("超时时间必须是正数")
                validation_results['valid'] = False
            
            # 验证重试次数
            if not isinstance(self.max_retries, int) or self.max_retries < 0:
                validation_results['errors'].append("最大重试次数必须是非负整数")
                validation_results['valid'] = False
            
            # 验证重试延迟
            if not isinstance(self.retry_delay, (int, float)) or self.retry_delay < 0:
                validation_results['errors'].append("重试延迟必须是非负数")
                validation_results['valid'] = False
            
            # 验证缓存设置
            if not isinstance(self.cache_duration, (int, float)) or self.cache_duration <= 0:
                validation_results['warnings'].append("缓存时长应该是正数")
            
            if not isinstance(self.max_cache_size, int) or self.max_cache_size <= 0:
                validation_results['warnings'].append("最大缓存大小应该是正整数")
            
            # 验证并发请求数
            if not isinstance(self.concurrent_requests, int) or self.concurrent_requests <= 0:
                validation_results['warnings'].append("并发请求数应该是正整数")
            
            # 验证语音风格和角色
            valid_styles = ['default', 'cheerful', 'sad', 'angry', 'fearful', 'disgruntled', 'serious', 'affectionate', 'gentle']
            if self.voice_style not in valid_styles:
                validation_results['warnings'].append(f"语音风格 '{self.voice_style}' 可能不是有效值")
            
            valid_roles = ['default', 'Girl', 'Boy', 'YoungAdultFemale', 'YoungAdultMale', 'OlderAdultFemale', 'OlderAdultMale', 'SeniorFemale', 'SeniorMale']
            if self.voice_role not in valid_roles:
                validation_results['warnings'].append(f"语音角色 '{self.voice_role}' 可能不是有效值")
            
            return validation_results
            
        except Exception as e:
            self.logger.error(f"验证配置失败: {e}")
            return {
                'valid': False,
                'errors': [f"验证过程出错: {e}"],
                'warnings': []
            }
    
    def synthesize_to_file(self, text: str, voice_config: VoiceConfig, output_path: str = None, 
                          output_config=None, chapter_info=None) -> str:
        """合成语音到文件"""
        try:
            if not text.strip():
                return ""
            
            self.logger.info(f"开始Edge TTS文件合成，语音: {voice_config.voice_name}")
            
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
            
            # Edge-TTS引擎硬编码：总是生成SRT字幕文件
            return self._synthesize_with_srt(text, voice_config, output_path)
            
        except Exception as e:
            self.logger.error(f"Edge TTS文件合成失败: {e}")
            raise
    
    def _synthesize_with_srt(self, text: str, voice_config: VoiceConfig, output_path: str) -> str:
        """同时生成音频和SRT字幕文件"""
        try:
            import asyncio
            
            # 创建事件循环
            loop = asyncio.new_event_loop()
            asyncio.set_event_loop(loop)
            
            try:
                return loop.run_until_complete(self._async_synthesize_with_srt(text, voice_config, output_path))
            finally:
                loop.close()
                
        except Exception as e:
            self.logger.error(f"Edge TTS带字幕合成失败: {e}")
            raise
    
    async def _async_synthesize_with_srt(self, text: str, voice_config: VoiceConfig, output_path: str) -> str:
        """异步同时生成音频和SRT字幕文件"""
        try:
            self.logger.info(f"开始Edge TTS带字幕合成，语音: {voice_config.voice_name}")
            
            # 获取语音配置
            voice_name = voice_config.voice_name or 'zh-CN-XiaoxiaoNeural'
            
            # 检查语音是否存在
            if voice_name not in self._voices:
                # 尝试找到其他可用的中文语音
                chinese_voices = [v for v in self._voices.values() if v.language.startswith('zh')]
                if chinese_voices:
                    voice_name = chinese_voices[0].id
                    self.logger.warning(f"语音 '{voice_config.voice_name}' 不存在，使用中文语音: {voice_name}")
                    # 更新voice_config中的voice_name
                    voice_config.voice_name = voice_name
                else:
                    # 使用第一个可用语音
                    voice_name = list(self._voices.keys())[0]
                    self.logger.warning(f"语音 '{voice_config.voice_name}' 不存在，使用默认语音: {voice_name}")
                    # 更新voice_config中的voice_name
                    voice_config.voice_name = voice_name
            
            # 计算语速和音量
            rate_str = self.convert_rate_to_percentage(voice_config.rate)
            volume_str = self.convert_volume_to_percentage(voice_config.volume)
            
            # 创建TTS对象 - 使用纯文本和参数，避免SSML可能的问题
            communicate = edge_tts.Communicate(text, voice_name, rate=rate_str, volume=volume_str)
            
            # 创建字幕生成器
            submaker = edge_tts.SubMaker()
            
            # 生成SRT文件路径
            base_path = os.path.splitext(output_path)[0]
            srt_path = f"{base_path}.srt"
            
            # 合成音频并收集字幕数据
            audio_data = b""
            with open(output_path, "wb") as audio_file:
                async for chunk in communicate.stream():
                    if chunk["type"] == "audio":
                        audio_data += chunk["data"]
                        audio_file.write(chunk["data"])
                    elif chunk["type"] in ("WordBoundary", "SentenceBoundary"):
                        submaker.feed(chunk)
            
            # 保存SRT字幕文件
            with open(srt_path, "w", encoding="utf-8") as srt_file:
                srt_content = submaker.get_srt()
                srt_file.write(srt_content)
            
            self.logger.info(f"Edge TTS带字幕合成完成: {output_path}")
            self.logger.info(f"SRT字幕文件已生成: {srt_path}")
            
            # 检测音频格式并调整文件扩展名
            if audio_data:
                actual_format = self._detect_audio_format(audio_data)
                if actual_format != 'wav' and not output_path.endswith(f'.{actual_format}'):
                    # 如果实际格式不是WAV，调整输出文件扩展名
                    new_output_path = f"{base_path}.{actual_format}"
                    new_srt_path = f"{base_path}.srt"
                    
                    # 重命名音频文件
                    if os.path.exists(output_path):
                        os.rename(output_path, new_output_path)
                        self.logger.info(f"检测到音频格式为{actual_format}，调整输出文件为: {new_output_path}")
                        return new_output_path
            
            return output_path
            
        except Exception as e:
            self.logger.error(f"Edge TTS异步带字幕合成失败: {e}")
            raise
    
    def _generate_output_path(self, voice_config: VoiceConfig, output_config, text: str, chapter_info=None) -> str:
        """根据输出配置生成文件路径"""
        try:
            import tempfile
            import re
            import time
            
            # 获取输出目录
            output_dir = getattr(output_config, 'output_dir', tempfile.gettempdir())
            os.makedirs(output_dir, exist_ok=True)
            
            # 获取文件格式
            file_format = getattr(output_config, 'format', 'wav')
            if not file_format.startswith('.'):
                file_format = f'.{file_format}'
            
            # 获取命名模式
            naming_mode = getattr(output_config, 'naming_mode', '章节序号 + 标题')
            custom_template = getattr(output_config, 'custom_template', '{chapter_num:02d}_{title}')
            name_length_limit = getattr(output_config, 'name_length_limit', 50)
            
            # 生成文件名
            if naming_mode == "自定义":
                filename = self._apply_custom_template(custom_template, chapter_info, text)
            elif naming_mode == "章节序号 + 标题":
                filename = self._generate_chapter_title_name(chapter_info, text)
            elif naming_mode == "序号 + 标题":
                filename = self._generate_number_title_name(chapter_info, text)
            elif naming_mode == "仅标题":
                filename = self._generate_title_only_name(chapter_info, text)
            elif naming_mode == "仅序号":
                filename = self._generate_number_only_name(chapter_info, text)
            elif naming_mode == "原始文件名":
                filename = self._generate_original_filename(chapter_info, text)
            else:
                filename = f"edge_tts_{int(time.time())}"
            
            # 限制文件名长度
            if len(filename) > name_length_limit:
                filename = filename[:name_length_limit]
            
            # 清理文件名中的非法字符
            filename = re.sub(r'[<>:"|?*]', '_', filename)
            
            # 构建完整路径
            full_path = os.path.join(output_dir, f"{filename}{file_format}")
            
            return os.path.normpath(full_path)
            
        except Exception as e:
            self.logger.error(f"生成输出路径失败: {e}")
            # 返回默认路径
            return os.path.join(tempfile.gettempdir(), f"edge_tts_{int(time.time())}.wav")
    
    def _apply_custom_template(self, template: str, chapter_info, text: str) -> str:
        """应用自定义模板生成文件名"""
        try:
            # 获取文本前50个字符作为标题
            title = text[:50].strip()
            title = re.sub(r'[<>:"|?*]', '_', title)
            
            # 安全获取章节信息
            if chapter_info:
                if isinstance(chapter_info, dict):
                    chapter_num = chapter_info.get('chapter_num', 1)
                    voice_name = chapter_info.get('voice_name', 'edge_tts')
                else:
                    # 如果是对象，尝试获取属性
                    chapter_num = getattr(chapter_info, 'chapter_num', 1)
                    voice_name = getattr(chapter_info, 'voice_name', 'edge_tts')
            else:
                chapter_num = 1
                voice_name = 'edge_tts'
            
            # 替换模板变量
            filename = template.format(
                chapter_num=chapter_num,
                title=title,
                voice_name=voice_name,
                timestamp=int(time.time()),
                date=time.strftime('%Y%m%d'),
                time=time.strftime('%H%M%S')
            )
            
            return filename
            
        except Exception as e:
            self.logger.error(f"应用自定义模板失败: {e}")
            return f"edge_tts_{int(time.time())}"
    
    def _generate_chapter_title_name(self, chapter_info, text: str) -> str:
        """生成章节序号+标题格式的文件名"""
        try:
            if chapter_info:
                if isinstance(chapter_info, dict):
                    chapter_num = chapter_info.get('chapter_num', 1)
                else:
                    # 如果是对象，尝试获取属性
                    chapter_num = getattr(chapter_info, 'chapter_num', 1)
            else:
                chapter_num = 1
            
            title = text[:30].strip()
            title = re.sub(r'[<>:"|?*]', '_', title)
            return f"{chapter_num:02d}_{title}"
        except Exception as e:
            self.logger.error(f"生成章节标题文件名失败: {e}")
            return f"edge_tts_{int(time.time())}"
    
    def _generate_number_title_name(self, chapter_info, text: str) -> str:
        """生成序号+标题格式的文件名"""
        try:
            if chapter_info:
                if isinstance(chapter_info, dict):
                    chapter_num = chapter_info.get('chapter_num', 1)
                else:
                    # 如果是对象，尝试获取属性
                    chapter_num = getattr(chapter_info, 'chapter_num', 1)
            else:
                chapter_num = 1
            
            title = text[:30].strip()
            title = re.sub(r'[<>:"|?*]', '_', title)
            return f"{chapter_num}_{title}"
        except Exception as e:
            self.logger.error(f"生成序号标题文件名失败: {e}")
            return f"edge_tts_{int(time.time())}"
    
    def _generate_title_only_name(self, chapter_info, text: str) -> str:
        """生成仅标题格式的文件名"""
        try:
            title = text[:50].strip()
            title = re.sub(r'[<>:"|?*]', '_', title)
            return title
        except Exception as e:
            self.logger.error(f"生成标题文件名失败: {e}")
            return f"edge_tts_{int(time.time())}"
    
    def _generate_number_only_name(self, chapter_info, text: str) -> str:
        """生成仅序号格式的文件名"""
        try:
            if chapter_info:
                if isinstance(chapter_info, dict):
                    chapter_num = chapter_info.get('chapter_num', 1)
                else:
                    # 如果是对象，尝试获取属性
                    chapter_num = getattr(chapter_info, 'chapter_num', 1)
            else:
                chapter_num = 1
            
            return f"{chapter_num:02d}"
        except Exception as e:
            self.logger.error(f"生成序号文件名失败: {e}")
            return f"edge_tts_{int(time.time())}"
    
    def _generate_original_filename(self, chapter_info, text: str) -> str:
        """生成原始文件名格式的文件名"""
        try:
            if chapter_info:
                if isinstance(chapter_info, dict):
                    if 'original_filename' in chapter_info:
                        original_name = chapter_info['original_filename']
                        # 移除扩展名
                        name_without_ext = os.path.splitext(original_name)[0]
                        return name_without_ext
                else:
                    # 如果是对象，尝试获取属性
                    original_name = getattr(chapter_info, 'original_filename', None)
                    if original_name:
                        # 移除扩展名
                        name_without_ext = os.path.splitext(original_name)[0]
                        return name_without_ext
            
            return f"edge_tts_{int(time.time())}"
        except Exception as e:
            self.logger.error(f"生成原始文件名失败: {e}")
            return f"edge_tts_{int(time.time())}"
    
    def export_audio(self, audio_data: bytes, output_path: str, format: str = 'wav') -> str:
        """导出音频数据到文件"""
        try:
            # 确保输出目录存在
            os.makedirs(os.path.dirname(output_path), exist_ok=True)
            
            # 根据格式保存文件
            if format.lower() == 'wav':
                with open(output_path, 'wb') as f:
                    f.write(audio_data)
            elif format.lower() == 'mp3':
                # 需要转换为MP3格式
                self._convert_to_mp3(audio_data, output_path)
            else:
                # 默认保存为WAV
                with open(output_path, 'wb') as f:
                    f.write(audio_data)
            
            self.logger.info(f"音频导出成功: {output_path}")
            return output_path
            
        except Exception as e:
            self.logger.error(f"音频导出失败: {e}")
            raise
    
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
    
    def _convert_to_mp3(self, audio_data: bytes, output_path: str):
        """将WAV音频转换为MP3格式"""
        try:
            import tempfile
            import subprocess
            
            # 创建临时WAV文件
            with tempfile.NamedTemporaryFile(suffix='.wav', delete=False) as temp_wav:
                temp_wav.write(audio_data)
                temp_wav_path = temp_wav.name
            
            try:
                # 使用ffmpeg转换
                cmd = [
                    'ffmpeg', '-i', temp_wav_path, 
                    '-acodec', 'mp3', '-ab', '128k',
                    '-y', output_path
                ]
                
                result = subprocess.run(cmd, capture_output=True, text=True)
                if result.returncode != 0:
                    raise Exception(f"ffmpeg转换失败: {result.stderr}")
                
            finally:
                # 清理临时文件
                try:
                    os.unlink(temp_wav_path)
                except:
                    pass
                    
        except Exception as e:
            self.logger.error(f"MP3转换失败: {e}")
            # 如果转换失败，直接保存为WAV
            with open(output_path, 'wb') as f:
                f.write(audio_data)
