"""
输出设置界面
"""

from PyQt6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QLabel, 
    QComboBox, QSpinBox, QCheckBox, QLineEdit,
    QPushButton, QGroupBox, QFormLayout, QMessageBox,
    QFileDialog, QSlider, QTextEdit, QProgressBar,
    QScrollArea
)
from PyQt6.QtCore import Qt, pyqtSignal
from PyQt6.QtGui import QFont
from services.language_service import get_text as tr

from models.audio_model import OutputConfig
from utils.log_manager import LogManager


class OutputSettingsWidget(QWidget):
    """输出设置界面"""
    
    # 信号定义
    output_changed = pyqtSignal(object)  # 输出设置改变信号
    
    def __init__(self):
        super().__init__()
        self.logger = LogManager().get_logger("OutputSettingsWidget")
        
        # 配置服务
        from services.json_config_service import JsonConfigService
        self.config_service = JsonConfigService()
        
        # 当前输出配置
        self.current_output_config = OutputConfig()
        
        # 初始化UI
        self.setup_ui()
        self.setup_connections()
        self.load_config()
    
    def setup_ui(self):
        """设置用户界面"""
        layout = QVBoxLayout(self)
        layout.setContentsMargins(5, 5, 5, 5)
        layout.setSpacing(10)
        
        # 标题
        title_label = QLabel(tr('output_settings.title'))
        title_label.setStyleSheet("font-size: 16px; font-weight: bold; margin-bottom: 10px;")
        layout.addWidget(title_label)
        
        # 创建滚动区域
        scroll_area = QScrollArea()
        scroll_area.setWidgetResizable(True)
        scroll_area.setHorizontalScrollBarPolicy(Qt.ScrollBarPolicy.ScrollBarAlwaysOff)
        
        # 主内容部件
        content_widget = QWidget()
        content_layout = QVBoxLayout(content_widget)
        content_layout.setContentsMargins(5, 5, 5, 5)
        
        # 配置管理 - 移到最上面
        self.create_config_group(content_layout)
        
        # 音频格式设置
        self.create_audio_format_group(content_layout)
        
        # 质量设置
        self.create_quality_group(content_layout)
        
        # 字幕输出设置
        self.create_subtitle_group(content_layout)
        
        # 输出目录设置
        self.create_output_directory_group(content_layout)
        
        # 文件命名设置
        self.create_naming_group(content_layout)
        
        # 合并设置
        self.create_merge_group(content_layout)
        
        # 高级设置（隐藏）
        # self.create_advanced_group(content_layout)
        
        # 预览和测试（隐藏）
        # self.create_preview_group(content_layout)
        
        scroll_area.setWidget(content_widget)
        layout.addWidget(scroll_area)
    
    def create_audio_format_group(self, parent_layout):
        """创建音频格式设置组"""
        group = QGroupBox(tr('output_settings.audio_format'))
        layout = QFormLayout(group)
        
        # 输出格式
        self.format_combo = QComboBox()
        self.format_combo.addItems(["WAV", "MP3", "OGG", "M4A"])
        self.format_combo.setCurrentText("WAV")
        layout.addRow(tr('output_settings.output_format'), self.format_combo)
        
        # 编码器
        self.encoder_combo = QComboBox()
        self.encoder_combo.addItems(["FFmpeg", "LAME", "系统默认"])
        self.encoder_combo.setCurrentText("FFmpeg")
        layout.addRow(tr('output_settings.encoder'), self.encoder_combo)
        
        parent_layout.addWidget(group)
    
    def create_quality_group(self, parent_layout):
        """创建质量设置组"""
        group = QGroupBox(tr('output_settings.quality_settings'))
        layout = QFormLayout(group)
        
        # 比特率
        bitrate_layout = QHBoxLayout()
        self.bitrate_slider = QSlider(Qt.Orientation.Horizontal)
        self.bitrate_slider.setRange(64, 320)
        self.bitrate_slider.setValue(128)
        self.bitrate_slider.setTickPosition(QSlider.TickPosition.TicksBelow)
        self.bitrate_slider.setTickInterval(32)
        
        self.bitrate_label = QLabel("128 kbps")
        self.bitrate_slider.valueChanged.connect(
            lambda v: self.bitrate_label.setText(f"{v} kbps")
        )
        
        bitrate_layout.addWidget(self.bitrate_slider)
        bitrate_layout.addWidget(self.bitrate_label)
        layout.addRow(tr('output_settings.bitrate'), bitrate_layout)
        
        # 采样率
        self.sample_rate_combo = QComboBox()
        self.sample_rate_combo.addItems(["22050 Hz", "44100 Hz", "48000 Hz"])
        self.sample_rate_combo.setCurrentText("44100 Hz")
        layout.addRow(tr('output_settings.sample_rate'), self.sample_rate_combo)
        
        # 声道
        self.channels_combo = QComboBox()
        self.channels_combo.addItems([tr('output_settings.mono'), tr('output_settings.stereo')])
        self.channels_combo.setCurrentText(tr('output_settings.stereo'))
        layout.addRow(tr('output_settings.channels'), self.channels_combo)
        
        parent_layout.addWidget(group)
    
    def create_subtitle_group(self, parent_layout):
        """创建字幕输出设置组"""
        group = QGroupBox(tr('output_settings.subtitle_output'))
        layout = QFormLayout(group)
        
        # 是否生成字幕文件
        self.generate_subtitle_check = QCheckBox(tr('output_settings.generate_subtitle'))
        self.generate_subtitle_check.setChecked(False)
        layout.addRow("", self.generate_subtitle_check)
        
        # 字幕文件类型选择
        self.subtitle_format_combo = QComboBox()
        self.subtitle_format_combo.addItems([
            tr('output_settings.lrc_format'),
            tr('output_settings.srt_format'),
            tr('output_settings.vtt_format'),
            tr('output_settings.ass_format')
        ])
        self.subtitle_format_combo.setCurrentText(tr('output_settings.lrc_format'))
        layout.addRow(tr('output_settings.subtitle_format'), self.subtitle_format_combo)
        
        # 字幕编码
        self.subtitle_encoding_combo = QComboBox()
        self.subtitle_encoding_combo.addItems(["UTF-8", "GBK", "GB2312"])
        self.subtitle_encoding_combo.setCurrentText("UTF-8")
        layout.addRow(tr('output_settings.subtitle_encoding'), self.subtitle_encoding_combo)
        
        # 时间偏移
        self.subtitle_offset_spin = QSpinBox()
        self.subtitle_offset_spin.setRange(-60, 60)
        self.subtitle_offset_spin.setValue(0)
        self.subtitle_offset_spin.setSuffix(f" {tr('output_settings.seconds')}")
        layout.addRow(tr('output_settings.time_offset'), self.subtitle_offset_spin)
        
        # 字幕样式设置（仅ASS格式显示）
        self.subtitle_style_label = QLabel(tr('output_settings.subtitle_style'))
        self.subtitle_style_button = QPushButton(tr('output_settings.set_style'))
        self.subtitle_style_button.setEnabled(False)
        self.subtitle_style_button.clicked.connect(self.open_subtitle_style_dialog)
        layout.addRow(self.subtitle_style_label, self.subtitle_style_button)
        
        # 初始时隐藏字幕样式设置
        self.subtitle_style_label.hide()
        self.subtitle_style_button.hide()
        
        # 根据字幕格式启用/禁用样式设置
        self.subtitle_format_combo.currentTextChanged.connect(self.update_subtitle_style_visibility)
        
        parent_layout.addWidget(group)
    
    def create_output_directory_group(self, parent_layout):
        """创建输出目录设置组"""
        group = QGroupBox(tr('output_settings.output_directory'))
        layout = QFormLayout(group)
        
        # 输出目录选择
        dir_layout = QHBoxLayout()
        self.output_dir_edit = QLineEdit()
        self.output_dir_edit.setPlaceholderText(tr('output_settings.select_output_dir'))
        self.output_dir_edit.setText("./output")
        
        self.browse_dir_button = QPushButton(tr('output_settings.browse'))
        self.browse_dir_button.clicked.connect(self.browse_output_directory)
        
        dir_layout.addWidget(self.output_dir_edit)
        dir_layout.addWidget(self.browse_dir_button)
        layout.addRow(tr('output_settings.output_dir'), dir_layout)
        
        # 创建子目录
        self.create_subdir_check = QCheckBox(tr('output_settings.create_subdir'))
        self.create_subdir_check.setChecked(True)
        layout.addRow("", self.create_subdir_check)
        
        # 子目录命名
        self.subdir_name_edit = QLineEdit()
        self.subdir_name_edit.setPlaceholderText(tr('output_settings.project_name'))
        self.subdir_name_edit.setText("{project_name}")
        layout.addRow(tr('output_settings.subdir_name'), self.subdir_name_edit)
        
        parent_layout.addWidget(group)
    
    def create_naming_group(self, parent_layout):
        """创建文件命名设置组"""
        group = QGroupBox(tr('output_settings.file_naming'))
        layout = QFormLayout(group)
        
        # 文件命名模式
        self.naming_combo = QComboBox()
        # 使用固定的中文文本，暂时不支持多语言
        self.naming_options = {
            "chapter_number_title": "章节序号 + 标题",
            "sequence_title": "顺序号 + 标题",
            "title_only": "仅标题",
            "sequence_only": "仅顺序号",
            "original_filename": "原始文件名",
            "custom": "自定义"
        }
        self.naming_combo.addItems(list(self.naming_options.values()))
        self.naming_combo.setCurrentText(self.naming_options["chapter_number_title"])
        layout.addRow(tr('output_settings.naming_mode'), self.naming_combo)
        
        # 自定义命名模板
        self.custom_name_edit = QLineEdit()
        self.custom_name_edit.setPlaceholderText("{chapter_num}_{title}")
        self.custom_name_edit.setText("{chapter_num:02d}_{title}")
        self.custom_name_edit.setEnabled(False)
        
        # 创建自定义模板标签
        self.custom_template_label = QLabel(tr('output_settings.custom_template'))
        
        # 将自定义模板添加到布局中，但初始时隐藏
        self.custom_template_row = layout.rowCount()
        layout.addRow(self.custom_template_label, self.custom_name_edit)
        
        # 初始时隐藏自定义模板
        self.custom_template_label.hide()
        self.custom_name_edit.hide()
        
        # 命名模式改变时控制自定义模板的显示/隐藏
        self.naming_combo.currentTextChanged.connect(self.on_naming_mode_changed)
        
        # 文件名长度限制
        self.name_length_spin = QSpinBox()
        self.name_length_spin.setRange(10, 200)
        self.name_length_spin.setValue(50)
        layout.addRow(tr('output_settings.name_length_limit'), self.name_length_spin)
        
        parent_layout.addWidget(group)
    
    def get_naming_mode_key(self, display_text):
        """根据显示文本获取命名模式键值"""
        try:
            if not hasattr(self, 'naming_options') or not self.naming_options:
                return "chapter_number_title"  # 默认值
            
            for key, value in self.naming_options.items():
                if value == display_text:
                    return key
            return "chapter_number_title"  # 默认值
        except:
            return "chapter_number_title"  # 默认值
    
    
    def create_merge_group(self, parent_layout):
        """创建合并设置组"""
        group = QGroupBox(tr('output_settings.merge_settings'))
        layout = QFormLayout(group)
        
        # 是否合并
        self.merge_check = QCheckBox(tr('output_settings.merge_all_chapters'))
        self.merge_check.setChecked(False)
        layout.addRow("", self.merge_check)
        
        # 合并文件名
        self.merge_name_edit = QLineEdit()
        self.merge_name_edit.setPlaceholderText(tr('output_settings.merge_name_placeholder'))
        self.merge_name_edit.setText("完整音频")
        self.merge_name_edit.setEnabled(False)
        layout.addRow(tr('output_settings.merge_filename'), self.merge_name_edit)
        
        # 启用合并文件名编辑
        self.merge_check.toggled.connect(self.merge_name_edit.setEnabled)
        
        # 章节标记
        self.chapter_markers_check = QCheckBox(tr('output_settings.add_chapter_markers'))
        self.chapter_markers_check.setChecked(True)
        layout.addRow("", self.chapter_markers_check)
        
        # 章节间隔
        self.chapter_interval_spin = QSpinBox()
        self.chapter_interval_spin.setRange(0, 10)
        self.chapter_interval_spin.setValue(2)
        self.chapter_interval_spin.setSuffix(f" {tr('output_settings.seconds')}")
        layout.addRow(tr('output_settings.chapter_interval'), self.chapter_interval_spin)
        
        parent_layout.addWidget(group)
    
    def create_advanced_group(self, parent_layout):
        """创建高级设置组"""
        group = QGroupBox("高级设置")
        layout = QFormLayout(group)
        
        # 音频预处理（隐藏）
        # self.normalize_check = QCheckBox("音频标准化")
        # self.normalize_check.setChecked(True)
        # layout.addRow("", self.normalize_check)
        # 
        # self.noise_reduction_check = QCheckBox("降噪处理")
        # self.noise_reduction_check.setChecked(False)
        # layout.addRow("", self.noise_reduction_check)
        
        # 并发处理
        self.concurrent_spin = QSpinBox()
        self.concurrent_spin.setRange(1, 8)
        self.concurrent_spin.setValue(2)
        layout.addRow("并发处理数:", self.concurrent_spin)
        
        # 临时文件清理
        self.cleanup_check = QCheckBox("处理完成后清理临时文件")
        self.cleanup_check.setChecked(True)
        layout.addRow("", self.cleanup_check)
        
        parent_layout.addWidget(group)
    
    def create_preview_group(self, parent_layout):
        """创建预览和测试组"""
        group = QGroupBox("预览和测试")
        layout = QFormLayout(group)
        
        # 预览按钮
        self.preview_button = QPushButton("预览输出设置")
        self.preview_button.clicked.connect(self.preview_settings)
        layout.addRow("", self.preview_button)
        
        # 测试输出按钮
        self.test_output_button = QPushButton("测试输出")
        self.test_output_button.clicked.connect(self.test_output)
        layout.addRow("", self.test_output_button)
        
        # 预览文本
        self.preview_text = QTextEdit()
        self.preview_text.setMaximumHeight(100)
        self.preview_text.setPlaceholderText("输出设置预览将显示在这里...")
        layout.addRow("预览:", self.preview_text)
        
        parent_layout.addWidget(group)
    
    def create_config_group(self, parent_layout):
        """创建配置管理组"""
        group = QGroupBox(tr('output_settings.config_management'))
        layout = QVBoxLayout(group)
        
        # 配置管理按钮
        config_button_layout = QHBoxLayout()
        
        self.save_config_button = QPushButton(tr('output_settings.save_config'))
        self.save_config_button.clicked.connect(self.save_config)
        config_button_layout.addWidget(self.save_config_button)
        
        self.load_config_button = QPushButton(tr('output_settings.load_config'))
        self.load_config_button.clicked.connect(self.load_config)
        config_button_layout.addWidget(self.load_config_button)
        
        self.export_config_button = QPushButton(tr('output_settings.export_config'))
        self.export_config_button.clicked.connect(self.export_config)
        config_button_layout.addWidget(self.export_config_button)
        
        self.import_config_button = QPushButton(tr('output_settings.import_config'))
        self.import_config_button.clicked.connect(self.import_config)
        config_button_layout.addWidget(self.import_config_button)
        
        layout.addLayout(config_button_layout)
        
        # 配置状态显示
        self.config_status_label = QLabel(f"{tr('output_settings.config_status')} {tr('output_settings.not_saved')}")
        self.config_status_label.setStyleSheet("color: #666; font-size: 12px;")
        layout.addWidget(self.config_status_label)
        
        parent_layout.addWidget(group)
    
    def setup_connections(self):
        """设置信号连接"""
        # 格式改变时更新编码器选项
        self.format_combo.currentTextChanged.connect(self.update_encoder_options)
        
        # 设置改变时更新预览
        self.format_combo.currentTextChanged.connect(self.update_preview)
        self.bitrate_slider.valueChanged.connect(self.update_preview)
        self.sample_rate_combo.currentTextChanged.connect(self.update_preview)
        self.channels_combo.currentTextChanged.connect(self.update_preview)
        self.output_dir_edit.textChanged.connect(self.update_preview)
        self.naming_combo.currentTextChanged.connect(self.update_preview)
        self.merge_check.toggled.connect(self.update_preview)
        
        # 字幕设置改变时更新预览
        self.generate_subtitle_check.toggled.connect(self.update_preview)
        self.subtitle_format_combo.currentTextChanged.connect(self.update_preview)
        self.subtitle_encoding_combo.currentTextChanged.connect(self.update_preview)
        self.subtitle_offset_spin.valueChanged.connect(self.update_preview)
        
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
            # 保存当前状态（在删除UI之前）
            current_naming_mode = "chapter_number_title"  # 默认值
            if hasattr(self, 'naming_combo') and self.naming_combo is not None:
                try:
                    current_naming_mode = self.get_naming_mode_key(self.naming_combo.currentText())
                except:
                    current_naming_mode = "chapter_number_title"
            
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
            
            # 重新设置命名选项（使用固定的中文文本）
            self.naming_options = {
                "chapter_number_title": "章节序号 + 标题",
                "sequence_title": "顺序号 + 标题",
                "title_only": "仅标题",
                "sequence_only": "仅顺序号",
                "original_filename": "原始文件名",
                "custom": "自定义"
            }
            
            # 恢复状态
            if hasattr(self, 'naming_combo') and self.naming_combo is not None:
                try:
                    self.naming_combo.setCurrentText(self.naming_options.get(current_naming_mode, self.naming_options["chapter_number_title"]))
                except:
                    pass  # 如果设置失败，使用默认值
            
        except Exception as e:
            self.logger.error(f"重新创建UI失败: {e}")
    
    def on_naming_mode_changed(self, naming_mode):
        """命名模式改变事件"""
        try:
            naming_mode_key = self.get_naming_mode_key(naming_mode)
            if naming_mode_key == "custom":
                # 显示自定义模板
                self.custom_template_label.show()
                self.custom_name_edit.show()
                self.custom_name_edit.setEnabled(True)
            else:
                # 隐藏自定义模板
                self.custom_template_label.hide()
                self.custom_name_edit.hide()
                self.custom_name_edit.setEnabled(False)
            
            # 更新预览
            self.update_preview()
            
        except Exception as e:
            self.logger.error(tr('output_settings.messages.naming_mode_changed_failed', error=str(e)))
    
    def update_encoder_options(self, format_text):
        """更新编码器选项"""
        self.encoder_combo.clear()
        
        if format_text == "WAV":
            self.encoder_combo.addItems(["FFmpeg", "PCM"])
        elif format_text == "MP3":
            self.encoder_combo.addItems(["FFmpeg", "LAME"])
        elif format_text == "OGG":
            self.encoder_combo.addItems(["FFmpeg", "Vorbis"])
        elif format_text == "M4A":
            self.encoder_combo.addItems(["FFmpeg", "AAC"])
        
        self.encoder_combo.setCurrentIndex(0)
    
    def update_preview(self):
        """更新预览"""
        preview_text = f"""
输出格式: {self.format_combo.currentText()}
编码器: {self.encoder_combo.currentText()}
比特率: {self.bitrate_slider.value()} kbps
采样率: {self.sample_rate_combo.currentText()}
声道: {self.channels_combo.currentText()}
输出目录: {self.output_dir_edit.text()}
命名模式: {self.naming_combo.currentText()}
合并文件: {'是' if self.merge_check.isChecked() else '否'}
字幕输出: {'是' if self.generate_subtitle_check.isChecked() else '否'}
字幕格式: {self.subtitle_format_combo.currentText()}
字幕编码: {self.subtitle_encoding_combo.currentText()}
时间偏移: {self.subtitle_offset_spin.value()} 秒
        """.strip()
        
        # 检查预览文本组件是否存在
        if hasattr(self, 'preview_text') and self.preview_text:
            self.preview_text.setPlainText(preview_text)
        
        # 更新当前配置并发送信号
        self.update_current_config()
        self.output_changed.emit(self.current_output_config)
    
    def update_current_config(self):
        """更新当前输出配置"""
        try:
            # 更新当前配置
            self.current_output_config.output_dir = self.output_dir_edit.text()
            self.current_output_config.format = self.format_combo.currentText().lower()
            self.current_output_config.bitrate = self.bitrate_slider.value()
            self.current_output_config.sample_rate = int(self.sample_rate_combo.currentText().replace(' Hz', ''))
            self.current_output_config.channels = 2 if self.channels_combo.currentText() == "立体声" else 1
            self.current_output_config.merge_files = self.merge_check.isChecked()
            self.current_output_config.merge_filename = self.merge_name_edit.text()
            self.current_output_config.chapter_markers = self.chapter_markers_check.isChecked()
            self.current_output_config.chapter_interval = self.chapter_interval_spin.value()
            # 音频预处理设置（已隐藏，使用默认值）
            self.current_output_config.normalize = True  # 默认启用音频标准化
            self.current_output_config.noise_reduction = False  # 默认禁用降噪处理
            # 高级设置（已隐藏，使用默认值）
            self.current_output_config.concurrent_workers = 2  # 默认并发处理数
            self.current_output_config.cleanup_temp = True  # 默认清理临时文件
            
            # 文件命名设置
            self.current_output_config.naming_mode = self.get_naming_mode_key(self.naming_combo.currentText())
            self.current_output_config.custom_template = self.custom_name_edit.text()
            self.current_output_config.name_length_limit = self.name_length_spin.value()
            
            # 字幕设置
            self.current_output_config.generate_subtitle = self.generate_subtitle_check.isChecked()
            self.current_output_config.subtitle_format = self.subtitle_format_combo.currentText().lower()
            self.current_output_config.subtitle_encoding = self.subtitle_encoding_combo.currentText()
            self.current_output_config.subtitle_offset = self.subtitle_offset_spin.value()
            
        except Exception as e:
            self.logger.error(tr('output_settings.messages.update_config_failed', error=str(e)))
    
    def browse_output_directory(self):
        """浏览输出目录"""
        directory = QFileDialog.getExistingDirectory(
            self, tr('output_settings.select_output_dir'), self.output_dir_edit.text()
        )
        if directory:
            self.output_dir_edit.setText(directory)
    
    def preview_settings(self):
        """预览输出设置"""
        self.update_preview()
        QMessageBox.information(self, tr('output_settings.preview'), tr('output_settings.messages.preview_updated'))
    
    def test_output(self):
        """测试输出"""
        # 这里可以添加实际的输出测试逻辑
        QMessageBox.information(self, tr('output_settings.test_output'), tr('output_settings.messages.test_pending'))
    
    def get_output_config(self):
        """获取输出配置"""
        # 获取输出目录路径
        output_dir = self.output_dir_edit.text().strip()
        if not output_dir:
            output_dir = "./output"
        
        # 获取字幕格式
        subtitle_format_text = self.subtitle_format_combo.currentText()
        if "LRC" in subtitle_format_text:
            subtitle_format = "lrc"
        elif "SRT" in subtitle_format_text:
            subtitle_format = "srt"
        elif "VTT" in subtitle_format_text:
            subtitle_format = "vtt"
        elif "ASS" in subtitle_format_text:
            subtitle_format = "ass"
        else:
            subtitle_format = "lrc"
        
        # 获取字幕编码
        subtitle_encoding = self.subtitle_encoding_combo.currentText().lower()
        
        # 创建配置对象，路径转换会在__post_init__中自动处理
        config = OutputConfig(
            output_dir=output_dir,
            format=self.format_combo.currentText().lower(),
            bitrate=self.bitrate_slider.value(),
            sample_rate=int(self.sample_rate_combo.currentText().split()[0]),
            channels=2 if self.channels_combo.currentText() == "立体声" else 1,
            merge_files=self.merge_check.isChecked(),
            merge_filename=self.merge_name_edit.text(),
            chapter_markers=self.chapter_markers_check.isChecked(),
            chapter_interval=self.chapter_interval_spin.value(),
            normalize=True,  # 默认启用音频标准化
            noise_reduction=False,  # 默认禁用降噪处理
            concurrent_workers=2,  # 默认并发处理数
            cleanup_temp=True,  # 默认清理临时文件
            # 文件命名设置
            naming_mode=self.get_naming_mode_key(self.naming_combo.currentText()),
            custom_template=self.custom_name_edit.text(),
            name_length_limit=self.name_length_spin.value(),
            # 字幕设置
            generate_subtitle=self.generate_subtitle_check.isChecked(),
            subtitle_format=subtitle_format,
            subtitle_encoding=subtitle_encoding,
            subtitle_offset=float(self.subtitle_offset_spin.value()),
            subtitle_style=getattr(self, 'subtitle_style_config', {})
        )
        
        return config
    
    def set_output_config(self, config: OutputConfig):
        """设置输出配置"""
        self.format_combo.setCurrentText(config.format.upper())
        self.bitrate_slider.setValue(config.bitrate)
        self.sample_rate_combo.setCurrentText(f"{config.sample_rate} Hz")
        self.channels_combo.setCurrentText("立体声" if config.channels == 2 else "单声道")
        self.output_dir_edit.setText(config.output_dir)
        self.merge_check.setChecked(config.merge_files)
        self.merge_name_edit.setText(config.merge_filename)
        self.chapter_markers_check.setChecked(config.chapter_markers)
        self.chapter_interval_spin.setValue(config.chapter_interval)
        # 高级设置（已隐藏，跳过设置）
        # self.normalize_check.setChecked(config.normalize)
        # self.noise_reduction_check.setChecked(config.noise_reduction)
        # self.concurrent_spin.setValue(config.concurrent_workers)
        # self.cleanup_check.setChecked(config.cleanup_temp)
        
        # 文件命名设置
        naming_mode = getattr(config, 'naming_mode', 'chapter_number_title')
        # 将键值转换为显示文本
        naming_display_text = self.naming_options.get(naming_mode, '章节序号 + 标题')
        self.naming_combo.setCurrentText(naming_display_text)
        self.custom_name_edit.setText(getattr(config, 'custom_template', '{chapter_num:02d}_{title}'))
        self.name_length_spin.setValue(getattr(config, 'name_length_limit', 50))
        
        # 根据命名模式设置自定义模板的显示状态
        self.on_naming_mode_changed(naming_display_text)
        
        # 字幕设置
        self.generate_subtitle_check.setChecked(getattr(config, 'generate_subtitle', False))
        
        # 设置字幕格式
        subtitle_format = getattr(config, 'subtitle_format', 'lrc')
        if subtitle_format == 'lrc':
            self.subtitle_format_combo.setCurrentText("LRC (歌词格式)")
        elif subtitle_format == 'srt':
            self.subtitle_format_combo.setCurrentText("SRT (通用字幕)")
        elif subtitle_format == 'vtt':
            self.subtitle_format_combo.setCurrentText("VTT (WebVTT)")
        elif subtitle_format == 'ass':
            self.subtitle_format_combo.setCurrentText("ASS (高级字幕)")
        else:
            self.subtitle_format_combo.setCurrentText("LRC (歌词格式)")
        
        # 根据字幕格式设置字幕样式的显示状态
        self.update_subtitle_style_visibility(self.subtitle_format_combo.currentText())
        
        # 设置字幕编码
        subtitle_encoding = getattr(config, 'subtitle_encoding', 'utf-8')
        self.subtitle_encoding_combo.setCurrentText(subtitle_encoding.upper())
        
        # 设置时间偏移
        self.subtitle_offset_spin.setValue(int(getattr(config, 'subtitle_offset', 0.0)))
        
        # 设置字幕样式
        self.subtitle_style_config = getattr(config, 'subtitle_style', {})
        
        self.update_preview()
    
    def load_config(self):
        """加载配置"""
        try:
            self.current_output_config = self.config_service.load_output_config()
            
            # 更新UI
            self.set_output_config(self.current_output_config)
            
            self.config_status_label.setText(f"{tr('output_settings.config_status')} {tr('output_settings.loaded')}")
            self.config_status_label.setStyleSheet("color: green; font-size: 12px;")
            
            self.logger.info(tr('output_settings.messages.config_loaded'))
            
        except Exception as e:
            self.logger.error(tr('output_settings.messages.load_failed', error=str(e)))
            QMessageBox.critical(self, tr('output_settings.messages.error'), tr('output_settings.messages.load_failed', error=str(e)))
    
    def save_config(self):
        """保存配置"""
        try:
            # 更新当前配置
            self.current_output_config = self.get_output_config()
            
            # 保存到配置文件
            self.config_service.save_output_config(self.current_output_config)
            
            self.config_status_label.setText(f"{tr('output_settings.config_status')} {tr('output_settings.saved')}")
            self.config_status_label.setStyleSheet("color: green; font-size: 12px;")
            
            QMessageBox.information(self, tr('output_settings.messages.success'), tr('output_settings.messages.config_saved'))
            self.logger.info(tr('output_settings.messages.config_saved'))
            
        except Exception as e:
            self.logger.error(tr('output_settings.messages.save_failed', error=str(e)))
            QMessageBox.critical(self, tr('output_settings.messages.error'), tr('output_settings.messages.save_failed', error=str(e)))
    
    def export_config(self):
        """导出配置"""
        try:
            file_path, _ = QFileDialog.getSaveFileName(
                self, 
                tr('output_settings.export_config'), 
                "output_config.ini",
                "配置文件 (*.ini);;所有文件 (*)"
            )
            
            if file_path:
                self.config_service.export_config(file_path)
                QMessageBox.information(self, tr('output_settings.messages.success'), tr('output_settings.messages.config_exported', path=file_path))
                self.logger.info(tr('output_settings.messages.config_exported', path=file_path))
                
        except Exception as e:
            self.logger.error(tr('output_settings.messages.export_failed', error=str(e)))
            QMessageBox.critical(self, tr('output_settings.messages.error'), tr('output_settings.messages.export_failed', error=str(e)))
    
    def import_config(self):
        """导入配置"""
        try:
            file_path, _ = QFileDialog.getOpenFileName(
                self, 
                tr('output_settings.import_config'), 
                "",
                "配置文件 (*.ini);;所有文件 (*)"
            )
            
            if file_path:
                self.config_service.import_config(file_path)
                # 重新加载配置
                self.load_config()
                QMessageBox.information(self, tr('output_settings.messages.success'), tr('output_settings.messages.config_imported', path=file_path))
                self.logger.info(tr('output_settings.messages.config_imported', path=file_path))
                
        except Exception as e:
            self.logger.error(tr('output_settings.messages.import_failed', error=str(e)))
            QMessageBox.critical(self, tr('output_settings.messages.error'), tr('output_settings.messages.import_failed', error=str(e)))
    
    def update_subtitle_style_visibility(self, format_text):
        """更新字幕样式设置的可见性"""
        is_ass_format = "ASS" in format_text
        self.subtitle_style_label.setVisible(is_ass_format)
        self.subtitle_style_button.setVisible(is_ass_format)
        self.subtitle_style_button.setEnabled(is_ass_format)
    
    def open_subtitle_style_dialog(self):
        """打开字幕样式设置对话框"""
        from PyQt6.QtWidgets import QDialog, QDialogButtonBox
        
        dialog = QDialog(self)
        dialog.setWindowTitle(tr('output_settings.subtitle_style_dialog'))
        dialog.setModal(True)
        dialog.resize(400, 300)
        
        layout = QVBoxLayout(dialog)
        
        # 样式设置表单
        form_layout = QFormLayout()
        
        # 字体设置
        font_name_edit = QLineEdit("Arial")
        font_size_spin = QSpinBox()
        font_size_spin.setRange(8, 72)
        font_size_spin.setValue(20)
        
        # 颜色设置
        primary_color_edit = QLineEdit("&H00FFFFFF")
        secondary_color_edit = QLineEdit("&H000000FF")
        outline_color_edit = QLineEdit("&H00000000")
        back_color_edit = QLineEdit("&H80000000")
        
        # 效果设置
        bold_check = QCheckBox(tr('output_settings.bold'))
        italic_check = QCheckBox(tr('output_settings.italic'))
        underline_check = QCheckBox(tr('output_settings.underline'))
        
        # 对齐设置
        alignment_combo = QComboBox()
        alignment_combo.addItems([
            tr('output_settings.bottom_left'), tr('output_settings.bottom_center'), tr('output_settings.bottom_right'),
            tr('output_settings.top_left'), tr('output_settings.top_center'), tr('output_settings.top_right'),
            tr('output_settings.left_center'), tr('output_settings.center'), tr('output_settings.right_center')
        ])
        alignment_combo.setCurrentText(tr('output_settings.bottom_center'))
        
        # 边距设置
        margin_l_spin = QSpinBox()
        margin_l_spin.setRange(0, 100)
        margin_l_spin.setValue(10)
        margin_r_spin = QSpinBox()
        margin_r_spin.setRange(0, 100)
        margin_r_spin.setValue(10)
        margin_v_spin = QSpinBox()
        margin_v_spin.setRange(0, 100)
        margin_v_spin.setValue(10)
        
        # 添加到表单
        form_layout.addRow(tr('output_settings.font_name'), font_name_edit)
        form_layout.addRow(tr('output_settings.font_size'), font_size_spin)
        form_layout.addRow(tr('output_settings.primary_color'), primary_color_edit)
        form_layout.addRow(tr('output_settings.secondary_color'), secondary_color_edit)
        form_layout.addRow(tr('output_settings.outline_color'), outline_color_edit)
        form_layout.addRow(tr('output_settings.back_color'), back_color_edit)
        form_layout.addRow("", bold_check)
        form_layout.addRow("", italic_check)
        form_layout.addRow("", underline_check)
        form_layout.addRow(tr('output_settings.alignment'), alignment_combo)
        form_layout.addRow(tr('output_settings.left_margin'), margin_l_spin)
        form_layout.addRow(tr('output_settings.right_margin'), margin_r_spin)
        form_layout.addRow(tr('output_settings.vertical_margin'), margin_v_spin)
        
        layout.addLayout(form_layout)
        
        # 按钮
        button_box = QDialogButtonBox(QDialogButtonBox.StandardButton.Ok | QDialogButtonBox.StandardButton.Cancel)
        button_box.accepted.connect(dialog.accept)
        button_box.rejected.connect(dialog.reject)
        layout.addWidget(button_box)
        
        if dialog.exec() == QDialog.DialogCode.Accepted:
            # 保存样式设置
            style_config = {
                "fontname": font_name_edit.text(),
                "fontsize": font_size_spin.value(),
                "primarycolor": primary_color_edit.text(),
                "secondarycolor": secondary_color_edit.text(),
                "outlinecolor": outline_color_edit.text(),
                "backcolor": back_color_edit.text(),
                "bold": 1 if bold_check.isChecked() else 0,
                "italic": 1 if italic_check.isChecked() else 0,
                "underline": 1 if underline_check.isChecked() else 0,
                "alignment": alignment_combo.currentIndex() + 1,
                "margin_l": margin_l_spin.value(),
                "margin_r": margin_r_spin.value(),
                "margin_v": margin_v_spin.value()
            }
            
            # 存储样式配置（这里可以保存到配置中）
            self.subtitle_style_config = style_config
            QMessageBox.information(self, tr('output_settings.messages.success'), tr('output_settings.messages.style_saved'))
