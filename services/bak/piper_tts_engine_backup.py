#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Piper TTS引擎实现
高质量本地TTS引擎，支持多种语言和语音模型
"""

import os
import tempfile
import time
import json
from typing import List, Dict, Any, Optional

# 使用预加载的 Piper TTS
try:
    from utils.piper_preloader import PIPER_AVAILABLE, get_piper_status
    piper_status = get_piper_status()
    PIPER_AVAILABLE = piper_status['available']
    PiperVoice = piper_status['voice_class']
    SynthesisConfig = piper_status['config_class']
except Exception as e:
    PIPER_AVAILABLE = False
    PiperVoice = None
    SynthesisConfig = None

from .base_tts_engine import BaseTTSEngine, TTSEngineType, TTSVoiceInfo, TTSQuality, TTSResult
from models.audio_model import VoiceConfig
from utils.log_manager import LogManager


class PiperTTSEngine(BaseTTSEngine):
    """Piper TTS引擎实现"""
    
    def __init__(self, engine_id: str = "piper_tts", engine_name: str = "Piper TTS", 
                 engine_type: TTSEngineType = TTSEngineType.OFFLINE, **kwargs):
        # Piper TTS特有参数 - 在调用父类之前设置
        self.models_dir = kwargs.get('models_dir', os.path.join(os.getcwd(), 'models', 'piper'))
        self.use_cuda = kwargs.get('use_cuda', False)
        self.noise_scale = kwargs.get('noise_scale', 0.667)
        self.length_scale = kwargs.get('length_scale', 1.0)
        self.noise_w = kwargs.get('noise_w', 0.8)
        self.sample_rate = kwargs.get('sample_rate', '22050')
        self.bit_depth = kwargs.get('bit_depth', '16')
        
        # 确保 _voices 属性存在
        self._voices = {}
        self.loaded_models = {}  # 缓存已加载的模型
        
        # 加载配置
        self._load_config()
        
        # 调用父类初始化
        super().__init__(engine_id, engine_name, engine_type)
    
    def _load_config(self):
        """加载配置文件"""
        try:
            # 在父类初始化之前，logger 可能不存在，使用 print 代替
            print(f"开始加载Piper TTS配置文件...")
            config_path = os.path.join(os.path.dirname(os.path.dirname(__file__)), "configs", "piper_tts.json")
            print(f"配置文件路径: {config_path}")
            
            if os.path.exists(config_path):
                print(f"配置文件存在，开始读取...")
                with open(config_path, 'r', encoding='utf-8') as f:
                    config = json.load(f)
                print(f"配置文件读取成功，配置项数量: {len(config) if isinstance(config, dict) else 0}")
                
                # 更新参数
                extra_params = config.get('extra_params', {})
                print(f"额外参数数量: {len(extra_params)}")
                
                self.models_dir = extra_params.get('models_dir', self.models_dir)
                self.use_cuda = extra_params.get('use_cuda', self.use_cuda)
                self.noise_scale = extra_params.get('noise_scale', self.noise_scale)
                self.length_scale = extra_params.get('length_scale', self.length_scale)
                self.noise_w = extra_params.get('noise_w', self.noise_w)
                
                print(f"配置参数更新完成:")
                print(f"  模型目录: {self.models_dir}")
                print(f"  使用CUDA: {self.use_cuda}")
            else:
                print(f"配置文件不存在: {config_path}")
                print(f"使用默认配置")
                
        except Exception as e:
            print(f"加载Piper TTS配置失败:")
            print(f"  错误类型: {type(e).__name__}")
            print(f"  错误信息: {e}")
            import traceback
            print(f"  堆栈跟踪: {traceback.format_exc()}")
            # 不抛出异常，使用默认配置
    
    def _load_engine(self):
        """加载Piper TTS引擎"""
        try:
            if not PIPER_AVAILABLE:
                self.logger.warning("Piper TTS库不可用，引擎将显示为不可用状态")
                return
            
            # 确保模型目录存在
            os.makedirs(self.models_dir, exist_ok=True)
            
            self.logger.info("Piper TTS引擎加载成功")
        except Exception as e:
            self.logger.error(f"Piper TTS引擎加载失败: {e}")
            raise
    
    def _load_voices(self):
        """加载Piper TTS语音列表"""
        try:
            self.logger.info(f"开始加载Piper TTS语音配置...")
            
            # 扫描模型目录
            self._scan_model_directory()
            
            # 如果没有找到模型，添加一些默认的语音配置
            if not self._voices:
                self._add_default_voice_configs()
            
            self.logger.info(f"语音配置加载完成: {len(self._voices)} 个语音")
            self.logger.info(f"可用语音ID: {list(self._voices.keys())}")
            
        except Exception as e:
            self.logger.error(f"加载Piper TTS语音配置失败:")
            self.logger.error(f"  错误类型: {type(e).__name__}")
            self.logger.error(f"  错误信息: {e}")
            import traceback
            self.logger.error(f"  堆栈跟踪: {traceback.format_exc()}")
            raise
    
    def _scan_model_directory(self):
        """扫描模型目录，查找可用的语音模型"""
        try:
            if not os.path.exists(self.models_dir):
                self.logger.warning(f"模型目录不存在: {self.models_dir}")
                return
            
            # 扫描子目录，每个子目录包含一个语音模型
            for item in os.listdir(self.models_dir):
                item_path = os.path.join(self.models_dir, item)
                
                # 只处理目录
                if not os.path.isdir(item_path):
                    continue
                
                # 查找该目录下的.onnx文件
                onnx_files = [f for f in os.listdir(item_path) if f.endswith('.onnx')]
                
                if not onnx_files:
                    self.logger.debug(f"目录 {item} 中没有找到.onnx文件")
                    continue
                
                # 使用第一个找到的.onnx文件
                onnx_filename = onnx_files[0]
                voice_id = os.path.splitext(onnx_filename)[0]
                model_path = os.path.join(item_path, onnx_filename)
                
                # 规范化路径，确保使用正确的路径分隔符
                model_path = os.path.normpath(model_path)
                # 确保路径是绝对路径
                model_path = os.path.abspath(model_path)
                
                # 尝试从文件名推断语言和性别
                language, gender = self._parse_voice_filename(onnx_filename)
                
                # 尝试读取模型配置文件获取更多信息
                model_info = self._load_model_info(item_path, onnx_filename)
                
                self._voices[voice_id] = TTSVoiceInfo(
                    id=voice_id,
                    name=model_info.get('name', f'Piper-{voice_id}'),
                    language=language,
                    gender=gender,
                    description=model_info.get('description', f'Piper TTS模型: {onnx_filename}'),
                    engine=self.engine_id,
                    quality=TTSQuality.HIGH,
                    sample_rate=int(self.sample_rate),
                    bit_depth=int(self.bit_depth),
                    channels=1,
                    custom_attributes={
                        'model_path': model_path,
                        'model_dir': item_path,
                        'filename': onnx_filename,
                        'use_cuda': self.use_cuda,
                        'model_info': model_info
                    }
                )
                
                self.logger.debug(f"添加语音模型: {voice_id} - {onnx_filename}")
            
        except Exception as e:
            self.logger.error(f"扫描模型目录失败: {e}")
            raise
    
    def _load_model_info(self, model_dir: str, onnx_filename: str) -> dict:
        """加载模型配置信息"""
        try:
            model_info = {}
            
            # 尝试读取.onnx.json配置文件
            json_filename = onnx_filename.replace('.onnx', '.onnx.json')
            json_path = os.path.join(model_dir, json_filename)
            
            if os.path.exists(json_path):
                try:
                    import json
                    with open(json_path, 'r', encoding='utf-8') as f:
                        config = json.load(f)
                    
                    # 提取语言信息
                    if 'language' in config:
                        lang_info = config['language']
                        if 'code' in lang_info:
                            model_info['language'] = lang_info['code']
                        elif 'name_english' in lang_info:
                            model_info['language'] = lang_info['name_english']
                    
                    # 提取其他有用信息
                    if 'num_speakers' in config:
                        model_info['num_speakers'] = config['num_speakers']
                    
                    if 'audio' in config:
                        audio_info = config['audio']
                        if 'sample_rate' in audio_info:
                            model_info['sample_rate'] = audio_info['sample_rate']
                        if 'quality' in audio_info:
                            model_info['quality'] = audio_info['quality']
                    
                    # 生成友好的名称
                    voice_id = os.path.splitext(onnx_filename)[0]
                    if 'language' in model_info and 'gender' in model_info:
                        lang = model_info['language']
                        gender = model_info['gender']
                        model_info['name'] = f"Piper-{lang}-{gender}"
                        model_info['description'] = f"Piper TTS {lang} {gender} voice model"
                    else:
                        model_info['name'] = f"Piper-{voice_id}"
                        model_info['description'] = f"Piper TTS model: {onnx_filename}"
                    
                    self.logger.debug(f"加载模型配置: {json_path}")
                    
                except Exception as e:
                    self.logger.warning(f"读取模型配置文件失败: {e}")
            
            # 尝试读取MODEL_CARD文件
            model_card_path = os.path.join(model_dir, 'MODEL_CARD')
            if os.path.exists(model_card_path):
                try:
                    with open(model_card_path, 'r', encoding='utf-8') as f:
                        content = f.read()
                        model_info['has_model_card'] = True
                        
                        # 解析MODEL_CARD中的信息
                        lines = content.split('\n')
                        for line in lines:
                            line = line.strip()
                            if line.startswith('* Language:'):
                                # 提取语言信息，例如: "* Language: en_GB (English, Great Britain)"
                                lang_part = line.replace('* Language:', '').strip()
                                if '(' in lang_part:
                                    lang_code = lang_part.split('(')[0].strip()
                                    model_info['language'] = lang_code
                            elif line.startswith('* Quality:'):
                                quality = line.replace('* Quality:', '').strip()
                                model_info['quality'] = quality
                            elif line.startswith('* Samplerate:'):
                                sample_rate = line.replace('* Samplerate:', '').strip()
                                model_info['sample_rate'] = sample_rate
                            elif 'female' in line.lower():
                                model_info['gender'] = 'female'
                            elif 'male' in line.lower():
                                model_info['gender'] = 'male'
                        
                        self.logger.debug(f"从MODEL_CARD解析信息: {model_info}")
                        
                except Exception as e:
                    self.logger.debug(f"读取MODEL_CARD失败: {e}")
            
            # 尝试读取README.md文件
            readme_path = os.path.join(model_dir, 'README.md')
            if os.path.exists(readme_path):
                try:
                    with open(readme_path, 'r', encoding='utf-8') as f:
                        content = f.read()
                        model_info['has_readme'] = True
                        
                        # 解析README中的语言信息
                        if 'language:' in content.lower():
                            lines = content.split('\n')
                            for line in lines:
                                if line.strip().startswith('language:'):
                                    lang = line.split(':')[1].strip()
                                    if not model_info.get('language'):
                                        model_info['language'] = lang
                                    break
                        
                        self.logger.debug(f"从README解析信息: {model_info}")
                        
                except Exception as e:
                    self.logger.debug(f"读取README失败: {e}")
            
            return model_info
            
        except Exception as e:
            self.logger.warning(f"加载模型信息失败: {e}")
            return {}
    
    def _parse_voice_filename(self, filename: str) -> tuple:
        """从文件名解析语言和性别信息"""
        try:
            # 常见的Piper模型命名模式
            # 例如: zh_CN-huayan-medium.onnx, en_US-amy-medium.onnx
            parts = filename.replace('.onnx', '').split('-')
            
            if len(parts) >= 2:
                language = parts[0]  # zh_CN, en_US等
                voice_name = parts[1]  # huayan, amy等
                
                # 改进的性别推断（基于常见名称和模式）
                gender = 'unknown'
                voice_name_lower = voice_name.lower()
                
                # 女性语音标识
                female_indicators = [
                    'female', 'woman', 'girl', 'xiaoxiao', 'huayan', 'cori', 
                    'amy', 'mary', 'sarah', 'lisa', 'anna', 'emma'
                ]
                
                # 男性语音标识
                male_indicators = [
                    'male', 'man', 'boy', 'yunxi', 'yunyang', 'alan', 
                    'john', 'mike', 'david', 'tom', 'james', 'robert'
                ]
                
                if any(name in voice_name_lower for name in female_indicators):
                    gender = 'female'
                elif any(name in voice_name_lower for name in male_indicators):
                    gender = 'male'
                
                return language, gender
            
            return 'unknown', 'unknown'
            
        except Exception as e:
            self.logger.warning(f"解析语音文件名失败: {e}")
            return 'unknown', 'unknown'
    
    def _add_default_voice_configs(self):
        """添加默认语音配置"""
        try:
            # 添加一些常见的默认语音配置
            default_voices = [
                {
                    'id': 'zh_CN-huayan-medium',
                    'name': '华严-中文女声',
                    'language': 'zh-CN',
                    'gender': 'female',
                    'description': 'Piper TTS中文女声模型'
                },
                {
                    'id': 'en_US-amy-medium',
                    'name': 'Amy-英文女声',
                    'language': 'en-US',
                    'gender': 'female',
                    'description': 'Piper TTS英文女声模型'
                },
                {
                    'id': 'en_GB-alan-medium',
                    'name': 'Alan-英文男声',
                    'language': 'en-GB',
                    'gender': 'male',
                    'description': 'Piper TTS英文男声模型'
                }
            ]
            
            for voice_data in default_voices:
                # 构建模型文件路径 - 检查两种可能的路径结构
                model_filename = f"{voice_data['id']}.onnx"
                model_path_flat = os.path.join(self.models_dir, model_filename)
                model_path_nested = os.path.join(self.models_dir, voice_data['id'], model_filename)
                
                # 规范化路径，确保使用正确的路径分隔符
                model_path_flat = os.path.normpath(model_path_flat)
                model_path_nested = os.path.normpath(model_path_nested)
                
                # 优先使用嵌套路径，如果不存在则使用扁平路径
                if os.path.exists(model_path_nested):
                    model_path = model_path_nested
                elif os.path.exists(model_path_flat):
                    model_path = model_path_flat
                else:
                    model_path = model_path_nested  # 默认使用嵌套路径
                
                # 确保路径是绝对路径
                model_path = os.path.abspath(model_path)
                
                self._voices[voice_data['id']] = TTSVoiceInfo(
                    id=voice_data['id'],
                    name=voice_data['name'],
                    language=voice_data['language'],
                    gender=voice_data['gender'],
                    description=voice_data['description'],
                    engine=self.engine_id,
                    quality=TTSQuality.HIGH,
                    sample_rate=int(self.sample_rate),
                    bit_depth=int(self.bit_depth),
                    channels=1,
                    custom_attributes={
                        'model_path': model_path,
                        'requires_model': True,
                        'use_cuda': self.use_cuda,
                        'model_exists': os.path.exists(model_path)
                    }
                )
            
            self.logger.info(f"添加了 {len(default_voices)} 个默认语音配置")
            
        except Exception as e:
            self.logger.error(f"添加默认语音配置失败: {e}")
            raise
    
    def _synthesize_audio(self, text: str, voice_config: VoiceConfig) -> bytes:
        """合成音频数据"""
        try:
            if not PIPER_AVAILABLE:
                raise Exception("Piper TTS库不可用")
            
            self.logger.info(f"开始Piper TTS合成，语音: {voice_config.voice_name}")
            
            # 获取语音配置
            voice_name = voice_config.voice_name or 'zh_CN-huayan-medium'
            
            # 安全获取语音信息
            if voice_name in self._voices:
                voice_info = self._voices[voice_name]
            else:
                voice_info = self._voices.get('zh_CN-huayan-medium', list(self._voices.values())[0])
                self.logger.warning(f"语音 '{voice_name}' 不存在，使用默认语音")
            
            # 检查是否需要模型文件
            if hasattr(voice_info, 'custom_attributes') and voice_info.custom_attributes.get('requires_model'):
                model_path = voice_info.custom_attributes.get('model_path')
                if not model_path or not os.path.exists(model_path):
                    # 尝试找到其他可用的语音
                    available_voices = [v for v in self._voices.values() 
                                      if v.custom_attributes.get('model_exists', False)]
                    if available_voices:
                        voice_info = available_voices[0]
                        self.logger.warning(f"语音 '{voice_name}' 的模型文件不存在，使用可用语音: {voice_info.id}")
                    else:
                        raise Exception(f"语音 '{voice_name}' 需要模型文件，但文件不存在: {model_path}。请下载相应的模型文件到 {self.models_dir} 目录。")
            
            # 生成临时文件路径
            temp_wav = os.path.join(tempfile.gettempdir(), f"piper_temp_{int(time.time())}.wav")
            
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
            
            self.logger.info(f"Piper TTS合成完成，音频大小: {len(audio_data)} 字节")
            return audio_data
            
        except Exception as e:
            self.logger.error(f"Piper TTS合成失败: {e}")
            raise
    
    def synthesize_to_file(self, text: str, voice_config: VoiceConfig, output_path: str = None, 
                          output_config=None, chapter_info=None) -> str:
        """合成语音到文件"""
        try:
            if not text.strip():
                return ""
            
            if not PIPER_AVAILABLE:
                raise Exception("Piper TTS库不可用")
            
            self.logger.info(f"开始Piper TTS文件合成，语音: {voice_config.voice_name}")
            
            # 生成输出文件路径
            if not output_path:
                if output_config and hasattr(output_config, 'naming_mode'):
                    # 使用输出设置中的文件命名规则
                    output_path = self._generate_output_path(voice_config, output_config, text, chapter_info)
                else:
                    # 使用统一的命名规则
                    output_path = os.path.join(tempfile.gettempdir(), f"piper_{voice_config.voice_name}.wav")
            
            # 确保输出目录存在
            os.makedirs(os.path.dirname(output_path), exist_ok=True)
            
            # 获取语音配置
            voice_name = voice_config.voice_name or 'zh_CN-huayan-medium'
            
            # 安全获取语音信息
            if voice_name in self._voices:
                voice_info = self._voices[voice_name]
            else:
                voice_info = self._voices.get('zh_CN-huayan-medium', list(self._voices.values())[0])
                self.logger.warning(f"语音 '{voice_name}' 不存在，使用默认语音")
            
            # 检查是否需要模型文件
            if hasattr(voice_info, 'custom_attributes') and voice_info.custom_attributes.get('requires_model'):
                model_path = voice_info.custom_attributes.get('model_path')
                if not model_path or not os.path.exists(model_path):
                    # 尝试找到其他可用的语音
                    available_voices = [v for v in self._voices.values() 
                                      if v.custom_attributes.get('model_exists', False)]
                    if available_voices:
                        voice_info = available_voices[0]
                        self.logger.warning(f"语音 '{voice_name}' 的模型文件不存在，使用可用语音: {voice_info.id}")
                    else:
                        raise Exception(f"语音 '{voice_name}' 需要模型文件，但文件不存在: {model_path}。请下载相应的模型文件到 {self.models_dir} 目录。")
            
            # 加载或获取缓存的模型
            model = self._get_or_load_model(voice_name, voice_info)
            
            # 创建合成配置
            config = SynthesisConfig(
                noise_scale=self.noise_scale,
                length_scale=self.length_scale
            )
            
            # 合成语音
            start_time = time.time()
            
            # 使用synthesize_wav方法保存到文件
            import wave
            with wave.open(output_path, 'wb') as wav_file:
                model.synthesize_wav(text, wav_file, config)
            
            end_time = time.time()
            
            self.logger.info(f"Piper TTS文件合成完成: {output_path}，耗时: {end_time - start_time:.2f}秒")
            return output_path
            
        except Exception as e:
            self.logger.error(f"Piper TTS文件合成失败: {e}")
            raise
    
    def _get_or_load_model(self, voice_name: str, voice_info: TTSVoiceInfo) -> Any:
        """获取或加载Piper模型"""
        try:
            # 检查是否已加载
            if voice_name in self.loaded_models:
                return self.loaded_models[voice_name]
            
            # 获取模型路径
            model_path = voice_info.custom_attributes.get('model_path')
            if not model_path or not os.path.exists(model_path):
                raise Exception(f"模型文件不存在: {model_path}")
            
            # 加载模型
            self.logger.info(f"加载Piper模型: {model_path}")
            model = PiperVoice.load(model_path, use_cuda=self.use_cuda)
            
            # 缓存模型
            self.loaded_models[voice_name] = model
            
            return model
            
        except Exception as e:
            self.logger.error(f"加载Piper模型失败: {e}")
            raise
    
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
                filename = f"piper_{int(time.time())}"
            
            # 限制文件名长度
            if len(filename) > name_length_limit:
                filename = filename[:name_length_limit]
            
            # 清理文件名中的非法字符（保留路径分隔符）
            filename = re.sub(r'[<>:"|?*]', '_', filename)
            
            # 使用os.path.normpath确保路径格式一致
            full_path = os.path.join(output_dir, f"{filename}{file_format}")
            return os.path.normpath(full_path)
            
        except Exception as e:
            self.logger.error(f"生成输出路径失败: {e}")
            return os.path.join(tempfile.gettempdir(), f"piper_{int(time.time())}.wav")
    
    def _apply_custom_template(self, template: str, chapter_info, text: str) -> str:
        """应用自定义模板"""
        try:
            if not chapter_info:
                return template.replace('{title}', text[:20]).replace('{chapter_num}', '01')
            
            # 替换模板变量
            result = template
            if hasattr(chapter_info, 'title'):
                result = result.replace('{title}', str(chapter_info.title))
            if hasattr(chapter_info, 'chapter_num'):
                result = result.replace('{chapter_num:02d}', f"{int(chapter_info.chapter_num):02d}")
                result = result.replace('{chapter_num}', str(int(chapter_info.chapter_num)))
            if hasattr(chapter_info, 'index'):
                result = result.replace('{index:02d}', f"{int(chapter_info.index):02d}")
                result = result.replace('{index}', str(int(chapter_info.index)))
            
            return result
        except Exception as e:
            self.logger.error(f"应用自定义模板失败: {e}")
            return f"piper_{int(time.time())}"
    
    def _generate_chapter_title_name(self, chapter_info, text: str) -> str:
        """生成章节序号+标题文件名"""
        try:
            if not chapter_info:
                return f"01_{text[:20]}"
            
            chapter_num = getattr(chapter_info, 'chapter_num', 1)
            title = getattr(chapter_info, 'title', text[:20])
            return f"{int(chapter_num):02d}_{title}"
        except Exception as e:
            self.logger.error(f"生成章节标题文件名失败: {e}")
            return f"01_{text[:20]}"
    
    def _generate_number_title_name(self, chapter_info, text: str) -> str:
        """生成序号+标题文件名"""
        try:
            if not chapter_info:
                return f"01_{text[:20]}"
            
            index = getattr(chapter_info, 'index', 1)
            title = getattr(chapter_info, 'title', text[:20])
            return f"{int(index):02d}_{title}"
        except Exception as e:
            self.logger.error(f"生成序号标题文件名失败: {e}")
            return f"01_{text[:20]}"
    
    def _generate_title_only_name(self, chapter_info, text: str) -> str:
        """生成仅标题文件名"""
        try:
            if not chapter_info:
                return text[:20]
            
            title = getattr(chapter_info, 'title', text[:20])
            return title
        except Exception as e:
            self.logger.error(f"生成标题文件名失败: {e}")
            return text[:20]
    
    def _generate_number_only_name(self, chapter_info, text: str) -> str:
        """生成仅序号文件名"""
        try:
            if not chapter_info:
                return "01"
            
            chapter_num = getattr(chapter_info, 'chapter_num', 1)
            return f"{int(chapter_num):02d}"
        except Exception as e:
            self.logger.error(f"生成序号文件名失败: {e}")
            return "01"
    
    def _generate_original_filename(self, chapter_info, text: str) -> str:
        """生成原始文件名"""
        try:
            if not chapter_info:
                return f"piper_{int(time.time())}"
            
            # 尝试从章节信息中获取原始文件名
            if hasattr(chapter_info, 'original_filename') and chapter_info.original_filename:
                # 清理路径，只保留文件名
                filename = os.path.basename(chapter_info.original_filename)
                # 移除扩展名
                name, _ = os.path.splitext(filename)
                return name
            elif hasattr(chapter_info, 'title') and chapter_info.title:
                return chapter_info.title
            else:
                return f"piper_{int(time.time())}"
        except Exception as e:
            self.logger.error(f"生成原始文件名失败: {e}")
            return f"piper_{int(time.time())}"
    
    def get_available_voices(self) -> List[TTSVoiceInfo]:
        """获取可用语音列表 - 从模型目录扫描获取"""
        try:
            # 如果还没有加载语音，先加载
            if not self._voices:
                self._load_voices()
            
            # 返回所有扫描到的语音
            voices = list(self._voices.values())
            
            if voices:
                self.logger.info(f"Piper TTS返回 {len(voices)} 个可用语音: {[v.id for v in voices]}")
                return voices
            else:
                self.logger.warning("Piper TTS没有找到可用语音模型")
                return []
                
        except Exception as e:
            self.logger.error(f"获取Piper TTS语音列表失败: {e}")
            return []
    
    def is_available(self) -> bool:
        """检查引擎是否可用"""
        try:
            return PIPER_AVAILABLE and len(self._voices) > 0
        except Exception:
            return False
    
    def add_voice(self, voice_id: str, name: str, model_path: str, language: str = 'zh-CN', gender: str = 'unknown'):
        """添加自定义语音配置"""
        try:
            # 规范化路径，确保使用正确的路径分隔符
            model_path = os.path.normpath(model_path)
            # 确保路径是绝对路径
            model_path = os.path.abspath(model_path)
            
            if not os.path.exists(model_path):
                raise Exception(f"模型文件不存在: {model_path}")
            
            self._voices[voice_id] = TTSVoiceInfo(
                id=voice_id,
                name=name,
                language=language,
                gender=gender,
                description=f'自定义语音: {name}',
                engine=self.engine_id,
                quality=TTSQuality.HIGH,
                sample_rate=int(self.sample_rate),
                bit_depth=int(self.bit_depth),
                channels=1,
                custom_attributes={
                    'model_path': model_path,
                    'requires_model': True,
                    'use_cuda': self.use_cuda
                }
            )
            
            self.logger.info(f"添加自定义语音: {voice_id} - {name}")
            
        except Exception as e:
            self.logger.error(f"添加自定义语音失败: {e}")
            raise
    
    def remove_voice(self, voice_id: str):
        """移除语音配置"""
        try:
            if voice_id in self._voices:
                del self._voices[voice_id]
                # 清理缓存的模型
                if voice_id in self.loaded_models:
                    del self.loaded_models[voice_id]
                self.logger.info(f"移除语音配置: {voice_id}")
            else:
                self.logger.warning(f"语音配置不存在: {voice_id}")
                
        except Exception as e:
            self.logger.error(f"移除语音配置失败: {e}")
            raise
