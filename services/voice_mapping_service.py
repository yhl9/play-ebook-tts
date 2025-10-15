#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
语音ID映射服务
提供统一的语音ID映射和转换功能，确保不同引擎间的语音选择兼容性
"""

from typing import Dict, List, Optional, Tuple
from dataclasses import dataclass
from enum import Enum
from utils.log_manager import LogManager


class VoiceMappingStrategy(Enum):
    """语音映射策略"""
    EXACT_MATCH = "exact_match"  # 精确匹配
    FUZZY_MATCH = "fuzzy_match"  # 模糊匹配
    FALLBACK = "fallback"        # 回退到默认
    AUTO_MAP = "auto_map"        # 自动映射


@dataclass
class VoiceMapping:
    """语音映射信息"""
    source_id: str
    target_id: str
    confidence: float = 1.0
    strategy: VoiceMappingStrategy = VoiceMappingStrategy.EXACT_MATCH


class VoiceMappingService:
    """语音ID映射服务"""
    
    def __init__(self):
        self.logger = LogManager().get_logger("VoiceMappingService")
        self.mappings: Dict[str, Dict[str, str]] = {}
        self.fallback_voices: Dict[str, str] = {}
        self._load_default_mappings()
    
    def _load_default_mappings(self):
        """加载默认语音映射"""
        # Edge TTS -> EmotiVoice TTS API 映射
        self.mappings['edge_tts_to_emotivoice_tts_api'] = {
            'zh-CN-XiaoxiaoNeural': '8051',
            'zh-CN-YunxiNeural': '8051',
            'zh-CN-YunyangNeural': '8051',
            'zh-CN-XiaoyiNeural': '8051',
            'zh-CN-YunjianNeural': '8051',
            'zh-CN-XiaochenNeural': '8051',
            'zh-CN-XiaohanNeural': '8051',
            'zh-CN-XiaomengNeural': '8051',
            'zh-CN-XiaomoNeural': '8051',
            'zh-CN-XiaoqiuNeural': '8051',
            'zh-CN-XiaoruiNeural': '8051',
            'zh-CN-XiaoshuangNeural': '8051',
            'zh-CN-XiaoxuanNeural': '8051',
            'zh-CN-XiaoyanNeural': '8051',
            'zh-CN-XiaoyouNeural': '8051',
            'zh-CN-XiaozhenNeural': '8051',
            'zh-CN-YunfengNeural': '8051',
            'zh-CN-YunhaoNeural': '8051',
            'en-US-AriaNeural': '8051',
            'en-US-GuyNeural': '8051',
            'en-US-JennyNeural': '8051',
            'en-US-DavisNeural': '8051',
            'en-US-EmmaNeural': '8051',
            'en-US-BrianNeural': '8051',
            'en-US-AvaNeural': '8051',
        }
        
        # Edge TTS -> Piper TTS 映射
        self.mappings['edge_tts_to_piper'] = {
            'zh-CN-XiaoxiaoNeural': 'zh_CN-huayan-medium',
            'zh-CN-YunxiNeural': 'zh_CN-huayan-medium',
            'zh-CN-YunyangNeural': 'zh_CN-huayan-medium',
            'zh-CN-XiaoyiNeural': 'zh_CN-huayan-medium',
            'zh-CN-YunjianNeural': 'zh_CN-huayan-medium',
            'zh-CN-XiaochenNeural': 'zh_CN-huayan-medium',
            'zh-CN-XiaohanNeural': 'zh_CN-huayan-medium',
            'zh-CN-XiaomengNeural': 'zh_CN-huayan-medium',
            'zh-CN-XiaomoNeural': 'zh_CN-huayan-medium',
            'zh-CN-XiaoqiuNeural': 'zh_CN-huayan-medium',
            'zh-CN-XiaoruiNeural': 'zh_CN-huayan-medium',
            'zh-CN-XiaoshuangNeural': 'zh_CN-huayan-medium',
            'zh-CN-XiaoxuanNeural': 'zh_CN-huayan-medium',
            'zh-CN-XiaoyanNeural': 'zh_CN-huayan-medium',
            'zh-CN-XiaoyouNeural': 'zh_CN-huayan-medium',
            'zh-CN-XiaozhenNeural': 'zh_CN-huayan-medium',
            'zh-CN-YunfengNeural': 'zh_CN-huayan-medium',
            'zh-CN-YunhaoNeural': 'zh_CN-huayan-medium',
            'en-US-AriaNeural': 'en_GB-alan-medium',
            'en-US-DavisNeural': 'en_GB-alan-medium',
            'en-US-EmmaNeural': 'en_GB-alan-medium',
            'en-US-GuyNeural': 'en_GB-alan-medium',
            'en-US-JennyNeural': 'en_GB-alan-medium',
            'en-US-BrianNeural': 'en_GB-alan-medium',
            'en-US-AvaNeural': 'en_GB-alan-medium',
        }
        
        # Piper TTS -> EmotiVoice TTS API 映射
        self.mappings['piper_tts_to_emotivoice_tts_api'] = {
            'zh_CN-huayan-medium': '8051',
            'en_US-amy-medium': '8051',
            'en_GB-alan-medium': '8051',
        }
        
        # Piper TTS -> Edge TTS 映射
        self.mappings['piper_tts_to_edge_tts'] = {
            'zh_CN-huayan-medium': 'zh-CN-XiaoxiaoNeural',
            'en_US-amy-medium': 'en-US-AriaNeural',
            'en_GB-alan-medium': 'en-GB-SoniaNeural',
        }
        
        # Piper TTS -> IndexTTS API 1.5 映射
        self.mappings['piper_tts_to_index_tts_api_15'] = {
            'zh_CN-huayan-medium': 'index-tts-zh-sampling',
            'en_US-amy-medium': 'index-tts-zh-sampling',  # 映射到实际存在的语音
            'en_GB-alan-medium': 'index-tts-zh-sampling',  # 映射到实际存在的语音
        }
        
        # 设置回退语音
        self.fallback_voices = {
            'edge_tts': 'zh-CN-XiaoxiaoNeural',
            'emotivoice_tts_api': '8051',
            'piper_tts': 'zh_CN-huayan-medium',
            'pyttsx3': 'default',
            'index_tts_api_15': 'index-tts-zh-kangHuiRead',
        }
    
    def map_voice_id(self, source_voice_id: str, source_engine: str, target_engine: str, 
                    available_voices: Optional[List[Dict]] = None) -> VoiceMapping:
        """
        映射语音ID
        
        Args:
            source_voice_id: 源语音ID
            source_engine: 源引擎
            target_engine: 目标引擎
            available_voices: 目标引擎的可用语音列表
            
        Returns:
            VoiceMapping: 映射结果
        """
        try:
            # 如果源引擎和目标引擎相同，直接返回
            if source_engine == target_engine:
                return VoiceMapping(
                    source_id=source_voice_id,
                    target_id=source_voice_id,
                    confidence=1.0,
                    strategy=VoiceMappingStrategy.EXACT_MATCH
                )
            
            # 构建映射键
            mapping_key = f"{source_engine}_to_{target_engine}"
            
            # 尝试精确映射
            if mapping_key in self.mappings:
                if source_voice_id in self.mappings[mapping_key]:
                    target_id = self.mappings[mapping_key][source_voice_id]
                    
                    # 验证目标语音是否存在
                    if available_voices:
                        if self._is_voice_available(target_id, available_voices):
                            return VoiceMapping(
                                source_id=source_voice_id,
                                target_id=target_id,
                                confidence=1.0,
                                strategy=VoiceMappingStrategy.EXACT_MATCH
                            )
                        else:
                            self.logger.warning(f"映射的语音 {target_id} 在目标引擎中不可用")
                    else:
                        return VoiceMapping(
                            source_id=source_voice_id,
                            target_id=target_id,
                            confidence=1.0,
                            strategy=VoiceMappingStrategy.EXACT_MATCH
                        )
            
            # 尝试模糊匹配
            fuzzy_match = self._fuzzy_match_voice(source_voice_id, target_engine, available_voices)
            if fuzzy_match:
                return VoiceMapping(
                    source_id=source_voice_id,
                    target_id=fuzzy_match,
                    confidence=0.8,
                    strategy=VoiceMappingStrategy.FUZZY_MATCH
                )
            
            # 回退到默认语音
            fallback_id = self.fallback_voices.get(target_engine, 'default')
            return VoiceMapping(
                source_id=source_voice_id,
                target_id=fallback_id,
                confidence=0.5,
                strategy=VoiceMappingStrategy.FALLBACK
            )
            
        except Exception as e:
            self.logger.error(f"语音映射失败: {e}")
            # 最后的回退
            fallback_id = self.fallback_voices.get(target_engine, 'default')
            return VoiceMapping(
                source_id=source_voice_id,
                target_id=fallback_id,
                confidence=0.0,
                strategy=VoiceMappingStrategy.FALLBACK
            )
    
    def _is_voice_available(self, voice_id: str, available_voices: List[Dict]) -> bool:
        """检查语音是否可用"""
        for voice in available_voices:
            if voice.get('id') == voice_id or voice.get('name') == voice_id:
                return True
        return False
    
    def _fuzzy_match_voice(self, source_voice_id: str, target_engine: str, 
                          available_voices: Optional[List[Dict]]) -> Optional[str]:
        """模糊匹配语音"""
        if not available_voices:
            return None
        
        # 提取语言信息
        source_lang = self._extract_language(source_voice_id)
        
        # 在可用语音中查找相同语言的语音
        for voice in available_voices:
            voice_id = voice.get('id', '')
            voice_lang = self._extract_language(voice_id)
            
            if source_lang and voice_lang and source_lang == voice_lang:
                return voice_id
        
        return None
    
    def _extract_language(self, voice_id: str) -> Optional[str]:
        """从语音ID中提取语言信息"""
        if not voice_id:
            return None
        
        # 提取语言代码（如 zh-CN, en-US）
        if '-' in voice_id:
            parts = voice_id.split('-')
            if len(parts) >= 2:
                return f"{parts[0]}-{parts[1]}"
        
        # 提取语言前缀（如 zh, en）
        if '_' in voice_id:
            parts = voice_id.split('_')
            if len(parts) >= 2:
                return parts[0]
        
        return None
    
    def add_custom_mapping(self, source_engine: str, target_engine: str, 
                          source_voice_id: str, target_voice_id: str):
        """添加自定义映射"""
        mapping_key = f"{source_engine}_to_{target_engine}"
        if mapping_key not in self.mappings:
            self.mappings[mapping_key] = {}
        
        self.mappings[mapping_key][source_voice_id] = target_voice_id
        self.logger.info(f"添加自定义映射: {source_engine}.{source_voice_id} -> {target_engine}.{target_voice_id}")
    
    def get_mapping_info(self, source_engine: str, target_engine: str) -> Dict[str, str]:
        """获取映射信息"""
        mapping_key = f"{source_engine}_to_{target_engine}"
        return self.mappings.get(mapping_key, {})
    
    def validate_voice_mapping(self, source_engine: str, target_engine: str, 
                              available_voices: List[Dict]) -> Dict[str, bool]:
        """验证语音映射的有效性"""
        mapping_key = f"{source_engine}_to_{target_engine}"
        mappings = self.mappings.get(mapping_key, {})
        
        validation_results = {}
        for source_id, target_id in mappings.items():
            validation_results[source_id] = self._is_voice_available(target_id, available_voices)
        
        return validation_results


# 全局语音映射服务实例
voice_mapping_service = VoiceMappingService()
