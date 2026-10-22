"""MARCUS 'IRON' COLE - the human boxer (player character)."""
import math
import pixelrig as R
from pixelrig import capsule, ellipse, poly, line, dot, Part, ramp, on_frame, on_limb, add, mul, sub, norm, lerp

ID = 'boxer'
FRAME = (144, 120, 72, 112)
OUTLINE = (34, 14, 10, 255)
CORE_W = 30
PORTRAIT_BOX = (-22, -100, 48, 44)

BODY = R.Body(thigh=22, shin=22, uarm=17, farm=16, torso=30, neck=3, head_r=8,
              sh_f=6, sh_b=7, sh_drop=3, hip_off=4, foot=9)

SKIN = ramp('#4a2416', '#83442a', '#b8703f', '#dc9a62', '#f2c391')
RED = ramp('#3a0a10', '#7a121c', '#bb2230', '#e44a3c', '#ff8f70')
GOLD = ramp('#4a2c08', '#8c5a12', '#d09a22', '#f4cc4c', '#fff2a6')
WHITE = ramp('#4c4a5c', '#8e8ca0', '#cfcfdb', '#efeff6', '#ffffff')
HAIR = ramp('#0e0806', '#1e120c', '#33201a', '#4a3024', '#644232')
BOOT = ramp('#120c10', '#241820', '#3a2a34', '#56404c', '#74606c')


def arm(sh, el, wr, back):
    d = norm(sub(wr, el))
    g = add(wr, mul(d, 5.0))
    a = R.ang(d)
    prims = [
        ellipse(sh, 5.4, 5.0, 0, SKIN),
        capsule(sh, el, 5.0, 4.3, SKIN),
        capsule(el, wr, 4.4, 3.5, SKIN),
        capsule(lerp(el, wr, 0.55), wr, 3.8, 3.8, WHITE),
        ellipse(g, 7.2, 6.4, a, RED),
        capsule(add(wr, mul(d, -0.5)), add(wr, mul(d, 1.6)), 4.8, 4.8, WHITE),
        ellipse(add(g, mul(d, -1.5)), 2.6, 2.2, a, RED, 1),  # thumb knuckle highlight
    ]
    # glove lace stripe
    prims.append(line(add(wr, mul(d, 2.2)), add(g, mul(d, -2.0)), GOLD[3]))
    return Part(prims, SKIN, back=back)


def leg(hip, kn, an, toe, fa, back):
    fd = R.dirv(fa)
    up = (fd[1], -fd[0])
    foot = on_frame(an, fd, up, [(-4.0, 3.5), (-4.6, -2.6), (9.6, -2.6), (10.2, -0.2), (6.0, 2.2), (1.5, 3.6)])
    prims = [
        capsule(hip, kn, 6.6, 5.0, SKIN),
        ellipse(kn, 4.6, 4.4, 0, SKIN),
        capsule(kn, an, 4.8, 3.6, SKIN),
        capsule(lerp(kn, an, 0.6), an, 4.4, 4.1, BOOT),
        poly(foot, BOOT, bevel=1.4),
        line(lerp(kn, an, 0.65), an, RED[2]),
    ]
    return Part(prims, SKIN, back=back)


def shorts_leg(hip, kn, back):
    mid = lerp(hip, kn, 0.42)
    return Part([capsule(hip, mid, 7.4, 6.6, RED),
                 line(lerp(hip, kn, 0.1), lerp(hip, kn, 0.4), GOLD[3])], RED, back=back)


