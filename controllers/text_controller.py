"""
文本控制器
"""

from typing import List, Optional
from abc import ABC, abstractmethod

from models.text_model import ProcessedText, Chapter
from services.text_service import TextService, TextProcessingError
from utils.log_manager import LogManager


class ITextController(ABC):
    """文本控制器接口"""
    
    @abstractmethod
    def process_text(self, text: str) -> ProcessedText:
        pass
    
    @abstractmethod
    def split_text_by_length(self, text: str, max_length: int) -> List[str]:
        pass
    
    @abstractmethod
    def split_text_by_chapters(self, text: str) -> List[Chapter]:
        pass


class TextController(ITextController):
    """文本控制器实现"""
    
    def __init__(self):
        self.logger = LogManager().get_logger("TextController")
        self.text_service = TextService()
    
    def process_text(self, text: str) -> ProcessedText:
        """处理文本"""
        try:
            self.logger.info(f"开始处理文本，长度: {len(text)}")
            
            processed_text = self.text_service.process_text(text)
            
            self.logger.info(f"文本处理完成，章节数: {len(processed_text.chapters)}, 分段数: {len(processed_text.segments)}")
            return processed_text
            
        except Exception as e:
            self.logger.error(f"文本处理失败: {e}")
            raise TextProcessingError(f"文本处理失败: {e}")
    
    def split_text_by_length(self, text: str, max_length: int) -> List[str]:
        """按长度分割文本"""
        try:
            self.logger.info(f"按长度分割文本，最大长度: {max_length}")
            
            segments = self.text_service.split_by_length(text, max_length)
            
            self.logger.info(f"文本分割完成，分段数: {len(segments)}")
            return segments
            
        except Exception as e:
            self.logger.error(f"按长度分割文本失败: {e}")
            raise TextProcessingError(f"按长度分割文本失败: {e}")
    
    def split_text_by_chapters(self, text: str) -> List[Chapter]:
        """按章节分割文本"""
        try:
            self.logger.info("按章节分割文本")
            
            chapters = self.text_service.detect_chapters(text)
            
            self.logger.info(f"章节分割完成，章节数: {len(chapters)}")
            return chapters
            
        except Exception as e:
            self.logger.error(f"按章节分割文本失败: {e}")
            raise TextProcessingError(f"按章节分割文本失败: {e}")
    
    def clean_text(self, text: str) -> str:
        """清理文本"""
        try:
            return self.text_service.clean_text(text)
        except Exception as e:
            self.logger.error(f"文本清理失败: {e}")
            return text
    
    def detect_chapters(self, text: str) -> List[Chapter]:
        """检测章节"""
        try:
            return self.text_service.detect_chapters(text)
        except Exception as e:
            self.logger.error(f"章节检测失败: {e}")
            return []
    
    def get_text_statistics(self, text: str) -> dict:
        """获取文本统计信息"""
        try:
            return self.text_service.get_text_statistics(text)
        except Exception as e:
            self.logger.error(f"获取文本统计信息失败: {e}")
            return {}
    
    def split_text_by_paragraphs(self, text: str) -> List[str]:
        """按段落分割文本"""
        try:
            self.logger.info("按段落分割文本")
            
            segments = self.text_service.split_by_paragraphs(text)
            
            self.logger.info(f"段落分割完成，分段数: {len(segments)}")
            return segments
            
        except Exception as e:
            self.logger.error(f"按段落分割文本失败: {e}")
            raise TextProcessingError(f"按段落分割文本失败: {e}")
    
    def split_text(self, text: str, split_type: str, **kwargs) -> List[str]:
        """分割文本"""
        try:
            self.logger.info(f"分割文本，类型: {split_type}")
            
            segments = self.text_service.split_text(text, split_type, **kwargs)
            
            self.logger.info(f"文本分割完成，分段数: {len(segments)}")
            return segments
            
        except Exception as e:
            self.logger.error(f"文本分割失败: {e}")
            raise TextProcessingError(f"文本分割失败: {e}")
    
    def get_chapter_text(self, text: str, chapter_index: int) -> str:
        """获取指定章节的文本"""
        try:
            chapters = self.detect_chapters(text)
            
            if chapter_index < 0 or chapter_index >= len(chapters):
                return ""
            
            chapter = chapters[chapter_index]
            return text[chapter.start_pos:chapter.end_pos]
            
        except Exception as e:
            self.logger.error(f"获取章节文本失败: {e}")
            return ""
    
    def get_text_preview(self, text: str, max_length: int = 500) -> str:
        """获取文本预览"""
        try:
            if not text:
                return ""
            
            if len(text) <= max_length:
                return text
            
            # 在句号处截断
            preview = text[:max_length]
            last_period = preview.rfind('。')
            if last_period > max_length // 2:
                preview = preview[:last_period + 1]
            else:
                preview = preview + "..."
            
            return preview
            
        except Exception as e:
            self.logger.error(f"获取文本预览失败: {e}")
            return text[:max_length] if text else ""
    
    def validate_text(self, text: str) -> dict:
        """验证文本"""
        try:
            result = {
                'valid': True,
                'length': len(text) if text else 0,
                'word_count': len(text.split()) if text else 0,
                'line_count': len(text.split('\n')) if text else 0,
                'issues': []
            }
            
            if not text:
                result['valid'] = False
                result['issues'].append("文本为空")
                return result
            
            if len(text) < 10:
                result['issues'].append("文本过短")
            
            if len(text) > 1000000:  # 100万字符
                result['valid'] = False
                result['issues'].append("文本过长")
            
            # 检查是否包含有效内容
            if not text.strip():
                result['valid'] = False
                result['issues'].append("文本只包含空白字符")
            
            return result
            
        except Exception as e:
            self.logger.error(f"文本验证失败: {e}")
            return {
                'valid': False,
                'length': 0,
                'word_count': 0,
                'line_count': 0,
                'issues': [f"验证失败: {e}"]
            }
    
    def optimize_text_for_tts(self, text: str) -> str:
        """优化文本用于TTS"""
        try:
            if not text:
                return ""
            
            # 清理文本
            optimized_text = self.clean_text(text)
            
            # 移除多余的标点符号
            import re
            optimized_text = re.sub(r'[。！？]{2,}', '。', optimized_text)
            
            # 确保句子以标点符号结尾
            if optimized_text and optimized_text[-1] not in '。！？':
                optimized_text += '。'
            
            # 移除过短的句子
            sentences = optimized_text.split('。')
            valid_sentences = [s.strip() for s in sentences if len(s.strip()) > 3]
            optimized_text = '。'.join(valid_sentences)
            
            return optimized_text
            
        except Exception as e:
            self.logger.error(f"文本TTS优化失败: {e}")
            return text
    
    def get_reading_estimate(self, text: str) -> dict:
        """获取阅读估算"""
        try:
            if not text:
                return {
                    'reading_time_minutes': 0,
                    'speech_time_minutes': 0,
                    'word_count': 0,
                    'character_count': 0
                }
            
            word_count = len(text.split())
            char_count = len(text)
            
            # 假设阅读速度：每分钟200字
            reading_time = word_count / 200
            
            # 假设语音速度：每分钟150字
            speech_time = word_count / 150
            
            return {
                'reading_time_minutes': round(reading_time, 2),
                'speech_time_minutes': round(speech_time, 2),
                'word_count': word_count,
                'character_count': char_count
            }
            
        except Exception as e:
            self.logger.error(f"获取阅读估算失败: {e}")
            return {
                'reading_time_minutes': 0,
                'speech_time_minutes': 0,
                'word_count': 0,
                'character_count': 0
            }
