"""
缓存服务
"""

import os
import json
import hashlib
from typing import Optional, Dict, Any
from datetime import datetime

from utils.log_manager import LogManager


class CacheService:
    """缓存服务"""
    
    def __init__(self, cache_dir: str = "cache"):
        self.cache_dir = cache_dir
        self.logger = LogManager().get_logger("CacheService")
        self._ensure_cache_dir()
    
    def _ensure_cache_dir(self):
        """确保缓存目录存在"""
        try:
            if not os.path.exists(self.cache_dir):
                os.makedirs(self.cache_dir, exist_ok=True)
                self.logger.info(f"创建缓存目录: {self.cache_dir}")
        except Exception as e:
            self.logger.error(f"创建缓存目录失败: {e}")
            raise
    
    def get_file_hash(self, file_path: str) -> str:
        """获取文件哈希值"""
        try:
            with open(file_path, 'rb') as f:
                content = f.read()
                return hashlib.md5(content).hexdigest()
        except Exception as e:
            self.logger.error(f"计算文件哈希失败: {e}")
            return ""
    
    def get_cache_path(self, file_path: str) -> str:
        """获取缓存文件路径"""
        file_hash = self.get_file_hash(file_path)
        if not file_hash:
            return ""
        
        # 获取文件名（不含扩展名）
        base_name = os.path.splitext(os.path.basename(file_path))[0]
        cache_file = f"{base_name}_{file_hash[:8]}.json"
        return os.path.join(self.cache_dir, cache_file)
    
    def save_to_cache(self, file_path: str, content: str, metadata: Dict[str, Any] = None) -> bool:
        """保存内容到缓存"""
        try:
            cache_path = self.get_cache_path(file_path)
            if not cache_path:
                return False
            
            cache_data = {
                "file_path": file_path,
                "content": content,
                "metadata": metadata or {},
                "cached_at": datetime.now().isoformat(),
                "file_size": len(content),
                "file_hash": self.get_file_hash(file_path)
            }
            
            with open(cache_path, 'w', encoding='utf-8') as f:
                json.dump(cache_data, f, ensure_ascii=False, indent=2)
            
            self.logger.info(f"文件已缓存: {cache_path}")
            return True
            
        except Exception as e:
            self.logger.error(f"保存缓存失败: {e}")
            return False
    
    def load_from_cache(self, file_path: str) -> Optional[Dict[str, Any]]:
        """从缓存加载内容"""
        try:
            cache_path = self.get_cache_path(file_path)
            if not cache_path or not os.path.exists(cache_path):
                return None
            
            # 检查文件是否已修改
            current_hash = self.get_file_hash(file_path)
            if not current_hash:
                return None
            
            with open(cache_path, 'r', encoding='utf-8') as f:
                cache_data = json.load(f)
            
            # 验证文件哈希
            if cache_data.get("file_hash") != current_hash:
                self.logger.info(f"文件已修改，缓存失效: {file_path}")
                return None
            
            self.logger.info(f"从缓存加载: {cache_path}")
            return cache_data
            
        except Exception as e:
            self.logger.error(f"加载缓存失败: {e}")
            return None
    
    def clear_cache(self) -> bool:
        """清空缓存"""
        try:
            if os.path.exists(self.cache_dir):
                for file in os.listdir(self.cache_dir):
                    file_path = os.path.join(self.cache_dir, file)
                    if os.path.isfile(file_path):
                        os.remove(file_path)
                
                self.logger.info("缓存已清空")
                return True
            return True
            
        except Exception as e:
            self.logger.error(f"清空缓存失败: {e}")
            return False
    
    def get_cache_info(self) -> Dict[str, Any]:
        """获取缓存信息"""
        try:
            if not os.path.exists(self.cache_dir):
                return {
                    "cache_dir": self.cache_dir,
                    "file_count": 0,
                    "total_size": 0,
                    "files": []
                }
            
            files = []
            total_size = 0
            
            for file in os.listdir(self.cache_dir):
                file_path = os.path.join(self.cache_dir, file)
                if os.path.isfile(file_path):
                    file_size = os.path.getsize(file_path)
                    files.append({
                        "name": file,
                        "size": file_size,
                        "modified": datetime.fromtimestamp(os.path.getmtime(file_path)).isoformat()
                    })
                    total_size += file_size
            
            return {
                "cache_dir": self.cache_dir,
                "file_count": len(files),
                "total_size": total_size,
                "files": files
            }
            
        except Exception as e:
            self.logger.error(f"获取缓存信息失败: {e}")
            return {
                "cache_dir": self.cache_dir,
                "file_count": 0,
                "total_size": 0,
                "files": []
            }
    
    def set_cache_dir(self, new_cache_dir: str) -> bool:
        """设置新的缓存目录"""
        try:
            old_cache_dir = self.cache_dir
            self.cache_dir = new_cache_dir
            self._ensure_cache_dir()
            self.logger.info(f"缓存目录已更改: {old_cache_dir} -> {new_cache_dir}")
            return True
        except Exception as e:
            self.logger.error(f"设置缓存目录失败: {e}")
            return False
