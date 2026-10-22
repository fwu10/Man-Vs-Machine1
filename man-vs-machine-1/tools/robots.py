"""The five robot opponents: SPARK, BULWARK, VOLT, RAZOR, OVERLORD.

Poses are authored in boxer-sized units and scaled by each robot's size factor
k; the skeleton IK adapts them to each body.  Silhouettes come from the part
builders (armour shapes) plus unique stances and attack poses.
"""
import math
from types import SimpleNamespace as NS

import pixelrig as R
from pixelrig import capsule, ellipse, poly, line, dot, Part, ramp, emit, on_frame, on_limb, add, mul, sub, norm, lerp
import char_boxer as BX

P = BX.P


def body(k, **kw):
    b = dict(thigh=22 * k, shin=22 * k, uarm=17 * k, farm=16 * k, torso=30 * k, neck=3 * k, head_r=8 * k,
             sh_f=6 * k, sh_b=7 * k, sh_drop=3 * k, hip_off=4 * k, foot=9 * k)
    b.update(kw)
    return R.Body(**b)


def frames_of(st, cr):
    """Derive the generic movement / reaction animations from a stance."""
    idle = [P(st, hip=(st['hip'][0], st['hip'][1] + b), fh=(st['fh'][0], st['fh'][1] + b * 1.2),
              bh=(st['bh'][0], st['bh'][1] + b * 1.2)) for b in (0, 0.8, 1.5, 0.8)]
    hands = lambda p, dy=0: P(p, fh=(st['fh'][0], st['fh'][1] + dy), bh=(st['bh'][0], st['bh'][1] + dy))
    return {
        'idle': idle,
        'walk_fwd': BX.gait(st),
        'walk_back': BX.gait(st, reverse=True),
        'crouch': [R.lerp_pose(st, cr, 0.55), cr],
        'jump': [hands(BX.JUMP_RISE, -2), hands(P(BX.JUMP_TUCK, torso=st['torso'] + 6), 2), hands(BX.JUMP_FALL, -2)],
        'land': [R.lerp_pose(st, cr, 0.6)],
        'hit_light': [BX.HIT_L, R.lerp_pose(BX.HIT_L, st, 0.5)],
        'hit_heavy': [BX.HIT_H, R.lerp_pose(BX.HIT_H, st, 0.4)],
        'hit_crouch': [P(cr, torso=-100, head=-115), R.lerp_pose(P(cr, torso=-100, head=-115), cr, 0.5)],
        'knockdown': [BX.KD0, BX.KD1, BX.KD2, BX.KD3],
        'getup': [BX.GET0, BX.GET1, R.lerp_pose(st, cr, 0.55)],
    }


def make(ID, k, FRAME, OUTLINE, CORE_W, BODY, build_parts, st, cr, block, block_c, victory, defeat, intro,
         attacks, specials, portrait_box):
    g = frames_of(st, cr)
    A = [
        ('idle', g['idle'], 7, True, {}),
        ('walk_fwd', g['walk_fwd'], 10, True, {}),
        ('walk_back', g['walk_back'], 9, True, {}),
        ('crouch', g['crouch'], 15, False, {}),
        ('jump', g['jump'], 8, False, {}),
        ('land', g['land'], 10, False, {}),
        ('block', [block], 1, False, {}),
        ('block_crouch', [block_c], 1, False, {}),
        ('hit_light', g['hit_light'], 10, False, {}),
        ('hit_heavy', g['hit_heavy'], 8, False, {}),
        ('hit_crouch', g['hit_crouch'], 10, False, {}),
        ('knockdown', g['knockdown'], 8, False, {}),
        ('getup', g['getup'], 8, False, {}),
        ('victory', victory, 6, True, {}),
        ('defeat', defeat, 3, True, {}),
        ('intro', intro, 6, False, {}),
    ]
    for name in ('lp', 'hp', 'lk', 'hk', 'c_lp', 'c_hp', 'c_lk', 'c_hk', 'j_p', 'j_k'):
        poses, fps, info = attacks[name]
        A.append((name, poses, fps, False, info))
    for name, poses, fps, info in specials:
        A.append((name, poses, fps, info.pop('loop', False), info))
    A = [(n, [R.scale_pose(p, k) for p in poses], fps, loop, info) for n, poses, fps, loop, info in A]
    return NS(ID=ID, FRAME=FRAME, OUTLINE=OUTLINE, CORE_W=CORE_W, BODY=BODY, build_parts=build_parts,
              ANIMS=A, PORTRAIT_POSE=R.scale_pose(P(st, fh=(st['fh'][0], st['fh'][1] + 6),
                                                     bh=(st['bh'][0], st['bh'][1] + 6)), k),
              PORTRAIT_BOX=portrait_box)


def frames(sk):
    tl = lambda f, u: add(add(sk.hip, mul(sk.p, f)), mul(sk.u, u))
    hl = lambda f, u: add(add(sk.head, mul(sk.hp, f)), mul(sk.hu, u))
    return tl, hl


def seg_plate(a, b, t0, t1, w0, w1, rp, bias=0, bevel=1.5):
    L = R.length(sub(b, a))
    return poly(on_limb(a, b, [(t0 * L, -w0), (t1 * L, -w1), (t1 * L, w1), (t0 * L, w0)]), rp, bias, bevel)


def foot_poly(an, fa, pts, rp, bevel=1.4):
    fd = R.dirv(fa)
    up = (fd[1], -fd[0])
    return poly(on_frame(an, fd, up, pts), rp, bevel=bevel)


# =================================================================== SPARK
SP_WHITE = ramp('#3a404e', '#727a8c', '#b2b8c6', '#e0e4ec', '#ffffff')
SP_STEEL = ramp('#14161c', '#2a2e38', '#464c5a', '#6a7282', '#949cae')
SP_OR = ramp('#4a1a04', '#8e3c0a', '#e06a12', '#ff9a34', '#ffd486')
SP_GLOW = emit('#802800', '#c04000', '#ff7a10', '#ffb040', '#fff0b0')


