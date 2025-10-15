#!/usr/bin/env python3
"""
文件命名工具
根据输出设置页面的命名规则生成文件名
"""

import re
import os
from typing import Dict, Any, Optional


class FileNamingUtils:
    """文件命名工具类"""
    
    @staticmethod
    def generate_filename(segment: Dict[str, Any], index: int, total: int, 
                         naming_mode: str, custom_template: str = "", 
                         name_length_limit: int = 50, file_extension: str = "wav") -> str:
        """生成文件名
        
        Args:
            segment: 段落数据，包含title、content等
            index: 当前段落索引（从0开始）
            total: 总段落数
            naming_mode: 命名模式
            custom_template: 自定义模板
            name_length_limit: 文件名长度限制
            file_extension: 文件扩展名
            
        Returns:
            生成的文件名（不含扩展名）
        """
        try:
            # 获取段落信息
            title = segment.get('title', f'段落{index+1}') if isinstance(segment, dict) else f'段落{index+1}'
            chapter_num = segment.get('chapter_num', index + 1) if isinstance(segment, dict) else index + 1
            
            # 清理标题，移除非法字符
            clean_title = FileNamingUtils._clean_filename(title)
            
            # 根据命名模式生成文件名
            if naming_mode == "章节序号 + 标题":
                filename = f"{chapter_num:02d}_{clean_title}"
            elif naming_mode == "顺序号 + 标题":
                filename = f"{index+1:03d}_{clean_title}"
            elif naming_mode == "仅标题":
                filename = clean_title
            elif naming_mode == "仅顺序号":
                filename = f"{index+1:03d}"
            elif naming_mode == "原始文件名":
                filename = FileNamingUtils._generate_original_filename(segment, index)
            elif naming_mode == "自定义":
                filename = FileNamingUtils._apply_custom_template(
                    custom_template, chapter_num, clean_title, index + 1
                )
            else:
                # 默认使用章节序号 + 标题
                filename = f"{chapter_num:02d}_{clean_title}"
            
            # 限制文件名长度
            if len(filename) > name_length_limit:
                filename = filename[:name_length_limit]
            
            # 确保文件名不为空
            if not filename.strip():
                filename = f"segment_{index+1:03d}"
            
            return filename
            
        except Exception as e:
            # 如果生成失败，使用默认命名
            return f"segment_{index+1:03d}"
    
    @staticmethod
    def _generate_original_filename(segment: Dict[str, Any], index: int) -> str:
        """生成原始文件名格式的文件名"""
        try:
            # 尝试从段落数据中获取原始文件名
            original_filename = segment.get('original_filename') if isinstance(segment, dict) else None
            if original_filename:
                # 移除文件扩展名
                import os
                name_without_ext = os.path.splitext(original_filename)[0]
                return FileNamingUtils._clean_filename(name_without_ext)
            
            # 如果没有原始文件名，使用标题
            title = segment.get('title', f'段落{index+1}') if isinstance(segment, dict) else f'段落{index+1}'
            return FileNamingUtils._clean_filename(title)
            
        except Exception as e:
            # 如果生成失败，使用默认命名
            return f"original_{index+1:03d}"
    
    @staticmethod
    def _clean_filename(filename: str) -> str:
        """清理文件名，移除非法字符"""
        try:
            # 移除或替换非法字符
            # Windows不允许的字符: < > : " | ? * \ /
            # 也移除一些其他可能有问题的字符
            illegal_chars = r'[<>:"|?*\\/]'
            clean_name = re.sub(illegal_chars, '_', filename)
            
            # 移除多余的空格和点
            clean_name = re.sub(r'\s+', ' ', clean_name)  # 多个空格合并为一个
            clean_name = re.sub(r'\.+', '.', clean_name)  # 多个点合并为一个
            clean_name = clean_name.strip(' .')  # 移除首尾空格和点
            
            # 确保文件名不为空
            if not clean_name:
                clean_name = "unnamed"
            
            return clean_name
            
        except Exception:
            return "unnamed"
    
    @staticmethod
    def _apply_custom_template(template: str, chapter_num: int, title: str, index: int) -> str:
        """应用自定义模板"""
        try:
            if not template:
                return f"{chapter_num:02d}_{title}"
            
            # 替换模板中的占位符
            result = template
            
            # 替换章节号
            result = result.replace('{chapter_num}', str(chapter_num))
            result = result.replace('{chapter_num:02d}', f"{chapter_num:02d}")
            result = result.replace('{chapter_num:03d}', f"{chapter_num:03d}")
            
            # 替换序号
            result = result.replace('{index}', str(index))
            result = result.replace('{index:02d}', f"{index:02d}")
            result = result.replace('{index:03d}', f"{index:03d}")
            
            # 替换标题
            result = result.replace('{title}', title)
            
            # 替换时间戳（如果需要）
            if '{timestamp}' in result:
                from datetime import datetime
                timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
                result = result.replace('{timestamp}', timestamp)
            
            return result
            
        except Exception:
            return f"{chapter_num:02d}_{title}"
    
    @staticmethod
    def get_full_file_path(output_dir: str, filename: str, file_extension: str) -> str:
        """获取完整的文件路径"""
        try:
            # 确保输出目录存在
            os.makedirs(output_dir, exist_ok=True)
            
            # 构建完整路径
            full_filename = f"{filename}.{file_extension}"
            full_path = os.path.join(output_dir, full_filename)
            
            # 如果文件已存在，添加序号
            counter = 1
            original_path = full_path
            while os.path.exists(full_path):
                name_without_ext = os.path.splitext(full_filename)[0]
                full_filename = f"{name_without_ext}_{counter:02d}.{file_extension}"
                full_path = os.path.join(output_dir, full_filename)
                counter += 1
                
                # 防止无限循环
                if counter > 999:
                    break
            
            return full_path
            
        except Exception as e:
            # 如果出错，使用默认路径
            return os.path.join(output_dir, f"segment_{int(time.time())}.{file_extension}")


# 测试函数
def test_file_naming():
    """测试文件命名功能"""
    print("=== 文件命名功能测试 ===")
    
    # 测试数据
    test_segments = [
        {"title": "第一章 开始", "chapter_num": 1, "content": "这是第一章的内容"},
        {"title": "第二章 发展", "chapter_num": 2, "content": "这是第二章的内容"},
        {"title": "第三章 结束", "chapter_num": 3, "content": "这是第三章的内容"},
        "纯文本段落",  # 字符串格式
    ]
    
    naming_modes = [
        "章节序号 + 标题",
        "序号 + 标题", 
        "仅标题",
        "仅序号",
        "自定义"
    ]
    
    for mode in naming_modes:
        print(f"\n命名模式: {mode}")
        for i, segment in enumerate(test_segments):
            if mode == "自定义":
                custom_template = "{chapter_num:02d}_{title}_{timestamp}"
            else:
                custom_template = ""
            
            filename = FileNamingUtils.generate_filename(
                segment, i, len(test_segments), mode, custom_template, 50, "wav"
            )
            print(f"  段落{i+1}: {filename}")

if __name__ == "__main__":
    test_file_naming()
