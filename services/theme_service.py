"""
主题管理服务模块

提供应用程序的主题和样式管理功能，包括：
- 多主题支持：浅色、深色、彩色主题等
- 动态主题切换：运行时切换界面主题
- 样式管理：统一的CSS样式定义和管理
- 主题配置：主题设置的保存和加载
- 信号通知：主题切换时通知相关组件

支持的主题：
- 浅色主题 (light)：默认主题，适合日间使用
- 深色主题 (dark)：护眼主题，适合夜间使用
- 蓝色主题 (blue)：商务风格主题
- 绿色主题 (green)：自然风格主题
- 紫色主题 (purple)：创意风格主题

设计模式：
- 观察者模式：主题切换时通知所有订阅者
- 单例模式：全局唯一的主题服务实例
- 策略模式：支持多种主题样式策略

作者: TTS开发团队
版本: 1.0.0
创建时间: 2024
"""

import json
import os
from PyQt6.QtWidgets import QApplication
from PyQt6.QtCore import QObject, pyqtSignal
from typing import Dict, Any, Optional
from utils.log_manager import LogManager


class ThemeService(QObject):
    """
    主题管理服务类
    
    提供应用程序的主题和样式管理功能，包括主题切换、样式应用等。
    采用观察者模式，当主题切换时自动通知所有订阅的组件。
    
    特性：
    - 多主题支持：内置多种预设主题
    - 动态切换：支持运行时切换界面主题
    - 样式统一：使用CSS样式确保界面一致性
    - 配置持久化：保存用户选择的主题设置
    - 信号通知：主题切换时发送信号通知相关组件
    """
    
    # 主题改变信号 - 当主题切换时发送
    theme_changed = pyqtSignal(str)
    
    def __init__(self):
        super().__init__()
        self.logger = LogManager().get_logger("ThemeService")
        self.current_theme = "light"
        self.config_file = "configs/theme_config.json"
        
        # 主题样式定义
        self.themes = {
            "light": self._get_light_theme(),
            "dark": self._get_dark_theme(),
            "blue": self._get_blue_theme(),
            "green": self._get_green_theme(),
            "purple": self._get_purple_theme(),
            "red": self._get_red_theme(),
            "gray": self._get_gray_theme(),
            "auto": self._get_auto_theme()
        }
        
        # 优先从主配置文件加载主题
        main_theme = self.load_from_main_config()
        if main_theme != 'light':
            self.current_theme = main_theme
        
        # 加载主题配置（作为备用）
        self.load_theme_config()
    
    def _get_light_theme(self) -> str:
        """获取浅色主题样式"""
        return """
        QWidget {
            background-color: #ffffff;
            color: #000000;
        }
        QMainWindow {
            background-color: #f5f5f5;
        }
        QGroupBox {
            font-weight: bold;
            border: 2px solid #cccccc;
            border-radius: 5px;
            margin-top: 1ex;
            padding-top: 10px;
        }
        QGroupBox::title {
            subcontrol-origin: margin;
            left: 10px;
            padding: 0 5px 0 5px;
        }
        QComboBox {
            border: 1px solid #cccccc;
            border-radius: 3px;
            padding: 5px;
            background-color: #ffffff;
            min-width: 100px;
        }
        QComboBox::drop-down {
            border: none;
            width: 20px;
        }
        QComboBox::down-arrow {
            image: none;
            border-left: 5px solid transparent;
            border-right: 5px solid transparent;
            border-top: 5px solid #000000;
            margin-right: 5px;
        }
        QComboBox:hover {
            border-color: #0078d4;
        }
        QComboBox:focus {
            border-color: #0078d4;
        }
        QSpinBox {
            border: 1px solid #cccccc;
            border-radius: 3px;
            padding: 5px;
            background-color: #ffffff;
        }
        QSpinBox:hover {
            border-color: #0078d4;
        }
        QSpinBox:focus {
            border-color: #0078d4;
        }
        QLineEdit {
            border: 1px solid #cccccc;
            border-radius: 3px;
            padding: 5px;
            background-color: #ffffff;
        }
        QLineEdit:hover {
            border-color: #0078d4;
        }
        QLineEdit:focus {
            border-color: #0078d4;
        }
        QPushButton {
            border: 1px solid #cccccc;
            border-radius: 3px;
            padding: 5px 10px;
            background-color: #f0f0f0;
            min-width: 80px;
        }
        QPushButton:hover {
            background-color: #e0e0e0;
            border-color: #0078d4;
        }
        QPushButton:pressed {
            background-color: #d0d0d0;
        }
        QPushButton:disabled {
            background-color: #f5f5f5;
            color: #999999;
            border-color: #dddddd;
        }
        QCheckBox {
            spacing: 5px;
        }
        QCheckBox::indicator {
            width: 18px;
            height: 18px;
        }
        QCheckBox::indicator:unchecked {
            border: 1px solid #cccccc;
            background-color: #ffffff;
        }
        QCheckBox::indicator:checked {
            border: 1px solid #0078d4;
            background-color: #0078d4;
        }
        QCheckBox::indicator:hover {
            border-color: #0078d4;
        }
        QRadioButton {
            spacing: 5px;
        }
        QRadioButton::indicator {
            width: 18px;
            height: 18px;
        }
        QRadioButton::indicator:unchecked {
            border: 1px solid #cccccc;
            background-color: #ffffff;
            border-radius: 9px;
        }
        QRadioButton::indicator:checked {
            border: 1px solid #0078d4;
            background-color: #0078d4;
            border-radius: 9px;
        }
        QRadioButton::indicator:hover {
            border-color: #0078d4;
        }
        QTabWidget::pane {
            border: 1px solid #cccccc;
            background-color: #ffffff;
        }
        QTabBar::tab {
            background-color: #f0f0f0;
            border: 1px solid #cccccc;
            padding: 5px 10px;
            margin-right: 2px;
        }
        QTabBar::tab:selected {
            background-color: #ffffff;
            border-bottom-color: #ffffff;
        }
        QTabBar::tab:hover {
            background-color: #e0e0e0;
        }
        QListWidget {
            border: 1px solid #cccccc;
            background-color: #ffffff;
            selection-background-color: #e3f2fd;
        }
        QListWidget::item {
            padding: 5px;
            border-bottom: 1px solid #f0f0f0;
        }
        QListWidget::item:selected {
            background-color: #e3f2fd;
            color: #000000;
        }
        QListWidget::item:hover {
            background-color: #f5f5f5;
        }
        QTextEdit {
            border: 1px solid #cccccc;
            background-color: #ffffff;
            selection-background-color: #e3f2fd;
        }
        QTextEdit:focus {
            border-color: #0078d4;
        }
        QScrollBar:vertical {
            background-color: #f0f0f0;
            width: 12px;
            border-radius: 6px;
        }
        QScrollBar::handle:vertical {
            background-color: #cccccc;
            border-radius: 6px;
            min-height: 20px;
        }
        QScrollBar::handle:vertical:hover {
            background-color: #999999;
        }
        QScrollBar::add-line:vertical, QScrollBar::sub-line:vertical {
            height: 0px;
        }
        QScrollBar:horizontal {
            background-color: #f0f0f0;
            height: 12px;
            border-radius: 6px;
        }
        QScrollBar::handle:horizontal {
            background-color: #cccccc;
            border-radius: 6px;
            min-width: 20px;
        }
        QScrollBar::handle:horizontal:hover {
            background-color: #999999;
        }
        QScrollBar::add-line:horizontal, QScrollBar::sub-line:horizontal {
            width: 0px;
        }
        QProgressBar {
            border: 1px solid #cccccc;
            border-radius: 3px;
            text-align: center;
            background-color: #f0f0f0;
        }
        QProgressBar::chunk {
            background-color: #0078d4;
            border-radius: 2px;
        }
        QSlider::groove:horizontal {
            border: 1px solid #cccccc;
            height: 6px;
            background-color: #f0f0f0;
            border-radius: 3px;
        }
        QSlider::handle:horizontal {
            background-color: #0078d4;
            border: 1px solid #0078d4;
            width: 18px;
            margin: -6px 0;
            border-radius: 9px;
        }
        QSlider::handle:horizontal:hover {
            background-color: #005a9e;
        }
        QMenuBar {
            background-color: #f5f5f5;
            border-bottom: 1px solid #cccccc;
        }
        QMenuBar::item {
            padding: 5px 10px;
        }
        QMenuBar::item:selected {
            background-color: #e0e0e0;
        }
        QMenu {
            background-color: #ffffff;
            border: 1px solid #cccccc;
        }
        QMenu::item {
            padding: 5px 20px;
        }
        QMenu::item:selected {
            background-color: #e3f2fd;
        }
        QToolBar {
            background-color: #f5f5f5;
            border: 1px solid #cccccc;
            spacing: 3px;
        }
        QToolButton {
            border: 1px solid transparent;
            border-radius: 3px;
            padding: 5px;
        }
        QToolButton:hover {
            background-color: #e0e0e0;
            border-color: #cccccc;
        }
        QToolButton:pressed {
            background-color: #d0d0d0;
        }
        QStatusBar {
            background-color: #f5f5f5;
            border-top: 1px solid #cccccc;
        }
        QSplitter::handle {
            background-color: #cccccc;
        }
        QSplitter::handle:horizontal {
            width: 1px;
        }
        QSplitter::handle:vertical {
            height: 1px;
        }
        """
    
    def _get_dark_theme(self) -> str:
        """获取深色主题样式"""
        return """
        QWidget {
            background-color: #2b2b2b;
            color: #ffffff;
        }
        QMainWindow {
            background-color: #1e1e1e;
        }
        QGroupBox {
            font-weight: bold;
            border: 2px solid #555555;
            border-radius: 5px;
            margin-top: 1ex;
            padding-top: 10px;
        }
        QGroupBox::title {
            subcontrol-origin: margin;
            left: 10px;
            padding: 0 5px 0 5px;
        }
        QComboBox {
            border: 1px solid #555555;
            border-radius: 3px;
            padding: 5px;
            background-color: #3c3c3c;
            min-width: 100px;
        }
        QComboBox::drop-down {
            border: none;
            width: 20px;
        }
        QComboBox::down-arrow {
            image: none;
            border-left: 5px solid transparent;
            border-right: 5px solid transparent;
            border-top: 5px solid #ffffff;
            margin-right: 5px;
        }
        QComboBox:hover {
            border-color: #0078d4;
        }
        QComboBox:focus {
            border-color: #0078d4;
        }
        QSpinBox {
            border: 1px solid #555555;
            border-radius: 3px;
            padding: 5px;
            background-color: #3c3c3c;
        }
        QSpinBox:hover {
            border-color: #0078d4;
        }
        QSpinBox:focus {
            border-color: #0078d4;
        }
        QLineEdit {
            border: 1px solid #555555;
            border-radius: 3px;
            padding: 5px;
            background-color: #3c3c3c;
        }
        QLineEdit:hover {
            border-color: #0078d4;
        }
        QLineEdit:focus {
            border-color: #0078d4;
        }
        QPushButton {
            border: 1px solid #555555;
            border-radius: 3px;
            padding: 5px 10px;
            background-color: #3c3c3c;
            min-width: 80px;
        }
        QPushButton:hover {
            background-color: #4c4c4c;
            border-color: #0078d4;
        }
        QPushButton:pressed {
            background-color: #2c2c2c;
        }
        QPushButton:disabled {
            background-color: #2b2b2b;
            color: #666666;
            border-color: #444444;
        }
        QCheckBox {
            spacing: 5px;
        }
        QCheckBox::indicator {
            width: 18px;
            height: 18px;
        }
        QCheckBox::indicator:unchecked {
            border: 1px solid #555555;
            background-color: #3c3c3c;
        }
        QCheckBox::indicator:checked {
            border: 1px solid #0078d4;
            background-color: #0078d4;
        }
        QCheckBox::indicator:hover {
            border-color: #0078d4;
        }
        QRadioButton {
            spacing: 5px;
        }
        QRadioButton::indicator {
            width: 18px;
            height: 18px;
        }
        QRadioButton::indicator:unchecked {
            border: 1px solid #555555;
            background-color: #3c3c3c;
            border-radius: 9px;
        }
        QRadioButton::indicator:checked {
            border: 1px solid #0078d4;
            background-color: #0078d4;
            border-radius: 9px;
        }
        QRadioButton::indicator:hover {
            border-color: #0078d4;
        }
        QTabWidget::pane {
            border: 1px solid #555555;
            background-color: #2b2b2b;
        }
        QTabBar::tab {
            background-color: #3c3c3c;
            color: #ffffff;
            border: 1px solid #555555;
            border-bottom: none;
            padding: 8px 16px;
            margin-right: 2px;
        }
        QTabBar::tab:selected {
            background-color: #2b2b2b;
            border-bottom: 1px solid #2b2b2b;
        }
        QTabBar::tab:hover {
            background-color: #4c4c4c;
        }
        QTabBar::tab:!selected {
            margin-top: 2px;
        }
        QListWidget {
            border: 1px solid #555555;
            background-color: #3c3c3c;
            selection-background-color: #404040;
        }
        QListWidget::item {
            padding: 5px;
            border-bottom: 1px solid #444444;
        }
        QListWidget::item:selected {
            background-color: #404040;
            color: #ffffff;
        }
        QListWidget::item:hover {
            background-color: #4c4c4c;
        }
        QTextEdit {
            border: 1px solid #555555;
            background-color: #3c3c3c;
            selection-background-color: #404040;
        }
        QTextEdit:focus {
            border-color: #0078d4;
        }
        QScrollBar:vertical {
            background-color: #3c3c3c;
            width: 12px;
            border-radius: 6px;
        }
        QScrollBar::handle:vertical {
            background-color: #666666;
            border-radius: 6px;
            min-height: 20px;
        }
        QScrollBar::handle:vertical:hover {
            background-color: #888888;
        }
        QScrollBar::add-line:vertical, QScrollBar::sub-line:vertical {
            height: 0px;
        }
        QScrollBar:horizontal {
            background-color: #3c3c3c;
            height: 12px;
            border-radius: 6px;
        }
        QScrollBar::handle:horizontal {
            background-color: #666666;
            border-radius: 6px;
            min-width: 20px;
        }
        QScrollBar::handle:horizontal:hover {
            background-color: #888888;
        }
        QScrollBar::add-line:horizontal, QScrollBar::sub-line:horizontal {
            width: 0px;
        }
        QProgressBar {
            border: 1px solid #555555;
            border-radius: 3px;
            text-align: center;
            background-color: #3c3c3c;
        }
        QProgressBar::chunk {
            background-color: #0078d4;
            border-radius: 2px;
        }
        QSlider::groove:horizontal {
            border: 1px solid #555555;
            height: 6px;
            background-color: #3c3c3c;
            border-radius: 3px;
        }
        QSlider::handle:horizontal {
            background-color: #0078d4;
            border: 1px solid #0078d4;
            width: 18px;
            margin: -6px 0;
            border-radius: 9px;
        }
        QSlider::handle:horizontal:hover {
            background-color: #005a9e;
        }
        QMenuBar {
            background-color: #2b2b2b;
            border-bottom: 1px solid #555555;
        }
        QMenuBar::item {
            padding: 5px 10px;
        }
        QMenuBar::item:selected {
            background-color: #4c4c4c;
        }
        QMenu {
            background-color: #3c3c3c;
            border: 1px solid #555555;
        }
        QMenu::item {
            padding: 5px 20px;
        }
        QMenu::item:selected {
            background-color: #404040;
        }
        QToolBar {
            background-color: #2b2b2b;
            border: 1px solid #555555;
            spacing: 3px;
        }
        QToolButton {
            border: 1px solid transparent;
            border-radius: 3px;
            padding: 5px;
        }
        QToolButton:hover {
            background-color: #4c4c4c;
            border-color: #555555;
        }
        QToolButton:pressed {
            background-color: #2c2c2c;
        }
        QStatusBar {
            background-color: #2b2b2b;
            border-top: 1px solid #555555;
        }
        QSplitter::handle {
            background-color: #555555;
        }
        QSplitter::handle:horizontal {
            width: 1px;
        }
        QSplitter::handle:vertical {
            height: 1px;
        }
        """
    
    def apply_theme(self, theme: str):
        """应用主题到整个应用程序"""
        try:
            if theme not in self.themes:
                self.logger.warning(f"未知主题: {theme}")
                return
            
            self.current_theme = theme
            style = self.themes[theme]
            
            # 应用到整个应用程序
            app = QApplication.instance()
            if app:
                app.setStyleSheet(style)
                
                # 应用字体设置
                self.apply_font_settings(theme)
                
                self.logger.info(f"已应用主题: {theme}")
                
                # 发送主题改变信号
                self.theme_changed.emit(theme)
                
                # 同步到主配置文件
                self.sync_to_main_config(theme)
            else:
                self.logger.error("无法获取QApplication实例")
                
        except Exception as e:
            self.logger.error(f"应用主题失败: {e}")
    
    def apply_font_settings(self, theme: str):
        """应用字体设置到整个应用程序"""
        try:
            from PyQt6.QtGui import QFont
            from PyQt6.QtWidgets import QApplication
            
            # 获取字体设置
            font_size, font_family = self.get_font_settings(theme)
            
            # 创建字体对象
            font = QFont(font_family, font_size)
            
            # 应用到整个应用程序
            app = QApplication.instance()
            if app:
                app.setFont(font)
                self.logger.info(f"已应用字体设置: {font_family}, 大小: {font_size}")
            
        except Exception as e:
            self.logger.error(f"应用字体设置失败: {e}")
    
    def get_font_settings(self, theme: str):
        """获取字体设置"""
        try:
            # 默认字体设置
            default_font_size = 12
            default_font_family = "Microsoft YaHei"
            
            # 如果是自定义主题，从主题配置服务获取字体设置
            if theme == 'custom':
                from services.theme_config_service import theme_config_service
                custom_config = theme_config_service.get_custom_theme()
                if custom_config and custom_config.get('enabled', False):
                    fonts = custom_config.get('fonts', {})
                    size = fonts.get('size', 'medium')
                    weight = fonts.get('weight', 'normal')
                    
                    # 转换字体大小 - 增加差异使其更明显
                    font_size_map = {'small': 9, 'medium': 12, 'large': 16}
                    font_size = font_size_map.get(size, default_font_size)
                    
                    # 获取字体族（暂时使用默认）
                    font_family = default_font_family
                    
                    return font_size, font_family
            
            # 从UI配置获取字体设置
            try:
                import json
                ui_config_file = "configs/app/ui.json"
                if os.path.exists(ui_config_file):
                    with open(ui_config_file, 'r', encoding='utf-8') as f:
                        ui_config = json.load(f)
                        font_size = ui_config.get('font_size', default_font_size)
                        font_family = ui_config.get('font_family', default_font_family)
                        return font_size, font_family
            except Exception as e:
                self.logger.warning(f"从UI配置获取字体设置失败: {e}")
            
            return default_font_size, default_font_family
            
        except Exception as e:
            self.logger.error(f"获取字体设置失败: {e}")
            return 12, "Microsoft YaHei"
    
    def sync_to_main_config(self, theme: str):
        """同步主题到主配置文件"""
        try:
            import json
            main_config_file = "config.json"
            
            if os.path.exists(main_config_file):
                with open(main_config_file, 'r', encoding='utf-8') as f:
                    config = json.load(f)
                
                # 更新主题设置
                if 'general' not in config:
                    config['general'] = {}
                config['general']['theme'] = theme
                
                # 保存回主配置文件
                with open(main_config_file, 'w', encoding='utf-8') as f:
                    json.dump(config, f, ensure_ascii=False, indent=2)
                
                self.logger.info(f"已同步主题到主配置文件: {theme}")
            
        except Exception as e:
            self.logger.error(f"同步主题到主配置文件失败: {e}")
    
    def load_from_main_config(self):
        """从主配置文件加载主题"""
        try:
            main_config_file = "config.json"
            
            if os.path.exists(main_config_file):
                with open(main_config_file, 'r', encoding='utf-8') as f:
                    config = json.load(f)
                
                # 获取主题设置
                theme = config.get('general', {}).get('theme', 'light')
                if theme in self.themes:
                    self.current_theme = theme
                    self.logger.info(f"从主配置文件加载主题: {theme}")
                    return theme
            
        except Exception as e:
            self.logger.error(f"从主配置文件加载主题失败: {e}")
        
        return 'light'  # 默认主题
    
    def get_current_theme(self) -> str:
        """获取当前主题"""
        return self.current_theme
    
    def get_available_themes(self) -> list:
        """获取可用主题列表"""
        return list(self.themes.keys())
    
    def _get_blue_theme(self) -> str:
        """获取蓝色主题样式"""
        return """
        QWidget {
            background-color: #f0f8ff;
            color: #000080;
        }
        QMainWindow {
            background-color: #e6f3ff;
        }
        QGroupBox {
            font-weight: bold;
            border: 2px solid #4a90e2;
            border-radius: 5px;
            margin-top: 1ex;
            padding-top: 10px;
            color: #000080;
        }
        QGroupBox::title {
            subcontrol-origin: margin;
            left: 10px;
            padding: 0 5px 0 5px;
            color: #000080;
        }
        QTabWidget::pane {
            border: 1px solid #4a90e2;
            background-color: #f0f8ff;
        }
        QTabBar::tab {
            background-color: #d1e7ff;
            color: #000080;
            border: 1px solid #4a90e2;
            border-bottom: none;
            padding: 8px 16px;
            margin-right: 2px;
        }
        QTabBar::tab:selected {
            background-color: #f0f8ff;
            border-bottom: 1px solid #f0f8ff;
        }
        QTabBar::tab:hover {
            background-color: #b8d4f0;
        }
        QPushButton {
            background-color: #4a90e2;
            color: #ffffff;
            border: 1px solid #357abd;
            border-radius: 4px;
            padding: 6px 12px;
        }
        QPushButton:hover {
            background-color: #357abd;
        }
        QPushButton:pressed {
            background-color: #2c5aa0;
        }
        QComboBox, QLineEdit, QTextEdit, QPlainTextEdit {
            background-color: #ffffff;
            color: #000080;
            border: 1px solid #4a90e2;
            border-radius: 4px;
            padding: 4px;
        }
        QComboBox:focus, QLineEdit:focus, QTextEdit:focus, QPlainTextEdit:focus {
            border: 2px solid #4a90e2;
        }
        QListWidget {
            background-color: #ffffff;
            color: #000080;
            border: 1px solid #4a90e2;
            border-radius: 4px;
        }
        QListWidget::item:selected {
            background-color: #d1e7ff;
        }
        QListWidget::item:hover {
            background-color: #e6f3ff;
        }
        """
    
    def _get_green_theme(self) -> str:
        """获取绿色主题样式"""
        return """
        QWidget {
            background-color: #f0fff0;
            color: #006400;
        }
        QMainWindow {
            background-color: #e6ffe6;
        }
        QGroupBox {
            font-weight: bold;
            border: 2px solid #32cd32;
            border-radius: 5px;
            margin-top: 1ex;
            padding-top: 10px;
            color: #006400;
        }
        QGroupBox::title {
            subcontrol-origin: margin;
            left: 10px;
            padding: 0 5px 0 5px;
            color: #006400;
        }
        QTabWidget::pane {
            border: 1px solid #32cd32;
            background-color: #f0fff0;
        }
        QTabBar::tab {
            background-color: #d4f4d4;
            color: #006400;
            border: 1px solid #32cd32;
            border-bottom: none;
            padding: 8px 16px;
            margin-right: 2px;
        }
        QTabBar::tab:selected {
            background-color: #f0fff0;
            border-bottom: 1px solid #f0fff0;
        }
        QTabBar::tab:hover {
            background-color: #b8e6b8;
        }
        QPushButton {
            background-color: #32cd32;
            color: #ffffff;
            border: 1px solid #228b22;
            border-radius: 4px;
            padding: 6px 12px;
        }
        QPushButton:hover {
            background-color: #228b22;
        }
        QPushButton:pressed {
            background-color: #1e7a1e;
        }
        QComboBox, QLineEdit, QTextEdit, QPlainTextEdit {
            background-color: #ffffff;
            color: #006400;
            border: 1px solid #32cd32;
            border-radius: 4px;
            padding: 4px;
        }
        QComboBox:focus, QLineEdit:focus, QTextEdit:focus, QPlainTextEdit:focus {
            border: 2px solid #32cd32;
        }
        QListWidget {
            background-color: #ffffff;
            color: #006400;
            border: 1px solid #32cd32;
            border-radius: 4px;
        }
        QListWidget::item:selected {
            background-color: #d4f4d4;
        }
        QListWidget::item:hover {
            background-color: #e6ffe6;
        }
        """
    
    def _get_purple_theme(self) -> str:
        """获取紫色主题样式"""
        return """
        QWidget {
            background-color: #f8f0ff;
            color: #4b0082;
        }
        QMainWindow {
            background-color: #f0e6ff;
        }
        QGroupBox {
            font-weight: bold;
            border: 2px solid #9370db;
            border-radius: 5px;
            margin-top: 1ex;
            padding-top: 10px;
            color: #4b0082;
        }
        QGroupBox::title {
            subcontrol-origin: margin;
            left: 10px;
            padding: 0 5px 0 5px;
            color: #4b0082;
        }
        QTabWidget::pane {
            border: 1px solid #9370db;
            background-color: #f8f0ff;
        }
        QTabBar::tab {
            background-color: #e6d4ff;
            color: #4b0082;
            border: 1px solid #9370db;
            border-bottom: none;
            padding: 8px 16px;
            margin-right: 2px;
        }
        QTabBar::tab:selected {
            background-color: #f8f0ff;
            border-bottom: 1px solid #f8f0ff;
        }
        QTabBar::tab:hover {
            background-color: #d4b8ff;
        }
        QPushButton {
            background-color: #9370db;
            color: #ffffff;
            border: 1px solid #7b68ee;
            border-radius: 4px;
            padding: 6px 12px;
        }
        QPushButton:hover {
            background-color: #7b68ee;
        }
        QPushButton:pressed {
            background-color: #6a5acd;
        }
        QComboBox, QLineEdit, QTextEdit, QPlainTextEdit {
            background-color: #ffffff;
            color: #4b0082;
            border: 1px solid #9370db;
            border-radius: 4px;
            padding: 4px;
        }
        QComboBox:focus, QLineEdit:focus, QTextEdit:focus, QPlainTextEdit:focus {
            border: 2px solid #9370db;
        }
        QListWidget {
            background-color: #ffffff;
            color: #4b0082;
            border: 1px solid #9370db;
            border-radius: 4px;
        }
        QListWidget::item:selected {
            background-color: #e6d4ff;
        }
        QListWidget::item:hover {
            background-color: #f0e6ff;
        }
        """
    
    def _get_red_theme(self) -> str:
        """获取红色主题样式"""
        return """
        QWidget {
            background-color: #fff5f5;
            color: #8b0000;
        }
        QMainWindow {
            background-color: #ffe6e6;
        }
        QGroupBox {
            font-weight: bold;
            border: 2px solid #dc3545;
            border-radius: 5px;
            margin-top: 1ex;
            padding-top: 10px;
            color: #8b0000;
        }
        QGroupBox::title {
            subcontrol-origin: margin;
            left: 10px;
            padding: 0 5px 0 5px;
            color: #8b0000;
        }
        QTabWidget::pane {
            border: 1px solid #dc3545;
            background-color: #fff5f5;
        }
        QTabBar::tab {
            background-color: #f8d7da;
            color: #8b0000;
            border: 1px solid #dc3545;
            border-bottom: none;
            padding: 8px 16px;
            margin-right: 2px;
        }
        QTabBar::tab:selected {
            background-color: #fff5f5;
            border-bottom: 1px solid #fff5f5;
        }
        QTabBar::tab:hover {
            background-color: #f1b0b7;
        }
        QPushButton {
            background-color: #dc3545;
            color: #ffffff;
            border: 1px solid #c82333;
            border-radius: 4px;
            padding: 6px 12px;
        }
        QPushButton:hover {
            background-color: #c82333;
        }
        QPushButton:pressed {
            background-color: #bd2130;
        }
        QComboBox, QLineEdit, QTextEdit, QPlainTextEdit {
            background-color: #ffffff;
            color: #8b0000;
            border: 1px solid #dc3545;
            border-radius: 4px;
            padding: 4px;
        }
        QComboBox:focus, QLineEdit:focus, QTextEdit:focus, QPlainTextEdit:focus {
            border: 2px solid #dc3545;
        }
        QListWidget {
            background-color: #ffffff;
            color: #8b0000;
            border: 1px solid #dc3545;
            border-radius: 4px;
        }
        QListWidget::item:selected {
            background-color: #f8d7da;
        }
        QListWidget::item:hover {
            background-color: #ffe6e6;
        }
        """
    
    def _get_gray_theme(self) -> str:
        """获取灰色主题样式"""
        return """
        QWidget {
            background-color: #f8f9fa;
            color: #495057;
        }
        QMainWindow {
            background-color: #e9ecef;
        }
        QGroupBox {
            font-weight: bold;
            border: 2px solid #6c757d;
            border-radius: 5px;
            margin-top: 1ex;
            padding-top: 10px;
            color: #495057;
        }
        QGroupBox::title {
            subcontrol-origin: margin;
            left: 10px;
            padding: 0 5px 0 5px;
            color: #495057;
        }
        QTabWidget::pane {
            border: 1px solid #6c757d;
            background-color: #f8f9fa;
        }
        QTabBar::tab {
            background-color: #e9ecef;
            color: #495057;
            border: 1px solid #6c757d;
            border-bottom: none;
            padding: 8px 16px;
            margin-right: 2px;
        }
        QTabBar::tab:selected {
            background-color: #f8f9fa;
            border-bottom: 1px solid #f8f9fa;
        }
        QTabBar::tab:hover {
            background-color: #dee2e6;
        }
        QPushButton {
            background-color: #6c757d;
            color: #ffffff;
            border: 1px solid #5a6268;
            border-radius: 4px;
            padding: 6px 12px;
        }
        QPushButton:hover {
            background-color: #5a6268;
        }
        QPushButton:pressed {
            background-color: #545b62;
        }
        QComboBox, QLineEdit, QTextEdit, QPlainTextEdit {
            background-color: #ffffff;
            color: #495057;
            border: 1px solid #6c757d;
            border-radius: 4px;
            padding: 4px;
        }
        QComboBox:focus, QLineEdit:focus, QTextEdit:focus, QPlainTextEdit:focus {
            border: 2px solid #6c757d;
        }
        QListWidget {
            background-color: #ffffff;
            color: #495057;
            border: 1px solid #6c757d;
            border-radius: 4px;
        }
        QListWidget::item:selected {
            background-color: #e9ecef;
        }
        QListWidget::item:hover {
            background-color: #f8f9fa;
        }
        """
    
    def _get_auto_theme(self) -> str:
        """获取自动主题样式（跟随系统）"""
        # 自动主题使用浅色主题作为默认，实际应该根据系统主题动态切换
        return self._get_light_theme()
    
    def load_theme_config(self):
        """加载主题配置"""
        try:
            if os.path.exists(self.config_file):
                with open(self.config_file, 'r', encoding='utf-8') as f:
                    config = json.load(f)
                    self.current_theme = config.get('current_theme', 'light')
                    self.logger.info(f"已加载主题配置: {self.current_theme}")
            else:
                self.save_theme_config()
        except Exception as e:
            self.logger.error(f"加载主题配置失败: {e}")
    
    def save_theme_config(self):
        """保存主题配置"""
        try:
            # 确保配置目录存在
            os.makedirs(os.path.dirname(self.config_file), exist_ok=True)
            
            config = {
                'current_theme': self.current_theme,
                'available_themes': list(self.themes.keys()),
                'theme_info': {
                    'light': {'name': '浅色主题', 'description': '经典的浅色界面'},
                    'dark': {'name': '暗色主题', 'description': '护眼的暗色界面'},
                    'blue': {'name': '蓝色主题', 'description': '清新的蓝色界面'},
                    'green': {'name': '绿色主题', 'description': '自然的绿色界面'},
                    'purple': {'name': '紫色主题', 'description': '优雅的紫色界面'}
                }
            }
            
            with open(self.config_file, 'w', encoding='utf-8') as f:
                json.dump(config, f, ensure_ascii=False, indent=2)
            
            self.logger.info(f"已保存主题配置: {self.current_theme}")
            
        except Exception as e:
            self.logger.error(f"保存主题配置失败: {e}")
    
    def get_theme_info(self, theme: str) -> Optional[Dict[str, str]]:
        """获取主题信息"""
        try:
            if os.path.exists(self.config_file):
                with open(self.config_file, 'r', encoding='utf-8') as f:
                    config = json.load(f)
                    return config.get('theme_info', {}).get(theme)
        except Exception as e:
            self.logger.error(f"获取主题信息失败: {e}")
        return None


# 全局主题服务实例
theme_service = ThemeService()
