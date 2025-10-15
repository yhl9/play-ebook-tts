"""
全局语言管理模块
应用启动时加载语言配置，提供全局翻译函数
"""

import json
import os
from typing import Dict, Any
from utils.log_manager import LogManager


class LanguageManager:
    """全局语言管理器"""
    
    def __init__(self):
        self.logger = LogManager().get_logger("LanguageManager")
        self.current_language = "zh-CN"
        self.language_dict = {}
        self.language_info = {}
        
        # 自动加载语言配置
        self.load_language_config()
        
    def load_language_config(self):
        """加载语言配置"""
        try:
            # 获取项目根目录
            current_dir = os.path.dirname(os.path.abspath(__file__))
            project_root = os.path.dirname(current_dir)
            
            # 1. 读取主配置文件获取当前语言
            config_file = os.path.join(project_root, "config.json")
            if os.path.exists(config_file):
                with open(config_file, 'r', encoding='utf-8') as f:
                    config = json.load(f)
                    # 支持两种配置结构
                    if 'language' in config:
                        self.current_language = config.get('language', 'zh-CN')
                    elif 'general' in config and 'language' in config['general']:
                        self.current_language = config['general'].get('language', 'zh-CN')
                    else:
                        self.current_language = 'zh-CN'
                    self.logger.info(f"从配置文件读取语言: {self.current_language}")
            else:
                self.logger.warning(f"配置文件不存在: {config_file}")
            
            # 2. 读取语言配置文件
            language_config_file = os.path.join(project_root, "configs", "language_config.json")
            if os.path.exists(language_config_file):
                with open(language_config_file, 'r', encoding='utf-8') as f:
                    self.language_info = json.load(f)
                    self.logger.info(f"语言配置加载成功，支持语言: {self.language_info.get('supported_languages', [])}")
            else:
                self.logger.warning(f"语言配置文件不存在: {language_config_file}")
            
            # 3. 加载对应语言的字典文件
            self.load_language_dict()
            
        except Exception as e:
            self.logger.error(f"加载语言配置失败: {e}")
            # 使用默认中文
            self.current_language = "zh-CN"
            self.load_language_dict()
    
    def load_language_dict(self):
        """加载当前语言的字典文件"""
        try:
            if self.current_language in self.language_info.get('language_info', {}):
                lang_info = self.language_info['language_info'][self.current_language]
                dict_file = lang_info['ui_config_file']
                # 获取项目根目录
                current_dir = os.path.dirname(os.path.abspath(__file__))
                project_root = os.path.dirname(current_dir)
                dict_path = os.path.join(project_root, "configs", "dicts", dict_file)
                
                if os.path.exists(dict_path):
                    with open(dict_path, 'r', encoding='utf-8') as f:
                        self.language_dict = json.load(f)
                    self.logger.info(f"已加载语言字典: {self.current_language} -> {dict_file}")
                else:
                    self.logger.error(f"语言字典文件不存在: {dict_path}")
            else:
                self.logger.error(f"不支持的语言: {self.current_language}")
                
        except Exception as e:
            self.logger.error(f"加载语言字典失败: {e}")
    
    def get_text(self, key: str, **kwargs) -> str:
        """获取翻译文本"""
        try:
            # 按层级获取文本，如 "settings.title"
            keys = key.split('.')
            text = self.language_dict
            
            for k in keys:
                if isinstance(text, dict) and k in text:
                    text = text[k]
                else:
                    return key  # 找不到返回键名
            
            # 如果是字符串，支持格式化参数
            if isinstance(text, str) and kwargs:
                return text.format(**kwargs)
            return text if isinstance(text, str) else key
            
        except Exception as e:
            self.logger.error(f"获取翻译文本失败: {key}, {e}")
            return key
    
    def set_language(self, language: str):
        """设置语言（只更新配置文件，不立即生效）"""
        try:
            if language in self.language_info.get('supported_languages', []):
                # 更新配置文件
                current_dir = os.path.dirname(os.path.abspath(__file__))
                project_root = os.path.dirname(current_dir)
                config_file = os.path.join(project_root, "config.json")
                if os.path.exists(config_file):
                    with open(config_file, 'r', encoding='utf-8') as f:
                        config = json.load(f)
                    
                    # 支持两种配置结构
                    if 'general' in config:
                        config['general']['language'] = language
                    else:
                        config['language'] = language
                    
                    with open(config_file, 'w', encoding='utf-8') as f:
                        json.dump(config, f, ensure_ascii=False, indent=2)
                    
                    self.logger.info(f"语言已设置为: {language}，重启应用后生效")
                    return True
                else:
                    self.logger.error("配置文件不存在")
            else:
                self.logger.error(f"不支持的语言: {language}")
                
        except Exception as e:
            self.logger.error(f"设置语言失败: {e}")
        
        return False
    
    def get_available_languages(self):
        """获取支持的语言列表"""
        return self.language_info.get('supported_languages', ['zh-CN'])
    
    def get_language_info(self):
        """获取语言信息"""
        return self.language_info.get('language_info', {})
    
    def get_current_language(self):
        """获取当前语言"""
        return self.current_language


# 全局语言管理器实例已废弃，请使用 language_service
# language_manager = LanguageManager()

# 全局翻译函数已废弃，请使用 language_service 中的 get_text
def tr(key: str, **kwargs) -> str:
    """全局翻译函数（已废弃）"""
    # 重定向到新的语言服务
    try:
        from services.language_service import get_language_service
        return get_language_service().get_text(key, **kwargs)
    except Exception as e:
        print(f"翻译函数调用失败，请使用 language_service: {e}")
        return key
