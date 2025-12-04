import sys
import math
import random
from PyQt5.QtWidgets import QApplication, QWidget
from PyQt5.QtCore import Qt, QTimer, QPointF, QPoint
from PyQt5.QtGui import QPainter, QColor, QPainterPath, QRadialGradient, QPen, QBrush, QLinearGradient


def clamp(v, lo=0, hi=1):
    return max(lo, min(hi, v))


class RosePetal:
    """玫瑰花瓣 - 使用玫瑰曲线"""
    def __init__(self, cx, cy, layer, petal_idx, total_petals):
        self.cx = cx
        self.cy = cy
        self.layer = layer  # 0=内层, 1=中层, 2=外层
        self.petal_idx = petal_idx
        self.total = total_petals
        self.base_angle = (petal_idx / total_petals) * math.pi * 2
        
        # 花瓣大小随层级增大
        if layer == 0:
            self.size = 25 + random.random() * 10
            self.z_offset = 15
        elif layer == 1:
            self.size = 40 + random.random() * 15
            self.z_offset = 5
        else:
            self.size = 55 + random.random() * 20
            self.z_offset = -5
        
        self.curl = random.random() * 0.3 + 0.2  # 花瓣卷曲程度
        self.hue_var = random.random() * 15 - 7  # 颜色变化

    def draw(self, painter, time, rotation, base_hue):
        angle = self.base_angle + rotation + math.sin(time * 0.5 + self.petal_idx) * 0.1
        
        # 3D透视
        z = self.z_offset + math.sin(time * 0.8 + self.petal_idx * 0.5) * 3
        perspective = 400 / (400 + z)
        
        # 花瓣中心位置
        dist = (self.layer + 1) * 18 * perspective
        px = self.cx + math.cos(angle) * dist
        py = self.cy + math.sin(angle) * dist * 0.6  # 椭圆形分布
        
        # 花瓣大小
        size = self.size * perspective
        
        # 花瓣颜色 - 内深外浅
        hue = (base_hue + self.hue_var) % 360
        if self.layer == 0:
            sat, light = 0.85, 0.35
        elif self.layer == 1:
            sat, light = 0.8, 0.45
        else:
            sat, light = 0.75, 0.55
        
        # 呼吸效果
        light += math.sin(time * 2 + self.petal_idx) * 0.05
        
        color = QColor.fromHslF(clamp(hue/360), clamp(sat), clamp(light), 0.9)
        
        # 绘制花瓣形状
        self.draw_petal_shape(painter, px, py, size, angle + math.pi/2, color, perspective)

    def draw_petal_shape(self, painter, x, y, size, angle, color, persp):
        painter.save()
        painter.translate(x, y)
        painter.rotate(math.degrees(angle))
        
        # 花瓣渐变
        grad = QRadialGradient(0, -size * 0.3, size)
        grad.setColorAt(0, color.lighter(130))
        grad.setColorAt(0.5, color)
        grad.setColorAt(1, color.darker(120))
        
        painter.setBrush(grad)
        painter.setPen(QPen(color.darker(150), 1))
        
        # 花瓣路径 - 心形变体
        path = QPainterPath()
        w = size * 0.6
        h = size
        
        path.moveTo(0, h * 0.4)
        path.cubicTo(-w * 0.8, h * 0.2, -w, -h * 0.3, 0, -h * 0.5)
        path.cubicTo(w, -h * 0.3, w * 0.8, h * 0.2, 0, h * 0.4)
        
        painter.drawPath(path)
        painter.restore()