def build_parts(sk):
    tl = lambda f, u: add(add(sk.hip, mul(sk.p, f)), mul(sk.u, u))
    hl = lambda f, u: add(add(sk.head, mul(sk.hp, f)), mul(sk.hu, u))
    parts = []
    parts.append(arm(sk.sh_b, sk.el_b, sk.wr_b, True))
    parts.append(leg(sk.hip_b, sk.kn_b, sk.an_b, sk.toe_b, sk.fa_b, True))
    parts.append(shorts_leg(sk.hip_b, sk.kn_b, True))
    # torso: V-taper
    torso = [
        capsule(tl(0.5, 6), tl(1.5, 22), 9.4, 12.2, SKIN),
        ellipse(tl(4.5, 21), 7.5, 5.2, sk.ta + 90, SKIN),   # pec
        line(tl(1.5, 17.5), tl(9.5, 17.8), 1),               # pec underline
        line(tl(5.5, 14.5), tl(7.5, 14.5), 1),               # abs
        line(tl(5.5, 11.0), tl(7.5, 11.0), 1),
        dot(tl(6.5, 8.5), 1),
    ]
    parts.append(Part(torso, SKIN))
    parts.append(leg(sk.hip_f, sk.kn_f, sk.an_f, sk.toe_f, sk.fa_f, False))
    shorts = [
        ellipse(tl(0, 2.5), 11.0, 8.5, sk.ta + 90, RED),
        capsule(sk.hip_f, lerp(sk.hip_f, sk.kn_f, 0.42), 7.4, 6.6, RED),
        line(lerp(sk.hip_f, sk.kn_f, 0.1), lerp(sk.hip_f, sk.kn_f, 0.4), GOLD[3]),
        capsule(tl(-10, 8.5), tl(10.5, 8.5), 2.6, 2.6, GOLD),
    ]
    parts.append(Part(shorts, RED))
    head = [
        capsule(sk.neck, R.lerp(sk.neck, sk.head, 0.6), 4.8, 4.8, SKIN),
        ellipse(sk.head, 7.0, 8.0, sk.ha + 90, SKIN),
        ellipse(hl(2.5, -3.5), 5.6, 4.4, sk.ha + 90, SKIN),          # jaw
        ellipse(hl(7.0, 0.2), 1.6, 1.8, 0, SKIN),                    # nose
        poly([hl(-7.4, 1.0), hl(-6.8, 5.6), hl(-3.0, 8.6), hl(2.5, 8.8), hl(6.2, 6.6),
              hl(6.6, 4.4), hl(3.0, 5.2), hl(-1.0, 4.4), hl(-3.5, 2.0), hl(-5.0, -2.5)], HAIR, bevel=1.2),
        ellipse(hl(-1.2, 0.2), 2.0, 2.4, 0, SKIN, -1),               # ear
        line(hl(3.0, 2.9), hl(6.2, 3.1), HAIR[0]),                  # brow
        dot(hl(4.9, 1.4), (20, 12, 10, 255)),                       # eye
        dot(hl(5.5, 1.4), (240, 236, 230, 255)),
        poly([hl(1.0, -1.0), hl(6.8, -3.4), hl(6.2, -6.6), hl(2.6, -7.8), hl(-0.5, -4.5)], HAIR, bevel=0.8),  # beard
        line(hl(4.4, -4.4), hl(6.4, -4.2), SKIN[1]),               # mouth
    ]
    parts.append(Part(head, SKIN))
    parts.append(arm(sk.sh_f, sk.el_f, sk.wr_f, False))
    return parts


# ------------------------------------------------------------------ poses
def P(base, **kw):
    d = dict(base)
    d.update(kw)
    return d


STANCE = dict(hip=(0, -41), torso=-80, head=-86, ff=(13, -3), bf=(-12, -3),
              fh=(19, -70), bh=(12, -75))


def idle_frames():
    out = []
    for b in (0, 0.8, 1.5, 0.8):
        out.append(P(STANCE, hip=(0, -41 + b), fh=(19, -70 + b * 1.2), bh=(12, -75 + b * 1.2)))
    return out


def gait(base, n=6, stride=10.0, lift=4.0, reverse=False):
    out = []
    fx, bx = base['ff'][0], base['bf'][0]
    for i in range(n):
        ph = i / n
        def foot(phase, x0):
            phase %= 1.0
            if phase < 0.5:
                t = phase / 0.5
                return (x0 - stride / 2 + stride * t, -3 - lift * math.sin(math.pi * t))
            t = (phase - 0.5) / 0.5
            return (x0 + stride / 2 - stride * t, -3)
        bob = 1.2 * abs(math.sin(2 * math.pi * ph))
        p = P(base, ff=foot(ph, fx), bf=foot(ph + 0.5, bx),
              hip=(base['hip'][0], base['hip'][1] + bob))
        p['fh'] = (base['fh'][0], base['fh'][1] + bob)
        p['bh'] = (base['bh'][0], base['bh'][1] + bob)
        out.append(p)
    if reverse:
        out = out[::-1]
    return out


CROUCH = P(STANCE, hip=(-1, -25), torso=-70, head=-82, ff=(15, -3), bf=(-13, -3),
           fh=(21, -51), bh=(13, -55))
