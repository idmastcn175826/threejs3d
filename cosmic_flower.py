import sys
import math
import random
from PyQt5.QtWidgets import QApplication, QWidget
from PyQt5.QtCore import Qt, QTimer, QPointF, QPoint, QRectF
from PyQt5.QtGui import (QPainter, QColor, QPainterPath, QRadialGradient, 
                         QPen, QBrush, QLinearGradient, QPolygonF)


def clamp(v, lo=0, hi=1):
    return max(lo, min(hi, v))


class CosmicBackground:
    """宇宙背景"""
    def __init__(self, W, H):
        self.W = W
        self.H = H
        # 星云
        self.nebulas = []
        for _ in range(8):
            self.nebulas.append({
                'x': random.random() * W,
                'y': random.random() * H,
                'size': random.random() * 300 + 150,
                'hue': random.choice([220, 240, 260, 280, 200]),  # 蓝紫色系
                'phase': random.random() * math.pi * 2
            })
        
        # 星星 - 多层
        self.stars_far = []  # 远处小星星
        self.stars_mid = []  # 中等星星
        self.stars_near = []  # 近处亮星
        
        for _ in range(300):
            self.stars_far.append({
                'x': random.random() * W, 'y': random.random() * H,
                'size': random.random() * 1 + 0.3,
                'phase': random.random() * math.pi * 2,
                'speed': random.random() * 1 + 0.5
            })
        for _ in range(100):
            self.stars_mid.append({
                'x': random.random() * W, 'y': random.random() * H,
                'size': random.random() * 2 + 1,
                'phase': random.random() * math.pi * 2,
                'speed': random.random() * 2 + 1,
                'hue': random.choice([200, 220, 240, 180, 260])
            })
        for _ in range(30):
            self.stars_near.append({
                'x': random.random() * W, 'y': random.random() * H,
                'size': random.random() * 3 + 2,
                'phase': random.random() * math.pi * 2,
                'speed': random.random() * 3 + 2
            })
    
    def draw(self, painter, time):
        # 深空背景渐变
        grad = QLinearGradient(0, 0, self.W, self.H)
        grad.setColorAt(0, QColor(5, 5, 20))
        grad.setColorAt(0.3, QColor(10, 15, 40))
        grad.setColorAt(0.6, QColor(15, 10, 35))
        grad.setColorAt(1, QColor(5, 8, 25))
        painter.fillRect(0, 0, self.W, self.H, grad)
        
        # 星云
        for n in self.nebulas:
            pulse = 1 + math.sin(time * 0.3 + n['phase']) * 0.1
            size = n['size'] * pulse
            
            grad = QRadialGradient(n['x'], n['y'], size)
            hue = n['hue'] / 360
            c1 = QColor.fromHslF(clamp(hue), 0.6, 0.3, 0.15)
            c2 = QColor.fromHslF(clamp(hue + 0.05), 0.5, 0.2, 0.08)
            c3 = QColor.fromHslF(clamp(hue), 0.4, 0.1, 0)
            grad.setColorAt(0, c1)
            grad.setColorAt(0.5, c2)
            grad.setColorAt(1, c3)
            
            painter.setBrush(grad)
            painter.setPen(Qt.NoPen)
            painter.drawEllipse(QPointF(n['x'], n['y']), size, size * 0.6)
        
        # 远处星星
        for s in self.stars_far:
            alpha = 0.3 + 0.3 * abs(math.sin(time * s['speed'] + s['phase']))
            painter.setBrush(QColor(255, 255, 255, int(alpha * 255)))
            painter.setPen(Qt.NoPen)
            painter.drawEllipse(QPointF(s['x'], s['y']), s['size'], s['size'])
        
        # 中等星星
        for s in self.stars_mid:
            alpha = 0.4 + 0.4 * abs(math.sin(time * s['speed'] + s['phase']))
            hue = s['hue'] / 360
            color = QColor.fromHslF(clamp(hue), 0.5, 0.8, clamp(alpha))
            painter.setBrush(color)
            painter.drawEllipse(QPointF(s['x'], s['y']), s['size'], s['size'])
        
        # 近处亮星（带光芒）
        for s in self.stars_near:
            alpha = 0.6 + 0.4 * abs(math.sin(time * s['speed'] + s['phase']))
            x, y, size = s['x'], s['y'], s['size']
            
            # 光晕
            for i in range(3, 0, -1):
                gc = QColor(200, 220, 255, int(alpha * 50 / i))
                painter.setBrush(gc)
                painter.drawEllipse(QPointF(x, y), size + i * 3, size + i * 3)
            
            # 星芒
            painter.setPen(QPen(QColor(200, 220, 255, int(alpha * 100)), 1))
            length = size * 3
            painter.drawLine(QPointF(x - length, y), QPointF(x + length, y))
            painter.drawLine(QPointF(x, y - length), QPointF(x, y + length))
            
            painter.setBrush(QColor(255, 255, 255, int(alpha * 255)))
            painter.setPen(Qt.NoPen)
            painter.drawEllipse(QPointF(x, y), size, size)