class Rose:
    """完整的3D玫瑰"""
    def __init__(self, cx, cy):
        self.cx = cx
        self.cy = cy
        self.petals = []
        
        # 创建多层花瓣
        # 内层 - 紧密卷曲
        for i in range(5):
            self.petals.append(RosePetal(cx, cy, 0, i, 5))
        # 中层
        for i in range(8):
            self.petals.append(RosePetal(cx, cy, 1, i, 8))
        # 外层 - 展开
        for i in range(12):
            self.petals.append(RosePetal(cx, cy, 2, i, 12))
    
    def draw(self, painter, time, rotation):
        # 玫瑰红色调 - 流光变化
        base_hue = 350 + math.sin(time * 0.3) * 10  # 340-360 红色范围
        
        # 按层级从外到内绘制
        for layer in [2, 1, 0]:
            for petal in self.petals:
                if petal.layer == layer:
                    petal.draw(painter, time, rotation, base_hue)
        
        # 花心
        self.draw_center(painter, time, base_hue)
    
    def draw_center(self, painter, time, base_hue):
        # 花心 - 深红色螺旋
        painter.save()
        painter.translate(self.cx, self.cy)
        
        for i in range(8):
            angle = i * math.pi / 4 + time * 0.5
            dist = 5 + i * 2
            x = math.cos(angle) * dist
            y = math.sin(angle) * dist * 0.6
            
            size = 8 - i * 0.5
            color = QColor.fromHslF(clamp((base_hue - 10) / 360), 0.9, 0.25 + i * 0.02, 0.9)
            
            painter.setBrush(color)
            painter.setPen(Qt.NoPen)
            painter.drawEllipse(QPointF(x, y), size, size * 0.7)
        
        painter.restore()


class FlowParticle:
    """流向玫瑰的粒子"""
    def __init__(self, cx, cy, W, H):
        self.cx = cx
        self.cy = cy
        self.W = W
        self.H = H
        self.reset()
    
    def reset(self):
        # 从屏幕边缘或远处生成
        edge = random.randint(0, 3)
        if edge == 0:  # 上
            self.x = random.random() * self.W
            self.y = -20
        elif edge == 1:  # 下
            self.x = random.random() * self.W
            self.y = self.H + 20
        elif edge == 2:  # 左
            self.x = -20
            self.y = random.random() * self.H
        else:  # 右
            self.x = self.W + 20
            self.y = random.random() * self.H
        
        self.size = random.random() * 3 + 1
        self.speed = random.random() * 3 + 2
        self.trail = []
        self.max_trail = 20
        self.hue = random.choice([340, 350, 0, 10, 320, 280])  # 红粉紫
        self.life = 0
        self.alpha = 0.8
    
    def update(self, time):
        self.life += 1
        
        # 向玫瑰中心移动，带有螺旋效果
        dx = self.cx - self.x
        dy = self.cy - self.y
        dist = math.sqrt(dx*dx + dy*dy)
        
        if dist > 30:
            # 螺旋轨迹
            angle = math.atan2(dy, dx)
            spiral = math.sin(self.life * 0.1) * 0.5
            angle += spiral
            
            self.x += math.cos(angle) * self.speed
            self.y += math.sin(angle) * self.speed
            
            self.trail.insert(0, (self.x, self.y, self.alpha))
            if len(self.trail) > self.max_trail:
                self.trail.pop()
        else:
            # 到达中心，融入玫瑰
            self.reset()
        
        # 接近时变亮
        self.alpha = min(1, 0.5 + (1 - dist / 500) * 0.5)
        self.cur_hue = (self.hue + time * 20) % 360
    
    def draw(self, painter):
        # 绘制尾迹
        for i, (tx, ty, a) in enumerate(self.trail):
            progress = i / self.max_trail
            alpha = (1 - progress) * a * 0.6
            size = self.size * (1 - progress * 0.5)
            
            color = QColor.fromHslF(clamp(self.cur_hue / 360), 0.8, 0.6, clamp(alpha))
            painter.setBrush(color)
            painter.setPen(Qt.NoPen)
            painter.drawEllipse(QPointF(tx, ty), size, size)
        
        # 绘制主体
        color = QColor.fromHslF(clamp(self.cur_hue / 360), 0.9, 0.7, clamp(self.alpha))
        
        # 发光
        for i in range(3, 0, -1):
            gc = QColor(color)
            gc.setAlphaF(clamp(self.alpha * 0.2 / i))
            painter.setBrush(gc)
            painter.drawEllipse(QPointF(self.x, self.y), self.size + i * 2, self.size + i * 2)
        
        painter.setBrush(color)
        painter.drawEllipse(QPointF(self.x, self.y), self.size, self.size)


