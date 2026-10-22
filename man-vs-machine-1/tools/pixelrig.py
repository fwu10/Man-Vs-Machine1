"""
Pixel-art skeletal rig renderer for MAN VS MACHINE.

Characters are described as a skeleton (bone lengths) plus a list of drawing
"parts" built from shaded primitives (capsules, ellipses, bevelled polygons).
Each animation frame is a pose (hip position, torso angle, IK targets for hands
and feet).  Frames are rasterised at 1:1 pixel scale with banded cel shading,
per-part selective outlines and a dark silhouette outline, so every frame
shares the same palette, light direction and pixel density.

Coordinates: x = forward (characters face right in the sheets), y = down,
origin = point on the ground between the feet.
"""
import math
from png import Image, hexc

LIGHT = (0.45, -0.62, 0.64)
_l = math.sqrt(sum(c * c for c in LIGHT))
LIGHT = tuple(c / _l for c in LIGHT)

# Shade thresholds -> ramp index (0 darkest .. 4 brightest)
THRESH = (0.0, 0.36, 0.74, 0.92)


def ramp(*hexes):
    return [hexc(h) for h in hexes]


class Emit(list):
    """A ramp that ignores lighting (glowing parts)."""
    pass


def emit(*hexes):
    return Emit(hexc(h) for h in hexes)


def shade_idx(s, bias=0):
    i = 0
    for t in THRESH:
        if s > t:
            i += 1
    return max(0, min(4, i + bias))


# ---------------------------------------------------------------- vectors
def v(x, y):
    return (float(x), float(y))


def add(a, b):
    return (a[0] + b[0], a[1] + b[1])


def sub(a, b):
    return (a[0] - b[0], a[1] - b[1])


def mul(a, s):
    return (a[0] * s, a[1] * s)


def length(a):
    return math.hypot(a[0], a[1])


def norm(a):
    l = length(a)
    return (a[0] / l, a[1] / l) if l > 1e-9 else (1.0, 0.0)


def dirv(deg):
    r = math.radians(deg)
    return (math.cos(r), math.sin(r))


def lerp(a, b, t):
    return (a[0] + (b[0] - a[0]) * t, a[1] + (b[1] - a[1]) * t)


def ang(a):
    return math.degrees(math.atan2(a[1], a[0]))


def ik2(root, target, l1, l2, pref):
    """Two-bone IK. Returns (joint, end). pref = preferred bend direction."""
    d = sub(target, root)
    dist = length(d)
    dist = max(abs(l1 - l2) + 0.01, min(l1 + l2 - 0.01, dist))
    base = norm(d)
    end = add(root, mul(base, dist))
    c = (l1 * l1 + dist * dist - l2 * l2) / (2 * l1 * dist)
    c = max(-1.0, min(1.0, c))
    a = math.acos(c)
    best = None
    for sgn in (1, -1):
        r = math.atan2(base[1], base[0]) + sgn * a
        j = add(root, (math.cos(r) * l1, math.sin(r) * l1))
        mid = lerp(root, end, 0.5)
        score = (j[0] - mid[0]) * pref[0] + (j[1] - mid[1]) * pref[1]
        if best is None or score > best[0]:
            best = (score, j)
    return best[1], end


# ---------------------------------------------------------------- primitives
class Prim:
    __slots__ = ('kind', 'a', 'b', 'ra', 'rb', 'pts', 'ramp', 'bias', 'bevel', 'col', 'rot', 'tilt')

    def __init__(self, kind, ramp=None, bias=0):
        self.kind = kind
        self.ramp = ramp
        self.bias = bias
        self.col = None
        self.tilt = (0.0, 0.0)


def capsule(a, b, ra, rb=None, rp=None, bias=0):
    p = Prim('cap', rp, bias)
    p.a, p.b, p.ra, p.rb = a, b, ra, (ra if rb is None else rb)
    return p


def ellipse(c, rx, ry, rot=0.0, rp=None, bias=0):
    p = Prim('ell', rp, bias)
    p.a, p.ra, p.rb, p.rot = c, rx, ry, math.radians(rot)
    return p


def poly(pts, rp=None, bias=0, bevel=1.6, tilt=(0.0, 0.0)):
    p = Prim('poly', rp, bias)
    p.pts, p.bevel, p.tilt = pts, bevel, tilt
    return p


def line(a, b, col):
    p = Prim('line')
    p.a, p.b, p.col = a, b, col
    return p


