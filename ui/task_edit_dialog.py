#!/usr/bin/env python3
"""
任务编辑对话框
"""

from PyQt6.QtWidgets import (
    QDialog, QVBoxLayout, QHBoxLayout, QLabel, 
    QPushButton, QComboBox, QSpinBox, QLineEdit,
    QFormLayout, QGroupBox, QMessageBox, QFileDialog
)
from PyQt6.QtCore import Qt
from PyQt6.QtGui import QIcon
from services.language_service import get_text as tr

from controllers.batch_controller import BatchTask, TaskStatus
from models.audio_model import VoiceConfig
from utils.log_manager import LogManager


class TaskEditDialog(QDialog):
    """任务编辑对话框"""
    
    def __init__(self, task: BatchTask, parent=None):
        super().__init__(parent)
        self.task = task
        self.logger = LogManager().get_logger("TaskEditDialog")
        self.setWindowTitle(tr('task_edit_dialog.title'))
        self.setModal(True)
        self.resize(500, 400)
        
        self.setup_ui()
        self.load_task_data()
    
    def setup_ui(self):
        """设置UI"""
        layout = QVBoxLayout(self)
        
        # 文件信息组
        file_group = QGroupBox(tr('task_edit_dialog.file_info'))
        file_layout = QFormLayout(file_group)
        
        # 输入文件
        input_layout = QHBoxLayout()
        self.input_file_edit = QLineEdit()
        self.input_file_edit.setReadOnly(True)
        input_layout.addWidget(self.input_file_edit)
        
        self.browse_input_button = QPushButton(tr('task_edit_dialog.browse'))
        self.browse_input_button.clicked.connect(self.browse_input_file)
        input_layout.addWidget(self.browse_input_button)
        
        file_layout.addRow(tr('task_edit_dialog.input_file'), input_layout)
        
        # 输出文件
        output_layout = QHBoxLayout()
        self.output_file_edit = QLineEdit()
        self.output_file_edit.setReadOnly(True)
        output_layout.addWidget(self.output_file_edit)
        
        self.browse_output_button = QPushButton(tr('task_edit_dialog.browse'))
        self.browse_output_button.clicked.connect(self.browse_output_file)
        output_layout.addWidget(self.browse_output_button)
        
        file_layout.addRow(tr('task_edit_dialog.output_file'), output_layout)
        
        layout.addWidget(file_group)
        
        # 语音配置组
        voice_group = QGroupBox(tr('task_edit_dialog.voice_config'))
        voice_layout = QFormLayout(voice_group)
        
        # 语音引擎
        self.engine_combo = QComboBox()
        self.engine_combo.currentTextChanged.connect(self.on_engine_changed)
        voice_layout.addRow(tr('task_edit_dialog.voice_engine'), self.engine_combo)
        
        # 加载可用引擎
        self.load_available_engines()
        
        # 语音名称
        self.voice_combo = QComboBox()
        voice_layout.addRow(tr('task_edit_dialog.voice_name'), self.voice_combo)
        
        # 语速
        self.rate_spinbox = QSpinBox()
        self.rate_spinbox.setRange(50, 200)
        self.rate_spinbox.setValue(100)
        self.rate_spinbox.setSuffix("%")
        voice_layout.addRow(tr('task_edit_dialog.rate'), self.rate_spinbox)
        
        # 音调
        self.pitch_spinbox = QSpinBox()
        self.pitch_spinbox.setRange(-50, 50)
        self.pitch_spinbox.setValue(0)
        voice_layout.addRow(tr('task_edit_dialog.pitch'), self.pitch_spinbox)
        
        # 音量
        self.volume_spinbox = QSpinBox()
        self.volume_spinbox.setRange(0, 200)
        self.volume_spinbox.setValue(100)
        self.volume_spinbox.setSuffix("%")
        voice_layout.addRow(tr('task_edit_dialog.volume'), self.volume_spinbox)
        
        layout.addWidget(voice_group)
        
        # 音频格式组
        audio_group = QGroupBox(tr('task_edit_dialog.audio_format'))
        audio_layout = QFormLayout(audio_group)
        
        # 输出格式
        self.output_format_combo = QComboBox()
        self.output_format_combo.addItems(["wav", "mp3", "ogg", "m4a", "flac"])
        audio_layout.addRow(tr('task_edit_dialog.output_format'), self.output_format_combo)
        
        # 采样率
        self.sample_rate_combo = QComboBox()
        self.sample_rate_combo.addItems(["8000", "16000", "22050", "44100", "48000"])
        audio_layout.addRow(tr('task_edit_dialog.sample_rate'), self.sample_rate_combo)
        
        # 位深度
        self.bit_depth_combo = QComboBox()
        self.bit_depth_combo.addItems(["8", "16", "24", "32"])
        audio_layout.addRow(tr('task_edit_dialog.bit_depth'), self.bit_depth_combo)
        
        # 声道数
        self.channels_combo = QComboBox()
        self.channels_combo.addItems([tr('task_edit_dialog.mono'), tr('task_edit_dialog.stereo')])
        audio_layout.addRow(tr('task_edit_dialog.channels'), self.channels_combo)
        
        # 比特率
        self.bitrate_combo = QComboBox()
        self.bitrate_combo.addItems(["64", "128", "192", "256", "320"])
        self.bitrate_combo.setVisible(False)
        audio_layout.addRow(tr('task_edit_dialog.bitrate'), self.bitrate_combo)
        
        layout.addWidget(audio_group)
        
        # 按钮
        button_layout = QHBoxLayout()
        button_layout.addStretch()
        
        self.ok_button = QPushButton(tr('task_edit_dialog.ok'))
        self.ok_button.clicked.connect(self.accept)
        button_layout.addWidget(self.ok_button)
        
        self.cancel_button = QPushButton(tr('task_edit_dialog.cancel'))
        self.cancel_button.clicked.connect(self.reject)
        button_layout.addWidget(self.cancel_button)
        
        layout.addLayout(button_layout)
        
        # 连接信号
        self.engine_combo.currentTextChanged.connect(self.on_engine_changed)
        self.output_format_combo.currentTextChanged.connect(self.on_format_changed)
    
    def load_task_data(self):
        """加载任务数据"""
        try:
            # 文件信息
            self.input_file_edit.setText(self.task.file_path)
            self.output_file_edit.setText(self.task.output_path)
            
            # 语音配置
            # 注意：引擎选择会在load_available_engines中处理
            self.rate_spinbox.setValue(int(self.task.voice_config.rate * 100))
            self.pitch_spinbox.setValue(int(self.task.voice_config.pitch))
            self.volume_spinbox.setValue(int(self.task.voice_config.volume * 100))
            
            # 输出格式
            self.output_format_combo.setCurrentText(self.task.voice_config.output_format)
            
            # 加载语音列表（这会触发引擎选择和语音加载）
            self.on_engine_changed()
            
            # 设置当前语音
            current_voice = self.task.voice_config.voice_name
            for i in range(self.voice_combo.count()):
                voice_data = self.voice_combo.itemData(i)
                if voice_data and voice_data.get('id') == current_voice:
                    self.voice_combo.setCurrentIndex(i)
                    break
                elif voice_data and voice_data.get('name') == current_voice:
                    self.voice_combo.setCurrentIndex(i)
                    break
            
            # 音频格式参数
            if hasattr(self.task.voice_config, 'extra_params') and self.task.voice_config.extra_params:
                extra_params = self.task.voice_config.extra_params
                self.sample_rate_combo.setCurrentText(str(extra_params.get('sample_rate', 22050)))
                self.bit_depth_combo.setCurrentText(str(extra_params.get('bit_depth', 16)))
                
                channels = extra_params.get('channels', 1)
                if channels == 1:
                    self.channels_combo.setCurrentText("1 (单声道)")
                else:
                    self.channels_combo.setCurrentText("2 (立体声)")
                
                bitrate = extra_params.get('bitrate')
                if bitrate:
                    self.bitrate_combo.setCurrentText(str(bitrate))
                    self.bitrate_combo.setVisible(True)
                else:
                    self.bitrate_combo.setVisible(False)
            
        except Exception as e:
            QMessageBox.critical(self, tr('task_edit_dialog.messages.error'), tr('task_edit_dialog.messages.load_task_failed', error=str(e)))
    
    def load_available_engines(self):
        """加载可用的TTS引擎"""
        try:
            # 清空现有选项
            self.engine_combo.clear()
            
            # 定义引擎显示顺序：piper_tts 第一，edge_tts 第二，其他按原顺序
            preferred_order = ['piper_tts', 'edge_tts', 'pyttsx3']
            
            # 获取所有注册的引擎
            from services.tts_service import TTSServiceFactory
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
            
            # 设置当前任务的引擎为选中状态
            current_engine = self.task.voice_config.engine
            engine_text = f"{current_engine} ✓" if current_engine in available_engines else f"{current_engine} ✗"
            self.engine_combo.setCurrentText(engine_text)
            
            self.logger.info(f"加载了 {len(all_engines)} 个TTS引擎，其中 {len(available_engines)} 个可用")
            
        except Exception as e:
            self.logger.error(tr('task_edit_dialog.messages.load_engines_failed', error=str(e)))
            # 如果失败，使用硬编码的引擎列表作为备用
            self.engine_combo.addItems(["piper_tts", "pyttsx3"])
    
    def on_engine_changed(self):
        """语音引擎改变事件"""
        try:
            # 检查voice_combo是否存在（可能在初始化过程中被调用）
            if not hasattr(self, 'voice_combo') or self.voice_combo is None:
                self.logger.debug("on_engine_changed被调用但voice_combo尚未创建，跳过处理")
                return
            
            # 获取当前选择的引擎（从UI获取，而不是从服务获取）
            engine_text = self.engine_combo.currentText()
            engine = engine_text.replace(" ✓", "").replace(" ✗", "")
            
            self.voice_combo.clear()
            
            # 动态加载该引擎支持的语音
            from services.tts_service import TTSServiceFactory
            
            try:
                # 创建TTS服务实例
                tts_service = TTSServiceFactory.create_service(engine)
                if tts_service:
                    voices = tts_service.get_available_voices()
                    
                    # 添加语音到下拉框，使用与添加任务页面相同的格式
                    for voice in voices:
                        voice_id = voice.get('id', '')
                        voice_name = voice.get('name', '')
                        voice_language = voice.get('language', 'unknown')
                        
                        if voice_id and voice_id != voice_name:
                            display_text = f"{voice_id} - {voice_name} ({voice_language})"
                        else:
                            display_text = f"{voice_name} ({voice_language})"
                        
                        self.voice_combo.addItem(display_text, voice)
                    
                    # 自动选择默认语音
                    self._select_default_voice(engine, voices)
                    
                    self.logger.info(f"为引擎 {engine} 加载了 {len(voices)} 个语音")
                else:
                    self.logger.warning(f"无法创建引擎服务: {engine}")
                    # 添加默认语音作为后备
                    self._add_default_voices(engine)
                    # 选择第一个语音作为默认
                    if self.voice_combo.count() > 0:
                        self.voice_combo.setCurrentIndex(0)
                    
            except Exception as e:
                self.logger.error(f"加载引擎 {engine} 语音失败: {e}")
                # 如果加载失败，使用默认语音
                self._add_default_voices(engine)
                # 选择第一个语音作为默认
                if self.voice_combo.count() > 0:
                    self.voice_combo.setCurrentIndex(0)
                    
        except Exception as e:
            self.logger.error(tr('task_edit_dialog.messages.engine_changed_failed', error=str(e)))
    
    def _add_default_voices(self, engine: str):
        """添加默认语音作为后备方案"""
        try:
            # 检查voice_combo是否存在
            if not hasattr(self, 'voice_combo') or self.voice_combo is None:
                self.logger.debug("_add_default_voices被调用但voice_combo尚未创建，跳过处理")
                return
                
            if engine == "piper_tts":
                self.voice_combo.addItem("zh_CN-huayan-medium (zh-CN)", "zh_CN-huayan-medium")
                self.voice_combo.addItem("en_GB-alan-medium (en-GB)", "en_GB-alan-medium")
                self.voice_combo.addItem("en_GB-cori-medium (en-GB)", "en_GB-cori-medium")
            elif engine == "pyttsx3":
                self.voice_combo.addItem("TTS_MS_ZH-CN_HUIHUI_11.0 (zh-CN)", "TTS_MS_ZH-CN_HUIHUI_11.0")
                self.voice_combo.addItem("TTS_MS_EN-US_ZIRA_11.0 (en-US)", "TTS_MS_EN-US_ZIRA_11.0")
            else:
                # 通用默认语音
                self.voice_combo.addItem("默认语音 (unknown)", "default")
                
            self.logger.info(f"为引擎 {engine} 添加了默认语音列表")
            
        except Exception as e:
            self.logger.error(tr('task_edit_dialog.messages.add_default_voices_failed', error=str(e)))
    
    def _select_default_voice(self, engine: str, voices: list):
        """自动选择默认语音"""
        try:
            # 检查voice_combo是否存在
            if not hasattr(self, 'voice_combo') or self.voice_combo is None:
                self.logger.debug("_select_default_voice被调用但voice_combo尚未创建，跳过处理")
                return
                
            # 定义各引擎的默认语音ID
            default_voice_mapping = {
                "piper_tts": "zh_CN-huayan-medium",
                "edge_tts": "zh-CN-XiaoxiaoNeural",
                "pyttsx3": None  # pyttsx3使用第一个可用语音
            }
            
            default_voice_id = default_voice_mapping.get(engine)
            selected_index = 0  # 默认选择第一个
            
            if default_voice_id:
                # 查找指定的默认语音
                for i, voice in enumerate(voices):
                    voice_id = voice.get('id', '')
                    if voice_id == default_voice_id:
                        selected_index = i
                        self.logger.info(f"为引擎 {engine} 选择了默认语音: {voice_id}")
                        break
                else:
                    # 如果没找到指定默认语音，选择第一个
                    self.logger.info(f"引擎 {engine} 的默认语音 {default_voice_id} 不存在，选择第一个可用语音")
            else:
                # 对于pyttsx3等没有特定默认语音的引擎，选择第一个
                self.logger.info(f"引擎 {engine} 选择第一个可用语音")
            
            # 设置选中的语音
            if self.voice_combo.count() > selected_index:
                self.voice_combo.setCurrentIndex(selected_index)
                selected_voice = voices[selected_index] if voices else {}
                self.logger.info(f"已选择语音: {selected_voice.get('name', 'Unknown')} ({selected_voice.get('language', 'unknown')})")
            
        except Exception as e:
            self.logger.error(tr('task_edit_dialog.messages.select_default_voice_failed', error=str(e)))
            # 如果选择失败，选择第一个
            if hasattr(self, 'voice_combo') and self.voice_combo and self.voice_combo.count() > 0:
                self.voice_combo.setCurrentIndex(0)
    
    def on_format_changed(self):
        """输出格式改变事件"""
        try:
            format_type = self.output_format_combo.currentText()
            
            # 根据格式类型设置比特率显示
            if format_type in ["mp3", "ogg", "m4a"]:
                self.bitrate_combo.setVisible(True)
            else:
                self.bitrate_combo.setVisible(False)
                
        except Exception as e:
            QMessageBox.critical(self, tr('task_edit_dialog.messages.error'), tr('task_edit_dialog.messages.format_changed_failed', error=str(e)))
    
    def browse_input_file(self):
        """浏览输入文件"""
        try:
            import os
            file_path, _ = QFileDialog.getOpenFileName(
                self, tr('task_edit_dialog.input_file'), "", 
                "文本文件 (*.txt);;所有文件 (*.*)"
            )
            if file_path:
                # 规范化路径，确保使用正确的路径分隔符
                normalized_path = os.path.normpath(file_path)
                self.input_file_edit.setText(normalized_path)
        except Exception as e:
            QMessageBox.critical(self, tr('task_edit_dialog.messages.error'), tr('task_edit_dialog.messages.browse_input_failed', error=str(e)))
    
    def browse_output_file(self):
        """浏览输出文件"""
        try:
            import os
            file_path, _ = QFileDialog.getSaveFileName(
                self, tr('task_edit_dialog.output_file'), "", 
                "音频文件 (*.wav *.mp3 *.ogg *.m4a *.flac);;所有文件 (*.*)"
            )
            if file_path:
                # 规范化路径，确保使用正确的路径分隔符
                normalized_path = os.path.normpath(file_path)
                self.output_file_edit.setText(normalized_path)
        except Exception as e:
            QMessageBox.critical(self, tr('task_edit_dialog.messages.error'), tr('task_edit_dialog.messages.browse_output_failed', error=str(e)))
    
    def get_updated_task(self) -> BatchTask:
        """获取更新后的任务"""
        try:
            # 获取选中的语音数据
            voice_data = self.voice_combo.currentData()
            if voice_data:
                # 从语音数据中提取信息
                voice_id = voice_data.get('id', '')
                voice_name = voice_data.get('name', '')
                voice_language = voice_data.get('language', 'zh-CN')
            else:
                # 如果没有语音数据，使用显示文本
                voice_id = self.voice_combo.currentText()
                voice_name = voice_id
                voice_language = "zh-CN"
            
            # 获取引擎名称（移除可用性标记）
            engine_text = self.engine_combo.currentText()
            engine = engine_text.replace(" ✓", "").replace(" ✗", "")
            
            # 创建新的语音配置
            voice_config = VoiceConfig(
                engine=engine,
                voice_name=voice_id,  # 使用语音ID
                rate=self.rate_spinbox.value() / 100.0,
                pitch=self.pitch_spinbox.value(),
                volume=self.volume_spinbox.value() / 100.0,
                language=voice_language,
                output_format=self.output_format_combo.currentText()
            )
            
            # 添加音频格式参数
            voice_config.extra_params = {
                'encoder': 'FFmpeg',  # 固定使用FFmpeg编码器
                'sample_rate': int(self.sample_rate_combo.currentText()),
                'bit_depth': int(self.bit_depth_combo.currentText()),
                'channels': 1 if "单声道" in self.channels_combo.currentText() else 2,
                'bitrate': int(self.bitrate_combo.currentText()) if self.bitrate_combo.isVisible() else None
            }
            
            # 创建更新后的任务
            updated_task = BatchTask(
                id=self.task.id,
                file_path=self.input_file_edit.text(),
                voice_config=voice_config,
                output_path=self.output_file_edit.text(),
                status=self.task.status
            )
            
            return updated_task
            
        except Exception as e:
            QMessageBox.critical(self, tr('task_edit_dialog.messages.error'), tr('task_edit_dialog.messages.create_updated_task_failed', error=str(e)))
            return self.task
