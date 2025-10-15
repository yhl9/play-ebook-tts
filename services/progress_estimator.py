#!/usr/bin/env python3
"""
进度估算服务
为IndexTTS API调用提供基于时间估算的进度条功能
"""

import time
import math
import threading
from typing import Dict, Any, Optional
from PyQt6.QtCore import QObject, pyqtSignal, QTimer, QMetaObject, Qt
from utils.log_manager import LogManager


class ProgressEstimator(QObject):
    """进度估算器"""
    
    # 信号定义
    progress_updated = pyqtSignal(int)  # 进度百分比 (0-100)
    status_updated = pyqtSignal(str)   # 状态信息
    phase_changed = pyqtSignal(str)    # 阶段变化
    
    def __init__(self):
        super().__init__()
        self.logger = LogManager().get_logger("ProgressEstimator")
        
        # 进度状态
        self.current_progress = 0
        self.current_phase = "准备中"
        self.is_running = False
        self.start_time = None
        self.estimated_total_time = 0
        
        # 多文件进度状态
        self.total_files = 1
        self.completed_files = 0
        self.file_estimated_times = []  # 每个文件的估算时间
        self.file_actual_times = []     # 每个文件的实际时间
        self.current_file_start_time = None
        
        # 线程安全锁
        self._lock = threading.Lock()
        
        # 定时器
        self.timer = QTimer()
        self.timer.timeout.connect(self._update_progress)
        
        # 阶段配置
        self.phases = {
            "准备中": {"duration_ratio": 0.05, "description": "准备API请求"},
            "连接中": {"duration_ratio": 0.10, "description": "建立API连接"},
            "处理中": {"duration_ratio": 0.75, "description": "AI语音合成处理"},
            "完成中": {"duration_ratio": 0.10, "description": "保存音频文件"}
        }
        
        # 历史数据（用于优化估算）
        self.history_data = []
        self.max_history = 50  # 保留最近50次的历史数据
    
    def start_estimation(self, text_length: int, text_complexity: float = 1.0, 
                        api_url: str = "", engine: str = "index_tts_api_15", 
                        total_files: int = 1, file_text_lengths: list = None):
        """开始进度估算"""
        try:
            self.logger.info(f"开始进度估算: 文本长度={text_length}, 复杂度={text_complexity}, 文件数={total_files}")
            
            # 设置多文件状态
            self.total_files = total_files
            self.completed_files = 0
            self.file_estimated_times = []
            self.file_actual_times = []
            
            # 计算每个文件的估算时间
            if file_text_lengths and len(file_text_lengths) > 0:
                # 多文件模式：为每个文件计算估算时间
                for i, file_length in enumerate(file_text_lengths):
                    file_complexity = TextComplexityAnalyzer.analyze_complexity("测试文本" * (file_length // 4))
                    file_estimated_time = self._calculate_estimated_time(file_length, file_complexity, engine)
                    self.file_estimated_times.append(file_estimated_time)
                    self.logger.info(f"文件{i+1}: 长度={file_length}, 估算时间={file_estimated_time:.1f}秒")
                
                # 总估算时间
                self.estimated_total_time = sum(self.file_estimated_times)
            else:
                # 单文件模式：使用原有逻辑
                self.estimated_total_time = self._calculate_estimated_time(
                    text_length, text_complexity, engine
                )
                self.file_estimated_times = [self.estimated_total_time]
            
            # 重置状态
            self.current_progress = 0
            self.current_phase = "准备中"
            self.is_running = True
            self.start_time = time.time()
            self.current_file_start_time = None
            
            # 发送初始信号
            self.progress_updated.emit(0)
            self.status_updated.emit("开始处理...")
            self.phase_changed.emit("准备中")
            
            # 启动定时器（每100ms更新一次）
            self.timer.start(100)
            
            self.logger.info(f"进度估算启动: 预计总时间={self.estimated_total_time:.1f}秒")
            
        except Exception as e:
            self.logger.error(f"启动进度估算失败: {e}")
    
    def stop_estimation(self, success: bool = True):
        """停止进度估算"""
        try:
            with self._lock:
                self.is_running = False
                
                # 在主线程中停止定时器
                if QMetaObject.invokeMethod(self.timer, "stop", Qt.ConnectionType.QueuedConnection):
                    pass
                else:
                    self.timer.stop()
            
            if success:
                self.current_progress = 100
                self.current_phase = "完成"
                self.progress_updated.emit(100)
                self.status_updated.emit("处理完成")
                self.phase_changed.emit("完成")
                
                # 记录历史数据
                if self.start_time:
                    actual_time = time.time() - self.start_time
                    self._record_history_data(actual_time)
            else:
                self.status_updated.emit("处理失败")
                self.phase_changed.emit("失败")
            
            self.logger.info(f"进度估算停止: 成功={success}")
            
        except Exception as e:
            self.logger.error(f"停止进度估算失败: {e}")
    
    def on_file_completed(self, file_index: int, actual_time: float = None):
        """文件完成回调"""
        try:
            if file_index < 0 or file_index >= self.total_files:
                return
            
            # 记录实际时间
            if actual_time is not None:
                self.file_actual_times.append(actual_time)
            elif self.current_file_start_time:
                actual_time = time.time() - self.current_file_start_time
                self.file_actual_times.append(actual_time)
            
            # 更新完成文件数
            self.completed_files = file_index + 1
            
            # 重新计算剩余时间
            if self.completed_files < self.total_files:
                # 计算已完成文件的实际时间总和
                completed_actual_time = sum(self.file_actual_times) if self.file_actual_times else 0
                
                # 计算剩余文件的估算时间
                remaining_estimated_time = sum(self.file_estimated_times[self.completed_files:])
                
                # 根据实际完成情况调整剩余时间估算
                if self.file_actual_times and len(self.file_actual_times) > 0:
                    # 计算实际时间与估算时间的比例
                    actual_ratio = sum(self.file_actual_times) / sum(self.file_estimated_times[:len(self.file_actual_times)])
                    # 调整剩余时间
                    remaining_estimated_time *= actual_ratio
                
                # 更新总估算时间
                self.estimated_total_time = completed_actual_time + remaining_estimated_time
                
                self.logger.info(f"文件{file_index + 1}完成: 实际时间={actual_time:.1f}s, "
                               f"已完成={self.completed_files}/{self.total_files}, "
                               f"剩余估算={remaining_estimated_time:.1f}s")
            
            # 重置当前文件开始时间
            self.current_file_start_time = None
            
        except Exception as e:
            self.logger.error(f"处理文件完成回调失败: {e}")
    
    def start_file_processing(self, file_index: int):
        """开始处理文件"""
        try:
            self.current_file_start_time = time.time()
            self.logger.debug(f"开始处理文件{file_index + 1}")
        except Exception as e:
            self.logger.error(f"开始文件处理失败: {e}")
    
    def _calculate_estimated_time(self, text_length: int, text_complexity: float, 
                                 engine: str) -> float:
        """计算估算时间（参照timeout计算方法）"""
        try:
            # 参照IndexTTS API的timeout计算方法
            if text_length <= 1000:
                # 1000字符以内，使用4分钟作为基础时间
                base_timeout = 240  # 4分钟
            else:
                # 超过1000字符，每100字符增加30秒
                extra_chars = text_length - 1000
                # 使用向上取整，确保每100字符增加30秒
                extra_time = ((extra_chars + 99) // 100) * 30
                base_timeout = 240 + extra_time
            
            # 根据引擎调整（基于实际处理时间）
            engine_factor = 1.0
            if engine == "index_tts_api_15":
                engine_factor = 1.0  # 使用timeout作为基准
            elif engine == "emotivoice_tts_api":
                # EmotiVoice: 按200字符分段，每段12秒
                if text_length <= 200:
                    engine_factor = 0.05  # 12秒/240秒 = 0.05
                else:
                    segments = (text_length + 199) // 200
                    emotivoice_time = segments * 12
                    engine_factor = emotivoice_time / base_timeout
            elif engine == "edge_tts":
                # Edge-TTS: 基础时间8秒，500字符。每超过500，增加7秒
                if text_length <= 500:
                    edge_tts_time = 8
                else:
                    extra_chars = text_length - 500
                    extra_time = ((extra_chars + 499) // 500) * 7
                    edge_tts_time = 8 + extra_time
                engine_factor = edge_tts_time / base_timeout
            elif engine == "pyttsx3":
                engine_factor = 0.1  # 本地引擎最快
            
            # 根据文本复杂度调整
            complexity_factor = 0.8 + (text_complexity - 1.0) * 0.4  # 0.8-1.2倍
            complexity_factor = max(0.5, min(complexity_factor, 2.0))  # 限制在0.5-2.0倍
            
            # 计算估算时间
            estimated_time = base_timeout * engine_factor * complexity_factor
            
            # 应用历史数据调整
            if self.history_data:
                avg_ratio = sum(data['ratio'] for data in self.history_data[-10:]) / min(10, len(self.history_data))
                estimated_time *= avg_ratio
            
            # 设置合理的时间范围
            estimated_time = max(10.0, min(estimated_time, 600.0))  # 10秒到10分钟
            
            self.logger.info(f"时间估算: 文本长度={text_length}, timeout基准={base_timeout}s, "
                           f"引擎因子={engine_factor:.2f}, 复杂度因子={complexity_factor:.2f}, "
                           f"最终={estimated_time:.1f}s")
            
            return estimated_time
            
        except Exception as e:
            self.logger.error(f"计算估算时间失败: {e}")
            return 60.0  # 默认60秒
    
    def _update_progress(self):
        """更新进度"""
        try:
            if not self.is_running or not self.start_time:
                return
            
            elapsed_time = time.time() - self.start_time
            
            # 多文件进度计算
            if self.total_files > 1:
                # 计算已完成文件的进度
                completed_progress = (self.completed_files / self.total_files) * 100
                
                # 计算当前文件的进度
                if self.completed_files < self.total_files and self.current_file_start_time:
                    current_file_elapsed = time.time() - self.current_file_start_time
                    current_file_estimated = self.file_estimated_times[self.completed_files]
                    current_file_progress = min(current_file_elapsed / current_file_estimated, 0.95)  # 最大95%
                    current_file_contribution = (1.0 / self.total_files) * current_file_progress * 100
                    total_progress = completed_progress + current_file_contribution
                else:
                    total_progress = completed_progress
                
                self.current_progress = min(int(total_progress), 100)
                
                # 计算剩余时间
                if self.completed_files < self.total_files:
                    # 已完成文件的实际时间
                    completed_actual_time = sum(self.file_actual_times) if self.file_actual_times else 0
                    
                    # 当前文件的剩余时间
                    current_file_remaining = 0
                    if self.current_file_start_time and self.completed_files < self.total_files:
                        current_file_elapsed = time.time() - self.current_file_start_time
                        current_file_estimated = self.file_estimated_times[self.completed_files]
                        current_file_remaining = max(0, current_file_estimated - current_file_elapsed)
                    
                    # 剩余文件的估算时间
                    remaining_files_estimated = sum(self.file_estimated_times[self.completed_files + 1:])
                    
                    # 根据实际完成情况调整剩余时间
                    if self.file_actual_times and len(self.file_actual_times) > 0:
                        actual_ratio = sum(self.file_actual_times) / sum(self.file_estimated_times[:len(self.file_actual_times)])
                        remaining_files_estimated *= actual_ratio
                    
                    remaining_time = current_file_remaining + remaining_files_estimated
                else:
                    remaining_time = 0
                
                status_text = f"{self.current_phase} - 文件 {self.completed_files}/{self.total_files} - 预计剩余: {remaining_time:.0f}秒"
                
            else:
                # 单文件进度计算（原有逻辑）
                progress_ratio = min(elapsed_time / self.estimated_total_time, 1.0)
                current_phase_progress = self._calculate_phase_progress(progress_ratio)
                
                # 单个文件在95%后不再增长
                if current_phase_progress >= 95:
                    self.current_progress = 95
                else:
                    self.current_progress = current_phase_progress
                
                remaining_time = max(0, self.estimated_total_time - elapsed_time)
                status_text = f"{self.current_phase} - 预计剩余: {remaining_time:.0f}秒"
            
            # 更新进度
            self.progress_updated.emit(self.current_progress)
            self.status_updated.emit(status_text)
            
            # 检查是否超时
            if elapsed_time > self.estimated_total_time * 1.5:  # 超时50%
                self.logger.warning("进度估算超时，可能需要更长时间")
                self.status_updated.emit(f"{self.current_phase} - 处理时间较长，请耐心等待...")
            
        except Exception as e:
            self.logger.error(f"更新进度失败: {e}")
    
    def _calculate_phase_progress(self, progress_ratio: float) -> int:
        """根据进度比例计算当前阶段和进度"""
        try:
            cumulative_ratio = 0.0
            current_phase = "准备中"
            
            for phase_name, phase_info in self.phases.items():
                phase_duration = phase_info["duration_ratio"]
                
                if progress_ratio <= cumulative_ratio + phase_duration:
                    # 当前阶段
                    phase_progress = (progress_ratio - cumulative_ratio) / phase_duration
                    phase_progress = max(0, min(1, phase_progress))
                    
                    # 计算总体进度
                    total_progress = int((cumulative_ratio + phase_progress * phase_duration) * 100)
                    
                    # 更新阶段
                    if current_phase != phase_name:
                        current_phase = phase_name
                        self.current_phase = phase_name
                        self.phase_changed.emit(phase_name)
                        self.logger.info(f"进入阶段: {phase_name}")
                    
                    return total_progress
                
                cumulative_ratio += phase_duration
            
            # 如果超出所有阶段，返回100%
            return 100
            
        except Exception as e:
            self.logger.error(f"计算阶段进度失败: {e}")
            return min(int(progress_ratio * 100), 100)
    
    def _record_history_data(self, actual_time: float):
        """记录历史数据"""
        try:
            if self.estimated_total_time > 0:
                ratio = actual_time / self.estimated_total_time
                
                history_entry = {
                    'estimated_time': self.estimated_total_time,
                    'actual_time': actual_time,
                    'ratio': ratio,
                    'timestamp': time.time()
                }
                
                self.history_data.append(history_entry)
                
                # 保持历史数据在合理范围内
                if len(self.history_data) > self.max_history:
                    self.history_data = self.history_data[-self.max_history:]
                
                self.logger.info(f"记录历史数据: 估算={self.estimated_total_time:.1f}s, "
                               f"实际={actual_time:.1f}s, 比例={ratio:.2f}")
                
        except Exception as e:
            self.logger.error(f"记录历史数据失败: {e}")
    
    def get_estimated_remaining_time(self) -> float:
        """获取估算剩余时间"""
        if not self.is_running or not self.start_time:
            return 0.0
        
        elapsed_time = time.time() - self.start_time
        return max(0, self.estimated_total_time - elapsed_time)
    
    def get_current_phase(self) -> str:
        """获取当前阶段"""
        return self.current_phase
    
    def get_progress_percentage(self) -> int:
        """获取当前进度百分比"""
        return self.current_progress


class TextComplexityAnalyzer:
    """文本复杂度分析器"""
    
    @staticmethod
    def analyze_complexity(text: str) -> float:
        """分析文本复杂度"""
        try:
            if not text:
                return 1.0
            
            complexity = 1.0
            
            # 长度因子
            length_factor = min(len(text) / 1000, 3.0)  # 最大3倍
            complexity *= (1.0 + length_factor * 0.5)
            
            # 中文字符比例
            chinese_chars = sum(1 for char in text if '\u4e00' <= char <= '\u9fff')
            chinese_ratio = chinese_chars / len(text) if text else 0
            if chinese_ratio > 0.5:
                complexity *= 1.2  # 中文处理相对复杂
            
            # 标点符号密度
            punctuation_count = sum(1 for char in text if char in '.,!?;:()（）【】《》""''""''')
            punctuation_density = punctuation_count / len(text) if text else 0
            if punctuation_density > 0.1:
                complexity *= 1.1  # 标点符号多，处理复杂
            
            # 数字和特殊字符
            special_chars = sum(1 for char in text if char.isdigit() or not char.isalnum())
            special_ratio = special_chars / len(text) if text else 0
            if special_ratio > 0.2:
                complexity *= 1.15  # 特殊字符多，处理复杂
            
            # 段落数量
            paragraphs = len([p for p in text.split('\n\n') if p.strip()])
            if paragraphs > 5:
                complexity *= 1.1  # 段落多，处理复杂
            
            return max(0.5, min(complexity, 3.0))  # 限制在0.5-3.0之间
            
        except Exception as e:
            return 1.0
