"""
转换控制界面模块

提供音频转换过程的控制和管理功能，包括：
- 转换进度监控和显示
- 转换过程的暂停、继续、停止控制
- 实时状态更新和日志显示
- 转换结果预览和管理
- 多线程转换支持

作者: TTS开发团队
版本: 1.0.0
创建时间: 2024
"""

from PyQt6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QLabel, 
    QPushButton, QProgressBar, QTextEdit, QGroupBox,
    QFrame, QScrollArea, QMessageBox, QFileDialog
)
from PyQt6.QtCore import Qt, pyqtSignal, QThread, QTimer, QElapsedTimer
from PyQt6.QtGui import QFont
from services.language_service import get_text as tr

from models.audio_model import VoiceConfig, OutputConfig
from utils.log_manager import LogManager


class ConversionWorker(QThread):
    """
    转换工作线程
    
    在后台线程中执行音频转换任务，避免阻塞UI。
    支持进度监控、暂停、停止等控制功能。
    
    特性：
    - 多线程执行：避免UI阻塞
    - 进度监控：实时更新转换进度
    - 状态管理：支持暂停、继续、停止
    - 错误处理：完善的异常处理机制
    - 信号通信：与UI线程安全通信
    """
    
    # 信号定义 - 用于与UI线程通信
    progress_updated = pyqtSignal(int, int)  # 当前进度, 总进度
    status_updated = pyqtSignal(str)  # 状态信息
    segment_completed = pyqtSignal(str, str)  # 段落标题, 文件路径
    conversion_completed = pyqtSignal(str)  # 输出目录
    error_occurred = pyqtSignal(str)  # 错误信息
    
    def __init__(self, segments, voice_config, output_config, progress_estimator=None, chapters=None):
        super().__init__()
        self.segments = segments
        self.voice_config = voice_config
        self.output_config = output_config
        self.progress_estimator = progress_estimator
        self.chapters = chapters  # 添加章节信息
        self.is_paused = False
        self.is_stopped = False
        self.current_segment = 0
        self.audio_files = []
        # 初始化日志记录器
        self.logger = LogManager().get_logger("ConversionWorker")
    
    def run(self):
        """执行转换"""
        try:
            total_segments = len(self.segments)
            self.status_updated.emit(tr('conversion_control.messages.start_conversion'))
            
            for i, segment in enumerate(self.segments):
                if self.is_stopped:
                    break
                
                # 等待暂停状态
                while self.is_paused and not self.is_stopped:
                    self.msleep(100)
                
                if self.is_stopped:
                    break
                
                self.current_segment = i
                self.status_updated.emit(tr('conversion_control.messages.converting_segment', current=i+1, total=total_segments))
                
                # 通知进度估算器开始处理文件
                if hasattr(self, 'progress_estimator') and self.progress_estimator:
                    self.progress_estimator.start_file_processing(i)
                
                # 调用实际的TTS转换
                try:
                    from services.tts_service import TTSService
                    tts_service = TTSService()
                    
                    # 生成输出文件路径
                    import os
                    from utils.path_utils import normalize_path
                    
                    output_dir = normalize_path(self.output_config.output_dir)
                    file_extension = self.output_config.format
                    
                    # 创建章节信息对象
                    class ChapterInfo:
                        def __init__(self, number, title, index=None, original_filename=None):
                            self.number = number
                            self.chapter_num = number  # 添加 chapter_num 属性，与 number 相同
                            self.title = title
                            self.index = index or number  # 如果没有提供index，使用number
                            self.original_filename = original_filename  # 添加原始文件名属性
                    
                    # 处理段落数据，支持字符串和字典两种格式
                    if isinstance(segment, dict):
                        # 如果是字典格式，直接使用
                        text_content = segment.get('content', '')
                        chapter_num = segment.get('chapter_num', i + 1)
                        chapter_title = segment.get('title', f'段落{i+1}')
                        original_filename = segment.get('original_filename', None)
                        # 对于"顺序号 + 标题"模式，index应该是处理顺序（从1开始）
                        chapter_index = i + 1
                    else:
                        # 如果是字符串格式，尝试从章节信息中获取标题
                        text_content = str(segment)
                        chapter_num = i + 1
                        chapter_title = f'段落{i+1}'
                        chapter_index = i + 1
                        original_filename = None
                        
                        # 尝试从外部获取章节信息（如果有的话）
                        if hasattr(self, 'chapters') and self.chapters and i < len(self.chapters):
                            chapter = self.chapters[i]
                            chapter_title = getattr(chapter, 'title', f'段落{i+1}')
                            chapter_num = getattr(chapter, 'number', i + 1)
                            original_filename = getattr(chapter, 'original_filename', None)
                    
                    chapter_info = ChapterInfo(chapter_num, chapter_title, chapter_index, original_filename)
                    
                    # 创建进度回调函数
                    def progress_callback(progress):
                        # 将进度传递给进度估算器
                        if hasattr(self, 'progress_estimator') and self.progress_estimator:
                            self.progress_estimator.progress_updated.emit(progress)
                    
                    # 不传递file_path，让TTS服务使用文件命名规则生成路径
                    result_path = tts_service.synthesize_text(text_content, self.voice_config, None, self.output_config, chapter_info, progress_callback)
                    
                    # 规范化路径，确保路径分隔符正确
                    if result_path:
                        result_path = os.path.normpath(result_path)
                        result_path = os.path.abspath(result_path)
                    
                    if result_path and os.path.exists(result_path):
                        self.audio_files.append(result_path)
                        segment_title = segment.get('title', f'段落{i+1}') if isinstance(segment, dict) else f'段落{i+1}'
                        self.segment_completed.emit(segment_title, result_path)
                        self.status_updated.emit(tr('conversion_control.messages.segment_completed', segment=i+1))
                        
                        # 通知进度估算器文件完成
                        if hasattr(self, 'progress_estimator') and self.progress_estimator:
                            self.progress_estimator.on_file_completed(i)
                    else:
                        error_msg = tr('conversion_control.messages.segment_failed', segment=i+1)
                        if not result_path:
                            self.logger.error(tr('conversion_control.messages.conversion_worker_error', error=f"{error_msg} - TTS服务返回空路径"))
                        else:
                            self.logger.error(tr('conversion_control.messages.conversion_worker_error', error=f"{error_msg} - 文件不存在: {result_path}"))
                        self.error_occurred.emit(error_msg)
                        
                except Exception as e:
                    error_msg = tr('conversion_control.messages.segment_failed', segment=i+1) + f": {str(e)}"
                    self.logger.error(tr('conversion_control.messages.conversion_worker_error', error=error_msg))
                    self.error_occurred.emit(error_msg)
                
                self.progress_updated.emit(i + 1, total_segments)
            
            if not self.is_stopped:
                # 检查是否需要合并文件
                if self.output_config.merge_files:
                    self.status_updated.emit(tr('conversion_control.messages.merging_files'))
                    self._merge_audio_files()
                else:
                    self.status_updated.emit(tr('conversion_control.messages.conversion_completed'))
                
                self.conversion_completed.emit(self.output_config.output_dir)
            
        except Exception as e:
            error_msg = tr('conversion_control.messages.conversion_error', error=str(e))
            self.logger.error(tr('conversion_control.messages.conversion_worker_severe_error', error=error_msg))
            self.error_occurred.emit(error_msg)
    
    def pause(self):
        """暂停转换"""
        self.is_paused = True
    
    def resume(self):
        """恢复转换"""
        self.is_paused = False
    
    def stop(self):
        """停止转换"""
        self.is_stopped = True
    
    def _merge_audio_files(self):
        """合并音频文件"""
        try:
            import os
            import glob
            from services.audio_service import AudioService
            from models.audio_model import AudioModel
            
            # 获取输出目录
            output_dir = self.output_config.output_dir
            if not os.path.exists(output_dir):
                self.logger.error(tr('conversion_control.messages.output_dir_not_exists', dir=output_dir))
                return
            
            # 查找所有生成的音频文件
            audio_files = []
            for ext in ['*.wav', '*.mp3', '*.ogg', '*.m4a']:
                pattern = os.path.join(output_dir, ext)
                audio_files.extend(glob.glob(pattern))
            
            # 按文件名排序，确保章节顺序
            audio_files.sort()
            
            if len(audio_files) < 2:
                self.logger.warning(tr('conversion_control.messages.insufficient_audio_files'))
                return
            
            self.logger.info(tr('conversion_control.messages.found_audio_files', count=len(audio_files)))
            
            # 创建音频服务
            audio_service = AudioService()
            
            # 读取音频文件
            audio_models = []
            for audio_file in audio_files:
                try:
                    with open(audio_file, 'rb') as f:
                        audio_data = f.read()
                    
                    # 创建音频模型
                    audio_model = AudioModel(
                        audio_data=audio_data,
                        voice_config=self.voice_config,
                        format=self.output_config.format,
                        sample_rate=self.output_config.sample_rate,
                        channels=self.output_config.channels,
                        bitrate=self.output_config.bitrate
                    )
                    audio_models.append(audio_model)
                    
                except Exception as e:
                    self.logger.error(tr('conversion_control.messages.read_audio_file_failed', file=audio_file, error=str(e)))
                    continue
            
            if len(audio_models) < 2:
                self.logger.warning(tr('conversion_control.messages.insufficient_valid_files'))
                return
            
            # 合并音频文件
            merged_audio = audio_service.merge_audio_files(audio_models)
            
            # 生成合并文件名
            merge_filename = self.output_config.merge_filename
            if not merge_filename:
                merge_filename = tr('conversion_control.messages.complete_audio')
            
            # 确保文件名有正确的扩展名
            if not merge_filename.endswith(f'.{self.output_config.format}'):
                merge_filename += f'.{self.output_config.format}'
            
            # 保存合并后的文件
            merged_file_path = os.path.join(output_dir, merge_filename)
            with open(merged_file_path, 'wb') as f:
                f.write(merged_audio.audio_data)
            
            self.logger.info(tr('conversion_control.messages.audio_merge_completed', path=merged_file_path))
            self.status_updated.emit(tr('conversion_control.messages.merge_completed', filename=merge_filename))
            
        except Exception as e:
            error_msg = tr('conversion_control.messages.merge_failed', error=str(e))
            self.logger.error(tr('conversion_control.messages.merge_audio_files_error', error=error_msg))
            self.error_occurred.emit(error_msg)


