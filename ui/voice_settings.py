"""
语音设置界面模块

提供TTS语音参数的配置界面，包括：
- 语音引擎选择（Piper TTS、Edge TTS等）
- 语音参数设置（语速、音调、音量等）
- 动态参数配置（根据引擎类型显示不同参数）
- 语音预览和测试功能
- 配置保存和加载

作者: TTS开发团队
版本: 1.0.0
创建时间: 2024
"""

# 先导入 piper，避免 PyQt6 的兼容性问题
try:
    from piper import PiperVoice, SynthesisConfig
    print("[OK] Piper TTS 在语音设置界面预加载成功")
except Exception as e:
    print(f"[WARN] Piper TTS 在语音设置界面预加载失败: {e}")

from PyQt6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QLabel, 
    QComboBox, QSlider, QSpinBox, QPushButton,
    QGroupBox, QFormLayout, QTextEdit, QMessageBox,
    QProgressBar, QFrame, QScrollArea
)
from PyQt6.QtCore import Qt, pyqtSignal, QThread
from PyQt6.QtGui import QFont
from datetime import datetime
from typing import Optional
from services.language_service import get_text as tr

from controllers.audio_controller import AudioController
from models.audio_model import VoiceConfig
from utils.log_manager import LogManager
from utils.feature_flags import feature_flags
from utils.backup_manager import backup_manager
from ui.dynamic_parameter_ui import DynamicParameterUI
from services.parameter_config_service import ParameterConfigService
from services.tts_service import TTSServiceFactory