class Petal:
    """花瓣"""
    def __init__(self, cx, cy, layer, idx, total):
        self.cx = cx
        self.cy = cy
        self.layer = layer
        self.idx = idx
        self.base_angle = (idx / total) * math.pi * 2
        
        if layer == 0:  # 内层
            self.length = 50 + random.random() * 15
            self.width = 25 + random.random() * 8
            self.z = 20
        elif layer == 1:  # 中层
            self.length = 75 + random.random() * 20
            self.width = 35 + random.random() * 10
            self.z = 10
        else:  # 外层
            self.length = 100 + random.random() * 25
            self.width = 45 + random.random() * 12
            self.z = 0
        
        self.curl = random.random() * 0.3 + 0.1
        self.hue_var = random.random() * 20 - 10
        self.phase = random.random() * math.pi * 2
    
    def draw(self, painter, time, rotation):
        angle = self.base_angle + rotation
        wave = math.sin(time * 0.8 + self.phase) * 0.08
        angle += wave
        
        # 3D效果
        z = self.z + math.sin(time * 0.5 + self.idx) * 5
        persp = 500 / (500 + z)
        
        # 位置
        dist = (self.layer + 1) * 25 * persp
        px = self.cx + math.cos(angle) * dist
        py = self.cy + math.sin(angle) * dist * 0.5 - 50  # 花朵位置上移
        
        length = self.length * persp
        width = self.width * persp
        
        # 蓝色系颜色
        base_hue = 210 + math.sin(time * 0.3) * 15 + self.hue_var
        if self.layer == 0:
            sat, light = 0.8, 0.55
        elif self.layer == 1:
            sat, light = 0.75, 0.5
        else:
            sat, light = 0.7, 0.45
        
        light += math.sin(time * 2 + self.phase) * 0.08
        
        painter.save()
        painter.translate(px, py)
        painter.rotate(math.degrees(angle) + 90)
        
        # 花瓣渐变
        grad = QLinearGradient(0, -length/2, 0, length/2)
        c1 = QColor.fromHslF(clamp(base_hue/360), clamp(sat), clamp(light + 0.15), 0.95)
        c2 = QColor.fromHslF(clamp((base_hue-10)/360), clamp(sat + 0.1), clamp(light), 0.9)
        c3 = QColor.fromHslF(clamp((base_hue-20)/360), clamp(sat), clamp(light - 0.1), 0.85)
        grad.setColorAt(0, c1)
        grad.setColorAt(0.5, c2)
        grad.setColorAt(1, c3)
        
        painter.setBrush(grad)
        painter.setPen(QPen(QColor.fromHslF(clamp((base_hue-20)/360), 0.8, 0.3, 0.5), 1))
        
        # 花瓣形状
        path = QPainterPath()
        path.moveTo(0, length * 0.4)
        path.cubicTo(-width * 0.6, length * 0.2, -width * 0.5, -length * 0.3, 0, -length * 0.5)
        path.cubicTo(width * 0.5, -length * 0.3, width * 0.6, length * 0.2, 0, length * 0.4)
        
        painter.drawPath(path)
        
        # 花瓣纹理
        painter.setPen(QPen(QColor(255, 255, 255, 30), 1))
        for i in range(3):
            y_pos = -length * 0.3 + i * length * 0.2
            painter.drawLine(QPointF(-width * 0.2, y_pos), QPointF(width * 0.2, y_pos + 5))
        
        painter.restore()


