"""
Markdown文件解析服务
"""

import re
from typing import List, Dict, Any, Optional
from dataclasses import dataclass

from utils.log_manager import LogManager


@dataclass
class MarkdownSection:
    """Markdown章节"""
    title: str
    content: str
    level: int
    line_number: int


class MarkdownParser:
    """Markdown解析器"""
    
    def __init__(self):
        self.logger = LogManager().get_logger("MarkdownParser")
    
    def parse_markdown(self, content: str) -> List[MarkdownSection]:
        """解析Markdown内容"""
        try:
            sections = []
            lines = content.split('\n')
            current_section = None
            current_content = []
            
            for i, line in enumerate(lines):
                # 检查是否是标题行
                header_match = re.match(r'^(#{1,6})\s+(.+)$', line.strip())
                
                if header_match:
                    # 保存之前的章节
                    if current_section and current_content:
                        current_section.content = '\n'.join(current_content).strip()
                        sections.append(current_section)
                    
                    # 开始新章节
                    level = len(header_match.group(1))
                    title = header_match.group(2).strip()
                    current_section = MarkdownSection(
                        title=title,
                        content="",
                        level=level,
                        line_number=i + 1
                    )
                    current_content = []
                else:
                    # 添加到当前章节内容
                    if current_section:
                        current_content.append(line)
                    else:
                        # 如果没有标题，创建默认章节
                        if not current_section and line.strip():
                            current_section = MarkdownSection(
                                title="未命名章节",
                                content="",
                                level=1,
                                line_number=1
                            )
                        if current_section:
                            current_content.append(line)
            
            # 保存最后一个章节
            if current_section and current_content:
                current_section.content = '\n'.join(current_content).strip()
                sections.append(current_section)
            
            # 如果没有找到任何章节，创建默认章节
            if not sections and content.strip():
                sections.append(MarkdownSection(
                    title="文档内容",
                    content=content.strip(),
                    level=1,
                    line_number=1
                ))
            
            self.logger.info(f"解析Markdown完成，共 {len(sections)} 个章节")
            return sections
            
        except Exception as e:
            self.logger.error(f"解析Markdown失败: {e}")
            return []
    
    def extract_text_from_markdown(self, content: str) -> str:
        """从Markdown中提取纯文本"""
        try:
            # 移除代码块
            content = re.sub(r'```[\s\S]*?```', '', content)
            content = re.sub(r'`[^`]+`', '', content)
            
            # 移除链接，保留文本
            content = re.sub(r'\[([^\]]+)\]\([^\)]+\)', r'\1', content)
            
            # 移除图片
            content = re.sub(r'!\[([^\]]*)\]\([^\)]+\)', r'\1', content)
            
            # 移除标题标记
            content = re.sub(r'^#{1,6}\s+', '', content, flags=re.MULTILINE)
            
            # 移除粗体和斜体标记
            content = re.sub(r'\*\*([^*]+)\*\*', r'\1', content)
            content = re.sub(r'\*([^*]+)\*', r'\1', content)
            content = re.sub(r'__([^_]+)__', r'\1', content)
            content = re.sub(r'_([^_]+)_', r'\1', content)
            
            # 移除删除线
            content = re.sub(r'~~([^~]+)~~', r'\1', content)
            
            # 移除引用标记
            content = re.sub(r'^>\s*', '', content, flags=re.MULTILINE)
            
            # 移除列表标记
            content = re.sub(r'^[\s]*[-*+]\s+', '', content, flags=re.MULTILINE)
            content = re.sub(r'^[\s]*\d+\.\s+', '', content, flags=re.MULTILINE)
            
            # 移除水平线
            content = re.sub(r'^[-*_]{3,}$', '', content, flags=re.MULTILINE)
            
            # 清理多余的空行
            content = re.sub(r'\n\s*\n\s*\n', '\n\n', content)
            
            return content.strip()
            
        except Exception as e:
            self.logger.error(f"提取Markdown文本失败: {e}")
            return content
    
    def get_markdown_toc(self, sections: List[MarkdownSection]) -> str:
        """生成Markdown目录"""
        try:
            toc_lines = ["# 目录\n"]
            
            for section in sections:
                indent = "  " * (section.level - 1)
                toc_lines.append(f"{indent}- {section.title}")
            
            return '\n'.join(toc_lines)
            
        except Exception as e:
            self.logger.error(f"生成目录失败: {e}")
            return ""
    
    def validate_markdown(self, content: str) -> Dict[str, Any]:
        """验证Markdown内容"""
        try:
            sections = self.parse_markdown(content)
            
            # 统计信息
            total_chars = len(content)
            total_lines = len(content.split('\n'))
            section_count = len(sections)
            
            # 检查是否有标题
            has_headers = any(section.level > 0 for section in sections)
            
            # 检查标题层级
            levels = [section.level for section in sections if section.level > 0]
            max_level = max(levels) if levels else 0
            min_level = min(levels) if levels else 0
            
            return {
                "valid": True,
                "total_chars": total_chars,
                "total_lines": total_lines,
                "section_count": section_count,
                "has_headers": has_headers,
                "max_level": max_level,
                "min_level": min_level,
                "sections": [
                    {
                        "title": section.title,
                        "level": section.level,
                        "content_length": len(section.content),
                        "line_number": section.line_number
                    }
                    for section in sections
                ]
            }
            
        except Exception as e:
            self.logger.error(f"验证Markdown失败: {e}")
            return {
                "valid": False,
                "error": str(e),
                "total_chars": 0,
                "total_lines": 0,
                "section_count": 0,
                "has_headers": False,
                "max_level": 0,
                "min_level": 0,
                "sections": []
            }
