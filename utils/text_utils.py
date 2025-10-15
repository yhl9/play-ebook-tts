"""
文本工具类
"""

import re
from typing import List, Optional, Tuple
from utils.log_manager import LogManager


class TextUtils:
    """文本工具类"""
    
    def __init__(self):
        self.logger = LogManager().get_logger("TextUtils")
    
    @staticmethod
    def clean_text(text: str) -> str:
        """清理文本"""
        if not text:
            return ""
        
        # 移除多余空格
        text = re.sub(r'\s+', ' ', text)
        
        # 移除特殊字符（保留中文、英文、数字、标点符号）
        text = re.sub(r'[^\w\s\u4e00-\u9fff.,!?;:()（）【】《》""''""''\n\r]', '', text)
        
        # 移除多余的换行符
        text = re.sub(r'\n\s*\n', '\n\n', text)
        
        return text.strip()
    
    @staticmethod
    def count_words(text: str) -> int:
        """统计单词数"""
        if not text:
            return 0
        return len(text.split())
    
    @staticmethod
    def count_characters(text: str) -> int:
        """统计字符数"""
        return len(text) if text else 0
    
    @staticmethod
    def count_lines(text: str) -> int:
        """统计行数"""
        if not text:
            return 0
        return len(text.split('\n'))
    
    @staticmethod
    def count_paragraphs(text: str) -> int:
        """统计段落数"""
        if not text:
            return 0
        paragraphs = [p for p in text.split('\n\n') if p.strip()]
        return len(paragraphs)
    
    @staticmethod
    def get_text_statistics(text: str) -> dict:
        """获取文本统计信息"""
        return {
            'characters': TextUtils.count_characters(text),
            'words': TextUtils.count_words(text),
            'lines': TextUtils.count_lines(text),
            'paragraphs': TextUtils.count_paragraphs(text)
        }
    
    @staticmethod
    def extract_sentences(text: str) -> List[str]:
        """提取句子"""
        if not text:
            return []
        
        # 按句号、问号、感叹号分割
        sentences = re.split(r'[。！？]', text)
        return [s.strip() for s in sentences if s.strip()]
    
    @staticmethod
    def extract_paragraphs(text: str) -> List[str]:
        """提取段落"""
        if not text:
            return []
        
        paragraphs = text.split('\n\n')
        return [p.strip() for p in paragraphs if p.strip()]
    
    @staticmethod
    def find_chapter_titles(text: str) -> List[Tuple[str, int]]:
        """查找章节标题"""
        if not text:
            return []
        
        chapter_patterns = [
            r'第[一二三四五六七八九十\d]+章[：:\s]*.*',
            r'Chapter\s+\d+[：:\s]*.*',
            r'第[一二三四五六七八九十\d]+节[：:\s]*.*',
            r'Section\s+\d+[：:\s]*.*'
        ]
        
        titles = []
        lines = text.split('\n')
        
        for i, line in enumerate(lines):
            line = line.strip()
            if not line:
                continue
            
            for pattern in chapter_patterns:
                if re.match(pattern, line, re.IGNORECASE):
                    titles.append((line, i))
                    break
        
        return titles
    
    @staticmethod
    def split_text_by_length(text: str, max_length: int) -> List[str]:
        """按长度分割文本"""
        if not text or max_length <= 0:
            return [text] if text else []
        
        segments = []
        current_pos = 0
        
        while current_pos < len(text):
            end_pos = min(current_pos + max_length, len(text))
            
            # 如果不是最后一段，尝试在句号处分割
            if end_pos < len(text):
                for i in range(end_pos, max(current_pos, end_pos - 200), -1):
                    if text[i] in '。！？':
                        end_pos = i + 1
                        break
            
            segment = text[current_pos:end_pos].strip()
            if segment:
                segments.append(segment)
            
            current_pos = end_pos
        
        return segments
    
    @staticmethod
    def split_text_by_sentences(text: str, max_sentences: int) -> List[str]:
        """按句子数分割文本"""
        if not text or max_sentences <= 0:
            return [text] if text else []
        
        sentences = TextUtils.extract_sentences(text)
        segments = []
        
        for i in range(0, len(sentences), max_sentences):
            segment = '。'.join(sentences[i:i + max_sentences])
            if segment:
                segments.append(segment)
        
        return segments
    
    @staticmethod
    def remove_extra_spaces(text: str) -> str:
        """移除多余空格"""
        if not text:
            return ""
        
        # 移除多余空格
        text = re.sub(r' +', ' ', text)
        
        # 移除行首行尾空格
        lines = text.split('\n')
        lines = [line.strip() for line in lines]
        
        return '\n'.join(lines)
    
    @staticmethod
    def remove_empty_lines(text: str) -> str:
        """移除空行"""
        if not text:
            return ""
        
        lines = text.split('\n')
        lines = [line for line in lines if line.strip()]
        
        return '\n'.join(lines)
    
    @staticmethod
    def normalize_whitespace(text: str) -> str:
        """标准化空白字符"""
        if not text:
            return ""
        
        # 将所有空白字符替换为单个空格
        text = re.sub(r'\s+', ' ', text)
        
        # 移除首尾空格
        text = text.strip()
        
        return text
    
    @staticmethod
    def extract_keywords(text: str, min_length: int = 2) -> List[str]:
        """提取关键词"""
        if not text:
            return []
        
        # 简单的关键词提取（基于词频）
        words = re.findall(r'\b\w+\b', text.lower())
        
        # 过滤短词和常见停用词
        stop_words = {'的', '了', '在', '是', '我', '有', '和', '就', '不', '人', '都', '一', '一个', '上', '也', '很', '到', '说', '要', '去', '你', '会', '着', '没有', '看', '好', '自己', '这'}
        
        word_freq = {}
        for word in words:
            if len(word) >= min_length and word not in stop_words:
                word_freq[word] = word_freq.get(word, 0) + 1
        
        # 按频率排序
        keywords = sorted(word_freq.items(), key=lambda x: x[1], reverse=True)
        
        return [word for word, freq in keywords[:20]]  # 返回前20个关键词
    
    @staticmethod
    def detect_language(text: str) -> str:
        """检测语言"""
        if not text:
            return 'unknown'
        
        # 简单的语言检测
        chinese_chars = len(re.findall(r'[\u4e00-\u9fff]', text))
        english_chars = len(re.findall(r'[a-zA-Z]', text))
        total_chars = len(text)
        
        if total_chars == 0:
            return 'unknown'
        
        chinese_ratio = chinese_chars / total_chars
        english_ratio = english_chars / total_chars
        
        if chinese_ratio > 0.3:
            return 'zh-CN'
        elif english_ratio > 0.3:
            return 'en-US'
        else:
            return 'unknown'
    
    @staticmethod
    def format_text_for_tts(text: str) -> str:
        """格式化文本用于TTS"""
        if not text:
            return ""
        
        # 清理文本
        text = TextUtils.clean_text(text)
        
        # 移除多余的标点符号
        text = re.sub(r'[。！？]{2,}', '。', text)
        
        # 确保句子以标点符号结尾
        if text and text[-1] not in '。！？':
            text += '。'
        
        return text
    
    @staticmethod
    def estimate_reading_time(text: str, words_per_minute: int = 200) -> float:
        """估算阅读时间（分钟）"""
        if not text:
            return 0.0
        
        word_count = TextUtils.count_words(text)
        return word_count / words_per_minute
    
    @staticmethod
    def estimate_speech_time(text: str, words_per_minute: int = 150) -> float:
        """估算语音时间（分钟）"""
        if not text:
            return 0.0
        
        word_count = TextUtils.count_words(text)
        return word_count / words_per_minute
