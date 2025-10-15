"""
文件管理界面
"""

from PyQt6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QLabel, 
    QPushButton, QListWidget, QListWidgetItem, QFileDialog,
    QMessageBox, QProgressBar, QFrame, QScrollArea
)
from PyQt6.QtCore import Qt, pyqtSignal, QThread, QMimeData
from PyQt6.QtGui import QDragEnterEvent, QDropEvent, QIcon, QPixmap

from controllers.file_controller import FileController
from models.file_model import FileModel
from utils.log_manager import LogManager
from services.language_service import get_text as tr


class FileManagerWidget(QWidget):
    """文件管理界面"""
    
    # 信号定义
    file_selected = pyqtSignal(str)  # 文件选择信号
    file_imported = pyqtSignal(str)  # 文件导入信号
    
    def __init__(self, file_controller: FileController):
        super().__init__()
        self.file_controller = file_controller
        self.logger = LogManager().get_logger("FileManagerWidget")
        
        # 文件列表
        self.file_models = []
        
        # 初始化UI
        self.setup_ui()
        self.setup_connections()
        
        # 启用拖拽
        self.setAcceptDrops(True)
    
    def setup_ui(self):
        """设置用户界面"""
        layout = QVBoxLayout(self)
        layout.setContentsMargins(5, 5, 5, 5)
        layout.setSpacing(5)
        
        # 标题
        title_label = QLabel(tr("file_manager.title"))
        title_label.setStyleSheet("font-size: 16px; font-weight: bold; margin-bottom: 10px;")
        layout.addWidget(title_label)
        
        # 按钮区域
        button_layout = QHBoxLayout()
        
        # 导入文件按钮
        self.import_button = QPushButton(tr("file_manager.import_file"))
        self.import_button.setIcon(QIcon("resources/icons/upload.svg"))
        self.import_button.clicked.connect(self.import_file)
        button_layout.addWidget(self.import_button)
        
        # 清除按钮
        self.clear_button = QPushButton(tr("file_manager.clear"))
        self.clear_button.clicked.connect(self.clear_files)
        button_layout.addWidget(self.clear_button)
        
        layout.addLayout(button_layout)
        
        # 文件列表
        self.file_list = QListWidget()
        self.file_list.setAlternatingRowColors(True)
        self.file_list.itemClicked.connect(self.on_file_clicked)
        layout.addWidget(self.file_list)
        
        # 进度条
        self.progress_bar = QProgressBar()
        self.progress_bar.setVisible(False)
        layout.addWidget(self.progress_bar)
        
        # 文件信息区域
        self.file_info_frame = QFrame()
        self.file_info_frame.setFrameStyle(QFrame.Shape.StyledPanel)
        self.file_info_frame.setVisible(False)
        layout.addWidget(self.file_info_frame)
        
        self.setup_file_info()
    
    def setup_file_info(self):
        """设置文件信息区域"""
        info_layout = QVBoxLayout(self.file_info_frame)
        
        # 文件信息标签
        self.file_info_label = QLabel(tr("file_manager.file_info"))
        self.file_info_label.setStyleSheet("font-weight: bold; margin-bottom: 5px;")
        info_layout.addWidget(self.file_info_label)
        
        # 文件详情
        self.file_details = QLabel()
        self.file_details.setWordWrap(True)
        self.file_details.setStyleSheet("font-size: 12px; color: #666;")
        info_layout.addWidget(self.file_details)
        
        # 操作按钮
        button_layout = QHBoxLayout()
        
        self.preview_button = QPushButton(tr("file_manager.preview"))
        self.preview_button.clicked.connect(self.preview_file)
        button_layout.addWidget(self.preview_button)
        
        self.remove_button = QPushButton(tr("file_manager.remove"))
        self.remove_button.clicked.connect(self.remove_file)
        button_layout.addWidget(self.remove_button)
        
        info_layout.addLayout(button_layout)
    
    def setup_connections(self):
        """设置信号槽连接"""
        pass
    
    def dragEnterEvent(self, event: QDragEnterEvent):
        """拖拽进入事件"""
        if event.mimeData().hasUrls():
            event.acceptProposedAction()
        else:
            event.ignore()
    
    def dropEvent(self, event: QDropEvent):
        """拖拽放下事件"""
        try:
            urls = event.mimeData().urls()
            file_paths = [url.toLocalFile() for url in urls if url.isLocalFile()]
            
            for file_path in file_paths:
                self.add_file(file_path)
            
            event.acceptProposedAction()
            
        except Exception as e:
            self.logger.error(f"处理拖拽文件失败: {e}")
            QMessageBox.critical(self, tr("file_manager.messages.error"), tr("file_manager.messages.drag_drop_failed", error=str(e)))
    
    def import_file(self):
        """导入文件"""
        try:
            file_dialog = QFileDialog(self)
            file_dialog.setFileMode(QFileDialog.FileMode.ExistingFiles)
            file_dialog.setNameFilter(
                f"{tr('file_manager.file_filters.supported_files')};;"
                f"{tr('file_manager.file_filters.text_files')};;"
                f"{tr('file_manager.file_filters.pdf_files')};;"
                f"{tr('file_manager.file_filters.epub_files')};;"
                f"{tr('file_manager.file_filters.word_files')};;"
                f"{tr('file_manager.file_filters.markdown_files')};;"
                f"{tr('file_manager.file_filters.all_files')}"
            )
            
            if file_dialog.exec():
                file_paths = file_dialog.selectedFiles()
                for file_path in file_paths:
                    self.add_file(file_path)
                    
        except Exception as e:
            self.logger.error(f"导入文件失败: {e}")
            QMessageBox.critical(self, tr("file_manager.messages.error"), tr("file_manager.messages.import_failed", error=str(e)))
    
    def add_file(self, file_path: str):
        """添加文件"""
        try:
            # 检查文件是否已存在
            for file_model in self.file_models:
                if file_model.file_path == file_path:
                    QMessageBox.information(self, tr("file_manager.messages.info"), tr("file_manager.messages.file_exists"))
                    return
            
            # 验证文件
            if not self.file_controller.validate_file(file_path):
                QMessageBox.warning(self, tr("file_manager.messages.warning"), tr("file_manager.messages.unsupported_format"))
                return
            
            # 显示进度条
            self.progress_bar.setVisible(True)
            self.progress_bar.setRange(0, 0)  # 不确定进度
            
            # 导入文件
            file_model = self.file_controller.import_file(file_path)
            self.file_models.append(file_model)
            
            # 添加到列表
            self.add_file_to_list(file_model)
            
            # 隐藏进度条
            self.progress_bar.setVisible(False)
            
            # 发送信号
            self.file_imported.emit(file_path)
            
            self.logger.info(f"文件添加成功: {file_path}")
            
        except Exception as e:
            self.progress_bar.setVisible(False)
            self.logger.error(f"添加文件失败: {e}")
            QMessageBox.critical(self, tr("file_manager.messages.error"), tr("file_manager.messages.add_file_failed", error=str(e)))
    
    def add_file_to_list(self, file_model: FileModel):
        """添加文件到列表"""
        try:
            item = QListWidgetItem()
            item.setText(file_model.file_name)
            item.setData(Qt.ItemDataRole.UserRole, file_model)
            
            # 设置图标
            icon = self.get_file_icon(file_model.file_type)
            if icon:
                item.setIcon(icon)
            
            # 设置工具提示
            tooltip = f"{tr('file_manager.file_info.file')}: {file_model.file_name}\n"
            tooltip += f"{tr('file_manager.file_info.size')}: {file_model.get_size_mb():.2f} {tr('file_manager.file_info.mb')}\n"
            tooltip += f"{tr('file_manager.file_info.type')}: {file_model.file_type}\n"
            tooltip += f"{tr('file_manager.file_info.path')}: {file_model.file_path}"
            item.setToolTip(tooltip)
            
            self.file_list.addItem(item)
            
        except Exception as e:
            self.logger.error(f"添加文件到列表失败: {e}")
    
    def get_file_icon(self, file_type: str) -> QIcon:
        """获取文件图标"""
        icon_map = {
            '.txt': QIcon("resources/icons/file.svg"),
            '.pdf': QIcon("resources/icons/file.svg"),
            '.epub': QIcon("resources/icons/file.svg"),
            '.docx': QIcon("resources/icons/file.svg"),
            '.md': QIcon("resources/icons/file.svg")
        }
        return icon_map.get(file_type, QIcon("resources/icons/file.svg"))
    
    def on_file_clicked(self, item: QListWidgetItem):
        """文件点击事件"""
        try:
            file_model = item.data(Qt.ItemDataRole.UserRole)
            if file_model:
                self.show_file_info(file_model)
                self.file_selected.emit(file_model.file_path)
                
                # 如果文件有内容，自动加载到文本处理器
                if file_model.content:
                    self.load_file_to_text_processor(file_model)
                
        except Exception as e:
            self.logger.error(f"处理文件点击事件失败: {e}")
    
    def load_file_to_text_processor(self, file_model: FileModel):
        """将文件内容加载到文本处理器"""
        try:
            # 发送文件内容到文本处理器
            # 这里可以通过信号发送文件内容
            self.file_content_loaded = file_model.content
            self.logger.info(f"文件内容已准备加载到文本处理器: {file_model.file_name}")
            
        except Exception as e:
            self.logger.error(f"加载文件到文本处理器失败: {e}")
    
    def show_file_info(self, file_model: FileModel):
        """显示文件信息"""
        try:
            info_text = f"{tr('file_manager.file_info.file_name')}: {file_model.file_name}\n"
            info_text += f"{tr('file_manager.file_info.size')}: {file_model.get_size_mb():.2f} {tr('file_manager.file_info.mb')}\n"
            info_text += f"{tr('file_manager.file_info.type')}: {file_model.file_type}\n"
            info_text += f"{tr('file_manager.file_info.created_time')}: {file_model.created_time.strftime('%Y-%m-%d %H:%M:%S')}\n"
            info_text += f"{tr('file_manager.file_info.modified_time')}: {file_model.modified_time.strftime('%Y-%m-%d %H:%M:%S')}\n"
            info_text += f"{tr('file_manager.file_info.path')}: {file_model.file_path}"
            
            self.file_details.setText(info_text)
            self.file_info_frame.setVisible(True)
            
        except Exception as e:
            self.logger.error(f"显示文件信息失败: {e}")
    
    def preview_file(self):
        """预览文件"""
        try:
            current_item = self.file_list.currentItem()
            if not current_item:
                QMessageBox.information(self, tr("file_manager.messages.info"), tr("file_manager.messages.select_file_first"))
                return
            
            file_model = current_item.data(Qt.ItemDataRole.UserRole)
            if not file_model:
                return
            
            # 获取文件预览
            preview_text = self.file_controller.get_file_preview(file_model.file_path)
            
            # 显示预览对话框
            from PyQt6.QtWidgets import QDialog, QTextEdit, QVBoxLayout, QPushButton
            
            dialog = QDialog(self)
            dialog.setWindowTitle(tr("file_manager.preview.title", file_name=file_model.file_name))
            dialog.setModal(True)
            dialog.resize(600, 400)
            
            layout = QVBoxLayout(dialog)
            
            text_edit = QTextEdit()
            text_edit.setPlainText(preview_text)
            text_edit.setReadOnly(True)
            layout.addWidget(text_edit)
            
            close_button = QPushButton(tr("file_manager.close"))
            close_button.clicked.connect(dialog.accept)
            layout.addWidget(close_button)
            
            dialog.exec()
            
        except Exception as e:
            self.logger.error(f"预览文件失败: {e}")
            QMessageBox.critical(self, tr("file_manager.messages.error"), tr("file_manager.messages.preview_failed", error=str(e)))
    
    def remove_file(self):
        """移除文件"""
        try:
            current_item = self.file_list.currentItem()
            if not current_item:
                QMessageBox.information(self, tr("file_manager.messages.info"), tr("file_manager.messages.select_file_first"))
                return
            
            # 确认删除
            reply = QMessageBox.question(
                self, tr("file_manager.messages.confirm"), tr("file_manager.messages.remove_confirm"),
                QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No
            )
            
            if reply == QMessageBox.StandardButton.Yes:
                file_model = current_item.data(Qt.ItemDataRole.UserRole)
                if file_model:
                    self.file_models.remove(file_model)
                
                self.file_list.takeItem(self.file_list.row(current_item))
                self.file_info_frame.setVisible(False)
                
                self.logger.info(f"文件移除成功: {file_model.file_name if file_model else 'Unknown'}")
                
        except Exception as e:
            self.logger.error(f"移除文件失败: {e}")
            QMessageBox.critical(self, tr("file_manager.messages.error"), tr("file_manager.messages.remove_failed", error=str(e)))
    
    def clear_files(self):
        """清除所有文件"""
        try:
            if not self.file_models:
                QMessageBox.information(self, tr("file_manager.messages.info"), tr("file_manager.messages.no_files_to_clear"))
                return
            
            # 确认清除
            reply = QMessageBox.question(
                self, tr("file_manager.messages.confirm"), tr("file_manager.messages.clear_confirm"),
                QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No
            )
            
            if reply == QMessageBox.StandardButton.Yes:
                self.file_models.clear()
                self.file_list.clear()
                self.file_info_frame.setVisible(False)
                
                self.logger.info("所有文件已清除")
                
        except Exception as e:
            self.logger.error(f"清除文件失败: {e}")
            QMessageBox.critical(self, tr("file_manager.messages.error"), tr("file_manager.messages.clear_failed", error=str(e)))
    
    def get_selected_file(self) -> FileModel:
        """获取选中的文件"""
        try:
            current_item = self.file_list.currentItem()
            if current_item:
                return current_item.data(Qt.ItemDataRole.UserRole)
            return None
        except Exception as e:
            self.logger.error(f"获取选中文件失败: {e}")
            return None
    
    def get_all_files(self) -> list:
        """获取所有文件"""
        return self.file_models.copy()
    
    def get_file_count(self) -> int:
        """获取文件数量"""
        return len(self.file_models)
