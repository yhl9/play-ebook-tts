#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
字幕工具类
支持多种字幕格式的生成和转换
"""

import re
from typing import List, Dict, Any, Optional, Tuple
from dataclasses import dataclass


@dataclass
class SubtitleEntry:
    """字幕条目"""
    start_time: float  # 开始时间（秒）
    end_time: float    # 结束时间（秒）
    text: str          # 字幕文本
    index: int = 0     # 序号（SRT格式需要）


class SubtitleConverter:
    """字幕格式转换器"""
    
    @staticmethod
    def format_time_lrc(seconds: float) -> str:
        """格式化为LRC时间格式 [mm:ss.xx]"""
        minutes = int(seconds // 60)
        secs = seconds % 60
        return f"[{minutes:02d}:{secs:05.2f}]"
    
    @staticmethod
    def format_time_srt(seconds: float) -> str:
        """格式化为SRT时间格式 HH:MM:SS,mmm"""
        hours = int(seconds // 3600)
        minutes = int((seconds % 3600) // 60)
        secs = seconds % 60
        return f"{hours:02d}:{minutes:02d}:{secs:06.3f}".replace('.', ',')
    
    @staticmethod
    def format_time_vtt(seconds: float) -> str:
        """格式化为VTT时间格式 HH:MM:SS.mmm"""
        hours = int(seconds // 3600)
        minutes = int((seconds % 3600) // 60)
        secs = seconds % 60
        return f"{hours:02d}:{minutes:02d}:{secs:06.3f}"
    
    @staticmethod
    def format_time_ass(seconds: float) -> str:
        """格式化为ASS时间格式 H:MM:SS.xx"""
        hours = int(seconds // 3600)
        minutes = int((seconds % 3600) // 60)
        secs = seconds % 60
        return f"{hours}:{minutes:02d}:{secs:05.2f}"
    
    @classmethod
    def convert_srt_to_lrc(cls, srt_content: str, offset: float = 0.0) -> str:
        """将SRT格式转换为LRC格式"""
        if not srt_content.strip():
            return ""
        
        lines = srt_content.strip().split('\n')
        lrc_lines = []
        
        i = 0
        while i < len(lines):
            line = lines[i].strip()
            
            # 跳过空行和序号行
            if not line or line.isdigit():
                i += 1
                continue
            
            # 解析时间行
            if '-->' in line:
                try:
                    start_str, end_str = line.split(' --> ')
                    start_time = cls._parse_srt_time(start_str) + offset
                    end_time = cls._parse_srt_time(end_str) + offset
                    
                    # 获取文本行
                    text_lines = []
                    i += 1
                    while i < len(lines) and lines[i].strip():
                        text_lines.append(lines[i].strip())
                        i += 1
                    
                    if text_lines:
                        text = ' '.join(text_lines)
                        lrc_line = f"{cls.format_time_lrc(start_time)}{text}"
                        lrc_lines.append(lrc_line)
                
                except Exception as e:
                    print(f"解析SRT时间行失败: {line}, 错误: {e}")
            
            i += 1
        
        return '\n'.join(lrc_lines)
    
    @classmethod
    def convert_srt_to_vtt(cls, srt_content: str, offset: float = 0.0) -> str:
        """将SRT格式转换为VTT格式"""
        if not srt_content.strip():
            return "WEBVTT\n\n"
        
        lines = srt_content.strip().split('\n')
        vtt_lines = ["WEBVTT", ""]
        
        i = 0
        while i < len(lines):
            line = lines[i].strip()
            
            # 跳过空行和序号行
            if not line or line.isdigit():
                i += 1
                continue
            
            # 解析时间行
            if '-->' in line:
                try:
                    start_str, end_str = line.split(' --> ')
                    start_time = cls._parse_srt_time(start_str) + offset
                    end_time = cls._parse_srt_time(end_str) + offset
                    
                    # 获取文本行
                    text_lines = []
                    i += 1
                    while i < len(lines) and lines[i].strip():
                        text_lines.append(lines[i].strip())
                        i += 1
                    
                    if text_lines:
                        text = ' '.join(text_lines)
                        time_line = f"{cls.format_time_vtt(start_time)} --> {cls.format_time_vtt(end_time)}"
                        vtt_lines.append(time_line)
                        vtt_lines.append(text)
                        vtt_lines.append("")
                
                except Exception as e:
                    print(f"解析SRT时间行失败: {line}, 错误: {e}")
            
            i += 1
        
        return '\n'.join(vtt_lines)
    
    @classmethod
    def convert_srt_to_ass(cls, srt_content: str, offset: float = 0.0, style: Dict[str, Any] = None) -> str:
        """将SRT格式转换为ASS格式"""
        if not srt_content.strip():
            return ""
        
        # 默认样式
        default_style = {
            'name': 'Default',
            'fontname': 'Arial',
            'fontsize': 20,
            'primarycolor': '&H00FFFFFF',
            'secondarycolor': '&H000000FF',
            'outlinecolor': '&H00000000',
            'backcolor': '&H80000000',
            'bold': 0,
            'italic': 0,
            'underline': 0,
            'strikeout': 0,
            'scale_x': 100,
            'scale_y': 100,
            'spacing': 0,
            'angle': 0,
            'borderstyle': 1,
            'outline': 2,
            'shadow': 2,
            'alignment': 2,
            'margin_l': 10,
            'margin_r': 10,
            'margin_v': 10,
            'encoding': 1
        }
        
        if style:
            default_style.update(style)
        
        lines = srt_content.strip().split('\n')
        ass_lines = [
            "[Script Info]",
            "Title: Generated Subtitle",
            "ScriptType: v4.00+",
            "",
            "[V4+ Styles]",
            "Format: Name, Fontname, Fontsize, PrimaryColour, SecondaryColour, OutlineColour, BackColour, Bold, Italic, Underline, StrikeOut, ScaleX, ScaleY, Spacing, Angle, BorderStyle, Outline, Shadow, Alignment, MarginL, MarginR, MarginV, Encoding",
            f"Style: {default_style['name']},{default_style['fontname']},{default_style['fontsize']},{default_style['primarycolor']},{default_style['secondarycolor']},{default_style['outlinecolor']},{default_style['backcolor']},{default_style['bold']},{default_style['italic']},{default_style['underline']},{default_style['strikeout']},{default_style['scale_x']},{default_style['scale_y']},{default_style['spacing']},{default_style['angle']},{default_style['borderstyle']},{default_style['outline']},{default_style['shadow']},{default_style['alignment']},{default_style['margin_l']},{default_style['margin_r']},{default_style['margin_v']},{default_style['encoding']}",
            "",
            "[Events]",
            "Format: Layer, Start, End, Style, Name, MarginL, MarginR, MarginV, Effect, Text"
        ]
        
        i = 0
        while i < len(lines):
            line = lines[i].strip()
            
            # 跳过空行和序号行
            if not line or line.isdigit():
                i += 1
                continue
            
            # 解析时间行
            if '-->' in line:
                try:
                    start_str, end_str = line.split(' --> ')
                    start_time = cls._parse_srt_time(start_str) + offset
                    end_time = cls._parse_srt_time(end_str) + offset
                    
                    # 获取文本行
                    text_lines = []
                    i += 1
                    while i < len(lines) and lines[i].strip():
                        text_lines.append(lines[i].strip())
                        i += 1
                    
                    if text_lines:
                        text = ' '.join(text_lines)
                        ass_line = f"Dialogue: 0,{cls.format_time_ass(start_time)},{cls.format_time_ass(end_time)},{default_style['name']},,0,0,0,,{text}"
                        ass_lines.append(ass_line)
                
                except Exception as e:
                    print(f"解析SRT时间行失败: {line}, 错误: {e}")
            
            i += 1
        
        return '\n'.join(ass_lines)
    
    @staticmethod
    def _parse_srt_time(time_str: str) -> float:
        """解析SRT时间格式为秒数"""
        # 格式: HH:MM:SS,mmm
        time_str = time_str.replace(',', '.')
        parts = time_str.split(':')
        
        if len(parts) == 3:
            hours = int(parts[0])
            minutes = int(parts[1])
            seconds = float(parts[2])
            return hours * 3600 + minutes * 60 + seconds
        else:
            raise ValueError(f"无效的SRT时间格式: {time_str}")
    
    @classmethod
    def convert_subtitle_format(cls, content: str, from_format: str, to_format: str, 
                               offset: float = 0.0, style: Dict[str, Any] = None) -> str:
        """通用字幕格式转换方法"""
        if not content.strip():
            return ""
        
        # 如果源格式和目标格式相同，直接返回
        if from_format.lower() == to_format.lower():
            return content
        
        # 目前只支持从SRT转换到其他格式
        if from_format.lower() == 'srt':
            if to_format.lower() == 'lrc':
                return cls.convert_srt_to_lrc(content, offset)
            elif to_format.lower() == 'vtt':
                return cls.convert_srt_to_vtt(content, offset)
            elif to_format.lower() in ['ass', 'ssa']:
                return cls.convert_srt_to_ass(content, offset, style)
            else:
                raise ValueError(f"不支持的目标格式: {to_format}")
        else:
            raise ValueError(f"不支持的源格式: {from_format}")


class SubtitleGenerator:
    """字幕生成器"""
    
    def __init__(self, format_type: str = 'lrc', encoding: str = 'utf-8', offset: float = 0.0):
        self.format_type = format_type.lower()
        self.encoding = encoding
        self.offset = offset
        self.converter = SubtitleConverter()
    
    def generate_subtitle_file(self, srt_content: str, output_path: str, style: Dict[str, Any] = None) -> str:
        """生成指定格式的字幕文件"""
        try:
            # 转换格式
            if self.format_type == 'srt':
                content = srt_content
            else:
                content = self.converter.convert_subtitle_format(
                    srt_content, 'srt', self.format_type, self.offset, style
                )
            
            # 确定文件扩展名
            if not output_path.endswith(f'.{self.format_type}'):
                output_path = f"{output_path.rsplit('.', 1)[0]}.{self.format_type}"
            
            # 写入文件
            with open(output_path, 'w', encoding=self.encoding) as f:
                f.write(content)
            
            return output_path
            
        except Exception as e:
            raise Exception(f"生成字幕文件失败: {e}")
    
    def get_subtitle_content(self, srt_content: str, style: Dict[str, Any] = None) -> str:
        """获取指定格式的字幕内容"""
        try:
            if self.format_type == 'srt':
                return srt_content
            else:
                return self.converter.convert_subtitle_format(
                    srt_content, 'srt', self.format_type, self.offset, style
                )
        except Exception as e:
            raise Exception(f"转换字幕格式失败: {e}")


def create_subtitle_generator(voice_config) -> Optional[SubtitleGenerator]:
    """根据语音配置创建字幕生成器"""
    if not getattr(voice_config, 'generate_subtitle', False):
        return None
    
    return SubtitleGenerator(
        format_type=getattr(voice_config, 'subtitle_format', 'lrc'),
        encoding=getattr(voice_config, 'subtitle_encoding', 'utf-8'),
        offset=getattr(voice_config, 'subtitle_offset', 0.0)
    )
