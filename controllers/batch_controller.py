"""
批量处理控制器
"""

from typing import List, Optional, Callable
from dataclasses import dataclass
from enum import Enum
import threading
import time
from queue import Queue, Empty

from PyQt6.QtCore import QObject, pyqtSignal

from models.file_model import FileModel
from models.audio_model import AudioModel, VoiceConfig
from controllers.file_controller import FileController
from controllers.text_controller import TextController
from controllers.audio_controller import AudioController
from services.audio_converter import AudioConverter
from utils.log_manager import LogManager


class TaskStatus(Enum):
    """任务状态"""
    PENDING = "pending"
    PROCESSING = "processing"
    PAUSED = "paused"
    COMPLETED = "completed"
    FAILED = "failed"
    CANCELLED = "cancelled"


@dataclass
class BatchTask:
    """批量任务"""
    id: str
    file_path: str
    voice_config: VoiceConfig
    output_path: str
    status: TaskStatus = TaskStatus.PENDING
    progress: int = 0
    error_message: str = ""
    start_time: Optional[float] = None
    end_time: Optional[float] = None
    result: Optional[AudioModel] = None
    estimated_duration: Optional[float] = None  # 预估总时间（秒）
    estimated_remaining_time: Optional[float] = None  # 预估剩余时间（秒）


