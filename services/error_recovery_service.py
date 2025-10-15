#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
错误恢复服务
提供统一的错误处理、恢复和降级机制
"""

from typing import Dict, Any, Optional, Callable, List, Tuple
from dataclasses import dataclass
from enum import Enum
import traceback
from utils.log_manager import LogManager


class ErrorSeverity(Enum):
    """错误严重级别"""
    LOW = "low"           # 低级别，可以忽略
    MEDIUM = "medium"     # 中级别，需要警告
    HIGH = "high"         # 高级别，需要降级
    CRITICAL = "critical" # 严重级别，需要停止


class RecoveryStrategy(Enum):
    """恢复策略"""
    IGNORE = "ignore"         # 忽略错误
    RETRY = "retry"           # 重试
    FALLBACK = "fallback"     # 回退到默认值
    SUBSTITUTE = "substitute" # 替换为替代方案
    ABORT = "abort"          # 中止操作


@dataclass
class ErrorContext:
    """错误上下文"""
    error_type: str
    error_message: str
    severity: ErrorSeverity
    component: str
    operation: str
    context_data: Dict[str, Any] = None
    recovery_strategy: RecoveryStrategy = RecoveryStrategy.FALLBACK
    max_retries: int = 3
    retry_delay: float = 1.0


@dataclass
class RecoveryResult:
    """恢复结果"""
    success: bool
    recovered_value: Any = None
    error_message: str = ""
    warnings: List[str] = None
    fallback_used: bool = False


class ErrorRecoveryService:
    """错误恢复服务"""
    
    def __init__(self):
        self.logger = LogManager().get_logger("ErrorRecoveryService")
        self.error_handlers: Dict[str, Callable] = {}
        self.recovery_strategies: Dict[str, RecoveryStrategy] = {}
        self.fallback_values: Dict[str, Any] = {}
        self._setup_default_handlers()
    
    def _setup_default_handlers(self):
        """设置默认错误处理器"""
        # 语音ID错误处理器
        self.error_handlers['voice_id_error'] = self._handle_voice_id_error
        self.recovery_strategies['voice_id_error'] = RecoveryStrategy.SUBSTITUTE
        
        # 配置错误处理器
        self.error_handlers['config_error'] = self._handle_config_error
        self.recovery_strategies['config_error'] = RecoveryStrategy.FALLBACK
        
        # 网络错误处理器
        self.error_handlers['network_error'] = self._handle_network_error
        self.recovery_strategies['network_error'] = RecoveryStrategy.RETRY
        
        # 引擎错误处理器
        self.error_handlers['engine_error'] = self._handle_engine_error
        self.recovery_strategies['engine_error'] = RecoveryStrategy.FALLBACK
    
    def handle_error(self, error_context: ErrorContext) -> RecoveryResult:
        """
        处理错误并尝试恢复
        
        Args:
            error_context: 错误上下文
            
        Returns:
            RecoveryResult: 恢复结果
        """
        try:
            self.logger.error(f"处理错误: {error_context.error_type} - {error_context.error_message}")
            
            # 获取错误处理器
            handler = self.error_handlers.get(error_context.error_type)
            if not handler:
                return self._default_error_handler(error_context)
            
            # 执行恢复策略
            if error_context.recovery_strategy == RecoveryStrategy.IGNORE:
                return RecoveryResult(success=True, recovered_value=None)
            
            elif error_context.recovery_strategy == RecoveryStrategy.RETRY:
                return self._retry_operation(error_context, handler)
            
            elif error_context.recovery_strategy == RecoveryStrategy.FALLBACK:
                return self._fallback_recovery(error_context, handler)
            
            elif error_context.recovery_strategy == RecoveryStrategy.SUBSTITUTE:
                return self._substitute_recovery(error_context, handler)
            
            elif error_context.recovery_strategy == RecoveryStrategy.ABORT:
                return RecoveryResult(success=False, error_message="操作已中止")
            
            else:
                return self._default_error_handler(error_context)
                
        except Exception as e:
            self.logger.error(f"错误处理失败: {e}")
            return RecoveryResult(
                success=False,
                error_message=f"错误处理失败: {e}",
                warnings=[f"原始错误: {error_context.error_message}"]
            )
    
    def _handle_voice_id_error(self, error_context: ErrorContext) -> RecoveryResult:
        """处理语音ID错误"""
        try:
            from services.voice_mapping_service import voice_mapping_service
            
            # 从错误上下文中提取信息
            source_voice_id = error_context.context_data.get('source_voice_id', '')
            source_engine = error_context.context_data.get('source_engine', '')
            target_engine = error_context.context_data.get('target_engine', '')
            available_voices = error_context.context_data.get('available_voices', [])
            
            # 尝试语音映射
            mapping = voice_mapping_service.map_voice_id(
                source_voice_id, source_engine, target_engine, available_voices
            )
            
            if mapping.target_id and mapping.target_id != source_voice_id:
                return RecoveryResult(
                    success=True,
                    recovered_value=mapping.target_id,
                    warnings=[f"语音ID已映射: {source_voice_id} -> {mapping.target_id}"]
                )
            else:
                # 使用默认语音
                default_voice = self.fallback_values.get(f'{target_engine}_default_voice', 'default')
                return RecoveryResult(
                    success=True,
                    recovered_value=default_voice,
                    fallback_used=True,
                    warnings=[f"使用默认语音: {default_voice}"]
                )
                
        except Exception as e:
            self.logger.error(f"语音ID错误处理失败: {e}")
            return RecoveryResult(
                success=False,
                error_message=f"语音ID错误处理失败: {e}"
            )
    
    def _handle_config_error(self, error_context: ErrorContext) -> RecoveryResult:
        """处理配置错误"""
        try:
            from services.robust_config_service import robust_config_service
            
            engine = error_context.context_data.get('engine', 'unknown')
            config_data = error_context.context_data.get('config_data', {})
            
            # 创建安全的默认配置
            safe_config = robust_config_service.create_safe_voice_config(engine, **config_data)
            
            return RecoveryResult(
                success=True,
                recovered_value=safe_config,
                fallback_used=True,
                warnings=[f"使用安全默认配置: {engine}"]
            )
            
        except Exception as e:
            self.logger.error(f"配置错误处理失败: {e}")
            return RecoveryResult(
                success=False,
                error_message=f"配置错误处理失败: {e}"
            )
    
    def _handle_network_error(self, error_context: ErrorContext) -> RecoveryResult:
        """处理网络错误"""
        try:
            import time
            
            # 重试逻辑
            max_retries = error_context.max_retries
            retry_delay = error_context.retry_delay
            
            for attempt in range(max_retries):
                try:
                    # 这里应该调用原始操作
                    operation = error_context.context_data.get('operation')
                    if operation and callable(operation):
                        result = operation()
                        return RecoveryResult(
                            success=True,
                            recovered_value=result,
                            warnings=[f"重试成功 (第{attempt + 1}次)"]
                        )
                except Exception as e:
                    if attempt < max_retries - 1:
                        self.logger.warning(f"重试失败 (第{attempt + 1}次): {e}")
                        time.sleep(retry_delay)
                    else:
                        raise e
            
            return RecoveryResult(
                success=False,
                error_message="重试次数已用完"
            )
            
        except Exception as e:
            self.logger.error(f"网络错误处理失败: {e}")
            return RecoveryResult(
                success=False,
                error_message=f"网络错误处理失败: {e}"
            )
    
    def _handle_engine_error(self, error_context: ErrorContext) -> RecoveryResult:
        """处理引擎错误"""
        try:
            # 尝试切换到备用引擎
            current_engine = error_context.context_data.get('current_engine', '')
            available_engines = error_context.context_data.get('available_engines', [])
            
            # 查找备用引擎
            fallback_engines = ['edge_tts', 'pyttsx3', 'emotivoice_tts_api']
            for fallback_engine in fallback_engines:
                if fallback_engine != current_engine and fallback_engine in available_engines:
                    return RecoveryResult(
                        success=True,
                        recovered_value=fallback_engine,
                        fallback_used=True,
                        warnings=[f"切换到备用引擎: {fallback_engine}"]
                    )
            
            return RecoveryResult(
                success=False,
                error_message="没有可用的备用引擎"
            )
            
        except Exception as e:
            self.logger.error(f"引擎错误处理失败: {e}")
            return RecoveryResult(
                success=False,
                error_message=f"引擎错误处理失败: {e}"
            )
    
    def _retry_operation(self, error_context: ErrorContext, handler: Callable) -> RecoveryResult:
        """重试操作"""
        import time
        
        for attempt in range(error_context.max_retries):
            try:
                result = handler(error_context)
                if result.success:
                    return result
            except Exception as e:
                if attempt < error_context.max_retries - 1:
                    self.logger.warning(f"重试失败 (第{attempt + 1}次): {e}")
                    time.sleep(error_context.retry_delay)
                else:
                    return RecoveryResult(
                        success=False,
                        error_message=f"重试失败: {e}"
                    )
        
        return RecoveryResult(
            success=False,
            error_message="重试次数已用完"
        )
    
    def _fallback_recovery(self, error_context: ErrorContext, handler: Callable) -> RecoveryResult:
        """回退恢复"""
        try:
            result = handler(error_context)
            if result.success:
                result.fallback_used = True
            return result
        except Exception as e:
            return RecoveryResult(
                success=False,
                error_message=f"回退恢复失败: {e}"
            )
    
    def _substitute_recovery(self, error_context: ErrorContext, handler: Callable) -> RecoveryResult:
        """替换恢复"""
        try:
            result = handler(error_context)
            if result.success:
                result.warnings = result.warnings or []
                result.warnings.append("使用了替代方案")
            return result
        except Exception as e:
            return RecoveryResult(
                success=False,
                error_message=f"替换恢复失败: {e}"
            )
    
    def _default_error_handler(self, error_context: ErrorContext) -> RecoveryResult:
        """默认错误处理器"""
        return RecoveryResult(
            success=False,
            error_message=f"未知错误类型: {error_context.error_type}"
        )
    
    def register_error_handler(self, error_type: str, handler: Callable, 
                              strategy: RecoveryStrategy = RecoveryStrategy.FALLBACK):
        """注册错误处理器"""
        self.error_handlers[error_type] = handler
        self.recovery_strategies[error_type] = strategy
        self.logger.info(f"注册错误处理器: {error_type} -> {strategy.value}")
    
    def set_fallback_value(self, key: str, value: Any):
        """设置回退值"""
        self.fallback_values[key] = value
        self.logger.info(f"设置回退值: {key} = {value}")
    
    def create_error_context(self, error_type: str, error_message: str, 
                           severity: ErrorSeverity, component: str, operation: str,
                           **context_data) -> ErrorContext:
        """创建错误上下文"""
        strategy = self.recovery_strategies.get(error_type, RecoveryStrategy.FALLBACK)
        return ErrorContext(
            error_type=error_type,
            error_message=error_message,
            severity=severity,
            component=component,
            operation=operation,
            context_data=context_data,
            recovery_strategy=strategy
        )


# 全局错误恢复服务实例
error_recovery_service = ErrorRecoveryService()
