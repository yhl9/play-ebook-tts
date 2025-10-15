"""
参数配置服务
"""

import json
import os
from typing import Dict, Any, List, Optional
from dataclasses import dataclass, field
from utils.log_manager import LogManager


@dataclass
class ParameterDefinition:
    """参数定义"""
    name: str
    type: str
    label: str
    required: bool = False
    default: Any = None
    description: str = ""
    options: List[Dict[str, Any]] = field(default_factory=list)
    min_value: Optional[float] = None
    max_value: Optional[float] = None
    step: Optional[float] = None
    unit: str = ""
    filters: str = ""
    source: str = ""


@dataclass
class ParameterGroup:
    """参数分组"""
    title: str
    parameters: Dict[str, ParameterDefinition] = field(default_factory=dict)


@dataclass
class EngineConfig:
    """引擎配置"""
    name: str
    description: str
    groups: Dict[str, ParameterGroup] = field(default_factory=dict)


class ParameterConfigService:
    """参数配置服务"""
    
    def __init__(self, config_file: str = "configs/engine_parameters.json"):
        self.logger = LogManager().get_logger("ParameterConfigService")
        self.config_file = config_file
        self.engine_configs: Dict[str, EngineConfig] = {}
        self.load_configs()
    
    def load_configs(self):
        """加载配置文件"""
        try:
            if not os.path.exists(self.config_file):
                self.logger.error(f"配置文件不存在: {self.config_file}")
                return
            
            with open(self.config_file, 'r', encoding='utf-8') as f:
                config_data = json.load(f)
            
            self._parse_configs(config_data)
            self.logger.info(f"成功加载 {len(self.engine_configs)} 个引擎配置")
            
        except Exception as e:
            self.logger.error(f"加载配置文件失败: {e}")
    
    def _parse_configs(self, config_data: Dict[str, Any]):
        """解析配置数据"""
        engines_data = config_data.get("engines", {})
        
        for engine_id, engine_data in engines_data.items():
            # 创建引擎配置
            engine_config = EngineConfig(
                name=engine_data.get("name", engine_id),
                description=engine_data.get("description", "")
            )
            
            # 解析参数分组
            groups_data = engine_data.get("groups", {})
            for group_id, group_data in groups_data.items():
                group = ParameterGroup(title=group_data.get("title", group_id))
                
                # 解析参数定义
                parameters_data = group_data.get("parameters", {})
                for param_id, param_data in parameters_data.items():
                    param_def = self._parse_parameter_definition(param_id, param_data)
                    group.parameters[param_id] = param_def
                
                engine_config.groups[group_id] = group
            
            self.engine_configs[engine_id] = engine_config
    
    def _parse_parameter_definition(self, param_id: str, param_data: Dict[str, Any]) -> ParameterDefinition:
        """解析参数定义"""
        return ParameterDefinition(
            name=param_id,
            type=param_data.get("type", "text"),
            label=param_data.get("label", param_id),
            required=param_data.get("required", False),
            default=param_data.get("default"),
            description=param_data.get("description", ""),
            options=param_data.get("options", []),
            min_value=param_data.get("min"),
            max_value=param_data.get("max"),
            step=param_data.get("step"),
            unit=param_data.get("unit", ""),
            filters=param_data.get("filters", ""),
            source=param_data.get("source", "")
        )
    
    def get_engine_config(self, engine_id: str) -> Optional[EngineConfig]:
        """获取引擎配置"""
        return self.engine_configs.get(engine_id)
    
    def get_available_engines(self) -> List[str]:
        """获取可用的引擎列表"""
        return list(self.engine_configs.keys())
    
    def get_parameter_definition(self, engine_id: str, group_id: str, param_id: str) -> Optional[ParameterDefinition]:
        """获取参数定义"""
        engine_config = self.get_engine_config(engine_id)
        if not engine_config:
            return None
        
        group = engine_config.groups.get(group_id)
        if not group:
            return None
        
        return group.parameters.get(param_id)
    
    def get_parameter_groups(self, engine_id: str) -> Dict[str, ParameterGroup]:
        """获取引擎的参数分组"""
        engine_config = self.get_engine_config(engine_id)
        if not engine_config:
            return {}
        
        return engine_config.groups
    
    def get_all_parameters(self, engine_id: str) -> Dict[str, ParameterDefinition]:
        """获取引擎的所有参数定义"""
        groups = self.get_parameter_groups(engine_id)
        all_params = {}
        
        for group in groups.values():
            all_params.update(group.parameters)
        
        return all_params
    
    def validate_parameter_value(self, engine_id: str, param_id: str, value: Any) -> tuple[bool, str]:
        """验证参数值"""
        all_params = self.get_all_parameters(engine_id)
        param_def = all_params.get(param_id)
        
        if not param_def:
            return False, f"参数 {param_id} 不存在"
        
        # 检查必填参数
        if param_def.required and (value is None or value == ""):
            return False, f"参数 {param_def.label} 是必填的"
        
        # 检查数值范围
        if param_def.type in ["slider", "spinbox"] and value is not None:
            if param_def.min_value is not None and value < param_def.min_value:
                return False, f"参数 {param_def.label} 不能小于 {param_def.min_value}"
            
            if param_def.max_value is not None and value > param_def.max_value:
                return False, f"参数 {param_def.label} 不能大于 {param_def.max_value}"
        
        # 检查选项值
        if param_def.type == "combo" and value is not None:
            valid_values = [option.get("value") for option in param_def.options]
            if valid_values and value not in valid_values:
                return False, f"参数 {param_def.label} 的值无效"
        
        return True, ""
    
    def get_default_values(self, engine_id: str) -> Dict[str, Any]:
        """获取引擎的默认参数值"""
        all_params = self.get_all_parameters(engine_id)
        default_values = {}
        
        for param_id, param_def in all_params.items():
            if param_def.default is not None:
                default_values[param_id] = param_def.default
        
        return default_values
    
    def save_config(self, engine_id: str, values: Dict[str, Any], file_path: str = None):
        """保存参数配置"""
        try:
            if not file_path:
                file_path = f"configs/{engine_id}_parameters.json"
            
            # 确保目录存在
            os.makedirs(os.path.dirname(file_path), exist_ok=True)
            
            with open(file_path, 'w', encoding='utf-8') as f:
                json.dump(values, f, ensure_ascii=False, indent=2)
            
            self.logger.info(f"参数配置已保存: {file_path}")
            
        except Exception as e:
            self.logger.error(f"保存参数配置失败: {e}")
            raise
    
    def load_config(self, engine_id: str, file_path: str = None) -> Dict[str, Any]:
        """加载参数配置"""
        try:
            if not file_path:
                file_path = f"configs/{engine_id}_parameters.json"
            
            if not os.path.exists(file_path):
                return self.get_default_values(engine_id)
            
            with open(file_path, 'r', encoding='utf-8') as f:
                values = json.load(f)
            
            self.logger.info(f"参数配置已加载: {file_path}")
            return values
            
        except Exception as e:
            self.logger.error(f"加载参数配置失败: {e}")
            return self.get_default_values(engine_id)
    
    def export_config(self, engine_id: str, file_path: str):
        """导出参数配置"""
        try:
            config = self.get_engine_config(engine_id)
            if not config:
                raise ValueError(f"引擎 {engine_id} 不存在")
            
            export_data = {
                "engine_id": engine_id,
                "engine_name": config.name,
                "description": config.description,
                "groups": {}
            }
            
            for group_id, group in config.groups.items():
                export_data["groups"][group_id] = {
                    "title": group.title,
                    "parameters": {}
                }
                
                for param_id, param_def in group.parameters.items():
                    export_data["groups"][group_id]["parameters"][param_id] = {
                        "type": param_def.type,
                        "label": param_def.label,
                        "required": param_def.required,
                        "default": param_def.default,
                        "description": param_def.description
                    }
            
            with open(file_path, 'w', encoding='utf-8') as f:
                json.dump(export_data, f, ensure_ascii=False, indent=2)
            
            self.logger.info(f"参数配置已导出: {file_path}")
            
        except Exception as e:
            self.logger.error(f"导出参数配置失败: {e}")
            raise
