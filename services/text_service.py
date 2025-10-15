"""
文本服务模块

提供文本处理和解析功能，包括：
- 文本清理：去除多余空白、特殊字符等
- 章节检测：自动识别文本中的章节结构
- 文本分段：按不同规则分割文本内容
- 格式解析：支持Markdown等格式的解析
- 缓存管理：文本处理结果的缓存和复用

支持的文本格式：
- 纯文本：TXT格式的文本文件
- Markdown：支持Markdown语法的文本
- 结构化文本：包含章节标题的文本

文本分段策略：
- 按章节分段：根据章节标题分割
- 按段落分段：根据段落分割
- 按长度分段：根据指定长度分割
- 按句子分段：根据句子分割

作者: TTS开发团队
版本: 1.0.0
创建时间: 2024
"""

import os
import re
from typing import List, Optional, Dict, Any
from abc import ABC, abstractmethod

from models.text_model import ProcessedText, Chapter
from utils.log_manager import LogManager
from services.cache_service import CacheService
from services.markdown_parser import MarkdownParser


class ITextService(ABC):
    """
    文本服务接口
    
    定义文本处理服务的标准接口，包括文本清理、章节检测、文本分段等功能。
    采用接口隔离原则，确保不同实现的一致性。
    """
    
    @abstractmethod
    def clean_text(self, text: str) -> str:
        """
        清理文本内容
        
        Args:
            text (str): 原始文本
            
        Returns:
            str: 清理后的文本
        """
        pass
    
    @abstractmethod
    def detect_chapters(self, text: str) -> List[Chapter]:
        """
        检测文本中的章节结构
        
        Args:
            text (str): 输入文本
            
        Returns:
            List[Chapter]: 章节列表
        """
        pass
    
    @abstractmethod
    def split_text(self, text: str, split_type: str, **kwargs) -> List[str]:
        """
        按指定方式分割文本
        
        Args:
            text (str): 输入文本
            split_type (str): 分割类型
            **kwargs: 额外参数
            
        Returns:
            List[str]: 分割后的文本片段列表
        """
        pass


