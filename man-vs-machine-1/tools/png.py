"""Minimal dependency-free PNG writer/reader helpers used by the asset generators."""
import struct
import zlib


def hexc(h, a=255):
    h = h.lstrip('#')
    return (int(h[0:2], 16), int(h[2:4], 16), int(h[4:6], 16), a)


class Image:
    """RGBA image stored as a flat list of tuples (or None for transparent)."""

    def __init__(self, w, h, fill=None):
        self.w = w
        self.h = h
        self.px = [fill] * (w * h)

    def get(self, x, y):
        if 0 <= x < self.w and 0 <= y < self.h:
            return self.px[y * self.w + x]
        return None

    def set(self, x, y, c):
        if 0 <= x < self.w and 0 <= y < self.h:
            self.px[y * self.w + x] = c

    def blend(self, x, y, c):
        """Alpha-blend colour c (r,g,b,a) over the pixel."""
        if not (0 <= x < self.w and 0 <= y < self.h):
            return
        a = c[3] / 255.0
        if a >= 0.999:
            self.px[y * self.w + x] = c
            return
        d = self.px[y * self.w + x]
        if d is None:
            self.px[y * self.w + x] = c
            return
        da = d[3] / 255.0
        oa = a + da * (1 - a)
        if oa <= 0:
            return
        r = (c[0] * a + d[0] * da * (1 - a)) / oa
        g = (c[1] * a + d[1] * da * (1 - a)) / oa
        b = (c[2] * a + d[2] * da * (1 - a)) / oa
        self.px[y * self.w + x] = (int(r), int(g), int(b), int(oa * 255))

    def paste(self, other, ox, oy):
        for y in range(other.h):
            ty = oy + y
            if ty < 0 or ty >= self.h:
                continue
            for x in range(other.w):
                c = other.px[y * other.w + x]
                if c is not None and c[3] > 0:
                    self.blend(ox + x, ty, c)

    def scaled(self, s):
        out = Image(self.w * s, self.h * s)
        for y in range(self.h):
            for x in range(self.w):
                c = self.px[y * self.w + x]
                if c is None:
                    continue
                for yy in range(s):
                    base = (y * s + yy) * out.w + x * s
                    for xx in range(s):
                        out.px[base + xx] = c
        return out

    def crop(self, x0, y0, w, h):
        out = Image(w, h)
        for y in range(h):
            for x in range(w):
                out.px[y * w + x] = self.get(x0 + x, y0 + y)
        return out

    def save(self, path):
        raw = bytearray()
        for y in range(self.h):
            raw.append(0)
            row = self.px[y * self.w:(y + 1) * self.w]
            for c in row:
                if c is None:
                    raw += b'\x00\x00\x00\x00'
                else:
                    raw += bytes((c[0] & 255, c[1] & 255, c[2] & 255, c[3] & 255))

        def chunk(tag, data):
            return struct.pack('>I', len(data)) + tag + data + struct.pack('>I', zlib.crc32(tag + data) & 0xffffffff)

        png = b'\x89PNG\r\n\x1a\n'
        png += chunk(b'IHDR', struct.pack('>IIBBBBB', self.w, self.h, 8, 6, 0, 0, 0))
        png += chunk(b'IDAT', zlib.compress(bytes(raw), 9))
        png += chunk(b'IEND', b'')
        with open(path, 'wb') as f:
            f.write(png)
