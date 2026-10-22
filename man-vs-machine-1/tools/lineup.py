import sys, json
from peek import load
from png import Image
ids=['boxer','spark','bulwark','volt','razor','overlord']
anim=sys.argv[1] if len(sys.argv)>1 else 'idle'; fi=int(sys.argv[2]) if len(sys.argv)>2 else 0
W=sum(json.load(open(f'../assets/characters/{c}/{c}_anims.json'))['frame_w'] for c in ids)
out=Image(W,160,(64,70,88,255)); x=0
for c in ids:
    m=json.load(open(f'../assets/characters/{c}/{c}_anims.json')); img=load(f'../assets/characters/{c}/{c}_sheet.png')
    a=m['anims'][anim]; fr=min(fi,a['frames']-1)
    cell=img.crop(fr*m['frame_w'],a['row']*m['frame_h'],m['frame_w'],m['frame_h'])
    out.paste(cell,x,150-m['origin_y']); x+=m['frame_w']
for xx in range(W): out.set(xx,150,(40,40,40,255))
out.scaled(2).save(f'preview/lineup_{anim}_{fi}.png')