class TextService(ITextService):
    """
    文本服务实现类
    
    提供完整的文本处理功能，包括文本清理、章节检测、文本分段等。
    支持多种文本格式和分段策略，提供缓存机制提高性能。
    
    特性：
    - 智能清理：自动清理文本中的多余字符和格式
    - 章节识别：支持多种章节标题格式的识别
    - 灵活分段：支持多种文本分段策略
    - 格式支持：支持Markdown等格式的解析
    - 缓存优化：使用缓存提高重复处理性能
    """
    
    def __init__(self, cache_dir: str = "cache"):
        self.logger = LogManager().get_logger("TextService")
        self.cache_service = CacheService(cache_dir)
        self.markdown_parser = MarkdownParser()
        
        # 定义不同的章节模式集合
        self.chapter_pattern_sets = {
            'chinese_chapter': [r'第[一二三四五六七八九十\d]+章[：:\s]*.*'],
            'chinese_section': [r'第[一二三四五六七八九十\d]+节[：:\s]*.*'],
            'english_chapter': [r'Chapter\s+\d+[：:\s]*.*'],
            'english_section': [r'Section\s+\d+[：:\s]*.*'],
            # 'numbered_dot': [r'^\d+\.\s+.*'],
            # 'numbered_space': [r'^\d+\s+.*'],
            'mixed': [  # 混合模式，保持原有行为
                r'第[一二三四五六七八九十\d]+章[：:\s]*.*',
                r'Chapter\s+\d+[：:\s]*.*',
                r'第[一二三四五六七八九十\d]+节[：:\s]*.*',
                r'Section\s+\d+[：:\s]*.*',
                # r'^\d+\.\s+.*',
                # r'^\d+\s+.*'
            ]
        }
        
        # 默认使用混合模式
        self.current_pattern_set = 'mixed'
        self.chapter_patterns = self.chapter_pattern_sets[self.current_pattern_set]
    
    def set_chapter_pattern(self, pattern_type: str) -> bool:
        """
        设置章节检测模式
        
        Args:
            pattern_type (str): 模式类型，可选值：
                - 'chinese_chapter': 中文章节模式
                - 'chinese_section': 中文节模式
                - 'english_chapter': 英文章节模式
                - 'english_section': 英文节模式
                - 'numbered_dot': 数字点号模式
                - 'numbered_space': 数字空格模式
                - 'mixed': 混合模式（默认）
        
        Returns:
            bool: 设置是否成功
        """
        try:
            if pattern_type not in self.chapter_pattern_sets:
                self.logger.error(f"不支持的章节模式类型: {pattern_type}")
                return False
            
            self.current_pattern_set = pattern_type
            self.chapter_patterns = self.chapter_pattern_sets[pattern_type]
            self.logger.info(f"章节检测模式已设置为: {pattern_type}")
            return True
            
        except Exception as e:
            self.logger.error(f"设置章节模式失败: {e}")
            return False
    
    def get_available_patterns(self) -> List[str]:
        """
        获取可用的章节模式列表
        
        Returns:
            List[str]: 可用的模式类型列表
        """
        return list(self.chapter_pattern_sets.keys())
    
    def get_current_pattern(self) -> str:
        """
        获取当前使用的章节模式
        
        Returns:
            str: 当前模式类型
        """
        return self.current_pattern_set
    
    def auto_detect_pattern(self, text: str) -> str:
        """
        自动检测最适合的章节模式
        
        Args:
            text (str): 要检测的文本
            
        Returns:
            str: 检测到的最佳模式类型
        """
        try:
            if not text:
                return 'mixed'
            
            # 统计各种模式的匹配数量
            pattern_scores = {}
            
            for pattern_type, patterns in self.chapter_pattern_sets.items():
                if pattern_type == 'mixed':
                    continue
                    
                match_count = 0
                lines = text.split('\n')
                
                for line in lines:
                    line = line.strip()
                    if not line:
                        continue
                    
                    for pattern in patterns:
                        if re.match(pattern, line, re.IGNORECASE):
                            match_count += 1
                            break
                
                pattern_scores[pattern_type] = match_count
            
            # 找到匹配数量最多的模式
            if pattern_scores:
                best_pattern = max(pattern_scores, key=pattern_scores.get)
                if pattern_scores[best_pattern] > 0:
                    self.logger.info(f"自动检测到最佳章节模式: {best_pattern} (匹配 {pattern_scores[best_pattern]} 个章节)")
                    return best_pattern
            
            # 如果没有找到匹配的模式，返回混合模式
            self.logger.info("未检测到特定章节模式，使用混合模式")
            return 'mixed'
            
        except Exception as e:
            self.logger.error(f"自动检测章节模式失败: {e}")
            return 'mixed'
    
    def clean_text(self, text: str) -> str:
        """清理文本"""
        try:
            if not text:
                return ""
            
            # 按行处理，保留换行符结构
            lines = text.split('\n')
            cleaned_lines = []
            
            for line in lines:
                # 清理每行的多余空格和制表符
                cleaned_line = re.sub(r'[ \t]+', ' ', line)
                # 移除行首行尾空格
                cleaned_line = cleaned_line.strip()
                cleaned_lines.append(cleaned_line)
            
            # 重新组合文本
            text = '\n'.join(cleaned_lines)
            
            # 移除特殊字符（保留中文、英文、数字、标点符号和换行符）
            # 使用更精确的字符集，确保标点符号不被移除，特别是对断句重要的标点
            # 保留的标点符号：基本标点、中文标点、省略号、破折号、引号、括号等
            text = re.sub(r'[^\w\s\u4e00-\u9fff.,!?;:()（）【】《》""''""''…—–—、，。！？；：""''（）【】《》〈〉「」『』〔〕〖〗〘〙〚〛\n\r\u3000-\u303f\uff00-\uffef]', '', text)
            
            # 清理多余的换行符（保留段落分隔）
            text = re.sub(r'\n\s*\n\s*\n+', '\n\n', text)
            
            # 移除首尾空白
            text = text.strip()
            
            self.logger.debug(f"文本清理完成，原始长度: {len(text)}, 清理后长度: {len(text)}")
            return text
            
        except Exception as e:
            self.logger.error(f"文本清理失败: {e}")
            return text
    
    def detect_chapters(self, text: str, auto_detect: bool = True) -> List[Chapter]:
        """
        检测章节
        
        Args:
            text (str): 输入文本
            auto_detect (bool): 是否自动检测最佳模式，默认True
            
        Returns:
            List[Chapter]: 章节列表
        """
        try:
            chapters = []
            if not text:
                return chapters
            
            # 如果启用自动检测，先检测最佳模式
            if auto_detect:
                best_pattern = self.auto_detect_pattern(text)
                if best_pattern != self.current_pattern_set:
                    self.set_chapter_pattern(best_pattern)
            
            # 按行分割文本
            lines = text.split('\n')
            current_pos = 0
            
            for i, line in enumerate(lines):
                line = line.strip()
                if not line:
                    current_pos += 1
                    continue
                
                # 检查是否匹配章节模式
                for pattern in self.chapter_patterns:
                    if re.match(pattern, line, re.IGNORECASE):
                        # 计算在原始文本中的位置
                        line_start = current_pos
                        line_end = current_pos + len(line)
                        
                        # 清理章节标题中的不可见字符
                        clean_title = self._clean_chapter_title(line)
                        
                        chapter = Chapter(
                            title=clean_title,  # 使用清理后的标题
                            start_pos=line_start,
                            end_pos=line_end,
                            level=self._get_chapter_level(line)
                        )
                        chapters.append(chapter)
                        break
                
                current_pos += len(line) + 1  # +1 for newline
            
            # 设置章节结束位置和内容
            for i, chapter in enumerate(chapters):
                if i < len(chapters) - 1:
                    # 下一个章节的开始位置
                    chapter.end_pos = chapters[i + 1].start_pos
                else:
                    # 最后一个章节到文本结尾
                    chapter.end_pos = len(text)
                
                # 提取章节内容
                chapter.content = text[chapter.start_pos:chapter.end_pos].strip()
            
            self.logger.info(f"检测到 {len(chapters)} 个章节")
            return chapters
            
        except Exception as e:
            self.logger.error(f"章节检测失败: {e}")
            return []
    
    def split_text(self, text: str, split_type: str, **kwargs) -> List[str]:
        """分割文本"""
        try:
            if split_type == 'length':
                max_length = kwargs.get('max_length', 2000)
                return self.split_by_length(text, max_length)
            elif split_type == 'chapters':
                return self.split_by_chapters(text)
            elif split_type == 'paragraphs':
                return self.split_by_paragraphs(text)
            else:
                raise ValueError(f"不支持的分割类型: {split_type}")
                
        except Exception as e:
            self.logger.error(f"文本分割失败: {e}")
            return [text]
    
    def split_by_length(self, text: str, max_length: int) -> List[str]:
        """按长度分割文本"""
        try:
            if not text or max_length <= 0:
                return [text] if text else []
            
            segments = []
            current_pos = 0
            
            while current_pos < len(text):
                end_pos = min(current_pos + max_length, len(text))
                
                # 如果不是最后一段，尝试在句号、问号、感叹号处分割
                if end_pos < len(text):
                    # 向前查找合适的分割点
                    for i in range(end_pos, max(current_pos, end_pos - 200), -1):
                        if text[i] in '。！？':
                            end_pos = i + 1
                            break
                
                segment = text[current_pos:end_pos].strip()
                if segment:
                    segments.append(segment)
                
                current_pos = end_pos
            
            self.logger.info(f"按长度分割完成，共 {len(segments)} 段")
            return segments
            
        except Exception as e:
            self.logger.error(f"按长度分割失败: {e}")
            return [text]
    
    def split_by_chapters(self, text: str) -> List[str]:
        """按章节分割文本"""
        try:
            chapters = self.detect_chapters(text)
            if not chapters:
                return [text]
            
            segments = []
            for chapter in chapters:
                segment = text[chapter.start_pos:chapter.end_pos].strip()
                if segment:
                    segments.append(segment)
            
            self.logger.info(f"按章节分割完成，共 {len(segments)} 段")
            return segments
            
        except Exception as e:
            self.logger.error(f"按章节分割失败: {e}")
            return [text]
    
    def split_by_paragraphs(self, text: str) -> List[str]:
        """按段落分割文本"""
        try:
            # 多种段落分割模式
            # 1. 按双换行符分割（标准段落分隔）
            paragraphs = re.split(r'\n\s*\n', text)
            
            # 2. 如果段落太少，尝试按单换行符分割（适用于某些PDF/EPUB）
            if len(paragraphs) <= 1:
                paragraphs = re.split(r'\n', text)
            
            # 3. 如果还是没有段落，尝试按句号分割（最后手段）
            if len(paragraphs) <= 1:
                paragraphs = re.split(r'[。！？]', text)
            
            # 清理和过滤段落
            segments = []
            for p in paragraphs:
                p = p.strip()
                if p and len(p) > 10:  # 过滤太短的段落
                    segments.append(p)
            
            # 如果还是没有有效段落，返回整个文本
            if not segments:
                segments = [text.strip()]
            
            self.logger.info(f"按段落分割完成，共 {len(segments)} 段")
            return segments
            
        except Exception as e:
            self.logger.error(f"按段落分割失败: {e}")
            return [text]
    
    def import_file(self, file_path: str, file_type: str = "auto") -> Optional[ProcessedText]:
        """导入文件"""
        try:
            if not os.path.exists(file_path):
                self.logger.error(f"文件不存在: {file_path}")
                return None
            
            # 检查缓存
            cached_data = self.cache_service.load_from_cache(file_path)
            if cached_data:
                self.logger.info(f"从缓存加载文件: {file_path}")
                return self._create_processed_text_from_cache(cached_data)
            
            # 读取文件内容
            content = self._read_file_content(file_path, file_type)
            if not content:
                return None
            
            # 处理文本
            processed_text = self._process_file_content(content, file_path, file_type)
            
            # 保存到缓存
            metadata = {
                "file_type": file_type,
                "file_size": len(content),
                "chapter_count": len(processed_text.chapters) if processed_text else 0
            }
            self.cache_service.save_to_cache(file_path, content, metadata)
            
            return processed_text
            
        except Exception as e:
            self.logger.error(f"导入文件失败: {e}")
            return None
    
    def _read_file_content(self, file_path: str, file_type: str) -> Optional[str]:
        """读取文件内容"""
        try:
            # 自动检测文件类型
            if file_type == "auto":
                file_type = self._detect_file_type(file_path)
            
            if file_type == "markdown":
                return self._read_markdown_file(file_path)
            elif file_type == "txt":
                return self._read_text_file(file_path)
            else:
                self.logger.warning(f"不支持的文件类型: {file_type}")
                return None
                
        except Exception as e:
            self.logger.error(f"读取文件内容失败: {e}")
            return None
    
    def _detect_file_type(self, file_path: str) -> str:
        """检测文件类型"""
        try:
            ext = os.path.splitext(file_path)[1].lower()
            if ext in ['.md', '.markdown']:
                return "markdown"
            elif ext in ['.txt']:
                return "txt"
            else:
                # 尝试读取文件内容判断
                with open(file_path, 'r', encoding='utf-8') as f:
                    content = f.read(1000)  # 读取前1000个字符
                    if re.search(r'^#{1,6}\s+', content, re.MULTILINE):
                        return "markdown"
                    else:
                        return "txt"
        except Exception as e:
            self.logger.error(f"检测文件类型失败: {e}")
            return "txt"
    
    def _read_markdown_file(self, file_path: str) -> Optional[str]:
        """读取Markdown文件"""
        try:
            with open(file_path, 'r', encoding='utf-8') as f:
                content = f.read()
            
            # 验证Markdown内容
            validation = self.markdown_parser.validate_markdown(content)
            if not validation["valid"]:
                self.logger.warning(f"Markdown文件验证失败: {file_path}")
            
            return content
            
        except Exception as e:
            self.logger.error(f"读取Markdown文件失败: {e}")
            return None
    
    def _read_text_file(self, file_path: str) -> Optional[str]:
        """读取文本文件"""
        try:
            with open(file_path, 'r', encoding='utf-8') as f:
                return f.read()
        except Exception as e:
            self.logger.error(f"读取文本文件失败: {e}")
            return None
    
    def _process_file_content(self, content: str, file_path: str, file_type: str) -> Optional[ProcessedText]:
        """处理文件内容"""
        try:
            if file_type == "markdown":
                return self._process_markdown_content(content, file_path)
            else:
                return self._process_text_content(content, file_path)
                
        except Exception as e:
            self.logger.error(f"处理文件内容失败: {e}")
            return None
    
    def _process_markdown_content(self, content: str, file_path: str) -> Optional[ProcessedText]:
        """处理Markdown内容"""
        try:
            # 解析Markdown章节
            sections = self.markdown_parser.parse_markdown(content)
            
            if not sections:
                return None
            
            # 转换为Chapter对象
            chapters = []
            for i, section in enumerate(sections):
                # 提取纯文本内容
                clean_content = self.markdown_parser.extract_text_from_markdown(section.content)
                
                chapter = Chapter(
                    title=section.title,
                    content=clean_content,
                    chapter_number=i + 1,
                    word_count=len(clean_content),
                    char_count=len(clean_content)
                )
                chapters.append(chapter)
            
            # 创建ProcessedText对象
            processed_text = ProcessedText(
                original_text=content,
                chapters=chapters,
                total_chapters=len(chapters),
                total_words=sum(chapter.word_count for chapter in chapters),
                total_chars=sum(chapter.char_count for chapter in chapters)
            )
            
            self.logger.info(f"Markdown文件处理完成: {file_path}, 共 {len(chapters)} 个章节")
            return processed_text
            
        except Exception as e:
            self.logger.error(f"处理Markdown内容失败: {e}")
            return None
    
    def _process_text_content(self, content: str, file_path: str) -> Optional[ProcessedText]:
        """处理文本内容"""
        try:
            # 清理文本
            clean_text = self.clean_text(content)
            
            # 检测章节
            chapters = self.detect_chapters(clean_text)
            
            if not chapters:
                # 如果没有检测到章节，创建默认章节
                chapters = [Chapter(
                    title="文档内容",
                    content=clean_text,
                    chapter_number=1,
                    word_count=len(clean_text.split()),
                    char_count=len(clean_text)
                )]
            
            # 创建ProcessedText对象
            processed_text = ProcessedText(
                original_text=content,
                chapters=chapters,
                total_chapters=len(chapters),
                total_words=sum(chapter.word_count for chapter in chapters),
                total_chars=sum(chapter.char_count for chapter in chapters)
            )
            
            self.logger.info(f"文本文件处理完成: {file_path}, 共 {len(chapters)} 个章节")
            return processed_text
            
        except Exception as e:
            self.logger.error(f"处理文本内容失败: {e}")
            return None
    
    def _create_processed_text_from_cache(self, cached_data: Dict[str, Any]) -> Optional[ProcessedText]:
        """从缓存数据创建ProcessedText对象"""
        try:
            content = cached_data.get("content", "")
            metadata = cached_data.get("metadata", {})
            
            # 根据文件类型处理内容
            file_type = metadata.get("file_type", "txt")
            if file_type == "markdown":
                return self._process_markdown_content(content, cached_data.get("file_path", ""))
            else:
                return self._process_text_content(content, cached_data.get("file_path", ""))
                
        except Exception as e:
            self.logger.error(f"从缓存创建ProcessedText失败: {e}")
            return None
    
    def get_cache_info(self) -> Dict[str, Any]:
        """获取缓存信息"""
        return self.cache_service.get_cache_info()
    
    def clear_cache(self) -> bool:
        """清空缓存"""
        return self.cache_service.clear_cache()
    
    def set_cache_dir(self, cache_dir: str) -> bool:
        """设置缓存目录"""
        return self.cache_service.set_cache_dir(cache_dir)
    
    def process_text(self, text: str) -> ProcessedText:
        """处理文本"""
        try:
            # 清理文本
            cleaned_text = self.clean_text(text)
            
            # 检测章节（使用原始文本，保持格式）
            chapters = self.detect_chapters(text)
            
            # 分割文本（使用清理后的文本）
            segments = self.split_by_length(cleaned_text, 100)  # 使用更小的分割长度进行测试
            
            # 统计信息
            word_count = len(cleaned_text.split())
            char_count = len(cleaned_text)
            
            processed_text = ProcessedText(
                original_text=text,
                cleaned_text=cleaned_text,
                chapters=chapters,
                segments=segments,
                word_count=word_count,
                char_count=char_count
            )
            
            self.logger.info(f"文本处理完成，字数: {word_count}, 字符数: {char_count}, 章节数: {len(chapters)}")
            return processed_text
            
        except Exception as e:
            self.logger.error(f"文本处理失败: {e}")
            raise TextProcessingError(f"文本处理失败: {e}")
    
    def _clean_chapter_title(self, title: str) -> str:
        """
        清理章节标题中的不可见字符和异常字符
        
        Args:
            title (str): 原始章节标题
            
        Returns:
            str: 清理后的章节标题
        """
        try:
            if not title:
                return ""
            
            # 移除不可见字符和控制字符
            # 包括：零宽空格、BOM、制表符、回车符等
            invisible_chars = [
                '\ufeff',  # BOM
                '\u200b',  # 零宽空格
                '\u200c',  # 零宽非连字符
                '\u200d',  # 零宽连字符
                '\u2060',  # 词连接符
                '\u00a0',  # 不间断空格
                '\t',      # 制表符
                '\r',      # 回车符
                '\v',      # 垂直制表符
                '\f',      # 换页符
            ]
            
            clean_title = title
            for char in invisible_chars:
                clean_title = clean_title.replace(char, '')
            
            # 移除控制字符（ASCII 0-31，除了换行符）
            clean_title = re.sub(r'[\x00-\x08\x0b\x0c\x0e-\x1f\x7f]', '', clean_title)
            
            # 移除Unicode替换字符
            clean_title = re.sub(r'[\ufffd]', '', clean_title)
            
            # 清理多余的空格
            clean_title = re.sub(r'\s+', ' ', clean_title)
            
            # 移除首尾空格
            clean_title = clean_title.strip()
            
            # 如果清理后为空，返回原始标题
            if not clean_title:
                return title.strip()
            
            self.logger.debug(f"章节标题清理: '{title}' -> '{clean_title}'")
            return clean_title
            
        except Exception as e:
            self.logger.error(f"清理章节标题失败: {e}")
            return title.strip()
    
    def _get_chapter_level(self, title: str) -> int:
        """获取章节级别"""
        if re.match(r'第[一二三四五六七八九十\d]+章', title):
            return 1
        elif re.match(r'第[一二三四五六七八九十\d]+节', title):
            return 2
        elif re.match(r'^\d+\.', title):
            return 3
        else:
            return 1
    
    def get_text_statistics(self, text: str) -> dict:
        """获取文本统计信息"""
        try:
            if not text:
                return {
                    'char_count': 0,
                    'word_count': 0,
                    'line_count': 0,
                    'paragraph_count': 0
                }
            
            char_count = len(text)
            word_count = len(text.split())
            line_count = len(text.split('\n'))
            paragraph_count = len([p for p in text.split('\n\n') if p.strip()])
            
            return {
                'char_count': char_count,
                'word_count': word_count,
                'line_count': line_count,
                'paragraph_count': paragraph_count
            }
            
        except Exception as e:
            self.logger.error(f"获取文本统计信息失败: {e}")
            return {}


class TextProcessingError(Exception):
    """文本处理异常"""
    pass
