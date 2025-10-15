"""
备份管理模块

提供配置和状态的备份与恢复功能，支持在修改失败时快速回滚。

作者: TTS开发团队
版本: 1.0.0
创建时间: 2024
"""

import os
import json
import shutil
from datetime import datetime
from pathlib import Path
from typing import Dict, Any, Optional
from utils.log_manager import LogManager


class BackupManager:
    """
    备份管理器
    
    提供配置文件和状态的备份与恢复功能。
    支持自动备份和手动备份，确保在修改失败时能够快速回滚。
    """
    
    def __init__(self, backup_dir: str = "backups"):
        self.logger = LogManager().get_logger("BackupManager")
        self.backup_dir = Path(backup_dir)
        self.backup_dir.mkdir(exist_ok=True)
    
    def create_backup(self, file_path: str, description: str = "") -> str:
        """
        创建文件备份
        
        Args:
            file_path (str): 要备份的文件路径
            description (str): 备份描述
            
        Returns:
            str: 备份文件路径
        """
        try:
            source_path = Path(file_path)
            if not source_path.exists():
                self.logger.warning(f"文件不存在，跳过备份: {file_path}")
                return ""
            
            # 生成备份文件名
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            backup_name = f"{source_path.stem}_{timestamp}.backup"
            if description:
                backup_name = f"{source_path.stem}_{description}_{timestamp}.backup"
            
            backup_path = self.backup_dir / backup_name
            
            # 复制文件
            shutil.copy2(source_path, backup_path)
            
            # 创建备份信息文件
            backup_info = {
                "original_path": str(source_path),
                "backup_path": str(backup_path),
                "timestamp": timestamp,
                "description": description,
                "file_size": source_path.stat().st_size
            }
            
            info_path = backup_path.with_suffix('.info')
            with open(info_path, 'w', encoding='utf-8') as f:
                json.dump(backup_info, f, indent=2, ensure_ascii=False)
            
            self.logger.info(f"备份创建成功: {backup_path}")
            return str(backup_path)
            
        except Exception as e:
            self.logger.error(f"创建备份失败: {e}")
            return ""
    
    def restore_backup(self, backup_path: str) -> bool:
        """
        恢复备份
        
        Args:
            backup_path (str): 备份文件路径
            
        Returns:
            bool: 恢复是否成功
        """
        try:
            backup_file = Path(backup_path)
            if not backup_file.exists():
                self.logger.error(f"备份文件不存在: {backup_path}")
                return False
            
            # 读取备份信息
            info_path = backup_file.with_suffix('.info')
            if info_path.exists():
                with open(info_path, 'r', encoding='utf-8') as f:
                    backup_info = json.load(f)
                original_path = backup_info['original_path']
            else:
                # 如果没有信息文件，尝试从文件名推断
                original_path = str(backup_file).replace('.backup', '')
            
            # 恢复文件
            shutil.copy2(backup_file, original_path)
            
            self.logger.info(f"备份恢复成功: {original_path}")
            return True
            
        except Exception as e:
            self.logger.error(f"恢复备份失败: {e}")
            return False
    
    def list_backups(self, file_pattern: str = "*") -> list:
        """
        列出备份文件
        
        Args:
            file_pattern (str): 文件匹配模式
            
        Returns:
            list: 备份文件列表
        """
        try:
            backups = []
            for backup_file in self.backup_dir.glob(f"{file_pattern}.backup"):
                info_file = backup_file.with_suffix('.info')
                if info_file.exists():
                    with open(info_file, 'r', encoding='utf-8') as f:
                        backup_info = json.load(f)
                    backups.append(backup_info)
                else:
                    backups.append({
                        "backup_path": str(backup_file),
                        "timestamp": backup_file.stem.split('_')[-1],
                        "description": "未知"
                    })
            
            # 按时间排序
            backups.sort(key=lambda x: x.get('timestamp', ''), reverse=True)
            return backups
            
        except Exception as e:
            self.logger.error(f"列出备份失败: {e}")
            return []
    
    def cleanup_old_backups(self, keep_count: int = 10):
        """
        清理旧备份
        
        Args:
            keep_count (int): 保留的备份数量
        """
        try:
            backups = self.list_backups()
            if len(backups) <= keep_count:
                return
            
            # 删除多余的备份
            for backup in backups[keep_count:]:
                backup_path = Path(backup['backup_path'])
                info_path = backup_path.with_suffix('.info')
                
                if backup_path.exists():
                    backup_path.unlink()
                if info_path.exists():
                    info_path.unlink()
                
                self.logger.info(f"已删除旧备份: {backup_path}")
                
        except Exception as e:
            self.logger.error(f"清理旧备份失败: {e}")
    
    def create_config_backup(self, config_files: list) -> str:
        """
        创建配置备份
        
        Args:
            config_files (list): 配置文件列表
            
        Returns:
            str: 备份目录路径
        """
        try:
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            backup_dir = self.backup_dir / f"config_backup_{timestamp}"
            backup_dir.mkdir(exist_ok=True)
            
            for config_file in config_files:
                source_path = Path(config_file)
                if source_path.exists():
                    dest_path = backup_dir / source_path.name
                    shutil.copy2(source_path, dest_path)
                    self.logger.info(f"配置备份: {source_path} -> {dest_path}")
            
            self.logger.info(f"配置备份完成: {backup_dir}")
            return str(backup_dir)
            
        except Exception as e:
            self.logger.error(f"创建配置备份失败: {e}")
            return ""


# 全局备份管理器实例
backup_manager = BackupManager()
