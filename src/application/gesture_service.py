"""
Gesture Service - 手势识别服务
负责协调手势识别流程
"""

import logging
from typing import Optional, List, Tuple, Callable
import numpy as np

from ..domain.gesture import (
    GestureType, GestureState, GestureEvent, 
    HandLandmarks, GestureStateMachine
)
from ..infrastructure.mediapipe_adapter import MediaPipeAdapter
from ..infrastructure.camera_adapter import SafeZone

logger = logging.getLogger(__name__)


class GestureService:
    """手势识别服务 - 协调手势识别和处理"""
    
    def __init__(self, config: dict):
        self.config = config
        
        # 初始化MediaPipe适配器
        recognition_config = config.get('recognition', {})
        self.mediapipe = MediaPipeAdapter(
            max_num_hands=recognition_config.get('max_num_hands', 2),
            min_detection_confidence=recognition_config.get('min_detection_confidence', 0.7),
            min_tracking_confidence=recognition_config.get('min_tracking_confidence', 0.5)
        )
        
        # 状态机配置
        self.mediapipe.state_machine.hold_time_ms = recognition_config.get('static_gesture_hold_time_ms', 150)
        self.mediapipe.state_machine.cooldown_ms = recognition_config.get('gesture_cooldown_ms', 700)
        
        # 安全区域
        safe_zone_config = config.get('safe_zone', {})
        self.safe_zone_enabled = safe_zone_config.get('enabled', True)
        self.safe_zone = SafeZone.from_config(safe_zone_config)
        
        # 事件回调
        self._on_gesture_callbacks: List[Callable[[GestureEvent], None]] = []
        self._on_landmarks_callbacks: List[Callable[[List[HandLandmarks]], None]] = []
        
        # 状态
        self._last_gesture: Optional[GestureType] = None
        self._last_landmarks: List[HandLandmarks] = []
        
        logger.info("手势识别服务已初始化")
    
    def process_frame(self, frame: np.ndarray) -> Tuple[List[HandLandmarks], Optional[GestureEvent]]:
        """
        处理视频帧进行手势识别
        
        Args:
            frame: RGB格式的图像帧
            
        Returns:
            (手部关键点列表, 手势事件)
        """
        # 调用MediaPipe处理
        landmarks_list, gesture_event = self.mediapipe.process_frame(frame)
        
        self._last_landmarks = landmarks_list
        
        # 检测双手比心
        if landmarks_list and len(landmarks_list) >= 2:
            if self.mediapipe.detect_double_hand_heart(landmarks_list):
                # 创建双手比心事件
                # 计算两手之间的中心点
                centers = [lm.get_palm_center() for lm in landmarks_list if lm.get_palm_center()]
                if len(centers) >= 2:
                    center_x = (centers[0][0] + centers[1][0]) / 2
                    center_y = (centers[0][1] + centers[1][1]) / 2
                    
                    gesture_event = GestureEvent(
                        gesture_type=GestureType.DOUBLE_HEART,
                        confidence=min(lm.confidence for lm in landmarks_list),
                        handedness="Both",
                        position=(center_x, center_y),
                        state=GestureState.TRIGGERED
                    )
        
        # 检查安全区域
        if gesture_event and self.safe_zone_enabled:
            if not self.safe_zone.is_inside(gesture_event.position[0], gesture_event.position[1]):
                logger.debug(f"手势 {gesture_event.gesture_type.name} 在安全区域外，忽略")
                gesture_event = None
        
        # 触发回调
        if landmarks_list:
            for callback in self._on_landmarks_callbacks:
                try:
                    callback(landmarks_list)
                except Exception as e:
                    logger.error(f"关键点回调错误: {e}")
        
        if gesture_event:
            self._last_gesture = gesture_event.gesture_type
            for callback in self._on_gesture_callbacks:
                try:
                    callback(gesture_event)
                except Exception as e:
                    logger.error(f"手势回调错误: {e}")
        
        return landmarks_list, gesture_event
    
    def on_gesture(self, callback: Callable[[GestureEvent], None]):
        """注册手势事件回调"""
        self._on_gesture_callbacks.append(callback)
    
    def on_landmarks(self, callback: Callable[[List[HandLandmarks]], None]):
        """注册关键点回调"""
        self._on_landmarks_callbacks.append(callback)
    
    def get_gesture_name(self, gesture: GestureType) -> str:
        """获取手势中文名称"""
        return self.mediapipe.get_gesture_name(gesture)
    
    def draw_landmarks(self, frame: np.ndarray) -> np.ndarray:
        """在帧上绘制手部关键点"""
        if self._last_landmarks:
            return self.mediapipe.draw_landmarks(frame, self._last_landmarks)
        return frame
    
    def set_safe_zone(self, x_min: float, x_max: float, y_min: float, y_max: float):
        """设置安全区域"""
        self.safe_zone = SafeZone(x_min, x_max, y_min, y_max)
    
    def enable_safe_zone(self, enabled: bool):
        """启用/禁用安全区域"""
        self.safe_zone_enabled = enabled
    
    def update_config(self, config: dict):
        """更新配置"""
        recognition_config = config.get('recognition', {})
        
        if 'static_gesture_hold_time_ms' in recognition_config:
            self.mediapipe.state_machine.hold_time_ms = recognition_config['static_gesture_hold_time_ms']
        
        if 'gesture_cooldown_ms' in recognition_config:
            self.mediapipe.state_machine.cooldown_ms = recognition_config['gesture_cooldown_ms']
        
        safe_zone_config = config.get('safe_zone', {})
        if safe_zone_config:
            self.safe_zone_enabled = safe_zone_config.get('enabled', True)
            self.safe_zone = SafeZone.from_config(safe_zone_config)
    
    @property
    def last_gesture(self) -> Optional[GestureType]:
        """获取最后识别的手势"""
        return self._last_gesture
    
    @property
    def last_landmarks(self) -> List[HandLandmarks]:
        """获取最后的关键点数据"""
        return self._last_landmarks
    
    def release(self):
        """释放资源"""
        self.mediapipe.release()
        self._on_gesture_callbacks.clear()
        self._on_landmarks_callbacks.clear()
        logger.info("手势识别服务已释放")