def dot(a, col):
    p = Prim('dot')
    p.a, p.col = a, col
    return p


class Part:
    def __init__(self, prims, rp, back=False, outline=True, name=''):
        self.prims = prims
        self.ramp = rp
        self.back = back
        self.outline = outline
        self.name = name


def _bbox(prim):
    if prim.kind == 'cap':
        r = max(prim.ra, prim.rb) + 1
        return (min(prim.a[0], prim.b[0]) - r, min(prim.a[1], prim.b[1]) - r,
                max(prim.a[0], prim.b[0]) + r, max(prim.a[1], prim.b[1]) + r)
    if prim.kind == 'ell':
        r = max(prim.ra, prim.rb) + 1
        return (prim.a[0] - r, prim.a[1] - r, prim.a[0] + r, prim.a[1] + r)
    xs = [q[0] for q in prim.pts]
    ys = [q[1] for q in prim.pts]
    return (min(xs) - 1, min(ys) - 1, max(xs) + 1, max(ys) + 1)


def _point_in_poly(x, y, pts):
    inside = False
    n = len(pts)
    j = n - 1
    for i in range(n):
        xi, yi = pts[i]
        xj, yj = pts[j]
        if (yi > y) != (yj > y):
            xc = xi + (y - yi) * (xj - xi) / (yj - yi)
            if x < xc:
                inside = not inside
        j = i
    return inside


def _poly_normal(x, y, prim):
    """Bevelled-plate normal: flat in the middle, tilted near the edges."""
    pts = prim.pts
    n = len(pts)
    best = 1e9
    bn = (0.0, 0.0)
    # polygon winding (for outward normals)
    area = 0.0
    for i in range(n):
        x1, y1 = pts[i]
        x2, y2 = pts[(i + 1) % n]
        area += x1 * y2 - x2 * y1
    sgn = 1.0 if area > 0 else -1.0
    for i in range(n):
        x1, y1 = pts[i]
        x2, y2 = pts[(i + 1) % n]
        ex, ey = x2 - x1, y2 - y1
        el2 = ex * ex + ey * ey
        if el2 < 1e-9:
            continue
        t = max(0.0, min(1.0, ((x - x1) * ex + (y - y1) * ey) / el2))
        dx = x - (x1 + ex * t)
        dy = y - (y1 + ey * t)
        d = math.sqrt(dx * dx + dy * dy)
        if d < best:
            best = d
            el = math.sqrt(el2)
            # outward normal of the edge
            bn = (sgn * ey / el, -sgn * ex / el)
    tx, ty = prim.tilt
    if best < prim.bevel:
        k = (1.0 - best / prim.bevel) * 0.85
        nx, ny = bn[0] * k + tx, bn[1] * k + ty
    else:
        nx, ny = tx, ty
    nz2 = max(0.05, 1.0 - nx * nx - ny * ny)
    return nx, ny, math.sqrt(nz2)


