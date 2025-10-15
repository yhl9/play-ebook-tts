"""
文件控制器
"""

from typing import List, Optional
from abc import ABC, abstractmethod

from models.file_model import FileModel
from services.file_service import FileService, FileImportError, UnsupportedFormatError
from utils.log_manager import LogManager


class IFileController(ABC):
    """文件控制器接口"""
    
    @abstractmethod
    def import_file(self, file_path: str) -> FileModel:
        pass
    
    @abstractmethod
    def validate_file(self, file_path: str) -> bool:
        pass
    
    @abstractmethod
    def get_file_info(self, file_path: str) -> dict:
        pass


class FileController(IFileController):
    """文件控制器实现"""
    
    def __init__(self):
        self.logger = LogManager().get_logger("FileController")
        self.file_service = FileService()
    
    def import_file(self, file_path: str) -> FileModel:
        """导入文件"""
        try:
            self.logger.info(f"开始导入文件: {file_path}")
            
            # 验证文件
            if not self.validate_file(file_path):
                raise FileImportError(f"文件验证失败: {file_path}")
            
            # 加载文件
            file_model = self.file_service.load_file(file_path)
            
            self.logger.info(f"文件导入成功: {file_path}")
            return file_model
            
        except Exception as e:
            self.logger.error(f"文件导入失败: {file_path}, 错误: {e}")
            raise FileImportError(f"文件导入失败: {e}")
    
    def validate_file(self, file_path: str) -> bool:
        """验证文件"""
        try:
            return self.file_service.validate_file(file_path)
        except Exception as e:
            self.logger.error(f"文件验证失败: {file_path}, 错误: {e}")
            return False
    
    def get_file_info(self, file_path: str) -> dict:
        """获取文件信息"""
        try:
            return self.file_service.get_file_info(file_path)
        except Exception as e:
            self.logger.error(f"获取文件信息失败: {file_path}, 错误: {e}")
            return {}
    
    def get_supported_formats(self) -> List[str]:
        """获取支持的文件格式"""
        try:
            return self.file_service.get_supported_formats()
        except Exception as e:
            self.logger.error(f"获取支持格式失败: {e}")
            return []
    
    def batch_import_files(self, file_paths: List[str]) -> List[FileModel]:
        """批量导入文件"""
        try:
            self.logger.info(f"开始批量导入 {len(file_paths)} 个文件")
            
            imported_files = []
            failed_files = []
            
            for file_path in file_paths:
                try:
                    file_model = self.import_file(file_path)
                    imported_files.append(file_model)
                except Exception as e:
                    self.logger.error(f"文件导入失败: {file_path}, 错误: {e}")
                    failed_files.append({'path': file_path, 'error': str(e)})
            
            self.logger.info(f"批量导入完成，成功: {len(imported_files)}, 失败: {len(failed_files)}")
            
            return imported_files
            
        except Exception as e:
            self.logger.error(f"批量导入失败: {e}")
            raise FileImportError(f"批量导入失败: {e}")
    
    def check_file_availability(self, file_path: str) -> dict:
        """检查文件可用性"""
        try:
            result = {
                'available': False,
                'exists': False,
                'readable': False,
                'supported': False,
                'size_valid': False,
                'error': None
            }
            
            # 检查文件是否存在
            import os
            result['exists'] = os.path.exists(file_path)
            if not result['exists']:
                result['error'] = "文件不存在"
                return result
            
            # 检查文件是否可读
            try:
                with open(file_path, 'rb') as f:
                    f.read(1)
                result['readable'] = True
            except Exception as e:
                result['error'] = f"文件不可读: {e}"
                return result
            
            # 检查文件格式是否支持
            result['supported'] = self.file_service.is_supported_format(file_path)
            if not result['supported']:
                result['error'] = "不支持的文件格式"
                return result
            
            # 检查文件大小
            file_size = os.path.getsize(file_path)
            max_size = 100 * 1024 * 1024  # 100MB
            result['size_valid'] = file_size <= max_size
            if not result['size_valid']:
                result['error'] = f"文件过大: {file_size / 1024 / 1024:.2f}MB"
                return result
            
            result['available'] = True
            return result
            
        except Exception as e:
            self.logger.error(f"检查文件可用性失败: {file_path}, 错误: {e}")
            return {
                'available': False,
                'exists': False,
                'readable': False,
                'supported': False,
                'size_valid': False,
                'error': str(e)
            }
    
    def get_file_preview(self, file_path: str, max_length: int = 1000) -> str:
        """获取文件预览"""
        try:
            if not self.validate_file(file_path):
                return "文件验证失败"
            
            # 导入文件
            file_model = self.file_service.load_file(file_path)
            
            if not file_model.content:
                return "文件内容为空"
            
            # 截取预览内容
            content = file_model.content
            if len(content) > max_length:
                content = content[:max_length] + "..."
            
            return content
            
        except Exception as e:
            self.logger.error(f"获取文件预览失败: {file_path}, 错误: {e}")
            return f"预览失败: {e}"
    
    def extract_text_from_file(self, file_path: str) -> str:
        """从文件中提取文本"""
        try:
            file_model = self.import_file(file_path)
            return file_model.content or ""
        except Exception as e:
            self.logger.error(f"提取文件文本失败: {file_path}, 错误: {e}")
            raise FileImportError(f"提取文件文本失败: {e}")
    
    def get_file_statistics(self, file_path: str) -> dict:
        """获取文件统计信息"""
        try:
            file_model = self.import_file(file_path)
            
            if not file_model.content:
                return {
                    'file_size': file_model.file_size,
                    'file_size_mb': file_model.get_size_mb(),
                    'text_length': 0,
                    'word_count': 0,
                    'line_count': 0
                }
            
            content = file_model.content
            word_count = len(content.split())
            line_count = len(content.split('\n'))
            
            return {
                'file_size': file_model.file_size,
                'file_size_mb': file_model.get_size_mb(),
                'text_length': len(content),
                'word_count': word_count,
                'line_count': line_count,
                'estimated_reading_time': word_count / 200,  # 假设每分钟200字
                'estimated_speech_time': word_count / 150   # 假设每分钟150字
            }
            
        except Exception as e:
            self.logger.error(f"获取文件统计信息失败: {file_path}, 错误: {e}")
            return {}