CROUCH_IN = R.lerp_pose(STANCE, CROUCH, 0.55)
LAND = R.lerp_pose(STANCE, CROUCH, 0.6)
JUMP_RISE = P(STANCE, hip=(0, -44), torso=-84, ff=(13, -24), bf=(-5, -12), fh=(19, -72), bh=(13, -77))
JUMP_TUCK = P(STANCE, hip=(0, -46), torso=-72, head=-80, ff=(13, -31), bf=(2, -25), fh=(20, -68), bh=(13, -72))
JUMP_FALL = P(STANCE, hip=(0, -44), torso=-82, ff=(10, -10), bf=(-6, -7), fh=(19, -72), bh=(13, -76))

BLOCK = P(STANCE, hip=(-2, -41), torso=-95, head=-98, fh=(15, -80), bh=(10, -84), ff=(12, -3), bf=(-14, -3))
BLOCK_C = P(CROUCH, torso=-84, head=-92, fh=(15, -58), bh=(11, -62))

HIT_L = P(STANCE, hip=(-3, -40), torso=-104, head=-115, fh=(12, -64), bh=(4, -68))
HIT_H = P(STANCE, hip=(-6, -39), torso=-124, head=-140, ff=(12, -3), bf=(-15, -3), fh=(2, -60), bh=(-6, -64))
HIT_C = P(CROUCH, torso=-100, head=-115, fh=(12, -48), bh=(6, -52))

KD0 = dict(hip=(0, -40), torso=-138, head=-155, ff=(18, -20), bf=(8, -16), fh=(-12, -76), bh=(-20, -62))
KD1 = dict(hip=(0, -22), torso=176, head=182, ff=(30, -34), bf=(26, -26), fh=(-22, -30), bh=(-28, -20))
KD2 = dict(hip=(0, -9), torso=182, head=184, ff=(36, -6), bf=(32, -4), fff=-80, bff=-80,
           fh=(-24, -6), bh=(-30, -4))
KD3 = P(KD2, hip=(0, -8), head=180)
GET0 = dict(hip=(0, -9), torso=-150, head=-128, ff=(24, -4), bf=(20, -3), fh=(-6, -6), bh=(-12, -4), fff=-40)
GET1 = dict(hip=(0, -27), torso=-98, head=-92, ff=(14, -3), bfa=(100, 182), bff=90, fh=(18, -52), bh=(12, -56))

VICT = [P(STANCE, hip=(0, -42), torso=-92, head=-96, bh=(2, -100), fh=(16, -62), ff=(10, -3), bf=(-11, -3)),
        P(STANCE, hip=(0, -43), torso=-94, head=-100, bh=(1, -106), fh=(16, -64), ff=(10, -3), bf=(-11, -3)),
        P(STANCE, hip=(0, -43.5), torso=-94, head=-102, bh=(1, -107), fh=(16, -65), ff=(10, -3), bf=(-11, -3)),
        P(STANCE, hip=(0, -42.5), torso=-93, head=-98, bh=(2, -103), fh=(16, -63), ff=(10, -3), bf=(-11, -3))]
DEFEAT = [P(STANCE, hip=(2, -36), torso=-66, head=-30, fh=(14, -32), bh=(6, -34), ff=(12, -3), bf=(-10, -3)),
          P(STANCE, hip=(2, -35), torso=-64, head=-28, fh=(14, -31), bh=(6, -33), ff=(12, -3), bf=(-10, -3))]
INTRO = [P(STANCE, torso=-88, head=-90, fh=(23, -73), bh=(22, -74)),
         P(STANCE, torso=-86, head=-88, fh=(25, -70), bh=(24, -71)),
         P(STANCE, torso=-88, head=-90, fh=(23, -74), bh=(22, -75)),
         STANCE]

# --- standing normals
LP = [P(STANCE, fh=(14, -71), torso=-78),
      P(STANCE, hip=(2, -41), torso=-74, fh=(46, -73)),
      P(STANCE, hip=(1, -41), torso=-76, fh=(32, -72)),
      P(STANCE, fh=(21, -71))]
