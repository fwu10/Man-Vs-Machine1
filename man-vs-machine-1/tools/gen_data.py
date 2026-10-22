"""Writes data/characters/*.json: stats, frame data, command specials and AI
profiles. Frame data is in 60 Hz frames: startup / active / recovery."""
import json
import os

ROOT = os.path.normpath(os.path.join(os.path.dirname(__file__), '..'))


def A(s, a, r, dmg, **kw):
    d = dict(startup=s, active=a, recovery=r, damage=dmg)
    d.setdefault('hitstun', kw.pop('hs', 12 + int(dmg / 12)))
    d.setdefault('blockstun', kw.pop('bs', 8 + int(dmg / 18)))
    d.update(kw)
    return d


JNORMALS = {'j_lp': 'j_p', 'j_hp': 'j_p', 'j_lk': 'j_k', 'j_hk': 'j_k'}
LIGHT_P = ['lp', 'hp', 'lk', 'c_lp', 'c_lk', 'special', 'super']
LIGHT_K = ['hk', 'hp', 'special', 'super']
HEAVY = ['special', 'super']
LOWS = ['c_lk', 'c_lp', 'lp', 'special', 'super']

CHARS = {}

# ----------------------------------------------------------------- the boxer
CHARS['boxer'] = dict(
    name='IRON COLE', full_name="MARCUS 'IRON' COLE", robot=False, hit_sfx='flesh',
    title='LAST CHAMPION OF THE HUMAN LEAGUE',
    bio='Undefeated heavyweight. When the leagues replaced fighters with machines, he kept training.',
    health=1000, walk_fwd=2.4, walk_back=1.9, jump_velocity=8.6, jump_x=2.8, gravity=0.45, weight=1.0, color='#e44a3c',
    attacks={
        'lp': A(3, 3, 7, 30, knockback=2.2, cancel=LIGHT_P, sfx='punch_l', name='JAB'),
        'hp': A(6, 4, 15, 75, knockback=4.0, strength='heavy', cancel=HEAVY, sfx='punch_h', name='CROSS'),
        'lk': A(5, 3, 10, 40, knockback=2.6, cancel=LIGHT_K, sfx='kick_l', name='SNAP KICK'),
        'hk': A(8, 4, 18, 85, knockback=4.5, strength='heavy', sfx='kick_h', name='ROUNDHOUSE'),
        'c_lp': A(3, 3, 7, 25, knockback=2.0, cancel=LOWS, sfx='punch_l'),
        'c_hp': A(5, 5, 18, 70, knockback=3.0, strength='heavy', cancel=HEAVY, sfx='punch_h', launch=[1.5, -6.0], name='UPPERCUT'),
        'c_lk': A(4, 3, 9, 25, level='low', knockback=2.0, cancel=LOWS, sfx='kick_l'),
        'c_hk': A(7, 4, 22, 60, level='low', knockdown=True, launch=[1.5, -3.5], strength='heavy', sfx='kick_h', name='SWEEP'),
        'j_p': A(5, 6, 4, 55, level='overhead', knockback=2.0, hs=16, sfx='punch_h'),
        'j_k': A(5, 8, 4, 65, level='overhead', knockback=2.4, hs=17, sfx='kick_h'),
        'sp_rush': A(10, 8, 20, 110, chip=15, special=True, strength='heavy', knockdown=True, launch=[4.5, -4.5],
                     move=[[6, 18, 7.0]], hitstop=12, shake=5, sfx='punch_h', name='IRON RUSH'),
        'sp_hook': A(4, 8, 22, 100, chip=12, special=True, strength='heavy', knockdown=True, launch=[2.2, -7.5],
                     invuln=7, air_launch=[4, 1.2, -6.6], hitstop=12, shake=5, sfx='punch_h', name='RISING HOOK'),
        'super': A(6, 30, 26, 40, special=True, super=True, hits=6, hit_interval=5, hs=22, bs=12, knockback=1.2,
                   move=[[6, 30, 2.6]], invuln=14, hitstop=5, shake=3, chip=8, strength='heavy', sfx='punch_h',
                   name='KNOCKOUT STORM'),
    },
    specials=[dict(attack='super', motion='DD', button='hp'),
              dict(attack='sp_rush', motion='FF', button='hp'),
              dict(attack='sp_hook', motion='QCF', button='hp')],
    # CPU profile for the boxer (used by attract-mode / automated tests only)
    ai=dict(reaction=16, aggression=0.55, range=60, block=0.5, anti_air=0.4, punish=0.5, jump=0.08, special=0.2,
            combo=0.5, retreat=0.15, pause=14,
            close=[['lp', 3], ['c_lk', 2], ['hp', 1], ['lk', 1]], mid=[['hk', 2], ['sp_rush', 1], ['lk', 2]],
            far_specials=[], anti_air_moves=['sp_hook', 'c_hp'], punish_moves=['sp_rush', 'hp', 'super'],
            combos={'lp': ['lp', 'hp'], 'hp': ['sp_rush', 'super'], 'c_lk': ['c_lp', 'sp_rush']}, jump_attack='j_k'),
)