def spark_parts(sk):
    tl, hl = frames(sk)
    k = 0.96

    def arm(sh, el, wr, back):
        d = norm(sub(wr, el))
        fist = add(wr, mul(d, 4.2))
        return Part([
            capsule(sh, el, 3.4, 3.2, SP_STEEL),
            seg_plate(sh, el, -0.1, 0.8, 5.0, 4.2, SP_WHITE),
            ellipse(el, 3.4, 3.4, 0, SP_STEEL),
            capsule(el, wr, 4.6, 3.8, SP_WHITE),
            line(lerp(el, wr, 0.25), lerp(el, wr, 0.8), SP_OR[2]),
            ellipse(fist, 5.0, 4.6, R.ang(d), SP_STEEL),
            capsule(add(fist, mul(d, 1.5)), add(fist, mul(d, 1.6)), 3.6, 3.6, SP_WHITE),
            ellipse(sh, 5.6, 5.0, 0, SP_WHITE),
            dot(sh, SP_OR[3]),
        ], SP_WHITE, back=back)

    def leg(hp, kn, an, fa, back):
        return Part([
            capsule(hp, kn, 4.0, 3.6, SP_STEEL),
            seg_plate(hp, kn, 0.0, 0.85, 6.2, 5.0, SP_WHITE),
            capsule(kn, an, 3.2, 3.0, SP_STEEL),
            seg_plate(kn, an, 0.15, 1.0, 5.2, 4.6, SP_WHITE),
            ellipse(kn, 3.8, 3.8, 0, SP_OR),
            foot_poly(an, fa, [(-4.5, 3.0), (-5.0, -2.6), (9.5, -2.6), (10.0, 0.4), (4.0, 3.2)], SP_WHITE),
            foot_poly(an, fa, [(-5.0, -1.4), (-5.0, -2.8), (10.0, -2.8), (10.0, -1.4)], SP_STEEL, 0.8),
        ], SP_WHITE, back=back)

    parts = [arm(sk.sh_b, sk.el_b, sk.wr_b, True), leg(sk.hip_b, sk.kn_b, sk.an_b, sk.fa_b, True)]
    parts.append(Part([
        capsule(tl(0, 3), tl(0, 13), 7.0, 7.4, SP_STEEL),
        line(tl(-6, 7), tl(6, 7), SP_STEEL[0]), line(tl(-6, 11), tl(6, 11), SP_STEEL[0]),
        poly([tl(-10, 15), tl(10, 15), tl(12.5, 26), tl(9, 31), tl(-9, 31), tl(-11, 25)], SP_WHITE, bevel=2.2),
        line(tl(3, 18), tl(10, 18), SP_OR[2]),
        ellipse(tl(4.5, 23), 2.6, 2.6, 0, SP_GLOW),
        ellipse(tl(0, 1), 9.0, 6.0, sk.ta + 90, SP_STEEL),
        poly([tl(-9, 4), tl(9, 4), tl(8, -3), tl(-8, -3)], SP_WHITE, bevel=1.4),
        line(tl(-2, -2), tl(4, -2), SP_OR[2]),
    ], SP_WHITE))
    parts.append(leg(sk.hip_f, sk.kn_f, sk.an_f, sk.fa_f, False))
    parts.append(Part([
        capsule(sk.neck, lerp(sk.neck, sk.head, 0.5), 3.4, 3.4, SP_STEEL),
        ellipse(sk.head, 7.2, 7.8, sk.ha + 90, SP_WHITE),
        poly([hl(-2, -3), hl(6, -3), hl(6.5, -7), hl(0, -8)], SP_STEEL, bevel=1),
        poly([hl(1.5, 3.4), hl(7.8, 3.0), hl(7.6, -0.6), hl(1.0, -0.4)], SP_GLOW, bevel=1),
        ellipse(hl(-2, 0.5), 2.6, 2.6, 0, SP_OR),
        line(hl(-3, 6), hl(-6, 12), SP_STEEL[2]),
        dot(hl(-6, 12), SP_OR[4]),
        line(hl(2, 6.5), hl(-4, 7.6), SP_OR[2]),
    ], SP_WHITE))
    parts.append(arm(sk.sh_f, sk.el_f, sk.wr_f, False))
    return parts


SP_ST = dict(hip=(0, -41), torso=-84, head=-88, ff=(12, -3), bf=(-11, -3), fh=(21, -63), bh=(9, -61))
SP_CR = P(SP_ST, hip=(-1, -26), torso=-74, head=-84, ff=(14, -3), bf=(-12, -3), fh=(21, -48), bh=(11, -46))


def spark():
    st, cr = SP_ST, SP_CR
    atk = {
        'lp': ([P(st, fh=(16, -64)), P(st, hip=(2, -41), torso=-78, fh=(45, -66)), P(st, fh=(30, -65)), st],
               20, {'active': [1], 'strike': 'fh', 'hr': 8}),
        'hp': ([P(st, torso=-92, bh=(2, -64)), P(st, hip=(5, -40), torso=-68, bh=(50, -68), fh=(12, -66), bf=(-13, -3), bff=25),
                P(st, hip=(5, -40), torso=-70, bh=(47, -68), fh=(12, -66), bf=(-13, -3), bff=25), P(st, bh=(28, -66)), st],
               15, {'active': [1, 2], 'strike': 'bh', 'hr': 9}),
        'lk': ([P(BX.LK[0], fh=st['fh'], bh=st['bh']), P(BX.LK[1], fh=st['fh'], bh=st['bh']), P(BX.LK[2], fh=st['fh'], bh=st['bh']), st],
               15, {'active': [1], 'strike': 'ff', 'hr': 9}),
        'hk': ([BX.HK[0], BX.HK[1], BX.HK[2], BX.HK[3], st], 12, {'active': [1, 2], 'strike': 'ff', 'hr': 10}),
        'c_lp': ([P(cr, fh=(16, -50)), P(cr, torso=-68, fh=(42, -48)), P(cr, fh=(28, -49))], 20, {'active': [1], 'strike': 'fh', 'hr': 8}),
        'c_hp': ([P(cr, bh=(8, -42)), P(cr, hip=(2, -34), torso=-96, bh=(20, -96), fh=(16, -60)), P(cr, hip=(2, -33), torso=-94, bh=(19, -94)), P(cr, bh=(14, -64)), cr],
                 14, {'active': [1, 2], 'strike': 'bh', 'hr': 11}),
        'c_lk': ([P(cr, ff=(18, -8)), P(cr, hip=(-4, -24), torso=-84, ff=(40, -4)), P(cr, ff=(24, -5))], 18, {'active': [1], 'strike': 'ff', 'hr': 7}),
        'c_hk': ([BX.C_HK[0], BX.C_HK[1], BX.C_HK[2], BX.C_HK[3], cr], 12, {'active': [1, 2], 'strike': 'ff', 'hr': 9}),
        'j_p': ([BX.J_P[0], BX.J_P[1], BX.J_P[2]], 14, {'active': [1], 'strike': 'bh', 'hr': 10}),
        'j_k': ([BX.J_K[0], BX.J_K[1], BX.J_K[2]], 14, {'active': [1], 'strike': 'ff', 'hr': 10}),
    }
    dash0 = P(st, hip=(-4, -38), torso=-70, fh=(12, -58), bh=(6, -56))
    dash1 = P(st, hip=(8, -36), torso=-48, head=-60, fh=(26, -60), bh=(18, -54), ff=(26, -3), bf=(-16, -3), bff=25)
    shot0 = P(st, torso=-96, fh=(6, -60), bh=(2, -62))
    shot1 = P(st, hip=(3, -41), torso=-76, fh=(38, -64), bh=(34, -60))
    specials = [
        ('sp_dash', [dash0, dash1, dash1, R.lerp_pose(dash1, st, 0.5), st], 12, {'active': [1, 2], 'strike': 'body', 'hr': 14}),
        ('sp_shot', [shot0, shot1, shot1, st], 10, {}),
    ]
    vict = [P(st, torso=-92, bh=(4, -98), fh=(16, -60)), P(st, torso=-94, bh=(3, -102), fh=(16, -62)),
            P(st, torso=-94, bh=(3, -103), fh=(16, -63)), P(st, torso=-92, bh=(4, -99), fh=(16, -61))]
    defeat = [P(st, hip=(2, -36), torso=-60, head=-20, fh=(14, -30), bh=(6, -32)), P(st, hip=(2, -35), torso=-58, head=-24, fh=(14, -29), bh=(6, -31))]
    intro = [P(st, torso=-92, fh=(14, -40), bh=(8, -40)), P(st, torso=-90, fh=(30, -66), bh=(14, -42)), P(st, torso=-86, fh=(22, -64), bh=(10, -62)), st]
    block = P(st, hip=(-2, -41), torso=-96, head=-98, fh=(16, -78), bh=(12, -74))
    block_c = P(cr, torso=-86, fh=(16, -56), bh=(12, -58))
    k = 0.96
    return make('spark', k, (136, 116, 68, 108), (12, 14, 24, 255), 28, body(k), spark_parts, st, cr, block, block_c,
                vict, defeat, intro, atk, specials, (-20, -94, 44, 40))