HP = [P(STANCE, hip=(-2, -41), torso=-88, bh=(4, -72), fh=(17, -74)),
      P(STANCE, hip=(5, -40), torso=-64, head=-74, bh=(51, -72), fh=(12, -75), ff=(17, -3), bf=(-13, -3), bff=25),
      P(STANCE, hip=(5, -40), torso=-66, head=-76, bh=(48, -72), fh=(12, -75), ff=(17, -3), bf=(-13, -3), bff=25),
      P(STANCE, hip=(3, -41), torso=-72, bh=(30, -73), fh=(15, -74)),
      P(STANCE, hip=(1, -41), torso=-78, bh=(16, -75))]
LK = [P(STANCE, hip=(-3, -42), torso=-96, ff=(14, -26), ffp=(1, -0.5), bf=(-8, -3)),
      P(STANCE, hip=(-4, -42), torso=-104, head=-96, ff=(42, -32), fff=-25, bf=(-8, -3)),
      P(STANCE, hip=(-3, -42), torso=-98, ff=(16, -24), ffp=(1, -0.5), bf=(-8, -3)),
      P(STANCE, hip=(-1, -41), torso=-86)]
HK = [P(STANCE, hip=(-4, -42), torso=-104, head=-96, ff=(12, -44), ffp=(1, -0.4), bf=(-9, -3)),
      P(STANCE, hip=(-6, -43), torso=-120, head=-100, ff=(43, -62), fff=-35, bf=(-10, -3), fh=(14, -76), bh=(4, -78)),
      P(STANCE, hip=(-6, -43), torso=-118, head=-100, ff=(42, -60), fff=-30, bf=(-10, -3), fh=(14, -76), bh=(4, -78)),
      P(STANCE, hip=(-4, -42), torso=-104, ff=(20, -36), ffp=(1, -0.3), bf=(-9, -3)),
      P(STANCE, hip=(-2, -41), torso=-90)]
# --- crouching normals
C_LP = [P(CROUCH, fh=(16, -52)),
        P(CROUCH, torso=-66, fh=(42, -50)),
        P(CROUCH, fh=(28, -51))]
C_HP = [P(CROUCH, hip=(-1, -23), torso=-68, bh=(8, -44)),
        P(CROUCH, hip=(2, -34), torso=-96, head=-100, bh=(20, -98), fh=(16, -62), ff=(14, -3), bf=(-12, -3)),
        P(CROUCH, hip=(2, -33), torso=-94, head=-98, bh=(19, -96), fh=(16, -62), ff=(14, -3), bf=(-12, -3)),
        P(CROUCH, hip=(0, -28), torso=-80, bh=(16, -66)),
        CROUCH]
C_LK = [P(CROUCH, hip=(-3, -25), torso=-80, ff=(18, -8)),
        P(CROUCH, hip=(-4, -24), torso=-84, ff=(40, -4), fff=0),
        P(CROUCH, hip=(-3, -25), torso=-80, ff=(24, -5))]
C_HK = [P(CROUCH, hip=(-3, -21), torso=-58, fh=(10, -14), bh=(4, -18)),
        P(CROUCH, hip=(-5, -17), torso=-60, ff=(47, -4), fff=5, bf=(-14, -3), fh=(8, -6), bh=(2, -10)),
        P(CROUCH, hip=(-5, -17), torso=-62, ff=(45, -4), fff=5, bf=(-14, -3), fh=(8, -6), bh=(2, -10)),
        P(CROUCH, hip=(-4, -20), torso=-64, ff=(28, -4), fh=(12, -20), bh=(6, -26)),
        CROUCH]
# --- air normals
J_P = [P(JUMP_TUCK, bh=(4, -70)),
       P(JUMP_TUCK, torso=-62, head=-70, bh=(40, -50), fh=(16, -72)),
       P(JUMP_TUCK, torso=-66, bh=(30, -54))]
J_K = [P(JUMP_TUCK),
       P(JUMP_TUCK, hip=(-2, -44), torso=-100, head=-90, ff=(40, -24), fff=25, bf=(0, -30)),
       P(JUMP_TUCK, hip=(-2, -44), torso=-98, head=-90, ff=(36, -24), fff=25, bf=(0, -30))]