class FlowerCenter:
    """花心"""
    def __init__(self, cx, cy):
        self.cx = cx
        self.cy = cy - 50  # 与花瓣位置对齐
        self.dots = []
        for i in range(20):
            angle = random.random() * math.pi * 2
            dist = random.random() * 15
            self.dots.append({
                'angle': angle, 'dist': dist,
                'size': random.random() * 3 + 2,
                'phase': random.random() * math.pi * 2
            })
    
    def draw(self, painter, time):
        # 花心光晕
        grad = QRadialGradient(self.cx, self.cy, 35)
        grad.setColorAt(0, QColor.fromHslF(0.15, 0.9, 0.6, 0.9))  # 金黄色
        grad.setColorAt(0.5, QColor.fromHslF(0.12, 0.85, 0.5, 0.7))
        grad.setColorAt(1, QColor.fromHslF(0.1, 0.8, 0.4, 0))
        
        painter.setBrush(grad)
        painter.setPen(Qt.NoPen)
        pulse = 1 + math.sin(time * 3) * 0.1
        painter.drawEllipse(QPointF(self.cx, self.cy), 35 * pulse, 25 * pulse)
        
        # 花蕊点
        for d in self.dots:
            angle = d['angle'] + time * 0.2
            dist = d['dist'] * (1 + math.sin(time * 2 + d['phase']) * 0.2)
            x = self.cx + math.cos(angle) * dist
            y = self.cy + math.sin(angle) * dist * 0.7
            
            alpha = 0.7 + 0.3 * math.sin(time * 3 + d['phase'])
            color = QColor.fromHslF(0.12, 0.9, 0.65, clamp(alpha))
            painter.setBrush(color)
            size = d['size'] * (1 + math.sin(time * 4 + d['phase']) * 0.2)
            painter.drawEllipse(QPointF(x, y), size, size * 0.8)


class Stem:
    """花茎"""
    def __init__(self, cx, cy):
        self.cx = cx
        self.top_y = cy - 50  # 连接花朵
        self.bottom_y = cy + 300
        self.control_points = []
        # 生成曲线控制点
        for i in range(5):
            y = self.top_y + i * (self.bottom_y - self.top_y) / 4
            offset = math.sin(i * 0.8) * 20
            self.control_points.append((cx + offset, y))
    
    def draw(self, painter, time):
        # 茎的摆动
        sway = math.sin(time * 0.5) * 10
        
        # 绘制茎
        path = QPainterPath()
        path.moveTo(self.cx + sway * 0.2, self.top_y)
        
        points = [(self.cx + sway * 0.2, self.top_y)]
        for i, (bx, by) in enumerate(self.control_points):
            sway_factor = (i + 1) / len(self.control_points)
            points.append((bx + sway * sway_factor, by))
        
        # 贝塞尔曲线
        for i in range(1, len(points)):
            x1, y1 = points[i-1]
            x2, y2 = points[i]
            cx1 = x1
            cy1 = (y1 + y2) / 2
            path.quadTo(cx1, cy1, x2, y2)
        
        # 茎渐变
        grad = QLinearGradient(self.cx, self.top_y, self.cx, self.bottom_y)
        grad.setColorAt(0, QColor(50, 120, 50))
        grad.setColorAt(0.5, QColor(40, 100, 45))
        grad.setColorAt(1, QColor(30, 80, 35))
        
        painter.setPen(QPen(QBrush(grad), 8, Qt.SolidLine, Qt.RoundCap))
        painter.setBrush(Qt.NoBrush)
        painter.drawPath(path)
        
        # 茎的高光
        painter.setPen(QPen(QColor(100, 180, 100, 100), 2))
        painter.drawPath(path)