# =================================================================== BULWARK
BW_GUN = ramp('#121418', '#282c32', '#444a54', '#68707c', '#949ca8')
BW_DARK = ramp('#0a0b0e', '#181a20', '#282c34', '#3c414c', '#565c68')
BW_YEL = ramp('#4a3606', '#8e6a0e', '#d8a81c', '#f8d24a', '#fff2a8')
BW_RED = emit('#600000', '#a00808', '#ff2a1a', '#ff7a5a', '#ffd0c0')


def bulwark_parts(sk):
    tl, hl = frames(sk)

    def arm(sh, el, wr, back):
        d = norm(sub(wr, el))
        n = (-d[1], d[0])
        c = add(wr, mul(d, 9.0))
        fist = on_frame(c, d, mul(n, -1), [(-8, -10), (9, -10.5), (11, -6), (11, 6), (9, 10.5), (-8, 10)])
        return Part([
            capsule(sh, el, 4.4, 4.4, BW_DARK),
            seg_plate(sh, el, 0.15, 0.8, 6.0, 5.6, BW_GUN),
            ellipse(el, 5.4, 5.4, 0, BW_DARK),
            capsule(el, wr, 6.0, 6.8, BW_GUN),
            line(lerp(el, wr, 0.3), lerp(el, wr, 0.9), BW_YEL[2]),
            poly(fist, BW_GUN, bevel=2.6),
            line(add(c, mul(n, 6)), add(c, mul(n, -6)), BW_DARK[1]),
            capsule(add(c, add(mul(d, 9.5), mul(n, 7))), add(c, add(mul(d, 9.5), mul(n, -7))), 1.5, 1.5, BW_YEL),
            # pauldron
            ellipse(add(sh, (0, -2)), 11.5, 9.5, 0, BW_GUN),
            poly([add(sh, (-10, -6)), add(sh, (10, -9)), add(sh, (11, -5)), add(sh, (-10, -2))], BW_YEL, bevel=1),
            line(add(sh, (-4, -7)), add(sh, (-2, -3)), BW_DARK[0]), line(add(sh, (2, -8)), add(sh, (4, -4)), BW_DARK[0]),
        ], BW_GUN, back=back)

    def leg(hp, kn, an, fa, back):
        return Part([
            capsule(hp, kn, 6.0, 5.4, BW_DARK),
            seg_plate(hp, kn, 0.0, 0.8, 8.4, 7.4, BW_GUN),
            ellipse(kn, 5.6, 5.6, 0, BW_YEL),
            capsule(kn, an, 7.6, 8.8, BW_GUN),
            line(lerp(kn, an, 0.3), lerp(kn, an, 0.8), BW_DARK[1]),
            foot_poly(an, fa, [(-8, 4), (-9, -3.4), (13, -3.4), (13.5, 1), (6, 4.5)], BW_DARK, 2.0),
        ], BW_GUN, back=back)

    parts = []
    # exhaust stacks
    parts.append(Part([capsule(tl(-12, 28), tl(-16, 44), 2.8, 2.8, BW_DARK), capsule(tl(-6, 30), tl(-9, 46), 2.6, 2.6, BW_DARK),
                       ellipse(tl(-16, 45), 3.4, 1.8, 0, BW_GUN), ellipse(tl(-9, 47), 3.2, 1.8, 0, BW_GUN)], BW_DARK))
    parts.append(arm(sk.sh_b, sk.el_b, sk.wr_b, True))
    parts.append(leg(sk.hip_b, sk.kn_b, sk.an_b, sk.fa_b, True))
    parts.append(Part([
        ellipse(tl(0, 4), 13, 9, sk.ta + 90, BW_DARK),
        capsule(tl(0, 9), tl(1, 25), 15.5, 18.0, BW_GUN),
        poly([tl(-13, 8), tl(14, 8), tl(13, 14), tl(-13, 14)], BW_YEL, bevel=1),
        line(tl(-10, 8), tl(-6, 14), BW_DARK[0]), line(tl(-3, 8), tl(1, 14), BW_DARK[0]),
        line(tl(4, 8), tl(8, 14), BW_DARK[0]), line(tl(11, 8), tl(13, 12), BW_DARK[0]),
        poly([tl(2, 18), tl(14, 18), tl(14, 28), tl(2, 28)], BW_DARK, bevel=1.2),
        line(tl(4, 20), tl(12, 20), BW_GUN[3]), line(tl(4, 23), tl(12, 23), BW_GUN[3]), line(tl(4, 26), tl(12, 26), BW_GUN[3]),
    ], BW_GUN))
    parts.append(leg(sk.hip_f, sk.kn_f, sk.an_f, sk.fa_f, False))
    parts.append(Part([
        poly([hl(-7, -5), hl(7, -5), hl(9, -1), hl(8, 6), hl(-6, 7), hl(-8, 2)], BW_GUN, bevel=1.8),
        poly([hl(2, 1.6), hl(9, 1.6), hl(9, -0.6), hl(2, -0.6)], BW_RED, bevel=0.6),
        line(hl(-6, -3), hl(6, -3), BW_DARK[1]),
    ], BW_GUN))
    parts.append(arm(sk.sh_f, sk.el_f, sk.wr_f, False))
    return parts


BW_ST = dict(hip=(0, -37), torso=-70, head=-80, ff=(16, -3), bf=(-15, -3), fh=(30, -50), bh=(24, -56))
BW_CR = P(BW_ST, hip=(-1, -26), torso=-58, head=-74, ff=(16, -3), bf=(-14, -3), fh=(24, -38), bh=(14, -36))


