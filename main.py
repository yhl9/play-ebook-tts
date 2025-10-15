#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
电子书生成音频工具 - 主程序入口
"""

import sys
import os
import warnings
from pathlib import Path

# 添加项目根目录到Python路径
project_root = Path(__file__).parent
sys.path.insert(0, str(project_root))

# 抑制libpng警告
warnings.filterwarnings("ignore", message=".*iCCP.*")
warnings.filterwarnings("ignore", message=".*known incorrect sRGB profile.*")

# 首先预加载 Piper TTS，避免 PyQt6 的兼容性问题
from utils.piper_preloader import PIPER_AVAILABLE, get_piper_status

from PyQt6.QtWidgets import QApplication
from PyQt6.QtCore import Qt
from PyQt6.QtGui import QIcon

from ui.main_window import MainWindow
from services.config.app_config_service import AppConfigService
from services.config.engine_config_service import EngineConfigService
from services.language_service import get_language_service
from utils.log_manager import LogManager


def setup_application():
    """设置应用程序"""
    # PyQt6中高DPI支持已默认启用，无需手动设置
    
    app = QApplication(sys.argv)
    app.setApplicationName("电子书生成音频工具")
    app.setApplicationVersion("1.0.0")
    app.setOrganizationName("AI开发团队")
    
    # 设置应用程序图标
    icon_path = project_root / "resources" / "icons" / "app.ico"
    if icon_path.exists():
        app.setWindowIcon(QIcon(str(icon_path)))
    
    return app


def setup_directories():
    """创建必要的目录"""
    directories = [
        "logs",
        "temp", 
        "output",
        "resources/icons",
        "resources/themes"
    ]
    
    for directory in directories:
        dir_path = project_root / directory
        dir_path.mkdir(parents=True, exist_ok=True)


def main():
    """主函数"""
    try:
        # 设置目录
        setup_directories()
        
        # 初始化日志系统
        log_manager = LogManager()
        logger = log_manager.get_logger("main")
        logger.info("应用程序启动")
        
        # 初始化语言服务
        language_service = get_language_service()
        logger.info(f"当前语言: {language_service.get_current_language()}")
        logger.info(f"支持的语言: {language_service.get_supported_languages()}")
        
        # 加载应用程序配置
        app_config_service = AppConfigService()
        app_config = app_config_service.load_config()
        
        # 启用调试模式
        import os
        debug_mode = os.getenv('TTS_DEBUG', 'false').lower() == 'true' or app_config.debug_mode
        if debug_mode:
            import logging
            logger.setLevel(logging.DEBUG)
            logger.info("调试模式已启用")
        
        # 加载引擎配置
        engine_config_service = EngineConfigService()
        engine_registry = engine_config_service.load_registry()
        
        # 创建配置对象（保持向后兼容）
        config = {
            'app_config': app_config,
            'engine_registry': engine_registry,
            'debug_mode': debug_mode
        }
        
        # 设置应用程序
        app = setup_application()
        
        # 创建主窗口
        logger.info("正在创建主窗口...")
        main_window = MainWindow(config)
        logger.info("主窗口创建完成")
        
        logger.info("正在显示主窗口...")
        main_window.show()
        logger.info("主窗口已显示")
        
        # 运行应用程序
        sys.exit(app.exec())
        
    except Exception as e:
        print(f"应用程序启动失败: {e}")
        sys.exit(1)


if __name__ == "__main__":
    main()