class ConversionControlWidget(QWidget):
    """转换控制界面"""
    
    # 信号定义
    conversion_started = pyqtSignal()
    conversion_paused = pyqtSignal()
    conversion_resumed = pyqtSignal()
    conversion_stopped = pyqtSignal()
    conversion_completed = pyqtSignal(str)
    
    def __init__(self):
        super().__init__()
        self.logger = LogManager().get_logger("ConversionControlWidget")
        
        # 转换状态
        self.is_converting = False
        self.is_paused = False
        self.current_progress = 0
        self.total_segments = 0
        self.processed_segments = 0
        self.audio_files = []
        
        # 输出设置引用
        self.output_settings_widget = None
        # 语音设置引用
        self.voice_settings_widget = None
        
        # 转换工作线程
        self.conversion_worker = None
        
        # 进度估算器
        self.progress_estimator = None
        
        # 初始化UI
        self.setup_ui()
        self.setup_connections()
    
    def setup_ui(self):
        """设置用户界面"""
        layout = QVBoxLayout(self)
        layout.setContentsMargins(5, 5, 5, 5)
        layout.setSpacing(10)
        
        # 标题
        title_label = QLabel(tr('conversion_control.title'))
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
        
        # 转换控制组
        self.create_conversion_control_group(content_layout)
        
        # 进度显示组
        self.create_progress_group(content_layout)
        
        # 状态信息组
        self.create_status_group(content_layout)
        
        # 转换详情组
        self.create_details_group(content_layout)
        
        # 输出管理组
        self.create_output_group(content_layout)
        
        scroll_area.setWidget(content_widget)
        layout.addWidget(scroll_area)
    
    def create_conversion_control_group(self, parent_layout):
        """创建转换控制组"""
        group = QGroupBox(tr('conversion_control.conversion_control'))
        layout = QVBoxLayout(group)
        
        # 控制按钮
        button_layout = QHBoxLayout()
        
        self.start_button = QPushButton(tr('conversion_control.start_conversion'))
        self.start_button.clicked.connect(self.on_start_button_clicked)
        self.start_button.setStyleSheet("""
            QPushButton {
                background-color: #28a745;
                color: white;
                font-weight: bold;
                padding: 10px 20px;
                border-radius: 5px;
            }
            QPushButton:hover {
                background-color: #218838;
            }
            QPushButton:disabled {
                background-color: #6c757d;
            }
        """)
        button_layout.addWidget(self.start_button)
        
        self.pause_button = QPushButton(tr('conversion_control.pause'))
        self.pause_button.clicked.connect(self.pause_conversion)
        self.pause_button.setEnabled(False)
        self.pause_button.setStyleSheet("""
            QPushButton {
                background-color: #ffc107;
                color: black;
                font-weight: bold;
                padding: 10px 20px;
                border-radius: 5px;
            }
            QPushButton:hover {
                background-color: #e0a800;
            }
            QPushButton:disabled {
                background-color: #6c757d;
            }
        """)
        button_layout.addWidget(self.pause_button)
        
        self.stop_button = QPushButton(tr('conversion_control.stop'))
        self.stop_button.clicked.connect(self.stop_conversion)
        self.stop_button.setEnabled(False)
        self.stop_button.setStyleSheet("""
            QPushButton {
                background-color: #dc3545;
                color: white;
                font-weight: bold;
                padding: 10px 20px;
                border-radius: 5px;
            }
            QPushButton:hover {
                background-color: #c82333;
            }
            QPushButton:disabled {
                background-color: #6c757d;
            }
        """)
        button_layout.addWidget(self.stop_button)
        
        button_layout.addStretch()
        layout.addLayout(button_layout)
        
        parent_layout.addWidget(group)
    
    def create_progress_group(self, parent_layout):
        """创建进度显示组"""
        group = QGroupBox(tr('conversion_control.conversion_progress'))
        layout = QVBoxLayout(group)
        
        # 总体进度
        self.overall_progress = QProgressBar()
        self.overall_progress.setRange(0, 100)
        self.overall_progress.setValue(0)
        self.overall_progress.setStyleSheet("""
            QProgressBar {
                border: 2px solid #ddd;
                border-radius: 5px;
                text-align: center;
                font-weight: bold;
            }
            QProgressBar::chunk {
                background-color: #007bff;
                border-radius: 3px;
            }
        """)
        layout.addWidget(self.overall_progress)
        
        # 进度信息
        progress_info_layout = QHBoxLayout()
        
        self.progress_label = QLabel(tr('conversion_control.ready'))
        self.progress_label.setStyleSheet("font-weight: bold; color: #666;")
        progress_info_layout.addWidget(self.progress_label)
        
        self.progress_info_label = QLabel("0/0")
        self.progress_info_label.setStyleSheet("color: #666;")
        progress_info_layout.addStretch()
        progress_info_layout.addWidget(self.progress_info_label)
        
        layout.addLayout(progress_info_layout)
        
        parent_layout.addWidget(group)
    
    def create_status_group(self, parent_layout):
        """创建状态信息组"""
        group = QGroupBox(tr('conversion_control.conversion_status'))
        layout = QVBoxLayout(group)
        
        # 当前状态
        status_layout = QHBoxLayout()
        status_layout.addWidget(QLabel(tr('conversion_control.status')))
        self.status_label = QLabel(tr('conversion_control.ready_status'))
        self.status_label.setStyleSheet("font-weight: bold; color: #28a745;")
        status_layout.addWidget(self.status_label)
        status_layout.addStretch()
        layout.addLayout(status_layout)
        
        # 状态信息
        self.status_text = QTextEdit()
        self.status_text.setMaximumHeight(100)
        self.status_text.setPlaceholderText(tr('conversion_control.status_placeholder'))
        self.status_text.setReadOnly(True)
        layout.addWidget(self.status_text)
        
        parent_layout.addWidget(group)
    
    def create_details_group(self, parent_layout):
        """创建转换详情组"""
        group = QGroupBox(tr('conversion_control.conversion_details'))
        layout = QVBoxLayout(group)
        
        # 详情信息
        details_layout = QHBoxLayout()
        
        # 总段落数
        self.total_segments_label = QLabel(tr('conversion_control.total_segments', count=0))
        details_layout.addWidget(self.total_segments_label)
        
        # 已处理
        self.processed_segments_label = QLabel(tr('conversion_control.processed_segments', count=0))
        details_layout.addWidget(self.processed_segments_label)
        
        # 剩余时间
        self.remaining_time_label = QLabel(tr('conversion_control.remaining_time', time="--"))
        details_layout.addWidget(self.remaining_time_label)
        
        details_layout.addStretch()
        layout.addLayout(details_layout)
        
        # 当前段落
        current_layout = QHBoxLayout()
        current_layout.addWidget(QLabel(tr('conversion_control.current_segment')))
        self.current_segment_label = QLabel(tr('conversion_control.none'))
        self.current_segment_label.setStyleSheet("font-weight: bold;")
        current_layout.addWidget(self.current_segment_label)
        current_layout.addStretch()
        layout.addLayout(current_layout)
        
        parent_layout.addWidget(group)
    
    def create_output_group(self, parent_layout):
        """创建输出管理组"""
        group = QGroupBox(tr('conversion_control.output_management'))
        layout = QVBoxLayout(group)
        
        # 输出目录
        output_layout = QHBoxLayout()
        output_layout.addWidget(QLabel(tr('conversion_control.output_directory')))
        self.output_dir_label = QLabel(tr('conversion_control.not_set'))
        self.output_dir_label.setStyleSheet("color: #666;")
        output_layout.addWidget(self.output_dir_label)
        output_layout.addStretch()
        
        self.open_output_button = QPushButton(tr('conversion_control.open_output_directory'))
        self.open_output_button.clicked.connect(self.open_output_directory)
        self.open_output_button.setEnabled(False)
        output_layout.addWidget(self.open_output_button)
        
        layout.addLayout(output_layout)
        
        # 生成的文件列表
        self.files_list = QTextEdit()
        self.files_list.setMaximumHeight(150)
        self.files_list.setPlaceholderText(tr('conversion_control.files_placeholder'))
        self.files_list.setReadOnly(True)
        layout.addWidget(self.files_list)
        
        parent_layout.addWidget(group)
    
    def setup_connections(self):
        """设置信号连接"""
        # 定时器用于更新剩余时间
        self.timer = QTimer()
        self.timer.timeout.connect(self.update_remaining_time)
        self.start_time = None
    
    def set_output_settings_widget(self, output_settings_widget):
        """设置输出设置页面引用"""
        self.output_settings_widget = output_settings_widget
    
    def set_voice_settings_widget(self, voice_settings_widget):
        """设置语音设置页面引用"""
        self.voice_settings_widget = voice_settings_widget
    
    def on_start_button_clicked(self):
        """开始转换按钮点击事件"""
        if self.is_converting:
            return
        
        # 检查是否有待转换的数据
        if not hasattr(self, 'pending_segments') or not self.pending_segments:
            QMessageBox.warning(self, tr('conversion_control.messages.warning'), tr('conversion_control.messages.warning_no_content'))
            return
        
        # 从输出设置页面获取最新配置
        if self.output_settings_widget:
            try:
                from models.audio_model import OutputConfig
                latest_output_config = self.output_settings_widget.get_output_config()
                if latest_output_config:
                    self.pending_output_config = latest_output_config
                    self.logger.info(f"已从输出设置页面获取最新配置: {latest_output_config.output_dir}")
            except Exception as e:
                self.logger.error(tr('conversion_control.messages.get_output_config_failed', error=str(e)))
        
        # 使用待转换的数据开始转换
        self.start_conversion(
            self.pending_segments, 
            self.pending_voice_config, 
            self.pending_output_config
        )
    
    def start_conversion(self, segments=None, voice_config=None, output_config=None, chapters=None):
        """开始转换"""
        if self.is_converting:
            return
        
        # 如果提供了参数，保存为待转换数据
        if segments and voice_config and output_config:
            self.pending_segments = segments
            self.pending_voice_config = voice_config
            self.pending_output_config = output_config
            self.pending_chapters = chapters
        
        # 检查是否有待转换的数据
        if not hasattr(self, 'pending_segments') or not self.pending_segments:
            QMessageBox.warning(self, tr('conversion_control.messages.warning'), tr('conversion_control.messages.warning_no_content'))
            return
        
        # 从输出设置页面获取最新配置
        if self.output_settings_widget:
            try:
                from models.audio_model import OutputConfig
                latest_output_config = self.output_settings_widget.get_output_config()
                if latest_output_config:
                    self.pending_output_config = latest_output_config
                    self.logger.info(f"已从输出设置页面获取最新配置: {latest_output_config.output_dir}")
                    self.logger.info(f"文件命名模式: {latest_output_config.naming_mode}")
                    self.logger.info(f"自定义模板: {latest_output_config.custom_template}")
            except Exception as e:
                self.logger.error(tr('conversion_control.messages.get_output_config_failed', error=str(e)))
        
        # 从语音设置页面获取最新配置
        if self.voice_settings_widget:
            try:
                latest_voice_config = self.voice_settings_widget.get_voice_config()
                if latest_voice_config:
                    self.pending_voice_config = latest_voice_config
                    self.logger.info(f"已从语音设置页面获取最新配置: {latest_voice_config.engine}")
            except Exception as e:
                self.logger.error(tr('conversion_control.messages.get_voice_config_failed', error=str(e)))
        
        try:
            self.is_converting = True
            self.is_paused = False
            self.current_progress = 0
            self.total_segments = len(self.pending_segments)
            self.processed_segments = 0
            self.audio_files = []
            
            # 初始化进度估算器（对Edge-TTS）
            if (self.pending_voice_config and 
                hasattr(self.pending_voice_config, 'engine') and 
                self.pending_voice_config.engine in ['edge_tts']):
                
                from services.progress_estimator import ProgressEstimator, TextComplexityAnalyzer
                
                # 创建进度估算器
                self.progress_estimator = ProgressEstimator()
                self.progress_estimator.progress_updated.connect(self.on_progress_updated)
                self.progress_estimator.status_updated.connect(self.on_status_updated)
                self.progress_estimator.phase_changed.connect(self.on_phase_changed)
                
                # 分析文本复杂度
                total_text = ' '.join([
                    segment.get('content', '') if isinstance(segment, dict) else str(segment)
                    for segment in self.pending_segments
                ])
                complexity = TextComplexityAnalyzer.analyze_complexity(total_text)
                
                # 准备多文件进度估算
                file_text_lengths = [
                    len(segment.get('content', '') if isinstance(segment, dict) else str(segment))
                    for segment in self.pending_segments
                ]
                
                # 根据引擎类型设置不同的配置
                if self.pending_voice_config.engine == 'edge_tts':
                    api_url = "edge-tts"
                    engine_name = "edge_tts"
                else:
                    api_url = "unknown"
                    engine_name = self.pending_voice_config.engine
                
                # 开始进度估算
                self.progress_estimator.start_estimation(
                    len(total_text), complexity, api_url, engine_name,
                    total_files=len(self.pending_segments), file_text_lengths=file_text_lengths
                )
                
                self.logger.info(tr('conversion_control.messages.progress_estimation_started', engine=engine_name, length=len(total_text), complexity=complexity))
            else:
                self.progress_estimator = None
            
            # 更新UI
            self.start_button.setEnabled(False)
            self.pause_button.setEnabled(True)
            self.stop_button.setEnabled(True)
            
            self.status_label.setText(tr('conversion_control.converting_status'))
            self.status_label.setStyleSheet("font-weight: bold; color: #007bff;")
            self.status_text.append(tr('conversion_control.messages.conversion_started'))
            
            self.total_segments_label.setText(tr('conversion_control.total_segments', count=self.total_segments))
            # 显示标准化后的输出目录路径
            from utils.path_utils import normalize_path
            normalized_output_dir = normalize_path(self.pending_output_config.output_dir)
            self.output_dir_label.setText(normalized_output_dir)
            self.open_output_button.setEnabled(True)
            
            # 创建并启动工作线程
            self.conversion_worker = ConversionWorker(self.pending_segments, self.pending_voice_config, self.pending_output_config, self.progress_estimator, self.pending_chapters)
            self.conversion_worker.progress_updated.connect(self.update_progress)
            self.conversion_worker.status_updated.connect(self.update_status)
            self.conversion_worker.segment_completed.connect(self.on_segment_completed)
            self.conversion_worker.conversion_completed.connect(self.on_conversion_completed)
            self.conversion_worker.error_occurred.connect(self.on_conversion_error)
            self.conversion_worker.start()
            
            # 开始计时
            self.start_time = QElapsedTimer()
            self.start_time.start()
            self.timer.start(1000)  # 每秒更新一次
            
            self.conversion_started.emit()
            
        except Exception as e:
            self.logger.error(tr('conversion_control.messages.start_conversion_failed', error=str(e)))
            QMessageBox.critical(self, tr('conversion_control.messages.error'), tr('conversion_control.messages.error_start_conversion', error=str(e)))
            self.reset_conversion_state()
    
    def pause_conversion(self):
        """暂停转换"""
        if not self.is_converting or self.is_paused:
            return
        
        if self.conversion_worker:
            self.conversion_worker.pause()
            self.is_paused = True
            self.pause_button.setText(tr('conversion_control.resume'))
            self.status_label.setText(tr('conversion_control.paused_status'))
            self.status_label.setStyleSheet("font-weight: bold; color: #ffc107;")
            self.status_text.append(tr('conversion_control.messages.conversion_paused'))
            self.conversion_paused.emit()
    
    def resume_conversion(self):
        """恢复转换"""
        if not self.is_converting or not self.is_paused:
            return
        
        if self.conversion_worker:
            self.conversion_worker.resume()
            self.is_paused = False
            self.pause_button.setText(tr('conversion_control.pause'))
            self.status_label.setText(tr('conversion_control.converting_status'))
            self.status_label.setStyleSheet("font-weight: bold; color: #007bff;")
            self.status_text.append(tr('conversion_control.messages.conversion_resumed'))
            self.conversion_resumed.emit()
    
    def stop_conversion(self):
        """停止转换"""
        if not self.is_converting:
            return
        
        if self.conversion_worker:
            self.conversion_worker.stop()
            self.conversion_worker.wait()
            self.conversion_worker = None
        
        # 停止进度估算器
        if self.progress_estimator:
            self.progress_estimator.stop_estimation(success=False)
            self.progress_estimator = None
        
        self.reset_conversion_state()
        self.status_text.append(tr('conversion_control.messages.conversion_stopped'))
        self.conversion_stopped.emit()
    
    def reset_conversion_state(self):
        """重置转换状态"""
        self.is_converting = False
        self.is_paused = False
        
        # 更新UI
        self.start_button.setEnabled(True)
        self.pause_button.setEnabled(False)
        self.pause_button.setText(tr('conversion_control.pause'))
        self.stop_button.setEnabled(False)
        
        self.status_label.setText(tr('conversion_control.ready_status'))
        self.status_label.setStyleSheet("font-weight: bold; color: #28a745;")
        
        self.timer.stop()
        if hasattr(self, 'start_time'):
            self.start_time = None
    
    def update_progress(self, current, total):
        """更新进度"""
        self.processed_segments = current
        self.current_progress = int((current / total) * 100) if total > 0 else 0
        
        self.overall_progress.setValue(self.current_progress)
        self.progress_label.setText(tr('conversion_control.conversion_progress_text', progress=self.current_progress))
        self.progress_info_label.setText(f"{current}/{total}")
        self.processed_segments_label.setText(tr('conversion_control.processed_segments', count=current))
    
    def update_status(self, status):
        """更新状态"""
        self.status_text.append(f"[{self.get_current_time()}] {status}")
    
    def on_segment_completed(self, segment_title, file_path):
        """段落完成"""
        self.audio_files.append(file_path)
        self.files_list.append(f"✓ {segment_title} -> {file_path}")
        self.current_segment_label.setText(segment_title)
    
    def on_conversion_completed(self, output_dir):
        """转换完成"""
        # 立即停止进度估算器
        if self.progress_estimator:
            self.progress_estimator.stop_estimation(success=True)
            self.progress_estimator = None
            self.logger.info(tr('conversion_control.messages.progress_estimator_stopped'))
        
        self.reset_conversion_state()
        self.status_text.append(f"[{self.get_current_time()}] {tr('conversion_control.messages.conversion_completed_full')}")
        self.status_text.append(tr('conversion_control.messages.output_directory_info', dir=output_dir))
        self.status_text.append(tr('conversion_control.messages.files_generated', count=len(self.audio_files)))
        
        self.conversion_completed.emit(output_dir)
        
        # 显示完成消息
        QMessageBox.information(self, tr('conversion_control.messages.conversion_completed'), tr('conversion_control.messages.success_conversion_completed', count=len(self.audio_files), dir=output_dir))
    
    def on_conversion_error(self, error_msg):
        """转换错误"""
        # 立即停止进度估算器
        if self.progress_estimator:
            self.progress_estimator.stop_estimation(success=False)
            self.progress_estimator = None
            self.logger.info(tr('conversion_control.messages.progress_estimator_stopped_error'))
        
        self.reset_conversion_state()
        self.status_text.append(f"[{self.get_current_time()}] {tr('conversion_control.messages.error')}: {error_msg}")
        # 记录错误到日志文件
        self.logger.error(tr('conversion_control.messages.conversion_error_log', error=error_msg))
        QMessageBox.critical(self, tr('conversion_control.messages.error_conversion'), error_msg)
    
    def update_remaining_time(self):
        """更新剩余时间"""
        if not self.is_converting or self.total_segments == 0:
            return
        
        if self.processed_segments > 0 and hasattr(self, 'start_time') and self.start_time:
            # 使用QElapsedTimer来计算经过的时间
            elapsed = self.start_time.elapsed() / 1000  # 秒
            avg_time_per_segment = elapsed / self.processed_segments
            remaining_segments = self.total_segments - self.processed_segments
            remaining_seconds = int(avg_time_per_segment * remaining_segments)
            
            hours = remaining_seconds // 3600
            minutes = (remaining_seconds % 3600) // 60
            seconds = remaining_seconds % 60
            
            if hours > 0:
                time_str = f"{hours:02d}:{minutes:02d}:{seconds:02d}"
            else:
                time_str = f"{minutes:02d}:{seconds:02d}"
            
            self.remaining_time_label.setText(tr('conversion_control.remaining_time_format', time=time_str))
    
    def get_current_time(self):
        """获取当前时间字符串"""
        from datetime import datetime
        return datetime.now().strftime("%H:%M:%S")
    
    def open_output_directory(self):
        """打开输出目录"""
        if self.output_dir_label.text() != tr('conversion_control.not_set'):
            import os
            import subprocess
            import platform
            
            # 获取显示的输出目录路径，并转换为系统路径格式
            output_dir = self.output_dir_label.text()
            # 将"/"分隔符转换为系统分隔符
            system_output_dir = output_dir.replace('/', os.sep)
            
            try:
                if os.path.exists(system_output_dir):
                    if platform.system() == "Windows":
                        os.startfile(system_output_dir)
                    elif platform.system() == "Darwin":  # macOS
                        subprocess.run(["open", system_output_dir])
                    else:  # Linux
                        subprocess.run(["xdg-open", system_output_dir])
                else:
                    # 创建目录如果不存在
                    try:
                        os.makedirs(system_output_dir, exist_ok=True)
                        if platform.system() == "Windows":
                            os.startfile(system_output_dir)
                        elif platform.system() == "Darwin":  # macOS
                            subprocess.run(["open", system_output_dir])
                        else:  # Linux
                            subprocess.run(["xdg-open", system_output_dir])
                    except Exception as e:
                        QMessageBox.warning(self, tr('conversion_control.messages.warning'), tr('conversion_control.messages.warning_cannot_create_output', error=str(e)))
            except Exception as e:
                QMessageBox.warning(self, tr('conversion_control.messages.warning'), tr('conversion_control.messages.warning_cannot_open_output', error=str(e)))
        else:
            QMessageBox.information(self, tr('conversion_control.messages.info'), tr('conversion_control.messages.info_start_conversion_first'))
    
    def on_progress_updated(self, progress):
        """进度更新回调（来自进度估算器）"""
        try:
            if self.progress_estimator and self.is_converting:
                # 更新总体进度条
                self.overall_progress.setValue(progress)
                
                # 更新进度信息
                self.progress_info_label.setText(f"{progress}%")
                
                self.logger.debug(tr('conversion_control.messages.progress_estimation_update', progress=progress))
                
        except Exception as e:
            self.logger.error(tr('conversion_control.messages.process_progress_update_failed', error=str(e)))
    
    def on_status_updated(self, status):
        """状态更新回调（来自进度估算器）"""
        try:
            if self.progress_estimator and self.is_converting:
                # 更新状态标签
                self.status_label.setText(status)
                self.status_label.setStyleSheet("font-weight: bold; color: #007bff;")
                
                self.logger.debug(tr('conversion_control.messages.status_update', status=status))
                
        except Exception as e:
            self.logger.error(tr('conversion_control.messages.process_status_update_failed', error=str(e)))
    
    def on_phase_changed(self, phase):
        """阶段变化回调（来自进度估算器）"""
        try:
            if self.progress_estimator and self.is_converting:
                # 更新状态文本，包含阶段信息
                current_status = self.status_label.text()
                if "阶段:" not in current_status:
                    self.status_label.setText(f"{current_status} - {tr('conversion_control.phase')}: {phase}")
                
                self.logger.info(tr('conversion_control.messages.phase_change', phase=phase))
                
        except Exception as e:
            self.logger.error(tr('conversion_control.messages.process_phase_change_failed', error=str(e)))