# ----------------------------------------------------------------- SPARK
CHARS['spark'] = dict(
    name='SPARK', full_name='SPARK  /  UNIT SP-01', title='SPARRING DROID',
    bio='Mass-produced training unit. Balanced, polite and relentlessly by-the-book.',
    health=900, walk_fwd=2.1, walk_back=1.7, jump_velocity=8.2, jump_x=2.6, gravity=0.44, weight=1.0, color='#ff9a34',
    attacks={
        'lp': A(4, 3, 8, 28, knockback=2.2, cancel=LIGHT_P, sfx='punch_l'),
        'hp': A(7, 4, 16, 70, knockback=4.0, strength='heavy', cancel=HEAVY, sfx='punch_h'),
        'lk': A(5, 3, 11, 38, knockback=2.6, cancel=LIGHT_K, sfx='kick_l'),
        'hk': A(9, 4, 19, 80, knockback=4.5, strength='heavy', sfx='kick_h'),
        'c_lp': A(4, 3, 8, 24, cancel=LOWS, sfx='punch_l'),
        'c_hp': A(6, 5, 19, 65, strength='heavy', cancel=HEAVY, sfx='punch_h', launch=[1.5, -6.0]),
        'c_lk': A(5, 3, 10, 24, level='low', cancel=LOWS, sfx='kick_l'),
        'c_hk': A(8, 4, 23, 55, level='low', knockdown=True, launch=[1.5, -3.5], strength='heavy', sfx='kick_h'),
        'j_p': A(5, 6, 4, 50, level='overhead', hs=16, sfx='punch_h'),
        'j_k': A(5, 8, 4, 60, level='overhead', hs=16, sfx='kick_h'),
        'sp_dash': A(12, 10, 20, 90, chip=10, special=True, strength='heavy', knockdown=True, launch=[4, -4],
                     move=[[8, 22, 6.0]], hitstop=11, shake=4, sfx='metal_h', name='SPARK DASH'),
        'sp_shot': A(12, 2, 28, 60, chip=10, special=True, hs=18, anim_active=[1, 2], no_hitbox=True,
                     projectile=dict(kind='pellet', speed=3.2, w=14, h=10, x=34, y=-62, color='#ff9a34', sfx='zap'),
                     sfx='zap', name='ION PELLET'),
    },
    specials=[dict(attack='sp_dash', motion='FF', button='hp'), dict(attack='sp_shot', motion='QCF', button='lp')],
    ai=dict(reaction=22, aggression=0.45, range=64, block=0.35, anti_air=0.25, punish=0.25, jump=0.08, special=0.2,
            combo=0.3, retreat=0.15, pause=20,
            close=[['lp', 3], ['lk', 2], ['c_lk', 2], ['hp', 1]], mid=[['hk', 2], ['lk', 2], ['sp_dash', 1]],
            far_specials=['sp_shot'], anti_air_moves=['c_hp'], punish_moves=['hp', 'sp_dash', 'hk'],
            combos={'lp': ['lp', 'hp'], 'c_lk': ['c_lk', 'sp_dash']}, jump_attack='j_k'),
)

