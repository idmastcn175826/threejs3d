"""
Action Domain Model - 动作领域模型
定义动作类型、动作实体和执行结果
"""

from dataclasses import dataclass, field
from enum import Enum, auto
from typing import Optional, Any, Dict
import time


class ActionType(Enum):
    """动作类型枚举"""
    KEYBOARD = auto()      # 键盘事件
    MOUSE = auto()         # 鼠标事件
    SYSTEM = auto()        # 系统控制
    SCRIPT = auto()        # 自定义脚本
    EFFECT = auto()        # 视觉特效
    COMPOSITE = auto()     # 组合动作


class MouseAction(Enum):
    """鼠标动作类型"""
    LEFT_CLICK = auto()
    RIGHT_CLICK = auto()
    DOUBLE_CLICK = auto()
    MIDDLE_CLICK = auto()
    SCROLL_UP = auto()
    SCROLL_DOWN = auto()
    MOVE = auto()
    DRAG = auto()


class SystemAction(Enum):
    """系统控制动作"""
    VOLUME_UP = auto()
    VOLUME_DOWN = auto()
    VOLUME_MUTE = auto()
    BRIGHTNESS_UP = auto()
    BRIGHTNESS_DOWN = auto()
    MEDIA_PLAY_PAUSE = auto()
    MEDIA_NEXT = auto()
    MEDIA_PREV = auto()
    LOCK_SCREEN = auto()
    SCREENSHOT = auto()
    TASK_MANAGER = auto()


@dataclass
class Action:
    """动作实体"""
    action_type: ActionType
    action_value: str  # 具体动作值（如 "ctrl+c", "left_click", "volume_up"）
    display_name: str = ""
    description: str = ""
    cooldown_ms: int = 500
    parameters: Dict[str, Any] = field(default_factory=dict)
    
    @classmethod
    def from_config(cls, config: dict) -> 'Action':
        """从配置字典创建动作"""
        action_type_map = {
            'keyboard': ActionType.KEYBOARD,
            'mouse': ActionType.MOUSE,
            'system': ActionType.SYSTEM,
            'script': ActionType.SCRIPT,
            'effect': ActionType.EFFECT,
            'composite': ActionType.COMPOSITE
        }
        
        return cls(
            action_type=action_type_map.get(config.get('action_type', 'keyboard'), ActionType.KEYBOARD),
            action_value=config.get('action', ''),
            display_name=config.get('display_name', ''),
            description=config.get('description', ''),
            cooldown_ms=config.get('cooldown_ms', 500),
            parameters=config.get('parameters', {})
        )
    
    def to_dict(self) -> dict:
        """转换为字典"""
        return {
            'action_type': self.action_type.name,
            'action_value': self.action_value,
            'display_name': self.display_name,
            'description': self.description,
            'cooldown_ms': self.cooldown_ms,
            'parameters': self.parameters
        }


@dataclass
class ActionResult:
    """动作执行结果"""
    success: bool
    action: Action
    message: str = ""
    timestamp: float = field(default_factory=time.time)
    execution_time_ms: float = 0
    error: Optional[str] = None
    
    @classmethod
    def success_result(cls, action: Action, message: str = "执行成功", exec_time: float = 0) -> 'ActionResult':
        """创建成功结果"""
        return cls(
            success=True,
            action=action,
            message=message,
            execution_time_ms=exec_time
        )
    
    @classmethod
    def failure_result(cls, action: Action, error: str) -> 'ActionResult':
        """创建失败结果"""
        return cls(
            success=False,
            action=action,
            message="执行失败",
            error=error
        )


class ActionMapping:
    """手势-动作映射管理"""
    
    def __init__(self):
        self._mappings: Dict[str, Action] = {}
        self._cooldown_tracker: Dict[str, float] = {}
    
    def register(self, gesture_name: str, action: Action):
        """注册手势-动作映射"""
        self._mappings[gesture_name] = action
    
    def get_action(self, gesture_name: str) -> Optional[Action]:
        """获取手势对应的动作"""
        return self._mappings.get(gesture_name)
    
    def is_in_cooldown(self, gesture_name: str) -> bool:
        """检查动作是否在冷却期"""
        if gesture_name not in self._cooldown_tracker:
            return False
        
        action = self._mappings.get(gesture_name)
        if not action:
            return False
        
        current_time = time.time() * 1000
        last_trigger = self._cooldown_tracker[gesture_name]
        return (current_time - last_trigger) < action.cooldown_ms
    
    def mark_triggered(self, gesture_name: str):
        """标记动作已触发"""
        self._cooldown_tracker[gesture_name] = time.time() * 1000
    
    def get_all_mappings(self) -> Dict[str, Action]:
        """获取所有映射"""
        return self._mappings.copy()
    
    def load_from_config(self, config: list):
        """从配置加载映射"""
        for mapping in config:
            gesture = mapping.get('gesture', '')
            if gesture:
                action = Action.from_config(mapping)
                self.register(gesture, action)
