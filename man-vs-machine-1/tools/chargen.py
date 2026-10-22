"""Sprite-sheet builder shared by all characters.

A character module exposes:
    ID, BODY, OUTLINE, FRAME=(w,h,ox,oy), build_parts(sk) -> [Part],
    ANIMS = [(name, [pose,...], fps, loop, meta_dict)], PORTRAIT_POSE
meta_dict may contain 'active': [frame indices], 'strike': key or list, 'hr': hit radius.

Output (assets/characters/<id>/):
    <id>_sheet.png   one animation per row, frames left-to-right, fixed cell size
    <id>_anims.json  cell size, origin, per-animation row/frame count/fps/loop,
                     auto-derived hitboxes for active frames and body hurtboxes
    <id>_portrait.png  2x detail head-and-shoulders render for HUD / VS screens
"""
import json
import math
import os
import sys

import pixelrig as R
from png import Image

ROOT = os.path.normpath(os.path.join(os.path.dirname(__file__), '..'))


def strike_point(sk, key):
    if key in ('fh', 'bh'):
        el, wr = (sk.el_f, sk.wr_f) if key == 'fh' else (sk.el_b, sk.wr_b)
        d = R.norm(R.sub(wr, el))
        return R.add(wr, R.mul(d, 5))
    if key in ('ff', 'bf'):
        an, toe = (sk.an_f, sk.toe_f) if key == 'ff' else (sk.an_b, sk.toe_b)
        return R.lerp(an, toe, 0.55)
    if key in ('fb', 'bb'):
        el, wr = (sk.el_f, sk.wr_f) if key == 'fb' else (sk.el_b, sk.wr_b)
        d = R.norm(R.sub(wr, el))
        return R.add(wr, R.mul(d, 15))
    if key in ('fk', 'bk'):
        return sk.kn_f if key == 'fk' else sk.kn_b
    if key == 'head':
        return sk.head
    if key == 'body':
        return R.lerp(sk.hip, sk.neck, 0.5)
    if key.startswith('pt_'):
        return sk.pose[key]
    raise KeyError(key)


def opaque_bbox(img):
    xs, ys = [], []
    for y in range(img.h):
        for x in range(img.w):
            if img.px[y * img.w + x] is not None:
                xs.append(x)
                ys.append(y)
    if not xs:
        return None
    return min(xs), min(ys), max(xs) + 1, max(ys) + 1


def build(mod, out_dir=None, preview=True):
    cid = mod.ID
    fw, fh, ox, oy = mod.FRAME
    out_dir = out_dir or os.path.join(ROOT, 'assets', 'characters', cid)
    os.makedirs(out_dir, exist_ok=True)
    anims = mod.ANIMS
    cols = max(len(a[1]) for a in anims)
    sheet = Image(fw * cols, fh * len(anims))
    meta = {'id': cid, 'frame_w': fw, 'frame_h': fh, 'origin_x': ox, 'origin_y': oy,
            'columns': cols, 'rows': len(anims), 'anims': {}}
    frames_cache = {}
    for row, (name, poses, fps, loop, info) in enumerate(anims):
        entry = {'row': row, 'frames': len(poses), 'fps': fps, 'loop': loop}
        hits = []
        for col, pose in enumerate(poses):
            sk = R.solve(mod.BODY, pose)
            img = R.render(mod.build_parts(sk), fw, fh, ox, oy, mod.OUTLINE)
            sheet.paste(img, col * fw, row * fh)
            frames_cache[(name, col)] = img
            if col in info.get('active', []):
                keys = info.get('strike', 'fh')
                if isinstance(keys, str):
                    keys = [keys]
                r = info.get('hr', 9)
                xs, ys = [], []
                for k in keys:
                    p = strike_point(sk, k)
                    xs += [p[0] - r, p[0] + r]
                    ys += [p[1] - r, p[1] + r]
                hits.append([round(min(xs)), round(min(ys)), round(max(xs) - min(xs)), round(max(ys) - min(ys))])
        if hits:
            # union of the active frames' strike areas
            x0 = min(h[0] for h in hits)
            y0 = min(h[1] for h in hits)
            x1 = max(h[0] + h[2] for h in hits)
            y1 = max(h[1] + h[3] for h in hits)
            entry['hitbox'] = [x0, y0, x1 - x0, y1 - y0]
        if 'active' in info:
            entry['active_frames'] = info['active']
        meta['anims'][name] = entry
    # body hurtboxes from silhouettes (shrunk to the torso core)
    def hb(name, idx=0, shrink=0.72):
        img = frames_cache.get((name, idx))
        bb = opaque_bbox(img)
        x0, y0, x1, y1 = bb
        # horizontal core: centred on the origin, limited width
        w = (x1 - x0) * shrink
        cx = (x0 + x1) / 2 - ox
        w = min(w, mod.CORE_W)
        return [round(cx - w / 2), y0 - oy + 2, round(w), (oy - y0) - 2]
    meta['hurt_stand'] = hb('idle')
    meta['hurt_crouch'] = hb('crouch', len([a for a in anims if a[0] == 'crouch'][0][1]) - 1)
    meta['hurt_air'] = hb('jump', 1)
    meta['push_w'] = mod.CORE_W
    with open(os.path.join(out_dir, cid + '_anims.json'), 'w') as f:
        json.dump(meta, f, indent=1)
    sheet.save(os.path.join(out_dir, cid + '_sheet.png'))
    # portrait: render the portrait pose at 2x and crop the head & shoulders
    pp = getattr(mod, 'PORTRAIT_POSE', anims[0][1][0])
    sk = R.solve(mod.BODY, pp)
    S = 2
    pw, ph = mod.PORTRAIT_BOX[2] * S, mod.PORTRAIT_BOX[3] * S
    px0, py0 = mod.PORTRAIT_BOX[0], mod.PORTRAIT_BOX[1]
    img = R.render(mod.build_parts(sk), pw, ph, -px0 * S, -py0 * S, mod.OUTLINE, scale=S)
    img.save(os.path.join(out_dir, cid + '_portrait.png'))
    if preview:
        prev_dir = os.path.join(ROOT, 'tools', 'preview')
        os.makedirs(prev_dir, exist_ok=True)
        bg = Image(sheet.w, sheet.h, (60, 64, 80, 255))
        bg.paste(sheet, 0, 0)
        # ground line marks
        for row in range(len(anims)):
            for x in range(sheet.w):
                if x % 4 == 0:
                    bg.set(x, row * fh + oy, (90, 200, 90, 255))
        bg.scaled(2).save(os.path.join(prev_dir, cid + '_sheet_preview.png'))
        img.scaled(2).save(os.path.join(prev_dir, cid + '_portrait_preview.png'))
    return meta


if __name__ == '__main__':
    import importlib
    for name in sys.argv[1:]:
        m = importlib.import_module(name.split(':')[0])
        mods = getattr(m, 'CHARS', [m])
        only = name.split(':')[1] if ':' in name else None
        for c in mods:
            if only and c.ID != only:
                continue
            meta = build(c)
            print(c.ID, 'rows', meta['rows'], 'cols', meta['columns'])
