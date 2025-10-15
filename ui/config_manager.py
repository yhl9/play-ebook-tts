"""
配置管理界面模块

提供统一的配置管理界面，包括：
- 应用程序配置管理
- 引擎配置管理
- 配置验证和修复
- 配置备份和恢复
- 配置导入导出

作者: TTS开发团队
版本: 2.0.0
创建时间: 2024
"""

from PyQt6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QTabWidget,
    QLabel, QPushButton, QTableWidget, QTableWidgetItem,
    QGroupBox, QFormLayout, QLineEdit, QSpinBox, QDoubleSpinBox,
    QComboBox, QCheckBox, QTextEdit, QMessageBox, QProgressBar,
    QSplitter, QTreeWidget, QTreeWidgetItem, QHeaderView,
    QProgressDialog, QDialog, QListWidget, QFileDialog
)
from PyQt6.QtCore import Qt, pyqtSignal, QThread, QTimer
from PyQt6.QtGui import QFont, QIcon, QColor
import time
from typing import Dict, Any
from services.language_service import get_text as tr

from services.config.app_config_service import AppConfigService
from services.config.engine_config_service import EngineConfigService
from services.config.config_validator import ConfigValidator
from services.config.config_backup import ConfigBackup
from services.config.engine_manager import EngineManager
from services.config.config_template_manager import ConfigTemplateManager
from services.config.config_monitor import ConfigMonitor
from models.config_models import EngineConfig, EngineStatusEnum
from utils.log_manager import LogManager


