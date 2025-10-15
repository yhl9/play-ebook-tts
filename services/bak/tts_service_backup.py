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
    def synthesize_to_file(self, text: str, voice_config: VoiceConfig, output_path: str = None) -> str:
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






class IndexTTSService(ITTSService):
    """IndexTTS API服务实现"""
    
    def __init__(self, api_url: str = "http://127.0.0.1:18000"):
        self.api_url = api_url.rstrip('/')
        self.voices = {}
        super().__init__()
    
    def _init_engine(self):
        """初始化IndexTTS API引擎"""
        try:
            self._load_voices()
            # 不在这里检查API连接，避免初始化失败
            # API连接在实际使用时检查
            self.logger.info("IndexTTS API引擎初始化成功")
        except Exception as e:
            self.logger.error(f"IndexTTS API引擎初始化失败: {e}")
            raise
    
    def _load_voices(self):
        """加载IndexTTS语音列表"""
        try:
            # 初始化语音字典
            self.voices = {}
            
            # 扫描音频文件夹
            audio_dir = "resources/audio"
            if os.path.exists(audio_dir):
                self._scan_audio_files(audio_dir)
            else:
                self.logger.warning(f"音频文件夹不存在: {audio_dir}")
            
            # 添加默认配置
            self.voices['default'] = {
                'name': '默认语音',
                'language': 'zh-CN',
                'gender': 'unknown',
                'prompt_audio': None,  # 需要用户提供参考音频
                'description': '需要提供参考音频文件'
            }
            
            # 如果扫描到了音频文件，设置默认的参考音频
            if len(self.voices) > 1:  # 除了default之外还有其他语音
                # 优先使用index-tts-zh-kangHuiRead.mp3作为默认
                default_audio = "4Code/resources/audio/index-tts-zh-kangHuiRead.mp3"
                if os.path.exists(default_audio):
                    self.voices['default']['prompt_audio'] = default_audio
                    self.voices['default']['description'] = f'使用默认参考音频: {os.path.basename(default_audio)}'
                else:
                    # 如果没有默认音频，使用第一个找到的音频
                    for voice_id, voice_info in self.voices.items():
                        if voice_id != 'default' and voice_info.get('prompt_audio'):
                            self.voices['default']['prompt_audio'] = voice_info['prompt_audio']
                            self.voices['default']['description'] = f'使用参考音频: {os.path.basename(voice_info["prompt_audio"])}'
                            break
            
            self.logger.info(f"加载了 {len(self.voices)} 个IndexTTS语音配置")
            
        except Exception as e:
            self.logger.error(f"加载IndexTTS语音配置失败: {e}")
            raise
    
    def _scan_audio_files(self, audio_dir: str):
        """扫描音频文件夹，查找以index-tts-开头的音频文件"""
        try:
            import glob
            
            # 支持的音频格式
            audio_extensions = ['*.wav', '*.mp3', '*.ogg', '*.m4a', '*.flac']
            
            for ext in audio_extensions:
                pattern = os.path.join(audio_dir, f"index-tts-*{ext}")
                audio_files = glob.glob(pattern)
                
                for audio_file in audio_files:
                    # 获取文件名（不含扩展名）
                    filename = os.path.basename(audio_file)
                    name_without_ext = os.path.splitext(filename)[0]
                    
                    # 生成语音ID（去掉index-tts-前缀）
                    voice_id = name_without_ext.replace('index-tts-', '')
                    if not voice_id:
                        voice_id = name_without_ext
                    
                    # 生成语音名称
                    voice_name = name_without_ext.replace('index-tts-', 'IndexTTS-')
                    
                    # 添加到语音列表
                    self.voices[voice_id] = {
                        'name': voice_name,
                        'language': 'zh-CN',  # 默认为中文
                        'gender': 'unknown',
                        'prompt_audio': audio_file,
                        'description': f'使用参考音频: {filename}'
                    }
                    
                    self.logger.info(f"发现音频文件: {filename} -> 语音ID: {voice_id}")
            
            self.logger.info(f"扫描完成，发现 {len([v for v in self.voices.values() if v.get('prompt_audio')])} 个音频文件")
            
        except Exception as e:
            self.logger.error(f"扫描音频文件失败: {e}")
            raise
    
    def _check_api_connection(self):
        """检查API连接"""
        try:
            # 尝试访问API文档端点
            response = requests.get(f"{self.api_url}/docs", timeout=5)
            if response.status_code == 200:
                self.logger.info("IndexTTS API连接正常")
            else:
                raise AudioGenerationError(f"IndexTTS API不可用，状态码: {response.status_code}")
        except requests.exceptions.RequestException as e:
            raise AudioGenerationError(f"无法连接到IndexTTS API: {e}")
    
    def synthesize(self, text: str, voice_config: VoiceConfig) -> bytes:
        """合成语音为字节数据"""
        try:
            if not text.strip():
                return b''
            
            self.logger.info(f"开始IndexTTS API合成，语音: {voice_config.voice_name}")
            
            # 检查API连接
            self._check_api_connection()
            
            # 生成临时文件路径
            temp_wav = os.path.join(tempfile.gettempdir(), f"index_tts_temp_{int(time.time())}.wav")
            
            # 合成到文件
            result_path = self.synthesize_to_file(text, voice_config, temp_wav)
            
            # 读取音频数据
            with open(result_path, 'rb') as f:
                audio_data = f.read()
            
            # 删除临时文件
            try:
                os.remove(result_path)
            except Exception:
                pass
            
            return audio_data
            
        except Exception as e:
            self.logger.error(f"IndexTTS API合成失败: {e}")
            raise AudioGenerationError(f"IndexTTS API合成失败: {e}")
    
    def _generate_output_path(self, voice_config: VoiceConfig, output_config, text: str, chapter_info=None) -> str:
        """根据输出配置生成文件路径"""
        try:
            import tempfile
            import re
            
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
                filename = f"index_tts_{int(time.time())}"
            
            # 限制文件名长度
            if len(filename) > name_length_limit:
                filename = filename[:name_length_limit]
            
            # 清理文件名中的非法字符
            filename = re.sub(r'[<>:"/\\|?*]', '_', filename)
            
            return os.path.join(output_dir, f"{filename}{file_format}")
            
        except Exception as e:
            self.logger.error(f"生成输出路径失败: {e}")
            # 回退到默认命名
            return os.path.join(tempfile.gettempdir(), f"index_tts_{int(time.time())}.wav")
    
    def _apply_custom_template(self, template: str, chapter_info, text: str) -> str:
        """应用自定义模板"""
        try:
            if not chapter_info:
                return f"custom_{int(time.time())}"
            
            # 替换模板中的占位符
            filename = template
            filename = filename.replace('{chapter_num}', str(getattr(chapter_info, 'number', 1)))
            filename = filename.replace('{chapter_num:02d}', f"{getattr(chapter_info, 'number', 1):02d}")
            # 清理标题
            from utils.chapter_name_cleaner import clean_chapter_name
            safe_title = clean_chapter_name(getattr(chapter_info, 'title', 'untitled'))
            filename = filename.replace('{title}', safe_title)
            filename = filename.replace('{engine}', 'index_tts')
            filename = filename.replace('{voice}', 'index_voice')
            
            return filename
        except Exception as e:
            self.logger.error(f"应用自定义模板失败: {e}")
            return f"custom_{int(time.time())}"
    
    def _generate_chapter_title_name(self, chapter_info, text: str) -> str:
        """生成章节序号+标题格式的文件名"""
        if not chapter_info:
            return f"chapter_{int(time.time())}"
        
        chapter_num = getattr(chapter_info, 'number', 1)
        title = getattr(chapter_info, 'title', 'untitled')
        
        # 清理章节标题
        from utils.chapter_name_cleaner import clean_chapter_name
        safe_title = clean_chapter_name(title)
        
        return f"{chapter_num:02d}_{safe_title}"
    
    def _generate_number_title_name(self, chapter_info, text: str) -> str:
        """生成序号+标题格式的文件名"""
        if not chapter_info:
            return f"audio_{int(time.time())}"
        
        chapter_num = getattr(chapter_info, 'number', 1)
        title = getattr(chapter_info, 'title', 'untitled')
        
        # 清理章节标题
        from utils.chapter_name_cleaner import clean_chapter_name
        safe_title = clean_chapter_name(title)
        
        return f"{chapter_num}_{safe_title}"
    
    def _generate_title_only_name(self, chapter_info, text: str) -> str:
        """生成仅标题格式的文件名"""
        if not chapter_info:
            return f"audio_{int(time.time())}"
        
        title = getattr(chapter_info, 'title', 'untitled')
        
        # 清理章节标题
        from utils.chapter_name_cleaner import clean_chapter_name
        return clean_chapter_name(title)
    
    def _generate_number_only_name(self, chapter_info, text: str) -> str:
        """生成仅序号格式的文件名"""
        if not chapter_info:
            return f"audio_{int(time.time())}"
        
        chapter_num = getattr(chapter_info, 'number', 1)
        return f"{chapter_num:02d}"
    
    def _generate_original_filename(self, chapter_info, text: str) -> str:
        """生成原始文件名格式的文件名"""
        if not chapter_info:
            return f"original_{int(time.time())}"
        
        # 尝试从章节信息中获取原始文件名
        original_filename = getattr(chapter_info, 'original_filename', None)
        if original_filename:
            # 移除文件扩展名
            import os
            name_without_ext = os.path.splitext(original_filename)[0]
            return name_without_ext
        
        # 如果没有原始文件名，使用标题
        title = getattr(chapter_info, 'title', 'untitled')
        
        # 清理章节标题
        from utils.chapter_name_cleaner import clean_chapter_name
        return clean_chapter_name(title)
    
    def synthesize_to_file(self, text: str, voice_config: VoiceConfig, output_path: str = None, 
                          progress_callback=None, output_config=None, chapter_info=None) -> str:
        """合成语音到文件"""
        try:
            if not text.strip():
                return ""
            
            self.logger.info(f"开始IndexTTS API文件合成，语音: {voice_config.voice_name}")
            
            # 检查API连接
            self._check_api_connection()
            
            # 启动进度估算
            if progress_callback:
                from services.progress_estimator import ProgressEstimator, TextComplexityAnalyzer
                estimator = ProgressEstimator()
                
                # 连接信号
                estimator.progress_updated.connect(progress_callback)
                
                # 分析文本复杂度
                complexity = TextComplexityAnalyzer.analyze_complexity(text)
                
                # 开始估算
                estimator.start_estimation(len(text), complexity, self.api_url, "index_tts_api_15")
            
            # 生成输出文件路径
            if not output_path:
                if output_config and hasattr(output_config, 'naming_mode'):
                    # 使用输出设置中的文件命名规则
                    output_path = self._generate_output_path(voice_config, output_config, text, chapter_info)
                else:
                    output_path = os.path.join(tempfile.gettempdir(), f"index_tts_output_{int(time.time())}.wav")
            
            # 确保输出目录存在
            os.makedirs(os.path.dirname(output_path), exist_ok=True)
            
            # 获取语音配置
            voice_info = self.voices.get(voice_config.voice_name, self.voices['default'])
            prompt_audio = voice_info.get('prompt_audio')
            
            if not prompt_audio:
                raise AudioGenerationError(f"语音 {voice_config.voice_name} 需要提供参考音频文件")
            
            # 检查参考音频文件是否存在
            if not os.path.exists(prompt_audio):
                raise AudioGenerationError(f"参考音频文件不存在: {prompt_audio}")
            
            # 检查参考音频文件是否为空
            if os.path.getsize(prompt_audio) == 0:
                raise AudioGenerationError(f"参考音频文件为空: {prompt_audio}")
            
            # 准备API请求数据
            # 将相对路径转换为绝对路径
            prompt_audio_abs = os.path.abspath(prompt_audio)
            
            # 基础参数
            api_data = {
                "prompt_audio": prompt_audio_abs,
                "text": text,
                "output_path": output_path
            }
            
            # 从voice_config的extra_params获取动态参数
            if hasattr(voice_config, 'extra_params') and voice_config.extra_params:
                # 使用用户配置的参数
                extra_params = voice_config.extra_params
                api_data.update({
                    "infer_mode": extra_params.get('infer_mode', '普通推理'),
                    "max_text_tokens_per_sentence": 120,
                    "sentences_bucket_max_size": 4,
                    "do_sample": True,
                    "top_p": extra_params.get('top_p', 0.8),
                    "top_k": extra_params.get('top_k', 30),
                    "temperature": extra_params.get('temperature', 1.0),
                    "length_penalty": 0.0,
                    "num_beams": 3,
                    "repetition_penalty": extra_params.get('repetition_penalty', 10.0),
                    "max_mel_tokens": extra_params.get('max_mel_tokens', 600)
                })
            else:
                # 使用默认参数
                api_data.update({
                    "infer_mode": "普通推理",
                    "max_text_tokens_per_sentence": 120,
                    "sentences_bucket_max_size": 4,
                    "do_sample": True,
                    "top_p": 0.8,
                    "top_k": 30,
                    "temperature": 1.0,
                    "length_penalty": 0.0,
                    "num_beams": 3,
                    "repetition_penalty": 10.0,
                    "max_mel_tokens": 600
                })
            
            # 记录API请求数据
            self.logger.info(f"IndexTTS API请求数据: {api_data}")
            
            # 根据文本长度计算超时时间
            text_length = len(text)
            if text_length <= 1000:
                timeout = 240  # 4分钟
            else:
                # 超过1000字符，每100字符增加30秒
                extra_chars = text_length - 1000
                # 使用向上取整，确保每100字符增加30秒
                extra_time = ((extra_chars + 99) // 100) * 30
                timeout = 240 + extra_time
            
            self.logger.info(f"文本长度: {text_length} 字符, 超时时间: {timeout} 秒")
            
            # 调用IndexTTS API
            try:
                response = requests.post(
                    f"{self.api_url}/tts",
                    json=api_data,
                    timeout=timeout
                )
                
                # 更新进度到处理完成阶段
                if progress_callback:
                    estimator.current_phase = "完成中"
                    estimator.progress_updated.emit(90)
                
                if response.status_code == 200:
                    result = response.json()
                    self.logger.info(f"IndexTTS API响应: {result}")
                    
                    generated_audio_path = result.get('audio_path')
                    
                    if generated_audio_path and os.path.exists(generated_audio_path):
                        # 如果API返回的路径与期望的输出路径不同，复制文件
                        if generated_audio_path != output_path:
                            import shutil
                            shutil.copy2(generated_audio_path, output_path)
                        
                        # 完成进度估算
                        if progress_callback:
                            estimator.stop_estimation(success=True)
                        
                        self.logger.info(f"IndexTTS API合成完成: {output_path}")
                        return output_path
                    else:
                        # 完成进度估算（失败）
                        if progress_callback:
                            estimator.stop_estimation(success=False)
                        
                        self.logger.error(f"API返回的音频路径无效: {generated_audio_path}")
                        self.logger.error(f"期望的输出路径: {output_path}")
                        raise AudioGenerationError("API返回的音频文件路径无效或文件不存在")
                else:
                    # 完成进度估算（失败）
                    if progress_callback:
                        estimator.stop_estimation(success=False)
                    
                    error_msg = f"API请求失败: {response.status_code} - {response.text}"
                    self.logger.error(error_msg)
                    raise AudioGenerationError(error_msg)
                    
            except Exception as e:
                # 完成进度估算（失败）
                if progress_callback:
                    estimator.stop_estimation(success=False)
                raise
                
        except Exception as e:
            self.logger.error(f"IndexTTS API文件合成失败: {e}")
            raise AudioGenerationError(f"IndexTTS API文件合成失败: {e}")
    
    def get_available_voices(self) -> List[dict]:
        """获取可用语音列表"""
        try:
            voices = []
            for voice_id, voice_info in self.voices.items():
                voices.append({
                    'id': voice_id,
                    'name': voice_info['name'],
                    'language': voice_info['language'],
                    'gender': voice_info['gender'],
                    'engine': 'index_tts',
                    'description': voice_info.get('description', ''),
                    'prompt_audio': voice_info.get('prompt_audio')
                })
            
            self.logger.info(f"获取到 {len(voices)} 个IndexTTS语音配置")
            return voices
            
        except Exception as e:
            self.logger.error(f"获取IndexTTS语音列表失败: {e}")
            return []
    
    def is_available(self) -> bool:
        """检查引擎是否可用"""
        try:
            # IndexTTS引擎本身可用，但API连接在实际使用时检查
            # 这样可以避免在UI中显示"不可用"状态
            return True
        except Exception:
            return False
    
    def get_engine_name(self) -> str:
        """获取引擎名称"""
        return "IndexTTS API"
    
    def get_engine_info(self) -> dict:
        """获取引擎信息"""
        return {
            'name': 'IndexTTS API',
            'description': 'IndexTTS API服务',
            'available': self.is_available(),
            'online': True,
            'voice_count': len(self.voices),
            'api_url': self.api_url
        }
    
    def add_voice(self, voice_id: str, name: str, prompt_audio: str, language: str = 'zh-CN', gender: str = 'unknown'):
        """添加自定义语音配置"""
        try:
            if not os.path.exists(prompt_audio):
                raise AudioGenerationError(f"参考音频文件不存在: {prompt_audio}")
            
            self.voices[voice_id] = {
                'name': name,
                'language': language,
                'gender': gender,
                'prompt_audio': prompt_audio,
                'description': f'自定义语音: {name}'
            }
            
            self.logger.info(f"添加自定义语音: {voice_id} - {name}")
            
        except Exception as e:
            self.logger.error(f"添加自定义语音失败: {e}")
            raise AudioGenerationError(f"添加自定义语音失败: {e}")
    
    def remove_voice(self, voice_id: str):
        """移除语音配置"""
        try:
            if voice_id in self.voices:
                del self.voices[voice_id]
                self.logger.info(f"移除语音配置: {voice_id}")
            else:
                self.logger.warning(f"语音配置不存在: {voice_id}")
                
        except Exception as e:
            self.logger.error(f"移除语音配置失败: {e}")
            raise AudioGenerationError(f"移除语音配置失败: {e}")


class PiperTTSService(ITTSService):
    """Piper TTS服务实现"""
    
    def __init__(self, models_dir: str = None):
        self.models_dir = models_dir or os.path.join(os.getcwd(), "models", "piper")
        self.voices = {}
        self.loaded_models = {}  # 缓存已加载的模型
        super().__init__()
    
    def _init_engine(self):
        """初始化Piper TTS引擎"""
        try:
            if not PIPER_AVAILABLE:
                self.logger.warning("Piper TTS库不可用，引擎将显示为不可用状态")
                return
            
            # 确保模型目录存在
            os.makedirs(self.models_dir, exist_ok=True)
            
            # 加载可用的语音模型
            self._load_available_voices()
            
            self.logger.info("Piper TTS引擎初始化成功")
        except Exception as e:
            self.logger.error(f"Piper TTS引擎初始化失败: {e}")
            # 不抛出异常，让引擎显示为不可用
    
    def _load_available_voices(self):
        """加载可用的语音模型"""
        try:
            # 扫描模型目录
            self._scan_model_directory()
            
            # 如果没有找到模型，添加一些默认的语音配置
            if not self.voices:
                self._add_default_voice_configs()
            
            self.logger.info(f"加载了 {len(self.voices)} 个Piper语音模型")
            
        except Exception as e:
            self.logger.error(f"加载Piper语音模型失败: {e}")
            raise
    
    def _scan_model_directory(self):
        """扫描模型目录，查找可用的语音模型"""
        try:
            if not os.path.exists(self.models_dir):
                self.logger.warning(f"模型目录不存在: {self.models_dir}")
                return
            
            self.logger.info(f"开始扫描Piper模型目录: {self.models_dir}")
            
            # 查找模型文件
            for item in os.listdir(self.models_dir):
                item_path = os.path.join(self.models_dir, item)
                
                if os.path.isdir(item_path):
                    # 检查是否是模型目录
                    model_files = self._find_model_files(item_path)
                    if model_files:
                        voice_id = item
                        model_path, config_path = model_files
                        
                        # 尝试从配置文件中获取语音信息
                        voice_info = self._extract_voice_info(config_path, voice_id)
                        
                        # 创建语音配置
                        voice_config = {
                            'name': voice_info['name'],
                            'language': voice_info['language'],
                            'gender': voice_info['gender'],
                            'model_path': model_path,
                            'config_path': config_path,
                            'description': f"Piper TTS模型: {voice_id}",
                            'id': voice_id
                        }
                        
                        self.voices[voice_id] = voice_config
                        
                        self.logger.info(f"发现Piper模型: {voice_id} - {voice_info['name']} ({voice_info['language']})")
                    else:
                        self.logger.debug(f"跳过目录 {item}，未找到有效的模型文件")
                else:
                    # 检查是否是直接的模型文件
                    if item.endswith('.onnx'):
                        voice_id = item.replace('.onnx', '')
                        config_path = os.path.join(self.models_dir, f"{voice_id}.onnx.json")
                        
                        if os.path.exists(config_path):
                            voice_info = self._extract_voice_info(config_path, voice_id)
                            
                            voice_config = {
                                'name': voice_info['name'],
                                'language': voice_info['language'],
                                'gender': voice_info['gender'],
                                'model_path': item_path,
                                'config_path': config_path,
                                'description': f"Piper TTS模型: {voice_id}",
                                'id': voice_id
                            }
                            
                            self.voices[voice_id] = voice_config
                            self.logger.info(f"发现Piper模型文件: {voice_id} - {voice_info['name']} ({voice_info['language']})")
            
            self.logger.info(f"Piper模型扫描完成，共发现 {len(self.voices)} 个模型")
            
        except Exception as e:
            self.logger.error(f"扫描模型目录失败: {e}")
    
    def _find_model_files(self, model_dir: str) -> Optional[tuple]:
        """在模型目录中查找模型文件和配置文件 - 基于testpiper.py的改进版本"""
        try:
            # 检查路径格式并确定模型文件名
            if os.path.isdir(model_dir):
                # 如果是目录，查找model.onnx和config.json
                model_path = os.path.join(model_dir, "model.onnx")
                config_path = os.path.join(model_dir, "config.json")
            else:
                # 如果是文件路径，从路径中提取信息
                model_path = model_dir
                config_path = model_dir.replace(".onnx", ".onnx.json")
            
            # 检查文件是否存在
            if os.path.exists(model_path) and os.path.exists(config_path):
                return model_path, config_path
            
            # 如果标准路径不存在，尝试其他常见的命名模式
            import glob
            
            # 常见的模型文件命名模式
            model_patterns = [
                "model.onnx",
                "*.onnx"
            ]
            config_patterns = [
                "config.json",
                "*.onnx.json",
                "*.json"
            ]
            
            model_path = None
            config_path = None
            
            # 查找模型文件
            for pattern in model_patterns:
                if pattern == "model.onnx":
                    candidate = os.path.join(model_dir, pattern)
                    if os.path.exists(candidate):
                        model_path = candidate
                        break
                else:
                    candidates = glob.glob(os.path.join(model_dir, pattern))
                    if candidates:
                        model_path = candidates[0]
                        break
            
            # 查找配置文件
            for pattern in config_patterns:
                if pattern == "config.json":
                    candidate = os.path.join(model_dir, pattern)
                    if os.path.exists(candidate):
                        config_path = candidate
                        break
                else:
                    candidates = glob.glob(os.path.join(model_dir, pattern))
                    if candidates:
                        config_path = candidates[0]
                        break
            
            if model_path and config_path:
                return model_path, config_path
            
            return None
            
        except Exception as e:
            self.logger.error(f"查找模型文件失败: {e}")
            return None
    
    def _extract_voice_info(self, config_path: str, voice_id: str) -> dict:
        """从配置文件中提取语音信息"""
        try:
            with open(config_path, 'r', encoding='utf-8') as f:
                config = json.load(f)
            
            # 提取语音信息
            name = config.get('speaker', {}).get('name', voice_id)
            language = config.get('language', {}).get('code', 'unknown')
            gender = config.get('speaker', {}).get('gender', 'unknown')
            
            # 如果speaker信息不存在，尝试从其他字段获取
            if name == voice_id:
                # 尝试从voice_id中提取信息
                if '_' in voice_id:
                    parts = voice_id.split('_')
                    if len(parts) >= 3:
                        # 格式: language_country-voice-quality
                        lang_country = parts[0] + '_' + parts[1]
                        voice_name = parts[2].split('-')[0] if '-' in parts[2] else parts[2]
                        name = f"{voice_name} ({lang_country})"
            
            # 如果语言信息不存在，尝试从voice_id中提取
            if language == 'unknown':
                if '_' in voice_id:
                    parts = voice_id.split('_')
                    if len(parts) >= 2:
                        language = parts[0] + '-' + parts[1]
            
            return {
                'name': name,
                'language': language,
                'gender': gender
            }
            
        except Exception as e:
            self.logger.warning(f"解析配置文件失败: {e}")
            # 尝试从voice_id中提取基本信息
            name = voice_id
            language = 'unknown'
            gender = 'unknown'
            
            if '_' in voice_id:
                parts = voice_id.split('_')
                if len(parts) >= 3:
                    lang_country = parts[0] + '_' + parts[1]
                    voice_name = parts[2].split('-')[0] if '-' in parts[2] else parts[2]
                    name = f"{voice_name} ({lang_country})"
                    language = parts[0] + '-' + parts[1]
            
            return {
                'name': name,
                'language': language,
                'gender': gender
            }
    
    def _add_default_voice_configs(self):
        """添加默认的语音配置"""
        # 添加一些常见的Piper语音配置
        default_voices = {
            'zh_CN-huayan-medium': {
                'name': '华严（中文）',
                'language': 'zh-CN',
                'gender': 'female',
                'model_path': None,  # 需要下载
                'config_path': None,
                'description': '中文女声，需要下载模型',
                'id': 'zh_CN-huayan-medium'
            },
            'en_GB-alan-medium': {
                'name': 'Alan（英文）',
                'language': 'en-GB',
                'gender': 'male',
                'model_path': None,  # 需要下载
                'config_path': None,
                'description': '英式男声，需要下载模型',
                'id': 'en_GB-alan-medium'
            }
        }
        
        self.voices.update(default_voices)
    
    def _map_voice_id(self, voice_name: str) -> str:
        """映射语音ID到Piper TTS的语音ID"""
        # 如果voice_name已经是Piper TTS的ID，直接返回
        if voice_name in self.voices:
            return voice_name
        
        # 语音映射表：Edge TTS -> Piper TTS
        voice_mapping = {
            'zh-CN-XiaoxiaoNeural': 'zh_CN-huayan-medium',
            'zh-CN-YunxiNeural': 'zh_CN-huayan-medium',
            'zh-CN-YunyangNeural': 'zh_CN-huayan-medium',
            'zh-CN-XiaoyiNeural': 'zh_CN-huayan-medium',
            'zh-CN-YunjianNeural': 'zh_CN-huayan-medium',
            'zh-CN-XiaochenNeural': 'zh_CN-huayan-medium',
            'zh-CN-XiaohanNeural': 'zh_CN-huayan-medium',
            'zh-CN-XiaomengNeural': 'zh_CN-huayan-medium',
            'en-US-AriaNeural': 'en_GB-alan-medium',
            'en-US-DavisNeural': 'en_GB-alan-medium',
            'en-US-EmmaNeural': 'en_GB-alan-medium',
            'en-US-GuyNeural': 'en_GB-alan-medium',
            'en-US-JaneNeural': 'en_GB-alan-medium',
            'en-US-JasonNeural': 'en_GB-alan-medium',
            'en-US-JennyNeural': 'en_GB-alan-medium',
            'en-US-MichelleNeural': 'en_GB-alan-medium',
            'en-US-RyanNeural': 'en_GB-alan-medium',
            'en-US-SaraNeural': 'en_GB-alan-medium',
            'en-US-TonyNeural': 'en_GB-alan-medium',
            'en-GB-LibbyNeural': 'en_GB-alan-medium',
            'en-GB-MaisieNeural': 'en_GB-alan-medium',
            'en-GB-RyanNeural': 'en_GB-alan-medium',
            'en-GB-SoniaNeural': 'en_GB-alan-medium',
            'en-GB-ThomasNeural': 'en_GB-alan-medium'
        }
        
        # 如果直接是Piper TTS的语音ID，直接返回
        if voice_name in self.voices:
            return voice_name
        
        # 如果是Edge TTS的语音ID，映射到Piper TTS
        if voice_name in voice_mapping:
            mapped_voice = voice_mapping[voice_name]
            if mapped_voice in self.voices:
                return mapped_voice
        
        # 默认使用中文语音
        if 'zh' in voice_name.lower() or 'cn' in voice_name.lower():
            return 'zh_CN-huayan-medium'
        else:
            return 'en_GB-alan-medium'
    
    def _generate_output_path(self, voice_config: VoiceConfig, output_config, text: str, chapter_info=None) -> str:
        """根据输出配置生成文件路径"""
        try:
            import tempfile
            import re
            
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
                filename = f"piper_tts_{int(time.time())}"
            
            # 限制文件名长度
            if len(filename) > name_length_limit:
                filename = filename[:name_length_limit]
            
            # 清理文件名中的非法字符
            filename = re.sub(r'[<>:"/\\|?*]', '_', filename)
            
            return os.path.join(output_dir, f"{filename}{file_format}")
            
        except Exception as e:
            self.logger.error(f"生成输出路径失败: {e}")
            # 回退到默认命名
            return os.path.join(tempfile.gettempdir(), f"piper_tts_{int(time.time())}.wav")
    
    def _apply_custom_template(self, template: str, chapter_info, text: str) -> str:
        """应用自定义模板"""
        try:
            if not chapter_info:
                return f"custom_{int(time.time())}"
            
            # 替换模板中的占位符
            filename = template
            filename = filename.replace('{chapter_num}', str(getattr(chapter_info, 'number', 1)))
            filename = filename.replace('{chapter_num:02d}', f"{getattr(chapter_info, 'number', 1):02d}")
            # 清理标题
            from utils.chapter_name_cleaner import clean_chapter_name
            safe_title = clean_chapter_name(getattr(chapter_info, 'title', 'untitled'))
            filename = filename.replace('{title}', safe_title)
            filename = filename.replace('{engine}', 'piper_tts')
            filename = filename.replace('{voice}', 'piper_voice')
            
            return filename
        except Exception as e:
            self.logger.error(f"应用自定义模板失败: {e}")
            return f"custom_{int(time.time())}"
    
    def _generate_chapter_title_name(self, chapter_info, text: str) -> str:
        """生成章节序号+标题格式的文件名"""
        if not chapter_info:
            return f"chapter_{int(time.time())}"
        
        chapter_num = getattr(chapter_info, 'number', 1)
        title = getattr(chapter_info, 'title', 'untitled')
        
        # 清理章节标题
        from utils.chapter_name_cleaner import clean_chapter_name
        safe_title = clean_chapter_name(title)
        
        return f"{chapter_num:02d}_{safe_title}"
    
    def _generate_number_title_name(self, chapter_info, text: str) -> str:
        """生成序号+标题格式的文件名"""
        if not chapter_info:
            return f"audio_{int(time.time())}"
        
        chapter_num = getattr(chapter_info, 'number', 1)
        title = getattr(chapter_info, 'title', 'untitled')
        
        # 清理章节标题
        from utils.chapter_name_cleaner import clean_chapter_name
        safe_title = clean_chapter_name(title)
        
        return f"{chapter_num}_{safe_title}"
    
    def _generate_title_only_name(self, chapter_info, text: str) -> str:
        """生成仅标题格式的文件名"""
        if not chapter_info:
            return f"audio_{int(time.time())}"
        
        title = getattr(chapter_info, 'title', 'untitled')
        
        # 清理章节标题
        from utils.chapter_name_cleaner import clean_chapter_name
        return clean_chapter_name(title)
    
    def _generate_number_only_name(self, chapter_info, text: str) -> str:
        """生成仅序号格式的文件名"""
        if not chapter_info:
            return f"audio_{int(time.time())}"
        
        chapter_num = getattr(chapter_info, 'number', 1)
        return f"{chapter_num:02d}"
    
    def _generate_original_filename(self, chapter_info, text: str) -> str:
        """生成原始文件名格式的文件名"""
        if not chapter_info:
            return f"original_{int(time.time())}"
        
        # 尝试从章节信息中获取原始文件名
        original_filename = getattr(chapter_info, 'original_filename', None)
        if original_filename:
            # 移除文件扩展名
            import os
            name_without_ext = os.path.splitext(original_filename)[0]
            return name_without_ext
        
        # 如果没有原始文件名，使用标题
        title = getattr(chapter_info, 'title', 'untitled')
        
        # 清理章节标题
        from utils.chapter_name_cleaner import clean_chapter_name
        return clean_chapter_name(title)
    
    def _get_voice_model(self, voice_id: str):
        """获取语音模型，支持缓存"""
        try:
            if voice_id in self.loaded_models:
                return self.loaded_models[voice_id]
            
            voice_info = self.voices.get(voice_id)
            if not voice_info:
                raise AudioGenerationError(f"未找到语音模型: {voice_id}")
            
            model_path = voice_info.get('model_path')
            config_path = voice_info.get('config_path')
            
            if not model_path or not config_path:
                raise AudioGenerationError(f"语音模型文件不完整: {voice_id}")
            
            if not os.path.exists(model_path) or not os.path.exists(config_path):
                raise AudioGenerationError(f"语音模型文件不存在: {voice_id}")
            
            # 加载模型
            voice = PiperVoice.load(model_path, config_path)
            self.loaded_models[voice_id] = voice
            
            self.logger.info(f"成功加载Piper模型: {voice_id}")
            return voice
            
        except Exception as e:
            self.logger.error(f"加载Piper模型失败: {e}")
            raise AudioGenerationError(f"加载Piper模型失败: {e}")
    
    def _detect_language(self, text: str) -> str:
        """检测文本语言 - 基于testpiper.py的改进版本"""
        if not text or not isinstance(text, str):
            return "unknown"
        
        # 判断是否包含中文字符
        if re.search(r'[\u4e00-\u9fa5]', text):
            return "zh-CN"
        
        # 判断是否主要是英文（包含常见英文标点和数字）
        ascii_count = sum(1 for c in text if ord(c) < 128)
        if ascii_count / len(text) > 0.7:
            return "en-US"
        
        # 可以根据需要添加更多语言的检测逻辑
        # 例如：日文、韩文、德文、法文、西班牙文等
        
        return "unknown"
    
    def synthesize(self, text: str, voice_config: VoiceConfig) -> bytes:
        """合成语音为字节数据"""
        try:
            if not text.strip():
                return b''
            
            self.logger.info(f"开始Piper TTS合成，语音: {voice_config.voice_name}")
            
            # 获取语音模型
            voice = self._get_voice_model(voice_config.voice_name)
            
            # 创建合成配置
            synthesis_config = SynthesisConfig(
                volume=voice_config.volume,
                length_scale=voice_config.rate,  # 语速
                noise_scale=1.0,
                noise_w_scale=1.0,
                normalize_audio=True
            )
            
            # 合成音频
            audio_data = b""
            for chunk in voice.synthesize(text, synthesis_config):
                audio_data += chunk.audio_int16_bytes
            
            self.logger.info(f"Piper TTS合成完成，音频大小: {len(audio_data)} 字节")
            return audio_data
            
        except Exception as e:
            self.logger.error(f"Piper TTS合成失败: {e}")
            raise AudioGenerationError(f"Piper TTS合成失败: {e}")
    
    def synthesize_to_file(self, text: str, voice_config: VoiceConfig, output_path: str = None, output_config=None, chapter_info=None) -> str:
        """合成语音到文件"""
        try:
            if not text.strip():
                return ""
            
            self.logger.info(f"开始Piper TTS文件合成，语音: {voice_config.voice_name}")
            
            # 生成输出文件路径
            if not output_path:
                if output_config and hasattr(output_config, 'naming_mode'):
                    # 使用输出设置中的文件命名规则
                    self.logger.info(f"使用文件命名规则: {output_config.naming_mode}")
                    self.logger.info(f"章节信息: {chapter_info}")
                    output_path = self._generate_output_path(voice_config, output_config, text, chapter_info)
                else:
                    # 使用统一的命名规则：tts_output_{voice_name}.wav
                    self.logger.info("使用默认命名规则")
                    output_path = os.path.join(tempfile.gettempdir(), f"tts_output_{voice_config.voice_name}.wav")
            
            # 确保输出目录存在
            os.makedirs(os.path.dirname(output_path), exist_ok=True)
            
            # 映射语音ID到Piper TTS的语音ID
            piper_voice_id = self._map_voice_id(voice_config.voice_name)
            
            # 获取语音模型
            voice = self._get_voice_model(piper_voice_id)
            
            # 创建合成配置
            synthesis_config = SynthesisConfig(
                volume=voice_config.volume,
                length_scale=voice_config.rate,  # 语速
                noise_scale=1.0,
                noise_w_scale=1.0,
                normalize_audio=True
            )
            
            # 合成到文件
            with wave.open(output_path, "wb") as wav_file:
                voice.synthesize_wav(text, wav_file, synthesis_config)
            
            self.logger.info(f"Piper TTS合成完成: {output_path}")
            return output_path
            
        except Exception as e:
            self.logger.error(f"Piper TTS文件合成失败: {e}")
            raise AudioGenerationError(f"Piper TTS文件合成失败: {e}")
    
    def get_available_voices(self) -> List[dict]:
        """获取可用语音列表"""
        try:
            voices = []
            for voice_id, voice_info in self.voices.items():
                voices.append({
                    'id': voice_id,
                    'name': voice_info['name'],
                    'language': voice_info['language'],
                    'gender': voice_info['gender'],
                    'engine': 'piper_tts',
                    'description': voice_info.get('description', ''),
                    'model_path': voice_info.get('model_path'),
                    'config_path': voice_info.get('config_path')
                })
            
            self.logger.info(f"获取到 {len(voices)} 个Piper语音")
            return voices
            
        except Exception as e:
            self.logger.error(f"获取Piper语音列表失败: {e}")
            return []
    
    def is_available(self) -> bool:
        """检查引擎是否可用"""
        try:
            return PIPER_AVAILABLE and len(self.voices) > 0
        except Exception:
            return False
    
    def get_engine_name(self) -> str:
        """获取引擎名称"""
        return "Piper TTS"
    
    def get_engine_info(self) -> dict:
        """获取引擎信息"""
        return {
            'name': 'Piper TTS',
            'description': '本地神经文本到语音引擎',
            'available': self.is_available(),
            'online': False,
            'voice_count': len(self.voices),
            'models_dir': self.models_dir
        }
    
    def synthesize_bilingual(self, text: str, voice_config: VoiceConfig, chinese_voice_id: str = "zh_CN-huayan-medium", english_voice_id: str = "en_US-amy-medium") -> bytes:
        """中英混合TTS合成 - 基于testpiper.py的实现"""
        try:
            if not text.strip():
                return b''
            
            self.logger.info(f"开始中英混合TTS合成: {text[:50]}...")
            
            # 使用正则表达式分割中英文文本
            bilingual_pattern = r'([\u4e00-\u9fa5]+|[A-Za-z0-9.,!?;:"\s]+)'
            segments = re.findall(bilingual_pattern, text)
            
            if not segments:
                # 如果没有分段，使用默认语音合成
                return self.synthesize(text, voice_config)
            
            self.logger.info(f"文本分段结果: {segments}")
            
            # 为每个分段生成音频
            audio_segments = []
            sample_rate = None
            sample_width = None
            channels = None
            
            for i, segment in enumerate(segments):
                # 判断当前分段是中文还是英文
                language_code = self._detect_language(segment)
                is_chinese = language_code == "zh-CN"
                
                # 选择对应的语音模型
                target_voice_id = chinese_voice_id if is_chinese else english_voice_id
                
                # 创建临时语音配置
                temp_voice_config = VoiceConfig(
                    engine=voice_config.engine,
                    voice_name=target_voice_id,
                    rate=voice_config.rate,
                    pitch=voice_config.pitch,
                    volume=voice_config.volume,
                    language=language_code,
                    output_format=voice_config.output_format
                )
                
                # 合成音频片段
                segment_audio = self.synthesize(segment, temp_voice_config)
                
                if segment_audio:
                    # 将字节数据转换为WAV格式进行合并
                    import io
                    import wave
                    
                    # 创建临时文件处理音频数据
                    temp_file = io.BytesIO(segment_audio)
                    
                    try:
                        with wave.open(temp_file, 'rb') as wav_file:
                            if sample_rate is None:
                                sample_rate = wav_file.getframerate()
                                sample_width = wav_file.getsampwidth()
                                channels = wav_file.getnchannels()
                            
                            # 读取音频数据
                            frames = wav_file.readframes(wav_file.getnframes())
                            audio_segments.append(frames)
                            
                        self.logger.info(f"生成音频片段 {i+1}/{len(segments)}: {'中文' if is_chinese else '英文'} - {segment.strip()}")
                        
                    except Exception as e:
                        self.logger.warning(f"处理音频片段失败: {e}")
                        continue
                else:
                    self.logger.warning(f"音频片段 {i+1} 合成失败")
            
            if not audio_segments:
                self.logger.error("所有音频片段合成失败")
                return b''
            
            # 合并所有音频片段
            output_buffer = io.BytesIO()
            with wave.open(output_buffer, 'wb') as wav_file:
                wav_file.setnchannels(channels)
                wav_file.setsampwidth(sample_width)
                wav_file.setframerate(sample_rate)
                
                # 写入所有音频片段
                for segment in audio_segments:
                    wav_file.writeframes(segment)
            
            result_audio = output_buffer.getvalue()
            self.logger.info(f"中英混合TTS合成完成，音频大小: {len(result_audio)} 字节")
            return result_audio
            
        except Exception as e:
            self.logger.error(f"中英混合TTS合成失败: {e}")
            # 如果混合合成失败，回退到普通合成
            self.logger.info("回退到普通TTS合成")
            return self.synthesize(text, voice_config)
    
    def synthesize_bilingual_to_file(self, text: str, voice_config: VoiceConfig, output_path: str = None, chinese_voice_id: str = "zh_CN-huayan-medium", english_voice_id: str = "en_US-amy-medium") -> str:
        """中英混合TTS合成到文件"""
        try:
            if not text.strip():
                return ""
            
            # 生成输出文件路径
            if not output_path:
                output_path = os.path.join(tempfile.gettempdir(), f"piper_bilingual_tts_{int(time.time())}.wav")
            
            # 确保输出目录存在
            os.makedirs(os.path.dirname(output_path), exist_ok=True)
            
            # 合成音频数据
            audio_data = self.synthesize_bilingual(text, voice_config, chinese_voice_id, english_voice_id)
            
            if audio_data:
                # 保存到文件
                with open(output_path, 'wb') as f:
                    f.write(audio_data)
                
                self.logger.info(f"中英混合TTS合成完成: {output_path}")
                return output_path
            else:
                self.logger.error("中英混合TTS合成失败，无音频数据")
                return ""
                
        except Exception as e:
            self.logger.error(f"中英混合TTS文件合成失败: {e}")
            raise AudioGenerationError(f"中英混合TTS文件合成失败: {e}")


class TTSServiceFactory:
    """TTS服务工厂类 - 使用新的统一架构"""
    
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
        """获取可用引擎列表"""
        engine_manager = cls.get_engine_manager()
        return engine_manager.get_available_engines()
    
    @classmethod
    def get_engine_status(cls, engine: str) -> str:
        """获取引擎状态"""
        engine_manager = cls.get_engine_manager()
        return engine_manager.get_engine_status(engine)
    
    @classmethod
    def create_service(cls, engine: str) -> ITTSService:
        """创建TTS服务实例 - 使用新的统一架构"""
        # 清理引擎名称，移除可用性标记
        clean_engine = engine.replace(" ✓", "").replace(" ✗", "").strip()
        
        if clean_engine not in cls._engines:
            raise UnsupportedTTSEngineError(f"不支持的TTS引擎: {clean_engine}")
        
        # 延迟导入引擎类
        if cls._engines[clean_engine] is None:
            try:
                engine_class = cls._import_engine_class(clean_engine)
                if engine_class:
                    cls._engines[clean_engine] = engine_class
                else:
                    raise AudioGenerationError(f"无法导入引擎类: {clean_engine}")
            except Exception as e:
                raise AudioGenerationError(f"导入{clean_engine}引擎失败: {e}")
        
        try:
            # 创建引擎实例
            engine_instance = cls._engines[clean_engine]()
            
            # 使用适配器包装引擎
            from .tts_engine_adapter import TTSEngineAdapter
            return TTSEngineAdapter(engine_instance)
        except Exception as e:
            raise AudioGenerationError(f"创建{clean_engine}服务失败: {e}")
    
    @classmethod
    def _import_engine_class(cls, engine_id: str):
        """动态导入引擎类"""
        try:
            # 引擎类映射
            engine_class_map = {
                'piper_tts': 'services.piper_tts_engine.PiperTTSEngine',
                'emotivoice_tts_api': 'services.emotivoice_engine.EmotiVoiceEngine',
                'edge_tts': 'services.edge_tts_engine.EdgeTTSEngine',
                'pyttsx3': 'services.pyttsx3_engine.Pyttsx3Engine',
                'index_tts_api_15': 'services.index_tts_engine.IndexTTSEngine'
            }
            
            if engine_id not in engine_class_map:
                return None
            
            class_path = engine_class_map[engine_id]
            module_path, class_name = class_path.rsplit('.', 1)
            
            # 导入模块
            import importlib
            module = importlib.import_module(module_path)
            
            # 获取类
            engine_class = getattr(module, class_name)
            
            return engine_class
            
        except Exception as e:
            print(f"导入引擎类失败 {engine_id}: {e}")
            return None
    
    
    @classmethod
    def get_engine_info(cls, engine: str) -> dict:
        """获取引擎信息"""
        if engine not in cls._engines:
            return {
                'name': engine,
                'description': '未知TTS引擎',
                'available': False,
                'online': False,
                'voice_count': 0
            }
        
        try:
            service = cls._engines[engine]()
            return service.get_engine_info()
        except Exception as e:
            return {
                'name': engine,
                'description': f'TTS引擎初始化失败: {e}',
                'available': False,
                'online': False,
                'voice_count': 0
            }


class TTSService(ITTSService):
    """TTS服务主类 - 使用工厂模式选择引擎"""
    
    def __init__(self, default_engine: str = 'piper_tts'):
        self.logger = LogManager().get_logger("TTSService")
        self.default_engine = default_engine
        self._current_service = None
        self._init_engine()
    
    def _init_engine(self):
        """初始化默认TTS引擎"""
        try:
            self._current_service = TTSServiceFactory.create_service(self.default_engine)
            self.logger.info(f"初始化TTS服务成功，引擎: {self.default_engine}")
        except Exception as e:
            self.logger.error(f"初始化TTS服务失败: {e}")
            # 尝试使用备用引擎
            available_engines = TTSServiceFactory.get_available_engines()
            if available_engines:
                self.default_engine = available_engines[0]
                try:
                    self._current_service = TTSServiceFactory.create_service(self.default_engine)
                    self.logger.info(f"使用备用引擎: {self.default_engine}")
                except Exception as e2:
                    self.logger.error(f"备用引擎初始化也失败: {e2}")
                    self._current_service = None
            else:
                self.logger.error("没有可用的TTS引擎")
                self._current_service = None
    
    def set_engine(self, engine: str):
        """切换TTS引擎"""
        try:
            self._current_service = TTSServiceFactory.create_service(engine)
            self.default_engine = engine
            self.logger.info(f"切换到TTS引擎: {engine}")
        except Exception as e:
            self.logger.error(f"切换TTS引擎失败: {e}")
            raise
    
    def synthesize(self, text: str, voice_config: VoiceConfig) -> bytes:
        """合成语音为字节数据"""
        try:
            if not self._current_service:
                raise AudioGenerationError("没有可用的TTS服务")
            
            # 如果配置的引擎与当前服务不同，切换服务
            if voice_config.engine != self.default_engine:
                self.set_engine(voice_config.engine)
            
            return self._current_service.synthesize(text, voice_config)
            
        except Exception as e:
            self.logger.error(f"语音合成失败: {e}")
            raise
    
    def synthesize_to_file(self, text: str, voice_config: VoiceConfig, output_path: str = None, output_config=None, chapter_info=None) -> str:
        """合成语音到文件"""
        try:
            if not self._current_service:
                raise AudioGenerationError("没有可用的TTS服务")
            
            # 如果配置的引擎与当前服务不同，切换服务
            if voice_config.engine != self.default_engine:
                self.set_engine(voice_config.engine)
            
            # 检查是否是IndexTTSService，需要传递progress_callback参数
            if hasattr(self._current_service, '__class__') and self._current_service.__class__.__name__ == 'IndexTTSService':
                return self._current_service.synthesize_to_file(text, voice_config, output_path, None, output_config, chapter_info)
            else:
                return self._current_service.synthesize_to_file(text, voice_config, output_path, output_config, chapter_info)
            
        except Exception as e:
            self.logger.error(f"语音文件合成失败: {e}")
            raise
    
    def get_available_voices(self) -> List[dict]:
        """获取可用语音列表"""
        try:
            if not self._current_service:
                return []
            
            return self._current_service.get_available_voices()
            
        except Exception as e:
            self.logger.error(f"获取语音列表失败: {e}")
            return []
    
    def get_all_available_voices(self) -> List[dict]:
        """获取所有引擎的可用语音列表"""
        try:
            all_voices = []
            available_engines = self.get_available_engines()
            
            for engine in available_engines:
                try:
                    # 创建引擎服务实例
                    service = TTSServiceFactory.create_service(engine)
                    if service:
                        voices = service.get_available_voices()
                        all_voices.extend(voices)
                        self.logger.debug(f"从 {engine} 获取到 {len(voices)} 个语音")
                except Exception as e:
                    self.logger.warning(f"获取 {engine} 语音失败: {e}")
                    continue
            
            self.logger.info(f"总共获取到 {len(all_voices)} 个语音")
            return all_voices
            
        except Exception as e:
            self.logger.error(f"获取所有语音列表失败: {e}")
            return []
    
    def is_available(self) -> bool:
        """检查引擎是否可用"""
        return self._current_service is not None and self._current_service.is_available()
    
    def get_engine_name(self) -> str:
        """获取引擎名称"""
        if self._current_service:
            return self._current_service.get_engine_name()
        return "无可用引擎"
    
    def get_engine_info(self) -> dict:
        """获取引擎信息"""
        if self._current_service:
            return self._current_service.get_engine_info()
        return {
            'name': '无可用引擎',
            'description': '没有可用的TTS引擎',
            'available': False,
            'online': False,
            'voice_count': 0
        }
    
    def get_all_engines_info(self) -> dict:
        """获取所有引擎信息"""
        engines_info = {}
        for engine_name in TTSServiceFactory._engines.keys():
            engines_info[engine_name] = TTSServiceFactory.get_engine_info(engine_name)
        return engines_info
    
    def get_available_engines(self) -> List[str]:
        """获取可用的引擎列表"""
        return TTSServiceFactory.get_available_engines()
    
    def synthesize_text(self, text: str, voice_config: VoiceConfig, output_path: str = None, output_config=None, chapter_info=None) -> str:
        """合成文本为音频文件（兼容旧接口）"""
        return self.synthesize_to_file(text, voice_config, output_path, output_config, chapter_info)
    
    def is_engine_available(self, engine: str) -> bool:
        """检查指定引擎是否可用（兼容旧接口）"""
        try:
            service = TTSServiceFactory.create_service(engine)
            return service.is_available()
        except Exception:
            return False
    
    def get_engine_info_by_name(self, engine: str) -> dict:
        """根据引擎名称获取信息（兼容旧接口）"""
        return TTSServiceFactory.get_engine_info(engine)
