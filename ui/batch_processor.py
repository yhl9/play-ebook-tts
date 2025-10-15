"""
批量处理界面
"""

import os
from PyQt6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QLabel, 
    QPushButton, QListWidget, QListWidgetItem, QTableWidget,
    QTableWidgetItem, QProgressBar, QGroupBox, QMessageBox,
    QFrame, QSplitter, QTextEdit, QComboBox, QSpinBox,
    QFileDialog
)
from PyQt6.QtCore import Qt, pyqtSignal, QTimer, QThread
from PyQt6.QtGui import QIcon, QFont
from services.language_service import get_text as tr, get_language_service

from controllers.batch_controller import BatchController, BatchTask, TaskStatus
from models.audio_model import VoiceConfig
from utils.log_manager import LogManager


class BatchProcessorWidget(QWidget):
    """批量处理界面"""
    
    # 信号定义
    task_completed = pyqtSignal(str)  # 任务完成信号
    
    def __init__(self, batch_controller: BatchController):
        super().__init__()
        self.batch_controller = batch_controller
        self.logger = LogManager().get_logger("BatchProcessorWidget")
        
        # 定时器用于更新状态
        self.update_timer = QTimer()
        self.update_timer.timeout.connect(self.update_status)
        # 不自动启动，只在有任务处理时启动
        
        # 性能优化：缓存语音ComboBox，避免重复创建
        self._voice_combo_cache = {}  # 缓存已创建的语音ComboBox
        self._cached_voices = {}  # 缓存各引擎的语音列表
        self._last_voice_update = 0  # 上次更新语音列表的时间戳
        
        # 初始化UI
        self.setup_ui()
        self.setup_connections()
    
    def setup_ui(self):
        """设置用户界面"""
        layout = QVBoxLayout(self)
        layout.setContentsMargins(3, 3, 3, 3)  # 减少边距
        layout.setSpacing(5)  # 减少间距
        
        # 标题 - 使用更紧凑的样式
        title_label = QLabel(tr("tabs.batch_processing"))
        title_label.setStyleSheet("font-size: 14px; font-weight: bold; margin: 2px 0px; padding: 2px;")

        splitterTop = QSplitter(Qt.Orientation.Vertical)
        splitterTop.setSizes([200,800])
        splitterTop.addWidget(title_label)

        layout.addWidget(splitterTop)

        # layout.addWidget(title_label)
        
        # 创建分割器
        splitter = QSplitter(Qt.Orientation.Horizontal)

        # layout.addWidget(splitter)
        splitterTop.addWidget(splitter)
        # 左侧：任务列表和任务详情
        left_widget = self.create_left_panel()
        splitter.addWidget(left_widget)
        
        # 右侧：生成文件列表和控制
        right_widget = self.create_right_panel()
        splitter.addWidget(right_widget)
        
        # 设置分割器比例 - 任务列表占用更多空间
        splitter.setSizes([700, 300])  # 7:3的比例，任务列表占70%
    
    def create_left_panel(self):
        """创建左侧面板（任务列表和任务详情）"""
        widget = QFrame()
        widget.setFrameStyle(QFrame.Shape.StyledPanel)
        layout = QVBoxLayout(widget)
        layout.setContentsMargins(3, 3, 3, 3)
        layout.setSpacing(5)
        
        # 任务列表
        task_list_widget = self.create_task_list()
        layout.addWidget(task_list_widget)
        
        # 任务详情组
        details_group = QGroupBox(tr("batch_processor.task_details"))
        details_group.setStyleSheet("QGroupBox { font-size: 12px; margin-top: 5px; }")
        details_layout = QVBoxLayout(details_group)
        details_layout.setContentsMargins(3, 8, 3, 3)
        details_layout.setSpacing(3)
        
        # 任务信息
        self.task_info_text = QTextEdit()
        self.task_info_text.setReadOnly(True)
        self.task_info_text.setMaximumHeight(120)
        self.task_info_text.setPlainText(tr("batch_processor.select_task_for_details"))
        details_layout.addWidget(self.task_info_text)
        
        layout.addWidget(details_group)
        
        return widget
    
    def create_right_panel(self):
        """创建右侧面板（生成文件列表和控制）"""
        widget = QFrame()
        widget.setFrameStyle(QFrame.Shape.StyledPanel)
        layout = QVBoxLayout(widget)
        layout.setContentsMargins(3, 3, 3, 3)
        layout.setSpacing(3)
        layout.setAlignment(Qt.AlignmentFlag.AlignTop)
        
        # 生成文件列表组
        files_group = QGroupBox(tr("batch_processor.generated_files"))
        files_group.setStyleSheet("QGroupBox { font-size: 12px; margin-top: 5px; }")
        files_layout = QVBoxLayout(files_group)
        files_layout.setContentsMargins(3, 8, 3, 3)
        files_layout.setSpacing(3)
        
        # 文件列表
        self.generated_files_list = QListWidget()
        self.generated_files_list.setMaximumHeight(200)
        self.generated_files_list.itemDoubleClicked.connect(self.on_file_double_clicked)
        files_layout.addWidget(self.generated_files_list)
        
        # 文件操作按钮
        file_buttons_layout = QHBoxLayout()
        
        self.open_file_button = QPushButton(tr("batch_processor.open_file"))
        self.open_file_button.setIcon(QIcon("resources/icons/open.svg"))
        self.open_file_button.clicked.connect(self.open_selected_file)
        self.open_file_button.setEnabled(False)
        file_buttons_layout.addWidget(self.open_file_button)
        
        self.open_folder_button = QPushButton(tr("batch_processor.open_folder"))
        self.open_folder_button.setIcon(QIcon("resources/icons/folder.svg"))
        self.open_folder_button.clicked.connect(self.open_file_folder)
        self.open_folder_button.setEnabled(False)
        file_buttons_layout.addWidget(self.open_folder_button)
        
        self.delete_file_button = QPushButton(tr("batch_processor.delete_file"))
        self.delete_file_button.setIcon(QIcon("resources/icons/delete.svg"))
        self.delete_file_button.clicked.connect(self.delete_selected_file)
        self.delete_file_button.setEnabled(False)
        file_buttons_layout.addWidget(self.delete_file_button)
        
        files_layout.addLayout(file_buttons_layout)
        
        # 连接文件列表选择信号
        self.generated_files_list.itemSelectionChanged.connect(self.on_file_selection_changed)
        
        layout.addWidget(files_group)
        
        # 处理控制组
        control_group = QGroupBox(tr("batch_processor.processing_control"))
        control_group.setStyleSheet("QGroupBox { font-size: 12px; margin-top: 5px; }")
        control_layout = QVBoxLayout(control_group)
        control_layout.setContentsMargins(3, 8, 3, 3)
        control_layout.setSpacing(3)
        
        # 控制按钮
        button_layout = QHBoxLayout()
        
        self.start_button = QPushButton(tr("batch_processor.start_processing"))
        self.start_button.setIcon(QIcon("resources/icons/play.svg"))
        self.start_button.clicked.connect(self.start_processing)
        button_layout.addWidget(self.start_button)
        
        self.pause_button = QPushButton(tr("batch_processor.pause"))
        self.pause_button.setIcon(QIcon("resources/icons/pause.svg"))
        self.pause_button.clicked.connect(self.pause_processing)
        self.pause_button.setEnabled(False)
        button_layout.addWidget(self.pause_button)
        
        self.stop_button = QPushButton(tr("batch_processor.stop"))
        self.stop_button.setIcon(QIcon("resources/icons/stop.svg"))
        self.stop_button.clicked.connect(self.stop_processing)
        self.stop_button.setEnabled(False)
        button_layout.addWidget(self.stop_button)
        
        control_layout.addLayout(button_layout)
        
        # 进度条
        self.overall_progress = QProgressBar()
        self.overall_progress.setVisible(False)
        control_layout.addWidget(self.overall_progress)
        
        # 状态信息
        self.status_label = QLabel(tr("batch_processor.ready"))
        self.status_label.setStyleSheet("color: #666; font-size: 12px;")
        control_layout.addWidget(self.status_label)
        
        # 控制说明
        self.control_description_label = QLabel(tr("batch_processor.control_description"))
        self.control_description_label.setStyleSheet("color: #666; font-size: 12px;")
        control_layout.addWidget(self.control_description_label)
        
        layout.addWidget(control_group)
        
        # 统计信息组
        stats_group = QGroupBox(tr("batch_processor.statistics"))
        stats_group.setStyleSheet("QGroupBox { font-size: 12px; margin-top: 5px; }")
        stats_layout = QVBoxLayout(stats_group)
        stats_layout.setContentsMargins(3, 8, 3, 3)
        stats_layout.setSpacing(3)
        
        self.stats_text = QTextEdit()
        self.stats_text.setReadOnly(True)
        self.stats_text.setMaximumHeight(80)
        self.stats_text.setPlainText(tr("batch_processor.no_statistics"))
        stats_layout.addWidget(self.stats_text)
        
        layout.addWidget(stats_group)
        
        return widget
    
    def create_task_list(self):
        """创建任务列表"""
        widget = QFrame()
        widget.setFrameStyle(QFrame.Shape.StyledPanel)
        layout = QVBoxLayout(widget)
        layout.setContentsMargins(3, 3, 3, 3)  # 减少边距
        layout.setSpacing(3)  # 减少间距
        
        # 任务列表组
        list_group = QGroupBox(tr("batch_processor.task_list"))
        list_group.setStyleSheet("QGroupBox { font-size: 12px; margin-top: 5px; }")  # 紧凑的组框样式
        list_layout = QVBoxLayout(list_group)
        list_layout.setContentsMargins(3, 8, 3, 3)  # 减少组内边距
        list_layout.setSpacing(3)  # 减少组内间距
        
        # 任务表格
        self.task_table = QTableWidget()
        self.task_table.setColumnCount(9)
        self.task_table.setHorizontalHeaderLabels([
            tr("batch_processor.file_name"), 
            tr("batch_processor.voice_engine"), 
            tr("batch_processor.voice"), 
            tr("batch_processor.output_format"), 
            tr("batch_processor.status"), 
            tr("batch_processor.progress"), 
            tr("batch_processor.estimated_time"), 
            tr("batch_processor.start_time"), 
            tr("batch_processor.error_info")
        ])
        self.task_table.horizontalHeader().setStretchLastSection(True)
        self.task_table.setAlternatingRowColors(True)
        self.task_table.itemClicked.connect(self.on_task_clicked)
        self.task_table.itemDoubleClicked.connect(self.on_task_double_clicked)
        
        # 设置表格为只读模式，只允许语音列编辑
        self.task_table.setEditTriggers(self.task_table.EditTrigger.NoEditTriggers)
        
        list_layout.addWidget(self.task_table)
        
        # 任务操作按钮 - 第一行
        task_button_layout1 = QHBoxLayout()
        
        self.batch_add_button = QPushButton(tr("batch_processor.batch_add"))
        self.batch_add_button.clicked.connect(self.batch_add_tasks)
        task_button_layout1.addWidget(self.batch_add_button)
        
        self.add_task_button = QPushButton(tr("batch_processor.add_task"))
        self.add_task_button.clicked.connect(self.add_task)
        task_button_layout1.addWidget(self.add_task_button)
        
        self.remove_task_button = QPushButton(tr("batch_processor.remove_task"))
        self.remove_task_button.clicked.connect(self.remove_task)
        task_button_layout1.addWidget(self.remove_task_button)
        
        self.edit_task_button = QPushButton(tr("batch_processor.edit_task"))
        self.edit_task_button.clicked.connect(self.edit_task)
        task_button_layout1.addWidget(self.edit_task_button)
        
        self.clear_tasks_button = QPushButton(tr("batch_processor.clear_tasks"))
        self.clear_tasks_button.clicked.connect(self.clear_tasks)
        task_button_layout1.addWidget(self.clear_tasks_button)
        
        # 任务列表管理按钮
        self.save_list_button = QPushButton(tr("batch_processor.save_list"))
        self.save_list_button.clicked.connect(self.save_task_list)
        task_button_layout1.addWidget(self.save_list_button)
        
        self.load_list_button = QPushButton(tr("batch_processor.load_list"))
        self.load_list_button.clicked.connect(self.load_task_list)
        task_button_layout1.addWidget(self.load_list_button)
        
        list_layout.addLayout(task_button_layout1)
        
        # 单任务控制按钮 - 第二行
        task_button_layout2 = QHBoxLayout()
        
        # 添加说明标签
        single_task_label = QLabel(tr("batch_processor.selected_task_control"))
        single_task_label.setStyleSheet("color: #666; font-size: 12px; margin-right: 5px;")
        task_button_layout2.addWidget(single_task_label)
        
        self.start_selected_button = QPushButton(tr("batch_processor.start"))
        self.start_selected_button.clicked.connect(self.start_selected_task)
        self.start_selected_button.setEnabled(False)  # 初始禁用
        task_button_layout2.addWidget(self.start_selected_button)
        
        self.pause_selected_button = QPushButton(tr("batch_processor.pause"))
        self.pause_selected_button.clicked.connect(self.pause_selected_task)
        self.pause_selected_button.setEnabled(False)  # 初始禁用
        task_button_layout2.addWidget(self.pause_selected_button)
        
        self.stop_selected_button = QPushButton(tr("batch_processor.stop"))
        self.stop_selected_button.clicked.connect(self.stop_selected_task)
        self.stop_selected_button.setEnabled(False)  # 初始禁用
        task_button_layout2.addWidget(self.stop_selected_button)
        
        # 添加弹性空间
        task_button_layout2.addStretch()
        
        list_layout.addLayout(task_button_layout2)
        
        layout.addWidget(list_group)
        
        return widget
    
    
    def setup_connections(self):
        """设置信号槽连接"""
        # 语言服务信号连接
        language_service = get_language_service()
        language_service.language_changed.connect(self.on_language_changed)
        
        # 批量控制器信号连接（线程安全）
        self.batch_controller.task_completed.connect(self.on_task_completed)
        self.batch_controller.task_error.connect(self.on_task_error)
    
    def on_language_changed(self):
        """语言切换时的处理"""
        try:
            # 重新创建UI以应用新的语言
            self.recreate_ui()
        except Exception as e:
            self.logger.error(f"语言切换失败: {e}")
    
    def recreate_ui(self):
        """重新创建UI以应用新的语言"""
        try:
            # 保存当前状态
            current_tasks = self.batch_controller.get_tasks()
            current_files = []
            for i in range(self.generated_files_list.count()):
                current_files.append(self.generated_files_list.item(i).text())
            
            # 清除当前UI
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
            self.update_task_list()
            for file_path in current_files:
                self.generated_files_list.addItem(file_path)
            
            self.logger.info("批量处理界面语言切换完成")
        except Exception as e:
            self.logger.error(f"重新创建UI失败: {e}")
    
    def add_task(self):
        """添加任务"""
        try:
            from PyQt6.QtWidgets import QDialog, QVBoxLayout, QHBoxLayout, QLabel, QLineEdit, QPushButton, QFileDialog, QFormLayout, QGroupBox, QCheckBox, QSpinBox, QDoubleSpinBox
            
            dialog = QDialog(self)
            dialog.setWindowTitle(tr("batch_processor.add_task_dialog.title"))
            dialog.setModal(True)
            dialog.resize(600, 500)
            
            layout = QVBoxLayout(dialog)
            
            # 文件选择组
            file_group = QGroupBox(tr("batch_processor.add_task_dialog.file_selection"))
            file_layout = QVBoxLayout(file_group)
            
            # 单文件选择
            single_file_layout = QHBoxLayout()
            single_file_layout.addWidget(QLabel(tr("batch_processor.add_task_dialog.file_path")))
            self.file_path_edit = QLineEdit()
            single_file_layout.addWidget(self.file_path_edit)
            
            browse_button = QPushButton(tr("batch_processor.add_task_dialog.browse"))
            browse_button.clicked.connect(self.browse_file)
            single_file_layout.addWidget(browse_button)
            
            file_layout.addLayout(single_file_layout)
            
            layout.addWidget(file_group)
            
            # 输出设置组
            output_group = QGroupBox(tr("batch_processor.add_task_dialog.output_settings"))
            output_layout = QVBoxLayout(output_group)
            
            # 输出目录
            output_dir_layout = QHBoxLayout()
            output_dir_layout.addWidget(QLabel(tr("batch_processor.add_task_dialog.output_directory")))
            self.output_path_edit = QLineEdit()
            output_dir_layout.addWidget(self.output_path_edit)
            
            output_browse_button = QPushButton(tr("batch_processor.add_task_dialog.browse"))
            output_browse_button.clicked.connect(self.browse_output)
            output_dir_layout.addWidget(output_browse_button)
            
            output_layout.addLayout(output_dir_layout)
            
            layout.addWidget(output_group)
            
            # 音频格式组
            audio_format_group = QGroupBox(tr("batch_processor.add_task_dialog.audio_format"))
            audio_format_layout = QFormLayout(audio_format_group)
            
            # 输出格式
            self.output_format_combo = QComboBox()
            self.output_format_combo.addItems(["wav", "mp3", "ogg", "m4a", "flac"])
            self.output_format_combo.setCurrentText("wav")
            self.output_format_combo.currentTextChanged.connect(self.on_format_changed)
            audio_format_layout.addRow(tr("batch_processor.add_task_dialog.output_format"), self.output_format_combo)
            
            # 编码器 (固定为FFmpeg，不可修改)
            self.encoder_label = QLabel("FFmpeg")
            self.encoder_label.setStyleSheet("color: #666666; font-style: italic;")
            audio_format_layout.addRow(tr("batch_processor.add_task_dialog.encoder"), self.encoder_label)
            
            # 采样率
            self.sample_rate_combo = QComboBox()
            self.sample_rate_combo.addItems(["8000", "16000", "22050", "44100", "48000"])
            self.sample_rate_combo.setCurrentText("22050")
            audio_format_layout.addRow(tr("batch_processor.add_task_dialog.sample_rate"), self.sample_rate_combo)
            
            # 位深度
            self.bit_depth_combo = QComboBox()
            self.bit_depth_combo.addItems(["8", "16", "24", "32"])
            self.bit_depth_combo.setCurrentText("16")
            audio_format_layout.addRow(tr("batch_processor.add_task_dialog.bit_depth"), self.bit_depth_combo)
            
            # 声道数
            self.channels_combo = QComboBox()
            self.channels_combo.addItems([tr("batch_processor.add_task_dialog.mono"), tr("batch_processor.add_task_dialog.stereo")])
            self.channels_combo.setCurrentText(tr("batch_processor.add_task_dialog.mono"))
            audio_format_layout.addRow(tr("batch_processor.add_task_dialog.channels"), self.channels_combo)
            
            # 比特率 (仅对压缩格式有效)
            self.bitrate_combo = QComboBox()
            self.bitrate_combo.addItems(["64", "128", "192", "256", "320"])
            self.bitrate_combo.setCurrentText("128")
            self.bitrate_combo.setVisible(False)  # 默认隐藏
            audio_format_layout.addRow(tr("batch_processor.add_task_dialog.bitrate"), self.bitrate_combo)
            
            layout.addWidget(audio_format_group)
            
            # 语音设置组
            voice_group = QGroupBox(tr("batch_processor.add_task_dialog.voice_settings"))
            voice_layout = QFormLayout(voice_group)
            
            # 语音引擎
            self.voice_engine_combo = QComboBox()
            voice_layout.addRow(tr("batch_processor.add_task_dialog.voice_engine"), self.voice_engine_combo)
            
            # 加载可用引擎
            self.load_available_engines()
            
            # 语音选择
            self.voice_combo = QComboBox()
            voice_layout.addRow(tr("batch_processor.add_task_dialog.voice"), self.voice_combo)
            
            # 连接引擎改变信号，传递voice_combo参数
            self.voice_engine_combo.currentTextChanged.connect(lambda: self.on_engine_changed(self.voice_combo, self.voice_engine_combo))
            
            # 语音参数
            self.rate_spinbox = QDoubleSpinBox()
            self.rate_spinbox.setRange(0.1, 3.0)
            self.rate_spinbox.setSingleStep(0.1)
            self.rate_spinbox.setValue(1.0)
            voice_layout.addRow(tr("batch_processor.add_task_dialog.rate"), self.rate_spinbox)
            
            self.pitch_spinbox = QSpinBox()
            self.pitch_spinbox.setRange(-50, 50)
            self.pitch_spinbox.setValue(0)
            voice_layout.addRow(tr("batch_processor.add_task_dialog.pitch"), self.pitch_spinbox)
            
            self.volume_spinbox = QDoubleSpinBox()
            self.volume_spinbox.setRange(0.0, 1.0)
            self.volume_spinbox.setSingleStep(0.1)
            self.volume_spinbox.setValue(0.8)
            voice_layout.addRow(tr("batch_processor.add_task_dialog.volume"), self.volume_spinbox)
            
            layout.addWidget(voice_group)
            
            # 任务设置组
            task_group = QGroupBox(tr("batch_processor.add_task_dialog.task_settings"))
            task_layout = QVBoxLayout(task_group)
            
            # 任务名称
            name_layout = QHBoxLayout()
            name_layout.addWidget(QLabel(tr("batch_processor.add_task_dialog.task_name")))
            self.task_name_edit = QLineEdit()
            self.task_name_edit.setPlaceholderText(tr("batch_processor.add_task_dialog.task_name_placeholder"))
            name_layout.addWidget(self.task_name_edit)
            task_layout.addLayout(name_layout)
            
            # 优先级
            priority_layout = QHBoxLayout()
            priority_layout.addWidget(QLabel(tr("batch_processor.add_task_dialog.priority")))
            self.priority_combo = QComboBox()
            self.priority_combo.addItems([tr("batch_processor.add_task_dialog.high"), tr("batch_processor.add_task_dialog.medium"), tr("batch_processor.add_task_dialog.low")])
            self.priority_combo.setCurrentText(tr("batch_processor.add_task_dialog.medium"))
            priority_layout.addWidget(self.priority_combo)
            priority_layout.addStretch()
            task_layout.addLayout(priority_layout)
            
            layout.addWidget(task_group)
            
            # 按钮
            button_layout = QHBoxLayout()
            
            ok_button = QPushButton(tr("batch_processor.add_task_dialog.ok"))
            ok_button.clicked.connect(dialog.accept)
            button_layout.addWidget(ok_button)
            
            cancel_button = QPushButton(tr("batch_processor.add_task_dialog.cancel"))
            cancel_button.clicked.connect(dialog.reject)
            button_layout.addWidget(cancel_button)
            
            layout.addLayout(button_layout)
            
            # 初始化语音引擎
            self.on_engine_changed(self.voice_combo, self.voice_engine_combo)
            
            if dialog.exec() == QDialog.DialogCode.Accepted:
                # 检查是否正在批量处理
                if self.batch_controller.is_running:
                    QMessageBox.information(self, tr("common.info"), tr("batch_processor.messages.processing_in_progress"))
                self.process_add_task()
                
        except Exception as e:
            self.logger.error(f"添加任务失败: {e}")
            QMessageBox.critical(self, tr("common.error"), tr("batch_processor.messages.add_task_failed").format(error=e))
    
    def browse_file(self):
        """浏览文件"""
        try:
            from PyQt6.QtWidgets import QFileDialog
            
            file_dialog = QFileDialog(self)
            file_dialog.setFileMode(QFileDialog.FileMode.ExistingFile)
            file_dialog.setNameFilter(
                tr("batch_processor.file_dialog.supported_files")
            )
            
            if file_dialog.exec():
                file_paths = file_dialog.selectedFiles()
                if file_paths:
                    file_path = file_paths[0]
                    self.file_path_edit.setText(file_path)
                    
                    # 自动设置输出目录为文件相同目录
                    import os
                    file_dir = os.path.normpath(os.path.dirname(file_path))
                    self.output_path_edit.setText(file_dir)
                    
                    self.logger.info(f"文件选择: {file_path}")
                    self.logger.info(f"自动设置输出目录: {file_dir}")
                    
        except Exception as e:
            self.logger.error(f"浏览文件失败: {e}")
    
    def browse_output(self):
        """浏览输出目录"""
        try:
            from PyQt6.QtWidgets import QFileDialog
            import os
            
            output_dir = QFileDialog.getExistingDirectory(self, tr("batch_processor.file_dialog.select_output_directory"))
            if output_dir:
                # 规范化路径，确保使用正确的路径分隔符
                normalized_dir = os.path.normpath(output_dir)
                self.output_path_edit.setText(normalized_dir)
                
        except Exception as e:
            self.logger.error(f"浏览输出目录失败: {e}")
    
    def load_available_engines(self):
        """加载可用的TTS引擎"""
        try:
            # 清空现有选项
            self.voice_engine_combo.clear()
            
            # 定义引擎显示顺序：piper_tts 第一，其他按原顺序
            preferred_order = ['piper_tts', 'pyttsx3']
            
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
                        self.voice_engine_combo.addItem(f"{engine} ✓")
                    else:
                        # 不可用引擎，添加不可用标记
                        self.voice_engine_combo.addItem(f"{engine} ✗")
            
            # 添加其他未在优先列表中的引擎
            for engine in all_engines:
                if engine not in preferred_order:
                    if engine in available_engines:
                        # 可用引擎，添加可用标记
                        self.voice_engine_combo.addItem(f"{engine} ✓")
                    else:
                        # 不可用引擎，添加不可用标记
                        self.voice_engine_combo.addItem(f"{engine} ✗")
            
            # 设置默认选择为第一个可用引擎
            if available_engines:
                # 暂时断开信号连接，避免触发on_engine_changed
                try:
                    self.voice_engine_combo.currentTextChanged.disconnect()
                except TypeError:
                    # 如果没有连接，disconnect会抛出TypeError，这是正常的
                    pass
                
                # 优先选择 piper_tts，如果不可用则选择第一个可用的
                if 'piper_tts' in available_engines:
                    self.voice_engine_combo.setCurrentText("piper_tts ✓")
                else:
                    self.voice_engine_combo.setCurrentText(f"{available_engines[0]} ✓")
                
                # 注意：这里不连接信号，因为BatchProcessorWidget没有voice_combo
                # 信号连接在add_task对话框中进行
            
            self.logger.info(f"加载了 {len(all_engines)} 个TTS引擎，其中 {len(available_engines)} 个可用")
            
        except Exception as e:
            self.logger.error(f"加载可用引擎失败: {e}")
            # 如果失败，使用硬编码的引擎列表作为备用
            self.voice_engine_combo.addItems(["piper_tts", "pyttsx3"])
    
    def on_engine_changed(self, voice_combo=None, engine_combo=None):
        """语音引擎改变事件"""
        try:
            # 检查是否有voice_combo参数（用于对话框调用）
            if voice_combo is None:
                # 如果没有提供voice_combo，说明是在BatchProcessorWidget中调用
                # 这种情况下不应该执行，因为BatchProcessorWidget没有voice_combo
                self.logger.warning("on_engine_changed被错误调用：BatchProcessorWidget没有voice_combo")
                return
            
            # 确定使用哪个引擎ComboBox
            if engine_combo is not None:
                # 使用传入的引擎ComboBox（批量添加对话框）
                engine_text = engine_combo.currentText()
            elif hasattr(self, 'voice_engine_combo') and self.voice_engine_combo is not None:
                # 使用默认的引擎ComboBox（添加任务对话框）
                engine_text = self.voice_engine_combo.currentText()
            else:
                self.logger.warning("无法确定引擎ComboBox")
                return
            
            engine = engine_text.replace(" ✓", "").replace(" ✗", "")
            
            voice_combo.clear()
            
            # 动态加载该引擎支持的语音
            from services.tts_service import TTSServiceFactory
            
            try:
                # 创建TTS服务实例
                tts_service = TTSServiceFactory.create_service(engine)
                if tts_service:
                    voices = tts_service.get_available_voices()
                    
                    # 添加语音到下拉框，使用与语音设置页面相同的格式
                    for voice in voices:
                        voice_id = voice.get('id', '')
                        voice_name = voice.get('name', '')
                        voice_language = voice.get('language', 'unknown')
                        
                        if voice_id and voice_id != voice_name:
                            display_text = f"{voice_id} - {voice_name} ({voice_language})"
                        else:
                            display_text = f"{voice_name} ({voice_language})"
                        
                        voice_combo.addItem(display_text, voice)
                    
                    # 自动选择默认语音
                    self._select_default_voice(engine, voices, voice_combo)
                    
                    self.logger.info(f"为引擎 {engine} 加载了 {len(voices)} 个语音")
                else:
                    self.logger.warning(f"无法创建引擎服务: {engine}")
                    # 添加默认语音作为后备
                    self._add_default_voices(engine, voice_combo)
                    # 选择第一个语音作为默认
                    if voice_combo.count() > 0:
                        voice_combo.setCurrentIndex(0)
                    
            except Exception as e:
                self.logger.error(f"加载引擎 {engine} 语音失败: {e}")
                # 如果加载失败，使用默认语音
                self._add_default_voices(engine, voice_combo)
                # 选择第一个语音作为默认
                if voice_combo.count() > 0:
                    voice_combo.setCurrentIndex(0)
                
        except Exception as e:
            self.logger.error(f"语音引擎切换失败: {e}")
    
    def _select_default_voice(self, engine: str, voices: list, voice_combo=None):
        """自动选择默认语音"""
        try:
            if voice_combo is None:
                self.logger.warning("_select_default_voice被错误调用：没有提供voice_combo参数")
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
            if voice_combo.count() > selected_index:
                voice_combo.setCurrentIndex(selected_index)
                selected_voice = voices[selected_index] if voices else {}
                self.logger.info(f"已选择语音: {selected_voice.get('name', 'Unknown')} ({selected_voice.get('language', 'unknown')})")
            
        except Exception as e:
            self.logger.error(f"选择默认语音失败: {e}")
            # 如果选择失败，选择第一个
            if voice_combo and voice_combo.count() > 0:
                voice_combo.setCurrentIndex(0)
    
    def _add_default_voices(self, engine: str, voice_combo=None):
        """添加默认语音（当动态加载失败时使用）"""
        if voice_combo is None:
            self.logger.warning("_add_default_voices被错误调用：没有提供voice_combo参数")
            return
            
        if engine == "piper_tts":
            voice_combo.addItem("zh_CN-huayan-medium (zh-CN)", "zh_CN-huayan-medium")
        elif engine == "pyttsx3":
            voice_combo.addItem("zh_CN-huayan-medium (zh-CN)", "zh_CN-huayan-medium")
    
    def on_format_changed(self):
        """输出格式改变事件"""
        try:
            format_type = self.output_format_combo.currentText()
            
            # 根据格式类型设置比特率显示
            if format_type in ["mp3", "ogg", "m4a"]:
                self.bitrate_combo.setVisible(True)
            else:
                self.bitrate_combo.setVisible(False)
            
            # 根据格式设置默认采样率
            if format_type in ["mp3", "ogg", "m4a"]:
                # 压缩格式推荐较低采样率
                if "44100" not in [self.sample_rate_combo.itemText(i) for i in range(self.sample_rate_combo.count())]:
                    self.sample_rate_combo.addItem("44100")
                self.sample_rate_combo.setCurrentText("44100")
            else:
                # 无损格式推荐较高采样率
                if "48000" not in [self.sample_rate_combo.itemText(i) for i in range(self.sample_rate_combo.count())]:
                    self.sample_rate_combo.addItem("48000")
                self.sample_rate_combo.setCurrentText("48000")
                
        except Exception as e:
            self.logger.error(f"格式切换失败: {e}")
    
    def process_add_task(self):
        """处理添加任务"""
        try:
            # 获取单个文件
            file_path = self.file_path_edit.text().strip()
            if not file_path:
                QMessageBox.warning(self, tr("common.warning"), tr("batch_processor.messages.please_select_file"))
                return
            
            output_dir = self.output_path_edit.text().strip()
            if not output_dir:
                QMessageBox.warning(self, tr("common.warning"), tr("batch_processor.messages.please_select_output_dir"))
                return
            
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
            engine_text = self.voice_engine_combo.currentText()
            engine = engine_text.replace(" ✓", "").replace(" ✗", "")
            
            # 创建语音配置
            voice_config = VoiceConfig(
                engine=engine,
                voice_name=voice_id,  # 使用语音ID
                rate=self.rate_spinbox.value(),
                pitch=self.pitch_spinbox.value(),
                volume=self.volume_spinbox.value(),
                language=voice_language,
                output_format=self.output_format_combo.currentText()
            )
            
            # 添加音频格式参数到extra_params
            voice_config.extra_params = {
                'encoder': 'FFmpeg',  # 固定使用FFmpeg编码器
                'sample_rate': int(self.sample_rate_combo.currentText()),
                'bit_depth': int(self.bit_depth_combo.currentText()),
                'channels': 1 if "单声道" in self.channels_combo.currentText() else 2,
                'bitrate': int(self.bitrate_combo.currentText()) if self.bitrate_combo.isVisible() else None
            }
            
            # 生成输出文件名
            import os
            file_name = os.path.basename(file_path)
            name, ext = os.path.splitext(file_name)
            output_file = f"{name}.{self.output_format_combo.currentText()}"
            # 规范化输出路径，确保使用正确的路径分隔符
            output_path = os.path.normpath(os.path.join(output_dir, output_file))
            
            # 添加任务
            task_id = self.batch_controller.add_task(file_path, voice_config, output_path)
            
            # 手动更新任务列表
            self.manual_update()
            
            QMessageBox.information(self, tr("common.success"), tr("batch_processor.messages.task_added_success").format(task_id=task_id))
            
        except Exception as e:
            self.logger.error(f"处理添加任务失败: {e}")
            QMessageBox.critical(self, "错误", f"处理添加任务失败: {e}")
    
    def remove_task(self):
        """移除任务"""
        try:
            current_row = self.task_table.currentRow()
            if current_row < 0:
                QMessageBox.information(self, "提示", "请先选择要移除的任务")
                return
            
            # 获取任务ID
            task_id = self.task_table.item(current_row, 0).data(Qt.ItemDataRole.UserRole)
            if not task_id:
                return
            
            # 确认删除
            reply = QMessageBox.question(
                self, "确认", "确定要移除这个任务吗？",
                QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No
            )
            
            if reply == QMessageBox.StandardButton.Yes:
                self.batch_controller.remove_task(task_id)
                self.manual_update()
                
        except Exception as e:
            self.logger.error(f"移除任务失败: {e}")
            QMessageBox.critical(self, "错误", f"移除任务失败: {e}")
    
    def clear_tasks(self):
        """清空任务"""
        try:
            if self.batch_controller.get_all_tasks():
                reply = QMessageBox.question(
                    self, "确认", "确定要清空所有任务吗？",
                    QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No
                )
                
                if reply == QMessageBox.StandardButton.Yes:
                    self.batch_controller.clear_all_tasks()
                    # 清理语音ComboBox缓存
                    self._clear_voice_combo_cache()
                    self.manual_update()
            else:
                QMessageBox.information(self, "提示", "没有任务需要清空")
                
        except Exception as e:
            self.logger.error(f"清空任务失败: {e}")
            QMessageBox.critical(self, "错误", f"清空任务失败: {e}")
    
    def _clear_voice_combo_cache(self):
        """清理语音ComboBox缓存"""
        try:
            self._voice_combo_cache.clear()
            self._cached_voices.clear()
            self._last_voice_update = 0
            # 重置日志标志
            if hasattr(self, '_combo_creation_logged'):
                delattr(self, '_combo_creation_logged')
            self.logger.debug("语音ComboBox缓存已清理")
        except Exception as e:
            self.logger.error(f"清理语音ComboBox缓存失败: {e}")
    
    def start_processing(self):
        """开始处理"""
        try:
            result = self.batch_controller.start_processing()
            
            # 检查是否因为状态验证失败而无法开始
            if result is False:
                QMessageBox.warning(self, "警告", "无法开始批量处理：存在正在处理或暂停的任务。请等待所有任务完成后再开始。")
                return
            
            self.start_button.setEnabled(False)
            self.pause_button.setEnabled(True)
            self.stop_button.setEnabled(True)
            
            self.status_label.setText(tr("batch_processor.processing"))
            self.overall_progress.setVisible(True)
            
            # 启动定时器更新
            self.update_timer.start(1000)
            
        except Exception as e:
            self.logger.error(f"开始处理失败: {e}")
            QMessageBox.critical(self, "错误", f"开始处理失败: {e}")
    
    def pause_processing(self):
        """暂停处理"""
        try:
            self.batch_controller.pause_processing()
            
            self.pause_button.setEnabled(False)
            self.start_button.setEnabled(True)
            
            self.status_label.setText(tr("batch_processor.paused"))
            
        except Exception as e:
            self.logger.error(f"暂停处理失败: {e}")
    
    def stop_processing(self):
        """停止处理"""
        try:
            self.batch_controller.stop_processing()
            
            self.start_button.setEnabled(True)
            self.pause_button.setEnabled(False)
            self.stop_button.setEnabled(False)
            
            self.status_label.setText(tr("batch_processor.stopped"))
            self.overall_progress.setVisible(False)
            
        except Exception as e:
            self.logger.error(f"停止处理失败: {e}")
    
    def update_task_list(self):
        """更新任务列表"""
        try:
            tasks = self.batch_controller.get_all_tasks()
            
            self.task_table.setRowCount(len(tasks))
            
            for row, task in enumerate(tasks):
                # 文件名
                file_name = task.file_path.split('/')[-1] if '/' in task.file_path else task.file_path.split('\\')[-1]
                file_item = QTableWidgetItem(file_name)
                file_item.setFlags(file_item.flags() & ~Qt.ItemFlag.ItemIsEditable)  # 设置为只读
                self.task_table.setItem(row, 0, file_item)
                self.task_table.item(row, 0).setData(Qt.ItemDataRole.UserRole, task.id)
                
                # 语音引擎
                engine_item = QTableWidgetItem(task.voice_config.engine)
                engine_item.setFlags(engine_item.flags() & ~Qt.ItemFlag.ItemIsEditable)  # 设置为只读
                self.task_table.setItem(row, 1, engine_item)
                
                # 语音 - 使用缓存的ComboBox
                voice_combo = self._get_or_create_voice_combo(task, row)
                self.task_table.setCellWidget(row, 2, voice_combo)
                
                # 输出格式
                output_format_item = QTableWidgetItem(task.voice_config.output_format.upper())
                output_format_item.setFlags(output_format_item.flags() & ~Qt.ItemFlag.ItemIsEditable)  # 设置为只读
                self.task_table.setItem(row, 3, output_format_item)
                
                # 状态
                status_item = QTableWidgetItem(task.status.value)
                status_item.setFlags(status_item.flags() & ~Qt.ItemFlag.ItemIsEditable)  # 设置为只读
                if task.status == TaskStatus.COMPLETED:
                    status_item.setBackground(Qt.GlobalColor.green)
                elif task.status == TaskStatus.FAILED:
                    status_item.setBackground(Qt.GlobalColor.red)
                elif task.status == TaskStatus.PROCESSING:
                    status_item.setBackground(Qt.GlobalColor.yellow)
                self.task_table.setItem(row, 4, status_item)
                
                # 进度
                progress_item = QTableWidgetItem(f"{task.progress}%")
                progress_item.setFlags(progress_item.flags() & ~Qt.ItemFlag.ItemIsEditable)  # 设置为只读
                self.task_table.setItem(row, 5, progress_item)
                
                # 预计剩余时间
                remaining_time = self._format_remaining_time(task)
                remaining_item = QTableWidgetItem(remaining_time)
                remaining_item.setFlags(remaining_item.flags() & ~Qt.ItemFlag.ItemIsEditable)  # 设置为只读
                self.task_table.setItem(row, 6, remaining_item)
                
                # 开始时间
                if task.start_time:
                    if isinstance(task.start_time, float):
                        from datetime import datetime
                        start_time = datetime.fromtimestamp(task.start_time).strftime("%H:%M:%S")
                    else:
                        start_time = task.start_time.strftime("%H:%M:%S")
                else:
                    start_time = "-"
                start_time_item = QTableWidgetItem(start_time)
                start_time_item.setFlags(start_time_item.flags() & ~Qt.ItemFlag.ItemIsEditable)  # 设置为只读
                self.task_table.setItem(row, 7, start_time_item)
                
                # 错误信息
                error_info = task.error_message if task.error_message else "-"
                error_item = QTableWidgetItem(error_info)
                error_item.setFlags(error_item.flags() & ~Qt.ItemFlag.ItemIsEditable)  # 设置为只读
                self.task_table.setItem(row, 8, error_item)
            
        except Exception as e:
            self.logger.error(f"更新任务列表失败: {e}")
    
    def _format_remaining_time(self, task):
        """格式化预计剩余时间"""
        try:
            if hasattr(task, 'estimated_remaining_time') and task.estimated_remaining_time is not None:
                remaining_seconds = int(task.estimated_remaining_time)
                if remaining_seconds == 0:
                    return "0秒"
                elif remaining_seconds < 60:
                    return f"{remaining_seconds}秒"
                elif remaining_seconds < 3600:
                    minutes = remaining_seconds // 60
                    seconds = remaining_seconds % 60
                    return f"{minutes}分{seconds}秒"
                else:
                    hours = remaining_seconds // 3600
                    minutes = (remaining_seconds % 3600) // 60
                    return f"{hours}时{minutes}分"
            else:
                return "-"
        except Exception:
            return "-"
    
    def edit_task(self):
        """编辑任务"""
        try:
            current_row = self.task_table.currentRow()
            if current_row < 0:
                QMessageBox.information(self, "提示", "请先选择要编辑的任务")
                return
            
            # 获取任务ID
            task_id = self.task_table.item(current_row, 0).data(Qt.ItemDataRole.UserRole)
            if not task_id:
                QMessageBox.warning(self, "警告", "无法获取任务ID")
                return
            
            # 获取任务
            task = self.batch_controller.get_task_by_id(task_id)
            if not task:
                QMessageBox.warning(self, "警告", "任务不存在")
                return
            
            # 检查任务状态
            if task.status == TaskStatus.PROCESSING:
                QMessageBox.warning(self, "警告", "正在处理的任务无法编辑")
                return
            
            # 打开编辑对话框
            from ui.task_edit_dialog import TaskEditDialog
            dialog = TaskEditDialog(task, self)
            if dialog.exec() == dialog.DialogCode.Accepted:
                # 更新任务
                updated_task = dialog.get_updated_task()
                self.batch_controller.update_task(task_id, updated_task)
                self.manual_update()
                QMessageBox.information(self, "成功", "任务编辑成功")
                
        except Exception as e:
            self.logger.error(f"编辑任务失败: {e}")
            QMessageBox.critical(self, "错误", f"编辑任务失败: {e}")
    
    def update_status(self):
        """更新状态"""
        try:
            # 检查是否有任务在处理中
            processing_tasks = self.batch_controller.get_processing_tasks()
            pending_tasks = self.batch_controller.get_pending_tasks()
            
            # 更新任务列表（无论是否有处理中的任务都要更新）
            self.update_task_list()
            
            # 更新总体进度
            progress_info = self.batch_controller.get_overall_progress()
            if progress_info['total'] > 0:
                self.overall_progress.setValue(progress_info['progress_percentage'])
                self.overall_progress.setVisible(True)
            else:
                self.overall_progress.setVisible(False)
            
            # 更新统计信息
            self.update_statistics()
            
            # 更新选中任务的按钮状态
            current_row = self.task_table.currentRow()
            if current_row >= 0:
                task_id = self.task_table.item(current_row, 0).data(Qt.ItemDataRole.UserRole)
                if task_id:
                    task = self.batch_controller.get_task_by_id(task_id)
                    if task:
                        self.update_selected_task_buttons(task)
            
            # 更新所有任务的语音ComboBox状态
            self._update_voice_combos_status()
            
            # 如果没有处理中或待处理的任务，停止定时器
            if not processing_tasks and not pending_tasks:
                self.update_timer.stop()
                self.logger.debug("没有任务处理中，停止定时器更新")
                # 更新状态标签为完成状态
                self._update_status_label()
            
        except Exception as e:
            self.logger.error(f"更新状态失败: {e}")
    
    def _update_status_label(self):
        """更新状态标签"""
        try:
            # 检查任务状态
            processing_tasks = self.batch_controller.get_processing_tasks()
            pending_tasks = self.batch_controller.get_pending_tasks()
            completed_tasks = self.batch_controller.get_completed_tasks()
            failed_tasks = self.batch_controller.get_failed_tasks()
            
            if processing_tasks:
                self.status_label.setText(tr("batch_processor.processing"))
            elif pending_tasks:
                self.status_label.setText(tr("batch_processor.waiting"))
            elif completed_tasks and not failed_tasks:
                self.status_label.setText(tr("batch_processor.completed"))
            elif failed_tasks:
                self.status_label.setText(tr("batch_processor.partial_failure"))
            else:
                self.status_label.setText(tr("batch_processor.ready"))
                
        except Exception as e:
            self.logger.error(f"更新状态标签失败: {e}")
    
    def manual_update(self):
        """手动更新状态（用于添加任务后等场景）"""
        try:
            # 更新任务列表
            self.update_task_list()
            
            # 更新总体进度
            progress_info = self.batch_controller.get_overall_progress()
            if progress_info['total'] > 0:
                self.overall_progress.setValue(progress_info['progress_percentage'])
                self.overall_progress.setVisible(True)
            else:
                self.overall_progress.setVisible(False)
            
            # 更新统计信息
            self.update_statistics()
            
            # 更新选中任务的按钮状态
            current_row = self.task_table.currentRow()
            if current_row >= 0:
                task_id = self.task_table.item(current_row, 0).data(Qt.ItemDataRole.UserRole)
                if task_id:
                    task = self.batch_controller.get_task_by_id(task_id)
                    if task:
                        self.update_selected_task_buttons(task)
            
            # 更新所有任务的语音ComboBox状态
            self._update_voice_combos_status()
            
        except Exception as e:
            self.logger.error(f"手动更新失败: {e}")
    
    def update_statistics(self):
        """更新统计信息"""
        try:
            stats = self.batch_controller.get_processing_statistics()
            
            stats_text = f"总任务数: {stats['total_tasks']}\n"
            stats_text += f"已完成: {stats['completed_tasks']}\n"
            stats_text += f"失败: {stats['failed_tasks']}\n"
            stats_text += f"处理中: {stats['processing_tasks']}\n"
            stats_text += f"等待中: {stats['pending_tasks']}\n"
            stats_text += f"成功率: {stats['success_rate']:.1f}%\n"
            stats_text += f"平均处理时间: {stats['average_processing_time']:.1f}秒"
            
            self.stats_text.setPlainText(stats_text)
            
        except Exception as e:
            self.logger.error(f"更新统计信息失败: {e}")
    
    def on_task_clicked(self, item):
        """任务点击事件"""
        try:
            if not item:
                return
            
            row = item.row()
            task_id = self.task_table.item(row, 0).data(Qt.ItemDataRole.UserRole)
            
            if not task_id:
                return
            
            # 获取任务详情
            tasks = self.batch_controller.get_all_tasks()
            task = next((t for t in tasks if t.id == task_id), None)
            
            if task:
                self.show_task_details(task)
                # 更新单任务控制按钮状态
                self.update_selected_task_buttons(task)
                
        except Exception as e:
            self.logger.error(f"处理任务点击事件失败: {e}")
    
    def on_task_double_clicked(self, item):
        """任务双击事件 - 启动单个任务"""
        try:
            if not item:
                return
            
            row = item.row()
            task_id = self.task_table.item(row, 0).data(Qt.ItemDataRole.UserRole)
            
            if not task_id:
                return
            
            # 获取任务详情
            tasks = self.batch_controller.get_all_tasks()
            task = next((t for t in tasks if t.id == task_id), None)
            
            if not task:
                return
            
            # 检查任务状态
            if task.status == TaskStatus.PROCESSING:
                QMessageBox.information(self, "提示", f"任务 '{task.id}' 正在处理中")
                return
            elif task.status == TaskStatus.COMPLETED:
                QMessageBox.information(self, "提示", f"任务 '{task.id}' 已完成")
                return
            elif task.status == TaskStatus.FAILED:
                # 失败的任务可以重新启动
                reply = QMessageBox.question(
                    self, 
                    "重新启动任务", 
                    f"任务 '{task.id}' 之前失败了，是否重新启动？",
                    QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No,
                    QMessageBox.StandardButton.Yes
                )
                if reply != QMessageBox.StandardButton.Yes:
                    return
            
            # 启动单个任务
            self.start_single_task(task)
            
        except Exception as e:
            self.logger.error(f"处理任务双击事件失败: {e}")
            QMessageBox.critical(self, "错误", f"启动任务失败: {e}")
    
    def start_single_task(self, task):
        """启动单个任务"""
        try:
            # 检查批量控制器是否正在处理
            if self.batch_controller.is_running:
                QMessageBox.warning(self, "警告", "批量处理正在进行中，无法启动单个任务")
                return
            
            # 检查任务是否准备就绪
            if not self.batch_controller._validate_single_task_ready(task.id):
                QMessageBox.warning(self, "警告", f"任务 '{task.id}' 未准备就绪，请检查配置")
                return
            
            # 启动单个任务处理
            self.logger.info(f"双击启动单个任务: {task.id}")
            
            # 使用批量控制器的worker来执行单个任务
            import threading
            worker_thread = threading.Thread(
                target=self.batch_controller._process_task, 
                args=(task,), 
                daemon=True
            )
            worker_thread.start()
            
            # 显示启动消息
            QMessageBox.information(self, "任务启动", f"任务 '{task.id}' 已开始处理")
            
        except Exception as e:
            self.logger.error(f"启动单个任务失败: {e}")
            QMessageBox.critical(self, "错误", f"启动任务失败: {e}")
    
    def show_task_details(self, task: BatchTask):
        """显示任务详情"""
        try:
            details_text = f"任务ID: {task.id}\n"
            details_text += f"文件路径: {task.file_path}\n"
            details_text += f"输出路径: {task.output_path}\n"
            details_text += f"状态: {task.status.value}\n"
            details_text += f"进度: {task.progress}%\n\n"
            
            details_text += "=== 语音设置 ===\n"
            details_text += f"语音引擎: {task.voice_config.engine}\n"
            details_text += f"语音名称: {task.voice_config.voice_name}\n"
            details_text += f"语速: {task.voice_config.rate}\n"
            details_text += f"音调: {task.voice_config.pitch}\n"
            details_text += f"音量: {task.voice_config.volume}\n"
            details_text += f"语言: {task.voice_config.language}\n\n"
            
            details_text += "=== 音频格式 ===\n"
            details_text += f"输出格式: {task.voice_config.output_format}\n"
            
            # 显示音频格式参数
            if hasattr(task.voice_config, 'extra_params') and task.voice_config.extra_params:
                extra_params = task.voice_config.extra_params
                details_text += f"编码器: {extra_params.get('encoder', '未知')}\n"
                details_text += f"采样率: {extra_params.get('sample_rate', '未知')} Hz\n"
                details_text += f"位深度: {extra_params.get('bit_depth', '未知')} bit\n"
                details_text += f"声道数: {extra_params.get('channels', '未知')}\n"
                if extra_params.get('bitrate'):
                    details_text += f"比特率: {extra_params.get('bitrate')} kbps\n"
            
            details_text += "\n=== 时间信息 ===\n"
            if task.start_time:
                if isinstance(task.start_time, float):
                    from datetime import datetime
                    start_time_str = datetime.fromtimestamp(task.start_time).strftime('%Y-%m-%d %H:%M:%S')
                else:
                    start_time_str = task.start_time.strftime('%Y-%m-%d %H:%M:%S')
                details_text += f"开始时间: {start_time_str}\n"
            
            if task.end_time:
                if isinstance(task.end_time, float):
                    from datetime import datetime
                    end_time_str = datetime.fromtimestamp(task.end_time).strftime('%Y-%m-%d %H:%M:%S')
                else:
                    end_time_str = task.end_time.strftime('%Y-%m-%d %H:%M:%S')
                details_text += f"结束时间: {end_time_str}\n"
            
            if task.error_message:
                details_text += f"\n=== 错误信息 ===\n{task.error_message}\n"
            
            self.task_info_text.setPlainText(details_text)
            
        except Exception as e:
            self.logger.error(f"显示任务详情失败: {e}")
    
    def on_task_completed(self, task: BatchTask):
        """任务完成事件"""
        try:
            self.task_completed.emit(task.id)
            self.logger.info(f"任务完成: {task.id}")
            
            # 如果任务有输出文件，添加到生成文件列表
            if task.output_path and os.path.exists(task.output_path):
                self.add_generated_file(task.output_path)
            
            # 使用QTimer.singleShot确保UI更新在主线程中进行
            from PyQt6.QtCore import QTimer
            QTimer.singleShot(0, self.manual_update)
            
        except Exception as e:
            self.logger.error(f"处理任务完成事件失败: {e}")
    
    def on_task_error(self, task: BatchTask):
        """任务错误事件"""
        try:
            self.logger.error(f"任务失败: {task.id}, 错误: {task.error_message}")
            
            # 使用QTimer.singleShot确保UI更新在主线程中进行
            from PyQt6.QtCore import QTimer
            QTimer.singleShot(0, self.manual_update)
            
        except Exception as e:
            self.logger.error(f"处理任务错误事件失败: {e}")
    
    def save_task_list(self):
        """保存任务列表"""
        try:
            from PyQt6.QtWidgets import QFileDialog, QInputDialog
            import json
            import os
            from datetime import datetime
            
            # 获取当前任务列表
            tasks = self.batch_controller.get_all_tasks()
            if not tasks:
                QMessageBox.information(self, "提示", "当前没有任务需要保存")
                return
            
            # 获取保存文件名
            default_name = f"task_list_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json"
            file_path, _ = QFileDialog.getSaveFileName(
                self, "保存任务列表", default_name,
                "JSON文件 (*.json);;所有文件 (*.*)"
            )
            
            if not file_path:
                return
            
            # 准备任务数据
            task_list_data = {
                "metadata": {
                    "version": "1.0.0",
                    "created_at": datetime.now().isoformat(),
                    "total_tasks": len(tasks),
                    "description": "批量处理任务列表"
                },
                "tasks": []
            }
            
            # 转换任务数据
            for task in tasks:
                task_data = {
                    "id": task.id,
                    "file_path": task.file_path,
                    "output_path": task.output_path,
                    "status": task.status.value,
                    "progress": task.progress,
                    "error_message": task.error_message,
                    "start_time": task.start_time.isoformat() if task.start_time else None,
                    "end_time": task.end_time.isoformat() if task.end_time else None,
                    "voice_config": {
                        "engine": task.voice_config.engine,
                        "voice_name": task.voice_config.voice_name,
                        "rate": task.voice_config.rate,
                        "pitch": task.voice_config.pitch,
                        "volume": task.voice_config.volume,
                        "language": task.voice_config.language,
                        "output_format": task.voice_config.output_format,
                        "extra_params": getattr(task.voice_config, 'extra_params', {})
                    }
                }
                task_list_data["tasks"].append(task_data)
            
            # 保存到文件
            with open(file_path, 'w', encoding='utf-8') as f:
                json.dump(task_list_data, f, ensure_ascii=False, indent=2)
            
            QMessageBox.information(self, "成功", f"任务列表已保存到: {os.path.basename(file_path)}")
            
        except Exception as e:
            self.logger.error(f"保存任务列表失败: {e}")
            QMessageBox.critical(self, "错误", f"保存任务列表失败: {e}")
    
    def load_task_list(self):
        """加载任务列表"""
        try:
            from PyQt6.QtWidgets import QFileDialog, QMessageBox
            import json
            from datetime import datetime
            
            # 选择任务列表文件
            file_path, _ = QFileDialog.getOpenFileName(
                self, "加载任务列表", "",
                "JSON文件 (*.json);;所有文件 (*.*)"
            )
            
            if not file_path:
                return
            
            # 读取任务列表数据
            with open(file_path, 'r', encoding='utf-8') as f:
                task_list_data = json.load(f)
            
            # 验证文件格式
            if "tasks" not in task_list_data:
                QMessageBox.warning(self, "警告", "无效的任务列表文件格式")
                return
            
            tasks_data = task_list_data["tasks"]
            if not tasks_data:
                QMessageBox.information(self, "提示", "任务列表文件为空")
                return
            
            # 确认加载
            reply = QMessageBox.question(
                self, "确认加载", 
                f"将加载 {len(tasks_data)} 个任务到当前任务列表。\n"
                f"当前任务列表将被清空，是否继续？",
                QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No
            )
            
            if reply != QMessageBox.StandardButton.Yes:
                return
            
            # 清空当前任务列表
            self.batch_controller.clear_all_tasks()
            
            # 加载任务
            loaded_count = 0
            for task_data in tasks_data:
                try:
                    # 创建语音配置
                    voice_config_data = task_data.get("voice_config", {})
                    voice_config = VoiceConfig(
                        engine=voice_config_data.get("engine", "piper_tts"),
                        voice_name=voice_config_data.get("voice_name", "zh_CN-huayan-medium"),
                        rate=voice_config_data.get("rate", 1.0),
                        pitch=voice_config_data.get("pitch", 0),
                        volume=voice_config_data.get("volume", 0.8),
                        language=voice_config_data.get("language", "zh-CN"),
                        output_format=voice_config_data.get("output_format", "wav")
                    )
                    
                    # 设置额外参数
                    extra_params = voice_config_data.get("extra_params", {})
                    if extra_params:
                        voice_config.extra_params = extra_params
                    
                    # 添加任务（只添加未完成的任务）
                    task_status = task_data.get("status", "pending")
                    if task_status in ["pending", "failed", "cancelled"]:
                        task_id = self.batch_controller.add_task(
                            task_data["file_path"],
                            voice_config,
                            task_data["output_path"]
                        )
                        loaded_count += 1
                        self.logger.info(f"加载任务: {task_id}")
                    
                except Exception as e:
                    self.logger.error(f"加载任务失败: {task_data.get('id', 'unknown')}: {e}")
                    continue
            
            # 更新任务列表显示
            self.update_task_list()
            
            QMessageBox.information(self, "成功", f"成功加载 {loaded_count} 个未完成任务")
            
        except Exception as e:
            self.logger.error(f"加载任务列表失败: {e}")
            QMessageBox.critical(self, "错误", f"加载任务列表失败: {e}")
    
    def update_selected_task_buttons(self, task):
        """更新选中任务的按钮状态"""
        try:
            if not task:
                # 没有选中任务，禁用所有按钮
                self.start_selected_button.setEnabled(False)
                self.pause_selected_button.setEnabled(False)
                self.stop_selected_button.setEnabled(False)
                return
            
            # 根据任务状态设置按钮状态
            if task.status == TaskStatus.PENDING:
                # 待处理任务：启用开始按钮
                self.start_selected_button.setEnabled(True)
                self.pause_selected_button.setEnabled(False)
                self.stop_selected_button.setEnabled(False)
            elif task.status == TaskStatus.PROCESSING:
                # 处理中任务：启用暂停和停止按钮
                self.start_selected_button.setEnabled(False)
                self.pause_selected_button.setEnabled(True)
                self.stop_selected_button.setEnabled(True)
            elif task.status == TaskStatus.PAUSED:
                # 暂停任务：启用开始和停止按钮
                self.start_selected_button.setEnabled(True)
                self.pause_selected_button.setEnabled(False)
                self.stop_selected_button.setEnabled(True)
            else:
                # 已完成、失败或取消的任务：禁用所有按钮
                self.start_selected_button.setEnabled(False)
                self.pause_selected_button.setEnabled(False)
                self.stop_selected_button.setEnabled(False)
                
        except Exception as e:
            self.logger.error(f"更新选中任务按钮状态失败: {e}")
    
    def start_selected_task(self):
        """开始选中的任务"""
        try:
            current_row = self.task_table.currentRow()
            if current_row < 0:
                QMessageBox.information(self, "提示", "请先选择一个任务")
                return
            
            # 获取任务ID
            task_id = self.task_table.item(current_row, 0).data(Qt.ItemDataRole.UserRole)
            if not task_id:
                QMessageBox.warning(self, "警告", "无法获取任务ID")
                return
            
            # 开始单个任务（控制器层会进行完整的状态验证）
            success = self.batch_controller.start_single_task(task_id)
            
            if success:
                # 启动定时器更新
                self.update_timer.start(1000)
                
                # 更新按钮状态
                task = self.batch_controller.get_task_by_id(task_id)
                if task:
                    self.update_selected_task_buttons(task)
                QMessageBox.information(self, "成功", f"任务 {task_id} 已开始处理")
            else:
                QMessageBox.warning(self, "警告", "无法开始单个任务：存在正在处理或暂停的任务，或目标任务状态不允许。请等待所有任务完成后再开始。")
            
        except Exception as e:
            self.logger.error(f"开始选中任务失败: {e}")
            QMessageBox.critical(self, "错误", f"开始选中任务失败: {e}")
    
    def pause_selected_task(self):
        """暂停选中的任务"""
        try:
            current_row = self.task_table.currentRow()
            if current_row < 0:
                QMessageBox.information(self, "提示", "请先选择一个任务")
                return
            
            # 获取任务ID
            task_id = self.task_table.item(current_row, 0).data(Qt.ItemDataRole.UserRole)
            if not task_id:
                QMessageBox.warning(self, "警告", "无法获取任务ID")
                return
            
            # 获取任务
            task = self.batch_controller.get_task_by_id(task_id)
            if not task:
                QMessageBox.warning(self, "警告", "任务不存在")
                return
            
            # 检查任务状态
            if task.status != TaskStatus.PROCESSING:
                QMessageBox.warning(self, "警告", "只能暂停正在处理的任务")
                return
            
            # 暂停单个任务
            success = self.batch_controller.pause_single_task(task_id)
            
            if success:
                # 更新按钮状态
                self.update_selected_task_buttons(task)
                QMessageBox.information(self, "成功", f"任务 {task_id} 已暂停")
            else:
                QMessageBox.warning(self, "警告", f"任务 {task_id} 暂停失败")
            
        except Exception as e:
            self.logger.error(f"暂停选中任务失败: {e}")
            QMessageBox.critical(self, "错误", f"暂停选中任务失败: {e}")
    
    def stop_selected_task(self):
        """停止选中的任务"""
        try:
            current_row = self.task_table.currentRow()
            if current_row < 0:
                QMessageBox.information(self, "提示", "请先选择一个任务")
                return
            
            # 获取任务ID
            task_id = self.task_table.item(current_row, 0).data(Qt.ItemDataRole.UserRole)
            if not task_id:
                QMessageBox.warning(self, "警告", "无法获取任务ID")
                return
            
            # 获取任务
            task = self.batch_controller.get_task_by_id(task_id)
            if not task:
                QMessageBox.warning(self, "警告", "任务不存在")
                return
            
            # 检查任务状态
            if task.status != TaskStatus.PROCESSING:
                QMessageBox.warning(self, "警告", "只能停止正在处理的任务")
                return
            
            # 确认停止
            reply = QMessageBox.question(
                self, "确认停止", 
                f"确定要停止任务 {task_id} 吗？",
                QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No
            )
            
            if reply == QMessageBox.StandardButton.Yes:
                # 停止单个任务
                success = self.batch_controller.stop_single_task(task_id)
                
                if success:
                    # 更新按钮状态
                    self.update_selected_task_buttons(task)
                    QMessageBox.information(self, "成功", f"任务 {task_id} 已停止")
                else:
                    QMessageBox.warning(self, "警告", f"任务 {task_id} 停止失败")
            
        except Exception as e:
            self.logger.error(f"停止选中任务失败: {e}")
            QMessageBox.critical(self, "错误", f"停止选中任务失败: {e}")
    
    def _get_or_create_voice_combo(self, task, row):
        """获取或创建语音ComboBox（带缓存优化）"""
        try:
            # 生成缓存键
            cache_key = f"{task.id}_{task.voice_config.engine}"
            
            # 检查是否已有缓存的ComboBox
            if cache_key in self._voice_combo_cache:
                voice_combo = self._voice_combo_cache[cache_key]
                # 更新ComboBox状态
                self._update_voice_combo_status(voice_combo, task)
                return voice_combo
            
            # 创建新的ComboBox
            voice_combo = self._create_voice_combo(task, row)
            
            # 缓存ComboBox
            self._voice_combo_cache[cache_key] = voice_combo
            
            return voice_combo
            
        except Exception as e:
            self.logger.error(f"获取或创建语音ComboBox失败: {e}")
            return self._create_voice_combo(task, row)
    
    def _update_voice_combo_status(self, voice_combo, task):
        """更新语音ComboBox的状态"""
        try:
            # 根据任务状态设置是否启用
            if task.status == TaskStatus.PENDING:
                voice_combo.setEnabled(True)
                voice_combo.setStyleSheet("")  # 清除禁用样式
            else:
                voice_combo.setEnabled(False)
                voice_combo.setStyleSheet("QComboBox { background-color: #f0f0f0; color: #666; }")
        except Exception as e:
            self.logger.error(f"更新语音ComboBox状态失败: {e}")
    
    def _get_cached_voices(self, engine):
        """获取缓存的语音列表"""
        try:
            import time
            current_time = time.time()
            
            # 检查缓存是否过期（5分钟）
            if (engine in self._cached_voices and 
                current_time - self._last_voice_update < 300):
                return self._cached_voices[engine]
            
            # 缓存过期或不存在，重新加载
            from services.tts_service import TTSServiceFactory
            tts_service = TTSServiceFactory.create_service(engine)
            if tts_service:
                voices = tts_service.get_available_voices()
                self._cached_voices[engine] = voices
                self._last_voice_update = current_time
                return voices
            
            return []
            
        except Exception as e:
            self.logger.error(f"获取缓存语音列表失败: {e}")
            return []
    
    def _create_voice_combo(self, task, row):
        """为任务创建语音选择ComboBox（优化版本）"""
        try:
            from PyQt6.QtWidgets import QComboBox
            
            # 创建ComboBox
            voice_combo = QComboBox()
            voice_combo.setObjectName(f"voice_combo_{row}")
            
            # 根据任务状态设置是否启用
            if task.status == TaskStatus.PENDING:
                voice_combo.setEnabled(True)
            else:
                voice_combo.setEnabled(False)
                voice_combo.setStyleSheet("QComboBox { background-color: #f0f0f0; color: #666; }")
            
            # 获取当前引擎
            engine = task.voice_config.engine
            
            # 使用缓存的语音列表
            voices = self._get_cached_voices(engine)
            
            if voices:
                # 添加语音到ComboBox，使用与添加任务页面相同的格式
                for voice in voices:
                    voice_id = voice.get('id', '')
                    voice_name = voice.get('name', '')
                    voice_language = voice.get('language', 'unknown')
                    
                    if voice_id and voice_id != voice_name:
                        display_text = f"{voice_id} - {voice_name} ({voice_language})"
                    else:
                        display_text = f"{voice_name} ({voice_language})"
                    
                    voice_combo.addItem(display_text, voice)
                
                # 设置当前选中的语音
                current_voice_name = task.voice_config.voice_name
                for i in range(voice_combo.count()):
                    voice_data = voice_combo.itemData(i)
                    if voice_data and voice_data.get('id') == current_voice_name:
                        voice_combo.setCurrentIndex(i)
                        break
                    elif voice_data and voice_data.get('name') == current_voice_name:
                        voice_combo.setCurrentIndex(i)
                        break
                
                # 只在第一次创建时记录日志，避免频繁日志输出
                if not hasattr(self, '_combo_creation_logged'):
                    self.logger.info(f"为任务 {task.id} 创建语音ComboBox，共 {len(voices)} 个选项")
                    self._combo_creation_logged = True
            else:
                # 如果无法获取语音列表，添加默认选项
                voice_combo.addItem(task.voice_config.voice_name, {'id': task.voice_config.voice_name, 'name': task.voice_config.voice_name})
                self.logger.warning(f"无法为引擎 {engine} 获取语音列表")
            
            # 连接信号，当语音改变时更新任务配置
            voice_combo.currentTextChanged.connect(lambda text, r=row: self._on_voice_changed(r, text))
            
            return voice_combo
            
        except Exception as e:
            self.logger.error(f"创建语音ComboBox失败: {e}")
            # 创建简单的ComboBox作为后备
            voice_combo = QComboBox()
            voice_combo.addItem(task.voice_config.voice_name)
            voice_combo.setEnabled(False)
            return voice_combo
    
    def _on_voice_changed(self, row, new_voice_text):
        """处理语音变更事件"""
        try:
            # 暂时停止定时器更新，避免干扰用户操作
            self.update_timer.stop()
            
            # 获取任务ID
            task_id_item = self.task_table.item(row, 0)
            if not task_id_item:
                self.update_timer.start(1000)  # 恢复定时器
                return
            
            task_id = task_id_item.data(Qt.ItemDataRole.UserRole)
            if not task_id:
                self.update_timer.start(1000)  # 恢复定时器
                return
            
            # 获取任务
            task = self.batch_controller.get_task_by_id(task_id)
            if not task:
                self.logger.warning(f"任务不存在: {task_id}")
                self.update_timer.start(1000)  # 恢复定时器
                return
            
            # 检查任务状态是否允许修改
            if task.status != TaskStatus.PENDING:
                self.logger.warning(f"任务 {task_id} 状态不允许修改语音: {task.status}")
                self.update_timer.start(1000)  # 恢复定时器
                return
            
            # 获取选中的语音数据
            voice_combo = self.task_table.cellWidget(row, 2)
            if not voice_combo:
                self.update_timer.start(1000)  # 恢复定时器
                return
            
            voice_data = voice_combo.currentData()
            if voice_data:
                # 从语音数据中提取信息
                new_voice_id = voice_data.get('id', '')
                new_voice_name = voice_data.get('name', '')
                new_voice_language = voice_data.get('language', 'zh-CN')
                
                # 更新任务配置
                task.voice_config.voice_name = new_voice_id
                task.voice_config.language = new_voice_language
                
                self.logger.info(f"任务 {task_id} 语音已更新为: {new_voice_id} - {new_voice_name}")
                
                # 更新任务详情显示（不重建表格）
                self.show_task_details(task)
            else:
                self.logger.warning(f"无法获取语音数据: {new_voice_text}")
            
            # 延迟恢复定时器，给用户足够时间完成操作
            from PyQt6.QtCore import QTimer
            QTimer.singleShot(2000, self.update_timer.start)  # 2秒后恢复定时器
                
        except Exception as e:
            self.logger.error(f"处理语音变更失败: {e}")
            self.update_timer.start(1000)  # 确保定时器恢复
    
    def _update_voice_combos_status(self):
        """更新所有语音ComboBox的状态"""
        try:
            tasks = self.batch_controller.get_all_tasks()
            
            for row in range(self.task_table.rowCount()):
                # 获取任务ID
                task_id_item = self.task_table.item(row, 0)
                if not task_id_item:
                    continue
                
                task_id = task_id_item.data(Qt.ItemDataRole.UserRole)
                if not task_id:
                    continue
                
                # 获取任务
                task = self.batch_controller.get_task_by_id(task_id)
                if not task:
                    continue
                
                # 获取语音ComboBox
                voice_combo = self.task_table.cellWidget(row, 2)
                if not voice_combo:
                    continue
                
                # 根据任务状态更新ComboBox状态
                if task.status == TaskStatus.PENDING:
                    voice_combo.setEnabled(True)
                    voice_combo.setStyleSheet("")  # 清除禁用样式
                else:
                    voice_combo.setEnabled(False)
                    voice_combo.setStyleSheet("QComboBox { background-color: #f0f0f0; color: #666; }")
                
        except Exception as e:
            self.logger.error(f"更新语音ComboBox状态失败: {e}")
    
    def batch_add_tasks(self):
        """批量添加任务"""
        try:
            from PyQt6.QtWidgets import QDialog, QVBoxLayout, QHBoxLayout, QLabel, QLineEdit, QPushButton, QFileDialog, QFormLayout, QGroupBox, QCheckBox, QSpinBox, QDoubleSpinBox, QComboBox
            
            dialog = QDialog(self)
            dialog.setWindowTitle("批量添加任务")
            dialog.setModal(True)
            dialog.resize(600, 500)
            
            layout = QVBoxLayout(dialog)
            
            # 文件夹选择组
            folder_group = QGroupBox("文件夹选择")
            folder_layout = QVBoxLayout(folder_group)
            
            # 文件夹选择
            folder_select_layout = QHBoxLayout()
            folder_select_layout.addWidget(QLabel("文件夹路径:"))
            self.folder_path_edit = QLineEdit()
            self.folder_path_edit.setReadOnly(True)
            folder_select_layout.addWidget(self.folder_path_edit)
            
            browse_folder_button = QPushButton("浏览")
            browse_folder_button.clicked.connect(self.browse_folder)
            folder_select_layout.addWidget(browse_folder_button)
            
            folder_layout.addLayout(folder_select_layout)
            
            # 文件类型选择
            file_type_layout = QHBoxLayout()
            file_type_layout.addWidget(QLabel("支持的文件类型:"))
            
            self.file_type_checks = {}
            supported_types = ['pdf', 'txt', 'docx', 'epub', 'md']
            for file_type in supported_types:
                check = QCheckBox(file_type.upper())
                check.setChecked(True)  # 默认全选
                self.file_type_checks[file_type] = check
                file_type_layout.addWidget(check)
            
            file_type_layout.addStretch()
            folder_layout.addLayout(file_type_layout)
            
            layout.addWidget(folder_group)
            
            # 输出设置组
            output_group = QGroupBox(tr("batch_processor.add_task_dialog.output_settings"))
            output_layout = QVBoxLayout(output_group)
            
            # 输出目录
            output_dir_layout = QHBoxLayout()
            output_dir_layout.addWidget(QLabel(tr("batch_processor.add_task_dialog.output_directory")))
            self.batch_output_path_edit = QLineEdit()
            output_dir_layout.addWidget(self.batch_output_path_edit)
            
            output_browse_button = QPushButton(tr("batch_processor.add_task_dialog.browse"))
            output_browse_button.clicked.connect(self.browse_batch_output)
            output_dir_layout.addWidget(output_browse_button)
            
            output_layout.addLayout(output_dir_layout)
            
            layout.addWidget(output_group)
            
            # 语音设置组
            voice_group = QGroupBox(tr("batch_processor.add_task_dialog.voice_settings"))
            voice_layout = QFormLayout(voice_group)
            
            # 语音引擎
            self.batch_voice_engine_combo = QComboBox()
            voice_layout.addRow("语音引擎:", self.batch_voice_engine_combo)
            
            # 加载可用引擎
            self.load_batch_available_engines()
            
            # 语音选择
            self.batch_voice_combo = QComboBox()
            voice_layout.addRow("语音:", self.batch_voice_combo)
            
            # 连接引擎改变信号，使用弱引用避免对象销毁问题
            self.batch_voice_engine_combo.currentTextChanged.connect(self.on_batch_engine_changed)
            
            # 语音参数
            self.batch_rate_spinbox = QDoubleSpinBox()
            self.batch_rate_spinbox.setRange(0.1, 3.0)
            self.batch_rate_spinbox.setSingleStep(0.1)
            self.batch_rate_spinbox.setValue(1.0)
            voice_layout.addRow("语速:", self.batch_rate_spinbox)
            
            self.batch_pitch_spinbox = QSpinBox()
            self.batch_pitch_spinbox.setRange(-50, 50)
            self.batch_pitch_spinbox.setValue(0)
            voice_layout.addRow("音调:", self.batch_pitch_spinbox)
            
            self.batch_volume_spinbox = QDoubleSpinBox()
            self.batch_volume_spinbox.setRange(0.0, 1.0)
            self.batch_volume_spinbox.setSingleStep(0.1)
            self.batch_volume_spinbox.setValue(0.8)
            voice_layout.addRow("音量:", self.batch_volume_spinbox)
            
            layout.addWidget(voice_group)
            
            # 音频格式组
            audio_format_group = QGroupBox(tr("batch_processor.add_task_dialog.audio_format"))
            audio_layout = QFormLayout(audio_format_group)
            
            # 输出格式
            self.batch_output_format_combo = QComboBox()
            self.batch_output_format_combo.addItems(["wav", "mp3", "ogg", "m4a", "flac"])
            self.batch_output_format_combo.setCurrentText("wav")
            self.batch_output_format_combo.currentTextChanged.connect(self.on_batch_format_changed)
            audio_layout.addRow("输出格式:", self.batch_output_format_combo)
            
            # 编码器 (固定为FFmpeg，不可修改)
            self.batch_encoder_label = QLabel("FFmpeg")
            self.batch_encoder_label.setStyleSheet("color: #666; font-style: italic;")
            audio_layout.addRow("编码器:", self.batch_encoder_label)
            
            # 采样率
            self.batch_sample_rate_combo = QComboBox()
            self.batch_sample_rate_combo.addItems(["8000", "16000", "22050", "44100", "48000"])
            self.batch_sample_rate_combo.setCurrentText("22050")
            audio_layout.addRow("采样率(Hz):", self.batch_sample_rate_combo)
            
            # 位深度
            self.batch_bit_depth_combo = QComboBox()
            self.batch_bit_depth_combo.addItems(["8", "16", "24", "32"])
            self.batch_bit_depth_combo.setCurrentText("16")
            audio_layout.addRow("位深度(bit):", self.batch_bit_depth_combo)
            
            # 声道数
            self.batch_channels_combo = QComboBox()
            self.batch_channels_combo.addItems(["1 (单声道)", "2 (立体声)"])
            self.batch_channels_combo.setCurrentText("1 (单声道)")
            audio_layout.addRow("声道数:", self.batch_channels_combo)
            
            # 比特率 (仅对压缩格式有效)
            self.batch_bitrate_combo = QComboBox()
            self.batch_bitrate_combo.addItems(["64", "128", "192", "256", "320"])
            self.batch_bitrate_combo.setCurrentText("128")
            self.batch_bitrate_combo.setVisible(False)  # 默认隐藏
            audio_layout.addRow("比特率(kbps):", self.batch_bitrate_combo)
            
            layout.addWidget(audio_format_group)
            
            # 按钮
            button_layout = QHBoxLayout()
            
            ok_button = QPushButton(tr("batch_processor.add_task_dialog.ok"))
            ok_button.clicked.connect(dialog.accept)
            button_layout.addWidget(ok_button)
            
            cancel_button = QPushButton(tr("batch_processor.add_task_dialog.cancel"))
            cancel_button.clicked.connect(dialog.reject)
            button_layout.addWidget(cancel_button)
            
            layout.addLayout(button_layout)
            
            # 初始化语音引擎
            self.on_engine_changed(self.batch_voice_combo, self.batch_voice_engine_combo)
            
            if dialog.exec() == QDialog.DialogCode.Accepted:
                # 检查是否正在批量处理
                if self.batch_controller.is_running:
                    QMessageBox.information(self, tr("common.info"), tr("batch_processor.messages.processing_in_progress"))
                self.process_batch_add_tasks()
                
        except Exception as e:
            self.logger.error(f"批量添加任务失败: {e}")
            QMessageBox.critical(self, "错误", f"批量添加任务失败: {e}")
    
    def browse_folder(self):
        """浏览文件夹"""
        try:
            folder_path = QFileDialog.getExistingDirectory(self, "选择文件夹")
            if folder_path:
                self.folder_path_edit.setText(folder_path)
                # 自动设置输出目录为同一文件夹
                self.batch_output_path_edit.setText(folder_path)
        except Exception as e:
            self.logger.error(f"浏览文件夹失败: {e}")
    
    def browse_batch_output(self):
        """浏览批量输出目录"""
        try:
            output_dir = QFileDialog.getExistingDirectory(self, tr("batch_processor.file_dialog.select_output_directory"))
            if output_dir:
                self.batch_output_path_edit.setText(output_dir)
        except Exception as e:
            self.logger.error(f"浏览输出目录失败: {e}")
    
    def load_batch_available_engines(self):
        """加载批量添加的可用引擎"""
        try:
            self.batch_voice_engine_combo.clear()
            preferred_order = ['piper_tts', 'pyttsx3']
            from services.tts_service import TTSServiceFactory
            all_engines = list(TTSServiceFactory._engines.keys())
            available_engines = TTSServiceFactory.get_available_engines()
            
            for engine in preferred_order:
                if engine in all_engines:
                    self.batch_voice_engine_combo.addItem(f"{engine} ✓" if engine in available_engines else f"{engine} ✗")
            
            for engine in all_engines:
                if engine not in preferred_order:
                    self.batch_voice_engine_combo.addItem(f"{engine} ✓" if engine in available_engines else f"{engine} ✗")
            
            # 设置默认选择
            if available_engines:
                if 'piper_tts' in available_engines:
                    self.batch_voice_engine_combo.setCurrentText("piper_tts ✓")
                else:
                    self.batch_voice_engine_combo.setCurrentText(f"{available_engines[0]} ✓")
            
            self.logger.info(f"加载了 {len(all_engines)} 个TTS引擎，其中 {len(available_engines)} 个可用")
            
        except Exception as e:
            self.logger.error(f"加载可用引擎失败: {e}")
            self.batch_voice_engine_combo.addItems(["piper_tts", "pyttsx3"])
    
    def on_batch_engine_changed(self):
        """批量添加引擎改变事件"""
        try:
            # 检查控件是否仍然存在
            if not hasattr(self, 'batch_voice_combo') or self.batch_voice_combo is None:
                self.logger.debug("批量添加语音ComboBox已被销毁，跳过引擎改变处理")
                return
            
            if not hasattr(self, 'batch_voice_engine_combo') or self.batch_voice_engine_combo is None:
                self.logger.debug("批量添加引擎ComboBox已被销毁，跳过引擎改变处理")
                return
            
            # 调用通用的引擎改变方法，传递引擎ComboBox
            self.on_engine_changed(self.batch_voice_combo, self.batch_voice_engine_combo)
        except Exception as e:
            self.logger.error(f"批量添加引擎改变失败: {e}")
    
    def on_batch_format_changed(self):
        """批量添加格式改变事件"""
        try:
            format_type = self.batch_output_format_combo.currentText()
            
            # 根据格式类型设置比特率显示
            if format_type in ["mp3", "ogg", "m4a"]:
                self.batch_bitrate_combo.setVisible(True)
            else:
                self.batch_bitrate_combo.setVisible(False)
            
            # 根据格式设置默认采样率
            if format_type in ["mp3", "ogg", "m4a"]:
                # 压缩格式推荐较低采样率
                if "44100" not in [self.batch_sample_rate_combo.itemText(i) for i in range(self.batch_sample_rate_combo.count())]:
                    self.batch_sample_rate_combo.addItem("44100")
                self.batch_sample_rate_combo.setCurrentText("44100")
            else:
                # 无损格式推荐较高采样率
                if "48000" not in [self.batch_sample_rate_combo.itemText(i) for i in range(self.batch_sample_rate_combo.count())]:
                    self.batch_sample_rate_combo.addItem("48000")
                self.batch_sample_rate_combo.setCurrentText("48000")
                
        except Exception as e:
            self.logger.error(f"批量添加格式改变失败: {e}")
    
    def process_batch_add_tasks(self):
        """处理批量添加任务"""
        try:
            import os
            import glob
            
            # 获取文件夹路径
            folder_path = self.folder_path_edit.text().strip()
            if not folder_path or not os.path.exists(folder_path):
                QMessageBox.warning(self, "警告", "请选择有效的文件夹")
                return
            
            # 获取选中的文件类型
            selected_types = []
            for file_type, check in self.file_type_checks.items():
                if check.isChecked():
                    selected_types.append(file_type)
            
            if not selected_types:
                QMessageBox.warning(self, "警告", "请至少选择一种文件类型")
                return
            
            # 搜索文件
            all_files = []
            for file_type in selected_types:
                pattern = os.path.join(folder_path, f"*.{file_type}")
                files = glob.glob(pattern, recursive=False)
                all_files.extend(files)
            
            if not all_files:
                QMessageBox.information(self, "提示", f"在文件夹中未找到 {', '.join(selected_types)} 类型的文件")
                return
            
            # 获取语音配置
            voice_data = self.batch_voice_combo.currentData()
            if voice_data:
                voice_id = voice_data.get('id', '')
                voice_name = voice_data.get('name', '')
                voice_language = voice_data.get('language', 'zh-CN')
            else:
                voice_id = self.batch_voice_combo.currentText()
                voice_name = voice_id
                voice_language = "zh-CN"
            
            engine_text = self.batch_voice_engine_combo.currentText()
            engine = engine_text.replace(" ✓", "").replace(" ✗", "")
            
            # 创建语音配置
            from models.audio_model import VoiceConfig
            voice_config = VoiceConfig(
                engine=engine,
                voice_name=voice_id,
                rate=self.batch_rate_spinbox.value(),
                pitch=self.batch_pitch_spinbox.value(),
                volume=self.batch_volume_spinbox.value(),
                language=voice_language,
                output_format=self.batch_output_format_combo.currentText()
            )
            
            # 添加音频参数
            voice_config.extra_params = {
                'encoder': 'FFmpeg',
                'sample_rate': int(self.batch_sample_rate_combo.currentText()),
                'bit_depth': int(self.batch_bit_depth_combo.currentText()),
                'channels': int(self.batch_channels_combo.currentText().split()[0]),  # 提取数字部分
                'bitrate': int(self.batch_bitrate_combo.currentText())
            }
            
            # 批量添加任务
            added_count = 0
            output_dir = self.batch_output_path_edit.text().strip()
            if not output_dir:
                output_dir = folder_path
            
            for file_path in all_files:
                try:
                    # 生成输出文件名
                    file_name = os.path.basename(file_path)
                    name, ext = os.path.splitext(file_name)
                    output_file = f"{name}.{voice_config.output_format}"
                    output_path = os.path.normpath(os.path.join(output_dir, output_file))
                    
                    # 添加任务
                    task_id = self.batch_controller.add_task(
                        file_path=file_path,
                        voice_config=voice_config,
                        output_path=output_path
                    )
                    
                    if task_id:
                        added_count += 1
                        self.logger.info(f"批量添加任务成功: {file_name}")
                    
                except Exception as e:
                    self.logger.error(f"添加文件 {file_path} 失败: {e}")
                    continue
            
            if added_count > 0:
                self.manual_update()
                QMessageBox.information(self, "成功", f"成功添加 {added_count} 个任务")
            else:
                QMessageBox.warning(self, "警告", "没有成功添加任何任务")
                
        except Exception as e:
            self.logger.error(f"处理批量添加任务失败: {e}")
            QMessageBox.critical(self, "错误", f"处理批量添加任务失败: {e}")
    
    # ==================== 生成文件列表相关方法 ====================
    
    def add_generated_file(self, file_path: str):
        """添加生成的文件到列表"""
        try:
            if file_path and os.path.exists(file_path):
                # 获取文件名
                filename = os.path.basename(file_path)
                
                # 创建列表项
                item = QListWidgetItem(filename)
                item.setData(Qt.ItemDataRole.UserRole, file_path)  # 存储完整路径
                
                # 设置图标（根据文件扩展名）
                if filename.lower().endswith(('.mp3', '.wav', '.ogg', '.flac')):
                    item.setIcon(QIcon("resources/icons/audio.svg"))
                elif filename.lower().endswith(('.srt', '.lrc', '.vtt', '.ass')):
                    item.setIcon(QIcon("resources/icons/subtitle.svg"))
                else:
                    item.setIcon(QIcon("resources/icons/file.svg"))
                
                # 添加到列表
                self.generated_files_list.addItem(item)
                
                self.logger.info(f"添加生成文件到列表: {filename}")
                
        except Exception as e:
            self.logger.error(f"添加生成文件到列表失败: {e}")
    
    def on_file_selection_changed(self):
        """文件选择变化时的处理"""
        try:
            current_item = self.generated_files_list.currentItem()
            has_selection = current_item is not None
            
            # 更新按钮状态
            self.open_file_button.setEnabled(has_selection)
            self.open_folder_button.setEnabled(has_selection)
            self.delete_file_button.setEnabled(has_selection)
            
        except Exception as e:
            self.logger.error(f"处理文件选择变化失败: {e}")
    
    def on_file_double_clicked(self, item):
        """双击文件项时的处理"""
        try:
            if item:
                file_path = item.data(Qt.ItemDataRole.UserRole)
                if file_path and os.path.exists(file_path):
                    self.open_file(file_path)
                    
        except Exception as e:
            self.logger.error(f"双击打开文件失败: {e}")
    
    def open_selected_file(self):
        """打开选中的文件"""
        try:
            current_item = self.generated_files_list.currentItem()
            if current_item:
                file_path = current_item.data(Qt.ItemDataRole.UserRole)
                if file_path and os.path.exists(file_path):
                    self.open_file(file_path)
                else:
                    QMessageBox.warning(self, "警告", "文件不存在")
            else:
                QMessageBox.information(self, "提示", "请先选择一个文件")
                
        except Exception as e:
            self.logger.error(f"打开选中文件失败: {e}")
            QMessageBox.critical(self, "错误", f"打开文件失败: {e}")
    
    def open_file(self, file_path: str):
        """打开文件"""
        try:
            import subprocess
            import platform
            
            system = platform.system()
            if system == "Windows":
                os.startfile(file_path)
            elif system == "Darwin":  # macOS
                subprocess.run(["open", file_path])
            else:  # Linux
                subprocess.run(["xdg-open", file_path])
                
            self.logger.info(f"打开文件: {file_path}")
            
        except Exception as e:
            self.logger.error(f"打开文件失败: {e}")
            QMessageBox.critical(self, "错误", f"打开文件失败: {e}")
    
    def open_file_folder(self):
        """打开文件所在文件夹"""
        try:
            current_item = self.generated_files_list.currentItem()
            if current_item:
                file_path = current_item.data(Qt.ItemDataRole.UserRole)
                if file_path and os.path.exists(file_path):
                    folder_path = os.path.dirname(file_path)
                    
                    import subprocess
                    import platform
                    
                    system = platform.system()
                    if system == "Windows":
                        os.startfile(folder_path)
                    elif system == "Darwin":  # macOS
                        subprocess.run(["open", folder_path])
                    else:  # Linux
                        subprocess.run(["xdg-open", folder_path])
                        
                    self.logger.info(f"打开文件夹: {folder_path}")
                else:
                    QMessageBox.warning(self, "警告", "文件不存在")
            else:
                QMessageBox.information(self, "提示", "请先选择一个文件")
                
        except Exception as e:
            self.logger.error(f"打开文件夹失败: {e}")
            QMessageBox.critical(self, "错误", f"打开文件夹失败: {e}")
    
    def delete_selected_file(self):
        """删除选中的文件"""
        try:
            current_item = self.generated_files_list.currentItem()
            if current_item:
                file_path = current_item.data(Qt.ItemDataRole.UserRole)
                filename = os.path.basename(file_path)
                
                # 确认删除
                reply = QMessageBox.question(
                    self, 
                    "确认删除", 
                    f"确定要删除文件 '{filename}' 吗？\n\n此操作不可撤销！",
                    QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No,
                    QMessageBox.StandardButton.No
                )
                
                if reply == QMessageBox.StandardButton.Yes:
                    file_deleted = False
                    
                    # 尝试删除文件（如果存在）
                    if os.path.exists(file_path):
                        try:
                            os.remove(file_path)
                            file_deleted = True
                            self.logger.info(f"删除文件: {file_path}")
                        except Exception as e:
                            self.logger.warning(f"删除文件失败: {e}")
                    else:
                        file_deleted = True
                        QMessageBox.warning(self, "警告", "文件不存在")
                    # 无论文件是否存在，都从列表中移除记录
                    row = self.generated_files_list.row(current_item)
                    self.generated_files_list.takeItem(row)
                    
                    # 根据文件是否实际删除显示不同的消息
                    if file_deleted:
                        QMessageBox.information(self, "成功", f"文件 '{filename}' 已删除")
                    else:
                        QMessageBox.information(self, "完成", f"文件记录已从列表中移除（文件不存在）")
            else:
                QMessageBox.information(self, "提示", "请先选择一个文件")
                
        except Exception as e:
            self.logger.error(f"删除文件失败: {e}")
            QMessageBox.critical(self, "错误", f"删除文件失败: {e}")
    
    def clear_generated_files_list(self):
        """清空生成文件列表"""
        try:
            self.generated_files_list.clear()
            self.logger.info("清空生成文件列表")
            
        except Exception as e:
            self.logger.error(f"清空生成文件列表失败: {e}")
    
    def refresh_generated_files_list(self):
        """刷新生成文件列表"""
        try:
            # 清空当前列表
            self.clear_generated_files_list()
            
            # 从批量控制器获取已完成的任务
            completed_tasks = []
            for task in self.batch_controller.tasks:
                if task.status == TaskStatus.COMPLETED and task.output_path:
                    completed_tasks.append(task.output_path)
            
            # 添加文件到列表
            for file_path in completed_tasks:
                self.add_generated_file(file_path)
                
            self.logger.info(f"刷新生成文件列表，共 {len(completed_tasks)} 个文件")
            
        except Exception as e:
            self.logger.error(f"刷新生成文件列表失败: {e}")