def bulwark():
    st, cr = BW_ST, BW_CR
    hammer0 = P(st, hip=(-3, -39), torso=-102, head=-92, fh=(8, -94), bh=(2, -94))
    hammer1 = P(st, hip=(6, -34), torso=-38, head=-55, fh=(38, -34), bh=(34, -36), ff=(20, -3), bf=(-16, -3))
    atk = {
        'lp': ([P(st, fh=(24, -52)), P(st, hip=(2, -37), torso=-62, fh=(46, -56)), P(st, fh=(30, -54)), st], 16, {'active': [1], 'strike': 'fh', 'hr': 9}),
        'hp': ([hammer0, R.lerp_pose(hammer0, hammer1, 0.5), hammer1, hammer1, R.lerp_pose(hammer1, st, 0.5), st], 12, {'active': [2, 3], 'strike': ['fh', 'bh'], 'hr': 10}),
        'lk': ([P(st, hip=(-2, -38), ff=(14, -18)), P(st, hip=(-3, -38), torso=-72, ff=(34, -12), fff=0), P(st, ff=(20, -10)), st], 14, {'active': [1], 'strike': 'ff', 'hr': 9}),
        'hk': ([P(st, hip=(-3, -39), torso=-90, ff=(12, -36)), P(st, hip=(-5, -39), torso=-104, ff=(40, -40), fff=-20, fh=(18, -64), bh=(8, -64)),
                P(st, hip=(-5, -39), torso=-102, ff=(38, -38), fff=-20, fh=(18, -64), bh=(8, -64)), P(st, ff=(22, -20)), st], 10, {'active': [1, 2], 'strike': 'ff', 'hr': 11}),
        'c_lp': ([P(cr, fh=(18, -38)), P(cr, fh=(40, -36)), P(cr, fh=(28, -37))], 16, {'active': [1], 'strike': 'fh', 'hr': 9}),
        'c_hp': ([P(cr, bh=(10, -30)), P(cr, hip=(2, -32), torso=-92, bh=(20, -88)), P(cr, hip=(2, -32), torso=-92, bh=(20, -86)), P(cr, bh=(18, -56)), cr], 11, {'active': [1, 2], 'strike': 'bh', 'hr': 12}),
        'c_lk': ([P(cr, ff=(18, -10)), P(cr, ff=(38, -4)), P(cr, ff=(24, -5))], 14, {'active': [1], 'strike': 'ff', 'hr': 8}),
        'c_hk': ([P(cr, hip=(-3, -22), torso=-50, fh=(14, -16)), P(cr, hip=(-4, -18), torso=-52, ff=(44, -4), fh=(12, -8), bh=(4, -10)),
                  P(cr, hip=(-4, -18), torso=-52, ff=(42, -4), fh=(12, -8), bh=(4, -10)), P(cr, ff=(26, -4)), cr], 10, {'active': [1, 2], 'strike': 'ff', 'hr': 10}),
        'j_p': ([P(BX.JUMP_TUCK, fh=(8, -86), bh=(2, -86)), P(BX.JUMP_TUCK, torso=-50, fh=(34, -40), bh=(30, -42)), P(BX.JUMP_TUCK, torso=-55, fh=(30, -44), bh=(26, -46))], 12, {'active': [1], 'strike': ['fh', 'bh'], 'hr': 10}),
        'j_k': ([P(BX.JUMP_TUCK, fh=st['fh'], bh=st['bh']), P(BX.JUMP_TUCK, ff=(24, -16), bf=(4, -24), fh=(24, -54), bh=(14, -54)), P(BX.JUMP_TUCK, ff=(22, -18), fh=(24, -54), bh=(14, -54))], 12, {'active': [1], 'strike': 'fk', 'hr': 12}),
    }
    stomp0 = P(st, hip=(-2, -40), torso=-80, ff=(16, -40), ffp=(1, -0.3), bf=(-12, -3), fh=(22, -62), bh=(12, -60))
    stomp1 = P(st, hip=(2, -32), torso=-56, ff=(22, -3), fh=(26, -30), bh=(18, -28))
    specials = [
        ('sp_hammer', [hammer0, P(hammer0, fh=(4, -98), bh=(-2, -98)), R.lerp_pose(hammer0, hammer1, 0.5), hammer1, hammer1, hammer1, R.lerp_pose(hammer1, st, 0.5)],
         10, {'active': [3, 4], 'strike': ['fh', 'bh'], 'hr': 13}),
        ('sp_stomp', [stomp0, P(stomp0, ff=(17, -44)), stomp1, stomp1, R.lerp_pose(stomp1, st, 0.5)], 9, {}),
    ]
    vict = [P(st, torso=-90, fh=(30, -70), bh=(20, -72)), P(st, torso=-92, fh=(26, -80), bh=(16, -82)),
            P(st, torso=-92, fh=(26, -81), bh=(16, -83)), P(st, torso=-90, fh=(30, -72), bh=(20, -74))]
    defeat = [P(st, hip=(2, -33), torso=-50, head=-20, fh=(26, -20), bh=(16, -20)), P(st, hip=(2, -32), torso=-48, head=-18, fh=(26, -19), bh=(16, -19))]
    intro = [P(st, torso=-80, fh=(20, -56), bh=(18, -56)), P(st, torso=-84, fh=(24, -60), bh=(22, -60)), P(st, torso=-70, fh=(22, -52), bh=(20, -52)), st]
    block = P(st, hip=(-2, -37), torso=-80, head=-88, fh=(20, -66), bh=(16, -68))
    block_c = P(cr, torso=-70, fh=(20, -46), bh=(16, -48))
    k = 1.22
    return make('bulwark', k, (184, 140, 92, 132), (8, 10, 14, 255), 44, body(k, sh_f=11 * k, sh_b=11 * k, head_r=7 * k, neck=1),
                bulwark_parts, st, cr, block, block_c, vict, defeat, intro, atk, specials, (-30, -98, 64, 50))


# =================================================================== VOLT
VT_NAVY = ramp('#0a0e1c', '#18223e', '#2a3c6a', '#4a64a0', '#7c98d4')
VT_BLK = ramp('#06070c', '#10131c', '#1c2030', '#2c3246', '#444c66')
VT_CYAN = emit('#0a4a6a', '#1488b0', '#38e0ff', '#a0f8ff', '#ffffff')
VT_SIL = ramp('#2e343c', '#5c6670', '#9ca8b4', '#d8e0e8', '#ffffff')


def volt_parts(sk):
    tl, hl = frames(sk)

    def arm(sh, el, wr, back):
        d = norm(sub(wr, el))
        n = (-d[1], d[0])
        claw = on_frame(wr, d, n, [(0, -3), (9, -1.2), (11, 0), (9, 1.5), (0, 3)])
        return Part([
            capsule(sh, el, 2.8, 2.6, VT_BLK),
            poly(on_limb(sh, el, [(-2, 0), (6, -5), (13, -3.5), (16, 0), (6, 4)]), VT_NAVY, bevel=1.2),
            capsule(el, wr, 2.8, 2.4, VT_BLK),
            poly(on_limb(el, wr, [(1, -1), (8, -4.4), (15, -2), (15, 2), (6, 3.4)]), VT_NAVY, bevel=1.2),
            line(lerp(el, wr, 0.2), lerp(el, wr, 0.85), VT_CYAN[2]),
            poly(claw, VT_SIL, bevel=1),
            poly(on_limb(sh, el, [(-4, -4), (3, -7), (6, -3), (0, 3)]), VT_NAVY, 1, bevel=1),
        ], VT_NAVY, back=back)

    def leg(hp, kn, an, fa, back):
        return Part([
            capsule(hp, kn, 3.6, 3.0, VT_BLK),
            poly(on_limb(hp, kn, [(-1, -5.2), (14, -4.6), (21, 0), (14, 4), (0, 4.4)]), VT_NAVY, bevel=1.4),
            capsule(kn, an, 3.0, 2.4, VT_BLK),
            poly(on_limb(kn, an, [(-3, 0), (4, -4), (20, -2.6), (20, 1.6), (4, 3)]), VT_NAVY, bevel=1.2),
            line(lerp(kn, an, 0.1), lerp(kn, an, 0.85), VT_CYAN[2]),
            foot_poly(an, fa, [(-3, 2.5), (-4, -2.6), (12, -2.6), (8, 0.6), (2, 2.6)], VT_SIL, 1),
        ], VT_NAVY, back=back)

    parts = [arm(sk.sh_b, sk.el_b, sk.wr_b, True), leg(sk.hip_b, sk.kn_b, sk.an_b, sk.fa_b, True)]
    parts.append(Part([
        capsule(tl(0, 2), tl(0, 14), 5.0, 4.0, VT_BLK),
        poly([tl(-7, -2), tl(7, -2), tl(5, 4), tl(-5, 4)], VT_NAVY, bevel=1.2),
        poly([tl(-9, 30), tl(11, 30), tl(9, 21), tl(2, 12), tl(-6, 18)], VT_NAVY, bevel=2.0),
        poly([tl(2, 26), tl(7, 26), tl(4, 21), tl(6, 21), tl(1, 15), tl(3, 20), tl(0, 20)], VT_CYAN, bevel=0.8),
        line(tl(-1, 6), tl(1, 6), VT_CYAN[2]), line(tl(-1, 9), tl(1, 9), VT_CYAN[2]),
    ], VT_NAVY))
    parts.append(leg(sk.hip_f, sk.kn_f, sk.an_f, sk.fa_f, False))
    parts.append(Part([
        capsule(sk.neck, lerp(sk.neck, sk.head, 0.5), 2.4, 2.4, VT_BLK),
        poly([hl(-6, -3), hl(3, -7), hl(9, -2), hl(8, 4), hl(0, 7), hl(-5, 4)], VT_NAVY, bevel=1.6),
        poly([hl(-4, 4), hl(-9, 9), hl(-6, 9.5), hl(-12, 16), hl(-3, 8.5), hl(-6, 8), hl(-1, 5)], VT_CYAN, bevel=0.8),
        poly([hl(3, 2.6), hl(9, 1.0), hl(9, -0.6), hl(3, 0.6)], VT_CYAN, bevel=0.6),
    ], VT_NAVY))
    parts.append(arm(sk.sh_f, sk.el_f, sk.wr_f, False))
    return parts


