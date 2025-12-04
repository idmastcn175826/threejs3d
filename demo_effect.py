#!/usr/bin/env python3
"""
星空心心特效演示
点击窗口任意位置或按空格键触发特效
"""

import sys
import math
import random
import time
from dataclasses import dataclass, field
from typing import List, Tuple
from PyQt5.QtWidgets import QApplication, QWidget, QLabel
from PyQt5.QtCore import Qt, QTimer, QPoint
from PyQt5.QtGui import QPainter, QColor, QPainterPath, QFont, QLinearGradient


@dataclass
class Particle:
    """粒子"""
    x: float = 0.5
    y: float = 0.5
    vx: float = 0
    vy: float = 0
    size: float = 5
    color: Tuple[int, int, int] = (255, 105, 180)
    alpha: float = 1.0
    lifetime: float = 2.0
    age: float = 0
    rotation: float = 0
    rotation_speed: float = 0
    glow: bool = True
    twinkle: bool = False
    twinkle_speed: float = 5.0
    layer: int = 0  # 粒子层级
    
    @property
    def is_alive(self) -> bool:
        return self.age < self.lifetime and self.alpha > 0.01
    
    def update(self, dt: float):
        self.age += dt
        self.x += self.vx * dt
        self.y += self.vy * dt
        self.rotation += self.rotation_speed * dt
        
        # 渐隐
        progress = self.age / self.lifetime
        if progress > 0.6:
            self.alpha = 1.0 - (progress - 0.6) / 0.4


class HeartCurve:
    """心形曲线"""
    
    @staticmethod
    def get_point(t: float, scale: float = 0.1, center: Tuple[float, float] = (0.5, 0.5)) -> Tuple[float, float]:
        """获取心形曲线上的点"""
        # 参数方程
        x = 16 * (math.sin(t) ** 3)
        y = 13 * math.cos(t) - 5 * math.cos(2*t) - 2 * math.cos(3*t) - math.cos(4*t)
        
        # 缩放和平移
        x = center[0] + x * scale / 16
        y = center[1] - y * scale / 16  # Y轴翻转
        
        return (x, y)