class Sparkle:
    """玫瑰周围的闪光"""
    def __init__(self, cx, cy):
        self.cx = cx
        self.cy = cy
        self.reset()
    
    def reset(self):
        angle = random.random() * math.pi * 2
        dist = random.random() * 80 + 20
        self.x = self.cx + math.cos(angle) * dist
        self.y = self.cy + math.sin(angle) * dist
        self.life = 0
        self.max_life = 30 + random.random() * 40
        self.size = random.random() * 3 + 1
        self.hue = random.choice([350, 0, 340, 320])
    
    def update(self):
        self.life += 1
        if self.life > self.max_life:
            self.reset()
    
    def draw(self, painter, time):
        progress = self.life / self.max_life
        alpha = math.sin(progress * math.pi) * 0.8
        size = self.size * (0.5 + 0.5 * alpha)
        
        if alpha < 0.1:
            return
        
        hue = (self.hue + time * 30) % 360
        color = QColor.fromHslF(clamp(hue / 360), 0.6, 0.85, clamp(alpha))
        
        painter.setBrush(color)
        painter.setPen(Qt.NoPen)
        
        x, y = int(self.x), int(self.y)
        # 十字闪光
        painter.fillRect(x - int(size * 3), y, int(size * 6), 1, color)
        painter.fillRect(x, y - int(size * 3), 1, int(size * 6), color)
        painter.drawEllipse(QPoint(x, y), int(size), int(size))


class BackgroundStar:
    """背景星星"""
    def __init__(self, W, H):
        self.x = random.random() * W
        self.y = random.random() * H
        self.size = random.random() * 1.5 + 0.5
        self.phase = random.random() * math.pi * 2
        self.speed = random.random() * 2 + 1
        self.hue = random.choice([350, 340, 320, 280, 220])
    
    def draw(self, painter, time):
        alpha = 0.2 + 0.3 * abs(math.sin(time * self.speed + self.phase))
        hue = (self.hue + time * 10) % 360
        color = QColor.fromHslF(clamp(hue / 360), 0.5, 0.8, clamp(alpha))
        painter.setBrush(color)
        painter.setPen(Qt.NoPen)
        painter.drawEllipse(QPointF(self.x, self.y), self.size, self.size)


class FloatingPetal:
    """漂浮的花瓣"""
    def __init__(self, W, H):
        self.W = W
        self.H = H
        self.reset()
    
    def reset(self):
        self.x = random.random() * self.W
        self.y = -30
        self.size = random.random() * 15 + 10
        self.rotation = random.random() * 360
        self.rot_speed = random.random() * 2 - 1
        self.fall_speed = random.random() * 1 + 0.5
        self.sway = random.random() * 2 + 1
        self.phase = random.random() * math.pi * 2
        self.hue = 350 + random.random() * 20 - 10
        self.alpha = random.random() * 0.3 + 0.2
    
    def update(self, time):
        self.y += self.fall_speed
        self.x += math.sin(time * self.sway + self.phase) * 0.5
        self.rotation += self.rot_speed
        
        if self.y > self.H + 30:
            self.reset()
    
    def draw(self, painter, time):
        painter.save()
        painter.translate(self.x, self.y)
        painter.rotate(self.rotation)
        
        color = QColor.fromHslF(clamp(self.hue / 360), 0.7, 0.5, clamp(self.alpha))
        painter.setBrush(color)
        painter.setPen(Qt.NoPen)
        
        # 简化花瓣形状
        path = QPainterPath()
        s = self.size
        path.moveTo(0, s * 0.5)
        path.cubicTo(-s * 0.4, s * 0.2, -s * 0.4, -s * 0.3, 0, -s * 0.5)
        path.cubicTo(s * 0.4, -s * 0.3, s * 0.4, s * 0.2, 0, s * 0.5)
        painter.drawPath(path)
        
        painter.restore()


