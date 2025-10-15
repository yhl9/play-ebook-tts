"""
配置监控和诊断系统

提供配置系统的实时监控、性能分析和问题诊断功能，包括：
- 配置变更监控
- 性能指标收集
- 问题诊断和修复建议
- 配置健康度评估

作者: TTS开发团队
版本: 2.0.0
创建时间: 2024
"""

import time
import psutil
import threading
from typing import Dict, Any, List, Optional, Callable
from datetime import datetime, timedelta
from collections import defaultdict, deque
from dataclasses import dataclass, field

from models.config_models import AppConfig, EngineConfig, EngineStatusEnum
from utils.log_manager import LogManager


@dataclass
class PerformanceMetrics:
    """性能指标"""
    timestamp: float
    cpu_usage: float
    memory_usage: float
    disk_usage: float
    config_load_time: float
    engine_check_time: float
    total_engines: int
    available_engines: int
    error_count: int


@dataclass
class ConfigChangeEvent:
    """配置变更事件"""
    timestamp: float
    config_type: str  # 'app' or 'engine'
    config_id: str
    change_type: str  # 'create', 'update', 'delete'
    old_value: Any = None
    new_value: Any = None
    user_id: str = "system"


@dataclass
class DiagnosticResult:
    """诊断结果"""
    issue_type: str
    severity: str  # 'low', 'medium', 'high', 'critical'
    description: str
    recommendation: str
    affected_components: List[str]
    auto_fixable: bool = False


