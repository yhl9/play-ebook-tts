"""
动态参数UI生成器
"""

from PyQt6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QLabel, 
    QComboBox, QSlider, QSpinBox, QLineEdit,
    QCheckBox, QPushButton, QFileDialog, QGroupBox,
    QFormLayout, QScrollArea, QFrame, QTextEdit,
    QToolButton, QToolTip
)
from PyQt6.QtCore import Qt, pyqtSignal, QTimer
from PyQt6.QtGui import QFont, QIcon

from services.parameter_config_service import ParameterConfigService, ParameterDefinition
from services.language_service import get_text as tr, get_language_service
from utils.log_manager import LogManager


class DynamicParameterWidget(QWidget):
    """动态参数控件"""
    
    # 信号定义
    parameter_changed = pyqtSignal(str, object)  # 参数改变信号
    validation_changed = pyqtSignal(str, bool, str)  # 验证状态改变信号
    
    def __init__(self, parameter_def: ParameterDefinition, parent=None):
        super().__init__(parent)
        self.parameter_def = parameter_def
        self.logger = LogManager().get_logger(f"DynamicParameterWidget_{parameter_def.name}")
        
        self.widget = None
        self.value = parameter_def.default
        self.is_valid = True
        self.error_message = ""
        
        self.setup_ui()
        self.setup_connections()
    
    def _get_parameter_label(self):
        """获取参数的翻译标签"""
        # 定义参数名称到翻译键的映射
        param_translations = {
            'voice_name': tr('dynamic_parameter.voice_name'),
            'use_sapi': tr('dynamic_parameter.use_sapi'),
            'debug_mode': tr('dynamic_parameter.debug_mode'),
            'api_url': tr('dynamic_parameter.api_url'),
            'voice_config': tr('dynamic_parameter.voice_config'),
            'prompt_audio': tr('dynamic_parameter.prompt_audio'),
            'inference_mode': tr('dynamic_parameter.inference_mode'),
            'temperature': tr('dynamic_parameter.temperature'),
            'top_p': tr('dynamic_parameter.top_p'),
            'top_k': tr('dynamic_parameter.top_k'),
            'repetition_penalty': tr('dynamic_parameter.repetition_penalty'),
            'max_mel_tokens': tr('dynamic_parameter.max_mel_tokens'),
            'emotion': tr('dynamic_parameter.emotion'),
            'model_path': tr('dynamic_parameter.model_path'),
            'language': tr('dynamic_parameter.language'),
            'sample_rate': tr('dynamic_parameter.sample_rate'),
            'bit_depth': tr('dynamic_parameter.bit_depth'),
            'channels': tr('dynamic_parameter.channels'),
            'quality': tr('dynamic_parameter.quality'),
            'speed': tr('dynamic_parameter.speed'),
            'pitch': tr('dynamic_parameter.pitch'),
            'volume': tr('dynamic_parameter.volume'),
            'rate': tr('dynamic_parameter.rate'),
            'voice': tr('dynamic_parameter.voice'),
            'engine': tr('dynamic_parameter.engine'),
            'output_format': tr('dynamic_parameter.output_format'),
            'file_path': tr('dynamic_parameter.file_path'),
            'directory': tr('dynamic_parameter.directory'),
            'filename': tr('dynamic_parameter.filename'),
            'enable': tr('dynamic_parameter.enable'),
            'disable': tr('dynamic_parameter.disable'),
            'auto': tr('dynamic_parameter.auto'),
            'manual': tr('dynamic_parameter.manual'),
            'custom': tr('dynamic_parameter.custom'),
            'default': tr('dynamic_parameter.default'),
            'advanced': tr('dynamic_parameter.advanced'),
            'basic': tr('dynamic_parameter.basic'),
            'expert': tr('dynamic_parameter.expert'),
            'beginner': tr('dynamic_parameter.beginner')
        }
        
        # 如果参数名称在翻译映射中，使用翻译文本
        if self.parameter_def.name in param_translations:
            return param_translations[self.parameter_def.name]
        
        # 否则使用原始标签
        return self.parameter_def.label
    
    def setup_ui(self):
        """设置UI"""
        layout = QHBoxLayout(self)
        layout.setContentsMargins(0, 2, 0, 2)  # 减少上下边距
        layout.setSpacing(5)  # 减少间距
        
        # 参数标签 - 使用翻译键
        label_text = self._get_parameter_label()
        label = QLabel(label_text)
        label.setMinimumWidth(120)  # 设置最小宽度
        label.setMaximumWidth(150)  # 设置最大宽度
        if self.parameter_def.required:
            label.setText(f"{label_text} *")
            label.setStyleSheet("color: red;")
        
        # 创建参数控件
        self.widget = self._create_widget()
        
        # 为高级参数添加问号图标和工具提示
        help_button = None
        if self.parameter_def.name in ['temperature', 'top_p', 'top_k', 'repetition_penalty', 'max_mel_tokens']:
            help_button = QToolButton()
            help_button.setText("?")
            help_button.setStyleSheet("""
                QToolButton {
                    background-color: #f0f0f0;
                    border: 1px solid #ccc;
                    border-radius: 10px;
                    width: 20px;
                    height: 20px;
                    font-weight: bold;
                    color: #666;
                }
                QToolButton:hover {
                    background-color: #e0e0e0;
                    color: #333;
                }
            """)
            help_button.setToolTip(self._get_parameter_description())
            help_button.setCursor(Qt.CursorShape.PointingHandCursor)
        
        # 单位标签
        unit_label = None
        if self.parameter_def.unit:
            unit_label = QLabel(self.parameter_def.unit)
            unit_label.setStyleSheet("color: #666;")
            unit_label.setMinimumWidth(30)
        
        # 布局
        layout.addWidget(label)
        if help_button:
            layout.addWidget(help_button)
        layout.addWidget(self.widget)
        if unit_label:
            layout.addWidget(unit_label)
        layout.addStretch()
        
        # 设置布局比例
        layout.setStretch(0, 0)  # 标签固定宽度
        if help_button:
            layout.setStretch(1, 0)  # 帮助按钮固定宽度
            layout.setStretch(2, 1)  # 控件自适应
            if unit_label:
                layout.setStretch(3, 0)  # 单位固定宽度
        else:
            layout.setStretch(1, 1)  # 控件自适应
            if unit_label:
                layout.setStretch(2, 0)  # 单位固定宽度
    
    def _get_parameter_description(self) -> str:
        """获取参数描述"""
        descriptions = {
            'temperature': tr('dynamic_parameter.parameter_descriptions.temperature'),
            'top_p': tr('dynamic_parameter.parameter_descriptions.top_p'),
            'top_k': tr('dynamic_parameter.parameter_descriptions.top_k'),
            'repetition_penalty': tr('dynamic_parameter.parameter_descriptions.repetition_penalty'),
            'max_mel_tokens': tr('dynamic_parameter.parameter_descriptions.max_mel_tokens')
        }
        return descriptions.get(self.parameter_def.name, self.parameter_def.description or '')
    
    def _create_widget(self) -> QWidget:
        """根据参数类型创建控件"""
        widget_type = self.parameter_def.type
        
        if widget_type == "slider":
            return self._create_slider()
        elif widget_type == "combo":
            return self._create_combo()
        elif widget_type == "spinbox":
            return self._create_spinbox()
        elif widget_type == "text":
            return self._create_text()
        elif widget_type == "checkbox":
            return self._create_checkbox()
        elif widget_type == "file":
            return self._create_file_selector()
        else:
            # 默认文本输入框
            return self._create_text()
    
    def _create_slider(self) -> QWidget:
        """创建滑块控件"""
        container = QWidget()
        layout = QHBoxLayout(container)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(5)
        
        slider = QSlider(Qt.Orientation.Horizontal)
        
        if self.parameter_def.min_value is not None:
            slider.setMinimum(int(self.parameter_def.min_value * 100))
        if self.parameter_def.max_value is not None:
            slider.setMaximum(int(self.parameter_def.max_value * 100))
        
        if self.parameter_def.default is not None:
            slider.setValue(int(self.parameter_def.default * 100))
            self.value = self.parameter_def.default
        
        # 为温度、top-p、重复惩罚添加当前值显示
        if self.parameter_def.name in ['temperature', 'top_p', 'repetition_penalty']:
            value_label = QLabel()
            value_label.setMinimumWidth(50)
            value_label.setStyleSheet("color: #666; font-weight: bold;")
            
            # 设置初始值显示
            current_value = self.parameter_def.default if self.parameter_def.default is not None else 0
            if self.parameter_def.name == 'temperature':
                value_label.setText(f"{current_value:.1f}")
            elif self.parameter_def.name == 'top_p':
                value_label.setText(f"{current_value:.1f}")
            elif self.parameter_def.name == 'repetition_penalty':
                value_label.setText(f"{current_value:.1f}")
            
            # 连接滑块值改变信号
            def update_value_label(value):
                actual_value = value / 100.0
                if self.parameter_def.name == 'temperature':
                    value_label.setText(f"{actual_value:.1f}")
                elif self.parameter_def.name == 'top_p':
                    value_label.setText(f"{actual_value:.1f}")
                elif self.parameter_def.name == 'repetition_penalty':
                    value_label.setText(f"{actual_value:.1f}")
            
            slider.valueChanged.connect(update_value_label)
            
            layout.addWidget(slider)
            layout.addWidget(value_label)
        else:
            layout.addWidget(slider)
        
        return container
    
    def _create_combo(self) -> QComboBox:
        """创建下拉选择框"""
        combo = QComboBox()
        
        # 检查是否有source字段，如果是voices，则动态加载语音列表
        if hasattr(self.parameter_def, 'source') and self.parameter_def.source == "voices":
            # 获取当前引擎ID
            current_engine = getattr(self, 'current_engine', None)
            if not current_engine:
                # 尝试从父级获取引擎ID
                parent = self.parent()
                while parent:
                    if hasattr(parent, 'current_engine'):
                        current_engine = parent.current_engine
                        break
                    parent = parent.parent()
            
            self._populate_voices_combo(combo, current_engine)
        else:
            # 原有的options处理逻辑
            for option in self.parameter_def.options:
                if isinstance(option, dict):
                    combo.addItem(option.get("label", ""), option.get("value"))
                else:
                    combo.addItem(str(option), option)
        
        if self.parameter_def.default is not None:
            index = combo.findData(self.parameter_def.default)
            if index >= 0:
                combo.setCurrentIndex(index)
                self.value = self.parameter_def.default
        
        return combo
    
    def _populate_voices_combo(self, combo: QComboBox, engine_id: str = None):
        """填充语音选择下拉框"""
        try:
            # 导入TTS服务来获取语音列表
            from services.tts_service import TTSService
            
            tts_service = TTSService()
            all_voices = tts_service.get_all_available_voices()
            
            # 获取引擎ID
            if engine_id is None:
                engine_id = getattr(self, 'current_engine', None)
            
            if not engine_id:
                self.logger.warning(tr('dynamic_parameter.messages.engine_id_not_set'))
                return
            
            # 过滤指定引擎的语音
            engine_voices = [
                voice for voice in all_voices 
                if voice.get('engine') == engine_id
            ]
            
            # 添加指定引擎的语音到下拉框，格式为 "ID - 名称 (语言)"
            for voice in engine_voices:
                voice_id = voice.get('id', '')
                voice_name = voice.get('name', '')
                voice_language = voice.get('language', 'unknown')
                display_text = f"{voice_id} - {voice_name} ({voice_language})"
                combo.addItem(display_text, voice_id)
            
            self.logger.info(tr('dynamic_parameter.messages.voices_loaded', engine_id=engine_id, count=len(engine_voices)))
            
        except Exception as e:
            self.logger.error(tr('dynamic_parameter.messages.load_voices_failed', error=str(e)))
            # 如果失败，添加一个默认选项
            combo.addItem(tr('dynamic_parameter.load_voices_failed'), "")
    
    def _create_spinbox(self) -> QSpinBox:
        """创建数字输入框"""
        spinbox = QSpinBox()
        
        if self.parameter_def.min_value is not None:
            spinbox.setMinimum(int(self.parameter_def.min_value))
        if self.parameter_def.max_value is not None:
            spinbox.setMaximum(int(self.parameter_def.max_value))
        if self.parameter_def.step is not None:
            spinbox.setSingleStep(int(self.parameter_def.step))
        
        if self.parameter_def.default is not None:
            spinbox.setValue(int(self.parameter_def.default))
            self.value = self.parameter_def.default
        
        return spinbox
    
    def _create_text(self) -> QLineEdit:
        """创建文本输入框"""
        text_edit = QLineEdit()
        
        if self.parameter_def.default is not None:
            text_edit.setText(str(self.parameter_def.default))
            self.value = self.parameter_def.default
        
        return text_edit
    
    def _create_checkbox(self) -> QCheckBox:
        """创建复选框"""
        checkbox = QCheckBox()
        
        if self.parameter_def.default is not None:
            checkbox.setChecked(bool(self.parameter_def.default))
            self.value = self.parameter_def.default
        
        return checkbox
    
    def _create_file_selector(self) -> QWidget:
        """创建文件选择器"""
        container = QWidget()
        layout = QHBoxLayout(container)
        layout.setContentsMargins(0, 0, 0, 0)
        
        line_edit = QLineEdit()
        line_edit.setReadOnly(True)
        
        browse_btn = QPushButton(tr('dynamic_parameter.browse'))
        browse_btn.clicked.connect(lambda: self._browse_file(line_edit))
        
        layout.addWidget(line_edit)
        layout.addWidget(browse_btn)
        
        self.file_line_edit = line_edit
        return container
    
    def _browse_file(self, line_edit: QLineEdit):
        """浏览文件"""
        filters = self.parameter_def.filters or tr('dynamic_parameter.all_files')
        file_path, _ = QFileDialog.getOpenFileName(
            self, 
            tr('dynamic_parameter.select_file', label=self.parameter_def.label),
            "",
            filters
        )
        
        if file_path:
            line_edit.setText(file_path)
            self.value = file_path
            self.parameter_changed.emit(self.parameter_def.name, self.value)
    
    def setup_connections(self):
        """设置信号连接"""
        # 查找实际的控件
        actual_widget = self.widget
        if hasattr(self.widget, 'layout') and self.widget.layout():
            # 如果是容器，查找其中的滑块
            for i in range(self.widget.layout().count()):
                child = self.widget.layout().itemAt(i).widget()
                if isinstance(child, QSlider):
                    actual_widget = child
                    break
        
        if isinstance(actual_widget, QSlider):
            actual_widget.valueChanged.connect(self._on_slider_changed)
        elif isinstance(actual_widget, QComboBox):
            actual_widget.currentTextChanged.connect(self._on_combo_changed)
        elif isinstance(actual_widget, QSpinBox):
            actual_widget.valueChanged.connect(self._on_spinbox_changed)
        elif isinstance(actual_widget, QLineEdit):
            actual_widget.textChanged.connect(self._on_text_changed)
        elif isinstance(actual_widget, QCheckBox):
            actual_widget.toggled.connect(self._on_checkbox_changed)
    
    def _on_slider_changed(self, value: int):
        """滑块值改变"""
        self.value = value / 100.0
        self.parameter_changed.emit(self.parameter_def.name, self.value)
        self._validate_value()
    
    def _on_combo_changed(self, text: str):
        """下拉框值改变"""
        combo = self.widget
        current_data = combo.currentData()
        self.value = current_data if current_data is not None else text
        self.parameter_changed.emit(self.parameter_def.name, self.value)
        self._validate_value()
    
    def _on_spinbox_changed(self, value: int):
        """数字输入框值改变"""
        self.value = value
        self.parameter_changed.emit(self.parameter_def.name, self.value)
        self._validate_value()
    
    def _on_text_changed(self, text: str):
        """文本输入框值改变"""
        self.value = text
        self.parameter_changed.emit(self.parameter_def.name, self.value)
        self._validate_value()
    
    def _on_checkbox_changed(self, checked: bool):
        """复选框状态改变"""
        self.value = checked
        self.parameter_changed.emit(self.parameter_def.name, self.value)
        self._validate_value()
    
    def _validate_value(self):
        """验证参数值"""
        # 这里可以添加更复杂的验证逻辑
        is_valid = True
        error_message = ""
        
        if self.parameter_def.required and (self.value is None or self.value == ""):
            is_valid = False
            error_message = tr('dynamic_parameter.required_field', label=self.parameter_def.label)
        
        if is_valid != self.is_valid or error_message != self.error_message:
            self.is_valid = is_valid
            self.error_message = error_message
            self.validation_changed.emit(self.parameter_def.name, is_valid, error_message)
    
    def get_value(self):
        """获取参数值"""
        return self.value
    
    def set_value(self, value):
        """设置参数值"""
        self.value = value
        
        # 查找实际的控件
        actual_widget = self.widget
        if hasattr(self.widget, 'layout') and self.widget.layout():
            # 如果是容器，查找其中的滑块
            for i in range(self.widget.layout().count()):
                child = self.widget.layout().itemAt(i).widget()
                if isinstance(child, QSlider):
                    actual_widget = child
                    break
        
        if isinstance(actual_widget, QSlider):
            actual_widget.setValue(int(value * 100))
        elif isinstance(actual_widget, QComboBox):
            index = actual_widget.findData(value)
            if index >= 0:
                actual_widget.setCurrentIndex(index)
        elif isinstance(actual_widget, QSpinBox):
            actual_widget.setValue(int(value))
        elif isinstance(actual_widget, QLineEdit):
            actual_widget.setText(str(value))
        elif isinstance(actual_widget, QCheckBox):
            actual_widget.setChecked(bool(value))
        elif hasattr(self, 'file_line_edit'):
            self.file_line_edit.setText(str(value))
        
        self._validate_value()