VT_ST = dict(hip=(0, -40), torso=-70, head=-82, ff=(16, -4), fff=12, bf=(-14, -5), bff=30, fh=(26, -58), bh=(-8, -54))
VT_CR = P(VT_ST, hip=(-1, -25), torso=-62, head=-78, ff=(16, -3), fff=0, bf=(-14, -4), fh=(26, -42), bh=(-6, -38))


def volt():
    st, cr = VT_ST, VT_CR
    rush0 = P(st, hip=(-3, -36), torso=-55, fh=(10, -46), bh=(-14, -44))
    rush1 = P(st, hip=(10, -32), torso=-36, head=-48, fh=(46, -48), bh=(-14, -52), ff=(28, -4), bf=(-18, -3), bff=30)
    rush2 = P(rush1, fh=(40, -54), bh=(44, -44))
    atk = {
        'lp': ([P(st, fh=(22, -60)), P(st, hip=(2, -40), torso=-66, fh=(48, -62)), P(st, fh=(34, -60))], 24, {'active': [1], 'strike': 'fh', 'hr': 8}),
        'hp': ([P(st, torso=-80, bh=(-6, -66)), P(st, hip=(5, -39), torso=-58, bh=(50, -62), fh=(14, -52)), P(st, hip=(4, -39), torso=-62, bh=(40, -62), fh=(14, -52)), st], 18, {'active': [1], 'strike': 'bh', 'hr': 9}),
        'lk': ([P(st, ff=(16, -24), ffp=(1, -0.5)), P(st, hip=(-3, -41), torso=-92, ff=(44, -38), fff=-20), P(st, ff=(20, -20))], 20, {'active': [1], 'strike': 'ff', 'hr': 8}),
        'hk': ([P(st, hip=(-4, -42), torso=-110, ff=(14, -46)), P(st, hip=(-6, -43), torso=-126, head=-110, ff=(42, -70), fff=-50), P(st, hip=(-6, -43), torso=-124, ff=(38, -70), fff=-50), st], 15, {'active': [1, 2], 'strike': 'ff', 'hr': 10}),
        'c_lp': ([P(cr, fh=(20, -44)), P(cr, fh=(46, -42)), P(cr, fh=(30, -43))], 24, {'active': [1], 'strike': 'fh', 'hr': 8}),
        'c_hp': ([P(cr, bh=(4, -36)), P(cr, hip=(2, -34), torso=-100, bh=(18, -98)), P(cr, hip=(2, -34), torso=-98, bh=(16, -96)), cr], 16, {'active': [1, 2], 'strike': 'bh', 'hr': 11}),
        'c_lk': ([P(cr, ff=(18, -8)), P(cr, ff=(44, -4)), P(cr, ff=(26, -5))], 22, {'active': [1], 'strike': 'ff', 'hr': 7}),
        'c_hk': ([BX.C_HK[0], BX.C_HK[1], BX.C_HK[2], cr], 14, {'active': [1, 2], 'strike': 'ff', 'hr': 9}),
        'j_p': ([P(BX.JUMP_TUCK, fh=(12, -70), bh=(-8, -60)), P(BX.JUMP_TUCK, torso=-58, fh=(40, -46), bh=(-10, -64)), P(BX.JUMP_TUCK, torso=-62, fh=(32, -50), bh=(-10, -64))], 16, {'active': [1], 'strike': 'fh', 'hr': 10}),
        'j_k': ([P(BX.JUMP_TUCK, fh=st['fh'], bh=st['bh']), P(BX.J_K[1], fh=(20, -64), bh=(-10, -60), fff=40), P(BX.J_K[2], fh=(20, -64), bh=(-10, -60), fff=40)], 16, {'active': [1], 'strike': 'ff', 'hr': 10}),
    }
    bolt0 = P(st, torso=-86, fh=(4, -64), bh=(-12, -56))
    bolt1 = P(st, hip=(3, -40), torso=-66, fh=(46, -62), bh=(-10, -50))
    specials = [
        ('sp_bolt', [bolt0, P(bolt0, fh=(2, -68)), bolt1, bolt1, st], 12, {}),
        ('sp_rush', [rush0, rush1, rush2, rush1, rush2, R.lerp_pose(rush1, st, 0.5)], 14, {'active': [1, 2, 3, 4], 'strike': 'fh', 'hr': 12}),
    ]
    vict = [P(st, torso=-90, fh=(10, -102), bh=(-14, -58), ff=(12, -3), fff=0), P(st, torso=-94, fh=(8, -106), bh=(-14, -60), ff=(12, -3), fff=0),
            P(st, torso=-90, fh=(10, -103), bh=(-12, -58), ff=(12, -3), fff=0), P(st, torso=-92, fh=(9, -105), bh=(-14, -59), ff=(12, -3), fff=0)]
    defeat = [P(st, hip=(2, -36), torso=-58, head=-24, fh=(14, -30), bh=(6, -30)), P(st, hip=(2, -35), torso=-56, head=-22, fh=(14, -29), bh=(6, -29))]
    intro = [P(st, torso=-92, fh=(12, -100), bh=(-12, -56)), P(st, torso=-88, fh=(30, -78), bh=(-12, -56)), P(st, torso=-76, fh=(30, -64), bh=(-8, -54)), st]
    block = P(st, hip=(-3, -40), torso=-92, head=-96, fh=(16, -80), bh=(12, -72), fff=0, ff=(14, -3))
    block_c = P(cr, torso=-80, fh=(16, -56), bh=(12, -52))
    k = 1.02
    return make('volt', k, (148, 120, 74, 112), (4, 6, 14, 255), 24, body(k, sh_f=4, sh_b=5, head_r=7), volt_parts,
                st, cr, block, block_c, vict, defeat, intro, atk, specials, (-20, -98, 44, 40))


# =================================================================== RAZOR
RZ_DM = ramp('#08080c', '#14141c', '#24242e', '#383846', '#565668')
RZ_RD = ramp('#300408', '#6a0a12', '#c41622', '#ff4040', '#ff9a9a')
RZ_SIL = ramp('#2e343c', '#5c6670', '#9ca8b4', '#d8e0e8', '#ffffff')
RZ_EYE = emit('#500000', '#900000', '#ff2020', '#ff8080', '#ffe0e0')


