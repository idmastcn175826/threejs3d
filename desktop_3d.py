import sys
import math
import random
from PyQt5.QtWidgets import QApplication, QWidget
from PyQt5.QtCore import Qt, QTimer, QPointF, QPoint
from PyQt5.QtGui import QPainter, QColor, QPainterPath, QRadialGradient, QPen


class Star:
    def __init__(self, W, H):
        self.x = random.random() * W
        self.y = random.random() * H
        self.size = random.random() * 2 + 0.5
        self.phase = random.random() * math.pi * 2
        self.speed = random.random() * 2 + 1
        self.hue = random.random() * 360

    def update(self, t):
        self.alpha = 0.2 + 0.3 * abs(math.sin(t * self.speed + self.phase))
        self.cur_hue = (self.hue + t * 20) % 360

    def draw(self, p):
        c = QColor.fromHslF(self.cur_hue / 360, 0.5, 0.8, self.alpha)
        p.setBrush(c)
        p.setPen(Qt.NoPen)
        p.drawEllipse(QPointF(self.x, self.y), self.size, self.size)


class Orb:
    def __init__(self, W, H):
        self.W, self.H = W, H
        self.reset()

    def reset(self):
        self.x = random.random() * self.W
        self.y = random.random() * self.H
        self.z = random.random() * 200 + 50
        self.base_size = random.random() * 30 + 10
        self.vx = (random.random() - 0.5) * 0.5
        self.vy = (random.random() - 0.5) * 0.3 - 0.2
        self.phase = random.random() * math.pi * 2
        self.hue = random.choice([330, 280, 200, 190, 170])

    def update(self, t):
        self.x += self.vx + math.sin(t + self.phase) * 0.3
        self.y += self.vy
        if self.x < -50: self.x = self.W + 50
        if self.x > self.W + 50: self.x = -50
        if self.y < -50:
            self.y = self.H + 50
            self.x = random.random() * self.W
        self.size = self.base_size * (150 / self.z)
        self.alpha = 0.15 * (100 / self.z)
        self.cur_hue = (self.hue + t * 15) % 360

    def draw(self, p, t):
        g = QRadialGradient(self.x, self.y, self.size)
        c = QColor.fromHslF(self.cur_hue / 360, 0.7, 0.6, self.alpha)
        g.setColorAt(0, c)
        c.setAlphaF(0)
        g.setColorAt(1, c)
        p.setBrush(g)
        p.setPen(Qt.NoPen)
        p.drawEllipse(QPointF(self.x, self.y), self.size, self.size)


class HeartParticle:
    def __init__(self, cx, cy, scale, layer):
        self.cx, self.cy, self.scale, self.layer = cx, cy, scale, layer
        self.reset()

    def reset(self):
        t = random.random() * math.pi * 2
        self.t = t
        hx = 16 * (math.sin(t) ** 3)
        hy = -(13 * math.cos(t) - 5 * math.cos(2*t) - 2 * math.cos(3*t) - math.cos(4*t))
        
        if self.layer == 0:
            r = random.random() * 0.5
            self.z = random.random() * 40 - 20
        elif self.layer == 1:
            r = 0.3 + random.random() * 0.7
            self.z = random.random() * 60 - 30
        else:
            r = 0.8 + random.random() * 0.4
            self.z = random.random() * 80 - 40
            self.prog = 0
            self.spd = random.random() * 0.006 + 0.003

        self.bx = hx * r
        self.by = hy * r
        self.bsize = random.random() * 3 + 1 if self.layer < 2 else random.random() * 4 + 2
        self.phase = random.random() * math.pi * 2
        self.wspd = random.random() * 2 + 0.5
        self.hue_off = random.random() * 60

    def update(self, time, breathe, rot_y):
        pulse = 1 + math.sin(breathe) * 0.08
        x3d = self.bx * self.scale * pulse
        z3d = self.z
        cos_r, sin_r = math.cos(rot_y), math.sin(rot_y)
        x_rot = x3d * cos_r - z3d * sin_r
        z_rot = x3d * sin_r + z3d * cos_r
        persp = 500
        sc3d = persp / (persp + z_rot)
        wx = math.sin(time * self.wspd + self.phase) * 2
        wy = math.cos(time * self.wspd * 0.8 + self.phase) * 2
        self.x = self.cx + x_rot * sc3d + wx
        self.y = self.cy + self.by * self.scale * pulse * sc3d + wy
        self.size = self.bsize * sc3d * (0.8 + 0.2 * math.sin(time * 2 + self.phase))
        d_alpha = 0.5 + 0.5 * sc3d
        twinkle = 0.6 + 0.4 * math.sin(time * self.wspd * 3 + self.phase)
        self.alpha = d_alpha * twinkle
        self.depth = z_rot

        if self.layer == 2:
            self.prog += self.spd
            if self.prog > 1:
                self.reset()
                return
            exp = 1 + self.prog * 0.8
            self.x = self.cx + x_rot * sc3d * exp
            self.y = self.cy + self.by * self.scale * pulse * sc3d * exp
            self.alpha *= (1 - self.prog)

    def get_color(self, t):
        cyc = (t * 25 + self.hue_off + self.t * 20) % 360
        if self.layer == 0:
            sat, lit = 0.3 + 0.2 * math.sin(t * 2), 0.85 + 0.1 * math.sin(t * 3)
        elif self.layer == 1:
            sat, lit = 0.6 + 0.2 * math.sin(t * 1.5), 0.65 + 0.15 * math.sin(t * 2)
        else:
            sat, lit = 0.75 + 0.15 * math.sin(t), 0.55 + 0.15 * math.sin(t * 1.5)
        h = max(0, min(1, cyc / 360))
        s = max(0, min(1, sat))
        l = max(0, min(1, lit))
        a = max(0, min(1, self.alpha))
        return QColor.fromHslF(h, s, l, a)


