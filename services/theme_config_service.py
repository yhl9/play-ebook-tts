"""
主题配置管理服务

提供主题配置的加载、保存、应用等功能
支持预设主题和自定义主题管理
"""

import json
import os
from typing import Dict, Any, Optional
from utils.log_manager import LogManager


class ThemeConfigService:
    """主题配置管理服务类"""
    
    def __init__(self):
        self.logger = LogManager().get_logger("ThemeConfigService")
        # 获取项目根目录
        current_dir = os.path.dirname(os.path.abspath(__file__))
        project_root = os.path.dirname(current_dir)
        
        self.theme_config_file = os.path.join(project_root, "configs", "theme_config.json")
        self.preset_themes_file = os.path.join(project_root, "configs", "dicts", "UI_theme_prepared.json")
        
        # 配置数据
        self.theme_config = {}
        self.preset_themes = {}
        
        # 加载配置
        self.load_configs()
    
    def load_configs(self):
        """加载所有配置文件"""
        try:
            # 加载主配置文件
            self.load_theme_config()
            
            # 加载预设主题配置
            self.load_preset_themes()
            
            self.logger.info("主题配置加载完成")
            
        except Exception as e:
            self.logger.error(f"加载主题配置失败: {e}")
    
    def load_theme_config(self):
        """加载主主题配置文件"""
        try:
            if os.path.exists(self.theme_config_file):
                with open(self.theme_config_file, 'r', encoding='utf-8') as f:
                    self.theme_config = json.load(f)
                self.logger.info(f"已加载主题配置文件: {self.theme_config_file}")
            else:
                self.logger.warning(f"主题配置文件不存在: {self.theme_config_file}")
                
        except Exception as e:
            self.logger.error(f"加载主题配置文件失败: {e}")
    
    def load_preset_themes(self):
        """加载预设主题配置"""
        try:
            if os.path.exists(self.preset_themes_file):
                with open(self.preset_themes_file, 'r', encoding='utf-8') as f:
                    data = json.load(f)
                    self.preset_themes = data.get('themes', {})
                self.logger.info(f"已加载预设主题配置: {len(self.preset_themes)} 个主题")
            else:
                self.logger.warning(f"预设主题配置文件不存在: {self.preset_themes_file}")
                
        except Exception as e:
            self.logger.error(f"加载预设主题配置失败: {e}")
    
    def get_available_themes(self) -> list:
        """获取可用主题列表"""
        return self.theme_config.get('available_themes', [])
    
    def get_theme_info(self, theme_id: str) -> Optional[Dict[str, Any]]:
        """获取主题信息"""
        return self.theme_config.get('theme_info', {}).get(theme_id)
    
    def get_preset_theme_config(self, theme_id: str) -> Optional[Dict[str, Any]]:
        """获取预设主题配置"""
        return self.preset_themes.get(theme_id)
    
    def get_current_theme(self) -> str:
        """获取当前主题"""
        return self.theme_config.get('current_theme', 'light')
    
    def set_current_theme(self, theme_id: str):
        """设置当前主题"""
        try:
            self.theme_config['current_theme'] = theme_id
            self.save_theme_config()
            self.logger.info(f"已设置当前主题: {theme_id}")
            
        except Exception as e:
            self.logger.error(f"设置当前主题失败: {e}")
    
    def get_custom_theme(self) -> Dict[str, Any]:
        """获取自定义主题配置"""
        return self.theme_config.get('custom_theme', {})
    
    def set_custom_theme(self, custom_config: Dict[str, Any]):
        """设置自定义主题配置"""
        try:
            self.theme_config['custom_theme'] = custom_config
            self.save_theme_config()
            self.logger.info("已更新自定义主题配置")
            
        except Exception as e:
            self.logger.error(f"设置自定义主题失败: {e}")
    
    def get_font_options(self) -> Dict[str, list]:
        """获取字体选项"""
        return self.theme_config.get('font_options', {
            'sizes': ['small', 'medium', 'large'],
            'weights': ['normal', 'bold']
        })
    
    def get_font_size_info(self, size_id: str) -> Optional[Dict[str, str]]:
        """获取字体大小信息"""
        if 'font_sizes' in self.preset_themes:
            return self.preset_themes['font_sizes'].get(size_id)
        return None
    
    def get_font_weight_info(self, weight_id: str) -> Optional[Dict[str, str]]:
        """获取字体粗细信息"""
        if 'font_weights' in self.preset_themes:
            return self.preset_themes['font_weights'].get(weight_id)
        return None
    
    def save_theme_config(self):
        """保存主题配置文件"""
        try:
            # 确保目录存在
            os.makedirs(os.path.dirname(self.theme_config_file), exist_ok=True)
            
            # 更新最后修改时间
            self.theme_config['last_updated'] = "2024-12-19"
            
            with open(self.theme_config_file, 'w', encoding='utf-8') as f:
                json.dump(self.theme_config, f, ensure_ascii=False, indent=2)
            
            self.logger.info(f"已保存主题配置文件: {self.theme_config_file}")
            
        except Exception as e:
            self.logger.error(f"保存主题配置文件失败: {e}")
    
    def apply_theme_config(self, theme_id: str) -> bool:
        """应用主题配置"""
        try:
            # 检查是否为自定义主题
            if theme_id == 'custom':
                custom_config = self.get_custom_theme()
                if not custom_config.get('enabled', False):
                    self.logger.warning("自定义主题未启用")
                    return False
                return self._apply_custom_theme(custom_config)
            else:
                # 应用预设主题
                preset_config = self.get_preset_theme_config(theme_id)
                if preset_config:
                    return self._apply_preset_theme(theme_id, preset_config)
                else:
                    self.logger.error(f"未找到主题配置: {theme_id}")
                    return False
                    
        except Exception as e:
            self.logger.error(f"应用主题配置失败: {e}")
            return False
    
    def _apply_preset_theme(self, theme_id: str, config: Dict[str, Any]) -> bool:
        """应用预设主题"""
        try:
            # 设置当前主题
            self.set_current_theme(theme_id)
            
            # 这里可以调用主题服务应用样式
            # theme_service.apply_theme_config(config)
            
            self.logger.info(f"已应用预设主题: {theme_id}")
            return True
            
        except Exception as e:
            self.logger.error(f"应用预设主题失败: {e}")
            return False
    
    def _apply_custom_theme(self, config: Dict[str, Any]) -> bool:
        """应用自定义主题"""
        try:
            # 设置当前主题为自定义
            self.set_current_theme('custom')
            
            # 这里可以调用主题服务应用自定义样式
            # theme_service.apply_custom_theme(config)
            
            self.logger.info("已应用自定义主题")
            return True
            
        except Exception as e:
            self.logger.error(f"应用自定义主题失败: {e}")
            return False
    
    def create_custom_theme(self, colors: Dict[str, str], fonts: Dict[str, str]) -> bool:
        """创建自定义主题"""
        try:
            custom_config = {
                'enabled': True,
                'colors': colors,
                'fonts': fonts
            }
            
            self.set_custom_theme(custom_config)
            self.logger.info("已创建自定义主题")
            return True
            
        except Exception as e:
            self.logger.error(f"创建自定义主题失败: {e}")
            return False


# 全局主题配置服务实例
theme_config_service = ThemeConfigService()