class BatchController(QObject):
    """批量处理控制器"""
    
    # 定义信号
    task_completed = pyqtSignal(object)  # 任务完成信号
    task_error = pyqtSignal(object)     # 任务错误信号
    
    def __init__(self, max_workers: int = 2, output_config=None):
        super().__init__()
        self.logger = LogManager().get_logger("BatchController")
        self.max_workers = max_workers
        self.output_config = output_config  # 输出配置
        self.tasks: List[BatchTask] = []
        self.task_queue = Queue()
        self.workers = []
        self.is_running = False
        self.is_paused = False
        
        # 控制器
        self.file_controller = FileController()
        self.text_controller = TextController()
        self.audio_controller = None  # 延迟初始化
        self.audio_converter = AudioConverter()
    
    def _ensure_audio_controller(self):
        """确保音频控制器已初始化"""
        if self.audio_controller is None:
            self.audio_controller = AudioController()
    
    def _setup_progress_timer(self):
        """设置进度监控定时器"""
        try:
            import threading
            import time
            
            def progress_monitor():
                while True:
                    try:
                        # 更新所有正在处理的任务的进度
                        for task in self.tasks:
                            if (task.status == TaskStatus.PROCESSING and 
                                task.estimated_duration and 
                                task.start_time):
                                self._update_progress_based_on_time(task)
                        
                        time.sleep(2)  # 每2秒更新一次
                    except Exception as e:
                        self.logger.error(f"进度监控错误: {e}")
                        time.sleep(5)
            
            # 启动后台监控线程
            self.progress_timer = threading.Thread(target=progress_monitor, daemon=True)
            self.progress_timer.start()
            
        except Exception as e:
            self.logger.error(f"设置进度监控定时器失败: {e}")
    
    def add_task(self, file_path: str, voice_config: VoiceConfig, output_path: str) -> str:
        """添加任务"""
        try:
            task_id = f"task_{len(self.tasks)}_{int(time.time())}"
            
            task = BatchTask(
                id=task_id,
                file_path=file_path,
                voice_config=voice_config,
                output_path=output_path
            )
            
            self.tasks.append(task)
            self.task_queue.put(task)
            
            self.logger.info(f"添加任务: {task_id}, 文件: {file_path}")
            return task_id
            
        except Exception as e:
            self.logger.error(f"添加任务失败: {e}")
            raise
    
    def remove_task(self, task_id: str) -> bool:
        """移除任务"""
        try:
            for i, task in enumerate(self.tasks):
                if task.id == task_id:
                    if task.status == TaskStatus.PROCESSING:
                        task.status = TaskStatus.CANCELLED
                        task.estimated_remaining_time = 0  # 任务取消，剩余时间为0
                    else:
                        self.tasks.pop(i)
                    self.logger.info(f"移除任务: {task_id}")
                    return True
            return False
            
        except Exception as e:
            self.logger.error(f"移除任务失败: {e}")
            return False
    
    def start_processing(self):
        """开始处理（单线程执行）"""
        try:
            if self.is_running:
                self.logger.warning("批量处理已在运行")
                return
            
            # 验证所有任务状态：只能是已完成或未开始
            if not self._validate_all_tasks_ready():
                self.logger.warning("无法开始批量处理：存在正在处理或暂停的任务")
                return False
            
            # 清空任务队列，只添加未完成的任务
            self._clear_task_queue()
            self._add_pending_tasks_to_queue()
            
            self.is_running = True
            self.is_paused = False
            
            # 启动单个工作线程（单线程执行）
            worker = threading.Thread(target=self._worker, daemon=True)
            worker.start()
            self.workers.append(worker)
            
            self.logger.info("批量处理开始，单线程执行")
            
        except Exception as e:
            self.logger.error(f"启动批量处理失败: {e}")
            self.is_running = False
    
    def _clear_task_queue(self):
        """清空任务队列"""
        try:
            # 清空队列中的所有任务
            while not self.task_queue.empty():
                try:
                    self.task_queue.get_nowait()
                except Empty:
                    break
            self.logger.debug("任务队列已清空")
        except Exception as e:
            self.logger.error(f"清空任务队列失败: {e}")
    
    def _add_pending_tasks_to_queue(self):
        """将未完成的任务添加到队列中"""
        try:
            pending_count = 0
            for task in self.tasks:
                # 只添加未完成的任务（PENDING、FAILED、CANCELLED）
                if task.status in [TaskStatus.PENDING, TaskStatus.FAILED, TaskStatus.CANCELLED]:
                    self.task_queue.put(task)
                    pending_count += 1
                    self.logger.debug(f"添加未完成任务到队列: {task.id}, 状态: {task.status.value}")
            
            self.logger.info(f"已将 {pending_count} 个未完成任务添加到队列")
            
        except Exception as e:
            self.logger.error(f"添加未完成任务到队列失败: {e}")
    
    def _validate_all_tasks_ready(self):
        """验证所有任务状态：不能有正在处理或暂停的任务"""
        try:
            for task in self.tasks:
                # 不允许 PROCESSING（正在处理）和 PAUSED（暂停）状态
                if task.status in [TaskStatus.PROCESSING, TaskStatus.PAUSED]:
                    self.logger.warning(f"任务 {task.id} 状态不允许开始处理: {task.status.value}")
                    return False
            
            self.logger.debug("所有任务状态验证通过：没有正在处理或暂停的任务")
            return True
            
        except Exception as e:
            self.logger.error(f"验证任务状态失败: {e}")
            return False
    
    def _validate_single_task_ready(self, task_id: str):
        """验证单个任务开始条件：所有任务只能是已完成或未开始"""
        try:
            # 首先验证所有任务状态
            if not self._validate_all_tasks_ready():
                return False
            
            # 验证目标任务状态
            task = self.get_task_by_id(task_id)
            if not task:
                self.logger.error(f"任务不存在: {task_id}")
                return False
            
            if task.status not in [TaskStatus.PENDING, TaskStatus.PAUSED]:
                self.logger.warning(f"任务 {task_id} 状态不允许开始: {task.status.value}")
                return False
            
            self.logger.debug(f"任务 {task_id} 开始条件验证通过")
            return True
            
        except Exception as e:
            self.logger.error(f"验证单个任务开始条件失败: {e}")
            return False
    
    def pause_processing(self):
        """暂停处理"""
        try:
            self.is_paused = True
            self.logger.info("批量处理已暂停")
            
        except Exception as e:
            self.logger.error(f"暂停批量处理失败: {e}")
    
    def resume_processing(self):
        """恢复处理"""
        try:
            self.is_paused = False
            self.logger.info("批量处理已恢复")
            
        except Exception as e:
            self.logger.error(f"恢复批量处理失败: {e}")
    
    def stop_processing(self):
        """停止处理"""
        try:
            self.is_running = False
            self.is_paused = False
            
            # 取消所有待处理的任务
            for task in self.tasks:
                if task.status == TaskStatus.PENDING:
                    task.status = TaskStatus.CANCELLED
                    task.estimated_remaining_time = 0  # 任务取消，剩余时间为0
            
            self.logger.info("批量处理已停止")
            
        except Exception as e:
            self.logger.error(f"停止批量处理失败: {e}")
    
    def _worker(self):
        """工作线程"""
        while self.is_running:
            try:
                if self.is_paused:
                    time.sleep(0.1)
                    continue
                
                try:
                    task = self.task_queue.get(timeout=1)
                except Empty:
                    continue
                
                # 跳过已取消或已完成的任务
                if task.status in [TaskStatus.CANCELLED, TaskStatus.COMPLETED]:
                    self.logger.debug(f"跳过任务 {task.id}，状态: {task.status.value}")
                    continue
                
                self._process_task(task)
                
            except Exception as e:
                self.logger.error(f"工作线程错误: {e}")
    
    def _process_task(self, task: BatchTask):
        """处理单个任务"""
        try:
            task.status = TaskStatus.PROCESSING
            task.start_time = time.time()
            task.progress = 0
            
            self.logger.info(f"开始处理任务: {task.id}")
            
            # 步骤1: 导入文件
            task.progress = 5
            file_model = self.file_controller.import_file(task.file_path)
            
            # 步骤2: 处理文本
            task.progress = 10
            processed_text = self.text_controller.process_text(file_model.content)
            
            # 步骤3: 生成预览音频（前20个字符）
            task.progress = 15
            preview_audio_path = self._generate_preview_audio(task, processed_text.cleaned_text)
            
            # 步骤4: 生成完整音频（使用时间估算更新进度）
            task.progress = 20
            full_audio_start_time = time.time()
            
            # 确保音频控制器已初始化
            self._ensure_audio_controller()
            
            # 如果有时间估算，启动进度监控
            if task.estimated_duration:
                self._start_progress_monitoring(task, full_audio_start_time)
            
            audio_model = self.audio_controller.generate_audio(
                processed_text.cleaned_text, 
                task.voice_config
            )
            
            # 停止进度监控
            if task.estimated_duration:
                self._stop_progress_monitoring(task)
            
            # 步骤5: 保存音频（根据格式决定是否需要转换）
            task.progress = 90
            self._save_audio_with_conversion(audio_model, task)
            
            # 步骤6: 清理预览文件
            task.progress = 95
            self._cleanup_preview_file(preview_audio_path)
            
            # 完成
            task.progress = 100
            task.status = TaskStatus.COMPLETED
            task.end_time = time.time()
            task.result = audio_model
            task.estimated_remaining_time = 0  # 任务完成，剩余时间为0
            
            self.logger.info(f"任务完成: {task.id}")
            
            # 发送任务完成信号（线程安全）
            self.task_completed.emit(task)
            
        except Exception as e:
            task.status = TaskStatus.FAILED
            task.error_message = str(e)
            task.end_time = time.time()
            task.estimated_remaining_time = 0  # 任务失败，剩余时间为0
            
            self.logger.error(f"任务失败: {task.id}, 错误: {e}")
            
            # 发送任务错误信号（线程安全）
            self.task_error.emit(task)
    
    def _generate_preview_audio(self, task: BatchTask, text: str) -> str:
        """生成预览音频文件并计算时间估算"""
        try:
            import os
            import time
            
            # 获取前20个字符作为预览文本
            preview_text = text[:20] if len(text) > 20 else text
            if not preview_text.strip():
                preview_text = "预览测试"
            
            # 生成预览文件名
            output_dir = os.path.dirname(task.output_path)
            output_filename = os.path.basename(task.output_path)
            name, ext = os.path.splitext(output_filename)
            preview_filename = f"{name}.tmp.wav"
            preview_path = os.path.join(output_dir, preview_filename)
            
            self.logger.info(f"生成预览音频: {preview_path}")
            self.logger.info(f"预览文本: {preview_text}")
            
            # 记录预览音频生成开始时间
            preview_start_time = time.time()
            
            # 确保音频控制器已初始化
            self._ensure_audio_controller()
            
            # 生成预览音频（总是使用WAV格式）
            import copy
            preview_voice_config = copy.deepcopy(task.voice_config)
            preview_voice_config.output_format = "wav"  # 预览音频总是使用WAV格式
            
            preview_audio = self.audio_controller.generate_audio(preview_text, preview_voice_config)
            self.audio_controller.save_audio(preview_audio, preview_path)
            
            # 记录预览音频生成结束时间
            preview_end_time = time.time()
            preview_duration = preview_end_time - preview_start_time
            
            # 计算基于预览的时间估算
            self._calculate_time_estimation(task, text, preview_text, preview_duration)
            
            self.logger.info(f"预览音频生成成功: {preview_path}, 耗时: {preview_duration:.2f}秒")
            return preview_path
            
        except Exception as e:
            self.logger.error(f"生成预览音频失败: {e}")
            # 预览失败不影响主任务，继续执行
            return ""
    
    def _calculate_time_estimation(self, task: BatchTask, full_text: str, preview_text: str, preview_duration: float):
        """基于预览音频计算时间估算"""
        try:
            # 对于Edge-TTS，使用动态时间估算规则
            if task.voice_config.engine == 'edge_tts':
                self._calculate_edge_tts_time_estimation(task, full_text)
                return
            
            # 对于EmotiVoice，使用动态时间估算规则
            if task.voice_config.engine == 'emotivoice_tts_api':
                self._calculate_emotivoice_time_estimation(task, full_text)
                return
            
            # 其他引擎使用预览音频估算
            # 计算字符比例
            preview_chars = len(preview_text)
            full_chars = len(full_text)
            
            if preview_chars == 0 or full_chars == 0:
                return
            
            # 计算每字符耗时
            time_per_char = preview_duration / preview_chars
            
            # 估算完整文本的生成时间
            estimated_full_time = time_per_char * full_chars
            
            # 添加一些缓冲时间（考虑模型加载、文件IO等固定开销）
            # 预览文本的固定开销已经在预览时间中体现，所以需要减去
            fixed_overhead = 0.5  # 假设固定开销为0.5秒
            estimated_full_time = estimated_full_time + fixed_overhead
            
            # 设置合理的时间范围
            estimated_full_time = max(10.0, min(estimated_full_time, 3600.0))  # 10秒到1小时
            
            # 将估算时间存储到任务中
            task.estimated_duration = estimated_full_time
            
            # 记录估算信息
            self.logger.info(f"时间估算完成:")
            self.logger.info(f"  预览文本: {preview_chars}字符, 耗时: {preview_duration:.2f}秒")
            self.logger.info(f"  完整文本: {full_chars}字符")
            self.logger.info(f"  每字符耗时: {time_per_char:.4f}秒")
            self.logger.info(f"  预计总时间: {estimated_full_time:.1f}秒 ({estimated_full_time/60:.1f}分钟)")
            
            # 更新任务状态信息
            task.estimated_remaining_time = estimated_full_time
            
        except Exception as e:
            self.logger.error(f"计算时间估算失败: {e}")
    
    def _calculate_edge_tts_time_estimation(self, task: BatchTask, full_text: str):
        """计算Edge-TTS的时间估算（使用动态规则）"""
        try:
            text_length = len(full_text)
            
            # Edge-TTS时间估算规则：基础时间10秒，500字符。每超过500，增加8秒
            if text_length <= 500:
                base_timeout = 10  # 基础10秒
            else:
                extra_chars = text_length - 500
                extra_time = ((extra_chars + 499) // 500) * 8  # 每500字符增加8秒
                base_timeout = 10 + extra_time
            
            # 添加一些缓冲时间（考虑网络延迟、API处理等）
            buffer_time = 3  # 3秒缓冲
            estimated_full_time = base_timeout + buffer_time
            
            # 设置合理的时间范围
            estimated_full_time = max(10.0, min(estimated_full_time, 300.0))  # 10秒到5分钟
            
            # 将估算时间存储到任务中
            task.estimated_duration = estimated_full_time
            
            # 记录估算信息
            self.logger.info(f"Edge-TTS时间估算完成:")
            self.logger.info(f"  文本长度: {text_length}字符")
            self.logger.info(f"  基础时间: {base_timeout}秒")
            self.logger.info(f"  缓冲时间: {buffer_time}秒")
            self.logger.info(f"  预计总时间: {estimated_full_time:.1f}秒 ({estimated_full_time/60:.1f}分钟)")
            
            # 更新任务状态信息
            task.estimated_remaining_time = estimated_full_time
            
        except Exception as e:
            self.logger.error(f"计算Edge-TTS时间估算失败: {e}")
    
    def _calculate_emotivoice_time_estimation(self, task: BatchTask, full_text: str):
        """计算EmotiVoice的时间估算（使用动态规则）"""
        try:
            text_length = len(full_text)
            
            # EmotiVoice时间估算规则：按200字符分割，每段12秒
            if text_length <= 200:
                # 单段文本，基础12秒
                base_timeout = 12
                segments = 1
            else:
                # 多段文本，按200字符分段计算
                segments = (text_length + 199) // 200  # 向上取整计算段数
                base_timeout = segments * 12  # 每段12秒
            
            # 添加一些缓冲时间（考虑网络延迟、API处理等）
            buffer_time = 5  # 5秒缓冲时间
            estimated_full_time = base_timeout + buffer_time
            
            # 设置合理的时间范围：最小15秒，最大10分钟
            estimated_full_time = max(15.0, min(estimated_full_time, 600.0))
            
            # 将估算时间存储到任务中
            task.estimated_duration = estimated_full_time
            
            # 记录估算信息
            self.logger.info(f"EmotiVoice时间估算完成:")
            self.logger.info(f"  文本长度: {text_length}字符")
            self.logger.info(f"  分段数量: {segments}段")
            self.logger.info(f"  基础时间: {base_timeout}秒")
            self.logger.info(f"  缓冲时间: {buffer_time}秒")
            self.logger.info(f"  预计总时间: {estimated_full_time:.1f}秒 ({estimated_full_time/60:.1f}分钟)")
            
            # 更新任务状态信息
            task.estimated_remaining_time = estimated_full_time
            
        except Exception as e:
            self.logger.error(f"计算EmotiVoice时间估算失败: {e}")
    
    def _start_progress_monitoring(self, task: BatchTask, start_time: float):
        """启动进度监控"""
        try:
            task.start_time = start_time
            self.logger.info(f"启动进度监控: 任务{task.id}, 预估时间: {task.estimated_duration:.1f}秒")
        except Exception as e:
            self.logger.error(f"启动进度监控失败: {e}")
    
    def _stop_progress_monitoring(self, task: BatchTask):
        """停止进度监控"""
        try:
            if task.start_time:
                actual_duration = time.time() - task.start_time
                self.logger.info(f"停止进度监控: 任务{task.id}, 实际耗时: {actual_duration:.1f}秒")
                
                # 更新剩余时间估算
                if task.estimated_remaining_time:
                    task.estimated_remaining_time = 0
        except Exception as e:
            self.logger.error(f"停止进度监控失败: {e}")
    
    def _update_progress_based_on_time(self, task: BatchTask):
        """基于时间更新进度"""
        try:
            if not task.start_time or not task.estimated_duration:
                return
            
            elapsed_time = time.time() - task.start_time
            progress_ratio = min(elapsed_time / task.estimated_duration, 0.95)  # 最大95%
            
            # 将时间进度映射到20-90%的进度范围（音频生成阶段）
            audio_progress = int(20 + progress_ratio * 70)  # 20%到90%
            task.progress = min(audio_progress, 90)
            
            # 更新剩余时间
            remaining_time = max(0, task.estimated_duration - elapsed_time)
            task.estimated_remaining_time = remaining_time
            
            # 记录进度更新
            if int(elapsed_time) % 5 == 0:  # 每5秒记录一次
                self.logger.info(f"进度更新: 任务{task.id}, 进度: {task.progress}%, "
                               f"已用时间: {elapsed_time:.1f}s, 剩余时间: {remaining_time:.1f}s")
            
        except Exception as e:
            self.logger.error(f"更新进度失败: {e}")
    
    def _save_audio_with_conversion(self, audio_model: AudioModel, task: BatchTask):
        """保存音频（根据格式决定是否需要转换）"""
        try:
            import os
            import shutil
            
            target_format = task.voice_config.output_format.lower()
            
            # 检测音频数据的实际格式
            actual_format = self._detect_audio_format(audio_model.audio_data)
            self.logger.info(f"音频数据实际格式: {actual_format}, 目标格式: {target_format}")
            
            # 如果实际格式与目标格式相同，直接保存
            if actual_format == target_format:
                self.logger.info(f"格式匹配，直接保存: {actual_format}")
                with open(task.output_path, 'wb') as f:
                    f.write(audio_model.audio_data)
                self.logger.info(f"音频文件已保存: {task.output_path}")
                
                # 检查并保存字幕文件
                self._save_subtitle_file_if_available(audio_model, task.output_path, self.output_config)
                return
            
            # 确保temp目录存在
            temp_dir = os.path.join(os.getcwd(), "temp")
            os.makedirs(temp_dir, exist_ok=True)
            
            # 生成临时文件路径，使用实际格式的扩展名
            output_filename = os.path.basename(task.output_path)
            name, _ = os.path.splitext(output_filename)
            temp_filename = f"{name}.{actual_format}"
            temp_file_path = os.path.join(temp_dir, temp_filename)
            
            # 保存音频数据到临时文件
            with open(temp_file_path, 'wb') as f:
                f.write(audio_model.audio_data)
            self.logger.info(f"临时{actual_format.upper()}文件已保存: {temp_file_path}")
            
            if target_format == actual_format:
                # 如果格式相同，直接复制
                shutil.copy2(temp_file_path, task.output_path)
                self.logger.info(f"{actual_format.upper()}文件已复制到输出目录: {task.output_path}")
            else:
                # 需要转换格式
                self.logger.info(f"需要转换音频格式: {actual_format.upper()} -> {target_format.upper()}")
                
                # 转换格式
                quality_params = {
                    'bitrate': task.voice_config.extra_params.get('bitrate', 128),
                    'sample_rate': task.voice_config.extra_params.get('sample_rate', 22050),
                    'channels': task.voice_config.extra_params.get('channels', 1)
                }
                
                success = self.audio_converter.convert_audio(
                    temp_file_path, 
                    task.output_path, 
                    target_format, 
                    quality_params
                )
                
                if success:
                    self.logger.info(f"音频格式转换成功: {task.output_path}")
                else:
                    raise Exception(f"音频格式转换失败: {actual_format.upper()} -> {target_format.upper()}")
            
            # 清理临时文件
            try:
                if os.path.exists(temp_file_path):
                    os.remove(temp_file_path)
                    self.logger.debug(f"已清理临时文件: {temp_file_path}")
            except Exception as e:
                self.logger.warning(f"清理临时文件失败: {e}")
                    
        except Exception as e:
            self.logger.error(f"保存音频失败: {e}")
            raise
    
    def _save_subtitle_file_if_available(self, audio_model: AudioModel, audio_file_path: str, output_config=None):
        """如果AudioModel包含字幕内容，则保存字幕文件"""
        try:
            import os
            
            # 检查AudioModel是否包含字幕内容
            if hasattr(audio_model, 'metadata') and audio_model.metadata:
                srt_content = audio_model.metadata.get('srt_content')
                if srt_content:
                    # 检查是否有输出配置来生成字幕
                    if output_config and getattr(output_config, 'generate_subtitle', False):
                        from utils.subtitle_utils import SubtitleGenerator
                        
                        # 创建字幕生成器
                        subtitle_gen = SubtitleGenerator(
                            format_type=getattr(output_config, 'subtitle_format', 'lrc'),
                            encoding=getattr(output_config, 'subtitle_encoding', 'utf-8'),
                            offset=getattr(output_config, 'subtitle_offset', 0.0)
                        )
                        
                        # 生成字幕文件
                        base_path = os.path.splitext(audio_file_path)[0]
                        subtitle_path = subtitle_gen.generate_subtitle_file(
                            srt_content, 
                            base_path,
                            getattr(output_config, 'subtitle_style', {})
                        )
                        
                        self.logger.info(f"字幕文件已保存: {subtitle_path} (格式: {getattr(output_config, 'subtitle_format', 'lrc')})")
                        return True
                    else:
                        # 默认生成SRT格式
                        base_path = os.path.splitext(audio_file_path)[0]
                        srt_path = f"{base_path}.srt"
                        
                        # 保存SRT文件
                        with open(srt_path, 'w', encoding='utf-8') as f:
                            f.write(srt_content)
                        
                        self.logger.info(f"SRT字幕文件已保存: {srt_path}")
                        return True
            
            return False
            
        except Exception as e:
            self.logger.error(f"保存字幕文件失败: {e}")
            return False
    
    def _detect_audio_format(self, audio_data: bytes) -> str:
        """检测音频数据格式"""
        try:
            if len(audio_data) < 16:
                return 'unknown'
            
            # 检查MP3格式标识
            if audio_data.startswith(b'ID3') or audio_data.startswith(b'\xff\xfb') or audio_data.startswith(b'\xff\xf3'):
                return 'mp3'
            
            # 检查WAV格式标识
            elif audio_data.startswith(b'RIFF'):
                return 'wav'
            
            # 检查OGG格式标识
            elif audio_data.startswith(b'OggS'):
                return 'ogg'
            
            # 检查M4A格式标识
            elif audio_data.startswith(b'\x00\x00\x00\x20ftypM4A'):
                return 'm4a'
            
            # 检查AAC格式标识
            elif audio_data.startswith(b'\xff\xf1') or audio_data.startswith(b'\xff\xf9'):
                return 'aac'
            
            else:
                # 记录前几个字节用于调试
                self.logger.warning(f"无法识别音频格式，前16字节: {audio_data[:16].hex()}")
                return 'unknown'
                
        except Exception as e:
            self.logger.error(f"检测音频格式失败: {e}")
            return 'unknown'
    
    def _cleanup_preview_file(self, preview_path: str):
        """清理预览文件"""
        try:
            import os
            if preview_path and os.path.exists(preview_path):
                os.remove(preview_path)
                self.logger.info(f"已清理预览文件: {preview_path}")
        except Exception as e:
            self.logger.warning(f"清理预览文件失败: {e}")
    
    def get_task_status(self, task_id: str) -> Optional[TaskStatus]:
        """获取任务状态"""
        for task in self.tasks:
            if task.id == task_id:
                return task.status
        return None
    
    def get_task_progress(self, task_id: str) -> int:
        """获取任务进度"""
        for task in self.tasks:
            if task.id == task_id:
                return task.progress
        return 0
    
    def get_all_tasks(self) -> List[BatchTask]:
        """获取所有任务"""
        return self.tasks
    
    def get_task_by_id(self, task_id: str) -> Optional[BatchTask]:
        """根据ID获取任务"""
        for task in self.tasks:
            if task.id == task_id:
                return task
        return None
    
    def update_task(self, task_id: str, updated_task: BatchTask) -> bool:
        """更新任务"""
        try:
            for i, task in enumerate(self.tasks):
                if task.id == task_id:
                    # 检查任务状态，正在处理的任务不能更新
                    if task.status == TaskStatus.PROCESSING:
                        self.logger.warning(f"无法更新正在处理的任务: {task_id}")
                        return False
                    
                    # 更新任务
                    self.tasks[i] = updated_task
                    self.logger.info(f"任务更新成功: {task_id}")
                    return True
            
            self.logger.warning(f"任务不存在: {task_id}")
            return False
            
        except Exception as e:
            self.logger.error(f"更新任务失败: {e}")
            return False
    
    def get_pending_tasks(self) -> List[BatchTask]:
        """获取待处理任务"""
        return [task for task in self.tasks if task.status == TaskStatus.PENDING]
    
    def get_processing_tasks(self) -> List[BatchTask]:
        """获取处理中任务"""
        return [task for task in self.tasks if task.status == TaskStatus.PROCESSING]
    
    def get_completed_tasks(self) -> List[BatchTask]:
        """获取已完成任务"""
        return [task for task in self.tasks if task.status == TaskStatus.COMPLETED]
    
    def get_failed_tasks(self) -> List[BatchTask]:
        """获取失败任务"""
        return [task for task in self.tasks if task.status == TaskStatus.FAILED]
    
    def get_overall_progress(self) -> dict:
        """获取总体进度"""
        try:
            total_tasks = len(self.tasks)
            if total_tasks == 0:
                return {
                    'total': 0,
                    'completed': 0,
                    'failed': 0,
                    'processing': 0,
                    'pending': 0,
                    'progress_percentage': 0
                }
            
            completed = len(self.get_completed_tasks())
            failed = len(self.get_failed_tasks())
            processing = len(self.get_processing_tasks())
            pending = len(self.get_pending_tasks())
            
            progress_percentage = int((completed + failed) / total_tasks * 100)
            
            return {
                'total': total_tasks,
                'completed': completed,
                'failed': failed,
                'processing': processing,
                'pending': pending,
                'progress_percentage': progress_percentage
            }
            
        except Exception as e:
            self.logger.error(f"获取总体进度失败: {e}")
            return {
                'total': 0,
                'completed': 0,
                'failed': 0,
                'processing': 0,
                'pending': 0,
                'progress_percentage': 0
            }
    
    def clear_completed_tasks(self):
        """清除已完成的任务"""
        try:
            self.tasks = [task for task in self.tasks if task.status != TaskStatus.COMPLETED]
            self.logger.info("已清除完成的任务")
            
        except Exception as e:
            self.logger.error(f"清除完成任务失败: {e}")
    
    def clear_all_tasks(self):
        """清除所有任务"""
        try:
            self.tasks.clear()
            self.logger.info("已清除所有任务")
            
        except Exception as e:
            self.logger.error(f"清除所有任务失败: {e}")
    
    def set_progress_callback(self, callback: Callable):
        """设置进度回调"""
        self.progress_callback = callback
    
    
    def get_processing_statistics(self) -> dict:
        """获取处理统计"""
        try:
            stats = {
                'total_tasks': len(self.tasks),
                'completed_tasks': len(self.get_completed_tasks()),
                'failed_tasks': len(self.get_failed_tasks()),
                'processing_tasks': len(self.get_processing_tasks()),
                'pending_tasks': len(self.get_pending_tasks()),
                'success_rate': 0,
                'average_processing_time': 0
            }
            
            # 计算成功率
            if stats['total_tasks'] > 0:
                stats['success_rate'] = stats['completed_tasks'] / stats['total_tasks'] * 100
            
            # 计算平均处理时间
            completed_tasks = self.get_completed_tasks()
            if completed_tasks:
                total_time = sum(
                    task.end_time - task.start_time 
                    for task in completed_tasks 
                    if task.start_time and task.end_time
                )
                stats['average_processing_time'] = total_time / len(completed_tasks)
            
            return stats
            
        except Exception as e:
            self.logger.error(f"获取处理统计失败: {e}")
            return {}
    
    def start_single_task(self, task_id: str) -> bool:
        """开始单个任务"""
        try:
            # 获取任务对象
            task = self.get_task_by_id(task_id)
            if not task:
                self.logger.error(f"任务不存在: {task_id}")
                return False
            
            # 验证所有任务状态：只能是已完成或未开始
            if not self._validate_single_task_ready(task_id):
                self.logger.warning(f"无法开始单个任务 {task_id}：存在正在处理或暂停的任务，或目标任务状态不允许")
                return False
            
            # 在单独线程中处理任务
            import threading
            task_thread = threading.Thread(
                target=self._process_single_task,
                args=(task,),
                daemon=True
            )
            task_thread.start()
            
            self.logger.info(f"开始处理单个任务: {task_id}")
            return True
            
        except Exception as e:
            self.logger.error(f"开始单个任务失败: {e}")
            return False
    
    def pause_single_task(self, task_id: str) -> bool:
        """暂停单个任务"""
        try:
            task = self.get_task_by_id(task_id)
            if not task:
                self.logger.error(f"任务不存在: {task_id}")
                return False
            
            if task.status != TaskStatus.PROCESSING:
                self.logger.warning(f"任务状态不允许暂停: {task_id}, 状态: {task.status}")
                return False
            
            # 设置任务状态为暂停
            task.status = TaskStatus.PAUSED
            task.estimated_remaining_time = 0  # 暂停时剩余时间为0
            
            self.logger.info(f"暂停单个任务: {task_id}")
            return True
            
        except Exception as e:
            self.logger.error(f"暂停单个任务失败: {e}")
            return False
    
    def stop_single_task(self, task_id: str) -> bool:
        """停止单个任务"""
        try:
            task = self.get_task_by_id(task_id)
            if not task:
                self.logger.error(f"任务不存在: {task_id}")
                return False
            
            if task.status not in [TaskStatus.PROCESSING, TaskStatus.PAUSED]:
                self.logger.warning(f"任务状态不允许停止: {task_id}, 状态: {task.status}")
                return False
            
            # 设置任务状态为取消
            task.status = TaskStatus.CANCELLED
            task.end_time = time.time()
            task.estimated_remaining_time = 0  # 停止时剩余时间为0
            
            self.logger.info(f"停止单个任务: {task_id}")
            return True
            
        except Exception as e:
            self.logger.error(f"停止单个任务失败: {e}")
            return False
    
    def _process_single_task(self, task: BatchTask):
        """在单独线程中处理单个任务"""
        try:
            # 直接调用现有的任务处理方法
            self._process_task(task)
        except Exception as e:
            self.logger.error(f"处理单个任务失败: {e}")
            task.status = TaskStatus.FAILED
            task.error_message = str(e)
            task.end_time = time.time()
            task.estimated_remaining_time = 0
