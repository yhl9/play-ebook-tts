#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
语言服务模块
"""

import json
import sys
from pathlib import Path
from typing import Dict, Any, Callable
from PyQt6.QtCore import QObject, pyqtSignal
from utils.log_manager import LogManager


class LanguageService(QObject):
    """语言服务类"""
    
    language_changed = pyqtSignal(str)
    
    def __init__(self):
        super().__init__()
        self.logger = LogManager().get_logger(__name__)
        self.current_language = "zh-CN"
        self.language_config = {}
        self.ui_texts = {}
        self.language_change_callbacks = []
        
        self._load_language_config()
        self._load_ui_texts()
    
    def _load_language_config(self):
        """加载语言配置"""
        try:
            # 从主配置文件读取语言设置
            main_config_path = Path(__file__).parent.parent / "config.json"
            if main_config_path.exists():
                with open(main_config_path, "r", encoding="utf-8") as f:
                    main_config = json.load(f)
                    
                    # 从 general 部分读取语言显示名称
                    main_language = main_config.get("general", {}).get("language", "")
                    if main_language:
                        # 确保 main_language 是字符串类型
                        if isinstance(main_language, int):
                            # 如果是整数，使用默认语言
                            self.current_language = "zh-CN"
                            self.logger.warning(f"配置中的语言是整数类型: {main_language}，使用默认语言: zh-CN")
                        elif isinstance(main_language, str):
                            # 提取语言代码（如 "简体中文 (zh-CN)" -> "zh-CN"）
                            if "(" in main_language and ")" in main_language:
                                self.current_language = main_language.split("(")[-1].split(")")[0]
                            else:
                                self.current_language = main_language
                            self.logger.info(f"从主配置文件读取语言: {self.current_language}")
                        else:
                            # 其他类型，使用默认语言
                            self.current_language = "zh-CN"
                            self.logger.warning(f"配置中的语言类型不支持: {type(main_language)}，使用默认语言: zh-CN")
                    
                    # 从 language 部分读取语言配置
                    language_config = main_config.get("language", {})
                    if language_config:
                        self.language_config = language_config
                        self.logger.info("从主配置文件读取语言配置")
                    else:
                        # 如果没有 language 部分，使用默认配置
                        self.language_config = {
                            "current_language": self.current_language or "zh-CN",
                            "supported_languages": ["zh-CN", "en-US", "ja-JP"],
                            "language_info": {
                                "zh-CN": {"name": "简体中文", "description": "中文界面", "ui_config_file": "UI_zh.json", "locale": "zh_CN"},
                                "en-US": {"name": "English", "description": "English Interface", "ui_config_file": "UI_en.json", "locale": "en_US"},
                                "ja-JP": {"name": "日本語", "description": "日本語インターフェース", "ui_config_file": "UI_jp.json", "locale": "ja_JP"}
                            },
                            "ui_config_path": "configs/dicts/",
                            "default_language": "zh-CN",
                            "fallback_language": "zh-CN"
                        }
                        self.logger.info("使用默认语言配置")
            else:
                # 如果主配置文件不存在，使用默认配置
                self.current_language = "zh-CN"
                self.language_config = {
                    "current_language": "zh-CN",
                    "supported_languages": ["zh-CN", "en-US", "ja-JP"],
                    "language_info": {
                        "zh-CN": {"name": "简体中文", "description": "中文界面", "ui_config_file": "UI_zh.json", "locale": "zh_CN"},
                        "en-US": {"name": "English", "description": "English Interface", "ui_config_file": "UI_en.json", "locale": "en_US"},
                        "ja-JP": {"name": "日本語", "description": "日本語インターフェース", "ui_config_file": "UI_jp.json", "locale": "ja_JP"}
                    },
                    "ui_config_path": "configs/dicts/",
                    "default_language": "zh-CN",
                    "fallback_language": "zh-CN"
                }
                self.logger.info("主配置文件不存在，使用默认语言配置")
            
        except Exception as e:
            self.logger.error(f"加载语言配置失败: {e}")
            self.current_language = "zh-CN"
            self.language_config = {
                "current_language": "zh-CN",
                "supported_languages": ["zh-CN", "en-US", "ja-JP"],
                "language_info": {
                    "zh-CN": {"name": "简体中文", "description": "中文界面", "ui_config_file": "UI_zh.json", "locale": "zh_CN"},
                    "en-US": {"name": "English", "description": "English Interface", "ui_config_file": "UI_en.json", "locale": "en_US"},
                    "ja-JP": {"name": "日本語", "description": "日本語インターフェース", "ui_config_file": "UI_jp.json", "locale": "ja_JP"}
                },
                "ui_config_path": "configs/dicts/",
                "default_language": "zh-CN",
                "fallback_language": "zh-CN"
            }
    
    def _load_ui_texts(self):
        """加载UI文本"""
        try:
            current_lang_info = self.language_config.get("language_info", {}).get(self.current_language)
            if not current_lang_info:
                return
            
            ui_config_file = current_lang_info.get("ui_config_file")
            if not ui_config_file:
                return
            
            # 支持 PyInstaller 打包环境
            if getattr(sys, 'frozen', False):
                # 打包后的环境
                base_path = Path(sys._MEIPASS)
                ui_config_path = base_path / "configs" / "dicts" / ui_config_file
            else:
                # 开发环境
                ui_config_path = Path(__file__).parent.parent / "configs" / "dicts" / ui_config_file
            
            with open(ui_config_path, "r", encoding="utf-8") as f:
                self.ui_texts = json.load(f)
            self.logger.info(f"UI文本加载成功: {self.current_language}")
        except Exception as e:
            self.logger.error(f"加载UI文本失败: {e}")
    
    def get_text(self, key_path: str, **kwargs) -> str:
        """获取UI文本"""
        try:
            keys = key_path.split(".")
            value = self.ui_texts
            for key in keys:
                if isinstance(value, dict) and key in value:
                    value = value[key]
                else:
                    return key_path
            
            if isinstance(value, str) and kwargs:
                return value.format(**kwargs)
            return str(value)
        except Exception as e:
            self.logger.error(f"获取UI文本失败: {e}")
            return key_path
    
    def get_current_language(self) -> str:
        """获取当前语言"""
        return self.current_language
    
    def set_language(self, language_code: str) -> bool:
        """设置语言"""
        try:
            if language_code not in self.language_config.get("supported_languages", []):
                return False
            
            if language_code == self.current_language:
                return True
            
            self.current_language = language_code
            self._load_ui_texts()
            self._save_language_config()
            self._save_main_config(language_code)
            self.language_changed.emit(language_code)
            
            for callback in self.language_change_callbacks:
                try:
                    callback(language_code)
                except Exception as e:
                    self.logger.error(f"语言改变回调执行失败: {e}")
            
            return True
        except Exception as e:
            self.logger.error(f"设置语言失败: {e}")
            return False
    
    def _save_language_config(self):
        """保存语言配置到主配置文件"""
        try:
            main_config_path = Path(__file__).parent.parent / "config.json"
            if main_config_path.exists():
                # 读取现有配置
                with open(main_config_path, "r", encoding="utf-8") as f:
                    main_config = json.load(f)
                
                # 更新语言配置
                self.language_config["current_language"] = self.current_language
                main_config["language"] = self.language_config
                
                # 保存配置
                with open(main_config_path, "w", encoding="utf-8") as f:
                    json.dump(main_config, f, ensure_ascii=False, indent=2)
                
                self.logger.info(f"语言配置已保存到主配置文件: {self.current_language}")
            else:
                self.logger.warning("主配置文件不存在，无法保存语言配置")
        except Exception as e:
            self.logger.error(f"保存语言配置失败: {e}")
    
    def _save_main_config(self, language_code: str):
        """保存主配置文件中的语言设置"""
        try:
            main_config_path = Path(__file__).parent.parent / "config.json"
            if main_config_path.exists():
                with open(main_config_path, "r", encoding="utf-8") as f:
                    main_config = json.load(f)
                
                # 获取语言显示名称
                lang_info = self.language_config.get("language_info", {}).get(language_code, {})
                lang_name = lang_info.get("name", language_code)
                language_display = f"{lang_name} ({language_code})"
                
                # 更新语言设置
                if "general" not in main_config:
                    main_config["general"] = {}
                main_config["general"]["language"] = language_display
                
                # 保存配置文件
                with open(main_config_path, "w", encoding="utf-8") as f:
                    json.dump(main_config, f, ensure_ascii=False, indent=2)
                
                self.logger.info(f"主配置文件语言已更新: {language_display}")
            
        except Exception as e:
            self.logger.error(f"保存主配置文件失败: {e}")
    
    def get_supported_languages(self) -> list:
        """获取支持的语言列表"""
        return self.language_config.get("supported_languages", [])
    
    def get_language_info(self, language_code: str) -> Dict[str, Any]:
        """获取语言信息"""
        return self.language_config.get("language_info", {}).get(language_code, {})
    
    def add_language_change_callback(self, callback: Callable[[str], None]):
        """添加语言改变回调"""
        if callback not in self.language_change_callbacks:
            self.language_change_callbacks.append(callback)


# 全局实例
_language_service = None

def get_language_service() -> LanguageService:
    """获取全局语言服务实例"""
    global _language_service
    if _language_service is None:
        _language_service = LanguageService()
    return _language_service

def get_text(key_path: str, **kwargs) -> str:
    """获取UI文本（便捷函数）"""
    return get_language_service().get_text(key_path, **kwargs)