class StarHeartEffect(QWidget):
    """星空心心特效窗口"""
    
    def __init__(self):
        super().__init__()
        
        self.setWindowTitle("✨ 星空心心特效演示 ✨")
        self.resize(1200, 800)
        self.setStyleSheet("background-color: #0a0a1a;")
        
        # 粒子列表
        self.particles: List[Particle] = []
        
        # 定时器
        self.timer = QTimer()
        self.timer.timeout.connect(self.update_and_render)
        self.timer.start(16)  # ~60fps
        
        self.last_time = time.time()
        
        # 颜色配置
        self.colors = [
            (255, 105, 180),   # 热粉红
            (255, 182, 193),   # 浅粉红
            (255, 20, 147),    # 深粉红
            (255, 192, 203),   # 粉红
            (255, 110, 199),   # 亮粉
            (219, 112, 219),   # 兰花紫
            (255, 0, 127),     # 玫瑰红
            (255, 174, 185),   # 浅珊瑚
            (255, 255, 255),   # 白色闪烁
        ]
        
        # 提示文字
        self.show_hint = True
    
    def trigger_effect(self, center: Tuple[float, float]):
        """触发特效"""
        self.create_star_heart_particles(center, particle_count=300)
        self.show_hint = False
    
    def create_star_heart_particles(self, center: Tuple[float, float], particle_count: int = 300):
        """创建星空心心粒子"""
        
        for i in range(particle_count):
            p = Particle()
            layer = i % 5  # 5层结构
            p.layer = layer
            
            if layer == 0:
                # 第1层：心形轮廓 - 密集的小粒子
                t = 2 * math.pi * (i / (particle_count / 5))
                scale = 0.12
                heart_point = HeartCurve.get_point(t, scale=scale, center=center)
                p.x = heart_point[0] + random.uniform(-0.005, 0.005)
                p.y = heart_point[1] + random.uniform(-0.005, 0.005)
                p.size = random.uniform(2, 5)
                # 缓慢向外扩散
                angle = math.atan2(heart_point[1] - center[1], heart_point[0] - center[0])
                speed = random.uniform(0.01, 0.03)
                p.vx = math.cos(angle) * speed
                p.vy = math.sin(angle) * speed
                p.color = random.choice([(255, 255, 255), (255, 182, 193), (255, 192, 203)])
                p.glow = True
                p.lifetime = random.uniform(2.0, 2.8)
                
            elif layer == 1:
                # 第2层：心形内部填充
                t = random.uniform(0, 2 * math.pi)
                r = random.uniform(0.3, 0.95)
                scale = 0.12 * r
                heart_point = HeartCurve.get_point(t, scale=scale, center=center)
                p.x = heart_point[0] + random.uniform(-0.01, 0.01)
                p.y = heart_point[1] + random.uniform(-0.01, 0.01)
                p.size = random.uniform(2, 4)
                # 轻微上浮飘动
                p.vx = random.uniform(-0.005, 0.005)
                p.vy = random.uniform(-0.015, -0.005)
                p.color = random.choice(self.colors[:4])
                p.twinkle = True
                p.twinkle_speed = random.uniform(4, 8)
                p.lifetime = random.uniform(1.8, 2.5)
                
            elif layer == 2:
                # 第3层：外圈发光大粒子
                t = 2 * math.pi * (i / (particle_count / 5))
                scale = 0.15
                heart_point = HeartCurve.get_point(t, scale=scale, center=center)
                p.x = heart_point[0]
                p.y = heart_point[1]
                p.size = random.uniform(5, 10)
                # 向外扩散
                angle = math.atan2(heart_point[1] - center[1], heart_point[0] - center[0])
                speed = random.uniform(0.02, 0.05)
                p.vx = math.cos(angle) * speed + random.uniform(-0.01, 0.01)
                p.vy = math.sin(angle) * speed + random.uniform(-0.01, 0.01)
                p.color = random.choice(self.colors)
                p.glow = True
                p.lifetime = random.uniform(1.5, 2.2)
                
            elif layer == 3:
                # 第4层：随机星星背景
                angle = random.uniform(0, 2 * math.pi)
                dist = random.uniform(0.08, 0.25)
                p.x = center[0] + math.cos(angle) * dist
                p.y = center[1] + math.sin(angle) * dist
                p.size = random.uniform(1, 3)
                p.vx = random.uniform(-0.008, 0.008)
                p.vy = random.uniform(-0.015, 0.005)
                p.color = random.choice(self.colors)
                p.twinkle = True
                p.twinkle_speed = random.uniform(5, 12)
                p.glow = False
                p.lifetime = random.uniform(1.5, 2.5)
                
            else:
                # 第5层：中心爆发粒子
                angle = random.uniform(0, 2 * math.pi)
                speed = random.uniform(0.05, 0.12)
                p.x = center[0]
                p.y = center[1]
                p.vx = math.cos(angle) * speed
                p.vy = math.sin(angle) * speed - 0.02  # 轻微向上
                p.size = random.uniform(3, 7)
                p.color = random.choice([(255, 255, 255), (255, 182, 193)])
                p.glow = True
                p.lifetime = random.uniform(0.8, 1.5)
            
            # 旋转
            p.rotation = random.uniform(0, 360)
            p.rotation_speed = random.uniform(-60, 60)
            
            self.particles.append(p)
    
    def update_and_render(self):
        """更新并渲染"""
        current_time = time.time()
        dt = current_time - self.last_time
        self.last_time = current_time
        
        # 更新粒子
        self.particles = [p for p in self.particles if p.is_alive]
        for p in self.particles:
            p.update(dt)
        
        self.update()
    
    def paintEvent(self, event):
        """绑定事件"""
        painter = QPainter(self)
        painter.setRenderHint(QPainter.Antialiasing)
        
        w, h = self.width(), self.height()
        
        # 绘制背景渐变
        gradient = QLinearGradient(0, 0, 0, h)
        gradient.setColorAt(0, QColor(10, 10, 35))
        gradient.setColorAt(1, QColor(5, 5, 20))
        painter.fillRect(0, 0, w, h, gradient)
        
        # 按层级排序绘制（先绘制底层）
        sorted_particles = sorted(self.particles, key=lambda p: p.layer)
        
        for p in sorted_particles:
            if not p.is_alive:
                continue
            
            px = int(p.x * w)
            py = int(p.y * h)
            
            if px < 0 or px >= w or py < 0 or py >= h:
                continue
            
            # 计算透明度
            alpha = p.alpha
            if p.twinkle:
                twinkle = 0.5 + 0.5 * math.sin(p.age * p.twinkle_speed)
                alpha *= twinkle
            
            size = max(1, int(p.size * (0.5 + 0.5 * alpha)))
            
            # 发光效果
            if p.glow and size >= 2:
                for i in range(4, 0, -1):
                    glow_size = size + i * 4
                    glow_alpha = int(alpha * 40 / i)
                    glow_color = QColor(p.color[0], p.color[1], p.color[2], glow_alpha)
                    painter.setBrush(glow_color)
                    painter.setPen(Qt.NoPen)
                    painter.drawEllipse(QPoint(px, py), glow_size, glow_size)
            
            # 绘制星形或圆点
            color = QColor(p.color[0], p.color[1], p.color[2], int(alpha * 255))
            painter.setBrush(color)
            painter.setPen(Qt.NoPen)
            
            if size >= 4:
                self.draw_star(painter, px, py, size, p.rotation)
            else:
                painter.drawEllipse(QPoint(px, py), size, size)
        
        # 绘制提示文字
        if self.show_hint:
            painter.setPen(QColor(255, 255, 255, 180))
            font = QFont("Microsoft YaHei", 24)
            painter.setFont(font)
            text = "点击屏幕或按空格键触发特效"
            text_rect = painter.fontMetrics().boundingRect(text)
            painter.drawText(w // 2 - text_rect.width() // 2, h // 2, text)
        
        # 粒子数量
        painter.setPen(QColor(100, 100, 100))
        painter.setFont(QFont("Consolas", 12))
        painter.drawText(10, 25, f"粒子数: {len(self.particles)}")
    
    def draw_star(self, painter: QPainter, x: int, y: int, size: int, rotation: float):
        """绘制星形"""
        path = QPainterPath()
        points = []
        num_points = 4 if size < 6 else 5
        
        for i in range(num_points * 2):
            angle = math.radians(rotation) + i * math.pi / num_points - math.pi / 2
            r = size if i % 2 == 0 else size * 0.4
            px = x + r * math.cos(angle)
            py = y + r * math.sin(angle)
            points.append((px, py))
        
        path.moveTo(points[0][0], points[0][1])
        for px, py in points[1:]:
            path.lineTo(px, py)
        path.closeSubpath()
        
        painter.drawPath(path)
    
    def mousePressEvent(self, event):
        """鼠标点击"""
        x = event.x() / self.width()
        y = event.y() / self.height()
        self.trigger_effect((x, y))
    
    def keyPressEvent(self, event):
        """按键"""
        if event.key() == Qt.Key_Space:
            self.trigger_effect((0.5, 0.5))
        elif event.key() == Qt.Key_Escape:
            self.close()


def main():
    app = QApplication(sys.argv)
    window = StarHeartEffect()
    window.show()
    
    # 自动触发一次演示
    QTimer.singleShot(500, lambda: window.trigger_effect((0.5, 0.5)))
    
    sys.exit(app.exec_())


if __name__ == "__main__":
    main()
