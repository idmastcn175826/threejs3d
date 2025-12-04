"""
配置管理模块测试
"""

import pytest
import sys
import tempfile
import json
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent / "src"))

from application.config_manager import ConfigManager


class TestConfigManager:
    """测试配置管理器"""
    
    def test_create_config_manager(self):
        """测试创建配置管理器"""
        with tempfile.TemporaryDirectory() as tmpdir:
            cm = ConfigManager(tmpdir)
            cm.load_all()
            
            assert cm.settings is not None
            assert cm.gestures is not None
            assert cm.effects is not None
    
    def test_default_settings(self):
        """测试默认设置"""
        with tempfile.TemporaryDirectory() as tmpdir:
            cm = ConfigManager(tmpdir)
            cm.load_all()
            
            assert 'camera' in cm.settings
            assert 'display' in cm.settings
            assert 'recognition' in cm.settings
    
    def test_get_camera_config(self):
        """测试获取摄像头配置"""
        with tempfile.TemporaryDirectory() as tmpdir:
            cm = ConfigManager(tmpdir)
            cm.load_all()
            
            camera = cm.get_camera_config()
            
            assert 'device_id' in camera
            assert 'width' in camera
            assert 'height' in camera
    
    def test_get_gesture_mappings(self):
        """测试获取手势映射"""
        with tempfile.TemporaryDirectory() as tmpdir:
            cm = ConfigManager(tmpdir)
            cm.load_all()
            
            mappings = cm.get_gesture_mappings()
            
            assert isinstance(mappings, list)
            assert len(mappings) > 0
    
    def test_update_setting(self):
        """测试更新设置"""
        with tempfile.TemporaryDirectory() as tmpdir:
            cm = ConfigManager(tmpdir)
            cm.load_all()
            
            cm.update_setting('display.show_fps', False)
            
            assert cm.settings['display']['show_fps'] == False
    
    def test_save_and_load(self):
        """测试保存和加载"""
        with tempfile.TemporaryDirectory() as tmpdir:
            # 创建并保存
            cm1 = ConfigManager(tmpdir)
            cm1.load_all()
            cm1.update_setting('camera.fps', 60)
            cm1.save_all()
            
            # 重新加载
            cm2 = ConfigManager(tmpdir)
            cm2.load_all()
            
            assert cm2.settings['camera']['fps'] == 60
    
    def test_get_effect_config(self):
        """测试获取特效配置"""
        with tempfile.TemporaryDirectory() as tmpdir:
            cm = ConfigManager(tmpdir)
            cm.load_all()
            
            star_heart = cm.get_effect_config('star_heart')
            
            assert star_heart is not None
            assert 'particle_count' in star_heart
    
    def test_deep_merge(self):
        """测试深度合并"""
        with tempfile.TemporaryDirectory() as tmpdir:
            cm = ConfigManager(tmpdir)
            
            default = {
                'a': {
                    'b': 1,
                    'c': 2
                },
                'd': 3
            }
            
            override = {
                'a': {
                    'b': 10
                },
                'e': 5
            }
            
            result = cm._deep_merge(default, override)
            
            assert result['a']['b'] == 10
            assert result['a']['c'] == 2
            assert result['d'] == 3
            assert result['e'] == 5


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
