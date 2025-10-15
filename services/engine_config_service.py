#!/usr/bin/env python3
"""
引擎配置服务
管理每个TTS引擎的独立配置文件
"""

import os
import json
from pathlib import Path
from typing import Optional, Dict, Any

from models.audio_model import VoiceConfig
from utils.log_manager import LogManager


class EngineConfigService:
    """引擎配置管理服务"""
    
    def __init__(self, configs_dir: str = "configs"):
        self.logger = LogManager().get_logger("EngineConfigService")
        self.configs_dir = Path(configs_dir)
        
        # 确保配置目录存在
        self.configs_dir.mkdir(parents=True, exist_ok=True)
        
        # 支持的引擎列表
        self.supported_engines = ["edge_tts", "pyttsx3", "index_tts_api_15", "emotivoice_tts_api"]
    
    def get_engine_config_path(self, engine: str) -> Path:
        """获取引擎配置文件路径"""
        return self.configs_dir / f"{engine}.json"
    
    def load_engine_config(self, engine: str) -> VoiceConfig:
        """加载指定引擎的配置"""
        try:
            config_path = self.get_engine_config_path(engine)
            
            if not config_path.exists():
                self.logger.warning(f"引擎配置文件不存在: {config_path}")
                return self._create_default_config(engine)
            
            with open(config_path, 'r', encoding='utf-8') as f:
                config_data = json.load(f)
            
            # 创建VoiceConfig对象
            voice_config = VoiceConfig(
                engine=config_data.get('engine', engine),
                voice_name=config_data.get('voice_name', ''),
                rate=config_data.get('rate', 1.0),
                pitch=config_data.get('pitch', 0.0),
                volume=config_data.get('volume', 1.0),
                language=config_data.get('language', 'zh-CN'),
                output_format=config_data.get('output_format', 'wav'),
                extra_params=config_data.get('extra_params', {})
            )
            
            self.logger.info(f"引擎配置加载成功: {engine}")
            return voice_config
            
        except Exception as e:
            self.logger.error(f"加载引擎配置失败: {engine}, {e}")
            return self._create_default_config(engine)
    
    def save_engine_config(self, engine: str, voice_config: VoiceConfig):
        """保存指定引擎的配置"""
        try:
            config_path = self.get_engine_config_path(engine)
            
            # 准备配置数据
            config_data = {
                'engine': voice_config.engine,
                'voice_name': voice_config.voice_name,
                'rate': voice_config.rate,
                'pitch': voice_config.pitch,
                'volume': voice_config.volume,
                'language': voice_config.language,
                'output_format': voice_config.output_format,
                'extra_params': getattr(voice_config, 'extra_params', {})
            }
            
            # 保存到文件
            with open(config_path, 'w', encoding='utf-8') as f:
                json.dump(config_data, f, ensure_ascii=False, indent=2)
            
            self.logger.info(f"引擎配置保存成功: {engine}")
            
        except Exception as e:
            self.logger.error(f"保存引擎配置失败: {engine}, {e}")
            raise
    
    def get_current_engine(self) -> str:
        """获取当前选择的引擎"""
        try:
            from services.json_config_service import JsonConfigService
            config_service = JsonConfigService()
            
            # 确保配置文件已加载
            if not config_service.config_data:
                config_service.load_config()
            
            voice_settings = config_service.config_data.get('voice_settings', {})
            current_engine = voice_settings.get('current_engine', 'edge_tts')
            
            self.logger.info(f"当前引擎: {current_engine}")
            return current_engine
            
        except Exception as e:
            self.logger.error(f"获取当前引擎失败: {e}")
            return 'edge_tts'
    
    def set_current_engine(self, engine: str):
        """设置当前选择的引擎"""
        try:
            from services.json_config_service import JsonConfigService
            config_service = JsonConfigService()
            
            # 确保配置文件已加载
            if not config_service.config_data:
                config_service.load_config()
            
            # 更新当前引擎
            if 'voice_settings' not in config_service.config_data:
                config_service.config_data['voice_settings'] = {}
            
            config_service.config_data['voice_settings']['current_engine'] = engine
            
            # 保存到文件
            config_service.config_file.parent.mkdir(parents=True, exist_ok=True)
            with open(config_service.config_file, 'w', encoding='utf-8') as f:
                json.dump(config_service.config_data, f, ensure_ascii=False, indent=2)
            
            self.logger.info(f"当前引擎设置成功: {engine}")
            
        except Exception as e:
            self.logger.error(f"设置当前引擎失败: {e}")
            raise
    
    def _create_default_config(self, engine: str) -> VoiceConfig:
        """创建默认配置"""
        try:
            if engine == "edge_tts":
                return VoiceConfig(
                    engine="edge_tts",
                    voice_name="zh-CN-XiaoxiaoNeural",
                    rate=1.0,
                    pitch=0.0,
                    volume=1.0,
                    language="zh-CN",
                    output_format="wav",
                    extra_params={}
                )
            elif engine == "pyttsx3":
                return VoiceConfig(
                    engine="pyttsx3",
                    voice_name="default",
                    rate=1.0,
                    pitch=0.0,
                    volume=1.0,
                    language="zh-CN",
                    output_format="wav",
                    extra_params={}
                )
            elif engine == "index_tts_api_15":
                return VoiceConfig(
                    engine="index_tts_api_15",
                    voice_name="zh-kangHuiRead",
                    rate=1.0,
                    pitch=0.0,
                    volume=1.0,
                    language="zh-CN",
                    output_format="wav",
                    extra_params={
                        "voice_name": "zh-kangHuiRead",
                        "prompt_audio": "resources/audio/index-tts-zh-kangHuiRead.mp3",
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
                    }
                )
            elif engine == "emotivoice_tts_api":
                return VoiceConfig(
                    engine="emotivoice_tts_api",
                    voice_name="8051",  # EmotiVoice TTS API 默认语音
                    rate=1.0,
                    pitch=0.0,
                    volume=1.0,
                    language="zh-CN",
                    output_format="wav",
                    emotion="自然",  # EmotiVoice 默认情感
                    extra_params={
                        "api_base": "http://localhost:8000",
                        "timeout": 30,
                        "max_retries": 3,
                        "sample_rate": "22050",
                        "bit_depth": "16",
                        "normalize_audio": True,
                        "enable_caching": True,
                        "cache_duration": 3600,
                        "max_cache_size": 100,
                        "concurrent_requests": 3
                    }
                )
            else:
                # 默认配置
                return VoiceConfig(
                    engine=engine,
                    voice_name="default",
                    rate=1.0,
                    pitch=0.0,
                    volume=1.0,
                    language="zh-CN",
                    output_format="wav",
                    extra_params={}
                )
                
        except Exception as e:
            self.logger.error(f"创建默认配置失败: {engine}, {e}")
            return VoiceConfig()
    
    def list_available_engines(self) -> list:
        """列出可用的引擎"""
        available_engines = []
        
        for engine in self.supported_engines:
            config_path = self.get_engine_config_path(engine)
            if config_path.exists():
                available_engines.append(engine)
        
        return available_engines
    
    def migrate_from_old_config(self, old_voice_config: VoiceConfig):
        """从旧配置迁移到新结构"""
        try:
            engine = old_voice_config.engine
            self.logger.info(f"开始迁移配置: {engine}")
            
            # 保存到新的引擎配置文件
            self.save_engine_config(engine, old_voice_config)
            
            # 设置当前引擎
            self.set_current_engine(engine)
            
            self.logger.info(f"配置迁移完成: {engine}")
            
        except Exception as e:
            self.logger.error(f"配置迁移失败: {e}")
            raise


# 测试函数
def test_engine_config_service():
    """测试引擎配置服务"""
    print("=== 测试引擎配置服务 ===")
    
    service = EngineConfigService()
    
    # 测试获取当前引擎
    current_engine = service.get_current_engine()
    print(f"当前引擎: {current_engine}")
    
    # 测试加载引擎配置
    for engine in ["edge_tts", "pyttsx3", "index_tts_api_15"]:
        config = service.load_engine_config(engine)
        print(f"{engine} 配置: {config.engine}, {config.voice_name}")
    
    # 测试列出可用引擎
    available = service.list_available_engines()
    print(f"可用引擎: {available}")

if __name__ == "__main__":
    test_engine_config_service()
