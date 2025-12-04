"""
Config Manager - 配置管理器
负责加载、保存和管理所有配置文件
"""

import json
import os
from typing import Optional, Dict, Any
from pathlib import Path
import logging

logger = logging.getLogger(__name__)


class ConfigManager:
    """配置管理器 - 统一管理所有配置"""
    
    DEFAULT_CONFIG_DIR = "config"
    
    def __init__(self, config_dir: Optional[str] = None):
        self.config_dir = Path(config_dir) if config_dir else Path(self.DEFAULT_CONFIG_DIR)
        
        # 配置缓存
        self._settings: Dict[str, Any] = {}
        self._gestures: Dict[str, Any] = {}
        self._effects: Dict[str, Any] = {}
        self._calibration: Dict[str, Any] = {}
        
        # 确保配置目录存在
        self.config_dir.mkdir(parents=True, exist_ok=True)
        
        logger.info(f"配置管理器初始化，配置目录: {self.config_dir}")
    
    def load_all(self):
        """加载所有配置文件"""
        self._settings = self._load_json("settings.json", self._default_settings())
        self._gestures = self._load_json("gestures.json", self._default_gestures())
        self._effects = self._load_json("effects.json", self._default_effects())
        self._calibration = self._load_json("calibration.json", self._default_calibration())
        
        logger.info("所有配置已加载")
    
    def save_all(self):
        """保存所有配置"""
        self._save_json("settings.json", self._settings)
        self._save_json("gestures.json", self._gestures)
        self._save_json("effects.json", self._effects)
        self._save_json("calibration.json", self._calibration)
        
        logger.info("所有配置已保存")
    
    def _load_json(self, filename: str, default: dict) -> dict:
        """加载JSON配置文件"""
        filepath = self.config_dir / filename
        try:
            if filepath.exists():
                with open(filepath, 'r', encoding='utf-8') as f:
                    data = json.load(f)
                    # 合并默认值（确保新增的配置项有值）
                    return self._deep_merge(default, data)
            else:
                # 创建默认配置
                self._save_json(filename, default)
                return default
        except Exception as e:
            logger.error(f"加载配置失败 {filename}: {e}")
            return default
    
    def _save_json(self, filename: str, data: dict):
        """保存JSON配置文件"""
        filepath = self.config_dir / filename
        try:
            with open(filepath, 'w', encoding='utf-8') as f:
                json.dump(data, f, ensure_ascii=False, indent=4)
        except Exception as e:
            logger.error(f"保存配置失败 {filename}: {e}")
    
    def _deep_merge(self, default: dict, override: dict) -> dict:
        """深度合并字典"""
        result = default.copy()
        for key, value in override.items():
            if key in result and isinstance(result[key], dict) and isinstance(value, dict):
                result[key] = self._deep_merge(result[key], value)
            else:
                result[key] = value
        return result
    
    # 属性访问器
    @property
    def settings(self) -> dict:
        return self._settings
    
    @property
    def gestures(self) -> dict:
        return self._gestures
    
    @property
    def effects(self) -> dict:
        return self._effects
    
    @property
    def calibration(self) -> dict:
        return self._calibration
    
    # 便捷访问方法
    def get_camera_config(self) -> dict:
        """获取摄像头配置"""
        return self._settings.get('camera', {})
    
    def get_display_config(self) -> dict:
        """获取显示配置"""
        return self._settings.get('display', {})
    
    def get_recognition_config(self) -> dict:
        """获取识别配置"""
        return self._settings.get('recognition', {})
    
    def get_safe_zone_config(self) -> dict:
        """获取安全区域配置"""
        return self._settings.get('safe_zone', {})
    
    def get_gesture_mappings(self) -> list:
        """获取手势映射列表"""
        return self._gestures.get('gesture_mappings', [])
    
    def get_effect_config(self, effect_name: str) -> dict:
        """获取特效配置"""
        effects = self._effects.get('effects', {})
        return effects.get(effect_name, {})
    
    def get_all_effect_configs(self) -> dict:
        """获取所有特效配置"""
        return self._effects.get('effects', {})
    
    # 更新方法
    def update_setting(self, key: str, value: Any):
        """更新设置"""
        keys = key.split('.')
        target = self._settings
        for k in keys[:-1]:
            target = target.setdefault(k, {})
        target[keys[-1]] = value
    
    def update_gesture_mapping(self, gesture: str, mapping: dict):
        """更新手势映射"""
        mappings = self._gestures.get('gesture_mappings', [])
        for i, m in enumerate(mappings):
            if m.get('gesture') == gesture:
                mappings[i] = mapping
                return
        mappings.append(mapping)
    
    def update_calibration(self, calibration: dict):
        """更新校准数据"""
        self._calibration.update(calibration)
    
    # 默认配置
    def _default_settings(self) -> dict:
        return {
            "app": {
                "name": "GestureControlPC",
                "version": "1.0.0",
                "language": "zh-CN"
            },
            "camera": {
                "device_id": 0,
                "width": 1280,
                "height": 720,
                "fps": 30,
                "mirror": True,
                "rotation": 0
            },
            "display": {
                "fullscreen": True,
                "background_opacity": 0.6,
                "blur_enabled": False,
                "blur_strength": 5,
                "show_skeleton": True,
                "show_gesture_name": True,
                "show_fps": True
            },
            "recognition": {
                "min_detection_confidence": 0.7,
                "min_tracking_confidence": 0.5,
                "max_num_hands": 2,
                "static_gesture_hold_time_ms": 150,
                "gesture_cooldown_ms": 700
            },
            "safe_zone": {
                "enabled": True,
                "x_min": 0.2,
                "x_max": 0.8,
                "y_min": 0.2,
                "y_max": 0.8
            },
            "effects": {
                "enabled": True,
                "particle_count": 200,
                "auto_adjust_particles": True,
                "target_fps": 30
            },
            "performance": {
                "target_fps": 30,
                "auto_downgrade": True,
                "low_power_mode": False
            }
        }
    
    def _default_gestures(self) -> dict:
        return {
            "gesture_mappings": [
                {
                    "gesture": "one_finger",
                    "display_name": "单指",
                    "action_type": "keyboard",
                    "action": "space",
                    "cooldown_ms": 500,
                    "description": "播放/暂停"
                },
                {
                    "gesture": "five_fingers",
                    "display_name": "五指张开",
                    "action_type": "keyboard",
                    "action": "alt+tab",
                    "cooldown_ms": 700,
                    "description": "切换应用"
                },
                {
                    "gesture": "fist",
                    "display_name": "握拳",
                    "action_type": "mouse",
                    "action": "left_click",
                    "cooldown_ms": 300,
                    "description": "左键点击"
                },
                {
                    "gesture": "heart",
                    "display_name": "比心",
                    "action_type": "effect",
                    "action": "star_heart",
                    "cooldown_ms": 1000,
                    "description": "星空心心特效"
                }
            ],
            "dynamic_gestures": {
                "swipe_threshold": 0.15,
                "swipe_min_frames": 5,
                "swipe_max_frames": 20
            }
        }
    
    def _default_effects(self) -> dict:
        return {
            "effects": {
                "star_heart": {
                    "name": "星空心心",
                    "enabled": True,
                    "particle_count": 150,
                    "duration_ms": 1500,
                    "follow_hand": True,
                    "colors": [
                        [255, 105, 180],
                        [255, 182, 193],
                        [147, 112, 219],
                        [138, 43, 226]
                    ],
                    "particle_size_range": [3, 8],
                    "particle_speed_range": [2, 6],
                    "glow_enabled": True,
                    "glow_intensity": 0.6,
                    "heart_scale": 100,
                    "fade_out": True,
                    "twinkle_enabled": True
                }
            },
            "global": {
                "max_particles": 500,
                "fps_adaptive": True
            }
        }
    
    def _default_calibration(self) -> dict:
        return {
            "camera_matrix": None,
            "distortion_coefficients": None,
            "mirror_horizontal": True,
            "mirror_vertical": False,
            "rotation_degrees": 0,
            "brightness_adjustment": 0,
            "contrast_adjustment": 1.0,
            "calibration_valid": False
        }
