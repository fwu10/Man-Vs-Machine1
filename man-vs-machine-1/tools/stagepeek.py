import sys, os, json
from peek import load
from png import Image
sid=sys.argv[1]; opp=sys.argv[2]
out=Image(640,360,(0,0,0,255))
for l in ['far','crowd','mid','floor']:
    p=f'../assets/backgrounds/{sid}/{l}.png'
    if os.path.exists(p):
        img=load(p); out.paste(img,-(img.w-640)//2,0)
for cid,x,flip in (('boxer',230,False),(opp,410,True)):
    m=json.load(open(f'../assets/characters/{cid}/{cid}_anims.json')); img=load(f'../assets/characters/{cid}/{cid}_sheet.png')
    cell=img.crop(0,0,m['frame_w'],m['frame_h'])
    if flip:
        f=Image(cell.w,cell.h)
        for y in range(cell.h):
            for xx in range(cell.w): f.px[y*cell.w+xx]=cell.px[y*cell.w+cell.w-1-xx]
        cell=f
    out.paste(cell,x-m['origin_x'],318-m['origin_y'])
out.scaled(2).save(f'preview/stage_{sid}.png')
