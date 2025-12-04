"""
Gesture Domain Model - 手势领域模型
定义手势类型、状态、事件和关键点
"""

from dataclasses import dataclass, field
from enum import Enum, auto
from typing import Optional, Tuple, List
import time


class GestureType(Enum):
    """手势类型枚举"""
    UNKNOWN = auto()
    # 静态手势
    ONE_FINGER = auto()      # 单指
    TWO_FINGERS = auto()     # 双指
    THREE_FINGERS = auto()   # 三指
    FOUR_FINGERS = auto()    # 四指
    FIVE_FINGERS = auto()    # 五指张开
    FIST = auto()            # 握拳
    OK = auto()              # OK手势
    THUMBS_UP = auto()       # 点赞
    THUMBS_DOWN = auto()     # 踩
    HEART = auto()           # 比心（单手）
    DOUBLE_HEART = auto()    # 双手比心
    ROCK = auto()            # 摇滚手势
    # 动态手势
    SWIPE_LEFT = auto()      # 左划
    SWIPE_RIGHT = auto()     # 右划
    SWIPE_UP = auto()        # 上划
    SWIPE_DOWN = auto()      # 下划
    PUSH = auto()            # 推
    PULL = auto()            # 拉
    CIRCLE = auto()          # 画圈
    DOUBLE_TAP = auto()      # 双击


class GestureState(Enum):
    """手势状态机状态"""
    IDLE = auto()            # 空闲状态
    DETECTED = auto()        # 检测到手势
    HOLDING = auto()         # 保持中（等待确认）
    TRIGGERED = auto()       # 已触发
    COOLDOWN = auto()        # 冷却中


@dataclass
class HandLandmarks:
    """手部21个关键点数据"""
    # MediaPipe Hands 21个关键点索引
    WRIST = 0
    THUMB_CMC = 1
    THUMB_MCP = 2
    THUMB_IP = 3
    THUMB_TIP = 4
    INDEX_FINGER_MCP = 5
    INDEX_FINGER_PIP = 6
    INDEX_FINGER_DIP = 7
    INDEX_FINGER_TIP = 8
    MIDDLE_FINGER_MCP = 9
    MIDDLE_FINGER_PIP = 10
    MIDDLE_FINGER_DIP = 11
    MIDDLE_FINGER_TIP = 12
    RING_FINGER_MCP = 13
    RING_FINGER_PIP = 14
    RING_FINGER_DIP = 15
    RING_FINGER_TIP = 16
    PINKY_MCP = 17
    PINKY_PIP = 18
    PINKY_DIP = 19
    PINKY_TIP = 20
    
    landmarks: List[Tuple[float, float, float]] = field(default_factory=list)
    handedness: str = "Right"  # "Left" or "Right"
    confidence: float = 0.0
    
    def get_landmark(self, index: int) -> Optional[Tuple[float, float, float]]:
        """获取指定索引的关键点坐标 (x, y, z)"""
        if 0 <= index < len(self.landmarks):
            return self.landmarks[index]
        return None
    
    def get_fingertips(self) -> List[Tuple[float, float, float]]:
        """获取所有指尖坐标"""
        tips = [4, 8, 12, 16, 20]  # 拇指、食指、中指、无名指、小指指尖
        return [self.landmarks[i] for i in tips if i < len(self.landmarks)]
    
    def get_palm_center(self) -> Optional[Tuple[float, float, float]]:
        """计算手掌中心位置"""
        if len(self.landmarks) < 21:
            return None
        # 使用手腕和中指MCP的中点作为手掌中心
        wrist = self.landmarks[0]
        middle_mcp = self.landmarks[9]
        return (
            (wrist[0] + middle_mcp[0]) / 2,
            (wrist[1] + middle_mcp[1]) / 2,
            (wrist[2] + middle_mcp[2]) / 2
        )
    
    def is_finger_extended(self, finger_index: int) -> bool:
        """
        判断手指是否伸展
        finger_index: 0=拇指, 1=食指, 2=中指, 3=无名指, 4=小指
        """
        if len(self.landmarks) < 21:
            return False
        
        # 各手指关键点索引
        finger_landmarks = {
            0: (1, 2, 3, 4),     # 拇指: CMC, MCP, IP, TIP
            1: (5, 6, 7, 8),     # 食指: MCP, PIP, DIP, TIP
            2: (9, 10, 11, 12),  # 中指
            3: (13, 14, 15, 16), # 无名指
            4: (17, 18, 19, 20)  # 小指
        }
        
        if finger_index not in finger_landmarks:
            return False
        
        indices = finger_landmarks[finger_index]
        
        if finger_index == 0:  # 拇指使用特殊逻辑
            # 比较拇指尖与拇指IP的x坐标距离
            tip = self.landmarks[indices[3]]
            ip = self.landmarks[indices[2]]
            mcp = self.landmarks[indices[1]]
            # 根据左右手判断方向
            if self.handedness == "Right":
                return tip[0] < ip[0]
            else:
                return tip[0] > ip[0]
        else:
            # 其他手指：指尖y坐标小于PIP关节（屏幕坐标系y向下）
            tip = self.landmarks[indices[3]]
            pip = self.landmarks[indices[1]]
            return tip[1] < pip[1]


