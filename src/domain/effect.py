"""
Effect Domain Model - 特效领域模型
定义粒子、特效配置和特效类型
"""

from dataclasses import dataclass, field
from enum import Enum, auto
from typing import Tuple, List, Optional
import math
import random
import time


class EffectType(Enum):
    """特效类型"""
    STAR_HEART = auto()      # 星空心心
    RIPPLE = auto()          # 波纹
    SPARKLE = auto()         # 火花
    TRAIL = auto()           # 拖尾
    BURST = auto()           # 爆发
    GLOW = auto()            # 发光


@dataclass
class Particle:
    """粒子实体"""
    x: float                 # x坐标
    y: float                 # y坐标
    vx: float = 0            # x速度
    vy: float = 0            # y速度
    ax: float = 0            # x加速度
    ay: float = 0            # y加速度
    size: float = 5          # 大小
    color: Tuple[int, int, int] = (255, 255, 255)  # RGB颜色
    alpha: float = 1.0       # 透明度 (0-1)
    rotation: float = 0      # 旋转角度
    rotation_speed: float = 0
    lifetime: float = 1.0    # 生命周期（秒）
    age: float = 0           # 当前年龄
    is_alive: bool = True
    
    # 额外属性
    glow: bool = False
    twinkle: bool = False
    twinkle_speed: float = 0.1
    
    def update(self, dt: float):
        """更新粒子状态"""
        if not self.is_alive:
            return
        
        # 更新位置
        self.vx += self.ax * dt
        self.vy += self.ay * dt
        self.x += self.vx * dt
        self.y += self.vy * dt
        
        # 更新旋转
        self.rotation += self.rotation_speed * dt
        
        # 更新年龄
        self.age += dt
        
        # 检查生命周期
        if self.age >= self.lifetime:
            self.is_alive = False
        else:
            # 随时间淡出
            life_ratio = 1 - (self.age / self.lifetime)
            self.alpha = life_ratio
            
            # 闪烁效果
            if self.twinkle:
                twinkle_factor = 0.7 + 0.3 * math.sin(self.age * self.twinkle_speed * 20)
                self.alpha *= twinkle_factor
    
    def reset(self, x: float, y: float):
        """重置粒子用于对象池"""
        self.x = x
        self.y = y
        self.vx = 0
        self.vy = 0
        self.ax = 0
        self.ay = 0
        self.age = 0
        self.alpha = 1.0
        self.is_alive = True


@dataclass
class EffectConfig:
    """特效配置"""
    effect_type: EffectType
    name: str = ""
    enabled: bool = True
    particle_count: int = 100
    duration_ms: int = 1000
    follow_hand: bool = True
    colors: List[Tuple[int, int, int]] = field(default_factory=lambda: [(255, 105, 180)])
    particle_size_range: Tuple[float, float] = (3, 8)
    particle_speed_range: Tuple[float, float] = (2, 6)
    glow_enabled: bool = True
    glow_intensity: float = 0.6
    scale: float = 100
    fade_out: bool = True
    fade_duration_ms: int = 500
    twinkle_enabled: bool = True
    twinkle_speed: float = 0.1
    
    @classmethod
    def from_config(cls, effect_type: EffectType, config: dict) -> 'EffectConfig':
        """从配置字典创建"""
        colors = config.get('colors', [[255, 105, 180]])
        return cls(
            effect_type=effect_type,
            name=config.get('name', ''),
            enabled=config.get('enabled', True),
            particle_count=config.get('particle_count', 100),
            duration_ms=config.get('duration_ms', 1000),
            follow_hand=config.get('follow_hand', True),
            colors=[tuple(c) for c in colors],
            particle_size_range=tuple(config.get('particle_size_range', [3, 8])),
            particle_speed_range=tuple(config.get('particle_speed_range', [2, 6])),
            glow_enabled=config.get('glow_enabled', True),
            glow_intensity=config.get('glow_intensity', 0.6),
            scale=config.get('heart_scale', config.get('scale', 100)),
            fade_out=config.get('fade_out', True),
            fade_duration_ms=config.get('fade_duration_ms', 500),
            twinkle_enabled=config.get('twinkle_enabled', True),
            twinkle_speed=config.get('twinkle_speed', 0.1)
        )