# ----------------------------------------------------------------- BULWARK
CHARS['bulwark'] = dict(
    name='BULWARK', full_name='BULWARK  /  SIEGE FRAME B-9', title='DEMOLITION HEAVYWEIGHT',
    bio='A walking breach-charge. Absorbs punishment and answers with tons of hydraulic force.',
    health=1300, walk_fwd=1.3, walk_back=1.0, jump_velocity=7.2, jump_x=2.0, gravity=0.46, weight=1.6, color='#f8d24a',
    attacks={
        'lp': A(5, 3, 10, 45, knockback=3.0, cancel=['hp', 'lp', 'special'], sfx='punch_l'),
        'hp': A(14, 4, 26, 140, knockback=6.0, strength='heavy', armor=10, hitstop=14, shake=6, sfx='slam', cancel=HEAVY),
        'lk': A(7, 3, 14, 55, knockback=3.5, sfx='kick_l', cancel=['special']),
        'hk': A(12, 4, 24, 120, knockback=7.0, strength='heavy', hitstop=13, shake=5, sfx='kick_h'),
        'c_lp': A(5, 3, 10, 40, cancel=['c_lp', 'special'], sfx='punch_l'),
        'c_hp': A(9, 5, 24, 110, strength='heavy', sfx='punch_h', launch=[2, -6]),
        'c_lk': A(7, 3, 14, 45, level='low', sfx='kick_l', cancel=['special']),
        'c_hk': A(12, 4, 28, 90, level='low', knockdown=True, launch=[2.5, -3.5], strength='heavy', sfx='kick_h'),
        'j_p': A(7, 6, 6, 110, level='overhead', strength='heavy', hs=18, sfx='slam'),
        'j_k': A(6, 8, 6, 100, level='overhead', strength='heavy', hs=18, sfx='kick_h'),
        'sp_hammer': A(20, 4, 32, 180, chip=25, special=True, armor=18, strength='heavy', knockdown=True, level='overhead',
                       launch=[5, -5], hitstop=16, shake=9, sfx='slam', name='SIEGE HAMMER'),
        'sp_stomp': A(22, 2, 30, 80, chip=12, special=True, level='low', hs=24, can_hit_air=False, anim_active=[2, 3],
                      no_hitbox=True, shake=4,
                      projectile=dict(kind='wave', speed=4.0, w=30, h=18, x=34, y=-9, life=120, color='#f8d24a', sfx='slam'),
                      sfx='slam', name='QUAKE STOMP'),
    },
    specials=[dict(attack='sp_hammer', motion='FF', button='hp'), dict(attack='sp_stomp', motion='QCF', button='hk')],
    ai=dict(reaction=20, aggression=0.3, range=80, block=0.55, anti_air=0.35, punish=0.6, jump=0.03, special=0.15,
            combo=0.3, retreat=0.05, armor=0.35, armor_move='sp_hammer', pause=30,
            close=[['lp', 2], ['hp', 2], ['c_hk', 1]], mid=[['hk', 2], ['sp_hammer', 1], ['lk', 1]],
            far_specials=['sp_stomp'], anti_air_moves=['c_hp'], punish_moves=['hp', 'hk', 'sp_hammer'],
            combos={'lp': ['hp'], 'c_lp': ['sp_hammer']}, jump_attack='j_p'),
)

# ----------------------------------------------------------------- VOLT
VCH = ['lp', 'hp', 'lk', 'c_lp', 'c_lk', 'special']
CHARS['volt'] = dict(
    name='VOLT', full_name='VOLT  /  PURSUIT UNIT V-3', title='HIGH-VOLTAGE STRIKER',
    bio='Built for speed above all. Overclocked servos and a short temper - and a shorter fuse.',
    health=800, walk_fwd=3.0, walk_back=2.4, jump_velocity=9.0, jump_x=3.2, gravity=0.5, weight=0.85, color='#38e0ff',
    attacks={
        'lp': A(2, 2, 6, 22, knockback=1.8, cancel=VCH, sfx='punch_l'),
        'hp': A(4, 3, 12, 55, knockback=3.2, strength='heavy', cancel=['special'], sfx='punch_h'),
        'lk': A(3, 3, 8, 28, knockback=2.0, cancel=['hk', 'lp', 'special'], sfx='kick_l'),
        'hk': A(6, 4, 14, 70, knockback=4.0, strength='heavy', sfx='kick_h', cancel=['special']),
        'c_lp': A(2, 2, 6, 20, cancel=VCH, sfx='punch_l'),
        'c_hp': A(4, 5, 14, 60, strength='heavy', sfx='punch_h', launch=[1.5, -6]),
        'c_lk': A(3, 2, 7, 22, level='low', cancel=VCH, sfx='kick_l'),
        'c_hk': A(6, 3, 16, 55, level='low', knockdown=True, launch=[1.5, -3.5], strength='heavy', sfx='kick_h'),
        'j_p': A(4, 6, 3, 45, level='overhead', hs=15, sfx='punch_h'),
        'j_k': A(4, 7, 3, 50, level='overhead', hs=15, sfx='kick_h'),
        'sp_bolt': A(9, 2, 20, 55, chip=8, special=True, hs=16, anim_active=[2, 3], no_hitbox=True,
                     projectile=dict(kind='bolt', speed=6.5, w=22, h=12, x=36, y=-62, color='#38e0ff', sfx='zap'),
                     sfx='zap', name='ARC BOLT'),
        'sp_rush': A(6, 18, 18, 35, chip=5, special=True, hits=3, hit_interval=6, hs=16, knockback=1.5,
                     move=[[5, 22, 6.5]], fx='electric', sfx='zap', name='THUNDER RUSH'),
    },
    specials=[dict(attack='sp_rush', motion='FF', button='hp'), dict(attack='sp_bolt', motion='QCF', button='lp')],
    ai=dict(reaction=14, aggression=0.75, range=52, block=0.4, anti_air=0.3, punish=0.4, jump=0.18, special=0.25,
            combo=0.55, retreat=0.1, pause=8,
            close=[['lp', 3], ['c_lk', 3], ['lk', 2], ['hp', 1]], mid=[['sp_rush', 1], ['hk', 2], ['lk', 2]],
            far_specials=['sp_bolt'], anti_air_moves=['c_hp'], punish_moves=['sp_rush', 'hp', 'hk'],
            combos={'lp': ['lp', 'hp', 'sp_rush'], 'c_lk': ['c_lk', 'lp', 'sp_rush'], 'lk': ['hk', 'sp_rush']},
            jump_attack='j_k'),
)

