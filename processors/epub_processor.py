"""
EPUB文件处理器
"""

from typing import Optional, List
from pathlib import Path

try:
    import ebooklib
    from ebooklib import epub
    EPUB_AVAILABLE = True
except ImportError:
    EPUB_AVAILABLE = False

from utils.log_manager import LogManager


class EPUBProcessor:
    """EPUB文件处理器"""
    
    def __init__(self):
        self.logger = LogManager().get_logger("EPUBProcessor")
        if not EPUB_AVAILABLE:
            self.logger.warning("ebooklib未安装，EPUB处理功能不可用")
    
    def extract_text(self, file_path: str) -> str:
        """提取EPUB文本"""
        try:
            if not EPUB_AVAILABLE:
                raise ImportError("ebooklib未安装，无法处理EPUB文件")
            
            if not Path(file_path).exists():
                raise FileNotFoundError(f"EPUB文件不存在: {file_path}")
            
            self.logger.info(f"开始提取EPUB文本: {file_path}")
            
            # 打开EPUB文件
            book = epub.read_epub(file_path)
            
            text_content = ""
            
            # 获取所有文本内容
            for item in book.get_items():
                if item.get_type() == ebooklib.ITEM_DOCUMENT:
                    # 提取HTML内容
                    html_content = item.get_content().decode('utf-8')
                    
                    # 简单的HTML标签清理
                    cleaned_text = self._clean_html(html_content)
                    
                    if cleaned_text.strip():
                        text_content += cleaned_text + "\n\n"
            
            if not text_content.strip():
                self.logger.warning("EPUB文件中未找到可提取的文本")
                return ""
            
            # 清理文本
            text_content = self._clean_extracted_text(text_content)
            
            self.logger.info(f"EPUB文本提取完成，文本长度: {len(text_content)}")
            return text_content
            
        except Exception as e:
            self.logger.error(f"EPUB文本提取失败: {file_path}, 错误: {e}")
            raise EPUBProcessingError(f"EPUB文本提取失败: {e}")
    
    def _clean_html(self, html_content: str) -> str:
        """清理HTML内容"""
        import re
        
        # 移除HTML标签
        text = re.sub(r'<[^>]+>', '', html_content)
        
        # 解码HTML实体
        html_entities = {
            '&amp;': '&',
            '&lt;': '<',
            '&gt;': '>',
            '&quot;': '"',
            '&#39;': "'",
            '&nbsp;': ' ',
            '&hellip;': '...',
            '&mdash;': '—',
            '&ndash;': '–',
            '&lsquo;': ''',
            '&rsquo;': ''',
            '&ldquo;': '"',
            '&rdquo;': '"'
        }
        
        for entity, char in html_entities.items():
            text = text.replace(entity, char)
        
        return text
    
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
    
    def get_epub_info(self, file_path: str) -> dict:
        """获取EPUB文件信息"""
        try:
            if not EPUB_AVAILABLE:
                return {}
            
            book = epub.read_epub(file_path)
            
            info = {
                'title': '',
                'author': '',
                'language': '',
                'publisher': '',
                'publication_date': '',
                'description': '',
                'num_chapters': 0
            }
            
            # 获取元数据
            metadata = book.get_metadata('DC', 'title')
            if metadata:
                info['title'] = metadata[0][0] if metadata[0] else ''
            
            metadata = book.get_metadata('DC', 'creator')
            if metadata:
                info['author'] = metadata[0][0] if metadata[0] else ''
            
            metadata = book.get_metadata('DC', 'language')
            if metadata:
                info['language'] = metadata[0][0] if metadata[0] else ''
            
            metadata = book.get_metadata('DC', 'publisher')
            if metadata:
                info['publisher'] = metadata[0][0] if metadata[0] else ''
            
            metadata = book.get_metadata('DC', 'date')
            if metadata:
                info['publication_date'] = metadata[0][0] if metadata[0] else ''
            
            metadata = book.get_metadata('DC', 'description')
            if metadata:
                info['description'] = metadata[0][0] if metadata[0] else ''
            
            # 计算章节数
            chapter_count = 0
            for item in book.get_items():
                if item.get_type() == ebooklib.ITEM_DOCUMENT:
                    chapter_count += 1
            info['num_chapters'] = chapter_count
            
            return info
            
        except Exception as e:
            self.logger.error(f"获取EPUB信息失败: {file_path}, 错误: {e}")
            return {}
    
    def get_chapter_list(self, file_path: str) -> List[dict]:
        """获取章节列表"""
        try:
            if not EPUB_AVAILABLE:
                return []
            
            book = epub.read_epub(file_path)
            chapters = []
            
            for item in book.get_items():
                if item.get_type() == ebooklib.ITEM_DOCUMENT:
                    # 获取章节标题
                    title = item.get_name()
                    
                    # 尝试从HTML中提取标题
                    html_content = item.get_content().decode('utf-8')
                    title_match = self._extract_title_from_html(html_content)
                    if title_match:
                        title = title_match
                    
                    chapters.append({
                        'id': item.get_id(),
                        'title': title,
                        'file_name': item.get_name(),
                        'size': len(item.get_content())
                    })
            
            return chapters
            
        except Exception as e:
            self.logger.error(f"获取EPUB章节列表失败: {file_path}, 错误: {e}")
            return []
    
    def _extract_title_from_html(self, html_content: str) -> Optional[str]:
        """从HTML中提取标题"""
        import re
        
        # 查找h1-h6标签
        title_patterns = [
            r'<h1[^>]*>(.*?)</h1>',
            r'<h2[^>]*>(.*?)</h2>',
            r'<h3[^>]*>(.*?)</h3>',
            r'<h4[^>]*>(.*?)</h4>',
            r'<h5[^>]*>(.*?)</h5>',
            r'<h6[^>]*>(.*?)</h6>',
            r'<title>(.*?)</title>'
        ]
        
        for pattern in title_patterns:
            match = re.search(pattern, html_content, re.IGNORECASE | re.DOTALL)
            if match:
                title = match.group(1).strip()
                # 清理HTML标签
                title = re.sub(r'<[^>]+>', '', title)
                if title:
                    return title
        
        return None
    
    def extract_chapter_text(self, file_path: str, chapter_id: str) -> str:
        """提取指定章节的文本"""
        try:
            if not EPUB_AVAILABLE:
                raise ImportError("ebooklib未安装，无法处理EPUB文件")
            
            book = epub.read_epub(file_path)
            
            # 查找指定章节
            item = book.get_item_by_id(chapter_id)
            if not item or item.get_type() != ebooklib.ITEM_DOCUMENT:
                raise ValueError(f"章节不存在: {chapter_id}")
            
            # 提取HTML内容
            html_content = item.get_content().decode('utf-8')
            
            # 清理HTML
            text = self._clean_html(html_content)
            
            return self._clean_extracted_text(text)
            
        except Exception as e:
            self.logger.error(f"提取EPUB章节文本失败: {file_path}, 章节: {chapter_id}, 错误: {e}")
            raise EPUBProcessingError(f"提取EPUB章节文本失败: {e}")
    
    def is_epub_valid(self, file_path: str) -> bool:
        """检查EPUB文件是否有效"""
        try:
            if not EPUB_AVAILABLE:
                return False
            
            book = epub.read_epub(file_path)
            return book is not None
            
        except Exception as e:
            self.logger.error(f"检查EPUB文件有效性失败: {file_path}, 错误: {e}")
            return False


class EPUBProcessingError(Exception):
    """EPUB处理异常"""
    pass
