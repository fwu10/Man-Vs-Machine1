"""Procedurally synthesises every sound effect and music loop (original audio,
no samples). Output: 22.05 kHz mono 16-bit WAV in assets/audio/."""
import math
import os
import random
import struct
import wave

ROOT = os.path.normpath(os.path.join(os.path.dirname(__file__), '..'))
SR = 22050


def buf(sec):
    return [0.0] * int(SR * sec)


def write(path, data, gain=0.9):
    peak = max(1e-6, max(abs(x) for x in data))
    k = gain / peak if peak > gain else 1.0
    with wave.open(path, 'wb') as w:
        w.setnchannels(1)
        w.setsampwidth(2)
        w.setframerate(SR)
        w.writeframes(b''.join(struct.pack('<h', int(max(-1, min(1, x * k)) * 32000)) for x in data))


def env(t, a, d, total):
    if t < a:
        return t / a
    return max(0.0, 1.0 - (t - a) / max(1e-6, d)) if t < total else 0.0


def osc(kind, ph):
    ph %= 1.0
    if kind == 'sin':
        return math.sin(2 * math.pi * ph)
    if kind == 'sq':
        return 1.0 if ph < 0.5 else -1.0
    if kind == 'pulse':
        return 1.0 if ph < 0.25 else -1.0
    if kind == 'saw':
        return 2 * ph - 1
    if kind == 'tri':
        return 4 * abs(ph - 0.5) - 1
    return 0.0


def tone(out, start, dur, f0, f1=None, kind='sq', vol=0.3, a=0.002, rel=None, vib=0.0):
    f1 = f0 if f1 is None else f1
    rel = dur if rel is None else rel
    s0 = int(start * SR)
    n = int(dur * SR)
    ph = 0.0
    for i in range(n):
        if s0 + i >= len(out):
            break
        t = i / SR
        f = f0 * (f1 / f0) ** (t / dur) if f0 > 0 and f1 > 0 else f0
        if vib:
            f *= 1 + 0.012 * math.sin(2 * math.pi * vib * t)
        ph += f / SR
        out[s0 + i] += osc(kind, ph) * vol * env(t, a, rel, dur)


def noise(out, start, dur, vol=0.3, lp=0.5, a=0.001, decay=None, hp=0.0):
    """Filtered noise burst. lp in (0,1]: one-pole low-pass coefficient."""
    s0 = int(start * SR)
    n = int(dur * SR)
    y = 0.0
    prev = 0.0
    decay = dur if decay is None else decay
    for i in range(n):
        if s0 + i >= len(out):
            break
        t = i / SR
        x = random.uniform(-1, 1)
        y += lp * (x - y)
        o = y - prev * hp
        prev = y
        out[s0 + i] += o * vol * env(t, a, decay, dur)