# --- specials
RUSH = [P(STANCE, hip=(-5, -40), torso=-102, head=-94, bh=(-10, -64), fh=(17, -77)),
        P(STANCE, hip=(9, -37), torso=-56, head=-68, bh=(56, -66), fh=(18, -62), ff=(27, -3), bf=(-19, -3), bff=28),
        P(STANCE, hip=(10, -37), torso=-55, head=-68, bh=(57, -66), fh=(18, -61), ff=(28, -3), bf=(-19, -3), bff=28),
        P(STANCE, hip=(5, -40), torso=-70, bh=(32, -70), fh=(17, -70)),
        P(STANCE, hip=(2, -41), torso=-78, bh=(18, -74))]
HOOK = [P(CROUCH, hip=(0, -30), torso=-68, bh=(10, -46)),
        P(STANCE, hip=(2, -45), torso=-98, head=-102, bh=(18, -104), fh=(16, -62), ff=(10, -12), bf=(-8, -4)),
        P(STANCE, hip=(1, -47), torso=-100, head=-104, bh=(13, -108), fh=(16, -64), ff=(12, -22), bf=(-4, -15)),
        P(JUMP_FALL, bh=(18, -84), torso=-88)]
SUPER = [P(STANCE, hip=(-2, -40), torso=-96, head=-92, fh=(18, -78), bh=(14, -80)),   # flash pose
         LP[1], HP[1], LP[1], HP[2],
         P(STANCE, hip=(4, -43), torso=-100, head=-104, bh=(20, -106), fh=(16, -64), ff=(14, -8), bf=(-10, -3)),
         P(STANCE, hip=(3, -42), torso=-90, bh=(18, -90))]

PORTRAIT_POSE = P(STANCE, torso=-86, head=-88, fh=(20, -62), bh=(14, -66))

ANIMS = [
    ('idle', idle_frames(), 7, True, {}),
    ('walk_fwd', gait(STANCE), 10, True, {}),
    ('walk_back', gait(STANCE, reverse=True), 9, True, {}),
    ('crouch', [CROUCH_IN, CROUCH], 15, False, {}),
    ('jump', [JUMP_RISE, JUMP_TUCK, JUMP_FALL], 8, False, {}),
    ('land', [LAND], 10, False, {}),
    ('block', [BLOCK], 1, False, {}),
    ('block_crouch', [BLOCK_C], 1, False, {}),
    ('hit_light', [HIT_L, R.lerp_pose(HIT_L, STANCE, 0.5)], 10, False, {}),
    ('hit_heavy', [HIT_H, R.lerp_pose(HIT_H, STANCE, 0.4)], 8, False, {}),
    ('hit_crouch', [HIT_C, R.lerp_pose(HIT_C, CROUCH, 0.5)], 10, False, {}),
    ('knockdown', [KD0, KD1, KD2, KD3], 8, False, {}),
    ('getup', [GET0, GET1, CROUCH_IN], 8, False, {}),
    ('victory', VICT, 6, True, {}),
    ('defeat', DEFEAT, 3, True, {}),
    ('intro', INTRO, 6, False, {}),
    ('lp', LP, 20, False, {'active': [1], 'strike': 'fh', 'hr': 8}),
    ('hp', HP, 15, False, {'active': [1, 2], 'strike': 'bh', 'hr': 9}),
    ('lk', LK, 15, False, {'active': [1], 'strike': 'ff', 'hr': 9}),
    ('hk', HK, 12, False, {'active': [1, 2], 'strike': 'ff', 'hr': 10}),
    ('c_lp', C_LP, 20, False, {'active': [1], 'strike': 'fh', 'hr': 8}),
    ('c_hp', C_HP, 14, False, {'active': [1, 2], 'strike': 'bh', 'hr': 11}),
    ('c_lk', C_LK, 18, False, {'active': [1], 'strike': 'ff', 'hr': 7}),
    ('c_hk', C_HK, 12, False, {'active': [1, 2], 'strike': 'ff', 'hr': 9}),
    ('j_p', J_P, 14, False, {'active': [1], 'strike': 'bh', 'hr': 10}),
    ('j_k', J_K, 14, False, {'active': [1], 'strike': 'ff', 'hr': 10}),
    ('sp_rush', RUSH, 12, False, {'active': [1, 2], 'strike': 'bh', 'hr': 11}),
    ('sp_hook', HOOK, 12, False, {'active': [1, 2], 'strike': 'bh', 'hr': 12}),
    ('super', SUPER, 12, False, {'active': [1, 2, 3, 4, 5], 'strike': ['fh', 'bh'], 'hr': 10}),
]
