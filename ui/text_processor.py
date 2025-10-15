"""
文本处理界面模块

提供文本处理和编辑功能，包括：
- 文本导入和显示
- 文本分段和章节管理
- 文本编辑和格式化
- 文本预览和验证
- 转换参数设置
- 历史记录管理（撤销/重做）

作者: TTS开发团队
版本: 1.0.0
创建时间: 2024
"""

import os
from PyQt6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QLabel, 
    QTextEdit, QPushButton, QComboBox, QSpinBox,
    QGroupBox, QSplitter, QListWidget, QListWidgetItem,
    QMessageBox, QProgressBar, QFrame, QScrollArea,
    QApplication, QDialog
)
from PyQt6.QtCore import Qt, pyqtSignal, QThread
from PyQt6.QtGui import QFont
from services.language_service import get_text as tr, get_language_service

from controllers.text_controller import TextController
from models.text_model import ProcessedText, Chapter
from models.audio_model import VoiceConfig
from utils.log_manager import LogManager


class TextProcessorWidget(QWidget):
    """
    文本处理界面组件
    
    提供完整的文本处理功能，包括文本导入、编辑、分段、预览等。
    支持多种文本格式的处理和转换参数配置。
    
    特性：
    - 多格式支持：支持TXT、PDF、DOCX等文本格式
    - 智能分段：自动识别章节和段落
    - 实时预览：支持文本处理结果实时预览
    - 历史管理：支持撤销/重做操作
    - 参数配置：支持转换参数的自定义设置
    """
    
    # 信号定义 - 用于与主窗口通信
    text_processed = pyqtSignal(str)  # 文本处理完成信号
    conversion_requested = pyqtSignal()  # 转换请求信号
    start_conversion_signal = pyqtSignal(list, object, object, object)  # 开始转换信号 (segments, voice_config, output_config, chapters)
    
    def __init__(self, text_controller: TextController):
        super().__init__()
        self.text_controller = text_controller
        self.logger = LogManager().get_logger("TextProcessorWidget")
        
        # 当前处理的文本
        self.current_text = ""
        self.processed_text = None
        
        # 当前语音配置
        self.current_voice_config = None
        
        # 当前输出配置
        self.current_output_config = None
        
        # 输出设置页面引用
        self.output_settings_widget = None
        
        # 文本历史记录（用于撤销重做）
        self.text_history = []
        self.history_index = -1
        self.is_modified = False
        
        # 初始化UI
        self.setup_ui()
        self.setup_connections()
        
        # 初始化时尝试获取输出配置
        self._try_load_initial_configs()
    
    def setup_ui(self):
        """设置用户界面"""
        layout = QVBoxLayout(self)
        layout.setContentsMargins(5, 5, 5, 5)
        layout.setSpacing(5)
        
        # 标题
        title_label = QLabel(tr("text_processing.title"))
        title_label.setStyleSheet("font-size: 16px; font-weight: bold; margin-bottom: 10px;")
        
        # 创建分割器
        splitterTop = QSplitter(Qt.Orientation.Vertical)
        splitterTop.setSizes([200,800])
        splitterTop.addWidget(title_label)
        layout.addWidget(splitterTop)

        # 创建水平分割器
        splitter = QSplitter(Qt.Orientation.Horizontal)
        splitterTop.addWidget(splitter)
        
        # 左侧：文本编辑区域
        left_widget = self.create_text_editor()
        splitter.addWidget(left_widget)
        
        # 右侧：处理选项和结果
        right_widget = self.create_processing_panel()
        splitter.addWidget(right_widget)
        
        # 设置分割器比例
        splitter.setSizes([650, 250])
    
    def create_text_editor(self):
        """创建文本编辑器"""
        widget = QFrame()
        widget.setFrameStyle(QFrame.Shape.StyledPanel)
        layout = QVBoxLayout(widget)
        layout.setContentsMargins(5, 5, 5, 5)
        
        # 主工具栏
        main_toolbar_layout = QHBoxLayout()
        
        # 文件操作按钮
        self.load_button = QPushButton(tr("text_processing.load_file"))
        self.load_button.clicked.connect(self.load_text)
        main_toolbar_layout.addWidget(self.load_button)
        
        self.load_sample_button = QPushButton(tr("text_processing.load_sample"))
        self.load_sample_button.clicked.connect(self.load_sample_text)
        main_toolbar_layout.addWidget(self.load_sample_button)
        
        self.save_button = QPushButton(tr("text_processing.save"))
        self.save_button.clicked.connect(self.save_text)
        main_toolbar_layout.addWidget(self.save_button)
        
        # 添加分隔符（使用空白标签）
        separator1 = QLabel("|")
        separator1.setStyleSheet("color: #ccc; margin: 0 5px;")
        main_toolbar_layout.addWidget(separator1)
        
        
        main_toolbar_layout.addStretch()
        
        # 统计信息
        self.stats_label = QLabel(f"{tr('text_processing.char_count')}: 0 | {tr('text_processing.word_count')}: 0 | {tr('text_processing.paragraph_count')}: 0")
        self.stats_label.setStyleSheet("color: #666; font-size: 12px;")
        main_toolbar_layout.addWidget(self.stats_label)
        
        layout.addLayout(main_toolbar_layout)
        
        # 编辑模式工具栏
        mode_toolbar_layout = QHBoxLayout()
        
        # 模式切换按钮
        self.edit_mode_button = QPushButton(tr("text_processing.edit_mode"))
        self.edit_mode_button.setCheckable(True)
        self.edit_mode_button.setChecked(True)
        self.edit_mode_button.clicked.connect(self.toggle_edit_mode)
        mode_toolbar_layout.addWidget(self.edit_mode_button)
        
        
        mode_toolbar_layout.addStretch()
        
        layout.addLayout(mode_toolbar_layout)
        
        # 文本编辑器
        self.text_edit = QTextEdit()
        self.text_edit.setFont(QFont("Consolas", 10))
        self.text_edit.textChanged.connect(self.on_text_changed)
        layout.addWidget(self.text_edit)
        
        return widget
    
    def create_processing_panel(self):
        """创建处理面板"""
        widget = QFrame()
        widget.setFrameStyle(QFrame.Shape.StyledPanel)
        layout = QVBoxLayout(widget)
        layout.setContentsMargins(5, 5, 5, 5)
        
        # 处理选项组
        options_group = QGroupBox(tr("text_processing.processing_options"))
        options_layout = QVBoxLayout(options_group)
        
        # 分割类型
        split_layout = QHBoxLayout()
        split_layout.addWidget(QLabel(tr("text_processing.split_type")))
        self.split_type_combo = QComboBox()
        # 使用固定的键值，避免语言切换后比较失败
        self.split_type_options = {
            "by_length": tr("text_processing.by_length"),
            "by_chapter": tr("text_processing.by_chapter"), 
            "by_paragraph": tr("text_processing.by_paragraph")
        }
        self.split_type_combo.addItems(list(self.split_type_options.values()))
        self.split_type_combo.currentTextChanged.connect(self.on_split_type_changed)
        split_layout.addWidget(self.split_type_combo)
        options_layout.addLayout(split_layout)
    
    def get_split_type_key(self, display_text):
        """根据显示文本获取分割类型键值"""
        for key, value in self.split_type_options.items():
            if value == display_text:
                return key
        return "by_length"  # 默认值
    
    def create_processing_panel(self):
        """创建处理面板"""
        widget = QFrame()
        widget.setFrameStyle(QFrame.Shape.StyledPanel)
        layout = QVBoxLayout(widget)
        layout.setContentsMargins(5, 5, 5, 5)
        
        # 处理选项组
        options_group = QGroupBox(tr("text_processing.processing_options"))
        options_layout = QVBoxLayout(options_group)
        
        # 分割类型
        split_layout = QHBoxLayout()
        split_layout.addWidget(QLabel(tr("text_processing.split_type")))
        self.split_type_combo = QComboBox()
        # 使用固定的键值，避免语言切换后比较失败
        self.split_type_options = {
            "by_length": tr("text_processing.by_length"),
            "by_chapter": tr("text_processing.by_chapter"), 
            "by_paragraph": tr("text_processing.by_paragraph")
        }
        self.split_type_combo.addItems(list(self.split_type_options.values()))
        self.split_type_combo.currentTextChanged.connect(self.on_split_type_changed)
        split_layout.addWidget(self.split_type_combo)
        options_layout.addLayout(split_layout)
        
        # 分割参数
        param_layout = QHBoxLayout()
        self.param_label = QLabel(tr("text_processing.max_length"))
        param_layout.addWidget(self.param_label)
        self.max_length_spin = QSpinBox()
        self.max_length_spin.setRange(0, 10000)
        self.max_length_spin.setValue(2000)
        self.max_length_spin.setSpecialValueText(tr("text_processing.no_split"))
        param_layout.addWidget(self.max_length_spin)
        options_layout.addLayout(param_layout)
        
        # 处理按钮
        self.process_button = QPushButton(tr("text_processing.process_text"))
        self.process_button.clicked.connect(self.process_text)
        options_layout.addWidget(self.process_button)
        
        layout.addWidget(options_group)
        
        # 章节列表组
        chapters_group = QGroupBox(tr("text_processing.chapter_management"))
        chapters_layout = QVBoxLayout(chapters_group)
        
        # 章节工具栏
        chapter_toolbar = QHBoxLayout()
        
        self.batch_process_button = QPushButton(tr("text_processing.batch_process"))
        self.batch_process_button.clicked.connect(self.batch_process_chapters)
        self.batch_process_button.setEnabled(False)
        chapter_toolbar.addWidget(self.batch_process_button)
        
        self.clear_chapters_button = QPushButton(tr("text_processing.clear_chapters"))
        self.clear_chapters_button.clicked.connect(self.clear_chapters)
        self.clear_chapters_button.setEnabled(False)
        chapter_toolbar.addWidget(self.clear_chapters_button)
        
        self.edit_chapter_title_button = QPushButton(tr("text_processing.edit_chapter_title"))
        self.edit_chapter_title_button.clicked.connect(self.edit_chapter)
        self.edit_chapter_title_button.setEnabled(False)
        chapter_toolbar.addWidget(self.edit_chapter_title_button)
        
        # 添加全选、全不选、导出按钮
        self.select_all_button = QPushButton(tr("text_processing.select_all"))
        self.select_all_button.clicked.connect(self.select_all_chapters)
        self.select_all_button.setEnabled(False)
        chapter_toolbar.addWidget(self.select_all_button)
        
        self.deselect_all_button = QPushButton(tr("text_processing.deselect_all"))
        self.deselect_all_button.clicked.connect(self.deselect_all_chapters)
        self.deselect_all_button.setEnabled(False)
        chapter_toolbar.addWidget(self.deselect_all_button)
        
        self.export_chapters_button = QPushButton(tr("text_processing.export"))
        self.export_chapters_button.clicked.connect(self.export_selected_chapters)
        self.export_chapters_button.setEnabled(False)
        chapter_toolbar.addWidget(self.export_chapters_button)
        
        chapter_toolbar.addStretch()
        chapters_layout.addLayout(chapter_toolbar)
        
        # 章节列表
        self.chapters_list = QListWidget()
        self.chapters_list.itemClicked.connect(self.on_chapter_clicked)
        self.chapters_list.itemDoubleClicked.connect(self.on_chapter_double_clicked)
        self.chapters_list.itemSelectionChanged.connect(self.on_chapter_selection_changed)
        chapters_layout.addWidget(self.chapters_list)
        
        # 转换音频按钮
        self.convert_audio_button = QPushButton(tr("text_processing.convert_audio"))
        self.convert_audio_button.clicked.connect(self.convert_selected_chapters_to_audio)
        self.convert_audio_button.setEnabled(False)
        chapters_layout.addWidget(self.convert_audio_button)
        
        layout.addWidget(chapters_group)
        
        # 进度条
        self.progress_bar = QProgressBar()
        self.progress_bar.setVisible(False)
        layout.addWidget(self.progress_bar)
        
        # 处理结果组
        results_group = QGroupBox(tr("text_processing.processing_results"))
        results_layout = QVBoxLayout(results_group)
        
        self.results_text = QTextEdit()
        self.results_text.setReadOnly(True)
        self.results_text.setMaximumHeight(150)
        results_layout.addWidget(self.results_text)
        
        layout.addWidget(results_group)
        
        return widget
    
    def setup_connections(self):
        """设置信号槽连接"""
        # 语言服务信号连接
        language_service = get_language_service()
        language_service.language_changed.connect(self.on_language_changed)
    
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
            current_text = self.text_edit.toPlainText() if hasattr(self, 'text_edit') else ""
            current_chapters = []
            if hasattr(self, 'chapter_list') and self.chapter_list:
                for i in range(self.chapter_list.count()):
                    current_chapters.append(self.chapter_list.item(i).text())
            
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
            
            # 重新设置分割类型选项
            self.split_type_options = {
                "by_length": tr("text_processing.by_length"),
                "by_chapter": tr("text_processing.by_chapter"), 
                "by_paragraph": tr("text_processing.by_paragraph")
            }
            
            # 恢复状态
            if hasattr(self, 'text_edit') and current_text:
                self.text_edit.setPlainText(current_text)
            if hasattr(self, 'chapter_list') and current_chapters:
                for chapter in current_chapters:
                    self.chapter_list.addItem(chapter)
            
            self.logger.info("文本处理界面语言切换完成")
        except Exception as e:
            self.logger.error(f"重新创建UI失败: {e}")
    
    def load_text(self):
        """加载文本"""
        try:
            from PyQt6.QtWidgets import QFileDialog
            
            # 打开文件对话框
            file_dialog = QFileDialog(self)
            file_dialog.setFileMode(QFileDialog.FileMode.ExistingFile)
            file_dialog.setNameFilter(
                tr("text_processing.file_dialog.supported_files")
            )
            file_dialog.setWindowTitle(tr("text_processing.file_dialog.select_file"))
            
            if file_dialog.exec():
                file_paths = file_dialog.selectedFiles()
                if file_paths:
                    file_path = file_paths[0]
                    self.load_file_content(file_path)
            
        except Exception as e:
            self.logger.error(tr("text_processing.messages.load_text_failed").format(error=e))
            QMessageBox.critical(self, tr("common.error"), tr("text_processing.messages.load_text_failed").format(error=e))
    
    def load_file_content(self, file_path: str):
        """加载文件内容"""
        try:
            from pathlib import Path
            from services.file_service import FileService
            
            # 检查文件是否存在
            if not Path(file_path).exists():
                QMessageBox.warning(self, tr("common.warning"), tr("text_processing.messages.file_not_exists"))
                return
            
            # 使用文件服务加载文件
            file_service = FileService()
            
            # 验证文件格式
            if not file_service.is_supported_format(file_path):
                QMessageBox.warning(self, tr("common.warning"), tr("text_processing.messages.unsupported_format"))
                return
            
            # 显示加载进度
            QMessageBox.information(self, tr("common.info"), tr("text_processing.messages.loading_file"))
            
            # 加载文件
            file_model = file_service.load_file(file_path)
            
            if file_model and file_model.content:
                # 设置文本内容
                self.text_edit.setPlainText(file_model.content)
                self.current_text = file_model.content
                
                # 设置当前文件名
                self.current_filename = file_model.file_name
                
                self.update_stats()
                
                # 显示文件信息
                file_info = f"文件: {file_model.file_name}\n"
                file_info += f"大小: {file_model.get_size_mb():.2f} MB\n"
                file_info += f"类型: {file_model.file_type}\n"
                file_info += f"字符数: {len(file_model.content)}"
                
                QMessageBox.information(self, tr("common.success"), tr("text_processing.messages.load_success").format(file_info=file_info))
                self.logger.info(f"文件加载成功: {file_path}")
                self.file_info = file_info
            else:
                QMessageBox.warning(self, tr("common.warning"), tr("text_processing.messages.file_content_empty"))
                
        except Exception as e:
            self.logger.error(f"加载文件内容失败: {e}")
            QMessageBox.critical(self, tr("common.error"), tr("text_processing.messages.load_file_content_failed").format(error=e))
    
    def load_sample_text(self):
        """加载示例文本"""
        try:
            sample_text = """
第一章 开始

这是一个示例文本，用于演示文本处理功能。

第二章 内容

这里包含更多的文本内容，用于测试文本分割和章节识别功能。

第三章 结束

这是最后一个章节，用于完成整个文本处理流程。
            """
            
            self.text_edit.setPlainText(sample_text)
            self.current_text = sample_text
            
            # 设置当前文件名
            self.current_filename = "示例文本.txt"
            
            self.update_stats()
            
            self.logger.info("示例文本已加载")
            
        except Exception as e:
            self.logger.error(f"加载示例文本失败: {e}")
            QMessageBox.critical(self, tr("common.error"), tr("text_processing.messages.load_sample_failed").format(error=e))
    
    def clear_text(self):
        """清空文本"""
        try:
            self.text_edit.clear()
            self.current_text = ""
            self.processed_text = None
            self.chapters_list.clear()
            self.results_text.clear()
            self.update_stats()
            
        except Exception as e:
            self.logger.error(f"清空文本失败: {e}")
    
    def on_text_changed(self):
        """文本改变事件"""
        try:
            self.current_text = self.text_edit.toPlainText()
            
            # 如果没有设置文件名，设置一个默认的文件名
            if not hasattr(self, 'current_filename') or not self.current_filename:
                self.current_filename = "无标题-3000.txt"
            
            self.update_stats()
            self.save_to_history()
            self.is_modified = True
            self.update_save_button()
            
        except Exception as e:
            self.logger.error(f"处理文本改变事件失败: {e}")
    
    def save_to_history(self):
        """保存到历史记录"""
        try:
            current_state = self.text_edit.toPlainText()
            if self.history_index < len(self.text_history) - 1:
                # 如果在历史记录中间，删除后面的记录
                self.text_history = self.text_history[:self.history_index + 1]
            
            if not self.text_history or self.text_history[-1] != current_state:
                self.text_history.append(current_state)
                self.history_index = len(self.text_history) - 1
                
                # 限制历史记录数量
                if len(self.text_history) > 50:
                    self.text_history.pop(0)
                    self.history_index -= 1
                
                
        except Exception as e:
            self.logger.error(f"保存历史记录失败: {e}")
    
    
    def save_text(self):
        """保存文本"""
        try:
            from PyQt6.QtWidgets import QFileDialog
            
            if not self.current_text.strip():
                QMessageBox.information(self, tr("common.info"), tr("text_processing.messages.no_content_to_save"))
                return
            
            # 打开保存对话框
            file_dialog = QFileDialog(self)
            file_dialog.setFileMode(QFileDialog.FileMode.AnyFile)
            file_dialog.setAcceptMode(QFileDialog.AcceptMode.AcceptSave)
            file_dialog.setNameFilter("文本文件 (*.txt);;所有文件 (*.*)")
            file_dialog.setWindowTitle("保存文本文件")
            
            if file_dialog.exec():
                file_paths = file_dialog.selectedFiles()
                if file_paths:
                    file_path = file_paths[0]
                    with open(file_path, 'w', encoding='utf-8') as f:
                        f.write(self.current_text)
                    
                    QMessageBox.information(self, tr("common.success"), tr("text_processing.messages.file_saved").format(file_path=file_path))
                    self.is_modified = False
                    self.update_save_button()
                    self.logger.info(f"文本已保存: {file_path}")
                    
                    # 保存后进入预览模式
                    self.edit_mode_button.setChecked(False)
                    self.toggle_edit_mode()
            
        except Exception as e:
            self.logger.error(f"保存文本失败: {e}")
            QMessageBox.critical(self, tr("common.error"), tr("text_processing.messages.save_text_failed").format(error=e))
    
    def update_save_button(self):
        """更新保存按钮状态"""
        try:
            if self.is_modified:
                self.save_button.setText("保存*")
                self.save_button.setStyleSheet("QPushButton { background-color: #e74c3c; }")
            else:
                self.save_button.setText("保存")
                self.save_button.setStyleSheet("")
                
        except Exception as e:
            self.logger.error(f"更新保存按钮失败: {e}")
    
    def show_find_replace_dialog(self):
        """显示查找替换对话框"""
        try:
            from PyQt6.QtWidgets import QDialog, QVBoxLayout, QHBoxLayout, QLabel, QLineEdit, QPushButton, QCheckBox
            
            dialog = QDialog(self)
            dialog.setWindowTitle("查找和替换")
            dialog.setModal(True)
            dialog.resize(400, 200)
            
            layout = QVBoxLayout(dialog)
            
            # 查找
            find_layout = QHBoxLayout()
            find_layout.addWidget(QLabel("查找:"))
            self.find_edit = QLineEdit()
            find_layout.addWidget(self.find_edit)
            layout.addLayout(find_layout)
            
            # 替换
            replace_layout = QHBoxLayout()
            replace_layout.addWidget(QLabel("替换:"))
            self.replace_edit = QLineEdit()
            replace_layout.addWidget(self.replace_edit)
            layout.addLayout(replace_layout)
            
            # 选项
            self.case_sensitive_check = QCheckBox("区分大小写")
            layout.addWidget(self.case_sensitive_check)
            
            # 按钮
            button_layout = QHBoxLayout()
            
            find_btn = QPushButton("查找下一个")
            find_btn.clicked.connect(self.find_next)
            button_layout.addWidget(find_btn)
            
            replace_btn = QPushButton("替换")
            replace_btn.clicked.connect(self.replace_current)
            button_layout.addWidget(replace_btn)
            
            replace_all_btn = QPushButton("全部替换")
            replace_all_btn.clicked.connect(self.replace_all)
            button_layout.addWidget(replace_all_btn)
            
            close_btn = QPushButton("关闭")
            close_btn.clicked.connect(dialog.accept)
            button_layout.addWidget(close_btn)
            
            layout.addLayout(button_layout)
            
            dialog.exec()
            
        except Exception as e:
            self.logger.error(f"显示查找替换对话框失败: {e}")
    
    def find_next(self):
        """查找下一个"""
        try:
            find_text = self.find_edit.text()
            if not find_text:
                return
            
            # 获取当前光标位置
            cursor = self.text_edit.textCursor()
            start_pos = cursor.position()
            
            # 设置搜索标志
            flags = 0
            if self.case_sensitive_check.isChecked():
                flags |= 0x00000001  # QTextDocument.FindFlag.FindCaseSensitively
            
            # 从当前位置开始查找
            found = self.text_edit.find(find_text, flags)
            
            if not found:
                # 如果没找到，从头开始查找
                cursor.setPosition(0)
                self.text_edit.setTextCursor(cursor)
                found = self.text_edit.find(find_text, flags)
                
                if not found:
                    QMessageBox.information(self, tr("common.info"), tr("text_processing.messages.no_matching_text"))
            
        except Exception as e:
            self.logger.error(f"查找下一个失败: {e}")
    
    def replace_current(self):
        """替换当前"""
        try:
            find_text = self.find_edit.text()
            replace_text = self.replace_edit.text()
            
            if not find_text:
                return
            
            cursor = self.text_edit.textCursor()
            if cursor.hasSelection():
                cursor.insertText(replace_text)
                self.save_to_history()
                self.is_modified = True
                self.update_save_button()
            
        except Exception as e:
            self.logger.error(f"替换当前失败: {e}")
    
    def replace_all(self):
        """全部替换"""
        try:
            find_text = self.find_edit.text()
            replace_text = self.replace_edit.text()
            
            if not find_text:
                return
            
            # 获取当前文本
            text = self.text_edit.toPlainText()
            
            # 设置替换标志
            if self.case_sensitive_check.isChecked():
                # 区分大小写
                new_text = text.replace(find_text, replace_text)
            else:
                # 不区分大小写
                import re
                pattern = re.escape(find_text)
                new_text = re.sub(pattern, replace_text, text, flags=re.IGNORECASE)
            
            # 计算替换次数
            if self.case_sensitive_check.isChecked():
                count = text.count(find_text)
            else:
                count = len(re.findall(re.escape(find_text), text, re.IGNORECASE))
            
            if count > 0:
                # 更新文本
                self.text_edit.setPlainText(new_text)
                self.current_text = new_text
                self.save_to_history()
                self.is_modified = True
                self.update_save_button()
                self.update_stats()
                
                QMessageBox.information(self, tr("common.success"), tr("text_processing.messages.replaced_count").format(count=count))
            else:
                QMessageBox.information(self, tr("common.info"), tr("text_processing.messages.no_matching_text"))
            
        except Exception as e:
            self.logger.error(f"全部替换失败: {e}")
    
    def toggle_edit_mode(self):
        """切换编辑模式"""
        try:
            if self.edit_mode_button.isChecked():
                # 进入编辑模式
                self.text_edit.setReadOnly(False)
                self.text_edit.setStyleSheet("background-color: #fafbfc;")
                self.edit_mode_button.setText("预览模式")
                self.logger.info("切换到编辑模式")
            else:
                # 进入预览模式
                self.text_edit.setReadOnly(True)
                self.text_edit.setStyleSheet("background-color: #f8f9fa;")
                self.edit_mode_button.setText("编辑模式")
                self.logger.info("切换到预览模式")
                
        except Exception as e:
            self.logger.error(f"切换编辑模式失败: {e}")
    
    def batch_process_chapters(self):
        """批量处理选中的章节"""
        try:
            # 获取选中的章节
            selected_chapters = []
            if self.processed_text and self.processed_text.chapters:
                for chapter in self.processed_text.chapters:
                    if chapter.selected:
                        selected_chapters.append(chapter)
            
            if not selected_chapters:
                QMessageBox.information(self, tr("common.info"), tr("text_processing.messages.please_select_chapters"))
                return
            
            # 显示批量处理对话框
            from PyQt6.QtWidgets import QDialog, QVBoxLayout, QLabel, QPushButton, QHBoxLayout, QTextEdit
            
            dialog = QDialog(self)
            dialog.setWindowTitle("批量处理章节")
            dialog.setModal(True)
            dialog.resize(400, 200)
            
            layout = QVBoxLayout(dialog)
            
            # 显示选中的章节
            info_label = QLabel(f"已选择 {len(selected_chapters)} 个章节进行批量处理")
            layout.addWidget(info_label)
            
            # 章节列表
            chapters_text = QTextEdit()
            chapters_text.setReadOnly(True)
            chapters_text.setMaximumHeight(100)
            chapters_list = "\n".join([f"• {chapter.title}" for chapter in selected_chapters])
            chapters_text.setPlainText(chapters_list)
            layout.addWidget(chapters_text)
            
            # 按钮
            button_layout = QHBoxLayout()
            button_layout.addStretch()
            
            cancel_button = QPushButton("取消")
            cancel_button.clicked.connect(dialog.reject)
            button_layout.addWidget(cancel_button)
            
            process_button = QPushButton("开始处理")
            process_button.clicked.connect(dialog.accept)
            button_layout.addWidget(process_button)
            
            layout.addLayout(button_layout)
            
            if dialog.exec() == QDialog.DialogCode.Accepted:
                # 开始批量处理
                self.start_batch_processing(selected_chapters)
                
        except Exception as e:
            self.logger.error(f"批量处理章节失败: {e}")
            QMessageBox.critical(self, tr("common.error"), tr("text_processing.messages.batch_process_failed").format(error=e))
    
    def start_batch_processing(self, chapters):
        """开始批量处理"""
        try:
            # 这里可以调用批量处理控制器
            QMessageBox.information(self, "批量处理", f"开始批量处理 {len(chapters)} 个章节")
            self.logger.info(f"开始批量处理 {len(chapters)} 个章节")
            
        except Exception as e:
            self.logger.error(f"开始批量处理失败: {e}")
            QMessageBox.critical(self, "错误", f"开始批量处理失败: {e}")
    
    def clear_chapters(self):
        """清空章节"""
        try:
            reply = QMessageBox.question(
                self, 
                "确认清空", 
                "确定要清空所有章节吗？此操作不可撤销。",
                QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No
            )
            
            if reply == QMessageBox.StandardButton.Yes:
                self.chapters_list.clear()
                if self.processed_text:
                    self.processed_text.chapters.clear()
                
                # 更新按钮状态
                self.update_batch_process_button()
                
                # 清空处理结果
                self.results_text.clear()
                
                self.logger.info("章节已清空")
                QMessageBox.information(self, "成功", "章节已清空")
                
        except Exception as e:
            self.logger.error(f"清空章节失败: {e}")
            QMessageBox.critical(self, "错误", f"清空章节失败: {e}")
    
    def convert_selected_chapters_to_audio(self):
        """转换选中的章节为音频"""
        try:
            # 获取选中的章节
            selected_chapters = []
            for i in range(self.chapters_list.count()):
                item = self.chapters_list.item(i)
                if item.text().startswith("☑"):
                    chapter_index = item.data(Qt.ItemDataRole.UserRole)
                    if chapter_index is not None and self.processed_text and self.processed_text.chapters:
                        selected_chapters.append(self.processed_text.chapters[chapter_index])
            
            if not selected_chapters:
                QMessageBox.information(self, "提示", "请先选择要转换的章节")
                return
            
            # 显示转换确认对话框
            from PyQt6.QtWidgets import QDialog, QVBoxLayout, QLabel, QPushButton, QHBoxLayout, QTextEdit
            
            dialog = QDialog(self)
            dialog.setWindowTitle("转换选中章节为音频")
            dialog.setModal(True)
            dialog.resize(500, 300)
            
            layout = QVBoxLayout(dialog)
            
            # 显示选中的章节
            info_label = QLabel(f"已选择 {len(selected_chapters)} 个章节进行音频转换")
            layout.addWidget(info_label)
            
            # 章节列表
            chapters_text = QTextEdit()
            chapters_text.setReadOnly(True)
            chapters_text.setMaximumHeight(150)
            chapters_list = "\n".join([f"• {chapter.title}" for chapter in selected_chapters])
            chapters_text.setPlainText(chapters_list)
            layout.addWidget(chapters_text)
            
            # 按钮
            button_layout = QHBoxLayout()
            button_layout.addStretch()
            
            cancel_button = QPushButton("取消")
            cancel_button.clicked.connect(dialog.reject)
            button_layout.addWidget(cancel_button)
            
            convert_button = QPushButton("开始转换")
            convert_button.clicked.connect(dialog.accept)
            button_layout.addWidget(convert_button)
            
            layout.addLayout(button_layout)
            
            if dialog.exec() == QDialog.DialogCode.Accepted:
                # 开始转换
                self.start_audio_conversion_with_chapters(selected_chapters)
                
        except Exception as e:
            self.logger.error(f"转换选中章节为音频失败: {e}")
            QMessageBox.critical(self, "错误", f"转换选中章节为音频失败: {e}")
    
    def start_audio_conversion_with_chapters(self, chapters):
        """开始音频转换（章节版本）"""
        try:
            if not chapters:
                QMessageBox.information(self, "提示", "没有选择要转换的章节")
                return
            
            # 修复：将章节转换为包含完整信息的字典格式
            segments = []
            for i, chapter in enumerate(chapters):
                if chapter.content.strip():
                    # 从章节标题中提取章节号，如果没有则使用索引+1
                    chapter_num = self._extract_chapter_number(chapter.title, i + 1)
                    
                    segment_data = {
                        'content': chapter.content.strip(),
                        'title': chapter.title,
                        'chapter_num': chapter_num,
                        'selected': True,
                        'original_filename': getattr(self, 'current_filename', 'unknown_file.txt')
                    }
                    segments.append(segment_data)
            
            if not segments:
                QMessageBox.information(self, "提示", "选中的章节没有内容")
                return
            
            # 使用当前语音配置，如果没有则创建默认配置
            from models.audio_model import VoiceConfig, OutputConfig
            
            if self.current_voice_config:
                # 使用当前语音配置
                voice_config = self.current_voice_config
                self.logger.info(f"使用当前语音配置: 引擎={voice_config.engine}, 语音={voice_config.voice_name}")
            else:
                # 创建默认配置
                voice_config = VoiceConfig(
                    engine="piper_tts",
                    voice_name="zh_CN-huayan-medium",
                    rate=1.0,
                    pitch=1.0,
                    volume=1.0
                )
                self.logger.info("使用默认语音配置")
            
            # 优先从输出设置页面获取最新配置
            if self.output_settings_widget:
                try:
                    output_config = self.output_settings_widget.get_output_config()
                    if output_config:
                        self.logger.info(f"从输出设置页面获取配置: 命名模式={output_config.naming_mode}")
                    else:
                        raise Exception("输出设置页面返回空配置")
                except Exception as e:
                    self.logger.warning(f"从输出设置页面获取配置失败: {e}")
                    output_config = None
            
            # 如果从输出设置页面获取失败，使用当前缓存的配置
            if not output_config and self.current_output_config:
                output_config = self.current_output_config
                self.logger.info(f"使用缓存的输出配置: 命名模式={output_config.naming_mode}")
            
            # 如果都没有，创建默认配置
            if not output_config:
                output_config = OutputConfig()
                output_config.output_dir = "./output"
                output_config.format = "wav"
                output_config.bitrate = 128
                output_config.sample_rate = 44100
                output_config.channels = 2
                self.logger.info("使用默认输出配置")
            
            # 发送转换请求信号，传递选中的章节信息
            self.conversion_requested.emit()
            self.start_conversion_signal.emit(segments, voice_config, output_config, chapters)
            
            self.logger.info(f"开始转换 {len(chapters)} 个章节为音频，共 {len(segments)} 个分段")
            
        except Exception as e:
            self.logger.error(f"开始音频转换失败: {e}")
            QMessageBox.critical(self, "错误", f"开始音频转换失败: {e}")
    
    def _extract_chapter_number(self, title: str, default_num: int) -> int:
        """从章节标题中提取章节号"""
        try:
            import re
            
            # 尝试匹配各种章节号格式
            patterns = [
                r'第(\d+)章',  # 第一章、第二章
                r'第(\d+)节',  # 第一节、第二节
                r'第(\d+)部分', # 第一部分、第二部分
                r'分段\s*(\d+)', # 分段 1、分段 2、分段 08
                r'^(\d+)\.',   # 1. 2. 3. (开头)
                r'^(\d+)\s*[、，]', # 1、 2、 3、 (开头)
                r'^(\d+)\s',   # 开头的数字
            ]
            
            for pattern in patterns:
                match = re.search(pattern, title)
                if match:
                    return int(match.group(1))
            
            # 如果没有找到，返回默认值
            return default_num
            
        except Exception as e:
            self.logger.warning(f"提取章节号失败: {e}")
            return default_num
    
    
    def update_stats(self):
        """更新统计信息"""
        try:
            if not self.current_text:
                self.stats_label.setText("字符数: 0 | 词数: 0 | 段落: 0")
                return
            
            char_count = len(self.current_text)
            word_count = len(self.current_text.split())
            paragraph_count = len([p for p in self.current_text.split('\n\n') if p.strip()])
            
            self.stats_label.setText(f"字符数: {char_count} | 词数: {word_count} | 段落: {paragraph_count}")
            
        except Exception as e:
            self.logger.error(f"更新统计信息失败: {e}")
    
    def process_text(self):
        """处理文本"""
        try:
            if not self.current_text.strip():
                QMessageBox.information(self, tr("common.info"), tr("text_processing.messages.please_input_text"))
                return
            
            # 显示进度条
            self.progress_bar.setVisible(True)
            self.progress_bar.setRange(0, 0)
            
            # 获取用户设置的分割参数
            split_type = self.split_type_combo.currentText()
            max_length = self.max_length_spin.value()
            
            # 根据分割类型处理文本
            split_type_key = self.get_split_type_key(split_type)
            if split_type_key == "by_length":
                # 先清理文本
                cleaned_text = self.text_controller.clean_text(self.current_text)
                
                # 检查是否不分割（最大长度为0）
                if max_length == 0:
                    # 不分割，直接将所有文本作为一个章节
                    from models.text_model import Chapter
                    chapter = Chapter(
                        title="完整文本",
                        content=cleaned_text,
                        start_pos=0,
                        end_pos=len(cleaned_text),
                        original_filename=getattr(self, 'current_filename', 'unknown_file.txt')
                    )
                    chapters = [chapter]
                    self.logger.info("最大长度设置为0，不分割文本，直接作为一个章节")
                else:
                    # 按长度分割文本
                    segments = self.text_controller.split_text_by_length(cleaned_text, max_length)
                    
                    # 为每个分段创建章节信息
                    from models.text_model import Chapter
                    chapters = []
                    current_pos = 0
                    for i, segment in enumerate(segments):
                        # 在原始文本中查找分段位置
                        segment_start = self.current_text.find(segment, current_pos)
                        if segment_start == -1:
                            segment_start = current_pos
                        segment_end = segment_start + len(segment)
                        
                        chapter = Chapter(
                            title=f"分段 {i+1}",
                            content=segment,
                            start_pos=segment_start,
                            end_pos=segment_end,
                            original_filename=getattr(self, 'current_filename', 'unknown_file.txt')
                        )
                        chapters.append(chapter)
                        current_pos = segment_end
                
                # 创建处理后的文本对象
                from models.text_model import ProcessedText
                self.processed_text = ProcessedText(
                    original_text=self.current_text,
                    cleaned_text=cleaned_text,
                    chapters=chapters,
                    segments=segments,
                    word_count=len(cleaned_text.split()),
                    char_count=len(cleaned_text)
                )
            elif split_type_key == "by_chapter":
                # 按章节分割
                chapters = self.text_controller.split_text_by_chapters(self.current_text)
                cleaned_text = self.text_controller.clean_text(self.current_text)
                
                # 按章节分割文本，每个章节作为一个分段
                segments = []
                for chapter in chapters:
                    # 获取章节内容
                    chapter_text = self.current_text[chapter.start_pos:chapter.end_pos]
                    # 清理章节内容
                    cleaned_chapter = self.text_controller.clean_text(chapter_text)
                    segments.append(cleaned_chapter)
                
                from models.text_model import ProcessedText
                self.processed_text = ProcessedText(
                    original_text=self.current_text,
                    cleaned_text=cleaned_text,
                    chapters=chapters,
                    segments=segments,
                    word_count=len(cleaned_text.split()),
                    char_count=len(cleaned_text)
                )
            elif split_type_key == "by_paragraph":
                # 按段落分割
                segments = self.text_controller.split_text_by_paragraphs(self.current_text)
                cleaned_text = self.text_controller.clean_text(self.current_text)
                
                # 为每个段落创建章节信息
                from models.text_model import Chapter
                chapters = []
                current_pos = 0
                for i, segment in enumerate(segments):
                    # 在原始文本中查找段落位置
                    segment_start = self.current_text.find(segment, current_pos)
                    if segment_start == -1:
                        segment_start = current_pos
                    segment_end = segment_start + len(segment)
                    
                    chapter = Chapter(
                        title=f"段落 {i+1}",
                        content=segment,
                        start_pos=segment_start,
                        end_pos=segment_end
                    )
                    chapters.append(chapter)
                    current_pos = segment_end
                
                from models.text_model import ProcessedText
                self.processed_text = ProcessedText(
                    original_text=self.current_text,
                    cleaned_text=cleaned_text,
                    chapters=chapters,
                    segments=segments,
                    word_count=len(cleaned_text.split()),
                    char_count=len(cleaned_text)
                )
            else:
                # 使用默认处理
                self.processed_text = self.text_controller.process_text(self.current_text)
            
            # 更新章节列表
            self.update_chapters_list()
            
            # 更新结果
            self.update_results()
            
            # 启用转换音频按钮
            self.convert_audio_button.setEnabled(True)
            
            # 隐藏进度条
            self.progress_bar.setVisible(False)
            
            # 发送信号
            self.text_processed.emit(self.current_text)
            
            self.logger.info(f"文本处理完成，分割类型: {split_type}, 分段数: {len(self.processed_text.segments)}")
            
        except Exception as e:
            self.progress_bar.setVisible(False)
            self.logger.error(f"处理文本失败: {e}")
            QMessageBox.critical(self, tr("common.error"), tr("text_processing.messages.process_text_failed").format(error=e))
    
    def update_chapters_list(self):
        """更新章节列表"""
        try:
            self.chapters_list.clear()
            
            if not self.processed_text or not self.processed_text.chapters:
                return
            
            for i, chapter in enumerate(self.processed_text.chapters):
                # 限制章节标题显示为20个字符
                display_title = chapter.title[:20] + "..." if len(chapter.title) > 20 else chapter.title
                
                # 根据选择状态显示不同的checkbox
                checkbox = "☑" if chapter.selected else "☐"
                item = QListWidgetItem(f"{checkbox} {i+1}. {display_title}")
                item.setData(Qt.ItemDataRole.UserRole, i)
                # 设置工具提示显示完整标题
                item.setToolTip(f"完整标题: {chapter.title}")
                self.chapters_list.addItem(item)
            
            # 更新按钮状态
            self.update_batch_process_button()
                
        except Exception as e:
            self.logger.error(f"更新章节列表失败: {e}")
    
    def update_results(self):
        """更新处理结果"""
        try:
            if not self.processed_text:
                return
            
            results = []
            results.append(f"原始文本长度: {len(self.processed_text.original_text)}")
            results.append(f"清理后长度: {len(self.processed_text.cleaned_text)}")
            results.append(f"章节数: {len(self.processed_text.chapters)}")
            results.append(f"分段数: {len(self.processed_text.segments)}")
            results.append(f"词数: {self.processed_text.word_count}")
            results.append(f"字符数: {self.processed_text.char_count}")
            
            self.results_text.setPlainText("\n".join(results))
            
        except Exception as e:
            self.logger.error(f"更新处理结果失败: {e}")
    
    def on_chapter_clicked(self, item: QListWidgetItem):
        """章节点击事件 - 切换checkbox状态"""
        try:
            # 使用定时器延迟处理单击事件，避免与双击事件冲突
            from PyQt6.QtCore import QTimer
            QTimer.singleShot(200, lambda: self._handle_chapter_click(item))
            
        except Exception as e:
            self.logger.error(f"处理章节点击事件失败: {e}")
    
    def _handle_chapter_click(self, item: QListWidgetItem):
        """处理章节点击事件（延迟执行）"""
        try:
            # 获取章节索引
            chapter_index = self.chapters_list.row(item)
            
            if 0 <= chapter_index < len(self.processed_text.chapters):
                # 切换选择状态
                self.toggle_chapter_selection(chapter_index)
            
        except Exception as e:
            self.logger.error(f"处理章节点击事件失败: {e}")
    
    def toggle_chapter_selection(self, chapter_index: int):
        """切换章节选择状态"""
        try:
            if 0 <= chapter_index < len(self.processed_text.chapters):
                chapter = self.processed_text.chapters[chapter_index]
                
                # 切换选择状态
                chapter.selected = not chapter.selected
                
                # 更新显示
                self.update_chapters_list()
                
                # 更新按钮状态
                self.update_batch_process_button()
                
                self.logger.info(f"章节 {chapter.title} 选择状态: {chapter.selected}")
            
        except Exception as e:
            self.logger.error(f"切换章节选择状态失败: {e}")
    
    def on_chapter_double_clicked(self, item: QListWidgetItem):
        """章节双击事件 - 打开章节内容预览"""
        try:
            chapter_index = item.data(Qt.ItemDataRole.UserRole)
            if chapter_index is not None and self.processed_text and self.processed_text.chapters:
                chapter = self.processed_text.chapters[chapter_index]
                self.logger.info(f"双击章节: {chapter.title}")
                self.show_chapter_preview(chapter)
            else:
                self.logger.warning(f"双击事件：无效的章节索引 {chapter_index}")
                
        except Exception as e:
            self.logger.error(f"处理章节双击事件失败: {e}")
            import traceback
            traceback.print_exc()
    
    def show_chapter_preview(self, chapter):
        """显示章节内容预览"""
        try:
            dialog = QDialog(self)
            dialog.setWindowTitle(f"章节预览: {chapter.title}")
            dialog.setModal(True)
            dialog.resize(600, 400)
            
            layout = QVBoxLayout(dialog)
            
            # 章节标题
            title_label = QLabel(f"章节: {chapter.title}")
            title_label.setStyleSheet("font-weight: bold; font-size: 14px; margin-bottom: 10px;")
            layout.addWidget(title_label)
            
            # 章节信息
            info_label = QLabel(f"位置: {chapter.start_pos}-{chapter.end_pos} | 长度: {len(chapter.content)} 字符")
            info_label.setStyleSheet("color: #666; font-size: 12px; margin-bottom: 10px;")
            layout.addWidget(info_label)
            
            # 章节内容
            content_text = QTextEdit()
            content_text.setPlainText(chapter.content if chapter.content else "章节内容为空")
            content_text.setReadOnly(True)
            layout.addWidget(content_text)
            
            # 按钮
            button_layout = QHBoxLayout()
            button_layout.addStretch()
            
            close_button = QPushButton("关闭")
            close_button.clicked.connect(dialog.accept)
            button_layout.addWidget(close_button)
            
            layout.addLayout(button_layout)
            
            dialog.exec()
            
        except Exception as e:
            self.logger.error(f"显示章节预览失败: {e}")
            QMessageBox.critical(self, "错误", f"显示章节预览失败: {e}")
    
    def update_batch_process_button(self):
        """更新批量处理按钮状态"""
        try:
            # 检查是否有选中的章节
            has_selected = False
            if self.processed_text and self.processed_text.chapters:
                for chapter in self.processed_text.chapters:
                    if chapter.selected:
                        has_selected = True
                        break
            
            self.batch_process_button.setEnabled(has_selected)
            self.convert_audio_button.setEnabled(has_selected)
            self.export_chapters_button.setEnabled(has_selected)
            
            # 全选和全不选按钮状态
            has_chapters = self.chapters_list.count() > 0
            self.select_all_button.setEnabled(has_chapters)
            self.deselect_all_button.setEnabled(has_chapters)
            
            # 清空章节按钮状态
            self.clear_chapters_button.setEnabled(has_chapters)
            
            # 修改标题按钮状态
            self.edit_chapter_title_button.setEnabled(has_chapters)
            
        except Exception as e:
            self.logger.error(f"更新批量处理按钮状态失败: {e}")
    
    def select_all_chapters(self):
        """全选章节"""
        try:
            for i in range(self.chapters_list.count()):
                item = self.chapters_list.item(i)
                if not item.text().startswith("☑"):
                    # 切换选择状态
                    self.toggle_chapter_selection(i)
            
            self.logger.info("已全选所有章节")
            
        except Exception as e:
            self.logger.error(f"全选章节失败: {e}")
            QMessageBox.critical(self, "错误", f"全选章节失败: {e}")
    
    def deselect_all_chapters(self):
        """全不选章节"""
        try:
            for i in range(self.chapters_list.count()):
                item = self.chapters_list.item(i)
                if item.text().startswith("☑"):
                    # 切换选择状态
                    self.toggle_chapter_selection(i)
            
            self.logger.info("已取消选择所有章节")
            
        except Exception as e:
            self.logger.error(f"全不选章节失败: {e}")
            QMessageBox.critical(self, "错误", f"全不选章节失败: {e}")
    
    def export_selected_chapters(self):
        """导出选中的章节"""
        try:
            if not self.processed_text or not self.processed_text.chapters:
                QMessageBox.information(self, "提示", "没有可导出的章节")
                return
            
            # 获取选中的章节
            selected_chapters = []
            for i, chapter in enumerate(self.processed_text.chapters):
                if chapter.selected:
                    selected_chapters.append((i, chapter))
            
            if not selected_chapters:
                QMessageBox.information(self, "提示", "请先选择要导出的章节")
                return
            
            # 选择导出目录
            from PyQt6.QtWidgets import QFileDialog
            export_dir = QFileDialog.getExistingDirectory(self, "选择导出目录")
            if not export_dir:
                return
            
            # 导出选中的章节
            exported_count = 0
            for i, chapter in selected_chapters:
                try:
                    # 创建文件名（使用章节名称清理器）
                    from utils.chapter_name_cleaner import clean_chapter_name
                    safe_title = clean_chapter_name(chapter.title)
                    filename = f"{i+1:03d}_{safe_title}.txt"
                    filepath = os.path.join(export_dir, filename)
                    
                    # 写入文件
                    with open(filepath, 'w', encoding='utf-8') as f:
                        f.write(f"标题: {chapter.title}\n")
                        f.write(f"位置: {chapter.start_pos}-{chapter.end_pos}\n")
                        f.write(f"长度: {len(chapter.content)} 字符\n")
                        f.write("-" * 50 + "\n")
                        f.write(chapter.content)
                    
                    exported_count += 1
                    
                except Exception as e:
                    self.logger.error(f"导出章节 {chapter.title} 失败: {e}")
                    continue
            
            if exported_count > 0:
                QMessageBox.information(self, "成功", f"已成功导出 {exported_count} 个章节到:\n{export_dir}")
                self.logger.info(f"已导出 {exported_count} 个章节到: {export_dir}")
            else:
                QMessageBox.warning(self, "警告", "没有成功导出任何章节")
            
        except Exception as e:
            self.logger.error(f"导出章节失败: {e}")
            QMessageBox.critical(self, "错误", f"导出章节失败: {e}")
    
    def on_split_type_changed(self, split_type):
        """分割类型改变事件"""
        try:
            split_type_key = self.get_split_type_key(split_type)
            if split_type_key == "by_length":
                self.param_label.setText("最大长度:")
                self.max_length_spin.setVisible(True)
                self.max_length_spin.setRange(0, 10000)
                self.max_length_spin.setValue(2000)
                self.max_length_spin.setSpecialValueText("不分割")
            elif split_type_key == "by_chapter":
                self.param_label.setText("章节标记:")
                self.max_length_spin.setVisible(False)
            elif split_type_key == "by_paragraph":
                self.param_label.setText("段落分隔:")
                self.max_length_spin.setVisible(False)
            
            self.logger.info(f"分割类型已更改为: {split_type}")
            
        except Exception as e:
            self.logger.error(f"更新分割类型失败: {e}")
    
    def on_chapter_selection_changed(self):
        """章节选择改变事件"""
        try:
            # 更新批量处理按钮状态
            self.update_batch_process_button()
            
        except Exception as e:
            self.logger.error(f"处理章节选择改变事件失败: {e}")
    
    def add_chapter(self):
        """添加章节"""
        try:
            from PyQt6.QtWidgets import QInputDialog
            
            title, ok = QInputDialog.getText(self, "添加章节", "请输入章节标题:")
            if not ok or not title.strip():
                return
            
            # 在文本末尾添加新章节
            if self.current_text:
                new_text = self.current_text + f"\n\n{title}\n\n"
            else:
                new_text = f"{title}\n\n"
            
            self.text_edit.setPlainText(new_text)
            self.current_text = new_text
            self.save_to_history()
            self.is_modified = True
            self.update_save_button()
            self.update_stats()
            
            # 重新处理文本以更新章节列表
            self.process_text()
            
            QMessageBox.information(self, "成功", f"章节 '{title}' 已添加")
            self.logger.info(f"添加章节: {title}")
            
        except Exception as e:
            self.logger.error(f"添加章节失败: {e}")
            QMessageBox.critical(self, "错误", f"添加章节失败: {e}")
    
    def edit_chapter(self):
        """编辑章节"""
        try:
            current_item = self.chapters_list.currentItem()
            if not current_item:
                QMessageBox.information(self, "提示", "请先选择要编辑的章节")
                return
            
            chapter_index = current_item.data(Qt.ItemDataRole.UserRole)
            if chapter_index is None or not self.processed_text:
                return
            
            # 获取当前章节标题
            current_title = self.processed_text.chapters[chapter_index].title
            
            from PyQt6.QtWidgets import QInputDialog
            new_title, ok = QInputDialog.getText(
                self, "编辑章节", "请输入新的章节标题:", text=current_title
            )
            
            if not ok or not new_title.strip() or new_title == current_title:
                return
            
            # 更新章节标题
            self.processed_text.chapters[chapter_index].title = new_title
            
            # 更新章节列表显示
            self.update_chapters_list()
            
            QMessageBox.information(self, "成功", f"章节标题已更新为: {new_title}")
            self.logger.info(f"编辑章节: {current_title} -> {new_title}")
            
        except Exception as e:
            self.logger.error(f"编辑章节失败: {e}")
            QMessageBox.critical(self, "错误", f"编辑章节失败: {e}")
    
    def split_chapter(self):
        """分割章节"""
        try:
            current_item = self.chapters_list.currentItem()
            if not current_item:
                QMessageBox.information(self, "提示", "请先选择要分割的章节")
                return
            
            chapter_index = current_item.data(Qt.ItemDataRole.UserRole)
            if chapter_index is None or not self.processed_text:
                return
            
            # 获取章节内容
            chapter = self.processed_text.chapters[chapter_index]
            chapter_text = self.processed_text.get_chapter_text(chapter_index)
            
            if len(chapter_text) < 1000:
                QMessageBox.information(self, "提示", "章节内容太短，无需分割")
                return
            
            from PyQt6.QtWidgets import QInputDialog
            max_length, ok = QInputDialog.getInt(
                self, "分割章节", "请输入分割长度:", 2000, 500, 10000
            )
            
            if not ok:
                return
            
            # 分割章节内容
            segments = self.text_controller.split_text_by_length(chapter_text, max_length)
            
            if len(segments) <= 1:
                QMessageBox.information(self, "提示", "分割后仍为一段，无需分割")
                return
            
            # 更新章节列表
            # 删除原章节
            del self.processed_text.chapters[chapter_index]
            
            # 添加新的分割章节
            for i, segment in enumerate(segments):
                new_chapter = Chapter(
                    title=f"{chapter.title} - 第{i+1}段",
                    start_pos=chapter.start_pos + i * max_length,
                    end_pos=chapter.start_pos + (i + 1) * max_length
                )
                self.processed_text.chapters.insert(chapter_index + i, new_chapter)
            
            # 更新显示
            self.update_chapters_list()
            
            QMessageBox.information(self, "成功", f"章节已分割为 {len(segments)} 段")
            self.logger.info(f"分割章节: {chapter.title} -> {len(segments)} 段")
            
        except Exception as e:
            self.logger.error(f"分割章节失败: {e}")
            QMessageBox.critical(self, "错误", f"分割章节失败: {e}")
    
    def delete_chapter(self):
        """删除章节"""
        try:
            current_item = self.chapters_list.currentItem()
            if not current_item:
                QMessageBox.information(self, "提示", "请先选择要删除的章节")
                return
            
            chapter_index = current_item.data(Qt.ItemDataRole.UserRole)
            if chapter_index is None or not self.processed_text:
                return
            
            # 确认删除
            chapter_title = self.processed_text.chapters[chapter_index].title
            reply = QMessageBox.question(
                self, "确认删除", 
                f"确定要删除章节 '{chapter_title}' 吗？\n此操作不可撤销。",
                QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No
            )
            
            if reply != QMessageBox.StandardButton.Yes:
                return
            
            # 删除章节
            del self.processed_text.chapters[chapter_index]
            
            # 更新显示
            self.update_chapters_list()
            
            QMessageBox.information(self, "成功", f"章节 '{chapter_title}' 已删除")
            self.logger.info(f"删除章节: {chapter_title}")
            
        except Exception as e:
            self.logger.error(f"删除章节失败: {e}")
            QMessageBox.critical(self, "错误", f"删除章节失败: {e}")
    
    def get_processed_text(self) -> ProcessedText:
        """获取处理后的文本"""
        return self.processed_text
    
    def get_current_text(self) -> str:
        """获取当前文本"""
        return self.current_text
    
    def set_voice_config(self, voice_config):
        """设置当前语音配置"""
        self.current_voice_config = voice_config
        self.logger.info(f"设置语音配置: 引擎={voice_config.engine}, 语音={voice_config.voice_name}")
    
    def set_output_config(self, output_config):
        """设置当前输出配置"""
        self.current_output_config = output_config
        self.logger.info(f"设置输出配置: 命名模式={output_config.naming_mode}")
    
    def set_output_settings_widget(self, output_settings_widget):
        """设置输出设置页面引用"""
        self.output_settings_widget = output_settings_widget
        self.logger.info("设置输出设置页面引用")
    
    def _try_load_initial_configs(self):
        """尝试加载初始配置"""
        try:
            # 尝试从配置服务加载输出配置
            from services.json_config_service import JsonConfigService
            config_service = JsonConfigService()
            
            # 加载输出配置
            output_config = config_service.load_output_config()
            if output_config:
                self.current_output_config = output_config
                self.logger.info(f"初始化时加载输出配置: 命名模式={output_config.naming_mode}")
            
            # 加载语音配置
            voice_config = config_service.load_voice_config()
            if voice_config:
                self.current_voice_config = voice_config
                self.logger.info(f"初始化时加载语音配置: 引擎={voice_config.engine}")
                
        except Exception as e:
            self.logger.warning(f"初始化时加载配置失败: {e}")
    
    def set_text(self, text: str):
        """设置文本"""
        try:
            self.text_edit.setPlainText(text)
            self.current_text = text
            self.update_stats()
            
        except Exception as e:
            self.logger.error(f"设置文本失败: {e}")
    
    def get_split_segments(self) -> list:
        """获取分割后的段落"""
        try:
            if not self.processed_text:
                return []
            
            split_type = self.split_type_combo.currentText()
            max_length = self.max_length_spin.value()
            
            split_type_key = self.get_split_type_key(split_type)
            if split_type_key == "by_length":
                if max_length == 0:
                    # 不分割，返回完整文本
                    return [self.current_text]
                else:
                    return self.text_controller.split_text_by_length(self.current_text, max_length)
            elif split_type_key == "by_chapter":
                chapters = self.text_controller.split_text_by_chapters(self.current_text)
                return [chapter.title for chapter in chapters]
            elif split_type_key == "by_paragraph":
                return self.text_controller.split_text_by_paragraphs(self.current_text)
            else:
                return []
                
        except Exception as e:
            self.logger.error(f"获取分割段落失败: {e}")
            return []
    
    def convert_to_audio(self):
        """转换音频"""
        try:
            if not self.processed_text or not self.processed_text.segments:
                QMessageBox.information(self, "提示", "请先处理文本")
                return
            
            # 显示音频转换对话框
            from PyQt6.QtWidgets import QDialog, QVBoxLayout, QHBoxLayout, QLabel, QComboBox, QSlider, QPushButton, QSpinBox
            from PyQt6.QtCore import Qt
            
            dialog = QDialog(self)
            dialog.setWindowTitle("音频转换设置")
            dialog.setModal(True)
            dialog.resize(400, 300)
            
            layout = QVBoxLayout(dialog)
            
            # TTS引擎选择
            engine_layout = QHBoxLayout()
            engine_layout.addWidget(QLabel("TTS引擎:"))
            engine_combo = QComboBox()
            engine_combo.addItems(["Edge TTS", "Windows SAPI", "Piper TTS"])
            engine_combo.setCurrentText("Edge TTS")
            engine_layout.addWidget(engine_combo)
            layout.addLayout(engine_layout)
            
            # 语音选择
            voice_layout = QHBoxLayout()
            voice_layout.addWidget(QLabel("语音:"))
            voice_combo = QComboBox()
            voice_combo.addItems(["zh-CN-XiaoxiaoNeural", "zh-CN-YunxiNeural", "zh-CN-YunyangNeural"])
            voice_layout.addWidget(voice_combo)
            layout.addLayout(voice_layout)
            
            # 语速设置
            rate_layout = QHBoxLayout()
            rate_layout.addWidget(QLabel("语速:"))
            rate_slider = QSlider(Qt.Orientation.Horizontal)
            rate_slider.setRange(50, 200)
            rate_slider.setValue(100)
            rate_label = QLabel("100%")
            rate_slider.valueChanged.connect(lambda v: rate_label.setText(f"{v}%"))
            rate_layout.addWidget(rate_slider)
            rate_layout.addWidget(rate_label)
            layout.addLayout(rate_layout)
            
            # 音调设置
            pitch_layout = QHBoxLayout()
            pitch_layout.addWidget(QLabel("音调:"))
            pitch_slider = QSlider(Qt.Orientation.Horizontal)
            pitch_slider.setRange(50, 200)
            pitch_slider.setValue(100)
            pitch_label = QLabel("100%")
            pitch_slider.valueChanged.connect(lambda v: pitch_label.setText(f"{v}%"))
            pitch_layout.addWidget(pitch_slider)
            pitch_layout.addWidget(pitch_label)
            layout.addLayout(pitch_layout)
            
            # 音量设置
            volume_layout = QHBoxLayout()
            volume_layout.addWidget(QLabel("音量:"))
            volume_slider = QSlider(Qt.Orientation.Horizontal)
            volume_slider.setRange(50, 200)
            volume_slider.setValue(100)
            volume_label = QLabel("100%")
            volume_slider.valueChanged.connect(lambda v: volume_label.setText(f"{v}%"))
            volume_layout.addWidget(volume_slider)
            volume_layout.addWidget(volume_label)
            layout.addLayout(volume_layout)
            
            # 按钮
            button_layout = QHBoxLayout()
            convert_btn = QPushButton("开始转换")
            cancel_btn = QPushButton("取消")
            button_layout.addWidget(convert_btn)
            button_layout.addWidget(cancel_btn)
            layout.addLayout(button_layout)
            
            # 连接信号
            convert_btn.clicked.connect(dialog.accept)
            cancel_btn.clicked.connect(dialog.reject)
            
            # 显示对话框
            if dialog.exec() == QDialog.DialogCode.Accepted:
                # 创建语音配置
                voice_config = VoiceConfig(
                    engine=engine_combo.currentText(),
                    voice_name=voice_combo.currentText(),
                    rate=rate_slider.value() / 100.0,
                    pitch=pitch_slider.value() / 100.0,
                    volume=volume_slider.value() / 100.0
                )
                
                # 创建输出配置
                from models.audio_model import OutputConfig
                output_config = OutputConfig()
                output_config.output_dir = "./output"
                output_config.format = "mp3"
                output_config.bitrate = 128
                output_config.sample_rate = 44100
                output_config.channels = 2
                
                # 切换到转换控制标签页并开始转换
                self.conversion_requested.emit()
                self.start_conversion_signal.emit(self.processed_text.segments, voice_config, output_config, self.processed_text.chapters)
                
        except Exception as e:
            self.logger.error(f"转换音频失败: {e}")
            QMessageBox.critical(self, "错误", f"转换音频失败: {e}")
    
    def start_audio_conversion(self, voice_config: VoiceConfig):
        """开始音频转换"""
        try:
            from PyQt6.QtWidgets import QFileDialog
            from pathlib import Path
            
            # 选择保存路径
            save_path, _ = QFileDialog.getSaveFileName(
                self, 
                "保存音频文件", 
                f"audio_{Path(self.current_text[:20]).stem}.mp3",
                "音频文件 (*.mp3 *.wav);;MP3文件 (*.mp3);;WAV文件 (*.wav)"
            )
            
            if not save_path:
                return
            
            # 显示进度
            self.progress_bar.setVisible(True)
            self.progress_bar.setRange(0, len(self.processed_text.segments))
            self.progress_bar.setValue(0)
            
            # 创建TTS服务
            from services.tts_service import TTSService
            tts_service = TTSService()
            
            # 转换每个分段
            audio_files = []
            for i, segment in enumerate(self.processed_text.segments):
                try:
                    # 生成音频文件
                    temp_file = f"temp_segment_{i}.wav"
                    output_path = tts_service.synthesize_text(segment, voice_config, temp_file)
                    
                    if output_path and os.path.exists(output_path):
                        audio_files.append(output_path)
                    else:
                        self.logger.error(f"音频文件生成失败: {temp_file}")
                        continue
                    
                    # 更新进度
                    self.progress_bar.setValue(i + 1)
                    QApplication.processEvents()
                    
                except Exception as e:
                    self.logger.error(f"转换分段 {i} 失败: {e}")
                    continue
            
            # 合并音频文件
            if audio_files:
                from services.audio_service import AudioService
                audio_service = AudioService()
                
                # 合并所有音频
                merged_audio = audio_service.merge_audio_files(audio_files)
                
                # 保存最终文件
                with open(save_path, 'wb') as f:
                    f.write(merged_audio)
                
                # 清理临时文件
                for temp_file in audio_files:
                    try:
                        Path(temp_file).unlink()
                    except:
                        pass
                
                # 隐藏进度条
                self.progress_bar.setVisible(False)
                
                QMessageBox.information(self, "成功", f"音频转换完成！\n保存路径: {save_path}")
                self.logger.info(f"音频转换完成: {save_path}")
            else:
                self.progress_bar.setVisible(False)
                QMessageBox.warning(self, "警告", "没有成功转换任何音频")
                
        except Exception as e:
            self.progress_bar.setVisible(False)
            self.logger.error(f"音频转换失败: {e}")
            QMessageBox.critical(self, "错误", f"音频转换失败: {e}")
