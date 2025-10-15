"""
业务服务层模块

提供TTS应用程序的核心业务逻辑服务，包括：
- 文件服务：文件读写、格式转换、路径管理
- 文本服务：文本处理、分段、格式化、编码转换
- 音频服务：音频格式转换、音频文件处理、音频质量优化
- TTS服务：语音合成引擎管理、语音参数配置、音频生成
- 配置服务：应用程序配置管理、用户设置保存和加载

架构设计：
- 服务层位于控制器和模型层之间
- 提供统一的业务逻辑接口
- 支持依赖注入和模块化设计
- 实现业务逻辑与UI的分离

作者: TTS开发团队
版本: 1.0.0
创建时间: 2024
"""

from .file_service import FileService
from .text_service import TextService
from .audio_service import AudioService
from .tts_service import TTSService
from .config_service import ConfigService

# 导出所有核心服务类
__all__ = [
    'FileService',      # 文件服务 - 处理文件操作和格式转换
    'TextService',      # 文本服务 - 处理文本内容和格式化
    'AudioService',     # 音频服务 - 处理音频文件和质量优化
    'TTSService',       # TTS服务 - 管理语音合成引擎
    'ConfigService'     # 配置服务 - 管理应用程序配置
]
