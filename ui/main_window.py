"""
主窗口模块

TTS应用程序的主窗口界面，提供：
- 多标签页界面布局
- 菜单栏和状态栏
- 文件管理、文本处理、语音设置等功能模块
- 主题和语言切换支持
- 信号槽机制实现模块间通信

作者: TTS开发团队
版本: 1.0.0
创建时间: 2024
"""

import sys
from pathlib import Path
from PyQt6.QtWidgets import (
    QMainWindow, QWidget, QVBoxLayout, QHBoxLayout, 
    QTabWidget, QMenuBar, QStatusBar, QMessageBox,
    QApplication, QSplitter, QFrame, QToolBar
)
from PyQt6.QtCore import Qt, QTimer, pyqtSignal
from PyQt6.QtGui import QIcon, QAction, QKeySequence

from models.config_model import AppConfig
from controllers.file_controller import FileController
from controllers.text_controller import TextController
from controllers.audio_controller import AudioController
from controllers.batch_controller import BatchController
from controllers.settings_controller import SettingsController
from .file_manager import FileManagerWidget
from .text_processor import TextProcessorWidget
from .voice_settings import VoiceSettingsWidget
from .output_settings import OutputSettingsWidget
from .conversion_control import ConversionControlWidget
from .batch_processor import BatchProcessorWidget
from .settings import SettingsWidget
from .config_manager import ConfigManagerWidget
from utils.log_manager import LogManager
from services.theme_service import theme_service
from services.language_service import get_language_service, get_text as tr


