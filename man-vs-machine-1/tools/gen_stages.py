"""Generates the three stage backgrounds as layered pixel art.

Each stage writes assets/backgrounds/<id>/{far,crowd,mid,floor}.png.
far/crowd/mid are 720px wide (parallax room), floor is 640x360 with the
fighting floor starting at y=300 (fighters stand at y=318)."""
import math
import os
import random

from png import Image, hexc

ROOT = os.path.normpath(os.path.join(os.path.dirname(__file__), '..'))
BAYER = [[0, 8, 2, 10], [12, 4, 14, 6], [3, 11, 1, 9], [15, 7, 13, 5]]


class C(Image):
    def rect(self, x, y, w, h, c):
        for yy in range(max(0, int(y)), min(self.h, int(y + h))):
            for xx in range(max(0, int(x)), min(self.w, int(x + w))):
                self.blend(xx, yy, c)

    def vgrad(self, x, y, w, h, c0, c1, steps=6):
        """Banded vertical gradient with ordered dithering between bands."""
        for yy in range(int(y), int(y + h)):
            t = (yy - y) / max(1, h - 1) * (steps - 1)
            band = int(t)
            frac = t - band
            ca = mix(c0, c1, band / (steps - 1))
            cb = mix(c0, c1, min(steps - 1, band + 1) / (steps - 1))
            for xx in range(int(x), int(x + w)):
                c = cb if frac * 16 > BAYER[yy % 4][xx % 4] else ca
                self.blend(xx, yy, c)

    def poly(self, pts, c):
        ys = [p[1] for p in pts]
        for yy in range(max(0, int(min(ys))), min(self.h, int(max(ys)) + 1)):
            xs = []
            n = len(pts)
            for i in range(n):
                x1, y1 = pts[i]
                x2, y2 = pts[(i + 1) % n]
                if (y1 <= yy + 0.5 < y2) or (y2 <= yy + 0.5 < y1):
                    xs.append(x1 + (yy + 0.5 - y1) * (x2 - x1) / (y2 - y1))
            xs.sort()
            for i in range(0, len(xs) - 1, 2):
                for xx in range(int(round(xs[i])), int(round(xs[i + 1]))):
                    self.blend(xx, yy, c)

    def circle(self, cx, cy, r, c, ring=0):
        for yy in range(int(cy - r - 1), int(cy + r + 2)):
            for xx in range(int(cx - r - 1), int(cx + r + 2)):
                d = math.hypot(xx + 0.5 - cx, yy + 0.5 - cy)
                if d <= r and (ring == 0 or d >= r - ring):
                    self.blend(xx, yy, c)

    def line(self, x0, y0, x1, y1, c, w=1):
        n = int(max(abs(x1 - x0), abs(y1 - y0))) + 1
        for i in range(n + 1):
            t = i / n
            x, y = x0 + (x1 - x0) * t, y0 + (y1 - y0) * t
            self.rect(int(x), int(y), w, w, c)

    def glow(self, cx, cy, r, col, strength=0.6):
        """Additive soft light, quantised into rings for a pixel-art look."""
        for yy in range(max(0, int(cy - r)), min(self.h, int(cy + r))):
            for xx in range(max(0, int(cx - r)), min(self.w, int(cx + r))):
                d = math.hypot(xx - cx, yy - cy) / r
                if d >= 1:
                    continue
                k = round((1 - d) * 4) / 4 * strength
                if k <= 0:
                    continue
                p = self.px[yy * self.w + xx]
                if p is None:
                    self.px[yy * self.w + xx] = (col[0], col[1], col[2], int(255 * k * 0.6))
                else:
                    self.px[yy * self.w + xx] = (min(255, int(p[0] + col[0] * k)), min(255, int(p[1] + col[1] * k)),
                                                 min(255, int(p[2] + col[2] * k)), p[3])

    def cone(self, x, y, top_w, bot_w, h, col, a=40):
        for yy in range(int(y), int(y + h)):
            t = (yy - y) / h
            w = top_w + (bot_w - top_w) * t
            al = int(a * (1 - t) * (0.6 + 0.4 * (BAYER[yy % 4][0] / 16)))
            for xx in range(int(x - w / 2), int(x + w / 2)):
                if BAYER[yy % 4][xx % 4] < 12:
                    self.blend(xx, yy, (col[0], col[1], col[2], al))