def raster_part(part, back_bias=0):
    """Rasterise a part into {(x,y): (colour, ramp)}."""
    buf = {}
    lx, ly, lz = LIGHT
    for prim in part.prims:
        rp = prim.ramp if prim.ramp is not None else part.ramp
        if prim.kind == 'line':
            x0, y0 = int(math.floor(prim.a[0])), int(math.floor(prim.a[1]))
            x1, y1 = int(math.floor(prim.b[0])), int(math.floor(prim.b[1]))
            dx, dy = abs(x1 - x0), -abs(y1 - y0)
            sx = 1 if x0 < x1 else -1
            sy = 1 if y0 < y1 else -1
            err = dx + dy
            lc = rp[prim.col] if isinstance(prim.col, int) else prim.col
            while True:
                buf[(x0, y0)] = (lc, rp)
                if x0 == x1 and y0 == y1:
                    break
                e2 = 2 * err
                if e2 >= dy:
                    err += dy
                    x0 += sx
                if e2 <= dx:
                    err += dx
                    y0 += sy
            continue
        if prim.kind == 'dot':
            lc = rp[prim.col] if isinstance(prim.col, int) else prim.col
            buf[(int(math.floor(prim.a[0])), int(math.floor(prim.a[1])))] = (lc, rp)
            continue
        x0, y0, x1, y1 = _bbox(prim)
        bias = prim.bias + back_bias
        is_emit = isinstance(rp, Emit)
        for py in range(int(math.floor(y0)), int(math.ceil(y1)) + 1):
            cy = py + 0.5
            for px in range(int(math.floor(x0)), int(math.ceil(x1)) + 1):
                cx = px + 0.5
                if prim.kind == 'cap':
                    ax, ay = prim.a
                    bx, by = prim.b
                    ex, ey = bx - ax, by - ay
                    el2 = ex * ex + ey * ey
                    t = 0.0 if el2 < 1e-9 else max(0.0, min(1.0, ((cx - ax) * ex + (cy - ay) * ey) / el2))
                    qx, qy = ax + ex * t, ay + ey * t
                    r = prim.ra + (prim.rb - prim.ra) * t
                    dx, dy = cx - qx, cy - qy
                    d2 = dx * dx + dy * dy
                    if d2 > r * r:
                        continue
                    nx, ny = dx / r, dy / r
                    nz = math.sqrt(max(0.0, 1.0 - nx * nx - ny * ny))
                elif prim.kind == 'ell':
                    dx, dy = cx - prim.a[0], cy - prim.a[1]
                    cr, sr = math.cos(-prim.rot), math.sin(-prim.rot)
                    lxp = dx * cr - dy * sr
                    lyp = dx * sr + dy * cr
                    ux, uy = lxp / prim.ra, lyp / prim.rb
                    d2 = ux * ux + uy * uy
                    if d2 > 1.0:
                        continue
                    # rotate normal back
                    c2, s2 = math.cos(prim.rot), math.sin(prim.rot)
                    nx = ux * c2 - uy * s2
                    ny = ux * s2 + uy * c2
                    nz = math.sqrt(max(0.0, 1.0 - d2))
                else:
                    if not _point_in_poly(cx, cy, prim.pts):
                        continue
                    nx, ny, nz = _poly_normal(cx, cy, prim)
                if is_emit:
                    idx = 4 if nz > 0.7 else (3 if nz > 0.35 else 2)
                else:
                    s = nx * lx + ny * ly + nz * lz
                    idx = shade_idx(s, bias)
                buf[(px, py)] = (rp[idx], rp)
    return buf


def render(parts, w, h, ox, oy, outline_col, scale=1):
    """Render parts (in character space) into an Image of size w x h with the
    character origin at pixel (ox, oy)."""
    canvas = {}
    for part in parts:
        if scale != 1:
            part = _scale_part(part, scale)
        buf = raster_part(part, -1 if part.back else 0)
        buf2 = {}
        for (x, y), (col, rp) in buf.items():
            if col is None:
                continue
            X, Y = x + ox, y + oy
            if part.outline:
                edge = False
                for ddx, ddy in ((1, 0), (-1, 0), (0, 1), (0, -1)):
                    if (x + ddx, y + ddy) not in buf:
                        if (X + ddx, Y + ddy) in canvas:
                            edge = True
                            break
                if edge and not isinstance(rp, Emit):
                    col = rp[0]
            buf2[(X, Y)] = col
        canvas.update(buf2)
    img = Image(w, h)
    for (x, y), c in canvas.items():
        img.set(x, y, c)
    # silhouette outline
    if outline_col is not None:
        add_pts = []
        for y in range(h):
            for x in range(w):
                if img.px[y * w + x] is not None:
                    continue
                if (img.get(x + 1, y) is not None or img.get(x - 1, y) is not None or
                        img.get(x, y + 1) is not None or img.get(x, y - 1) is not None):
                    add_pts.append((x, y))
        for x, y in add_pts:
            img.set(x, y, outline_col)
    return img


def _scale_part(part, s):
    np_ = []
    for p in part.prims:
        q = Prim(p.kind, p.ramp, p.bias)
        q.col = p.col
        q.tilt = p.tilt
        if p.kind == 'cap':
            q.a, q.b, q.ra, q.rb = mul(p.a, s), mul(p.b, s), p.ra * s, p.rb * s
        elif p.kind == 'ell':
            q.a, q.ra, q.rb, q.rot = mul(p.a, s), p.ra * s, p.rb * s, p.rot
        elif p.kind == 'poly':
            q.pts, q.bevel = [mul(t, s) for t in p.pts], p.bevel * s
        elif p.kind in ('line', 'dot'):
            q.a = mul(p.a, s)
            q.b = mul(p.b, s) if p.kind == 'line' else None
        np_.append(q)
    return Part(np_, part.ramp, part.back, part.outline, part.name)


