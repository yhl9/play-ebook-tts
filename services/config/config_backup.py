"""
配置备份服务

提供配置备份和恢复功能，确保配置的安全性和可恢复性。
支持自动备份、手动备份和配置回滚。

作者: TTS开发团队
版本: 2.0.0
创建时间: 2024
"""

import json
import os
import shutil
from pathlib import Path
from typing import Dict, Any, List, Optional, Tuple
from datetime import datetime, timedelta

from utils.log_manager import LogManager


class ConfigBackup:
    """
    配置备份服务
    
    提供配置备份和恢复功能，确保配置的安全性和可恢复性。
    支持自动备份、手动备份和配置回滚。
    """
    
    def __init__(self, backup_dir: str = "configs/backups", max_backups: int = 10):
        self.logger = LogManager().get_logger("ConfigBackup")
        self.backup_dir = Path(backup_dir)
        self.backup_dir.mkdir(parents=True, exist_ok=True)
        self.max_backups = max_backups
        
        # 备份索引文件
        self.index_file = self.backup_dir / "backup_index.json"
        self._backup_index = self._load_backup_index()
    
    def create_backup(self, config_type: str, description: str = "", 
                     auto_backup: bool = False) -> Optional[str]:
        """
        创建配置备份
        
        Args:
            config_type (str): 配置类型 (app, engine, all)
            description (str): 备份描述
            auto_backup (bool): 是否为自动备份
            
        Returns:
            Optional[str]: 备份ID，失败返回None
        """
        try:
            backup_id = self._generate_backup_id()
            backup_path = self.backup_dir / backup_id
            
            # 创建备份目录
            backup_path.mkdir(parents=True, exist_ok=True)
            
            # 初始化备份统计
            backed_up_files = []
            total_size = 0
            
            # 备份配置
            if config_type == "app" or config_type == "all":
                app_files, app_size = self._backup_app_config(backup_path)
                backed_up_files.extend(app_files)
                total_size += app_size
            
            if config_type == "engine" or config_type == "all":
                engine_files, engine_size = self._backup_engine_configs(backup_path)
                backed_up_files.extend(engine_files)
                total_size += engine_size
            
            # 创建备份元数据
            metadata = {
                "backup_id": backup_id,
                "config_type": config_type,
                "description": description,
                "auto_backup": auto_backup,
                "created_at": datetime.now().isoformat(),
                "file_count": self._count_backup_files(backup_path),
                "total_size": self._calculate_backup_size(backup_path)
            }
            
            # 保存元数据
            metadata_file = backup_path / "metadata.json"
            with open(metadata_file, 'w', encoding='utf-8') as f:
                json.dump(metadata, f, indent=2, ensure_ascii=False)
            
            # 更新备份索引
            self._backup_index[backup_id] = metadata
            self._save_backup_index()
            
            # 清理旧备份
            self._cleanup_old_backups()
            
            self.logger.info(f"配置备份创建成功: {backup_id}")
            return {
                "id": backup_id,
                "description": description,
                "created_at": metadata["created_at"],
                "config_type": config_type,
                "files": backed_up_files,
                "total_size": total_size
            }
            
        except Exception as e:
            self.logger.error(f"创建配置备份失败: {e}")
            return None
    
    def restore_backup(self, backup_id: str, target_dir: str = None) -> bool:
        """
        恢复配置备份
        
        Args:
            backup_id (str): 备份ID
            target_dir (str): 目标目录，None表示恢复到原位置
            
        Returns:
            bool: 恢复是否成功
        """
        try:
            if backup_id not in self._backup_index:
                self.logger.error(f"备份不存在: {backup_id}")
                return False
            
            backup_path = self.backup_dir / backup_id
            if not backup_path.exists():
                self.logger.error(f"备份目录不存在: {backup_path}")
                return False
            
            # 确定目标目录
            if target_dir is None:
                target_dir = "configs"
            target_path = Path(target_dir)
            target_path.mkdir(parents=True, exist_ok=True)
            
            # 恢复配置
            metadata = self._backup_index[backup_id]
            config_type = metadata["config_type"]
            
            if config_type == "app" or config_type == "all":
                self._restore_app_config(backup_path, target_path)
            
            if config_type == "engine" or config_type == "all":
                self._restore_engine_configs(backup_path, target_path)
            
            self.logger.info(f"配置备份恢复成功: {backup_id}")
            return True
            
        except Exception as e:
            self.logger.error(f"恢复配置备份失败 {backup_id}: {e}")
            return False
    
    def list_backups(self, config_type: str = None, 
                    auto_backup: bool = None) -> List[Dict[str, Any]]:
        """
        列出备份
        
        Args:
            config_type (str): 配置类型过滤
            auto_backup (bool): 自动备份过滤
            
        Returns:
            List[Dict[str, Any]]: 备份列表
        """
        backups = []
        
        for backup_id, metadata in self._backup_index.items():
            # 应用过滤条件
            if config_type and metadata["config_type"] != config_type:
                continue
            if auto_backup is not None and metadata["auto_backup"] != auto_backup:
                continue
            
            # 检查备份是否仍然存在
            backup_path = self.backup_dir / backup_id
            if backup_path.exists():
                backups.append(metadata)
            else:
                # 清理不存在的备份记录
                del self._backup_index[backup_id]
        
        # 按创建时间排序
        backups.sort(key=lambda x: x["created_at"], reverse=True)
        return backups
    
    def delete_backup(self, backup_id: str) -> bool:
        """
        删除备份
        
        Args:
            backup_id (str): 备份ID
            
        Returns:
            bool: 删除是否成功
        """
        try:
            if backup_id not in self._backup_index:
                self.logger.error(f"备份不存在: {backup_id}")
                return False
            
            backup_path = self.backup_dir / backup_id
            if backup_path.exists():
                shutil.rmtree(backup_path)
            
            # 从索引中移除
            del self._backup_index[backup_id]
            self._save_backup_index()
            
            self.logger.info(f"备份删除成功: {backup_id}")
            return True
            
        except Exception as e:
            self.logger.error(f"删除备份失败 {backup_id}: {e}")
            return False
    
    def get_backup_info(self, backup_id: str) -> Optional[Dict[str, Any]]:
        """
        获取备份信息
        
        Args:
            backup_id (str): 备份ID
            
        Returns:
            Optional[Dict[str, Any]]: 备份信息
        """
        return self._backup_index.get(backup_id)
    
    def cleanup_old_backups(self, days: int = 30) -> int:
        """
        清理旧备份
        
        Args:
            days (int): 保留天数
            
        Returns:
            int: 清理的备份数量
        """
        try:
            cutoff_date = datetime.now() - timedelta(days=days)
            cleaned_count = 0
            
            for backup_id, metadata in list(self._backup_index.items()):
                created_at = datetime.fromisoformat(metadata["created_at"])
                if created_at < cutoff_date:
                    if self.delete_backup(backup_id):
                        cleaned_count += 1
            
            self.logger.info(f"清理旧备份完成，清理数量: {cleaned_count}")
            return cleaned_count
            
        except Exception as e:
            self.logger.error(f"清理旧备份失败: {e}")
            return 0
    
    def _backup_app_config(self, backup_path: Path):
        """备份应用程序配置"""
        app_config_dir = Path("configs/app")
        backed_up_files = []
        total_size = 0
        
        if app_config_dir.exists():
            target_dir = backup_path / "app"
            shutil.copytree(app_config_dir, target_dir)
            
            # 统计备份的文件
            for file_path in target_dir.rglob("*"):
                if file_path.is_file():
                    backed_up_files.append(str(file_path.relative_to(backup_path)))
                    total_size += file_path.stat().st_size
        
        return backed_up_files, total_size
    
    def _backup_engine_configs(self, backup_path: Path):
        """备份引擎配置"""
        engine_config_dir = Path("configs/engines")
        backed_up_files = []
        total_size = 0
        
        if engine_config_dir.exists():
            target_dir = backup_path / "engines"
            shutil.copytree(engine_config_dir, target_dir)
            
            # 统计备份的文件
            for file_path in target_dir.rglob("*"):
                if file_path.is_file():
                    backed_up_files.append(str(file_path.relative_to(backup_path)))
                    total_size += file_path.stat().st_size
        
        return backed_up_files, total_size
    
    def _restore_app_config(self, backup_path: Path, target_path: Path):
        """恢复应用程序配置"""
        app_backup_dir = backup_path / "app"
        if app_backup_dir.exists():
            target_app_dir = target_path / "app"
            if target_app_dir.exists():
                shutil.rmtree(target_app_dir)
            shutil.copytree(app_backup_dir, target_app_dir)
    
    def _restore_engine_configs(self, backup_path: Path, target_path: Path):
        """恢复引擎配置"""
        engine_backup_dir = backup_path / "engines"
        if engine_backup_dir.exists():
            target_engine_dir = target_path / "engines"
            if target_engine_dir.exists():
                shutil.rmtree(target_engine_dir)
            shutil.copytree(engine_backup_dir, target_engine_dir)
    
    def _generate_backup_id(self) -> str:
        """生成备份ID"""
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        return f"backup_{timestamp}"
    
    def _count_backup_files(self, backup_path: Path) -> int:
        """计算备份文件数量"""
        count = 0
        for root, dirs, files in os.walk(backup_path):
            count += len(files)
        return count
    
    def _calculate_backup_size(self, backup_path: Path) -> int:
        """计算备份大小"""
        total_size = 0
        for root, dirs, files in os.walk(backup_path):
            for file in files:
                file_path = Path(root) / file
                total_size += file_path.stat().st_size
        return total_size
    
    def _cleanup_old_backups(self):
        """清理旧备份"""
        if len(self._backup_index) > self.max_backups:
            # 按创建时间排序，删除最旧的备份
            sorted_backups = sorted(
                self._backup_index.items(),
                key=lambda x: x[1]["created_at"]
            )
            
            # 删除超出限制的备份
            for backup_id, _ in sorted_backups[:-self.max_backups]:
                self.delete_backup(backup_id)
    
    def _load_backup_index(self) -> Dict[str, Any]:
        """加载备份索引"""
        try:
            if self.index_file.exists():
                with open(self.index_file, 'r', encoding='utf-8') as f:
                    return json.load(f)
            return {}
        except Exception as e:
            self.logger.error(f"加载备份索引失败: {e}")
            return {}
    
    def _save_backup_index(self):
        """保存备份索引"""
        try:
            with open(self.index_file, 'w', encoding='utf-8') as f:
                json.dump(self._backup_index, f, indent=2, ensure_ascii=False)
        except Exception as e:
            self.logger.error(f"保存备份索引失败: {e}")
