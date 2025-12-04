"""
Overlay Widget - 叠加层组件
负责绘制手势骨架、状态提示、安全区域等
"""

from PyQt5.QtWidgets import QWidget
from PyQt5.QtCore import Qt, QRect, QPoint, QTimer
from PyQt5.QtGui import QPainter, QPen, QColor, QFont, QBrush, QPainterPath
import math
from typing import List, Optional, Tuple

from ..domain.gesture import HandLandmarks, GestureType


class OverlayWidget(QWidget):
    """叠加层组件 - 绘制骨架、提示、安全区域"""
    
    def __init__(self, parent=None):
        super().__init__(parent)
        
        # 设置透明背景
        self.setAttribute(Qt.WA_TransparentForMouseEvents)
        self.setAttribute(Qt.WA_TranslucentBackground)
        
        # 数据
        self._landmarks: List[HandLandmarks] = []
        self._current_gesture: Optional[GestureType] = None
        self._gesture_name: str = ""
        self._fps: float = 0
        self._show_safe_zone: bool = True
        self._safe_zone: Tuple[float, float, float, float] = (0.2, 0.8, 0.2, 0.8)
        
        # 显示设置
        self._show_skeleton = True
        self._show_gesture_name = True
        self._show_fps = True
        
        # 动画状态
        self._action_feedback: Optional[str] = None
        self._action_feedback_timer = QTimer(self)
        self._action_feedback_timer.setSingleShot(True)
        self._action_feedback_timer.timeout.connect(self._clear_action_feedback)
        
        # 颜色配置
        self._skeleton_color = QColor(0, 255, 255, 200)
        self._joint_color = QColor(0, 255, 0, 230)
        self._safe_zone_color = QColor(100, 149, 237, 50)
        self._text_color = QColor(255, 255, 255, 230)
        self._feedback_color = QColor(50, 205, 50, 200)
    
    def set_landmarks(self, landmarks: List[HandLandmarks]):
        """设置手部关键点"""
        self._landmarks = landmarks
        self.update()
    
    def set_gesture(self, gesture: Optional[GestureType], name: str = ""):
        """设置当前手势"""
        self._current_gesture = gesture
        self._gesture_name = name
        self.update()
    
    def set_fps(self, fps: float):
        """设置FPS显示"""
        self._fps = fps
        self.update()
    
    def show_action_feedback(self, text: str, duration_ms: int = 1000):
        """显示动作反馈"""
        self._action_feedback = text
        self._action_feedback_timer.start(duration_ms)
        self.update()
    
    def _clear_action_feedback(self):
        """清除动作反馈"""
        self._action_feedback = None
        self.update()
    
    def set_safe_zone(self, x_min: float, x_max: float, y_min: float, y_max: float):
        """设置安全区域"""
        self._safe_zone = (x_min, x_max, y_min, y_max)
        self.update()
    
    def set_show_safe_zone(self, show: bool):
        """设置是否显示安全区域"""
        self._show_safe_zone = show
        self.update()
    
    def set_display_options(self, skeleton: bool = True, gesture: bool = True, fps: bool = True):
        """设置显示选项"""
        self._show_skeleton = skeleton
        self._show_gesture_name = gesture
        self._show_fps = fps
        self.update()
    
    def paintEvent(self, event):
        """绑定事件"""
        painter = QPainter(self)
        painter.setRenderHint(QPainter.Antialiasing)
        
        w, h = self.width(), self.height()
        
        # 绘制安全区域
        if self._show_safe_zone:
            self._draw_safe_zone(painter, w, h)
        
        # 绘制骨架
        if self._show_skeleton and self._landmarks:
            for landmarks in self._landmarks:
                self._draw_skeleton(painter, landmarks, w, h)
        
        # 绘制手势名称
        if self._show_gesture_name and self._gesture_name:
            self._draw_gesture_name(painter, w, h)
        
        # 绘制FPS
        if self._show_fps:
            self._draw_fps(painter, w, h)
        
        # 绘制动作反馈
        if self._action_feedback:
            self._draw_action_feedback(painter, w, h)
    
    def _draw_safe_zone(self, painter: QPainter, w: int, h: int):
        """绘制安全区域边框"""
        x_min, x_max, y_min, y_max = self._safe_zone
        
        x = int(x_min * w)
        y = int(y_min * h)
        width = int((x_max - x_min) * w)
        height = int((y_max - y_min) * h)
        
        # 绘制半透明填充
        painter.fillRect(x, y, width, height, self._safe_zone_color)
        
        # 绘制边框
        pen = QPen(QColor(100, 149, 237, 150))
        pen.setWidth(2)
        pen.setStyle(Qt.DashLine)
        painter.setPen(pen)
        painter.drawRect(x, y, width, height)
        
        # 标注
        painter.setPen(QColor(100, 149, 237, 200))
        font = QFont("Microsoft YaHei", 10)
        painter.setFont(font)
        painter.drawText(x + 5, y + 20, "安全区域")
    
    def _draw_skeleton(self, painter: QPainter, landmarks: HandLandmarks, w: int, h: int):
        """绘制手部骨架"""
        if len(landmarks.landmarks) < 21:
            return
        
        # 转换坐标
        points = [(int(lm[0] * w), int(lm[1] * h)) for lm in landmarks.landmarks]
        
        # 定义骨骼连接
        connections = [
            # 拇指
            (0, 1), (1, 2), (2, 3), (3, 4),
            # 食指
            (0, 5), (5, 6), (6, 7), (7, 8),
            # 中指
            (5, 9), (9, 10), (10, 11), (11, 12),
            # 无名指
            (9, 13), (13, 14), (14, 15), (15, 16),
            # 小指
            (13, 17), (0, 17), (17, 18), (18, 19), (19, 20)
        ]
        
        # 绘制连接线
        pen = QPen(self._skeleton_color)
        pen.setWidth(3)
        painter.setPen(pen)
        
        for start, end in connections:
            if start < len(points) and end < len(points):
                painter.drawLine(points[start][0], points[start][1],
                               points[end][0], points[end][1])
        
        # 绘制关节点
        for i, point in enumerate(points):
            # 指尖用大一点的圆
            if i in [4, 8, 12, 16, 20]:
                radius = 8
                color = QColor(255, 100, 100, 230)
            else:
                radius = 5
                color = self._joint_color
            
            painter.setBrush(QBrush(color))
            painter.setPen(QPen(Qt.white, 1))
            painter.drawEllipse(QPoint(point[0], point[1]), radius, radius)
    
    def _draw_gesture_name(self, painter: QPainter, w: int, h: int):
        """绘制手势名称"""
        font = QFont("Microsoft YaHei", 24, QFont.Bold)
        painter.setFont(font)
        
        # 绘制阴影
        painter.setPen(QColor(0, 0, 0, 150))
        painter.drawText(w // 2 - 100 + 2, 52, self._gesture_name)
        
        # 绘制文字
        painter.setPen(self._text_color)
        painter.drawText(w // 2 - 100, 50, self._gesture_name)
    
    def _draw_fps(self, painter: QPainter, w: int, h: int):
        """绘制FPS"""
        font = QFont("Consolas", 14)
        painter.setFont(font)
        
        fps_text = f"FPS: {self._fps:.1f}"
        
        # 根据FPS选择颜色
        if self._fps >= 25:
            color = QColor(50, 205, 50)
        elif self._fps >= 15:
            color = QColor(255, 165, 0)
        else:
            color = QColor(255, 69, 0)
        
        painter.setPen(color)
        painter.drawText(w - 100, 30, fps_text)
    
    def _draw_action_feedback(self, painter: QPainter, w: int, h: int):
        """绘制动作反馈"""
        font = QFont("Microsoft YaHei", 18, QFont.Bold)
        painter.setFont(font)
        
        # 绘制背景框
        text_width = len(self._action_feedback) * 20 + 40
        rect = QRect(w // 2 - text_width // 2, h // 2 - 30, text_width, 60)
        
        painter.setBrush(QBrush(QColor(0, 0, 0, 150)))
        painter.setPen(QPen(self._feedback_color, 2))
        painter.drawRoundedRect(rect, 10, 10)
        
        # 绘制文字
        painter.setPen(self._feedback_color)
        painter.drawText(rect, Qt.AlignCenter, self._action_feedback)


class ParticleOverlay(QWidget):
    """粒子特效叠加层"""
    
    def __init__(self, parent=None):
        super().__init__(parent)
        
        self.setAttribute(Qt.WA_TransparentForMouseEvents)
        self.setAttribute(Qt.WA_TranslucentBackground)
        
        self._particles = []
    
    def set_particles(self, particles: list):
        """设置粒子列表"""
        self._particles = particles
        self.update()
    
    def paintEvent(self, event):
        """绑定事件"""
        painter = QPainter(self)
        painter.setRenderHint(QPainter.Antialiasing)
        
        w, h = self.width(), self.height()
        
        for particle in self._particles:
            if not particle.is_alive:
                continue
            
            x = int(particle.x * w)
            y = int(particle.y * h)
            size = int(particle.size)
            
            # 颜色和透明度
            r, g, b = particle.color
            alpha = int(particle.alpha * 255)
            color = QColor(r, g, b, alpha)
            
            # 发光效果
            if particle.glow:
                for i in range(3, 0, -1):
                    glow_alpha = alpha // (i * 2)
                    glow_color = QColor(r, g, b, glow_alpha)
                    painter.setBrush(QBrush(glow_color))
                    painter.setPen(Qt.NoPen)
                    painter.drawEllipse(QPoint(x, y), size + i * 3, size + i * 3)
            
            # 绘制粒子
            painter.setBrush(QBrush(color))
            painter.setPen(Qt.NoPen)
            
            # 绘制星形
            if particle.size > 4:
                self._draw_star(painter, x, y, size, particle.rotation)
            else:
                painter.drawEllipse(QPoint(x, y), size, size)
    
    def _draw_star(self, painter: QPainter, x: int, y: int, size: int, rotation: float):
        """绘制星形"""
        path = QPainterPath()
        
        points = []
        for i in range(10):
            angle = math.radians(rotation + i * 36 - 90)
            r = size if i % 2 == 0 else size // 2
            px = x + r * math.cos(angle)
            py = y + r * math.sin(angle)
            points.append((px, py))
        
        path.moveTo(points[0][0], points[0][1])
        for px, py in points[1:]:
            path.lineTo(px, py)
        path.closeSubpath()
        
        painter.drawPath(path)
