"""
设置界面
"""

# 先导入 piper，避免 PyQt6 的兼容性问题
try:
    from piper import PiperVoice, SynthesisConfig
    print("[OK] Piper TTS 在设置界面预加载成功")
except Exception as e:
    print(f"[WARN] Piper TTS 在设置界面预加载失败: {e}")

from PyQt6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QLabel, 
    QComboBox, QSpinBox, QCheckBox, QLineEdit,
    QPushButton, QGroupBox, QFormLayout, QMessageBox,
    QTabWidget, QScrollArea, QFrame, QFileDialog,
    QTextEdit, QDialog, QDialogButtonBox, QListWidget,
    QListWidgetItem, QInputDialog, QColorDialog, QGridLayout
)
from PyQt6.QtCore import Qt, pyqtSignal
from PyQt6.QtGui import QFont

from controllers.settings_controller import SettingsController
from models.config_model import AppConfig
from utils.log_manager import LogManager
from services.theme_service import theme_service
from services.theme_config_service import theme_config_service
from services.language_service import get_language_service, get_text as tr
from services.tts_service import TTSServiceFactory


class SettingsWidget(QWidget):
    """设置界面"""
    
    # 信号定义
    settings_changed = pyqtSignal(object)  # 设置改变信号
    
    def __init__(self, settings_controller: SettingsController):
        super().__init__()
        self.settings_controller = settings_controller
        self.logger = LogManager().get_logger("SettingsWidget")
        
        # 当前配置
        self.current_config = None
        
        # 主窗口引用
        self.main_window = None
        
        # 初始化UI
        self.setup_ui()
        self.setup_connections()
        self.load_settings()
    
    def set_main_window(self, main_window):
        """设置主窗口引用"""
        self.main_window = main_window
        self.logger.info("主窗口引用已设置")
    
    def setup_ui(self):
        """设置用户界面"""
        layout = QVBoxLayout(self)
        layout.setContentsMargins(5, 5, 5, 5)
        layout.setSpacing(10)
        
        # 标题
        title_label = QLabel(tr("settings.title"))
        title_label.setStyleSheet("font-size: 16px; font-weight: bold; margin-bottom: 10px;")
        layout.addWidget(title_label)
        
        # 创建标签页
        self.tab_widget = QTabWidget()
        layout.addWidget(self.tab_widget)
        
        # 界面设置标签页
        self.create_ui_tab()
        
        # 音频设置标签页
        self.create_audio_tab()
        
        # TTS设置标签页
        self.create_tts_tab()
        
        # 高级设置标签页
        self.create_advanced_tab()
        
        # 按钮区域
        button_layout = QHBoxLayout()
        
        self.apply_button = QPushButton(tr("settings.apply"))
        self.apply_button.clicked.connect(self.apply_settings)
        button_layout.addWidget(self.apply_button)
        
        self.reset_button = QPushButton(tr("settings.reset"))
        self.reset_button.clicked.connect(self.reset_settings)
        button_layout.addWidget(self.reset_button)
        
        self.export_button = QPushButton(tr("settings.export"))
        self.export_button.clicked.connect(self.export_settings)
        button_layout.addWidget(self.export_button)
        
        self.import_button = QPushButton(tr("settings.import"))
        self.import_button.clicked.connect(self.import_settings)
        button_layout.addWidget(self.import_button)
        
        button_layout.addStretch()
        layout.addLayout(button_layout)
    
    def create_ui_tab(self):
        """创建界面设置标签页"""
        widget = QFrame()
        widget.setFrameStyle(QFrame.Shape.StyledPanel)
        layout = QVBoxLayout(widget)
        layout.setContentsMargins(10, 10, 10, 10)
        
        # 主题选择组
        theme_group = QGroupBox(tr("settings.theme_selection"))
        theme_layout = QVBoxLayout(theme_group)
        
        # 预设主题网格布局
        self.theme_grid_layout = QHBoxLayout()
        self.create_theme_buttons()
        theme_layout.addLayout(self.theme_grid_layout)
        
        # 主题预览区域
        self.create_theme_preview(theme_layout)
        
        layout.addWidget(theme_group)
        
        # 自定义设置组
        custom_group = QGroupBox(tr("settings.custom_settings"))
        custom_layout = QFormLayout(custom_group)
        
        # 颜色自定义
        color_layout = QHBoxLayout()
        self.primary_color_btn = QPushButton(tr("settings.colors.primary"))
        self.primary_color_btn.clicked.connect(lambda: self.choose_color("primary"))
        color_layout.addWidget(self.primary_color_btn)
        
        self.background_color_btn = QPushButton(tr("settings.colors.background"))
        self.background_color_btn.clicked.connect(lambda: self.choose_color("background"))
        color_layout.addWidget(self.background_color_btn)
        
        self.text_color_btn = QPushButton(tr("settings.colors.text"))
        self.text_color_btn.clicked.connect(lambda: self.choose_color("text"))
        color_layout.addWidget(self.text_color_btn)
        
        self.tab_color_btn = QPushButton(tr("settings.colors.tab_text"))
        self.tab_color_btn.clicked.connect(lambda: self.choose_color("tab_text"))
        color_layout.addWidget(self.tab_color_btn)
        
        custom_layout.addRow(tr("settings.colors.primary") + ":", color_layout)
        
        # 字体设置
        font_layout = QHBoxLayout()
        
        self.font_size_combo = QComboBox()
        self.font_size_combo.addItems([
            tr("settings.fonts.small"),
            tr("settings.fonts.medium"),
            tr("settings.fonts.large")
        ])
        self.font_size_combo.setCurrentText(tr("settings.fonts.medium"))
        font_layout.addWidget(QLabel(tr("settings.fonts.size") + ":"))
        font_layout.addWidget(self.font_size_combo)
        
        self.font_weight_combo = QComboBox()
        self.font_weight_combo.addItems([
            tr("settings.fonts.normal"),
            tr("settings.fonts.bold")
        ])
        self.font_weight_combo.setCurrentText(tr("settings.fonts.normal"))
        font_layout.addWidget(QLabel(tr("settings.fonts.weight") + ":"))
        font_layout.addWidget(self.font_weight_combo)
        
        custom_layout.addRow(tr("settings.fonts.size") + ":", font_layout)
        
        # 自定义主题按钮
        self.custom_theme_btn = QPushButton(tr("settings.apply_custom_theme"))
        self.custom_theme_btn.clicked.connect(self.apply_custom_theme)
        custom_layout.addRow("", self.custom_theme_btn)
        
        layout.addWidget(custom_group)
        
        # 窗口设置组
        window_group = QGroupBox(tr("settings.window_settings"))
        window_layout = QFormLayout(window_group)
        
        # 窗口大小
        size_layout = QHBoxLayout()
        self.window_width_spin = QSpinBox()
        self.window_width_spin.setRange(800, 2000)
        self.window_width_spin.setValue(1200)
        size_layout.addWidget(self.window_width_spin)
        size_layout.addWidget(QLabel("x"))
        self.window_height_spin = QSpinBox()
        self.window_height_spin.setRange(600, 1500)
        self.window_height_spin.setValue(800)
        size_layout.addWidget(self.window_height_spin)
        window_layout.addRow(tr("settings.window_size"), size_layout)
        
        # 语言选择
        language_layout = QHBoxLayout()
        language_layout.addWidget(QLabel(tr("settings.language")))
        self.language_combo = QComboBox()
        
        # 添加支持的语言选项
        language_service = get_language_service()
        supported_languages = language_service.get_supported_languages()
        
        for lang in supported_languages:
            info = language_service.get_language_info(lang)
            if info:
                self.language_combo.addItem(f"{info['name']} ({lang})", lang)
        
        # 设置当前语言
        current_lang = language_service.get_current_language()
        current_index = self.language_combo.findData(current_lang)
        if current_index >= 0:
            self.language_combo.setCurrentIndex(current_index)
        
        self.language_combo.currentIndexChanged.connect(self.on_language_changed)
        language_layout.addWidget(self.language_combo)
        window_layout.addRow(tr("settings.language"), language_layout)
        
        layout.addWidget(window_group)
        
        # 连接信号
        self.setup_theme_connections()
        
        # 加载当前设置
        self.load_ui_settings()
        
        self.tab_widget.addTab(widget, tr("settings.title"))
    
    def create_theme_buttons(self):
        """创建主题选择按钮"""
        try:
            # 获取可用主题
            available_themes = theme_config_service.get_available_themes()
            
            # 主题按钮映射
            self.theme_buttons = {}
            
            for theme_id in available_themes:
                theme_info = theme_config_service.get_theme_info(theme_id)
                if theme_info:
                    btn = QPushButton(theme_info['name'])
                    btn.setCheckable(True)
                    btn.clicked.connect(lambda checked, tid=theme_id: self.select_theme(tid))
                    
                    # 设置按钮样式
                    self.set_theme_button_style(btn, theme_id)
                    
                    self.theme_buttons[theme_id] = btn
                    self.theme_grid_layout.addWidget(btn)
            
            # 添加自定义主题按钮
            custom_btn = QPushButton(tr("settings.custom"))
            custom_btn.setCheckable(True)
            custom_btn.clicked.connect(lambda checked: self.select_theme('custom'))
            self.theme_buttons['custom'] = custom_btn
            self.theme_grid_layout.addWidget(custom_btn)
            
        except Exception as e:
            self.logger.error(f"创建主题按钮失败: {e}")
    
    def set_theme_button_style(self, button, theme_id):
        """设置主题按钮样式"""
        try:
            theme_config = theme_config_service.get_preset_theme_config(theme_id)
            if theme_config and 'colors' in theme_config:
                colors = theme_config['colors']
                primary_color = colors.get('primary', '#0078d4')
                background_color = colors.get('background', '#ffffff')
                text_color = colors.get('text', '#000000')
                
                style = f"""
                QPushButton {{
                    background-color: {background_color};
                    color: {text_color};
                    border: 2px solid {primary_color};
                    border-radius: 5px;
                    padding: 8px 12px;
                    font-weight: bold;
                }}
                QPushButton:hover {{
                    background-color: {primary_color};
                    color: {background_color};
                }}
                QPushButton:checked {{
                    background-color: {primary_color};
                    color: {background_color};
                    border: 2px solid {text_color};
                }}
                """
                button.setStyleSheet(style)
                
        except Exception as e:
            self.logger.error(f"设置主题按钮样式失败: {e}")
    
    def create_theme_preview(self, parent_layout):
        """创建主题预览区域"""
        try:
            # 预览标签
            preview_label = QLabel(tr("settings.theme_preview"))
            preview_label.setStyleSheet("font-weight: bold; margin-top: 10px;")
            parent_layout.addWidget(preview_label)
            
            # 预览框架
            self.preview_frame = QFrame()
            self.preview_frame.setFrameStyle(QFrame.Shape.StyledPanel)
            self.preview_frame.setFixedHeight(100)
            self.preview_frame.setStyleSheet("""
                QFrame {
                    background-color: #f0f0f0;
                    border: 1px solid #cccccc;
                    border-radius: 5px;
                }
            """)
            
            # 预览内容布局
            preview_layout = QHBoxLayout(self.preview_frame)
            preview_layout.setContentsMargins(10, 10, 10, 10)
            
            # 预览组件
            self.preview_button = QPushButton(tr("settings.theme_preview"))
            self.preview_button.setFixedSize(60, 30)
            preview_layout.addWidget(self.preview_button)
            
            self.preview_edit = QLineEdit(tr("settings.theme_preview"))
            self.preview_edit.setFixedSize(100, 30)
            preview_layout.addWidget(self.preview_edit)
            
            self.preview_label = QLabel(tr("settings.theme_preview"))
            self.preview_label.setFixedSize(60, 30)
            preview_layout.addWidget(self.preview_label)
            
            preview_layout.addStretch()
            parent_layout.addWidget(self.preview_frame)
            
        except Exception as e:
            self.logger.error(f"创建主题预览失败: {e}")
    
    def setup_theme_connections(self):
        """设置主题相关信号连接"""
        try:
            # 字体设置变化
            self.font_size_combo.currentTextChanged.connect(self.update_font_preview)
            self.font_weight_combo.currentTextChanged.connect(self.update_font_preview)
            
        except Exception as e:
            self.logger.error(f"设置主题连接失败: {e}")
    
    def select_theme(self, theme_id):
        """选择主题"""
        try:
            # 更新按钮状态
            for tid, btn in self.theme_buttons.items():
                btn.setChecked(tid == theme_id)
            
            # 应用主题
            if theme_id == 'custom':
                self.show_custom_theme_options()
            else:
                self.apply_preset_theme(theme_id)
                self.update_theme_preview(theme_id)
            
        except Exception as e:
            self.logger.error(f"选择主题失败: {e}")
    
    def apply_preset_theme(self, theme_id):
        """应用预设主题"""
        try:
            # 通过主题配置服务应用主题
            success = theme_config_service.apply_theme_config(theme_id)
            
            if success:
                # 通过主题服务应用样式
                theme_service.apply_theme(theme_id)
                self.logger.info(f"已应用预设主题: {theme_id}")
            else:
                QMessageBox.warning(self, "警告", f"应用主题失败: {theme_id}")
                
        except Exception as e:
            self.logger.error(f"应用预设主题失败: {e}")
            QMessageBox.critical(self, "错误", f"应用预设主题失败: {e}")
    
    def update_theme_preview(self, theme_id):
        """更新主题预览"""
        try:
            theme_config = theme_config_service.get_preset_theme_config(theme_id)
            if theme_config and 'colors' in theme_config:
                colors = theme_config['colors']
                self.apply_preview_styles(colors)
                
        except Exception as e:
            self.logger.error(f"更新主题预览失败: {e}")
    
    def apply_preview_styles(self, colors):
        """应用预览样式"""
        try:
            primary_color = colors.get('primary', '#0078d4')
            background_color = colors.get('background', '#ffffff')
            text_color = colors.get('text', '#000000')
            
            # 更新预览框架样式
            self.preview_frame.setStyleSheet(f"""
                QFrame {{
                    background-color: {background_color};
                    border: 1px solid {primary_color};
                    border-radius: 5px;
                }}
            """)
            
            # 更新预览按钮样式
            self.preview_button.setStyleSheet(f"""
                QPushButton {{
                    background-color: {primary_color};
                    color: {background_color};
                    border: 1px solid {primary_color};
                    border-radius: 3px;
                }}
            """)
            
            # 更新预览输入框样式
            self.preview_edit.setStyleSheet(f"""
                QLineEdit {{
                    background-color: {background_color};
                    color: {text_color};
                    border: 1px solid {primary_color};
                    border-radius: 3px;
                }}
            """)
            
            # 更新预览标签样式
            self.preview_label.setStyleSheet(f"""
                QLabel {{
                    color: {text_color};
                }}
            """)
            
        except Exception as e:
            self.logger.error(f"应用预览样式失败: {e}")
    
    def choose_color(self, color_type):
        """选择颜色"""
        try:
            color = QColorDialog.getColor()
            if color.isValid():
                color_hex = color.name()
                
                # 更新按钮文本显示颜色
                if color_type == "primary":
                    self.primary_color_btn.setText(f"{tr('settings.colors.primary')} #{color_hex}")
                    self.primary_color_btn.setStyleSheet(f"background-color: {color_hex}; color: white;")
                elif color_type == "background":
                    self.background_color_btn.setText(f"{tr('settings.colors.background')} #{color_hex}")
                    self.background_color_btn.setStyleSheet(f"background-color: {color_hex}; color: white;")
                elif color_type == "text":
                    self.text_color_btn.setText(f"{tr('settings.colors.text')} #{color_hex}")
                    self.text_color_btn.setStyleSheet(f"background-color: {color_hex}; color: white;")
                elif color_type == "tab_text":
                    self.tab_color_btn.setText(f"{tr('settings.colors.tab_text')} #{color_hex}")
                    self.tab_color_btn.setStyleSheet(f"background-color: {color_hex}; color: white;")
                
                # 存储颜色值
                if not hasattr(self, 'custom_colors'):
                    self.custom_colors = {}
                self.custom_colors[color_type] = color_hex
                
        except Exception as e:
            self.logger.error(f"选择颜色失败: {e}")
    
    def apply_custom_theme(self):
        """应用自定义主题"""
        try:
            if not hasattr(self, 'custom_colors'):
                QMessageBox.warning(self, tr("settings.messages.warning"), tr("settings.messages.warning"))
                return
            
            # 获取字体设置
            font_size_map = {tr("settings.fonts.small"): "small", tr("settings.fonts.medium"): "medium", tr("settings.fonts.large"): "large"}
            font_weight_map = {tr("settings.fonts.normal"): "normal", tr("settings.fonts.bold"): "bold"}
            
            font_size = font_size_map.get(self.font_size_combo.currentText(), "medium")
            font_weight = font_weight_map.get(self.font_weight_combo.currentText(), "normal")
            
            # 创建自定义主题配置
            custom_config = {
                'enabled': True,
                'colors': self.custom_colors,
                'fonts': {
                    'size': font_size,
                    'weight': font_weight
                }
            }
            
            # 应用自定义主题
            success = theme_config_service.create_custom_theme(
                custom_config['colors'], 
                custom_config['fonts']
            )
            
            if success:
                # 选择自定义主题
                self.select_theme('custom')
                
                # 同时保存字体设置到UI配置文件
                self.save_font_settings_to_ui_config(font_size, font_weight)
                
                QMessageBox.information(self, tr("settings.messages.success"), tr("settings.messages.success"))
            else:
                QMessageBox.warning(self, tr("settings.messages.warning"), tr("settings.messages.warning"))
                
        except Exception as e:
            self.logger.error(f"应用自定义主题失败: {e}")
            QMessageBox.critical(self, tr("settings.messages.error"), tr("settings.messages.error"))
    
    def save_font_settings_to_ui_config(self, font_size: str, font_weight: str):
        """保存字体设置到UI配置文件"""
        try:
            import json
            import os
            
            # 字体大小映射 - 增加差异使其更明显
            font_size_map = {'small': 9, 'medium': 12, 'large': 16}
            actual_font_size = font_size_map.get(font_size, 12)
            
            # UI配置文件路径
            ui_config_file = "configs/app/ui.json"
            
            # 确保目录存在
            os.makedirs(os.path.dirname(ui_config_file), exist_ok=True)
            
            # 读取现有配置
            config = {}
            if os.path.exists(ui_config_file):
                with open(ui_config_file, 'r', encoding='utf-8') as f:
                    config = json.load(f)
            
            # 更新字体设置
            config['font_size'] = actual_font_size
            config['font_family'] = "Microsoft YaHei"  # 默认字体族
            
            # 保存配置
            with open(ui_config_file, 'w', encoding='utf-8') as f:
                json.dump(config, f, ensure_ascii=False, indent=2)
            
            self.logger.info(f"已保存字体设置到UI配置: 大小={actual_font_size}, 粗细={font_weight}")
            
        except Exception as e:
            self.logger.error(f"保存字体设置到UI配置失败: {e}")
    
    def show_custom_theme_options(self):
        """显示自定义主题选项"""
        try:
            # 启用自定义设置组
            # 这里可以添加更多自定义选项的显示逻辑
            pass
            
        except Exception as e:
            self.logger.error(f"显示自定义主题选项失败: {e}")
    
    def update_font_preview(self):
        """更新字体预览"""
        try:
            # 获取当前字体设置
            font_size_map = {tr("settings.fonts.small"): 9, tr("settings.fonts.medium"): 12, tr("settings.fonts.large"): 16}
            font_weight_map = {tr("settings.fonts.normal"): "normal", tr("settings.fonts.bold"): "bold"}
            
            size = font_size_map.get(self.font_size_combo.currentText(), 12)
            weight = font_weight_map.get(self.font_weight_combo.currentText(), "normal")
            
            # 更新预览组件字体
            font = QFont()
            font.setPointSize(size)
            font.setBold(weight == "bold")
            
            self.preview_button.setFont(font)
            self.preview_edit.setFont(font)
            self.preview_label.setFont(font)
            
        except Exception as e:
            self.logger.error(f"更新字体预览失败: {e}")
    
    def load_ui_settings(self):
        """加载UI设置"""
        try:
            # 加载当前主题
            current_theme = theme_config_service.get_current_theme()
            if current_theme in self.theme_buttons:
                self.theme_buttons[current_theme].setChecked(True)
            
            # 加载自定义主题配置
            custom_config = theme_config_service.get_custom_theme()
            if custom_config.get('enabled', False):
                # 加载自定义颜色
                colors = custom_config.get('colors', {})
                if colors:
                    self.custom_colors = colors
                    self.update_custom_color_buttons()
                
                # 加载自定义字体
                fonts = custom_config.get('fonts', {})
                if fonts:
                    font_size_map = {"small": tr("settings.fonts.small"), "medium": tr("settings.fonts.medium"), "large": tr("settings.fonts.large")}
                    font_weight_map = {"normal": tr("settings.fonts.normal"), "bold": tr("settings.fonts.bold")}
                    
                    size = font_size_map.get(fonts.get('size', 'medium'), tr("settings.fonts.medium"))
                    weight = font_weight_map.get(fonts.get('weight', 'normal'), tr("settings.fonts.normal"))
                    
                    self.font_size_combo.setCurrentText(size)
                    self.font_weight_combo.setCurrentText(weight)
            
        except Exception as e:
            self.logger.error(f"加载UI设置失败: {e}")
    
    def update_custom_color_buttons(self):
        """更新自定义颜色按钮显示"""
        try:
            if hasattr(self, 'custom_colors'):
                colors = self.custom_colors
                
                if 'primary' in colors:
                    self.primary_color_btn.setText(f"{tr('settings.colors.primary')} #{colors['primary']}")
                    self.primary_color_btn.setStyleSheet(f"background-color: {colors['primary']}; color: white;")
                
                if 'background' in colors:
                    self.background_color_btn.setText(f"{tr('settings.colors.background')} #{colors['background']}")
                    self.background_color_btn.setStyleSheet(f"background-color: {colors['background']}; color: white;")
                
                if 'text' in colors:
                    self.text_color_btn.setText(f"{tr('settings.colors.text')} #{colors['text']}")
                    self.text_color_btn.setStyleSheet(f"background-color: {colors['text']}; color: white;")
                
                if 'tab_text' in colors:
                    self.tab_color_btn.setText(f"{tr('settings.colors.tab_text')} #{colors['tab_text']}")
                    self.tab_color_btn.setStyleSheet(f"background-color: {colors['tab_text']}; color: white;")
                    
        except Exception as e:
            self.logger.error(f"更新自定义颜色按钮失败: {e}")
    
    def on_language_changed(self, index):
        """语言选择改变"""
        try:
            # 获取选中的语言代码
            current_data = self.language_combo.currentData()
            current_text = self.language_combo.currentText()
            self.logger.info(f"语言选择改变 - 索引: {index}, 文本: {current_text}, 数据: {current_data}")
            
            if current_data:
                self.logger.info(f"开始语言切换: {current_data}")
                language_service = get_language_service()
                success = language_service.set_language(current_data)
                if success:
                    self.logger.info(f"语言切换成功: {current_data}")
                    # 通知主窗口重新应用语言
                    self.notify_main_window_language_changed(current_data)
                    self.logger.info(f"语言切换完成: {current_data}")
                else:
                    self.logger.warning(f"语言切换失败: {current_data}")
            else:
                self.logger.warning(f"无法获取语言代码，索引: {index}, 文本: {current_text}")
        except Exception as e:
            self.logger.error(f"语言切换失败: {e}")
    
    def notify_main_window_language_changed(self, language):
        """通知主窗口语言已改变"""
        try:
            self.logger.info(f"开始通知主窗口语言改变: {language}")
            self.logger.info(f"主窗口引用存在: {self.main_window is not None}")
            
            if self.main_window and hasattr(self.main_window, 'apply_language'):
                self.logger.info("使用主窗口引用通知语言改变")
                # 更新主窗口的语言配置
                if hasattr(self.main_window, 'app_config') and self.main_window.app_config:
                    self.main_window.app_config.ui.language = language
                
                # 重新应用语言（这会重新创建菜单）
                self.main_window.apply_language()
                self.logger.info(f"已通知主窗口语言改变: {language}")
            else:
                # 如果主窗口引用不存在，尝试通过父窗口找到主窗口
                parent = self.parent()
                while parent and not hasattr(parent, 'apply_language'):
                    parent = parent.parent()
                
                if parent and hasattr(parent, 'apply_language'):
                    # 更新主窗口的语言配置
                    if hasattr(parent, 'app_config') and parent.app_config:
                        parent.app_config.ui.language = language
                    
                    # 重新应用语言（这会重新创建菜单）
                    parent.apply_language()
                    self.logger.info(f"已通过父窗口通知主窗口语言改变: {language}")
                else:
                    # 如果找不到主窗口，尝试通过全局方式通知
                    self.logger.warning("未找到主窗口，尝试全局通知")
                    self.notify_global_language_change(language)
                
        except Exception as e:
            self.logger.error(f"通知主窗口语言改变失败: {e}")
    
    def notify_global_language_change(self, language):
        """全局语言改变通知"""
        try:
            # 通过信号或其他方式通知全局语言改变
            # 这里我们可以直接调用语言服务的全局更新
            from services.language_service import get_language_service
            language_service = get_language_service()
            
            # 触发语言改变信号
            if hasattr(language_service, 'language_changed'):
                language_service.language_changed.emit(language)
            
            self.logger.info(f"已发送全局语言改变通知: {language}")
            
        except Exception as e:
            self.logger.error(f"全局语言改变通知失败: {e}")
    
    def create_audio_tab(self):
        """创建音频设置标签页"""
        widget = QFrame()
        widget.setFrameStyle(QFrame.Shape.StyledPanel)
        layout = QVBoxLayout(widget)
        layout.setContentsMargins(10, 10, 10, 10)
        
        # 音频格式设置组
        format_group = QGroupBox(tr("settings.audio_format_settings"))
        format_layout = QFormLayout(format_group)
        
        # 默认格式
        self.audio_format_combo = QComboBox()
        self.audio_format_combo.addItems(["wav", "mp3", "ogg", "m4a"])
        format_layout.addRow(tr("settings.default_format") + ":", self.audio_format_combo)
        
        # 采样率
        self.sample_rate_combo = QComboBox()
        self.sample_rate_combo.addItems(["8000", "16000", "22050", "44100", "48000"])
        self.sample_rate_combo.setCurrentText("44100")
        format_layout.addRow(tr("settings.sample_rate") + ":", self.sample_rate_combo)
        
        # 比特率
        self.bitrate_spin = QSpinBox()
        self.bitrate_spin.setRange(64, 320)
        self.bitrate_spin.setValue(128)
        format_layout.addRow(tr("settings.bitrate") + ":", self.bitrate_spin)
        
        layout.addWidget(format_group)
        
        # 文件设置组
        file_group = QGroupBox(tr("settings.file_settings"))
        file_layout = QFormLayout(file_group)
        
        # 默认输出目录
        output_layout = QHBoxLayout()
        self.output_dir_edit = QLineEdit()
        self.output_dir_edit.setText("./output")
        output_layout.addWidget(self.output_dir_edit)
        
        browse_output_button = QPushButton(tr("settings.browse"))
        browse_output_button.clicked.connect(self.browse_output_dir)
        output_layout.addWidget(browse_output_button)
        file_layout.addRow(tr("settings.output_directory") + ":", output_layout)
        
        # 临时目录
        temp_layout = QHBoxLayout()
        self.temp_dir_edit = QLineEdit()
        self.temp_dir_edit.setText("./temp")
        temp_layout.addWidget(self.temp_dir_edit)
        
        browse_temp_button = QPushButton(tr("settings.browse"))
        browse_temp_button.clicked.connect(self.browse_temp_dir)
        temp_layout.addWidget(browse_temp_button)
        file_layout.addRow(tr("settings.temp_directory") + ":", temp_layout)
        
        # 自动清理临时文件
        self.auto_clean_checkbox = QCheckBox(tr("settings.auto_clean_temp_files"))
        self.auto_clean_checkbox.setChecked(True)
        file_layout.addRow("", self.auto_clean_checkbox)
        
        layout.addWidget(file_group)
        
        self.tab_widget.addTab(widget, tr("settings.audio_settings"))
    
    def load_available_engines(self):
        """加载可用的TTS引擎"""
        try:
            # 清空现有选项
            self.tts_engine_combo.clear()
            
            # 定义引擎显示顺序：piper_tts 第一，其他按原顺序
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
                        self.tts_engine_combo.addItem(f"{engine} ✓")
                    else:
                        # 不可用引擎，添加不可用标记
                        self.tts_engine_combo.addItem(f"{engine} ✗")
            
            # 添加其他未在优先列表中的引擎
            for engine in all_engines:
                if engine not in preferred_order:
                    if engine in available_engines:
                        # 可用引擎，添加可用标记
                        self.tts_engine_combo.addItem(f"{engine} ✓")
                    else:
                        # 不可用引擎，添加不可用标记
                        self.tts_engine_combo.addItem(f"{engine} ✗")
            
            # 设置默认选择为第一个可用引擎
            if available_engines:
                # 优先选择 piper_tts，如果不可用则选择第一个可用的
                if 'piper_tts' in available_engines:
                    self.tts_engine_combo.setCurrentText("piper_tts ✓")
                else:
                    self.tts_engine_combo.setCurrentText(f"{available_engines[0]} ✓")
            
            self.logger.info(f"加载了 {len(all_engines)} 个TTS引擎，其中 {len(available_engines)} 个可用")
            
        except Exception as e:
            self.logger.error(f"加载可用引擎失败: {e}")
            # 如果失败，使用硬编码的引擎列表作为备用
            self.tts_engine_combo.addItems(["piper_tts", "edge_tts", "pyttsx3"])

    def create_tts_tab(self):
        """创建TTS设置标签页"""
        widget = QFrame()
        widget.setFrameStyle(QFrame.Shape.StyledPanel)
        layout = QVBoxLayout(widget)
        layout.setContentsMargins(10, 10, 10, 10)
        
        # TTS引擎设置组
        engine_group = QGroupBox(tr("settings.tts_engine_settings"))
        engine_layout = QFormLayout(engine_group)
        
        # 默认引擎
        self.tts_engine_combo = QComboBox()
        self.load_available_engines()
        self.tts_engine_combo.currentTextChanged.connect(self.on_tts_engine_changed)
        engine_layout.addRow(tr("settings.default_engine") + ":", self.tts_engine_combo)
        
        # 默认语音
        self.default_voice_edit = QLineEdit()
        self.default_voice_edit.setText("zh-CN-XiaoxiaoNeural")
        engine_layout.addRow(tr("settings.default_voice") + ":", self.default_voice_edit)
        
        layout.addWidget(engine_group)
        
        # 语音参数设置组
        params_group = QGroupBox(tr("settings.voice_params_settings"))
        params_layout = QFormLayout(params_group)
        
        # 默认语速
        self.default_rate_spin = QSpinBox()
        self.default_rate_spin.setRange(10, 300)
        self.default_rate_spin.setValue(100)
        params_layout.addRow(tr("settings.default_rate") + ":", self.default_rate_spin)
        
        # 默认音调
        self.default_pitch_spin = QSpinBox()
        self.default_pitch_spin.setRange(-50, 50)
        self.default_pitch_spin.setValue(0)
        params_layout.addRow(tr("settings.default_pitch") + ":", self.default_pitch_spin)
        
        # 默认音量
        self.default_volume_spin = QSpinBox()
        self.default_volume_spin.setRange(0, 100)
        self.default_volume_spin.setValue(100)
        params_layout.addRow(tr("settings.default_volume") + ":", self.default_volume_spin)
        
        layout.addWidget(params_group)
        
        self.tab_widget.addTab(widget, tr("settings.tts_settings"))
    
    def create_advanced_tab(self):
        """创建高级设置标签页"""
        widget = QFrame()
        widget.setFrameStyle(QFrame.Shape.StyledPanel)
        layout = QVBoxLayout(widget)
        layout.setContentsMargins(10, 10, 10, 10)
        
        # 性能设置组
        performance_group = QGroupBox(tr("settings.performance_settings"))
        performance_layout = QFormLayout(performance_group)
        
        # 最大并发任务数
        self.max_tasks_spin = QSpinBox()
        self.max_tasks_spin.setRange(1, 10)
        self.max_tasks_spin.setValue(2)
        performance_layout.addRow(tr("settings.max_concurrent_tasks") + ":", self.max_tasks_spin)
        
        # 内存限制
        self.memory_limit_spin = QSpinBox()
        self.memory_limit_spin.setRange(256, 8192)
        self.memory_limit_spin.setValue(1024)
        performance_layout.addRow(tr("settings.memory_limit") + ":", self.memory_limit_spin)
        
        # 硬件加速
        self.hardware_accel_checkbox = QCheckBox(tr("settings.enable_hardware_acceleration"))
        performance_layout.addRow("", self.hardware_accel_checkbox)
        
        layout.addWidget(performance_group)
        
        # 调试设置组
        debug_group = QGroupBox(tr("settings.debug_settings"))
        debug_layout = QFormLayout(debug_group)
        
        # 调试模式
        self.debug_mode_checkbox = QCheckBox(tr("settings.debug_mode"))
        debug_layout.addRow("", self.debug_mode_checkbox)
        
        # 日志级别
        self.log_level_combo = QComboBox()
        self.log_level_combo.addItems(["DEBUG", "INFO", "WARNING", "ERROR"])
        self.log_level_combo.setCurrentText("INFO")
        debug_layout.addRow(tr("settings.log_level") + ":", self.log_level_combo)
        
        layout.addWidget(debug_group)
        
        # 文本处理设置组
        text_group = QGroupBox(tr("settings.text_processing_settings"))
        text_layout = QFormLayout(text_group)
        
        # 最大文本长度
        self.max_text_length_spin = QSpinBox()
        self.max_text_length_spin.setRange(1000, 10000000)
        self.max_text_length_spin.setValue(1000000)
        text_layout.addRow(tr("settings.max_text_length") + ":", self.max_text_length_spin)
        
        # 自动分割长度
        self.auto_split_length_spin = QSpinBox()
        self.auto_split_length_spin.setRange(500, 10000)
        self.auto_split_length_spin.setValue(2000)
        text_layout.addRow(tr("settings.auto_split_length") + ":", self.auto_split_length_spin)
        
        # 自动检测章节
        self.auto_detect_chapters_checkbox = QCheckBox(tr("settings.auto_detect_chapters"))
        self.auto_detect_chapters_checkbox.setChecked(True)
        text_layout.addRow("", self.auto_detect_chapters_checkbox)
        
        layout.addWidget(text_group)
        
        # 章节检测规则设置组
        chapter_group = QGroupBox(tr("settings.chapter_detection_rules"))
        chapter_layout = QVBoxLayout(chapter_group)
        
        # 当前规则说明
        rules_label = QLabel(tr("settings.current_chapter_rules"))
        rules_label.setStyleSheet("font-weight: bold; margin-bottom: 5px;")
        chapter_layout.addWidget(rules_label)
        
        # 规则说明文本
        self.rules_text = QTextEdit()
        self.rules_text.setReadOnly(True)
        self.rules_text.setMaximumHeight(120)
        self.rules_text.setPlainText(tr("settings.chapter_rules_description"))
        chapter_layout.addWidget(self.rules_text)
        
        # 规则管理按钮
        rules_button_layout = QHBoxLayout()
        
        self.add_rule_button = QPushButton(tr("settings.add_rule"))
        self.add_rule_button.clicked.connect(self.add_chapter_rule)
        rules_button_layout.addWidget(self.add_rule_button)
        
        self.edit_rule_button = QPushButton(tr("settings.edit_rule"))
        self.edit_rule_button.clicked.connect(self.edit_chapter_rules)
        rules_button_layout.addWidget(self.edit_rule_button)
        
        self.test_rule_button = QPushButton(tr("settings.test_rule"))
        self.test_rule_button.clicked.connect(self.test_chapter_rules)
        rules_button_layout.addWidget(self.test_rule_button)
        
        rules_button_layout.addStretch()
        chapter_layout.addLayout(rules_button_layout)
        
        layout.addWidget(chapter_group)
        
        self.tab_widget.addTab(widget, tr("settings.advanced_settings"))
    
    def setup_connections(self):
        """设置信号槽连接"""
        # 语言改变时立即应用（已在create_ui_tab中连接）
    
    def load_settings(self):
        """加载设置"""
        try:
            self.current_config = self.settings_controller.load_settings()
            
            # 更新UI
            self.update_ui_from_config()
            
            self.logger.info(tr("settings.messages.settings_loaded"))
            
        except Exception as e:
            self.logger.error(f"加载设置失败: {e}")
            QMessageBox.critical(self, tr("settings.messages.error"), tr("settings.messages.load_settings_failed", error=str(e)))
    
    def update_ui_from_config(self):
        """从配置更新UI"""
        try:
            if not self.current_config:
                return
            
            # 界面设置
            # 主题设置通过新的主题配置服务处理
            current_theme = theme_config_service.get_current_theme()
            if hasattr(self, 'theme_buttons') and current_theme in self.theme_buttons:
                self.theme_buttons[current_theme].setChecked(True)
            
            # 设置语言选择框（使用语言代码）
            if hasattr(self.current_config, 'language') and self.current_config.language:
                # 如果配置中的语言是显示名称格式，提取语言代码
                config_language = self.current_config.language
                
                # 确保 config_language 是字符串类型
                if isinstance(config_language, int):
                    # 如果是整数，使用默认语言
                    config_language = "zh-CN"
                    self.logger.warning(f"配置中的语言是整数类型: {self.current_config.language}，使用默认语言: zh-CN")
                elif isinstance(config_language, str):
                    # 提取语言代码（如 "简体中文 (zh-CN)" -> "zh-CN"）
                    if "(" in config_language and ")" in config_language:
                        config_language = config_language.split("(")[-1].split(")")[0]
                else:
                    # 其他类型，使用默认语言
                    config_language = "zh-CN"
                    self.logger.warning(f"配置中的语言类型不支持: {type(config_language)}，使用默认语言: zh-CN")
                
                # 找到对应的索引
                current_index = self.language_combo.findData(config_language)
                if current_index >= 0:
                    self.language_combo.setCurrentIndex(current_index)
            self.window_width_spin.setValue(self.current_config.window_width)
            self.window_height_spin.setValue(self.current_config.window_height)
            # 窗口位置设置已移除，不再需要设置
            
            # 音频设置
            self.audio_format_combo.setCurrentText(self.current_config.default_audio_format)
            self.sample_rate_combo.setCurrentText(str(self.current_config.default_sample_rate))
            self.bitrate_spin.setValue(self.current_config.default_bitrate)
            self.output_dir_edit.setText(self.current_config.default_output_dir)
            self.temp_dir_edit.setText(self.current_config.temp_dir)
            self.auto_clean_checkbox.setChecked(self.current_config.auto_clean_temp)
            
            # TTS设置
            # 临时断开信号连接，避免在加载时触发保存
            self.tts_engine_combo.currentTextChanged.disconnect()
            self.tts_engine_combo.setCurrentText(self.current_config.default_tts_engine)
            # 根据引擎设置默认语音
            clean_engine = self.current_config.default_tts_engine.replace(" ✓", "").replace(" ✗", "")
            default_voice = self._get_default_voice_for_engine(clean_engine)
            self.default_voice_edit.setText(default_voice)
            # 重新连接信号
            self.tts_engine_combo.currentTextChanged.connect(self.on_tts_engine_changed)
            self.default_rate_spin.setValue(int(self.current_config.default_rate * 100))
            self.default_pitch_spin.setValue(int(self.current_config.default_pitch))
            self.default_volume_spin.setValue(int(self.current_config.default_volume * 100))
            
            # 高级设置
            self.max_tasks_spin.setValue(self.current_config.max_concurrent_tasks)
            self.memory_limit_spin.setValue(self.current_config.memory_limit_mb)
            self.hardware_accel_checkbox.setChecked(self.current_config.enable_hardware_acceleration)
            self.debug_mode_checkbox.setChecked(self.current_config.debug_mode)
            self.log_level_combo.setCurrentText(self.current_config.log_level)
            self.max_text_length_spin.setValue(self.current_config.max_text_length)
            self.auto_split_length_spin.setValue(self.current_config.auto_split_length)
            self.auto_detect_chapters_checkbox.setChecked(self.current_config.auto_detect_chapters)
            
        except Exception as e:
            self.logger.error(f"更新UI失败: {e}")
    
    def update_config_from_ui(self):
        """从UI更新配置"""
        try:
            if not self.current_config:
                return
            
            # 界面设置
            # 主题设置通过新的主题配置服务处理
            current_theme = theme_config_service.get_current_theme()
            self.current_config.theme = current_theme
            
            # 获取当前选中的语言代码
            current_data = self.language_combo.currentData()
            if current_data:
                # 获取语言显示名称
                language_service = get_language_service()
                lang_info = language_service.language_config.get("language_info", {}).get(current_data, {})
                lang_name = lang_info.get("name", current_data)
                language_display = f"{lang_name} ({current_data})"
                self.current_config.language = language_display
            else:
                self.current_config.language = "简体中文 (zh-CN)"
            self.current_config.window_width = self.window_width_spin.value()
            self.current_config.window_height = self.window_height_spin.value()
            # 窗口位置设置已移除，使用默认值
            self.current_config.window_x = 100
            self.current_config.window_y = 100
            
            # 音频设置
            self.current_config.default_audio_format = self.audio_format_combo.currentText()
            self.current_config.default_sample_rate = int(self.sample_rate_combo.currentText())
            self.current_config.default_bitrate = self.bitrate_spin.value()
            self.current_config.default_output_dir = self.output_dir_edit.text()
            self.current_config.temp_dir = self.temp_dir_edit.text()
            self.current_config.auto_clean_temp = self.auto_clean_checkbox.isChecked()
            
            # TTS设置
            self.current_config.default_tts_engine = self.tts_engine_combo.currentText()
            self.current_config.default_voice = self.default_voice_edit.text()
            self.current_config.default_rate = self.default_rate_spin.value() / 100.0
            self.current_config.default_pitch = self.default_pitch_spin.value()
            self.current_config.default_volume = self.default_volume_spin.value() / 100.0
            
            # 高级设置
            self.current_config.max_concurrent_tasks = self.max_tasks_spin.value()
            self.current_config.memory_limit_mb = self.memory_limit_spin.value()
            self.current_config.enable_hardware_acceleration = self.hardware_accel_checkbox.isChecked()
            self.current_config.debug_mode = self.debug_mode_checkbox.isChecked()
            self.current_config.log_level = self.log_level_combo.currentText()
            self.current_config.max_text_length = self.max_text_length_spin.value()
            self.current_config.auto_split_length = self.auto_split_length_spin.value()
            self.current_config.auto_detect_chapters = self.auto_detect_chapters_checkbox.isChecked()
            
        except Exception as e:
            self.logger.error(f"更新配置失败: {e}")
    
    def browse_output_dir(self):
        """浏览输出目录"""
        try:
            output_dir = QFileDialog.getExistingDirectory(self, tr("settings.output_directory"))
            if output_dir:
                self.output_dir_edit.setText(output_dir)
                
        except Exception as e:
            self.logger.error(f"浏览输出目录失败: {e}")
    
    def browse_temp_dir(self):
        """浏览临时目录"""
        try:
            temp_dir = QFileDialog.getExistingDirectory(self, tr("settings.temp_directory"))
            if temp_dir:
                self.temp_dir_edit.setText(temp_dir)
                
        except Exception as e:
            self.logger.error(f"浏览临时目录失败: {e}")
    
    def apply_settings(self):
        """应用设置"""
        try:
            # 更新配置
            self.update_config_from_ui()
            
            # 验证配置
            validation_result = self.settings_controller.validate_settings(self.current_config)
            if not validation_result['valid']:
                QMessageBox.warning(self, tr("settings.messages.warning"), tr("settings.messages.settings_validation_failed") + "\n" + "\n".join(validation_result['issues']))
                return
            
            # 保存设置
            self.settings_controller.save_settings(self.current_config)
            
            # 应用主题（确保主题立即生效）
            from services.theme_service import theme_service
            theme_service.apply_theme(self.current_config.theme)
            
            # 发送信号
            self.settings_changed.emit(self.current_config)
            
            QMessageBox.information(self, tr("settings.messages.success"), tr("settings.messages.settings_applied"))
            self.logger.info("设置已应用")
            
        except Exception as e:
            self.logger.error(f"应用设置失败: {e}")
            QMessageBox.critical(self, tr("settings.messages.error"), tr("settings.messages.apply_settings_failed", error=str(e)))
    
    def reset_settings(self):
        """重置设置"""
        try:
            reply = QMessageBox.question(
                self, tr("settings.messages.confirm"), tr("settings.messages.reset_confirm"),
                QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No
            )
            
            if reply == QMessageBox.StandardButton.Yes:
                self.settings_controller.reset_to_defaults()
                self.load_settings()
                QMessageBox.information(self, tr("settings.messages.success"), tr("settings.messages.settings_reset"))
                
        except Exception as e:
            self.logger.error(f"重置设置失败: {e}")
            QMessageBox.critical(self, tr("settings.messages.error"), tr("settings.messages.reset_settings_failed", error=str(e)))
    
    def export_settings(self):
        """导出设置"""
        try:
            file_path, _ = QFileDialog.getSaveFileName(
                self, tr("settings.messages.export_settings"), "settings.ini", "INI文件 (*.ini)"
            )
            
            if file_path:
                self.settings_controller.export_settings(file_path)
                QMessageBox.information(self, tr("settings.messages.success"), tr("settings.messages.settings_exported", path=file_path))
                
        except Exception as e:
            self.logger.error(f"导出设置失败: {e}")
            QMessageBox.critical(self, tr("settings.messages.error"), tr("settings.messages.export_settings_failed", error=str(e)))
    
    def import_settings(self):
        """导入设置"""
        try:
            file_path, _ = QFileDialog.getOpenFileName(
                self, tr("settings.messages.import_settings"), "", "INI文件 (*.ini)"
            )
            
            if file_path:
                self.settings_controller.import_settings(file_path)
                self.load_settings()
                QMessageBox.information(self, tr("settings.messages.success"), tr("settings.messages.settings_imported", path=file_path))
                
        except Exception as e:
            self.logger.error(f"导入设置失败: {e}")
            QMessageBox.critical(self, tr("settings.messages.error"), tr("settings.messages.import_settings_failed", error=str(e)))
    
    def on_theme_changed(self, theme: str):
        """主题改变事件"""
        try:
            if not self.current_config:
                return
            
            # 更新配置
            self.current_config.theme = theme
            
            # 立即保存配置
            self.settings_controller.save_settings(self.current_config)
            
            # 应用全局主题（这会自动同步到主配置文件）
            theme_service.apply_theme(theme)
            
            self.logger.info(f"主题已更改为: {theme}")
            
        except Exception as e:
            self.logger.error(f"主题改变处理失败: {e}")
    
    def on_language_changed(self, language: str):
        """语言改变事件"""
        try:
            if not self.current_config:
                return
            
            # 更新配置
            self.current_config.language = language
            
            # 立即保存配置
            self.settings_controller.save_settings(self.current_config)
            
            # 应用语言（这会自动同步到主配置文件）
            from services.language_service import get_language_service
            get_language_service().set_language(language)
            
            self.logger.info(f"语言已更改为: {language}")
            
        except Exception as e:
            self.logger.error(f"语言改变处理失败: {e}")
    
    def on_tts_engine_changed(self, engine: str):
        """TTS引擎改变事件"""
        try:
            if not self.current_config:
                return
            
            # 清理引擎名称，移除可用性标记
            clean_engine = engine.replace(" ✓", "").replace(" ✗", "")
            
            # 根据引擎类型设置默认语音
            default_voice = self._get_default_voice_for_engine(clean_engine)
            
            # 更新默认语音输入框
            self.default_voice_edit.setText(default_voice)
            
            # 更新配置
            self.current_config.default_tts_engine = clean_engine
            self.current_config.default_voice = default_voice
            
            # 立即保存配置
            self.settings_controller.save_settings(self.current_config)
            
            self.logger.info(f"TTS引擎已更改为: {clean_engine}, 默认语音: {default_voice}")
            
        except Exception as e:
            self.logger.error(f"TTS引擎改变处理失败: {e}")
    
    def _get_default_voice_for_engine(self, engine: str) -> str:
        """根据引擎类型获取默认语音"""
        try:
            # 清理引擎名称，移除可用性标记
            clean_engine = engine.replace(" ✓", "").replace(" ✗", "")
            
            # 导入必要的服务
            from services.engine_config_service import EngineConfigService
            
            engine_config_service = EngineConfigService()
            engine_config = engine_config_service.load_engine_config(clean_engine)
            
            if engine_config and hasattr(engine_config, 'parameters') and hasattr(engine_config.parameters, 'voice_name'):
                return engine_config.parameters.voice_name
            
            # 如果无法从配置加载，使用硬编码的默认值
            default_voices = {
                'edge_tts': 'zh-CN-XiaoxiaoNeural',
                'piper_tts': 'zh_CN-huayan-medium',
                'pyttsx3': 'zh-CN-XiaoxiaoNeural'
            }
            
            return default_voices.get(clean_engine, 'zh-CN-XiaoxiaoNeural')
            
        except Exception as e:
            self.logger.error(f"获取引擎默认语音失败: {e}")
            return 'zh-CN-XiaoxiaoNeural'
    
    def update_theme_description(self, theme: str):
        """更新主题描述（已弃用，新界面使用主题按钮）"""
        try:
            # 新界面不再需要主题描述标签
            # 主题信息直接显示在按钮上
            pass
            
        except Exception as e:
            self.logger.error(f"更新主题描述失败: {e}")
    
    
    def apply_language(self, language: str):
        """应用语言"""
        try:
            # 这里可以实现语言切换逻辑
            # 目前只是记录日志，实际的语言切换需要重新加载界面文本
            self.logger.info(f"语言已切换到: {language}")
            
            # 发送语言改变信号
            self.settings_changed.emit(self.current_config)
            
        except Exception as e:
            self.logger.error(f"应用语言失败: {e}")
    
    def get_chapter_detection_rules_description(self) -> str:
        """获取章节检测规则说明"""
        return """当前支持的章节检测规则：

1. 中文章节格式：
   • 第[一二三四五六七八九十\\d]+章[：:\\s]*.*
   • 第[一二三四五六七八九十\\d]+节[：:\\s]*.*

2. 英文章节格式：
   • Chapter\\s+\\d+[：:\\s]*.*
   • Section\\s+\\d+[：:\\s]*.*

3. 数字章节格式：
   • ^\\d+\\s+.*

这些规则使用正则表达式匹配，支持：
- 中文数字和阿拉伯数字
- 冒号和空格分隔符
- 章节标题内容

您可以通过"编辑规则"按钮修改这些规则，或通过"添加规则"按钮添加新的检测模式。"""
    
    def add_chapter_rule(self):
        """添加章节检测规则"""
        try:
            # 获取新规则
            rule, ok = QInputDialog.getText(
                self, 
                "添加章节检测规则", 
                "请输入新的正则表达式规则:",
                text="^第\\d+章.*"
            )
            
            if ok and rule.strip():
                # 验证正则表达式
                import re
                try:
                    re.compile(rule)
                    
                    # 添加到配置中
                    if not hasattr(self.current_config, 'chapter_detection_rules'):
                        self.current_config.chapter_detection_rules = []
                    
                    self.current_config.chapter_detection_rules.append(rule)
                    
                    # 保存配置
                    self.settings_controller.save_settings(self.current_config)
                    
                    # 更新规则说明
                    self.rules_text.setPlainText(self.get_chapter_detection_rules_description())
                    
                    QMessageBox.information(self, "成功", f"规则已添加: {rule}")
                    self.logger.info(f"添加章节检测规则: {rule}")
                    
                except re.error as e:
                    QMessageBox.warning(self, "错误", f"正则表达式格式错误: {e}")
                    
        except Exception as e:
            self.logger.error(f"添加章节检测规则失败: {e}")
            QMessageBox.critical(self, "错误", f"添加规则失败: {e}")
    
    def edit_chapter_rules(self):
        """编辑章节检测规则"""
        try:
            # 创建编辑对话框
            dialog = QDialog(self)
            dialog.setWindowTitle("编辑章节检测规则")
            dialog.setModal(True)
            dialog.resize(600, 400)
            
            layout = QVBoxLayout(dialog)
            
            # 规则列表
            rules_label = QLabel("当前规则列表:")
            layout.addWidget(rules_label)
            
            rules_list = QListWidget()
            
            # 获取当前规则
            if hasattr(self.current_config, 'chapter_detection_rules'):
                for rule in self.current_config.chapter_detection_rules:
                    rules_list.addItem(rule)
            else:
                # 添加默认规则
                default_rules = [
                    r'第[一二三四五六七八九十\d]+章[：:\s]*.*',
                    r'Chapter\s+\d+[：:\s]*.*',
                    r'第[一二三四五六七八九十\d]+节[：:\s]*.*',
                    r'Section\s+\d+[：:\s]*.*',
                    r'^\d+\s+.*'
                ]
                for rule in default_rules:
                    rules_list.addItem(rule)
            
            layout.addWidget(rules_list)
            
            # 按钮
            button_layout = QHBoxLayout()
            
            add_btn = QPushButton("添加")
            add_btn.clicked.connect(lambda: self.add_rule_to_list(rules_list))
            button_layout.addWidget(add_btn)
            
            edit_btn = QPushButton("编辑")
            edit_btn.clicked.connect(lambda: self.edit_rule_in_list(rules_list))
            button_layout.addWidget(edit_btn)
            
            remove_btn = QPushButton("删除")
            remove_btn.clicked.connect(lambda: self.remove_rule_from_list(rules_list))
            button_layout.addWidget(remove_btn)
            
            button_layout.addStretch()
            layout.addLayout(button_layout)
            
            # 对话框按钮
            dialog_buttons = QDialogButtonBox(
                QDialogButtonBox.StandardButton.Ok | QDialogButtonBox.StandardButton.Cancel
            )
            dialog_buttons.accepted.connect(dialog.accept)
            dialog_buttons.rejected.connect(dialog.reject)
            layout.addWidget(dialog_buttons)
            
            # 显示对话框
            if dialog.exec() == QDialog.DialogCode.Accepted:
                # 保存规则
                rules = []
                for i in range(rules_list.count()):
                    rules.append(rules_list.item(i).text())
                
                self.current_config.chapter_detection_rules = rules
                self.settings_controller.save_settings(self.current_config)
                
                # 更新规则说明
                self.rules_text.setPlainText(self.get_chapter_detection_rules_description())
                
                QMessageBox.information(self, "成功", "章节检测规则已更新")
                self.logger.info(f"更新章节检测规则: {rules}")
                
        except Exception as e:
            self.logger.error(f"编辑章节检测规则失败: {e}")
            QMessageBox.critical(self, "错误", f"编辑规则失败: {e}")
    
    def add_rule_to_list(self, rules_list: QListWidget):
        """向规则列表添加规则"""
        try:
            rule, ok = QInputDialog.getText(
                self, 
                "添加规则", 
                "请输入正则表达式规则:",
                text="^第\\d+章.*"
            )
            
            if ok and rule.strip():
                # 验证正则表达式
                import re
                try:
                    re.compile(rule)
                    rules_list.addItem(rule)
                except re.error as e:
                    QMessageBox.warning(self, "错误", f"正则表达式格式错误: {e}")
                    
        except Exception as e:
            self.logger.error(f"添加规则到列表失败: {e}")
    
    def edit_rule_in_list(self, rules_list: QListWidget):
        """编辑列表中的规则"""
        try:
            current_item = rules_list.currentItem()
            if not current_item:
                QMessageBox.information(self, "提示", "请先选择要编辑的规则")
                return
            
            rule, ok = QInputDialog.getText(
                self, 
                "编辑规则", 
                "请输入正则表达式规则:",
                text=current_item.text()
            )
            
            if ok and rule.strip():
                # 验证正则表达式
                import re
                try:
                    re.compile(rule)
                    current_item.setText(rule)
                except re.error as e:
                    QMessageBox.warning(self, "错误", f"正则表达式格式错误: {e}")
                    
        except Exception as e:
            self.logger.error(f"编辑列表规则失败: {e}")
    
    def remove_rule_from_list(self, rules_list: QListWidget):
        """从列表中删除规则"""
        try:
            current_item = rules_list.currentItem()
            if not current_item:
                QMessageBox.information(self, "提示", "请先选择要删除的规则")
                return
            
            reply = QMessageBox.question(
                self, "确认", f"确定要删除规则 '{current_item.text()}' 吗？",
                QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No
            )
            
            if reply == QMessageBox.StandardButton.Yes:
                rules_list.takeItem(rules_list.row(current_item))
                
        except Exception as e:
            self.logger.error(f"删除列表规则失败: {e}")
    
    def test_chapter_rules(self):
        """测试章节检测规则"""
        try:
            # 创建测试对话框
            dialog = QDialog(self)
            dialog.setWindowTitle("测试章节检测规则")
            dialog.setModal(True)
            dialog.resize(500, 400)
            
            layout = QVBoxLayout(dialog)
            
            # 测试文本输入
            test_label = QLabel("输入测试文本:")
            layout.addWidget(test_label)
            
            test_text = QTextEdit()
            test_text.setPlainText("""第一章 开始
这是第一章的内容。

第二章 发展
这是第二章的内容。

Chapter 3: Conclusion
This is chapter 3 content.""")
            layout.addWidget(test_text)
            
            # 检测结果
            result_label = QLabel("检测结果:")
            layout.addWidget(result_label)
            
            result_text = QTextEdit()
            result_text.setReadOnly(True)
            layout.addWidget(result_text)
            
            # 测试按钮
            test_btn = QPushButton("测试检测")
            test_btn.clicked.connect(lambda: self.run_chapter_detection_test(test_text, result_text))
            layout.addWidget(test_btn)
            
            # 对话框按钮
            dialog_buttons = QDialogButtonBox(QDialogButtonBox.StandardButton.Close)
            dialog_buttons.rejected.connect(dialog.reject)
            layout.addWidget(dialog_buttons)
            
            # 显示对话框
            dialog.exec()
            
        except Exception as e:
            self.logger.error(f"测试章节检测规则失败: {e}")
            QMessageBox.critical(self, "错误", f"测试规则失败: {e}")
    
    def run_chapter_detection_test(self, test_text_widget: QTextEdit, result_widget: QTextEdit):
        """运行章节检测测试"""
        try:
            test_text = test_text_widget.toPlainText()
            
            # 获取当前规则
            if hasattr(self.current_config, 'chapter_detection_rules'):
                rules = self.current_config.chapter_detection_rules
            else:
                # 使用默认规则
                rules = [
                    r'第[一二三四五六七八九十\d]+章[：:\s]*.*',
                    r'Chapter\s+\d+[：:\s]*.*',
                    r'第[一二三四五六七八九十\d]+节[：:\s]*.*',
                    r'Section\s+\d+[：:\s]*.*',
                    r'^\d+\s+.*'
                ]
            
            # 执行检测
            import re
            lines = test_text.split('\n')
            results = []
            
            for i, line in enumerate(lines):
                line = line.strip()
                if not line:
                    continue
                
                for rule in rules:
                    if re.match(rule, line, re.IGNORECASE):
                        results.append(f"第{i+1}行: {line} ✓ (匹配规则: {rule})")
                        break
                else:
                    results.append(f"第{i+1}行: {line} ✗ (未匹配任何规则)")
            
            # 显示结果
            if results:
                result_widget.setPlainText('\n'.join(results))
            else:
                result_widget.setPlainText("未检测到任何章节标题")
                
        except Exception as e:
            self.logger.error(f"运行章节检测测试失败: {e}")
            result_widget.setPlainText(f"测试失败: {e}")
    
    def get_current_config(self) -> AppConfig:
        """获取当前配置"""
        return self.current_config