class ConfigManagerWidget(QWidget):
    """
    配置管理界面组件
    
    提供完整的配置管理功能，包括应用程序配置、引擎配置、
    配置验证、备份恢复等功能。
    """
    
    # 信号定义
    config_changed = pyqtSignal(str)  # 配置变更信号
    
    def __init__(self):
        super().__init__()
        self.logger = LogManager().get_logger("ConfigManager")
        
        # 配置服务
        self.app_config_service = AppConfigService()
        self.engine_config_service = EngineConfigService()
        self.engine_manager = EngineManager()
        self.config_validator = ConfigValidator()
        self.config_backup = ConfigBackup()
        self.template_manager = ConfigTemplateManager()
        self.config_monitor = ConfigMonitor()
        
        # 当前配置
        self.app_config = None
        self.engine_registry = None
        
        # 初始化UI
        self.setup_ui()
        self.load_config()
        

        # self.refresh_engine_status()
        # 定时刷新
        # self.refresh_timer = QTimer()
        # self.refresh_timer.timeout.connect(self.refresh_engine_status)
        # self.refresh_timer.start(5000)  # 每5秒刷新一次
    
    def setup_ui(self):
        """设置UI界面"""
        layout = QVBoxLayout()
        
        # 创建标签页
        self.tab_widget = QTabWidget()
        
        # 应用程序配置标签页
        self.app_config_tab = self.create_app_config_tab()
        self.tab_widget.addTab(self.app_config_tab, tr('config_manager.app_config'))
        
        # 引擎配置标签页
        self.engine_config_tab = self.create_engine_config_tab()
        self.tab_widget.addTab(self.engine_config_tab, tr('config_manager.engine_config'))
        
        # 配置验证标签页
        self.validation_tab = self.create_validation_tab()
        self.tab_widget.addTab(self.validation_tab, tr('config_manager.validation'))
        
        # 备份管理标签页
        self.backup_tab = self.create_backup_tab()
        self.tab_widget.addTab(self.backup_tab, tr('config_manager.backup_management'))
        
        # 模板管理标签页
        self.template_tab = self.create_template_tab()
        self.tab_widget.addTab(self.template_tab, tr('config_manager.template_management'))
        
        # 监控诊断标签页
        self.monitor_tab = self.create_monitor_tab()
        self.tab_widget.addTab(self.monitor_tab, tr('config_manager.monitor_diagnosis'))
        
        layout.addWidget(self.tab_widget)
        
        # 底部按钮
        button_layout = QHBoxLayout()
        
        self.save_button = QPushButton(tr('config_manager.save_config'))
        self.save_button.clicked.connect(self.save_config)
        
        self.reload_button = QPushButton(tr('config_manager.reload'))
        self.reload_button.clicked.connect(self.load_config)
        
        self.reset_button = QPushButton(tr('config_manager.reset_to_default'))
        self.reset_button.clicked.connect(self.reset_config)
        
        button_layout.addWidget(self.save_button)
        button_layout.addWidget(self.reload_button)
        button_layout.addWidget(self.reset_button)
        button_layout.addStretch()
        
        layout.addLayout(button_layout)
        self.setLayout(layout)
    
    def create_app_config_tab(self):
        """创建应用程序配置标签页"""
        widget = QWidget()
        layout = QVBoxLayout()
        
        # UI配置组
        ui_group = QGroupBox(tr('config_manager.ui_config'))
        ui_layout = QFormLayout()
        
        self.theme_combo = QComboBox()
        self.theme_combo.addItems(["light", "dark", "blue", "green", "purple"])
        ui_layout.addRow(tr('config_manager.theme') + ":", self.theme_combo)
        
        self.language_combo = QComboBox()
        self.language_combo.addItems(["zh-CN", "en-US", "ja-JP"])
        ui_layout.addRow(tr('config_manager.language') + ":", self.language_combo)
        
        self.window_width_spin = QSpinBox()
        self.window_width_spin.setRange(800, 2560)
        ui_layout.addRow(tr('config_manager.window_width') + ":", self.window_width_spin)
        
        self.window_height_spin = QSpinBox()
        self.window_height_spin.setRange(600, 1440)
        ui_layout.addRow(tr('config_manager.window_height') + ":", self.window_height_spin)
        
        self.font_size_spin = QSpinBox()
        self.font_size_spin.setRange(8, 24)
        ui_layout.addRow(tr('config_manager.font_size') + ":", self.font_size_spin)
        
        ui_group.setLayout(ui_layout)
        layout.addWidget(ui_group)
        
        # 文件配置组
        files_group = QGroupBox(tr('config_manager.file_config'))
        files_layout = QFormLayout()
        
        self.input_dir_edit = QLineEdit()
        files_layout.addRow(tr('config_manager.input_directory') + ":", self.input_dir_edit)
        
        self.output_dir_edit = QLineEdit()
        files_layout.addRow(tr('config_manager.output_directory') + ":", self.output_dir_edit)
        
        self.temp_dir_edit = QLineEdit()
        files_layout.addRow(tr('config_manager.temp_directory') + ":", self.temp_dir_edit)
        
        self.max_file_size_spin = QSpinBox()
        self.max_file_size_spin.setRange(1, 1024)
        self.max_file_size_spin.setSuffix(" MB")
        files_layout.addRow(tr('config_manager.max_file_size') + ":", self.max_file_size_spin)
        
        files_group.setLayout(files_layout)
        layout.addWidget(files_group)
        
        # 性能配置组
        performance_group = QGroupBox(tr('config_manager.performance_config'))
        performance_layout = QFormLayout()
        
        self.max_concurrent_spin = QSpinBox()
        self.max_concurrent_spin.setRange(1, 16)
        performance_layout.addRow(tr('config_manager.max_concurrent_tasks') + ":", self.max_concurrent_spin)
        
        self.memory_limit_spin = QSpinBox()
        self.memory_limit_spin.setRange(256, 8192)
        self.memory_limit_spin.setSuffix(" MB")
        performance_layout.addRow(tr('config_manager.memory_limit') + ":", self.memory_limit_spin)
        
        self.enable_caching_check = QCheckBox(tr('config_manager.enable_caching'))
        performance_layout.addRow("", self.enable_caching_check)
        
        self.cache_duration_spin = QSpinBox()
        self.cache_duration_spin.setRange(60, 86400)
        self.cache_duration_spin.setSuffix(" " + tr('config_manager.seconds'))
        performance_layout.addRow(tr('config_manager.cache_duration') + ":", self.cache_duration_spin)
        
        performance_group.setLayout(performance_layout)
        layout.addWidget(performance_group)
        
        # 用户偏好组
        preferences_group = QGroupBox(tr('config_manager.user_preferences'))
        preferences_layout = QFormLayout()
        
        self.default_engine_combo = QComboBox()
        preferences_layout.addRow(tr('config_manager.default_engine') + ":", self.default_engine_combo)
        
        self.default_rate_spin = QDoubleSpinBox()
        self.default_rate_spin.setRange(0.1, 3.0)
        self.default_rate_spin.setSingleStep(0.1)
        preferences_layout.addRow(tr('config_manager.default_rate') + ":", self.default_rate_spin)
        
        self.default_pitch_spin = QSpinBox()
        self.default_pitch_spin.setRange(-50, 50)
        preferences_layout.addRow(tr('config_manager.default_pitch') + ":", self.default_pitch_spin)
        
        self.default_volume_spin = QDoubleSpinBox()
        self.default_volume_spin.setRange(0.0, 2.0)
        self.default_volume_spin.setSingleStep(0.1)
        preferences_layout.addRow(tr('config_manager.default_volume') + ":", self.default_volume_spin)
        
        preferences_group.setLayout(preferences_layout)
        layout.addWidget(preferences_group)
        
        layout.addStretch()
        widget.setLayout(layout)
        return widget
    
    def create_engine_config_tab(self):
        """创建引擎配置标签页"""
        widget = QWidget()
        layout = QVBoxLayout()
        
        # 引擎列表
        self.engine_table = QTableWidget()
        self.engine_table.setColumnCount(6)
        self.engine_table.setHorizontalHeaderLabels([
            tr('config_manager.engine_name'), tr('config_manager.status'), tr('config_manager.enabled'), 
            tr('config_manager.priority'), tr('config_manager.online'), tr('config_manager.action')
        ])
        
        # 设置表格属性
        self.engine_table.horizontalHeader().setStretchLastSection(True)
        self.engine_table.setSelectionBehavior(QTableWidget.SelectionBehavior.SelectRows)
        self.engine_table.setAlternatingRowColors(True)
        
        layout.addWidget(QLabel(tr('config_manager.engine_config_title') + ":"))
        layout.addWidget(self.engine_table)
        
        # 引擎详情
        details_group = QGroupBox(tr('config_manager.engine_details'))
        details_layout = QFormLayout()
        
        self.engine_name_label = QLabel()
        details_layout.addRow(tr('config_manager.name') + ":", self.engine_name_label)
        
        self.engine_version_label = QLabel()
        details_layout.addRow(tr('config_manager.version') + ":", self.engine_version_label)
        
        self.engine_description_label = QLabel()
        details_layout.addRow(tr('config_manager.description') + ":", self.engine_description_label)
        
        self.engine_languages_label = QLabel()
        details_layout.addRow(tr('config_manager.supported_languages') + ":", self.engine_languages_label)
        
        self.engine_formats_label = QLabel()
        details_layout.addRow(tr('config_manager.supported_formats') + ":", self.engine_formats_label)
        
        details_group.setLayout(details_layout)
        layout.addWidget(details_group)
        
        # 操作按钮
        button_layout = QHBoxLayout()
        
        self.refresh_engines_button = QPushButton(tr('config_manager.refresh_engine_status'))
        self.refresh_engines_button.clicked.connect(self.refresh_engine_status)
        
        self.health_check_button = QPushButton(tr('config_manager.perform_health_check'))
        self.health_check_button.clicked.connect(self.perform_health_check)
        
        button_layout.addWidget(self.refresh_engines_button)
        button_layout.addWidget(self.health_check_button)
        button_layout.addStretch()
        
        layout.addLayout(button_layout)
        
        widget.setLayout(layout)
        return widget
    
    def create_validation_tab(self):
        """创建配置验证标签页"""
        widget = QWidget()
        layout = QVBoxLayout()
        
        # 验证按钮
        button_layout = QHBoxLayout()
        
        self.validate_button = QPushButton(tr('config_manager.validate_config'))
        self.validate_button.clicked.connect(self.validate_config)
        
        self.fix_button = QPushButton(tr('config_manager.auto_fix'))
        self.fix_button.clicked.connect(self.auto_fix_config)
        
        button_layout.addWidget(self.validate_button)
        button_layout.addWidget(self.fix_button)
        button_layout.addStretch()
        
        layout.addLayout(button_layout)
        
        # 验证结果
        self.validation_text = QTextEdit()
        self.validation_text.setReadOnly(True)
        self.validation_text.setFont(QFont("Consolas", 10))
        
        layout.addWidget(QLabel(tr('config_manager.validation_results') + ":"))
        layout.addWidget(self.validation_text)
        
        widget.setLayout(layout)
        return widget
    
    def create_backup_tab(self):
        """创建备份管理标签页"""
        widget = QWidget()
        layout = QVBoxLayout()
        
        # 备份操作按钮
        backup_button_layout = QHBoxLayout()
        
        self.create_backup_button = QPushButton(tr('config_manager.create_backup'))
        self.create_backup_button.clicked.connect(self.create_backup)
        
        self.restore_backup_button = QPushButton(tr('config_manager.restore_backup'))
        self.restore_backup_button.clicked.connect(self.restore_backup)
        
        self.delete_backup_button = QPushButton(tr('config_manager.delete_backup'))
        self.delete_backup_button.clicked.connect(self.delete_backup)
        
        backup_button_layout.addWidget(self.create_backup_button)
        backup_button_layout.addWidget(self.restore_backup_button)
        backup_button_layout.addWidget(self.delete_backup_button)
        backup_button_layout.addStretch()
        
        layout.addLayout(backup_button_layout)
        
        # 备份列表
        self.backup_table = QTableWidget()
        self.backup_table.setColumnCount(5)
        self.backup_table.setHorizontalHeaderLabels([
            tr('config_manager.backup_id'), tr('config_manager.type'), tr('config_manager.description'), 
            tr('config_manager.created_time'), tr('config_manager.file_count')
        ])
        
        self.backup_table.horizontalHeader().setStretchLastSection(True)
        self.backup_table.setSelectionBehavior(QTableWidget.SelectionBehavior.SelectRows)
        
        layout.addWidget(QLabel(tr('config_manager.backup_list') + ":"))
        layout.addWidget(self.backup_table)
        
        widget.setLayout(layout)
        return widget
    
    def load_config(self):
        """加载配置"""
        try:
            # 加载应用程序配置
            self.app_config = self.app_config_service.load_config()
            
            # 加载引擎配置
            self.engine_registry = self.engine_config_service.load_registry()
            
            # 更新UI
            self.update_app_config_ui()
            self.update_engine_config_ui()
            self.update_backup_list()
            
            self.logger.info(tr('config_manager.messages.config_loaded_success'))
            
        except Exception as e:
            self.logger.error(tr('config_manager.messages.config_load_failed', error=str(e)))
            QMessageBox.critical(self, tr('config_manager.messages.error'), tr('config_manager.messages.config_load_failed', error=str(e)))
    
    def update_app_config_ui(self):
        """更新应用程序配置UI"""
        if not self.app_config:
            return
        
        # UI配置
        self.theme_combo.setCurrentText(self.app_config.ui.theme)
        self.language_combo.setCurrentText(self.app_config.ui.language)
        self.window_width_spin.setValue(self.app_config.ui.window_width)
        self.window_height_spin.setValue(self.app_config.ui.window_height)
        self.font_size_spin.setValue(self.app_config.ui.font_size)
        
        # 文件配置
        self.input_dir_edit.setText(self.app_config.files.input_dir)
        self.output_dir_edit.setText(self.app_config.files.output_dir)
        self.temp_dir_edit.setText(self.app_config.files.temp_dir)
        self.max_file_size_spin.setValue(self.app_config.files.max_file_size_mb)
        
        # 性能配置
        self.max_concurrent_spin.setValue(self.app_config.performance.max_concurrent_tasks)
        self.memory_limit_spin.setValue(self.app_config.performance.memory_limit_mb)
        self.enable_caching_check.setChecked(self.app_config.performance.enable_caching)
        self.cache_duration_spin.setValue(self.app_config.performance.cache_duration)
        
        # 用户偏好
        self.default_engine_combo.clear()
        available_engines = self.engine_manager.get_available_engines()
        self.default_engine_combo.addItems(available_engines)
        self.default_engine_combo.setCurrentText(self.app_config.preferences.default_engine)
        self.default_rate_spin.setValue(self.app_config.preferences.default_rate)
        self.default_pitch_spin.setValue(int(self.app_config.preferences.default_pitch))
        self.default_volume_spin.setValue(self.app_config.preferences.default_volume)
    
    def update_engine_config_ui(self):
        """更新引擎配置UI"""
        if not self.engine_registry:
            return
        
        # 清空表格
        self.engine_table.setRowCount(0)
        
        # 添加引擎行
        for engine_id, config in self.engine_registry._engine_configs.items():
            row = self.engine_table.rowCount()
            self.engine_table.insertRow(row)
            
            # 引擎名称
            self.engine_table.setItem(row, 0, QTableWidgetItem(config.info.name))
            
            # 状态
            status_item = QTableWidgetItem(config.status.status.value)
            if config.status.status.value == "available":
                status_item.setBackground(Qt.GlobalColor.green)
            elif config.status.status.value == "error":
                status_item.setBackground(Qt.GlobalColor.red)
            else:
                status_item.setBackground(Qt.GlobalColor.yellow)
            self.engine_table.setItem(row, 1, status_item)
            
            # 启用状态
            enabled_check = QCheckBox()
            enabled_check.setChecked(config.enabled)
            enabled_check.stateChanged.connect(
                lambda state, eid=engine_id: self.toggle_engine_enabled(eid, state == Qt.CheckState.Checked.value)
            )
            self.engine_table.setCellWidget(row, 2, enabled_check)
            
            # 优先级
            priority_spin = QSpinBox()
            priority_spin.setRange(0, 100)
            priority_spin.setValue(config.priority)
            priority_spin.valueChanged.connect(
                lambda value, eid=engine_id: self.set_engine_priority(eid, value)
            )
            self.engine_table.setCellWidget(row, 3, priority_spin)
            
            # 在线状态
            online_item = QTableWidgetItem(tr('config_manager.yes') if config.info.is_online else tr('config_manager.no'))
            self.engine_table.setItem(row, 4, online_item)
            
            # 操作按钮
            details_button = QPushButton(tr('config_manager.details'))
            details_button.clicked.connect(
                lambda checked, eid=engine_id: self.show_engine_details(eid)
            )
            self.engine_table.setCellWidget(row, 5, details_button)
    
    def update_backup_list(self):
        """更新备份列表"""
        try:
            backups = self.config_backup.list_backups()
            
            self.backup_table.setRowCount(len(backups))
            
            for i, backup in enumerate(backups):
                self.backup_table.setItem(i, 0, QTableWidgetItem(backup['backup_id']))
                self.backup_table.setItem(i, 1, QTableWidgetItem(backup['config_type']))
                self.backup_table.setItem(i, 2, QTableWidgetItem(backup['description']))
                self.backup_table.setItem(i, 3, QTableWidgetItem(backup['created_at']))
                self.backup_table.setItem(i, 4, QTableWidgetItem(str(backup['file_count'])))
                
        except Exception as e:
            self.logger.error(tr('config_manager.messages.update_backup_list_failed', error=str(e)))
    
    def save_config(self):
        """保存配置"""
        try:
            # 保存应用程序配置
            if self.app_config:
                self.app_config_service.save_config(self.app_config)
            
            # 保存引擎配置
            if self.engine_registry:
                self.engine_config_service.save_registry(self.engine_registry)
            
            QMessageBox.information(self, tr('config_manager.messages.success'), tr('config_manager.messages.config_save_success'))
            self.config_changed.emit("config_saved")
            
        except Exception as e:
            self.logger.error(tr('config_manager.messages.config_save_failed', error=str(e)))
            QMessageBox.critical(self, tr('config_manager.messages.error'), tr('config_manager.messages.config_save_failed', error=str(e)))
    
    def reset_config(self):
        """重置配置为默认值"""
        reply = QMessageBox.question(
            self, tr('config_manager.messages.confirm'), tr('config_manager.messages.config_reset_confirm'),
            QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No
        )
        
        if reply == QMessageBox.StandardButton.Yes:
            try:
                self.app_config_service.reset_to_defaults()
                self.load_config()
                QMessageBox.information(self, tr('config_manager.messages.success'), tr('config_manager.messages.config_reset_success'))
                
            except Exception as e:
                self.logger.error(tr('config_manager.messages.config_reset_failed', error=str(e)))
                QMessageBox.critical(self, tr('config_manager.messages.error'), tr('config_manager.messages.config_reset_failed', error=str(e)))
    
    def validate_config(self):
        """验证配置"""
        try:
            self.validation_text.clear()
            self.validation_text.append(tr('config_manager.messages.validation_started'))
            
            # 验证应用程序配置
            if self.app_config:
                is_valid, errors = self.config_validator.validate_app_config(self.app_config)
                if is_valid:
                    self.validation_text.append(tr('config_manager.messages.app_config_valid'))
                else:
                    self.validation_text.append(tr('config_manager.messages.app_config_invalid'))
                    for error in errors:
                        self.validation_text.append(f"  - {error}")
            
            # 验证引擎配置
            if self.engine_registry:
                for engine_id, config in self.engine_registry._engine_configs.items():
                    is_valid, errors = self.config_validator.validate_engine_config(config)
                    if is_valid:
                        self.validation_text.append(tr('config_manager.messages.engine_config_valid', engine_id=engine_id))
                    else:
                        self.validation_text.append(tr('config_manager.messages.engine_config_invalid', engine_id=engine_id))
                        for error in errors:
                            self.validation_text.append(f"  - {error}")
            
            self.validation_text.append("\n" + tr('config_manager.messages.validation_completed'))
            
        except Exception as e:
            self.logger.error(tr('config_manager.messages.validation_failed', error=str(e)))
            self.validation_text.append(tr('config_manager.messages.validation_failed', error=str(e)))
    
    def auto_fix_config(self):
        """自动修复配置"""
        QMessageBox.information(self, tr('config_manager.messages.info'), tr('config_manager.messages.auto_fix_development'))
    
    def create_backup(self):
        """创建备份"""
        try:
            backup_id = self.config_backup.create_backup("all", tr('config_manager.messages.manual_backup'), auto_backup=False)
            if backup_id:
                QMessageBox.information(self, tr('config_manager.messages.success'), tr('config_manager.messages.backup_created_success', backup_id=backup_id))
                self.update_backup_list()
            else:
                QMessageBox.warning(self, tr('config_manager.messages.warning'), tr('config_manager.messages.backup_created_failed'))
                
        except Exception as e:
            self.logger.error(tr('config_manager.messages.backup_created_failed', error=str(e)))
            QMessageBox.critical(self, tr('config_manager.messages.error'), tr('config_manager.messages.backup_created_failed', error=str(e)))
    
    def restore_backup(self):
        """恢复备份"""
        current_row = self.backup_table.currentRow()
        if current_row < 0:
            QMessageBox.warning(self, tr('config_manager.messages.warning'), tr('config_manager.messages.backup_restore_confirm'))
            return
        
        backup_id = self.backup_table.item(current_row, 0).text()
        
        reply = QMessageBox.question(
            self, tr('config_manager.messages.confirm'), tr('config_manager.messages.backup_restore_confirm', backup_id=backup_id),
            QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No
        )
        
        if reply == QMessageBox.StandardButton.Yes:
            try:
                success = self.config_backup.restore_backup(backup_id)
                if success:
                    QMessageBox.information(self, tr('config_manager.messages.success'), tr('config_manager.messages.backup_restore_success'))
                    self.load_config()
                else:
                    QMessageBox.warning(self, tr('config_manager.messages.warning'), tr('config_manager.messages.backup_restore_failed'))
                    
            except Exception as e:
                self.logger.error(tr('config_manager.messages.backup_restore_failed', error=str(e)))
                QMessageBox.critical(self, tr('config_manager.messages.error'), tr('config_manager.messages.backup_restore_failed', error=str(e)))
    
    def delete_backup(self):
        """删除备份"""
        current_row = self.backup_table.currentRow()
        if current_row < 0:
            QMessageBox.warning(self, tr('config_manager.messages.warning'), tr('config_manager.messages.backup_delete_confirm'))
            return
        
        backup_id = self.backup_table.item(current_row, 0).text()
        
        reply = QMessageBox.question(
            self, tr('config_manager.messages.confirm'), tr('config_manager.messages.backup_delete_confirm', backup_id=backup_id),
            QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No
        )
        
        if reply == QMessageBox.StandardButton.Yes:
            try:
                success = self.config_backup.delete_backup(backup_id)
                if success:
                    QMessageBox.information(self, tr('config_manager.messages.success'), tr('config_manager.messages.backup_delete_success'))
                    self.update_backup_list()
                else:
                    QMessageBox.warning(self, tr('config_manager.messages.warning'), tr('config_manager.messages.backup_delete_failed'))
                    
            except Exception as e:
                self.logger.error(tr('config_manager.messages.backup_delete_failed', error=str(e)))
                QMessageBox.critical(self, tr('config_manager.messages.error'), tr('config_manager.messages.backup_delete_failed', error=str(e)))
    
    def toggle_engine_enabled(self, engine_id: str, enabled: bool):
        """切换引擎启用状态"""
        try:
            if enabled:
                success = self.engine_manager.enable_engine(engine_id)
            else:
                success = self.engine_manager.disable_engine(engine_id)
            
            if success:
                self.logger.info(tr('config_manager.messages.engine_status_updated', engine_id=engine_id, enabled=enabled))
            else:
                self.logger.warning(tr('config_manager.messages.engine_status_update_failed', engine_id=engine_id))
                
        except Exception as e:
            self.logger.error(tr('config_manager.messages.engine_status_update_failed', engine_id=engine_id, error=str(e)))
    
    def set_engine_priority(self, engine_id: str, priority: int):
        """设置引擎优先级"""
        try:
            success = self.engine_manager.set_engine_priority(engine_id, priority)
            if success:
                self.logger.info(tr('config_manager.messages.engine_priority_set', engine_id=engine_id, priority=priority))
            else:
                self.logger.warning(tr('config_manager.messages.engine_priority_set_failed', engine_id=engine_id))
                
        except Exception as e:
            self.logger.error(tr('config_manager.messages.engine_priority_set_failed', engine_id=engine_id, error=str(e)))
    
    def show_engine_details(self, engine_id: str):
        """显示引擎详情"""
        try:
            config = self.engine_manager.get_engine_config(engine_id)
            if config:
                self.engine_name_label.setText(config.info.name)
                self.engine_version_label.setText(config.info.version)
                self.engine_description_label.setText(config.info.description)
                self.engine_languages_label.setText(", ".join(config.info.supported_languages))
                self.engine_formats_label.setText(", ".join(config.info.supported_formats))
                
        except Exception as e:
            self.logger.error(tr('config_manager.messages.show_engine_details_failed', engine_id=engine_id, error=str(e)))
    
    def refresh_engine_status(self):
        """刷新引擎状态"""
        try:
            # 执行引擎状态检查
            health_report = self.engine_manager.perform_health_check()
            
            # 更新引擎表格
            self.update_engine_table()
            
            # 显示结果
            available_count = health_report.get('available_engines', 0)
            total_count = health_report.get('total_engines', 0)
            QMessageBox.information(
                self, 
                tr('config_manager.messages.engine_status_refreshed'), 
                tr('config_manager.messages.engine_status_refreshed', available=available_count, total=total_count)
            )
        except Exception as e:
            QMessageBox.critical(self, tr('config_manager.messages.error'), tr('config_manager.messages.engine_status_refresh_failed', error=str(e)))
    
    def perform_health_check(self):
        """执行健康检查"""
        try:
            # 显示进度对话框
            progress = QProgressDialog(tr('config_manager.messages.health_check_progress'), tr('config_manager.messages.cancel'), 0, 0, self)
            progress.setWindowModality(Qt.WindowModality.WindowModal)
            progress.show()
            
            # 执行健康检查
            health_report = self.engine_manager.perform_health_check()
            
            progress.close()
            
            # 显示健康检查结果
            self.show_health_check_results(health_report)
            
        except Exception as e:
            QMessageBox.critical(self, tr('config_manager.messages.error'), tr('config_manager.messages.health_check_failed', error=str(e)))
    
    def show_health_check_results(self, health_report: Dict[str, Any]):
        """显示健康检查结果"""
        try:
            # 创建结果对话框
            dialog = QDialog(self)
            dialog.setWindowTitle(tr('config_manager.messages.health_check_results'))
            dialog.setModal(True)
            dialog.resize(600, 400)
            
            layout = QVBoxLayout()
            
            # 摘要信息
            summary_text = f"""
健康检查摘要:
- 总引擎数: {health_report.get('total_engines', 0)}
- 可用引擎: {health_report.get('available_engines', 0)}
- 不可用引擎: {health_report.get('unavailable_engines', 0)}
- 检查时间: {time.strftime('%Y-%m-%d %H:%M:%S', time.localtime(health_report.get('check_time', 0)))}
            """
            
            summary_label = QLabel(summary_text)
            summary_label.setStyleSheet("font-weight: bold; padding: 10px;")
            layout.addWidget(summary_label)
            
            # 详细结果
            results_text = QTextEdit()
            results_text.setReadOnly(True)
            results_text.setFont(QFont("Consolas", 9))
            
            results_content = tr('config_manager.messages.detailed_results') + ":\n\n"
            for engine_id, result in health_report.get('results', {}).items():
                status_icon = "✓" if result.get('available', False) else "✗"
                results_content += f"{status_icon} {engine_id}: {result.get('status_message', tr('config_manager.messages.unknown_status'))}\n"
                if result.get('details'):
                    for key, value in result['details'].items():
                        results_content += f"    {key}: {value}\n"
                results_content += "\n"
            
            results_text.setPlainText(results_content)
            layout.addWidget(results_text)
            
            # 关闭按钮
            close_button = QPushButton(tr('config_manager.messages.close'))
            close_button.clicked.connect(dialog.accept)
            layout.addWidget(close_button)
            
            dialog.setLayout(layout)
            dialog.exec()
            
        except Exception as e:
            QMessageBox.critical(self, tr('config_manager.messages.error'), tr('config_manager.messages.show_health_check_results_failed', error=str(e)))
    
    def update_engine_table(self):
        """更新引擎表格"""
        try:
            # 获取所有引擎配置
            engine_configs = self.engine_manager.get_all_engine_configs()
            
            # 设置表格行数
            self.engine_table.setRowCount(len(engine_configs))
            
            # 填充表格数据
            for row, (engine_id, config) in enumerate(engine_configs.items()):
                # 引擎名称
                name_item = QTableWidgetItem(config.info.name)
                self.engine_table.setItem(row, 0, name_item)
                
                # 状态
                status_text = config.status.status.value
                status_item = QTableWidgetItem(status_text)
                if config.status.status == EngineStatusEnum.AVAILABLE:
                    status_item.setBackground(QColor(200, 255, 200))  # 绿色
                elif config.status.status == EngineStatusEnum.UNAVAILABLE:
                    status_item.setBackground(QColor(255, 200, 200))  # 红色
                else:
                    status_item.setBackground(QColor(255, 255, 200))  # 黄色
                self.engine_table.setItem(row, 1, status_item)
                
                # 启用状态
                enabled_item = QTableWidgetItem(tr('config_manager.yes') if config.enabled else tr('config_manager.no'))
                self.engine_table.setItem(row, 2, enabled_item)
                
                # 优先级
                priority_item = QTableWidgetItem(str(config.priority))
                self.engine_table.setItem(row, 3, priority_item)
                
                # 在线状态
                online_item = QTableWidgetItem(tr('config_manager.yes') if config.info.is_online else tr('config_manager.no'))
                self.engine_table.setItem(row, 4, online_item)
                
                # 操作按钮
                action_button = QPushButton(tr('config_manager.messages.configure'))
                action_button.clicked.connect(lambda checked, eid=engine_id: self.edit_engine_config(eid))
                self.engine_table.setCellWidget(row, 5, action_button)
            
            # 调整列宽
            self.engine_table.resizeColumnsToContents()
            
        except Exception as e:
            self.logger.error(tr('config_manager.messages.update_engine_table_failed', error=str(e)))
    
    def edit_engine_config(self, engine_id: str):
        """编辑引擎配置"""
        try:
            # 这里可以添加编辑引擎配置的逻辑
            QMessageBox.information(self, tr('config_manager.messages.info'), tr('config_manager.messages.edit_engine_config', engine_id=engine_id))
        except Exception as e:
            QMessageBox.critical(self, tr('config_manager.messages.error'), tr('config_manager.messages.edit_engine_config_failed', error=str(e)))
    
    def create_template_tab(self):
        """创建模板管理标签页"""
        widget = QWidget()
        layout = QVBoxLayout()
        
        # 模板列表
        template_group = QGroupBox(tr('config_manager.config_templates'))
        template_layout = QVBoxLayout(template_group)
        
        self.template_list = QListWidget()
        template_layout.addWidget(self.template_list)
        
        # 模板操作按钮
        template_buttons = QHBoxLayout()
        self.apply_template_btn = QPushButton(tr('config_manager.apply_template'))
        self.create_template_btn = QPushButton(tr('config_manager.create_template'))
        self.export_template_btn = QPushButton(tr('config_manager.export_template'))
        self.import_template_btn = QPushButton(tr('config_manager.import_template'))
        self.delete_template_btn = QPushButton(tr('config_manager.delete_template'))
        
        template_buttons.addWidget(self.apply_template_btn)
        template_buttons.addWidget(self.create_template_btn)
        template_buttons.addWidget(self.export_template_btn)
        template_buttons.addWidget(self.import_template_btn)
        template_buttons.addWidget(self.delete_template_btn)
        template_buttons.addStretch()
        
        template_layout.addLayout(template_buttons)
        layout.addWidget(template_group)
        
        # 模板详情
        details_group = QGroupBox(tr('config_manager.messages.template_details'))
        details_layout = QFormLayout(details_group)
        
        self.template_name_label = QLabel()
        self.template_desc_label = QLabel()
        self.template_version_label = QLabel()
        self.template_created_label = QLabel()
        
        details_layout.addRow(tr('config_manager.messages.name') + ":", self.template_name_label)
        details_layout.addRow(tr('config_manager.messages.description') + ":", self.template_desc_label)
        details_layout.addRow(tr('config_manager.messages.version') + ":", self.template_version_label)
        details_layout.addRow(tr('config_manager.messages.created_time') + ":", self.template_created_label)
        
        layout.addWidget(details_group)
        
        # 连接信号
        self.template_list.currentItemChanged.connect(self.on_template_selected)
        self.apply_template_btn.clicked.connect(self.apply_selected_template)
        self.create_template_btn.clicked.connect(self.create_new_template)
        self.export_template_btn.clicked.connect(self.export_selected_template)
        self.import_template_btn.clicked.connect(self.import_template)
        self.delete_template_btn.clicked.connect(self.delete_selected_template)
        
        # 加载模板列表
        self.load_template_list()
        
        widget.setLayout(layout)
        return widget
    
    def create_monitor_tab(self):
        """创建监控诊断标签页"""
        widget = QWidget()
        layout = QVBoxLayout()
        
        # 系统状态
        status_group = QGroupBox(tr('config_manager.system_status'))
        status_layout = QFormLayout(status_group)
        
        self.health_score_label = QLabel(tr('config_manager.unknown'))
        self.health_level_label = QLabel(tr('config_manager.unknown'))
        self.uptime_label = QLabel(tr('config_manager.unknown'))
        self.monitoring_status_label = QLabel(tr('config_manager.unknown'))
        
        status_layout.addRow(tr('config_manager.health_score') + ":", self.health_score_label)
        status_layout.addRow(tr('config_manager.health_level') + ":", self.health_level_label)
        status_layout.addRow(tr('config_manager.uptime') + ":", self.uptime_label)
        status_layout.addRow(tr('config_manager.monitoring_status') + ":", self.monitoring_status_label)
        
        layout.addWidget(status_group)
        
        # 性能图表区域
        performance_group = QGroupBox(tr('config_manager.performance_monitoring'))
        performance_layout = QVBoxLayout(performance_group)
        
        self.performance_text = QTextEdit()
        self.performance_text.setReadOnly(True)
        self.performance_text.setFont(QFont("Consolas", 9))
        performance_layout.addWidget(self.performance_text)
        
        layout.addWidget(performance_group)
        
        # 诊断结果
        diagnostic_group = QGroupBox(tr('config_manager.messages.diagnostic_results'))
        diagnostic_layout = QVBoxLayout(diagnostic_group)
        
        self.diagnostic_text = QTextEdit()
        self.diagnostic_text.setReadOnly(True)
        self.diagnostic_text.setFont(QFont("Consolas", 9))
        diagnostic_layout.addWidget(self.diagnostic_text)
        
        layout.addWidget(diagnostic_group)
        
        # 操作按钮
        monitor_buttons = QHBoxLayout()
        self.start_monitoring_btn = QPushButton(tr('config_manager.start_monitoring'))
        self.stop_monitoring_btn = QPushButton(tr('config_manager.stop_monitoring'))
        self.refresh_status_btn = QPushButton(tr('config_manager.refresh_status'))
        self.run_diagnostic_btn = QPushButton(tr('config_manager.run_diagnostic'))
        self.cleanup_data_btn = QPushButton(tr('config_manager.cleanup_data'))
        
        monitor_buttons.addWidget(self.start_monitoring_btn)
        monitor_buttons.addWidget(self.stop_monitoring_btn)
        monitor_buttons.addWidget(self.refresh_status_btn)
        monitor_buttons.addWidget(self.run_diagnostic_btn)
        monitor_buttons.addWidget(self.cleanup_data_btn)
        monitor_buttons.addStretch()
        
        layout.addLayout(monitor_buttons)
        
        # 连接信号
        self.start_monitoring_btn.clicked.connect(self.start_monitoring)
        self.stop_monitoring_btn.clicked.connect(self.stop_monitoring)
        self.refresh_status_btn.clicked.connect(self.refresh_monitor_status)
        self.run_diagnostic_btn.clicked.connect(self.run_diagnostic)
        self.cleanup_data_btn.clicked.connect(self.cleanup_monitor_data)
        
        # 初始化监控状态
        self.refresh_monitor_status()
        
        widget.setLayout(layout)
        return widget
    
    def load_template_list(self):
        """加载模板列表"""
        try:
            self.template_list.clear()
            templates = self.template_manager.get_available_templates()
            for template_name in templates:
                self.template_list.addItem(template_name)
        except Exception as e:
            self.logger.error(tr('config_manager.messages.load_template_list_failed', error=str(e)))
    
    def on_template_selected(self, current, previous):
        """模板选择事件"""
        if current:
            template_name = current.text()
            template = self.template_manager.get_template(template_name)
            if template:
                self.template_name_label.setText(template.get("name", ""))
                self.template_desc_label.setText(template.get("description", ""))
                self.template_version_label.setText(template.get("version", ""))
                self.template_created_label.setText(template.get("created_at", ""))
    
    def apply_selected_template(self):
        """应用选中的模板"""
        try:
            current_item = self.template_list.currentItem()
            if not current_item:
                QMessageBox.warning(self, tr('config_manager.messages.warning'), tr('config_manager.messages.template_apply_confirm'))
                return
            
            template_name = current_item.text()
            success = self.template_manager.apply_template(
                template_name, 
                self.app_config_service, 
                self.engine_config_service
            )
            
            if success:
                QMessageBox.information(self, tr('config_manager.messages.success'), tr('config_manager.messages.template_apply_success', template_name=template_name))
                # 刷新配置显示
                self.load_configs_to_ui()
            else:
                QMessageBox.critical(self, tr('config_manager.messages.error'), tr('config_manager.messages.template_apply_failed', template_name=template_name))
                
        except Exception as e:
            QMessageBox.critical(self, tr('config_manager.messages.error'), tr('config_manager.messages.template_apply_error', error=str(e)))
    
    def create_new_template(self):
        """创建新模板"""
        try:
            # 这里可以添加创建模板的对话框
            QMessageBox.information(self, tr('config_manager.messages.info'), tr('config_manager.messages.template_create_development'))
        except Exception as e:
            QMessageBox.critical(self, tr('config_manager.messages.error'), tr('config_manager.messages.template_create_failed', error=str(e)))
    
    def export_selected_template(self):
        """导出选中的模板"""
        try:
            current_item = self.template_list.currentItem()
            if not current_item:
                QMessageBox.warning(self, tr('config_manager.messages.warning'), tr('config_manager.messages.template_apply_confirm'))
                return
            
            template_name = current_item.text()
            file_path, _ = QFileDialog.getSaveFileName(
                self, tr('config_manager.export_template'), f"{template_name}.json", tr('config_manager.json_files')
            )
            
            if file_path:
                success = self.template_manager.export_template(template_name, file_path)
                if success:
                    QMessageBox.information(self, tr('config_manager.messages.success'), tr('config_manager.messages.template_export_success', path=file_path))
                else:
                    QMessageBox.critical(self, tr('config_manager.messages.error'), tr('config_manager.messages.template_export_failed'))
                    
        except Exception as e:
            QMessageBox.critical(self, tr('config_manager.messages.error'), tr('config_manager.messages.template_export_failed'))
    
    def import_template(self):
        """导入模板"""
        try:
            file_path, _ = QFileDialog.getOpenFileName(
                self, tr('config_manager.import_template'), "", tr('config_manager.json_files')
            )
            
            if file_path:
                success = self.template_manager.import_template(file_path)
                if success:
                    QMessageBox.information(self, tr('config_manager.messages.success'), tr('config_manager.messages.template_import_success'))
                    self.load_template_list()
                else:
                    QMessageBox.critical(self, tr('config_manager.messages.error'), tr('config_manager.messages.template_import_failed'))
                    
        except Exception as e:
            QMessageBox.critical(self, tr('config_manager.messages.error'), tr('config_manager.messages.template_import_failed'))
    
    def delete_selected_template(self):
        """删除选中的模板"""
        try:
            current_item = self.template_list.currentItem()
            if not current_item:
                QMessageBox.warning(self, tr('config_manager.messages.warning'), tr('config_manager.messages.template_apply_confirm'))
                return
            
            template_name = current_item.text()
            reply = QMessageBox.question(
                self, tr('config_manager.messages.confirm'), 
                tr('config_manager.messages.template_delete_confirm', template_name=template_name),
                QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No
            )
            
            if reply == QMessageBox.StandardButton.Yes:
                success = self.template_manager.delete_template(template_name)
                if success:
                    QMessageBox.information(self, tr('config_manager.messages.success'), tr('config_manager.messages.template_delete_success', template_name=template_name))
                    self.load_template_list()
                else:
                    QMessageBox.critical(self, tr('config_manager.messages.error'), tr('config_manager.messages.template_delete_failed', template_name=template_name))
                    
        except Exception as e:
            QMessageBox.critical(self, tr('config_manager.messages.error'), tr('config_manager.messages.template_delete_failed', template_name=""))
    
    def start_monitoring(self):
        """开始监控"""
        try:
            self.config_monitor.start_monitoring()
            QMessageBox.information(self, tr('config_manager.messages.success'), tr('config_manager.messages.monitoring_started'))
            self.refresh_monitor_status()
        except Exception as e:
            QMessageBox.critical(self, tr('config_manager.messages.error'), tr('config_manager.messages.monitoring_start_failed', error=str(e)))
    
    def stop_monitoring(self):
        """停止监控"""
        try:
            self.config_monitor.stop_monitoring()
            QMessageBox.information(self, tr('config_manager.messages.success'), tr('config_manager.messages.monitoring_stopped'))
            self.refresh_monitor_status()
        except Exception as e:
            QMessageBox.critical(self, tr('config_manager.messages.error'), tr('config_manager.messages.monitoring_stop_failed', error=str(e)))
    
    def refresh_monitor_status(self):
        """刷新监控状态"""
        try:
            health_status = self.config_monitor.get_health_status()
            
            self.health_score_label.setText(f"{health_status.get('health_score', 0)}/100")
            self.health_level_label.setText(health_status.get('health_level', 'unknown'))
            self.uptime_label.setText(health_status.get('uptime_human', 'unknown'))
            self.monitoring_status_label.setText(
                tr('config_manager.running') if health_status.get('monitoring_active', False) else tr('config_manager.stopped')
            )
            
            # 更新性能信息
            performance_summary = self.config_monitor.get_performance_summary(1)
            if "error" not in performance_summary:
                perf_text = f"""性能摘要 (最近1小时):
数据点数: {performance_summary.get('data_points', 0)}
CPU使用率: 平均 {performance_summary.get('cpu', {}).get('avg', 0):.1f}%, 最大 {performance_summary.get('cpu', {}).get('max', 0):.1f}%
内存使用率: 平均 {performance_summary.get('memory', {}).get('avg', 0):.1f}%, 最大 {performance_summary.get('memory', {}).get('max', 0):.1f}%
磁盘使用率: 平均 {performance_summary.get('disk', {}).get('avg', 0):.1f}%, 最大 {performance_summary.get('disk', {}).get('max', 0):.1f}%
引擎可用性: {performance_summary.get('engines', {}).get('availability_rate', 0)*100:.1f}% ({performance_summary.get('engines', {}).get('available', 0)}/{performance_summary.get('engines', {}).get('total', 0)})
"""
                self.performance_text.setPlainText(perf_text)
            else:
                self.performance_text.setPlainText(tr('config_manager.no_performance_data'))
                
        except Exception as e:
            self.logger.error(tr('config_manager.messages.refresh_monitor_status_failed', error=str(e)))
    
    def run_diagnostic(self):
        """运行诊断"""
        try:
            diagnostics = self.config_monitor.generate_diagnostic_report()
            
            if diagnostics:
                diag_text = tr('config_manager.diagnostic_results') + ":\n\n"
                for i, diag in enumerate(diagnostics, 1):
                    diag_text += f"{i}. [{diag.severity.upper()}] {diag.description}\n"
                    diag_text += f"   {tr('config_manager.recommendation')}: {diag.recommendation}\n"
                    diag_text += f"   {tr('config_manager.affected_components')}: {', '.join(diag.affected_components)}\n"
                    diag_text += f"   {tr('config_manager.auto_fixable')}: {tr('config_manager.yes') if diag.auto_fixable else tr('config_manager.no')}\n\n"
                
                self.diagnostic_text.setPlainText(diag_text)
            else:
                self.diagnostic_text.setPlainText(tr('config_manager.messages.diagnostic_no_issues'))
                
        except Exception as e:
            QMessageBox.critical(self, tr('config_manager.messages.error'), tr('config_manager.messages.diagnostic_run_failed', error=str(e)))
    
    def cleanup_monitor_data(self):
        """清理监控数据"""
        try:
            reply = QMessageBox.question(
                self, tr('config_manager.messages.confirm'), 
                tr('config_manager.messages.cleanup_confirm'),
                QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No
            )
            
            if reply == QMessageBox.StandardButton.Yes:
                self.config_monitor.cleanup_old_data(7)
                QMessageBox.information(self, tr('config_manager.messages.success'), tr('config_manager.messages.cleanup_success'))
                self.refresh_monitor_status()
                
        except Exception as e:
            QMessageBox.critical(self, tr('config_manager.messages.error'), tr('config_manager.messages.cleanup_failed', error=str(e)))
