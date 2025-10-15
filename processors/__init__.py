"""
文件处理器
"""

from .pdf_processor import PDFProcessor
from .epub_processor import EPUBProcessor
from .docx_processor import DOCXProcessor

__all__ = [
    'PDFProcessor',
    'EPUBProcessor',
    'DOCXProcessor'
]
