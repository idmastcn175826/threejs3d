"""
Orchestrator - 核心调度器
负责协调所有模块，管理系统生命周期和数据流
"""

import logging
import threading
import time
import queue
from typing import Optional, Callable
from enum import Enum, auto

import numpy as np

from .config_manager import ConfigManager
from .gesture_service import GestureService
from .action_service import ActionService
from ..infrastructure.camera_adapter import CameraAdapter, CameraConfig
from ..domain.gesture import GestureEvent, GestureType

logger = logging.getLogger(__name__)


class SystemState(Enum):
    """系统状态"""
    STOPPED = auto()
    STARTING = auto()
    RUNNING = auto()
    PAUSED = auto()
    STOPPING = auto()
    ERROR = auto()


class Orchestrator:
    """核心调度器 - 管理整个系统的运行"""
    
    def __init__(self, config_dir: str = "config"):
        # 配置管理
        self.config_manager = ConfigManager(config_dir)
        self.config_manager.load_all()
        
        # 系统状态
        self.state = SystemState.STOPPED
        self._lock = threading.Lock()
        
        # 组件
        self.camera: Optional[CameraAdapter] = None
        self.gesture_service: Optional[GestureService] = None
        self.action_service: Optional[ActionService] = None
        
        # 线程
        self._capture_thread: Optional[threading.Thread] = None
        self._process_thread: Optional[threading.Thread] = None
        self._running = False
        
        # 帧队列
        self._frame_queue: queue.Queue = queue.Queue(maxsize=2)
        self._result_queue: queue.Queue = queue.Queue(maxsize=10)
        
        # 性能统计
        self._fps_counter = FPSCounter()
        self._last_frame_time = time.time()
        
        # 回调
        self._on_frame_callbacks: list = []
        self._on_gesture_callbacks: list = []
        self._on_state_change_callbacks: list = []
        
        logger.info("调度器已初始化")
    
    def start(self) -> bool:
        """启动系统"""
        with self._lock:
            if self.state != SystemState.STOPPED:
                logger.warning(f"无法启动，当前状态: {self.state}")
                return False
            
            self._set_state(SystemState.STARTING)
        
        try:
            # 初始化摄像头
            camera_config = CameraConfig.from_dict(self.config_manager.get_camera_config())
            self.camera = CameraAdapter(camera_config)
            
            if not self.camera.start():
                raise RuntimeError("摄像头启动失败")
            
            # 初始化手势服务
            self.gesture_service = GestureService(self.config_manager.settings)
            
            # 初始化动作服务
            action_config = {
                'gesture_mappings': self.config_manager.get_gesture_mappings(),
                'effects': self.config_manager.effects
            }
            self.action_service = ActionService(action_config)
            
            # 连接手势服务和动作服务
            self.gesture_service.on_gesture(self._handle_gesture)
            
            # 启动处理线程
            self._running = True
            
            self._capture_thread = threading.Thread(target=self._capture_loop, daemon=True)
            self._capture_thread.start()
            
            self._process_thread = threading.Thread(target=self._process_loop, daemon=True)
            self._process_thread.start()
            
            self._set_state(SystemState.RUNNING)
            logger.info("系统已启动")
            return True
            
        except Exception as e:
            logger.error(f"启动失败: {e}")
            self._set_state(SystemState.ERROR)
            self.stop()
            return False
    
    def stop(self):
        """停止系统"""
        with self._lock:
            if self.state == SystemState.STOPPED:
                return
            
            self._set_state(SystemState.STOPPING)
        
        self._running = False
        
        # 等待线程结束
        if self._capture_thread and self._capture_thread.is_alive():
            self._capture_thread.join(timeout=2)
        
        if self._process_thread and self._process_thread.is_alive():
            self._process_thread.join(timeout=2)
        
        # 释放资源
        if self.camera:
            self.camera.stop()
            self.camera = None
        
        if self.gesture_service:
            self.gesture_service.release()
            self.gesture_service = None
        
        if self.action_service:
            self.action_service.clear_effects()
            self.action_service = None
        
        # 清空队列
        while not self._frame_queue.empty():
            try:
                self._frame_queue.get_nowait()
            except queue.Empty:
                break
        
        self._set_state(SystemState.STOPPED)
        logger.info("系统已停止")
    
    def pause(self):
        """暂停系统"""
        with self._lock:
            if self.state == SystemState.RUNNING:
                self._set_state(SystemState.PAUSED)
                logger.info("系统已暂停")
    
    def resume(self):
        """恢复系统"""
        with self._lock:
            if self.state == SystemState.PAUSED:
                self._set_state(SystemState.RUNNING)
                logger.info("系统已恢复")
    
    def _capture_loop(self):
        """摄像头采集循环"""
        logger.info("采集线程已启动")
        
        while self._running:
            if self.state == SystemState.PAUSED:
                time.sleep(0.1)
                continue
            
            try:
                frame = self.camera.get_frame()
                if frame is not None:
                    # 预处理
                    frame_rgb = self.camera.preprocess_for_detection(frame)
                    
                    # 放入队列（非阻塞，丢弃旧帧）
                    try:
                        self._frame_queue.put_nowait((frame, frame_rgb))
                    except queue.Full:
                        try:
                            self._frame_queue.get_nowait()
                            self._frame_queue.put_nowait((frame, frame_rgb))
                        except queue.Empty:
                            pass
            except Exception as e:
                logger.error(f"采集错误: {e}")
            
            # 控制帧率
            time.sleep(0.001)
        
        logger.info("采集线程已停止")
    
    def _process_loop(self):
        """处理循环"""
        logger.info("处理线程已启动")
        
        while self._running:
            if self.state == SystemState.PAUSED:
                time.sleep(0.1)
                continue
            
            try:
                # 获取帧
                try:
                    frame, frame_rgb = self._frame_queue.get(timeout=0.1)
                except queue.Empty:
                    continue
                
                # 更新时间
                current_time = time.time()
                dt = current_time - self._last_frame_time
                self._last_frame_time = current_time
                
                # 手势识别
                landmarks, gesture_event = self.gesture_service.process_frame(frame_rgb)
                
                # 更新特效
                self.action_service.update_effect(dt)
                
                # 绘制骨架
                if self.config_manager.get_display_config().get('show_skeleton', True):
                    frame = self.gesture_service.draw_landmarks(frame)
                
                # 渲染特效
                frame = self.action_service.render_effects(frame)
                
                # 更新FPS
                self._fps_counter.update()
                
                # 放入结果队列
                result = {
                    'frame': frame,
                    'landmarks': landmarks,
                    'gesture_event': gesture_event,
                    'fps': self._fps_counter.fps
                }
                
                try:
                    self._result_queue.put_nowait(result)
                except queue.Full:
                    try:
                        self._result_queue.get_nowait()
                        self._result_queue.put_nowait(result)
                    except queue.Empty:
                        pass
                
                # 触发帧回调
                for callback in self._on_frame_callbacks:
                    try:
                        callback(result)
                    except Exception as e:
                        logger.error(f"帧回调错误: {e}")
                
            except Exception as e:
                logger.error(f"处理错误: {e}")
        
        logger.info("处理线程已停止")
    
    def _handle_gesture(self, event: GestureEvent):
        """处理手势事件"""
        # 执行动作
        result = self.action_service.handle_gesture(event)
        
        # 触发回调
        for callback in self._on_gesture_callbacks:
            try:
                callback(event, result)
            except Exception as e:
                logger.error(f"手势回调错误: {e}")
    
    def _set_state(self, state: SystemState):
        """设置系统状态"""
        old_state = self.state
        self.state = state
        
        for callback in self._on_state_change_callbacks:
            try:
                callback(old_state, state)
            except Exception as e:
                logger.error(f"状态变更回调错误: {e}")
    
    def get_latest_result(self) -> Optional[dict]:
        """获取最新处理结果"""
        try:
            return self._result_queue.get_nowait()
        except queue.Empty:
            return None
    
    def on_frame(self, callback: Callable[[dict], None]):
        """注册帧处理回调"""
        self._on_frame_callbacks.append(callback)
    
    def on_gesture(self, callback: Callable[[GestureEvent, any], None]):
        """注册手势回调"""
        self._on_gesture_callbacks.append(callback)
    
    def on_state_change(self, callback: Callable[[SystemState, SystemState], None]):
        """注册状态变更回调"""
        self._on_state_change_callbacks.append(callback)
    
    def trigger_effect(self, effect_name: str, position: tuple = (0.5, 0.5)):
        """手动触发特效"""
        if self.action_service:
            self.action_service.trigger_effect_manually(effect_name, position)
    
    def save_config(self):
        """保存配置"""
        self.config_manager.save_all()
    
    def reload_config(self):
        """重新加载配置"""
        self.config_manager.load_all()
        
        # 更新服务配置
        if self.gesture_service:
            self.gesture_service.update_config(self.config_manager.settings)
    
    @property
    def fps(self) -> float:
        """获取当前FPS"""
        return self._fps_counter.fps
    
    @property
    def is_running(self) -> bool:
        """是否正在运行"""
        return self.state == SystemState.RUNNING


class FPSCounter:
    """FPS计数器"""
    
    def __init__(self, window_size: int = 30):
        self.window_size = window_size
        self._timestamps: list = []
        self._fps = 0.0
    
    def update(self):
        """更新计数"""
        current_time = time.time()
        self._timestamps.append(current_time)
        
        # 保持窗口大小
        if len(self._timestamps) > self.window_size:
            self._timestamps.pop(0)
        
        # 计算FPS
        if len(self._timestamps) >= 2:
            elapsed = self._timestamps[-1] - self._timestamps[0]
            if elapsed > 0:
                self._fps = (len(self._timestamps) - 1) / elapsed
    
    @property
    def fps(self) -> float:
        return self._fps