class Leaf:
    """叶子"""
    def __init__(self, cx, stem_top_y, side, y_offset):
        self.cx = cx
        self.y = stem_top_y + y_offset
        self.side = side  # -1左, 1右
        self.size = random.random() * 30 + 50
        self.angle = (random.random() * 20 + 30) * side
        self.phase = random.random() * math.pi * 2
    
    def draw(self, painter, time):
        sway = math.sin(time * 0.6 + self.phase) * 5
        
        painter.save()
        
        # 叶子位置
        stem_sway = math.sin(time * 0.5) * 10
        x = self.cx + stem_sway * (self.y - (self.y - 100)) / 300 + self.side * 10
        
        painter.translate(x, self.y)
        painter.rotate(self.angle + sway)
        
        # 叶子渐变
        grad = QLinearGradient(0, 0, self.size * self.side, 0)
        grad.setColorAt(0, QColor(45, 110, 50, 230))
        grad.setColorAt(0.5, QColor(60, 140, 60, 220))
        grad.setColorAt(1, QColor(50, 120, 55, 200))
        
        painter.setBrush(grad)
        painter.setPen(QPen(QColor(30, 80, 35), 1))
        
        # 叶子形状
        path = QPainterPath()
        w = self.size
        h = self.size * 0.4
        
        path.moveTo(0, 0)
        path.cubicTo(w * 0.3 * self.side, -h * 0.5, w * 0.7 * self.side, -h * 0.3, w * self.side, 0)
        path.cubicTo(w * 0.7 * self.side, h * 0.3, w * 0.3 * self.side, h * 0.5, 0, 0)
        
        painter.drawPath(path)
        
        # 叶脉
        painter.setPen(QPen(QColor(80, 160, 80, 150), 1))
        painter.drawLine(QPointF(0, 0), QPointF(w * 0.85 * self.side, 0))
        for i in range(1, 5):
            vx = w * 0.2 * i * self.side
            painter.drawLine(QPointF(vx, 0), QPointF(vx + 10 * self.side, -8))
            painter.drawLine(QPointF(vx, 0), QPointF(vx + 10 * self.side, 8))
        
        painter.restore()


class EnergyParticle:
    """能量粒子 - 流向花朵"""
    def __init__(self, cx, cy, W, H):
        self.cx = cx
        self.cy = cy - 50
        self.W = W
        self.H = H
        self.reset()
    
    def reset(self):
        angle = random.random() * math.pi * 2
        dist = random.random() * 300 + 200
        self.x = self.cx + math.cos(angle) * dist
        self.y = self.cy + math.sin(angle) * dist
        self.size = random.random() * 2 + 1
        self.speed = random.random() * 2 + 1.5
        self.trail = []
        self.hue = random.choice([200, 210, 220, 230, 190])
        self.alpha = 0.8
        self.life = 0
    
    def update(self, time):
        self.life += 1
        dx = self.cx - self.x
        dy = self.cy - self.y
        dist = math.sqrt(dx*dx + dy*dy)
        
        if dist > 30:
            angle = math.atan2(dy, dx)
            spiral = math.sin(self.life * 0.08) * 0.3
            angle += spiral
            self.x += math.cos(angle) * self.speed
            self.y += math.sin(angle) * self.speed
            self.trail.insert(0, (self.x, self.y))
            if len(self.trail) > 15:
                self.trail.pop()
        else:
            self.reset()
        
        self.cur_hue = (self.hue + time * 15) % 360
        self.alpha = min(1, 0.4 + (1 - dist / 400) * 0.6)
    
    def draw(self, painter):
        for i, (tx, ty) in enumerate(self.trail):
            prog = i / 15
            alpha = (1 - prog) * self.alpha * 0.5
            size = self.size * (1 - prog * 0.5)
            color = QColor.fromHslF(clamp(self.cur_hue / 360), 0.8, 0.6, clamp(alpha))
            painter.setBrush(color)
            painter.setPen(Qt.NoPen)
            painter.drawEllipse(QPointF(tx, ty), size, size)
        
        # 发光
        for i in range(2, 0, -1):
            gc = QColor.fromHslF(clamp(self.cur_hue / 360), 0.7, 0.7, clamp(self.alpha * 0.2 / i))
            painter.setBrush(gc)
            painter.drawEllipse(QPointF(self.x, self.y), self.size + i * 2, self.size + i * 2)
        
        color = QColor.fromHslF(clamp(self.cur_hue / 360), 0.9, 0.75, clamp(self.alpha))
        painter.setBrush(color)
        painter.drawEllipse(QPointF(self.x, self.y), self.size, self.size)


