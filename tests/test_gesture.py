"""
手势识别模块测试
"""

import pytest
import sys
from pathlib import Path

# 添加src到路径
sys.path.insert(0, str(Path(__file__).parent.parent / "src"))

from domain.gesture import (
    GestureType, GestureState, GestureEvent, 
    HandLandmarks, GestureStateMachine
)
from domain.effect import HeartCurve, Particle, ParticlePool
import math
import time


class TestGestureType:
    """测试手势类型"""
    
    def test_gesture_types_exist(self):
        """测试手势类型枚举存在"""
        assert GestureType.ONE_FINGER
        assert GestureType.FIVE_FINGERS
        assert GestureType.FIST
        assert GestureType.OK
        assert GestureType.HEART
        assert GestureType.SWIPE_LEFT
        assert GestureType.SWIPE_RIGHT


class TestHandLandmarks:
    """测试手部关键点"""
    
    def test_create_landmarks(self):
        """测试创建关键点"""
        landmarks = HandLandmarks(
            landmarks=[(0.5, 0.5, 0) for _ in range(21)],
            handedness="Right",
            confidence=0.9
        )
        
        assert len(landmarks.landmarks) == 21
        assert landmarks.handedness == "Right"
        assert landmarks.confidence == 0.9
    
    def test_get_landmark(self):
        """测试获取单个关键点"""
        landmarks = HandLandmarks(
            landmarks=[(i * 0.1, i * 0.1, 0) for i in range(21)],
            handedness="Right"
        )
        
        lm = landmarks.get_landmark(5)
        assert lm == (0.5, 0.5, 0)
    
    def test_get_palm_center(self):
        """测试获取手掌中心"""
        # 创建简单的测试数据
        test_landmarks = [(0.5, 0.5, 0) for _ in range(21)]
        test_landmarks[0] = (0.4, 0.6, 0)  # 手腕
        test_landmarks[9] = (0.6, 0.4, 0)  # 中指MCP
        
        landmarks = HandLandmarks(landmarks=test_landmarks)
        center = landmarks.get_palm_center()
        
        assert center is not None
        assert abs(center[0] - 0.5) < 0.01
        assert abs(center[1] - 0.5) < 0.01
    
    def test_get_fingertips(self):
        """测试获取指尖"""
        landmarks = HandLandmarks(
            landmarks=[(i * 0.01, i * 0.01, 0) for i in range(21)]
        )
        
        tips = landmarks.get_fingertips()
        assert len(tips) == 5
        assert tips[0] == (0.04, 0.04, 0)  # 拇指尖
        assert tips[1] == (0.08, 0.08, 0)  # 食指尖


class TestGestureStateMachine:
    """测试手势状态机"""
    
    def test_initial_state(self):
        """测试初始状态"""
        sm = GestureStateMachine()
        assert sm.current_state == GestureState.IDLE
    
    def test_gesture_detection(self):
        """测试手势检测"""
        sm = GestureStateMachine(hold_time_ms=100, cooldown_ms=500)
        
        # 检测到手势
        state, trigger = sm.update(GestureType.FIST)
        assert state == GestureState.DETECTED
        assert not trigger
    
    def test_gesture_holding(self):
        """测试手势保持"""
        sm = GestureStateMachine(hold_time_ms=50, cooldown_ms=100)
        
        # 检测
        sm.update(GestureType.FIST)
        
        # 等待保持时间
        time.sleep(0.1)
        
        # 再次更新
        state, trigger = sm.update(GestureType.FIST)
        assert state == GestureState.HOLDING or state == GestureState.TRIGGERED
    
    def test_gesture_reset_on_change(self):
        """测试手势变化时重置"""
        sm = GestureStateMachine()
        
        sm.update(GestureType.FIST)
        assert sm.current_state == GestureState.DETECTED
        
        sm.update(GestureType.OK)  # 手势变化
        assert sm.current_state == GestureState.DETECTED


class TestGestureEvent:
    """测试手势事件"""
    
    def test_create_event(self):
        """测试创建事件"""
        event = GestureEvent(
            gesture_type=GestureType.OK,
            confidence=0.95,
            handedness="Right",
            position=(0.5, 0.5)
        )
        
        assert event.gesture_type == GestureType.OK
        assert event.confidence == 0.95
        assert event.handedness == "Right"
    
    def test_to_dict(self):
        """测试转换为字典"""
        event = GestureEvent(
            gesture_type=GestureType.HEART,
            confidence=0.9,
            handedness="Both",
            position=(0.5, 0.5)
        )
        
        d = event.to_dict()
        assert d['gesture_type'] == 'HEART'
        assert d['confidence'] == 0.9


class TestHeartCurve:
    """测试心形曲线"""
    
    def test_get_point(self):
        """测试获取曲线上的点"""
        point = HeartCurve.get_point(0, scale=1.0, center=(0, 0))
        assert point is not None
        assert len(point) == 2
    
    def test_get_points(self):
        """测试获取多个点"""
        points = HeartCurve.get_points(10, scale=1.0, center=(0, 0))
        assert len(points) == 10
    
    def test_heart_shape(self):
        """测试心形形状正确性"""
        # 心形顶部应该有一个凹陷
        top_point = HeartCurve.get_point(math.pi / 2, scale=100)
        
        # 心形底部应该是尖的
        bottom_point = HeartCurve.get_point(math.pi * 3 / 2, scale=100)
        
        # 底部y坐标应该大于顶部
        assert bottom_point[1] > top_point[1]


class TestParticle:
    """测试粒子"""
    
    def test_create_particle(self):
        """测试创建粒子"""
        p = Particle(x=0.5, y=0.5, vx=0.01, vy=0.01)
        assert p.is_alive
        assert p.alpha == 1.0
    
    def test_particle_update(self):
        """测试粒子更新"""
        p = Particle(x=0.5, y=0.5, vx=0.1, vy=0.1, lifetime=1.0)
        
        p.update(0.1)  # 更新0.1秒
        
        assert p.x > 0.5
        assert p.y > 0.5
        assert p.age == 0.1
        assert p.is_alive
    
    def test_particle_death(self):
        """测试粒子死亡"""
        p = Particle(x=0.5, y=0.5, lifetime=0.1)
        
        p.update(0.2)  # 超过生命周期
        
        assert not p.is_alive


class TestParticlePool:
    """测试粒子对象池"""
    
    def test_acquire_particle(self):
        """测试获取粒子"""
        pool = ParticlePool(initial_size=10)
        
        p = pool.acquire(0.5, 0.5)
        assert p is not None
        assert p.is_alive
        assert pool.active_count == 1
    
    def test_release_particle(self):
        """测试释放粒子"""
        pool = ParticlePool(initial_size=10)
        
        p = pool.acquire()
        pool.release(p)
        
        assert pool.active_count == 0
        assert pool.pool_size == 10
    
    def test_update_all(self):
        """测试批量更新"""
        pool = ParticlePool(initial_size=5)
        
        for _ in range(3):
            p = pool.acquire()
            p.lifetime = 0.1
        
        assert pool.active_count == 3
        
        pool.update_all(0.2)  # 超过生命周期
        
        assert pool.active_count == 0
    
    def test_clear_active(self):
        """测试清除所有活跃粒子"""
        pool = ParticlePool(initial_size=10)
        
        for _ in range(5):
            pool.acquire()
        
        assert pool.active_count == 5
        
        pool.clear_active()
        
        assert pool.active_count == 0


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