def razor_parts(sk):
    tl, hl = frames(sk)
    wave = math.sin(sk.hip[0] * 0.3 + sk.hip[1] * 0.7) * 3

    def arm(sh, el, wr, back):
        d = norm(sub(wr, el))
        n = (-d[1], d[0])
        blade = on_frame(wr, d, n, [(-12, -3.6), (-4, -4.2), (15, -0.4), (16.5, 0.6), (-4, 1.0), (-12, 0.0)])
        return Part([
            capsule(sh, el, 3.6, 3.2, RZ_DM),
            seg_plate(sh, el, 0.1, 0.85, 4.6, 3.8, RZ_DM, 1),
            ellipse(el, 3.2, 3.2, 0, RZ_RD),
            capsule(el, wr, 3.8, 3.2, RZ_DM),
            poly(blade, RZ_SIL, bevel=1.2),
            line(add(wr, mul(n, -2.6)), add(add(wr, mul(d, 12)), mul(n, -0.6)), RZ_SIL[4]),
            ellipse(add(wr, mul(d, 2.5)), 3.6, 3.2, R.ang(d), RZ_DM),
            poly([add(sh, (-6, -1)), add(sh, (4, -6)), add(sh, (8, -1)), add(sh, (2, 4))], RZ_DM, bevel=1.4),
            line(add(sh, (-5, -1)), add(sh, (4, -5)), RZ_RD[2]),
        ], RZ_DM, back=back)

    def leg(hp, kn, an, fa, back):
        return Part([
            capsule(hp, kn, 5.0, 3.8, RZ_DM),
            capsule(kn, an, 3.8, 3.0, RZ_DM),
            poly(on_limb(kn, an, [(-4, 0), (2, -4.6), (16, -3), (18, 0)]), RZ_DM, 1, bevel=1.2),
            line(lerp(hp, kn, 0.2), lerp(hp, kn, 0.85), RZ_RD[2]),
            foot_poly(an, fa, [(-4, 2.8), (-4.6, -2.4), (12, -2.4), (9, 0.6), (2, 2.8)], RZ_DM, 1.2),
        ], RZ_DM, back=back)

    nk = sk.neck
    scarf = [add(nk, (2, -2)), add(nk, (-4, -3)), add(nk, (-16, 2 + wave)), add(nk, (-30, 6 + wave * 1.6)),
             add(nk, (-26, 10 + wave)), add(nk, (-34, 15 + wave * 2)), add(nk, (-18, 10 + wave * 0.6)), add(nk, (-6, 5)), add(nk, (2, 3))]
    parts = [Part([poly(scarf, RZ_RD, bevel=1.4)], RZ_RD)]
    parts += [arm(sk.sh_b, sk.el_b, sk.wr_b, True), leg(sk.hip_b, sk.kn_b, sk.an_b, sk.fa_b, True)]
    parts.append(Part([
        capsule(tl(0, 2), tl(0, 16), 6.0, 5.0, RZ_DM),
        poly([tl(-9, 31), tl(10, 31), tl(9, 22), tl(1, 13), tl(-8, 20)], RZ_DM, bevel=2.0),
        line(tl(1, 14), tl(8, 27), RZ_RD[2]), line(tl(1, 14), tl(-6, 26), RZ_RD[2]),
        ellipse(tl(0, 1), 7, 5, sk.ta + 90, RZ_DM, 1),
    ], RZ_DM))
    parts.append(leg(sk.hip_f, sk.kn_f, sk.an_f, sk.fa_f, False))
    parts.append(Part([
        capsule(sk.neck, lerp(sk.neck, sk.head, 0.4), 3.0, 3.0, RZ_DM),
        poly([hl(-6, -4), hl(4, -7), hl(8.5, -2), hl(8, 3), hl(2, 7), hl(-6, 6), hl(-14, 9), hl(-8, 2)], RZ_DM, bevel=1.6),
        poly([hl(2, 1.8), hl(8.6, 0.6), hl(8.6, -0.8), hl(2, 0.2)], RZ_EYE, bevel=0.5),
        line(hl(-5, 5), hl(-12, 8), RZ_RD[2]),
    ], RZ_DM))
    parts.append(arm(sk.sh_f, sk.el_f, sk.wr_f, False))
    return parts


RZ_ST = dict(hip=(-2, -37), torso=-76, head=-86, ff=(20, -3), bf=(-18, -3), bff=20, fh=(30, -62), bh=(-4, -74))
RZ_CR = P(RZ_ST, hip=(-2, -25), torso=-68, ff=(18, -3), bf=(-16, -3), fh=(28, -46), bh=(-2, -56))


def razor():
    st, cr = RZ_ST, RZ_CR
    lunge0 = P(st, hip=(-6, -36), torso=-90, fh=(10, -64), bh=(-8, -76))
    lunge1 = P(st, hip=(12, -28), torso=-48, head=-64, ff=(36, -3), bf=(-22, -3), bff=40, fh=(58, -50), bh=(-10, -64))
    parry = P(st, hip=(-3, -37), torso=-90, head=-92, fh=(20, -76), fhp=(1, 0.5), bh=(22, -62))
    slash0 = P(st, torso=-96, fh=(4, -90), bh=(-10, -60))
    slash1 = P(st, hip=(6, -34), torso=-58, fh=(44, -46), bh=(-8, -60), ff=(24, -3))
    atk = {
        'lp': ([P(st, fh=(24, -62)), P(st, hip=(3, -37), torso=-72, fh=(48, -62)), P(st, fh=(36, -62))], 22, {'active': [1], 'strike': 'fb', 'hr': 6}),
        'hp': ([slash0, R.lerp_pose(slash0, slash1, 0.5), slash1, R.lerp_pose(slash1, st, 0.5), st], 14, {'active': [1, 2], 'strike': 'fb', 'hr': 9}),
        'lk': ([P(st, ff=(18, -26), ffp=(1, -0.4)), P(st, hip=(-4, -38), torso=-98, ff=(46, -36), fff=-20), P(st, ff=(22, -22))], 16, {'active': [1], 'strike': 'ff', 'hr': 9}),
        'hk': ([P(st, hip=(-5, -39), torso=-110, ff=(14, -46)), P(st, hip=(-7, -40), torso=-124, ff=(46, -62), fff=-40), P(st, hip=(-7, -40), torso=-122, ff=(44, -60), fff=-40), st], 12, {'active': [1, 2], 'strike': 'ff', 'hr': 10}),
        'c_lp': ([P(cr, fh=(22, -44)), P(cr, fh=(48, -40)), P(cr, fh=(34, -42))], 22, {'active': [1], 'strike': 'fb', 'hr': 6}),
        'c_hp': ([P(cr, fh=(12, -30)), P(cr, hip=(2, -32), torso=-96, fh=(26, -92)), P(cr, hip=(2, -32), torso=-94, fh=(24, -90)), cr], 14, {'active': [1, 2], 'strike': 'fb', 'hr': 10}),
        'c_lk': ([P(cr, ff=(20, -8)), P(cr, ff=(46, -4)), P(cr, ff=(28, -5))], 18, {'active': [1], 'strike': 'ff', 'hr': 7}),
        'c_hk': ([BX.C_HK[0], BX.C_HK[1], BX.C_HK[2], cr], 12, {'active': [1, 2], 'strike': 'ff', 'hr': 10}),
        'j_p': ([P(BX.JUMP_TUCK, fh=(8, -84), bh=(-8, -66)), P(BX.JUMP_TUCK, torso=-56, fh=(42, -40), bh=(-8, -66)), P(BX.JUMP_TUCK, torso=-60, fh=(36, -44), bh=(-8, -66))], 14, {'active': [1], 'strike': 'fb', 'hr': 9}),
        'j_k': ([P(BX.JUMP_TUCK, fh=st['fh'], bh=st['bh']), P(BX.J_K[1], fh=(26, -62), bh=(-6, -70)), P(BX.J_K[2], fh=(26, -62), bh=(-6, -70))], 14, {'active': [1], 'strike': 'ff', 'hr': 10}),
    }
    counter1 = P(st, hip=(8, -33), torso=-52, fh=(56, -58), bh=(40, -66), ff=(30, -3), bf=(-20, -3))
    specials = [
        ('sp_lunge', [lunge0, P(lunge0, hip=(-7, -35)), lunge1, lunge1, lunge1, R.lerp_pose(lunge1, st, 0.5)], 12, {'active': [2, 3], 'strike': 'fb', 'hr': 9}),
        ('sp_parry', [parry, P(parry, hip=(-3, -36.5))], 6, {'loop': True}),
        ('sp_counter', [parry, counter1, counter1, R.lerp_pose(counter1, st, 0.5)], 14, {'active': [1, 2], 'strike': ['fb', 'bb'], 'hr': 12}),
    ]
    vict = [P(st, torso=-90, fh=(12, -96), bh=(-14, -48)), P(st, torso=-92, fh=(10, -100), bh=(-14, -48)),
            P(st, torso=-92, fh=(10, -101), bh=(-14, -49)), P(st, torso=-90, fh=(12, -97), bh=(-14, -48))]
    defeat = [P(st, hip=(2, -34), torso=-58, head=-20, fh=(16, -26), bh=(8, -28)), P(st, hip=(2, -33), torso=-56, head=-22, fh=(16, -25), bh=(8, -27))]
    intro = [P(st, torso=-92, fh=(4, -64), bh=(-2, -64)), P(st, torso=-88, fh=(40, -60), bh=(-6, -72)), P(st, torso=-80, fh=(34, -62), bh=(-4, -74)), st]
    block = P(st, hip=(-4, -37), torso=-92, head=-94, fh=(20, -76), fhp=(1, 0.5), bh=(18, -66))
    block_c = P(cr, torso=-82, fh=(20, -56), fhp=(1, 0.5), bh=(18, -48))
    k = 1.06
    return make('razor', k, (164, 120, 82, 112), (6, 4, 8, 255), 26, body(k, sh_f=5, sh_b=6, head_r=7.5), razor_parts,
                st, cr, block, block_c, vict, defeat, intro, atk, specials, (-22, -100, 48, 42))


