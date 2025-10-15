#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
健壮的配置管理服务
提供统一的配置管理、验证和错误处理功能
"""

from typing import Dict, Any, Optional, List, Union
from dataclasses import dataclass, field
from enum import Enum
import json
import os
from pathlib import Path
from utils.log_manager import LogManager
from models.audio_model import VoiceConfig


class ConfigValidationLevel(Enum):
    """配置验证级别"""
    STRICT = "strict"      # 严格验证，任何错误都会抛出异常
    WARN = "warn"          # 警告级别，记录警告但继续执行
    IGNORE = "ignore"      # 忽略级别，静默处理错误


@dataclass
class ConfigValidationResult:
    """配置验证结果"""
    is_valid: bool
    errors: List[str] = field(default_factory=list)
    warnings: List[str] = field(default_factory=list)
    suggestions: List[str] = field(default_factory=list)


@dataclass
class EngineConfigTemplate:
    """引擎配置模板"""
    engine_id: str
    name: str
    description: str
    required_params: List[str] = field(default_factory=list)
    optional_params: Dict[str, Any] = field(default_factory=dict)
    default_voice_id: str = "default"
    fallback_voice_id: str = "default"
    validation_rules: Dict[str, Dict[str, Any]] = field(default_factory=dict)


class RobustConfigService:
    """健壮的配置管理服务"""
    
    def __init__(self, validation_level: ConfigValidationLevel = ConfigValidationLevel.WARN):
        self.logger = LogManager().get_logger("RobustConfigService")
        self.validation_level = validation_level
        self.config_templates: Dict[str, EngineConfigTemplate] = {}
        self._load_engine_templates()
    
    def _load_engine_templates(self):
        """加载引擎配置模板"""
        # Edge TTS 模板
        self.config_templates['edge_tts'] = EngineConfigTemplate(
            engine_id='edge_tts',
            name='Edge TTS',
            description='Microsoft Edge TTS 语音合成引擎',
            required_params=['voice_name'],
            optional_params={
                'rate': 1.0,
                'pitch': 0.0,
                'volume': 1.0,
                'language': 'zh-CN',
                'output_format': 'wav'
            },
            default_voice_id='zh-CN-XiaoxiaoNeural',
            fallback_voice_id='zh-CN-XiaoxiaoNeural',
            validation_rules={
                'voice_name': {
                    'type': 'string',
                    'required': True,
                    'pattern': r'^[a-zA-Z-]+$'
                },
                'rate': {
                    'type': 'number',
                    'min': 0.1,
                    'max': 3.0,
                    'default': 1.0
                },
                'volume': {
                    'type': 'number',
                    'min': 0.0,
                    'max': 2.0,
                    'default': 1.0
                }
            }
        )
        
        # EmotiVoice TTS API 模板
        self.config_templates['emotivoice_tts_api'] = EngineConfigTemplate(
            engine_id='emotivoice_tts_api',
            name='EmotiVoice TTS API',
            description='基于OpenAI兼容API的EmotiVoice语音合成引擎',
            required_params=['voice_name', 'emotion'],
            optional_params={
                'rate': 1.0,
                'pitch': 0.0,
                'volume': 1.0,
                'language': 'zh-CN',
                'output_format': 'wav',
                'api_base': 'http://localhost:8000',
                'timeout': 30,
                'max_retries': 3
            },
            default_voice_id='8051',
            fallback_voice_id='8051',
            validation_rules={
                'voice_name': {
                    'type': 'string',
                    'required': True,
                    'pattern': r'^\d+$'
                },
                'emotion': {
                    'type': 'string',
                    'required': True,
                    'options': ['开心', '兴奋', '平静', '悲伤', '生气', '自然']
                },
                'api_base': {
                    'type': 'string',
                    'pattern': r'^https?://.+',
                    'default': 'http://localhost:8000'
                }
            }
        )
        
        # Piper TTS 模板
        self.config_templates['piper_tts'] = EngineConfigTemplate(
            engine_id='piper_tts',
            name='Piper TTS',
            description='Piper 本地语音合成引擎',
            required_params=['voice_name'],
            optional_params={
                'rate': 1.0,
                'pitch': 0.0,
                'volume': 1.0,
                'language': 'zh-CN',
                'output_format': 'wav'
            },
            default_voice_id='zh_CN-huayan-medium',
            fallback_voice_id='zh_CN-huayan-medium',
            validation_rules={
                'voice_name': {
                    'type': 'string',
                    'required': True,
                    'pattern': r'^[a-zA-Z_]+$'
                }
            }
        )
    
    def create_safe_voice_config(self, engine: str, **kwargs) -> VoiceConfig:
        """
        创建安全的语音配置
        
        Args:
            engine: 引擎ID
            **kwargs: 配置参数
            
        Returns:
            VoiceConfig: 安全的语音配置
        """
        try:
            # 获取引擎模板
            template = self.config_templates.get(engine)
            if not template:
                self.logger.warning(f"未知引擎: {engine}，使用默认配置")
                return self._create_fallback_config(engine, **kwargs)
            
            # 验证和清理参数
            validated_params = self._validate_and_clean_params(engine, kwargs)
            
            # 创建配置
            config = VoiceConfig(
                engine=engine,
                voice_name=validated_params.get('voice_name', template.default_voice_id),
                rate=validated_params.get('rate', template.optional_params.get('rate', 1.0)),
                pitch=validated_params.get('pitch', template.optional_params.get('pitch', 0.0)),
                volume=validated_params.get('volume', template.optional_params.get('volume', 1.0)),
                language=validated_params.get('language', template.optional_params.get('language', 'zh-CN')),
                output_format=validated_params.get('output_format', template.optional_params.get('output_format', 'wav')),
                emotion=validated_params.get('emotion', template.optional_params.get('emotion', '自然')),
                extra_params={k: v for k, v in validated_params.items() 
                            if k not in ['voice_name', 'rate', 'pitch', 'volume', 'language', 'output_format', 'emotion']}
            )
            
            # 验证最终配置
            validation_result = self.validate_voice_config(config)
            if not validation_result.is_valid and self.validation_level == ConfigValidationLevel.STRICT:
                raise ValueError(f"配置验证失败: {validation_result.errors}")
            
            if validation_result.warnings:
                for warning in validation_result.warnings:
                    self.logger.warning(f"配置警告: {warning}")
            
            return config
            
        except Exception as e:
            self.logger.error(f"创建安全配置失败: {e}")
            return self._create_fallback_config(engine, **kwargs)
    
    def _validate_and_clean_params(self, engine: str, params: Dict[str, Any]) -> Dict[str, Any]:
        """验证和清理参数"""
        template = self.config_templates.get(engine)
        if not template:
            return params
        
        validated_params = {}
        validation_rules = template.validation_rules
        
        for key, value in params.items():
            if key in validation_rules:
                rule = validation_rules[key]
                validated_value = self._validate_parameter(key, value, rule)
                if validated_value is not None:
                    validated_params[key] = validated_value
            else:
                # 未知参数，直接添加
                validated_params[key] = value
        
        return validated_params
    
    def _validate_parameter(self, key: str, value: Any, rule: Dict[str, Any]) -> Any:
        """验证单个参数"""
        try:
            # 类型验证
            expected_type = rule.get('type')
            if expected_type == 'string' and not isinstance(value, str):
                if self.validation_level == ConfigValidationLevel.STRICT:
                    raise ValueError(f"参数 {key} 必须是字符串类型")
                self.logger.warning(f"参数 {key} 类型不匹配，期望字符串，实际 {type(value)}")
                value = str(value)
            elif expected_type == 'number' and not isinstance(value, (int, float)):
                if self.validation_level == ConfigValidationLevel.STRICT:
                    raise ValueError(f"参数 {key} 必须是数字类型")
                self.logger.warning(f"参数 {key} 类型不匹配，期望数字，实际 {type(value)}")
                try:
                    value = float(value)
                except (ValueError, TypeError):
                    value = rule.get('default', 0)
            
            # 范围验证
            if isinstance(value, (int, float)):
                if 'min' in rule and value < rule['min']:
                    value = rule['min']
                    self.logger.warning(f"参数 {key} 值过小，已调整为 {value}")
                if 'max' in rule and value > rule['max']:
                    value = rule['max']
                    self.logger.warning(f"参数 {key} 值过大，已调整为 {value}")
            
            # 模式验证
            if isinstance(value, str) and 'pattern' in rule:
                import re
                if not re.match(rule['pattern'], value):
                    if self.validation_level == ConfigValidationLevel.STRICT:
                        raise ValueError(f"参数 {key} 格式不正确")
                    self.logger.warning(f"参数 {key} 格式不正确，使用默认值")
                    value = rule.get('default', '')
            
            # 选项验证
            if 'options' in rule and value not in rule['options']:
                if self.validation_level == ConfigValidationLevel.STRICT:
                    raise ValueError(f"参数 {key} 值不在允许的选项中")
                self.logger.warning(f"参数 {key} 值不在允许的选项中，使用默认值")
                value = rule.get('default', rule['options'][0] if rule['options'] else '')
            
            return value
            
        except Exception as e:
            self.logger.error(f"验证参数 {key} 失败: {e}")
            return rule.get('default', None)
    
    def validate_voice_config(self, config: VoiceConfig) -> ConfigValidationResult:
        """验证语音配置"""
        result = ConfigValidationResult(is_valid=True)
        
        try:
            template = self.config_templates.get(config.engine)
            if not template:
                result.warnings.append(f"未知引擎: {config.engine}")
                return result
            
            # 验证必需参数
            for required_param in template.required_params:
                if not hasattr(config, required_param) or getattr(config, required_param) is None:
                    result.errors.append(f"缺少必需参数: {required_param}")
                    result.is_valid = False
            
            # 验证语音ID
            if hasattr(config, 'voice_name') and config.voice_name:
                if not isinstance(config.voice_name, str):
                    result.errors.append("voice_name 必须是字符串")
                    result.is_valid = False
                elif not config.voice_name.strip():
                    result.errors.append("voice_name 不能为空")
                    result.is_valid = False
            
            # 验证数值范围
            if hasattr(config, 'rate') and config.rate is not None:
                if not isinstance(config.rate, (int, float)) or config.rate <= 0:
                    result.errors.append("rate 必须是正数")
                    result.is_valid = False
            
            if hasattr(config, 'volume') and config.volume is not None:
                if not isinstance(config.volume, (int, float)) or config.volume < 0:
                    result.errors.append("volume 必须是非负数")
                    result.is_valid = False
            
        except Exception as e:
            result.errors.append(f"验证过程出错: {e}")
            result.is_valid = False
        
        return result
    
    def _create_fallback_config(self, engine: str, **kwargs) -> VoiceConfig:
        """创建回退配置"""
        template = self.config_templates.get(engine)
        if template:
            return VoiceConfig(
                engine=engine,
                voice_name=template.fallback_voice_id,
                rate=1.0,
                pitch=0.0,
                volume=1.0,
                language='zh-CN',
                output_format='wav',
                emotion='自然',
                extra_params={}
            )
        else:
            return VoiceConfig(
                engine=engine,
                voice_name='default',
                rate=1.0,
                pitch=0.0,
                volume=1.0,
                language='zh-CN',
                output_format='wav',
                emotion='自然',
                extra_params={}
            )
    
    def get_engine_template(self, engine: str) -> Optional[EngineConfigTemplate]:
        """获取引擎模板"""
        return self.config_templates.get(engine)
    
    def add_engine_template(self, template: EngineConfigTemplate):
        """添加引擎模板"""
        self.config_templates[template.engine_id] = template
        self.logger.info(f"添加引擎模板: {template.engine_id}")
    
    def get_safe_default_voice(self, engine: str) -> str:
        """获取安全的默认语音ID"""
        template = self.config_templates.get(engine)
        if template:
            return template.default_voice_id
        return 'default'


# 全局健壮配置服务实例
robust_config_service = RobustConfigService()