class VoiceSettingsWidget(QWidget):
    """
    语音设置界面组件
    
    提供完整的语音参数配置功能，支持多种TTS引擎的参数设置。
    采用动态参数UI设计，根据选择的引擎类型显示相应的参数配置项。
    
    特性：
    - 多引擎支持：Piper TTS、Edge TTS等
    - 动态参数：根据引擎类型动态显示参数配置
    - 实时预览：支持语音参数实时预览和测试
    - 配置管理：自动保存和加载用户配置
    - 参数验证：确保参数值的有效性和安全性
    """
    
    # 信号定义 - 用于与主窗口通信
    voice_changed = pyqtSignal(object)  # 语音设置改变信号，传递VoiceConfig对象
    
    def __init__(self, audio_controller: AudioController):
        super().__init__()
        self.audio_controller = audio_controller
        self.logger = LogManager().get_logger("VoiceSettingsWidget")
        
        # 配置服务
        from services.config.app_config_service import AppConfigService
        from services.config.engine_config_service import EngineConfigService
        self.app_config_service = AppConfigService()
        self.engine_config_service = EngineConfigService()
        
        # 参数配置服务
        self.parameter_config_service = ParameterConfigService()
        
        # 当前语音配置
        self.current_voice_config = VoiceConfig()
        
        # 可用语音列表
        self.available_voices = []
        
        # 输出设置页面引用
        self.output_settings_widget = None
        
        # 动态参数UI
        self.dynamic_parameter_ui = None
        
        # 初始化标志，避免死循环
        self._initializing = True
        
        # 初始化UI
        self.setup_ui()
        self.setup_connections()
        self.load_voices()
        self.load_config()
        
        # 初始化完成后，确保动态参数界面被正确加载
        self._ensure_dynamic_ui_loaded()
    
    def _ensure_dynamic_ui_loaded(self):
        """确保动态参数界面被正确加载"""
        try:
            current_engine_text = self.engine_combo.currentText()
            if current_engine_text:
                self.logger.info(tr("voice_settings.messages.ensure_dynamic_ui_loaded").format(engine=current_engine_text))
                self.on_engine_changed(current_engine_text)
        except Exception as e:
            self.logger.error(tr("voice_settings.messages.ensure_dynamic_ui_loaded_failed").format(error=e))
    
    def _load_edge_tts_languages(self):
        """加载Edge-TTS支持的语言列表"""
        try:
            import json
            import os
            
            # 构建语言字典文件路径
            current_dir = os.path.dirname(__file__)  # ui目录
            project_root = os.path.dirname(current_dir)  # 4Code目录
            language_file_path = os.path.join(project_root, "configs", "dicts", "edge_tts_language.json")
            
            if not os.path.exists(language_file_path):
                self.logger.warning(f"Edge-TTS语言字典文件不存在: {language_file_path}")
                return []
            
            # 读取语言字典文件
            with open(language_file_path, 'r', encoding='utf-8') as f:
                language_data = json.load(f)
            
            # 提取语言列表
            languages = []
            for lang_code, lang_info in language_data.get('languages', {}).items():
                lang_name = lang_info.get('name', lang_code)
                voices_count = lang_info.get('voices_count', 0)
                display_text = f"{lang_name} ({lang_code}) - {voices_count}个语音"
                languages.append((display_text, lang_code))
            
            # 按推荐顺序排序
            recommended_languages = language_data.get('recommended_languages', [])
            sorted_languages = []
            
            # 先添加推荐语言
            for rec_lang in recommended_languages:
                for display_text, lang_code in languages:
                    if lang_code == rec_lang:
                        sorted_languages.append((display_text, lang_code))
                        break
            
            # 再添加其他语言
            for display_text, lang_code in languages:
                if lang_code not in recommended_languages:
                    sorted_languages.append((display_text, lang_code))
            
            self.logger.info(tr("voice_settings.messages.loaded_edge_tts_languages").format(count=len(sorted_languages)))
            return sorted_languages
            
        except Exception as e:
            self.logger.error(tr("voice_settings.messages.load_edge_tts_languages_failed").format(error=e))
            return []
    
    def _update_language_combo_for_edge_tts(self):
        """为Edge-TTS更新语言选择框"""
        try:
            # 获取Edge-TTS支持的语言列表
            edge_tts_languages = self._load_edge_tts_languages()
            
            if edge_tts_languages:
                # 清空现有选项
                self.language_combo.clear()
                
                # 添加Edge-TTS支持的语言
                for display_text, lang_code in edge_tts_languages:
                    self.language_combo.addItem(display_text, lang_code)
                
                # 设置默认选择为中文（普通话）
                current_language = getattr(self.current_voice_config, 'language', 'zh-CN')
                for i in range(self.language_combo.count()):
                    if self.language_combo.itemData(i) == current_language:
                        self.language_combo.setCurrentIndex(i)
                        break
                else:
                    # 如果没找到当前语言，选择第一个（通常是中文）
                    self.language_combo.setCurrentIndex(0)
                
                self.logger.info(tr("voice_settings.messages.updated_edge_tts_language_combo").format(count=len(edge_tts_languages)))
            else:
                self.logger.warning(tr("voice_settings.messages.no_edge_tts_languages"))
                
        except Exception as e:
            self.logger.error(tr("voice_settings.messages.update_edge_tts_language_combo_failed").format(error=e))
    
    def setup_ui(self):
        """设置用户界面"""
        layout = QVBoxLayout(self)
        layout.setContentsMargins(5, 5, 5, 5)
        layout.setSpacing(10)
        
        # 标题
        title_label = QLabel(tr("voice_settings.title"))
        title_label.setStyleSheet("font-size: 16px; font-weight: bold; margin-bottom: 10px;")
        layout.addWidget(title_label)
        
        # 创建滚动区域
        scroll_area = QScrollArea()
        scroll_area.setWidgetResizable(True)
        scroll_area.setFrameStyle(QFrame.Shape.NoFrame)
        
        scroll_widget = QWidget()
        scroll_layout = QVBoxLayout(scroll_widget)
        scroll_layout.setContentsMargins(5, 5, 5, 5)
        
        # 配置管理组 - 移到最上面
        config_group = QGroupBox(tr("voice_settings.voice_config"))
        config_layout = QVBoxLayout(config_group)
        
        # 配置管理按钮
        config_button_layout = QHBoxLayout()
        
        self.save_config_button = QPushButton(tr("voice_settings.save_preset"))
        self.save_config_button.clicked.connect(self.save_config)
        config_button_layout.addWidget(self.save_config_button)
        
        self.load_config_button = QPushButton(tr("voice_settings.load_preset"))
        self.load_config_button.clicked.connect(self.load_config)
        config_button_layout.addWidget(self.load_config_button)
        
        self.export_config_button = QPushButton(tr("voice_settings.export_preset"))
        self.export_config_button.clicked.connect(self.export_config)
        config_button_layout.addWidget(self.export_config_button)
        
        self.import_config_button = QPushButton(tr("voice_settings.import_preset"))
        self.import_config_button.clicked.connect(self.import_config)
        config_button_layout.addWidget(self.import_config_button)
        
        self.reset_button = QPushButton(tr("voice_settings.reset_defaults"))
        self.reset_button.clicked.connect(self.reset_settings)
        config_button_layout.addWidget(self.reset_button)
        
        config_layout.addLayout(config_button_layout)
        
        # 配置状态显示
        self.config_status_label = QLabel(tr("voice_settings.config_status_unsaved"))
        self.config_status_label.setStyleSheet("color: #666; font-size: 12px;")
        config_layout.addWidget(self.config_status_label)
        
        scroll_layout.addWidget(config_group)
        
        # TTS引擎设置组
        engine_group = QGroupBox(tr("voice_settings.tts_engine_settings"))
        engine_layout = QFormLayout(engine_group)
        
        # 引擎选择
        self.engine_combo = QComboBox()
        self.load_available_engines()
        self.engine_combo.currentTextChanged.connect(self.on_engine_changed)
        engine_layout.addRow(tr("voice_settings.tts_engine"), self.engine_combo)
        
        # 引擎状态
        self.engine_status_label = QLabel(tr("voice_settings.checking"))
        self.engine_status_label.setStyleSheet("color: #666; font-size: 12px;")
        engine_layout.addRow(tr("voice_settings.status"), self.engine_status_label)
        
        scroll_layout.addWidget(engine_group)
        
        # 语音选择组（仅用于Edge TTS和pyttsx3）
        self.voice_group = QGroupBox(tr("voice_settings.voice_selection"))
        voice_layout = QFormLayout(self.voice_group)
        
        # 语音选择
        self.voice_combo = QComboBox()
        self.voice_combo.currentTextChanged.connect(self.on_voice_changed)
        voice_layout.addRow(tr("voice_settings.voice"), self.voice_combo)
        
        # 语言选择
        self.language_combo = QComboBox()
        # 初始时添加通用语言选项，具体语言将在引擎切换时动态加载
        self.language_combo.addItems(["zh-CN", "zh-US", "en-US", "ja-JP"])
        self.language_combo.currentTextChanged.connect(self.on_language_changed)
        voice_layout.addRow(tr("voice_settings.language"), self.language_combo)
        
        scroll_layout.addWidget(self.voice_group)
        
        # 动态参数设置组
        self.create_dynamic_parameter_group(scroll_layout)
        
        # 输出格式设置组
        format_group = QGroupBox(tr("voice_settings.output_format_settings"))
        format_layout = QFormLayout(format_group)
        
        # 默认输出格式（固定为WAV，不允许更改）
        self.output_format_combo = QComboBox()
        self.output_format_combo.addItems(["WAV"])
        self.output_format_combo.setCurrentText("WAV")
        self.output_format_combo.setEnabled(False)  # 禁用下拉框
        # 不再需要连接信号，因为用户无法更改
        # self.output_format_combo.activated.connect(self.on_output_format_activated)
        format_layout.addRow(tr("voice_settings.default_output_format"), self.output_format_combo)
        
        # Edge TTS格式说明
        self.format_note_label = QLabel(tr("voice_settings.format_note_edge"))
        self.format_note_label.setStyleSheet("color: #666; font-size: 11px;")
        format_layout.addRow("", self.format_note_label)
        
        scroll_layout.addWidget(format_group)
        
        # 语音参数组
        params_group = QGroupBox(tr("voice_settings.voice_parameters"))
        params_layout = QFormLayout(params_group)
        
        # 语速设置
        self.rate_slider = QSlider(Qt.Orientation.Horizontal)
        self.rate_slider.setRange(10, 300)
        self.rate_slider.setValue(100)
        self.rate_slider.valueChanged.connect(self.on_rate_changed)
        
        self.rate_label = QLabel("100%")
        self.rate_label.setMinimumWidth(50)
        
        rate_layout = QHBoxLayout()
        rate_layout.addWidget(self.rate_slider)
        rate_layout.addWidget(self.rate_label)
        params_layout.addRow(tr("voice_settings.rate"), rate_layout)
        
        # 音调设置
        self.pitch_slider = QSlider(Qt.Orientation.Horizontal)
        self.pitch_slider.setRange(-50, 50)
        self.pitch_slider.setValue(0)
        self.pitch_slider.valueChanged.connect(self.on_pitch_changed)
        
        self.pitch_label = QLabel("0%")
        self.pitch_label.setMinimumWidth(50)
        
        pitch_layout = QHBoxLayout()
        pitch_layout.addWidget(self.pitch_slider)
        pitch_layout.addWidget(self.pitch_label)
        params_layout.addRow(tr("voice_settings.pitch"), pitch_layout)
        
        # 音量设置
        self.volume_slider = QSlider(Qt.Orientation.Horizontal)
        self.volume_slider.setRange(0, 100)
        self.volume_slider.setValue(100)
        self.volume_slider.valueChanged.connect(self.on_volume_changed)
        
        self.volume_label = QLabel("100%")
        self.volume_label.setMinimumWidth(50)
        
        volume_layout = QHBoxLayout()
        volume_layout.addWidget(self.volume_slider)
        volume_layout.addWidget(self.volume_label)
        params_layout.addRow(tr("voice_settings.volume"), volume_layout)
        
        scroll_layout.addWidget(params_group)
        
        # 测试区域组（隐藏）
        # test_group = QGroupBox("语音测试")
        # test_layout = QVBoxLayout(test_group)
        # 
        # # 测试文本
        # test_layout.addWidget(QLabel("测试文本:"))
        # self.test_text = QTextEdit()
        # self.test_text.setMaximumHeight(80)
        # self.test_text.setPlainText("你好，这是一个语音测试。Hello, this is a voice test.")
        # test_layout.addWidget(self.test_text)
        # 
        # # 测试按钮
        # test_button_layout = QHBoxLayout()
        # 
        # self.test_button = QPushButton("测试语音")
        # self.test_button.clicked.connect(self.test_voice)
        # test_button_layout.addWidget(self.test_button)
        # 
        # self.stop_test_button = QPushButton("停止测试")
        # self.stop_test_button.clicked.connect(self.stop_test)
        # self.stop_test_button.setEnabled(False)
        # test_button_layout.addWidget(self.stop_test_button)
        # 
        # test_layout.addLayout(test_button_layout)
        # 
        # # 进度条
        # self.progress_bar = QProgressBar()
        # self.progress_bar.setVisible(False)
        # test_layout.addWidget(self.progress_bar)
        # 
        # scroll_layout.addWidget(test_group)
        # 
        # # 音频信息组（隐藏）
        # info_group = QGroupBox("音频信息")
        # info_layout = QVBoxLayout(info_group)
        # 
        # self.info_text = QTextEdit()
        # self.info_text.setReadOnly(True)
        # self.info_text.setMaximumHeight(100)
        # self.info_text.setPlainText("暂无音频信息")
        # info_layout.addWidget(self.info_text)
        # 
        # scroll_layout.addWidget(info_group)
        
        # 按钮组（隐藏）
        button_group = QGroupBox(tr("voice_settings.operations"))
        button_layout = QHBoxLayout(button_group)
        
        self.apply_button = QPushButton(tr("voice_settings.apply_settings"))
        self.apply_button.clicked.connect(self.apply_settings)
        button_layout.addWidget(self.apply_button)
        
        # 隐藏操作组
        button_group.hide()
        
        # scroll_layout.addWidget(button_group)
        
        scroll_area.setWidget(scroll_widget)
        layout.addWidget(scroll_area)
    
    def setup_connections(self):
        """设置信号槽连接"""
        # 语言切换支持
        from services.language_service import get_language_service
        language_service = get_language_service()
        language_service.language_changed.connect(self.on_language_changed)
    
    def on_language_changed(self):
        """语言切换事件"""
        try:
            # 重新创建UI以更新翻译
            self.recreate_ui()
        except Exception as e:
            self.logger.error(f"语言切换失败: {e}")
    
    def recreate_ui(self):
        """重新创建UI"""
        try:
            # 保存当前状态
            current_engine = self.engine_combo.currentText() if hasattr(self, 'engine_combo') else ""
            current_voice = self.voice_combo.currentText() if hasattr(self, 'voice_combo') else ""
            current_language = self.language_combo.currentText() if hasattr(self, 'language_combo') else ""
            
            # 清除现有UI
            layout = self.layout()
            if layout:
                while layout.count():
                    child = layout.takeAt(0)
                    if child.widget():
                        child.widget().deleteLater()
            
            # 重新创建UI
            self.setup_ui()
            self.setup_connections()
            
            # 恢复状态
            if hasattr(self, 'engine_combo') and current_engine:
                try:
                    index = self.engine_combo.findText(current_engine)
                    if index >= 0:
                        self.engine_combo.setCurrentIndex(index)
                except:
                    pass
            
            if hasattr(self, 'voice_combo') and current_voice:
                try:
                    index = self.voice_combo.findText(current_voice)
                    if index >= 0:
                        self.voice_combo.setCurrentIndex(index)
                except:
                    pass
            
            if hasattr(self, 'language_combo') and current_language:
                try:
                    index = self.language_combo.findText(current_language)
                    if index >= 0:
                        self.language_combo.setCurrentIndex(index)
                except:
                    pass
            
        except Exception as e:
            self.logger.error(f"重新创建UI失败: {e}")
    
    def create_dynamic_parameter_group(self, parent_layout):
        """创建动态参数设置组"""
        # 动态参数组
        self.dynamic_parameter_group = QGroupBox(tr("voice_settings.engine_parameter_settings"))
        dynamic_layout = QVBoxLayout(self.dynamic_parameter_group)
        
        # 创建动态参数UI
        self.dynamic_parameter_ui = DynamicParameterUI()
        self.dynamic_parameter_ui.parameters_changed.connect(self.on_dynamic_parameters_changed)
        self.dynamic_parameter_ui.validation_changed.connect(self.on_dynamic_validation_changed)
        
        # 设置动态参数UI的最小高度
        self.dynamic_parameter_ui.setMinimumHeight(400)  # 设置最小高度为400像素
        
        dynamic_layout.addWidget(self.dynamic_parameter_ui)
        parent_layout.addWidget(self.dynamic_parameter_group)
        
        # 初始时隐藏，等待引擎选择
        self.dynamic_parameter_group.setVisible(False)
    
    def set_output_settings_widget(self, output_settings_widget):
        """设置输出设置页面引用"""
        self.output_settings_widget = output_settings_widget
    
    def set_default_parameter_values(self, engine: str):
        """设置默认参数值"""
        try:
            # 功能开关检查
            if not feature_flags.is_enabled('voice_settings_defaults'):
                self.logger.info(f"语音设置默认值功能已禁用，跳过 {engine}")
                return
            
            if not self.dynamic_parameter_ui:
                self.logger.warning("动态参数UI未初始化，跳过默认值设置")
                return
            
            # 创建备份
            if feature_flags.is_enabled('debug_logging'):
                backup_manager.create_backup('config.json', f'before_{engine}_defaults')
            
            # 获取默认值
            default_values = self.parameter_config_service.get_default_values(engine)
            
            # 为不同引擎设置特殊的默认值
            if engine == "pyttsx3":
                # pyttsx3使用系统默认语音
                from services.tts_service import TTSServiceFactory
                tts_service = TTSServiceFactory.create_service(engine)
                if tts_service:
                    voices = tts_service.get_available_voices()
                    if voices:
                        # 使用第一个可用的语音
                        default_voice_id = voices[0]['id']
                        default_values['voice_name'] = default_voice_id
                        
                        self.logger.info(f"pyttsx3默认语音配置: {default_voice_id}")
            
            elif engine == "piper_tts":
                # Piper TTS使用默认语音
                from services.tts_service import TTSServiceFactory
                tts_service = TTSServiceFactory.create_service(engine)
                if tts_service:
                    voices = tts_service.get_available_voices()
                    if voices:
                        # 优先使用zh_CN-huayan-medium，如果不存在则使用第一个
                        default_voice_id = "zh_CN-huayan-medium"
                        found_default = False
                        
                        for voice in voices:
                            if voice['id'] == default_voice_id:
                                found_default = True
                                break
                        
                        if not found_default:
                            # 如果没找到zh_CN-huayan-medium，使用第一个可用的
                            default_voice_id = voices[0]['id']
                        
                        default_values['voice_name'] = default_voice_id
                        
                        # 设置对应的模型路径
                        for voice in voices:
                            if voice['id'] == default_voice_id:
                                default_values['model_path'] = voice.get('model_path', '')
                                break
                        
                        self.logger.info(f"Piper TTS默认语音配置: {default_values['voice_name']}")
                        self.logger.info(f"对应模型路径: {default_values.get('model_path', 'N/A')}")
            
            elif engine == "edge_tts":
                # Edge TTS使用新的JSON文件语音加载功能
                from services.tts_service import TTSServiceFactory
                tts_service = TTSServiceFactory.create_service(engine)
                if tts_service:
                    try:
                        # 使用新的语音管理方法
                        voices = tts_service.get_available_voices()
                        if voices:
                            # 优先使用热门语音
                            popular_voices = tts_service.get_popular_voices()
                            if popular_voices:
                                # 优先选择中文热门语音
                                chinese_popular = [v for v in popular_voices if v.language.startswith('zh')]
                                if chinese_popular:
                                    default_voice_id = chinese_popular[0].id
                                    default_values['language'] = chinese_popular[0].language
                                else:
                                    default_voice_id = popular_voices[0].id
                                    default_values['language'] = popular_voices[0].language
                            else:
                                # 如果没有热门语音，寻找中文语音
                                chinese_voices = tts_service.get_voice_by_language('zh-CN')
                                if chinese_voices:
                                    default_voice_id = chinese_voices[0].id
                                    default_values['language'] = chinese_voices[0].language
                                else:
                                    # 使用第一个可用语音
                                    default_voice_id = voices[0].id
                                    default_values['language'] = voices[0].language
                            
                            default_values['voice_name'] = default_voice_id
                            
                            self.logger.info(f"Edge TTS默认语音配置: {default_values['voice_name']}")
                            self.logger.info(f"对应语言: {default_values.get('language', 'N/A')}")
                            self.logger.info(f"可用语音总数: {len(voices)}")
                            
                    except Exception as e:
                        self.logger.error(f"Edge TTS语音加载失败: {e}")
                        # 使用默认配置
                        default_values['voice_name'] = 'zh-CN-XiaoxiaoNeural'
                        default_values['language'] = 'zh-CN'

            
            # 设置默认值到UI
            self.dynamic_parameter_ui.set_all_parameter_values(default_values)
            
            # 更新当前语音配置
            for param_name, param_value in default_values.items():
                if hasattr(self.current_voice_config, param_name):
                    setattr(self.current_voice_config, param_name, param_value)
                else:
                    if not hasattr(self.current_voice_config, 'extra_params'):
                        self.current_voice_config.extra_params = {}
                    self.current_voice_config.extra_params[param_name] = param_value
            
            self.logger.info(f"已设置 {engine} 的默认参数值: {default_values}")
            
        except Exception as e:
            self.logger.error(f"设置默认参数值失败: {e}")
    
    def load_voices(self):
        """加载可用语音"""
        try:
            self.available_voices = self.audio_controller.get_all_available_voices()
            
            # 更新引擎状态
            self.update_engine_status()
            
            # 使用update_voice_combo进行正确的引擎过滤，而不是直接添加所有语音
            self.update_voice_combo()
            
            self.logger.info(f"加载了 {len(self.available_voices)} 个语音")
            
        except Exception as e:
            self.logger.error(tr("voice_settings.messages.load_voices_failed").format(error=e))
            QMessageBox.critical(self, tr("common.error"), tr("voice_settings.messages.load_voices_failed").format(error=e))
    
    def update_engine_status(self):
        """更新引擎状态"""
        try:
            engine_text = self.engine_combo.currentText()
            # 清理引擎名称，移除可用性标记
            current_engine = engine_text.replace(" ✓", "").replace(" ✗", "")
            is_available = self.audio_controller.is_engine_available(current_engine)
            
            if is_available:
                self.engine_status_label.setText(tr("voice_settings.available"))
                self.engine_status_label.setStyleSheet("color: green; font-size: 12px;")
            else:
                self.engine_status_label.setText(tr("voice_settings.unavailable"))
                self.engine_status_label.setStyleSheet("color: red; font-size: 12px;")
                
        except Exception as e:
            self.logger.error(tr("voice_settings.messages.update_engine_status_failed").format(error=e))
    
    def on_engine_changed(self, engine: str):
        """引擎改变事件"""
        try:
            # 清理引擎名称，移除可用性标记
            clean_engine = engine.replace(" ✓", "").replace(" ✗", "")
            
            # 保存当前语音配置以便映射
            previous_voice_name = getattr(self.current_voice_config, 'voice_name', '')
            previous_engine = getattr(self.current_voice_config, 'engine', '')
            
            # 优先从对应的JSON配置文件加载配置
            voice_config = self._load_engine_json_config(clean_engine)
            
            if voice_config:
                self.current_voice_config = voice_config
                self.logger.info(f"从JSON配置文件加载 {clean_engine} 配置")
                self.logger.info(f"加载的配置: 语音={voice_config.voice_name}, 语言={voice_config.language}")
            else:
                # 如果JSON文件不存在，从registry.json加载
                engine_config = self.engine_config_service.load_engine_config(clean_engine)
                
                if engine_config:
                    # 将EngineConfig转换为VoiceConfig
                    voice_config = VoiceConfig(
                        engine=clean_engine,
                        voice_name=engine_config.parameters.voice_name,
                        rate=engine_config.parameters.rate,
                        pitch=engine_config.parameters.pitch,
                        volume=engine_config.parameters.volume,
                        language=engine_config.parameters.language,
                        output_format=engine_config.parameters.output_format,
                        extra_params=engine_config.parameters.extra_params
                    )
                    self.current_voice_config = voice_config
                    self.logger.info(f"从registry.json加载 {clean_engine} 配置")
                else:
                    # 使用默认配置
                    self.current_voice_config = VoiceConfig(engine=clean_engine)
                    self.logger.info(f"使用 {clean_engine} 默认配置")
            
            # 如果之前有语音配置且引擎不同，尝试映射语音ID
            # 但是，如果已经从配置文件加载了正确的配置，就不要被语音映射覆盖
            if (previous_voice_name and previous_engine and previous_engine != clean_engine and 
                not (voice_config and voice_config.voice_name and voice_config.voice_name != '')):
                from services.voice_mapping_service import VoiceMappingService
                voice_mapping_service = VoiceMappingService()
                
                # 获取目标引擎的可用语音
                available_voices = []
                try:
                    from services.tts_service import TTSServiceFactory
                    tts_service = TTSServiceFactory.create_service(clean_engine)
                    if tts_service:
                        available_voices = tts_service.get_available_voices()
                except Exception as e:
                    self.logger.warning(f"获取{clean_engine}可用语音失败: {e}")
                
                # 尝试映射语音ID
                mapping = voice_mapping_service.map_voice_id(
                    previous_voice_name, 
                    previous_engine, 
                    clean_engine, 
                    available_voices
                )
                
                if mapping.target_id != previous_voice_name:
                    self.logger.info(f"语音映射: {previous_voice_name} ({previous_engine}) -> {mapping.target_id} ({clean_engine})")
                    self.current_voice_config.voice_name = mapping.target_id
            
            # 更新UI以反映新引擎的配置
            # 查找引擎选择框中对应的带标记的引擎名称
            engine_text = None
            for i in range(self.engine_combo.count()):
                item_text = self.engine_combo.itemText(i)
                if item_text.replace(" ✓", "").replace(" ✗", "") == clean_engine:
                    engine_text = item_text
                    break
            
            if engine_text:
                self.engine_combo.setCurrentText(engine_text)
            else:
                self.logger.warning(f"在引擎选择框中找不到引擎: {clean_engine}")
            self.rate_slider.setValue(int(self.current_voice_config.rate * 100))
            self.pitch_slider.setValue(int(self.current_voice_config.pitch))
            self.volume_slider.setValue(int(self.current_voice_config.volume * 100))
            self.language_combo.setCurrentText(self.current_voice_config.language)
            self.output_format_combo.setCurrentText(self.current_voice_config.output_format.upper())
            
            # 启用语速滑块和语言选择
            self.rate_slider.setEnabled(True)
            self.rate_slider.setToolTip("")
            self.language_combo.setEnabled(True)
            self.language_combo.setToolTip("")
            
            # 更新语音选择
            self.update_voice_combo()
            
            # 根据引擎类型显示不同的参数组
            if clean_engine == "edge_tts":
                # Edge TTS使用传统的语音选择组
                self.voice_group.setVisible(True)
                self.voice_group.setTitle("语音选择")
                self.dynamic_parameter_group.setVisible(False)
                
                # 加载Edge-TTS支持的语言列表
                self._update_language_combo_for_edge_tts()
            elif clean_engine in ["pyttsx3", "piper_tts"]:
                # pyttsx3、Piper TTS使用动态参数组
                self.voice_group.setVisible(False)
                self.dynamic_parameter_group.setVisible(True)
                
                # 调试信息
                self.logger.info(f"设置动态参数组可见性为True，引擎: {clean_engine}")
                
                # 更新动态参数UI
                if self.dynamic_parameter_ui:
                    self.dynamic_parameter_ui.set_engine(clean_engine)
                    
                    # 检查是否有该引擎的配置
                    engine_config = self.engine_config_service.get_engine_config(clean_engine)
                    if engine_config:
                        self.dynamic_parameter_group.setTitle(f"{engine_config.info.name} 参数设置")
                        
                        # 加载引擎的配置到动态参数UI（优先使用已保存的配置）
                        if hasattr(self.current_voice_config, 'extra_params') and self.current_voice_config.extra_params:
                            # 如果有已保存的配置，直接使用
                            self.dynamic_parameter_ui.set_all_parameter_values(self.current_voice_config.extra_params)
                            self.logger.info(f"使用已保存的 {clean_engine} 配置")
                        else:
                            # 如果没有已保存的配置，才设置默认值
                            self.set_default_parameter_values(clean_engine)
                            self.logger.info(f"使用 {clean_engine} 默认配置")
                        
                        # 确保动态参数组和UI都可见
                        self.dynamic_parameter_group.setVisible(True)
                        self.dynamic_parameter_ui.setVisible(True)
                        self.dynamic_parameter_group.update()
                        self.dynamic_parameter_ui.update()
                        
                        self.logger.info(f"动态参数组设置完成，可见性: {self.dynamic_parameter_group.isVisible()}")
                else:
                    self.logger.error("动态参数UI未创建")
            else:
                # 其他引擎隐藏所有参数组
                self.voice_group.setVisible(False)
                self.dynamic_parameter_group.setVisible(False)
            
            # 输出格式已固定为WAV，始终禁用
            self.output_format_combo.setCurrentText("WAV")
            self.output_format_combo.setEnabled(False)  # 始终禁用
            
            # 根据引擎显示相应的格式说明
            if clean_engine == "edge_tts":
                self.format_note_label.setText(tr("voice_settings.format_note_edge"))
            else:
                self.format_note_label.setText(tr("voice_settings.format_note_default"))
            
            # self.update_engine_status()
            # 不需要重新加载语音，只需要更新语音选择框的过滤
            
        except Exception as e:
            self.logger.error(tr("voice_settings.messages.engine_changed_failed").format(error=e))
    
    def on_voice_changed(self, voice_text: str):
        """语音改变事件"""
        try:
            if not voice_text:
                return
            
            # 获取选中的语音数据
            voice_data = self.voice_combo.currentData()
            if voice_data:
                self.current_voice_config.voice_name = voice_data['id']
                self.current_voice_config.language = voice_data['language']
                
        except Exception as e:
            self.logger.error(tr("voice_settings.messages.voice_changed_failed").format(error=e))
    
    def on_language_changed(self, language_display_text: str):
        """语言改变事件"""
        try:
            # 获取当前引擎
            engine_text = self.engine_combo.currentText()
            current_engine = engine_text.replace(" ✓", "").replace(" ✗", "")
            
            # 获取实际的语言代码
            if current_engine == "edge_tts":
                # 对于Edge-TTS，从语言选择框的itemData获取语言代码
                current_index = self.language_combo.currentIndex()
                if current_index >= 0:
                    language_code = self.language_combo.itemData(current_index)
                    if language_code:
                        language = language_code
                    else:
                        # 如果没有itemData，从显示文本中提取语言代码
                        language = language_display_text.split('(')[-1].split(')')[0] if '(' in language_display_text else language_display_text
                else:
                    language = language_display_text
            else:
                language = language_display_text
            
            self.current_voice_config.language = language
            
            # 过滤对应语言的语音
            self.voice_combo.clear()
            
            if current_engine == "edge_tts":
                # Edge TTS使用新的语音管理功能
                from services.tts_service import TTSServiceFactory
                tts_service = TTSServiceFactory.create_service(current_engine)
                if tts_service:
                    try:
                        voices = tts_service.get_available_voices()
                        if voices:
                            filtered_count = 0
                            for voice in voices:
                                # 处理对象格式的语音数据
                                if hasattr(voice, 'language'):
                                    voice_lang = voice.language
                                    voice_id = voice.id
                                    voice_name = voice.name
                                else:
                                    # 处理字典格式的语音数据
                                    voice_lang = voice.get('language', '')
                                    voice_id = voice.get('id', '')
                                    voice_name = voice.get('name', '')
                                
                                if voice_lang == language:
                                    display_text = f"{voice_id} - {voice_name} ({voice_lang})"
                                    self.voice_combo.addItem(display_text, voice)
                                    filtered_count += 1
                            
                            self.logger.info(f"Edge-TTS语言 {language} 过滤出 {filtered_count} 个语音")
                    except Exception as e:
                        self.logger.error(f"Edge TTS语音过滤失败: {e}")
            else:
                # 其他引擎使用原有逻辑
                for voice in self.available_voices:
                    voice_lang = voice.get('language', '') if isinstance(voice, dict) else getattr(voice, 'language', '')
                    if voice_lang == language:
                        voice_name = voice.get('name', '') if isinstance(voice, dict) else getattr(voice, 'name', '')
                        self.voice_combo.addItem(f"{voice_name} ({voice_lang})", voice)
                    
        except Exception as e:
            self.logger.error(tr("voice_settings.messages.language_changed_failed").format(error=e))
    
    def on_output_format_activated(self, index: int):
        """输出格式激活事件（用户点击选择时触发）- 已禁用，输出格式固定为WAV"""
        try:
            # 输出格式已固定为WAV，直接设置
            format_text = "WAV"
            self.current_voice_config.output_format = format_text.lower()
            
            # 同步到输出设置页面
            if self.output_settings_widget:
                self.output_settings_widget.format_combo.setCurrentText(format_text)
                self.logger.info(f"已同步输出格式到输出设置页面: {format_text}")
            
            self.logger.info(f"输出格式已设置为: {format_text}")
            
        except Exception as e:
            self.logger.error(f"输出格式激活处理失败: {e}")
    
    def on_output_format_changed(self):
        """输出格式改变事件（程序内部调用时使用）- 已禁用，输出格式固定为WAV"""
        try:
            # 输出格式已固定为WAV，直接设置
            format_text = "WAV"
            self.current_voice_config.output_format = format_text.lower()
            
            # 同步到输出设置页面
            if self.output_settings_widget:
                self.output_settings_widget.format_combo.setCurrentText(format_text)
                self.logger.info(f"已同步输出格式到输出设置页面: {format_text}")
            
            self.logger.info(f"输出格式已设置为: {format_text}")
            
        except Exception as e:
            self.logger.error(f"输出格式改变处理失败: {e}")
    
    def on_rate_changed(self, value: int):
        """语速改变事件"""
        try:
            self.current_voice_config.rate = value / 100.0
            self.rate_label.setText(f"{value}%")
            
        except Exception as e:
            self.logger.error(tr("voice_settings.messages.rate_changed_failed").format(error=e))
    
    def on_pitch_changed(self, value: int):
        """音调改变事件"""
        try:
            self.current_voice_config.pitch = value
            self.pitch_label.setText(f"{value}%")
            
        except Exception as e:
            self.logger.error(tr("voice_settings.messages.pitch_changed_failed").format(error=e))
    
    def on_volume_changed(self, value: int):
        """音量改变事件"""
        try:
            self.current_voice_config.volume = value / 100.0
            self.volume_label.setText(f"{value}%")
            
        except Exception as e:
            self.logger.error(tr("voice_settings.messages.volume_changed_failed").format(error=e))
    
    def on_dynamic_parameters_changed(self, parameters: dict):
        """动态参数改变事件"""
        try:
            # 更新当前语音配置中的动态参数
            for param_name, param_value in parameters.items():
                if hasattr(self.current_voice_config, param_name):
                    setattr(self.current_voice_config, param_name, param_value)
                else:
                    # 如果参数不存在，添加到额外参数字典中
                    if not hasattr(self.current_voice_config, 'extra_params'):
                        self.current_voice_config.extra_params = {}
                    self.current_voice_config.extra_params[param_name] = param_value
            
            self.logger.info(f"动态参数已更新: {parameters}")
            
        except Exception as e:
            self.logger.error(f"处理动态参数改变事件失败: {e}")
    
    def on_dynamic_validation_changed(self, is_valid: bool):
        """动态参数验证状态改变事件"""
        try:
            # 更新应用按钮状态
            if hasattr(self, 'apply_button'):
                self.apply_button.setEnabled(is_valid)
            
            # 显示验证错误
            if not is_valid and self.dynamic_parameter_ui:
                errors = self.dynamic_parameter_ui.get_validation_errors()
                if errors:
                    self.logger.warning(f"参数验证失败: {errors}")
            
        except Exception as e:
            self.logger.error(f"处理动态参数验证状态改变事件失败: {e}")
    
    def test_voice(self):
        """测试语音"""
        try:
            # 检查测试组件是否存在
            if not hasattr(self, 'test_text') or not self.test_text:
                QMessageBox.information(self, tr("common.info"), tr("voice_settings.messages.voice_test_disabled"))
                return
                
            test_text = self.test_text.toPlainText().strip()
            if not test_text:
                QMessageBox.information(self, tr("common.info"), tr("voice_settings.messages.please_enter_test_text"))
                return
            
            # 显示进度条
            if hasattr(self, 'progress_bar') and self.progress_bar:
                self.progress_bar.setVisible(True)
                self.progress_bar.setRange(0, 0)
            
            # 禁用测试按钮
            if hasattr(self, 'test_button') and self.test_button:
                self.test_button.setEnabled(False)
            if hasattr(self, 'stop_test_button') and self.stop_test_button:
                self.stop_test_button.setEnabled(True)
            
            # 测试语音
            audio_model = self.audio_controller.test_voice(test_text, self.current_voice_config)
            
            # 更新音频信息
            self.update_audio_info(audio_model)
            
            # 隐藏进度条
            if hasattr(self, 'progress_bar') and self.progress_bar:
                self.progress_bar.setVisible(False)
            
            # 恢复按钮状态
            if hasattr(self, 'test_button') and self.test_button:
                self.test_button.setEnabled(True)
            if hasattr(self, 'stop_test_button') and self.stop_test_button:
                self.stop_test_button.setEnabled(False)
            
            self.logger.info(tr("voice_settings.messages.voice_test_completed"))
            
        except Exception as e:
            if hasattr(self, 'progress_bar') and self.progress_bar:
                self.progress_bar.setVisible(False)
            if hasattr(self, 'test_button') and self.test_button:
                self.test_button.setEnabled(True)
            if hasattr(self, 'stop_test_button') and self.stop_test_button:
                self.stop_test_button.setEnabled(False)
            self.logger.error(tr("voice_settings.messages.voice_test_failed").format(error=e))
            QMessageBox.critical(self, tr("common.error"), tr("voice_settings.messages.voice_test_failed").format(error=e))
    
    def stop_test(self):
        """停止测试"""
        try:
            # 这里可以实现停止测试的逻辑
            if hasattr(self, 'progress_bar') and self.progress_bar:
                self.progress_bar.setVisible(False)
            if hasattr(self, 'test_button') and self.test_button:
                self.test_button.setEnabled(True)
            if hasattr(self, 'stop_test_button') and self.stop_test_button:
                self.stop_test_button.setEnabled(False)
            
        except Exception as e:
            self.logger.error(f"停止测试失败: {e}")
    
    def update_audio_info(self, audio_model):
        """更新音频信息"""
        try:
            # 检查音频信息组件是否存在
            if not hasattr(self, 'info_text') or not self.info_text:
                return
                
            info = audio_model.get_info()
            
            info_text = f"格式: {info['format']}\n"
            info_text += f"采样率: {info['sample_rate']}\n"
            info_text += f"声道: {info['channels']}\n"
            info_text += f"时长: {info['duration']}\n"
            info_text += f"比特率: {info['bitrate']}\n"
            info_text += f"大小: {info['size']}\n"
            info_text += f"语音: {info['voice']}\n"
            info_text += f"引擎: {info['engine']}"
            
            self.info_text.setPlainText(info_text)
            
        except Exception as e:
            self.logger.error(f"更新音频信息失败: {e}")
    
    def apply_settings(self):
        """应用设置"""
        try:
            # 验证设置
            validation_result = self.audio_controller.validate_voice_config(self.current_voice_config)
            
            if not validation_result['valid']:
                QMessageBox.warning(self, tr("common.warning"), tr("voice_settings.messages.settings_validation_failed").format(issues="\n".join(validation_result['issues'])))
                return
            
            # 发送信号
            self.voice_changed.emit(self.current_voice_config)
            
            QMessageBox.information(self, tr("common.success"), tr("voice_settings.messages.voice_settings_applied"))
            self.logger.info(tr("voice_settings.messages.voice_settings_applied"))
            
        except Exception as e:
            self.logger.error(tr("voice_settings.messages.apply_settings_failed").format(error=e))
            QMessageBox.critical(self, tr("common.error"), tr("voice_settings.messages.apply_settings_failed").format(error=e))
    
    def reset_settings(self):
        """重置设置"""
        try:
            # 获取当前引擎
            engine_text = self.engine_combo.currentText()
            # 清理引擎名称，移除可用性标记
            current_engine = engine_text.replace(" ✓", "").replace(" ✗", "")
            
            # 重置为当前引擎的默认值
            engine_config = self.engine_config_service.load_engine_config(current_engine)
            if engine_config:
                # 将EngineConfig转换为VoiceConfig
                self.current_voice_config = VoiceConfig(
                    engine=current_engine,
                    voice_name=engine_config.parameters.voice_name,
                    rate=engine_config.parameters.rate,
                    pitch=engine_config.parameters.pitch,
                    volume=engine_config.parameters.volume,
                    language=engine_config.parameters.language,
                    output_format=engine_config.parameters.output_format,
                    extra_params=engine_config.parameters.extra_params
                )
            else:
                self.current_voice_config = VoiceConfig(engine=current_engine)
            
            # 更新UI
            self.rate_slider.setValue(int(self.current_voice_config.rate * 100))
            self.pitch_slider.setValue(int(self.current_voice_config.pitch))
            self.volume_slider.setValue(int(self.current_voice_config.volume * 100))
            self.language_combo.setCurrentText(self.current_voice_config.language)
            self.output_format_combo.setCurrentText(self.current_voice_config.output_format.upper())
            
            # 更新语音选择
            self.update_voice_combo()
            
            # 更新动态参数UI
            if self.dynamic_parameter_ui and hasattr(self.current_voice_config, 'extra_params'):
                self.dynamic_parameter_ui.set_all_parameter_values(self.current_voice_config.extra_params)
            
            # 设置默认参数值
            self.set_default_parameter_values(current_engine)
            
            self.logger.info(tr("voice_settings.messages.reset_engine_settings").format(engine=current_engine))
            QMessageBox.information(self, tr("common.success"), tr("voice_settings.messages.reset_engine_settings").format(engine=current_engine))
            
        except Exception as e:
            self.logger.error(tr("voice_settings.messages.reset_settings_failed").format(error=e))
            QMessageBox.critical(self, tr("common.error"), tr("voice_settings.messages.reset_settings_failed").format(error=e))
    
    def get_voice_config(self) -> VoiceConfig:
        """获取语音配置"""
        return self.current_voice_config
    
    def set_voice_config(self, voice_config: VoiceConfig):
        """设置语音配置"""
        try:
            self.current_voice_config = voice_config
            
            # 更新UI
            self.engine_combo.setCurrentText(voice_config.engine)
            self.rate_slider.setValue(int(voice_config.rate * 100))
            self.pitch_slider.setValue(int(voice_config.pitch))
            self.volume_slider.setValue(int(voice_config.volume * 100))
            
        except Exception as e:
            self.logger.error(tr("voice_settings.messages.set_voice_config_failed").format(error=e))
    
    def load_available_engines(self):
        """加载可用的TTS引擎"""
        try:
            # 清空现有选项
            self.engine_combo.clear()
            
            # 定义引擎显示顺序：piper_tts 第一，edge_tts 第二，其他按原顺序
            preferred_order = ['piper_tts', 'edge_tts', 'pyttsx3']
            
            # 获取所有注册的引擎
            all_engines = list(TTSServiceFactory._engines.keys())
            
            # 获取可用的引擎
            available_engines = TTSServiceFactory.get_available_engines()
            
            # 按照指定顺序添加引擎到下拉框
            for engine in preferred_order:
                if engine in all_engines:
                    if engine in available_engines:
                        # 可用引擎，添加可用标记
                        self.engine_combo.addItem(f"{engine} ✓")
                    else:
                        # 不可用引擎，添加不可用标记
                        self.engine_combo.addItem(f"{engine} ✗")
            
            # 添加其他未在优先列表中的引擎
            for engine in all_engines:
                if engine not in preferred_order:
                    if engine in available_engines:
                        # 可用引擎，添加可用标记
                        self.engine_combo.addItem(f"{engine} ✓")
                    else:
                        # 不可用引擎，添加不可用标记
                        self.engine_combo.addItem(f"{engine} ✗")
            
            # 设置默认选择为第一个可用引擎
            if available_engines:
                # 暂时断开信号连接，避免触发on_engine_changed
                try:
                    self.engine_combo.currentTextChanged.disconnect()
                except TypeError:
                    # 如果没有连接，disconnect会抛出TypeError，这是正常的
                    pass
                
                # 优先选择 piper_tts，其次选择 edge_tts，如果都不可用则选择第一个可用的
                if 'piper_tts' in available_engines:
                    self.engine_combo.setCurrentText("piper_tts ✓")
                elif 'edge_tts' in available_engines:
                    self.engine_combo.setCurrentText("edge_tts ✓")
                else:
                    self.engine_combo.setCurrentText(f"{available_engines[0]} ✓")
                
                # 重新连接信号
                self.engine_combo.currentTextChanged.connect(self.on_engine_changed)
            
            self.logger.info(f"加载了 {len(all_engines)} 个TTS引擎，其中 {len(available_engines)} 个可用")
            
        except Exception as e:
            self.logger.error(tr("voice_settings.messages.load_available_engines_failed").format(error=e))
            # 如果失败，使用硬编码的引擎列表作为备用
            self.engine_combo.addItems(["piper_tts", "pyttsx3"])

    def load_config(self):
        """加载配置"""
        try:
            # 获取当前选择的引擎（从UI获取，而不是从服务获取）
            engine_text = self.engine_combo.currentText()
            current_engine = engine_text.replace(" ✓", "").replace(" ✗", "")
            
            # 优先从对应的JSON配置文件加载配置
            voice_config = self._load_engine_json_config(current_engine)
            
            if voice_config:
                self.current_voice_config = voice_config
                self.logger.info(f"从JSON配置文件加载 {current_engine} 配置")
            else:
                # 如果JSON文件不存在，从registry.json加载
                engine_config = self.engine_config_service.load_engine_config(current_engine)
                
                if engine_config:
                    # 将EngineConfig转换为VoiceConfig
                    voice_config = VoiceConfig(
                        engine=current_engine,
                        voice_name=engine_config.parameters.voice_name,
                        rate=engine_config.parameters.rate,
                        pitch=engine_config.parameters.pitch,
                        volume=engine_config.parameters.volume,
                        language=engine_config.parameters.language,
                        output_format=engine_config.parameters.output_format,
                        extra_params=engine_config.parameters.extra_params
                    )
                    self.current_voice_config = voice_config
                    self.logger.info(f"从registry.json加载 {current_engine} 配置")
                else:
                    # 使用默认配置
                    self.current_voice_config = VoiceConfig(engine=current_engine)
                    self.logger.info(f"使用 {current_engine} 默认配置")
            
            # 更新UI（临时断开信号连接，避免触发on_engine_changed）
            try:
                self.engine_combo.currentTextChanged.disconnect()
            except TypeError:
                pass  # 如果没有连接，disconnect会抛出TypeError，这是正常的
            
            # 查找引擎选择框中对应的带标记的引擎名称
            engine_text = None
            for i in range(self.engine_combo.count()):
                item_text = self.engine_combo.itemText(i)
                if item_text.replace(" ✓", "").replace(" ✗", "") == self.current_voice_config.engine:
                    engine_text = item_text
                    break
            
            if engine_text:
                self.engine_combo.setCurrentText(engine_text)
            else:
                self.logger.warning(f"在引擎选择框中找不到引擎: {self.current_voice_config.engine}")
            
            # 重新连接信号
            self.engine_combo.currentTextChanged.connect(self.on_engine_changed)
            
            self.rate_slider.setValue(int(self.current_voice_config.rate * 100))
            self.pitch_slider.setValue(int(self.current_voice_config.pitch))
            self.volume_slider.setValue(int(self.current_voice_config.volume * 100))
            self.language_combo.setCurrentText(self.current_voice_config.language)
            self.output_format_combo.setCurrentText(self.current_voice_config.output_format.upper())
            
            # 启用语速滑块和语言选择
            self.rate_slider.setEnabled(True)
            self.rate_slider.setToolTip("")
            self.language_combo.setEnabled(True)
            self.language_combo.setToolTip("")
            
            # 更新语音选择
            self.update_voice_combo()
            
            # 更新动态参数UI（在引擎设置之后）
            if self.dynamic_parameter_ui and hasattr(self.current_voice_config, 'extra_params'):
                try:
                    self.dynamic_parameter_ui.set_all_parameter_values(self.current_voice_config.extra_params)
                    self.logger.debug(f"加载动态参数: {self.current_voice_config.extra_params}")
                except Exception as e:
                    self.logger.error(f"加载动态参数失败: {e}")
            
            self.config_status_label.setText(tr("voice_settings.config_status_loaded"))
            self.config_status_label.setStyleSheet("color: green; font-size: 12px;")
            
            self.logger.info(f"语音配置加载成功: {current_engine}")
            
        except Exception as e:
            self.logger.error(tr("voice_settings.messages.load_config_failed").format(error=e))
            QMessageBox.critical(self, tr("common.error"), tr("voice_settings.messages.load_config_failed").format(error=e))
    
    def save_config(self):
        """保存配置"""
        try:
            # 更新当前配置
            self.update_current_config()
            
            # 保存当前引擎的配置
            current_engine = self.current_voice_config.engine
            # 清理引擎名称，移除可用性标记
            current_engine = current_engine.replace(" ✓", "").replace(" ✗", "")
            
            # 将VoiceConfig转换为EngineConfig并保存
            self._save_voice_config_to_engine_config(current_engine, self.current_voice_config)
            
            self.config_status_label.setText(tr("voice_settings.config_status_saved"))
            self.config_status_label.setStyleSheet("color: green; font-size: 12px;")
            
            QMessageBox.information(self, tr("common.success"), tr("voice_settings.messages.save_config_success"))
            self.logger.info(f"语音配置保存成功: {current_engine}")
            
        except Exception as e:
            self.logger.error(tr("voice_settings.messages.save_config_failed").format(error=e))
            QMessageBox.critical(self, tr("common.error"), tr("voice_settings.messages.save_config_failed").format(error=e))
    
    def _save_voice_config_to_engine_config(self, engine_id: str, voice_config: VoiceConfig):
        """将VoiceConfig保存为EngineConfig"""
        try:
            from models.config_models import EngineConfig, EngineInfo, EngineParameters, EngineStatus, EngineStatusEnum
            
            # 获取现有引擎配置或创建新的
            existing_config = self.engine_config_service.get_engine_config(engine_id)
            
            if existing_config:
                # 更新现有配置的参数
                existing_config.parameters.voice_name = voice_config.voice_name
                existing_config.parameters.rate = voice_config.rate
                existing_config.parameters.pitch = voice_config.pitch
                existing_config.parameters.volume = voice_config.volume
                existing_config.parameters.language = voice_config.language
                existing_config.parameters.output_format = voice_config.output_format
                existing_config.parameters.extra_params = getattr(voice_config, 'extra_params', {})
                existing_config.updated_at = datetime.now().isoformat()
                
                # 保存更新后的配置到registry.json
                self.engine_config_service.set_engine_config(engine_id, existing_config)
                
                # 同时保存到对应的JSON文件以保持兼容性
                self._save_to_engine_json_file(engine_id, voice_config)
            else:
                # 创建新的引擎配置
                engine_info = EngineInfo(
                    id=engine_id,
                    name=f"{engine_id.title()} TTS",
                    version="1.0.0",
                    description=f"{engine_id.title()} 语音合成引擎",
                    author="TTS开发团队",
                    website="",
                    license="",
                    supported_languages=["zh-CN", "en-US"],
                    supported_formats=["wav", "mp3"],
                    is_online=engine_id in ["edge_tts"],
                    requires_auth=False
                )
                
                engine_parameters = EngineParameters(
                    voice_name=voice_config.voice_name,
                    rate=voice_config.rate,
                    pitch=voice_config.pitch,
                    volume=voice_config.volume,
                    language=voice_config.language,
                    output_format=voice_config.output_format,
                    extra_params=getattr(voice_config, 'extra_params', {})
                )
                
                engine_status = EngineStatus(
                    status=EngineStatusEnum.AVAILABLE,
                    last_check=datetime.now().isoformat(),
                    error_message="",
                    available_voices=[],
                    performance_metrics={}
                )
                
                engine_config = EngineConfig(
                    info=engine_info,
                    parameters=engine_parameters,
                    status=engine_status,
                    config_version="1.0.0",
                    enabled=True,
                    priority=0,
                    created_at=datetime.now().isoformat(),
                    updated_at=datetime.now().isoformat()
                )
                
                # 保存新配置到registry.json
                self.engine_config_service.set_engine_config(engine_id, engine_config)
                
                # 同时保存到对应的JSON文件以保持兼容性
                self._save_to_engine_json_file(engine_id, voice_config)
            
            self.logger.info(f"引擎配置保存成功: {engine_id}")
            
        except Exception as e:
            self.logger.error(tr("voice_settings.messages.save_engine_config_failed").format(engine=engine_id, error=e))
            raise
    
    def _save_to_engine_json_file(self, engine_id: str, voice_config: VoiceConfig):
        """保存配置到对应的JSON文件以保持兼容性"""
        try:
            import json
            import os
            
            # 构建JSON文件路径
            # 从ui目录回到项目根目录，然后进入configs目录
            current_dir = os.path.dirname(__file__)  # ui目录
            project_root = os.path.dirname(current_dir)  # 4Code目录
            json_file_path = os.path.join(project_root, "configs", f"{engine_id}.json")
            
            # 准备配置数据
            config_data = {
                "engine": engine_id,
                "voice_name": voice_config.voice_name,
                "rate": voice_config.rate,
                "pitch": voice_config.pitch,
                "volume": voice_config.volume,
                "language": voice_config.language,
                "output_format": voice_config.output_format,
                "extra_params": getattr(voice_config, 'extra_params', {})
            }
            
            # 保存到JSON文件
            with open(json_file_path, 'w', encoding='utf-8') as f:
                json.dump(config_data, f, indent=2, ensure_ascii=False)
            
            self.logger.info(f"配置已同步保存到: {json_file_path}")
            
        except Exception as e:
            self.logger.warning(tr("voice_settings.messages.save_to_json_failed").format(error=e))
    
    def _load_engine_json_config(self, engine_id: str) -> Optional[VoiceConfig]:
        """从对应的JSON配置文件加载引擎配置"""
        try:
            import json
            import os
            
            # 构建JSON文件路径
            # 从ui目录回到项目根目录，然后进入configs目录
            current_dir = os.path.dirname(__file__)  # ui目录
            project_root = os.path.dirname(current_dir)  # 4Code目录
            json_file_path = os.path.join(project_root, "configs", f"{engine_id}.json")
            
            if not os.path.exists(json_file_path):
                self.logger.debug(f"JSON配置文件不存在: {json_file_path}")
                return None
            
            # 读取JSON配置文件
            with open(json_file_path, 'r', encoding='utf-8') as f:
                config_data = json.load(f)
            
            # 创建VoiceConfig对象
            voice_config = VoiceConfig(
                engine=config_data.get('engine', engine_id),
                voice_name=config_data.get('voice_name', ''),
                rate=config_data.get('rate', 1.0),
                pitch=config_data.get('pitch', 0.0),
                volume=config_data.get('volume', 1.0),
                language=config_data.get('language', 'zh-CN'),
                output_format=config_data.get('output_format', 'wav'),
                extra_params=config_data.get('extra_params', {})
            )
            
            self.logger.info(f"成功从JSON文件加载 {engine_id} 配置: {json_file_path}")
            self.logger.info(f"加载的配置: 引擎={voice_config.engine}, 语音={voice_config.voice_name}, 语言={voice_config.language}")
            return voice_config
            
        except Exception as e:
            self.logger.warning(tr("voice_settings.messages.load_from_json_failed").format(error=e))
            return None
    
    def export_config(self):
        """导出配置"""
        try:
            from PyQt6.QtWidgets import QFileDialog
            import json
            
            # 更新当前配置
            self.update_current_config()
            
            # 获取当前引擎
            current_engine = self.current_voice_config.engine
            
            file_path, _ = QFileDialog.getSaveFileName(
                self, 
                tr("voice_settings.messages.export_config").format(engine=current_engine), 
                f"{current_engine}_config.json",
                tr("voice_settings.messages.json_files")
            )
            
            if file_path:
                # 准备配置数据
                config_data = {
                    'engine': self.current_voice_config.engine,
                    'voice_name': self.current_voice_config.voice_name,
                    'rate': self.current_voice_config.rate,
                    'pitch': self.current_voice_config.pitch,
                    'volume': self.current_voice_config.volume,
                    'language': self.current_voice_config.language,
                    'output_format': self.current_voice_config.output_format,
                    'extra_params': getattr(self.current_voice_config, 'extra_params', {})
                }
                
                # 保存到文件
                with open(file_path, 'w', encoding='utf-8') as f:
                    json.dump(config_data, f, ensure_ascii=False, indent=2)
                
                QMessageBox.information(self, tr("common.success"), tr("voice_settings.messages.export_config_success").format(engine=current_engine, path=file_path))
                self.logger.info(f"{current_engine}语音配置导出成功: {file_path}")
                
        except Exception as e:
            self.logger.error(tr("voice_settings.messages.export_config_failed").format(error=e))
            QMessageBox.critical(self, tr("common.error"), tr("voice_settings.messages.export_config_failed").format(error=e))
    
    def import_config(self):
        """导入配置"""
        try:
            from PyQt6.QtWidgets import QFileDialog
            import json
            
            file_path, _ = QFileDialog.getOpenFileName(
                self, 
                tr("voice_settings.messages.import_config"), 
                "",
                tr("voice_settings.messages.json_files")
            )
            
            if file_path:
                with open(file_path, 'r', encoding='utf-8') as f:
                    config_data = json.load(f)
                
                # 验证配置数据
                if 'engine' not in config_data:
                    QMessageBox.warning(self, tr("common.warning"), tr("voice_settings.messages.invalid_config_format"))
                    return
                
                # 创建VoiceConfig对象
                imported_config = VoiceConfig(
                    engine=config_data.get('engine', ''),
                    voice_name=config_data.get('voice_name', ''),
                    rate=config_data.get('rate', 1.0),
                    pitch=config_data.get('pitch', 0.0),
                    volume=config_data.get('volume', 1.0),
                    language=config_data.get('language', 'zh-CN'),
                    output_format=config_data.get('output_format', 'wav'),
                    extra_params=config_data.get('extra_params', {})
                )
                
                # 更新当前配置
                self.current_voice_config = imported_config
                
                # 更新UI
                self.engine_combo.setCurrentText(imported_config.engine)
                self.rate_slider.setValue(int(imported_config.rate * 100))
                self.pitch_slider.setValue(int(imported_config.pitch))
                self.volume_slider.setValue(int(imported_config.volume * 100))
                self.language_combo.setCurrentText(imported_config.language)
                self.output_format_combo.setCurrentText(imported_config.output_format.upper())
                
                # 更新语音选择
                self.update_voice_combo()
                
                # 更新动态参数UI
                if self.dynamic_parameter_ui and hasattr(imported_config, 'extra_params'):
                    try:
                        self.dynamic_parameter_ui.set_all_parameter_values(imported_config.extra_params)
                    except Exception as e:
                        self.logger.error(f"更新动态参数失败: {e}")
                
                QMessageBox.information(self, tr("common.success"), tr("voice_settings.messages.import_config_success").format(engine=imported_config.engine, path=file_path))
                self.logger.info(f"{imported_config.engine}语音配置导入成功: {file_path}")
                
        except Exception as e:
            self.logger.error(tr("voice_settings.messages.import_config_failed").format(error=e))
            QMessageBox.critical(self, tr("common.error"), tr("voice_settings.messages.import_config_failed").format(error=e))
    
    def update_current_config(self):
        """更新当前配置"""
        try:
            # 清理引擎名称，移除可用性标记
            engine_text = self.engine_combo.currentText()
            clean_engine = engine_text.replace(" ✓", "").replace(" ✗", "")
            self.current_voice_config.engine = clean_engine
            self.current_voice_config.rate = self.rate_slider.value() / 100.0
            self.current_voice_config.pitch = self.pitch_slider.value()
            self.current_voice_config.volume = self.volume_slider.value() / 100.0
            self.current_voice_config.language = self.language_combo.currentText()
            
            # 更新语音名称
            if self.voice_combo.currentData():
                voice_data = self.voice_combo.currentData()
                # 优先使用ID，如果没有ID则使用name（向后兼容）
                self.current_voice_config.voice_name = voice_data.get('id', voice_data.get('name', ''))
            
            # 更新输出格式
            self.current_voice_config.output_format = self.output_format_combo.currentText().lower()
            
            # 更新动态参数
            if self.dynamic_parameter_ui:
                try:
                    dynamic_values = self.dynamic_parameter_ui.get_all_parameter_values()
                    if dynamic_values:
                        self.current_voice_config.extra_params = dynamic_values
                        self.logger.debug(f"更新动态参数: {dynamic_values}")
                except Exception as e:
                    self.logger.error(f"更新动态参数失败: {e}")
            
        except Exception as e:
            self.logger.error(tr("voice_settings.messages.update_current_config_failed").format(error=e))
    
    def update_voice_combo(self):
        """更新语音选择框"""
        try:
            # 根据当前引擎和语言更新语音选择
            engine_text = self.engine_combo.currentText()
            # 清理引擎名称，移除可用性标记
            current_engine = engine_text.replace(" ✓", "").replace(" ✗", "")
            current_language = self.language_combo.currentText()
            
            # 过滤可用语音 - 只按引擎过滤，不按语言过滤
            # 因为某些引擎（如EmotiVoice）的语音可能使用不同的语言标记
            if current_engine == "edge_tts":
                # Edge TTS使用新的语音管理功能
                from services.tts_service import TTSServiceFactory
                tts_service = TTSServiceFactory.create_service(current_engine)
                if tts_service:
                    try:
                        # 使用新的语音管理方法
                        voices = tts_service.get_available_voices()
                        if voices:
                            # 转换为字典格式以保持兼容性
                            filtered_voices = []
                            for voice in voices:
                                # 检查voice是对象还是字典
                                if isinstance(voice, dict):
                                    # 如果已经是字典格式，直接使用
                                    voice_dict = voice.copy()
                                    voice_dict['engine'] = current_engine
                                    filtered_voices.append(voice_dict)
                                else:
                                    # 如果是对象格式，转换为字典
                                    voice_dict = {
                                        'id': voice.id,
                                        'name': voice.name,
                                        'language': voice.language,
                                        'gender': voice.gender,
                                        'engine': current_engine,
                                        'description': voice.description,
                                        'quality': voice.quality.value if hasattr(voice.quality, 'value') else str(voice.quality),
                                        'sample_rate': voice.sample_rate,
                                        'bit_depth': voice.bit_depth,
                                        'channels': voice.channels
                                    }
                                    # 添加自定义属性
                                    if hasattr(voice, 'custom_attributes') and voice.custom_attributes:
                                        voice_dict.update(voice.custom_attributes)
                                    filtered_voices.append(voice_dict)
                            
                            self.logger.info(f"Edge TTS加载了 {len(filtered_voices)} 个语音")
                        else:
                            filtered_voices = []
                    except Exception as e:
                        self.logger.error(f"Edge TTS语音加载失败: {e}")
                        filtered_voices = []
                else:
                    filtered_voices = []
            else:
                # 其他引擎使用原有逻辑
                filtered_voices = [
                    voice for voice in self.available_voices
                    if voice.get('engine') == current_engine
                ]
            
            # 如果按语言过滤后没有语音，则显示该引擎的所有语音
            if not filtered_voices:
                self.logger.warning(f"引擎 {current_engine} 没有找到语音")
                return
            
            # 更新语音选择框
            self.voice_combo.clear()
            for voice in filtered_voices:
                # 显示格式：语音名称 (语言) 或 语音ID - 语音名称 (语言)
                voice_id = voice.get('id', '')
                voice_name = voice.get('name', '')
                voice_language = voice.get('language', 'unknown')
                
                if voice_id and voice_id != voice_name:
                    display_text = f"{voice_id} - {voice_name} ({voice_language})"
                else:
                    display_text = f"{voice_name} ({voice_language})"
                
                self.voice_combo.addItem(display_text, voice)
            
            # 设置当前语音
            target_voice_name = self.current_voice_config.voice_name
            
            if target_voice_name:
                for i in range(self.voice_combo.count()):
                    voice_data = self.voice_combo.itemData(i)
                    if voice_data:
                        # 优先比较 ID，如果没有 ID 则比较 name
                        voice_id = voice_data.get('id', voice_data.get('name', ''))
                        if voice_id == target_voice_name:
                            self.voice_combo.setCurrentIndex(i)
                            break
                        # 如果 ID 不匹配，也尝试比较 name（向后兼容）
                        elif voice_data.get('name') == target_voice_name:
                            self.voice_combo.setCurrentIndex(i)
                            break
            
            self.logger.info(f"更新语音选择框完成，引擎: {current_engine}，语音数量: {len(filtered_voices)}")
            
        except Exception as e:
            self.logger.error(tr("voice_settings.messages.update_voice_combo_failed").format(error=e))
