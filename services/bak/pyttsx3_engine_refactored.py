#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
PyTTSx3 TTS引擎实现 - 重构版本
跨平台TTS库，支持Windows、macOS和Linux
简化版本，移除重复代码和冗余逻辑
"""

import os
import tempfile
import time
import threading
from typing import List, Dict, Any, Optional

import pyttsx3

# Windows注册表访问
try:
    import winreg
    WINDOWS_REGISTRY_AVAILABLE = True
except ImportError:
    WINDOWS_REGISTRY_AVAILABLE = False

from .base_tts_engine import BaseTTSEngine, TTSEngineType, TTSVoiceInfo, TTSQuality, TTSResult
from models.audio_model import VoiceConfig
from utils.log_manager import LogManager


class Pyttsx3Engine(BaseTTSEngine):
    """PyTTSx3 TTS引擎实现 - 重构版本"""
    
    def __init__(self, engine_id: str = "pyttsx3", engine_name: str = "PyTTSx3", 
                 engine_type: TTSEngineType = TTSEngineType.OFFLINE, **kwargs):
        # PyTTSx3特有参数
        self.use_sapi = kwargs.get('use_sapi', True)
        self.debug_mode = kwargs.get('debug', False)
        self.sample_rate = kwargs.get('sample_rate', '22050')
        self.bit_depth = kwargs.get('bit_depth', '16')
        
        # PyTTSx3引擎实例
        self._engine = None
        
        # 线程安全锁
        self._synthesis_lock = threading.Lock()
        
        # 调用父类初始化
        super().__init__(engine_id, engine_name, engine_type)
    
    def _load_engine(self):
        """加载PyTTSx3引擎"""
        try:
            # 创建PyTTSx3引擎实例
            self._engine = pyttsx3.init()
            
            if not self._engine:
                raise Exception("无法初始化PyTTSx3引擎")
            
            # 设置调试模式
            if self.debug_mode:
                self._engine.setProperty('debug', True)
            
            self.logger.info("PyTTSx3引擎加载成功")
            
        except Exception as e:
            self.logger.error(f"PyTTSx3引擎加载失败: {e}")
            raise
    
    def _load_voices(self):
        """加载PyTTSx3语音列表 - 简化版本"""
        try:
            # 首先尝试从Windows注册表读取语音信息
            registry_voices = self._load_voices_from_registry()
            
            if registry_voices:
                self.logger.info(f"从Windows注册表加载了 {len(registry_voices)} 个语音")
                self._voices.update(registry_voices)
            else:
                self.logger.info("Windows注册表语音加载失败，回退到pyttsx3引擎")
                # 回退到pyttsx3引擎获取语音
                self._load_voices_from_engine()
            
            # 如果仍然没有语音，添加默认语音
            if not self._voices:
                self._voices['default'] = TTSVoiceInfo(
                    id='default',
                    name='Default Voice',
                    language='en-US',
                    gender='unknown',
                    description='PyTTSx3默认语音',
                    engine=self.engine_id,
                    quality=TTSQuality.MEDIUM,
                    sample_rate=22050,
                    bit_depth=16,
                    channels=1
                )
            
            self.logger.info(f"总共加载了 {len(self._voices)} 个PyTTSx3语音")
            
        except Exception as e:
            self.logger.error(f"加载PyTTSx3语音失败: {e}")
            raise
    
    def _load_voices_from_registry(self) -> Dict[str, TTSVoiceInfo]:
        """从Windows注册表读取语音信息 - 简化版本"""
        voices = {}
        
        if not WINDOWS_REGISTRY_AVAILABLE:
            self.logger.warning("Windows注册表访问不可用，跳过注册表语音加载")
            return voices
        
        try:
            # 打开语音注册表键
            registry_path = r"SOFTWARE\Microsoft\Speech\Voices\Tokens"
            with winreg.OpenKey(winreg.HKEY_LOCAL_MACHINE, registry_path) as key:
                i = 0
                while True:
                    try:
                        # 枚举子键
                        voice_token = winreg.EnumKey(key, i)
                        voice_info = self._parse_voice_registry_entry(voice_token)
                        if voice_info:
                            voices[voice_info.id] = voice_info
                        i += 1
                    except OSError:
                        # 没有更多子键
                        break
                        
        except Exception as e:
            self.logger.warning(f"从Windows注册表读取语音失败: {e}")
            
        return voices
    
    def _parse_voice_registry_entry(self, voice_token: str) -> Optional[TTSVoiceInfo]:
        """解析单个语音注册表条目 - 简化版本"""
        try:
            registry_path = rf"SOFTWARE\Microsoft\Speech\Voices\Tokens\{voice_token}"
            
            with winreg.OpenKey(winreg.HKEY_LOCAL_MACHINE, registry_path) as key:
                # 读取语音属性
                voice_id = voice_token
                voice_name = self._read_registry_value(key, "", voice_token)
                language = self._read_registry_value(key, "Language", "en-US")
                gender = self._read_registry_value(key, "Gender", "unknown")
                vendor = self._read_registry_value(key, "Vendor", "Microsoft")
                
                # 构建描述
                description = f"{vendor} {voice_name}"
                
                # 标准化语言代码和性别
                language = self._normalize_language_code(language)
                gender = self._normalize_gender(gender)
                
                # 如果性别识别失败，尝试从语音名称中推断
                if gender == "unknown":
                    gender = self._infer_gender_from_name(voice_name, voice_token)
                
                # 尝试从pyttsx3引擎获取对应的语音对象
                voice_object = self._find_voice_object_by_id(voice_id)
                
                return TTSVoiceInfo(
                    id=voice_id,
                    name=voice_name,
                    language=language,
                    gender=gender,
                    description=description,
                    engine=self.engine_id,
                    quality=TTSQuality.MEDIUM,
                    sample_rate=22050,
                    bit_depth=16,
                    channels=1,
                    custom_attributes={
                        'voice_token': voice_token,
                        'vendor': vendor,
                        'is_registry_voice': True,
                        'voice_object': voice_object,
                        'is_system_voice': voice_object is not None
                    }
                )
                
        except Exception as e:
            self.logger.debug(f"解析语音注册表条目失败 {voice_token}: {e}")
            return None
    
    def _read_registry_value(self, key, value_name: str, default: str = "") -> str:
        """读取注册表值"""
        try:
            value, _ = winreg.QueryValueEx(key, value_name)
            return str(value) if value else default
        except OSError:
            return default
    
    def _normalize_language_code(self, language: str) -> str:
        """标准化语言代码 - 简化版本"""
        if not language:
            return "en-US"
        
        # 处理常见的语言代码格式
        language = language.strip()
        
        # 如果是数字格式，转换为标准格式
        language_map = {
            "2052": "zh-CN",  # 简体中文
            "1028": "zh-TW",  # 繁体中文
            "1033": "en-US",  # 英语(美国)
            "2057": "en-GB",  # 英语(英国)
            "1041": "ja-JP",  # 日语
            "1042": "ko-KR",  # 韩语
            "1036": "fr-FR",  # 法语
            "1031": "de-DE",  # 德语
            "1049": "ru-RU",  # 俄语
            "3082": "es-ES",  # 西班牙语
        }
        
        if language in language_map:
            return language_map[language]
        
        # 如果已经是标准格式，直接返回
        if "-" in language and len(language) >= 5:
            return language
        
        # 默认返回英语
        return "en-US"
    
    def _normalize_gender(self, gender: str) -> str:
        """标准化性别"""
        if not gender:
            return "unknown"
        
        gender = gender.strip().lower()
        
        if gender in ["male", "m", "man", "masculine"]:
            return "male"
        elif gender in ["female", "f", "woman", "feminine"]:
            return "female"
        else:
            return "unknown"
    
    def _infer_gender_from_name(self, voice_name: str, voice_token: str) -> str:
        """从语音名称推断性别 - 简化版本"""
        try:
            # 将名称和token转换为小写进行匹配
            name_lower = voice_name.lower()
            token_lower = voice_token.lower()
            
            # 女性语音标识
            female_indicators = ['zira', 'huihui', 'xiaoxiao', 'cori', 'amy', 'mary', 'sarah', 'lisa', 'anna', 'emma', 'female', 'woman', 'girl']
            # 男性语音标识
            male_indicators = ['david', 'mark', 'richard', 'alan', 'john', 'mike', 'tom', 'james', 'robert', 'male', 'man', 'boy']
            
            # 检查名称中是否包含性别标识
            for indicator in female_indicators:
                if indicator in name_lower or indicator in token_lower:
                    return "female"
            
            for indicator in male_indicators:
                if indicator in name_lower or indicator in token_lower:
                    return "male"
            
            return "unknown"
            
        except Exception as e:
            self.logger.debug(f"从语音名称推断性别失败: {e}")
            return "unknown"
    
    def _find_voice_object_by_id(self, voice_id: str):
        """根据语音ID从pyttsx3引擎中查找对应的语音对象"""
        try:
            if not self._engine:
                return None
            
            # 获取pyttsx3引擎的所有语音
            voices = self._engine.getProperty('voices')
            if not voices:
                return None
            
            # 查找匹配的语音对象
            for voice in voices:
                if hasattr(voice, 'id'):
                    voice_pyttsx3_id = voice.id
                    # 检查是否匹配（pyttsx3的ID是完整路径，我们的ID是token部分）
                    if voice_pyttsx3_id == voice_id or voice_pyttsx3_id.endswith(f"\\{voice_id}"):
                        return voice
                
                # 也尝试匹配名称
                if hasattr(voice, 'name') and voice.name == voice_id:
                    return voice
            
            return None
            
        except Exception as e:
            self.logger.debug(f"查找语音对象失败 {voice_id}: {e}")
            return None
    
    def _load_voices_from_engine(self):
        """从pyttsx3引擎加载语音（回退方法） - 简化版本"""
        try:
            if not self._engine:
                self.logger.warning("PyTTSx3引擎未初始化，无法加载语音")
                return
            
            # 获取系统语音
            voices = self._engine.getProperty('voices')
            
            if voices:
                for i, voice in enumerate(voices):
                    voice_id = voice.id if hasattr(voice, 'id') else f"voice_{i}"
                    voice_name = voice.name if hasattr(voice, 'name') else f"Voice {i+1}"
                    
                    # 提取语言信息
                    language = self._extract_language_from_voice_id(voice_id)
                    
                    self._voices[voice_id] = TTSVoiceInfo(
                        id=voice_id,
                        name=voice_name,
                        language=language,
                        gender='unknown',
                        description=f'PyTTSx3系统语音: {voice_name}',
                        engine=self.engine_id,
                        quality=TTSQuality.MEDIUM,
                        sample_rate=22050,
                        bit_depth=16,
                        channels=1,
                        custom_attributes={
                            'voice_object': voice,
                            'is_system_voice': True
                        }
                    )
                    
        except Exception as e:
            self.logger.error(f"从pyttsx3引擎加载语音失败: {e}")
    
    def _extract_language_from_voice_id(self, voice_id: str) -> str:
        """从语音ID中提取语言信息 - 简化版本"""
        try:
            voice_id_lower = voice_id.lower()
            
            # 常见语言映射
            language_mapping = {
                'zh': 'zh-CN', 'chinese': 'zh-CN', 'cn': 'zh-CN',
                'en': 'en-US', 'english': 'en-US', 'us': 'en-US',
                'ja': 'ja-JP', 'japanese': 'ja-JP', 'jp': 'ja-JP',
                'ko': 'ko-KR', 'korean': 'ko-KR', 'kr': 'ko-KR',
                'fr': 'fr-FR', 'french': 'fr-FR',
                'de': 'de-DE', 'german': 'de-DE',
                'es': 'es-ES', 'spanish': 'es-ES',
                'it': 'it-IT', 'italian': 'it-IT',
                'ru': 'ru-RU', 'russian': 'ru-RU',
                'pt': 'pt-PT', 'portuguese': 'pt-PT'
            }
            
            for key, lang in language_mapping.items():
                if key in voice_id_lower:
                    return lang
            
            # 默认返回英文
            return 'en-US'
            
        except Exception as e:
            self.logger.warning(f"提取语言信息失败 {voice_id}: {e}")
            return 'en-US'
    
    def synthesize(self, text: str, voice_config: VoiceConfig) -> TTSResult:
        """合成语音（重写基类方法，统一返回TTSResult）"""
        try:
            if not text.strip():
                return TTSResult(
                    success=False,
                    error_message="输入文本为空"
                )
            
            if not self._engine:
                return TTSResult(
                    success=False,
                    error_message="PyTTSx3引擎未初始化"
                )
            
            self.logger.info(f"开始PyTTSx3合成，语音: {voice_config.voice_name}")
            
            # 使用线程锁确保同时只有一个合成操作
            with self._synthesis_lock:
                # 配置语音参数
                self._configure_voice(voice_config)
                
                # 创建临时文件
                temp_file = tempfile.NamedTemporaryFile(suffix='.wav', delete=False)
                temp_path = temp_file.name
                temp_file.close()
                
                try:
                    # 使用pyttsx3的save_to_file方法保存到临时文件
                    self._engine.save_to_file(text, temp_path)
                    
                    # 使用超时机制避免runAndWait()无限阻塞
                    self._run_and_wait_with_timeout()
                    
                    # 重置引擎状态，避免连续调用时的问题
                    self._reset_engine_state()
                    
                    # 检查文件是否生成且不为空
                    if not os.path.exists(temp_path):
                        return TTSResult(
                            success=False,
                            error_message="临时音频文件未生成"
                        )
                    
                    if os.path.getsize(temp_path) == 0:
                        return TTSResult(
                            success=False,
                            error_message="生成的音频文件为空"
                        )
                    
                    # 读取音频数据
                    with open(temp_path, 'rb') as f:
                        audio_data = f.read()
                    
                    self.logger.info(f"PyTTSx3合成完成，音频大小: {len(audio_data)} 字节")
                    
                    return TTSResult(
                        success=True,
                        audio_data=audio_data,
                        duration=0.0,  # PyTTSx3不提供时长信息
                        sample_rate=int(self.sample_rate),
                        bit_depth=int(self.bit_depth),
                        channels=1,
                        format='wav'
                    )
                    
                finally:
                    # 清理临时文件
                    if os.path.exists(temp_path):
                        try:
                            os.unlink(temp_path)
                        except Exception as e:
                            self.logger.warning(f"清理临时文件失败: {e}")
                    
        except Exception as e:
            self.logger.error(f"PyTTSx3合成失败: {e}")
            return TTSResult(
                success=False,
                error_message=str(e)
            )
    
    def _synthesize_audio(self, text: str, voice_config: VoiceConfig) -> bytes:
        """合成音频数据（基类要求的方法）"""
        result = self.synthesize(text, voice_config)
        if result.success:
            return result.audio_data
        else:
            raise Exception(result.error_message)
    
    def _run_and_wait_with_timeout(self, timeout: int = 10):
        """带超时的runAndWait方法 - 简化版本"""
        try:
            # 创建一个线程来运行runAndWait
            result = [None]
            exception = [None]
            
            def run_worker():
                try:
                    self._engine.runAndWait()
                    result[0] = True
                except Exception as e:
                    exception[0] = e
            
            # 启动工作线程
            worker_thread = threading.Thread(target=run_worker)
            worker_thread.daemon = True
            worker_thread.start()
            
            # 等待完成或超时
            worker_thread.join(timeout=timeout)
            
            if worker_thread.is_alive():
                # 超时了，记录警告但继续
                self.logger.warning(f"PyTTSx3合成超时({timeout}秒)，但可能已完成")
                # 给一点额外时间让文件写入完成
                time.sleep(0.5)
            elif exception[0]:
                # 有异常
                raise exception[0]
            # 如果result[0]为True，说明正常完成
            
        except Exception as e:
            self.logger.warning(f"PyTTSx3 runAndWait超时处理失败: {e}")
            # 即使超时处理失败，也继续执行，因为文件可能已经生成
    
    def _reset_engine_state(self):
        """重置引擎状态，避免连续调用时的问题 - 简化版本"""
        try:
            # 停止当前引擎
            if self._engine:
                try:
                    self._engine.stop()
                except:
                    pass
                
                # 重新初始化引擎
                self._engine = pyttsx3.init()
                
                # 重新配置基本参数
                if hasattr(self, 'use_sapi'):
                    # 设置SAPI模式（Windows）
                    try:
                        self._engine.setProperty('voice', self._engine.getProperty('voices')[0].id)
                    except:
                        pass
                
                self.logger.debug("PyTTSx3引擎状态已重置")
                
        except Exception as e:
            self.logger.warning(f"重置PyTTSx3引擎状态失败: {e}")
            # 即使重置失败，也继续执行
    
    def _configure_voice(self, voice_config: VoiceConfig):
        """配置语音参数 - 简化版本"""
        try:
            if not self._engine:
                return
            
            # 设置语速 (PyTTSx3范围: 50-300, 默认200)
            # 将0.1-3.0的范围映射到50-300
            if voice_config.rate <= 0:
                rate = 50
            elif voice_config.rate >= 3.0:
                rate = 300
            else:
                # 线性映射: 0.1->50, 1.0->200, 3.0->300
                rate = int(50 + (voice_config.rate - 0.1) * (250 / 2.9))
                rate = max(50, min(300, rate))  # 确保在范围内
            
            self._engine.setProperty('rate', rate)
            
            # 设置音量 (PyTTSx3范围: 0.0-1.0)
            volume = max(0.0, min(1.0, voice_config.volume))
            self._engine.setProperty('volume', volume)
            
            # 设置语音
            if voice_config.voice_name and voice_config.voice_name in self._voices:
                voice_info = self._voices[voice_config.voice_name]
                if 'voice_object' in voice_info.custom_attributes:
                    voice_obj = voice_info.custom_attributes['voice_object']
                    self._engine.setProperty('voice', voice_obj.id)
                else:
                    self._engine.setProperty('voice', voice_config.voice_name)
            else:
                # 尝试找到匹配的语音
                voices = self._engine.getProperty('voices')
                if voices and voice_config.voice_name:
                    for voice in voices:
                        if (voice_config.voice_name in voice.name or 
                            voice_config.voice_name in getattr(voice, 'id', '')):
                            self._engine.setProperty('voice', voice.id)
                            break
                else:
                    # 如果没有指定语音或找不到匹配的，使用第一个可用的语音
                    voices = self._engine.getProperty('voices')
                    if voices and len(voices) > 0:
                        self._engine.setProperty('voice', voices[0].id)
            
            self.logger.debug(f"PyTTSx3语音配置: 语速={rate}, 音量={volume:.2f}, 语音={voice_config.voice_name}")
                        
        except Exception as e:
            self.logger.warning(f"配置PyTTSx3语音参数失败: {e}")
    
    def get_available_voices(self) -> List[TTSVoiceInfo]:
        """获取可用语音列表"""
        try:
            # 如果还没有加载语音，先加载
            if not self._voices:
                self._load_voices()
            
            # 返回所有可用的语音
            voices = list(self._voices.values())
            
            if voices:
                self.logger.info(f"pyttsx3返回 {len(voices)} 个可用语音: {[v.id for v in voices]}")
                return voices
            else:
                self.logger.warning("pyttsx3没有可用语音")
                return []
            
        except Exception as e:
            self.logger.error(f"获取pyttsx3语音列表失败: {e}")
            return []
    
    def get_available_voices_by_language(self, language: str) -> List[TTSVoiceInfo]:
        """根据语言获取可用语音"""
        return [
            voice for voice in self._voices.values()
            if voice.language == language
        ]
    
    def get_system_voices(self) -> List[TTSVoiceInfo]:
        """获取系统语音"""
        return [
            voice for voice in self._voices.values()
            if voice.custom_attributes.get('is_system_voice', False)
        ]
    
    def test_voice(self, voice_id: str, test_text: str = "Hello, this is a test.") -> bool:
        """测试语音"""
        try:
            if voice_id not in self._voices:
                return False
            
            voice_info = self._voices[voice_id]
            if 'voice_object' in voice_info.custom_attributes:
                voice_obj = voice_info.custom_attributes['voice_object']
                self._engine.setProperty('voice', voice_obj.id)
            else:
                self._engine.setProperty('voice', voice_id)
            
            # 创建临时文件进行测试
            temp_file = tempfile.NamedTemporaryFile(suffix='.wav', delete=False)
            temp_path = temp_file.name
            temp_file.close()
            
            try:
                self._engine.save_to_file(test_text, temp_path)
                self._engine.runAndWait()
                
                # 检查文件是否生成且不为空
                success = os.path.exists(temp_path) and os.path.getsize(temp_path) > 0
                return success
                
            finally:
                if os.path.exists(temp_path):
                    os.unlink(temp_path)
                
        except Exception as e:
            self.logger.error(f"测试语音失败 {voice_id}: {e}")
            return False
