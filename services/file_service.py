"""
文件服务
"""

import os
from pathlib import Path
from typing import List, Optional
from abc import ABC, abstractmethod

from models.file_model import FileModel
from processors.pdf_processor import PDFProcessor
from processors.epub_processor import EPUBProcessor
from processors.docx_processor import DOCXProcessor
from utils.log_manager import LogManager


class IFileService(ABC):
    """文件服务接口"""
    
    @abstractmethod
    def load_file(self, file_path: str) -> FileModel:
        pass
    
    @abstractmethod
    def is_supported_format(self, file_path: str) -> bool:
        pass
    
    @abstractmethod
    def get_supported_formats(self) -> List[str]:
        pass


class FileService(IFileService):
    """文件服务实现"""
    
    def __init__(self):
        self.logger = LogManager().get_logger("FileService")
        self.supported_formats = ['.txt', '.pdf', '.epub', '.docx', '.md']
        self.pdf_processor = PDFProcessor()
        self.epub_processor = EPUBProcessor()
        self.docx_processor = DOCXProcessor()
    
    def load_file(self, file_path: str) -> FileModel:
        """加载文件"""
        try:
            if not self.is_supported_format(file_path):
                raise UnsupportedFormatError(f"不支持的文件格式: {file_path}")
            
            file_model = FileModel.from_path(file_path)
            file_extension = file_model.get_extension()
            
            self.logger.info(f"开始加载文件: {file_path}")
            
            # 根据文件类型选择处理器
            if file_extension == '.pdf':
                content = self.pdf_processor.extract_text(file_path)
            elif file_extension == '.epub':
                content = self.epub_processor.extract_text(file_path)
            elif file_extension == '.docx':
                content = self.docx_processor.extract_text(file_path)
            elif file_extension == '.txt':
                content = self._load_txt_file(file_path)
            elif file_extension == '.md':
                content = self._load_markdown_file(file_path)
            else:
                raise UnsupportedFormatError(f"不支持的文件格式: {file_extension}")
            
            file_model.content = content
            self.logger.info(f"文件加载完成: {file_path}, 内容长度: {len(content)}")
            
            return file_model
            
        except Exception as e:
            self.logger.error(f"文件加载失败: {file_path}, 错误: {e}")
            raise FileImportError(f"文件加载失败: {e}")
    
    def is_supported_format(self, file_path: str) -> bool:
        """检查文件格式是否支持"""
        file_extension = Path(file_path).suffix.lower()
        return file_extension in self.supported_formats
    
    def get_supported_formats(self) -> List[str]:
        """获取支持的文件格式列表"""
        return self.supported_formats.copy()
    
    def _load_txt_file(self, file_path: str) -> str:
        """加载TXT文件"""
        try:
            with open(file_path, 'r', encoding='utf-8') as file:
                content = file.read()
            return content
        except UnicodeDecodeError:
            # 尝试其他编码
            encodings = ['gbk', 'gb2312', 'latin-1']
            for encoding in encodings:
                try:
                    with open(file_path, 'r', encoding=encoding) as file:
                        content = file.read()
                    return content
                except UnicodeDecodeError:
                    continue
            raise FileImportError(f"无法解码文件: {file_path}")
    
    def _load_markdown_file(self, file_path: str) -> str:
        """加载Markdown文件"""
        try:
            with open(file_path, 'r', encoding='utf-8') as file:
                content = file.read()
            return content
        except UnicodeDecodeError:
            # 尝试其他编码
            encodings = ['gbk', 'gb2312', 'latin-1']
            for encoding in encodings:
                try:
                    with open(file_path, 'r', encoding=encoding) as file:
                        content = file.read()
                    return content
                except UnicodeDecodeError:
                    continue
            raise FileImportError(f"无法解码Markdown文件: {file_path}")
    
    def validate_file(self, file_path: str) -> bool:
        """验证文件"""
        try:
            if not os.path.exists(file_path):
                return False
            
            if not self.is_supported_format(file_path):
                return False
            
            # 检查文件大小
            file_size = os.path.getsize(file_path)
            max_size = 100 * 1024 * 1024  # 100MB
            if file_size > max_size:
                self.logger.warning(f"文件过大: {file_path}, 大小: {file_size / 1024 / 1024:.2f}MB")
                return False
            
            return True
            
        except Exception as e:
            self.logger.error(f"文件验证失败: {file_path}, 错误: {e}")
            return False
    
    def get_file_info(self, file_path: str) -> dict:
        """获取文件信息"""
        try:
            file_model = FileModel.from_path(file_path)
            return {
                'file_name': file_model.file_name,
                'file_size': file_model.file_size,
                'file_type': file_model.file_type,
                'created_time': file_model.created_time,
                'modified_time': file_model.modified_time,
                'is_supported': self.is_supported_format(file_path)
            }
        except Exception as e:
            self.logger.error(f"获取文件信息失败: {file_path}, 错误: {e}")
            return {}


class FileImportError(Exception):
    """文件导入异常"""
    pass


class UnsupportedFormatError(FileImportError):
    """不支持的文件格式异常"""
    pass
