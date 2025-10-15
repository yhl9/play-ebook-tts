"""
文本模型模块

提供文本处理相关的数据模型，包括：
- 章节模型：章节信息、内容、位置等
- 处理后的文本模型：清理后的文本、分段、统计信息等
- 文本统计：字数、字符数、章节数等
- 内容访问：按章节获取文本内容
- 序列化：支持字典格式转换

文本模型特性：
- 自动统计：自动计算字数、字符数等统计信息
- 章节管理：支持章节的创建、访问和管理
- 内容分段：支持文本的分段处理
- 类型安全：完整的类型提示
- 序列化：支持字典格式转换

作者: TTS开发团队
版本: 1.0.0
创建时间: 2024
"""

from dataclasses import dataclass
from typing import List, Optional


@dataclass
class Chapter:
    """
    章节模型
    
    存储单个章节的信息，包括标题、位置、内容等。
    提供章节的基本操作和统计功能。
    
    Attributes:
        title (str): 章节标题
        start_pos (int): 开始位置
        end_pos (int): 结束位置
        level (int): 章节级别
        content (str): 章节内容
        selected (bool): 是否被选中
        original_filename (str): 原始文件名
    """
    title: str
    start_pos: int
    end_pos: int
    level: int = 1
    content: str = ""
    original_filename: str = ""
    selected: bool = False
    
    def get_length(self) -> int:
        """
        获取章节长度
        
        计算章节的字符长度。
        
        Returns:
            int: 章节长度（字符数）
        """
        return self.end_pos - self.start_pos
    
    def to_dict(self) -> dict:
        """
        转换为字典格式
        
        将章节对象转换为字典，便于序列化和存储。
        
        Returns:
            dict: 包含章节信息的字典
        """
        return {
            'title': self.title,
            'start_pos': self.start_pos,
            'end_pos': self.end_pos,
            'level': self.level,
            'length': self.get_length()
        }


@dataclass
class ProcessedText:
    """
    处理后的文本模型
    
    存储文本处理后的完整信息，包括原始文本、清理后的文本、
    章节列表、分段列表、统计信息等。提供文本内容的访问和管理功能。
    
    Attributes:
        original_text (str): 原始文本
        cleaned_text (str): 清理后的文本
        chapters (List[Chapter]): 章节列表
        segments (List[str]): 分段列表
        word_count (int): 单词数
        char_count (int): 字符数
    """
    original_text: str
    cleaned_text: str
    chapters: List[Chapter]
    segments: List[str]
    word_count: int
    char_count: int
    
    def __post_init__(self):
        """
        初始化后处理
        
        在对象创建后自动执行，如果统计信息为0则自动计算。
        """
        if not self.word_count:
            self.word_count = len(self.cleaned_text.split())
        if not self.char_count:
            self.char_count = len(self.cleaned_text)
    
    def get_chapter_text(self, chapter_index: int) -> str:
        """
        获取指定章节的文本
        
        根据章节索引获取对应章节的文本内容。
        
        Args:
            chapter_index (int): 章节索引
            
        Returns:
            str: 章节文本内容，如果索引无效返回空字符串
        """
        if 0 <= chapter_index < len(self.chapters):
            chapter = self.chapters[chapter_index]
            return self.cleaned_text[chapter.start_pos:chapter.end_pos]
        return ""
    
    def get_chapter_count(self) -> int:
        """
        获取章节数量
        
        返回文本中的章节总数。
        
        Returns:
            int: 章节数量
        """
        return len(self.chapters)
    
    def get_segment_count(self) -> int:
        """
        获取分段数量
        
        返回文本的分段总数。
        
        Returns:
            int: 分段数量
        """
        return len(self.segments)
    
    def get_total_length(self) -> int:
        """
        获取总文本长度
        
        返回清理后文本的总字符数。
        
        Returns:
            int: 总文本长度（字符数）
        """
        return len(self.cleaned_text)
    
    def to_dict(self) -> dict:
        """
        转换为字典格式
        
        将处理后的文本对象转换为字典，便于序列化和存储。
        
        Returns:
            dict: 包含所有文本信息的字典
        """
        return {
            'original_text': self.original_text,
            'cleaned_text': self.cleaned_text,
            'chapters': [chapter.to_dict() for chapter in self.chapters],
            'segments': self.segments,
            'word_count': self.word_count,
            'char_count': self.char_count,
            'chapter_count': self.get_chapter_count(),
            'segment_count': self.get_segment_count(),
            'total_length': self.get_total_length()
        }
    
    def get_summary(self) -> dict:
        """
        获取文本摘要
        
        返回文本的统计摘要信息，包括字数、字符数、章节数等。
        
        Returns:
            dict: 文本摘要信息字典
        """
        return {
            'word_count': self.word_count,
            'char_count': self.char_count,
            'chapter_count': self.get_chapter_count(),
            'segment_count': self.get_segment_count(),
            'total_length': self.get_total_length()
        }