# ---------------------------------------------------------------- skeleton
class Body:
    def __init__(self, **kw):
        self.thigh = 22
        self.shin = 22
        self.uarm = 17
        self.farm = 16
        self.torso = 30
        self.neck = 3
        self.head_r = 8
        self.sh_f = 6
        self.sh_b = 7
        self.sh_drop = 3
        self.hip_off = 4
        self.foot = 9
        self.__dict__.update(kw)


class Skel:
    pass


def solve(body, pose):
    s = Skel()
    s.pose = pose
    hip = v(*pose['hip'])
    ta = pose.get('torso', -90.0)
    u = dirv(ta)
    p = (-u[1], u[0])
    s.hip, s.u, s.p, s.ta = hip, u, p, ta
    s.neck = add(hip, mul(u, body.torso))
    ha = pose.get('head', ta)
    hu = dirv(ha)
    s.hu = hu
    s.hp = (-hu[1], hu[0])
    s.ha = ha
    s.head = add(s.neck, mul(hu, body.neck + body.head_r))
    s.sh_f = add(add(s.neck, mul(p, body.sh_f)), mul(u, -body.sh_drop))
    s.sh_b = add(add(s.neck, mul(p, -body.sh_b)), mul(u, -body.sh_drop))
    pa = pose.get('pelvis', ta)
    pu = dirv(pa)
    pp = (-pu[1], pu[0])
    s.hip_f = add(hip, mul(pp, body.hip_off))
    s.hip_b = add(hip, mul(pp, -body.hip_off))

    def leg(root, key):
        if key + 'a' in pose:
            a1, a2 = pose[key + 'a']
            knee = add(root, mul(dirv(a1), body.thigh))
            ank = add(knee, mul(dirv(a2), body.shin))
        else:
            knee, ank = ik2(root, v(*pose[key]), body.thigh, body.shin, pose.get(key + 'p', (1.0, 0.0)))
        fa = pose.get(key + 'f', 0.0)
        toe = add(ank, mul(dirv(fa), body.foot))
        return knee, ank, toe, fa

    s.kn_f, s.an_f, s.toe_f, s.fa_f = leg(s.hip_f, 'ff')
    s.kn_b, s.an_b, s.toe_b, s.fa_b = leg(s.hip_b, 'bf')

    def arm(root, key):
        if key + 'a' in pose:
            a1, a2 = pose[key + 'a']
            el = add(root, mul(dirv(a1), body.uarm))
            wr = add(el, mul(dirv(a2), body.farm))
        else:
            el, wr = ik2(root, v(*pose[key]), body.uarm, body.farm, pose.get(key + 'p', (-0.35, 1.0)))
        return el, wr

    s.el_f, s.wr_f = arm(s.sh_f, 'fh')
    s.el_b, s.wr_b = arm(s.sh_b, 'bh')
    return s


def limb_frame(a, b):
    d = norm(sub(b, a))
    n = (-d[1], d[0])
    return d, n


def on_limb(a, b, pts):
    """Map limb-local points (t along a->b in px, side offset px) to world."""
    d, n = limb_frame(a, b)
    return [add(add(a, mul(d, t)), mul(n, sd)) for t, sd in pts]


def on_frame(origin, fwd, up, pts):
    """Map (fwd, up) local points into world using basis vectors fwd/up."""
    return [add(add(origin, mul(fwd, f)), mul(up, u)) for f, u in pts]


def scale_pose(pose, k):
    out = {}
    for key, val in pose.items():
        if key in ('hip', 'ff', 'bf', 'fh', 'bh') or key.startswith('pt_'):
            out[key] = (val[0] * k, val[1] * k)
        else:
            out[key] = val
    return out


def lerp_pose(a, b, t):
    out = dict(a)
    for key, vb in b.items():
        va = a.get(key)
        if va is None:
            out[key] = vb
        elif isinstance(vb, tuple) and isinstance(va, tuple) and len(va) == len(vb) and all(isinstance(q, (int, float)) for q in vb):
            out[key] = tuple(x + (y - x) * t for x, y in zip(va, vb))
        elif isinstance(vb, (int, float)) and isinstance(va, (int, float)) and not isinstance(vb, bool):
            out[key] = va + (vb - va) * t
        else:
            out[key] = vb if t >= 0.5 else va
    return out