class Stream:
    def __init__(self, cx, cy, scale):
        self.cx, self.cy, self.scale = cx, cy, scale
        self.reset()

    def reset(self):
        ang = random.random() * math.pi * 2
        dist = self.scale * (20 + random.random() * 15)
        self.x = self.cx + math.cos(ang) * dist
        self.y = self.cy + math.sin(ang) * dist
        self.trail = [(self.x, self.y)]
        self.spd = random.random() * 4 + 3
        self.life = 0
        self.max_life = 80 + random.random() * 60
        self.hue = random.choice([340, 300, 220, 190])
        self.size = random.random() * 2 + 1

    def update(self, t):
        self.life += 1
        if self.life > self.max_life:
            self.reset()
            return
        dx, dy = self.cx - self.x, self.cy - self.y
        dist = math.sqrt(dx*dx + dy*dy)
        if dist > self.scale * 5:
            self.x += (dx / dist) * self.spd
            self.y += (dy / dist) * self.spd
            self.trail.insert(0, (self.x, self.y))
            if len(self.trail) > 25:
                self.trail.pop()
        else:
            self.reset()
        self.cur_hue = (self.hue + t * 30) % 360

    def draw(self, p, t):
        for i, (tx, ty) in enumerate(self.trail):
            prog = i / len(self.trail)
            alpha = (1 - prog) * 0.8
            sz = self.size * (1 - prog * 0.5)
            c = QColor.fromHslF(self.cur_hue / 360, 0.8, 0.6 + prog * 0.2, alpha)
            p.setBrush(c)
            p.setPen(Qt.NoPen)
            p.drawEllipse(QPointF(tx, ty), sz, sz)