class DynamicParameterGroupWidget(QGroupBox):
    """动态参数分组控件"""
    
    def __init__(self, group_title: str, parameters: dict, parent=None):
        super().__init__(group_title, parent)
        self.parameters = parameters
        self.parameter_widgets = {}
        
        self.setup_ui()
        self.setup_connections()
    
    def setup_ui(self):
        """设置UI"""
        layout = QVBoxLayout(self)
        layout.setContentsMargins(5, 5, 5, 5)
        layout.setSpacing(5)  # 减少间距
        
        for param_id, param_def in self.parameters.items():
            param_widget = DynamicParameterWidget(param_def, self)
            self.parameter_widgets[param_id] = param_widget
            layout.addWidget(param_widget)
    
    def setup_connections(self):
        """设置信号连接"""
        for param_widget in self.parameter_widgets.values():
            param_widget.parameter_changed.connect(self._on_parameter_changed)
    
    def _on_parameter_changed(self, param_name: str, value):
        """参数改变事件"""
        # 可以在这里添加参数间的依赖关系处理
        pass
    
    def get_parameter_values(self) -> dict:
        """获取所有参数值"""
        values = {}
        for param_id, param_widget in self.parameter_widgets.items():
            values[param_id] = param_widget.get_value()
        return values
    
    def set_parameter_values(self, values: dict):
        """设置所有参数值"""
        for param_id, value in values.items():
            if param_id in self.parameter_widgets:
                self.parameter_widgets[param_id].set_value(value)


