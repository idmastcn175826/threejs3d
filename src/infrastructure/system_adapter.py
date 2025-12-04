"""
System Adapter - 系统控制适配器
负责键盘、鼠标模拟和系统命令执行
"""

import logging
import subprocess
import time
from typing import Optional, Tuple
from enum import Enum

try:
    import pyautogui
    pyautogui.FAILSAFE = False  # 禁用安全模式
    pyautogui.PAUSE = 0.01     # 减少操作间隔
except ImportError:
    pyautogui = None
    logging.warning("pyautogui 未安装")

try:
    import win32api
    import win32con
    HAS_WIN32 = True
except ImportError:
    HAS_WIN32 = False
    logging.warning("win32api 未安装，部分功能可能不可用")

from ..domain.action import Action, ActionType, ActionResult, MouseAction, SystemAction

logger = logging.getLogger(__name__)


class SystemAdapter:
    """系统控制适配器 - 执行键鼠和系统命令"""
    
    def __init__(self):
        if pyautogui is None:
            raise RuntimeError("pyautogui 未安装")
        
        self.screen_width, self.screen_height = pyautogui.size()
        logger.info(f"系统适配器已初始化，屏幕尺寸: {self.screen_width}x{self.screen_height}")
    
    def execute(self, action: Action, position: Optional[Tuple[int, int]] = None) -> ActionResult:
        """
        执行动作
        
        Args:
            action: 动作对象
            position: 可选的位置坐标（用于鼠标操作）
        
        Returns:
            ActionResult: 执行结果
        """
        start_time = time.time()
        
        try:
            if action.action_type == ActionType.KEYBOARD:
                self._execute_keyboard(action)
            elif action.action_type == ActionType.MOUSE:
                self._execute_mouse(action, position)
            elif action.action_type == ActionType.SYSTEM:
                self._execute_system(action)
            elif action.action_type == ActionType.SCRIPT:
                self._execute_script(action)
            elif action.action_type == ActionType.EFFECT:
                # 特效不在这里处理，返回成功让上层处理
                pass
            
            exec_time = (time.time() - start_time) * 1000
            logger.debug(f"动作执行成功: {action.display_name} ({exec_time:.1f}ms)")
            return ActionResult.success_result(action, exec_time=exec_time)
            
        except Exception as e:
            logger.error(f"动作执行失败: {action.display_name} - {e}")
            return ActionResult.failure_result(action, str(e))
    
    def _execute_keyboard(self, action: Action):
        """执行键盘动作"""
        key = action.action_value.lower()
        
        # 处理组合键
        if '+' in key:
            keys = key.split('+')
            # 使用hotkey发送组合键
            pyautogui.hotkey(*keys)
        else:
            # 处理特殊键映射
            key_map = {
                'space': 'space',
                'enter': 'enter',
                'tab': 'tab',
                'escape': 'escape',
                'esc': 'escape',
                'backspace': 'backspace',
                'delete': 'delete',
                'up': 'up',
                'down': 'down',
                'left': 'left',
                'right': 'right',
                'home': 'home',
                'end': 'end',
                'pageup': 'pageup',
                'pagedown': 'pagedown',
                'f1': 'f1', 'f2': 'f2', 'f3': 'f3', 'f4': 'f4',
                'f5': 'f5', 'f6': 'f6', 'f7': 'f7', 'f8': 'f8',
                'f9': 'f9', 'f10': 'f10', 'f11': 'f11', 'f12': 'f12',
            }
            
            mapped_key = key_map.get(key, key)
            pyautogui.press(mapped_key)
    
    def _execute_mouse(self, action: Action, position: Optional[Tuple[int, int]] = None):
        """执行鼠标动作"""
        mouse_action = action.action_value.lower()
        
        # 移动到指定位置
        if position and mouse_action != 'move':
            pyautogui.moveTo(position[0], position[1], duration=0)
        
        if mouse_action == 'left_click':
            pyautogui.click()
        elif mouse_action == 'right_click':
            pyautogui.rightClick()
        elif mouse_action == 'double_click':
            pyautogui.doubleClick()
        elif mouse_action == 'middle_click':
            pyautogui.middleClick()
        elif mouse_action == 'scroll_up':
            amount = action.parameters.get('amount', 3)
            pyautogui.scroll(amount)
        elif mouse_action == 'scroll_down':
            amount = action.parameters.get('amount', 3)
            pyautogui.scroll(-amount)
        elif mouse_action == 'move':
            if position:
                pyautogui.moveTo(position[0], position[1], duration=0.1)
    
    def _execute_system(self, action: Action):
        """执行系统控制动作"""
        system_action = action.action_value.lower()
        
        if system_action == 'volume_up':
            self._adjust_volume(2)
        elif system_action == 'volume_down':
            self._adjust_volume(-2)
        elif system_action == 'volume_mute':
            pyautogui.press('volumemute')
        elif system_action == 'media_play_pause':
            pyautogui.press('playpause')
        elif system_action == 'media_next':
            pyautogui.press('nexttrack')
        elif system_action == 'media_prev':
            pyautogui.press('prevtrack')
        elif system_action == 'lock_screen':
            self._lock_screen()
        elif system_action == 'screenshot':
            self._take_screenshot()
        elif system_action == 'task_manager':
            pyautogui.hotkey('ctrl', 'shift', 'escape')
        elif system_action == 'brightness_up':
            self._adjust_brightness(10)
        elif system_action == 'brightness_down':
            self._adjust_brightness(-10)
    
    def _execute_script(self, action: Action):
        """执行自定义脚本"""
        script_path = action.action_value
        script_type = action.parameters.get('type', 'powershell')
        timeout = action.parameters.get('timeout', 30)
        
        try:
            if script_type == 'powershell':
                result = subprocess.run(
                    ['powershell', '-ExecutionPolicy', 'Bypass', '-File', script_path],
                    capture_output=True, text=True, timeout=timeout
                )
            elif script_type == 'cmd':
                result = subprocess.run(
                    ['cmd', '/c', script_path],
                    capture_output=True, text=True, timeout=timeout
                )
            elif script_type == 'python':
                result = subprocess.run(
                    ['python', script_path],
                    capture_output=True, text=True, timeout=timeout
                )
            else:
                # 直接执行
                result = subprocess.run(
                    script_path, shell=True,
                    capture_output=True, text=True, timeout=timeout
                )
            
            if result.returncode != 0:
                logger.warning(f"脚本执行返回非0: {result.stderr}")
                
        except subprocess.TimeoutExpired:
            logger.error(f"脚本执行超时: {script_path}")
            raise
        except Exception as e:
            logger.error(f"脚本执行错误: {e}")
            raise
    
    def _adjust_volume(self, delta: int):
        """调整音量"""
        key = 'volumeup' if delta > 0 else 'volumedown'
        for _ in range(abs(delta)):
            pyautogui.press(key)
            time.sleep(0.05)
    
    def _adjust_brightness(self, delta: int):
        """调整屏幕亮度（Windows）"""
        try:
            # 使用PowerShell调整亮度
            if delta > 0:
                cmd = f'(Get-WmiObject -Namespace root/wmi -Class WmiMonitorBrightnessMethods).WmiSetBrightness(1, [Math]::Min(100, (Get-WmiObject -Namespace root/wmi -Class WmiMonitorBrightness).CurrentBrightness + {delta}))'
            else:
                cmd = f'(Get-WmiObject -Namespace root/wmi -Class WmiMonitorBrightnessMethods).WmiSetBrightness(1, [Math]::Max(0, (Get-WmiObject -Namespace root/wmi -Class WmiMonitorBrightness).CurrentBrightness + {delta}))'
            
            subprocess.run(['powershell', '-Command', cmd], 
                          capture_output=True, timeout=5)
        except Exception as e:
            logger.warning(f"调整亮度失败: {e}")
    
    def _lock_screen(self):
        """锁定屏幕"""
        pyautogui.hotkey('win', 'l')
    
    def _take_screenshot(self):
        """截图"""
        pyautogui.hotkey('win', 'shift', 's')
    
    def move_mouse(self, x: int, y: int, relative: bool = False):
        """移动鼠标"""
        if relative:
            pyautogui.move(x, y, duration=0)
        else:
            pyautogui.moveTo(x, y, duration=0)
    
    def get_mouse_position(self) -> Tuple[int, int]:
        """获取鼠标位置"""
        return pyautogui.position()
    
    def normalized_to_screen(self, x: float, y: float) -> Tuple[int, int]:
        """归一化坐标转屏幕坐标"""
        screen_x = int(x * self.screen_width)
        screen_y = int(y * self.screen_height)
        return (screen_x, screen_y)
    
    def screen_to_normalized(self, x: int, y: int) -> Tuple[float, float]:
        """屏幕坐标转归一化坐标"""
        norm_x = x / self.screen_width
        norm_y = y / self.screen_height
        return (norm_x, norm_y)
    
    def open_application(self, path: str) -> bool:
        """打开应用程序"""
        try:
            subprocess.Popen(path, shell=True)
            return True
        except Exception as e:
            logger.error(f"打开应用失败: {e}")
            return False