# =================================================================== OVERLORD
OV_OBS = ramp('#07060c', '#141020', '#241c34', '#3a2e50', '#584872')
OV_CHR = ramp('#2c3038', '#5a626e', '#9aa4b0', '#d6dde6', '#ffffff')
OV_CORE = emit('#500000', '#a00000', '#ff1a1a', '#ff8060', '#fff0e0')
OV_CAPE = ramp('#0c0408', '#1e0a12', '#36121e', '#521a2c', '#70263c')
OV_JET = emit('#401000', '#a03000', '#ff6a10', '#ffc060', '#fff8e0')


def overlord_parts(sk):
    tl, hl = frames(sk)
    wave = math.sin(sk.hip[0] * 0.25 + sk.hip[1] * 0.5) * 3

    def arm(sh, el, wr, back):
        d = norm(sub(wr, el))
        n = (-d[1], d[0])
        claws = [poly(on_frame(wr, d, n, [(2, s - 1.4), (13, s * 1.6 - 0.5), (14, s * 1.6 + 0.8), (2, s + 1.4)]), OV_CHR, bevel=0.8) for s in (-3.2, 0, 3.2)]
        return Part([
            capsule(sh, el, 5.0, 4.4, OV_OBS),
            ellipse(el, 4.6, 4.6, 0, OV_CHR),
            capsule(el, wr, 5.8, 4.6, OV_OBS),
            seg_plate(el, wr, 0.15, 0.9, 6.8, 5.4, OV_OBS, 1),
            line(lerp(el, wr, 0.2), lerp(el, wr, 0.85), OV_CORE[2]),
            ellipse(add(wr, mul(d, 2)), 4.8, 4.4, 0, OV_OBS),
        ] + claws + [
            poly([add(sh, (-12, 2)), add(sh, (-8, -9)), add(sh, (2, -13)), add(sh, (12, -8)), add(sh, (10, 4)), add(sh, (-4, 7))], OV_OBS, bevel=2.4),
            poly([add(sh, (-6, -9)), add(sh, (-2, -22)), add(sh, (1, -11))], OV_CHR, bevel=1),
            line(add(sh, (-10, 1)), add(sh, (10, -7)), OV_CHR[2]),
        ], OV_OBS, back=back)

    def leg(hp, kn, an, fa, back):
        return Part([
            capsule(hp, kn, 7.0, 5.6, OV_OBS),
            capsule(kn, an, 5.6, 4.6, OV_OBS),
            seg_plate(kn, an, 0.0, 1.0, 7.2, 5.6, OV_OBS, 1),
            poly(on_limb(kn, an, [(-6, -2), (-2, -8), (4, -4)]), OV_CHR, bevel=1),
            ellipse(kn, 4.6, 4.6, 0, OV_CHR),
            foot_poly(an, fa, [(-6, 3.4), (-7, -3), (14, -3), (16, 0), (8, 3.6)], OV_OBS, 1.6),
            foot_poly(an, fa, [(9, -3), (16, -3), (17, -1), (10, -1)], OV_CHR, 0.6),
        ], OV_OBS, back=back)

    parts = []
    cape = [add(sk.sh_b, (2, -4)), add(sk.sh_f, (-2, -4)), add(tl(-4, 0), (0, 0)), add(tl(-12, -18), (-4, 6 + wave)),
            add(tl(-22, -22), (-6, 8 + wave * 1.5)), add(tl(-26, -6), (-4, wave)), add(tl(-18, 14), (0, 0))]
    parts.append(Part([poly(cape, OV_CAPE, bevel=2)], OV_CAPE))
    for a in (sk.an_b, sk.an_f):
        if a[1] < -4:
            parts.append(Part([ellipse(add(a, (0, 6)), 3.4, 5.5, 0, OV_JET)], OV_JET, outline=False))
    parts += [arm(sk.sh_b, sk.el_b, sk.wr_b, True), leg(sk.hip_b, sk.kn_b, sk.an_b, sk.fa_b, True)]
    parts.append(Part([
        ellipse(tl(0, 2), 12, 8, sk.ta + 90, OV_OBS),
        poly([tl(-10, -2), tl(10, -2), tl(12, -12), tl(-10, -14)], OV_OBS, 1, bevel=1.6),
        line(tl(-8, -6), tl(10, -6), OV_CHR[2]),
        capsule(tl(0, 6), tl(0, 18), 8, 7, OV_OBS),
        line(tl(-6, 9), tl(6, 9), OV_CHR[1]), line(tl(-6, 13), tl(6, 13), OV_CHR[1]),
        poly([tl(-14, 20), tl(15, 20), tl(18, 34), tl(12, 40), tl(-12, 40), tl(-16, 32)], OV_OBS, bevel=2.6),
        ellipse(tl(3, 30), 6.0, 6.0, 0, OV_CHR),
        ellipse(tl(3, 30), 4.2, 4.2, 0, OV_CORE),
        line(tl(-12, 22), tl(-2, 22), OV_CHR[2]), line(tl(8, 22), tl(14, 22), OV_CHR[2]),
    ], OV_OBS))
    parts.append(leg(sk.hip_f, sk.kn_f, sk.an_f, sk.fa_f, False))
    parts.append(Part([
        capsule(sk.neck, lerp(sk.neck, sk.head, 0.5), 5, 5, OV_OBS),
        poly([hl(-8, -6), hl(4, -10), hl(10, -4), hl(10, 4), hl(4, 9), hl(-6, 9), hl(-10, 2)], OV_OBS, bevel=2),
        poly([hl(-7, 7), hl(-8, 17), hl(-4, 9)], OV_CHR, bevel=1),
        poly([hl(-2, 9), hl(0, 21), hl(3, 9)], OV_CHR, bevel=1),
        poly([hl(4, 8), hl(9, 16), hl(8, 6)], OV_CHR, bevel=1),
        poly([hl(-6, 7), hl(7, 7), hl(7, 5), hl(-6, 5)], OV_CHR, bevel=0.6),
        poly([hl(3, 2), hl(10, 1), hl(10, -1), hl(3, 0)], OV_CORE, bevel=0.6),
        dot(hl(6, -4), OV_CORE[2]), dot(hl(8, -4), OV_CORE[2]),
    ], OV_OBS))
    parts.append(arm(sk.sh_f, sk.el_f, sk.wr_f, False))
    return parts


