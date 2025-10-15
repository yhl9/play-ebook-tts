"""
TTS服务模块

提供多种TTS引擎的统一服务接口，包括：
- 多种TTS引擎支持：Edge TTS、Piper TTS、pyttsx3、EmotiVoice、IndexTTS
- 统一接口：所有引擎使用相同的调用方式
- 引擎管理：自动检测和加载可用的TTS引擎
- 错误处理：统一的异常处理和重试机制
- 性能优化：缓存、并发处理、进度监控

支持的TTS引擎：
- Edge TTS：微软在线TTS服务，支持多种语言
- Piper TTS：高质量本地TTS引擎，支持多语言
- pyttsx3：跨平台本地TTS引擎，使用系统语音
- EmotiVoice：支持情感控制的在线TTS服务
- IndexTTS：基于参考音频的语音克隆服务

作者: TTS开发团队
版本: 1.0.0
创建时间: 2024
"""

import asyncio
import io
import os
import tempfile
import socket
import subprocess
import requests
import json
import time
import wave
import re
from typing import List, Optional
from abc import ABC, abstractmethod

# 使用预加载的 Piper TTS
try:
    from utils.piper_preloader import PIPER_AVAILABLE, get_piper_status
    piper_status = get_piper_status()
    PIPER_AVAILABLE = piper_status['available']
    PiperVoice = piper_status['voice_class']
    SynthesisConfig = piper_status['config_class']
    if PIPER_AVAILABLE:
        print("✓ Piper TTS 从预加载模块导入成功")
    else:
        print("⚠️ Piper TTS 从预加载模块导入失败")
except Exception as e:
    PIPER_AVAILABLE = False
    PiperVoice = None
    SynthesisConfig = None
    print(f"⚠️ Piper TTS 预加载模块导入失败: {e}")
    print("Piper TTS 功能将不可用，但其他 TTS 引擎仍可正常使用")

import edge_tts
import pyttsx3
from PyQt6.QtCore import QObject, pyqtSignal

from models.audio_model import VoiceConfig
from utils.log_manager import LogManager
from utils.text_utils import TextUtils


class AudioGenerationError(Exception):
    """
    音频生成错误异常类
    
    当TTS引擎无法生成音频时抛出的自定义异常。
    包含详细的错误信息，便于调试和错误处理。
    """
    pass


class UnsupportedTTSEngineError(Exception):
    """不支持的TTS引擎错误"""
    pass


class ITTSService(ABC):
    """TTS服务抽象基类"""
    
    def __init__(self):
        self.logger = LogManager().get_logger(self.__class__.__name__)
        self._init_engine()
    
    @abstractmethod
    def _init_engine(self):
        """初始化TTS引擎"""
        pass
    
    @abstractmethod
    def synthesize(self, text: str, voice_config: VoiceConfig) -> bytes:
        """合成语音为字节数据"""
        pass
    
    @abstractmethod
    def synthesize_to_file(self, text: str, voice_config: VoiceConfig, output_path: str = None, output_config=None, chapter_info=None) -> str:
        """合成语音到文件"""
        pass
    
    @abstractmethod
    def get_available_voices(self) -> List[dict]:
        """获取可用语音列表"""
        pass
    
    @abstractmethod
    def is_available(self) -> bool:
        """检查引擎是否可用"""
        pass
    
    @abstractmethod
    def get_engine_name(self) -> str:
        """获取引擎名称"""
        pass
    
    @abstractmethod
    def get_engine_info(self) -> dict:
        """获取引擎信息"""
        pass