class HeartCurve:
    """心形曲线生成器"""
    
    @staticmethod
    def get_point(t: float, scale: float = 1.0, center: Tuple[float, float] = (0, 0)) -> Tuple[float, float]:
        """
        根据参数t获取心形曲线上的点
        使用参数方程：
        x = 16 * sin³(t)
        y = 13*cos(t) - 5*cos(2t) - 2*cos(3t) - cos(4t)
        
        Args:
            t: 参数值 (0 到 2π)
            scale: 缩放比例
            center: 中心点坐标
        
        Returns:
            (x, y) 坐标
        """
        sin_t = math.sin(t)
        cos_t = math.cos(t)
        
        x = 16 * (sin_t ** 3)
        y = 13 * cos_t - 5 * math.cos(2 * t) - 2 * math.cos(3 * t) - math.cos(4 * t)
        
        # 缩放并平移
        x = x * scale / 16 + center[0]
        y = -y * scale / 16 + center[1]  # 翻转y轴使心形正向
        
        return (x, y)
    
    @staticmethod
    def get_points(num_points: int, scale: float = 1.0, center: Tuple[float, float] = (0, 0)) -> List[Tuple[float, float]]:
        """获取心形曲线上的多个点"""
        points = []
        for i in range(num_points):
            t = 2 * math.pi * i / num_points
            points.append(HeartCurve.get_point(t, scale, center))
        return points
    
    @staticmethod
    def get_random_point_on_heart(scale: float = 1.0, center: Tuple[float, float] = (0, 0)) -> Tuple[float, float]:
        """获取心形曲线上的随机点"""
        t = random.uniform(0, 2 * math.pi)
        return HeartCurve.get_point(t, scale, center)
    
    @staticmethod
    def get_random_point_inside_heart(scale: float = 1.0, center: Tuple[float, float] = (0, 0)) -> Tuple[float, float]:
        """获取心形内部的随机点"""
        # 使用rejection sampling
        while True:
            x = random.uniform(-1, 1) * scale
            y = random.uniform(-1, 1) * scale
            
            # 检查点是否在心形内
            # 简化判断：使用隐式方程近似
            nx = x / scale
            ny = -y / scale
            
            # 心形隐式方程: (x² + y² - 1)³ - x²y³ < 0
            val = (nx**2 + ny**2 - 1)**3 - nx**2 * ny**3
            
            if val < 0:
                return (x + center[0], y + center[1])


class ParticlePool:
    """粒子对象池 - 避免频繁创建/销毁"""
    
    def __init__(self, initial_size: int = 200):
        self._pool: List[Particle] = []
        self._active: List[Particle] = []
        
        # 预创建粒子
        for _ in range(initial_size):
            self._pool.append(Particle(0, 0))
    
    def acquire(self, x: float = 0, y: float = 0) -> Particle:
        """获取一个粒子"""
        if self._pool:
            particle = self._pool.pop()
        else:
            particle = Particle(0, 0)
        
        particle.reset(x, y)
        self._active.append(particle)
        return particle
    
    def release(self, particle: Particle):
        """释放粒子回池"""
        if particle in self._active:
            self._active.remove(particle)
            particle.is_alive = False
            self._pool.append(particle)
    
    def update_all(self, dt: float):
        """更新所有活跃粒子"""
        dead_particles = []
        for particle in self._active:
            particle.update(dt)
            if not particle.is_alive:
                dead_particles.append(particle)
        
        # 回收死亡粒子
        for particle in dead_particles:
            self.release(particle)
    
    def get_active_particles(self) -> List[Particle]:
        """获取所有活跃粒子"""
        return self._active.copy()
    
    def clear_active(self):
        """清除所有活跃粒子"""
        for particle in self._active[:]:
            self.release(particle)
    
    @property
    def active_count(self) -> int:
        """活跃粒子数量"""
        return len(self._active)
    
    @property
    def pool_size(self) -> int:
        """池中可用粒子数量"""
        return len(self._pool)