class DynamicParameterUI(QWidget):
    """动态参数UI主控件"""
    
    # 信号定义
    parameters_changed = pyqtSignal(dict)  # 参数改变信号
    validation_changed = pyqtSignal(bool)  # 验证状态改变信号
    
    def __init__(self, parent=None):
        super().__init__(parent)
        self.logger = LogManager().get_logger("DynamicParameterUI")
        
        self.config_service = ParameterConfigService()
        self.current_engine = None
        self.group_widgets = {}
        self.parameter_widgets = {}
        
        self.setup_ui()
        self.setup_connections()
    
    def setup_ui(self):
        """设置UI"""
        layout = QVBoxLayout(self)
        layout.setContentsMargins(5, 5, 5, 5)
        
        # 创建滚动区域
        scroll_area = QScrollArea()
        scroll_area.setWidgetResizable(True)
        scroll_area.setFrameStyle(QFrame.Shape.NoFrame)
        scroll_area.setVerticalScrollBarPolicy(Qt.ScrollBarPolicy.ScrollBarAsNeeded)
        scroll_area.setHorizontalScrollBarPolicy(Qt.ScrollBarPolicy.ScrollBarAsNeeded)
        scroll_area.setMinimumHeight(350)  # 设置滚动区域最小高度
        
        # 主内容部件
        self.content_widget = QWidget()
        self.content_layout = QVBoxLayout(self.content_widget)
        self.content_layout.setContentsMargins(5, 5, 5, 5)
        self.content_layout.setSpacing(8)  # 减少间距以显示更多内容
        
        scroll_area.setWidget(self.content_widget)
        layout.addWidget(scroll_area)
    
    def setup_connections(self):
        """设置信号连接"""
        # 监听语言切换事件
        language_service = get_language_service()
        language_service.language_changed.connect(self.on_language_changed)
    
    def on_language_changed(self, language):
        """语言切换事件处理"""
        try:
            self.logger.info(f"动态参数UI语言切换: {language}")
            # 如果有当前引擎，重新创建UI以更新文本
            if self.current_engine:
                self._clear_ui()
                self._create_engine_ui(self.current_engine)
        except Exception as e:
            self.logger.error(f"动态参数UI语言切换失败: {e}")
    
    def set_engine(self, engine_id: str):
        """设置当前引擎"""
        if self.current_engine == engine_id:
            return
        
        self.current_engine = engine_id
        self._clear_ui()
        self._create_engine_ui(engine_id)
    
    def _clear_ui(self):
        """清空UI"""
        for widget in self.group_widgets.values():
            widget.deleteLater()
        
        self.group_widgets.clear()
        self.parameter_widgets.clear()
    
    def _create_engine_ui(self, engine_id: str):
        """创建引擎UI"""
        engine_config = self.config_service.get_engine_config(engine_id)
        if not engine_config:
            self.logger.error(tr('dynamic_parameter.messages.engine_config_not_found', engine_id=engine_id))
            return
        
        # 定义需要过滤的重复参数（这些参数在固定参数中已经存在）
        duplicate_params = {'rate', 'volume', 'pitch', 'language'}
        
        # 创建参数分组
        for group_id, group in engine_config.groups.items():
            # 过滤掉重复参数
            filtered_parameters = {
                param_id: param_def for param_id, param_def in group.parameters.items()
                if param_id not in duplicate_params
            }
            
            # 如果过滤后没有参数，跳过这个分组
            if not filtered_parameters:
                self.logger.info(tr('dynamic_parameter.messages.group_no_parameters', group_title=group.title))
                continue
            
            group_widget = DynamicParameterGroupWidget(
                group.title, 
                filtered_parameters, 
                self
            )
            self.group_widgets[group_id] = group_widget
            self.content_layout.addWidget(group_widget)
            
            # 收集参数控件
            for param_id, param_widget in group_widget.parameter_widgets.items():
                self.parameter_widgets[param_id] = param_widget
                param_widget.parameter_changed.connect(self._on_parameter_changed)
                param_widget.validation_changed.connect(self._on_validation_changed)
        
        self.content_layout.addStretch()
        
        # 确保UI可见
        self.setVisible(True)
        self.update()
    
    def _on_parameter_changed(self, param_name: str, value):
        """参数改变事件"""
        # 发出参数改变信号
        all_values = self.get_all_parameter_values()
        self.parameters_changed.emit(all_values)
    
    def _on_validation_changed(self, param_name: str, is_valid: bool, error_message: str):
        """验证状态改变事件"""
        # 检查所有参数的验证状态
        all_valid = all(
            widget.is_valid for widget in self.parameter_widgets.values()
        )
        self.validation_changed.emit(all_valid)
    
    def get_all_parameter_values(self) -> dict:
        """获取所有参数值"""
        values = {}
        for group_widget in self.group_widgets.values():
            group_values = group_widget.get_parameter_values()
            values.update(group_values)
        return values
    
    def set_all_parameter_values(self, values: dict):
        """设置所有参数值"""
        # 临时禁用信号，防止在批量设置时触发参数改变信号
        self.blockSignals(True)
        try:
            for group_widget in self.group_widgets.values():
                group_widget.set_parameter_values(values)
        finally:
            # 恢复信号
            self.blockSignals(False)
            # 设置完成后发出一次参数改变信号
            all_values = self.get_all_parameter_values()
            self.parameters_changed.emit(all_values)
    
    def get_parameter_value(self, param_name: str):
        """获取指定参数值"""
        if param_name in self.parameter_widgets:
            return self.parameter_widgets[param_name].get_value()
        return None
    
    def set_parameter_value(self, param_name: str, value):
        """设置指定参数值"""
        if param_name in self.parameter_widgets:
            self.parameter_widgets[param_name].set_value(value)
    
    def is_valid(self) -> bool:
        """检查所有参数是否有效"""
        return all(
            widget.is_valid for widget in self.parameter_widgets.values()
        )
    
    def get_validation_errors(self) -> list:
        """获取验证错误信息"""
        errors = []
        for widget in self.parameter_widgets.values():
            if not widget.is_valid and widget.error_message:
                errors.append(widget.error_message)
        return errors