class CosmicFlower(QWidget):
    """宇宙之花"""
    
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
        
        # 宇宙背景
        self.background = CosmicBackground(self.W, self.H)
        
        # 花瓣
        self.petals = []
        for i in range(6):
            self.petals.append(Petal(self.cx, self.cy, 0, i, 6))
        for i in range(10):
            self.petals.append(Petal(self.cx, self.cy, 1, i, 10))
        for i in range(14):
            self.petals.append(Petal(self.cx, self.cy, 2, i, 14))
        
        # 花心
        self.center = FlowerCenter(self.cx, self.cy)
        
        # 花茎
        self.stem = Stem(self.cx, self.cy)
        
        # 叶子
        self.leaves = [
            Leaf(self.cx, self.cy - 50, -1, 120),
            Leaf(self.cx, self.cy - 50, 1, 180),
            Leaf(self.cx, self.cy - 50, -1, 250),
        ]
        
        # 能量粒子
        self.particles = [EnergyParticle(self.cx, self.cy, self.W, self.H) for _ in range(60)]
        
        self.time = 0
        self.rotation = 0
        
        self.timer = QTimer()
        self.timer.timeout.connect(self.tick)
        self.timer.start(16)
    
    def tick(self):
        self.time += 0.016
        self.rotation += 0.005
        
        for p in self.particles:
            p.update(self.time)
        
        self.update()
    
    def paintEvent(self, e):
        painter = QPainter(self)
        painter.setRenderHint(QPainter.Antialiasing)
        
        # 1. 宇宙背景
        self.background.draw(painter, self.time)
        
        # 2. 能量粒子
        for p in self.particles:
            p.draw(painter)
        
        # 3. 花茎
        self.stem.draw(painter, self.time)
        
        # 4. 叶子
        for leaf in self.leaves:
            leaf.draw(painter, self.time)
        
        # 5. 花朵光晕
        self.draw_flower_glow(painter)
        
        # 6. 花瓣（从外到内）
        for layer in [2, 1, 0]:
            for petal in self.petals:
                if petal.layer == layer:
                    petal.draw(painter, self.time, self.rotation)
        
        # 7. 花心
        self.center.draw(painter, self.time)
    
    def draw_flower_glow(self, painter):
        cy = self.cy - 50
        pulse = 1 + math.sin(self.time * 2) * 0.15
        
        for i in range(4, 0, -1):
            radius = 80 + i * 30
            alpha = 0.1 / i
            hue = (210 + self.time * 10) % 360
            
            grad = QRadialGradient(self.cx, cy, radius * pulse)
            c1 = QColor.fromHslF(clamp(hue/360), 0.7, 0.5, clamp(alpha))
            c2 = QColor.fromHslF(clamp(hue/360), 0.6, 0.4, 0)
            grad.setColorAt(0, c1)
            grad.setColorAt(1, c2)
            
            painter.setBrush(grad)
            painter.setPen(Qt.NoPen)
            painter.drawEllipse(QPointF(self.cx, cy), radius * pulse, radius * pulse * 0.6)
    
    def keyPressEvent(self, e):
        if e.key() == Qt.Key_Escape:
            self.close()


if __name__ == "__main__":
    app = QApplication(sys.argv)
    w = CosmicFlower()
    w.show()
    print("=" * 50)
    print("🌸 宇宙之花特效已启动 🌸")
    print("=" * 50)
    print("• 蓝色花瓣三层(6+10+14=30片)")
    print("• 金色花心旋转")
    print("• 绿色花茎摆动")
    print("• 三片叶子")
    print("• 浩瀚宇宙背景")
    print("• 能量粒子流入")
    print("=" * 50)
    print("按 ESC 退出")
    sys.exit(app.exec_())