class MainWindow(QMainWindow):
    """
    主窗口类
    
    TTS应用程序的主界面，采用多标签页设计，集成所有功能模块。
    提供统一的用户界面和模块间的协调管理。
    
    特性：
    - 多标签页布局：文件管理、文本处理、语音设置等
    - 菜单栏：提供应用程序级别的操作
    - 状态栏：显示当前状态和进度信息
    - 主题支持：支持明暗主题切换
    - 多语言支持：支持中英文界面切换
    - 信号槽机制：实现模块间的松耦合通信
    """
    
    # 信号定义 - 用于模块间通信
    file_imported = pyqtSignal(str)      # 文件导入完成信号
    text_processed = pyqtSignal(str)     # 文本处理完成信号
    audio_generated = pyqtSignal(str)    # 音频生成完成信号
    
    def __init__(self, config):
        """
        初始化主窗口
        
        创建主窗口实例，初始化所有控制器和UI组件，
        设置信号槽连接，加载配置并应用主题和语言设置。
        
        Args:
            config (dict): 配置字典，包含app_config和engine_registry
        """
        super().__init__()
        self.config = config
        self.app_config = config.get('app_config')
        self.engine_registry = config.get('engine_registry')
        self.debug_mode = config.get('debug_mode', False)
        self.logger = LogManager().get_logger("MainWindow")
        
        # 初始化所有控制器
        # 控制器负责处理业务逻辑，与UI分离
        self.file_controller = FileController()        # 文件操作控制器
        self.text_controller = TextController()        # 文本处理控制器
        self.audio_controller = AudioController()      # 音频处理控制器
        self.batch_controller = BatchController()      # 批量处理控制器
        self.settings_controller = SettingsController() # 设置管理控制器
        
        # 先加载设置，确保语言服务正确初始化
        self.load_settings()         # 加载用户设置
        
        # 然后创建UI组件
        self.setup_ui()              # 创建和布局UI组件
        self.setup_connections()     # 设置信号槽连接
        
        # 应用界面样式和语言
        self.apply_theme()           # 应用主题样式
        self.apply_language(recreate_menu=False)  # 应用语言设置（初始化时不重新创建菜单）
        
        # 监听语言改变信号
        self.setup_language_signal_connection()
        
        self.logger.info("主窗口初始化完成")
    
    def setup_ui(self):
        """
        设置用户界面
        
        创建主窗口的UI布局，包括：
        - 窗口基本属性设置
        - 菜单栏创建
        - 状态栏创建
        - 标签页组件创建和布局
        - 各功能模块的初始化
        """
        from services.language_service import get_text as tr
        self.setWindowTitle(tr("app.title"))
        self.setMinimumSize(1000, 700)
        
        # 设置窗口大小和位置
        if self.app_config:
            self.resize(self.app_config.ui.window_width, self.app_config.ui.window_height)
            # 首次启动时居中显示，或者如果窗口位置为默认值(0,0)则居中
            if (self.app_config.ui.window_x == 0 and self.app_config.ui.window_y == 0) or \
               (self.app_config.ui.window_x == 2659 and self.app_config.ui.window_y == 410):
                # 这是默认的配置值，强制居中显示
                self.center_window()
            else:
                self.move(self.app_config.ui.window_x, self.app_config.ui.window_y)
        else:
            # 如果没有配置，默认居中显示
            self.center_window()
        
        # 创建菜单栏
        self.create_menu_bar()
        
        # 创建工具栏
        self.create_toolbar()
        
        # 创建中央部件
        self.create_central_widget()
        
        # 创建状态栏
        self.create_status_bar()
        
        # 设置样式
        self.setup_styles()
    
    def create_menu_bar(self):
        """创建菜单栏"""
        from services.language_service import get_text as tr
        menubar = self.menuBar()
        
        # 文件菜单
        file_menu = menubar.addMenu(tr("menu.file"))
        
        # 导入文件
        import_action = QAction(tr("menu.import_file"), self)
        import_action.setShortcut(QKeySequence.StandardKey.Open)
        import_action.triggered.connect(self.import_file)
        file_menu.addAction(import_action)
        
        file_menu.addSeparator()
        
        # 退出
        exit_action = QAction(tr("menu.exit"), self)
        exit_action.setShortcut(QKeySequence.StandardKey.Quit)
        exit_action.triggered.connect(self.close)
        file_menu.addAction(exit_action)
        
        # 编辑菜单
        edit_menu = menubar.addMenu(tr("menu.edit"))
        
        # 设置
        settings_action = QAction(tr("menu.settings"), self)
        settings_action.triggered.connect(self.show_settings)
        edit_menu.addAction(settings_action)
        
        # 帮助菜单
        help_menu = menubar.addMenu(tr("menu.help"))
        
        # 关于
        about_action = QAction(tr("menu.about"), self)
        about_action.triggered.connect(self.show_about)
        help_menu.addAction(about_action)
    
    def recreate_menu_bar(self):
        """重新创建菜单栏和工具栏（用于语言切换）"""
        try:
            # 清除现有菜单
            menubar = self.menuBar()
            menubar.clear()
            
            # 清除现有工具栏
            for toolbar in self.findChildren(QToolBar):
                toolbar.clear()
                self.removeToolBar(toolbar)
            
            # 重新创建菜单和工具栏
            self.create_menu_bar()
            self.create_toolbar()
            self.logger.info("菜单栏和工具栏已重新创建")
            
        except Exception as e:
            self.logger.error(f"重新创建菜单栏和工具栏失败: {e}")
    
    def recreate_menu_bar_only(self):
        """仅重新创建菜单栏（用于语言切换）"""
        try:
            # 清除现有菜单
            menubar = self.menuBar()
            menubar.clear()
            
            # 重新创建菜单
            self.create_menu_bar()
            self.logger.info("菜单栏已重新创建")
            
        except Exception as e:
            self.logger.error(f"重新创建菜单栏失败: {e}")
    
    def create_toolbar(self):
        """创建工具栏"""
        from services.language_service import get_text as tr
        toolbar = self.addToolBar(tr("toolbar.main"))
        
        # 导入文件
        import_action = QAction(tr("toolbar.import_file"), self)
        import_action.setIcon(QIcon('resources/icons/upload.svg'))
        import_action.triggered.connect(self.import_file)
        toolbar.addAction(import_action)
        
        toolbar.addSeparator()
        
        # 播放
        play_action = QAction(tr("toolbar.play"), self)
        play_action.setIcon(QIcon('resources/icons/play.svg'))
        play_action.triggered.connect(self.play_audio)
        toolbar.addAction(play_action)
        
        # 暂停
        pause_action = QAction(tr("toolbar.pause"), self)
        pause_action.setIcon(QIcon('resources/icons/pause.svg'))
        pause_action.triggered.connect(self.pause_audio)
        toolbar.addAction(pause_action)
        
        # 停止
        stop_action = QAction(tr("toolbar.stop"), self)
        stop_action.setIcon(QIcon('resources/icons/stop.svg'))
        stop_action.triggered.connect(self.stop_audio)
        toolbar.addAction(stop_action)
    
    def create_central_widget(self):
        """创建中央部件"""
        central_widget = QWidget()
        self.setCentralWidget(central_widget)
        
        # 主布局
        main_layout = QHBoxLayout(central_widget)
        main_layout.setContentsMargins(5, 5, 5, 5)
        
        # 创建分割器
        splitter = QSplitter(Qt.Orientation.Horizontal)
        main_layout.addWidget(splitter)
        
        # 左侧面板（文件管理）
        left_panel = self.create_left_panel()
        splitter.addWidget(left_panel)
        
        # 右侧面板（标签页）
        right_panel = self.create_right_panel()
        splitter.addWidget(right_panel)
        
        # 设置分割器比例
        splitter.setSizes([300, 700])
    
    def create_left_panel(self):
        """创建左侧面板"""
        panel = QFrame()
        panel.setFrameStyle(QFrame.Shape.StyledPanel)
        panel.setMaximumWidth(350)
        
        layout = QVBoxLayout(panel)
        layout.setContentsMargins(5, 5, 5, 5)
        
        # 文件管理组件
        self.file_manager = FileManagerWidget(self.file_controller)
        layout.addWidget(self.file_manager)
        
        return panel
    
    def create_right_panel(self):
        """创建右侧面板"""
        # 创建标签页
        self.tab_widget = QTabWidget()
        
        # 文本处理标签页
        self.text_processor = TextProcessorWidget(self.text_controller)
        self.tab_widget.addTab(self.text_processor, tr("tabs.text_processing"))
        
        # 语音设置标签页
        self.voice_settings = VoiceSettingsWidget(self.audio_controller)
        self.tab_widget.addTab(self.voice_settings, tr("tabs.voice_settings"))
        
        # 输出设置标签页
        self.output_settings = OutputSettingsWidget()
        self.tab_widget.addTab(self.output_settings, tr("tabs.output_settings"))
        
        # 建立页面间的关联
        self.voice_settings.set_output_settings_widget(self.output_settings)
        self.text_processor.set_output_settings_widget(self.output_settings)
        
        # 转换控制标签页
        self.conversion_control = ConversionControlWidget()
        self.conversion_control.set_output_settings_widget(self.output_settings)
        self.conversion_control.set_voice_settings_widget(self.voice_settings)
        self.tab_widget.addTab(self.conversion_control, tr("tabs.conversion_control"))
        
        # 批量处理标签页
        self.batch_processor = BatchProcessorWidget(self.batch_controller)
        self.tab_widget.addTab(self.batch_processor, tr("tabs.batch_processing"))
        
        # 设置标签页
        self.settings_widget = SettingsWidget(self.settings_controller)
        self.settings_widget.set_main_window(self)  # 设置主窗口引用
        self.tab_widget.addTab(self.settings_widget, tr("tabs.settings"))
        
        # 配置管理标签页
        self.config_manager = ConfigManagerWidget()
        self.tab_widget.addTab(self.config_manager, tr("tabs.config_management"))
        
        return self.tab_widget
    
    def create_status_bar(self):
        """创建状态栏"""
        self.status_bar = QStatusBar()
        self.setStatusBar(self.status_bar)
        
        # 状态信息
        self.status_bar.showMessage(tr("common.ready"))
        
        # 进度条
        self.progress_bar = self.status_bar.addPermanentWidget(
            QWidget(), 1
        )
    
    def center_window(self):
        """将窗口居中显示"""
        try:
            # 获取屏幕几何信息
            screen = QApplication.primaryScreen()
            screen_geometry = screen.availableGeometry()
            
            # 获取窗口几何信息
            window_geometry = self.frameGeometry()
            
            # 计算居中位置
            center_point = screen_geometry.center()
            window_geometry.moveCenter(center_point)
            
            # 移动窗口到居中位置
            self.move(window_geometry.topLeft())
            
            self.logger.info(f"窗口已居中显示，位置: {window_geometry.topLeft()}")
        except Exception as e:
            self.logger.error(f"窗口居中失败: {e}")
            # 如果居中失败，使用默认位置
            self.move(100, 100)
    
    def setup_styles(self):
        """设置样式"""
        style = """
        QMainWindow {
            background-color: #f5f5f5;
        }
        
        QTabWidget::pane {
            border: 1px solid #c0c0c0;
            background-color: white;
        }
        
        QTabBar::tab {
            background-color: #e0e0e0;
            padding: 8px 16px;
            margin-right: 2px;
        }
        
        QTabBar::tab:selected {
            background-color: white;
            border-bottom: 2px solid #0078d4;
        }
        
        QPushButton {
            background-color: #0078d4;
            color: white;
            border: none;
            padding: 8px 16px;
            border-radius: 4px;
        }
        
        QPushButton:hover {
            background-color: #106ebe;
        }
        
        QPushButton:pressed {
            background-color: #005a9e;
        }
        
        QLineEdit, QTextEdit, QComboBox {
            border: 1px solid #c0c0c0;
            padding: 4px;
            border-radius: 4px;
        }
        
        QLineEdit:focus, QTextEdit:focus, QComboBox:focus {
            border-color: #0078d4;
        }
        """
        
        self.setStyleSheet(style)
    
    def setup_connections(self):
        """设置信号槽连接"""
        # 文件管理信号
        self.file_manager.file_selected.connect(self.on_file_selected)
        self.file_manager.file_imported.connect(self.on_file_imported)
        
        # 文本处理信号
        self.text_processor.text_processed.connect(self.on_text_processed)
        self.text_processor.conversion_requested.connect(self.switch_to_conversion_tab)
        self.text_processor.start_conversion_signal.connect(self.start_conversion)
        
        # 语音设置信号
        self.voice_settings.voice_changed.connect(self.on_voice_changed)
        
        # 输出设置信号
        self.output_settings.output_changed.connect(self.on_output_changed)
        
        # 加载配置到各个界面
        self.load_config_to_widgets()
        
        # 批量处理信号
        self.batch_processor.task_completed.connect(self.on_task_completed)
    
    def load_settings(self):
        """加载设置"""
        try:
            self.logger.info("设置加载完成")
            
        except Exception as e:
            self.logger.error(f"加载设置失败: {e}")
    
    def apply_theme(self):
        """应用主题"""
        try:
            # 优先使用主题服务中的当前主题
            current_theme = theme_service.get_current_theme()
            if self.app_config and current_theme and current_theme != self.app_config.ui.theme:
                # 如果主题服务中的主题与配置不同，更新配置
                self.app_config.ui.theme = current_theme
                self.logger.info(f"主题已同步: {current_theme}")
            
            # 使用全局主题服务应用主题
            theme = self.app_config.ui.theme if self.app_config else "light"
            theme_service.apply_theme(theme)
            self.logger.info(f"已应用主题: {theme}")
            
            # 重新应用字体设置
            self.apply_font_settings()
            
        except Exception as e:
            self.logger.error(f"应用主题失败: {e}")
    
    def apply_font_settings(self):
        """应用字体设置"""
        try:
            from PyQt6.QtGui import QFont
            from PyQt6.QtWidgets import QApplication
            import os
            import json
            
            # 从UI配置获取字体设置
            ui_config_file = "configs/app/ui.json"
            if os.path.exists(ui_config_file):
                with open(ui_config_file, 'r', encoding='utf-8') as f:
                    ui_config = json.load(f)
                    font_size = ui_config.get('font_size', 12)
                    font_family = ui_config.get('font_family', 'Microsoft YaHei')
                    
                    # 创建字体对象
                    font = QFont(font_family, font_size)
                    
                    # 应用到整个应用程序
                    app = QApplication.instance()
                    if app:
                        app.setFont(font)
                        self.logger.info(f"已应用字体设置: {font_family}, 大小: {font_size}")
            
        except Exception as e:
            self.logger.error(f"应用字体设置失败: {e}")
    
    def apply_language(self, recreate_menu=True):
        """应用语言"""
        try:
            # 获取当前语言
            current_language = get_language_service().get_current_language()
            self.logger.info(f"当前语言: {current_language}")
            
            # 更新应用配置中的语言设置（如果存在）
            if self.app_config and hasattr(self.app_config, 'ui'):
                # 获取语言显示名称
                language_service = get_language_service()
                lang_info = language_service.language_config.get("language_info", {}).get(current_language, {})
                lang_name = lang_info.get("name", current_language)
                language_display = f"{lang_name} ({current_language})"
                
                # 更新应用配置
                self.app_config.ui.language = language_display
                self.logger.info(f"已更新应用配置语言: {language_display}")
            
            # 只有在需要时才重新创建菜单
            if recreate_menu:
                self.recreate_menu_bar_only()
            
        except Exception as e:
            self.logger.error(f"应用语言失败: {e}")
    
    def setup_language_signal_connection(self):
        """设置语言改变信号连接"""
        try:
            from services.language_service import get_language_service
            language_service = get_language_service()
            
            # 连接语言改变信号
            language_service.language_changed.connect(self.on_language_changed)
            self.logger.info("语言改变信号连接已设置")
            
        except Exception as e:
            self.logger.error(f"设置语言信号连接失败: {e}")
    
    def on_language_changed(self, language):
        """语言改变事件处理"""
        try:
            self.logger.info(f"收到语言改变信号: {language}")
            
            # 更新应用配置
            if self.app_config:
                self.app_config.ui.language = language
            
            # 重新应用语言
            self.apply_language()
            
        except Exception as e:
            self.logger.error(f"处理语言改变事件失败: {e}")
    
    def sync_theme_and_language(self):
        """同步主题和语言设置"""
        try:
            # 从主题服务获取当前主题
            current_theme = theme_service.get_current_theme()
            if self.app_config and current_theme and current_theme != self.app_config.ui.theme:
                self.app_config.ui.theme = current_theme
                self.logger.info(f"主题已同步: {current_theme}")
            
            # 从语言服务获取当前语言
            current_language = get_language_service().get_current_language()
            if self.app_config and current_language and current_language != self.app_config.ui.language:
                self.app_config.ui.language = current_language
                self.logger.info(f"语言已同步: {current_language}")
            
        except Exception as e:
            self.logger.error(f"同步主题和语言失败: {e}")
    
    def import_file(self):
        """导入文件"""
        try:
            self.file_manager.import_file()
        except Exception as e:
            self.logger.error(f"导入文件失败: {e}")
            QMessageBox.critical(self, tr("common.error"), tr("main_window.messages.import_file_failed", error=str(e)))
    
    def play_audio(self):
        """播放音频"""
        try:
            # 实现音频播放逻辑
            self.status_bar.showMessage(tr("main_window.status.playing_audio"))
        except Exception as e:
            self.logger.error(f"播放音频失败: {e}")
    
    def pause_audio(self):
        """暂停音频"""
        try:
            # 实现音频暂停逻辑
            self.status_bar.showMessage(tr("main_window.status.paused_audio"))
        except Exception as e:
            self.logger.error(f"暂停音频失败: {e}")
    
    def stop_audio(self):
        """停止音频"""
        try:
            # 实现音频停止逻辑
            self.status_bar.showMessage(tr("main_window.status.stopped_audio"))
        except Exception as e:
            self.logger.error(f"停止音频失败: {e}")
    
    def show_settings(self):
        """显示设置"""
        try:
            self.tab_widget.setCurrentWidget(self.settings_widget)
        except Exception as e:
            self.logger.error(f"显示设置失败: {e}")
    
    def show_about(self):
        """显示关于对话框"""
        QMessageBox.about(
            self,
            tr("main_window.about.title"),
            tr("main_window.about.content")
        )
    
    def on_file_selected(self, file_path: str):
        """文件选择事件"""
        try:
            self.status_bar.showMessage(tr("main_window.status.file_selected", file_path=file_path))
            self.logger.info(f"文件选择: {file_path}")
            
            # 获取文件内容并加载到文本处理器
            file_model = self.file_manager.get_selected_file()
            if file_model and file_model.content:
                self.text_processor.set_text(file_model.content)
                # 切换到文本处理标签页
                self.tab_widget.setCurrentWidget(self.text_processor)
                
        except Exception as e:
            self.logger.error(f"处理文件选择事件失败: {e}")
    
    def on_file_imported(self, file_path: str):
        """文件导入事件"""
        try:
            self.status_bar.showMessage(tr("main_window.status.file_imported", file_path=file_path))
            self.file_imported.emit(file_path)
            self.logger.info(f"文件导入: {file_path}")
        except Exception as e:
            self.logger.error(f"处理文件导入事件失败: {e}")
    
    def on_text_processed(self, text: str):
        """文本处理事件"""
        try:
            self.status_bar.showMessage(tr("main_window.status.text_processed"))
            self.text_processed.emit(text)
            self.logger.info("文本处理完成")
        except Exception as e:
            self.logger.error(f"处理文本处理事件失败: {e}")
    
    def on_voice_changed(self, voice_config):
        """语音设置改变事件"""
        try:
            # 将语音配置传递给text_processor
            if hasattr(self.text_processor, 'set_voice_config'):
                self.text_processor.set_voice_config(voice_config)
            
            self.status_bar.showMessage(tr("main_window.status.voice_settings_updated"))
            self.logger.info("语音设置已更新")
        except Exception as e:
            self.logger.error(f"处理语音设置改变事件失败: {e}")
    
    def on_output_changed(self, output_config):
        """输出设置改变事件"""
        try:
            # 将输出配置传递给text_processor
            if hasattr(self.text_processor, 'set_output_config'):
                self.text_processor.set_output_config(output_config)
            
            self.status_bar.showMessage(tr("main_window.status.output_settings_updated"))
            self.logger.info("输出设置已更新")
        except Exception as e:
            self.logger.error(f"处理输出设置改变事件失败: {e}")
    
    def on_task_completed(self, task_id: str):
        """任务完成事件"""
        try:
            self.status_bar.showMessage(tr("main_window.status.task_completed", task_id=task_id))
            self.logger.info(f"任务完成: {task_id}")
        except Exception as e:
            self.logger.error(f"处理任务完成事件失败: {e}")
    
    def switch_to_conversion_tab(self):
        """切换到转换控制标签页"""
        # 找到转换控制标签页的索引
        conversion_tab_text = tr("tabs.conversion_control")
        for i in range(self.tab_widget.count()):
            if self.tab_widget.tabText(i) == conversion_tab_text:
                self.tab_widget.setCurrentIndex(i)
                break
    
    def start_conversion(self, segments, voice_config, output_config, chapters=None):
        """开始转换"""
        self.conversion_control.start_conversion(segments, voice_config, output_config, chapters)
    
    def load_config_to_widgets(self):
        """加载配置到各个界面"""
        try:
            # 加载语音配置
            from services.json_config_service import JsonConfigService
            config_service = JsonConfigService()
            
            # 加载语音设置
            voice_config = config_service.load_voice_config()
            self.voice_settings.set_voice_config(voice_config)
            
            # 加载输出设置
            output_config = config_service.load_output_config()
            self.output_settings.set_output_config(output_config)
            
            self.logger.info("配置已加载到各个界面")
            
        except Exception as e:
            self.logger.error(f"加载配置到界面失败: {e}")
    
    def closeEvent(self, event):
        """窗口关闭事件"""
        try:
            # 保存窗口状态
            if self.app_config:
                self.app_config.ui.window_width = self.width()
                self.app_config.ui.window_height = self.height()
                self.app_config.ui.window_x = self.x()
                self.app_config.ui.window_y = self.y()
            
            # 同步主题和语言设置
            self.sync_theme_and_language()
            
            # 保存应用程序配置
            if self.app_config:
                from services.config.app_config_service import AppConfigService
                app_config_service = AppConfigService()
                app_config_service.save_config(self.app_config)
                self.logger.info("应用程序配置已保存")
            
            self.logger.info("主窗口关闭")
            event.accept()
            
        except Exception as e:
            self.logger.error(f"关闭窗口失败: {e}")
            event.accept()