class TTSServiceFactory:
    """TTS服务工厂类"""
    
    _engines = {
        'piper_tts': None,  # 延迟导入
        'emotivoice_tts_api': None,  # 延迟导入
        'edge_tts': None,  # 延迟导入
        'pyttsx3': None,  # 延迟导入
        'index_tts_api_15': None  # 延迟导入
    }
    
    _engine_manager = None  # 引擎管理器
    
    @classmethod
    def get_engine_manager(cls):
        """获取引擎管理器"""
        if cls._engine_manager is None:
            from services.config.engine_manager import EngineManager
            cls._engine_manager = EngineManager()
        return cls._engine_manager
    
    @classmethod
    def get_available_engines(cls) -> List[str]:
        """获取可用的引擎列表"""
        available_engines = []
        
        for engine_id in cls._engines.keys():
            try:
                if cls.is_engine_available(engine_id):
                    available_engines.append(engine_id)
            except Exception as e:
                print(f"检查引擎 {engine_id} 可用性时出错: {e}")
                continue
        
        return available_engines
    
    @classmethod
    def is_engine_available(cls, engine_id: str) -> bool:
        """检查指定引擎是否可用"""
        try:
            # 使用新的引擎架构检查
            engine_class_map = {
                'piper_tts': 'services.piper_tts_engine.PiperTTSEngine',
                'emotivoice_tts_api': 'services.emotivoice_engine.EmotiVoiceEngine',
                'edge_tts': 'services.edge_tts_engine.EdgeTTSEngine',
                'pyttsx3': 'services.pyttsx3_engine.Pyttsx3Engine',
                'index_tts_api_15': 'services.index_tts_engine.IndexTTSEngine'
            }
            
            if engine_id not in engine_class_map:
                return False
            
            # 动态导入引擎类
            module_path, class_name = engine_class_map[engine_id].rsplit('.', 1)
            module = __import__(module_path, fromlist=[class_name])
            engine_class = getattr(module, class_name)
            
            # 创建引擎实例并检查可用性
            engine = engine_class()
            return engine.is_available()
            
        except Exception as e:
            print(f"检查引擎 {engine_id} 可用性失败: {e}")
            return False
    
    @classmethod
    def create_service(cls, engine_id: str, **kwargs):
        """创建TTS服务实例"""
        try:
            # 使用新的引擎架构
            engine_class_map = {
                'piper_tts': 'services.piper_tts_engine.PiperTTSEngine',
                'emotivoice_tts_api': 'services.emotivoice_engine.EmotiVoiceEngine',
                'edge_tts': 'services.edge_tts_engine.EdgeTTSEngine',
                'pyttsx3': 'services.pyttsx3_engine.Pyttsx3Engine',
                'index_tts_api_15': 'services.index_tts_engine.IndexTTSEngine'
            }
            
            if engine_id not in engine_class_map:
                raise UnsupportedTTSEngineError(f"不支持的TTS引擎: {engine_id}")
            
            # 动态导入引擎类
            module_path, class_name = engine_class_map[engine_id].rsplit('.', 1)
            module = __import__(module_path, fromlist=[class_name])
            engine_class = getattr(module, class_name)
            
            # 创建引擎实例
            engine = engine_class(**kwargs)
            
            # 使用适配器包装引擎
            from services.tts_engine_adapter import TTSEngineAdapter
            return TTSEngineAdapter(engine)
            
        except Exception as e:
            raise UnsupportedTTSEngineError(f"创建TTS服务失败: {e}")


class TTSService(ITTSService):
    """统一TTS服务"""
    
    def __init__(self, engine_id: str = 'edge_tts', **kwargs):
        self.engine_id = engine_id
        self._current_service = None
        super().__init__()
    
    def _init_engine(self):
        """初始化TTS引擎"""
        try:
            self._current_service = TTSServiceFactory.create_service(self.engine_id)
            self.logger.info(f"TTS服务初始化成功，引擎: {self.engine_id}")
        except Exception as e:
            self.logger.error(f"TTS服务初始化失败: {e}")
            raise
    
    def synthesize(self, text: str, voice_config: VoiceConfig) -> bytes:
        """合成语音为字节数据"""
        if not self._current_service:
            raise AudioGenerationError("TTS服务未初始化")
        
        return self._current_service.synthesize(text, voice_config)
    
    def synthesize_to_file(self, text: str, voice_config: VoiceConfig, output_path: str = None, output_config=None, chapter_info=None) -> str:
        """合成语音到文件"""
        if not self._current_service:
            raise AudioGenerationError("TTS服务未初始化")
        
        return self._current_service.synthesize_to_file(text, voice_config, output_path, output_config, chapter_info)
    
    def synthesize_text(self, text: str, voice_config: VoiceConfig, output_path: str = None, output_config=None, chapter_info=None) -> str:
        """合成文本为音频文件（兼容旧接口）"""
        return self.synthesize_to_file(text, voice_config, output_path, output_config, chapter_info)
    
    def get_available_voices(self) -> List[dict]:
        """获取可用语音列表"""
        if not self._current_service:
            return []
        
        return self._current_service.get_available_voices()
    
    def is_available(self) -> bool:
        """检查引擎是否可用"""
        if not self._current_service:
            return False
        
        return self._current_service.is_available()
    
    def get_engine_name(self) -> str:
        """获取引擎名称"""
        if not self._current_service:
            return "Unknown"
        
        return self._current_service.get_engine_name()
    
    def get_engine_info(self) -> dict:
        """获取引擎信息"""
        if not self._current_service:
            return {
                'name': 'Unknown',
                'description': 'TTS引擎未初始化',
                'available': False,
                'online': False,
                'voice_count': 0
            }
        
        return self._current_service.get_engine_info()
    
    def switch_engine(self, engine_id: str, **kwargs):
        """切换TTS引擎"""
        try:
            self.engine_id = engine_id
            self._current_service = TTSServiceFactory.create_service(engine_id, **kwargs)
            self.logger.info(f"TTS引擎切换成功: {engine_id}")
        except Exception as e:
            self.logger.error(f"TTS引擎切换失败: {e}")
            raise
