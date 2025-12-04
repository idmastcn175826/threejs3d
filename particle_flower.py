import sys
import math
import random
from PyQt5.QtWidgets import QApplication, QWidget, QSystemTrayIcon, QMenu, QAction
from PyQt5.QtCore import Qt, QTimer, QPointF
from PyQt5.QtGui import QPainter, QColor, QIcon


def clamp(v, lo=0, hi=1):
    return max(lo, min(hi, v))


class Particle:
    """通用粒子"""
    def __init__(self):
        self.x = 0
        self.y = 0
        self.vx = 0
        self.vy = 0
        self.size = 1
        self.alpha = 1
        self.hue = 200
        self.life = 0
        self.max_life = 100


class ParticleFlower(QWidget):
    """全粒子花朵效果"""
    
    def __init__(self):
        super().__init__()
        self.setWindowFlags(
            Qt.FramelessWindowHint | Qt.WindowStaysOnTopHint | Qt.Tool
        )
        self.setAttribute(Qt.WA_TranslucentBackground)
        # 允许键盘输入，鼠标穿透
        from ctypes import windll, c_int, byref
        self.show()
        hwnd = int(self.winId())
        # 设置鼠标穿透但保留键盘输入
        GWL_EXSTYLE = -20
        WS_EX_TRANSPARENT = 0x20
        WS_EX_LAYERED = 0x80000
        style = windll.user32.GetWindowLongW(hwnd, GWL_EXSTYLE)
        windll.user32.SetWindowLongW(hwnd, GWL_EXSTYLE, style | WS_EX_TRANSPARENT | WS_EX_LAYERED)
        
        scr = QApplication.primaryScreen().geometry()
        self.setGeometry(scr)
        self.W, self.H = scr.width(), scr.height()
        self.cx, self.cy = self.W // 2, self.H // 2 - 50
        
        # 背景粒子 - 宇宙尘埃
        self.bg_particles = []
        for _ in range(2000):
            p = Particle()
            p.x = random.random() * self.W
            p.y = random.random() * self.H
            p.vx = (random.random() - 0.5) * 0.2
            p.vy = (random.random() - 0.5) * 0.2
            p.size = random.random() * 1.2 + 0.3
            p.hue = random.choice([200, 210, 220, 230, 240, 250, 260])
            p.phase = random.random() * math.pi * 2
            p.speed = random.random() * 2 + 1
            self.bg_particles.append(p)
        
        # 花瓣粒子
        self.petal_particles = []
        self.init_petal_particles()
        
        # 花心粒子
        self.center_particles = []
        self.init_center_particles()
        
        # 花茎粒子
        self.stem_particles = []
        self.init_stem_particles()
        
        # 流入粒子
        self.flow_particles = []
        for _ in range(200):
            self.flow_particles.append(self.create_flow_particle())
        
        self.time = 0
        self.timer = QTimer()
        self.timer.timeout.connect(self.tick)
        self.timer.start(16)
        
        # 系统托盘退出
        self.setup_tray()
    
    def setup_tray(self):
        """设置系统托盘"""
        self.tray = QSystemTrayIcon(self)
        self.tray.setIcon(self.style().standardIcon(self.style().SP_ComputerIcon))
        
        menu = QMenu()
        quit_action = QAction("退出特效", self)
        quit_action.triggered.connect(self.close_app)
        menu.addAction(quit_action)
        
        self.tray.setContextMenu(menu)
        self.tray.setToolTip("粒子花朵 - 右键托盘图标退出")
        self.tray.show()
        self.tray.showMessage("粒子花朵", "右键点击托盘图标退出", QSystemTrayIcon.Information, 3000)
    
    def close_app(self):
        """关闭应用"""
        self.tray.hide()
        QApplication.quit()
    
    def init_petal_particles(self):
        """初始化花瓣粒子"""
        # 3层花瓣，每层用粒子形成
        layers = [
            (6, 60, 35),    # (花瓣数, 长度, 宽度)
            (10, 85, 45),
            (14, 110, 55)
        ]
        
        for layer_idx, (num_petals, length, width) in enumerate(layers):
            for petal_idx in range(num_petals):
                base_angle = (petal_idx / num_petals) * math.pi * 2
                
                # 每个花瓣用多个粒子
                for i in range(120):
                    p = Particle()
                    # 花瓣形状分布
                    t = random.random()
                    spread = random.random() * width * 0.5
                    
                    p.petal_angle = base_angle
                    p.petal_dist = t * length
                    p.petal_spread = (random.random() - 0.5) * spread * (1 - t * 0.5)
                    p.layer = layer_idx
                    p.size = random.random() * 1.5 + 0.5
                    p.hue = 200 + random.random() * 40  # 蓝色系
                    p.phase = random.random() * math.pi * 2
                    p.speed = random.random() * 1.5 + 0.5
                    
                    self.petal_particles.append(p)
    
    def init_center_particles(self):
        """初始化花心粒子"""
        for _ in range(250):
            p = Particle()
            angle = random.random() * math.pi * 2
            dist = random.random() * 25
            p.center_angle = angle
            p.center_dist = dist
            p.size = random.random() * 1.8 + 0.8
            p.hue = 45 + random.random() * 20  # 金黄色
            p.phase = random.random() * math.pi * 2
            p.speed = random.random() * 2 + 1
            self.center_particles.append(p)
    
    def init_stem_particles(self):
        """初始化花茎粒子"""
        stem_length = 280
        for i in range(400):
            p = Particle()
            p.stem_t = random.random()  # 茎上的位置 0-1
            p.stem_offset = (random.random() - 0.5) * 8
            p.size = random.random() * 1.2 + 0.5
            p.hue = 120 + random.random() * 20  # 绿色
            p.phase = random.random() * math.pi * 2
            p.speed = random.random() * 1 + 0.5
            
            # 叶子粒子
            if 0.3 < p.stem_t < 0.4 or 0.5 < p.stem_t < 0.6 or 0.7 < p.stem_t < 0.8:
                p.is_leaf = True
                p.leaf_side = 1 if random.random() > 0.5 else -1
                p.leaf_spread = random.random() * 50 + 10
            else:
                p.is_leaf = False
            
            self.stem_particles.append(p)
    
    def create_flow_particle(self):
        """创建流入粒子"""
        p = Particle()
        angle = random.random() * math.pi * 2
        dist = random.random() * 200 + 250
        p.x = self.cx + math.cos(angle) * dist
        p.y = self.cy + math.sin(angle) * dist
        p.size = random.random() * 1.5 + 0.5
        p.hue = random.choice([200, 210, 220, 230, 45, 50])  # 蓝色+金色
        p.speed = random.random() * 4 + 2
        p.trail = []
        p.phase = random.random() * math.pi * 2
        return p
    
    def tick(self):
        self.time += 0.016
        
        # 更新背景粒子
        for p in self.bg_particles:
            p.x += p.vx
            p.y += p.vy
            # 边界循环
            if p.x < 0: p.x = self.W
            if p.x > self.W: p.x = 0
            if p.y < 0: p.y = self.H
            if p.y > self.H: p.y = 0
        
        # 更新流入粒子
        for p in self.flow_particles:
            dx = self.cx - p.x
            dy = self.cy - p.y
            dist = math.sqrt(dx*dx + dy*dy)
            
            if dist > 40:
                angle = math.atan2(dy, dx)
                spiral = math.sin(self.time * 2 + p.phase) * 0.4
                angle += spiral
                p.x += math.cos(angle) * p.speed
                p.y += math.sin(angle) * p.speed
                p.trail.insert(0, (p.x, p.y))
                if len(p.trail) > 12:
                    p.trail.pop()
            else:
                # 重置
                angle = random.random() * math.pi * 2
                dist = random.random() * 200 + 250
                p.x = self.cx + math.cos(angle) * dist
                p.y = self.cy + math.sin(angle) * dist
                p.trail = []
        
        self.update()
    
    def paintEvent(self, e):
        painter = QPainter(self)
        painter.setRenderHint(QPainter.Antialiasing)
        
        # 1. 背景粒子
        self.draw_bg_particles(painter)
        
        # 2. 流入粒子
        self.draw_flow_particles(painter)
        
        # 3. 花茎粒子
        self.draw_stem_particles(painter)
        
        # 4. 花瓣粒子
        self.draw_petal_particles(painter)
        
        # 5. 花心粒子
        self.draw_center_particles(painter)
    
    def draw_bg_particles(self, painter):
        """绘制背景粒子"""
        for p in self.bg_particles:
            alpha = 0.3 + 0.3 * abs(math.sin(self.time * p.speed + p.phase))
            color = QColor.fromHslF(clamp(p.hue / 360), 0.6, 0.6, clamp(alpha))
            painter.setBrush(color)
            painter.setPen(Qt.NoPen)
            painter.drawEllipse(QPointF(p.x, p.y), p.size, p.size)
    
    def draw_flow_particles(self, painter):
        """绘制流入粒子"""
        for p in self.flow_particles:
            # 尾迹
            for i, (tx, ty) in enumerate(p.trail):
                prog = i / 12
                alpha = (1 - prog) * 0.5
                size = p.size * (1 - prog * 0.5)
                hue = (p.hue + self.time * 20) % 360
                color = QColor.fromHslF(clamp(hue / 360), 0.8, 0.6, clamp(alpha))
                painter.setBrush(color)
                painter.setPen(Qt.NoPen)
                painter.drawEllipse(QPointF(tx, ty), size, size)
            
            # 主体发光
            hue = (p.hue + self.time * 20) % 360
            for i in range(2, 0, -1):
                gc = QColor.fromHslF(clamp(hue / 360), 0.7, 0.7, 0.15 / i)
                painter.setBrush(gc)
                painter.drawEllipse(QPointF(p.x, p.y), p.size + i * 2, p.size + i * 2)
            
            color = QColor.fromHslF(clamp(hue / 360), 0.9, 0.75, 0.9)
            painter.setBrush(color)
            painter.drawEllipse(QPointF(p.x, p.y), p.size, p.size)
    
    def draw_stem_particles(self, painter):
        """绘制花茎粒子"""
        stem_top = self.cy + 30
        stem_bottom = self.cy + 310
        stem_length = stem_bottom - stem_top
        
        sway = math.sin(self.time * 0.5) * 15
        
        for p in self.stem_particles:
            y = stem_top + p.stem_t * stem_length
            sway_factor = p.stem_t
            x = self.cx + sway * sway_factor + p.stem_offset
            
            # 叶子粒子
            if p.is_leaf:
                leaf_sway = math.sin(self.time * 0.7 + p.phase) * 0.2
                angle = (0.5 + leaf_sway) * p.leaf_side
                x += math.cos(angle) * p.leaf_spread
                y += math.sin(angle) * p.leaf_spread * 0.3
            
            alpha = 0.5 + 0.3 * math.sin(self.time * p.speed + p.phase)
            hue = (p.hue + self.time * 5) % 360
            color = QColor.fromHslF(clamp(hue / 360), 0.7, 0.45, clamp(alpha))
            
            # 发光
            gc = QColor(color)
            gc.setAlphaF(clamp(alpha * 0.3))
            painter.setBrush(gc)
            painter.setPen(Qt.NoPen)
            painter.drawEllipse(QPointF(x, y), p.size + 2, p.size + 2)
            
            painter.setBrush(color)
            painter.drawEllipse(QPointF(x, y), p.size, p.size)
    
    def draw_petal_particles(self, painter):
        """绘制花瓣粒子"""
        rotation = self.time * 0.15
        breathe = self.time * 2
        pulse = 1 + math.sin(breathe) * 0.08
        
        for p in self.petal_particles:
            angle = p.petal_angle + rotation
            wave = math.sin(self.time * 0.8 + p.phase) * 0.1
            angle += wave
            
            # 3D透视
            z_offset = [15, 8, 0][p.layer]
            z = z_offset + math.sin(self.time * 0.6 + p.phase) * 3
            persp = 400 / (400 + z)
            
            # 花瓣位置
            dist = (p.layer + 1) * 30 * persp * pulse
            base_x = self.cx + math.cos(angle) * dist
            base_y = self.cy + math.sin(angle) * dist * 0.5
            
            # 粒子在花瓣内的位置
            petal_angle = angle + math.pi / 2
            px = base_x + math.cos(petal_angle) * p.petal_dist * persp
            py = base_y + math.sin(petal_angle) * p.petal_dist * persp * 0.6
            
            # 加上横向展开
            spread_angle = angle
            px += math.cos(spread_angle) * p.petal_spread * persp
            py += math.sin(spread_angle) * p.petal_spread * persp * 0.5
            
            # 闪烁
            alpha = 0.5 + 0.4 * math.sin(self.time * p.speed * 2 + p.phase)
            # 边缘更透明
            edge_fade = 1 - (p.petal_dist / 110) * 0.4
            alpha *= edge_fade
            
            hue = (p.hue + self.time * 10) % 360
            sat = 0.7 + 0.15 * math.sin(self.time + p.phase)
            light = 0.5 + 0.15 * math.sin(self.time * 1.5 + p.phase)
            
            size = p.size * persp
            
            # 发光
            for i in range(2, 0, -1):
                gc = QColor.fromHslF(clamp(hue / 360), clamp(sat), clamp(light + 0.1), clamp(alpha * 0.2 / i))
                painter.setBrush(gc)
                painter.setPen(Qt.NoPen)
                painter.drawEllipse(QPointF(px, py), size + i * 2, size + i * 2)
            
            color = QColor.fromHslF(clamp(hue / 360), clamp(sat), clamp(light), clamp(alpha))
            painter.setBrush(color)
            painter.drawEllipse(QPointF(px, py), size, size)
    
    def draw_center_particles(self, painter):
        """绘制花心粒子"""
        for p in self.center_particles:
            angle = p.center_angle + self.time * 0.3
            dist = p.center_dist * (1 + math.sin(self.time * 2 + p.phase) * 0.15)
            
            x = self.cx + math.cos(angle) * dist
            y = self.cy + math.sin(angle) * dist * 0.6
            
            alpha = 0.6 + 0.4 * math.sin(self.time * p.speed * 2 + p.phase)
            hue = (p.hue + self.time * 15) % 360
            
            # 强发光
            for i in range(3, 0, -1):
                gc = QColor.fromHslF(clamp(hue / 360), 0.9, 0.7, clamp(alpha * 0.25 / i))
                painter.setBrush(gc)
                painter.setPen(Qt.NoPen)
                painter.drawEllipse(QPointF(x, y), p.size + i * 2.5, p.size + i * 2.5)
            
            color = QColor.fromHslF(clamp(hue / 360), 0.95, 0.65, clamp(alpha))
            painter.setBrush(color)
            painter.drawEllipse(QPointF(x, y), p.size, p.size)
    
    def keyPressEvent(self, e):
        if e.key() == Qt.Key_Escape:
            self.close()


if __name__ == "__main__":
    app = QApplication(sys.argv)
    w = ParticleFlower()
    w.show()
    print("=" * 50)
    print("✨ 全粒子花朵特效 ✨")
    print("=" * 50)
    print("• 500 背景宇宙粒子")
    print("• 1200 花瓣粒子(3层)")
    print("• 80 花心金色粒子")
    print("• 150 花茎+叶子粒子")
    print("• 100 流入粒子")
    print("=" * 50)
    print("按 ESC 退出")
    sys.exit(app.exec_())
