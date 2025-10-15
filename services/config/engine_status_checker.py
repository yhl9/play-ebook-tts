"""
引擎状态检查器

提供TTS引擎的可用性检查功能，包括：
- 引擎连接测试
- 引擎功能验证
- 引擎性能监控
- 引擎状态报告

作者: TTS开发团队
版本: 2.0.0
创建时间: 2024
"""

import asyncio
import subprocess
import requests
import time
import os
from typing import Dict, Any, List, Optional, Tuple
from pathlib import Path
from models.config_models import EngineConfig, EngineStatusEnum
from utils.log_manager import LogManager


class EngineStatusChecker:
    """
    引擎状态检查器
    
    提供TTS引擎的可用性检查功能，包括连接测试、功能验证等。
    支持同步和异步检查模式。
    """
    
    def __init__(self):
        self.logger = LogManager().get_logger("EngineStatusChecker")
        self.check_timeout = 10  # 检查超时时间（秒）
        self.check_results = {}  # 检查结果缓存
    
    def check_engine_status(self, engine_id: str, engine_config: EngineConfig) -> Tuple[bool, str, Dict[str, Any]]:
        """
        检查引擎状态
        
        Args:
            engine_id (str): 引擎ID
            engine_config (EngineConfig): 引擎配置
            
        Returns:
            Tuple[bool, str, Dict[str, Any]]: (是否可用, 状态信息, 详细信息)
        """
        try:
            self.logger.info(f"开始检查引擎状态: {engine_id}")
            
            # 根据引擎类型选择检查方法
            if engine_id == "piper_tts":
                return self._check_piper_tts(engine_config)
            elif engine_id == "emotivoice_tts_api":
                return self._check_emotivoice(engine_config)
            elif engine_id == "pyttsx3":
                return self._check_pyttsx3(engine_config)
            elif engine_id == "index_tts_api_15":
                return self._check_index_tts(engine_config)
            else:
                return False, "不支持的引擎类型", {}
                
        except Exception as e:
            self.logger.error(f"检查引擎状态失败 {engine_id}: {e}")
            return False, f"检查失败: {e}", {}
    
    def _check_piper_tts(self, engine_config: EngineConfig) -> Tuple[bool, str, Dict[str, Any]]:
        """检查Piper TTS状态"""
        try:
            # 检查Piper TTS是否可用
            from utils.piper_preloader import PIPER_AVAILABLE, get_piper_status
            
            if not PIPER_AVAILABLE:
                return False, "Piper TTS未安装或不可用", {}
            
            # 检查模型文件
            model_path = engine_config.parameters.extra_params.get('model_path', '')
            if model_path and not os.path.exists(model_path):
                return False, f"模型文件不存在: {model_path}", {}
            
            # 尝试创建PiperVoice实例
            try:
                from piper import PiperVoice
                if model_path and os.path.exists(model_path):
                    voice = PiperVoice.load(model_path)
                    voice.close()
                
                return True, "Piper TTS可用", {
                    "model_path": model_path,
                    "status": "available"
                }
            except Exception as e:
                return False, f"Piper TTS初始化失败: {e}", {}
                
        except Exception as e:
            return False, f"Piper TTS检查失败: {e}", {}
    
    def _check_emotivoice(self, engine_config: EngineConfig) -> Tuple[bool, str, Dict[str, Any]]:
        """检查EmotiVoice状态"""
        try:
            # 检查API端点
            api_base = engine_config.parameters.extra_params.get('api_base', 'http://localhost:8000')
            if not api_base:
                return False, "API端点未配置", {}
            
            # 测试API连接
            try:
                response = requests.get(f"{api_base}/v1/voices", timeout=self.check_timeout)
                if response.status_code == 200:
                    voices = response.json()
                    return True, "EmotiVoice API可用", {
                        "api_base": api_base,
                        "voices_count": len(voices) if isinstance(voices, list) else 0,
                        "status": "available"
                    }
                else:
                    return False, f"EmotiVoice API响应错误: {response.status_code}", {}
            except requests.exceptions.ConnectionError:
                return False, "EmotiVoice API连接失败", {}
            except requests.exceptions.Timeout:
                return False, "EmotiVoice API连接超时", {}
            except Exception as e:
                return False, f"EmotiVoice API检查失败: {e}", {}
                
        except Exception as e:
            return False, f"EmotiVoice检查失败: {e}", {}
    
    
    def _check_pyttsx3(self, engine_config: EngineConfig) -> Tuple[bool, str, Dict[str, Any]]:
        """检查pyttsx3状态"""
        try:
            # 检查pyttsx3是否可用
            try:
                import pyttsx3
                
                # 尝试初始化引擎
                engine = pyttsx3.init()
                voices = engine.getProperty('voices')
                engine.stop()
                
                return True, "pyttsx3可用", {
                    "voices_count": len(voices) if voices else 0,
                    "status": "available"
                }
                
            except ImportError:
                return False, "pyttsx3未安装", {}
            except Exception as e:
                return False, f"pyttsx3初始化失败: {e}", {}
                
        except Exception as e:
            return False, f"pyttsx3检查失败: {e}", {}
    
    def _check_index_tts(self, engine_config: EngineConfig) -> Tuple[bool, str, Dict[str, Any]]:
        """检查IndexTTS状态"""
        try:
            # 检查API端点
            api_base = engine_config.parameters.extra_params.get('api_base', 'http://localhost:8000')
            if not api_base:
                return False, "API端点未配置", {}
            
            # 测试API连接
            try:
                response = requests.get(f"{api_base}/v1/voices", timeout=self.check_timeout)
                if response.status_code == 200:
                    voices = response.json()
                    return True, "IndexTTS API可用", {
                        "api_base": api_base,
                        "voices_count": len(voices) if isinstance(voices, list) else 0,
                        "status": "available"
                    }
                else:
                    return False, f"IndexTTS API响应错误: {response.status_code}", {}
            except requests.exceptions.ConnectionError:
                return False, "IndexTTS API连接失败", {}
            except requests.exceptions.Timeout:
                return False, "IndexTTS API连接超时", {}
            except Exception as e:
                return False, f"IndexTTS API检查失败: {e}", {}
                
        except Exception as e:
            return False, f"IndexTTS检查失败: {e}", {}
    
    def check_all_engines(self, engine_configs: Dict[str, EngineConfig]) -> Dict[str, Dict[str, Any]]:
        """
        检查所有引擎状态
        
        Args:
            engine_configs (Dict[str, EngineConfig]): 引擎配置字典
            
        Returns:
            Dict[str, Dict[str, Any]]: 检查结果字典
        """
        results = {}
        
        for engine_id, engine_config in engine_configs.items():
            try:
                is_available, status_message, details = self.check_engine_status(engine_id, engine_config)
                
                results[engine_id] = {
                    "available": is_available,
                    "status_message": status_message,
                    "details": details,
                    "check_time": time.time(),
                    "status": "available" if is_available else "unavailable"
                }
                
                self.logger.info(f"引擎 {engine_id} 状态检查完成: {status_message}")
                
            except Exception as e:
                self.logger.error(f"检查引擎 {engine_id} 状态失败: {e}")
                results[engine_id] = {
                    "available": False,
                    "status_message": f"检查失败: {e}",
                    "details": {},
                    "check_time": time.time(),
                    "status": "error"
                }
        
        return results
    
    def get_engine_performance_metrics(self, engine_id: str, engine_config: EngineConfig) -> Dict[str, Any]:
        """
        获取引擎性能指标
        
        Args:
            engine_id (str): 引擎ID
            engine_config (EngineConfig): 引擎配置
            
        Returns:
            Dict[str, Any]: 性能指标字典
        """
        try:
            metrics = {
                "engine_id": engine_id,
                "check_time": time.time(),
                "response_time": 0,
                "memory_usage": 0,
                "cpu_usage": 0
            }
            
            # 根据引擎类型获取特定指标
            if engine_id == "piper_tts":
                metrics.update(self._get_piper_metrics(engine_config))
            elif engine_id == "emotivoice_tts_api":
                metrics.update(self._get_emotivoice_metrics(engine_config))
            
            return metrics
            
        except Exception as e:
            self.logger.error(f"获取引擎性能指标失败 {engine_id}: {e}")
            return {"error": str(e)}
    
    def _get_piper_metrics(self, engine_config: EngineConfig) -> Dict[str, Any]:
        """获取Piper TTS性能指标"""
        return {
            "model_loaded": False,
            "model_size": 0
        }
    
    def _get_emotivoice_metrics(self, engine_config: EngineConfig) -> Dict[str, Any]:
        """获取EmotiVoice性能指标"""
        return {
            "api_response_time": 0,
            "concurrent_requests": 0
        }
    
    
    def clear_cache(self):
        """清空检查结果缓存"""
        self.check_results.clear()
        self.logger.info("引擎状态检查缓存已清空")
