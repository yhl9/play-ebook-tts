"""
文件模型模块

提供文件系统相关的数据模型，包括：
- 文件信息：路径、名称、大小、类型等
- 时间信息：创建时间、修改时间等
- 内容管理：文件内容存储和访问
- 格式支持：支持的文件格式检测
- 工具方法：文件大小转换、扩展名获取等

文件模型特性：
- 自动提取：从文件路径自动提取文件信息
- 类型安全：完整的类型提示
- 序列化：支持字典格式转换
- 格式检测：自动检测支持的文件格式
- 工具方法：提供便捷的文件操作方法

支持的文件格式：
- 文本文件：TXT格式
- 文档文件：PDF、DOCX格式
- 电子书：EPUB格式

作者: TTS开发团队
版本: 1.0.0
创建时间: 2024
"""

from dataclasses import dataclass
from datetime import datetime
from typing import Optional
from pathlib import Path


@dataclass
class FileModel:
    """
    文件模型
    
    存储文件的基本信息和元数据，包括路径、大小、时间戳等。
    提供文件操作的便捷方法和格式检测功能。
    
    Attributes:
        file_path (str): 文件完整路径
        file_name (str): 文件名
        file_size (int): 文件大小（字节）
        file_type (str): 文件类型（扩展名）
        created_time (datetime): 创建时间
        modified_time (datetime): 修改时间
        content (Optional[str]): 文件内容（可选）
    """
    file_path: str
    file_name: str
    file_size: int
    file_type: str
    created_time: datetime
    modified_time: datetime
    content: Optional[str] = None
    
    def __post_init__(self):
        """
        初始化后处理
        
        在对象创建后自动执行，如果文件名为空则从路径中提取。
        """
        if not self.file_name:
            self.file_name = Path(self.file_path).name
    
    @classmethod
    def from_path(cls, file_path: str) -> 'FileModel':
        """
        从文件路径创建文件模型
        
        从文件路径自动提取文件信息，包括大小、时间戳等。
        
        Args:
            file_path (str): 文件路径
            
        Returns:
            FileModel: 新创建的文件模型实例
        """
        path = Path(file_path)
        stat = path.stat()
        
        return cls(
            file_path=str(path.absolute()),
            file_name=path.name,
            file_size=stat.st_size,
            file_type=path.suffix.lower(),
            created_time=datetime.fromtimestamp(stat.st_ctime),
            modified_time=datetime.fromtimestamp(stat.st_mtime)
        )
    
    def to_dict(self) -> dict:
        """
        转换为字典格式
        
        将文件模型对象转换为字典，便于序列化和存储。
        
        Returns:
            dict: 包含所有文件信息的字典
        """
        return {
            'file_path': self.file_path,
            'file_name': self.file_name,
            'file_size': self.file_size,
            'file_type': self.file_type,
            'created_time': self.created_time.isoformat(),
            'modified_time': self.modified_time.isoformat(),
            'content': self.content
        }
    
    def is_supported_format(self) -> bool:
        """
        检查文件格式是否支持
        
        检查当前文件格式是否在支持的文件格式列表中。
        
        Returns:
            bool: 支持返回True，否则返回False
        """
        supported_formats = ['.txt', '.pdf', '.epub', '.docx']
        return self.file_type in supported_formats
    
    def get_size_mb(self) -> float:
        """
        获取文件大小（MB）
        
        将文件大小从字节转换为MB单位。
        
        Returns:
            float: 文件大小（MB）
        """
        return self.file_size / (1024 * 1024)
    
    def get_extension(self) -> str:
        """
        获取文件扩展名
        
        返回文件扩展名（包含点号）。
        
        Returns:
            str: 文件扩展名
        """
        return self.file_type