# ----------------------------------------------------------------- RAZOR
CHARS['razor'] = dict(
    name='RAZOR', full_name='RAZOR  /  DUELIST R-0', title='BLADE COUNTER-FIGHTER',
    bio='Trained on ten thousand recorded duels. It waits for your mistake - and it never misses one.',
    health=950, walk_fwd=2.3, walk_back=2.0, jump_velocity=8.3, jump_x=2.7, gravity=0.45, weight=1.0, color='#ff4040',
    attacks={
        'lp': A(4, 3, 9, 32, knockback=2.2, cancel=['lp', 'hp', 'special'], sfx='slash_l'),
        'hp': A(8, 4, 18, 85, knockback=4.0, strength='heavy', sfx='slash', cancel=HEAVY),
        'lk': A(5, 3, 11, 40, knockback=2.6, sfx='kick_l', cancel=['special']),
        'hk': A(9, 4, 18, 85, knockback=4.5, strength='heavy', sfx='kick_h'),
        'c_lp': A(4, 3, 9, 28, cancel=LOWS, sfx='slash_l'),
        'c_hp': A(6, 5, 18, 75, strength='heavy', sfx='slash', launch=[1.5, -6]),
        'c_lk': A(5, 3, 10, 30, level='low', cancel=LOWS, sfx='kick_l'),
        'c_hk': A(8, 4, 22, 65, level='low', knockdown=True, launch=[1.5, -3.5], strength='heavy', sfx='kick_h'),
        'j_p': A(5, 6, 4, 60, level='overhead', hs=16, sfx='slash'),
        'j_k': A(5, 7, 4, 60, level='overhead', hs=16, sfx='kick_h'),
        'sp_lunge': A(11, 6, 22, 100, chip=12, special=True, strength='heavy', knockdown=True, launch=[4, -4],
                      move=[[6, 16, 5.5]], hitstop=12, shake=4, sfx='slash', name='EDGE LUNGE'),
        'sp_parry': A(3, 26, 16, 0, special=True, counter=True, counter_attack='sp_counter', no_hitbox=True, name='BLADE PARRY'),
        'sp_counter': A(3, 5, 18, 120, special=True, strength='heavy', knockdown=True, launch=[4, -5], hitstop=16, shake=6,
                        sfx='slash', name='COUNTER EDGE'),
    },
    specials=[dict(attack='sp_lunge', motion='FF', button='hp'), dict(attack='sp_parry', motion='QCB', button='hp')],
    ai=dict(reaction=12, aggression=0.4, range=84, block=0.6, anti_air=0.45, punish=0.75, parry=0.4, parry_move='sp_parry',
            jump=0.06, special=0.2, combo=0.45, retreat=0.4, pause=16,
            close=[['lp', 2], ['c_lk', 2], ['hp', 1]], mid=[['lp', 3], ['hk', 1], ['c_hk', 1], ['sp_lunge', 1]],
            far_specials=[], anti_air_moves=['c_hp'], punish_moves=['sp_lunge', 'hp', 'lp'],
            combos={'lp': ['lp', 'sp_lunge'], 'c_lk': ['c_lp', 'sp_lunge']}, jump_attack='j_p'),
)

