"""
日志管理器模块

提供统一的日志记录功能，支持：
- 单例模式确保全局唯一实例
- 多级别日志记录（DEBUG, INFO, WARNING, ERROR, CRITICAL）
- 文件和控制台双重输出
- 错误日志单独记录
- 日志文件自动清理
- 支持中文编码

作者: TTS开发团队
版本: 1.0.0
创建时间: 2024
"""

import logging
import os
import json
from pathlib import Path
from datetime import datetime


class LogManager:
    """
    日志管理器类
    
    采用单例模式设计，确保整个应用程序中只有一个日志管理器实例。
    提供统一的日志记录接口，支持多级别日志输出和文件管理。
    
    特性：
    - 单例模式：全局唯一实例
    - 多处理器：文件 + 控制台输出
    - 分级记录：不同级别输出到不同位置
    - 中文支持：UTF-8编码
    - 自动清理：定期清理旧日志文件
    """
    
    # 单例模式相关属性
    _instance = None      # 存储唯一实例
    _initialized = False  # 标记是否已初始化
    
    def __new__(cls):
        """
        创建单例实例
        
        确保整个应用程序中只有一个LogManager实例。
        如果实例已存在，直接返回现有实例。
        
        Returns:
            LogManager: 唯一的日志管理器实例
        """
        if cls._instance is None:
            cls._instance = super().__new__(cls)
        return cls._instance
    
    def __init__(self):
        """
        初始化日志管理器
        
        使用_initialized标志确保初始化只执行一次，
        避免重复初始化导致的问题。
        """
        if not self._initialized:
            self._setup_logging()
            LogManager._initialized = True
    
    def _load_config(self):
        """
        加载配置文件中的日志级别设置
        
        Returns:
            str: 配置的日志级别，默认为ERROR
        """
        try:
            config_file = Path("config.json")
            if config_file.exists():
                with open(config_file, 'r', encoding='utf-8') as f:
                    config = json.load(f)
                    # 从advanced配置中获取log_level
                    log_level = config.get('advanced', {}).get('log_level', 'ERROR')
                    return log_level.upper()
            else:
                print("配置文件不存在，使用默认日志级别: ERROR")
                return 'ERROR'
        except Exception as e:
            print(f"加载配置文件失败: {e}，使用默认日志级别: ERROR")
            return 'ERROR'
    
    def _setup_logging(self):
        """
        设置日志系统
        
        配置多处理器日志系统，包括：
        - 应用日志文件（app.log）：记录所有INFO级别以上的日志
        - 错误日志文件（error.log）：专门记录ERROR级别以上的日志
        - 控制台输出：只显示WARNING级别以上的日志
        
        日志格式：时间 - 模块名 - 级别 - 消息
        编码：UTF-8，支持中文日志内容
        """
        try:
            # 从配置文件加载日志级别
            config_log_level = self._load_config()
            
            # 创建日志目录
            log_dir = Path("logs")
            log_dir.mkdir(exist_ok=True)
            
            # 设置统一的日志格式
            # 格式：年-月-日 时:分:秒 - 模块名 - 级别 - 消息内容
            formatter = logging.Formatter(
                '%(asctime)s - %(name)s - %(levelname)s - %(message)s',
                datefmt='%Y-%m-%d %H:%M:%S'
            )
            
            # 创建根日志记录器
            root_logger = logging.getLogger()
            # 使用配置文件中的日志级别
            log_level = getattr(logging, config_log_level, logging.ERROR)
            root_logger.setLevel(log_level)
            
            # 清除现有处理器，避免重复添加
            for handler in root_logger.handlers[:]:
                root_logger.removeHandler(handler)
            
            # 1. 应用日志文件处理器
            # 记录配置级别以上的日志到app.log文件
            file_handler = logging.FileHandler(
                log_dir / 'app.log',
                encoding='utf-8'  # 支持中文编码
            )
            file_handler.setLevel(log_level)
            file_handler.setFormatter(formatter)
            root_logger.addHandler(file_handler)
            
            # 2. 控制台处理器
            # 只在控制台显示WARNING级别以上的日志，避免信息过载
            console_handler = logging.StreamHandler()
            console_handler.setLevel(logging.WARNING)
            console_handler.setFormatter(formatter)
            root_logger.addHandler(console_handler)
            
            # 3. 错误日志文件处理器
            # 专门记录ERROR级别以上的日志到error.log文件，便于错误追踪
            error_handler = logging.FileHandler(
                log_dir / 'error.log',
                encoding='utf-8'  # 支持中文编码
            )
            error_handler.setLevel(logging.ERROR)
            error_handler.setFormatter(formatter)
            root_logger.addHandler(error_handler)
            
        except Exception as e:
            # 如果日志系统初始化失败，至少要在控制台输出错误信息
            print(f"日志系统初始化失败: {e}")
    
    def get_logger(self, name: str) -> logging.Logger:
        """
        获取指定名称的日志记录器
        
        为不同的模块或组件创建独立的日志记录器，
        便于在日志中区分不同来源的日志消息。
        
        Args:
            name (str): 日志记录器名称，通常使用模块名或类名
            
        Returns:
            logging.Logger: 配置好的日志记录器实例
        """
        return logging.getLogger(name)
    
    def set_log_level(self, level: str = None):
        """
        动态设置日志级别
        
        支持运行时调整日志输出级别，便于调试和问题排查。
        如果不指定级别，则从配置文件重新加载。
        控制台输出始终保持在WARNING级别以上，避免信息过载。
        
        Args:
            level (str, optional): 日志级别，支持：DEBUG, INFO, WARNING, ERROR, CRITICAL
                                  如果为None，则从配置文件加载
        """
        try:
            if level is None:
                # 从配置文件重新加载日志级别
                level = self._load_config()
            
            # 将字符串转换为logging级别常量
            log_level = getattr(logging, level.upper(), logging.ERROR)
            root_logger = logging.getLogger()
            root_logger.setLevel(log_level)
            
            # 更新所有处理器的级别
            for handler in root_logger.handlers:
                if isinstance(handler, logging.FileHandler):
                    # 文件处理器使用设置的级别
                    handler.setLevel(log_level)
                elif isinstance(handler, logging.StreamHandler):
                    # 控制台处理器至少保持WARNING级别，避免信息过载
                    handler.setLevel(max(log_level, logging.WARNING))
                    
        except Exception as e:
            print(f"设置日志级别失败: {e}")
    
    def reload_config(self):
        """
        重新加载配置文件并更新日志级别
        
        当配置文件发生变化时，可以调用此方法重新加载配置。
        """
        try:
            # 重新加载配置并更新日志级别
            self.set_log_level()
            print(f"已重新加载日志配置，当前级别: {self._load_config()}")
        except Exception as e:
            print(f"重新加载日志配置失败: {e}")
    
    def cleanup_old_logs(self, days: int = 30):
        """
        清理指定天数之前的旧日志文件
        
        定期清理过期的日志文件，防止日志文件占用过多磁盘空间。
        只清理.log和.log.*格式的文件，保留其他重要文件。
        
        Args:
            days (int): 保留天数，默认30天
        """
        try:
            log_dir = Path("logs")
            if not log_dir.exists():
                return
            
            current_time = datetime.now()
            # 查找所有日志文件（包括轮转的日志文件）
            for log_file in log_dir.glob("*.log*"):
                file_time = datetime.fromtimestamp(log_file.stat().st_mtime)
                # 如果文件修改时间超过指定天数，则删除
                if (current_time - file_time).days > days:
                    log_file.unlink()
                    print(f"已删除过期日志文件: {log_file}")
                    
        except Exception as e:
            print(f"清理旧日志失败: {e}")
    
    def get_log_file_path(self) -> str:
        """
        获取应用日志文件路径
        
        Returns:
            str: app.log文件的完整路径
        """
        return str(Path("logs") / "app.log")
    
    def get_error_log_file_path(self) -> str:
        """
        获取错误日志文件路径
        
        Returns:
            str: error.log文件的完整路径
        """
        return str(Path("logs") / "error.log")
