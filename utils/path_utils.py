"""
路径工具模块
提供路径处理相关的工具函数
"""

import os
from pathlib import Path
from typing import Union


def normalize_path(path: Union[str, Path]) -> str:
    """
    标准化路径，将相对路径转换为绝对路径，并使用"/"分隔符
    
    Args:
        path: 输入路径
        
    Returns:
        str: 标准化后的绝对路径，使用"/"分隔符
    """
    try:
        if isinstance(path, str):
            path = Path(path)
        
        # 如果是相对路径，转换为绝对路径
        if not path.is_absolute():
            path = path.resolve()
        
        # 转换为字符串并使用"/"分隔符
        normalized_path = str(path).replace('\\', '/')
        return normalized_path
        
    except Exception as e:
        # 如果转换失败，返回原始路径并标准化分隔符
        return str(path).replace('\\', '/')


def ensure_directory_exists(path: Union[str, Path]) -> str:
    """
    确保目录存在，如果不存在则创建
    
    Args:
        path: 目录路径
        
    Returns:
        str: 标准化后的绝对路径，使用"/"分隔符
    """
    try:
        normalized_path = normalize_path(path)
        # 创建目录时使用原始路径对象
        Path(path).mkdir(parents=True, exist_ok=True)
        return normalized_path
        
    except Exception as e:
        # 如果创建失败，返回原始路径并标准化分隔符
        return str(path).replace('\\', '/')


def is_relative_path(path: Union[str, Path]) -> bool:
    """
    检查路径是否为相对路径
    
    Args:
        path: 输入路径
        
    Returns:
        bool: 如果是相对路径返回True，否则返回False
    """
    try:
        if isinstance(path, str):
            path = Path(path)
        return not path.is_absolute()
        
    except Exception:
        return True  # 如果无法判断，假设为相对路径


def get_relative_path(base_path: Union[str, Path], target_path: Union[str, Path]) -> str:
    """
    获取相对于基础路径的相对路径
    
    Args:
        base_path: 基础路径
        target_path: 目标路径
        
    Returns:
        str: 相对路径
    """
    try:
        base = Path(base_path).resolve()
        target = Path(target_path).resolve()
        return str(target.relative_to(base))
        
    except Exception:
        return str(target_path)
