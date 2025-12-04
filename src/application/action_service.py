"""
Action Service - 动作执行服务
负责将手势映射为动作并执行
"""

import logging
from typing import Optional, Dict, Callable, Tuple
import time

from ..domain.gesture import GestureType, GestureEvent
from ..domain.action import Action, ActionType, ActionResult, ActionMapping
from ..infrastructure.system_adapter import SystemAdapter
from ..infrastructure.effect_renderer import EffectRenderer

logger = logging.getLogger(__name__)


class ActionService:
    """动作执行服务 - 协调手势到动作的映射和执行"""
    
    def __init__(self, config: dict):
        self.config = config
        
        # 初始化系统适配器
        self.system_adapter = SystemAdapter()
        
        # 初始化特效渲染器
        effects_config = config.get('effects', {})
        max_particles = effects_config.get('particle_count', 200)
        self.effect_renderer = EffectRenderer(max_particles=max_particles)
        
        # 加载特效配置
        self._load_effect_configs(config)
        
        # 动作映射
        self.action_mapping = ActionMapping()
        self._load_gesture_mappings(config)
        
        # 冷却追踪
        self._cooldown_tracker: Dict[str, float] = {}
        
        # 回调
        self._on_action_callbacks: list = []
        self._on_effect_callbacks: list = []
        
        logger.info("动作执行服务已初始化")
    
    def _load_gesture_mappings(self, config: dict):
        """加载手势映射配置"""
        mappings = config.get('gesture_mappings', [])
        self.action_mapping.load_from_config(mappings)
        logger.info(f"已加载 {len(mappings)} 个手势映射")
    
    def _load_effect_configs(self, config: dict):
        """加载特效配置"""
        effects = config.get('effects', {}).get('effects', {})
        for effect_name, effect_config in effects.items():
            self.effect_renderer.load_effect_config(effect_name, effect_config)
        logger.info(f"已加载 {len(effects)} 个特效配置")
    
    def handle_gesture(self, event: GestureEvent) -> Optional[ActionResult]:
        """
        处理手势事件，执行对应动作
        
        Args:
            event: 手势事件
            
        Returns:
            动作执行结果
        """
        gesture_name = self._gesture_type_to_name(event.gesture_type)
        
        # 获取对应动作
        action = self.action_mapping.get_action(gesture_name)
        if not action:
            logger.debug(f"手势 {gesture_name} 没有配置动作映射")
            return None
        
        # 检查冷却
        if self._is_in_cooldown(gesture_name, action.cooldown_ms):
            logger.debug(f"动作 {action.display_name} 在冷却中")
            return None
        
        # 执行动作
        result = self._execute_action(action, event)
        
        # 更新冷却
        if result and result.success:
            self._cooldown_tracker[gesture_name] = time.time() * 1000
            
            # 触发回调
            for callback in self._on_action_callbacks:
                try:
                    callback(action, result)
                except Exception as e:
                    logger.error(f"动作回调错误: {e}")
        
        return result
    
    def _execute_action(self, action: Action, event: GestureEvent) -> ActionResult:
        """执行单个动作"""
        if action.action_type == ActionType.EFFECT:
            return self._execute_effect(action, event)
        else:
            # 转换坐标
            screen_pos = self.system_adapter.normalized_to_screen(
                event.position[0], event.position[1]
            )
            return self.system_adapter.execute(action, screen_pos)
    
    def _execute_effect(self, action: Action, event: GestureEvent) -> ActionResult:
        """执行特效动作"""
        try:
            effect_name = action.action_value
            
            # 确定特效位置
            if action.parameters.get('follow_hand', True):
                center = event.position
            else:
                center = (0.5, 0.5)  # 屏幕中心
            
            # 触发特效
            self.effect_renderer.trigger_effect(effect_name, center)
            
            # 触发特效回调
            for callback in self._on_effect_callbacks:
                try:
                    callback(effect_name, center)
                except Exception as e:
                    logger.error(f"特效回调错误: {e}")
            
            logger.info(f"触发特效: {effect_name} 在位置 {center}")
            return ActionResult.success_result(action, f"特效 {effect_name} 已触发")
            
        except Exception as e:
            logger.error(f"执行特效失败: {e}")
            return ActionResult.failure_result(action, str(e))
    
    def _is_in_cooldown(self, gesture_name: str, cooldown_ms: int) -> bool:
        """检查是否在冷却期"""
        if gesture_name not in self._cooldown_tracker:
            return False
        
        current_time = time.time() * 1000
        last_trigger = self._cooldown_tracker[gesture_name]
        return (current_time - last_trigger) < cooldown_ms
    
    def _gesture_type_to_name(self, gesture_type: GestureType) -> str:
        """将手势类型转换为配置名称"""
        name_map = {
            GestureType.ONE_FINGER: "one_finger",
            GestureType.TWO_FINGERS: "two_fingers",
            GestureType.THREE_FINGERS: "three_fingers",
            GestureType.FOUR_FINGERS: "four_fingers",
            GestureType.FIVE_FINGERS: "five_fingers",
            GestureType.FIST: "fist",
            GestureType.OK: "ok",
            GestureType.THUMBS_UP: "thumbs_up",
            GestureType.THUMBS_DOWN: "thumbs_down",
            GestureType.HEART: "heart",
            GestureType.DOUBLE_HEART: "heart",  # 双手比心也触发heart动作
            GestureType.ROCK: "rock",
            GestureType.SWIPE_LEFT: "swipe_left",
            GestureType.SWIPE_RIGHT: "swipe_right",
            GestureType.SWIPE_UP: "swipe_up",
            GestureType.SWIPE_DOWN: "swipe_down",
            GestureType.PUSH: "push",
            GestureType.PULL: "pull",
            GestureType.CIRCLE: "circle",
            GestureType.DOUBLE_TAP: "double_tap"
        }
        return name_map.get(gesture_type, "unknown")
    
    def on_action(self, callback: Callable[[Action, ActionResult], None]):
        """注册动作执行回调"""
        self._on_action_callbacks.append(callback)
    
    def on_effect(self, callback: Callable[[str, Tuple[float, float]], None]):
        """注册特效触发回调"""
        self._on_effect_callbacks.append(callback)
    
    def update_effect(self, dt: float):
        """更新特效状态"""
        self.effect_renderer.update(dt)
    
    def render_effects(self, frame) -> any:
        """渲染特效到帧"""
        return self.effect_renderer.render(frame)
    
    def trigger_effect_manually(self, effect_name: str, position: Tuple[float, float] = (0.5, 0.5)):
        """手动触发特效（用于测试）"""
        self.effect_renderer.trigger_effect(effect_name, position)
    
    def get_action_for_gesture(self, gesture_type: GestureType) -> Optional[Action]:
        """获取手势对应的动作"""
        gesture_name = self._gesture_type_to_name(gesture_type)
        return self.action_mapping.get_action(gesture_name)
    
    def update_gesture_mapping(self, gesture_name: str, action_config: dict):
        """更新手势映射"""
        action = Action.from_config(action_config)
        self.action_mapping.register(gesture_name, action)
    
    def get_all_mappings(self) -> Dict[str, Action]:
        """获取所有映射"""
        return self.action_mapping.get_all_mappings()
    
    def get_active_particle_count(self) -> int:
        """获取活跃粒子数量"""
        return self.effect_renderer.get_active_particle_count()
    
    def clear_effects(self):
        """清除所有特效"""
        self.effect_renderer.clear_all_effects()