OV_ST = dict(hip=(0, -45), torso=-88, head=-90, ff=(10, -8), fff=20, bf=(-10, -9), bff=30, fh=(28, -56), bh=(-14, -54))
OV_CR = P(OV_ST, hip=(-1, -28), torso=-74, head=-82, ff=(14, -3), fff=0, bf=(-12, -3), bff=0, fh=(28, -40), bh=(-10, -38))


def overlord():
    st, cr = OV_ST, OV_CR
    beam0 = P(st, torso=-96, fh=(14, -70), bh=(10, -72))
    beam1 = P(st, hip=(-3, -45), torso=-86, fh=(36, -68), bh=(34, -66))
    slam0 = P(st, hip=(0, -48), torso=-96, fh=(10, -100), bh=(0, -98))
    slam1 = P(cr, hip=(4, -26), torso=-40, fh=(34, -4), bh=(26, -4))
    orb = P(st, torso=-94, bh=(2, -110), fh=(26, -60))
    atk = {
        'lp': ([P(st, fh=(24, -60)), P(st, hip=(2, -45), torso=-82, fh=(50, -62)), P(st, fh=(36, -60))], 18, {'active': [1], 'strike': 'fh', 'hr': 10}),
        'hp': ([P(st, torso=-100, bh=(-24, -70)), P(st, hip=(4, -45), torso=-76, bh=(54, -64), fh=(20, -50)), P(st, hip=(4, -45), torso=-78, bh=(50, -60), fh=(20, -50)), P(st, bh=(20, -58)), st],
               13, {'active': [1, 2], 'strike': 'bh', 'hr': 12}),
        'lk': ([P(st, ff=(16, -26), ffp=(1, -0.4)), P(st, hip=(-3, -46), torso=-98, ff=(44, -36), fff=-10), P(st, ff=(20, -22))], 15, {'active': [1], 'strike': 'ff', 'hr': 10}),
        'hk': ([P(st, hip=(-4, -47), torso=-106, ff=(14, -48)), P(st, hip=(-6, -48), torso=-118, ff=(46, -64), fff=-30), P(st, hip=(-6, -48), torso=-116, ff=(44, -62), fff=-30), st], 11, {'active': [1, 2], 'strike': 'ff', 'hr': 12}),
        'c_lp': ([P(cr, fh=(22, -42)), P(cr, fh=(48, -40)), P(cr, fh=(34, -41))], 18, {'active': [1], 'strike': 'fh', 'hr': 10}),
        'c_hp': ([P(cr, bh=(6, -34)), P(cr, hip=(2, -36), torso=-98, bh=(22, -100)), P(cr, hip=(2, -36), torso=-96, bh=(20, -98)), cr], 13, {'active': [1, 2], 'strike': 'bh', 'hr': 12}),
        'c_lk': ([P(cr, ff=(20, -8)), P(cr, ff=(44, -4)), P(cr, ff=(28, -5))], 16, {'active': [1], 'strike': 'ff', 'hr': 9}),
        'c_hk': ([BX.C_HK[0], BX.C_HK[1], BX.C_HK[2], cr], 11, {'active': [1, 2], 'strike': 'ff', 'hr': 11}),
        'j_p': ([P(BX.JUMP_TUCK, fh=(12, -78), bh=(-10, -60)), P(BX.JUMP_TUCK, torso=-60, fh=(44, -44), bh=(-10, -60)), P(BX.JUMP_TUCK, torso=-64, fh=(36, -48), bh=(-10, -60))], 14, {'active': [1], 'strike': 'fh', 'hr': 11}),
        'j_k': ([P(BX.JUMP_TUCK, fh=st['fh'], bh=st['bh']), P(BX.J_K[1], fh=(26, -60), bh=(-12, -60)), P(BX.J_K[2], fh=(26, -60), bh=(-12, -60))], 14, {'active': [1], 'strike': 'ff', 'hr': 11}),
    }
    specials = [
        ('sp_beam', [beam0, P(beam0, fh=(16, -72), bh=(12, -74)), beam1, P(beam1, hip=(-4, -45)), beam1, R.lerp_pose(beam1, st, 0.5)], 6, {}),
        ('sp_slam', [slam0, P(slam0, hip=(0, -50)), slam1, slam1, R.lerp_pose(slam1, st, 0.5)], 9, {'active': [2], 'strike': ['fh', 'bh'], 'hr': 12}),
        ('sp_orbital', [P(st, torso=-90, bh=(-4, -76)), orb, P(orb, bh=(3, -112)), orb], 6, {}),
        ('sp_phase', [P(cr, torso=-60, fh=(14, -30), bh=(4, -30)), cr], 8, {}),
    ]
    vict = [P(st, torso=-92, fh=(40, -90), bh=(-30, -88)), P(st, torso=-94, fh=(42, -96), bh=(-32, -94)),
            P(st, torso=-94, fh=(42, -97), bh=(-32, -95)), P(st, torso=-92, fh=(40, -92), bh=(-30, -90))]
    defeat = [P(cr, hip=(2, -30), torso=-50, head=-10, fh=(20, -6), bh=(10, -6)), P(cr, hip=(2, -29), torso=-48, head=-8, fh=(20, -5), bh=(10, -5))]
    intro = [P(cr, torso=-50, head=-10, fh=(16, -10), bh=(8, -10)), P(cr, torso=-70, head=-60, fh=(20, -30), bh=(6, -30)),
             P(st, torso=-94, fh=(40, -90), bh=(-30, -88)), st]
    block = P(st, hip=(-3, -45), torso=-96, head=-98, fh=(20, -80), bh=(16, -76))
    block_c = P(cr, torso=-84, fh=(20, -56), bh=(16, -52))
    k = 1.3
    return make('overlord', k, (196, 156, 98, 148), (6, 2, 10, 255), 40, body(k, sh_f=10 * k, sh_b=10 * k, head_r=8 * k, torso=36 * k),
                overlord_parts, st, cr, block, block_c, vict, defeat, intro, atk, specials, (-32, -134, 70, 56))


CHARS = [spark(), bulwark(), volt(), razor(), overlord()]
