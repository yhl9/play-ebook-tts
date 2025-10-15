"""
UI界面层
"""

from .main_window import MainWindow
from .file_manager import FileManagerWidget
from .text_processor import TextProcessorWidget
from .voice_settings import VoiceSettingsWidget
from .batch_processor import BatchProcessorWidget
from .settings import SettingsWidget

__all__ = [
    'MainWindow',
    'FileManagerWidget',
    'TextProcessorWidget',
    'VoiceSettingsWidget',
    'BatchProcessorWidget',
    'SettingsWidget'
]