class RoseDesktop(QWidget):
    """3D旋转玫瑰桌面特效"""
    
    def __init__(self):
        super().__init__()
        self.setWindowFlags(
            Qt.FramelessWindowHint | Qt.WindowStaysOnTopHint |
            Qt.Tool | Qt.WindowTransparentForInput
        )
        self.setAttribute(Qt.WA_TranslucentBackground)
        self.setAttribute(Qt.WA_TransparentForMouseEvents)
        
        scr = QApplication.primaryScreen().geometry()
        self.setGeometry(scr)
        self.W, self.H = scr.width(), scr.height()
        self.cx, self.cy = self.W // 2, self.H // 2
        
        # 创建玫瑰
        self.rose = Rose(self.cx, self.cy)
        
        # 流向玫瑰的粒子
        self.particles = [FlowParticle(self.cx, self.cy, self.W, self.H) for _ in range(80)]
        
        # 闪光
        self.sparkles = [Sparkle(self.cx, self.cy) for _ in range(40)]
        
        # 背景星星
        self.stars = [BackgroundStar(self.W, self.H) for _ in range(150)]
        
        # 漂浮花瓣
        self.petals = [FloatingPetal(self.W, self.H) for _ in range(20)]
        
        self.time = 0
        self.rotation = 0
        
        self.timer = QTimer()
        self.timer.timeout.connect(self.tick)
        self.timer.start(16)
    
    def tick(self):
        self.time += 0.016
        self.rotation += 0.008  # 缓慢旋转
        
        for p in self.particles:
            p.update(self.time)
        for s in self.sparkles:
            s.update()
        for p in self.petals:
            p.update(self.time)
        
        self.update()
    
    def paintEvent(self, e):
        painter = QPainter(self)
        painter.setRenderHint(QPainter.Antialiasing)
        
        # 1. 背景星星
        for s in self.stars:
            s.draw(painter, self.time)
        
        # 2. 漂浮花瓣
        for p in self.petals:
            p.draw(painter, self.time)
        
        # 3. 流入粒子
        for p in self.particles:
            p.draw(painter)
        
        # 4. 玫瑰光环
        self.draw_rose_glow(painter)
        
        # 5. 玫瑰
        self.rose.draw(painter, self.time, self.rotation)
        
        # 6. 闪光
        for s in self.sparkles:
            s.draw(painter, self.time)
    
    def draw_rose_glow(self, painter):
        """玫瑰周围的光晕"""
        pulse = 1 + math.sin(self.time * 2) * 0.1
        
        for i in range(5, 0, -1):
            radius = 100 + i * 20
            alpha = 0.08 / i
            hue = (350 + self.time * 10) % 360
            
            grad = QRadialGradient(self.cx, self.cy, radius * pulse)
            c1 = QColor.fromHslF(clamp(hue / 360), 0.8, 0.5, clamp(alpha))
            c2 = QColor.fromHslF(clamp(hue / 360), 0.8, 0.5, 0)
            grad.setColorAt(0, c1)
            grad.setColorAt(1, c2)
            
            painter.setBrush(grad)
            painter.setPen(Qt.NoPen)
            painter.drawEllipse(QPointF(self.cx, self.cy), radius * pulse, radius * pulse * 0.7)
    
    def keyPressEvent(self, e):
        if e.key() == Qt.Key_Escape:
            self.close()


if __name__ == "__main__":
    app = QApplication(sys.argv)
    w = RoseDesktop()
    w.show()
    print("=" * 50)
    print("🌹 3D旋转玫瑰特效已启动 🌹")
    print("=" * 50)
    print("• 真实花瓣层叠")
    print("• 动态缓慢旋转")
    print("• 粒子螺旋流入")
    print("• 漂浮花瓣装饰")
    print("=" * 50)
    print("按 ESC 退出")
    sys.exit(app.exec_())