class ConfigMonitor:
    """
    配置监控和诊断系统
    
    负责监控配置系统的运行状态，收集性能指标，
    诊断问题并提供修复建议。
    """
    
    def __init__(self, monitoring_interval: int = 30):
        self.logger = LogManager().get_logger("ConfigMonitor")
        self.monitoring_interval = monitoring_interval
        self.is_monitoring = False
        self.monitor_thread = None
        
        # 性能指标历史
        self.performance_history = deque(maxlen=1000)
        
        # 配置变更历史
        self.change_history = deque(maxlen=500)
        
        # 事件监听器
        self.change_listeners: List[Callable] = []
        
        # 诊断规则
        self.diagnostic_rules = self._initialize_diagnostic_rules()
        
        # 监控统计
        self.stats = {
            "total_changes": 0,
            "total_errors": 0,
            "uptime_start": time.time(),
            "last_health_check": 0
        }
        
        # 引擎健康检查标志
        self.engine_health_checked = False
        
        self.logger.info("配置监控系统初始化完成")
    
    def start_monitoring(self):
        """开始监控"""
        if self.is_monitoring:
            self.logger.warning("监控已在运行中")
            return
        
        self.is_monitoring = True
        self.monitor_thread = threading.Thread(target=self._monitoring_loop, daemon=True)
        self.monitor_thread.start()
        self.logger.info("配置监控已启动")
    
    def stop_monitoring(self):
        """停止监控"""
        self.is_monitoring = False
        if self.monitor_thread:
            self.monitor_thread.join(timeout=5)
        self.logger.info("配置监控已停止")
    
    def reset_engine_health_check(self):
        """重置引擎健康检查标志，允许重新检查引擎状态"""
        self.engine_health_checked = False
        self.logger.info("引擎健康检查标志已重置，下次监控时将重新检查引擎状态")
    
    def _monitoring_loop(self):
        """监控循环"""
        while self.is_monitoring:
            try:
                # 收集性能指标
                metrics = self._collect_performance_metrics()
                self.performance_history.append(metrics)
                
                # 执行健康检查（引擎健康检查只执行一次）
                self._perform_health_check()
                
                # 更新统计信息
                self.stats["last_health_check"] = time.time()
                
                time.sleep(self.monitoring_interval)
                
            except Exception as e:
                self.logger.error(f"监控循环异常: {e}")
                time.sleep(5)  # 出错时短暂等待
    
    def _collect_performance_metrics(self) -> PerformanceMetrics:
        """收集性能指标"""
        try:
            # 系统资源使用情况
            cpu_usage = psutil.cpu_percent(interval=1)
            memory = psutil.virtual_memory()
            disk = psutil.disk_usage('/')
            
            # 配置加载时间（模拟）
            config_load_time = self._measure_config_load_time()
            
            # 引擎检查时间（模拟）
            engine_check_time = self._measure_engine_check_time()
            
            return PerformanceMetrics(
                timestamp=time.time(),
                cpu_usage=cpu_usage,
                memory_usage=memory.percent,
                disk_usage=disk.percent,
                config_load_time=config_load_time,
                engine_check_time=engine_check_time,
                total_engines=5,  # 假设有5个引擎
                available_engines=3,  # 假设有3个可用
                error_count=self.stats["total_errors"]
            )
            
        except Exception as e:
            self.logger.error(f"收集性能指标失败: {e}")
            return PerformanceMetrics(
                timestamp=time.time(),
                cpu_usage=0, memory_usage=0, disk_usage=0,
                config_load_time=0, engine_check_time=0,
                total_engines=0, available_engines=0, error_count=0
            )
    
    def _measure_config_load_time(self) -> float:
        """测量配置加载时间"""
        start_time = time.time()
        # 这里可以添加实际的配置加载测试
        time.sleep(0.01)  # 模拟加载时间
        return time.time() - start_time
    
    def _measure_engine_check_time(self) -> float:
        """测量引擎检查时间"""
        start_time = time.time()
        # 这里可以添加实际的引擎检查测试
        time.sleep(0.05)  # 模拟检查时间
        return time.time() - start_time
    
    def _perform_health_check(self):
        """执行健康检查"""
        try:
            # 检查系统资源
            if len(self.performance_history) > 0:
                latest_metrics = self.performance_history[-1]
                
                # CPU使用率检查
                if latest_metrics.cpu_usage > 90:
                    self._record_diagnostic("high_cpu_usage", "high", 
                                          "CPU使用率过高", "考虑减少并发任务或优化配置")
                
                # 内存使用率检查
                if latest_metrics.memory_usage > 85:
                    self._record_diagnostic("high_memory_usage", "high",
                                          "内存使用率过高", "考虑清理缓存或减少缓冲区大小")
                
                # 磁盘使用率检查
                if latest_metrics.disk_usage > 90:
                    self._record_diagnostic("high_disk_usage", "critical",
                                          "磁盘空间不足", "立即清理临时文件或增加存储空间")
                
                # 引擎可用性检查（只执行一次）
                if not self.engine_health_checked:
                    if latest_metrics.available_engines == 0:
                        self._record_diagnostic("no_available_engines", "critical",
                                              "没有可用的TTS引擎", "检查引擎配置和网络连接")
                    elif latest_metrics.available_engines < latest_metrics.total_engines * 0.5:
                        self._record_diagnostic("low_engine_availability", "medium",
                                              "可用引擎数量较少", "检查引擎状态和配置")
                    
                    # 标记引擎健康检查已完成
                    self.engine_health_checked = True
                    self.logger.info("引擎健康检查已完成，后续将跳过引擎检查")
                
                # 错误率检查
                if latest_metrics.error_count > 10:
                    self._record_diagnostic("high_error_rate", "high",
                                          "错误率过高", "检查日志文件并修复配置问题")
            
        except Exception as e:
            self.logger.error(f"健康检查失败: {e}")
    
    def _record_diagnostic(self, issue_type: str, severity: str, 
                          description: str, recommendation: str):
        """记录诊断结果"""
        diagnostic = DiagnosticResult(
            issue_type=issue_type,
            severity=severity,
            description=description,
            recommendation=recommendation,
            affected_components=["config_system"],
            auto_fixable=False
        )
        
        self.logger.warning(f"诊断问题: {description} - {recommendation}")
    
    def _initialize_diagnostic_rules(self) -> Dict[str, Dict[str, Any]]:
        """初始化诊断规则"""
        return {
            "high_cpu_usage": {
                "threshold": 90,
                "severity": "high",
                "auto_fixable": False
            },
            "high_memory_usage": {
                "threshold": 85,
                "severity": "high",
                "auto_fixable": True
            },
            "high_disk_usage": {
                "threshold": 90,
                "severity": "critical",
                "auto_fixable": False
            },
            "no_available_engines": {
                "threshold": 0,
                "severity": "critical",
                "auto_fixable": False
            },
            "low_engine_availability": {
                "threshold": 0.5,
                "severity": "medium",
                "auto_fixable": False
            }
        }
    
    def record_config_change(self, config_type: str, config_id: str, 
                           change_type: str, old_value: Any = None, 
                           new_value: Any = None, user_id: str = "system"):
        """记录配置变更"""
        try:
            change_event = ConfigChangeEvent(
                timestamp=time.time(),
                config_type=config_type,
                config_id=config_id,
                change_type=change_type,
                old_value=old_value,
                new_value=new_value,
                user_id=user_id
            )
            
            self.change_history.append(change_event)
            self.stats["total_changes"] += 1
            
            # 通知监听器
            for listener in self.change_listeners:
                try:
                    listener(change_event)
                except Exception as e:
                    self.logger.error(f"配置变更监听器异常: {e}")
            
            self.logger.debug(f"配置变更记录: {config_type}.{config_id} - {change_type}")
            
        except Exception as e:
            self.logger.error(f"记录配置变更失败: {e}")
    
    def add_change_listener(self, listener: Callable):
        """添加配置变更监听器"""
        self.change_listeners.append(listener)
        self.logger.debug("配置变更监听器已添加")
    
    def remove_change_listener(self, listener: Callable):
        """移除配置变更监听器"""
        if listener in self.change_listeners:
            self.change_listeners.remove(listener)
            self.logger.debug("配置变更监听器已移除")
    
    def get_performance_summary(self, hours: int = 1) -> Dict[str, Any]:
        """获取性能摘要"""
        try:
            cutoff_time = time.time() - (hours * 3600)
            recent_metrics = [m for m in self.performance_history if m.timestamp >= cutoff_time]
            
            if not recent_metrics:
                return {"error": "没有可用的性能数据"}
            
            # 计算统计信息
            cpu_values = [m.cpu_usage for m in recent_metrics]
            memory_values = [m.memory_usage for m in recent_metrics]
            disk_values = [m.disk_usage for m in recent_metrics]
            
            return {
                "time_range_hours": hours,
                "data_points": len(recent_metrics),
                "cpu": {
                    "avg": sum(cpu_values) / len(cpu_values),
                    "max": max(cpu_values),
                    "min": min(cpu_values)
                },
                "memory": {
                    "avg": sum(memory_values) / len(memory_values),
                    "max": max(memory_values),
                    "min": min(memory_values)
                },
                "disk": {
                    "avg": sum(disk_values) / len(disk_values),
                    "max": max(disk_values),
                    "min": min(disk_values)
                },
                "engines": {
                    "total": recent_metrics[-1].total_engines,
                    "available": recent_metrics[-1].available_engines,
                    "availability_rate": recent_metrics[-1].available_engines / recent_metrics[-1].total_engines if recent_metrics[-1].total_engines > 0 else 0
                }
            }
            
        except Exception as e:
            self.logger.error(f"获取性能摘要失败: {e}")
            return {"error": str(e)}
    
    def get_change_summary(self, hours: int = 24) -> Dict[str, Any]:
        """获取配置变更摘要"""
        try:
            cutoff_time = time.time() - (hours * 3600)
            recent_changes = [c for c in self.change_history if c.timestamp >= cutoff_time]
            
            # 按类型统计
            change_counts = defaultdict(int)
            for change in recent_changes:
                change_counts[f"{change.config_type}_{change.change_type}"] += 1
            
            return {
                "time_range_hours": hours,
                "total_changes": len(recent_changes),
                "change_breakdown": dict(change_counts),
                "recent_changes": [
                    {
                        "timestamp": change.timestamp,
                        "type": f"{change.config_type}.{change.change_type}",
                        "id": change.config_id,
                        "user": change.user_id
                    }
                    for change in recent_changes[-10:]  # 最近10个变更
                ]
            }
            
        except Exception as e:
            self.logger.error(f"获取变更摘要失败: {e}")
            return {"error": str(e)}
    
    def get_health_status(self) -> Dict[str, Any]:
        """获取系统健康状态"""
        try:
            uptime = time.time() - self.stats["uptime_start"]
            
            # 基于最近的性能数据评估健康状态
            if len(self.performance_history) > 0:
                latest_metrics = self.performance_history[-1]
                
                # 健康评分 (0-100)
                health_score = 100
                
                # CPU使用率影响
                if latest_metrics.cpu_usage > 80:
                    health_score -= 20
                elif latest_metrics.cpu_usage > 60:
                    health_score -= 10
                
                # 内存使用率影响
                if latest_metrics.memory_usage > 80:
                    health_score -= 20
                elif latest_metrics.memory_usage > 60:
                    health_score -= 10
                
                # 磁盘使用率影响
                if latest_metrics.disk_usage > 90:
                    health_score -= 30
                elif latest_metrics.disk_usage > 80:
                    health_score -= 15
                
                # 引擎可用性影响
                if latest_metrics.available_engines == 0:
                    health_score -= 40
                elif latest_metrics.available_engines < latest_metrics.total_engines * 0.5:
                    health_score -= 20
                
                # 错误率影响
                if latest_metrics.error_count > 5:
                    health_score -= 15
                
                health_score = max(0, health_score)
                
                # 健康等级
                if health_score >= 90:
                    health_level = "excellent"
                elif health_score >= 70:
                    health_level = "good"
                elif health_score >= 50:
                    health_level = "fair"
                elif health_score >= 30:
                    health_level = "poor"
                else:
                    health_level = "critical"
            else:
                health_score = 50
                health_level = "unknown"
            
            return {
                "health_score": health_score,
                "health_level": health_level,
                "uptime_seconds": uptime,
                "uptime_human": str(timedelta(seconds=int(uptime))),
                "monitoring_active": self.is_monitoring,
                "last_check": self.stats["last_health_check"],
                "total_changes": self.stats["total_changes"],
                "total_errors": self.stats["total_errors"]
            }
            
        except Exception as e:
            self.logger.error(f"获取健康状态失败: {e}")
            return {"error": str(e)}
    
    def generate_diagnostic_report(self) -> List[DiagnosticResult]:
        """生成诊断报告"""
        diagnostics = []
        
        try:
            if len(self.performance_history) > 0:
                latest_metrics = self.performance_history[-1]
                
                # 检查各种问题
                if latest_metrics.cpu_usage > 90:
                    diagnostics.append(DiagnosticResult(
                        issue_type="high_cpu_usage",
                        severity="high",
                        description=f"CPU使用率过高: {latest_metrics.cpu_usage:.1f}%",
                        recommendation="考虑减少并发任务数量或优化配置参数",
                        affected_components=["performance"],
                        auto_fixable=False
                    ))
                
                if latest_metrics.memory_usage > 85:
                    diagnostics.append(DiagnosticResult(
                        issue_type="high_memory_usage",
                        severity="high",
                        description=f"内存使用率过高: {latest_metrics.memory_usage:.1f}%",
                        recommendation="清理缓存或减少缓冲区大小",
                        affected_components=["performance", "caching"],
                        auto_fixable=True
                    ))
                
                if latest_metrics.disk_usage > 90:
                    diagnostics.append(DiagnosticResult(
                        issue_type="high_disk_usage",
                        severity="critical",
                        description=f"磁盘空间不足: {latest_metrics.disk_usage:.1f}%",
                        recommendation="立即清理临时文件或增加存储空间",
                        affected_components=["storage"],
                        auto_fixable=False
                    ))
                
                if latest_metrics.available_engines == 0:
                    diagnostics.append(DiagnosticResult(
                        issue_type="no_available_engines",
                        severity="critical",
                        description="没有可用的TTS引擎",
                        recommendation="检查引擎配置和网络连接",
                        affected_components=["engines"],
                        auto_fixable=False
                    ))
                
                if latest_metrics.error_count > 10:
                    diagnostics.append(DiagnosticResult(
                        issue_type="high_error_rate",
                        severity="high",
                        description=f"错误率过高: {latest_metrics.error_count} 个错误",
                        recommendation="检查日志文件并修复配置问题",
                        affected_components=["configuration"],
                        auto_fixable=False
                    ))
            
        except Exception as e:
            self.logger.error(f"生成诊断报告失败: {e}")
        
        return diagnostics
    
    def cleanup_old_data(self, days: int = 7):
        """清理旧数据"""
        try:
            cutoff_time = time.time() - (days * 24 * 3600)
            
            # 清理性能历史
            self.performance_history = deque(
                [m for m in self.performance_history if m.timestamp >= cutoff_time],
                maxlen=1000
            )
            
            # 清理变更历史
            self.change_history = deque(
                [c for c in self.change_history if c.timestamp >= cutoff_time],
                maxlen=500
            )
            
            self.logger.info(f"清理了 {days} 天前的监控数据")
            
        except Exception as e:
            self.logger.error(f"清理旧数据失败: {e}")