def mix(a, b, t):
    return tuple(int(a[i] + (b[i] - a[i]) * t) for i in range(4))


def H(h, a=255):
    return hexc(h, a)


def save(img, sid, name):
    d = os.path.join(ROOT, 'assets', 'backgrounds', sid)
    os.makedirs(d, exist_ok=True)
    img.save(os.path.join(d, name + '.png'))


def girder(c, x, y, w, h, dark, mid, light, vertical=True):
    c.rect(x, y, w, h, mid)
    if vertical:
        c.rect(x, y, 3, h, light)
        c.rect(x + w - 3, y, 3, h, dark)
        for yy in range(int(y) + 6, int(y + h), 18):
            c.line(x + 3, yy, x + w - 4, yy + 12, dark)
            c.line(x + w - 4, yy, x + 3, yy + 12, dark)
    else:
        c.rect(x, y, w, 2, light)
        c.rect(x, y + h - 2, w, 2, dark)


def steel_floor(c, y0, base, seam, hi, stripe=None, center_col=None):
    """Perspective steel floor converging to the screen centre."""
    W, Hh = c.w, c.h
    c.vgrad(0, y0, W, Hh - y0, mix(base, H('#000000'), 0.35), base, 5)
    cx = W / 2
    # perspective seams
    for i in range(-14, 15):
        xb = cx + i * 64
        xt = cx + i * 30
        c.line(xt, y0, xb, Hh, seam)
    # depth rows
    for k, yy in enumerate([y0 + 6, y0 + 15, y0 + 28, y0 + 46]):
        if yy < Hh:
            c.rect(0, yy, W, 1, seam)
            c.rect(0, yy + 1, W, 1, hi)
    if stripe:
        for xx in range(0, W):
            c.set(xx, y0, stripe[1])
            c.set(xx, y0 + 1, stripe[1])
            col = stripe[0] if ((xx + 0) // 8) % 2 == 0 else stripe[1]
            for yy in range(y0 + 2, y0 + 5):
                c.set(xx, yy, col if ((xx - yy) // 6) % 2 == 0 else stripe[1])
    if center_col:
        # painted centre emblem (flattened ellipse)
        for yy in range(y0 + 14, y0 + 40):
            for xx in range(int(cx - 110), int(cx + 110)):
                d = ((xx - cx) / 105) ** 2 + ((yy - (y0 + 27)) / 12) ** 2
                if 0.78 < d < 1.0:
                    c.blend(xx, yy, center_col)


# ===================================================================== STAGE 1
def industrial_arena():
    random.seed(1)
    sid = 'industrial_arena'
    far = C(720, 360, H('#101218'))
    far.vgrad(0, 0, 720, 300, H('#0b0c12'), H('#262a36'), 7)
    # back wall panels
    for x in range(0, 720, 48):
        far.rect(x, 120, 1, 180, H('#0c0d12'))
        far.rect(x + 1, 120, 1, 180, H('#30343f'))
    for y in (150, 210, 262):
        far.rect(0, y, 720, 1, H('#0c0d12'))
    # big ventilation fan
    for cx in (130, 590):
        far.circle(cx, 205, 34, H('#1a1c24'))
        far.circle(cx, 205, 34, H('#3a3e4a'), 3)
        for k in range(6):
            a = k * math.pi / 3 + 0.3
            far.poly([(cx, 205), (cx + math.cos(a) * 30, 205 + math.sin(a) * 30),
                      (cx + math.cos(a + 0.45) * 30, 205 + math.sin(a + 0.45) * 30)], H('#2a2e38'))
        far.circle(cx, 205, 6, H('#4a4f5c'))
    # balcony with railing (crowd stands behind it)
    far.rect(0, 108, 720, 12, H('#1e2028'))
    far.rect(0, 108, 720, 2, H('#4a4f5c'))
    # roof trusses
    for x in range(-20, 720, 120):
        girder(far, x + 50, 0, 16, 120, H('#14161c'), H('#2c303a'), H('#4a505e'))
    girder(far, 0, 30, 720, 10, H('#14161c'), H('#2c303a'), H('#4a505e'), False)
    # lamp cones
    for i in range(4):
        x = 80 + i * 160 + 40
        far.rect(x - 8, 40, 16, 6, H('#3a3e4a'))
        far.cone(x, 46, 14, 120, 250, H('#ffd890'), 34)
        far.glow(x, 46, 20, H('#ffd080'), 0.5)
    # chain-link fence lower wall
    for x in range(0, 720, 8):
        for y in range(220, 300, 8):
            far.set(x + (y // 8) % 2 * 4, y, H('#3a3e48'))
    save(far, sid, 'far')

    crowd = C(720, 360)
    for x in range(0, 720, 11):
        h = random.randint(16, 26)
        sh = random.choice([H('#07080c'), H('#0b0c12'), H('#0f1118')])
        crowd.circle(x + 5, 108 - h + 3, 4.5, sh)
        crowd.rect(x, 108 - h + 7, 11, h - 7, sh)
        if random.random() < 0.3:   # raised fists
            crowd.rect(x + 8, 108 - h - 6, 3, 10, sh)
        if random.random() < 0.08:  # camera flash
            crowd.glow(x + 5, 108 - h, 6, H('#ffffff'), 0.9)
    crowd.rect(0, 104, 720, 2, H('#5a606e'))
    for x in range(0, 720, 20):
        crowd.rect(x, 96, 2, 10, H('#5a606e'))
    save(crowd, sid, 'crowd')

    mid = C(720, 360)
    # side steel platforms with crates / barrels (outside the central fight area)
    for (x0, flip) in ((0, 1), (560, -1)):
        mid.rect(x0, 236, 160, 8, H('#4a4f5c'))
        mid.rect(x0, 244, 160, 3, H('#1a1c24'))
        for k in range(3):
            mid.rect(x0 + 10 + k * 50, 247, 6, 55, H('#2a2d36'))
        bx = x0 + (20 if flip > 0 else 90)
        mid.rect(bx, 204, 32, 32, H('#5a3e22'))
        mid.rect(bx, 204, 32, 2, H('#8a6a3e'))
        mid.line(bx, 204, bx + 31, 235, H('#3a2814'))
        mid.line(bx + 31, 204, bx, 235, H('#3a2814'))
        mid.rect(bx + 40 * flip if flip > 0 else bx - 30, 212, 22, 24, H('#7a1a14'))
        mid.rect(bx + 40 * flip if flip > 0 else bx - 30, 218, 22, 3, H('#c8a030'))
    # hanging chains
    for x in (210, 510):
        for y in range(0, 70, 4):
            mid.rect(x, y, 2, 3, H('#5a5e6a'))
        mid.rect(x - 4, 70, 10, 6, H('#5a5e6a'))
    save(mid, sid, 'mid')

    floor = C(640, 360)
    steel_floor(floor, 300, H('#3a3e48'), H('#22252c'), H('#5a606c'),
                stripe=(H('#e8b420'), H('#1a1a1a')), center_col=H('#b82a20', 140))
    for x in range(10, 640, 40):
        for y in (308, 322, 342):
            floor.set(x + (y % 7), y, H('#7a808c'))
    save(floor, sid, 'floor')


# ===================================================================== STAGE 2
def neon_foundry():
    random.seed(2)
    sid = 'neon_foundry'
    far = C(720, 360, H('#070a16'))
    far.vgrad(0, 0, 720, 300, H('#04060e'), H('#122046'), 7)
    # molten furnace glow at the back
    far.glow(360, 260, 240, H('#ff6a10'), 0.35)
    # factory windows
    for x in range(20, 720, 70):
        far.rect(x, 30, 44, 52, H('#0a1022'))
        far.rect(x, 30, 44, 52, H('#2a3c6a'), )
        far.rect(x + 2, 32, 40, 48, H('#0c1630'))
        far.rect(x + 21, 32, 2, 48, H('#2a3c6a'))
        far.rect(x + 2, 55, 40, 2, H('#2a3c6a'))
        far.glow(x + 22, 56, 26, H('#3060ff'), 0.25)
    # assembly-line robot arms silhouettes
    for x in (110, 300, 480, 640):
        far.rect(x, 150, 18, 120, H('#0a0e1c'))
        far.poly([(x + 9, 150), (x + 50, 118), (x + 56, 126), (x + 15, 160)], H('#0e1426'))
        far.poly([(x + 50, 118), (x + 80, 150), (x + 72, 154), (x + 46, 128)], H('#0e1426'))
        far.circle(x + 9, 150, 8, H('#16203a'))
        far.circle(x + 52, 122, 6, H('#16203a'))
        far.glow(x + 78, 152, 12, H('#ff9030'), 0.8)
    # glowing conduits (pulses animated in-engine)
    for i, y in enumerate((96, 142, 188)):
        far.rect(0, y - 3, 720, 7, H('#0e1830'))
        far.rect(0, y - 1, 720, 3, H('#1a8cd0'))
        far.rect(0, y, 720, 1, H('#80f0ff'))
        for x in range(30 + i * 40, 720, 130):
            far.rect(x, y - 6, 8, 13, H('#2a3c6a'))
    for x in (60, 660):
        far.rect(x - 3, 0, 7, 300, H('#0e1830'))
        far.rect(x - 1, 0, 3, 300, H('#ff8a20'))
        far.rect(x, 0, 1, 300, H('#ffe0a0'))
    # molten vats
    for x in (40, 600):
        far.rect(x, 240, 80, 60, H('#1a1418'))
        far.rect(x + 4, 236, 72, 8, H('#ff7a18'))
        far.rect(x + 8, 236, 64, 3, H('#ffe080'))
        far.glow(x + 40, 238, 50, H('#ff6a10'), 0.6)
    save(far, sid, 'far')

    mid = C(720, 360)
    # overhead conveyor with robot torsos on hooks
    mid.rect(0, 58, 720, 6, H('#2a3346'))
    mid.rect(0, 58, 720, 1, H('#5a6a8a'))
    for k, x in enumerate(range(20, 720, 90)):
        mid.rect(x + 14, 64, 2, 16, H('#5a6a8a'))
        mid.poly([(x, 80), (x + 30, 80), (x + 26, 108), (x + 4, 108)], H('#26324e'))
        mid.rect(x + 2, 80, 26, 2, H('#6a80b0'))
        mid.circle(x + 15, 90, 3, H('#ff9a34') if k % 2 else H('#38e0ff'))
    # foreground pillars at the edges
    for x in (0, 690):
        mid.rect(x, 0, 30, 300, H('#141c30'))
        mid.rect(x + (26 if x == 0 else 0), 0, 4, 300, H('#38e0ff'))
        for y in range(20, 300, 40):
            mid.rect(x + 6, y, 18, 4, H('#e06a12'))
    save(mid, sid, 'mid')

    floor = C(640, 360)
    steel_floor(floor, 300, H('#1a2238'), H('#0a0e1a'), H('#2c3a5c'), stripe=(H('#38e0ff'), H('#0a0e1a')))
    # grating holes with orange underglow
    for y in range(312, 360, 9):
        for x in range(4, 640, 12):
            floor.rect(x + (y // 9 % 2) * 6, y, 6, 2, H('#ff7a18', 110))
    save(floor, sid, 'floor')


# ===================================================================== STAGE 3
def machine_core():
    random.seed(3)
    sid = 'machine_core'
    far = C(720, 360, H('#050306'))
    far.vgrad(0, 0, 720, 300, H('#030204'), H('#2a0a0e'), 7)
    cx, cy = 360, 132
    # the enormous central machine: concentric armoured rings around a red eye
    far.glow(cx, cy, 200, H('#ff1a10'), 0.3)
    for r, col, w in ((128, H('#1a1218'), 26), (100, H('#2a1c26'), 10), (84, H('#130c12'), 20), (60, H('#3a2834'), 6),
                      (50, H('#0e080c'), 14), (34, H('#4a3442'), 4)):
        far.circle(cx, cy, r, col, w)
    for k in range(16):
        a = k * math.pi / 8
        x0, y0 = cx + math.cos(a) * 104, cy + math.sin(a) * 104
        x1, y1 = cx + math.cos(a) * 126, cy + math.sin(a) * 126
        far.line(x0, y0, x1, y1, H('#5a4450'), 2)
    for k in range(8):
        a = k * math.pi / 4 + 0.2
        far.circle(cx + math.cos(a) * 92, cy + math.sin(a) * 92, 3, H('#ff3020'))
    far.circle(cx, cy, 30, H('#2a0408'))
    far.circle(cx, cy, 22, H('#8a0a0a'))
    far.circle(cx, cy, 14, H('#ff2a1a'))
    far.circle(cx, cy, 6, H('#ffd0b0'))
    # support pylons and cables
    for x in (120, 600):
        far.poly([(x - 30, 300), (x - 12, 40), (x + 12, 40), (x + 30, 300)], H('#120c12'))
        far.line(x - 12, 40, x - 12, 300, H('#3a2834'))
        for y in range(60, 300, 30):
            far.rect(x - 8, y, 16, 3, H('#ff2a1a', 160))
    for i in range(14):
        x0 = random.randint(0, 720)
        sag = random.randint(20, 70)
        x1 = x0 + random.randint(-140, 140)
        for t in range(0, 101):
            tt = t / 100
            x = x0 + (x1 - x0) * tt
            y = 10 + sag * math.sin(math.pi * tt) + 30 * tt
            far.rect(int(x), int(y), 2, 2, H('#0a0608'))
    # side walls with hazard light boxes
    for x in (0, 660):
        far.rect(x, 0, 60, 300, H('#0c080c'))
        far.rect(x + (56 if x == 0 else 0), 0, 4, 300, H('#3a2834'))
    save(far, sid, 'far')

    mid = C(720, 360)
    for x in (40, 600):
        mid.rect(x - 8, 66, 16, 16, H('#1a1218'))   # beacon housings (light animated in-engine)
        mid.rect(x - 10, 82, 20, 4, H('#3a2834'))
    # foreground conduits framing the arena
    for x in (0, 696):
        mid.rect(x, 0, 24, 300, H('#100a10'))
        mid.rect(x + 8, 0, 8, 300, H('#2a1c26'))
        for y in range(10, 300, 24):
            mid.rect(x + 4, y, 16, 3, H('#5a4450'))
    save(mid, sid, 'mid')

    floor = C(640, 360)
    steel_floor(floor, 300, H('#1e161c'), H('#0a0608'), H('#3a2a34'), stripe=(H('#ff2a1a'), H('#140a0e')))
    # hex grate with red underglow
    for y in range(308, 360, 10):
        for x in range(0, 640, 14):
            xx = x + (7 if (y // 10) % 2 else 0)
            floor.poly([(xx, y + 3), (xx + 3, y), (xx + 8, y), (xx + 11, y + 3), (xx + 8, y + 6), (xx + 3, y + 6)], H('#ff1a10', 70))
    save(floor, sid, 'floor')


if __name__ == '__main__':
    industrial_arena()
    neon_foundry()
    machine_core()
    print('stages done')