def sfx():
    d = os.path.join(ROOT, 'assets', 'audio', 'sfx')
    os.makedirs(d, exist_ok=True)
    random.seed(7)
    S = {}

    def mk(name, sec, fn, gain=0.9):
        b = buf(sec)
        fn(b)
        S[name] = (b, gain)

    mk('punch_l', 0.16, lambda b: (noise(b, 0, 0.08, 0.7, 0.35, decay=0.06), tone(b, 0, 0.1, 180, 70, 'sin', 0.6)))
    mk('punch_h', 0.3, lambda b: (noise(b, 0, 0.18, 0.9, 0.25, decay=0.14), tone(b, 0, 0.22, 140, 45, 'sin', 0.9), tone(b, 0, 0.05, 900, 300, 'sq', 0.15)))
    mk('kick_l', 0.18, lambda b: (noise(b, 0, 0.1, 0.7, 0.45, decay=0.07), tone(b, 0, 0.12, 220, 80, 'sin', 0.5)))
    mk('kick_h', 0.32, lambda b: (noise(b, 0, 0.2, 0.9, 0.3, decay=0.16), tone(b, 0, 0.25, 160, 40, 'sin', 0.9)))
    mk('flesh_l', 0.12, lambda b: noise(b, 0, 0.1, 0.5, 0.2, decay=0.08))
    mk('flesh_h', 0.2, lambda b: (noise(b, 0, 0.18, 0.7, 0.15, decay=0.15), tone(b, 0, 0.15, 90, 50, 'sin', 0.5)))

    def metal(b, base, length, vol):
        for k, m in enumerate((1.0, 2.76, 5.4, 8.93)):
            tone(b, 0, length, base * m, base * m * 0.97, 'sin', vol / (k + 1.2), rel=length * (1 - k * 0.15))
        noise(b, 0, 0.04, vol, 0.9, decay=0.03)
    mk('metal_l', 0.35, lambda b: metal(b, 620, 0.3, 0.5))
    mk('metal_h', 0.6, lambda b: metal(b, 380, 0.55, 0.8))
    mk('armor', 0.5, lambda b: (metal(b, 300, 0.45, 0.8), tone(b, 0, 0.2, 90, 60, 'sq', 0.2)))
    mk('block', 0.2, lambda b: (noise(b, 0, 0.06, 0.6, 0.8, decay=0.05), tone(b, 0, 0.15, 1400, 1200, 'tri', 0.25), tone(b, 0, 0.1, 300, 200, 'sin', 0.4)))
    mk('parry', 0.6, lambda b: (metal(b, 900, 0.5, 0.6), tone(b, 0.0, 0.4, 1800, 2400, 'tri', 0.25)))
    mk('whoosh_l', 0.14, lambda b: noise(b, 0, 0.13, 0.25, 0.25, a=0.04, decay=0.09, hp=0.6))
    mk('whoosh_h', 0.22, lambda b: noise(b, 0, 0.21, 0.35, 0.2, a=0.07, decay=0.14, hp=0.6))
    mk('land', 0.14, lambda b: (noise(b, 0, 0.1, 0.4, 0.12, decay=0.08), tone(b, 0, 0.1, 110, 60, 'sin', 0.4)))
    mk('thud', 0.4, lambda b: (noise(b, 0, 0.3, 0.8, 0.08, decay=0.25), tone(b, 0, 0.3, 80, 35, 'sin', 0.9)))
    mk('ko', 1.6, lambda b: (tone(b, 0, 1.4, 120, 30, 'sin', 1.0, rel=1.3), noise(b, 0, 1.2, 0.8, 0.1, decay=1.1),
                             tone(b, 0, 0.6, 880, 110, 'sq', 0.25)))

    def bell(b):
        for st in (0.0, 0.18, 0.36):
            for m, v in ((1.0, 0.5), (2.4, 0.3), (3.9, 0.2), (5.6, 0.12)):
                tone(b, st, 0.9, 1250 * m, 1250 * m, 'sin', v, rel=0.85)
    mk('bell', 1.3, bell)

    def fight(b):
        tone(b, 0, 0.12, 220, 220, 'saw', 0.3)
        tone(b, 0.12, 0.5, 330, 330, 'saw', 0.3, vib=7)
        tone(b, 0.12, 0.5, 440, 440, 'sq', 0.2, vib=7)
        noise(b, 0.12, 0.4, 0.5, 0.3, decay=0.35)
        tone(b, 0.12, 0.4, 110, 50, 'sin', 0.8)
    mk('fight', 0.7, fight)

    def alarm(b):
        for k in range(3):
            tone(b, k * 0.25, 0.22, 880, 660, 'sq', 0.25)
    mk('alarm', 0.8, alarm)
    mk('charge', 0.7, lambda b: (tone(b, 0, 0.7, 120, 900, 'saw', 0.25), tone(b, 0, 0.7, 240, 1800, 'sq', 0.08)))
    mk('laser', 0.8, lambda b: (tone(b, 0, 0.75, 1600, 200, 'saw', 0.35), noise(b, 0, 0.7, 0.4, 0.5, decay=0.65), tone(b, 0, 0.7, 70, 50, 'sq', 0.3)))
    mk('zap', 0.3, lambda b: (tone(b, 0, 0.25, 2000, 400, 'sq', 0.2), noise(b, 0, 0.25, 0.5, 0.95, decay=0.2)))
    mk('slam', 0.6, lambda b: (tone(b, 0, 0.5, 90, 30, 'sin', 1.0), noise(b, 0, 0.45, 0.9, 0.1, decay=0.4), metal(b, 200, 0.3, 0.3)))
    mk('slash', 0.3, lambda b: (noise(b, 0, 0.22, 0.6, 0.9, a=0.02, decay=0.18, hp=0.9), tone(b, 0, 0.2, 3000, 1500, 'tri', 0.12)))
    mk('slash_l', 0.2, lambda b: noise(b, 0, 0.15, 0.5, 0.9, a=0.01, decay=0.12, hp=0.9))
    mk('explode', 1.0, lambda b: (noise(b, 0, 0.9, 1.0, 0.12, decay=0.85), tone(b, 0, 0.6, 70, 25, 'sin', 1.0)))
    mk('super', 1.0, lambda b: (tone(b, 0, 0.9, 200, 1600, 'saw', 0.25), tone(b, 0, 0.9, 400, 3200, 'sq', 0.08), noise(b, 0, 0.3, 0.4, 0.5)))

    def jingle(b, notes, kind='sq', step=0.14, vol=0.25):
        for i, n in enumerate(notes):
            if n:
                f = 440 * 2 ** ((n - 69) / 12)
                tone(b, i * step, step * 1.8, f, f, kind, vol, vib=6)
                tone(b, i * step, step * 1.8, f / 2, f / 2, 'tri', vol * 0.8)
    mk('victory', 2.4, lambda b: jingle(b, [60, 64, 67, 72, 0, 67, 72, 76, 76, 76, 0, 0]))
    mk('defeat', 2.6, lambda b: jingle(b, [64, 63, 62, 61, 0, 57, 0, 52, 52], 'saw', 0.2))
    mk('menu_move', 0.06, lambda b: tone(b, 0, 0.05, 1200, 1200, 'sq', 0.2))
    mk('menu_select', 0.25, lambda b: (tone(b, 0, 0.08, 880, 880, 'sq', 0.25), tone(b, 0.08, 0.15, 1320, 1320, 'sq', 0.25)))
    mk('menu_back', 0.2, lambda b: (tone(b, 0, 0.08, 660, 660, 'sq', 0.25), tone(b, 0.08, 0.1, 440, 440, 'sq', 0.25)))
    mk('pause', 0.25, lambda b: (tone(b, 0, 0.1, 990, 990, 'pulse', 0.25), tone(b, 0.1, 0.12, 660, 660, 'pulse', 0.25)))
    for name, (b, g) in S.items():
        write(os.path.join(d, name + '.wav'), b, g)
    print('sfx:', len(S))


