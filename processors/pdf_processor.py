"""
PDF文件处理器
"""

import io
from typing import Optional
from pathlib import Path

try:
    import PyPDF2
    PDF_AVAILABLE = True
except ImportError:
    PDF_AVAILABLE = False

from utils.log_manager import LogManager


class PDFProcessor:
    """PDF文件处理器"""
    
    def __init__(self):
        self.logger = LogManager().get_logger("PDFProcessor")
        if not PDF_AVAILABLE:
            self.logger.warning("PyPDF2未安装，PDF处理功能不可用")
    
    def extract_text(self, file_path: str) -> str:
        """提取PDF文本"""
        try:
            if not PDF_AVAILABLE:
                raise ImportError("PyPDF2未安装，无法处理PDF文件")
            
            if not Path(file_path).exists():
                raise FileNotFoundError(f"PDF文件不存在: {file_path}")
            
            self.logger.info(f"开始提取PDF文本: {file_path}")
            
            text_content = ""
            
            with open(file_path, 'rb') as file:
                pdf_reader = PyPDF2.PdfReader(file)
                
                # 获取页数
                num_pages = len(pdf_reader.pages)
                self.logger.info(f"PDF文件页数: {num_pages}")
                
                # 提取每页文本
                for page_num in range(num_pages):
                    try:
                        page = pdf_reader.pages[page_num]
                        page_text = page.extract_text()
                        
                        if page_text:
                            text_content += page_text + "\n"
                        
                        self.logger.debug(f"提取第 {page_num + 1} 页文本完成")
                        
                    except Exception as e:
                        self.logger.warning(f"提取第 {page_num + 1} 页文本失败: {e}")
                        continue
            
            if not text_content.strip():
                self.logger.warning("PDF文件中未找到可提取的文本")
                return ""
            
            # 清理文本
            text_content = self._clean_extracted_text(text_content)
            
            self.logger.info(f"PDF文本提取完成，文本长度: {len(text_content)}")
            return text_content
            
        except Exception as e:
            self.logger.error(f"PDF文本提取失败: {file_path}, 错误: {e}")
            raise PDFProcessingError(f"PDF文本提取失败: {e}")
    
    def _clean_extracted_text(self, text: str) -> str:
        """清理提取的文本"""
        if not text:
            return ""
        
        import re
        
        # 保持段落结构，不要将所有空白字符合并为单个空格
        # 只清理多余的空白字符，但保留段落间的双换行符
        text = re.sub(r'[ \t]+', ' ', text)  # 将多个空格/制表符合并为单个空格
        text = re.sub(r'\n[ \t]+', '\n', text)  # 清理行首空白
        text = re.sub(r'[ \t]+\n', '\n', text)  # 清理行尾空白
        
        # 保持段落间的双换行符，但清理多余的空行
        text = re.sub(r'\n\s*\n\s*\n+', '\n\n', text)
        
        # 移除首尾空白
        text = text.strip()
        
        return text
    
    def get_pdf_info(self, file_path: str) -> dict:
        """获取PDF文件信息"""
        try:
            if not PDF_AVAILABLE:
                return {}
            
            with open(file_path, 'rb') as file:
                pdf_reader = PyPDF2.PdfReader(file)
                
                info = {
                    'num_pages': len(pdf_reader.pages),
                    'is_encrypted': pdf_reader.is_encrypted,
                    'metadata': {}
                }
                
                # 获取元数据
                if pdf_reader.metadata:
                    metadata = pdf_reader.metadata
                    info['metadata'] = {
                        'title': metadata.get('/Title', ''),
                        'author': metadata.get('/Author', ''),
                        'subject': metadata.get('/Subject', ''),
                        'creator': metadata.get('/Creator', ''),
                        'producer': metadata.get('/Producer', ''),
                        'creation_date': metadata.get('/CreationDate', ''),
                        'modification_date': metadata.get('/ModDate', '')
                    }
                
                return info
                
        except Exception as e:
            self.logger.error(f"获取PDF信息失败: {file_path}, 错误: {e}")
            return {}
    
    def is_pdf_encrypted(self, file_path: str) -> bool:
        """检查PDF是否加密"""
        try:
            if not PDF_AVAILABLE:
                return False
            
            with open(file_path, 'rb') as file:
                pdf_reader = PyPDF2.PdfReader(file)
                return pdf_reader.is_encrypted
                
        except Exception as e:
            self.logger.error(f"检查PDF加密状态失败: {file_path}, 错误: {e}")
            return False
    
    def extract_text_from_page(self, file_path: str, page_number: int) -> str:
        """提取指定页的文本"""
        try:
            if not PDF_AVAILABLE:
                raise ImportError("PyPDF2未安装，无法处理PDF文件")
            
            with open(file_path, 'rb') as file:
                pdf_reader = PyPDF2.PdfReader(file)
                
                if page_number < 0 or page_number >= len(pdf_reader.pages):
                    raise ValueError(f"页码超出范围: {page_number}")
                
                page = pdf_reader.pages[page_number]
                text = page.extract_text()
                
                return self._clean_extracted_text(text)
                
        except Exception as e:
            self.logger.error(f"提取PDF页面文本失败: {file_path}, 页面: {page_number}, 错误: {e}")
            raise PDFProcessingError(f"提取PDF页面文本失败: {e}")
    
    def get_page_count(self, file_path: str) -> int:
        """获取PDF页数"""
        try:
            if not PDF_AVAILABLE:
                return 0
            
            with open(file_path, 'rb') as file:
                pdf_reader = PyPDF2.PdfReader(file)
                return len(pdf_reader.pages)
                
        except Exception as e:
            self.logger.error(f"获取PDF页数失败: {file_path}, 错误: {e}")
            return 0


class PDFProcessingError(Exception):
    """PDF处理异常"""
    pass
