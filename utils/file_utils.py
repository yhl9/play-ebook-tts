"""
文件工具类模块

提供文件操作相关的工具函数，包括：
- 目录创建和管理
- 文件信息获取（大小、扩展名、修改时间等）
- 文件复制、移动、删除操作
- 文件搜索和过滤
- 路径处理和规范化
- 文件权限和安全检查

作者: TTS开发团队
版本: 1.0.0
创建时间: 2024
"""

import os
import shutil
from pathlib import Path
from typing import List, Optional
from datetime import datetime

from utils.log_manager import LogManager


class FileUtils:
    """
    文件工具类
    
    提供各种文件操作相关的静态方法和实例方法，
    封装常用的文件系统操作，提供统一的错误处理和日志记录。
    
    特性：
    - 静态方法：无需实例化即可使用
    - 错误处理：统一的异常捕获和日志记录
    - 路径安全：使用pathlib确保跨平台兼容性
    - 类型提示：完整的类型注解支持
    """
    
    def __init__(self):
        """
        初始化文件工具类
        
        创建日志记录器用于记录文件操作过程中的信息。
        """
        self.logger = LogManager().get_logger("FileUtils")
    
    @staticmethod
    def ensure_directory(path: str) -> bool:
        """
        确保指定目录存在
        
        如果目录不存在，则递归创建所有必要的父目录。
        如果目录已存在，则不进行任何操作。
        
        Args:
            path (str): 要创建的目录路径
            
        Returns:
            bool: 成功返回True，失败返回False
        """
        try:
            Path(path).mkdir(parents=True, exist_ok=True)
            return True
        except Exception as e:
            LogManager().get_logger("FileUtils").error(f"创建目录失败: {path}, 错误: {e}")
            return False
    
    @staticmethod
    def get_file_size_mb(file_path: str) -> float:
        """
        获取文件大小（以MB为单位）
        
        Args:
            file_path (str): 文件路径
            
        Returns:
            float: 文件大小（MB），如果文件不存在或无法访问则返回0.0
        """
        try:
            return os.path.getsize(file_path) / (1024 * 1024)
        except Exception:
            return 0.0
    
    @staticmethod
    def get_file_extension(file_path: str) -> str:
        """
        获取文件扩展名（小写）
        
        Args:
            file_path (str): 文件路径
            
        Returns:
            str: 文件扩展名（包含点号，如'.txt'），如果没有扩展名则返回空字符串
        """
        return Path(file_path).suffix.lower()
    
    @staticmethod
    def get_file_name_without_extension(file_path: str) -> str:
        """
        获取不带扩展名的文件名
        
        Args:
            file_path (str): 文件路径
            
        Returns:
            str: 不带扩展名的文件名
        """
        return Path(file_path).stem
    
    @staticmethod
    def is_file_exists(file_path: str) -> bool:
        """
        检查文件是否存在
        
        Args:
            file_path (str): 文件路径
            
        Returns:
            bool: 文件存在返回True，否则返回False
        """
        return os.path.exists(file_path)
    
    @staticmethod
    def is_directory(path: str) -> bool:
        """
        检查指定路径是否为目录
        
        Args:
            path (str): 要检查的路径
            
        Returns:
            bool: 是目录返回True，否则返回False
        """
        return os.path.isdir(path)
    
    @staticmethod
    def get_file_modified_time(file_path: str) -> Optional[datetime]:
        """
        获取文件最后修改时间
        
        Args:
            file_path (str): 文件路径
            
        Returns:
            Optional[datetime]: 文件修改时间，如果文件不存在或无法访问则返回None
        """
        try:
            timestamp = os.path.getmtime(file_path)
            return datetime.fromtimestamp(timestamp)
        except Exception:
            return None
    
    @staticmethod
    def copy_file(src: str, dst: str) -> bool:
        """
        复制文件到指定位置
        
        使用shutil.copy2复制文件，保留文件的元数据（如修改时间、权限等）。
        
        Args:
            src (str): 源文件路径
            dst (str): 目标文件路径
            
        Returns:
            bool: 复制成功返回True，失败返回False
        """
        try:
            shutil.copy2(src, dst)
            return True
        except Exception as e:
            LogManager().get_logger("FileUtils").error(f"复制文件失败: {src} -> {dst}, 错误: {e}")
            return False
    
    @staticmethod
    def move_file(src: str, dst: str) -> bool:
        """
        移动文件到指定位置
        
        使用shutil.move移动文件，如果目标位置在不同磁盘上则先复制后删除。
        
        Args:
            src (str): 源文件路径
            dst (str): 目标文件路径
            
        Returns:
            bool: 移动成功返回True，失败返回False
        """
        try:
            shutil.move(src, dst)
            return True
        except Exception as e:
            LogManager().get_logger("FileUtils").error(f"移动文件失败: {src} -> {dst}, 错误: {e}")
            return False
    
    @staticmethod
    def delete_file(file_path: str) -> bool:
        """
        删除指定文件
        
        Args:
            file_path (str): 要删除的文件路径
            
        Returns:
            bool: 删除成功返回True，失败返回False
        """
        try:
            os.remove(file_path)
            return True
        except Exception as e:
            LogManager().get_logger("FileUtils").error(f"删除文件失败: {file_path}, 错误: {e}")
            return False
    
    @staticmethod
    def delete_directory(dir_path: str) -> bool:
        """
        递归删除目录及其所有内容
        
        Args:
            dir_path (str): 要删除的目录路径
            
        Returns:
            bool: 删除成功返回True，失败返回False
        """
        try:
            shutil.rmtree(dir_path)
            return True
        except Exception as e:
            LogManager().get_logger("FileUtils").error(f"删除目录失败: {dir_path}, 错误: {e}")
            return False
    
    @staticmethod
    def get_directory_size_mb(dir_path: str) -> float:
        """
        计算目录及其所有子目录和文件的总大小（以MB为单位）
        
        Args:
            dir_path (str): 目录路径
            
        Returns:
            float: 目录总大小（MB），如果目录不存在或无法访问则返回0.0
        """
        try:
            total_size = 0
            for dirpath, dirnames, filenames in os.walk(dir_path):
                for filename in filenames:
                    filepath = os.path.join(dirpath, filename)
                    total_size += os.path.getsize(filepath)
            return total_size / (1024 * 1024)
        except Exception:
            return 0.0
    
    @staticmethod
    def list_files_in_directory(dir_path: str, extensions: List[str] = None) -> List[str]:
        """
        列出目录中指定扩展名的文件
        
        Args:
            dir_path (str): 目录路径
            extensions (List[str], optional): 文件扩展名列表，如['.txt', '.pdf']。
                                           如果为None，则列出所有文件
            
        Returns:
            List[str]: 符合条件的文件路径列表
        """
        try:
            files = []
            for file_path in Path(dir_path).iterdir():
                if file_path.is_file():
                    if extensions is None or file_path.suffix.lower() in extensions:
                        files.append(str(file_path))
            return files
        except Exception as e:
            LogManager().get_logger("FileUtils").error(f"列出目录文件失败: {dir_path}, 错误: {e}")
            return []
    
    @staticmethod
    def create_unique_filename(file_path: str) -> str:
        """
        创建唯一的文件名，如果文件已存在则添加数字后缀
        
        例如：file.txt -> file_1.txt -> file_2.txt
        
        Args:
            file_path (str): 原始文件路径
            
        Returns:
            str: 唯一的文件路径
        """
        try:
            path = Path(file_path)
            if not path.exists():
                return file_path
            
            counter = 1
            while True:
                new_name = f"{path.stem}_{counter}{path.suffix}"
                new_path = path.parent / new_name
                if not new_path.exists():
                    return str(new_path)
                counter += 1
        except Exception as e:
            LogManager().get_logger("FileUtils").error(f"创建唯一文件名失败: {file_path}, 错误: {e}")
            return file_path
    
    @staticmethod
    def get_relative_path(file_path: str, base_path: str) -> str:
        """
        获取文件相对于基础路径的相对路径
        
        Args:
            file_path (str): 文件路径
            base_path (str): 基础路径
            
        Returns:
            str: 相对路径
        """
        try:
            return os.path.relpath(file_path, base_path)
        except Exception:
            return file_path
    
    @staticmethod
    def normalize_path(file_path: str) -> str:
        """
        规范化文件路径，处理路径分隔符和相对路径
        
        Args:
            file_path (str): 原始路径
            
        Returns:
            str: 规范化后的路径
        """
        return str(Path(file_path).resolve())
    
    @staticmethod
    def is_safe_path(file_path: str) -> bool:
        """
        检查文件路径是否安全，防止路径遍历攻击
        
        检查路径中是否包含危险字符或路径遍历序列（如../、..\\等）
        
        Args:
            file_path (str): 要检查的文件路径
            
        Returns:
            bool: 路径安全返回True，否则返回False
        """
        try:
            # 检查路径是否包含危险字符
            dangerous_chars = ['..', '~', '$', '`']
            for char in dangerous_chars:
                if char in file_path:
                    return False
            
            # 检查路径是否在允许的目录内
            resolved_path = Path(file_path).resolve()
            current_dir = Path.cwd().resolve()
            
            # 确保路径在当前目录内
            try:
                resolved_path.relative_to(current_dir)
                return True
            except ValueError:
                return False
                
        except Exception:
            return False
    
    @staticmethod
    def clean_filename(filename: str) -> str:
        """
        清理文件名，移除或替换不安全的字符
        
        移除或替换Windows和Unix系统中不允许的字符，
        确保文件名在所有平台上都有效。
        
        Args:
            filename (str): 原始文件名
            
        Returns:
            str: 清理后的安全文件名
        """
        # 移除或替换不安全的字符
        unsafe_chars = '<>:"/\\|?*'
        for char in unsafe_chars:
            filename = filename.replace(char, '_')
        
        # 移除多余的空格和点
        filename = filename.strip(' .')
        
        # 限制文件名长度
        if len(filename) > 200:
            name, ext = os.path.splitext(filename)
            filename = name[:200-len(ext)] + ext
        
        return filename
    
    @staticmethod
    def get_file_info(file_path: str) -> dict:
        """
        获取文件的详细信息
        
        返回包含文件大小、修改时间、扩展名等信息的字典。
        
        Args:
            file_path (str): 文件路径
            
        Returns:
            dict: 包含文件信息的字典，如果文件不存在则返回空字典
        """
        try:
            path = Path(file_path)
            stat = path.stat()
            
            return {
                'name': path.name,
                'size': stat.st_size,
                'size_mb': stat.st_size / (1024 * 1024),
                'extension': path.suffix.lower(),
                'created_time': datetime.fromtimestamp(stat.st_ctime),
                'modified_time': datetime.fromtimestamp(stat.st_mtime),
                'is_file': path.is_file(),
                'is_directory': path.is_dir(),
                'exists': path.exists()
            }
        except Exception as e:
            LogManager().get_logger("FileUtils").error(f"获取文件信息失败: {file_path}, 错误: {e}")
            return {}