# ------------------------------------------------------------------ music
def midi(n):
    return 440 * 2 ** ((n - 69) / 12)


def song(path, bpm, root, scale, prog, bars, lead_kind='sq', bass_kind='saw', seed=1, drive=1.0, boss=False):
    random.seed(seed)
    beat = 60 / bpm
    bar = beat * 4
    out = buf(bar * bars + 0.05)
    for b in range(bars):
        t0 = b * bar
        chord = prog[b % len(prog)]
        croot = root + scale[chord % len(scale)] + (12 * (chord // len(scale)))
        # bass: driving eighths with octave jumps
        for e in range(8):
            n = croot - 12 + (12 if e % 4 == 3 else 0)
            if boss and e % 2 == 1:
                n = croot - 12 + 7
            tone(out, t0 + e * beat / 2, beat / 2 * 0.9, midi(n), None, bass_kind, 0.18 * drive)
        # pads/arpeggio
        triad = [0, scale[2 % len(scale)], scale[4 % len(scale)]]
        for e in range(16):
            n = croot + 12 + triad[e % 3] + (12 if e % 6 >= 3 else 0)
            tone(out, t0 + e * beat / 4, beat / 4 * 0.8, midi(n), None, 'pulse', 0.045)
        # drums
        for q in range(4):
            tq = t0 + q * beat
            tone(out, tq, 0.16, 150, 40, 'sin', 0.55)                       # kick
            if q in (1, 3):
                noise(out, tq, 0.14, 0.32, 0.6, decay=0.12)                   # snare
            for h in range(2):
                noise(out, tq + h * beat / 2, 0.03, 0.08, 0.95, decay=0.025, hp=0.9)  # hats
            if boss and q in (0, 2):
                tone(out, tq + beat / 2, 0.12, 120, 45, 'sin', 0.4)
        # lead: phrase built from scale degrees, repeating every 4 bars with variation
        if b % 8 >= 2 or bars <= 8:
            rng = random.Random(seed * 100 + (b % 4))
            pos = 0.0
            while pos < 4:
                ln = rng.choice([0.5, 0.5, 1.0, 0.25, 1.5])
                if pos + ln > 4:
                    ln = 4 - pos
                deg = rng.choice([0, 2, 4, 4, 5, 7, 2, 1])
                n = croot + 12 + scale[deg % len(scale)] + 12 * (deg // len(scale))
                if rng.random() > 0.15:
                    tone(out, t0 + pos * beat, ln * beat * 0.92, midi(n), None, lead_kind, 0.11, vib=5.5)
                pos += ln
    write(path, out, 0.8)


def music():
    d = os.path.join(ROOT, 'assets', 'audio', 'music')
    os.makedirs(d, exist_ok=True)
    minor = [0, 2, 3, 5, 7, 8, 10]
    phryg = [0, 1, 3, 5, 7, 8, 10]
    song(os.path.join(d, 'menu.wav'), 112, 45, minor, [0, 5, 3, 6, 0, 5, 4, 4], 16, 'tri', 'sq', seed=3, drive=0.8)
    song(os.path.join(d, 'fight_industrial.wav'), 146, 40, minor, [0, 0, 5, 6, 0, 3, 4, 4], 16, 'sq', 'saw', seed=11)
    song(os.path.join(d, 'fight_foundry.wav'), 158, 43, minor, [0, 6, 5, 6, 0, 6, 3, 4], 16, 'pulse', 'saw', seed=23)
    song(os.path.join(d, 'fight_boss.wav'), 168, 38, phryg, [0, 1, 0, 5, 0, 1, 3, 1], 16, 'saw', 'sq', seed=31, boss=True)
    print('music done')


if __name__ == '__main__':
    sfx()
    music()