# ----------------------------------------------------------------- OVERLORD
CHARS['overlord'] = dict(
    name='OVERLORD', full_name='OVERLORD  /  CORE INTELLIGENCE', title='THE MACHINE THAT RUNS THE MACHINES',
    bio='The mind behind the robot leagues. It has studied every human fighter ever recorded. Except one.',
    health=1400, walk_fwd=1.9, walk_back=1.7, jump_velocity=8.0, jump_x=2.4, gravity=0.42, weight=1.4, color='#ff1a1a',
    attacks={
        'lp': A(4, 3, 10, 40, knockback=2.4, cancel=['lp', 'hp', 'special', 'super'], sfx='slash_l'),
        'hp': A(9, 4, 20, 110, knockback=5.5, strength='heavy', hitstop=12, shake=4, sfx='punch_h', cancel=HEAVY),
        'lk': A(6, 3, 12, 50, knockback=2.8, sfx='kick_l', cancel=['special']),
        'hk': A(10, 4, 20, 110, knockback=5.0, strength='heavy', sfx='kick_h'),
        'c_lp': A(4, 3, 9, 35, cancel=LOWS, sfx='slash_l'),
        'c_hp': A(7, 5, 20, 100, strength='heavy', sfx='punch_h', launch=[2, -6]),
        'c_lk': A(6, 3, 12, 40, level='low', cancel=LOWS, sfx='kick_l'),
        'c_hk': A(9, 4, 24, 90, level='low', knockdown=True, launch=[2, -3.5], strength='heavy', sfx='kick_h'),
        'j_p': A(6, 6, 5, 90, level='overhead', strength='heavy', hs=17, sfx='punch_h'),
        'j_k': A(6, 7, 5, 90, level='overhead', strength='heavy', hs=17, sfx='kick_h'),
        'sp_beam': A(34, 16, 30, 150, chip=30, special=True, strength='heavy', knockdown=True, launch=[5, -5], level='high',
                     hitbox=[40, -102, 640, 22], fx='beam', telegraph=34, hitstop=12, shake=6, sfx='laser',
                     anim_active=[2, 4], name='ANNIHILATOR BEAM'),
        'sp_slam': A(22, 3, 30, 120, chip=15, special=True, strength='heavy', knockdown=True, launch=[3, -5], fx='charge',
                     telegraph=22, hitstop=14, shake=8, sfx='slam', name='GRAVITY SLAM',
                     projectile=dict(kind='wave', speed=5.0, w=34, h=22, x=40, y=-11, life=120, color='#ff3a2a', sfx='slam')),
        'sp_orbital': A(24, 2, 26, 120, chip=20, special=True, strength='heavy', knockdown=True, launch=[2, -5], no_hitbox=True,
                        anim_active=[1, 2], telegraph=24, hitstop=12, shake=6, sfx='laser', name='ORBITAL STRIKE',
                        projectile=dict(kind='orbital', delay=45, active=10, w=30, sfx='alarm')),
        'sp_extinction': A(20, 2, 30, 100, chip=15, special=True, super=True, strength='heavy', knockdown=True, launch=[2, -5],
                           no_hitbox=True, anim='sp_orbital', anim_active=[1, 2], hitstop=12, shake=7, sfx='laser',
                           name='EXTINCTION PROTOCOL',
                           projectile=dict(kind='orbital', delay=40, active=10, w=30, count=3, spacing=90, stagger=14, sfx='alarm')),
        'sp_phase': A(10, 1, 14, 0, special=True, teleport=True, invuln=18, no_hitbox=True, name='PHASE SHIFT'),
    },
    specials=[dict(attack='sp_extinction', motion='DD', button='hp'),
              dict(attack='sp_beam', motion='QCF', button='hp'), dict(attack='sp_slam', motion='QCF', button='hk'),
              dict(attack='sp_orbital', motion='QCB', button='hp'), dict(attack='sp_phase', motion='BF', button='lk')],
    ai=dict(reaction=10, aggression=0.6, range=76, block=0.65, anti_air=0.5, punish=0.65, jump=0.05, special=0.35,
            combo=0.5, retreat=0.15, phase2=True, pause=12,
            close=[['lp', 2], ['hp', 2], ['c_lk', 1], ['sp_slam', 1], ['sp_phase', 1]],
            mid=[['hk', 2], ['sp_beam', 1], ['c_hk', 1], ['sp_slam', 1]],
            far_specials=['sp_beam', 'sp_orbital', 'sp_extinction', 'sp_phase'], anti_air_moves=['c_hp'],
            punish_moves=['hp', 'hk', 'sp_slam'], combos={'lp': ['hp', 'sp_slam'], 'c_lp': ['c_hk'], 'lk': ['sp_beam']},
            jump_attack='j_p'),
)

for cid, d in CHARS.items():
    d.setdefault('normals', JNORMALS)
    d.setdefault('ai', {})
    with open(os.path.join(ROOT, 'data', 'characters', cid + '.json'), 'w', newline='\n') as f:
        json.dump(d, f, indent=1)
print('wrote', list(CHARS))
