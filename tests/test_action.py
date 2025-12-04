"""
动作映射模块测试
"""

import pytest
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent / "src"))

from domain.action import Action, ActionType, ActionResult, ActionMapping


class TestAction:
    """测试动作"""
    
    def test_create_action(self):
        """测试创建动作"""
        action = Action(
            action_type=ActionType.KEYBOARD,
            action_value="ctrl+c",
            display_name="复制",
            cooldown_ms=500
        )
        
        assert action.action_type == ActionType.KEYBOARD
        assert action.action_value == "ctrl+c"
        assert action.cooldown_ms == 500
    
    def test_from_config(self):
        """测试从配置创建"""
        config = {
            'action_type': 'keyboard',
            'action': 'alt+tab',
            'display_name': '切换应用',
            'cooldown_ms': 700
        }
        
        action = Action.from_config(config)
        
        assert action.action_type == ActionType.KEYBOARD
        assert action.action_value == 'alt+tab'
    
    def test_to_dict(self):
        """测试转换为字典"""
        action = Action(
            action_type=ActionType.MOUSE,
            action_value="left_click",
            display_name="左键点击"
        )
        
        d = action.to_dict()
        assert d['action_type'] == 'MOUSE'
        assert d['action_value'] == 'left_click'


class TestActionResult:
    """测试动作执行结果"""
    
    def test_success_result(self):
        """测试成功结果"""
        action = Action(ActionType.KEYBOARD, "space")
        result = ActionResult.success_result(action, "播放/暂停")
        
        assert result.success
        assert result.message == "播放/暂停"
    
    def test_failure_result(self):
        """测试失败结果"""
        action = Action(ActionType.SCRIPT, "test.ps1")
        result = ActionResult.failure_result(action, "脚本不存在")
        
        assert not result.success
        assert result.error == "脚本不存在"


class TestActionMapping:
    """测试动作映射"""
    
    def test_register_action(self):
        """测试注册动作"""
        mapping = ActionMapping()
        action = Action(ActionType.KEYBOARD, "space", "播放")
        
        mapping.register("one_finger", action)
        
        result = mapping.get_action("one_finger")
        assert result is not None
        assert result.action_value == "space"
    
    def test_get_nonexistent_action(self):
        """测试获取不存在的动作"""
        mapping = ActionMapping()
        
        result = mapping.get_action("unknown")
        assert result is None
    
    def test_load_from_config(self):
        """测试从配置加载"""
        mapping = ActionMapping()
        
        config = [
            {
                'gesture': 'fist',
                'action_type': 'mouse',
                'action': 'left_click',
                'cooldown_ms': 300
            },
            {
                'gesture': 'ok',
                'action_type': 'keyboard',
                'action': 'ctrl+c',
                'cooldown_ms': 400
            }
        ]
        
        mapping.load_from_config(config)
        
        fist_action = mapping.get_action('fist')
        assert fist_action is not None
        assert fist_action.action_value == 'left_click'
        
        ok_action = mapping.get_action('ok')
        assert ok_action is not None
        assert ok_action.action_value == 'ctrl+c'
    
    def test_get_all_mappings(self):
        """测试获取所有映射"""
        mapping = ActionMapping()
        mapping.register("a", Action(ActionType.KEYBOARD, "1"))
        mapping.register("b", Action(ActionType.KEYBOARD, "2"))
        
        all_mappings = mapping.get_all_mappings()
        
        assert len(all_mappings) == 2
        assert "a" in all_mappings
        assert "b" in all_mappings


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