@dataclass
class GestureEvent:
    """手势事件"""
    gesture_type: GestureType
    confidence: float
    handedness: str  # "Left", "Right", "Both"
    position: Tuple[float, float]  # 归一化坐标 (0-1)
    screen_position: Tuple[int, int] = (0, 0)  # 屏幕像素坐标
    timestamp: float = field(default_factory=time.time)
    state: GestureState = GestureState.DETECTED
    landmarks: Optional[HandLandmarks] = None
    
    def to_dict(self) -> dict:
        """转换为字典"""
        return {
            'gesture_type': self.gesture_type.name,
            'confidence': self.confidence,
            'handedness': self.handedness,
            'position': self.position,
            'screen_position': self.screen_position,
            'timestamp': self.timestamp,
            'state': self.state.name
        }


class GestureStateMachine:
    """手势状态机 - 处理防误触逻辑"""
    
    def __init__(self, hold_time_ms: int = 150, cooldown_ms: int = 700):
        self.hold_time_ms = hold_time_ms
        self.cooldown_ms = cooldown_ms
        self.current_state = GestureState.IDLE
        self.current_gesture: Optional[GestureType] = None
        self.state_start_time: float = 0
        self.last_trigger_time: float = 0
        self._gesture_cooldowns: dict = {}
    
    def update(self, gesture: Optional[GestureType]) -> Tuple[GestureState, bool]:
        """
        更新状态机
        返回: (当前状态, 是否应该触发动作)
        """
        current_time = time.time() * 1000  # 转换为毫秒
        should_trigger = False
        
        if self.current_state == GestureState.IDLE:
            if gesture and gesture != GestureType.UNKNOWN:
                self.current_gesture = gesture
                self.current_state = GestureState.DETECTED
                self.state_start_time = current_time
        
        elif self.current_state == GestureState.DETECTED:
            if gesture == self.current_gesture:
                elapsed = current_time - self.state_start_time
                if elapsed >= self.hold_time_ms:
                    self.current_state = GestureState.HOLDING
            else:
                self._reset()
        
        elif self.current_state == GestureState.HOLDING:
            if gesture == self.current_gesture:
                # 检查是否在冷却期
                if not self._is_in_cooldown(gesture):
                    self.current_state = GestureState.TRIGGERED
                    should_trigger = True
                    self._gesture_cooldowns[gesture] = current_time
            else:
                self._reset()
        
        elif self.current_state == GestureState.TRIGGERED:
            self.current_state = GestureState.COOLDOWN
            self.state_start_time = current_time
        
        elif self.current_state == GestureState.COOLDOWN:
            elapsed = current_time - self.state_start_time
            if elapsed >= self.cooldown_ms:
                self._reset()
        
        return self.current_state, should_trigger
    
    def _is_in_cooldown(self, gesture: GestureType) -> bool:
        """检查手势是否在冷却期"""
        if gesture not in self._gesture_cooldowns:
            return False
        current_time = time.time() * 1000
        elapsed = current_time - self._gesture_cooldowns[gesture]
        return elapsed < self.cooldown_ms
    
    def _reset(self):
        """重置状态机"""
        self.current_state = GestureState.IDLE
        self.current_gesture = None
        self.state_start_time = 0
    
    def set_cooldown(self, gesture: GestureType, cooldown_ms: int):
        """为特定手势设置冷却时间"""
        # 可以扩展为每个手势独立冷却时间
        pass
