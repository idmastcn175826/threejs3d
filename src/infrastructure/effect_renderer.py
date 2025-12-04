"""
Effect Renderer - 特效渲染器
负责粒子特效渲染，包括星空心心效果
"""

import math
import random
import time
from typing import Tuple, List, Optional
from dataclasses import dataclass
import logging

import numpy as np

try:
    import cv2
except ImportError:
    cv2 = None

from ..domain.effect import (
    EffectType, Particle, EffectConfig, 
    HeartCurve, ParticlePool
)

logger = logging.getLogger(__name__)


@dataclass
class ActiveEffect:
    """活跃的特效实例"""
    effect_type: EffectType
    config: EffectConfig
    start_time: float
    center: Tuple[float, float]
    particles: List[Particle]
    is_finished: bool = False


class EffectRenderer:
    """特效渲染器 - 管理和渲染粒子特效"""
    
    def __init__(self, max_particles: int = 500):
        self.max_particles = max_particles
        self.particle_pool = ParticlePool(max_particles)
        self.active_effects: List[ActiveEffect] = []
        self.effect_configs: dict = {}
        
        # 性能监控
        self.target_fps = 30
        self.last_frame_time = time.time()
        self.fps_adaptive = True
        
        logger.info("特效渲染器已初始化")
    
    def load_effect_config(self, effect_name: str, config: dict):
        """加载特效配置"""
        effect_type_map = {
            'star_heart': EffectType.STAR_HEART,
            'ripple': EffectType.RIPPLE,
            'sparkle': EffectType.SPARKLE,
            'trail': EffectType.TRAIL,
            'burst': EffectType.BURST
        }
        
        effect_type = effect_type_map.get(effect_name, EffectType.STAR_HEART)
        self.effect_configs[effect_name] = EffectConfig.from_config(effect_type, config)
    
    def trigger_effect(self, effect_name: str, 
                       center: Tuple[float, float] = (0.5, 0.5)):
        """
        触发特效
        
        Args:
            effect_name: 特效名称
            center: 特效中心位置（归一化坐标 0-1）
        """
        config = self.effect_configs.get(effect_name)
        if not config or not config.enabled:
            return
        
        # 检查粒子数量限制
        current_particles = self.particle_pool.active_count
        if current_particles >= self.max_particles:
            logger.warning("粒子数量已达上限，跳过特效")
            return
        
        # 创建特效实例
        particles = self._create_particles(config, center)
        
        effect = ActiveEffect(
            effect_type=config.effect_type,
            config=config,
            start_time=time.time(),
            center=center,
            particles=particles
        )
        
        self.active_effects.append(effect)
        logger.debug(f"触发特效: {effect_name} 在位置 {center}")
    
    def _create_particles(self, config: EffectConfig, 
                          center: Tuple[float, float]) -> List[Particle]:
        """创建粒子"""
        particles = []
        
        # 根据FPS自动调整粒子数量
        particle_count = config.particle_count
        if self.fps_adaptive:
            current_fps = self._estimate_fps()
            if current_fps < self.target_fps * 0.8:
                particle_count = int(particle_count * 0.6)
        
        for i in range(particle_count):
            particle = self.particle_pool.acquire(center[0], center[1])
            
            if config.effect_type == EffectType.STAR_HEART:
                self._init_star_heart_particle(particle, config, center, i, particle_count)
            elif config.effect_type == EffectType.RIPPLE:
                self._init_ripple_particle(particle, config, center, i, particle_count)
            elif config.effect_type == EffectType.SPARKLE:
                self._init_sparkle_particle(particle, config, center)
            else:
                self._init_default_particle(particle, config, center)
            
            particles.append(particle)
        
        return particles
    
    def _init_star_heart_particle(self, particle: Particle, config: EffectConfig,
                                   center: Tuple[float, float], index: int, total: int):
        """初始化星空心心粒子 - 优化版"""
        # 多层心形分布：内层密集 + 外层扩散 + 随机星星
        layer = index % 4  # 4层结构
        layer_ratio = index / total
        
        if layer == 0:
            # 第一层：心形轮廓上的粒子（密集）
            t = 2 * math.pi * (index / (total / 4))
            scale = config.scale / 800
            heart_point = HeartCurve.get_point(t, scale=scale, center=center)
            offset = random.uniform(-0.008, 0.008)
            particle.x = heart_point[0] + offset
            particle.y = heart_point[1] + offset
            particle.size = random.uniform(3, 6)
            # 较慢的向外扩散
            angle = math.atan2(heart_point[1] - center[1], heart_point[0] - center[0])
            speed = random.uniform(0.002, 0.008)
            particle.vx = math.cos(angle) * speed
            particle.vy = math.sin(angle) * speed
            
        elif layer == 1:
            # 第二层：内部填充的小星星
            t = random.uniform(0, 2 * math.pi)
            # 在心形内部随机分布
            r = random.uniform(0.3, 0.9)
            scale = config.scale / 800 * r
            heart_point = HeartCurve.get_point(t, scale=scale, center=center)
            particle.x = heart_point[0] + random.uniform(-0.015, 0.015)
            particle.y = heart_point[1] + random.uniform(-0.015, 0.015)
            particle.size = random.uniform(2, 4)
            # 随机漂浮
            particle.vx = random.uniform(-0.003, 0.003)
            particle.vy = random.uniform(-0.005, 0.001)  # 轻微上浮
            
        elif layer == 2:
            # 第三层：外围扩散的发光粒子
            t = 2 * math.pi * (index / (total / 4))
            scale = config.scale / 600
            heart_point = HeartCurve.get_point(t, scale=scale, center=center)
            particle.x = heart_point[0]
            particle.y = heart_point[1]
            particle.size = random.uniform(4, 8)
            # 向外扩散
            angle = math.atan2(heart_point[1] - center[1], heart_point[0] - center[0])
            speed = random.uniform(0.01, 0.025)
            particle.vx = math.cos(angle) * speed + random.uniform(-0.005, 0.005)
            particle.vy = math.sin(angle) * speed + random.uniform(-0.005, 0.005)
            particle.glow = True
            
        else:
            # 第四层：随机分布的闪烁星星（背景）
            # 在心形周围随机分布
            angle = random.uniform(0, 2 * math.pi)
            dist = random.uniform(0.05, 0.18)
            particle.x = center[0] + math.cos(angle) * dist
            particle.y = center[1] + math.sin(angle) * dist
            particle.size = random.uniform(1, 3)
            # 轻微飘动
            particle.vx = random.uniform(-0.002, 0.002)
            particle.vy = random.uniform(-0.004, 0.001)
            particle.twinkle = True
            particle.twinkle_speed = random.uniform(3, 8)
        
        # 设置颜色 - 根据层次选择不同颜色
        if layer <= 1:
            # 内层用更亮的颜色
            bright_colors = [
                (255, 182, 193),  # 浅粉
                (255, 192, 203),  # 粉红
                (255, 255, 255),  # 白色闪烁
                (255, 218, 233),  # 淡粉
            ]
            particle.color = random.choice(bright_colors)
        else:
            # 外层用配置颜色
            particle.color = random.choice(config.colors) if config.colors else (255, 105, 180)
        
        # 设置生命周期 - 内层更长
        base_lifetime = config.duration_ms / 1000
        if layer <= 1:
            particle.lifetime = base_lifetime * random.uniform(0.8, 1.0)
        else:
            particle.lifetime = base_lifetime * random.uniform(0.5, 0.9)
        
        # 设置旋转
        particle.rotation = random.uniform(0, 360)
        particle.rotation_speed = random.uniform(-90, 90)
        
        # 发光和闪烁
        if not hasattr(particle, 'glow') or layer == 2:
            particle.glow = config.glow_enabled
        if not hasattr(particle, 'twinkle') or layer == 3:
            particle.twinkle = config.twinkle_enabled
        particle.twinkle_speed = config.twinkle_speed
    
    def _init_ripple_particle(self, particle: Particle, config: EffectConfig,
                               center: Tuple[float, float], index: int, total: int):
        """初始化波纹粒子"""
        # 圆形分布
        angle = 2 * math.pi * index / total
        radius = random.uniform(0.01, 0.05)
        
        particle.x = center[0] + math.cos(angle) * radius
        particle.y = center[1] + math.sin(angle) * radius
        
        # 向外扩散
        speed = 0.05
        particle.vx = math.cos(angle) * speed
        particle.vy = math.sin(angle) * speed
        
        particle.size = 2
        particle.color = random.choice(config.colors) if config.colors else (100, 149, 237)
        particle.lifetime = config.duration_ms / 1000
    
    def _init_sparkle_particle(self, particle: Particle, config: EffectConfig,
                                center: Tuple[float, float]):
        """初始化火花粒子"""
        # 随机爆发
        angle = random.uniform(0, 2 * math.pi)
        speed = random.uniform(0.05, 0.15)
        
        particle.x = center[0]
        particle.y = center[1]
        particle.vx = math.cos(angle) * speed
        particle.vy = math.sin(angle) * speed
        particle.ay = 0.01  # 重力
        
        particle.size = random.uniform(2, 5)
        particle.color = random.choice(config.colors) if config.colors else (255, 255, 0)
        particle.lifetime = config.duration_ms / 1000 * random.uniform(0.5, 1.0)
    
    def _init_default_particle(self, particle: Particle, config: EffectConfig,
                                center: Tuple[float, float]):
        """初始化默认粒子"""
        particle.x = center[0] + random.uniform(-0.1, 0.1)
        particle.y = center[1] + random.uniform(-0.1, 0.1)
        particle.vx = random.uniform(-0.02, 0.02)
        particle.vy = random.uniform(-0.02, 0.02)
        particle.size = random.uniform(3, 6)
        particle.color = random.choice(config.colors) if config.colors else (255, 255, 255)
        particle.lifetime = config.duration_ms / 1000
    
    def update(self, dt: float):
        """
        更新所有特效
        
        Args:
            dt: 时间增量（秒）
        """
        current_time = time.time()
        
        # 更新所有活跃特效
        finished_effects = []
        for effect in self.active_effects:
            elapsed = current_time - effect.start_time
            
            # 更新粒子
            for particle in effect.particles:
                particle.update(dt)
            
            # 检查特效是否结束
            duration_sec = effect.config.duration_ms / 1000
            if elapsed > duration_sec:
                effect.is_finished = True
                finished_effects.append(effect)
        
        # 清理结束的特效
        for effect in finished_effects:
            for particle in effect.particles:
                self.particle_pool.release(particle)
            self.active_effects.remove(effect)
        
        self.last_frame_time = current_time
    
    def render(self, frame: np.ndarray) -> np.ndarray:
        """
        渲染特效到帧 - 优化版
        
        Args:
            frame: BGR格式的图像帧
            
        Returns:
            渲染后的帧
        """
        if cv2 is None or not self.active_effects:
            return frame
        
        h, w = frame.shape[:2]
        
        # 创建透明叠加层
        overlay = frame.copy()
        
        # 先绘制发光层（底层）
        glow_layer = np.zeros_like(frame, dtype=np.float32)
        
        for effect in self.active_effects:
            # 计算特效进度
            elapsed = time.time() - effect.start_time
            progress = min(elapsed / (effect.config.duration_ms / 1000), 1.0)
            
            for particle in effect.particles:
                if not particle.is_alive:
                    continue
                
                # 转换坐标
                px = int(particle.x * w)
                py = int(particle.y * h)
                
                # 检查边界
                if px < 5 or px >= w - 5 or py < 5 or py >= h - 5:
                    continue
                
                # 获取颜色（BGR格式）
                color = (particle.color[2], particle.color[1], particle.color[0])
                
                # 计算透明度
                alpha = particle.alpha
                
                # 闪烁效果
                if particle.twinkle:
                    twinkle_factor = 0.5 + 0.5 * math.sin(particle.age * particle.twinkle_speed)
                    alpha *= twinkle_factor
                
                # 粒子大小
                size = max(1, int(particle.size * alpha))
                
                # 发光效果
                if particle.glow and size >= 2:
                    # 柔和的多层发光
                    for i in range(4, 0, -1):
                        glow_size = size + i * 3
                        glow_intensity = alpha * 0.15 / i
                        glow_color = tuple(c * glow_intensity for c in color)
                        cv2.circle(glow_layer, (px, py), glow_size, glow_color, -1, cv2.LINE_AA)
                
                # 绘制主体粒子
                if size >= 3:
                    # 大粒子绘制星形
                    self._draw_star(overlay, (px, py), size, color, particle.rotation, alpha)
                else:
                    # 小粒子绘制圆点
                    cv2.circle(overlay, (px, py), size, color, -1, cv2.LINE_AA)
        
        # 混合发光层
        glow_layer = np.clip(glow_layer, 0, 255).astype(np.uint8)
        overlay = cv2.add(overlay, glow_layer)
        
        # 混合叠加层
        frame = cv2.addWeighted(overlay, 0.85, frame, 0.15, 0)
        
        return frame
    
    def _draw_star(self, frame: np.ndarray, center: Tuple[int, int], 
                   size: int, color: Tuple[int, int, int], 
                   rotation: float, alpha: float):
        """绘制星形粒子"""
        # 生成4角星/5角星顶点
        points_count = 4 if size < 5 else 5
        points = []
        
        for i in range(points_count * 2):
            angle = math.radians(rotation) + i * math.pi / points_count - math.pi / 2
            r = size if i % 2 == 0 else size * 0.4
            x = int(center[0] + r * math.cos(angle))
            y = int(center[1] + r * math.sin(angle))
            points.append([x, y])
        
        points = np.array(points, dtype=np.int32)
        
        # 绘制填充星形
        adjusted_color = tuple(int(c * alpha) for c in color)
        cv2.fillPoly(frame, [points], adjusted_color, cv2.LINE_AA)
    
    def render_star_shape(self, frame: np.ndarray, center: Tuple[int, int], 
                          size: int, color: Tuple[int, int, int], 
                          rotation: float = 0) -> np.ndarray:
        """
        渲染星形粒子
        """
        if cv2 is None:
            return frame
        
        # 生成5角星顶点
        points = []
        for i in range(10):
            angle = rotation + i * math.pi / 5 - math.pi / 2
            r = size if i % 2 == 0 else size / 2
            x = int(center[0] + r * math.cos(angle))
            y = int(center[1] + r * math.sin(angle))
            points.append([x, y])
        
        points = np.array(points, dtype=np.int32)
        cv2.fillPoly(frame, [points], color)
        
        return frame
    
    def _estimate_fps(self) -> float:
        """估算当前FPS"""
        current_time = time.time()
        dt = current_time - self.last_frame_time
        return 1.0 / dt if dt > 0 else 60
    
    def clear_all_effects(self):
        """清除所有特效"""
        for effect in self.active_effects:
            for particle in effect.particles:
                self.particle_pool.release(particle)
        self.active_effects.clear()
    
    def get_active_particle_count(self) -> int:
        """获取活跃粒子数量"""
        return self.particle_pool.active_count
    
    def set_fps_target(self, fps: int):
        """设置目标FPS"""
        self.target_fps = fps
    
    def set_adaptive_mode(self, enabled: bool):
        """设置自适应模式"""
        self.fps_adaptive = enabled
