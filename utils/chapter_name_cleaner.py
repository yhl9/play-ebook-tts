#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
章节名称清理工具

提供强大的章节名称清理功能，确保生成的章节名称可以作为有效的文件路径。
处理各种特殊字符、乱码、非法文件名字符等问题。

作者: TTS开发团队
版本: 1.0.0
创建时间: 2024
"""

import re
import unicodedata
from typing import Optional, Dict, List
from utils.log_manager import LogManager


class ChapterNameCleaner:
    """章节名称清理器"""
    
    def __init__(self):
        self.logger = LogManager().get_logger("ChapterNameCleaner")
        
        # Windows系统非法字符
        self.windows_invalid_chars = r'[<>:"/\\|?*]'
        
        # 其他系统可能不支持的字符
        self.other_invalid_chars = r'[\x00-\x1f\x7f-\x9f]'
        
        # 控制字符和不可见字符
        self.control_chars = r'[\x00-\x08\x0b\x0c\x0e-\x1f\x7f-\x9f]'
        
        # 常见的乱码模式
        self.garbled_patterns = [
            r'[\ufffd]+',  # Unicode替换字符
            r'[^\x00-\x7f\u4e00-\u9fff\u3000-\u303f\uff00-\uffef]+',  # 非ASCII、非中文、非全角字符
        ]
        
        # 需要替换的特殊字符映射
        self.char_replacements = {
            # 引号类
            '"': '"',  # 左双引号
            '"': '"',  # 右双引号
            ''': "'",  # 左单引号
            ''': "'",  # 右单引号
            '`': "'",  # 反引号
            
            # 破折号类
            '—': '-',  # em dash
            '–': '-',  # en dash
            '―': '-',  # horizontal bar
            
            # 省略号
            '…': '...',
            
            # 其他符号
            '·': '.',  # 中点
            '•': '.',  # 项目符号
            '※': '*',  # 参考符号
            '★': '*',  # 星号
            '☆': '*',  # 空心星
            '◆': '*',  # 菱形
            '◇': '*',  # 空心菱形
            '■': '*',  # 实心方块
            '□': '*',  # 空心方块
            '▲': '*',  # 实心三角
            '△': '*',  # 空心三角
            '●': '*',  # 实心圆
            '○': '*',  # 空心圆
            
            # 数学符号
            '×': 'x',  # 乘号
            '÷': '/',  # 除号
            '±': '+/-',  # 正负号
            '≤': '<=',  # 小于等于
            '≥': '>=',  # 大于等于
            '≠': '!=',  # 不等于
            '≈': '~',  # 约等于
            
            # 货币符号
            '¥': 'Y',  # 人民币
            '$': 'D',  # 美元
            '€': 'E',  # 欧元
            '£': 'L',  # 英镑
            
            # 版权符号
            '©': '(c)',  # 版权
            '®': '(R)',  # 注册商标
            '™': '(TM)',  # 商标
        }
        
        # 需要移除的字符
        self.chars_to_remove = [
            '\ufeff',  # BOM
            '\u200b',  # 零宽空格
            '\u200c',  # 零宽非连字符
            '\u200d',  # 零宽连字符
            '\u2060',  # 词连接符
            '\ufeff',  # 字节顺序标记
        ]
    
    def clean_chapter_name(self, name: str, max_length: int = 50) -> str:
        """
        清理章节名称，确保可以作为有效的文件路径
        
        Args:
            name (str): 原始章节名称
            max_length (int): 最大长度限制
            
        Returns:
            str: 清理后的章节名称
        """
        if not name or not isinstance(name, str):
            return "untitled"
        
        try:
            # 记录原始名称用于日志
            original_name = name
            
            # 1. 移除BOM和零宽字符
            name = self._remove_invisible_chars(name)
            
            # 2. 处理乱码
            name = self._fix_garbled_text(name)
            
            # 3. 标准化Unicode字符
            name = self._normalize_unicode(name)
            
            # 4. 替换特殊字符
            name = self._replace_special_chars(name)
            
            # 5. 移除或替换非法文件名字符
            name = self._remove_invalid_filename_chars(name)
            
            # 6. 清理多余的空格和标点
            name = self._clean_spaces_and_punctuation(name)
            
            # 7. 限制长度
            name = self._limit_length(name, max_length)
            
            # 8. 最终验证
            name = self._final_validation(name)
            
            # 记录清理结果
            if name != original_name:
                self.logger.info(f"章节名称清理: '{original_name}' -> '{name}'")
            
            return name
            
        except Exception as e:
            self.logger.error(f"清理章节名称失败: {e}")
            return f"chapter_{hash(name) % 10000:04d}"
    
    def _remove_invisible_chars(self, text: str) -> str:
        """移除不可见字符"""
        for char in self.chars_to_remove:
            text = text.replace(char, '')
        
        # 移除控制字符
        text = re.sub(self.control_chars, '', text)
        
        return text
    
    def _fix_garbled_text(self, text: str) -> str:
        """修复乱码文本"""
        # 移除Unicode替换字符
        text = re.sub(r'[\ufffd]+', '', text)
        
        # 尝试修复常见的编码问题
        try:
            # 如果包含大量非ASCII字符，可能是编码问题
            non_ascii_ratio = len([c for c in text if ord(c) > 127]) / len(text) if text else 0
            if non_ascii_ratio > 0.8:
                # 尝试重新编码
                text_bytes = text.encode('utf-8', errors='ignore')
                text = text_bytes.decode('utf-8', errors='ignore')
        except:
            pass
        
        return text
    
    def _normalize_unicode(self, text: str) -> str:
        """标准化Unicode字符"""
        try:
            # 使用NFKC标准化，将兼容字符转换为规范形式
            text = unicodedata.normalize('NFKC', text)
        except:
            pass
        
        return text
    
    def _replace_special_chars(self, text: str) -> str:
        """替换特殊字符"""
        for old_char, new_char in self.char_replacements.items():
            text = text.replace(old_char, new_char)
        
        return text
    
    def _remove_invalid_filename_chars(self, text: str) -> str:
        """移除或替换非法文件名字符"""
        # Windows非法字符
        text = re.sub(self.windows_invalid_chars, '_', text)
        
        # 其他系统非法字符
        text = re.sub(self.other_invalid_chars, '_', text)
        
        # 移除或替换其他可能有问题的字符
        text = re.sub(r'[^\w\s\u4e00-\u9fff\-_\.]', '_', text)
        
        return text
    
    def _clean_spaces_and_punctuation(self, text: str) -> str:
        """清理多余的空格和标点"""
        # 移除首尾空格
        text = text.strip()
        
        # 将多个连续空格替换为单个空格
        text = re.sub(r'\s+', ' ', text)
        
        # 将多个连续下划线替换为单个下划线
        text = re.sub(r'_+', '_', text)
        
        # 移除首尾的下划线和点
        text = text.strip('_.')
        
        return text
    
    def _limit_length(self, text: str, max_length: int) -> str:
        """限制文本长度"""
        if len(text) <= max_length:
            return text
        
        # 如果超长，尝试在合适的位置截断
        if max_length > 10:
            # 保留前80%和后20%的字符
            keep_start = int(max_length * 0.8)
            keep_end = max_length - keep_start
            text = text[:keep_start] + text[-keep_end:]
        
        return text[:max_length]
    
    def _final_validation(self, text: str) -> str:
        """最终验证和清理"""
        # 确保不为空
        if not text or not text.strip():
            return "untitled"
        
        # 确保不以点开头（隐藏文件）
        if text.startswith('.'):
            text = 'chapter_' + text
        
        # 确保不以空格开头或结尾
        text = text.strip()
        
        # 如果清理后为空，返回默认名称
        if not text:
            return "untitled"
        
        return text
    
    def is_valid_filename(self, filename: str) -> bool:
        """
        检查文件名是否有效
        
        Args:
            filename (str): 要检查的文件名
            
        Returns:
            bool: 是否为有效的文件名
        """
        if not filename or not filename.strip():
            return False
        
        # 检查是否包含非法字符
        if re.search(self.windows_invalid_chars, filename):
            return False
        
        if re.search(self.other_invalid_chars, filename):
            return False
        
        # 检查是否为保留名称（Windows）
        reserved_names = {
            'CON', 'PRN', 'AUX', 'NUL',
            'COM1', 'COM2', 'COM3', 'COM4', 'COM5', 'COM6', 'COM7', 'COM8', 'COM9',
            'LPT1', 'LPT2', 'LPT3', 'LPT4', 'LPT5', 'LPT6', 'LPT7', 'LPT8', 'LPT9'
        }
        
        name_without_ext = filename.split('.')[0].upper()
        if name_without_ext in reserved_names:
            return False
        
        return True
    
    def get_safe_filename(self, filename: str, max_length: int = 50) -> str:
        """
        获取安全的文件名
        
        Args:
            filename (str): 原始文件名
            max_length (int): 最大长度
            
        Returns:
            str: 安全的文件名
        """
        # 分离文件名和扩展名
        if '.' in filename:
            name_part, ext_part = filename.rsplit('.', 1)
            cleaned_name = self.clean_chapter_name(name_part, max_length - len(ext_part) - 1)
            return f"{cleaned_name}.{ext_part}"
        else:
            return self.clean_chapter_name(filename, max_length)


# 全局实例
chapter_name_cleaner = ChapterNameCleaner()


def clean_chapter_name(name: str, max_length: int = 50) -> str:
    """
    清理章节名称的便捷函数
    
    Args:
        name (str): 原始章节名称
        max_length (int): 最大长度限制
        
    Returns:
        str: 清理后的章节名称
    """
    return chapter_name_cleaner.clean_chapter_name(name, max_length)


def is_valid_filename(filename: str) -> bool:
    """
    检查文件名是否有效的便捷函数
    
    Args:
        filename (str): 要检查的文件名
        
    Returns:
        bool: 是否为有效的文件名
    """
    return chapter_name_cleaner.is_valid_filename(filename)


def get_safe_filename(filename: str, max_length: int = 50) -> str:
    """
    获取安全文件名的便捷函数
    
    Args:
        filename (str): 原始文件名
        max_length (int): 最大长度
        
    Returns:
        str: 安全的文件名
    """
    return chapter_name_cleaner.get_safe_filename(filename, max_length)
