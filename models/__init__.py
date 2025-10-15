"""
数据模型层模块

提供TTS应用程序的核心数据模型，包括：
- 文件模型：文件信息、路径、大小等属性
- 文本模型：处理后的文本、章节、分段等结构
- 音频模型：音频数据、语音配置、输出配置等
- 配置模型：应用程序配置、用户设置等

数据模型设计原则：
- 数据封装：使用dataclass简化数据类定义
- 类型安全：使用typing提供完整的类型提示
- 序列化支持：提供to_dict/from_dict方法
- 验证机制：内置数据验证和错误处理
- 默认值：提供合理的默认配置值

模型分类：
- 文件模型：FileModel - 文件系统相关数据
- 文本模型：ProcessedText, Chapter - 文本处理相关数据
- 音频模型：AudioModel, VoiceConfig, OutputConfig - 音频处理相关数据
- 配置模型：AppConfig - 应用程序配置数据

作者: TTS开发团队
版本: 1.0.0
创建时间: 2024
"""

from .file_model import FileModel
from .text_model import ProcessedText, Chapter
from .audio_model import AudioModel, VoiceConfig
from .config_model import AppConfig

# 导出所有核心数据模型
__all__ = [
    'FileModel',        # 文件模型 - 文件信息和属性
    'ProcessedText',    # 处理后的文本模型 - 文本内容和结构
    'Chapter',          # 章节模型 - 章节信息和内容
    'AudioModel',       # 音频模型 - 音频数据和属性
    'VoiceConfig',      # 语音配置模型 - TTS语音参数
    'AppConfig'         # 应用配置模型 - 应用程序设置
]