class Desktop3D(QWidget):
    def __init__(self):
        super().__init__()
        self.setWindowFlags(Qt.FramelessWindowHint | Qt.WindowStaysOnTopHint | Qt.Tool | Qt.WindowTransparentForInput)
        self.setAttribute(Qt.WA_TranslucentBackground)
        self.setAttribute(Qt.WA_TransparentForMouseEvents)
        
        scr = QApplication.primaryScreen().geometry()
        self.setGeometry(scr)
        self.W, self.H = scr.width(), scr.height()
        self.cx, self.cy = self.W // 2, self.H // 2
        self.scale = min(self.W, self.H) / 50

        self.stars = [Star(self.W, self.H) for _ in range(200)]
        self.orbs = [Orb(self.W, self.H) for _ in range(25)]
        self.particles = []
        for _ in range(200): self.particles.append(HeartParticle(self.cx, self.cy, self.scale, 0))
        for _ in range(350): self.particles.append(HeartParticle(self.cx, self.cy, self.scale, 1))
        for _ in range(100): self.particles.append(HeartParticle(self.cx, self.cy, self.scale, 2))
        self.streams = [Stream(self.cx, self.cy, self.scale) for _ in range(20)]
        self.sparkles = [self.mk_sparkle() for _ in range(35)]

        self.time = 0
        self.rot_y = 0
        self.timer = QTimer()
        self.timer.timeout.connect(self.tick)
        self.timer.start(16)

    def mk_sparkle(self):
        t = random.random() * math.pi * 2
        r = random.random() * 1.1
        hx = 16 * (math.sin(t) ** 3) * r
        hy = -(13 * math.cos(t) - 5 * math.cos(2*t) - 2 * math.cos(3*t) - math.cos(4*t)) * r
        return {'x': self.cx + hx * self.scale, 'y': self.cy + hy * self.scale,
                'life': random.random() * 30, 'max': 30 + random.random() * 40,
                'size': random.random() * 4 + 2, 'hue': random.random() * 360}

    def tick(self):
        self.time += 0.016
        self.rot_y = math.sin(self.time * 0.3) * 0.4
        br = self.time * 2.5
        for s in self.stars: s.update(self.time)
        for o in self.orbs: o.update(self.time)
        for p in self.particles: p.update(self.time, br, self.rot_y)
        for s in self.streams: s.update(self.time)
        for s in self.sparkles:
            s['life'] += 1
            if s['life'] > s['max']:
                s.update(self.mk_sparkle())
        self.update()

    def paintEvent(self, e):
        p = QPainter(self)
        p.setRenderHint(QPainter.Antialiasing)
        for s in self.stars: s.draw(p)
        for o in self.orbs: o.draw(p, self.time)
        for s in self.streams: s.draw(p, self.time)
        self.draw_glow(p)
        for pt in sorted(self.particles, key=lambda x: x.depth, reverse=True):
            self.draw_pt(p, pt)
        for s in self.sparkles: self.draw_spk(p, s)

    def draw_pt(self, p, pt):
        if pt.alpha < 0.05 or pt.size < 0.5: return
        c = pt.get_color(self.time)
        for i in range(3, 0, -1):
            gc = QColor(c)
            gc.setAlphaF(min(1, c.alphaF() * 0.3 / i))
            p.setBrush(gc)
            p.setPen(Qt.NoPen)
            p.drawEllipse(QPointF(pt.x, pt.y), pt.size + i * 3, pt.size + i * 3)
        p.setBrush(c)
        p.drawEllipse(QPointF(pt.x, pt.y), pt.size, pt.size)

    def draw_spk(self, p, s):
        prog = s['life'] / s['max']
        alpha = math.sin(prog * math.pi) * 0.9
        sz = s['size'] * (0.5 + 0.5 * math.sin(prog * math.pi))
        if alpha < 0.1: return
        hue = (s['hue'] + self.time * 40) % 360
        c = QColor.fromHslF(hue / 360, 0.5, 0.9, alpha)
        x, y = int(s['x']), int(s['y'])
        p.setBrush(c)
        p.setPen(Qt.NoPen)
        p.fillRect(x - int(sz * 4), y - 1, int(sz * 8), 2, c)
        p.fillRect(x - 1, y - int(sz * 4), 2, int(sz * 8), c)
        p.drawEllipse(QPoint(x, y), int(sz * 1.5), int(sz * 1.5))

    def draw_glow(self, p):
        pulse = 1 + math.sin(self.time * 2.5) * 0.08
        hue1 = (self.time * 25) % 360
        path = QPainterPath()
        first = True
        for i in range(100):
            t = i / 100 * math.pi * 2
            hx = 16 * (math.sin(t) ** 3)
            hy = -(13 * math.cos(t) - 5 * math.cos(2*t) - 2 * math.cos(3*t) - math.cos(4*t))
            x3d = hx * self.scale * pulse
            cos_r, sin_r = math.cos(self.rot_y), math.sin(self.rot_y)
            x_rot = x3d * cos_r
            persp = 500
            sc3d = persp / (persp + x3d * sin_r)
            x = self.cx + x_rot * sc3d
            y = self.cy + hy * self.scale * pulse * sc3d
            if first:
                path.moveTo(x, y)
                first = False
            else:
                path.lineTo(x, y)
        path.closeSubpath()
        for i in range(6, 0, -1):
            c = QColor.fromHslF(hue1 / 360, 0.8, 0.6, 0.12 / i)
            pen = QPen(c, i * 4)
            p.setPen(pen)
            p.setBrush(Qt.NoBrush)
            p.drawPath(path)

    def keyPressEvent(self, e):
        if e.key() == Qt.Key_Escape:
            self.close()


if __name__ == "__main__":
    app = QApplication(sys.argv)
    w = Desktop3D()
    w.show()
    print("=" * 50)
    print("3D立体桌面特效已启动")
    print("按 ESC 退出")
    print("=" * 50)
    sys.exit(app.exec_())
