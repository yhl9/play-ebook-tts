#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
TTS引擎配置管理系统
管理不同TTS引擎的配置参数和特有属性
"""

import json
import os
from typing import Dict, Any, List, Optional, Type
from dataclasses import dataclass, field
from pathlib import Path

from .base_tts_engine import BaseTTSEngine, TTSEngineType, TTSCommonParams
from utils.log_manager import LogManager


@dataclass
class TTSEngineConfig:
    """TTS引擎配置"""
    engine_id: str
    engine_name: str
    engine_type: TTSEngineType
    engine_class: str  # 引擎类的完整路径
    is_enabled: bool = True
    priority: int = 0  # 优先级，数字越小优先级越高
    
    # 通用参数默认值
    common_params: TTSCommonParams = field(default_factory=TTSCommonParams)
    
    # 引擎特有参数
    specific_params: Dict[str, Any] = field(default_factory=dict)
    
    # 依赖项
    dependencies: List[str] = field(default_factory=list)
    
    # 配置验证规则
    validation_rules: Dict[str, Any] = field(default_factory=dict)
    
    # 引擎描述
    description: str = ""
    version: str = "1.0.0"
    author: str = ""
    homepage: str = ""


class TTSEngineConfigManager:
    """TTS引擎配置管理器"""
    
    def __init__(self, config_dir: str = "configs/tts_engines"):
        self.config_dir = Path(config_dir)
        self.logger = LogManager().get_logger("TTSEngineConfigManager")
        
        # 确保配置目录存在
        self.config_dir.mkdir(parents=True, exist_ok=True)
        
        # 引擎配置缓存
        self._engine_configs: Dict[str, TTSEngineConfig] = {}
        self._loaded = False
        
        # 加载配置
        self._load_configs()
    
    def _load_configs(self):
        """加载所有引擎配置"""
        try:
            # 加载默认配置
            self._load_default_configs()
            
            # 加载用户配置
            self._load_user_configs()
            
            self._loaded = True
            self.logger.info(f"加载了 {len(self._engine_configs)} 个TTS引擎配置")
            
        except Exception as e:
            self.logger.error(f"加载TTS引擎配置失败: {e}")
            self._loaded = False
    
    def _load_default_configs(self):
        """加载默认引擎配置"""
        default_configs = {
            "edge_tts": TTSEngineConfig(
                engine_id="edge_tts",
                engine_name="Edge TTS",
                engine_type=TTSEngineType.ONLINE,
                engine_class="services.edge_tts_engine.EdgeTTSEngine",
                is_enabled=True,
                priority=1,
                common_params=TTSCommonParams(
                    voice_name="zh-CN-XiaoxiaoNeural",
                    rate=1.0,
                    volume=1.0,
                    language="zh-CN",
                    output_format="wav",
                    sample_rate=22050,
                    bit_depth=16,
                    channels=1
                ),
                specific_params={
                    "use_async": True,
                    "voice_style": "default",
                    "voice_role": "default"
                },
                dependencies=["edge-tts"],
                validation_rules={
                    "rate": {"min": 0.5, "max": 2.0},
                    "volume": {"min": 0.0, "max": 1.0},
                    "voice_name": {"required": True, "type": "string"}
                },
                description="微软Edge浏览器TTS引擎，支持多种语言和语音",
                version="1.0.0",
                author="Microsoft",
                homepage="https://github.com/rany2/edge-tts"
            ),
            
            "pyttsx3": TTSEngineConfig(
                engine_id="pyttsx3",
                engine_name="PyTTSx3",
                engine_type=TTSEngineType.OFFLINE,
                engine_class="services.pyttsx3_engine.Pyttsx3Engine",
                is_enabled=True,
                priority=2,
                common_params=TTSCommonParams(
                    voice_name="default",
                    rate=1.0,
                    volume=1.0,
                    language="zh-CN",
                    output_format="wav",
                    sample_rate=22050,
                    bit_depth=16,
                    channels=1
                ),
                specific_params={
                    "use_sapi": True,
                    "debug": False
                },
                dependencies=["pyttsx3"],
                validation_rules={
                    "rate": {"min": 0.1, "max": 3.0},
                    "volume": {"min": 0.0, "max": 1.0}
                },
                description="跨平台TTS库，支持Windows、macOS和Linux",
                version="1.0.0",
                author="Natesh M Bhat",
                homepage="https://github.com/nateshmbhat/pyttsx3"
            ),
            
            "piper_tts": TTSEngineConfig(
                engine_id="piper_tts",
                engine_name="Piper TTS",
                engine_type=TTSEngineType.OFFLINE,
                engine_class="services.piper_tts_engine.PiperTTSEngine",
                is_enabled=True,
                priority=3,
                common_params=TTSCommonParams(
                    voice_name="zh_CN-huayan-medium",
                    rate=1.0,
                    volume=1.0,
                    language="zh-CN",
                    output_format="wav",
                    sample_rate=22050,
                    bit_depth=16,
                    channels=1
                ),
                specific_params={
                    "models_dir": "models/piper",
                    "use_cuda": False,
                    "noise_scale": 0.667,
                    "length_scale": 1.0,
                    "noise_w": 0.8
                },
                dependencies=["piper-tts"],
                validation_rules={
                    "rate": {"min": 0.5, "max": 2.0},
                    "volume": {"min": 0.1, "max": 2.0},
                    "voice_name": {"required": True, "type": "string"}
                },
                description="高质量本地TTS引擎，支持多种语言和语音模型",
                version="1.0.0",
                author="Rhasspy",
                homepage="https://github.com/rhasspy/piper"
            ),
            
            "index_tts_api_15": TTSEngineConfig(
                engine_id="index_tts_api_15",
                engine_name="IndexTTS API 1.5",
                engine_type=TTSEngineType.ONLINE,
                engine_class="services.index_tts_engine.IndexTTSEngine",
                is_enabled=True,
                priority=4,
                common_params=TTSCommonParams(
                    voice_name="zh-kangHuiRead",
                    rate=1.0,
                    volume=1.0,
                    language="zh-CN",
                    output_format="wav",
                    sample_rate=22050,
                    bit_depth=16,
                    channels=1
                ),
                specific_params={
                    "api_url": "http://localhost:8000",
                    "prompt_audio": "",
                    "infer_mode": "普通推理",
                    "temperature": 1.0,
                    "top_p": 0.8,
                    "top_k": 30,
                    "repetition_penalty": 10.0,
                    "max_mel_tokens": 600,
                    "max_text_tokens_per_sentence": 120,
                    "sentences_bucket_max_size": 4,
                    "do_sample": True,
                    "length_penalty": 0.0,
                    "num_beams": 3
                },
                dependencies=["requests"],
                validation_rules={
                    "rate": {"min": 0.5, "max": 2.0},
                    "volume": {"min": 0.1, "max": 2.0},
                    "voice_name": {"required": True, "type": "string"},
                    "api_url": {"required": True, "type": "string"}
                },
                description="IndexTTS API 1.5版本，支持高质量中文语音合成",
                version="1.5.0",
                author="IndexTTS",
                homepage="https://github.com/IndexTTS/IndexTTS"
            ),
            
            "index_tts_api_15": TTSEngineConfig(
                engine_id="index_tts_api_15",
                engine_name="IndexTTS API",
                engine_type=TTSEngineType.ONLINE,
                engine_class="services.index_tts_engine.IndexTTSEngine",
                is_enabled=True,
                priority=3,
                common_params=TTSCommonParams(
                    voice_name="default",
                    rate=1.0,
                    volume=1.0,
                    language="zh-CN",
                    output_format="wav",
                    sample_rate=22050,
                    bit_depth=16,
                    channels=1
                ),
                specific_params={
                    "api_url": "http://127.0.0.1:18000",
                    "timeout": 30,
                    "max_retries": 3,
                    "retry_delay": 1.0,
                    "audio_dir": "resources/audio"
                },
                dependencies=["requests"],
                validation_rules={
                    "voice_name": {"required": True, "type": "string"},
                    "api_url": {"required": True, "type": "string"}
                },
                description="IndexTTS API服务，支持自定义语音克隆",
                version="1.0.0",
                author="IndexTTS",
                homepage="https://github.com/IndexTTS/IndexTTS"
            ),
            
            "emotivoice_tts_api": TTSEngineConfig(
                engine_id="emotivoice_tts_api",
                engine_name="EmotiVoice TTS API",
                engine_type=TTSEngineType.ONLINE,
                engine_class="services.emotivoice_engine.EmotiVoiceEngine",
                is_enabled=True,
                priority=4,
                common_params=TTSCommonParams(
                    voice_name="8051",
                    rate=1.0,
                    volume=1.0,
                    language="zh-CN",
                    output_format="wav",
                    sample_rate=22050,
                    bit_depth=16,
                    channels=1
                ),
                specific_params={
                    "api_base": "http://localhost:8000",
                    "api_endpoint": "/v1/audio/speech",
                    "emotion": "自然",
                    "timeout": 30,
                    "max_retries": 3,
                    "retry_delay": 1.0,
                    "sample_rate": "22050",
                    "bit_depth": "16",
                    "normalize_audio": True,
                    "enable_caching": True,
                    "cache_duration": 3600,
                    "max_cache_size": 100,
                    "concurrent_requests": 3
                },
                dependencies=["requests"],
                validation_rules={
                    "rate": {"min": 0.5, "max": 2.0},
                    "volume": {"min": 0.1, "max": 2.0},
                    "voice_name": {"required": True, "type": "string"},
                    "emotion": {"required": True, "type": "string"},
                    "api_base": {"required": True, "type": "string"}
                },
                description="基于OpenAI兼容API的EmotiVoice语音合成引擎",
                version="1.0.0",
                author="EmotiVoice",
                homepage="https://github.com/netease-youdao/EmotiVoice"
            )
        }
        
        for engine_id, config in default_configs.items():
            self._engine_configs[engine_id] = config
    
    def _load_user_configs(self):
        """加载用户自定义配置"""
        try:
            config_file = self.config_dir / "engines.json"
            if config_file.exists():
                with open(config_file, 'r', encoding='utf-8') as f:
                    user_configs = json.load(f)
                
                for engine_id, config_data in user_configs.items():
                    if engine_id in self._engine_configs:
                        # 更新现有配置
                        self._update_engine_config(engine_id, config_data)
                    else:
                        # 添加新配置
                        self._add_engine_config(engine_id, config_data)
                
                self.logger.info(f"加载了 {len(user_configs)} 个用户自定义配置")
                
        except Exception as e:
            self.logger.error(f"加载用户配置失败: {e}")
    
    def _update_engine_config(self, engine_id: str, config_data: Dict[str, Any]):
        """更新引擎配置"""
        try:
            config = self._engine_configs[engine_id]
            
            # 更新基本属性
            if 'engine_name' in config_data:
                config.engine_name = config_data['engine_name']
            if 'is_enabled' in config_data:
                config.is_enabled = config_data['is_enabled']
            if 'priority' in config_data:
                config.priority = config_data['priority']
            
            # 更新通用参数
            if 'common_params' in config_data:
                common_params_data = config_data['common_params']
                for key, value in common_params_data.items():
                    if hasattr(config.common_params, key):
                        setattr(config.common_params, key, value)
            
            # 更新特有参数
            if 'specific_params' in config_data:
                config.specific_params.update(config_data['specific_params'])
            
            self.logger.info(f"更新引擎配置: {engine_id}")
            
        except Exception as e:
            self.logger.error(f"更新引擎配置失败 {engine_id}: {e}")
    
    def _add_engine_config(self, engine_id: str, config_data: Dict[str, Any]):
        """添加新引擎配置"""
        try:
            # 这里可以添加新引擎配置的逻辑
            self.logger.info(f"添加新引擎配置: {engine_id}")
            
        except Exception as e:
            self.logger.error(f"添加引擎配置失败 {engine_id}: {e}")
    
    def get_engine_config(self, engine_id: str) -> Optional[TTSEngineConfig]:
        """获取指定引擎配置"""
        return self._engine_configs.get(engine_id)
    
    def get_all_engine_configs(self) -> Dict[str, TTSEngineConfig]:
        """获取所有引擎配置"""
        return self._engine_configs.copy()
    
    def get_enabled_engines(self) -> Dict[str, TTSEngineConfig]:
        """获取启用的引擎配置"""
        return {
            engine_id: config for engine_id, config in self._engine_configs.items()
            if config.is_enabled
        }
    
    def get_engines_by_type(self, engine_type: TTSEngineType) -> Dict[str, TTSEngineConfig]:
        """根据类型获取引擎配置"""
        return {
            engine_id: config for engine_id, config in self._engine_configs.items()
            if config.engine_type == engine_type and config.is_enabled
        }
    
    def get_engines_by_priority(self) -> List[TTSEngineConfig]:
        """按优先级获取引擎配置列表"""
        return sorted(
            [config for config in self._engine_configs.values() if config.is_enabled],
            key=lambda x: x.priority
        )
    
    def enable_engine(self, engine_id: str):
        """启用引擎"""
        if engine_id in self._engine_configs:
            self._engine_configs[engine_id].is_enabled = True
            self.logger.info(f"启用引擎: {engine_id}")
    
    def disable_engine(self, engine_id: str):
        """禁用引擎"""
        if engine_id in self._engine_configs:
            self._engine_configs[engine_id].is_enabled = False
            self.logger.info(f"禁用引擎: {engine_id}")
    
    def update_engine_config(self, engine_id: str, config: TTSEngineConfig):
        """更新引擎配置"""
        self._engine_configs[engine_id] = config
        self.logger.info(f"更新引擎配置: {engine_id}")
    
    def save_user_configs(self):
        """保存用户配置到文件"""
        try:
            config_file = self.config_dir / "engines.json"
            
            # 只保存用户修改的配置
            user_configs = {}
            for engine_id, config in self._engine_configs.items():
                # 这里可以添加逻辑来判断哪些配置是用户修改的
                user_configs[engine_id] = {
                    'engine_name': config.engine_name,
                    'is_enabled': config.is_enabled,
                    'priority': config.priority,
                    'common_params': config.common_params.__dict__,
                    'specific_params': config.specific_params
                }
            
            with open(config_file, 'w', encoding='utf-8') as f:
                json.dump(user_configs, f, ensure_ascii=False, indent=2)
            
            self.logger.info("用户配置保存成功")
            
        except Exception as e:
            self.logger.error(f"保存用户配置失败: {e}")
    
    def validate_engine_config(self, engine_id: str) -> bool:
        """验证引擎配置"""
        try:
            config = self._engine_configs.get(engine_id)
            if not config:
                return False
            
            # 验证基本属性
            if not config.engine_id or not config.engine_name:
                return False
            
            # 验证引擎类
            if not config.engine_class:
                return False
            
            # 验证通用参数
            common_params = config.common_params
            if not (0.1 <= common_params.rate <= 3.0):
                return False
            
            if not (0.0 <= common_params.volume <= 2.0):
                return False
            
            return True
            
        except Exception as e:
            self.logger.error(f"验证引擎配置失败 {engine_id}: {e}")
            return False
    
    def get_engine_dependencies(self, engine_id: str) -> List[str]:
        """获取引擎依赖项"""
        config = self._engine_configs.get(engine_id)
        return config.dependencies if config else []
    
    def check_dependencies(self, engine_id: str) -> Dict[str, bool]:
        """检查引擎依赖项是否满足"""
        dependencies = self.get_engine_dependencies(engine_id)
        results = {}
        
        for dep in dependencies:
            try:
                __import__(dep)
                results[dep] = True
            except ImportError:
                results[dep] = False
        
        return results
